#!/usr/bin/env python3
"""
综合技术词典系统
Comprehensive Technical Dictionary System

为专利分析提供全面的技术术语支持和领域适配
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import json
import logging
import pickle
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TermInfo:
    """术语信息"""
    text: str
    domain: str  # 所属领域
    category: str  # 术语类别
    importance: str  # 重要性：high/medium/low
    synonyms: List[str] = field(default_factory=list)  # 同义词
    related_terms: List[str] = field(default_factory=list)  # 相关术语
    definition: str | None = None  # 定义
    features: List[str] = field(default_factory=list)  # 特征标签
    frequency: int = 0  # 使用频率
    confidence: float = 1.0  # 置信度

class TechnicalDictionaryManager:
    """技术词典管理器"""

    def __init__(self, dict_path: str | None = None):
        self.dict_path = dict_path or 'patent-platform/workspace/data/technical_dictionary.json'
        self.terms: Dict[str, TermInfo] = {}
        self.domain_terms: Dict[str, List[str]] = defaultdict(list)
        self.category_terms: Dict[str, List[str]] = defaultdict(list)
        self.synonym_index: Dict[str, str] = {}  # 同义词到主词的映射
        self.is_loaded = False

    def load_dictionary(self):
        """加载词典"""
        try:
            if Path(self.dict_path).exists():
                with open(self.dict_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._deserialize_dictionary(data)
                logger.info(f"✅ 技术词典加载成功: {len(self.terms)} 个术语")
            else:
                logger.warning('⚠️ 词典文件不存在，加载默认词典')
                self._load_default_dictionary()
                self.save_dictionary()
        except Exception as e:
            logger.error(f"❌ 词典加载失败: {e}")
            self._load_default_dictionary()

        self.is_loaded = True
        self._build_indices()

    def _load_default_dictionary(self):
        """加载默认词典"""
        # 机械领域术语
        mechanical_terms = {
            '齿轮': {'domain': 'mechanical', 'category': 'component', 'importance': 'high'},
            '轴': {'domain': 'mechanical', 'category': 'component', 'importance': 'high'},
            '轴承': {'domain': 'mechanical', 'category': 'component', 'importance': 'high'},
            '传动': {'domain': 'mechanical', 'category': 'action', 'importance': 'high'},
            '机构': {'domain': 'mechanical', 'category': 'structure', 'importance': 'medium'},
            '装置': {'domain': 'mechanical', 'category': 'structure', 'importance': 'medium'},
            '设备': {'domain': 'mechanical', 'category': 'structure', 'importance': 'medium'},
            '离合器': {'domain': 'mechanical', 'category': 'component', 'importance': 'high'},
            '变速箱': {'domain': 'mechanical', 'category': 'assembly', 'importance': 'high'},
            '发动机': {'domain': 'mechanical', 'category': 'assembly', 'importance': 'high'},
        }

        # 电子领域术语
        electronic_terms = {
            '芯片': {'domain': 'electronic', 'category': 'component', 'importance': 'high'},
            '电路': {'domain': 'electronic', 'category': 'component', 'importance': 'high'},
            '传感器': {'domain': 'electronic', 'category': 'component', 'importance': 'high'},
            '控制器': {'domain': 'electronic', 'category': 'component', 'importance': 'high'},
            '处理器': {'domain': 'electronic', 'category': 'component', 'importance': 'high'},
            '模块': {'domain': 'electronic', 'category': 'component', 'importance': 'medium'},
            '单元': {'domain': 'electronic', 'category': 'component', 'importance': 'medium'},
            '集成电路': {'domain': 'electronic', 'category': 'component', 'importance': 'high'},
            '半导体': {'domain': 'electronic', 'category': 'material', 'importance': 'high'},
            '晶体管': {'domain': 'electronic', 'category': 'component', 'importance': 'high'},
        }

        # 软件领域术语
        software_terms = {
            '算法': {'domain': 'software', 'category': 'method', 'importance': 'high'},
            '模型': {'domain': 'software', 'category': 'method', 'importance': 'high'},
            '接口': {'domain': 'software', 'category': 'component', 'importance': 'medium'},
            '系统': {'domain': 'software', 'category': 'structure', 'importance': 'medium'},
            '程序': {'domain': 'software', 'category': 'software', 'importance': 'medium'},
            '数据': {'domain': 'software', 'category': 'resource', 'importance': 'medium'},
            '深度学习': {'domain': 'software', 'category': 'method', 'importance': 'high'},
            '神经网络': {'domain': 'software', 'category': 'method', 'importance': 'high'},
            '卷积神经网络': {'domain': 'software', 'category': 'method', 'importance': 'high'},
            '注意力机制': {'domain': 'software', 'category': 'method', 'importance': 'high'},
            '机器学习': {'domain': 'software', 'category': 'method', 'importance': 'high'},
            '人工智能': {'domain': 'software', 'category': 'field', 'importance': 'high'},
        }

        # 化学领域术语
        chemical_terms = {
            '化合物': {'domain': 'chemical', 'category': 'substance', 'importance': 'high'},
            '催化剂': {'domain': 'chemical', 'category': 'substance', 'importance': 'high'},
            '溶剂': {'domain': 'chemical', 'category': 'substance', 'importance': 'medium'},
            '反应器': {'domain': 'chemical', 'category': 'equipment', 'importance': 'high'},
            '分离': {'domain': 'chemical', 'category': 'process', 'importance': 'medium'},
            '纯化': {'domain': 'chemical', 'category': 'process', 'importance': 'medium'},
            '合成': {'domain': 'chemical', 'category': 'process', 'importance': 'high'},
            '聚合': {'domain': 'chemical', 'category': 'process', 'importance': 'high'},
            '组合物': {'domain': 'chemical', 'category': 'mixture', 'importance': 'high'},
            '混合物': {'domain': 'chemical', 'category': 'mixture', 'importance': 'medium'},
        }

        # 生物技术领域术语
        biotech_terms = {
            '基因': {'domain': 'biotech', 'category': 'molecule', 'importance': 'high'},
            '蛋白质': {'domain': 'biotech', 'category': 'molecule', 'importance': 'high'},
            '抗体': {'domain': 'biotech', 'category': 'molecule', 'importance': 'high'},
            '细胞': {'domain': 'biotech', 'category': 'organism', 'importance': 'high'},
            '序列': {'domain': 'biotech', 'category': 'structure', 'importance': 'high'},
            '载体': {'domain': 'biotech', 'category': 'vector', 'importance': 'high'},
            '表达': {'domain': 'biotech', 'category': 'process', 'importance': 'medium'},
            '克隆': {'domain': 'biotech', 'category': 'process', 'importance': 'medium'},
            '突变': {'domain': 'biotech', 'category': 'process', 'importance': 'medium'},
        }

        # 医疗领域术语
        medical_terms = {
            '诊断': {'domain': 'medical', 'category': 'application', 'importance': 'high'},
            '治疗': {'domain': 'medical', 'category': 'application', 'importance': 'high'},
            '药物': {'domain': 'medical', 'category': 'substance', 'importance': 'high'},
            '医疗器械': {'domain': 'medical', 'category': 'device', 'importance': 'high'},
            '医学影像': {'domain': 'medical', 'category': 'method', 'importance': 'high'},
            'CT': {'domain': 'medical', 'category': 'equipment', 'importance': 'medium'},
            'MRI': {'domain': 'medical', 'category': 'equipment', 'importance': 'medium'},
            'X光': {'domain': 'medical', 'category': 'equipment', 'importance': 'medium'},
            '超声': {'domain': 'medical', 'category': 'equipment', 'importance': 'medium'},
        }

        # 通信领域术语
        communication_terms = {
            '通信': {'domain': 'communication', 'category': 'field', 'importance': 'high'},
            '信号': {'domain': 'communication', 'category': 'resource', 'importance': 'high'},
            '网络': {'domain': 'communication', 'category': 'structure', 'importance': 'high'},
            '基站': {'domain': 'communication', 'category': 'equipment', 'importance': 'high'},
            '天线': {'domain': 'communication', 'category': 'component', 'importance': 'high'},
            '频谱': {'domain': 'communication', 'category': 'resource', 'importance': 'medium'},
            '协议': {'domain': 'communication', 'category': 'standard', 'importance': 'high'},
            '编码': {'domain': 'communication', 'category': 'process', 'importance': 'medium'},
            '调制': {'domain': 'communication', 'category': 'process', 'importance': 'medium'},
            '5G': {'domain': 'communication', 'category': 'standard', 'importance': 'high'},
        }

        # 合并所有术语
        all_terms = {
            **mechanical_terms,
            **electronic_terms,
            **software_terms,
            **chemical_terms,
            **biotech_terms,
            **medical_terms,
            **communication_terms
        }

        # 添加同义词
        synonyms = {
            '深度学习': ['深度神经网络', 'DNN'],
            '卷积神经网络': ['CNN', '卷积网络'],
            '注意力机制': ['注意力', 'Attention机制'],
            '芯片': ['集成电路', 'IC'],
            '传感器': ['感应器', '探测器件'],
            '算法': ['运算法则', '计算方法'],
            '装置': ['设备', '器械', '器具'],
            '系统': ['体系', '架构'],
            '方法': ['方式', '途径', '手段'],
            'CT': ['计算机断层扫描', 'CT扫描'],
            'MRI': ['磁共振成像', '核磁共振'],
        }

        # 创建术语对象
        for term_text, info in all_terms.items():
            term_info = TermInfo(
                text=term_text,
                domain=info['domain'],
                category=info['category'],
                importance=info['importance'],
                synonyms=synonyms.get(term_text, []),
                confidence=1.0
            )
            self.terms[term_text] = term_info

        # 构建同义词索引
        for main_term, syn_list in synonyms.items():
            for syn in syn_list:
                self.synonym_index[syn] = main_term

    def _deserialize_dictionary(self, data: Dict):
        """反序列化词典数据"""
        self.terms = {}
        for term_text, term_data in data.get('terms', {}).items():
            term_info = TermInfo(
                text=term_text,
                domain=term_data['domain'],
                category=term_data['category'],
                importance=term_data['importance'],
                synonyms=term_data.get('synonyms', []),
                related_terms=term_data.get('related_terms', []),
                definition=term_data.get('definition'),
                features=term_data.get('features', []),
                frequency=term_data.get('frequency', 0),
                confidence=term_data.get('confidence', 1.0)
            )
            self.terms[term_text] = term_info

        # 加载同义词索引
        self.synonym_index = data.get('synonym_index', {})

    def _build_indices(self):
        """构建索引"""
        self.domain_terms = defaultdict(list)
        self.category_terms = defaultdict(list)

        for term_text, term_info in self.terms.items():
            self.domain_terms[term_info.domain].append(term_text)
            self.category_terms[term_info.category].append(term_text)

    def add_term(self, term_text: str, domain: str, category: str, importance: str = 'medium',
                 synonyms: Optional[List[str] = None, definition: str | None = None):
        """添加新术语"""
        term_info = TermInfo(
            text=term_text,
            domain=domain,
            category=category,
            importance=importance,
            synonyms=synonyms or [],
            definition=definition
        )

        self.terms[term_text] = term_info

        # 更新索引
        self.domain_terms[domain].append(term_text)
        self.category_terms[category].append(term_text)

        # 更新同义词索引
        if synonyms:
            for syn in synonyms:
                self.synonym_index[syn] = term_text

    def search_term(self, term: str) -> TermInfo | None:
        """搜索术语"""
        # 精确匹配
        if term in self.terms:
            return self.terms[term]

        # 同义词匹配
        if term in self.synonym_index:
            main_term = self.synonym_index[term]
            return self.terms.get(main_term)

        # 模糊匹配
        best_match = None
        best_score = 0

        for dict_term, term_info in self.terms.items():
            # 完全包含
            if term in dict_term or dict_term in term:
                score = len(term) / len(dict_term) if len(dict_term) > len(term) else len(dict_term) / len(term)
                if score > best_score:
                    best_score = score
                    best_match = term_info

        return best_match if best_score > 0.7 else None

    def get_domain_terms(self, domain: str) -> List[str]:
        """获取领域术语"""
        return self.domain_terms.get(domain, [])

    def get_category_terms(self, category: str) -> List[str]:
        """获取类别术语"""
        return self.category_terms.get(category, [])

    def extract_terms_from_text(self, text: str) -> List[Tuple[str, TermInfo, int, int]]:
        """从文本中提取术语"""
        extracted_terms = []

        # 按长度排序，优先匹配长术语
        sorted_terms = sorted(self.terms.keys(), key=len, reverse=True)

        for term in sorted_terms:
            # 查找术语在文本中的所有位置
            start = 0
            while True:
                pos = text.find(term, start)
                if pos == -1:
                    break

                # 检查边界
                if self._is_term_boundary(text, pos, pos + len(term)):
                    term_info = self.terms[term]
                    extracted_terms.append((term, term_info, pos, pos + len(term)))

                start = pos + 1

        # 按位置排序
        extracted_terms.sort(key=lambda x: x[2])

        return extracted_terms

    def _is_term_boundary(self, text: str, start: int, end: int) -> bool:
        """检查是否为术语边界"""
        # 检查前面字符
        if start > 0:
            prev_char = text[start - 1]
            if prev_char.isalnum() or prev_char in '一二三四五六七八九十':
                return False

        # 检查后面字符
        if end < len(text):
            next_char = text[end]
            if next_char.isalnum() or next_char in '一二三四五六七八九十':
                return False

        return True

    def save_dictionary(self):
        """保存词典"""
        # 确保目录存在
        Path(self.dict_path).parent.mkdir(parents=True, exist_ok=True)

        # 序列化数据
        data = {
            'terms': {},
            'synonym_index': self.synonym_index
        }

        for term_text, term_info in self.terms.items():
            data['terms'][term_text] = {
                'domain': term_info.domain,
                'category': term_info.category,
                'importance': term_info.importance,
                'synonyms': term_info.synonyms,
                'related_terms': term_info.related_terms,
                'definition': term_info.definition,
                'features': term_info.features,
                'frequency': term_info.frequency,
                'confidence': term_info.confidence
            }

        # 保存文件
        with open(self.dict_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 技术词典已保存: {self.dict_path}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取词典统计信息"""
        stats = {
            'total_terms': len(self.terms),
            'domain_distribution': {},
            'category_distribution': {},
            'importance_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'synonym_pairs': len(self.synonym_index)
        }

        for term_info in self.terms.values():
            # 领域分布
            stats['domain_distribution'][term_info.domain] = \
                stats['domain_distribution'].get(term_info.domain, 0) + 1

            # 类别分布
            stats['category_distribution'][term_info.category] = \
                stats['category_distribution'].get(term_info.category, 0) + 1

            # 重要性分布
            stats['importance_distribution'][term_info.importance] += 1

        return stats

