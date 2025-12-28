import os
import time
import logging
import asyncio
import requests
from telegram import Update
from telegram.ext import ContextTypes
from io import BytesIO
import urllib.parse

# Importar desde utils
from utils.credits import consume_credits, get_credits, add_credits, get_user_subscription, check_usage_limit

logger = logging.getLogger(__name__)

# Configuración
output_dir = os.getenv("IMAGE_OUTPUT_DIR", "imagenes_generadas")
os.makedirs(output_dir, exist_ok=True)

# Costo en créditos por imagen
IMAGE_COST = int(os.getenv("IMAGE_CREDIT_COST", "10"))

# Estilos especializados para creators
ESTILOS_PREMIUM = {
    "glamour": "professional glamour photography, soft lighting, luxury aesthetic, beauty portrait, high fashion, studio lighting",
    "fitness": "gym motivation, athletic pose, inspirational fitness, muscular, strength, professional sports photography",
    "lifestyle": "casual lifestyle, natural lighting, authentic moment, everyday aesthetic, relatable content",
    "boudoir": "elegant boudoir style, soft focus, artistic composition, intimate aesthetic, professional photography",
    "minimalist": "minimalist style, clean background, modern aesthetic, professional, high contrast, studio lighting",
    "neon": "neon aesthetic, cyberpunk, vibrant colors, modern, glowing neon lights, dark background",
    "vintage": "vintage aesthetic, retro style, film photography, classic beauty, warm colors, nostalgic",
    "artistic": "artistic nude, fine art photography, body positive, creative composition, professional artist",
    "sultry": "sultry expression, confident pose, professional lighting, editorial style, high fashion aesthetic",
    "romantic": "romantic aesthetic, soft colors, dreamy composition, elegant pose, intimate yet artistic"
}


def generate_image_pollinations(prompt: str, style: str = None, timeout: int = 60) -> bytes:
    """Genera una imagen usando Pollinations.ai con estilos especializados.
    
    Args:
        prompt: Descripción de la imagen
        style: Estilo predefinido (ver ESTILOS_PREMIUM)
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        bytes: Imagen en formato PNG
        
    Raises:
        Exception: Si falla la generación
    """
    # Mejorar el prompt con el estilo
    if style and style in ESTILOS_PREMIUM:
        enhanced_prompt = f"{ESTILOS_PREMIUM[style]}, {prompt}, high quality, professional photography, 8k resolution"
    else:
        enhanced_prompt = f"{prompt}, high quality, professional photography, 8k resolution"
    
    # Codificar el prompt para URL
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    
    # URL de Pollinations (genera imagen al vuelo)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    
    # Parámetros opcionales
    params = {
        "width": 1024,
        "height": 1024,
        "seed": int(time.time()),  # Seed aleatorio basado en tiempo
        "nologo": "true"  # Sin marca de agua
    }
    
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Error API: {response.status_code}")
        
        return response.content
        
    except requests.exceptions.Timeout:
        raise Exception("Timeout: la generación tardó demasiado.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {str(e)}")


