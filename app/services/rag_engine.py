from app.db.chroma_client import chroma_client
from app.db.neo4j_client import neo4j_client
from app.services.yandex_ai import yandex_ai

class RAGEngine:
    def __init__(self):
        self.collection_name = "nornickel_knowledge"

    def search_vector(self, query: str, limit: int = 5, filters: dict = None):
        """
        Поиск похожих документов в ChromaDB по вектору запроса
        """
        try:
            coll = chroma_client.get_or_create_collection(self.collection_name)
            # В рабочей версии сначала генерируем вектор:
            # query_vector = yandex_ai.get_embedding(query, "text-search-query")
            # results = coll.query(query_embeddings=[query_vector], n_results=limit, where=filters)
            # return results
            return []
        except Exception as e:
            print(f"Ошибка поиска в ChromaDB: {e}")
            return []

    def search_graph(self, query: str):
        """
        Поиск связанных сущностей, параметров и экспертов в Neo4j
        """
        cypher_query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($query) OR toLower(n.description) CONTAINS toLower($query)
        RETURN n LIMIT 10
        """
        try:
            return neo4j_client.execute_query(cypher_query, {"query": query})
        except Exception as e:
            print(f"Ошибка поиска в Neo4j: {e}")
            return []

    def answer_question(self, query: str, filters: dict = None) -> dict:
        """
        Гибридный поиск (ChromaDB + Neo4j) и генерация ответа через YandexGPT Pro
        """
        # 1. Поиск в векторной базе
        vector_results = self.search_vector(query, filters=filters)
        
        # 2. Поиск в графе знаний
        graph_results = self.search_graph(query)
        
        # 3. Формирование контекста
        context = "Контекст из векторного индекса:\n"
        if vector_results:
            # Обработка результатов ChromaDB
            pass
        else:
            context += "[Нет данных в векторном индексе]\n"
            
        context += "\nПараметры и связи из графа знаний Neo4j:\n"
        if graph_results:
            for record in graph_results:
                node = record.get("n", {})
                labels = list(node.labels) if hasattr(node, "labels") else []
                node_props = dict(node)
                context += f"- [{', '.join(labels)}] {node_props.get('name')}: {node_props.get('description', '')} (параметры: {node_props})\n"
        else:
            context += "[Нет данных в графе знаний]\n"

        system_prompt = (
            "Ты — опытный инженер и R&D-аналитик Норникеля. "
            "Ответь на вопрос пользователя на основе предоставленного технического контекста. "
            "Если в данных есть числовые параметры, обязательно укажи их. "
            "Если данные расходятся (например, разные скорости потока или ПДК), "
            "выдели блок '⚠️ Зона разногласий в данных' и перечисли нестыковки. "
            "Всегда ссылайся на источники в формате [Название_файла, стр. X] или аналогичном."
        )
        
        user_prompt = f"Вопрос: {query}\n\nКонтекст:\n{context}"
        
        try:
            answer = yandex_ai.generate_completion(system_prompt, user_prompt, model="yandexgpt")
        except Exception as e:
            answer = f"Ошибка генерации ответа через Yandex AI: {e}"

        return {
            "query": query,
            "answer": answer,
            "sources": vector_results,
            "subgraph": graph_results
        }

rag_engine = RAGEngine()
