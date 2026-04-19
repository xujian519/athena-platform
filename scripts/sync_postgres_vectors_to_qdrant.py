#!/usr/bin/env python3
"""
PostgreSQL向量数据 → Qdrant同步脚本（修复版）
Sync PostgreSQL vector embeddings to Qdrant (Fixed Version)

处理PostgreSQL中存储为JSON字符串的向量数据
"""

import psycopg2
import numpy as np
import requests
import time
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import Any

load_dotenv()

# PostgreSQL配置
PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "postgres"
PG_PASSWORD = "athena_dev_password_2024_secure"
PG_DATABASE = "legal_world_model"

# Qdrant配置
QDRANT_URL = "http://localhost:6333"

# 批量大小
BATCH_SIZE = 500

def log(msg: str):
    """日志输出"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_vector(vec: Any) -> list:
    """解析向量数据（支持JSON字符串和列表）"""
    if isinstance(vec, str):
        # JSON字符串
        return json.loads(vec)
    elif isinstance(vec, (list, tuple)):
        # 已经是列表
        return list(vec)
    elif hasattr(vec, 'tolist'):
        # numpy数组
        return vec.tolist()
    else:
        # 其他类型，尝试转换
        return list(vec)


def create_qdrant_collection(collection_name: str, vector_size: int = 1024):
    """创建Qdrant集合"""
    log(f"检查集合: {collection_name}")

    # 检查集合是否存在
    response = requests.get(f"{QDRANT_URL}/collections/{collection_name}")
    if response.status_code == 200:
        info = response.json()["result"]
        config_size = info["config"]["params"]["vectors"]["size"]
        points_count = info["points_count"]
        log(f"  ✅ 集合已存在（维度: {config_size}, 数据: {points_count:,}）")
        return True, points_count

    # 创建集合
    log(f"  创建集合（向量维度: {vector_size}）...")
    response = requests.put(f"{QDRANT_URL}/collections/{collection_name}", json={
        "vectors": {
            "size": vector_size,
            "distance": "Cosine"
        },
        "optimizers_config": {
            "indexing_threshold": 20000
        },
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100
        }
    })

    if response.status_code == 200:
        log(f"  ✅ 集合创建成功")
        return True, 0
    else:
        log(f"  ❌ 集合创建失败: {response.text}")
        return False, 0


def sync_legal_articles_vectors():
    """同步法律条文向量"""
    collection_name = "legal_articles_v2"

    log(f"\n{'='*80}")
    log(f"同步法律条文向量: legal_articles_v2_embeddings")
    log(f"{'='*80}\n")

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=PG_PASSWORD, dbname=PG_DATABASE
    )
    cursor = conn.cursor()

    # 检查总数
    cursor.execute("SELECT COUNT(*) FROM legal_articles_v2_embeddings")
    total_count = cursor.fetchone()[0]
    log(f"总记录数: {total_count:,}")

    # 检查向量维度
    cursor.execute("SELECT vector FROM legal_articles_v2_embeddings LIMIT 1")
    sample = cursor.fetchone()
    if sample and sample[0]:
        vec = parse_vector(sample[0])
        vector_size = len(vec)
        log(f"向量维度: {vector_size}")
        del vec
    else:
        log("❌ 无法获取向量维度")
        conn.close()
        return 0

    # 创建集合
    success, existing = create_qdrant_collection(collection_name, vector_size)
    if not success:
        conn.close()
        return 0

    if existing >= total_count * 0.95:  # 95%以上就算完成
        log(f"⏭️ 数据已基本完整（{existing:,}条），跳过")
        conn.close()
        return existing

    # 开始同步
    log(f"开始同步（批量大小: {BATCH_SIZE}）...")

    cursor.execute("""
        SELECT id, article_id, chunk_type, chunk_text, vector
        FROM legal_articles_v2_embeddings
        ORDER BY id
    """)

    imported = 0
    batch = []
    t0 = time.time()

    for row in cursor:
        id_val, article_id, chunk_type, chunk_text, vec_str = row

        # 解析向量
        try:
            vector = parse_vector(vec_str)
        except Exception as e:
            log(f"  ⚠️  向量解析失败 (ID={id_val}): {e}")
            continue

        # 构建payload
        payload = {
            "article_id": article_id,
            "chunk_type": chunk_type,
            "chunk_text": (chunk_text or "")[:500]
        }

        # 生成唯一ID
        point_id = hash(f"legal_articles_{id_val}") % (2**63)

        batch.append({
            "id": point_id,
            "vector": vector,
            "payload": payload
        })

        if len(batch) >= BATCH_SIZE:
            # 上传批次
            response = requests.put(
                f"{QDRANT_URL}/collections/{collection_name}/points",
                json={"points": batch},
                timeout=60
            )

            if response.status_code != 200:
                log(f"  ❌ 批次上传失败: {response.status_code} - {response.text}")

            imported += len(batch)
            batch = []

            # 进度报告
            if imported % 5000 == 0 or imported >= total_count:
                elapsed = time.time() - t0
                speed = imported / elapsed if elapsed > 0 else 0
                remain = (total_count - imported) / speed if speed > 0 else 0
                log(f"  进度: {imported:,}/{total_count:,} ({speed:.0f}/s, 剩余{remain:.0f}s)")

    # 上传最后一批
    if batch:
        requests.put(
            f"{QDRANT_URL}/collections/{collection_name}/points",
            json={"points": batch},
            timeout=60
        )
        imported += len(batch)

    cursor.close()
    conn.close()

    elapsed = time.time() - t0
    log(f"✅ 完成! 导入: {imported:,}条, 耗时: {elapsed:.1f}秒")

    return imported


def sync_patent_invalid_vectors():
    """同步专利无效向量"""
    collection_name = "patent_invalid_embeddings"

    log(f"\n{'='*80}")
    log(f"同步专利无效向量: patent_invalid_embeddings")
    log(f"{'='*80}\n")

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=PG_PASSWORD, dbname=PG_DATABASE
    )
    cursor = conn.cursor()

    # 检查总数
    cursor.execute("SELECT COUNT(*) FROM patent_invalid_embeddings")
    total_count = cursor.fetchone()[0]
    log(f"总记录数: {total_count:,}")

    # 检查向量维度
    cursor.execute("SELECT vector FROM patent_invalid_embeddings LIMIT 1")
    sample = cursor.fetchone()
    if sample and sample[0]:
        vec = parse_vector(sample[0])
        vector_size = len(vec)
        log(f"向量维度: {vector_size}")
        del vec
    else:
        log("❌ 无法获取向量维度")
        conn.close()
        return 0

    # 创建集合
    success, existing = create_qdrant_collection(collection_name, vector_size)
    if not success:
        conn.close()
        return 0

    if existing >= total_count * 0.95:
        log(f"⏭️ 数据已基本完整（{existing:,}条），跳过")
        conn.close()
        return existing

    # 开始同步
    log(f"开始同步（批量大小: {BATCH_SIZE}）...")

    cursor.execute("""
        SELECT id, document_id, chunk_type, chunk_text, vector
        FROM patent_invalid_embeddings
        ORDER BY id
    """)

    imported = 0
    batch = []
    t0 = time.time()

    for row in cursor:
        id_val, document_id, chunk_type, chunk_text, vec_str = row

        try:
            vector = parse_vector(vec_str)
        except Exception as e:
            log(f"  ⚠️  向量解析失败 (ID={id_val}): {e}")
            continue

        payload = {
            "document_id": document_id,
            "chunk_type": chunk_type,
            "chunk_text": (chunk_text or "")[:500]
        }

        point_id = hash(f"patent_invalid_{id_val}") % (2**63)

        batch.append({
            "id": point_id,
            "vector": vector,
            "payload": payload
        })

        if len(batch) >= BATCH_SIZE:
            response = requests.put(
                f"{QDRANT_URL}/collections/{collection_name}/points",
                json={"points": batch},
                timeout=60
            )

            imported += len(batch)
            batch = []

            if imported % 5000 == 0 or imported >= total_count:
                elapsed = time.time() - t0
                speed = imported / elapsed if elapsed > 0 else 0
                remain = (total_count - imported) / speed if speed > 0 else 0
                log(f"  进度: {imported:,}/{total_count:,} ({speed:.0f}/s, 剩余{remain:.0f}s)")

    if batch:
        requests.put(
            f"{QDRANT_URL}/collections/{collection_name}/points",
            json={"points": batch},
            timeout=60
        )
        imported += len(batch)

    cursor.close()
    conn.close()

    elapsed = time.time() - t0
    log(f"✅ 完成! 导入: {imported:,}条, 耗时: {elapsed:.1f}秒")

    return imported


def sync_judgment_vectors():
    """同步判决向量"""
    collection_name = "judgment_embeddings"

    log(f"\n{'='*80}")
    log(f"同步判决向量: judgment_embeddings")
    log(f"{'='*80}\n")

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=PG_PASSWORD, dbname=PG_DATABASE
    )
    cursor = conn.cursor()

    # 检查总数
    cursor.execute("SELECT COUNT(*) FROM judgment_embeddings")
    total_count = cursor.fetchone()[0]
    log(f"总记录数: {total_count:,}")

    # 检查向量维度
    cursor.execute("SELECT vector FROM judgment_embeddings LIMIT 1")
    sample = cursor.fetchone()
    if sample and sample[0]:
        vec = parse_vector(sample[0])
        vector_size = len(vec)
        log(f"向量维度: {vector_size}")
        del vec
    else:
        log("❌ 无法获取向量维度")
        conn.close()
        return 0

    # 创建集合
    success, existing = create_qdrant_collection(collection_name, vector_size)
    if not success:
        conn.close()
        return 0

    if existing >= total_count * 0.95:
        log(f"⏭️ 数据已基本完整（{existing:,}条），跳过")
        conn.close()
        return existing

    # 开始同步
    log(f"开始同步（批量大小: {BATCH_SIZE}）...")

    cursor.execute("""
        SELECT id, judgment_id, content_type, text_content, vector
        FROM judgment_embeddings
        ORDER BY id
    """)

    imported = 0
    batch = []
    t0 = time.time()

    for row in cursor:
        id_val, judgment_id, content_type, text_content, vec_str = row

        try:
            vector = parse_vector(vec_str)
        except Exception as e:
            log(f"  ⚠️  向量解析失败 (ID={id_val}): {e}")
            continue

        payload = {
            "judgment_id": judgment_id,
            "content_type": content_type,
            "text_content": (text_content or "")[:500]
        }

        point_id = hash(f"judgment_{id_val}") % (2**63)

        batch.append({
            "id": point_id,
            "vector": vector,
            "payload": payload
        })

        if len(batch) >= BATCH_SIZE:
            response = requests.put(
                f"{QDRANT_URL}/collections/{collection_name}/points",
                json={"points": batch},
                timeout=60
            )

            imported += len(batch)
            batch = []

            if imported % 5000 == 0 or imported >= total_count:
                elapsed = time.time() - t0
                speed = imported / elapsed if elapsed > 0 else 0
                remain = (total_count - imported) / speed if speed > 0 else 0
                log(f"  进度: {imported:,}/{total_count:,} ({speed:.0f}/s, 剩余{remain:.0f}s)")

    if batch:
        requests.put(
            f"{QDRANT_URL}/collections/{collection_name}/points",
            json={"points": batch},
            timeout=60
        )
        imported += len(batch)

    cursor.close()
    conn.close()

    elapsed = time.time() - t0
    log(f"✅ 完成! 导入: {imported:,}条, 耗时: {elapsed:.1f}秒")

    return imported


def sync_patent_judgment_vectors():
    """同步专利判决向量"""
    collection_name = "patent_judgment_vectors"

    log(f"\n{'='*80}")
    log(f"同步专利判决向量: patent_judgment_vectors")
    log(f"{'='*80}\n")

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=PG_PASSWORD, dbname=PG_DATABASE
    )
    cursor = conn.cursor()

    # 检查总数
    cursor.execute("SELECT COUNT(*) FROM patent_judgment_vectors")
    total_count = cursor.fetchone()[0]
    log(f"总记录数: {total_count:,}")

    # 检查向量维度
    cursor.execute("SELECT vector FROM patent_judgment_vectors LIMIT 1")
    sample = cursor.fetchone()
    if sample and sample[0]:
        vec = parse_vector(sample[0])
        vector_size = len(vec)
        log(f"向量维度: {vector_size}")
        del vec
    else:
        log("❌ 无法获取向量维度")
        conn.close()
        return 0

    # 创建集合
    success, existing = create_qdrant_collection(collection_name, vector_size)
    if not success:
        conn.close()
        return 0

    if existing >= total_count * 0.95:
        log(f"⏭️ 数据已基本完整（{existing:,}条），跳过")
        conn.close()
        return existing

    # 开始同步
    log(f"开始同步（批量大小: {BATCH_SIZE}）...")

    cursor.execute("""
        SELECT id, case_id, content_type, text_content, vector
        FROM patent_judgment_vectors
        ORDER BY id
    """)

    imported = 0
    batch = []
    t0 = time.time()

    for row in cursor:
        id_val, case_id, content_type, text_content, vec_str = row

        try:
            vector = parse_vector(vec_str)
        except Exception as e:
            log(f"  ⚠️  向量解析失败 (ID={id_val}): {e}")
            continue

        payload = {
            "case_id": case_id,
            "content_type": content_type,
            "text_content": (text_content or "")[:500]
        }

        point_id = hash(f"patent_judgment_{id_val}") % (2**63)

        batch.append({
            "id": point_id,
            "vector": vector,
            "payload": payload
        })

        if len(batch) >= BATCH_SIZE:
            response = requests.put(
                f"{QDRANT_URL}/collections/{collection_name}/points",
                json={"points": batch},
                timeout=60
            )

            imported += len(batch)
            batch = []

            if imported % 5000 == 0 or imported >= total_count:
                elapsed = time.time() - t0
                speed = imported / elapsed if elapsed > 0 else 0
                remain = (total_count - imported) / speed if speed > 0 else 0
                log(f"  进度: {imported:,}/{total_count:,} ({speed:.0f}/s, 剩余{remain:.0f}s)")

    if batch:
        requests.put(
            f"{QDRANT_URL}/collections/{collection_name}/points",
            json={"points": batch},
            timeout=60
        )
        imported += len(batch)

    cursor.close()
    conn.close()

    elapsed = time.time() - t0
    log(f"✅ 完成! 导入: {imported:,}条, 耗时: {elapsed:.1f}秒")

    return imported


def main():
    """主函数"""
    log("="*80)
    log("PostgreSQL向量数据 → Qdrant同步（修复版）")
    log("="*80)
    log(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    t0 = time.time()
    results = {}

    # 同步各类向量数据
    results["legal_articles_v2"] = sync_legal_articles_vectors()
    results["patent_invalid_embeddings"] = sync_patent_invalid_vectors()
    results["judgment_embeddings"] = sync_judgment_vectors()
    results["patent_judgment_vectors"] = sync_patent_judgment_vectors()

    # 总结
    total_elapsed = time.time() - t0
    total_imported = sum(results.values())

    log("\n" + "="*80)
    log("同步完成总结")
    log("="*80)

    for name, count in results.items():
        log(f"{name}: {count:,}条")

    log(f"\n总计导入: {total_imported:,}条")
    log(f"总耗时: {total_elapsed/60:.1f}分钟")
    log("="*80)

    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": total_elapsed,
        "results": results,
        "total_imported": total_imported
    }

    report_path = Path("reports/postgresql_qdrant_sync_report.json")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    log(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    main()
