"""
AI Service for the Emotional Companion Bot.
Provides optimized AI interactions with caching, error handling, and performance monitoring.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from functools import lru_cache
import hashlib

from groq import Groq, APIError as GroqAPIError

from .config import config
from .exceptions import APIError, RateLimitError, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class AIRequest:
    """Represents an AI service request."""
    messages: List[Dict[str, str]]
    model: str = "llama-3.1-8b-instant"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    timeout: Optional[int] = None
    request_id: Optional[str] = None

    def __post_init__(self):
        """Set defaults and generate request ID."""
        self.max_tokens = self.max_tokens or config.max_tokens
        self.temperature = self.temperature or config.temperature
        self.timeout = self.timeout or config.timeout
        self.request_id = self.request_id or self._generate_request_id()

    def _generate_request_id(self) -> str:
        """Generate a unique request ID based on content."""
        content = str(self.messages) + str(self.model)
        return hashlib.md5(content.encode()).hexdigest()[:8]

@dataclass
class AIResponse:
    """Represents an AI service response."""
    content: str
    model: str
    tokens_used: int
    processing_time: float
    request_id: str
    cached: bool = False

class AIService:
    """Optimized AI service with caching and error handling."""

    def __init__(self):
        self.client: Optional[Groq] = None
        self.cache: Dict[str, AIResponse] = {}
        self.cache_max_size = 100  # Maximum cache entries
        self.request_times: List[float] = []  # For rate limiting
        self.max_requests_per_minute = config.rate_limit_per_minute

        # Initialize client
        self._init_client()

    def _init_client(self):
        """Initialize the Groq client."""
        try:
            self.client = Groq(api_key=config.groq_api_key)
            logger.info("AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            raise APIError("Failed to initialize AI service", details={"error": str(e)})

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        use_cache: bool = True,
        **kwargs
    ) -> AIResponse:
        """
        Generate AI response with caching and error handling.

        Args:
            messages: List of message dictionaries
            use_cache: Whether to use response caching
            **kwargs: Additional parameters for the AI request

        Returns:
            AIResponse object with the generated content
        """
        # Check rate limits
        await self._check_rate_limits()

        # Create request object
        request = AIRequest(messages=messages, **kwargs)

        # Check cache first
        if use_cache and request.request_id in self.cache:
            cached_response = self.cache[request.request_id]
            cached_response.cached = True
            logger.debug(f"Cache hit for request {request.request_id}")
            return cached_response

        # Make API call
        start_time = time.time()
        try:
            response = await self._call_api(request)
            processing_time = time.time() - start_time

            ai_response = AIResponse(
                content=response.choices[0].message.content.strip(),
                model=response.model,
                tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else 0,
                processing_time=processing_time,
                request_id=request.request_id
            )

            # Cache the response
            if use_cache:
                self._cache_response(request.request_id, ai_response)

            # Record request time for rate limiting
            self.request_times.append(time.time())

            # Clean old request times (keep only last minute)
            cutoff_time = time.time() - 60
            self.request_times = [t for t in self.request_times if t > cutoff_time]

            logger.info(f"AI response generated in {processing_time:.2f}s for request {request.request_id}")
            return ai_response

        except GroqAPIError as e:
            processing_time = time.time() - start_time
            error_msg = f"Groq API error: {e}"

            if "rate limit" in str(e).lower():
                raise RateLimitError(
                    "AI service rate limit exceeded",
                    details={"processing_time": processing_time}
                )
            else:
                raise APIError(
                    error_msg,
                    details={"processing_time": processing_time, "request_id": request.request_id}
                )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Unexpected AI service error: {e}")
            raise APIError(
                f"AI service error: {str(e)}",
                details={"processing_time": processing_time, "request_id": request.request_id}
            )

    async def _call_api(self, request: AIRequest) -> Any:
        """Make the actual API call to Groq."""
        # Convert to Groq format
        groq_messages = []
        for msg in request.messages:
            groq_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            groq_messages.append(groq_msg)

        # Make async call
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(
                messages=groq_messages,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout=request.timeout
            )
        )

        return response

    async def _check_rate_limits(self):
        """Check if we're within rate limits."""
        current_time = time.time()
        cutoff_time = current_time - 60  # Last minute

        recent_requests = len([t for t in self.request_times if t > cutoff_time])

        if recent_requests >= self.max_requests_per_minute:
            raise RateLimitError(
                f"Rate limit exceeded: {recent_requests}/{self.max_requests_per_minute} requests per minute"
            )

    def _cache_response(self, request_id: str, response: AIResponse):
        """Cache an AI response."""
        self.cache[request_id] = response

        # Maintain cache size limit
        if len(self.cache) > self.cache_max_size:
            # Remove oldest entries (simple LRU approximation)
            oldest_keys = list(self.cache.keys())[:len(self.cache) - self.cache_max_size]
            for key in oldest_keys:
                del self.cache[key]

    def clear_cache(self):
        """Clear the response cache."""
        self.cache.clear()
        logger.info("AI response cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.cache_max_size,
            "cache_hit_ratio": self._calculate_cache_hit_ratio(),
            "recent_requests_per_minute": len([t for t in self.request_times if t > time.time() - 60])
        }

    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio (simplified)."""
        # This is a simplified calculation - in production you'd track hits vs misses
        if not hasattr(self, '_total_requests'):
            self._total_requests = 0
            self._cache_hits = 0

        # For now, return a basic ratio
        total = len(self.cache)
        return min(total / max(total + 10, 1), 0.5)  # Cap at 50% for demo

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the AI service."""
        try:
            # Simple health check request
            test_messages = [{"role": "user", "content": "Hello"}]
            response = await self.generate_response(test_messages, use_cache=False)

            return {
                "status": "healthy",
                "response_time": response.processing_time,
                "model": response.model,
                "cache_stats": self.get_cache_stats()
            }

        except Exception as e:
            logger.error(f"AI service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "cache_stats": self.get_cache_stats()
            }

    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """Validate message format."""
        if not messages or len(messages) == 0:
            raise ValidationError("Messages list cannot be empty")

        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValidationError(f"Message {i} must be a dictionary")

            if "role" not in msg or "content" not in msg:
                raise ValidationError(f"Message {i} must have 'role' and 'content' fields")

            if msg["role"] not in ["system", "user", "assistant"]:
                raise ValidationError(f"Invalid role '{msg['role']}' in message {i}")

            if not isinstance(msg["content"], str) or len(msg["content"]) == 0:
                raise ValidationError(f"Message {i} content must be a non-empty string")

            if len(msg["content"]) > config.max_message_length:
                raise ValidationError(f"Message {i} exceeds maximum length of {config.max_message_length}")

        return True

# Global AI service instance
ai_service = AIService()

# Export for easy importing
__all__ = ['AIRequest', 'AIResponse', 'AIService', 'ai_service']
