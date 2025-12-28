#!/usr/bin/env python3
"""
Script de verificación del bot - Prueba que todos los imports funcionan
Ejecuta: python verify_bot.py
"""

import sys
import os

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Verificando dependencias y estructura del bot...\n")

# Paso 1: Verificar .env
print("1️⃣ Verificando archivo .env...")
if os.path.exists(".env"):
    print("   ✅ Archivo .env encontrado")
else:
    print("   ❌ Archivo .env no encontrado")
    sys.exit(1)

# Paso 2: Verificar variables de entorno requeridas
print("\n2️⃣ Verificando variables de entorno...")
required_vars = ["TELEGRAM_BOT_TOKEN", "GROQ_API_KEY", "ADMIN_IDS"]
from dotenv import load_dotenv
load_dotenv()

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"   ✅ {var} configurado")
    else:
        print(f"   ❌ {var} NO configurado")
        missing_vars.append(var)

if missing_vars:
    print(f"\n⚠️ Variables faltantes: {', '.join(missing_vars)}")
    sys.exit(1)

# Paso 3: Verificar imports principales
print("\n3️⃣ Verificando imports principales...")
try:
    from telegram.ext import Application, CommandHandler
    print("   ✅ telegram.ext importado correctamente")
except ImportError as e:
    print(f"   ❌ Error importando telegram: {e}")
    sys.exit(1)

try:
    from groq import Groq
    print("   ✅ groq importado correctamente")
except ImportError as e:
    print(f"   ❌ Error importando groq: {e}")
    sys.exit(1)

try:
    from utils.credits import init_db, get_credits
    print("   ✅ utils.credits importado correctamente")
except ImportError as e:
    print(f"   ❌ Error importando utils.credits: {e}")
    sys.exit(1)

# Paso 4: Verificar archivos de comandos
print("\n4️⃣ Verificando archivos de comandos...")
command_files = [
    "Commands/start.py",
    "Commands/help.py",
    "Commands/chat.py",
    "Commands/crear.py",
    "Commands/estado.py",
    "Commands/credits.py",
    "Commands/donate.py",
    "Commands/callbacks.py"
]

for file in command_files:
    if os.path.exists(file):
        print(f"   ✅ {file} existe")
    else:
        print(f"   ❌ {file} NO encontrado")
        sys.exit(1)

# Paso 5: Verificar funciones principales
print("\n5️⃣ Verificando funciones principales...")
try:
    from Commands.start import start_command
    print("   ✅ start_command importado")
except ImportError as e:
    print(f"   ❌ Error importando start_command: {e}")
    sys.exit(1)

try:
    from Commands.help import help_command
    print("   ✅ help_command importado")
except ImportError as e:
    print(f"   ❌ Error importando help_command: {e}")
    sys.exit(1)

try:
    from Commands.chat import start_chat, handle_chat
    print("   ✅ chat functions importadas")
except ImportError as e:
    print(f"   ❌ Error importando chat functions: {e}")
    sys.exit(1)

try:
    from Commands.credits import credits_command, addcredits_command
    print("   ✅ credits functions importadas")
except ImportError as e:
    print(f"   ❌ Error importando credits functions: {e}")
    sys.exit(1)

# Paso 6: Verificar base de datos
print("\n6️⃣ Verificando base de datos...")
try:
    init_db()
    print("   ✅ Base de datos inicializada")
except Exception as e:
    print(f"   ❌ Error inicializando BD: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ ¡VERIFICACIÓN COMPLETADA EXITOSAMENTE!")
print("="*50)
print("\n🚀 Ahora puedes ejecutar: python bot.py\n")
