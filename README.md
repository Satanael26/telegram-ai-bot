Telegram bot minimal

Requisitos
- Python 3.10+
- Variables de entorno:
  - TELEGRAM_TOKEN: token de tu bot (obligatorio)
  - DONATION_URL: (opcional) enlace a PayPal/Ko-fi
  - ADMIN_IDS: (opcional) lista separada por comas de IDs de Telegram que recibirán alertas de error y pueden usar comandos admin, por ejemplo: "12345678,87654321"
  - LOG_LEVEL: (opcional) nivel de logs (DEBUG/INFO/WARNING/ERROR). Default: INFO
  - LOG_FILE: (opcional) fichero donde escribir logs. Default: bot.log
  - SENTRY_DSN: (opcional) DSN de Sentry para reporte de errores remoto

Instalación
En PowerShell (temporal):

```powershell
python -m pip install -r requirements.txt
$env:TELEGRAM_TOKEN = "TU_TOKEN_AQUI"
$env:DONATION_URL = "https://paypal.me/TU_USUARIO"  # opcional
python .\bot.py
```

Comandos disponibles
- /start - inicia el bot
- /donar o /donate - enlace para donar
- /help - muestra ayuda (localizada según el idioma del cliente: es/en/ru)

Notas
- El token debe mantenerse privado; no lo subas a repositorios públicos.
- Para producción considera usar webhooks, logging, y una base de datos para persistencia de usuarios y créditos.
 - Logging: el bot escribe logs a consola y a un fichero rotatorio (LOG_FILE). Puedes configurar LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES y LOG_BACKUP_COUNT.
 - Si quieres recibir alertas de errores por Sentry, configura SENTRY_DSN.
