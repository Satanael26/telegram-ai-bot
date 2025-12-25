import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from groq import Groq

# Importar desde utils (import relativo)
from utils.credits import consume_credits, get_credits, add_credits

logger = logging.getLogger(__name__)

# Cliente de Groq (se inicializa una vez)
groq_client = None


def init_groq():
    """Inicializa el cliente de Groq si aún no existe."""
    global groq_client
    if groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY no está definida en el .env")
            raise ValueError("GROQ_API_KEY requerida")
        groq_client = Groq(api_key=api_key)
        logger.info("Cliente Groq inicializado")


async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /chat - Inicia el modo conversación."""
    user = update.effective_user
    credits = get_credits(user.id)
    
    await update.message.reply_text(
        f"🧠 Chatbot IA activado.\n\n"
        f"Escribe cualquier cosa y te responderé. "
        f"Cada mensaje cuesta 1 crédito.\n\n"
        f"💰 Créditos disponibles: {credits}"
    )


async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto y genera respuestas con Groq."""
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    prompt = update.message.text.strip()
    
    # Validar longitud del prompt
    if len(prompt) > 2000:
        await update.message.reply_text("⚠️ Mensaje demasiado largo. Máximo 2000 caracteres.")
        return
    
    if len(prompt) < 2:
        await update.message.reply_text("🤔 Escribe algo más específico.")
        return
    
    # Verificar y consumir créditos
    if not consume_credits(user_id, 1):
        remaining = get_credits(user_id)
        await update.message.reply_text(
            f"⚠️ Sin créditos suficientes.\n"
            f"Tienes {remaining} créditos.\n"
            f"Usa /credits para ver tu saldo o /donar para apoyar el proyecto."
        )
        return
    
    # Inicializar Groq si es necesario
    try:
        init_groq()
    except ValueError as e:
        logger.error(f"Error inicializando Groq: {e}")
        await update.message.reply_text("⚠️ Error de configuración del bot. Contacta al administrador.")
        return
    
    # Mantener historial de conversación (opcional)
    if "chat_history" not in context.user_data:
        context.user_data["chat_history"] = []
    
    # Añadir mensaje del usuario al historial
    context.user_data["chat_history"].append({
        "role": "user",
        "content": prompt
    })
    
    # Limitar historial a últimos 10 mensajes (5 intercambios)
    if len(context.user_data["chat_history"]) > 10:
        context.user_data["chat_history"] = context.user_data["chat_history"][-10:]
    
    try:
        # Llamar a Groq API
        response = groq_client.chat.completions.create(
            messages=context.user_data["chat_history"],
            model="llama-3.1-8b-instant",
            max_tokens=300,
            temperature=0.7,
            timeout=10
        )
        
        bot_reply = response.choices[0].message.content.strip()
        
        # Añadir respuesta del bot al historial
        context.user_data["chat_history"].append({
            "role": "assistant",
            "content": bot_reply
        })
        
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        logger.error(f"Error en Groq API: {e}")
        
        # Devolver crédito si falló
        add_credits(user_id, 1, kind="refund")
        
        await update.message.reply_text(
            "⚠️ Error al generar respuesta. Tu crédito ha sido devuelto.\n"
            "Intenta de nuevo en unos segundos."
        )


async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /clear - Borra el historial de conversación."""
    if "chat_history" in context.user_data:
        context.user_data["chat_history"] = []
    
    await update.message.reply_text("🧹 Historial de conversación borrado. Empecemos de nuevo.")