from neo4j import GraphDatabase
from app.core.config import settings

SYNONYMS_MAP = {
    # Штейн и драгметаллы
    "МПГ": "Металлы платиновой группы",
    "ПГМ": "Металлы платиновой группы",
    "PGM": "Металлы платиновой группы",
    "АУ": "Золото",
    "AU": "Золото",
    "АГ": "Серебро",
    "AG": "Серебро",
    # Металлургия
    "ELECTROWINNING": "Электроэкстракция",
    "ПВП": "Печь взвешенной плавки",
    "FLUIDIZED BED FURNACE": "Печь взвешенной плавки"
}

ALLOWED_RELATIONS = {"USES_MATERIAL", "OPERATES_AT_CONDITION", "PRODUCES_OUTPUT", "DESCRIBED_IN", "VALIDATED_BY", "CONFLICTS", "RELATED_TO"}

class Neo4jClient:
    def __init__(self):
        self.uri = f"bolt://{settings.NEO4J_HOST}:{settings.NEO4J_PORT}"
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.driver = None

    def clear_database(self):
        driver = self.connect()
        query = "MATCH (n) DETACH DELETE n"
        with driver.session() as session:
            session.run(query)
        print("🧹 Граф Neo4j успешно очищен.")

    def connect(self):
        if not self.driver:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Создаем базовые индексы / ограничения
            try:
                self.setup_constraints()
            except Exception as e:
                print(f"Предупреждение при создании индексов: {e}")
        return self.driver

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    def verify_connectivity(self):
        driver = self.connect()
        driver.verify_connectivity()
        return True

    def setup_constraints(self):
        # Ограничение уникальности имени сущности для ускорения MERGE
        query = "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE"
        with self.driver.session() as session:
            session.run(query)

    def normalize_name(self, name: str) -> str:
        if not name:
            return ""
        cleaned = name.strip().upper()
        return SYNONYMS_MAP.get(cleaned, name.strip().capitalize())

    def execute_query(self, query: str, parameters: dict = None):
        driver = self.connect()
        with driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def add_triplet(self, source: str, source_type: str, target: str, target_type: str, relationship: str, metadata: dict):
        self.connect()
        source = self.normalize_name(source)
        target = self.normalize_name(target)
        
        # Защита от Cypher-инъекций и галлюцинаций LLM
        rel_type = relationship.strip().upper()
        if rel_type not in ALLOWED_RELATIONS:
            rel_type = "RELATED_TO"
            
        # Защита меток типов от некорректных символов
        source_type = "".join([c for c in source_type if c.isalnum()]) or "Entity"
        target_type = "".join([c for c in target_type if c.isalnum()]) or "Entity"

        # Шаблон безопасного Cypher-запроса
        query = f"""
        MERGE (s:Entity {{name: $source}})
        ON CREATE SET s.type = $source_type
        WITH s
        CALL apoc.create.addLabels(s, [$source_type]) YIELD node as sNode
        MERGE (t:Entity {{name: $target}})
        ON CREATE SET t.type = $target_type
        WITH sNode, t
        CALL apoc.create.addLabels(t, [$target_type]) YIELD node as tNode
        MERGE (sNode)-[r:{rel_type}]->(tNode)
        SET r.source_file = $source_file, r.year = $year
        RETURN r
        """
        
        # Fallback без использования APOC для стандартного community-образа
        fallback_query = f"""
        MERGE (s:Entity {{name: $source}})
        ON CREATE SET s.type = $source_type
        MERGE (t:Entity {{name: $target}})
        ON CREATE SET t.type = $target_type
        WITH s, t
        MERGE (s)-[r:{rel_type}]->(t)
        SET r.source_file = $source_file, r.year = $year
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                session.run(fallback_query, 
                            source=source, 
                            source_type=source_type, 
                            target=target, 
                            target_type=target_type, 
                            source_file=metadata.get("source", "unknown"), 
                            year=int(metadata.get("year", 2023)))
        except Exception as e:
            print(f"Ошибка при сохранении триплета: {e}")

neo4j_client = Neo4jClient()

