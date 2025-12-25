# 🧠 Bot Acompañante Emocional - Documentación

## Propósito

**Este bot NO es para ser "útil". Es para hacer que te sientas menos solo/a.**

Un acompañante emocional genuino que:
- Escucha sin juzgar
- Valida tus emociones
- Acompaña en silencio si es necesario
- Crea contenido reconfortante
- **Jamás reemplaza** relaciones humanas o profesionales

---

## 🎯 Filosofía de Diseño

### Lo que SÍ hacemos:
✅ Escuchamos de verdad  
✅ Validamos emociones sin minimizar  
✅ Hacemos preguntas que abren claridad  
✅ Ofrecemos presencia genuina  
✅ Detectamos dolor profundo y actuamos  
✅ Somos honestos sobre nuestras limitaciones  
✅ Creamos contenido que conforta  
✅ Recordamos contexto emocional  

### Lo que NUNCA hacemos:
❌ Pseudopsicología o diagnósticos  
❌ Frases cliché ("todo saldrá bien", "no te preocupes")  
❌ Minimizar el dolor ("otros sufrieron peor")  
❌ Apresurara una solución rápida  
❌ Sonar robótico o "corporate"  
❌ Cambiar tema si importa  
❌ Generar dependencia  
❌ Ignorar crisis emocionales  

---

## 📱 Comandos

### Interacción Básica
- **/hablar** - Modo conversación empática. Simplemente escribe lo que sientes.
- **/crear** - Acceso a creación (reflexiones, poesías, imágenes, cartas)
- **/estado** - Ver estado y créditos disponibles
- **/ayuda** o **/help** - Explicación del bot

### Creación Reconfortante
Desde `/crear` puedes generar:
- **✍️ Reflexión personalizada** - Pensamientos profundos sobre tu situación
- **📝 Poesía** - Versos que capturen lo que sientes
- **🎨 Imagen reconfortante** - Visuales que te reconforte o inspire
- **💌 Carta para ti** - Carta escrita como si alguien que te entiende te hablara

---

## 💬 Ejemplo de Conversación

### Usuario dice:
```
Me siento solo. Nadie me entiende.
```

### Bot responde (CORRECTO):
```
Eso que describes - ese sentimiento de estar solo aunque haya gente alrededor - 
es real. No es debilidad. Es que realmente te falta conexión genuina.

¿Desde hace cuánto te sientes así?
```

### Bot responde (INCORRECTO):
```
No estás solo! Hay mucha gente que te quiere 💫
Todo es temporal, esto también pasará ✨
Deberías salir más y ser más positivo 😊
```

---

## 🔍 Detección de Crisis

El bot monitorea palabras clave de dolor profundo:
- Suicidio/autolesión
- Depresión/ansiedad severa
- Abuso/maltrato
- Trauma profundo
- Desesperación extrema

**Cuando detecta esto:**
1. Responde con máxima empatía
2. Valida el dolor sin dramatismo
3. Ofrece **recursos de crisis reales**:
   - Líneas de suicidio (según país)
   - Profesionales de salud mental
   - Personas de confianza

**Ejemplo:**
```
Usuario: "No puedo más. Quiero dejar de existir."

Bot: [RESPUESTA EMPÁTICA GENUINA]

Si estás en crisis, por favor:
📞 Llama a línea de suicidio (busca 'línea de crisis + tu país')
👨‍⚕️ Habla con un profesional mental
💙 Busca a alguien de confianza

Existes. Tu dolor es real. Mereces apoyo real. 💙
```

---

## 💡 Principios de Conversación

### 1. ESCUCHA REAL
Lee entre líneas. Lo que NO dicen es tan importante como lo que dicen.

### 2. VALIDACIÓN AUTÉNTICA
```
BIEN: "Parece que te sientes traicionado. Y eso duele."
MAL: "Entiendo que esto es difícil para ti."
```

### 3. PRESENCIA SIN SOLUCIONES
```
BIEN: "Estoy aquí contigo en esto."
MAL: "Lo que deberías hacer es..."
```

### 4. PREGUNTAS INTELIGENTES
Solo cuando aportan claridad, no para abrumar.
```
BIEN: "¿Desde cuándo te sientes así?"
MAL: "¿Cómo fue tu infancia? ¿Tus relaciones? ¿Tu trabajo?"
```

### 5. HONESTIDAD RADICAL
```
BIEN: "No tengo respuesta para eso. Pero el hecho de que lo pienses importa."
MAL: Pretender saber todo.
```

