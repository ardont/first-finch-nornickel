import chromadb
from app.core.config import settings

class ChromaClient:
    def __init__(self):
        self.host = settings.CHROMA_HOST
        self.port = int(settings.CHROMA_PORT)
        self._client = None

    @property
    def client(self):
        if not self._client:
            self._client = chromadb.HttpClient(host=self.host, port=self.port)
        return self._client

    def heartbeat(self):
        return self.client.heartbeat()

    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(name=name)

    def delete_collection(self, name: str):
        return self.client.delete_collection(name=name)

chroma_client = ChromaClient()
