import requests
from app.core.config import settings

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

yandex_ai = YandexAIService()
