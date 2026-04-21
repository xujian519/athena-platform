#!/usr/bin/env python3
"""
增强版技术特征提取器
Enhanced Technical Feature Extractor

集成语义理解模型和专业技术词典
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# 模拟语义理解模型（实际使用时应接入真实的语义模型）
class MockSemanticModel:
    """模拟语义理解模型"""

    def __init__(self):
        self.is_loaded = False

    def load_model(self, model_path: str):
        """加载模型"""
        # 实际实现：加载BERT、RoBERTa等预训练模型
        logger.info(f"🔄 正在加载语义理解模型: {model_path}")
        self.is_loaded = True
        return True

    def encode_text(self, text: str) -> np.ndarray:
        """文本编码"""
        if not self.is_loaded:
            # 返回模拟编码
            return random((768))

        # 实际实现：使用模型进行文本编码
        return random((768))

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """实体识别"""
        entities = [
            {'text': '图像采集模块', 'type': 'MODULE', 'start': 0, 'end': 6},
            {'text': '预处理模块', 'type': 'MODULE', 'start': 10, 'end': 16},
            {'text': '卷积神经网络', 'type': 'TECHNOLOGY', 'start': 30, 'end': 37}
        ]
        return entities

    def extract_relations(self, text: str, entities: List[Dict]) -> List[Dict[str, Any]]:
        """关系抽取"""
        relations = [
            {'subject': '图像采集模块', 'relation': '连接到', 'object': '预处理模块'},
            {'subject': '特征提取模块', 'relation': '采用', 'object': '卷积神经网络'}
        ]
        return relations

class TechnicalDictionary:
    """技术词典系统"""

    def __init__(self):
        self.terms = {}
        self.domain_terms = {}
        self.load_default_dictionaries()

    def load_default_dictionaries(self):
        """加载默认词典"""
        # 技术组件词典
        component_terms = {
            '机械': ['齿轮', '轴', '轴承', '传动', '机构', '装置', '设备'],
            '电子': ['芯片', '电路', '传感器', '控制器', '处理器', '模块'],
            '化学': ['化合物', '催化剂', '溶剂', '反应器', '分离', '纯化'],
            '软件': ['算法', '模型', '模块', '接口', '系统', '程序']
        }

        # 技术动作词典
        action_terms = {
            'process': ['处理', '计算', '分析', '识别', '检测', '提取'],
            'connect': ['连接', '固定', '安装', '装配', '组合'],
            'control': ['控制', '调节', '管理', '操作', '驱动'],
            'transform': ['转换', '变换', '生成', '输出', '产生']
        }

        # 技术参数词典
        parameter_terms = {
            'physical': ['温度', '压力', '速度', '尺寸', '重量', '材料'],
            'chemical': ['浓度', '纯度', 'pH值', '分子量', '含量', '比例'],
            'digital': ['分辨率', '精度', '带宽', '频率', '内存', '吞吐量']
        }

        self.domain_terms['component'] = component_terms
        self.domain_terms['action'] = action_terms
        self.domain_terms['parameter'] = parameter_terms

        # 合并所有术语
        for domain, terms in self.domain_terms.items():
            for term in terms:
                self.terms[term] = {
                    'domain': domain,
                    'type': domain[:-1],  # 去掉复数
                    'importance': 'high' if '机械' in term else 'medium'
                }

    def add_term(self, term: str, domain: str, category: str, importance: str = 'medium'):
        """添加术语"""
        self.terms[term] = {
            'domain': domain,
            'type': category,
            'importance': importance
        }

    def search_term(self, term: str) -> Dict | None:
        """搜索术语"""
        # 精确匹配
        if term in self.terms:
            return self.terms[term]

        # 模糊匹配
        for key, value in self.terms.items():
            if term in key or key in term:
                return value

        return None

    def get_domain_terms(self, domain: str) -> List[str]:
        """获取领域术语"""
        domain_terms = []
        for term, info in self.terms.items():
            if info['domain'] == domain:
                domain_terms.append(term)
        return domain_terms

    def save_dictionary(self, file_path: str):
        """保存词典"""
        dictionary_data = {
            'terms': self.terms,
            'domain_terms': self.domain_terms
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dictionary_data, f, ensure_ascii=False, indent=2)

    def load_dictionary(self, file_path: str):
        """加载词典"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                dictionary_data = json.load(f)
                self.terms = dictionary_data.get('terms', {})
                self.domain_terms = dictionary_data.get('domain_terms', {})
            logger.info(f"✅ 技术词典加载完成: {file_path}")
        except FileNotFoundError:
            logger.info(f"⚠️ 词典文件不存在，使用默认词典: {file_path}")
        except Exception as e:
            logger.info(f"❌ 词典加载失败: {e}")

