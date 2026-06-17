"""
OpenAI service for embeddings, query translation, and AI answers.
"""
import hashlib
import logging
import math
import os
import re
from typing import AsyncGenerator, List, Tuple

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIService:
    """Wrapper around OpenAI-compatible APIs."""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.base_url = os.getenv('OPENAI_BASE_URL')
        self.embedding_dimension = int(os.getenv('OPENAI_EMBEDDING_DIMENSION', '1536'))
        self.enable_local_embedding_fallback = os.getenv('ENABLE_LOCAL_EMBEDDING_FALLBACK', 'true').lower() != 'false'

        client_kwargs = {
            'api_key': self.api_key,
            'timeout': 60.0,
            'max_retries': 2,
        }
        if self.base_url:
            client_kwargs['base_url'] = self.base_url

        try:
            self.client = AsyncOpenAI(**client_kwargs)
            logger.info("OpenAI client initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize OpenAI client: %s", exc)
            raise

        self.default_model = os.getenv('OPENAI_MODEL', 'qwen-max')
        configured_translation_model = os.getenv('OPENAI_TRANSLATION_MODEL')
        self.translation_model = configured_translation_model or self.default_model
        self.embedding_model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        self.embedding_batch_size = max(1, int(os.getenv('OPENAI_EMBEDDING_BATCH_SIZE', '20')))
        logger.info("Using chat model: %s", self.default_model)
        logger.info("Using translation model: %s", self.translation_model)
        logger.info("Using embedding model: %s", self.embedding_model)
        logger.info("Using embedding batch size: %s", self.embedding_batch_size)
        logger.info("Local embedding fallback enabled: %s", self.enable_local_embedding_fallback)
        if self.base_url:
            logger.info("Using OpenAI base URL: %s", self.base_url)

    def _tokenize_for_fallback(self, text: str) -> List[str]:
        tokens = re.findall(r'[\u4e00-\u9fff]|[A-Za-z0-9_]+', text.lower())
        return tokens or ['']

    def _generate_local_embedding(self, text: str) -> List[float]:
        vector = [0.0] * self.embedding_dimension
        tokens = self._tokenize_for_fallback(text)

        for token in tokens:
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            bucket = int.from_bytes(digest[:8], 'big') % self.embedding_dimension
            sign = -1.0 if digest[8] % 2 else 1.0
            weight = 1.0 + (digest[9] / 255.0)
            vector[bucket] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _generate_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        logger.warning(
            "Falling back to local hashed embeddings for %s texts; semantic quality will be reduced",
            len(texts)
        )
        return [self._generate_local_embedding(text) for text in texts]

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = None,
        batch_size: int = None
    ) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            if not texts:
                return []

            effective_batch_size = max(1, batch_size or self.embedding_batch_size)
            embeddings = []

            for start in range(0, len(texts), effective_batch_size):
                batch = texts[start:start + effective_batch_size]
                response = await self.client.embeddings.create(
                    model=model or self.embedding_model,
                    input=batch
                )
                embeddings.extend(item.embedding for item in response.data)
                logger.info(
                    "Generated embeddings batch %s-%s of %s",
                    start + 1,
                    start + len(batch),
                    len(texts)
                )

            logger.info("Generated %s embeddings", len(embeddings))
            return embeddings

        except Exception as exc:
            logger.error("Error generating embeddings: %s", exc)
            if self.enable_local_embedding_fallback:
                return self._generate_local_embeddings(texts)
            raise Exception(f"Failed to generate embeddings: {exc}")

    async def chat_completion_stream(
        self,
        messages: List[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions."""
        try:
            stream = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as exc:
            logger.error("Error in streaming chat: %s", exc)
            yield f"\n\n[Error: {exc}]"

    async def generate_answer(
        self,
        question: str,
        context: str,
        chat_history: List[dict] = None,
        model: str = None
    ) -> str:
        """Generate an answer grounded in the provided context."""
        try:
            system_prompt = """You are a professional academic assistant.
Answer based only on the provided paper context.
If the context is insufficient, say so clearly.
Use Chinese in the reply."""

            user_prompt = f"""Reference content:
{context}

Question:
{question}

Please answer based on the reference content above."""

            messages = [{"role": "system", "content": system_prompt}]

            if chat_history:
                for msg in chat_history[-5:]:
                    messages.append(msg)

            messages.append({"role": "user", "content": user_prompt})

            response = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            answer = response.choices[0].message.content
            logger.info("Generated answer for question: %s...", question[:50])
            return answer

        except Exception as exc:
            logger.error("Error generating answer: %s", exc)
            return f"抱歉，生成答案时出错：{exc}"

    def detect_language(self, text: str) -> str:
        """Detect whether text is Chinese, English, or mixed."""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        chinese_chars = len(chinese_pattern.findall(text))

        english_pattern = re.compile(r'[a-zA-Z]+')
        english_words = len(english_pattern.findall(text))

        total_chars = len(text.strip())

        if total_chars == 0:
            return 'en'

        chinese_ratio = chinese_chars / total_chars

        if chinese_ratio > 0.3:
            return 'zh'
        if chinese_ratio < 0.1 and english_words > 0:
            return 'en'
        return 'mixed'

    async def translate_query(
        self,
        query: str,
        target_language: str = 'en',
        model: str = None
    ) -> Tuple[str, bool]:
        """Translate a query for cross-language search."""
        try:
            if target_language == 'en':
                system_prompt = """You are a professional translator for academic queries.
Translate the following Chinese query to English.
Keep academic terms accurate and natural.
Only output the translation, nothing else."""
            else:
                system_prompt = """你是一个专业的学术查询翻译器。
将以下英文查询翻译成中文。
保持学术术语准确自然。
只输出翻译结果，不要其他内容。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]

            response = await self.client.chat.completions.create(
                model=model or self.translation_model,
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )

            translated = response.choices[0].message.content.strip()
            logger.info("Translated query: '%s' -> '%s'", query, translated)
            return translated, True

        except Exception as exc:
            logger.error("Translation failed: %s, using original query", exc)
            return query, False


_openai_service = None


def get_openai_service() -> OpenAIService:
    """Get the shared OpenAI service instance."""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
