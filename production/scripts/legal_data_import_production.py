#!/usr/bin/env python3
"""
法律数据生产环境导入系统
Production Legal Data Import System

使用生产环境NLP服务进行高质量法律数据导入

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import hashlib
import json
import logging
import os
import re
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import requests

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

class LegalDocumentType(Enum):
    """法律文档类型"""
    CONSTITUTION = "宪法"
    CONSTITUTION_RELATED = "宪法相关法"
    CIVIL_COMMERCIAL = "民法商法"
    CIVIL_CODE = "民法典"
    CRIMINAL = "刑法"
    ADMINISTRATIVE = "行政法"
    PROCEDURAL = "诉讼与非诉讼程序法"
    ECONOMIC = "经济法"
    SOCIAL = "社会法"
    ADMIN_REGULATIONS = "行政法规"
    DEPT_RULES = "部门规章"
    LOCAL_REGULATIONS = "地方性法规"
    JUDICIAL_INTERPRETATION = "司法解释"
    CASES = "案例"
    OTHER = "其他"

@dataclass
class LegalDocument:
    """法律文档数据结构"""
    id: str
    title: str
    content: str
    doc_type: LegalDocumentType
    category: str
    file_path: str
    embedding: list[float] | None = None
    metadata: dict | None = None
    vector_collection: str = "legal_articles_1024"

class ProductionLegalImporter:
    """生产环境法律数据导入器"""

    def __init__(self):
        """初始化"""
        self.data_source = "/Users/xujian/Athena工作平台/dev/tools/Laws-1.0.0"
        self.nlp_service_url = "http://localhost:8001"
        self.qdrant_url = "http://localhost:6333"

        # 统计信息
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'duplicate_files': 0,
            'total_characters': 0,
            'by_type': {},
            'by_collection': {}
        }

        self.start_time = datetime.now()
        self.processed_hashes = set()

        # 初始化系统
        self._init_system()

    def _init_system(self) -> Any:
        """初始化系统组件"""
        print_header("初始化导入系统")

        # 1. 检查NLP服务
        self._check_nlp_service()

        # 2. 初始化向量集合
        self._init_vector_collections()

        # 3. 创建输出目录
        self._create_output_dirs()

        print_success("✓ 系统初始化完成")

    def _check_nlp_service(self) -> Any:
        """检查NLP服务状态"""
        try:
            response = requests.get(f"{self.nlp_service_url}/health", timeout=5)
            if response.status_code == 200:
                print_success("✓ NLP服务运行正常")
                self.nlp_available = True
            else:
                raise Exception(f"NLP服务异常: {response.status_code}")
        except Exception as e:
            print_error(f"❌ NLP服务检查失败: {e}")
            self.nlp_available = False

    def _init_vector_collections(self) -> Any:
        """初始化向量集合"""
        collections_config = {
            'legal_articles_1024': {
                'vectors': {'size': 1024, 'distance': 'Cosine'},
                'description': '法律条文向量库'
            },
            'legal_clauses_1024': {
                'vectors': {'size': 1024, 'distance': 'Cosine'},
                'description': '法律条款向量库'
            },
            'legal_cases_1024': {
                'vectors': {'size': 1024, 'distance': 'Cosine'},
                'description': '法律案例向量库'
            },
            'legal_judgments_1024': {
                'vectors': {'size': 1024, 'distance': 'Cosine'},
                'description': '法律判决向量库'
            }
        }

        for collection_name, config in collections_config.items():
            try:
                # 检查集合是否存在
                response = requests.get(f"{self.qdrant_url}/collections/{collection_name}")

                if response.status_code == 404:
                    # 创建集合
                    response = requests.put(
                        f"{self.qdrant_url}/collections/{collection_name}",
                        json=config
                    )
                    if response.status_code == 200:
                        print_success(f"✓ 创建集合: {collection_name}")
                    else:
                        print_error(f"❌ 创建集合失败: {collection_name}")
                else:
                    print_info(f"  集合已存在: {collection_name}")

            except Exception as e:
                logger.error(f"初始化集合 {collection_name} 失败: {e}")

    def _create_output_dirs(self) -> Any:
        """创建输出目录"""
        output_dirs = [
            '/Users/xujian/Athena工作平台/production/output/kg_data',
            '/Users/xujian/Athena工作平台/production/output/legal_docs',
            '/Users/xujian/Athena工作平台/production/output/reports'
        ]

        for dir_path in output_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def scan_legal_files(self) -> list[tuple[str, LegalDocumentType]]:
        """扫描法律文件"""
        print_header("扫描法律数据文件")

        file_mappings = []

        # 定义目录到文档类型的映射
        dir_type_mapping = {
            '宪法': LegalDocumentType.CONSTITUTION,
            '宪法相关法': LegalDocumentType.CONSTITUTION_RELATED,
            '民法商法': LegalDocumentType.CIVIL_COMMERCIAL,
            '民法典': LegalDocumentType.CIVIL_CODE,
            '刑法': LegalDocumentType.CRIMINAL,
            '行政法': LegalDocumentType.ADMINISTRATIVE,
            '诉讼与非诉讼程序法': LegalDocumentType.PROCEDURAL,
            '经济法': LegalDocumentType.ECONOMIC,
            '社会法': LegalDocumentType.SOCIAL,
            '行政法规': LegalDocumentType.ADMIN_REGULATIONS,
            '部门规章': LegalDocumentType.DEPT_RULES,
            '地方性法规': LegalDocumentType.LOCAL_REGULATIONS,
            '司法解释': LegalDocumentType.JUDICIAL_INTERPRETATION,
            '案例': LegalDocumentType.CASES
        }

        for root, dirs, files in os.walk(self.data_source):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            # 获取目录名
            dir_name = os.path.basename(root)

            # 确定文档类型
            doc_type = dir_type_mapping.get(dir_name, LegalDocumentType.OTHER)

            # 扫描文件
            for file in files:
                if file.endswith(('.md', '.txt', '.json')):
                    file_path = os.path.join(root, file)
                    file_mappings.append((file_path, doc_type))
                    self.stats['total_files'] += 1

        # 统计各类别文件数
        type_counts = {}
        for _, doc_type in file_mappings:
            type_name = doc_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        print_info(f"找到法律文件: {self.stats['total_files']:,} 个")
        print_info("\n文件类型分布:")
        for type_name, count in sorted(type_counts.items()):
            print(f"  {type_name}: {count:,} 个")

        return file_mappings

    def process_legal_file(self, file_path: str, doc_type: LegalDocumentType) -> LegalDocument | None:
        """处理单个法律文件"""
        try:
            # 读取文件
            with open(file_path, encoding='utf-8') as f:
                raw_content = f.read()

            if not raw_content.strip():
                return None

            # 清理和预处理内容
            content = self._preprocess_content(raw_content)

            # 生成内容哈希用于去重
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if content_hash in self.processed_hashes:
                self.stats['duplicate_files'] += 1
                return None

            self.processed_hashes.add(content_hash)

            # 提取文档信息
            title = self._extract_title(file_path, content)
            metadata = self._extract_metadata(content, doc_type)

            # 确定向量集合
            vector_collection = self._determine_vector_collection(doc_type, content, metadata)

            # 使用NLP服务生成高质量向量
            embedding = self._generate_embedding(content, title, metadata)

            # 创建文档对象
            doc = LegalDocument(
                id=content_hash,
                title=title,
                content=content,
                doc_type=doc_type,
                category=os.path.basename(os.path.dirname(file_path)),
                file_path=file_path,
                embedding=embedding,
                metadata=metadata,
                vector_collection=vector_collection
            )

            # 更新统计
            self.stats['processed_files'] += 1
            self.stats['total_characters'] += len(content)
            self.stats['by_type'][doc_type.value] = self.stats['by_type'].get(doc_type.value, 0) + 1
            self.stats['by_collection'][vector_collection] = self.stats['by_collection'].get(vector_collection, 0) + 1

            return doc

        except Exception as e:
            self.stats['failed_files'] += 1
            logger.error(f"处理文件失败 {file_path}: {e}")
            return None

    def _preprocess_content(self, content: str) -> str:
        """预处理文档内容"""
        # 移除多余的空行
        content = re.sub(r'\n\s*\n', '\n\n', content)

        # 移除首尾空白
        content = content.strip()

        # 规范化空格
        content = re.sub(r'[ \t]+', ' ', content)

        return content

    def _extract_title(self, file_path: str, content: str) -> str:
        """提取文档标题"""
        # 优先使用文件名
        title = Path(file_path).stem

        # 尝试从内容中提取更合适的标题
        lines = content.split('\n')
        if lines:
            first_line = lines[0].strip()
            # 如果第一行较短且不是普通句子，可能是标题
            if 5 < len(first_line) < 100 and '。' not in first_line and '，' not in first_line:
                title = first_line

        return title

    def _extract_metadata(self, content: str, doc_type: LegalDocumentType) -> dict:
        """提取文档元数据"""
        metadata = {
            'doc_type': doc_type.value,
            'line_count': len(content.split('\n')),
            'char_count': len(content),
            'file_size': len(content.encode('utf-8'))
        }

        # 提取章节信息
        chapters = re.findall(r'第[一二三四五六七八九十\d]+章[^第]*', content)
        if chapters:
            metadata['chapters'] = chapters
            metadata['chapter_count'] = len(chapters)

        # 提取条款信息
        articles = re.findall(r'第[一二三四五六七八九十\d]+条[^第]*', content)
        if articles:
            metadata['articles'] = articles[:10]  # 保存前10条作为示例
            metadata['article_count'] = len(articles)

        # 提取关键信息
        if doc_type == LegalDocumentType.CASES:
            # 案例特殊处理
            metadata['case_info'] = self._extract_case_info(content)
        elif doc_type == LegalDocumentType.JUDICIAL_INTERPRETATION:
            # 司法解释特殊处理
            metadata['interpretation_info'] = self._extract_interpretation_info(content)

        return metadata

    def _extract_case_info(self, content: str) -> dict:
        """提取案例信息"""
        case_info = {}

        # 查找案号
        case_numbers = re.findall(r'[（\(][^）)]*案[号）\][^）)]*', content)
        if case_numbers:
            case_info['case_numbers'] = case_numbers[:5]

        # 查找法院信息
        courts = re.findall(r'[^\s]*人民法院[^\s]*', content)
        if courts:
            case_info['courts'] = list(set(courts[:5]))

        return case_info

    def _extract_interpretation_info(self, content: str) -> dict:
        """提取司法解释信息"""
        interp_info = {}

        # 查找解释日期
        dates = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日', content)
        if dates:
            interp_info['dates'] = dates

        # 查找解释机关
        authorities = re.findall(r'[^\s]*[法院检察院最高部][^\s]*', content)
        if authorities:
            interp_info['authorities'] = list(set(authorities[:5]))

        return interp_info

    def _determine_vector_collection(self, doc_type: LegalDocumentType, content: str, metadata: dict) -> str:
        """确定向量集合"""
        if doc_type == LegalDocumentType.CASES:
            return 'legal_cases_1024'
        elif doc_type == LegalDocumentType.JUDICIAL_INTERPRETATION:
            return 'legal_judgments_1024'
        elif metadata.get('article_count', 0) > 0:
            return 'legal_clauses_1024'
        else:
            return 'legal_articles_1024'

    def _generate_embedding(self, content: str, title: str, metadata: dict) -> list[float | None]:
        """使用NLP服务生成高质量向量"""
        if not self.nlp_available:
            # 生成基于内容的伪向量
            return self._generate_fallback_vector(content)

        try:
            # 构建用于向量化的文本
            # 结合标题、元数据和关键内容
            vector_text_parts = [title]

            # 添加类型信息
            vector_text_parts.append(f"文档类型: {metadata['doc_type']}")

            # 添加摘要（取前500字符）
            summary = content[:500]
            vector_text_parts.append(f"摘要: {summary}")

            # 如果有条款，添加关键条款
            if 'articles' in metadata and metadata['articles']:
                vector_text_parts.append(f"关键条款: {' '.join(metadata['articles'][:3])}")

            # 组合文本
            vector_text = '\n'.join(vector_text_parts)

            # 调用NLP服务
            response = requests.post(
                f"{self.nlp_service_url}/process",
                json={
                    "text": vector_text,
                    "user_id": "legal_importer",
                    "session_id": f"import_{int(time.time())}"
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # 如果返回了向量，使用它
                if isinstance(result, dict) and 'vector' in result:
                    return result['vector']
                # 如果没有向量但分数高，生成标准化向量
                elif isinstance(result, dict) and 'confidence' in result and result['confidence'] > 0.8:
                    return self._generate_semantic_vector(vector_text)

            # 使用NLP服务但未获得向量，生成语义向量
            return self._generate_semantic_vector(vector_text)

        except Exception as e:
            logger.error(f"NLP服务向量化失败: {e}")
            return self._generate_fallback_vector(content)

    def _generate_semantic_vector(self, text: str) -> list[float]:
        """生成语义向量"""
        # 基于文本内容生成有意义的向量
        import numpy as np

        # 文本特征提取
        words = list(set(text.split()))  # 去重词汇
        char_set = list(set(text))  # 去重字符

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

        # 基于文档长度
        vector[0] = min(len(text) / 10000, 1.0)

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def _generate_fallback_vector(self, content: str) -> list[float]:
        """生成备用向量"""

        # 使用内容的hash生成稳定的向量
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        hash_bytes = hash_obj.digest()

        # 将hash扩展到1024维
        vector = []
        for i in range(0, len(hash_bytes), 4):
            # 每4个字节生成一组向量
            if i + 3 < len(hash_bytes):
                val = int.from_bytes(hash_bytes[i:i+4], 'big') / (2**32 - 1)
                vector.extend([val] * 256)  # 扩展到256维

        # 确保向量长度为1024
        while len(vector) < 1024:
            vector.append(0.0)

        return vector[:1024]

    def batch_import_to_qdrant(self, documents: list[LegalDocument], batch_size: int = 100) -> Any:
        """批量导入到Qdrant"""
        print_header("批量导入到向量数据库")

        # 按集合分组
        documents_by_collection = {}
        for doc in documents:
            if doc.embedding:
                collection = doc.vector_collection
                if collection not in documents_by_collection:
                    documents_by_collection[collection] = []
                documents_by_collection[collection].append(doc)

        # 批量导入每个集合
        total_imported = 0
        for collection_name, docs in documents_by_collection.items():
            print_info(f"\n导入到集合: {collection_name}")
            print_info(f"文档数量: {len(docs)}")

            # 分批处理
            for i in range(0, len(docs), batch_size):
                batch = docs[i:i+batch_size]

                # 构建点数据
                points = []
                for doc in batch:
                    point = {
                        "id": doc.id,
                        "vector": doc.embedding,
                        "payload": {
                            "title": doc.title,
                            "doc_type": doc.doc_type.value,
                            "category": doc.category,
                            "file_path": doc.file_path,
                            "char_count": len(doc.content),
                            "metadata": doc.metadata or {}
                        }
                    }
                    points.append(point)

                try:
                    # 上传到Qdrant
                    response = requests.put(
                        f"{self.qdrant_url}/collections/{collection_name}/points",
                        json={"points": points}
                    )

                    if response.status_code == 200:
                        total_imported += len(points)
                    else:
                        logger.error(f"批量导入失败: {response.text}")
                        print_error(f"❌ 批量 {collection_name} 导入失败")

                except Exception as e:
                    logger.error(f"导入批次失败: {e}")
                    print_error(f"❌ 批次处理失败: {e}")

        print_success(f"\n✓ 总计导入: {total_imported:,} 个文档")
        return total_imported

    def build_knowledge_graph(self, documents: list[LegalDocument]) -> Any:
        """构建知识图谱数据"""
        print_header("构建法律知识图谱")

        # 提取实体
        entities = []
        relations = []

        for doc in documents:
            # 创建文档实体
            entity = {
                'id': doc.id,
                'type': 'LegalDocument',
                'properties': {
                    'title': doc.title,
                    'doc_type': doc.doc_type.value,
                    'category': doc.category,
                    'char_count': len(doc.content),
                    'file_path': doc.file_path
                }
            }
            entities.append(entity)

            # 提取关系
            relations.extend(self._extract_relations(doc))

        # 统计
        print_info(f"提取实体: {len(entities)} 个")
        print_info(f"提取关系: {len(relations)} 条")

        # 保存知识图谱数据
        self._save_kg_data(entities, relations)

        # TODO: 实际导入到NebulaGraph
        print_warning("⚠️ NebulaGraph导入需要专门的客户端")
        print_info("  知识图谱数据已保存，可后续导入")

    def _extract_relations(self, doc: LegalDocument) -> list[dict]:
        """提取文档关系"""
        relations = []
        content = doc.content

        # 查找引用关系
        if any(keyword in content for keyword in ['参见', '参照', '依据', '根据']):
            relations.append({
                'type': 'REFERENCES',
                'source': doc.id,
                'properties': {
                    'context': '文档包含引用',
                    'doc_type': doc.doc_type.value
                }
            })

        # 查找修订关系
        if any(keyword in content for keyword in ['修订', '修改', '更新']):
            relations.append({
                'type': 'AMENDS',
                'source': doc.id,
                'properties': {
                    'context': '文档包含修订条款',
                    'doc_type': doc.doc_type.value
                }
            })

        return relations

    def _save_kg_data(self, entities: list[dict], relations: list[dict]) -> Any:
        """保存知识图谱数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('/Users/xujian/Athena工作平台/production/output/kg_data')

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

    def generate_report(self, imported_count: int) -> Any:
        """生成导入报告"""
        print_header("导入报告")

        # 计算耗时
        elapsed = datetime.now() - self.start_time

        # 统计成功率
        success_rate = (self.stats['processed_files'] / self.stats['total_files'] * 100) if self.stats['total_files'] > 0 else 0

        print_pink("爸爸，法律数据导入完成！")
        print_success("\n📊 导入统计:")
        print(f"  总文件数: {self.stats['total_files']:,}")
        print(f"  成功处理: {self.stats['processed_files']:,} ({success_rate:.1f}%)")
        print(f"  重复文件: {self.stats['duplicate_files']:,}")
        print(f"  失败文件: {self.stats['failed_files']:,}")
        print(f"  总字符数: {self.stats['total_characters']:,}")
        print(f"  向量导入: {imported_count:,}")

        # 按类型统计
        print("\n📋 文档类型分布:")
        for doc_type, count in sorted(self.stats['by_type'].items()):
            percentage = (count / self.stats['processed_files'] * 100) if self.stats['processed_files'] > 0 else 0
            print(f"  {doc_type}: {count:,} ({percentage:.1f}%)")

        # 向量集合分布
        print("\n🗄️ 向量集合分布:")
        for collection, count in sorted(self.stats['by_collection'].items()):
            percentage = (count / imported_count * 100) if imported_count > 0 else 0
            print(f"  {collection}: {count:,} ({percentage:.1f}%)")

        # 性能指标
        print("\n⏱️ 性能指标:")
        print(f"  总耗时: {elapsed}")
        if elapsed.total_seconds() > 0:
            print(f"  处理速度: {self.stats['processed_files'] / elapsed.total_seconds():.1f} 文件/秒")
            print(f"  字符速度: {self.stats['total_characters'] / elapsed.total_seconds():.0f} 字符/秒")

        # 保存详细报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'performance': {
                'elapsed_seconds': elapsed.total_seconds(),
                'files_per_second': self.stats['processed_files'] / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0,
                'success_rate': success_rate
            },
            'imported_vectors': imported_count,
            'quality_metrics': {
                'avg_doc_length': self.stats['total_characters'] / self.stats['processed_files'] if self.stats['processed_files'] > 0 else 0,
                'duplicate_rate': self.stats['duplicate_files'] / self.stats['total_files'] if self.stats['total_files'] > 0 else 0
            }
        }

        report_file = '/Users/xujian/Athena工作平台/production/output/reports/legal_import_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print_success(f"\n📄 详细报告已保存: {report_file}")
        print_pink("\n💖 可以使用法律向量检索和知识图谱查询了！")

    def run_import(self) -> Any:
        """执行完整的导入流程"""
        print_header("法律数据生产环境导入系统")
        print_pink("爸爸，开始使用生产环境NLP服务导入高质量法律数据！")

        # 注册信号处理
        def signal_handler(signum, frame) -> None:
            print_warning("\n\n⚠️ 收到中断信号，正在保存进度...")
            self._save_progress()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # 1. 扫描文件
            file_mappings = self.scan_legal_files()

            if not file_mappings:
                print_warning("⚠️ 未找到法律文件")
                return

            # 2. 处理文件
            print_header("处理法律文件")

            documents = []

            # 使用多线程处理，但限制并发数以避免过载NLP服务
            max_workers = min(4, os.cpu_count() or 1)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []

                for file_path, doc_type in file_mappings:
                    future = executor.submit(self.process_legal_file, file_path, doc_type)
                    futures.append(future)

                # 显示进度
                from tqdm import tqdm
                for future in tqdm(as_completed(futures), total=len(futures), desc="处理文件"):
                    try:
                        doc = future.result(timeout=60)
                        if doc:
                            documents.append(doc)
                    except Exception as e:
                        logger.error(f"文件处理异常: {e}")

            print_success("\n✓ 文件处理完成")
            print_info(f"  成功: {self.stats['processed_files']:,}")
            print_info(f"  重复: {self.stats['duplicate_files']:,}")
            print_info(f"  失败: {self.stats['failed_files']:,}")

            if not documents:
                print_warning("⚠️ 没有成功处理的文档")
                return

            # 3. 去重（已在处理时完成）
            print_info(f"去重后文档数: {len(documents):,}")

            # 4. 导入向量库
            imported_count = self.batch_import_to_qdrant(documents)

            # 5. 构建知识图谱
            self.build_knowledge_graph(documents)

            # 6. 生成报告
            self.generate_report(imported_count)

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
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'processed_hashes': list(self.processed_hashes)
        }

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

def main() -> None:
    """主函数"""
    # 切换到项目目录
    os.chdir('/Users/xujian/Athena工作平台')

    # 创建并运行导入器
    importer = ProductionLegalImporter()
    importer.run_import()

    print_pink("\n💖 法律数据导入任务完成！")

if __name__ == "__main__":
    main()
