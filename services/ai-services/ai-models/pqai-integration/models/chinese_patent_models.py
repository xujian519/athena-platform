#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文专利语义模型配置和推荐
针对中文专利数据优化的语义模型选择
"""

import logging
from core.async_main import async_main
from typing import Dict, List, Tuple

import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class ChinesePatentModelRegistry:
    """中文专利语义模型注册表"""

    def __init__(self):
        self.models = self._get_model_registry()

    def _get_model_registry(self) -> Dict[str, Dict]:
        """获取模型注册表"""
        return {
            # 专门针对中文优化的模型
            'text2vec-base-chinese': {
                'model_name': 'shibing624/text2vec-base-chinese',
                'description': '专门针对中文优化的语义模型',
                "dimension = 1024,
                'max_seq_length': 512,
                'file_size_mb': 410,
                'advantages': [
                    '专门针对中文文本优化',
                    '在中文相似度计算任务上表现优异',
                    '支持专利、法律等专业领域',
                    '中文语义理解能力强'
                ],
                'use_cases': ['专利检索', '法律文档分析', '中文文本匹配'],
                'recommended': True,
                'priority': 1
            },

            # 多语言模型，中文支持良好
            'paraphrase-multilingual': {
                'model_name': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                'description': '支持多语言的高效语义模型',
                'dimension': 384,
                'max_seq_length': 512,
                'file_size_mb': 480,
                'advantages': [
                    '支持包括中文在内的50+种语言',
                    '在跨语言检索任务上表现优秀',
                    '轻量级设计，推理速度快',
                    '多语言专利检索支持'
                ],
                'use_cases': ['多语言专利检索', '跨语言文本匹配', '国际化专利分析'],
                'recommended': True,
                'priority': 2
            },

            # 中文SimCSE模型
            'erlangshen-simcse': {
                'model_name': 'IDEA-CCNL/Erlangshen-SimCSE-110M-Chinese',
                'description': '基于SimCSE技术的中文语义理解模型',
                "dimension = 1024,
                'max_seq_length': 512,
                'file_size_mb': 440,
                'advantages': [
                    '基于SimCSE技术训练，语义理解准确',
                    '专门针对中文语义相似度任务',
                    '在中文文本匹配上效果显著',
                    '适合专业领域文本'
                ],
                'use_cases': ['中文专利相似度计算', '专业文档匹配', '语义检索'],
                'recommended': True,
                'priority': 3
            },

            # 中文BERT base
            'chinese-bert-wwm': {
                'model_name': 'hfl/chinese-bert-wwm-ext',
                'description': '中文BERT预训练模型（全词掩码）',
                "dimension = 1024,
                'max_seq_length': 512,
                'file_size_mb': 390,
                'advantages': [
                    '基于大量中文语料预训练',
                    '全词掩码技术增强语义理解',
                    '适合中文专业领域',
                    '可进一步微调'
                ],
                'use_cases': ['中文专利文本理解', '专业术语分析', '基础语义表示'],
                'recommended': False,
                'priority': 4
            },

            # 中文RoBERTa
            'chinese-roberta': {
                'model_name': 'hfl/chinese-roberta-wwm-ext',
                'description': '中文RoBERTa预训练模型',
                "dimension = 1024,
                'max_seq_length': 512,
                'file_size_mb': 400,
                'advantages': [
                    'RoBERTa架构，性能优于BERT',
                    '中文语料充分训练',
                    '适合复杂语义理解任务',
                    '专利术语理解能力强'
                ],
                'use_cases': ['复杂专利语义分析', '专利术语理解', '高级语义检索'],
                'recommended': False,
                'priority': 5
            }
        }

    def get_recommended_models(self, top_k: int = 3) -> List[Tuple[str, Dict]]:
        """获取推荐的中文专利模型"""
        recommended = [
            (name, config) for name, config in self.models.items()
            if config.get('recommended', False)
        ]
        # 按优先级排序
        recommended.sort(key=lambda x: x[1]['priority'])
        return recommended[:top_k]

    def get_model_info(self, model_name: str) -> Dict:
        """获取模型详细信息"""
        return self.models.get(model_name, {})

    def compare_models(self, model_names: List[str]) -> Dict:
        """对比多个模型"""
        comparison = {
            'models': {},
            'comparison_metrics': {
                'dimension': {},
                'file_size_mb': {},
                'max_seq_length': {}
            }
        }

        for name in model_names:
            if name in self.models:
                config = self.models[name]
                comparison['models'][name] = config

                for metric in comparison['comparison_metrics']:
                    comparison['comparison_metrics'][metric][name] = config.get(metric)

        return comparison

    def recommend_for_patent_search(self) -> str:
        """为专利检索任务推荐模型"""
        # 基于专利检索的特定需求推荐
        patent_requirements = {
            'chinese_understanding': True,
            'domain_specialization': True,
            'semantic_similarity': True,
            'inference_speed': True
        }

        # 综合评分推荐
        best_model = 'text2vec-base-chinese'  # 默认推荐

        # 如果需要多语言支持
        if patent_requirements.get('multilingual_support'):
            best_model = 'paraphrase-multilingual'

        # 如果需要最佳语义理解
        elif patent_requirements.get('best_semantic'):
            best_model = 'erlangshen-simcse'

        return best_model

class ChinesePatentModelTrainer:
    """中文专利模型训练器"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def load_model(self):
        """加载预训练模型"""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.model.to(self.device)
            logger.info(f"✅ 成功加载模型: {self.model_name}")
            logger.info(f"📱 设备: {self.device}")
            logger.info(f"📏 向量维度: {self.model.get_sentence_embedding_dimension()}")
            return True
        except Exception as e:
            logger.info(f"❌ 模型加载失败: {e}")
            return False

    def prepare_patent_training_data(self, patent_data: List[Dict]) -> List[Tuple[str, str]]:
        """准备专利训练数据"""
        training_examples = []

        for patent in patent_data:
            title = patent.get('title', '')
            abstract = patent.get('abstract', '')
            keywords = patent.get('keywords', [])

            # 创建正样本对 (标题-摘要)
            if title and abstract:
                training_examples.append((title, abstract))

            # 创建关键词相关样本
            for keyword in keywords:
                if keyword and title:
                    training_examples.append((keyword, title))
                if keyword and abstract:
                    training_examples.append((keyword, abstract))

        return training_examples

    def fine_tune_model(self, training_examples: List[Tuple[str, str]],
                       epochs: int = 3, batch_size: int = 16):
        """微调模型"""
        from sentence_transformers import InputExample, losses
        from torch.utils.data import DataLoader

        logger.info(f"🔄 开始微调模型...")
        logger.info(f"📊 训练样本数: {len(training_examples)}")
        logger.info(f"🔢 训练轮数: {epochs}")
        logger.info(f"📦 批次大小: {batch_size}")

        # 准备训练数据
        train_examples = [
            InputExample(texts=[text1, text2])
            for text1, text2 in training_examples
        ]

        # 定义损失函数
        train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
        train_loss = losses.CosineSimilarityLoss(self.model)

        # 微调模型
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=100,
            output_path='./fine_tuned_chinese_patent_model',
            show_progress_bar=True
        )

        logger.info('✅ 模型微调完成!')

