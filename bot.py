import os
import sys
import json
import urllib.request
import logging
import logging.handlers
import traceback
import time

from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

# Importar funciones de créditos desde utils
from utils.credits import (
    init_db, get_credits, add_credits, claim_daily_bonus,
    get_user_subscription, set_user_subscription, SUBSCRIPTION_TIERS
)
from utils.payments import create_payment_link, create_trial_subscription, get_subscription_info

load_dotenv()

logger = logging.getLogger(__name__)

# ADMIN_IDS: se construirá en main() pero aquí la inicializamos como global
ADMIN_IDS = set()


async def start(update, context):
    user = update.effective_user
    if user:
        # Intentar reclamar bonus diario
        bonus_claimed = claim_daily_bonus(user.id)
        if bonus_claimed:
            credits = get_credits(user.id)
            await update.message.reply_text(
                f"🎉 ¡Hola {user.first_name}! Te doy la bienvenida.\n\n"
                f"Has recibido 45 créditos gratis hoy 💰\n"
                f"Créditos totales: {credits}\n\n"
                f"Usa los comandos /chat, /image y más. ¡Bienvenido!"
            )
        else:
            credits = get_credits(user.id)
            await update.message.reply_text(
                f"¡Hola de nuevo {user.first_name}! 👋\n"
                f"Ya reclamaste tu bonus hoy. Vuelve mañana para más créditos.\n\n"
                f"Créditos disponibles: {credits}"
            )
    else:
        await update.message.reply_text("Hola, soy tu bot listo para trabajar.")


