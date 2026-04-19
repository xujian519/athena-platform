#!/usr/bin/env python3
"""
大规模专利数据生成与质量优化器
基于DeepSeekMath V2论文的数据生成策略
Athena智能工作平台专利分析专用数据处理系统

作者: Athena AI团队
版本: 1.0.0
创建时间: 2025-11-28
"""

import concurrent.futures
import hashlib
import json
import logging
import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class DataGenerationConfig:
    """数据生成配置"""

    # 生成参数
    num_samples_per_input: int = 8  # 每个输入生成的样本数
    temperature_range: tuple[float, float] = (0.6, 1.2)
    top_p_range: tuple[float, float] = (0.8, 0.95)
    max_length_range: tuple[int, int] = (256, 1024)

    # 质量筛选参数
    min_solution_length: int = 50
    max_solution_length: int = 2000
    diversity_threshold: float = 0.3
    coherence_score_threshold: float = 0.6
    correctness_score_threshold: float = 0.7

    # 数据增强参数
    paraphrase_probability: float = 0.3
    synonym_replacement_probability: float = 0.2
    difficulty_augmentation: bool = True

    # 并行处理
    max_workers: int = 4
    batch_size: int = 32


class PatentDataGenerator:
    """专利分析数据生成器"""

    def __init__(self, config: DataGenerationConfig = None):
        self.config = config or DataGenerationConfig()
        self.quality_scorer = PatentQualityScorer()
        self.diversity_calculator = DiversityCalculator()
        self.augmenter = PatentDataAugmenter()

        # 统计信息
        self.generation_stats = {
            'total_inputs': 0,
            'total_generated': 0,
            'quality_passed': 0,
            'diversity_passed': 0,
            'final_selected': 0,
            'generation_time': 0.0,
        }

    def generate_from_patent_corpus(
        self, patent_corpus: list[dict], output_dir: str = './generated_data'
    ) -> dict[str, Any]:
        """从专利语料库生成训练数据"""
        start_time = datetime.now()

        logger.info(f"开始从{len(patent_corpus)}个专利生成训练数据...")

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成任务列表
        generation_tasks = []
        for i, patent in enumerate(patent_corpus):
            for _ in range(self.config.num_samples_per_input):
                task = {
                    'patent_id': patent.get('patent_id', f"patent_{i}"),
                    'patent_data': patent,
                    'task_id': f"{patent.get('patent_id', f'patent_{i}')}_{_}",
                }
                generation_tasks.append(task)

        # 并行生成数据
        generated_data = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.max_workers
        ) as executor:
            # 分批处理
            for i in range(0, len(generation_tasks), self.config.batch_size):
                batch = generation_tasks[i : i + self.config.batch_size]

                # 提交批量任务
                futures = []
                for task in batch:
                    future = executor.submit(self._generate_single_sample, task)
                    futures.append(future)

                # 收集结果
                for future in concurrent.futures.as_completed(futures):
                    try:
                        sample = future.result()
                        if sample:
                            generated_data.append(sample)
                    except Exception as e:
                        logger.warning(f"生成样本失败: {e}")

        self.generation_stats['total_inputs'] = len(patent_corpus)
        self.generation_stats['total_generated'] = len(generated_data)

        logger.info(f"生成完成，总共{len(generated_data)}个样本，开始质量筛选...")

        # 质量筛选
        quality_passed = self._quality_filter(generated_data)
        self.generation_stats['quality_passed'] = len(quality_passed)

        # 多样性筛选
        diversity_passed = self._diversity_filter(quality_passed)
        self.generation_stats['diversity_passed'] = len(diversity_passed)

        # 数据增强
        augmented_data = self._augment_data(diversity_passed)

        # 最终选择
        final_data = self._final_selection(augmented_data)
        self.generation_stats['final_selected'] = len(final_data)

        # 保存数据
        self._save_generated_data(final_data, output_path)

        end_time = datetime.now()
        self.generation_stats['generation_time'] = (
            end_time - start_time
        ).total_seconds()

        # 保存统计信息
        self._save_generation_stats(output_path)

        logger.info("数据生成完成!")
        logger.info(f"总输入: {self.generation_stats['total_inputs']}")
        logger.info(f"生成样本: {self.generation_stats['total_generated']}")
        logger.info(f"质量通过: {self.generation_stats['quality_passed']}")
        logger.info(f"多样性通过: {self.generation_stats['diversity_passed']}")
        logger.info(f"最终选择: {self.generation_stats['final_selected']}")
        logger.info(f"耗时: {self.generation_stats['generation_time']:.2f}秒")

        return {
            'final_data': final_data,
            'statistics': self.generation_stats,
            'output_path': str(output_path),
        }

    def _generate_single_sample(self, task: dict) -> dict | None:
        """生成单个样本"""
        try:
            patent = task['patent_data']
            task_id = task['task_id']

            # 随机生成参数
            temperature = random.uniform(*self.config.temperature_range)
            top_p = random.uniform(*self.config.top_p_range)
            max_length = random.randint(*self.config.max_length_range)

            # 选择生成任务类型
            task_type = random.choice(
                [
                    'patent_summary',
                    'novelty_analysis',
                    'inventive_step',
                    'technical_features',
                    'claim_analysis',
                    'prior_art_search',
                    'infringement_assessment',
                    'licensing_strategy',
                ]
            )

            # 生成样本
            if task_type == 'patent_summary':
                sample = self._generate_patent_summary(
                    patent, temperature, top_p, max_length
                )
            elif task_type == 'novelty_analysis':
                sample = self._generate_novelty_analysis(
                    patent, temperature, top_p, max_length
                )
            elif task_type == 'inventive_step':
                sample = self._generate_inventive_step_analysis(
                    patent, temperature, top_p, max_length
                )
            elif task_type == 'technical_features':
                sample = self._generate_technical_features_analysis(
                    patent, temperature, top_p, max_length
                )
            elif task_type == 'claim_analysis':
                sample = self._generate_claim_analysis(
                    patent, temperature, top_p, max_length
                )
            elif task_type == 'prior_art_search':
                sample = self._generate_prior_art_search(
                    patent, temperature, top_p, max_length
                )
            elif task_type == 'infringement_assessment':
                sample = self._generate_infringement_assessment(
                    patent, temperature, top_p, max_length
                )
            elif task_type == 'licensing_strategy':
                sample = self._generate_licensing_strategy(
                    patent, temperature, top_p, max_length
                )

            if sample:
                sample.update(
                    {
                        'task_id': task_id,
                        'patent_id': task['patent_id'],
                        'task_type': task_type,
                        'generation_params': {
                            'temperature': temperature,
                            'top_p': top_p,
                            'max_length': max_length,
                        },
                        'timestamp': datetime.now().isoformat(),
                    }
                )

            return sample

        except Exception as e:
            logger.warning(f"生成样本失败 {task.get('task_id', 'unknown')}: {e}")
            return None

    def _generate_patent_summary(
        self, patent: dict, temperature: float, top_p: float, max_length: int
    ) -> dict:
        """生成专利摘要"""
        title = patent.get('title', '未知标题')
        abstract = patent.get('abstract', '无摘要')
        description = patent.get('description', '无描述')

        question = (
            f"请为以下专利生成技术摘要：\n标题: {title}\n摘要: {abstract}\n描述: {description[:500]}..."
        )

        # 模拟生成回答（实际应该调用语言模型）
        answer = f"""
        专利技术摘要：

        1. 技术领域：{patent.get('technical_field', '未指定')}

        2. 背景技术：本技术解决了{patent.get('problem_solved', '现有技术中的问题')}

        3. 发明内容：主要包括{patent.get('main_invention', '技术创新点')}

        4. 技术效果：实现了{patent.get('technical_effects', '预期的技术效果')}

        5. 应用前景：可应用于{patent.get('application_fields', '相关技术领域')}
        """

        return {
            'question': question,
            'answer': answer,
            'reasoning': '通过分析专利标题、摘要和描述，提取关键技术信息并进行结构化总结',
            'difficulty': 'easy',
            'reasoning_steps': 1,
            'expected_output_type': 'patent_summary',
        }

    def _generate_novelty_analysis(
        self, patent: dict, temperature: float, top_p: float, max_length: int
    ) -> dict:
        """生成新颖性分析"""
        title = patent.get('title', '未知标题')
        claims = patent.get('claims', [])

        question = (
            f"分析以下专利的新颖性：\n标题: {title}\n权利要求: {claims[:3] if claims else '无权利要求信息'}"
        )

        # 模拟新颖性分析
        answer = f"""
        新颖性分析：

        1. 现有技术调研：经过检索，发现{random.randint(5, 15)}篇相关现有技术文献

        2. 技术特征对比：
           - 现有技术特征A：{patent.get('existing_feature_a', '已知技术')}
           - 现有技术特征B：{patent.get('existing_feature_b', '已知技术')}
           - 本发明特征：{patent.get('novel_feature', '技术创新点')}

        3. 新颖性结论：本发明在{patent.get('novelty_aspect', '技术方案')}方面具有显著的新颖性

        4. 创新点识别：
           - 创新点1：{patent.get('innovation_1', '第一个创新点')}
           - 创新点2：{patent.get('innovation_2', '第二个创新点')}
        """

        return {
            'question': question,
            'answer': answer,
            'reasoning': '通过对比现有技术，识别本发明的独特技术特征',
            'difficulty': 'medium',
            'reasoning_steps': 3,
            'expected_output_type': 'novelty_analysis',
        }

    def _generate_inventive_step_analysis(
        self, patent: dict, temperature: float, top_p: float, max_length: int
    ) -> dict:
        """生成创造性分析"""
        question = (
            f"分析以下专利的创造性步骤：\n{patent.get('title', '')}\n{patent.get('abstract', '')}"
        )

        answer = f"""
        创造性分析：

        1. 技术问题：本发明要解决的技术问题是{patent.get('technical_problem', '现有技术问题')}

        2. 现有技术局限：现有技术方案存在{patent.get('existing_limitations', '技术局限性')}

        3. 创造性思路：
           - 突破点：{patent.get('breakthrough_point', '技术突破')}
           - 解决方案：{patent.get('solution_approach', '创新解决方案')}
           - 预期效果：{patent.get('expected_effects', '技术效果')}

        4. 创造性评价：本发明具有显著的创造性，主要体现在{patent.get('creativity_aspects', '技术创新方面')}
        """

        return {
            'question': question,
            'answer': answer,
            'reasoning': '分析技术问题的解决难度和创新程度',
            'difficulty': 'hard',
            'reasoning_steps': 4,
            'expected_output_type': 'inventive_step',
        }

    def _generate_technical_features_analysis(
        self, patent: dict, temperature: float, top_p: float, max_length: int
    ) -> dict:
        """生成技术特征分析"""
        question = f"分析以下专利的技术特征：\n{patent.get('description', patent.get('abstract', ''))[:500]}..."

        answer = f"""
        技术特征分析：

        1. 核心技术特征：
           - 结构特征：{patent.get('structural_features', '技术结构')}
           - 功能特征：{patent.get('functional_features', '技术功能')}
           - 材料特征：{patent.get('material_features', '材料特性')}

        2. 技术参数：
           - 关键参数1：{patent.get('parameter_1', '技术参数A')}
           - 关键参数2：{patent.get('parameter_2', '技术参数B')}

        3. 技术优势：{patent.get('technical_advantages', '相比现有技术的优势')}
        """

        return {
            'question': question,
            'answer': answer,
            'reasoning': '提取和分类专利文档中的关键技术信息',
            'difficulty': 'medium',
            'reasoning_steps': 2,
            'expected_output_type': 'technical_features',
        }

    def _generate_claim_analysis(
        self, patent: dict, temperature: float, top_p: float, max_length: int
    ) -> dict:
        """生成权利要求分析"""
        claims = patent.get('claims', [])
        question = f"分析以下专利的权利要求：\n{claims[:2] if claims else '无权利要求信息'}"

        answer = f"""
        权利要求分析：

        1. 独立权利要求：
           - 保护范围：{patent.get('protection_scope', '技术保护范围')}
           - 技术特征：{patent.get('claim_features', '权利要求技术特征')}

        2. 从属权利要求：
           - 细化特征：{patent.get('dependent_features', '从属权利要求特征')}
           - 备选方案：{patent.get('alternative_solutions', '替代技术方案')}

        3. 权利要求布局：{patent.get('claim_layout', '权利要求的层次和布局')}
        """

        return {
            'question': question,
            'answer': answer,
            'reasoning': '分析权利要求的层次结构和技术保护范围',
            'difficulty': 'medium',
            'reasoning_steps': 3,
            'expected_output_type': 'claim_analysis',
        }

    def _generate_prior_art_search(
        self, patent: dict, temperature: float, top_p: float, max_length: int
    ) -> dict:
        """生成现有技术检索分析"""
        question = (
            f"为以下专利进行现有技术检索分析：\n{patent.get('title', '')}\n{patent.get('abstract', '')}"
        )

        answer = f"""
        现有技术检索分析：

        1. 检索策略：
           - 关键词：{patent.get('search_keywords', '技术关键词')}
           - 分类号：{patent.get('ipc_classifications', '技术分类号')}
           - 数据库：专利数据库、学术论文、技术标准

        2. 相关现有技术：
           - 最接近现有技术1：{patent.get('closest_prior_art_1', '相关技术')}
           - 最接近现有技术2：{patent.get('closest_prior_art_2', '相关技术')}

        3. 差异分析：{patent.get('differences_analysis', '与现有技术的差异')}
        """

        return {
            'question': question,
            'answer': answer,
            'reasoning': '系统性地检索和分析相关现有技术',
            'difficulty': 'medium',
            'reasoning_steps': 3,
            'expected_output_type': 'prior_art_search',
        }

    def _generate_infringement_assessment(
        self, patent: dict, temperature: float, top_p: float, max_length: int
    ) -> dict:
        """生成侵权评估分析"""
        question = f"进行专利侵权风险评估：\n{patent.get('title', '')}\n权利要求: {patent.get('claims', [])[:2]}"

        answer = f"""
        侵权风险评估：

        1. 权利要求解释：
           - 权利要求1解释：{patent.get('claim_1_interpretation', '权利要求解释')}
           - 保护范围界定：{patent.get('scope_determination', '保护范围')}

        2. 侵权判定要素：
           - 技术特征对比：{patent.get('feature_comparison', '技术特征比较')}
           - 等同原则适用：{patent.get('equivalent_principle', '等同原则适用')}

        3. 风险等级：{patent.get('risk_level', '风险评估等级')}
        """

        return {
            'question': question,
            'answer': answer,
            'reasoning': '分析权利要求保护范围和潜在侵权风险',
            'difficulty': 'hard',
            'reasoning_steps': 4,
            'expected_output_type': 'infringement_assessment',
        }

    def _generate_licensing_strategy(
        self, patent: dict, temperature: float, top_p: float, max_length: int
    ) -> dict:
        """生成许可策略分析"""
        question = f"制定专利许可策略：\n{patent.get('title', '')}\n技术领域: {patent.get('technical_field', '')}"

        answer = f"""
        专利许可策略：

        1. 市场分析：
           - 目标市场：{patent.get('target_market', '应用市场')}
           - 市场规模：{patent.get('market_size', '市场规模评估')}

        2. 许可模式：
           - 独家许可：{patent.get('exclusive_licensing', '独家许可策略')}
           - 非独家许可：{patent.get('non_exclusive_licensing', '非独家许可策略')}

        3. 定价策略：{patent.get('pricing_strategy', '许可费用策略')}
        """

        return {
            'question': question,
            'answer': answer,
            'reasoning': '基于市场分析制定专利许可策略',
            'difficulty': 'hard',
            'reasoning_steps': 4,
            'expected_output_type': 'licensing_strategy',
        }

    def _quality_filter(self, data: list[dict]) -> list[dict]:
        """质量筛选"""
        quality_passed = []

        for item in data:
            try:
                # 计算质量分数
                quality_scores = self.quality_scorer.calculate_scores(item)

                # 应用质量阈值
                if (
                    quality_scores['coherence'] >= self.config.coherence_score_threshold
                    and quality_scores['correctness']
                    >= self.config.correctness_score_threshold
                    and quality_scores['length_score'] >= 0.5
                ):
                    item['quality_scores'] = quality_scores
                    quality_passed.append(item)

            except Exception as e:
                logger.warning(f"质量评估失败: {e}")

        logger.info(f"质量筛选: {len(data)} -> {len(quality_passed)}")
        return quality_passed

    def _diversity_filter(self, data: list[dict]) -> list[dict]:
        """多样性筛选"""
        if len(data) <= 10:  # 数据量少时跳过多样性筛选
            return data

        diversity_passed = []
        selected_hashes = set()

        # 按质量分数排序
        sorted_data = sorted(
            data, key=lambda x: x['quality_scores']['overall'], reverse=True
        )

        for item in sorted_data:
            # 计算内容哈希
            content_hash = self._calculate_content_hash(item)

            # 检查与已选内容的相似度
            is_diverse = True
            for selected_hash in selected_hashes:
                similarity = self.diversity_calculator.calculate_similarity(
                    content_hash, selected_hash
                )
                if similarity > (1 - self.config.diversity_threshold):
                    is_diverse = False
                    break

            if is_diverse:
                diversity_passed.append(item)
                selected_hashes.add(content_hash)

            # 限制最终数量
            if len(diversity_passed) >= 1000:  # 限制最大数量
                break

        logger.info(f"多样性筛选: {len(data)} -> {len(diversity_passed)}")
        return diversity_passed

    def _calculate_content_hash(self, item: dict) -> str:
        """计算内容哈希"""
        content = f"{item.get('question', '')}{item.get('answer', '')}{item.get('task_type', '')}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def _augment_data(self, data: list[dict]) -> list[dict]:
        """数据增强"""
        augmented_data = data.copy()

        for item in data:
            if random.random() < self.config.paraphrase_probability:
                # 改写增强
                paraphrased = self.augmenter.paraphrase(item)
                if paraphrased:
                    augmented_data.append(paraphrased)

            if random.random() < self.config.synonym_replacement_probability:
                # 同义词替换增强
                synonym_replaced = self.augmenter.replace_synonyms(item)
                if synonym_replaced:
                    augmented_data.append(synonym_replaced)

            if self.config.difficulty_augmentation:
                # 难度增强
                difficulty_augmented = self.augmenter.adjust_difficulty(item)
                if difficulty_augmented:
                    augmented_data.append(difficulty_augmented)

        logger.info(f"数据增强: {len(data)} -> {len(augmented_data)}")
        return augmented_data

    def _final_selection(self, data: list[dict]) -> list[dict]:
        """最终选择"""
        # 按难度平衡选择
        sum(1 for item in data if item.get('difficulty') == 'easy')
        sum(1 for item in data if item.get('difficulty') == 'medium')
        sum(1 for item in data if item.get('difficulty') == 'hard')

        # 计算目标比例
        total_count = len(data)
        easy_target = int(total_count * 0.3)  # 30%简单
        medium_target = int(total_count * 0.5)  # 50%中等
        hard_target = total_count - easy_target - medium_target  # 20%困难

        # 按比例选择
        final_data = []
        easy_selected = 0
        medium_selected = 0
        hard_selected = 0

        # 按质量分数排序
        sorted_data = sorted(
            data,
            key=lambda x: x.get('quality_scores', {}).get('overall', 0),
            reverse=True,
        )

        for item in sorted_data:
            difficulty = item.get('difficulty', 'medium')

            if difficulty == 'easy' and easy_selected < easy_target:
                final_data.append(item)
                easy_selected += 1
            elif difficulty == 'medium' and medium_selected < medium_target:
                final_data.append(item)
                medium_selected += 1
            elif difficulty == 'hard' and hard_selected < hard_target:
                final_data.append(item)
                hard_selected += 1

        logger.info(f"最终选择: 简单{easy_selected}, 中等{medium_selected}, 困难{hard_selected}")
        return final_data

    def _save_generated_data(self, data: list[dict], output_path: Path):
        """保存生成的数据"""
        # 保存为JSONL格式
        jsonl_path = output_path / 'generated_patent_data.jsonl'
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # 保存为JSON格式
        json_path = output_path / 'generated_patent_data.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 保存为SQLite格式（便于查询）
        db_path = output_path / 'generated_patent_data.db'
        self._save_to_sqlite(data, db_path)

        logger.info(f"数据已保存到: {output_path}")

    def _save_to_sqlite(self, data: list[dict], db_path: Path):
        """保存到SQLite数据库"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patent_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                patent_id TEXT,
                task_type TEXT,
                question TEXT,
                answer TEXT,
                reasoning TEXT,
                difficulty TEXT,
                reasoning_steps INTEGER,
                quality_score REAL,
                timestamp TEXT,
                generation_params TEXT
            )
        """
        )

        # 插入数据
        for item in data:
            cursor.execute(
                """
                INSERT INTO patent_training_data (
                    task_id, patent_id, task_type, question, answer, reasoning,
                    difficulty, reasoning_steps, quality_score, timestamp, generation_params
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    item.get('task_id'),
                    item.get('patent_id'),
                    item.get('task_type'),
                    item.get('question'),
                    item.get('answer'),
                    item.get('reasoning'),
                    item.get('difficulty'),
                    item.get('reasoning_steps'),
                    item.get('quality_scores', {}).get('overall', 0),
                    item.get('timestamp'),
                    json.dumps(item.get('generation_params', {})),
                ),
            )

        conn.commit()
        conn.close()

    def _save_generation_stats(self, output_path: Path):
        """保存生成统计信息"""
        stats_path = output_path / 'generation_statistics.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.generation_stats, f, indent=2, ensure_ascii=False)


class PatentQualityScorer:
    """专利质量评分器"""

    def calculate_scores(self, item: dict) -> dict[str, float]:
        """计算质量分数"""
        question = item.get('question', '')
        answer = item.get('answer', '')

        # 长度分数
        length_score = self._calculate_length_score(answer)

        # 连贯性分数
        coherence_score = self._calculate_coherence_score(question, answer)

        # 正确性分数（基于关键词匹配）
        correctness_score = self._calculate_correctness_score(question, answer)

        # 综合分数
        overall_score = (length_score + coherence_score + correctness_score) / 3

        return {
            'length': length_score,
            'coherence': coherence_score,
            'correctness': correctness_score,
            'overall': overall_score,
        }

    def _calculate_length_score(self, answer: str) -> float:
        """计算长度分数"""
        length = len(answer)
        if length < 50:
            return 0.2
        elif length > 2000:
            return 0.8
        else:
            return min(1.0, length / 500)

    def _calculate_coherence_score(self, question: str, answer: str) -> float:
        """计算连贯性分数"""
        # 简化的连贯性评分
        if not answer:
            return 0.0

        # 检查是否有明显的结构
        has_structure = any(
            marker in answer for marker in ['1.', '2.', '3.', '第一', '第二', '第三']
        )
        has_conclusion = any(marker in answer for marker in ['综上', '因此', '总结', '结论'])

        structure_score = 0.6 if has_structure else 0.3
        conclusion_score = 0.4 if has_conclusion else 0.2

        return min(1.0, structure_score + conclusion_score)

    def _calculate_correctness_score(self, question: str, answer: str) -> float:
        """计算正确性分数"""
        # 简化的正确性评分，基于关键词匹配
        question_keywords = set(self._extract_keywords(question))
        answer_keywords = set(self._extract_keywords(answer))

        if not question_keywords:
            return 0.5

        overlap = len(question_keywords & answer_keywords)
        coverage = overlap / len(question_keywords)

        return min(1.0, coverage * 2)  # 给予一定的容错

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        import re

        words = re.findall(r"\b\w+\b", text.lower())
        # 过滤停用词
        stop_words = {
            '的',
            '是',
            '在',
            '有',
            '和',
            '与',
            '或',
            '但',
            '如果',
            '因为',
            '所以',
            'the',
            'is',
            'at',
            'which',
            'on',
        }
        return [word for word in words if word not in stop_words and len(word) > 1]


class DiversityCalculator:
    """多样性计算器"""

    def calculate_similarity(self, hash1: str, hash2: str) -> float:
        """计算两个内容的相似度"""
        # 简化的相似度计算
        if hash1 == hash2:
            return 1.0

        # 计算哈希差异
        diff = sum(c1 != c2 for c1, c2 in zip(hash1, hash2, strict=False))
        max_len = max(len(hash1), len(hash2))

        similarity = 1 - (diff / max_len)
        return similarity


class PatentDataAugmenter:
    """专利数据增强器"""

    def paraphrase(self, item: dict) -> dict | None:
        """改写增强"""
        try:
            # 简化的改写实现
            question = item.get('question', '')
            answer = item.get('answer', '')

            # 改写问法
            if '请分析' in question:
                paraphrased_question = question.replace('请分析', '请评估')
            elif '请为' in question:
                paraphrased_question = question.replace('请为', '请制作')
            else:
                paraphrased_question = question + '（详细版本）'

            # 轻微修改回答
            paraphrased_answer = answer.replace('分析：', '评估：')

            new_item = item.copy()
            new_item.update(
                {
                    'question': paraphrased_question,
                    'answer': paraphrased_answer,
                    'augmentation_type': 'paraphrase',
                }
            )

            return new_item

        except Exception as e:
            logger.warning(f"改写增强失败: {e}")
            return None

    def replace_synonyms(self, item: dict) -> dict | None:
        """同义词替换增强"""
        try:
            answer = item.get('answer', '')

            # 简化的同义词替换
            synonym_map = {'分析': '评估', '技术': '工艺', '方法': '方案', '系统': '装置', '特征': '属性'}

            augmented_answer = answer
            for original, synonym in synonym_map.items():
                augmented_answer = augmented_answer.replace(original, synonym)

            if augmented_answer != answer:
                new_item = item.copy()
                new_item.update(
                    {
                        'answer': augmented_answer,
                        'augmentation_type': 'synonym_replacement',
                    }
                )
                return new_item

        except Exception as e:
            logger.warning(f"同义词替换失败: {e}")

        return None

    def adjust_difficulty(self, item: dict) -> dict | None:
        """难度调整增强"""
        try:
            current_difficulty = item.get('difficulty', 'medium')
            reasoning_steps = item.get('reasoning_steps', 1)

            # 随机调整难度
            if random.random() < 0.5:
                # 增加难度
                if current_difficulty == 'easy':
                    new_difficulty = 'medium'
                    new_steps = reasoning_steps + 1
                elif current_difficulty == 'medium':
                    new_difficulty = 'hard'
                    new_steps = reasoning_steps + 2
                else:
                    return None  # 已经是最难
            else:
                # 降低难度
                if current_difficulty == 'hard':
                    new_difficulty = 'medium'
                    new_steps = max(1, reasoning_steps - 1)
                elif current_difficulty == 'medium':
                    new_difficulty = 'easy'
                    new_steps = max(1, reasoning_steps - 1)
                else:
                    return None  # 已经是最简单

            new_item = item.copy()
            new_item.update(
                {
                    'difficulty': new_difficulty,
                    'reasoning_steps': new_steps,
                    'augmentation_type': 'difficulty_adjustment',
                }
            )

            return new_item

        except Exception as e:
            logger.warning(f"难度调整失败: {e}")
            return None


# 使用示例
if __name__ == '__main__':
    # 创建数据生成器
    config = DataGenerationConfig(num_samples_per_input=4, max_workers=2, batch_size=8)
    generator = PatentDataGenerator(config)

    # 模拟专利语料库
    patent_corpus = [
        {
            'patent_id': 'PAT001',
            'title': '一种新型机器学习算法',
            'abstract': '本发明涉及一种改进的机器学习算法...',
            'description': '详细描述...',
            'technical_field': '人工智能',
            'claims': ['1. 一种机器学习算法，其特征在于...'],
        },
        {
            'patent_id': 'PAT002',
            'title': '智能专利检索系统',
            'abstract': '本发明提供了一种智能专利检索方法...',
            'description': '系统详细描述...',
            'technical_field': '信息检索',
            'claims': ['1. 一种专利检索系统，包括...'],
        },
    ]

    # 生成训练数据
    results = generator.generate_from_patent_corpus(
        patent_corpus=patent_corpus, output_dir='./generated_patent_data'
    )

    logger.info("数据生成完成!")
    logger.info(f"最终样本数: {len(results['final_data'])}")
    logger.info(f"输出路径: {results['output_path']}")
