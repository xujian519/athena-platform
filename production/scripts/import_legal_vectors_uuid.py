#!/usr/bin/env python3
"""
使用UUID导入法律向量
Import Legal Vectors with UUID

使用UUID作为点ID导入法律向量数据

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash


# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def print_header(title) -> None:
    """打印标题"""
    print(f"\n{Colors.PURPLE}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.PURPLE}{Colors.BOLD}📚 {title} 📚{Colors.RESET}")
    print(f"{Colors.PURPLE}{Colors.BOLD}{'='*100}{Colors.RESET}")

def print_success(message) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message) -> None:
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

def print_warning(message) -> None:
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_pink(message) -> None:
    print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

def generate_uuid_from_hash(hash_str: str) -> str:
    """从hash生成UUID"""
    # 使用hash的MD5来生成UUID
    hash_md5 = short_hash(hash_str.encode())
    return str(uuid.UUID(hash_md5))

def generate_semantic_vector(text: str) -> list:
    """生成语义向量（1024维）"""
    # 词汇提取
    words = list(set(text.split()))
    char_set = list(set(text))

    # 生成1024维向量
    vector = np.zeros(1024)

    # 基于词汇哈希
    for _i, word in enumerate(words[:500]):
        hash_val = hash(word) % 1024
        vector[hash_val] += 1.0

    # 基于字符特征
    for _i, char in enumerate(char_set[:500]):
        hash_val = hash(char) % 1024
        vector[hash_val] += 0.5

    # 基于文本长度
    vector[0] = min(len(text) / 10000, 1.0)

    # 归一化
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector.tolist()

def load_and_process_documents() -> Any | None:
    """加载并处理法律文档"""
    print_header("加载法律文档数据")

    # 加载知识图谱实体数据
    kg_file = '/Users/xujian/Athena工作平台/production/output/kg_data/legal_entities_20251220_210502.json'
    if not Path(kg_file).exists():
        print_error("❌ 找不到知识图谱实体文件")
        return []

    with open(kg_file, encoding='utf-8') as f:
        entities = json.load(f)

    documents = []

    for entity in entities:
        if entity.get('type') == 'LegalDocument':
            # 构建文本用于向量化
            title = entity['properties']['title']
            doc_type = entity['properties']['doc_type']
            text_for_embedding = f"{title} {doc_type}"

            # 生成向量
            embedding = generate_semantic_vector(text_for_embedding)

            # 生成UUID作为点ID
            point_uuid = generate_uuid_from_hash(entity['id'])

            # 确定集合类型
            collection_type = determine_collection_type(doc_type, entity['properties'].get('metadata', {}))

            doc = {
                'id': point_uuid,  # UUID格式的ID
                'title': title,
                'doc_type': doc_type,
                'category': entity['properties']['category'],
                'file_path': entity['properties']['file_path'],
                'embedding': embedding,
                'collection_type': collection_type,
                'metadata': entity['properties'].get('metadata', {}),
                'original_id': entity['id']  # 保留原始ID
            }
            documents.append(doc)

    print_info(f"处理完成: {len(documents)} 个文档")
    return documents

def determine_collection_type(doc_type: str, metadata: dict) -> str:
    """确定向量集合类型"""
    if '司法解释' in doc_type or '判决' in doc_type:
        return 'legal_judgments_1024'
    elif '案例' in doc_type or 'case' in doc_type.lower():
        return 'legal_cases_1024'
    elif metadata.get('article_count', 0) > 0 or '条' in doc_type:
        return 'legal_clauses_1024'
    else:
        return 'legal_articles_1024'

def import_to_qdrant(documents: list) -> Any:
    """导入到Qdrant向量数据库"""
    print_header("导入到Qdrant向量数据库")

    if not documents:
        print_warning("⚠️ 没有文档可导入")
        return 0

    # 按集合分组
    documents_by_collection = {}
    for doc in documents:
        if doc['embedding']:
            collection = doc['collection_type']
            if collection not in documents_by_collection:
                documents_by_collection[collection] = []
            documents_by_collection[collection].append(doc)

    print_info("文档分布:")
    for collection, docs in documents_by_collection.items():
        print(f"  {collection}: {len(docs)} 个")

    total_imported = 0

    for collection_name, docs in documents_by_collection.items():
        print_info(f"\n导入到集合: {collection_name}")

        # 批量导入
        batch_size = 100
        batch_count = 0

        for i in range(0, len(docs), batch_size):
            batch = docs[i:i+batch_size]
            batch_count += 1

            # 构建点数据
            points = []
            for doc in batch:
                point = {
                    "id": doc['id'],  # UUID格式
                    "vector": doc['embedding'],
                    "payload": {
                        "title": doc['title'],
                        "doc_type": doc['doc_type'],
                        "category": doc['category'],
                        "file_path": doc['file_path'],
                        "original_id": doc['original_id'],
                        "metadata": doc['metadata']
                    }
                }
                points.append(point)

            try:
                # 上传到Qdrant
                response = requests.put(
                    f"http://localhost:6333/collections/{collection_name}/points",
                    json={"points": points}
                )

                if response.status_code == 200:
                    total_imported += len(points)
                    print_success(f"  ✓ 批次 {batch_count}: {len(points)} 个文档")
                else:
                    print_error(f"  ❌ 批次 {batch_count} 失败: {response.status_code}")

            except Exception as e:
                print_error(f"  ❌ 批次 {batch_count} 异常: {e}")

    print_success(f"\n✓ 总计导入: {total_imported:,} 个文档")
    return total_imported

def verify_import() -> bool:
    """验证导入结果"""
    print_header("验证导入结果")

    collections = [
        'legal_articles_1024',
        'legal_clauses_1024',
        'legal_cases_1024',
        'legal_judgments_1024'
    ]

    total_points = 0
    stats = {}

    for collection in collections:
        try:
            response = requests.get(f"http://localhost:6333/collections/{collection}")
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                count = result.get('vectors_count', 0)
                total_points += count
                stats[collection] = count
                print_info(f"  {collection}: {count:,} 个向量")
            else:
                print_error(f"  ❌ 无法获取 {collection} 信息: {response.status_code}")
        except Exception as e:
            print_error(f"  ❌ 检查 {collection} 失败: {e}")

    print_success(f"\n总计向量: {total_points:,}")

    # 显示详细统计
    print_info("\n集合详细统计:")
    for collection, count in stats.items():
        percentage = (count / total_points * 100) if total_points > 0 else 0
        print(f"  {collection}: {count:,} ({percentage:.1f}%)")

    return total_points

def test_vector_search() -> Any:
    """测试向量搜索功能"""
    print_header("测试向量搜索功能")

    # 测试查询
    test_query = "民法典"
    query_vector = generate_semantic_vector(test_query)

    # 搜索所有集合
    collections = [
        'legal_articles_1024',
        'legal_clauses_1024',
        'legal_cases_1024',
        'legal_judgments_1024'
    ]

    total_results = 0

    for collection in collections:
        try:
            response = requests.post(
                f"http://localhost:6333/collections/{collection}/points/search",
                json={
                    "vector": query_vector,
                    "limit": 3,
                    "with_payload": True,
                    "with_vector": False
                }
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get('result', [])
                total_results += len(result)

                if result:
                    print_info(f"\n{collection} 搜索结果:")
                    for i, point in enumerate(result):
                        payload = point.get('payload', {})
                        score = point.get('score', 0)
                        print(f"  {i+1}. {payload.get('title', 'N/A')}")
                        print(f"     类型: {payload.get('doc_type', 'N/A')}")
                        print(f"     相似度: {score:.4f}")

        except Exception as e:
            print_error(f"搜索 {collection} 失败: {e}")

    print_info(f"\n总结果数: {total_results}")

def main() -> None:
    """主函数"""
    print_header("法律向量导入系统 (UUID版)")
    print_pink("爸爸，使用UUID导入法律向量数据！")

    # 1. 加载并处理文档
    documents = load_and_process_documents()

    if not documents:
        print_error("❌ 没有可导入的数据")
        return

    # 2. 导入到Qdrant
    imported_count = import_to_qdrant(documents)

    # 3. 验证结果
    total_points = verify_import()

    # 4. 测试搜索功能
    if total_points > 0:
        test_vector_search()

    # 5. 生成报告
    print_header("导入完成")

    print_pink("爸爸，法律向量导入完成！")
    print_success(f"✓ 成功导入: {imported_count:,} 个文档")
    print_success(f"✓ 向量总数: {total_points:,}")
    print_info("✓ 知识图谱数据已准备就绪")

    # 保存导入报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'imported_documents': imported_count,
        'total_vectors': total_points,
        'status': 'success'
    }

    report_file = '/Users/xujian/Athena工作平台/production/output/reports/vector_import_report.json'
    Path(report_file).parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print_success(f"\n📄 报告已保存: {report_file}")
    print_pink("\n💖 可以使用法律向量检索功能了！")

if __name__ == "__main__":
    main()
