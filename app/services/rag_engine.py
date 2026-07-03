import re
from app.db.chroma_client import chroma_client
from app.db.neo4j_client import neo4j_client
from app.services.yandex_ai import yandex_ai

SYSTEM_PROMPT = """
Ты — главный эксперт R&D центра Норникеля. Твоя задача — дать точный, научно обоснованный ответ по предоставленным данным.

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:
1. Аргументация: Указывай источник каждого утверждения в скобках [Имя_файла.docx].
2. Детектор противоречий: Если в разных статьях или экспериментах указаны разные оптимальные значения (например, разная скорость потока католита или разные температуры выщелачивания), ОБЯЗАТЕЛЬНО выдели отдельный абзац с заголовком:
"⚠️ ЗОНА РАЗНОГЛАСИЙ В ДАННЫХ:" и опиши, какие источники противоречат друг другу.
3. Если данных в контексте недостаточно, прямо скажи об этом (это индикатор "белого пятна").
"""

class RAGEngine:
    def __init__(self):
        self.collection_name = "nornickel_knowledge"

    def search_vector(self, query: str, limit: int = 5, filters: dict = None):
        """
        Поиск похожих документов в ChromaDB по вектору запроса
        """
        try:
            # Сначала генерируем эмбеддинг запроса
            query_vector = yandex_ai.get_embedding(query, "text-search-query")
            # Выполняем запрос к ChromaDB
            results = chroma_client.query_collection(
                collection_name=self.collection_name,
                query_embeddings=[query_vector],
                n_results=limit,
                where=filters
            )
            # Приводим к структурированному виду списка словарей
            formatted = []
            if results and results.get("documents") and results["documents"]:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
                ids = results["ids"][0] if results.get("ids") else []
                for i in range(len(documents)):
                    formatted.append({
                        "id": ids[i] if i < len(ids) else f"chunk_{i}",
                        "text": documents[i],
                        "metadata": metadatas[i]
                    })
            return formatted
        except Exception as e:
            print(f"Ошибка поиска в ChromaDB: {e}")
            return []

    def search_graph(self, query: str):
        """
        Поиск связанных сущностей, параметров и экспертов в Neo4j
        """
        # Разбиваем запрос на отдельные слова (длиной > 3 символов) для поиска в Neo4j
        words = [w.strip() for w in re.split(r'\W+', query) if len(w.strip()) > 3]
        if not words:
            # Если слов нет, попробуем поискать по всему запросу
            words = [query]
            
        results = []
        for word in words:
            # Находим узлы, содержащие слово, и их непосредственные связи
            cypher_query = """
            MATCH (s:Entity)-[r]->(t:Entity)
            WHERE toLower(s.name) CONTAINS toLower($word) OR toLower(t.name) CONTAINS toLower($word)
            RETURN s.name AS source, s.type AS source_type, t.name AS target, t.type AS target_type, type(r) AS relationship, r.source_file AS source_file, r.year AS year
            LIMIT 15
            """
            try:
                res = neo4j_client.execute_query(cypher_query, {"word": word})
                results.extend(res)
            except Exception as e:
                print(f"Ошибка поиска в Neo4j для слова '{word}': {e}")
                
        # Дедупликация по уникальным связям
        seen = set()
        dedup_results = []
        for item in results:
            key = (item.get("source"), item.get("relationship"), item.get("target"))
            if key not in seen:
                seen.add(key)
                dedup_results.append(item)
        return dedup_results[:30]

    def answer_question(self, query: str, filters: dict = None) -> dict:
        """
        Гибридный поиск (ChromaDB + Neo4j) и генерация ответа через YandexGPT Pro
        """
        # 1. Поиск в векторной базе
        vector_results = self.search_vector(query, limit=5, filters=filters)
        
        # 2. Поиск в графе знаний
        graph_results = self.search_graph(query)
        
        # 3. Формирование контекста
        context = "Контекст из векторного индекса:\n"
        if vector_results:
            for idx, res in enumerate(vector_results):
                source_name = res["metadata"].get("source", "неизвестный источник")
                context += f"[{idx+1}] (Источник: {source_name}) {res['text']}\n"
        else:
            context += "[Нет данных в векторном индексе]\n"
            
        context += "\nПараметры и онтология связей из графа знаний Neo4j:\n"
        if graph_results:
            for r in graph_results:
                context += f"- ({r['source']}:{r['source_type']}) -[:{r['relationship']}]-> ({r['target']}:{r['target_type']}) [Источник: {r.get('source_file')}, Год: {r.get('year')}]\n"
        else:
            context += "[Нет данных в графе знаний]\n"

        user_prompt = f"Вопрос пользователя: {query}\n\nКонтекст для ответа:\n{context}"
        
        try:
            answer = yandex_ai.generate_completion(SYSTEM_PROMPT, user_prompt, model="yandexgpt")
        except Exception as e:
            answer = f"Ошибка генерации ответа через Yandex AI: {e}"

        return {
            "query": query,
            "answer": answer,
            "sources": vector_results,
            "subgraph": graph_results
        }

rag_engine = RAGEngine()

