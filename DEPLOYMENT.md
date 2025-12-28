# 🚀 DEPLOYMENT - PONER EL BOT EN PRODUCCIÓN

## 📍 OPCIONES DE HOSTING

### OPCIÓN 1: Heroku (Más fácil, gratis no disponible)
- Costo: $50-100/mes (mínimo)
- Setup: 20 minutos
- Mejor para: Rápido deployment

### OPCIÓN 2: DigitalOcean (Recomendado)
- Costo: $6-20/mes
- Setup: 45 minutos
- Mejor para: Costo-beneficio

### OPCIÓN 3: AWS (Escalable)
- Costo: $10-50/mes (depende uso)
- Setup: 1-2 horas
- Mejor para: Alto tráfico

### OPCIÓN 4: VPS Económico (Bandwagon, Linode)
- Costo: $3.50-5/mes
- Setup: 1 hora
- Mejor para: Presupuesto bajo

---

## 📚 DEPLOYMENT EN DIGITALOCEAN (Recomendado)

### PASO 1: Crear Droplet

1. Ve a https://digitalocean.com
2. Click en "Create" → "Droplets"
3. Selecciona:
   - **OS:** Ubuntu 22.04
   - **Plan:** Basic $6/mes (suficiente para empezar)
   - **Region:** Cercana a tus usuarios
   - **SSH Key:** Crea una (o usa password)
4. Click "Create Droplet"

### PASO 2: Conectar al Droplet

```bash
# En tu terminal local
ssh root@TU_IP_DROPLET

# Primera vez: verifica el fingerprint
# Escribir: yes
```

### PASO 3: Instalar Dependencias

```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar Python y pip
apt install -y python3 python3-pip python3-venv git

# Instalar Nginx (proxy reverso)
apt install -y nginx

# Instalar Certbot (SSL gratis)
apt install -y certbot python3-certbot-nginx
```

### PASO 4: Clonar y Configurar Bot

```bash
# Crear directorio
mkdir -p /var/www/telegram-bot
cd /var/www/telegram-bot

# Clonar tu repo (o copiar archivos)
git clone https://github.com/TU_USER/telegram-bot.git .

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env desde ejemplo
cp .env.example .env

# EDITAR .env CON TUS VALORES
nano .env

# Verificar setup
python3 validate_setup.py
```

### PASO 5: Crear Servicio Systemd para Bot

Crear archivo: `/etc/systemd/system/telegram-bot.service`

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Pegar contenido:

```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/telegram-bot
Environment="PATH=/var/www/telegram-bot/venv/bin"
ExecStart=/var/www/telegram-bot/venv/bin/python3 /var/www/telegram-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

### PASO 6: Crear Servicio Systemd para Flask

Crear archivo: `/etc/systemd/system/flask-webhook.service`

```bash
sudo nano /etc/systemd/system/flask-webhook.service
```

```ini
[Unit]
Description=Flask Webhook Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/telegram-bot
Environment="PATH=/var/www/telegram-bot/venv/bin"
Environment="FLASK_PORT=5000"
ExecStart=/var/www/telegram-bot/venv/bin/python3 /var/www/telegram-bot/webhook_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo systemctl enable flask-webhook
sudo systemctl start flask-webhook
sudo systemctl status flask-webhook
```

### PASO 7: Configurar Nginx Proxy

Crear archivo: `/etc/nginx/sites-available/telegram-bot`

```bash
sudo nano /etc/nginx/sites-available/telegram-bot
```

```nginx
upstream flask_app {
    server localhost:5000;
}

server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        access_log off;
        proxy_pass http://flask_app;
    }
}
```

Activar:

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/

# Probar config
sudo nginx -t

# Reiniciar
sudo systemctl restart nginx
```

### PASO 8: SSL (HTTPS)

```bash
# Generar certificado Let's Encrypt
sudo certbot --nginx -d tu-dominio.com

# Seguir las instrucciones
# Seleccionar: 2 (redirect HTTP a HTTPS)
```

### PASO 9: Configurar Stripe Webhook

1. Ve a https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. URL: `https://tu-dominio.com/stripe-webhook`
4. Eventos: 
   - customer.subscription.created
   - customer.subscription.updated
   - customer.subscription.deleted
   - invoice.payment_succeeded
5. Copia el webhook secret
6. Actualiza `.env`:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_xxxxx
   ```

### PASO 10: Monitoreo

```bash
# Ver logs del bot
journalctl -u telegram-bot -f

# Ver logs de Flask
journalctl -u flask-webhook -f

