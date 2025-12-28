
import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.credits import get_credits

logger = logging.getLogger(__name__)

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el estado actual del usuario (créditos, estadísticas).
    """
    user = update.effective_user
    if not user:
        return
    
    user_credits = get_credits(user.id)
    
    status = (
        "📊 **Tu estado actual**\n\n"
        f"💎 Créditos disponibles: {user_credits}\n\n"
        "**Usa créditos para:**\n"
        "• Reflexiones personalizadas (10 créditos)\n"
        "• Poesías (10 créditos)\n"
        "• Cartas reconfortantes (10 créditos)\n"
        "• Imágenes reconfortantes (15 créditos)\n\n"
        "🎁 **Obtén más créditos:**\n"
        "• +45 créditos diarios (automático con /start)\n"
        "• Conversar es GRATIS\n\n"
        "💙 No hay presión. Úsalos cuando realmente los necesites.\n"
        "Lo importante es que estés bien, no que gastes."
    )
    
    await update.message.reply_text(status)
    logger.info("Usuario %s consultó su estado", user.id)