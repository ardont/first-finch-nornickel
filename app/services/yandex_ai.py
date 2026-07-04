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

Выводи результат в формате JSON-объекта со следующей структурой:
{
  "nodes": [
    {
      "id": "уникальный_id_в_пределах_текста",
      "type": "Тип сущности (одно из: Experiment, Material, Condition, Property, Publication, Facility, Expert, Equipment)",
      "properties": {
        "name": "Название сущности (нормализованное, в именительном падеже)",
        ... другие дополнительные свойства, обнаруженные в тексте (например: manufacturer, role, date, result_status и т.д.)
      }
    }
  ],
  "relationships": [
    {
      "source": "id_исходного_узла",
      "target": "id_целевого_узла",
      "type": "Тип связи (одно из: USES_MATERIAL, OPERATES_AT_CONDITION, PRODUCES_OUTPUT, DESCRIBED_IN, VALIDATED_BY, CONFLICTS, RELATED_TO)",
      "properties": {
        ... дополнительные свойства связи, обнаруженные в тексте (например: confidence и т.д.)
      }
    }
  ]
}

ПРАВИЛО ОГРАНИЧЕНИЯ: Извлеки не более 10 самых главных и точных связей из текста. Не пытайся извлечь всё.
"""

class YandexAIService:
    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.proxies = {
            "http": settings.PROXY,
            "https": settings.PROXY
        } if getattr(settings, "PROXY", None) else None

    @retry_on_429(max_retries=3, delay=1.5)
    def get_embedding(self, text: str, model_type: str = "text-embeddings-v2-doc") -> list[float]:
        """
        model_type: указывает на документ или запрос.
        """
        # Определяем taskType для Google Gemini Embedding API
        task_type = "RETRIEVAL_QUERY" if "query" in model_type else "RETRIEVAL_DOCUMENT"
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "content": {
                "parts": [
                    {
                        "text": text
                    }
                ]
            },
            "taskType": task_type,
            "outputDimensionality": 256
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10, proxies=self.proxies)
        response.raise_for_status()
        return response.json()["embedding"]["values"]

    @retry_on_429(max_retries=3, delay=2.0)
    def generate_completion(self, system_prompt: str, user_prompt: str, model: str = "gemini-2.5-flash", temperature: float = 0.3, response_mime_type: str = None, response_schema: dict = None) -> str:
        """
        model: 'gemini-2.5-flash'
        """
        # Перенаправляем yandexgpt на gemini-2.5-flash
        if "yandexgpt" in model or "gpt" in model:
            model = "gemini-2.5-flash"
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": system_prompt
                    }
                ]
            },
            "contents": [
                {
                    "parts": [
                        {
                            "text": user_prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2000
            }
        }
        
        # Если запрашивается извлечение онтологии, заставляем модель отдавать валидный JSON
        if response_mime_type:
            payload["generationConfig"]["responseMimeType"] = response_mime_type
        if response_schema:
            payload["generationConfig"]["responseSchema"] = response_schema
            
        response = requests.post(url, json=payload, headers=headers, timeout=60, proxies=self.proxies)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    def extract_ontology(self, chunk_text: str) -> list[dict]:
        """
        Отправляет чанк в Gemini для извлечения триплетов онтологии.
        Возвращает список извлеченных связей в виде словарей.
        """
        schema = {
            "type": "OBJECT",
            "properties": {
                "nodes": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "id": {"type": "STRING"},
                            "type": {
                                "type": "STRING",
                                "enum": ["Experiment", "Material", "Condition", "Property", "Publication", "Facility", "Expert", "Equipment"]
                            },
                            "properties": {
                                "type": "OBJECT",
                                "properties": {
                                    "name": {"type": "STRING"}
                                },
                                "required": ["name"]
                            }
                        },
                        "required": ["id", "type", "properties"]
                    }
                },
                "relationships": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "source": {"type": "STRING"},
                            "target": {"type": "STRING"},
                            "type": {
                                "type": "STRING",
                                "enum": ["USES_MATERIAL", "OPERATES_AT_CONDITION", "PRODUCES_OUTPUT", "DESCRIBED_IN", "VALIDATED_BY", "CONFLICTS", "RELATED_TO"]
                            },
                            "properties": {
                                "type": "OBJECT"
                            }
                        },
                        "required": ["source", "target", "type"]
                    }
                }
            },
            "required": ["nodes", "relationships"]
        }
        
        try:
            raw_response = self.generate_completion(
                system_prompt=ONTOLOGY_SYSTEM_PROMPT,
                user_prompt=f"Извлеки онтологию из следующего текста:\n\n{chunk_text}",
                model="gemini-2.5-flash",
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=schema
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
            return {}

yandex_ai = YandexAIService()