class EnhancedTechnicalAnalyzer:
    """增强版技术分析器"""

    def __init__(self):
        self.semantic_model = MockSemanticModel()
        self.technical_dict = TechnicalDictionary()
        self.domain_models = self._init_domain_models()

    def _init_domain_models(self):
        """初始化领域模型"""
        return {
            'mechanical': {
                'key_concepts': ['结构', '运动', '传动', '力'],
                'analysis_focus': ['几何形状', '材料属性', '运动关系', '装配关系'],
                'feature_patterns': [
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([结构|机构|装置|设备])",
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([连接|固定|安装|配合])",
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([材料|合金|塑料|金属])"
                ]
            },
            'electronic': {
                'key_concepts': ['电路', '信号', '处理', '控制'],
                'analysis_focus': ['电路设计', '信号处理', '功耗', '频率'],
                'feature_patterns': [
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([电路|芯片|模块|单元])",
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([信号|数据|信息])",
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([控制|调节|处理|计算])"
                ]
            },
            'chemical': {
                'key_concepts': ['反应', '合成', '分离', '纯化'],
                'analysis_focus': ['化学组成', '反应条件', '物理性质', '生物活性'],
                'feature_patterns': [
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([化合物|组合物|混合物])",
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([反应|合成|制备|提取])",
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([浓度|比例|含量|纯度])"
                ]
            },
            'software': {
                'key_concepts': ['算法', '数据', '模型', '系统'],
                'analysis_focus': ['算法结构', '数据处理', '性能指标', '接口设计'],
                'feature_patterns': [
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([算法|模型|方法|技术])",
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([数据|信息|特征|向量])",
                    r"([^\uff0c\uff1b\uff1a\uff0e]*)([系统|平台|框架|架构])"
                ]
            }
        }

    def load_models(self, config: Dict[str, Any]):
        """加载配置的模型"""
        logger.info("\n🔄 加载语义理解模型和专业词典...")

        # 加载语义模型
        semantic_config = config.get('semantic_model', {})
        if semantic_config.get('model_path'):
            self.semantic_model.load_model(semantic_config['model_path'])
            logger.info(f"✅ 语义模型加载完成: {semantic_config['model_path']}")

        # 加载技术词典
        dict_config = config.get('technical_dictionary', {})
        if dict_config.get('custom_dictionary_path'):
            self.technical_dict.load_dictionary(dict_config['custom_dictionary_path'])
            logger.info(f"✅ 技术词典加载完成: {dict_config['custom_dictionary_path']}")

        # 添加自定义术语
        custom_terms = dict_config.get('custom_terms', [])
        for term in custom_terms:
            self.technical_dict.add_term(**term)

        if custom_terms:
            logger.info(f"✅ 添加自定义术语: {len(custom_terms)} 个")

    def enhanced_text_understanding(self, text: str) -> Dict[str, Any]:
        """增强版文本理解"""
        understanding_result = {
            'original_text': text,
            'semantic_encoding': None,
            'entities': [],
            'relations': [],
            'domain_terms': [],
            'technical_score': 0,
            'domain': 'unknown'
        }

        # 1. 语义编码
        if self.semantic_model.is_loaded:
            understanding_result['semantic_encoding'] = self.semantic_model.encode_text(text)

        # 2. 实体识别
        understanding_result['entities'] = self.semantic_model.extract_entities(text)

        # 3. 关系抽取
        if understanding_result['entities']:
            understanding_result['relations'] = self.semantic_model.extract_relations(
                text, understanding_result['entities']
            )

        # 4. 技术术语匹配
        matched_terms = []
        for term in self.technical_dict.terms.keys():
            if term in text:
                matched_terms.append(term)
        understanding_result['domain_terms'] = matched_terms

        # 5. 技术性评分
        domain_counts = {}
        for term in matched_terms:
            domain = self.technical_dict.terms[term]['domain']
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # 确定主要领域
        if domain_counts:
            main_domain = max(domain_counts, key=domain_counts.get)
            understanding_result['domain'] = main_domain
            understanding_result['technical_score'] = domain_counts[main_domain]

        return understanding_result

    def enhanced_feature_extraction(self, claim_text: str, claim_number: int) -> Dict[str, Any]:
        """增强版特征提取"""
        logger.info(f"\n🔍 增强特征提取 - 权利要求{claim_number}")

        # 1. 文本理解
        text_understanding = self.enhanced_text_understanding(claim_text)

        # 2. 基于领域模型提取特征
        domain = text_understanding['domain']
        if domain in self.domain_models:
            domain_model = self.domain_models[domain]
            features = self._extract_domain_specific_features(claim_text, claim_number, domain_model)
        else:
            features = self._extract_general_features(claim_text, claim_number)

        # 3. 语义增强
        for feature in features:
            # 添加语义信息
            feature['semantic_embedding'] = None
            if self.semantic_model.is_loaded:
                feature['semantic_embedding'] = self.semantic_model.encode_text(feature['text'])

            # 添加词典信息
            term_info = self.technical_dict.search_term(feature['text'])
            if term_info:
                feature['domain'] = term_info['domain']
                feature['importance'] = term_info['importance']

        # 4. 实体和关系信息
        result = {
            'claim_number': claim_number,
            'text_understanding': text_understanding,
            'extracted_features': features,
            'identified_entities': text_understanding['entities'],
            'identified_relations': text_understanding['relations'],
            'enhanced_metadata': {
                'domain': domain,
                'technical_score': text_understanding['technical_score'],
                'matched_terms': len(text_understanding['domain_terms'])
            }
        }

        return result

    def _extract_domain_specific_features(self, text: str, claim_number: int, domain_model: Dict):
        """领域特定特征提取"""
        features = []
        import re

        for pattern in domain_model['feature_patterns']:
            matches = re.finditer(pattern, text)
            for match in matches:
                domain_name = domain_model.get('name', 'GENERIC')
                feature = {
                    'feature_id': f"{domain_name}_{claim_number}_{len(features)}",
                    'text': match.group(0),
                    'type': domain_model['key_concepts'][0] if domain_model['key_concepts'] else 'unknown',
                    'position': (match.start(), match.end()),
                    'domain': domain_name,
                    'confidence': 0.9  # 基于模式匹配的置信度
                }
                features.append(feature)

        return features

    def _extract_general_features(self, text: str, claim_number: int):
        """通用特征提取"""
        # 使用基本的特征提取逻辑
        from tech_feature_extractor import TechnicalFeatureExtractor
        base_extractor = TechnicalFeatureExtractor()
        return base_extractor.extract_claim_features(text, claim_number)

    def generate_feature_analysis_report(self, analysis_result: Dict) -> str:
        """生成特征分析报告"""
        report = []

        # 基本信息
        metadata = analysis_result['enhanced_metadata']
        report.append(f"权利要求{analysis_result['claim_number']}特征分析报告")
        report.append('=' * 50)
        report.append(f"技术领域: {metadata['domain']}")
        report.append(f"技术性评分: {metadata['technical_score']}")
        report.append(f"匹配术语数: {metadata['matched_terms']}")

        # 文本理解
        text_understanding = analysis_result['text_understanding']
        report.append("\n文本理解结果:")
        report.append(f"- 识别实体: {len(text_understanding['entities'])}个")
        report.append(f"- 识别关系: {len(text_understanding['relations'])}个")

        # 提取特征
        features = analysis_result['extracted_features']
        report.append(f"\n提取特征: {len(features)}个")

        # 按类型统计
        type_stats = {}
        for feature in features:
            ftype = feature.get('type', 'unknown')
            type_stats[ftype] = type_stats.get(ftype, 0) + 1

        report.append("\n特征类型分布:")
        for ftype, count in type_stats.items():
            report.append(f"- {ftype}: {count}个")

        # 重要特征
        important_features = [f for f in features if f.get('importance') == 'high']
        if important_features:
            report.append(f"\n重要特征({len(important_features)}个):")
            for i, feature in enumerate(important_features[:5]):  # 显示前5个
                report.append(f"{i+1}. {feature['text']}")

        return "\n".join(report)