def main():
    """主函数：演示中文专利模型选择"""
    registry = ChinesePatentModelRegistry()

    logger.info('🎯 中文专利语义模型推荐')
    logger.info(str('=' * 50))

    # 获取推荐的模型
    recommended_models = registry.get_recommended_models(3)

    logger.info("\n🏆 推荐的中文专利语义模型:")
    for i, (model_key, config) in enumerate(recommended_models, 1):
        logger.info(f"\n{i}. {config['model_name']}")
        logger.info(f"   描述: {config['description']}")
        logger.info(f"   向量维度: {config['dimension']}")
        logger.info(f"   文件大小: {config['file_size_mb']}MB")
        logger.info(f"   优势: {', '.join(config['advantages'][:2])}")

    # 为专利检索推荐最佳模型
    best_model = registry.recommend_for_patent_search()
    best_config = registry.get_model_info(best_model)

    logger.info(f"\n🎯 专利检索最佳推荐:")
    logger.info(f"模型: {best_config['model_name']}")
    logger.info(f"理由: 专门针对中文优化，适合专利领域的语义理解")

    # 模型对比
    logger.info(f"\n📊 模型对比:")
    comparison = registry.compare_models([model[0] for model in recommended_models])

    for metric, values in comparison['comparison_metrics'].items():
        logger.info(f"{metric}:")
        for model, value in values.items():
            logger.info(f"  {model}: {value}")

if __name__ == '__main__':
    main()