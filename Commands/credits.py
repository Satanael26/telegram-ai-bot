import logging
from telegram import Update
from telegram.ext import ContextTypes
import os

from utils.credits import get_credits, add_credits

logger = logging.getLogger(__name__)


async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /credits.
    Muestra los créditos disponibles del usuario.
    """
    user = update.effective_user
    if not user:
        await update.message.reply_text("No pude identificarte.")
        return
    
    user_credits = get_credits(user.id)
    
    credits_text = (
        f"💰 **Tus Créditos**\n\n"
        f"Tienes: **{user_credits}** créditos disponibles\n\n"
        f"📌 **Cómo funcionan los créditos:**\n"
        f"• Cada mensaje en /hablar cuesta 1 crédito\n"
        f"• Crear contenido cuesta entre 5-20 créditos\n"
        f"• Recibes 45 créditos gratis cada día\n\n"
        f"💝 **Apoya el proyecto:**\n"
        f"Usa /donar para hacer una donación y conseguir más créditos\n"
    )
    
    await update.message.reply_text(credits_text)


async def addcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /addcredits.
    Solo administradores pueden usar este comando para añadir créditos a usuarios.
    """
    user = update.effective_user
    if not user:
        await update.message.reply_text("No pude identificarte.")
        return
    
    # Cargar IDs de administradores
    admin_env = os.getenv("ADMIN_IDS", "")
    try:
        admin_ids = {int(x) for x in admin_env.split(",") if x.strip()}
    except Exception:
        admin_ids = set()
    
    # Verificar si el usuario es administrador
    if user.id not in admin_ids:
        await update.message.reply_text(
            "❌ Solo administradores pueden usar este comando."
        )
        return
    
    # Parsear argumentos: /addcredits <user_id> <amount> [reason]
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Uso: /addcredits <user_id> <amount> [reason]\n"
            "Ejemplo: /addcredits 123456789 100 Donación manual"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        reason = " ".join(context.args[2:]) if len(context.args) > 2 else "Admin manual"
        
        if amount <= 0:
            await update.message.reply_text("❌ La cantidad debe ser mayor a 0.")
            return
        
        # Añadir créditos
        add_credits(target_user_id, amount, kind=reason)
        
        new_balance = get_credits(target_user_id)
        
        await update.message.reply_text(
            f"✅ Se añadieron {amount} créditos a usuario {target_user_id}\n"
            f"Motivo: {reason}\n"
            f"Nuevo balance: {new_balance} créditos"
        )
        
        # Notificar al usuario
        try:
            await context.bot.send_message(
                target_user_id,
                f"🎁 ¡Recibiste {amount} créditos gratis!\n"
                f"Motivo: {reason}\n"
                f"Nuevo balance: {new_balance} créditos"
            )
        except Exception as e:
            logger.warning("No se pudo notificar al usuario %s: %s", target_user_id, e)
    
    except ValueError:
        await update.message.reply_text(
            "❌ Argumentos inválidos. Usa: /addcredits <user_id> <amount> [reason]\n"
            "user_id y amount deben ser números."
        )
