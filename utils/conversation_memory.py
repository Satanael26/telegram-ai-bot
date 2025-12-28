import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Sistema de memoria de conversaciones para personalización del bot."""

    def __init__(self, memory_dir: str = "conversation_memory"):
        self.memory_dir = memory_dir
        self.user_memories = {}  # Cache de memorias en memoria
        self.global_patterns = {}  # Patrones aprendidos globalmente

        # Crear directorio si no existe
        os.makedirs(memory_dir, exist_ok=True)
        os.makedirs(os.path.join(memory_dir, "users"), exist_ok=True)

        # Cargar patrones globales si existen
        self._load_global_patterns()

    def _get_user_file(self, user_id: int) -> str:
        """Obtiene la ruta del archivo JSON del usuario."""
        return os.path.join(self.memory_dir, "users", f"user_{user_id}.json")

    def _load_global_patterns(self):
        """Carga patrones aprendidos globalmente."""
        pattern_file = os.path.join(self.memory_dir, "global_patterns.json")
        if os.path.exists(pattern_file):
            try:
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    self.global_patterns = json.load(f)
                logger.info(f"Cargados {len(self.global_patterns)} patrones globales")
            except Exception as e:
                logger.error(f"Error cargando patrones globales: {e}")

    def _save_global_patterns(self):
        """Guarda patrones aprendidos globalmente."""
        pattern_file = os.path.join(self.memory_dir, "global_patterns.json")
        try:
            with open(pattern_file, 'w', encoding='utf-8') as f:
                json.dump(self.global_patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando patrones globales: {e}")

    def load_user_memory(self, user_id: int) -> Dict:
        """Carga la memoria de un usuario desde archivo."""
        if user_id in self.user_memories:
            return self.user_memories[user_id]

        user_file = self._get_user_file(user_id)
        if os.path.exists(user_file):
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    memory = json.load(f)
                self.user_memories[user_id] = memory
                logger.debug(f"Memoria cargada para usuario {user_id}")
                return memory
            except Exception as e:
                logger.error(f"Error cargando memoria de usuario {user_id}: {e}")

        # Crear memoria nueva si no existe
        memory = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "conversations": [],
            "personal_info": {},
            "patterns": {},
            "emotional_profile": {
                "dominant_emotions": [],
                "triggers": [],
                "coping_strategies": [],
                "growth_areas": []
            },
            "insights": []
        }
        self.user_memories[user_id] = memory
        return memory

    def save_user_memory(self, user_id: int, memory: Dict):
        """Guarda la memoria de un usuario en archivo."""
        self.user_memories[user_id] = memory
        user_file = self._get_user_file(user_id)

        try:
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            logger.debug(f"Memoria guardada para usuario {user_id}")
        except Exception as e:
            logger.error(f"Error guardando memoria de usuario {user_id}: {e}")

    def add_conversation(self, user_id: int, user_message: str, bot_response: str,
                        context: Optional[Dict] = None):
        """Agrega una conversación a la memoria del usuario."""
        memory = self.load_user_memory(user_id)

        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "context": context or {},
            "sentiment": self._analyze_sentiment(user_message),
            "topics": self._extract_topics(user_message)
        }

        memory["conversations"].append(conversation)

        # Limitar a últimas 50 conversaciones para no hacer el archivo demasiado grande
        if len(memory["conversations"]) > 50:
            memory["conversations"] = memory["conversations"][-50:]

        # Aprender de esta conversación
        self._learn_from_conversation(user_id, conversation)

        self.save_user_memory(user_id, memory)

    def _analyze_sentiment(self, message: str) -> str:
        """Análisis simple de sentimiento (puede ser mejorado)."""
        positive_words = ["feliz", "bien", "genial", "excelente", "maravilloso", "contento", "alegre"]
        negative_words = ["triste", "mal", "terrible", "horrible", "deprimido", "ansioso", "miedo", "preocupado"]

        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _extract_topics(self, message: str) -> List[str]:
        """Extrae temas/topics de un mensaje."""
        topics = []
        message_lower = message.lower()

        # Temas comunes
        topic_keywords = {
            "ansiedad": ["ansiedad", "ansioso", "nervioso", "preocupado"],
            "depresion": ["deprimido", "triste", "depresion", "bajon"],
            "relaciones": ["pareja", "amigo", "familia", "relacion", "amor"],
            "trabajo": ["trabajo", "jefe", "empresa", "estudio"],
            "autoestima": ["valgo", "merece", "confianza", "inseguro"],
            "estres": ["estreso", "presion", "agotado", "cansado"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)

        return topics

    def _learn_from_conversation(self, user_id: int, conversation: Dict):
        """Aprende patrones de la conversación."""
        memory = self.load_user_memory(user_id)

        # Actualizar perfil emocional
        sentiment = conversation["sentiment"]
        topics = conversation["topics"]

        if sentiment not in memory["emotional_profile"]["dominant_emotions"]:
            memory["emotional_profile"]["dominant_emotions"].append(sentiment)

        for topic in topics:
            if topic not in memory["emotional_profile"]["triggers"]:
                memory["emotional_profile"]["triggers"].append(topic)

        # Aprender patrones globales útiles
        user_message = conversation["user_message"].lower()
        bot_response = conversation["bot_response"]

        # Si la respuesta fue útil (contiene consejos específicos), guardarla
        if len(bot_response.split()) > 5 and any(word in bot_response.lower()
                                                for word in ["podrías", "intenta", "considera", "recuerda"]):
            pattern_key = f"{sentiment}_{topics[0] if topics else 'general'}"
            if pattern_key not in self.global_patterns:
                self.global_patterns[pattern_key] = []

            if len(self.global_patterns[pattern_key]) < 5:  # Máximo 5 ejemplos por patrón
                self.global_patterns[pattern_key].append({
                    "user_input": user_message,
                    "bot_response": bot_response,
                    "timestamp": conversation["timestamp"]
                })

            self._save_global_patterns()

    def get_personalized_context(self, user_id: int) -> str:
        """Genera contexto personalizado para el prompt basado en la memoria del usuario."""
        memory = self.load_user_memory(user_id)

        context_parts = []

        # Información emocional
        if memory["emotional_profile"]["dominant_emotions"]:
            emotions = ", ".join(memory["emotional_profile"]["dominant_emotions"][:3])
            context_parts.append(f"Emociones frecuentes: {emotions}")

        if memory["emotional_profile"]["triggers"]:
            triggers = ", ".join(memory["emotional_profile"]["triggers"][:3])
            context_parts.append(f"Temas recurrentes: {triggers}")

        # Insights previos
        if memory["insights"]:
            recent_insights = memory["insights"][-2:]  # Últimos 2 insights
            context_parts.append("Insights previos: " + "; ".join(recent_insights))

        # Conversaciones recientes para contexto
        recent_convos = memory["conversations"][-3:]  # Últimas 3 conversaciones
        if recent_convos:
            context_parts.append("Conversaciones recientes:")
            for convo in recent_convos:
                context_parts.append(f"- Usuario: {convo['user_message'][:50]}...")
                context_parts.append(f"- Tú: {convo['bot_response'][:50]}...")

        return "\n".join(context_parts) if context_parts else ""

    def add_insight(self, user_id: int, insight: str):
        """Agrega un insight aprendido sobre el usuario."""
        memory = self.load_user_memory(user_id)
        memory["insights"].append(insight)

        # Limitar a 10 insights
        if len(memory["insights"]) > 10:
            memory["insights"] = memory["insights"][-10:]

        self.save_user_memory(user_id, memory)

    def get_learning_stats(self) -> Dict:
        """Obtiene estadísticas de aprendizaje."""
        total_users = len([f for f in os.listdir(os.path.join(self.memory_dir, "users"))
                          if f.endswith('.json')])
        total_patterns = len(self.global_patterns)

        return {
            "total_users": total_users,
            "total_patterns": total_patterns,
            "memory_dir": self.memory_dir
        }

# Instancia global
conversation_memory = ConversationMemory()