class TechnicalDictionaryEnhancer:
    """技术词典增强器"""

    def __init__(self, dict_manager: TechnicalDictionaryManager):
        self.dict_manager = dict_manager

    def enhance_from_patents(self, patent_texts: List[str]):
        """从专利文本中增强词典"""
        logger.info(f"🚀 从 {len(patent_texts)} 个专利文本中增强词典")

        # 提取潜在术语
        potential_terms = self._extract_potential_terms(patent_texts)

        # 添加新术语
        added_count = 0
        for term, confidence in potential_terms:
            if term not in self.dict_manager.terms and term not in self.dict_manager.synonym_index:
                # 推断领域和类别
                domain, category = self._infer_domain_category(term)

                self.dict_manager.add_term(
                    term_text=term,
                    domain=domain,
                    category=category,
                    importance='medium',
                    confidence=confidence
                )
                added_count += 1

        logger.info(f"✅ 词典增强完成，新增 {added_count} 个术语")

    def _extract_potential_terms(self, texts: List[str]) -> List[Tuple[str, float]]:
        """提取潜在术语"""
        potential_terms = []

        # 技术术语模式
        patterns = [
            r'([^，。；！？]*(?:装置|设备|系统|平台|架构|框架|模块|单元))',
            r'([^，。；！？]*(：|：|是|为|包括|包含)([^，。；！？]*(?:方法|技术|算法|方案|策略)))[^，。；！？]*',
            r'([^，。；！？]*(?:器|仪|表|计|阀|泵|机|管|线|板|片|膜|层|网|栅|阵列))',
            r'([^，。；！？]*[A-Z]{2,}[^，。；！？]*)',
        ]

        term_counts = defaultdict(int)

        for text in texts:
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if match.groups():
                        for group in match.groups():
                            if group and len(group.strip()) > 1:
                                term = group.strip()
                                # 过滤常见词
                                if not self._is_common_word(term):
                                    term_counts[term] += 1

        # 计算置信度
        total_texts = len(texts)
        for term, count in term_counts.items():
            confidence = min(count / total_texts, 1.0)
            if confidence > 0.1:  # 至少出现在10%的文本中
                potential_terms.append((term, confidence))

        # 按置信度排序
        potential_terms.sort(key=lambda x: x[1], reverse=True)

        return potential_terms[:100]  # 返回前100个

    def _is_common_word(self, word: str) -> bool:
        """判断是否为常见词"""
        common_words = {
            '技术', '方法', '系统', '装置', '设备', '一种', '包括', '包含', '具有',
            '可以', '能够', '用于', '实现', '获得', '提高', '增加', '减少', '改善',
            '本发明', '该', '上述', '以下', '所述', '其中', '因此', '此外'
        }
        return word in common_words

    def _infer_domain_category(self, term: str) -> Tuple[str, str]:
        """推断术语的领域和类别"""
        # 基于关键词推断
        if any(keyword in term for keyword in ['基因', '蛋白', '细胞', '抗体', '序列']):
            return 'biotech', 'molecule'
        elif any(keyword in term for keyword in ['化合', '催化', '溶剂', '反应', '合成']):
            return 'chemical', 'substance'
        elif any(keyword in term for keyword in ['学习', '网络', '算法', '模型', '数据']):
            return 'software', 'method'
        elif any(keyword in term for keyword in ['诊断', '治疗', '医疗', '医学', '药物']):
            return 'medical', 'application'
        elif any(keyword in term for keyword in ['通信', '信号', '网络', '基站', '天线']):
            return 'communication', 'component'
        elif any(keyword in term for keyword in ['电路', '芯片', '传感器', '控制', '处理']):
            return 'electronic', 'component'
        else:
            return 'general', 'unknown'

