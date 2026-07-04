import requests
import json
import re
import time
from functools import wraps
from app.core.config import settings

def retry_on_429(max_retries=3, delay=1.5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Проверяем наличие ошибки 429 или Too Many Requests
                    if "429" in str(e) or "too many requests" in str(e).lower():
                        sleep_time = delay * (2 ** attempt)
                        print(f"⚠️ Получен лимит запросов (429). Ожидание {sleep_time}с перед повторной попыткой...")
                        time.sleep(sleep_time)
                    else:
                        raise e
            return func(*args, **kwargs)
        return wrapper
    return decorator

ONTOLOGY_SYSTEM_PROMPT = """
Ты — модуль извлечения онтологии знаний для научно-технического отдела Норникеля.
Проанализируй научно-технический текст и выдели строго структурированные сущности (вершины графа) и их взаимосвязи (ребра).

ПРАВИЛО ОГРАНИЧЕНИЯ: Извлеки не более 10 самых главных и точных связей из текста. Не пытайся извлечь всё. Главное — строго валидный закрытый JSON-массив.

Выводи результат ТОЛЬКО в формате JSON-списка объектов с полями:
- "source": Название исходной сущности (нормализованное, в именительном падеже)
- "source_type": Тип исходной сущности (одно из: Experiment, Material, Condition, Property, Publication, Facility, Expert, Equipment)
- "target": Название связанной сущности (нормализованное, в именительном падеже)
- "target_type": Тип связанной сущности (одно из: Experiment, Material, Condition, Property, Publication, Facility, Expert, Equipment)
- "relationship": Тип связи (одно из: USES_MATERIAL, OPERATES_AT_CONDITION, PRODUCES_OUTPUT, DESCRIBED_IN, VALIDATED_BY, CONFLICTS)

Пример вывода:
[
  {"source": "Эксперимент 1", "source_type": "Experiment", "target": "Сульфаты", "target_type": "Material", "relationship": "USES_MATERIAL"},
  {"source": "Электроэкстракция", "source_type": "Experiment", "target": "Католит", "target_type": "Material", "relationship": "USES_MATERIAL"}
]
"""

class YandexAIService:
    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.embedding_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
        self.completion_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def get_headers(self):
        return {
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

    @retry_on_429(max_retries=3, delay=1.5)
    def get_embedding(self, text: str, model_type: str = "text-embeddings-v2-doc") -> list[float]:
        """
        model_type: 'text-embeddings-v2-doc' или 'text-embeddings-v2-query'
        """
        payload = {
            "modelUri": f"emb://{self.folder_id}/{model_type}/latest",
            "text": text
        }
        response = requests.post(self.embedding_url, json=payload, headers=self.get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()["embedding"]

    @retry_on_429(max_retries=3, delay=2.0)
    def generate_completion(self, system_prompt: str, user_prompt: str, model: str = "yandexgpt", temperature: float = 0.3) -> str:
        """
        model: 'yandexgpt' (Pro) или 'yandexgpt-lite'
        """
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}/latest",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": "2000"
            },
            "messages": [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_prompt}
            ]
        }
        response = requests.post(self.completion_url, json=payload, headers=self.get_headers(), timeout=60)
        response.raise_for_status()
        return response.json()["result"]["alternatives"][0]["message"]["text"]

    def extract_ontology(self, chunk_text: str) -> list[dict]:
        """
        Отправляет чанк в YandexGPT Lite для извлечения триплетов онтологии.
        Возвращает список извлеченных связей в виде словарей.
        """
        try:
            raw_response = self.generate_completion(
                system_prompt=ONTOLOGY_SYSTEM_PROMPT,
                user_prompt=f"Извлеки онтологию из следующего текста:\n\n{chunk_text}",
                model="yandexgpt-lite",
                temperature=0.1
            )
            
            # Очистка разметки ```json ... ``` если LLM её добавила
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
                cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
        except Exception as e:
            print(f"Ошибка при извлечении онтологии из чанка: {e}")
            return []

yandex_ai = YandexAIService()


