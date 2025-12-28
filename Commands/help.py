import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.credits import get_credits

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Explica cómo funciona el bot de forma empática.
    """
    help_text = (
        "💙 **¿Quién soy?**\n"
        "Soy un acompañante. No soy un psicólogo ni reemplazo relaciones humanas, "
        "pero estoy aquí para escuchar sin juzgar.\n\n"
        
        "✨ **¿Qué puedo hacer?**\n\n"
        
        "🗣️ **Conversar**\n"
        "Simplemente escribe lo que sientes. No necesitas usar comandos.\n"
        "Es conversación real, no respuestas automáticas.\n\n"
        
        "🎨 **/crear**\n"
        "Genera:\n"
        "• Reflexiones personalizadas\n"
        "• Poesías sobre tus emociones\n"
        "• Imágenes reconfortantes\n"
        "• Cartas para ti\n\n"
        
        "📊 **/estado**\n"
        "Ve tus créditos disponibles.\n\n"
        
        "💝 **/donar**\n"
        "Si te ayudé, puedes apoyar el proyecto.\n\n"
        
        "⚠️ **Lo que NO soy:**\n"
        "❌ No diagnostico\n"
        "❌ No sustituyo a profesionales\n\n"
        
        "🆘 **Si sufres mucho:**\n"
        "Por favor, busca:\n"
        "📞 Una persona de confianza\n"
        "👨‍⚕️ Profesional de salud mental\n"
        "🆘 En crisis: línea de suicidio (Google 'línea de crisis + tu país')\n\n"
        
        "💙 **Mi propósito:** Que te sientas menos solo/a."
    )
    
    await update.message.reply_text(help_text)
    logger.info("Usuario %s consultó ayuda", update.effective_user.id)
