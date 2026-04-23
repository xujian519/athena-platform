#!/usr/bin/env python3
"""
GLM模型选择器 - 智能选择最适合的GLM模型
基于任务类型、性能需求和成本预算自动选择模型

Author: Athena平台团队
Date: 2026-04-22
"""

from pathlib import Path

import yaml
from typing import Optional


class GLMModel(str):
    """GLM模型枚举"""

    # 旗舰模型
    GLM_4_PLUS = "glm-4-plus"
    GLM_4_0520 = "glm-4-0520"

    # 高性能模型
    GLM_4_AIR = "glm-4-air"
    GLM_4_FLASH = "glm-4-flash"

    # 基础模型
    GLM_4 = "glm-4"


class TaskType(str):
    """任务类型枚举"""
    PATENT_DEEP_ANALYSIS = "patent_deep_analysis"  # 深度专利分析
    PATENT_SCREENING = "patent_screening"  # 专利筛选
    FEATURE_EXTRACTION = "feature_extraction"  # 特征提取
    EVIDENCE_EVALUATION = "evidence_evaluation"  # 证据评估
    REASONING_WRITING = "reasoning_writing"  # 理由撰写
    QUICK_QUERY = "quick_query"  # 快速查询


class PerformancePreference(str):
    """性能偏好枚举"""
    QUALITY = "quality"  # 质量优先
    BALANCED = "balanced"  # 平衡
    SPEED = "speed"  # 速度优先
    COST = "cost"  # 成本优先


