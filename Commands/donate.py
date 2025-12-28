import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

logger = logging.getLogger(__name__)

async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el enlace de donación al usuario.
    """
    donation_url = os.getenv("DONATION_URL", "https://ko-fi.com/sammy26")
    
    keyboard = [[InlineKeyboardButton("💝 Donar", url=donation_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "💙 **Gracias por considerar apoyar este proyecto**\n\n"
        "Este bot existe para acompañar a personas que se sienten solas.\n\n"
        "Si te ha ayudado de alguna forma, tu apoyo ayuda a mantenerlo vivo "
        "para otros que lo necesitan.\n\n"
        "No es obligatorio. Lo importante es que estés bien. 💙"
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)
    logger.info("Usuario %s vio enlace de donación", update.effective_user.id)