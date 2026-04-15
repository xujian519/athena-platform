#!/bin/bash
# 专利规则向量库+知识图谱服务
cd "/Users/xujian/Athena工作平台"
echo "🚀 启动专利规则向量库+知识图谱服务..."

# 专利向量库API (8011)
python3 -c "
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')
from domains.patent_ai.services.patent_vector_search_service import PatentVectorSearchService
from fastapi import FastAPI
import uvicorn

app = FastAPI()
service = PatentVectorSearchService()

@app.get('/health')
def health():
    stats = service.get_search_statistics()
    return {'status': 'healthy', 'service': 'patent_vector_db', 'statistics': stats}

@app.get('/search')
def search(query: str, limit: int = 10, collection: str = 'patent_decisions'):
    return service.search_patent_vectors(query, collection_name=collection, limit=limit)

uvicorn.run(app, host='0.0.0.0', port=8011)
" > production/logs/patent_vector_service.log 2>&1 &
echo $! > production/pids/patent_vector_service.pid
echo "✅ 专利向量库服务已启动 (端口: 8011)"

# 专利知识图谱API (8013)
sleep 2
python3 -c '
import sys
sys.path.insert(0, "/Users/xujian/Athena工作平台")
import psycopg2
from fastapi import FastAPI
import uvicorn

app = FastAPI()
DB_CONFIG = {"host": "localhost", "port": 5432, "database": "patent_legal_db", "user": "xujian"}

@app.get("/health")
def health():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM legal_entities WHERE entity_type IN (%s, %s)", ("patent_number", "application_number"))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"status": "healthy", "service": "patent_kg", "patent_entities": count}

@app.get("/patent_entities")
def get_patent_entities(limit: int = 100):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT entity_text, entity_type, confidence FROM legal_entities WHERE entity_type IN (%s, %s, %s) ORDER BY created_at DESC LIMIT %s", ("patent_number", "application_number", "ipc_code", limit))
    results = [{"text": row[0], "type": row[1], "confidence": float(row[2])} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return results

uvicorn.run(app, host="0.0.0.0", port=8013)
' > production/logs/patent_kg_service.log 2>&1 &
echo $! > production/pids/patent_kg_service.pid
echo "✅ 专利知识图谱服务已启动 (端口: 8013)"

echo "🎉 专利服务启动完成！"
