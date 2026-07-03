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

    def add_documents(self, collection_name: str, documents: list[str], embeddings: list[list[float]], metadatas: list[dict], ids: list[str]):
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def query_collection(self, collection_name: str, query_embeddings: list[list[float]], n_results: int = 5, where: dict = None):
        collection = self.get_or_create_collection(collection_name)
        # Если фильтр пустой, не передаем его
        query_args = {
            "query_embeddings": query_embeddings,
            "n_results": n_results
        }
        if where:
            query_args["where"] = where
            
        return collection.query(**query_args)

chroma_client = ChromaClient()