class GLMModelSelector:
    """GLM模型智能选择器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化模型选择器

        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "glm_models.yaml"

        with open(config_path, encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.models = self.config['models']
        self.scenarios = self.config['scenarios']
        self.performance = self.config['performance_comparison']

    def select_model(
        self,
        task_type: TaskType,
        preference: PerformancePreference = PerformancePreference.BALANCED,
        custom_model: Optional[str] = None
    ) -> str:
        """
        智能选择模型

        Args:
            task_type: 任务类型
            preference: 性能偏好
            custom_model: 自定义模型（优先级最高）

        Returns:
            模型名称
        """
        # 如果指定了自定义模型，直接返回
        if custom_model:
            if custom_model in self.models:
                return custom_model
            else:
                raise ValueError(f"未知模型: {custom_model}，可用模型: {list(self.models.keys())}")

        # 基于任务类型选择
        if task_type in self.scenarios:
            scenario_config = self.scenarios[task_type]
            primary_model = scenario_config['primary']

            # 根据偏好调整
            if preference == PerformancePreference.SPEED:
                # 优先选择更快的模型
                alternatives = scenario_config.get('alternatives', [])
                if 'glm-4-flash' in alternatives:
                    return 'glm-4-flash'
                elif 'glm-4-air' in alternatives:
                    return 'glm-4-air'

            elif preference == PerformancePreference.COST:
                # 优先选择更便宜的模型
                alternatives = scenario_config.get('alternatives', [])
                if 'glm-4-flash' in alternatives:
                    return 'glm-4-flash'
                elif 'glm-4-air' in alternatives:
                    return 'glm-4-air'

            elif preference == PerformancePreference.QUALITY:
                # 质量优先，使用主要推荐
                return primary_model

            else:  # BALANCED
                # 平衡模式，返回主要推荐
                return primary_model

        # 默认返回项目默认配置
        return self.config['project_defaults']['patent_analysis']

    def get_model_info(self, model: str) -> dict:
        """
        获取模型详细信息

        Args:
            model: 模型名称

        Returns:
            模型信息字典
        """
        return self.models.get(model, {})

    def compare_models(self, models: list) -> dict:
        """
        比较多个模型

        Args:
            models: 模型列表

        Returns:
            比较结果
        """
        comparison = {}
        for model in models:
            if model in self.models:
                comparison[model] = {
                    'name': self.models[model]['name'],
                    'speed': self.models[model]['speed'],
                    'quality': self.models[model]['quality'],
                    'pricing': self.models[model]['pricing']
                }
        return comparison

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        files: int = 1
    ) -> dict:
        """
        估算成本

        Args:
            model: 模型名称
            input_tokens: 输入token数
            output_tokens: 输出token数
            files: 文件数量

        Returns:
            成本估算
        """
        if model not in self.models:
            raise ValueError(f"未知模型: {model}")

        pricing = self.models[model]['pricing']
        input_cost = (input_tokens * files / 1000) * pricing['input']
        output_cost = (output_tokens * files / 1000) * pricing['output']
        total_cost = input_cost + output_cost

        return {
            'input_cost': round(input_cost, 4),
            'output_cost': round(output_cost, 4),
            'total_cost': round(total_cost, 4),
            'currency': 'CNY'
        }

    def recommend_for_batch(
        self,
        total_files: int,
        task_type: TaskType,
        budget_limit: Optional[float] = None
    ) -> dict:
        """
        批量任务模型推荐

        Args:
            total_files: 总文件数
            task_type: 任务类型
            budget_limit: 预算限制（元）

        Returns:
            推荐结果
        """
        recommendations = []

        # 尝试每个模型
        for model_name, model_info in self.models.items():
            # 估算token使用
            if task_type == TaskType.PATENT_DEEP_ANALYSIS:
                input_tokens = 1500
                output_tokens = 400
            elif task_type == TaskType.PATENT_SCREENING:
                input_tokens = 500
                output_tokens = 200
            elif task_type == TaskType.QUICK_QUERY:
                input_tokens = 300
                output_tokens = 100
            else:
                input_tokens = 1000
                output_tokens = 300

            # 估算成本
            cost = self.estimate_cost(model_name, input_tokens, output_tokens, total_files)

            # 检查预算
            if budget_limit and cost['total_cost'] > budget_limit:
                continue

            recommendations.append({
                'model': model_name,
                'name': model_info['name'],
                'speed': model_info['speed'],
                'quality': model_info['quality'],
                'estimated_cost': cost['total_cost'],
                'estimated_time': self._estimate_time(model_name, total_files)
            })

        # 按质量排序
        recommendations.sort(key=lambda x: {
            '⭐⭐⭐⭐⭐': 5,
            '⭐⭐⭐⭐': 4,
            '⭐⭐⭐': 3
        }.get(x['quality'], 0), reverse=True)

        return {
            'task_type': task_type,
            'total_files': total_files,
            'budget_limit': budget_limit,
            'recommendations': recommendations
        }

    def _estimate_time(self, model: str, files: int) -> str:
        """估算处理时间"""
        speed_map = {
            'glm-4-flash': 2,  # 秒/文件
            'glm-4-air': 5,
            'glm-4-plus': 10,
            'glm-4-0520': 10,
            'glm-4': 12
        }

        seconds_per_file = speed_map.get(model, 10)
        total_seconds = seconds_per_file * files
        minutes = total_seconds / 60

        if minutes < 60:
            return f"{minutes:.1f}分钟"
        else:
            hours = minutes / 60
            return f"{hours:.1f}小时"


# ==================== 便捷函数 ====================

def get_recommended_model(task_type: TaskType = TaskType.PATENT_DEEP_ANALYSIS) -> str:
    """
    获取推荐模型

    Args:
        task_type: 任务类型

    Returns:
        模型名称
    """
    selector = GLMModelSelector()
    return selector.select_model(task_type)


def get_model_info(model: str) -> dict:
    """
    获取模型信息

    Args:
        model: 模型名称

    Returns:
        模型信息
    """
    selector = GLMModelSelector()
    return selector.get_model_info(model)


def compare_glm_models() -> dict:
    """对比所有GLM模型"""
    selector = GLMModelSelector()
    return selector.compare_models(['glm-4-plus', 'glm-4-air', 'glm-4-flash'])


def estimate_analysis_cost(model: str, files: int) -> dict:
    """
    估算分析成本

    Args:
        model: 模型名称
        files: 文件数量

    Returns:
        成本估算
    """
    selector = GLMModelSelector()
    return selector.estimate_cost(
        model,
        input_tokens=1500,
        output_tokens=400,
        files=files
    )


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例1：获取推荐模型
    print("示例1：深度专利分析推荐模型")
    model = get_recommended_model(TaskType.PATENT_DEEP_ANALYSIS)
    print(f"推荐模型: {model}\n")

    # 示例2：对比模型
    print("示例2：GLM模型对比")
    comparison = compare_glm_models()
    for model_name, info in comparison.items():
        print(f"{model_name}:")
        print(f"  名称: {info['name']}")
        print(f"  速度: {info['speed']}")
        print(f"  质量: {info['quality']}")
        print(f"  价格: 输入¥{info['pricing']['input']}/1K, 输出¥{info['pricing']['output']}/1K")
        print()

    # 示例3：成本估算
    print("示例3：169个专利分析成本估算")
    for model in ['glm-4-plus', 'glm-4-air', 'glm-4-flash']:
        cost = estimate_analysis_cost(model, 169)
        print(f"{model}: ¥{cost['total_cost']:.2f}")
    print()

    # 示例4：批量任务推荐
    print("示例4：批量任务智能推荐")
    selector = GLMModelSelector()
    recommendation = selector.recommend_for_batch(
        total_files=169,
        task_type=TaskType.PATENT_DEEP_ANALYSIS,
        budget_limit=5.0  # 预算限制5元
    )
    print(f"任务类型: {recommendation['task_type']}")
    print(f"文件数量: {recommendation['total_files']}")
    print(f"预算限制: ¥{recommendation['budget_limit']}")
    print("\n推荐模型:")
    for rec in recommendation['recommendations']:
        print(f"  {rec['model']} ({rec['name']})")
        print(f"    质量: {rec['quality']}")
        print(f"    速度: {rec['speed']}")
        print(f"    成本: ¥{rec['estimated_cost']:.2f}")
        print(f"    预计时间: {rec['estimated_time']}")