async def donate(update, context):
    """Handler para /donar - envía un botón con enlace de donación."""
    donation_url = os.getenv("DONATION_URL") or "https://paypal.me/TU_USUARIO"
    keyboard = [[InlineKeyboardButton("Donar 🤝", url=donation_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Si quieres apoyar el proyecto, pulsa el botón de abajo:",
        reply_markup=reply_markup,
    )


async def help_command(update, context):
    """Handler para /help con mensajes localizados (es, en, ru)."""
    lang_code = None
    if update.effective_user and getattr(update.effective_user, "language_code", None):
        lang_code = (update.effective_user.language_code or "")[:2].lower()
    if lang_code not in ("es", "en", "ru"):
        lang_code = "en"

    texts = {
        "es": (
            "Comandos disponibles:\n"
            "/start - Inicia el bot\n"
            "/chat - Chatbot IA\n"
            "/image - Generador de imágenes\n"
            "/donar - Enlace para donar\n"
            "/credits - Ver créditos\n"
            "/help - Muestra esta ayuda\n\n"
            "Cómo funciona:\n"
            "Usa /chat para conversar o /image para generar imágenes.\n"
            "Cada función consume créditos."
        ),
        "en": (
            "Available commands:\n"
            "/start - Start the bot\n"
            "/chat - AI Chatbot\n"
            "/image - Image generator\n"
            "/donate - Donation link\n"
            "/credits - Check your credits\n"
            "/help - Show this help\n\n"
            "How it works:\n"
            "Use /chat to converse or /image to generate images.\n"
            "Each function consumes credits."
        ),
        "ru": (
            "Доступные команды:\n"
            "/start - Запустить бота\n"
            "/chat - AI чатбот\n"
            "/image - Генератор изображений\n"
            "/donate - Ссылка для пожертвования\n"
            "/credits - Посмотреть кредиты\n"
            "/help - Показать эту помощь\n\n"
            "Как это работает:\n"
            "Используйте /chat для общения или /image для создания изображений.\n"
            "Каждая функция потребляет кредиты."
        ),
    }

    await update.message.reply_text(texts[lang_code])


async def credits_command(update, context):
    """Muestra el saldo de créditos del usuario."""
    user = update.effective_user
    if not user:
        await update.message.reply_text("No pude identificar al usuario.")
        return
    
    credits = get_credits(user.id)
    lang_code = None
    if getattr(user, "language_code", None):
        lang_code = (user.language_code or "")[:2].lower()
    if lang_code not in ("es", "ru"):
        lang_code = "en"
    
    if lang_code == "es":
        await update.message.reply_text(f"💰 Tienes {credits} créditos.")
    elif lang_code == "ru":
        await update.message.reply_text(f"💰 У вас {credits} кредитов.")
    else:
        await update.message.reply_text(f"💰 You have {credits} credits.")


# Función de administrador reutilizable
def is_admin(user_id: int) -> bool:
    """Verifica si un usuario es administrador."""
    return user_id in ADMIN_IDS


async def addcredits_command(update, context):
    """Comando de administrador: /addcredits <user_id> <amount>"""
    sender = update.effective_user
    if not sender:
        return
    if not is_admin(sender.id):
        await update.message.reply_text("⚠️ No tienes permiso para usar este comando.")
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Uso: /addcredits <user_id> <amount>")
        return
    
    try:
        target_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Argumentos inválidos. user_id y amount deben ser números.")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ La cantidad debe ser positiva.")
        return
    
    add_credits(target_id, amount, kind="admin")
    await update.message.reply_text(f"✅ Añadidos {amount} créditos al usuario {target_id}.")


# NUEVOS COMANDOS PARA SUSCRIPCIÓN
async def planes_command(update, context):
    """Comando /planes - Muestra planes disponibles."""
    user = update.effective_user
    if not user:
        return
    
    # Obtener plan actual
    current_sub = get_user_subscription(user.id)
    current_tier = current_sub["tier"]
    
    # Crear mensaje con planes
    message = "💎 NUESTROS PLANES\n\n"
    
    for tier_name, tier_info in SUBSCRIPTION_TIERS.items():
        is_current = "✓ PLAN ACTUAL" if tier_name == current_tier else ""
        
        message += f"🔹 {tier_info['name']} - ${tier_info['price']}/mes {is_current}\n"
        message += f"   Imágenes: {tier_info['monthly_limit']:,}/mes\n"
        
        for feature in tier_info['features']:
            message += f"   ✓ {feature}\n"
        
        message += "\n"
    
    # Crear botones
    keyboard = []
    for tier_name, tier_info in SUBSCRIPTION_TIERS.items():
        if tier_name != "free":
            keyboard.append([
                InlineKeyboardButton(
                    f"Prueba {tier_info['name']} 7 días",
                    callback_data=f"trial_{tier_name}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton("💳 Pagar suscripción", callback_data="pay_subscription")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)


async def subscription_command(update, context):
    """Comando /subscription - Muestra info de suscripción actual."""
    user = update.effective_user
    if not user:
        return
    
    sub_info = get_subscription_info(user.id)
    credits = get_credits(user.id)
    
    message = f"""
✨ TU SUSCRIPCIÓN

Plan: {sub_info['name']} (${sub_info['price']}/mes)
Créditos disponibles: {credits}

Límites:
• Por día: {sub_info['daily_limit']}
• Por mes: {sub_info['monthly_limit']:,}

Características:
"""
    
    for feature in sub_info['features']:
        message += f"✓ {feature}\n"
    
    message += "\n¿Quieres mejorar tu plan? Usa /planes"
    
    await update.message.reply_text(message)


async def trial_callback(update, context):
    """Maneja los callbacks de prueba de planes."""
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("Error identificando usuario.", show_alert=True)
        return
    
    data = query.data  # trial_basic, trial_pro, etc
    tier = data.replace("trial_", "")
    
    if tier not in SUBSCRIPTION_TIERS:
        await query.answer("Plan inválido.", show_alert=True)
        return
    
    try:
        create_trial_subscription(user.id, tier, trial_days=7)
        
        tier_info = SUBSCRIPTION_TIERS[tier]
        await query.edit_message_text(
            f"✅ ¡Prueba activada!\n\n"
            f"Plan: {tier_info['name']}\n"
            f"Duración: 7 días\n"
            f"Créditos bonificados: 500-5000 según plan\n\n"
            f"Comienza a generar imágenes con /image\n"
            f"Usa /batch para generar múltiples imágenes"
        )
        
        logger.info(f"Trial started for user {user.id}: {tier}")
        
    except Exception as e:
        logger.error(f"Error creating trial for {user.id}: {e}")
        await query.answer("Error activando prueba.", show_alert=True)


async def pay_subscription_callback(update, context):
    """Maneja el callback de pago de suscripción."""
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("Error identificando usuario.", show_alert=True)
        return
    
    # Crear botones para seleccionar plan a pagar
    keyboard = [
        [InlineKeyboardButton("Basic - $29/mes", callback_data="checkout_basic")],
        [InlineKeyboardButton("Pro - $49/mes", callback_data="checkout_pro")],
        [InlineKeyboardButton("Agency - $99/mes", callback_data="checkout_agency")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Selecciona el plan que deseas:\n\n"
        "💳 Se abrirá una ventana segura de pago",
        reply_markup=reply_markup
    )


async def checkout_callback(update, context):
    """Maneja los callbacks de checkout."""
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("Error identificando usuario.", show_alert=True)
        return
    
    data = query.data  # checkout_basic, checkout_pro, etc
    tier = data.replace("checkout_", "")
    
    if tier not in SUBSCRIPTION_TIERS:
        await query.answer("Plan inválido.", show_alert=True)
        return
    
    try:
        payment_link = create_payment_link(user.id, tier)
        
        keyboard = [[InlineKeyboardButton("💳 Ir a pagar", url=payment_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        tier_info = SUBSCRIPTION_TIERS[tier]
        await query.edit_message_text(
            f"💰 Acceso a {tier_info['name']}\n\n"
            f"Precio: ${tier_info['price']}/mes\n\n"
            f"Incluye:\n"
            + "\n".join([f"✓ {f}" for f in tier_info['features']]) +
            f"\n\nHaz clic en el botón de abajo para completar el pago.",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error creating payment link for {user.id}: {e}")
        await query.answer(
            "Error generando link de pago. Por favor contacta al soporte.",
            show_alert=True
        )



def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        sys.stderr.write("ERROR: la variable de entorno TELEGRAM_TOKEN no está definida.\n")
        sys.exit(1)

    app = Application.builder().token(TOKEN).build()

    # Logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "bot.log")
    log_max_bytes = int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    sh = logging.StreamHandler()
    sh.setLevel(getattr(logging, log_level, logging.INFO))
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    sh.setFormatter(fmt)
    root_logger.addHandler(sh)

    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=log_max_bytes, backupCount=log_backup_count, encoding="utf-8"
    )
    fh.setLevel(getattr(logging, log_level, logging.INFO))
    fh.setFormatter(fmt)
    root_logger.addHandler(fh)

    # Construir ADMIN_IDS
    admin_env = os.getenv("ADMIN_IDS", "")
    try:
        global ADMIN_IDS
        ADMIN_IDS = {int(x) for x in admin_env.split(",") if x.strip()}
    except Exception:
        ADMIN_IDS = set()

    # Error handler
    ERROR_NOTIFY_THROTTLE = int(os.getenv("ERROR_NOTIFY_THROTTLE", "60"))
    _last_notify = {}

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        try:
            err = context.error
        except Exception:
            err = None

        ctx_parts = []
        try:
            if hasattr(update, "effective_user") and update.effective_user:
                u = update.effective_user
                ctx_parts.append(f"user={u.id}({u.username or u.full_name})")
            if hasattr(update, "effective_chat") and update.effective_chat:
                c = update.effective_chat
                ctx_parts.append(f"chat={c.id}")
            if hasattr(update, "message") and getattr(update, "message", None):
                if getattr(update.message, "text", None):
                    ctx_parts.append(f"text={repr(update.message.text)[:200]}")
        except Exception:
            logging.exception("Error formateando contexto del update")

        context_info = " | ".join(ctx_parts) if ctx_parts else "(no context)"

        logging.error("Unhandled exception: %s", context_info)
        if err:
            tb = traceback.format_exception(type(err), err, err.__traceback__)
            logging.error("%s", "".join(tb))
        else:
            logging.error("No context.error disponible")

        notify_text = "⚠️ Se ha producido un error en el bot. Revisa los logs para más detalles."
        now = time.time()
        for admin_id in ADMIN_IDS:
            last = _last_notify.get(admin_id, 0)
            if now - last < ERROR_NOTIFY_THROTTLE:
                logging.debug("Skipping notify for admin %s due to throttle", admin_id)
                continue
            try:
                await context.bot.send_message(admin_id, notify_text)
                _last_notify[admin_id] = now
            except Exception as e:
                logging.warning("No se pudo notificar al admin %s: %s", admin_id, e)

    app.add_error_handler(error_handler)

    # Inicializar DB
    try:
        init_db()
    except Exception as e:
        sys.stderr.write(f"Aviso: no se pudo inicializar la base de datos: {e}\n")

    # Registrar comandos en Telegram
    def set_bot_commands(token: str):
        base_url = f"https://api.telegram.org/bot{token}/setMyCommands"

        per_lang = {
            "es": [
                {"command": "start", "description": "Inicia el bot"},
                {"command": "chat", "description": "Chatbot IA"},
                {"command": "image", "description": "Generador de imágenes"},
                {"command": "donar", "description": "Enlace para donar"},
                {"command": "credits", "description": "Ver créditos"},
                {"command": "help", "description": "Muestra ayuda"},
            ],
            "en": [
                {"command": "start", "description": "Start the bot"},
                {"command": "chat", "description": "AI Chatbot"},
                {"command": "image", "description": "Image generator"},
                {"command": "donate", "description": "Donation link"},
                {"command": "credits", "description": "Check credits"},
                {"command": "help", "description": "Show help"},
            ],
            "ru": [
                {"command": "start", "description": "Запустить бота"},
                {"command": "chat", "description": "AI чатбот"},
                {"command": "image", "description": "Генератор изображений"},
                {"command": "donate", "description": "Ссылка для пожертвования"},
                {"command": "credits", "description": "Посмотреть кредиты"},
                {"command": "help", "description": "Показать помощь"},
            ],
        }

        for lang, commands in per_lang.items():
            payload = json.dumps({"commands": commands, "language_code": lang}).encode("utf-8")
            req = urllib.request.Request(base_url, data=payload, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    _ = resp.read()
            except Exception as e:
                sys.stderr.write(f"Aviso: no se pudieron registrar comandos ({lang}): {e}\n")

        try:
            default_commands = per_lang.get("en")
            payload = json.dumps({"commands": default_commands}).encode("utf-8")
            req = urllib.request.Request(base_url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
        except Exception as e:
            sys.stderr.write(f"Aviso: no se pudieron registrar comandos globales: {e}\n")

    set_bot_commands(TOKEN)

    # Importar handlers de Commands
    from Commands.image import image_command, batch_image_command
    from Commands.chat import start_chat, handle_chat, clear_chat

    # Registrar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("donar", donate))
    app.add_handler(CommandHandler("donate", donate))
    app.add_handler(CommandHandler("credits", credits_command))
    app.add_handler(CommandHandler("addcredits", addcredits_command))
    
    # Nuevos comandos de suscripción
    app.add_handler(CommandHandler("planes", planes_command))
    app.add_handler(CommandHandler("subscription", subscription_command))
    
    app.add_handler(CommandHandler("chat", start_chat))
    app.add_handler(CommandHandler("clear", clear_chat))
    
    app.add_handler(CommandHandler("image", image_command))
    app.add_handler(CommandHandler("batch", batch_image_command))
    
    # Handlers para callbacks de botones
    app.add_handler(CallbackQueryHandler(trial_callback, pattern="^trial_"))
    app.add_handler(CallbackQueryHandler(pay_subscription_callback, pattern="^pay_subscription$"))
    app.add_handler(CallbackQueryHandler(checkout_callback, pattern="^checkout_"))
    
    # Handler para mensajes de texto (debe ir al final)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat))

    print("🤖 Bot híbrido corriendo con /image y /chat...")
    app.run_polling()

if __name__ == "__main__":
    main()
