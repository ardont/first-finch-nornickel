from neo4j import GraphDatabase
from app.core.config import settings

class Neo4jClient:
    def __init__(self):
        self.uri = f"bolt://{settings.NEO4J_HOST}:{settings.NEO4J_PORT}"
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.driver = None

    def connect(self):
        if not self.driver:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self.driver

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    def verify_connectivity(self):
        driver = self.connect()
        driver.verify_connectivity()
        return True

    def execute_query(self, query: str, parameters: dict = None):
        driver = self.connect()
        with driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

neo4j_client = Neo4jClient()