# Ver logs de Nginx
tail -f /var/log/nginx/error.log
```

---

## 🐳 DEPLOYMENT CON DOCKER (Alternativa)

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorio para imágenes
RUN mkdir -p imagenes_generadas

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/health')"

# Por defecto, ejecutar bot
CMD ["python3", "bot.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: telegram-bot
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}
    volumes:
      - ./imagenes_generadas:/app/imagenes_generadas
      - ./bot_data.sqlite:/app/bot_data.sqlite
    restart: always

  webhook:
    build: .
    container_name: flask-webhook
    command: python3 webhook_server.py
    environment:
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}
      - FLASK_PORT=5000
    ports:
      - "5000:5000"
    volumes:
      - ./bot_data.sqlite:/app/bot_data.sqlite
    restart: always

  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certbot:/etc/letsencrypt:ro
    depends_on:
      - webhook
    restart: always
```

Deploy:

```bash
# Construir imágenes
docker-compose build

# Ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f bot
```

---

## ✅ CHECKLIST PRE-PRODUCCIÓN

### Antes de ir live:

- [ ] Base de datos SQL en producción (no SQLite)
- [ ] Backups automáticos de BD
- [ ] Monitoreo de errors (Sentry)
- [ ] Rate limiting en Telegram
- [ ] SSL/HTTPS configurado
- [ ] Logs persistentes
- [ ] Alertas de errores por email
- [ ] Test de pago completo (usar tarjeta de prueba Stripe)
- [ ] Test de renovación automática
- [ ] Plan de rollback

---

## 📊 MONITOREO EN PRODUCCIÓN

### Uptime Monitoring

```bash
# Usar servicios como:
# - UptimeRobot.com (gratis)
# - Pingdom.com
# - StatusCake.com

# Config: healthcheck cada 5 minutos
URL: https://tu-dominio.com/health
```

### Error Tracking

```bash
# Usar Sentry.io:
# 1. Crea cuenta
# 2. Crea proyecto Python
# 3. Copia DSN en .env
# 4. Ya está monitoreando errores
```

### Logging

```bash
# Ver errores
journalctl -u telegram-bot -n 100

# Guardar logs en archivo
journalctl -u telegram-bot > logs.txt

# Búsqueda de errores
journalctl -u telegram-bot | grep ERROR
```

---

## 🔄 ACTUALIZAR BOT EN PRODUCCIÓN

```bash
# Conectar al servidor
ssh root@TU_IP

# Cambiar a directorio
cd /var/www/telegram-bot

# Descargar cambios
git pull

# Instalar nuevas dependencias (si las hay)
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar servicio
sudo systemctl restart telegram-bot
sudo systemctl restart flask-webhook

# Verificar estado
sudo systemctl status telegram-bot
```

---

## 💾 BACKUP DE BASE DE DATOS

```bash
# Backup manual
cp bot_data.sqlite bot_data.sqlite.backup

# Backup automático diario
crontab -e

# Agregar línea:
0 2 * * * cp /var/www/telegram-bot/bot_data.sqlite /var/backups/bot_data_$(date +\%Y\%m\%d).sqlite
```

---

## 🚨 TROUBLESHOOTING

### Bot no responde

```bash
# Revisar estado
sudo systemctl status telegram-bot

# Si está stopped
sudo systemctl start telegram-bot

# Ver últimos logs
journalctl -u telegram-bot -n 50
```

### Webhook no funciona

```bash
# Verificar Flask está corriendo
curl http://localhost:5000/health

# Si no responde
sudo systemctl restart flask-webhook

# Verificar logs
journalctl -u flask-webhook -n 50
```

### Certificado SSL expirado

```bash
# Renovar
sudo certbot renew

# Automatizado (cron):
# 0 0 1 * * /usr/bin/certbot renew
```

---

## 📈 ESCALAMIENTO

### Cuando crece el tráfico:

1. **Incrementar recursos del Droplet**
   - Upgrade a $12-20/mes si es necesario

2. **Database upgrade**
   - Cambiar de SQLite a PostgreSQL

3. **Cache layer**
   - Agregar Redis para sesiones

4. **CDN**
   - CloudFlare para imágenes estáticas

5. **Load balancer**
   - Si múltiples servidores

---

## 💰 COSTOS MENSUALES

| Servicio | Costo |
|----------|-------|
| DigitalOcean Droplet | $6 |
| Dominio | $10 |
| Stripe | 2.9% + $0.30 por transacción |
| Sentry (opcional) | $0-29 |
| **Total mínimo** | **~$16/mes** |

Con 30 clientes @ $35/mes = $1050 - $16 = **$1034 ganancia**

---

**¡Listo! Ahora tu bot está en línea y monetizando 24/7** 🚀
