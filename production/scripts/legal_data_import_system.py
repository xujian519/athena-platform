#!/usr/bin/env python3
"""
法律数据综合导入系统
Comprehensive Legal Data Import System

从Laws-1.0.0导入法律数据到向量库和知识图谱

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "modules/nlp/modules/nlp/xiaonuo_nlp_deployment"))
sys.path.insert(0, str(project_root / "venv_xiaonuo_bert" / "lib" / "python3.14" / "site-packages"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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

class LegalDataImportSystem:
    """法律数据导入系统"""

    def __init__(self):
        """初始化"""
        self.data_source = "/Users/xujian/Athena工作平台/dev/tools/Laws-1.0.0"
        self.processed_hashes = set()
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.start_time = datetime.now()

        # 向量库配置
        self.vector_collections = {
            'legal_articles': {
                'name': 'legal_articles_1024',
                'dimension': 1024,
                'distance': 'Cosine'
            },
            'legal_clauses': {
                'name': 'legal_clauses_1024',
                'dimension': 1024,
                'distance': 'Cosine'
            },
            'legal_cases': {
                'name': 'legal_cases_1024',
                'dimension': 1024,
                'distance': 'Cosine'
            },
            'legal_judgments': {
                'name': 'legal_judgments_1024',
                'dimension': 1024,
                'distance': 'Cosine'
            }
        }

        # 法律分类映射
        self.category_mapping = {
            '宪法': 'constitution',
            '宪法相关法': 'constitution_related',
            '民法商法': 'civil_commercial',
            '民法典': 'civil_code',
            '刑法': 'criminal',
            '行政法': 'administrative',
            '行政诉讼法': 'administrative_procedure',
            '经济法': 'economic',
            '社会法': 'social',
            '诉讼与非诉讼程序法': 'procedural',
            '行政法规': 'administrative_regulations',
            '部门规章': 'departmental_rules',
            '地方性法规': 'local_regulations',
            '司法解释': 'judicial_interpretation',
            '案例': 'cases'
        }

        # 初始化组件
        self._init_components()

    def _init_components(self) -> Any:
        """初始化各个组件"""
        print_info("初始化系统组件...")

        # 1. 初始化向量化服务
        self._init_vectorization()

        # 2. 初始化向量数据库
        self._init_vector_db()

        # 3. 初始化知识图谱
        self._init_knowledge_graph()

        print_success("✓ 系统组件初始化完成")

    def _init_vectorization(self) -> Any:
        """初始化向量化服务"""
        try:
            # 使用本地的BGE模型
            from xiaonuo_local_bert_models import XiaonuoLocalBERTModels

            self.bert_models = XiaonuoLocalBERTModels()
            self.embedding_model = self.bert_models.get_bge_model()

            print_success("✓ BGE向量化模型加载成功")
        except Exception as e:
            logger.error(f"向量化模型初始化失败: {e}")
            # 使用备选方案
            print_warning("⚠️ 使用简化向量化方案")
            self.embedding_model = None

    def _init_vector_db(self) -> Any:
        """初始化向量数据库"""
        try:
            import requests

            # 测试Qdrant连接
            response = requests.get("http://localhost:6333/", timeout=5)
            if response.status_code == 200:
                print_success("✓ Qdrant连接成功")

                # 创建集合
                self._create_qdrant_collections()
            else:
                raise Exception("Qdrant连接失败")
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            print_error(f"❌ 向量数据库初始化失败: {e}")

    def _create_qdrant_collections(self) -> Any:
        """创建Qdrant集合"""
        import requests

        for _collection_key, config in self.vector_collections.items():
            try:
                # 检查集合是否存在
                response = requests.get(f"http://localhost:6333/collections/{config['name']}")

                if response.status_code == 404:
                    # 创建集合
                    collection_config = {
                        "vectors": {
                            "size": config['dimension'],
                            "distance": config['distance']
                        }
                    }

                    response = requests.put(
                        f"http://localhost:6333/collections/{config['name']}",
                        json=collection_config
                    )

                    if response.status_code == 200:
                        print_success(f"✓ 创建集合: {config['name']}")
                    else:
                        print_error(f"❌ 创建集合失败: {config['name']}")
                else:
                    print_info(f"  集合已存在: {config['name']}")

            except Exception as e:
                logger.error(f"创建集合 {config['name']} 失败: {e}")

    def _init_knowledge_graph(self) -> Any:
        """初始化知识图谱"""
        try:
            # NebulaGraph配置
            self.ng_config = {
                'space': 'legal_kg',
                'tags': ['LegalDocument', 'LegalArticle', 'LegalClause', 'LegalCase'],
                'edges': ['REFERENCES', 'AMENDS', 'SUPERSEDES', 'APPLIES_TO']
            }
            print_success("✓ 知识图谱配置准备完成")
        except Exception as e:
            logger.error(f"知识图谱初始化失败: {e}")
            print_warning("⚠️ 知识图谱功能受限")

    def generate_embedding(self, text: str) -> list[float | None]:
        """生成文本向量"""
        try:
            if self.embedding_model:
                # 使用BGE模型
                return self.embedding_model.encode(text, normalize_embeddings=True).tolist()
            else:
                # 简化向量化（用于测试）
                # 创建基于文本hash的伪向量
                hash_hex = short_hash(text.encode('utf-8'), 32)
                # 转换为1024维向量
                vector = []
                for i in range(0, len(hash_hex), 2):
                    val = int(hash_hex[i:i+2], 16) / 255.0
                    vector.extend([val] * (1024 // len(hash_hex) + 1))
                return vector[:1024]
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            return None

    def scan_legal_files(self) -> list[tuple[str, str]]:
        """扫描所有法律文件"""
        print_header("扫描法律数据文件")

        legal_files = []

        for root, dirs, files in os.walk(self.data_source):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                if file.endswith(('.md', '.txt', '.json')):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.data_source)
                    category = self._get_category_from_path(relative_path)
                    legal_files.append((file_path, category))

        self.total_files = len(legal_files)
        print_info(f"找到法律文件: {self.total_files:,} 个")

        # 按类别统计
        category_count = {}
        for _, category in legal_files:
            category_count[category] = category_count.get(category, 0) + 1

        print_info("\n文件分类统计:")
        for category, count in sorted(category_count.items()):
            print(f"  {category}: {count:,} 个文件")

        return legal_files

    def _get_category_from_path(self, path: str) -> str:
        """从路径获取法律分类"""
        for chinese_name, english_name in self.category_mapping.items():
            if chinese_name in path:
                return english_name
        return 'other'

    def process_legal_file(self, file_path: str, category: str) -> dict | None:
        """处理单个法律文件"""
        try:
            # 读取文件
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                return None

            # 清理内容
            content = self._clean_content(content)

            # 生成唯一ID
            file_hash = short_hash(content.encode())
            if file_hash in self.processed_hashes:
                return None  # 跳过重复

            self.processed_hashes.add(file_hash)

            # 解析文件信息
            parsed = self._parse_legal_document(file_path, content, category)

            # 生成向量
            if len(content) > 100:
                # 使用完整内容或摘要生成向量
                text_for_embedding = content[:5000] if len(content) > 5000 else content
                embedding = self.generate_embedding(text_for_embedding)
            else:
                embedding = None

            # 构建文档对象
            doc = {
                'id': file_hash,
                'file_path': file_path,
                'category': category,
                'title': parsed.get('title', Path(file_path).stem),
                'content': content,
                'embedding': embedding,
                'metadata': {
                    'file_size': len(content),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    'parsed_info': parsed
                }
            }

            return doc

        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            return None

    def _clean_content(self, content: str) -> str:
        """清理文档内容"""
        # 移除多余空白
        content = re.sub(r'\n\s*\n', '\n\n', content)
        # 移除首尾空白
        content = content.strip()
        return content

    def _parse_legal_document(self, file_path: str, content: str, category: str) -> dict:
        """解析法律文档"""
        parsed = {
            'category': category,
            'file_type': Path(file_path).suffix.lower()
        }

        # 提取标题（通常是第一行）
        lines = content.split('\n')
        if lines:
            first_line = lines[0].strip()
            # 如果第一行较短且不包含句号，可能是标题
            if len(first_line) < 100 and '。' not in first_line:
                parsed['title'] = first_line

        # 提取章节信息
        if '第' in content and '章' in content:
            chapters = re.findall(r'第[一二三四五六七八九十\d]+章[^第]*', content)
            if chapters:
                parsed['chapters'] = chapters

        # 提取条款信息
        if '条' in content:
            articles = re.findall(r'第[一二三四五六七八九十\d]+条[^第]*', content)
            if articles:
                parsed['articles'] = articles

        return parsed

    def import_to_vector_db(self, documents: list[dict]) -> Any:
        """导入到向量数据库"""
        print_header("导入数据到向量数据库")

        import requests
        from tqdm import tqdm

        # 按类别分组
        documents_by_category = {}
        for doc in documents:
            category = self._classify_document(doc)
            if category not in documents_by_category:
                documents_by_category[category] = []
            documents_by_category[category].append(doc)

        # 批量导入
        for category, docs in documents_by_category.items():
            print_info(f"\n导入类别: {category} ({len(docs)} 个文档)")

            collection_name = self._get_collection_for_category(category)
            if not collection_name:
                print_warning(f"  ⚠️ 跳过未知类别: {category}")
                continue

            # 批量上传
            batch_size = 100
            for i in tqdm(range(0, len(docs), batch_size), desc=f"  导入{category}"):
                batch = docs[i:i+batch_size]
                points = []

                for doc in batch:
                    if doc['embedding']:
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

                if points:
                    response = requests.put(
                        f"http://localhost:6333/collections/{collection_name}/points",
                        json={"points": points}
                    )

                    if response.status_code != 200:
                        logger.error(f"批量导入失败: {response.text}")

    def _classify_document(self, doc: dict) -> str:
        """分类文档"""
        # 根据内容和类别确定向量库类型
        if 'case' in doc['category'] or '案例' in doc['title']:
            return 'legal_cases'
        elif 'judgment' in doc['title'] or '判决' in doc['title']:
            return 'legal_judgments'
        elif '条款' in doc['title'] or '条' in doc.get('content', '')[:100]:
            return 'legal_clauses'
        else:
            return 'legal_articles'

    def _get_collection_for_category(self, doc_type: str) -> str | None:
        """获取文档类型对应的集合"""
        collection_map = {
            'legal_cases': 'legal_cases_1024',
            'legal_judgments': 'legal_judgments_1024',
            'legal_clauses': 'legal_clauses_1024',
            'legal_articles': 'legal_articles_1024'
        }
        return collection_map.get(doc_type)

    def build_knowledge_graph(self, documents: list[dict]) -> Any:
        """构建知识图谱"""
        print_header("构建法律知识图谱")

        # 这里实现NebulaGraph的导入逻辑
        # 由于NebulaGraph需要特定的客户端，这里提供框架

        entities = []
        relations = []

        for doc in documents:
            # 创建实体
            entity = {
                'id': doc['id'],
                'type': 'LegalDocument',
                'properties': {
                    'title': doc['title'],
                    'category': doc['category'],
                    'content_length': len(doc['content']),
                    'file_path': doc['file_path']
                }
            }
            entities.append(entity)

            # 提取关系（如引用关系）
            relations.extend(self._extract_relations(doc))

        print_info(f"提取实体: {len(entities)} 个")
        print_info(f"提取关系: {len(relations)} 条")

        # TODO: 实际导入到NebulaGraph
        print_warning("⚠️ NebulaGraph导入需要专门的客户端，这里仅展示数据提取")

        # 保存提取的数据供后续使用
        self._save_kg_data(entities, relations)

    def _extract_relations(self, doc: dict) -> list[dict]:
        """提取文档中的关系"""
        relations = []
        content = doc.get('content', '')

        # 简单的关系提取示例
        # 实际应用中需要更复杂的NLP处理

        # 查找引用
        if '参见' in content or '引用' in content:
            relations.append({
                'type': 'REFERENCES',
                'source': doc['id'],
                'properties': {
                    'context': '文档包含引用'
                }
            })

        return relations

    def _save_kg_data(self, entities: list[dict], relations: list[dict]) -> Any:
        """保存知识图谱数据"""
        output_dir = Path('/Users/xujian/Athena工作平台/production/output/kg_data')
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存实体
        entities_file = output_dir / f'legal_entities_{timestamp}.json'
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)

        # 保存关系
        relations_file = output_dir / f'legal_relations_{timestamp}.json'
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(relations, f, ensure_ascii=False, indent=2)

        print_success("✓ 知识图谱数据已保存:")
        print(f"  实体: {entities_file}")
        print(f"  关系: {relations_file}")

    def remove_duplicates(self, documents: list[dict]) -> list[dict]:
        """去重处理"""
        print_header("数据去重")

        seen_hashes = set()
        unique_docs = []

        for doc in documents:
            content_hash = short_hash(doc['content'].encode())
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_docs.append(doc)

        print_info(f"原始文档: {len(documents):,}")
        print_info(f"去重后: {len(unique_docs):,}")
        print_info(f"重复文档: {len(documents) - len(unique_docs):,}")

        return unique_docs

    def run_import(self) -> Any:
        """执行导入"""
        print_header("开始法律数据导入")

        # 注册信号处理
        def signal_handler(signum, frame) -> None:
            print_warning("\n\n⚠️ 收到中断信号，正在保存进度...")
            self._save_progress()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # 1. 扫描文件
            legal_files = self.scan_legal_files()

            if not legal_files:
                print_warning("⚠️ 未找到法律文件")
                return

            # 2. 处理文件
            print_header("处理法律文件")

            documents = []

            # 使用多线程处理
            max_workers = min(8, os.cpu_count() or 1)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []

                for file_path, category in legal_files:
                    future = executor.submit(self.process_legal_file, file_path, category)
                    futures.append(future)

                # 使用tqdm显示进度
                from tqdm import tqdm
                for future in tqdm(as_completed(futures), total=len(futures), desc="处理文件"):
                    try:
                        doc = future.result(timeout=30)
                        if doc:
                            documents.append(doc)
                            self.processed_files += 1
                    except Exception as e:
                        self.failed_files += 1
                        logger.error(f"文件处理失败: {e}")

            print_success("\n✓ 文件处理完成")
            print_info(f"  成功: {self.processed_files:,}")
            print_info(f"  失败: {self.failed_files:,}")

            if not documents:
                print_warning("⚠️ 没有成功处理的文档")
                return

            # 3. 去重
            documents = self.remove_duplicates(documents)

            # 4. 导入向量库
            self.import_to_vector_db(documents)

            # 5. 构建知识图谱
            self.build_knowledge_graph(documents)

            # 6. 生成报告
            self._generate_report(documents)

        except Exception as e:
            logger.error(f"导入过程出错: {e}")
            print_error(f"❌ 导入失败: {e}")
            raise
        finally:
            # 保存进度
            self._save_progress()

    def _save_progress(self) -> Any:
        """保存进度"""
        progress_file = '/Users/xujian/Athena工作平台/production/logs/legal_import_progress.json'
        progress = {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'processed_hashes': list(self.processed_hashes),
            'timestamp': datetime.now().isoformat()
        }

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

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
        for doc in documents:
            cat = doc['category']
            category_stats[cat] = category_stats.get(cat, 0) + 1

        print("\n📋 分类统计:")
        for category, count in sorted(category_stats.items()):
            print(f"  {category}: {count:,} 个文档")

        # 向量库统计
        print("\n🗄️ 向量库统计:")
        for _collection_key, config in self.vector_collections.items():
            print(f"  {config['name']}: 预计包含部分文档")

        # 时间统计
        elapsed = datetime.now() - self.start_time
        print(f"\n⏱️ 耗时: {elapsed}")

        print_pink("\n💖 下一步可以运行法律向量检索测试！")

def main() -> None:
    """主函数"""
    print_header("法律数据综合导入系统")
    print_pink("爸爸，让我为您导入法律数据到向量库和知识图谱！")

    # 创建系统实例
    system = LegalDataImportSystem()

    # 执行导入
    system.run_import()

    print_pink("\n💖 法律数据导入完成！")

if __name__ == "__main__":
    main()
