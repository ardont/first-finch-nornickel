import requests
import json
import re
from app.core.config import settings

ONTOLOGY_SYSTEM_PROMPT = """
Ты — модуль извлечения онтологии знаний для научно-технического отдела Норникеля.
Проанализируй научно-технический текст и выдели строго структурированные сущности (вершины графа) и их взаимосвязи (ребра).

Выводи результат ТОЛЬКО в формате JSON-списка объектов с полями:
- "source": Название исходной сущности (нормализованное, в именительном падеже)
- "source_type": Тип исходной сущности (одно из: Material, Process, Equipment, Expert, Facility, Parameter)
- "target": Название связанной сущности (нормализованное, в именительном падеже)
- "target_type": Тип связанной сущности (одно из: Material, Process, Equipment, Expert, Facility, Parameter)
- "relationship": Тип связи (одно из: USES, PRODUCES, CONTRADICTS, LOCATED_IN, WORKS_ON, MEASURES, CONTAINS)

Пример вывода:
[
  {"source": "Обратный осмос", "source_type": "Process", "target": "Сухой остаток", "target_type": "Parameter", "relationship": "MEASURES"},
  {"source": "Электроэкстракция", "source_type": "Process", "target": "Католит", "target_type": "Material", "relationship": "USES"}
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

    def get_embedding(self, text: str, model_type: str = "text-search-doc") -> list[float]:
        """
        model_type: 'text-search-doc' или 'text-search-query'
        """
        payload = {
            "modelUri": f"emb://{self.folder_id}/{model_type}/latest",
            "text": text
        }
        response = requests.post(self.embedding_url, json=payload, headers=self.get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()["embedding"]

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

