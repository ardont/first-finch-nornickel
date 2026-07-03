from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.db.neo4j_client import neo4j_client
from app.db.chroma_client import chroma_client
from app.services.yandex_ai import yandex_ai
from app.services.rag_engine import rag_engine

app = FastAPI(title="Nornickel GraphRAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    geography: str = "all"
    year_from: int = None
    role: str = "researcher"

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list
    subgraph: list

@app.get("/health")
def health_check():
    health = {
        "status": "healthy",
        "neo4j": "connected",
        "chromadb": "connected",
        "yandex_ai": "connected"
    }
    
    # 1. Проверка Neo4j
    try:
        neo4j_client.verify_connectivity()
    except Exception as e:
        health["neo4j"] = f"error: {str(e)}"
        health["status"] = "degraded"
        
    # 2. Проверка ChromaDB
    try:
        chroma_client.heartbeat()
    except Exception as e:
        health["chromadb"] = f"error: {str(e)}"
        health["status"] = "degraded"
        
    # 3. Проверка Yandex AI (быстрый эмбеддинг-тест)
    try:
        yandex_ai.get_embedding("тест")
    except Exception as e:
        health["yandex_ai"] = f"error: {str(e)}"
        health["status"] = "degraded"
        
    return health

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    filters = {}
    if request.geography != "all":
        filters["geography"] = request.geography
    if request.year_from:
        filters["year"] = {"$gte": request.year_from}
        
    # Ролевая модель ИБ
    if request.role == "partner":
        filters["confidentiality"] = "public"
        
    try:
        result = rag_engine.answer_question(request.query, filters=filters)
        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            sources=result["sources"] if result["sources"] else [],
            subgraph=result["subgraph"] if result["subgraph"] else []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки RAG: {str(e)}")
