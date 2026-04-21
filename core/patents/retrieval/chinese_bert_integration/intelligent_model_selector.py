#!/usr/bin/env python3
"""
智能模型选择器
Intelligent Model Selector

根据查询内容自动选择最适合的BERT模型
"""

import logging
import re
from typing import Any

import jieba
from model_manager import ChineseBERTModelManager

# 配置日志
logger = logging.getLogger(__name__)

class IntelligentModelSelector:
    """智能模型选择器"""

    def __init__(self):
        """初始化选择器"""
        self.model_manager = ChineseBERTModelManager()

        # 关键词词典
        self.keyword_patterns = {
            'patent': {
                'keywords': [
                    '专利', '发明', '实用新型', '外观设计', '权利要求', '说明书',
                    '优先权', '新颖性', '创造性', '技术方案', '实施例',
                    '现有技术', '技术领域', '背景技术', '发明内容'
                ],
                'ipc_patterns': [
                    r'A[0-9]{2}[A-Z]',  # IPC分类号格式
                    r'C[0-9]{2}[A-Z]',  # CPC分类号格式
                ],
                'weight': 1.0
            },
            'legal': {
                'keywords': [
                    '法条', '法规', '法律', '条款', '规定', '实施细则',
                    '合同', '协议', '条款', '责任', '义务', '权利',
                    '法院', '判决', '诉讼', '仲裁', '律师', '法官'
                ],
                'patterns': [
                    r'第[一二三四五六七八九十\d]+条',  # 法条引用格式
                    r'专利法第\d+条',  # 专利法条文
                ],
                'weight': 1.0
            },
            'medical': {
                'keywords': [
                    '医疗', '医院', '诊断', '治疗', '药物', '药品',
                    '疾病', '病症', '手术', '医疗器械', '临床试验',
                    '患者', '医生', '护士', '病理', '药理', '疗效'
                ],
                'weight': 0.8
            },
            'technical': {
                'keywords': [
                    '算法', '系统', '装置', '设备', '方法', '技术',
                    '计算机', '软件', '程序', '代码', '数据',
                    '网络', '服务器', '数据库', '人工智能', '机器学习'
                ],
                'weight': 0.6
            },
            'financial': {
                'keywords': [
                    '金融', '银行', '投资', '理财', '保险', '证券',
                    '股票', '基金', '债券', '贷款', '利息', '汇率',
                    '财务', '会计', '审计', '税务', '预算'
                ],
                'weight': 0.6
            }
        }

        # 查询复杂度分析规则
        self.complexity_rules = {
            'simple': {
                'max_length': 50,
                'max_terms': 10,
                'models': ['bge-base-zh-v1.5']
            },
            'medium': {
                'max_length': 200,
                'max_terms': 30,
                'models': ['bge-base-zh-v1.5', 'chinese-legal-electra']
            },
            'complex': {
                'max_length': float('inf'),
                'max_terms': float('inf'),
                'models': ['bge-large-zh-v1.5', 'chinese-legal-electra']
            }
        }

    def analyze_query(self, query: str) -> dict[str, Any]:
        """分析查询特征

        Args:
            query: 查询文本

        Returns:
            查询分析结果
        """
        analysis = {
            'length': len(query),
            'terms': [],
            'domain_scores': {},
            'complexity': 'medium',
            'special_features': []
        }

        # 分词
        analysis['terms'] = list(jieba.cut(query))
        analysis['unique_terms'] = set(analysis['terms'])
        analysis['term_count'] = len(analysis['unique_terms'])

        # 领域分析
        for domain, config in self.keyword_patterns.items():
            score = 0
            matched_keywords = []

            # 关键词匹配
            for keyword in config['keywords']:
                if keyword in query:
                    score += config['weight']
                    matched_keywords.append(keyword)

            # 模式匹配
            if 'patterns' in config:
                for pattern in config['patterns']:
                    if re.search(pattern, query):
                        score += config['weight'] * 1.5  # 模式匹配权重更高
                        matched_keywords.append(f"pattern:{pattern}")

            analysis['domain_scores'][domain] = {
                'score': score,
                'matched_keywords': matched_keywords,
                'weight': config['weight']
            }

        # 复杂度分析
        query_length = analysis['length']
        term_count = analysis['term_count']

        if query_length <= self.complexity_rules['simple']['max_length'] and term_count <= self.complexity_rules['simple']['max_terms']:
            analysis['complexity'] = 'simple'
        elif query_length > self.complexity_rules['medium']['max_length'] or term_count > self.complexity_rules['medium']['max_terms']:
            analysis['complexity'] = 'complex'

        # 特殊特征检测
        if re.search(r'[；。！？]', query):
            analysis['special_features'].append('multiple_sentences')
        if len(re.findall(r'[a-zA-Z]+', query)) > 3:
            analysis['special_features'].append('contains_english')
        if re.search(r'[①②③④⑤⑥⑦⑧⑨⑩]', query):
            analysis['special_features'].append('has_numbered_items')
        if len(query) > 1000:
            analysis['special_features'].append('long_document')

        return analysis

    def select_model(
        self,
        query: str,
        preferred_models: list[str] | None = None,
        speed_preference: str = 'medium'
    ) -> tuple[str, dict[str, Any]]:
        """智能选择最适合的模型

        Args:
            query: 查询文本
            preferred_models: 首选模型列表
            speed_preference: 速度偏好 ('fast', 'medium', 'slow')

        Returns:
            (模型名称, 选择原因)
        """
        # 分析查询
        analysis = self.analyze_query(query)

        # 如果有首选模型，优先使用
        if preferred_models:
            for model in preferred_models:
                if model in self.model_manager.model_configs:
                    return model, {
                        'reason': 'preferred_model',
                        'analysis': analysis
                    }

        # 根据领域选择模型
        main_domain = max(analysis['domain_scores'].items(), key=lambda x: x[1]['score'])[0]
        main_score = analysis['domain_scores'][main_domain]['score']

        # 根据领域和复杂度选择
        complexity = analysis['complexity']
        candidate_models = self.complexity_rules[complexity]['models']

        # 领域特定的模型偏好
        domain_preferences = {
            'patent': ['bge-large-zh-v1.5', 'bge-base-zh-v1.5'],
            'legal': ['chinese-legal-electra', 'bge-large-zh-v1.5', 'bge-base-zh-v1.5'],
            'medical': ['bge-large-zh-v1.5', 'bge-base-zh-v1.5'],
            'technical': ['bge-large-zh-v1.5', 'bge-base-zh-v1.5'],
            'financial': ['bge-base-zh-v1.5', 'bge-large-zh-v1.5']
        }

        if main_domain in domain_preferences:
            for model in domain_preferences[main_domain]:
                if model in candidate_models:
                    return model, {
                        'reason': f'domain_specific_{main_domain}',
                        'analysis': analysis,
                        'domain_score': main_score,
                        'matched_keywords': analysis['domain_scores'][main_domain]['matched_keywords']
                    }

        # 根据速度偏好选择
        speed_preferences = {
            'fast': ['bge-base-zh-v1.5'],
            'medium': ['bge-base-zh-v1.5', 'chinese-legal-electra', 'bge-large-zh-v1.5'],
            'slow': ['bge-large-zh-v1.5', 'chinese-legal-electra']
        }

        for model in speed_preferences.get(speed_preference, []):
            if model in candidate_models:
                return model, {
                    'reason': f'speed_preference_{speed_preference}',
                    'analysis': analysis
                }

        # 默认选择
        default_model = candidate_models[0] if candidate_models else 'bge-base-zh-v1.5'
        return default_model, {
            'reason': 'default_selection',
            'analysis': analysis
        }

    def select_models_for_ensemble(
        self,
        query: str,
        max_models: int = 3
    ) -> list[tuple[str, float, str]]:
        """选择多个模型用于集成

        Args:
            query: 查询文本
            max_models: 最大模型数量

        Returns:
            [(模型名称, 权重, 选择原因)]
        """
        analysis = self.analyze_query(query)

        # 模型评分
        model_scores = {}

        # 领域匹配评分
        for domain, _config in self.keyword_patterns.items():
            score = analysis['domain_scores'][domain]['score']
            if score > 0:
                domain_models = {
                    'patent': ['patent-bert-base', 'bge-large-zh-v1.5'],
                    'legal': ['text2vec-large-chinese'],
                    'medical': ['bge-large-zh-v1.5'],
                    'technical': ['bge-base-zh-v1.5', 'patent-bert-base'],
                    'financial': ['bge-base-zh-v1.5']
                }

                if domain in domain_models:
                    for model in domain_models[domain]:
                        if model not in model_scores:
                            model_scores[model] = 0
                        model_scores[model] += score

        # 复杂度匹配评分
        complexity = analysis['complexity']
        complexity_models = {
            'simple': ['paraphrase-multilingual-MiniLM-L12-v2', 'bge-base-zh-v1.5'],
            'medium': ['bge-base-zh-v1.5', 'patent-bert-base'],
            'complex': ['bge-large-zh-v1.5', 'text2vec-large-chinese']
        }

        for model in complexity_models.get(complexity, []):
            if model not in model_scores:
                model_scores[model] = 0.5
            else:
                model_scores[model] += 0.5

        # 长度适配评分
        if analysis['length'] > 1000:
            long_text_models = ['bge-large-zh-v1.5', 'text2vec-large-chinese']
            for model in long_text_models:
                if model not in model_scores:
                    model_scores[model] = 0.3
                else:
                    model_scores[model] += 0.3

        # 排序并选择
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)

        selected = []
        total_score = sum(score for _, score in sorted_models[:max_models])

        for model, score in sorted_models[:max_models]:
            weight = score / total_score if total_score > 0 else 1.0 / max_models
            reason = f'ensemble_selection_score_{score:.2f}'
            selected.append((model, weight, reason))

        return selected

    def explain_selection(self, query: str) -> dict[str, Any]:
        """解释模型选择原因

        Args:
            query: 查询文本

        Returns:
            详细的解释信息
        """
        analysis = self.analyze_query(query)
        model_name, reason_info = self.select_model(query)

        explanation = {
            'query': query,
            'analysis': analysis,
            'selected_model': model_name,
            'selection_reason': reason_info['reason'],
            'model_info': self.model_manager.get_model_info(model_name),
            'alternatives': []
        }

        # 提供备选方案
        analysis['complexity'] = analysis['complexity']
        for complexity in ['simple', 'medium', 'complex']:
            if complexity != analysis['complexity']:
                alt_models = self.complexity_rules[complexity]['models']
                if alt_models:
                    explanation['alternatives'].append({
                        'complexity': complexity,
                        'models': alt_models[:2],
                        'description': f"适合{'简单' if complexity == 'simple' else '中等' if complexity == 'medium' else '复杂'}查询"
                    })

        return explanation

