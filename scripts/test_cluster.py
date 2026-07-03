import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase
import chromadb

load_dotenv()

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
NEO4J_HOST = os.getenv("NEO4J_HOST")
NEO4J_PORT = os.getenv("NEO4J_PORT")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = os.getenv("CHROMA_PORT")

print("==================================================")
print("🚀 ЗАПУСК СКВОЗНОЙ ПРОВЕРКИ КЛАСТЕРА FIRST FINCH")
print("==================================================\n")

# 1. ПРОВЕРКА YANDEX AI STUDIO (Эмбеддинги)
print("[1/3] Проверка Yandex AI Studio (Embeddings API)...")
try:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}", "x-folder-id": YANDEX_FOLDER_ID}
    payload = {
        "modelUri": f"emb://{YANDEX_FOLDER_ID}/text-search-doc/latest",
        "text": "Тестовый запрос Норникель"
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=5)
    resp.raise_for_status()
    vec_len = len(resp.json()["embedding"])
    print(f"  ✅ Успешно! Облако вернуло вектор размером: {vec_len}\n")
except Exception as e:
    print(f"  ❌ Ошибка подключения к Yandex AI: {e}\n")

# 2. ПРОВЕРКА NEO4J
print(f"[2/3] Проверка удаленного Neo4j на {NEO4J_HOST}:{NEO4J_PORT}...")
try:
    uri = f"bolt://{NEO4J_HOST}:{NEO4J_PORT}"
    driver = GraphDatabase.driver(uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print(f"  ✅ Успешно! Ноут Neo4j ({NEO4J_HOST}) готов принимать графы.\n")
    driver.close()
except Exception as e:
    print(f"  ❌ Ошибка подключения к Neo4j: {e}\n")

# 3. ПРОВЕРКА CHROMADB
print(f"[3/3] Проверка удаленного ChromaDB на {CHROMA_HOST}:{CHROMA_PORT}...")
try:
    client = chromadb.HttpClient(host=CHROMA_HOST, port=int(CHROMA_PORT))
    heartbeat = client.heartbeat()
    # Создадим и удалим тестовую коллекцию
    coll = client.get_or_create_collection("test_heartbeat")
    client.delete_collection("test_heartbeat")
    print(f"  ✅ Успешно! Ноут ChromaDB ({CHROMA_HOST}) готов принимать векторы (heartbeat: {heartbeat}).\n")
except Exception as e:
    print(f"  ❌ Ошибка подключения к ChromaDB: {e}\n")

print("==================================================")
print("🏁 ПРОВЕРКА ЗАВЕРШЕНА!")
print("==================================================")
