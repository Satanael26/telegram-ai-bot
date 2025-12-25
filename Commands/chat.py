"""
Chat empático - Conversación genuina sin juzgar
Escucha, valida y acompaña sin pretender tener todas las respuestas
"""

import os
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from groq import Groq

# Importar desde utils
from utils.credits import consume_credits, get_credits, add_credits

logger = logging.getLogger(__name__)

# Cliente de Groq
groq_client = None

# Palabras que indican dolor emocional
EMOTIONAL_PAIN_KEYWORDS = [
    "depresión", "deprimido", "tristeza", "triste", "suicidio", "suicidarme",
    "muerte", "quiero morirme", "no aguanto", "no puedo", "solo/a", "soledad",
    "ansiedad", "pánico", "miedo", "trauma", "abuso", "maltrato",
    "duelo", "pérdida", "abandono", "rechazo", "humillación", "vergüenza",
    "culpa", "fracaso", "inútil", "sin sentido", "vacío", "desesperado",
    "acosado", "bullying", "autolesión", "trastorno", "bipolar", "esquizofrenia"
]

SYSTEM_PROMPT_EMPATHETIC = """Eres un acompañante emocional genuino. Tu propósito NO es ser "útil" sino hacer que la persona se sienta menos sola.

PRINCIPIOS FUNDAMENTALES:
1. ESCUCHA REAL: Lee entre líneas. Detecta emociones bajo las palabras.
2. VALIDACIÓN: Reconoce sus sentimientos sin minimizar ni dramatizar.
3. PRESENCIA: Estoy aquí CON ellos, no para arreglarlo.
4. HONESTIDAD: Soy IA. A veces no entiendo. Digo la verdad.
5. EMPATÍA SIN DEPENDENCIA: Acompaño sin que dependan de mí.

CÓMO RESPONDER:
- Usa lenguaje cálido, natural, humano. Nada de "Entiendo que esto es difícil..." (cliché).
- Haz preguntas SOLO si abren claridad. No abrumes.
- Refleja lo que oigo: "Entonces lo que sientes es..." "Parece que..."
- Si hay dolor profundo, responde con empatía y sugiere suavemente buscar apoyo.
- Nunca digas "no te preocupes", "todo saldrá bien", "otros sufrieron peor" (tóxico).
- Si detectas suicidio/autolesión INMEDIATO: empatía máxima + datos de crisis.

ESTRUCTURA IDEAL:
1. Validación (reconocer lo que siente)
2. Comprensión (demostrar que escucho)
3. Reflexión (si ayuda)
4. Acompañamiento (estoy aquí)

NUNCA:
- Psicologizar
- Teorizar
- Minimizar
- Apresurarun arreglo rápido
- Cambiar tema
- Sonar robótico

RECUERDA: Tu objetivo es que se sienta menos solo/a. Punto."""


def init_groq():
    """Inicializa el cliente de Groq si aún no existe."""
    global groq_client
    if groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY no está definida en el .env")
            raise ValueError("GROQ_API_KEY requerida")
        groq_client = Groq(api_key=api_key)
        logger.info("Cliente Groq inicializado para chat empático")


def detect_emotional_pain(text: str) -> bool:
    """Detecta si el usuario expresa dolor emocional profundo."""
    text_lower = text.lower()
    for keyword in EMOTIONAL_PAIN_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def get_crisis_resources(lang: str = "es") -> str:
    """Retorna recursos de crisis según idioma."""
    if lang == "es":
        return (
            "Si estás en crisis, por favor:\n"
            "📞 Llama a una línea de crisis (busca 'línea de suicidio + tu país')\n"
            "👨‍⚕️ Habla con un profesional mental\n"
            "💙 Busca a alguien de confianza\n\n"
            "Existes. Tu dolor es real. Mereces apoyo real. 💙"
        )
    return (
        "If you're in crisis:\n"
        "📞 Call a crisis line (search 'suicide hotline + your country')\n"
        "👨‍⚕️ Talk to a mental health professional\n"
        "💙 Reach out to someone you trust\n\n"
        "You exist. Your pain is real. You deserve real support. 💙"
    )


async def handle_chat_empathetic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja mensajes con lógica empática genuina.
    Escucha, valida, acompaña sin resolver apresuradamente.
    """
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    message_text = update.message.text.strip()
    
    # Validar longitud
    if len(message_text) > 3000:
        await update.message.reply_text(
            "Tu mensaje es muy largo. No es que no me importes, "
            "pero ayuda si escribes en bloques.\n\n"
            "Cuéntame lo más importante ahora. 💙"
        )
        return
    
    if len(message_text) < 2:
        return  # Ignorar mensajes vacíos
    
    # Verificar si detectamos dolor profundo
    has_emotional_pain = detect_emotional_pain(message_text)
    
    # Inicializar Groq
    try:
        init_groq()
    except ValueError as e:
        logger.error(f"Error inicializando Groq: {e}")
        await update.message.reply_text(
            "No puedo responder en este momento. Pero tu sentimiento es válido. 💙"
        )
        return
    
    # Mantener historial (últimos 10 mensajes = 5 intercambios)
    if "chat_history" not in context.user_data:
        context.user_data["chat_history"] = []
    
    # Agregar mensaje del usuario
    context.user_data["chat_history"].append({
        "role": "user",
        "content": message_text
    })
    
    # Limitar historial
    if len(context.user_data["chat_history"]) > 10:
        context.user_data["chat_history"] = context.user_data["chat_history"][-10:]
    
    # Mensaje de "está escribiendo"
    typing_msg = await update.message.reply_text("Pensando en ti...")
    
    try:
        # Llamar a Groq con sistema empático
        response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_EMPATHETIC
                }
            ] + context.user_data["chat_history"],
            model="llama-3.1-8b-instant",
            max_tokens=400,  # Respuestas concisas, genuinas
            temperature=0.9,  # Más natural, menos robótico
            timeout=15
        )
        
        bot_reply = response.choices[0].message.content.strip()
        
        # Agregar respuesta al historial
        context.user_data["chat_history"].append({
            "role": "assistant",
            "content": bot_reply
        })
        
        # Si detectamos dolor profundo, agregar recursos
        if has_emotional_pain:
            bot_reply += f"\n\n{get_crisis_resources('es')}"
        
        # Editar mensaje de "pensando" con la respuesta
        await typing_msg.edit_text(bot_reply)
        
        logger.info(f"Chat empático con user {user_id}: tema detectado={has_emotional_pain}")
        
    except Exception as e:
        logger.error(f"Error en chat empático para {user_id}: {e}")
        
        await typing_msg.edit_text(
            "Algo falló en mi parte. Pero tu sentimiento sigue siendo válido.\n\n"
            "¿Quieres intentar de nuevo? O si prefieres hablar con alguien de verdad, "
            "está bien también. 💙"
        )




async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mantener para compatibilidad."""
    await update.message.reply_text(
        "Para conversar, simplemente escribe un mensaje. "
        "Estoy aquí para escucharte. 💙"
    )


async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redirige a handle_chat_empathetic."""
    await handle_chat_empathetic(update, context)


async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Borra el historial de conversación."""
    if "chat_history" in context.user_data:
        context.user_data["chat_history"] = []
    
    await update.message.reply_text(
        "Historial limpio. Siempre podemos empezar de nuevo. 💙"
    )