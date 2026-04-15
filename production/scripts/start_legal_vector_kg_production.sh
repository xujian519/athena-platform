#!/bin/bash
# 法律向量库+知识图谱服务
cd "/Users/xujian/Athena工作平台"
echo "🚀 启动法律向量库+知识图谱服务..."

# 法律向量库API (8010)
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
    return {'status': 'healthy', 'service': 'legal_vector_db', 'collections': service.qdrant_collections}

@app.get('/search')
def search(query: str, limit: int = 10):
    return service.hybrid_search(query, search_type='vector_only', limit=limit)

@app.get('/statistics')
def statistics():
    return service.get_search_statistics()

@app.get('/collections')
def collections():
    return service.get_available_patent_collections()

uvicorn.run(app, host='0.0.0.0', port=8010)
" > production/logs/legal_vector_service.log 2>&1 &
echo $! > production/pids/legal_vector_service.pid
echo "✅ 法律向量库服务已启动 (端口: 8010)"

# 法律知识图谱API (8012)
sleep 2
python3 -c "
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')
import psycopg2
from fastapi import FastAPI
import uvicorn

app = FastAPI()
DB_CONFIG = {'host': 'localhost', 'port': 5432, 'database': 'patent_legal_db', 'user': 'xujian'}

@app.get('/health')
def health():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM legal_entities')
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {'status': 'healthy', 'service': 'legal_kg', 'entities': count}

@app.get('/entities')
def get_entities(limit: int = 100, entity_type: str = None):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    if entity_type:
        cur.execute('SELECT entity_text, entity_type, confidence FROM legal_entities WHERE entity_type = %s LIMIT %s', (entity_type, limit))
    else:
        cur.execute('SELECT entity_text, entity_type, confidence FROM legal_entities ORDER BY created_at DESC LIMIT %s', (limit,))
    results = [{'text': row[0], 'type': row[1], 'confidence': float(row[2])} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return results

@app.get('/relations')
def get_relations(limit: int = 100):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute('SELECT subject_entity, object_entity, relation_type, confidence FROM legal_relations ORDER BY created_at DESC LIMIT %s', (limit,))
    results = [{'subject': row[0], 'object': row[1], 'type': row[2], 'confidence': float(row[3])} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return results

uvicorn.run(app, host='0.0.0.0', port=8012)
" > production/logs/legal_kg_service.log 2>&1 &
echo $! > production/pids/legal_kg_service.pid
echo "✅ 法律知识图谱服务已启动 (端口: 8012)"

echo "🎉 法律服务启动完成！"
