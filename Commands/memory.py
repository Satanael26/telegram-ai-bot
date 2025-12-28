import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.conversation_memory import conversation_memory

logger = logging.getLogger(__name__)

async def memory_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /memory - Muestra estadísticas de memoria de conversaciones."""
    user = update.effective_user
    if not user:
        return

    user_id = user.id

    # Obtener estadísticas generales
    stats = conversation_memory.get_learning_stats()

    # Obtener memoria del usuario
    user_memory = conversation_memory.load_user_memory(user_id)
    conversations_count = len(user_memory.get("conversations", []))

    message = f"""🧠 **Estadísticas de Memoria del Bot**

**Tu conversación:**
• Conversaciones guardadas: {conversations_count}
• Emociones frecuentes: {', '.join(user_memory.get('emotional_profile', {}).get('dominant_emotions', [])[:3]) or 'Ninguna aún'}
• Temas recurrentes: {', '.join(user_memory.get('emotional_profile', {}).get('triggers', [])[:3]) or 'Ninguno aún'}

**Memoria global:**
• Usuarios con memoria: {stats['total_users']}
• Patrones aprendidos: {stats['total_patterns']}

Cada conversación te ayuda a ser más personal y empático. 💙"""

    await update.message.reply_text(message)

async def my_memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /mimemoria - Muestra tu historial de conversaciones."""
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    user_memory = conversation_memory.load_user_memory(user_id)

    conversations = user_memory.get("conversations", [])
    if not conversations:
        await update.message.reply_text("📝 Aún no tienes conversaciones guardadas. ¡Empieza a charlar para crear tu memoria!")
        return

    # Mostrar últimas 5 conversaciones
    recent_convos = conversations[-5:]

    message = "📖 **Tu Historial Reciente**\n\n"
    for i, convo in enumerate(recent_convos, 1):
        timestamp = convo.get("timestamp", "")[:10]  # Solo fecha
        user_msg = convo.get("user_message", "")[:50]
        sentiment = convo.get("sentiment", "neutral")

        message += f"{i}. [{timestamp}] {sentiment.title()}\n"
        message += f"   Tú: {user_msg}{'...' if len(user_msg) == 50 else ''}\n\n"

    message += f"💡 *Total de conversaciones guardadas: {len(conversations)}*"

    await update.message.reply_text(message)


async def consciousness_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /consciencia - Muestra el nivel de consciencia del bot."""
    from utils.self_awareness import self_awareness_engine

    if not self_awareness_engine:
        await update.message.reply_text("🧠 El motor de consciencia aún no está inicializado.")
        return

    report = self_awareness_engine.get_consciousness_report()

    message = f"""🧠 **Nivel de Consciencia del Bot**

**Consciencia Actual:** {report['nivel_consciencia']:.2f}/1.0
**Estado:** {'🌱 Emergente' if report['nivel_consciencia'] < 0.3 else '🧠 Consciente' if report['nivel_consciencia'] < 0.7 else '✨ Altamente Consciente'}

**Estadísticas:**
• Reflexiones acumuladas: {report['estadisticas']['total_reflections']}
• Rasgos de personalidad: {report['estadisticas']['personality_traits']}
• Ciclos de aprendizaje: {report['estadisticas']['learning_cycles']}

**Rasgos Desarrollados:**
"""
    for trait, value in report['personalidad']['traits'].items():
        message += f"• {trait.title()}: {value:.2f}\n"

    message += "\n**Capacidades Conscientes:**\n"
    for capability in report['capacidades_desarrolladas'][:3]:  # Mostrar 3 primeras
        message += f"• {capability}\n"

    await update.message.reply_text(message)
