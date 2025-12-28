"""
Bot Acompañante Emocional para Telegram
Un compañero IA que escucha sin juzgar y acompaña en momentos difíciles.

Autor: Sammy26
Versión: 2.0
"""

import os
import sys
import json
import urllib.request
import logging
import logging.handlers
import time

from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)
from dotenv import load_dotenv

# Importar utilidades
from utils.credits import init_db
from utils.logger_config import setup_logging

# Importar handlers de comandos
from Commands.start import start_command
from Commands.help import help_command
from Commands.chat import handle_chat, start_chat, clear_chat
from Commands.crear import crear_command
from Commands.estado import estado_command
from Commands.credits import credits_command, addcredits_command
from Commands.donate import donate_command
from Commands.memory import memory_stats_command, my_memory_command, consciousness_command

# Importar handlers de callbacks
from Commands.callbacks import (
    create_reflection_callback,
    create_poetry_callback,
    create_image_callback,
    create_letter_callback
)

# Importar handler de chat empático
handle_chat_empathetic = handle_chat

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

# IDs de administradores (global para acceso desde otros módulos)
ADMIN_IDS = set()


def load_admin_ids():
    """Carga los IDs de administradores desde variables de entorno."""
    global ADMIN_IDS
    admin_env = os.getenv("ADMIN_IDS", "")
    try:
        ADMIN_IDS = {int(x) for x in admin_env.split(",") if x.strip()}
        logger.info("Cargados %d administradores", len(ADMIN_IDS))
    except Exception as e:
        logger.warning("Error cargando ADMIN_IDS: %s", e)
        ADMIN_IDS = set()


