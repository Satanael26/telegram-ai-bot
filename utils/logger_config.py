import logging
import logging.handlers
import os

def setup_logging():
    """
    Configura el sistema de logging para el bot.
    """
    # Obtener configuración de entorno
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "bot.log")

    # Convertir string a nivel de logging
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configurar logger root
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # Limpiar handlers existentes
    logger.handlers.clear()

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo (con rotación)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