# 配置示例
def get_enhanced_config():
    """获取增强配置示例"""
    return {
        'semantic_model': {
            'model_path': 'models/bert-base-chinese',
            'model_type': 'bert',
            'language': 'zh',
            'max_sequence_length': 512
        },
        'technical_dictionary': {
            'custom_dictionary_path': 'patent-platform/workspace/data/technical_dictionary.json',
            'custom_terms': [
                {
                    'term': '深度神经网络',
                    'domain': 'software',
                    'category': 'technology',
                    'importance': 'high'
                },
                {
                    'term': '注意力机制',
                    'domain': 'software',
                    'category': 'algorithm',
                    'importance': 'high'
                }
            ]
        }
    }

# 演示函数
def demonstrate_enhanced_system():
    """演示增强版系统"""
    logger.info('🚀 增强版技术特征提取系统演示')
    logger.info(str('=' * 80))

    # 初始化系统
    analyzer = EnhancedTechnicalAnalyzer()

    # 加载配置
    config = get_enhanced_config()
    analyzer.load_models(config)

    # 测试文本
    test_claim = """
    一种基于深度学习的医疗图像诊断装置，其特征在于包括：
    图像采集模块，用于采集多模态医疗图像数据；
    预处理模块，采用自适应算法进行图像标准化和增强；
    特征提取模块，使用改进的残差网络和注意力机制提取深层特征；
    诊断模块，通过多尺度特征融合实现高精度疾病分类。
    """

    # 执行增强分析
    result = analyzer.enhanced_feature_extraction(test_claim, 1)

    # 生成报告
    report = analyzer.generate_feature_analysis_report(result)
    logger.info(str(report))

    # 保存技术词典
    analyzer.technical_dict.save_dictionary('patent-platform/workspace/data/custom_technical_dict.json')
    logger.info("\n✅ 技术词典已保存")

if __name__ == '__main__':
    demonstrate_enhanced_system()