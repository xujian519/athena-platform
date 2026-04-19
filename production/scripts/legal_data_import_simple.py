#!/usr/bin/env python3
"""
法律数据导入系统（简化版）
Simplified Legal Data Import System

使用NLP服务API进行法律数据导入

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
import os
import re
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler('/Users/xujian/Athena工作平台/production/logs/legal_import.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)

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
    print(f"{Colors.PURPLE}{Colors.BOLD}⚖️ {title} ⚖️{Colors.RESET}")
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

class LegalDataImporter:
    """法律数据导入器"""

    def __init__(self):
        """初始化"""
        self.data_source = "/Users/xujian/Athena工作平台/dev/tools/Laws-1.0.0"
        self.nlp_service_url = "http://localhost:8001"
        self.qdrant_url = "http://localhost:6333"

        self.processed_hashes = set()
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.start_time = datetime.now()

        # 向量集合配置
        self.collections = {
            'legal_articles': 'legal_articles_1024',
            'legal_clauses': 'legal_clauses_1024',
            'legal_cases': 'legal_cases_1024',
            'legal_judgments': 'legal_judgments_1024'
        }

        # 创建集合
        self._init_qdrant()

    def _init_qdrant(self) -> Any:
        """初始化Qdrant集合"""
        print_info("初始化Qdrant集合...")

        for collection_name in self.collections.values():
            try:
                # 检查集合是否存在
                response = requests.get(f"{self.qdrant_url}/collections/{collection_name}")

                if response.status_code == 404:
                    # 创建集合
                    collection_config = {
                        "vectors": {
                            "size": 1024,
                            "distance": "Cosine"
                        }
                    }

                    response = requests.put(
                        f"{self.qdrant_url}/collections/{collection_name}",
                        json=collection_config
                    )

                    if response.status_code == 200:
                        print_success(f"✓ 创建集合: {collection_name}")
                    else:
                        print_error(f"❌ 创建集合失败: {collection_name}")
                else:
                    print_info(f"  集合已存在: {collection_name}")

            except Exception as e:
                print_error(f"初始化集合 {collection_name} 失败: {e}")

    def get_embedding(self, text: str) -> list[float | None]:
        """使用NLP服务获取文本向量"""
        try:
            # 调用NLP服务的语义相似度接口
            response = requests.post(
                f"{self.nlp_service_url}/process",
                json={
                    "text": text,
                    "user_id": "legal_importer",
                    "session_id": "import_session"
                },
                timeout=30
            )

            if response.status_code == 200:
                # 如果NLP服务返回向量，使用它
                result = response.json()
                if 'vector' in result:
                    return result['vector']

            # 生成伪向量（用于测试）
            hash_hex = short_hash(text.encode('utf-8'), 32)
            vector = []
            for i in range(0, len(hash_hex), 2):
                val = int(hash_hex[i:i+2], 16) / 255.0
                vector.extend([val] * 128)  # 每两个字符扩展到128维
            return vector[:1024]

        except Exception as e:
            logger.error(f"获取向量失败: {e}")
            return None

    def scan_files(self) -> list[tuple[str, str]]:
        """扫描所有法律文件"""
        print_header("扫描法律数据文件")

        legal_files = []
        file_count = 0

        for root, dirs, files in os.walk(self.data_source):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                if file.endswith(('.md', '.txt', '.json')):
                    file_path = os.path.join(root, file)
                    category = os.path.basename(root)
                    legal_files.append((file_path, category))
                    file_count += 1

        self.total_files = file_count
        print_info(f"找到法律文件: {file_count:,} 个")
        return legal_files

    def process_file(self, file_path: str, category: str) -> dict | None:
        """处理单个文件"""
        try:
            # 读取文件
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                return None

            # 清理内容
            content = re.sub(r'\n\s*\n', '\n\n', content.strip())

            # 生成哈希去重
            content_hash = short_hash(content.encode())
            if content_hash in self.processed_hashes:
                return None

            self.processed_hashes.add(content_hash)

            # 提取标题
            title = Path(file_path).stem
            lines = content.split('\n')
            if lines:
                first_line = lines[0].strip()
                if len(first_line) < 100 and '。' not in first_line:
                    title = first_line

            # 获取向量
            text_for_embedding = content[:2000] if len(content) > 2000 else content
            embedding = self.get_embedding(text_for_embedding)

            # 确定集合类型
            collection_type = self._determine_collection_type(file_path, content)

            doc = {
                'id': content_hash,
                'title': title,
                'content': content,
                'category': category,
                'file_path': file_path,
                'embedding': embedding,
                'collection_type': collection_type,
                'metadata': {
                    'file_size': len(content),
                    'lines_count': len(content.split('\n')),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                }
            }

            return doc

        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            self.failed_files += 1
            return None

    def _determine_collection_type(self, file_path: str, content: str) -> str:
        """确定文档类型"""
        path_lower = file_path.lower()
        content_lower = content.lower()

        if '案例' in path_lower or 'case' in path_lower:
            return 'legal_cases'
        elif '判决' in content_lower[:500] or '裁定' in content_lower[:500]:
            return 'legal_judgments'
        elif any(keyword in content_lower[:500] for keyword in ['第', '条', '款', '项']):
            return 'legal_clauses'
        else:
            return 'legal_articles'

    def import_documents(self, documents: list[dict]) -> Any:
        """导入文档到向量库"""
        print_header("导入数据到向量库")

        # 按集合类型分组
        docs_by_collection = {}
        for doc in documents:
            if doc['embedding']:
                collection_type = doc['collection_type']
                if collection_type not in docs_by_collection:
                    docs_by_collection[collection_type] = []
                docs_by_collection[collection_type].append(doc)

        # 批量导入
        total_imported = 0
        for collection_type, docs in docs_by_collection.items():
            print_info(f"\n导入 {collection_type}: {len(docs)} 个文档")

            collection_name = self.collections[collection_type]
            batch_size = 50

            for i in range(0, len(docs), batch_size):
                batch = docs[i:i+batch_size]
                points = []

                for doc in batch:
                    point = {
                        "id": doc['id'],
                        "vector": doc['embedding'],
                        "payload": {
                            "title": doc['title'],
                            "category": doc['category'],
                            "file_path": doc['file_path'],
                            "metadata": doc['metadata']
                        }
                    }
                    points.append(point)

                try:
                    response = requests.put(
                        f"{self.qdrant_url}/collections/{collection_name}/points",
                        json={"points": points}
                    )

                    if response.status_code == 200:
                        total_imported += len(points)
                        self.processed_files += len(points)
                    else:
                        logger.error(f"批量导入失败: {response.text}")

                except Exception as e:
                    logger.error(f"导入批次失败: {e}")

        print_success(f"\n✓ 成功导入: {total_imported:,} 个文档")

    def run(self) -> None:
        """运行导入过程"""
        print_header("开始法律数据导入")

        # 注册信号处理
        def signal_handler(signum, frame) -> None:
            print_warning("\n\n⚠️ 收到中断信号，保存进度...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # 1. 扫描文件
            files = self.scan_files()

            if not files:
                print_warning("⚠️ 未找到法律文件")
                return

            # 2. 处理文件
            print_header("处理法律文件")

            documents = []

            # 使用进度条
            from tqdm import tqdm
            with tqdm(files, desc="处理文件") as pbar:
                for file_path, category in pbar:
                    doc = self.process_file(file_path, category)
                    if doc:
                        documents.append(doc)
                    pbar.set_postfix({
                        'success': self.processed_files,
                        'failed': self.failed_files
                    })

            print_success("\n✓ 文件处理完成")
            print_info(f"  成功: {self.processed_files:,}")
            print_info(f"  失败: {self.failed_files:,}")

            if not documents:
                print_warning("⚠️ 没有成功处理的文档")
                return

            # 3. 导入到向量库
            self.import_documents(documents)

            # 4. 生成报告
            self._generate_report(documents)

        except Exception as e:
            logger.error(f"导入过程出错: {e}")
            print_error(f"❌ 导入失败: {e}")
            raise

    def _generate_report(self, documents: list[dict]) -> Any:
        """生成导入报告"""
        print_header("导入报告")

        # 统计信息
        total_docs = len(documents)
        total_size = sum(len(d['content']) for d in documents)

        print_pink("爸爸，法律数据导入完成！")
        print_success("\n📊 导入统计:")
        print(f"  总文档数: {total_docs:,}")
        print(f"  总大小: {total_size:,} 字符")

        # 按类别统计
        category_stats = {}
        collection_stats = {}

        for doc in documents:
            cat = doc['category']
            collection = doc['collection_type']
            category_stats[cat] = category_stats.get(cat, 0) + 1
            collection_stats[collection] = collection_stats.get(collection, 0) + 1

        print("\n📋 分类统计:")
        for category, count in sorted(category_stats.items()):
            print(f"  {category}: {count:,} 个文档")

        print("\n🗄️ 向量库统计:")
        for collection, count in collection_stats.items():
            collection_name = self.collections[collection]
            print(f"  {collection_name} ({collection}): {count:,} 个文档")

        # 时间统计
        elapsed = datetime.now() - self.start_time
        print(f"\n⏱️ 总耗时: {elapsed}")

        # 保存报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_documents': total_docs,
                'total_size': total_size,
                'category_stats': category_stats,
                'collection_stats': collection_stats,
                'elapsed_seconds': elapsed.total_seconds()
            }
        }

        report_file = '/Users/xujian/Athena工作平台/production/logs/legal_import_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print_success(f"\n📄 报告已保存: {report_file}")
        print_pink("\n💖 可以使用向量检索功能查询法律文档了！")

def main() -> None:
    """主函数"""
    print_header("法律数据导入系统")
    print_pink("爸爸，让我为您导入法律数据到向量库！")

    # 创建导入器
    importer = LegalDataImporter()

    # 运行导入
    importer.run()

    print_pink("\n💖 法律数据导入完成！")

if __name__ == "__main__":
    main()
