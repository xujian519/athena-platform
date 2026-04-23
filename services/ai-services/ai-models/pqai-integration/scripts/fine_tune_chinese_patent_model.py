#!/usr/bin/env python3
"""
中文专利语义模型微调脚本
使用专利数据微调中文语义模型，提升检索质量
"""

import json
import os
import sys
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
from sentence_transformers import InputExample, SentenceTransformer, evaluation, losses
from torch.utils.data import DataLoader
from tqdm import tqdm

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class ChinesePatentModelFineTuner:
    """中文专利模型微调器"""

    def __init__(self, model_name: str = 'shibing624/text2vec-base-chinese'):
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.training_data = []
        self.validation_data = []

    def load_model(self) -> Any | None:
        """加载预训练模型"""
        try:
            logger.info(f"🔄 正在加载模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.model.to(self.device)

            logger.info("✅ 模型加载成功!")
            logger.info(f"📱 设备: {self.device}")
            logger.info(f"📏 向量维度: {self.model.get_sentence_embedding_dimension()}")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            return False

    def load_patent_data(self, data_path: str) -> list[dict]:
        """加载专利数据"""
        try:
            with open(data_path, encoding='utf-8') as f:
                patents = json.load(f).get('patents', [])

            logger.info(f"✅ 成功加载 {len(patents)} 个专利")
            return patents

        except Exception as e:
            logger.error(f"❌ 专利数据加载失败: {e}")
            return []

    def prepare_training_examples(self, patents: list[dict]) -> list[InputExample]:
        """准备训练样本"""
        logger.info('🔄 准备训练样本...')
        examples = []

        for patent in tqdm(patents, desc='生成训练样本'):
            title = patent.get('title', '').strip()
            abstract = patent.get('abstract', '').strip()
            keywords = patent.get('keywords', [])
            category = patent.get('category', '')

            if not title or not abstract:
                continue

            # 1. 标题-摘要对 (强正样本)
            examples.append(InputExample(texts=[title, abstract], label=1.0))

            # 2. 关键词-标题/摘要对 (中等正样本)
            for keyword in keywords[:3]:  # 限制关键词数量
                if keyword.strip():
                    examples.append(InputExample(texts=[keyword, title], label=0.9))
                    examples.append(InputExample(texts=[keyword, abstract], label=0.8))

            # 3. 分类-描述对 (弱正样本)
            if category:
                category_desc = self._get_category_description(category)
                if category_desc:
                    examples.append(InputExample(texts=[category, category_desc], label=0.7))
                    examples.append(InputExample(texts=[category, title], label=0.6))

        logger.info(f"✅ 生成 {len(examples)} 个训练样本")
        return examples

    def _get_category_description(self, category: str) -> str:
        """获取专利分类描述"""
        category_descriptions = {
            'G06F16/9535': '信息检索、数据库结构、文档处理',
            'G06F16/35': '信息检索、数据库结构和文件系统',
            'G06N5/02': '基于生物模型的计算机系统、神经网络',
            'G06Q40/04': '金融、货币、银行或保险系统的处理',
            'G06Q20/06': '电子资金转账、电子商务支付系统',
            'G06F16/9537': '语义分析、自然语言处理、机器翻译',
            'G06F16/35': '文档分析、文本处理、信息提取',
            'G06F40/24': '语言分析、语法检查、语义理解'
        }
        return category_descriptions.get(category, '')

    def create_negative_samples(self, positive_examples: list[InputExample],
                               negative_ratio: float = 0.3) -> list[InputExample]:
        """创建负样本"""
        logger.info(f"🔄 创建负样本 (比率: {negative_ratio})...")
        negative_examples = []
        texts = [example.texts[0] for example in positive_examples]

        num_negative = int(len(positive_examples) * negative_ratio)

        for _ in tqdm(range(num_negative), desc='生成负样本'):
            # 随机选择两个不相关的专利文本
            idx1, idx2 = np.random.choice(len(texts), 2, replace=False)
            if idx1 != idx2:
                # 确保不是来自同一个专利
                negative_examples.append(InputExample(texts=[texts[idx1], texts[idx2], label=0.0))

        logger.info(f"✅ 生成 {len(negative_examples)} 个负样本")
        return negative_examples

    def prepare_validation_data(self, patents: list[dict]) -> list[tuple[str, str, float]:
        """准备验证数据"""
        validation_pairs = []

        # 使用前20个专利进行验证
        validation_patents = patents[:20]

        for i, patent1 in enumerate(validation_patents):
            title1 = patent1.get('title', '')
            abstract1 = patent1.get('abstract', '')
            keywords1 = patent1.get('keywords', [])

            # 正样本对
            if title1 and abstract1:
                validation_pairs.append((title1, abstract1, 1.0))

            for keyword in keywords1[:2]:
                if keyword:
                    validation_pairs.append((keyword, title1, 0.9))

            # 与其他专利的负样本对
            for j, patent2 in enumerate(validation_patents):
                if i != j and np.random.random() < 0.1:  # 10%概率
                    title2 = patent2.get('title', '')
                    if title1 and title2:
                        validation_pairs.append((title1, title2, 0.0))

        logger.info(f"✅ 准备 {len(validation_pairs)} 个验证样本")
        return validation_pairs

    def fine_tune_model(self, training_examples: list[InputExample],
                       validation_examples: list[tuple[str, str, float] = None,
                       epochs: int = 3, batch_size: int = 16, warmup_steps: int = 100,
                       output_path: str = './fine_tuned_chinese_patent_model'):
        """微调模型"""
        logger.info('🚀 开始微调中文专利语义模型...')
        logger.info(f"📊 训练样本数: {len(training_examples)}")
        logger.info(f"🔢 训练轮数: {epochs}")
        logger.info(f"📦 批次大小: {batch_size}")
        logger.info(f"🔥 预热步数: {warmup_steps}")

        # 准备数据加载器
        train_dataloader = DataLoader(training_examples, shuffle=True, batch_size=batch_size)
        train_loss = losses.CosineSimilarityLoss(self.model)

        # 准备验证器
        evaluator = None
        if validation_examples:
            evaluator = evaluation.EmbeddingSimilarityEvaluator(
                sentences1=[pair[0] for pair in validation_examples],
                sentences2=[pair[1] for pair in validation_examples],
                scores=[pair[2] for pair in validation_examples],
                name='patent-validation'
            )

        # 微调模型
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=output_path,
            show_progress_bar=True,
            save_best_model=True,
            checkpoint_path=os.path.join(output_path, 'checkpoints'),
            checkpoint_save_steps=1000
        )

        logger.info(f"✅ 模型微调完成! 模型已保存到: {output_path}")

    def evaluate_model(self, test_patents: list[dict],
                       original_model_path: str = None) -> dict:
        """评估微调效果"""
        logger.info('📊 评估模型微调效果...')

        if original_model_path:
            # 加载原始模型进行对比
            original_model = SentenceTransformer(original_model_path)
        else:
            original_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        # 准备测试查询
        test_queries = [
            '人工智能专利检索系统',
            '深度学习算法优化',
            '区块链技术应用',
            '自然语言处理',
            '机器学习模型训练'
        ]

        results = {'before_fine_tune': {}, 'after_fine_tune': {}}

        for query in test_queries:
            # 原始模型结果
            original_embeddings = original_model.encode([query], convert_to_tensor=True)
            patent_texts = [p.get('title', '') + ' ' + p.get('abstract', '') for p in test_patents]
            patent_embeddings = original_model.encode(patent_texts, convert_to_tensor=True)

            original_scores = torch.nn.functional.cosine_similarity(
                original_embeddings, patent_embeddings
            ).numpy()

            # 微调后模型结果
            fine_tuned_embeddings = self.model.encode([query], convert_to_tensor=True)
            fine_tuned_patent_embeddings = self.model.encode(patent_texts, convert_to_tensor=True)

            fine_tuned_scores = torch.nn.functional.cosine_similarity(
                fine_tuned_embeddings, fine_tuned_patent_embeddings
            ).numpy()

            results['before_fine_tune'][query] = {
                'top_scores': np.sort(original_scores)[-3:][::-1].tolist(),
                'mean_score': float(np.mean(original_scores)),
                'max_score': float(np.max(original_scores))
            }

            results['after_fine_tune'][query] = {
                'top_scores': np.sort(fine_tuned_scores)[-3:][::-1].tolist(),
                'mean_score': float(np.mean(fine_tuned_scores)),
                'max_score': float(np.max(fine_tuned_scores))
            }

        return results

    def save_evaluation_results(self, results: dict, output_path: str) -> None:
        """保存评估结果"""
        results_path = os.path.join(output_path, 'fine_tuning_evaluation.json')

        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 评估结果已保存到: {results_path}")

def main() -> None:
    """主函数：执行模型微调"""
    # 配置参数
    MODEL_NAME = 'shibing624/text2vec-base-chinese'  # 推荐的中文专利模型
    PATENT_DATA_PATH = '/Users/xujian/Athena工作平台/services/ai-models/pqai-integration/data/sample_patents.json'
    OUTPUT_PATH = '/Users/xujian/Athena工作平台/services/ai-models/pqai-integration/models/fine_tuned_chinese_patent_model'

    # 训练参数
    EPOCHS = 3
    BATCH_SIZE = 16
    WARMUP_STEPS = 100

    logger.info('🎯 中文专利语义模型微调')
    logger.info(str('=' * 50))

    # 初始化微调器
    fine_tuner = ChinesePatentModelFineTuner(MODEL_NAME)

    # 1. 加载模型
    if not fine_tuner.load_model():
        logger.info('❌ 模型加载失败，退出程序')
        return 1

    # 2. 加载专利数据
    patents = fine_tuner.load_patent_data(PATENT_DATA_PATH)
    if not patents:
        logger.info('❌ 专利数据加载失败，退出程序')
        return 1

    # 3. 准备训练数据
    positive_examples = fine_tuner.prepare_training_examples(patents)
    negative_examples = fine_tuner.create_negative_samples(positive_examples, negative_ratio=0.3)
    all_examples = positive_examples + negative_examples

    # 4. 准备验证数据
    validation_examples = fine_tuner.prepare_validation_data(patents)

    # 5. 微调模型
    fine_tuner.fine_tune_model(
        training_examples=all_examples,
        validation_examples=validation_examples,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        warmup_steps=WARMUP_STEPS,
        output_path=OUTPUT_PATH
    )

    # 6. 评估模型效果
    evaluation_results = fine_tuner.evaluate_model(patents)
    fine_tuner.save_evaluation_results(evaluation_results, OUTPUT_PATH)

    logger.info("\n🎉 中文专利语义模型微调完成!")
    logger.info(f"📁 模型保存路径: {OUTPUT_PATH}")
    logger.info(f"📊 评估报告: {OUTPUT_PATH}/fine_tuning_evaluation.json")

    return 0

if __name__ == '__main__':
    exit(main())