async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera imágenes con IA usando Pollinations.ai.
    
    Uso: /image <descripción>
    Ejemplo: /image glamour un gato astronauta en el espacio
    """
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    args = context.args or []
    
    # Verificar que hay un prompt
    if not args:
        credits = get_credits(user_id)
        sub = get_user_subscription(user_id)
        
        styles_list = "\n".join([f"  • {k}" for k in ESTILOS_PREMIUM.keys()])
        
        await update.message.reply_text(
            f"🎨 Generador de imágenes IA Premium\n\n"
            f"Uso: /image [estilo] <descripción>\n"
            f"Ejemplo: /image glamour mujer elegante en playa\n\n"
            f"Estilos disponibles:\n{styles_list}\n\n"
            f"💰 Costo: {IMAGE_COST} créditos por imagen\n"
            f"📊 Plan actual: {sub['tier'].upper()}\n"
            f"⭐ Tus créditos: {credits}"
        )
        return
    
    # Detectar estilo
    style = None
    prompt_start = 0
    
    if args[0] in ESTILOS_PREMIUM:
        style = args[0]
        prompt_start = 1
    
    # Construir prompt
    if prompt_start < len(args):
        prompt = " ".join(args[prompt_start:]).strip()
    else:
        await update.message.reply_text("⚠️ Especifica la descripción después del estilo.")
        return
    
    # Validar longitud
    if len(prompt) < 3:
        await update.message.reply_text("⚠️ La descripción es muy corta. Sé más específico.")
        return
    
    if len(prompt) > 500:
        await update.message.reply_text("⚠️ Descripción muy larga. Máximo 500 caracteres.")
        return
    
    # Verificar límites de uso
    usage = check_usage_limit(user_id, IMAGE_COST)
    if not usage["allowed"]:
        remaining = usage["credits"]
        await update.message.reply_text(
            f"⚠️ Créditos insuficientes.\n\n"
            f"Necesitas: {IMAGE_COST} créditos\n"
            f"Tienes: {remaining} créditos\n\n"
            f"Mejora tu plan para obtener más créditos.\n"
            f"Usa /planes para ver opciones."
        )
        return
    
    # Verificar y consumir créditos
    if not consume_credits(user_id, IMAGE_COST):
        remaining = get_credits(user_id)
        await update.message.reply_text(
            f"⚠️ Créditos insuficientes.\n\n"
            f"Necesitas: {IMAGE_COST} créditos\n"
            f"Tienes: {remaining} créditos\n\n"
            f"Usa /planes para mejorar tu plan."
        )
        return
    
    # Mensaje de espera
    style_text = f"Estilo: {style.upper()}\n" if style else ""
    status_msg = await update.message.reply_text(
        f"🎨 Generando imagen...\n"
        f"{style_text}"
        f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}\n\n"
        f"⏳ Esto puede tardar 10-30 segundos."
    )
    
    try:
        # Generar imagen en thread separado
        image_bytes = await asyncio.to_thread(generate_image_pollinations, prompt, style, timeout=60)
        
        # Guardar localmente (opcional)
        filename = f"img_{user_id}_{int(time.time())}.png"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        # Enviar imagen al usuario
        await update.message.reply_photo(
            photo=BytesIO(image_bytes),
            caption=f"✨ Generado: {prompt[:200]}"
        )
        
        # Borrar mensaje de espera
        await status_msg.delete()
        
        logger.info(f"Imagen generada para user {user_id}: {prompt[:50]} (style: {style})")
        
    except Exception as e:
        logger.error(f"Error generando imagen para {user_id}: {e}")
        
        # Devolver créditos
        add_credits(user_id, IMAGE_COST, kind="refund")
        
        # Mensaje de error
        await status_msg.edit_text(
            f"❌ Error generando imagen.\n"
            f"Tus {IMAGE_COST} créditos han sido devueltos.\n\n"
            f"Detalles: {str(e)[:200]}\n\n"
            f"Si el error persiste, contacta al soporte."
        )


async def batch_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera múltiples imágenes a la vez (solo para suscriptores).
    
    Uso: /batch 5 glamour descripción general
    """
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    args = context.args or []
    
    if not args:
        await update.message.reply_text(
            "🎨 Generador en lote\n\n"
            "Uso: /batch <cantidad> [estilo] <descripción>\n"
            "Ejemplo: /batch 5 glamour mujer en la playa\n\n"
            "⚠️ Solo disponible en planes Pro y Agency"
        )
        return
    
    try:
        count = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ La cantidad debe ser un número.")
        return
    
    if count < 1 or count > 10:
        await update.message.reply_text("❌ Puedes generar entre 1 y 10 imágenes a la vez.")
        return
    
    # Verificar suscripción
    sub = get_user_subscription(user_id)
    if sub["tier"] not in ["pro", "agency"]:
        await update.message.reply_text(
            f"⚠️ La generación en lote solo está disponible en planes Pro y Agency.\n"
            f"Tu plan actual: {sub['tier'].upper()}\n\n"
            f"Usa /planes para mejorar."
        )
        return
    
    total_cost = IMAGE_COST * count
    if not consume_credits(user_id, total_cost):
        remaining = get_credits(user_id)
        await update.message.reply_text(
            f"⚠️ Créditos insuficientes.\n\n"
            f"Necesitas: {total_cost} créditos\n"
            f"Tienes: {remaining} créditos"
        )
        return
    
    # Detectar estilo
    style = None
    prompt_start = 1
    
    if len(args) > 1 and args[1] in ESTILOS_PREMIUM:
        style = args[1]
        prompt_start = 2
    
    # Construir prompt
    if prompt_start < len(args):
        prompt = " ".join(args[prompt_start:]).strip()
    else:
        await update.message.reply_text("⚠️ Especifica la descripción.")
        add_credits(user_id, total_cost, kind="refund")
        return
    
    # Generar imágenes
    status_msg = await update.message.reply_text(
        f"🎨 Generando {count} imágenes...\n"
        f"Esto puede tardar un minuto."
    )
    
    successful = 0
    for i in range(count):
        try:
            image_bytes = await asyncio.to_thread(generate_image_pollinations, prompt, style, timeout=60)
            await update.message.reply_photo(
                photo=BytesIO(image_bytes),
                caption=f"✨ Imagen {i+1}/{count}"
            )
            successful += 1
        except Exception as e:
            logger.error(f"Error en imagen {i+1}: {e}")
            continue
    
    await status_msg.edit_text(
        f"✅ Generadas {successful}/{count} imágenes.\n"
        f"Créditos gastados: {total_cost}"
    )