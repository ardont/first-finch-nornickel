import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import uuid
import time
from app.services.parser import parser
from app.services.yandex_ai import yandex_ai
from app.db.chroma_client import chroma_client
from app.db.neo4j_client import neo4j_client

RAW_DATA_DIR = os.path.join("data", "raw")
CHROMA_COLLECTION = "nornickel_knowledge"

def extract_year(filename: str) -> int:
    # Ищем год от 1900 до 2029 в названии файла
    match = re.search(r'\b(19|20)\d{2}\b', filename)
    return int(match.group(0)) if match else 2023

def detect_geography(filename: str, content: str) -> str:
    # Проверка на кириллицу или специфические российские термины
    text_to_check = (filename + " " + content).lower()
    has_cyrillic = bool(re.search('[а-яА-Я]', text_to_check))
    nornickel_keywords = ["норильск", "кольский", "гипроникель", "рф", "гост", "гмк", "гнп", "никель", "ссср", "россия"]
    
    if has_cyrillic or any(k in text_to_check for k in nornickel_keywords):
        return "RU"
    return "GLOBAL"

def process_file(file_path: str):
    filename = os.path.basename(file_path)
    print(f"\n[Обработка] {filename}...")
    
    year = extract_year(filename)
    
    try:
        text, table_facts = parser.parse_file(file_path)
    except Exception as e:
        print(f"  ❌ Ошибка парсинга {filename}: {e}")
        return
        
    combined_content = text + " " + " ".join(table_facts)
    geography = detect_geography(filename, combined_content)
    
    metadata = {
        "source": filename,
        "year": year,
        "geography": geography,
        "confidentiality": "public"  # по умолчанию ставим public
    }
    
    chunks_processed = 0
    triplets_processed = 0
    
    # 1. Импорт текстового содержимого
    if text.strip():
        chunks = parser.chunk_text(text)
        print(f"  Разбито на {len(chunks)} текстовых чанков.")
        
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{filename}_chunk_{idx}"
            try:
                # Векторизация и запись в ChromaDB
                embedding = yandex_ai.get_embedding(chunk)
                chroma_client.add_documents(
                    collection_name=CHROMA_COLLECTION,
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[chunk_id]
                )
                chunks_processed += 1
                
                # Извлечение онтологии и запись в Neo4j
                triplets = yandex_ai.extract_ontology(chunk)
                for t in triplets:
                    if "source" in t and "target" in t and "relationship" in t:
                        neo4j_client.add_triplet(
                            source=t["source"],
                            source_type=t.get("source_type", "Entity"),
                            target=t["target"],
                            target_type=t.get("target_type", "Entity"),
                            relationship=t["relationship"],
                            metadata=metadata
                        )
                        triplets_processed += 1
                
                # Задержка для предотвращения лимитов 429
                time.sleep(0.15)
            except Exception as e:
                print(f"    ⚠️ Ошибка обработки чанка {idx}: {e}")
                
    # 2. Импорт табличных фактов (Excel)
    if table_facts:
        print(f"  Извлечено {len(table_facts)} фактов из таблицы.")
        for idx, fact in enumerate(table_facts):
            fact_id = f"{filename}_fact_{idx}_{uuid.uuid4().hex[:6]}"
            try:
                # Векторизация в ChromaDB
                embedding = yandex_ai.get_embedding(fact)
                chroma_client.add_documents(
                    collection_name=CHROMA_COLLECTION,
                    documents=[fact],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[fact_id]
                )
                chunks_processed += 1
                
                # Отправляем факт в LLM для извлечения триплетов
                triplets = yandex_ai.extract_ontology(fact)
                for t in triplets:
                    if "source" in t and "target" in t and "relationship" in t:
                        neo4j_client.add_triplet(
                            source=t["source"],
                            source_type=t.get("source_type", "Entity"),
                            target=t["target"],
                            target_type=t.get("target_type", "Entity"),
                            relationship=t["relationship"],
                            metadata=metadata
                        )
                        triplets_processed += 1
                
                # Задержка для предотвращения лимитов 429
                time.sleep(0.15)
            except Exception as e:
                print(f"    ⚠️ Ошибка обработки факта {idx}: {e}")
                
    print(f"  ✅ Завершено! Успешно загружено чанков: {chunks_processed}, связей добавлено в граф: {triplets_processed}")

def main():
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        print(f"Создана директория для исходных файлов: {RAW_DATA_DIR}")
        print("Положите туда документы и запустите скрипт повторно.")
        return
        
    # Рекурсивный поиск файлов во всех поддиректориях
    files = []
    for root, _, filenames in os.walk(RAW_DATA_DIR):
        for filename in filenames:
            # Игнорируем .gitkeep и временные файлы Office (начинающиеся с ~$)
            if filename != ".gitkeep" and not filename.startswith("~$"):
                files.append(os.path.join(root, filename))
                
    if not files:
        print(f"В папке {RAW_DATA_DIR} нет файлов для обработки.")
        return
        
    print(f"Найдено {len(files)} файлов для импорта (включая поддиректории).")
    
    # Инициализация клиентов баз данных
    try:
        neo4j_client.connect()
        chroma_client.heartbeat()
    except Exception as e:
        print(f"❌ Ошибка подключения к базам данных перед импортом: {e}")
        return
        
    # Автоматическая очистка графа Neo4j перед новым импортом
    try:
        neo4j_client.clear_database()
        print("🧹 Граф Neo4j успешно очищен.")
    except Exception as e:
        print(f"⚠️ Не удалось автоматически очистить Neo4j: {e}")
        
    # Автоматическое удаление старой коллекции ChromaDB перед импортом
    try:
        print(f"🧹 Удаление старой коллекции ChromaDB '{CHROMA_COLLECTION}'...")
        chroma_client.delete_collection(CHROMA_COLLECTION)
        print("  ✅ Коллекция ChromaDB успешно удалена (будет воссоздана с новой размерностью).")
    except Exception as e:
        print(f"⚠️ Не удалось удалить коллекцию ChromaDB: {e} (возможно, она не существовала)")
        
    for file in files:
        process_file(file)
        
    print("\n🏁 Импорт полностью завершен!")

if __name__ == "__main__":
    main()

