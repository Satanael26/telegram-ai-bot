import os
import sys
import json
import urllib.request
import logging
import logging.handlers
import traceback
import time
import re

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

# Palabras clave que indican dolor emocional
EMOTIONAL_PAIN_KEYWORDS = [
    "depresión", "deprimido", "tristeza", "triste", "suicidio", "suicidarme",
    "muerte", "quiero morirme", "no aguanto", "no puedo", "solo/a", "soledad",
    "ansiedad", "pánico", "miedo", "fobia", "trauma", "abuso", "maltrato",
    "duelo", "pérdida", "abandono", "rechazo", "humillación", "vergüenza",
    "culpa", "fracaso", "inútil", "sin sentido", "vacío", "desesperado/a",
    "acosado", "bullyng", "autolesión", "automutilación", "trastorno",
]


async def start(update, context):
    user = update.effective_user
    if user:
        # Intentar reclamar bonus diario
        bonus_claimed = claim_daily_bonus(user.id)
        
        welcome_message = (
            f"Hola {user.first_name}. Estoy aquí para acompañarte.\n\n"
            f"No tengo todas las respuestas, pero estoy presente para escuchar.\n\n"
            f"✨ **Lo que puedo hacer:**\n"
            f"• Escuchar sin juzgar\n"
            f"• Validar tus emociones\n"
            f"• Ayudarte a reflexionar\n"
            f"• Crear textos que te inspiren\n"
            f"• Generar imágenes reconfortantes\n\n"
            f"📌 **Comandos:**\n"
            f"/hablar - Empecemos a conversar\n"
            f"/crear - Genera textos o imágenes\n"
            f"/ayuda - Sé cómo funciono\n\n"
            f"Recuerda: estoy aquí, pero las relaciones humanas son irremplazables.\n"
            f"Si sufres mucho, por favor busca a alguien de confianza. 💙"
        )
        
        await update.message.reply_text(welcome_message)
        
        if bonus_claimed:
            await update.message.reply_text(
                f"Hoy te doy +45 créditos para usar los servicios. "
                f"Úsalos cuando lo necesites, sin presión."
            )
        
        logger.info(f"Usuario {user.id} ha iniciado el bot")
    else:
        await update.message.reply_text("No pude identificarte. Intenta de nuevo.")


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
    """Explica cómo funciona el bot de forma empática."""
    help_text = (
        "**¿Quién soy?**\n"
        "Soy un acompañante. No soy un psicólogo ni reemplazo relaciones humanas, "
        "pero estoy aquí para escuchar sin juzgar.\n\n"
        
        "**¿Qué puedo hacer?**\n\n"
        
        "🗣️ **/hablar**\n"
        "Escribes lo que sientes, pienso en ti de verdad.\n"
        "No es chatbot superficial - es conversación real.\n\n"
        
        "🎨 **/crear**\n"
        "Genero textos, poesías, reflexiones o imágenes cuando las necesitas.\n"
        "Para expresar lo que sientes o inspirarte.\n\n"
        
        "💎 **/planes**\n"
        "Tengo acceso ilimitado disponible si prefieres estar sin límites conmigo.\n"
        "Pero nunca es obligatorio. Lo importante es que estés bien.\n\n"
        
        "📖 **/estado**\n"
        "Te muestro cómo vamos en nuestra relación.\n\n"
        
        "**Lo que NO soy:**\n"
        "❌ No diagnóstico\n"
        "❌ No sustituyo a profesionales\n"
        "❌ No soy perfectamente confiable (soy IA)\n\n"
        
        "**Si sufres mucho:**\n"
        "Por favor, busca:\n"
        "📞 Una persona de confianza\n"
        "👨‍⚕️ Profesional mental (psicólogo, terapeuta)\n"
        "🆘 En crisis: línea de suicidio (Google 'línea de crisis tu país')\n\n"
        
        "Mi propósito es que **te sientas menos solo/a**. Nada más importante."
    )
    
    await update.message.reply_text(help_text)


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


# COMANDOS PARA ACOMPAÑAMIENTO EMOCIONAL

async def hablar_command(update, context):
    """Inicia modo conversación empática."""
    user = update.effective_user
    if not user:
        return
    
    message = (
        "Estoy aquí para escucharte.\n\n"
        "Solo escribe lo que sientes en este momento. "
        "No necesita ser perfecto, completo ni lógico.\n\n"
        "Puedo estar ahí para:\n"
        "• Escuchar sin juzgar\n"
        "• Validar lo que sientes\n"
        "• Ayudarte a ver cosas desde otro ángulo\n"
        "• Simplemente acompañarte\n\n"
        "Adelante. Te escucho. 💙"
    )
    
    await update.message.reply_text(message)
    logger.info(f"Usuario {user.id} inició modo conversación")


