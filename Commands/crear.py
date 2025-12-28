import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

from utils.credits import get_credits, add_credits

logger = logging.getLogger(__name__)

async def crear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el menú de creación de contenido reconfortante.
    """
    user = update.effective_user
    if not user:
        return
    
    # Crear teclado con opciones
    keyboard = [
        [InlineKeyboardButton(
            "✍️ Reflexión personalizada", 
            callback_data="create_reflection"
        )],
        [InlineKeyboardButton(
            "📝 Poesía", 
            callback_data="create_poetry"
        )],
        [InlineKeyboardButton(
            "🎨 Imagen reconfortante", 
            callback_data="create_image"
        )],
        [InlineKeyboardButton(
            "💌 Carta para ti", 
            callback_data="create_letter"
        )],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Obtener créditos
    credits = get_credits(user.id)
    
    message = (
        "💙 **¿Qué necesitas crear hoy?**\n\n"
        "Puedo ayudarte a:\n"
        "• Expresar sentimientos en reflexiones\n"
        "• Crear poesías sobre lo que sientes\n"
        "• Generar imágenes que te inspiren\n"
        "• Escribir cartas reconfortantes\n\n"
        f"💎 Tus créditos: {credits}\n"
        "💰 Costo: 10 créditos (texto) / 15 créditos (imagen)\n\n"
        "Elige una opción:"
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)
    logger.info("Usuario %s abrio menu de creacion", user.id)