def register_bot_commands(token: str):
    """
    Registra los comandos del bot en la API de Telegram.
    Esto permite que aparezcan en el menú de comandos del usuario.
    """
    base_url = f"https://api.telegram.org/bot{token}/setMyCommands"

    # Comandos por idioma
    commands_by_lang = {
        "es": [
            {"command": "start", "description": "Inicia el bot"},
            {"command": "hablar", "description": "Modo conversación empática"},
            {"command": "crear", "description": "Crea reflexiones, poesía, imágenes"},
            {"command": "estado", "description": "Ver tu estado y créditos"},
            {"command": "ayuda", "description": "Cómo funciona el bot"},
            {"command": "donar", "description": "Apoya el proyecto"},
        ],
        "en": [
            {"command": "start", "description": "Start the bot"},
            {"command": "hablar", "description": "Empathetic conversation mode"},
            {"command": "crear", "description": "Create reflections, poetry, images"},
            {"command": "estado", "description": "Check your status and credits"},
            {"command": "help", "description": "How the bot works"},
            {"command": "donate", "description": "Support the project"},
        ],
    }

    # Registrar comandos por idioma
    for lang, commands in commands_by_lang.items():
        payload = json.dumps({
            "commands": commands, 
            "language_code": lang
        }).encode("utf-8")
        
        req = urllib.request.Request(
            base_url, 
            data=payload, 
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
            logger.info("Comandos registrados para idioma: %s", lang)
        except Exception as e:
            logger.warning("No se pudieron registrar comandos (%s): %s", lang, e)

    # Registrar comandos globales (español por defecto)
    try:
        default_commands = commands_by_lang.get("es")
        payload = json.dumps({"commands": default_commands}).encode("utf-8")
        req = urllib.request.Request(
            base_url, 
            data=payload, 
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            _ = resp.read()
        logger.info("Comandos globales registrados")
    except Exception as e:
        logger.warning("No se pudieron registrar comandos globales: %s", e)


def setup_error_handler(app: Application):
    """
    Configura el manejador de errores global del bot.
    Envía notificaciones a los administradores cuando ocurre un error.
    """
    ERROR_NOTIFY_THROTTLE = int(os.getenv("ERROR_NOTIFY_THROTTLE", "60"))
    _last_notify = {}

    async def error_handler(update: object, context):
        """Maneja errores no capturados en el bot."""
        try:
            err = context.error
        except Exception:
            err = None

        # Recopilar contexto del error
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

        # Loggear el error
        logging.error("Unhandled exception: %s", context_info)
        if err:
            import traceback
            tb = traceback.format_exception(type(err), err, err.__traceback__)
            logging.error("%s", "".join(tb))
        else:
            logging.error("No context.error disponible")

        # Notificar a administradores (con throttling)
        notify_text = "⚠️ Se ha producido un error en el bot. Revisa los logs."
        now = time.time()
        
        for admin_id in ADMIN_IDS:
            last = _last_notify.get(admin_id, 0)
            if now - last < ERROR_NOTIFY_THROTTLE:
                logger.debug("Skipping notify for admin %s due to throttle", admin_id)
                continue
            
            try:
                await context.bot.send_message(admin_id, notify_text)
                _last_notify[admin_id] = now
            except Exception as e:
                logger.warning("No se pudo notificar al admin %s: %s", admin_id, e)

    app.add_error_handler(error_handler)
    logger.info("Error handler configurado")


def main():
    """Función principal que inicia el bot."""
    
    # Verificar token
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        sys.stderr.write(
            "ERROR: la variable TELEGRAM_TOKEN no está definida.\n"
            "Configura tu .env con TELEGRAM_TOKEN=tu_token_aqui\n"
        )
        sys.exit(1)

    # Configurar logging
    setup_logging()
    logger.info("=" * 60)
    logger.info("🤖 Iniciando Bot Acompañante Emocional")
    logger.info("=" * 60)

    # Cargar administradores
    load_admin_ids()

    # Inicializar base de datos
    try:
        init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error("❌ Error inicializando base de datos: %s", e)
        sys.exit(1)

    # Crear aplicación
    app = Application.builder().token(TOKEN).build()
    logger.info("✅ Aplicación de Telegram creada")

    # Configurar manejador de errores
    setup_error_handler(app)

    # Registrar comandos básicos
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ayuda", help_command))  # Alias español
    
    # Registrar comandos de interacción
    app.add_handler(CommandHandler("hablar", start_chat))
    app.add_handler(CommandHandler("chat", start_chat))
    app.add_handler(CommandHandler("crear", crear_command))
    app.add_handler(CommandHandler("estado", estado_command))
    app.add_handler(CommandHandler("clear", clear_chat))
    
    # Registrar comandos de créditos
    app.add_handler(CommandHandler("credits", credits_command))
    app.add_handler(CommandHandler("addcredits", addcredits_command))

    # Registrar comandos de memoria
    app.add_handler(CommandHandler("memory", memory_stats_command))
    app.add_handler(CommandHandler("memoria", memory_stats_command))  # Alias español
    app.add_handler(CommandHandler("mimemoria", my_memory_command))
    app.add_handler(CommandHandler("consciencia", consciousness_command))

    # Registrar comando de donación
    app.add_handler(CommandHandler("donar", donate_command))
    app.add_handler(CommandHandler("donate", donate_command))  # Alias inglés
    
    # Registrar callbacks de creación
    app.add_handler(CallbackQueryHandler(
        create_reflection_callback, 
        pattern="^create_reflection$"
    ))
    app.add_handler(CallbackQueryHandler(
        create_poetry_callback, 
        pattern="^create_poetry$"
    ))
    app.add_handler(CallbackQueryHandler(
        create_image_callback, 
        pattern="^create_image$"
    ))
    app.add_handler(CallbackQueryHandler(
        create_letter_callback, 
        pattern="^create_letter$"
    ))
    
    # Handler para mensajes de texto (conversación empática)
    # IMPORTANTE: Debe ir al final para no interceptar comandos
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_chat_empathetic
    ))
    
    logger.info("✅ Todos los handlers registrados")

    # Registrar comandos en Telegram
    register_bot_commands(TOKEN)

    # Iniciar bot
    logger.info("=" * 60)
    logger.info("🚀 Bot corriendo - Esperando mensajes...")
    logger.info("=" * 60)
    print("\n🤖 Bot Acompañante Emocional - Activo")
    print("💙 Presiona Ctrl+C para detener\n")
    
    app.run_polling()


if __name__ == "__main__":
    main()
