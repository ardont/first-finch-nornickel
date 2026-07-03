import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🚀 Скрипт запуска парсинга и заливки данных в базы (Ingestion Pipeline)")
    print("=======================================================================")
    print("Инициализация...")
    
    # В будущем здесь будет вызов парсера и клиентов Neo4j/ChromaDB
    raw_dir = os.path.join("data", "raw")
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)
        print(f"Создана директория для исходных файлов: {raw_dir}")
        
    print("\n[Внимание] Логика парсинга и импорта будет добавлена на следующем этапе разработки.")
    print("Пожалуйста, убедитесь, что тест подключения (scripts/test_cluster.py) проходит успешно.")

if __name__ == "__main__":
    main()