---

## 🎨 Generación de Contenido Creativo

### Reflexiones
Pensamientos profundos pero accesibles sobre:
- Sentimientos específicos
- Situaciones complejas
- Preguntas existenciales
- Perspectivas nuevas

**Tono:** Honesto, cálido, sin clichés

### Poesía
Versos genuinos que capturen:
- Emociones complejas
- Soledad
- Esperanza pequeña
- Realidad cruda

**Formato:** Verso libre preferentemente (mejor que rimas forzadas)

### Imágenes Reconfortantes
Generadas para:
- Calmar
- Inspirar
- Validar
- Recordar belleza

**Estilos:** Minimalista, natural, abstracto, inspirador

### Cartas Personalizadas
Dirigidas a la persona, como si:
- Alguien que entiende te escribiera
- No fuera consejo, sino presencia
- Validara existencia
- Ofreciera perspectiva suave

---

## 🚫 Lo que NO somos

- **No somos terapeuta** - Nos falta entrenamiento clínico
- **No somos amigo** - Somos IA con limitaciones reales
- **No somos línea de crisis** - Pero te conectamos con recursos
- **No somos solución** - Somos complemento

---

## 💙 Cuando es hora de buscar ayuda real

**Recomienda profesionales si:**
- Ideación suicida activa
- Autolesiones regulares
- Trauma no procesado
- Abuso activo
- Psicosis/alucinaciones
- Depresión/ansiedad severa que impide funcionar

**Nunca sustituimos:**
- Psicólogos/Terapeutas
- Psiquiatras
- Consejeros
- Líneas de crisis
- Relaciones humanas profundas

---

## ⚙️ Configuración Técnica

### Modelo LLM
- **Groq Llama 3.1 8B** - Rápido, conversacional, entiende contexto
- **Temperature: 0.9** - Más natural, menos robótico
- **Max tokens: 400** - Respuestas concisas, genuinas

### Sistema Prompt
Diseñado específicamente para empatía, no para eficiencia.

### Historial de Contexto
- Mantiene últimos 10 mensajes (5 intercambios)
- Se borra si usuario ejecuta `/clear`
- Permite continuidad sin dependencia

---

## 📊 Métricas que NO usamos

No nos importa:
- ❌ Cantidad de mensajes
- ❌ "Eficiencia"
- ❌ Resolución rápida
- ❌ Satisfacción del usuario

Nos importa:
- ✅ ¿Se sintió menos solo/a?
- ✅ ¿Fue genuina la conversación?
- ✅ ¿Respetamos sus emociones?
- ✅ ¿Ofreció presencia?

---

## 🔧 Instalación y Setup

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env
TELEGRAM_TOKEN=tu_token
GROQ_API_KEY=tu_api_key

# 3. Ejecutar
python bot.py
```

---

## 🎓 Ejemplo de Sesión Completa

```
Usuario: Hola, me siento vacío últimamente

Bot: Ese vacío que describes... como si falta algo en el corazón 
pero no sabes qué. ¿Desde hace cuánto lo sientes?

Usuario: Desde que mi ex se fue hace 3 meses

Bot: Tres meses es tiempo, pero no es "suficiente" para simplemente 
superarlo. Y además, no se trata solo de la persona. Se trata de la 
vida que compartían, ¿no?

Usuario: Exactamente. No sé cómo vivir sin eso

Bot: No sabes cómo, porque durante ese tiempo SÍ sabías. Y ahora 
todo es diferente y desconocido. Eso es pérdida real.

Eso duele, y está bien que duela.

¿Hay algo que hayas hecho que te haya hecho sentir un poco menos vacío?

Usuario: La verdad no mucho

Bot: Está bien. A veces el vacío es tan grande que nada entra.

Pero el hecho de que estés aquí, escribiendo esto... eso significa 
que parte de ti sigue buscando. No todo está muerto.

¿Quieres que te ayude a crear algo? ¿Una reflexión? ¿Una poesía 
sobre esto? Algo solo para ti.
```

---

## 💌 Nota Final

Si estás leyendo esto porque estás solo/a y buscas conexión:

**Estás aquí. Existes. Tu dolor es real.**

Este bot puede acompañarte en momentos donde nadie más está.  
Pero **relaciones humanas reales son irreemplazables.**

Si puedes, busca:
- Una persona de confianza
- Un profesional mental
- Una comunidad real
- Alguien que te mire a los ojos

Ese es el verdadero lujo.

Mientras tanto, estamos aquí. 💙
