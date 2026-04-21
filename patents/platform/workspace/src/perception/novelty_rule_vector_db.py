#!/usr/bin/env python3
"""
新颖性规则向量数据库
Novelty Rule Vector Database

存储和检索专利新颖性判断规则向量
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import asyncio
import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

@dataclass
class RuleVector:
    """规则向量"""
    rule_id: str
    rule_type: str
    vector: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SearchRule:
    """搜索结果规则"""
    rule_id: str
    rule_type: str
    title: str
    description: str
    similarity_score: float
    relevance_score: float
    application_count: int = 0

class NoveltyRuleVectorDB:
    """新颖性规则向量数据库"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self.model = None
        self.index = None
        self.rule_vectors = {}
        self.db_path = 'patent-platform/workspace/data/novelty_rules.db'

        # 初始化
        self._init_model()
        self._init_database()
        self._load_rules()

    def _init_model(self):
        """初始化编码模型"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ 加载向量模型: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ 加载向量模型失败: {str(e)}")
            # 使用简单实现作为降级方案
            self.model = None

    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS novelty_rules (
                rule_id TEXT PRIMARY KEY,
                rule_type TEXT,
                title TEXT,
                description TEXT,
                vector_data BLOB,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT,
                patent_id TEXT,
                usage_date TEXT,
                success_rate REAL,
                FOREIGN KEY (rule_id) REFERENCES novelty_rules (rule_id)
            )
        ''')

        conn.commit()
        conn.close()

    def _encode_text(self, text: str) -> np.ndarray:
        """文本编码"""
        if self.model is not None:
            return self.model.encode(text, normalize_embeddings=True)
        else:
            # 简单降级实现
            words = text.lower().split()
            vector = zeros(self.dimension, dtype=np.float64)
            for i, word in enumerate(words[:self.dimension]):
                vector[i] = hash(word) % 1000 / 1000.0
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            return vector

    def _load_rules(self):
        """加载规则到向量库"""
        # 核心新颖性判断规则
        core_rules = [
            {
                'rule_id': 'NOVELTY_001',
                'rule_type': 'same_invention',
                'title': '相同发明判断规则',
                'description': '判断发明是否与现有技术构成相同发明，考虑技术领域、技术问题、技术方案和预期效果的同一性',
                'keywords': ['技术领域', '技术问题', '技术方案', '技术效果', '同一性'],
                'priority': 'high'
            },
            {
                'rule_id': 'NOVELTY_002',
                'rule_type': 'prior_art',
                'title': '现有技术检索规则',
                'description': '确定检索范围和检索策略，包括专利文献、非专利文献、公知常识等，确保全面检索',
                'keywords': ['检索策略', '专利文献', '非专利文献', 'IPC分类', '关键词'],
                'priority': 'high'
            },
            {
                'rule_id': 'NOVELTY_003',
                'rule_type': 'comparison',
                'title': '技术特征对比规则',
                'description': '逐项对比权利要求的技术特征与现有技术公开的特征，确定区别特征',
                'keywords': ['技术特征', '权利要求', '现有技术', '区别特征', '对比分析'],
                'priority': 'high'
            },
            {
                'rule_id': 'NOVELTY_004',
                'rule_type': 'disclosure',
                'title': '技术公开充分性规则',
                'description': '判断现有技术是否充分公开了相关的技术方案，能够实现相同的技术效果',
                'keywords': ['充分公开', '实现条件', '技术效果', '可实施性'],
                'priority': 'medium'
            },
            {
                'rule_id': 'NOVELTY_005',
                'rule_type': 'technical_field',
                'title': '技术领域相同性判断',
                'description': '判断发明与现有技术是否属于相同或相近的技术领域，考虑IPC/CPC分类',
                'keywords': ['技术领域', 'IPC分类', 'CPC分类', '相近领域'],
                'priority': 'high'
            },
            {
                'rule_id': 'NOVELTY_006',
                'rule_type': 'problem_solution',
                'title': '技术问题同一性判断',
                'description': '判断要解决的技术问题是否相同，考虑技术问题的本质和技术目标',
                'keywords': ['技术问题', '技术目标', '问题本质', '解决需求'],
                'priority': 'high'
            },
            {
                'rule_id': 'NOVELTY_007',
                'rule_type': 'effect_analysis',
                'title': '技术效果对比规则',
                'description': '对比发明与现有技术的技术效果，判断是否产生预料不到的技术效果',
                'keywords': ['技术效果', '预料不到', '性能参数', '技术指标'],
                'priority': 'medium'
            },
            {
                'rule_id': 'NOVELTY_008',
                'rule_type': 'feature_combination',
                'title': '特征组合判断规则',
                'description': '判断技术特征的组合是否属于常规技术组合，或产生协同效应',
                'keywords': ['特征组合', '协同效应', '常规组合', '功能配合'],
                'priority': 'medium'
            },
            {
                'rule_id': 'NOVELTY_009',
                'rule_type': 'selection_invention',
                'title': '选择发明判断规则',
                'description': '判断是否为选择发明，考虑选择的范围、效果和是否属于常规选择',
                'keywords': ['选择发明', '数值范围', '优化选择', '预料不到效果'],
                'priority': 'medium'
            },
            {
                'rule_id': 'NOVELTY_010',
                'rule_type': 'use_invention',
                'title': '用途发明判断规则',
                'description': '判断是否为用途发明，考虑产品的已知性质、新用途的技术启示',
                'keywords': ['用途发明', '新用途', '技术启示', '产品性质'],
                'priority': 'medium'
            }
        ]

        # 特殊领域规则
        special_rules = [
            {
                'rule_id': 'NOVELTY_BIOTECH_001',
                'rule_type': 'biotech_sequence',
                'title': '生物序列新颖性规则',
                'description': '生物序列的新颖性判断，考虑序列同一性、功能差异和公开程度',
                'keywords': ['生物序列', '基因序列', '蛋白质', '同一性', '功能差异'],
                'priority': 'high',
                'domain': 'biotechnology'
            },
            {
                'rule_id': 'NOVELTY_BIOTECH_002',
                'rule_type': 'biotech_material',
                'title': '生物材料保藏规则',
                'description': '生物材料的保藏要求，考虑保藏日期、保藏单位和可获取性',
                'keywords': ['生物材料', '保藏要求', '保藏日期', '可获取性'],
                'priority': 'high',
                'domain': 'biotechnology'
            },
            {
                'rule_id': 'NOVELTY_CHEMICAL_001',
                'rule_type': 'chemical_compound',
                'title': '化学化合物新颖性规则',
                'description': '化学化合物的新颖性判断，考虑结构确认、制备方法和用途',
                'keywords': ['化学化合物', '结构确认', '制备方法', '用途'],
                'priority': 'high',
                'domain': 'chemistry'
            },
            {
                'rule_id': 'NOVELTY_CHEMICAL_002',
                'rule_type': 'chemical_combination',
                'title': '化学组合物规则',
                'description': '化学组合物的新颖性，考虑组分比例、协同效应和选择范围',
                'keywords': ['化学组合物', '组分比例', '协同效应', '选择范围'],
                'priority': 'medium',
                'domain': 'chemistry'
            },
            {
                'rule_id': 'NOVELTY_SOFTWARE_001',
                'rule_type': 'software_invention',
                'title': '软件发明新颖性规则',
                'description': '软件相关发明的新颖性判断，考虑技术方案、解决的技术问题和效果',
                'keywords': ['软件发明', '算法', '数据处理', '技术方案'],
                'priority': 'medium',
                'domain': 'software'
            },
            {
                'rule_id': 'NOVELTY_SOFTWARE_002',
                'rule_type': 'business_method',
                'title': '商业方法规则',
                'description': '商业方法相关发明的技术特征分析，排除纯商业规则',
                'keywords': ['商业方法', '技术特征', '数据处理', '技术手段'],
                'priority': 'low',
                'domain': 'software'
            },
            {
                'rule_id': 'NOVELTY_MECHANICAL_001',
                'rule_type': 'mechanical_structure',
                'title': '机械结构规则',
                'description': '机械结构的新颖性，考虑结构特征、连接关系和功能实现',
                'keywords': ['机械结构', '结构特征', '连接关系', '功能实现'],
                'priority': 'high',
                'domain': 'mechanical'
            },
            {
                'rule_id': 'NOVELTY_MECHANICAL_002',
                'rule_type': 'manufacturing_process',
                'title': '制造工艺规则',
                'description': '制造工艺的新颖性，考虑工艺参数、步骤顺序和设备改进',
                'keywords': ['制造工艺', '工艺参数', '步骤顺序', '设备改进'],
                'priority': 'medium',
                'domain': 'mechanical'
            }
        ]

        all_rules = core_rules + special_rules

        # 编码并存储规则
        vectors = []
        rule_ids = []

        for rule in all_rules:
            # 组合文本用于编码
            text = f"{rule['title']} {rule['description']} {' '.join(rule.get('keywords', []))}"
            vector = self._encode_text(text)

            # 存储规则向量
            rule_vector = RuleVector(
                rule_id=rule['rule_id'],
                rule_type=rule['rule_type'],
                vector=vector,
                metadata=rule
            )
            self.rule_vectors[rule['rule_id']] = rule_vector

            vectors.append(vector)
            rule_ids.append(rule['rule_id'])

            # 保存到数据库
            self._save_rule_to_db(rule, vector)

        # 构建FAISS索引
        if vectors:
            vectors_array = np.array(vectors).astype('float32')
            self.index = faiss.IndexFlatIP(self.dimension)
            self.index.add(vectors_array)

        logger.info(f"✅ 加载规则向量: {len(all_rules)} 条")

    def _save_rule_to_db(self, rule: Dict[str, Any], vector: np.ndarray):
        """保存规则到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        vector_blob = vector.tobytes()
        metadata_json = json.dumps({k: v for k, v in rule.items() if k != 'rule_id'})

        cursor.execute('''
            INSERT OR REPLACE INTO novelty_rules
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rule['rule_id'],
            rule['rule_type'],
            rule['title'],
            rule['description'],
            vector_blob,
            metadata_json,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    async def search_rules(self, query_text: str, rule_type: str = None,
                          domain: str = None, top_k: int = 10) -> List[SearchRule]:
        """搜索相关规则"""
        try:
            # 编码查询文本
            query_vector = self._encode_text(query_text)
            query_vector = query_vector.reshape(1, -1).astype('float32')

            # 搜索向量
            if self.index is None:
                return []

            scores, indices = self.index.search(query_vector, top_k * 2)  # 多搜一些用于过滤

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.rule_vectors):
                    continue

                rule_id = list(self.rule_vectors.keys())[idx]
                rule_vector = self.rule_vectors[rule_id]

                # 过滤条件
                if rule_type and rule_vector.rule_type != rule_type:
                    continue
                if domain and rule_vector.metadata.get('domain') != domain:
                    continue

                # 计算相关性分数（考虑多种因素）
                relevance_score = self._calculate_relevance_score(
                    query_text, rule_vector.metadata, score
                )

                # 获取使用次数
                usage_count = self._get_rule_usage_count(rule_id)

                search_rule = SearchRule(
                    rule_id=rule_vector.rule_id,
                    rule_type=rule_vector.rule_type,
                    title=rule_vector.metadata.get('title', ''),
                    description=rule_vector.metadata.get('description', ''),
                    similarity_score=float(score),
                    relevance_score=relevance_score,
                    application_count=usage_count
                )
                results.append(search_rule)

            # 按相关性分数排序
            results.sort(key=lambda x: x.relevance_score, reverse=True)

            return results[:top_k]

        except Exception as e:
            logger.error(f"❌ 规则搜索失败: {str(e)}")
            return []

    def _calculate_relevance_score(self, query_text: str, metadata: Dict[str, Any],
                                 similarity_score: float) -> float:
        """计算相关性分数"""
        # 基础相似度分数
        base_score = float(similarity_score)

        # 关键词匹配分数
        keywords = metadata.get('keywords', [])
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in query_text.lower())
        keyword_score = min(keyword_matches / len(keywords), 1.0) if keywords else 0

        # 优先级权重
        priority_weights = {'high': 1.2, 'medium': 1.0, 'low': 0.8}
        priority = metadata.get('priority', 'medium')
        priority_weight = priority_weights.get(priority, 1.0)

        # 综合分数
        relevance_score = base_score * 0.6 + keyword_score * 0.3 + priority_weight * 0.1

        return relevance_score

    def _get_rule_usage_count(self, rule_id: str) -> int:
        """获取规则使用次数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM rule_usage WHERE rule_id = ?',
            (rule_id,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def record_rule_usage(self, rule_id: str, patent_id: str, success_rate: float):
        """记录规则使用情况"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO rule_usage VALUES (NULL, ?, ?, ?, ?)',
            (rule_id, patent_id, datetime.now().isoformat(), success_rate)
        )
        conn.commit()
        conn.close()

    def get_rule_statistics(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总规则数
        cursor.execute('SELECT COUNT(*) FROM novelty_rules')
        total_rules = cursor.fetchone()[0]

        # 按类型统计
        cursor.execute("""
            SELECT rule_type, COUNT(*)
            FROM novelty_rules
            GROUP BY rule_type
        """)
        type_stats = dict(cursor.fetchall())

        # 按领域统计
        cursor.execute("""
            SELECT json_extract(metadata, '$.domain'), COUNT(*)
            FROM novelty_rules
            WHERE json_extract(metadata, '$.domain') IS NOT NULL
            GROUP BY json_extract(metadata, '$.domain')
        """)
        domain_stats = dict(cursor.fetchall())

        # 使用频率统计
        cursor.execute("""
            SELECT rule_id, COUNT(*) as usage_count
            FROM rule_usage
            GROUP BY rule_id
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        usage_stats = cursor.fetchall()

        conn.close()

        return {
            'total_rules': total_rules,
            'type_distribution': type_stats,
            'domain_distribution': domain_stats,
            'top_used_rules': usage_stats
        }

    def export_rules(self, output_path: str):
        """导出规则库"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'model_name': self.model_name,
            'dimension': self.dimension,
            'rules': []
        }

        for rule_id, rule_vector in self.rule_vectors.items():
            export_data['rules'].append({
                'rule_id': rule_vector.rule_id,
                'rule_type': rule_vector.rule_type,
                'metadata': rule_vector.metadata
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 规则库已导出到: {output_path}")

# 全局规则向量库实例
novelty_rule_vector_db = NoveltyRuleVectorDB()

# 测试代码
if __name__ == '__main__':
    import asyncio

    async def test_rule_vector_db():
        """测试规则向量数据库"""
        logger.info('🔍 测试新颖性规则向量数据库...')

        # 测试规则搜索
        query = '判断发明与现有技术的区别特征'
        rules = await novelty_rule_vector_db.search_rules(query, top_k=5)

        logger.info(f"\n📊 搜索结果: {len(rules)} 条规则")
        for rule in rules:
            logger.info(f"  - {rule.rule_id}: {rule.title} (相似度: {rule.similarity_score:.3f})")

        # 获取统计信息
        stats = novelty_rule_vector_db.get_rule_statistics()
        logger.info(f"\n📈 统计信息:")
        logger.info(f"  总规则数: {stats['total_rules']}")
        logger.info(f"  规则类型: {list(stats['type_distribution'].keys())}")

        # 导出规则库
        novelty_rule_vector_db.export_rules('patent-platform/workspace/data/novelty_rules_export.json')

        return True

    # 运行测试
    result = asyncio.run(test_rule_vector_db())
    logger.info(f"\n🎯 规则向量数据库测试: {'成功' if result else '失败'}")