# 全局实例
_dictionary_manager = None

def get_dictionary_manager() -> TechnicalDictionaryManager:
    """获取全局词典管理器实例"""
    global _dictionary_manager
    if _dictionary_manager is None:
        _dictionary_manager = TechnicalDictionaryManager()
        _dictionary_manager.load_dictionary()
    return _dictionary_manager

# 测试函数
def test_technical_dictionary():
    """测试技术词典系统"""
    logger.info('🧪 测试技术词典系统')
    logger.info(str('=' * 60))

    # 获取词典管理器
    dict_manager = get_dictionary_manager()

    # 显示统计信息
    stats = dict_manager.get_statistics()
    logger.info(f"\n📊 词典统计:")
    logger.info(f"总术语数: {stats['total_terms']}")
    logger.info(f"同义词对数: {stats['synonym_pairs']}")
    logger.info(f"领域分布: {stats['domain_distribution']}")
    logger.info(f"类别分布: {dict(list(stats['category_distribution'].items())[:5])}")

    # 测试搜索功能
    test_terms = ['深度学习', 'CNN', '芯片', '传感器', '算法', '不存在的词']
    logger.info(f"\n🔍 术语搜索测试:")
    for term in test_terms:
        result = dict_manager.search_term(term)
        if result:
            logger.info(f"  • {term} → {result.text} ({result.domain}/{result.category})")
            if result.synonyms:
                logger.info(f"    同义词: {result.synonyms}")
        else:
            logger.info(f"  • {term} → 未找到")

    # 测试文本提取
    test_text = """
    一种基于深度学习的医疗图像诊断装置，包括图像采集模块、预处理模块、
    特征提取模块和分类诊断模块。该装置采用改进的卷积神经网络和注意力机制，
    准确率提升30%，处理速度提高2倍。
    """

    logger.info(f"\n📝 文本术语提取测试:")
    logger.info(f"测试文本: {test_text[:50]}...")

    extracted = dict_manager.extract_terms_from_text(test_text)
    for term, info, start, end in extracted[:10]:
        logger.info(f"  • {term} ({info.domain}/{info.importance}) [{start}:{end}]")

if __name__ == '__main__':
    test_technical_dictionary()