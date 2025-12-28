import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def create_reflection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback para crear una reflexión personalizada.
    Guarda el estado y espera el tema del usuario.
    """
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("No pude identificarte.", show_alert=True)
        return
    
    # Guardar tipo de creación en contexto del usuario
    context.user_data['creation_type'] = 'reflection'
    context.user_data['waiting_for_input'] = True
    
    await query.answer()  # Responder al callback
    
    message = (
        "✍️ **Reflexión Personalizada**\n\n"
        "Dime sobre qué tema quieres reflexionar.\n\n"
        "Puede ser:\n"
        "• Un sentimiento (tristeza, confusión, miedo)\n"
        "• Una situación (cambio de vida, pérdida, decisión)\n"
        "• Un miedo o esperanza\n"
        "• Cualquier cosa que te ronde la mente\n\n"
        "Escribe el tema y crearé una reflexión profunda para ti. 🌙"
    )
    
    await query.edit_message_text(message)
    logger.info("Usuario %s solicitó reflexión personalizada", user.id)


async def create_poetry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback para crear una poesía personalizada.
    Guarda el estado y espera el tema del usuario.
    """
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("No pude identificarte.", show_alert=True)
        return
    
    # Guardar tipo de creación
    context.user_data['creation_type'] = 'poetry'
    context.user_data['waiting_for_input'] = True
    
    await query.answer()
    
    message = (
        "📝 **Poesía Personalizada**\n\n"
        "¿Sobre qué quieres una poesía?\n\n"
        "Puede ser sobre:\n"
        "• Tu dolor, tu fuerza, tu soledad\n"
        "• Tu esperanza, tu miedo, tu pasado\n"
        "• Una persona, un lugar, un recuerdo\n"
        "• Algo que sientes en tu corazón\n\n"
        "Cuéntame qué quieres que salga en versos. 📖"
    )
    
    await query.edit_message_text(message)
    logger.info("Usuario %s solicitó poesía personalizada", user.id)


async def create_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback para generar una imagen reconfortante.
    Guarda el estado y espera la descripción del usuario.
    """
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("No pude identificarte.", show_alert=True)
        return
    
    # Guardar tipo de creación
    context.user_data['creation_type'] = 'image'
    context.user_data['waiting_for_input'] = True
    
    await query.answer()
    
    message = (
        "🎨 **Imagen Reconfortante**\n\n"
        "¿Qué necesitas ver hoy?\n\n"
        "Describe:\n"
        "• Cómo te sientes y qué te reconfortaría\n"
        "• Un lugar, paisaje o escena que te inspire\n"
        "• Un símbolo o sensación visual\n"
        "• Algo que te haga sentir menos solo/a\n\n"
        "Ejemplo: \"Un atardecer tranquilo en la montaña\"\n\n"
        "Escribe tu descripción y generaré la imagen. ✨"
    )
    
    await query.edit_message_text(message)
    logger.info("Usuario %s solicitó imagen reconfortante", user.id)


async def create_letter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback para crear una carta personalizada.
    Guarda el estado y espera lo que el usuario necesita escuchar.
    """
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("No pude identificarte.", show_alert=True)
        return
    
    # Guardar tipo de creación
    context.user_data['creation_type'] = 'letter'
    context.user_data['waiting_for_input'] = True
    
    await query.answer()
    
    message = (
        "💌 **Carta Personalizada**\n\n"
        "¿Qué debería decirte una carta en este momento?\n\n"
        "Puedes compartir:\n"
        "• Cómo te sientes ahora mismo\n"
        "• Qué necesitas escuchar\n"
        "• Dudas sobre ti mismo/a\n"
        "• Lo que te pesa en el corazón\n\n"
        "Escribiré una carta como si alguien que te entiende te hablara. 💙"
    )
    
    await query.edit_message_text(message)
    logger.info("Usuario %s solicitó carta personalizada", user.id)