# 测试函数
def test_intelligent_selector():
    """测试智能模型选择器"""
    logger.info("=== 测试智能模型选择器 ===\n")

    selector = IntelligentModelSelector()

    test_queries = [
        {
            'query': '本发明涉及一种新型电池管理系统，包括电池状态监测模块和均衡控制模块。',
            'expected_domain': 'patent'
        },
        {
            'query': '根据专利法第二十二条规定，发明创造应当具备新颖性、创造性和实用性。',
            'expected_domain': 'legal'
        },
        {
            'query': '人工智能在医疗诊断中的应用，包括图像识别和病理分析。',
            'expected_domain': 'medical'
        },
        {
            'query': '快速检索系统',
            'expected_complexity': 'simple'
        },
        {
            'query': '一种基于深度学习的自然语言处理方法及其在智能客服系统中的应用，包括文本预处理、特征提取、模型训练和预测输出等完整流程，以及相应的系统架构设计。',
            'expected_complexity': 'complex'
        }
    ]

    try:
        for i, test_case in enumerate(test_queries, 1):
            logger.info(f"\n{i}. 测试查询: {test_case['query'][:50]}...")
            logger.info(str('-' * 60))

            # 选择模型
            model_name, reason = selector.select_model(test_case['query'])
            logger.info(f"   选择的模型: {model_name}")
            logger.info(f"   选择原因: {reason['reason']}")

            # 显示分析结果
            if 'analysis' in reason:
                analysis = reason['analysis']
                logger.info("\n   查询分析:")
                logger.info(f"   - 长度: {analysis['length']} 字符")
                logger.info(f"   - 词汇数: {analysis['term_count']}")
                logger.info(f"   - 复杂度: {analysis['complexity']}")

                logger.info("\n   领域评分:")
                for domain, score_info in analysis['domain_scores'].items():
                    if score_info['score'] > 0:
                        logger.info(f"   - {domain}: {score_info['score']:.2f}")
                        if score_info['matched_keywords']:
                            logger.info(f"     匹配关键词: {', '.join(score_info['matched_keywords'][:3])}")

            # 集成模型选择
            ensemble_models = selector.select_models_for_ensemble(test_case['query'], max_models=3)
            if ensemble_models:
                logger.info("\n   推荐的集成模型:")
                for model, weight, reason in ensemble_models:
                    logger.info(f"   - {model}: 权重 {weight:.3f} ({reason})")

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_intelligent_selector()