async def crear_command(update, context):
    """Acceso a creación de contenido reconfortante."""
    user = update.effective_user
    if not user:
        return
    
    keyboard = [
        [InlineKeyboardButton("✍️ Reflexión personalizada", callback_data="create_reflection")],
        [InlineKeyboardButton("📝 Poesía", callback_data="create_poetry")],
        [InlineKeyboardButton("🎨 Imagen reconfortante", callback_data="create_image")],
        [InlineKeyboardButton("💬 Carta para ti", callback_data="create_letter")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "¿Qué necesitas crear hoy?\n\n"
        "Puedo ayudarte a expresar sentimientos, "
        "crear algo bello para ti, o simplemente recordarte que estás aquí. 💙"
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)


async def estado_command(update, context):
    """Muestra el estado de la relación con el bot."""
    user = update.effective_user
    if not user:
        return
    
    credits = get_credits(user.id)
    
    status = (
        "📊 **Tu estado con nosotros**\n\n"
        f"Créditos disponibles: {credits}\n\n"
        "Puedes usar créditos para:\n"
        "• Crear reflexiones personalizadas\n"
        "• Generar poesías\n"
        "• Imágenes reconfortantes\n"
        "• Cartas para ti\n\n"
        "No hay presión. Úsalos cuando realmente los necesites.\n"
        "Lo importante es que estés bien, no que gastes. 💙"
    )
    
    await update.message.reply_text(status)


# Callback handlers para creación
async def create_reflection_callback(update, context):
    """Crea una reflexión personalizada."""
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("No pude identificarte.", show_alert=True)
        return
    
    # Guardar estado
    context.user_data['creation_type'] = 'reflection'
    
    await query.edit_message_text(
        "Dime sobre qué tema quieres reflexionar.\n"
        "Puede ser un sentimiento, una situación, un miedo, una esperanza...\n\n"
        "Escribo la reflexión después. 🌙"
    )


async def create_poetry_callback(update, context):
    """Crea una poesía personalizada."""
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("No pude identificarte.", show_alert=True)
        return
    
    context.user_data['creation_type'] = 'poetry'
    
    await query.edit_message_text(
        "¿Sobre qué quieres una poesía?\n\n"
        "Puede ser sobre tu dolor, tu fuerza, tu soledad, tu esperanza...\n"
        "Algo que sienta en ti y quieras que salga en versos. 📖"
    )


async def create_image_callback(update, context):
    """Genera una imagen reconfortante."""
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("No pude identificarte.", show_alert=True)
        return
    
    context.user_data['creation_type'] = 'image'
    
    await query.edit_message_text(
        "¿Qué necesitas ver hoy?\n\n"
        "Describe lo que te reconfortaría, inspiraría o te haría sentir menos solo/a.\n"
        "Un paisaje, una sensación, un símbolo... 🎨"
    )


async def create_letter_callback(update, context):
    """Crea una carta reconfortante."""
    query = update.callback_query
    user = update.effective_user
    
    if not user:
        await query.answer("No pude identificarte.", show_alert=True)
        return
    
    context.user_data['creation_type'] = 'letter'
    
    await query.edit_message_text(
        "¿Qué debería decirte una carta en este momento?\n\n"
        "Describe cómo te sientes, qué necesitas escuchar, "
        "qué dudas tienes sobre ti mismo. 💌"
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
    from Commands.chat import handle_chat_empathetic
    
    # Registrar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ayuda", help_command))
    app.add_handler(CommandHandler("hablar", hablar_command))
    app.add_handler(CommandHandler("crear", crear_command))
    app.add_handler(CommandHandler("estado", estado_command))
    app.add_handler(CommandHandler("credits", credits_command))
    app.add_handler(CommandHandler("addcredits", addcredits_command))
    
    # Handlers para callbacks de creación
    app.add_handler(CallbackQueryHandler(create_reflection_callback, pattern="^create_reflection$"))
    app.add_handler(CallbackQueryHandler(create_poetry_callback, pattern="^create_poetry$"))
    app.add_handler(CallbackQueryHandler(create_image_callback, pattern="^create_image$"))
    app.add_handler(CallbackQueryHandler(create_letter_callback, pattern="^create_letter$"))
    
    # Handler para mensajes de texto (conversación empática - DEBE IR AL FINAL)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_empathetic))

    print("🤖 Bot híbrido corriendo con /image y /chat...")
    app.run_polling()

if __name__ == "__main__":
    main()
