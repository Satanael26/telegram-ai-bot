#!/usr/bin/env python3
"""
Script de validación para el bot de monetización.
Verifica que todos los módulos, dependencias y configuración son correctas.
"""

import os
import sys
import importlib
from pathlib import Path

def check_file_exists(filepath, description):
    """Verifica si un archivo existe."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NO ENCONTRADO: {filepath}")
        return False


def check_import(module_name, description):
    """Verifica si un módulo puede ser importado."""
    try:
        importlib.import_module(module_name)
        print(f"✓ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"✗ {description} NO DISPONIBLE: {module_name}")
        print(f"  Error: {e}")
        return False


def check_env_var(var_name, required=False):
    """Verifica si una variable de entorno está configurada."""
    value = os.getenv(var_name)
    if value:
        masked = value[:5] + "..." if len(value) > 5 else value
        print(f"✓ {var_name}: {masked}")
        return True
    elif required:
        print(f"✗ {var_name}: NO CONFIGURADO (REQUERIDO)")
        return False
    else:
        print(f"⚠ {var_name}: No configurado (opcional)")
        return False


def main():
    """Ejecuta todas las validaciones."""
    print("\n" + "="*60)
    print("🔍 VALIDACIÓN DEL BOT DE MONETIZACIÓN")
    print("="*60 + "\n")
    
    # Estado general
    all_ok = True
    
    # 1. Validar archivos del proyecto
    print("📁 Validando archivos del proyecto...")
    files_to_check = [
        ("bot.py", "Bot principal"),
        ("webhook_server.py", "Servidor Flask"),
        ("requirements.txt", "Dependencias"),
        (".env.example", "Plantilla de configuración"),
        ("Commands/chat.py", "Módulo Chat"),
        ("Commands/image.py", "Módulo Imagen"),
        ("utils/credits.py", "Sistema de créditos"),
        ("utils/payments.py", "Sistema de pagos"),
    ]
    
    for filepath, desc in files_to_check:
        if not check_file_exists(filepath, desc):
            all_ok = False
    print()
    
    # 2. Validar dependencias
    print("📦 Validando dependencias de Python...")
    required_modules = [
        ("telegram", "python-telegram-bot"),
        ("requests", "requests"),
        ("dotenv", "python-dotenv"),
        ("groq", "groq"),
        ("stripe", "stripe"),
        ("flask", "flask"),
        ("sqlite3", "sqlite3 (built-in)"),
    ]
    
    for module, description in required_modules:
        if not check_import(module, description):
            all_ok = False
    print()
    
    # 3. Validar variables de entorno
    print("🔑 Validando variables de entorno...")
    
    # Cargar .env si existe
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        ("TELEGRAM_TOKEN", True),
        ("GROQ_API_KEY", True),
        ("STRIPE_PUBLIC_KEY", True),
        ("STRIPE_SECRET_KEY", True),
        ("STRIPE_WEBHOOK_SECRET", True),
        ("STRIPE_PRICE_BASIC", True),
        ("STRIPE_PRICE_PRO", True),
        ("STRIPE_PRICE_AGENCY", True),
    ]
    
    optional_vars = [
        ("ADMIN_IDS", False),
        ("DB_PATH", False),
        ("FLASK_PORT", False),
        ("IMAGE_CREDIT_COST", False),
    ]
    
    for var, required in required_vars:
        if not check_env_var(var, required=required):
            if required:
                all_ok = False
    
    for var, required in optional_vars:
        check_env_var(var, required=required)
    print()
    
    # 4. Validar base de datos
    print("💾 Validando base de datos...")
    db_path = os.getenv("DB_PATH", "bot_data.sqlite")
    if os.path.exists(db_path):
        size = os.path.getsize(db_path) / 1024  # KB
        print(f"✓ Base de datos existe: {db_path} ({size:.1f} KB)")
    else:
        print(f"⚠ Base de datos no existe (se creará al ejecutar bot): {db_path}")
    print()
    
    # 5. Validar directorios
    print("📂 Validando directorios...")
    dirs_to_check = [
        ("Commands", "Módulos de comandos"),
        ("utils", "Módulos de utilidad"),
        ("imagenes_generadas", "Almacenamiento de imágenes"),
    ]
    
    for dirname, desc in dirs_to_check:
        if os.path.isdir(dirname):
            print(f"✓ {desc}: {dirname}")
        else:
            print(f"⚠ {desc} NO EXISTE: {dirname}")
            print(f"  Se creará automáticamente")
    print()
    
    # 6. Resumen
    print("="*60)
    if all_ok:
        print("✅ VALIDACIÓN EXITOSA - Bot listo para ejecutar")
        print("\nPróximos pasos:")
        print("1. Configura STRIPE en https://dashboard.stripe.com")
        print("2. Copia los precios en .env")
        print("3. Ejecuta: python bot.py")
        print("4. En otra terminal: python webhook_server.py")
    else:
        print("❌ HAY ERRORES - Verifica la configuración")
        print("\nErrores detectados:")
        print("• Verifica que todas las variables de entorno están configuradas")
        print("• Revisa que los archivos existen")
        print("• Instala dependencias: pip install -r requirements.txt")
    print("="*60 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
