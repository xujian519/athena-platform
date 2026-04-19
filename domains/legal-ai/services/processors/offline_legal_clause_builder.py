#!/usr/bin/env python3
"""
离线版本的法律条款向量化系统
绕过Qdrant连接问题，专注于条款识别和向量化
"""

import json
import logging
import pickle
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LegalClause:
    """法律条款数据结构"""
    content: str                    # 条款内容
    clause_number: str             # 条款编号（如'第十三条'）
    clause_type: str               # 条款类型（条/项/款/修正条等）
    law_name: str                  # 法律名称
    law_category: str              # 法律分类
    file_path: str                 # 文件路径
    line_number: int               # 行号
    vector: list[float] | None = None  # 向量表示

class OfflineLegalClauseBuilder:
    """离线版本的法律条款向量构建器"""

    def __init__(self, laws_root_path: str, output_path: str, model_name: str = None):
        self.laws_root_path = Path(laws_root_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

        # 初始化模型（使用本地模型）
        if model_name is None:
            model_name = '/Users/xujian/Athena工作平台/models/pretrained/bge-large-zh-v1.5'

        logger.info(f"正在加载BGE模型: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        self.vector_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"向量维度: {self.vector_dim}")

        # 简化的条款识别模式
        self.clause_pattern = re.compile(r'^第([一二三四五六七八九十百千万\d]+)条[：:\s]*(.*)$', re.MULTILINE | re.IGNORECASE)

        # 其他条款模式
        self.other_patterns = [
            (re.compile(r'^([一二三四五六七八九十百千万\d]+)[、.:,]\s*(.*)$', re.MULTILINE | re.IGNORECASE), '修正条'),
            (re.compile(r'^（([一二三四五六七八九十百千万\d]+)）[：:\s]*(.*)$', re.MULTILINE | re.IGNORECASE), '项'),
            (re.compile(r'^\(([一二三四五六七八九十百千万\d]+)\)[：:\s]*(.*)$', re.MULTILINE | re.IGNORECASE), '项'),
            (re.compile(r'^(\d+)\.[：:\s]*(.*)$', re.MULTILINE), '目'),
        ]

        # 统计数据
        self.stats = {
            'total_files': 0,
            'total_clauses': 0,
            'clause_types': {},
            'categories': {},
            'processing_errors': 0,
            'vector_generation_time': 0.0
        }

    def extract_clauses_from_text(self, text: str, file_path: str) -> list[LegalClause]:
        """从文本中提取法律条款"""
        clauses = []
        law_name = Path(file_path).parent.name
        category = self._get_category_from_path(file_path)
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # 尝试主要条款模式
            match = self.clause_pattern.match(line)
            if match:
                try:
                    clause_number = f"第{match.group(1)}条"
                    clause_content = match.group(2).strip()

                    if len(clause_content) > 5:
                        clause = LegalClause(
                            content=clause_content,
                            clause_number=clause_number,
                            clause_type='条',
                            law_name=law_name,
                            law_category=category,
                            file_path=str(file_path),
                            line_number=line_num
                        )
                        clauses.append(clause)
                        self.stats['clause_types']['条'] = self.stats['clause_types'].get('条', 0) + 1
                except Exception as e:
                    logger.warning(f"处理条款时出错: {e}")
                continue

            # 尝试其他模式
            for pattern, clause_type in self.other_patterns:
                match = pattern.match(line)
                if match:
                    try:
                        if clause_type == '修正条':
                            clause_number = f"{match.group(1)}"
                        else:
                            clause_number = f"{match.group(0).split()[0]}"

                        clause_content = match.group(2).strip()

                        if len(clause_content) > 5:
                            clause = LegalClause(
                                content=clause_content,
                                clause_number=clause_number,
                                clause_type=clause_type,
                                law_name=law_name,
                                law_category=category,
                                file_path=str(file_path),
                                line_number=line_num
                            )
                            clauses.append(clause)
                            self.stats['clause_types'][clause_type] = self.stats['clause_types'].get(clause_type, 0) + 1
                            break
                    except Exception as e:
                        logger.warning(f"处理其他条款时出错: {e}")
                        continue

        return clauses

    def _get_category_from_path(self, file_path: str) -> str:
        """从路径获取法律分类"""
        path_parts = Path(file_path).parts
        if len(path_parts) > 1:
            return path_parts[-2]
        return '其他'

    def test_single_file(self, test_file: str = None):
        """测试单个文件的条款提取效果"""
        if test_file is None:
            test_file = '/Users/xujian/Athena工作平台/projects/Laws-1.0.0/民法典/总则.md'

        logger.info(f"=== 测试文件: {test_file} ===")

        try:
            with open(test_file, encoding='utf-8') as f:
                content = f.read()

            clauses = self.extract_clauses_from_text(content, test_file)

            logger.info("提取结果:")
            logger.info(f"  总条款数: {len(clauses)}")

            # 按类型统计
            type_stats = {}
            for clause in clauses:
                type_stats[clause.clause_type] = type_stats.get(clause.clause_type, 0) + 1

            logger.info("  条款类型分布:")
            for clause_type, count in sorted(type_stats.items()):
                logger.info(f"    {clause_type}: {count}")

            # 显示前10个条款示例
            logger.info("  条款示例:")
            for i, clause in enumerate(clauses[:10]):
                logger.info(f"    {i+1}. [{clause.clause_type}] {clause.clause_number}: {clause.content[:60]}...")

            return clauses

        except Exception as e:
            logger.error(f"测试失败: {e}")
            return []

    def generate_vectors_for_clauses(self, clauses: list[LegalClause], batch_size: int = 32):
        """为条款批量生成向量"""
        logger.info(f"开始为 {len(clauses)} 个条款生成向量（批次大小: {batch_size}）")
        start_time = time.time()

        for i in range(0, len(clauses), batch_size):
            batch_clauses = clauses[i:i + batch_size]

            # 生成向量
            texts = [clause.content for clause in batch_clauses]
            vectors = self.embedding_model.encode(texts)

            # 将向量赋值给条款对象
            for _j, (clause, vector) in enumerate(zip(batch_clauses, vectors, strict=False)):
                clause.vector = vector.tolist()

            if (i // batch_size + 1) % 10 == 0:
                logger.info(f"已生成 {i + len(batch_clauses)}/{len(clauses)} 个向量")

        self.stats['vector_generation_time'] = time.time() - start_time
        logger.info(f"向量生成完成，耗时: {self.stats['vector_generation_time']:.2f} 秒")

    def process_all_files(self):
        """处理所有文件并生成向量化数据"""
        logger.info('=== 开始处理所有法律文件 ===')
        start_time = time.time()

        # 处理所有文件
        all_clauses = []
        markdown_files = list(self.laws_root_path.rglob('*.md'))

        logger.info(f"找到 {len(markdown_files)} 个Markdown文件")

        for file_path in markdown_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                clauses = self.extract_clauses_from_text(content, str(file_path))
                all_clauses.extend(clauses)

                # 更新分类统计
                for clause in clauses:
                    category = clause.law_category
                    self.stats['categories'][category] = self.stats['categories'].get(category, 0) + 1

                if len(all_clauses) % 100 == 0:
                    logger.info(f"已提取 {len(all_clauses)} 个条款...")

            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                self.stats['processing_errors'] += 1

        # 更新统计信息
        self.stats['total_files'] = len(markdown_files)
        self.stats['total_clauses'] = len(all_clauses)

        # 生成向量
        if all_clauses:
            self.generate_vectors_for_clauses(all_clauses)

        # 保存数据
        self._save_clauses_to_files(all_clauses)
        self._save_metadata()

        elapsed_time = time.time() - start_time
        logger.info("=== 离线处理完成 ===")
        logger.info(f"总耗时: {elapsed_time:.2f} 秒")
        logger.info(f"处理文件数: {self.stats['total_files']}")
        logger.info(f"总条款数: {self.stats['total_clauses']}")
        logger.info(f"平均每文件条款数: {self.stats['total_clauses']/self.stats['total_files']:.1f}")
        logger.info(f"处理错误数: {self.stats['processing_errors']}")
        logger.info(f"向量生成时间: {self.stats['vector_generation_time']:.2f} 秒")

        return all_clauses

    def _save_clauses_to_files(self, clauses: list[LegalClause]):
        """保存条款数据到文件"""
        logger.info('保存条款数据到文件...')

        # 保存为JSON格式（便于查看）
        json_data = []
        for clause in clauses:
            clause_dict = asdict(clause)
            # 将numpy向量转换为列表以便JSON序列化
            if clause.vector:
                clause_dict['vector'] = clause.vector
            json_data.append(clause_dict)

        json_path = self.output_path / 'legal_clauses_with_vectors.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        # 保存为pickle格式（便于后续加载）
        pickle_path = self.output_path / 'legal_clauses_with_vectors.pkl'
        with open(pickle_path, 'wb') as f:
            pickle.dump(clauses, f)

        # 保存向量矩阵（用于快速向量搜索）
        if clauses and all(clause.vector for clause in clauses):
            vectors = np.array([clause.vector for clause in clauses])
            vector_path = self.output_path / 'vectors.npy'
            np.save(vector_path, vectors)

            # 保存对应的条款信息
            clause_info_path = self.output_path / 'clause_info.json'
            clause_info = []
            for clause in clauses:
                clause_info.append({
                    'content': clause.content,
                    'clause_number': clause.clause_number,
                    'clause_type': clause.clause_type,
                    'law_name': clause.law_name,
                    'law_category': clause.law_category,
                    'file_path': clause.file_path,
                    'line_number': clause.line_number
                })
            with open(clause_info_path, 'w', encoding='utf-8') as f:
                json.dump(clause_info, f, ensure_ascii=False, indent=2)

        logger.info(f"数据已保存到: {self.output_path}")
        logger.info(f"  - JSON文件: {json_path}")
        logger.info(f"  - Pickle文件: {pickle_path}")
        if clauses and all(clause.vector for clause in clauses):
            logger.info(f"  - 向量矩阵: {vector_path}")
            logger.info(f"  - 条款信息: {clause_info_path}")

    def _save_metadata(self):
        """保存元数据"""
        metadata = {
            'version': '4.0.0',
            'created_time': datetime.now().isoformat(),
            'total_clauses': self.stats['total_clauses'],
            'total_files': self.stats['total_files'],
            'vector_dim': self.vector_dim,
            'model_path': '/Users/xujian/Athena工作平台/models/pretrained/bge-large-zh-v1.5',
            'clause_type_distribution': self.stats['clause_types'],
            'category_distribution': dict(sorted(self.stats['categories'].items(), key=lambda x: x[1], reverse=True)),
            'processing_errors': self.stats['processing_errors'],
            'avg_clauses_per_file': self.stats['total_clauses'] / self.stats['total_files'] if self.stats['total_files'] > 0 else 0,
            'vector_generation_time': self.stats['vector_generation_time']
        }

        metadata_path = self.output_path / 'offline_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"元数据已保存到: {metadata_path}")
        logger.info(f"条款类型分布: {self.stats['clause_types']}")
        logger.info(f"分类分布（前10）: {dict(sorted(self.stats['categories'].items(), key=lambda x: x[1], reverse=True)[:10])}")

def main():
    """主函数"""
    logger.info('启动离线版本的法律条款向量化系统')

    # 初始化构建器
    builder = OfflineLegalClauseBuilder(
        laws_root_path='/Users/xujian/Athena工作平台/projects/Laws-1.0.0',
        output_path='/Users/xujian/Athena工作平台/data/offline_legal_vector_db'
    )

    # 先测试条款识别效果
    logger.info("\n" + '='*50)
    logger.info('第一步：测试条款识别效果')
    logger.info('='*50)
    test_clauses = builder.test_single_file()

    if test_clauses:
        logger.info(f"测试成功！识别到 {len(test_clauses)} 个条款")

        # 处理所有文件
        logger.info("\n" + '='*50)
        logger.info('第二步：处理所有文件并生成向量')
        logger.info('='*50)

        all_clauses = builder.process_all_files()

        logger.info('离线法律条款向量化完成！')
        logger.info(f"总共处理了 {len(all_clauses)} 个法律条款，每个都生成了1024维向量")

        # 后续可以轻松导入到Qdrant或其他向量数据库
        logger.info("\n" + '='*50)
        logger.info('后续建议：')
        logger.info('1. 数据已保存在 /Users/xujian/Athena工作平台/data/offline_legal_vector_db')
        logger.info('2. 可以使用 legal_clauses_with_vectors.pkl 直接加载')
        logger.info('3. 向量矩阵保存在 vectors.npy 中，便于快速检索')
        logger.info('4. 稍后Qdrant问题解决后，可以批量导入这些数据')
        logger.info('='*50)

    else:
        logger.error('测试失败，请检查条款识别逻辑')

if __name__ == '__main__':
    main()
