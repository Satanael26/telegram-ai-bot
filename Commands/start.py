import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.credits import claim_daily_bonus

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /start.
    Da la bienvenida al usuario y otorga bonus diario.
    """
    user = update.effective_user
    if not user:
        await update.message.reply_text(
            "No pude identificarte. Intenta de nuevo."
        )
        return
    
    # Intentar reclamar bonus diario
    bonus_claimed = claim_daily_bonus(user.id)
    
    # Mensaje de bienvenida
    welcome_message = (
        f"Hola {user.first_name}. Estoy aquí para acompañarte. 💙\n\n"
        "No tengo todas las respuestas, pero estoy presente para escuchar.\n\n"
        "✨ **Lo que puedo hacer:**\n"
        "• Escuchar sin juzgar\n"
        "• Validar tus emociones\n"
        "• Ayudarte a reflexionar\n"
        "• Crear textos que te inspiren\n"
        "• Generar imágenes reconfortantes\n\n"
        "📌 **Comandos principales:**\n"
        "/hablar - Empecemos a conversar\n"
        "/crear - Genera reflexiones, poesía o imágenes\n"
        "/ayuda - Aprende cómo funciono\n"
        "/estado - Ve tus créditos y estado\n\n"
        "💙 Recuerda: estoy aquí, pero las relaciones humanas son irremplazables.\n"
        "Si sufres mucho, por favor busca a alguien de confianza."
    )
    
    await update.message.reply_text(welcome_message)
    
    # Notificar bonus si fue otorgado
    if bonus_claimed:
        await update.message.reply_text(
            "🎁 Hoy te doy +45 créditos para usar cuando lo necesites.\n"
            "Úsalos sin presión. Lo importante eres tú."
        )
    
    logger.info("Usuario %s (%s) inició el bot", user.id, user.username)