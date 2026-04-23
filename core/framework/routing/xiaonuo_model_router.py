#!/usr/bin/env python3

"""
小诺·双鱼公主智能模型路由器
Xiaonuo Intelligent Model Router

智能路由任务到最适合的模型,优先使用GLM-4包月服务
集成LLM缓存管理器,优化响应性能

作者: 小诺·双鱼座
创建时间: 2025-12-14
更新时间: 2025-12-16 (集成缓存系统)
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

# 导入缓存管理器
try:
    from llm_cache_manager import CacheConfig, LLMCacheManager
except ImportError:
    # 如果缓存管理器模块不存在,使用简单的缓存实现
    class CacheStrategy:
        ADAPTIVE = "adaptive"

    class CacheConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class LLMCacheManager:
        def __init__(self, config=None):
            self.config = config or {}

        def get_cache_statistics(self):
            return {"enabled": False}

        def clear_cache(self, pattern=None):
            pass


class TaskType(Enum):
    """任务类型"""

    PATENT_ANALYSIS = "patent_analysis"
    PATENT_APPLICATION = "patent_application"
    LEGAL_ANALYSIS = "legal_analysis"
    LEGAL_REVIEW = "legal_review"
    CODE_GENERATION = "code_generation"
    TECHNICAL_DEVELOPMENT = "technical_development"
    CONTENT_CREATION = "content_creation"
    CREATIVE_WRITING = "creative_writing"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"
    GENERAL_CHAT = "general_chat"
    QA = "qa"
    EMBEDDING = "embedding"


@dataclass
class ModelConfig:
    """模型配置"""

    name: str
    provider: str
    api_endpoint: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    priority: int = 10
    monthly_cost: float = 0.0
    capabilities: Optional[list[str]] = None


@dataclass
class TaskRequest:
    """任务请求"""

    id: str
    task_type: TaskType
    content: str
    priority: int = 1
    context: Optional[dict[str, Any]] = None
    timestamp: datetime = None
    user_id: Optional[str] = None


@dataclass
class RoutingDecision:
    """路由决策"""

    selected_model: ModelConfig
    confidence: float
    reasoning: str
    fallback_options: Optional[list[ModelConfig]] = None


class XiaonuoModelRouter:
    """小诺·双鱼公主智能模型路由器"""

    def __init__(self):
        self.name = "小诺·双鱼公主智能模型路由器"
        self.version = "2.1.0"  # 升级版本以支持缓存
        self.logger = logging.getLogger(self.name)

        # 加载配置
        self.priority_config = self._load_priority_config()

        # 初始化模型
        self.models = self._initialize_models()

        # 初始化缓存系统
        self.cache_manager = self._init_cache_manager()

        # 使用统计
        self.usage_stats = {
            "glm_4_usage": 0,
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cost_savings": 0.0,
            "fallback_count": 0,
            "avg_response_time": 0.0,
        }

        # 性能缓存
        self.model_performance = {}

        print(f"🎯 {self.name} 初始化完成 - 优先使用GLM-4 + 智能缓存")

    def _load_priority_config(self) -> dict[str, Any]:
        """加载优先级配置"""
        try:
            with open(
                "/Users/xujian/Athena工作平台/config/xiaonuo_model_priority_config.json",
                encoding="utf-8",
            ) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "primary_model": {"name": "glm-4", "provider": "zhipu", "priority": 1},
            "model_selection_rules": {
                "default_rule": {"selected_model": "glm-4", "confidence": 0.95}
            },
        }

    def _initialize_models(self) -> dict[str, ModelConfig]:
        """初始化模型配置"""
        models = {}

        # GLM-4 - 主要模型
        models["glm-4"] = ModelConfig(
            name="glm-4",
            provider="zhipu",
            api_endpoint="https://open.bigmodel.cn/api/paas/v4/",
            priority=1,
            monthly_cost=0.0,  # 包月服务
            capabilities=["chat", "reasoning", "code", "creative", "analysis"],
        )

        # 备用模型
        models["qwen:7b"] = ModelConfig(
            name="qwen:7b",
            provider="ollama",
            priority=2,
            monthly_cost=0.0,
            capabilities=["chat", "reasoning"],
        )

        models["qwen2.5vl:latest"] = ModelConfig(
            name="qwen2.5vl:latest",
            provider="ollama",
            priority=3,
            capabilities=["chat", "multimodal", "reasoning"],
        )

        # BGE向量模型(高质量中文嵌入)
        models["bge-large-zh-v1.5"] = ModelConfig(
            name="bge-large-zh-v1.5",
            provider="local",
            priority=1,
            capabilities=["embedding", "chinese", "patent", "legal"],
        )

        # Ollama嵌入模型(快速响应)
        models["nomic-embed-text"] = ModelConfig(
            name="nomic-embed-text",
            provider="ollama",
            priority=2,
            capabilities=["embedding", "fast"],
        )

        return models

    def _init_cache_manager(self) -> LLMCacheManager:
        """初始化缓存管理器"""
        cache_config = CacheConfig(
            enabled=True,
            strategy="adaptive",
            max_size=5000,  # 内存缓存5000条
            ttl=7200,  # 2小时过期
            similarity_threshold=0.85,
            min_response_length=30,
            cleanup_interval=300,
            preload_hot_cache=True,
        )

        cache_manager = LLMCacheManager(cache_config)
        self.logger.info(f"LLM缓存系统已启用 - 策略: {cache_config.strategy}")
        return cache_manager

    async def call_llm_with_cache(
        self,
        prompt: str,
        model_name: str,
        task_type: str = "general_chat",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_cache: bool = True,
    ) -> Optional[str]:
        """
        调用LLM并使用缓存

        Args:
            prompt: 用户提示
            model_name: 模型名称
            task_type: 任务类型
            temperature: 温度参数
            max_tokens: 最大令牌数
            use_cache: 是否使用缓存

        Returns:
            LLM响应
        """
        start_time = time.time()
        self.usage_stats["total_requests"] += 1

        try:
            # 1. 尝试从缓存获取
            if use_cache and self.cache_manager:
                cached_response = await self.cache_manager.get(
                    prompt, model_name, task_type, temperature, max_tokens
                )
                if cached_response:
                    self.usage_stats["cache_hits"] += 1
                    self.logger.info(f"缓存命中: {model_name} - {task_type}")
                    return cached_response
                else:
                    self.usage_stats["cache_misses"] += 1

            # 2. 调用实际的LLM
            response = await self._call_actual_llm(
                prompt, model_name, task_type, temperature, max_tokens
            )

            # 3. 存储到缓存
            if response and use_cache and self.cache_manager:
                await self.cache_manager.set(
                    prompt, response, model_name, task_type, temperature, max_tokens
                )
                self.logger.info(f"响应已缓存: {model_name} - {len(response)}字符")

            # 4. 更新统计
            if model_name == "glm-4":
                self.usage_stats["glm_4_usage"] += 1

            response_time = time.time() - start_time
            self.usage_stats["avg_response_time"] = (
                self.usage_stats["avg_response_time"] * (self.usage_stats["total_requests"] - 1)
                + response_time
            ) / self.usage_stats["total_requests"]

            return response

        except Exception as e:
            self.logger.error(f"LLM调用失败 {model_name}: {e}")
            return None

    async def _call_actual_llm(
        self, prompt: str, model_name: str, task_type: str, temperature: float, max_tokens: int
    ) -> Optional[str]:
        """调用实际的LLM API"""
        # 这里应集成实际的LLM调用逻辑
        # 简化实现,实际应用中需要根据不同provider实现

        if model_name == "glm-4":
            return await self._call_glm4_api(prompt, temperature, max_tokens)
        elif model_name.startswith(("qwen", "nomic", "llama")):
            return await self._call_ollama_api(model_name, prompt, temperature, max_tokens)
        else:
            self.logger.warning(f"未知模型: {model_name}")
            return None

    async def get_embedding(
        self, texts: str | list[str], task_type: str = "default"
    ) -> list[Optional[float]]:
        """
        获取文本嵌入向量

        Args:
            texts: 文本或文本列表
            task_type: 任务类型,用于选择最佳嵌入模型

        Returns:
            嵌入向量或向量列表
        """
        try:
            # 根据任务类型选择模型
            if task_type in [
                "patent_search",
                "legal_analysis",
                "patent_analysis",
                "document_classification",
            ]:
                model_name = "bge-large-zh-v1.5"  # 高质量任务使用BGE
            elif task_type in ["simple_chat", "quick_match"]:
                model_name = "nomic-embed-text"  # 快速任务使用Ollama
            else:
                model_name = "bge-large-zh-v1.5"  # 默认使用BGE

            # 使用BGE服务
            if model_name == "bge-large-zh-v1.5":
                from ..nlp.bge_embedding_service import get_bge_service

                bge_service = await get_bge_service()
                result = await bge_service.encode(texts, task_type=task_type)
                return result.embeddings

            # 使用Ollama嵌入
            elif model_name == "nomic-embed-text":
                return await self._get_ollama_embedding(texts)

            return None

        except Exception as e:
            self.logger.error(f"获取嵌入失败: {e}")
            return None

    async def _get_ollama_embedding(self, texts: str | list[str]) -> list[float]:
        """获取Ollama嵌入向量"""
        import requests

        if isinstance(texts, list):
            texts = texts[0]  # Ollama API一次只能处理一个文本

        try:
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": texts},
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return result["embedding"]
            else:
                self.logger.error(f"Ollama嵌入API错误: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Ollama嵌入调用失败: {e}")
            return None

    async def _call_glm4_api(
        self, prompt: str, temperature: float, max_tokens: int
    ) -> Optional[str]:
        """调用智谱GLM-4 API"""
        try:
            import requests

            # 加载API配置
            with open("/Users/xujian/Athena工作平台/config/domestic_llm_config.json") as f:
                config = json.load(f)

            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {
                "Authorization": f"Bearer {config['zhipu_api_key']}",
                "Content-Type": "application/json",
            }
            data = {
                "model": "glm-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                self.logger.error(f"GLM-4 API错误: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"GLM-4调用失败: {e}")
            return None

    async def _call_ollama_api(
        self, model_name: str, prompt: str, temperature: float, max_tokens: int
    ) -> Optional[str]:
        """调用Ollama本地API"""
        try:
            import requests

            url = "http://localhost:11434/api/generate"
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }

            response = requests.post(url, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                self.logger.error(f"Ollama API错误: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Ollama调用失败: {e}")
            return None

    def select_model(self, task_type: str, fallback_allowed: bool = True) -> ModelConfig:
        """
        根据任务类型选择模型

        Args:
            task_type: 任务类型字符串
            fallback_allowed: 是否允许使用备用模型

        Returns:
            ModelConfig: 选中的模型配置
        """
        # 1. 优先选择GLM-4
        if self._can_use_glm4_type(task_type):
            model = self.models["glm-4"]
            self.logger.info(f"选择GLM-4处理任务: {task_type}")
            return model

        # 2. 根据任务类型规则选择
        rules = self.priority_config.get("model_selection_rules", {})

        # 任务类型映射
        task_mapping = {
            "patent_analysis": "patent_tasks",
            "patent_application": "patent_tasks",
            "legal_analysis": "legal_tasks",
            "legal_review": "legal_tasks",
            "code_generation": "code_generation",
            "technical_development": "code_generation",
            "content_creation": "creative_tasks",
            "creative_writing": "creative_tasks",
            "data_analysis": "data_analysis",
            "report_generation": "data_analysis",
            "general_chat": "conversation",
            "qa": "conversation",
        }

        rule_name = task_mapping.get(task_type, "default_rule")
        rule = rules.get(rule_name, {})
        model_name = rule.get("selected_model", "glm-4")

        if model_name in self.models:
            model = self.models[model_name]
            # 优化参数
            if "temperature" in rule:
                model.temperature = rule["temperature"]
            if "max_tokens" in rule:
                model.max_tokens = rule["max_tokens"]
            self.logger.info(f"根据规则选择模型: {task_type} -> {model_name}")
            return model

        # 3. 如果允许备用,选择备用模型
        if fallback_allowed:
            # 选择可用的备用模型
            for model in sorted(self.models.values(), key=lambda x: x.priority):
                if model.name != "glm-4" and self._is_model_available(model):
                    self.logger.info(f"使用备用模型: {task_type} -> {model.name}")
                    return model

        # 4. 默认返回GLM-4
        return self.models["glm-4"]

    def _can_use_glm4_type(self, task_type: str) -> bool:
        """判断任务类型是否适合使用GLM-4"""
        # GLM-4可以处理所有类型的任务,但可以根据负载等因素调整
        # 这里可以添加更复杂的逻辑,比如:
        # - 负载过高时使用备用模型
        # - 特定任务使用特定模型
        # - 成本控制等
        return True

    async def route_task(self, task: TaskRequest) -> RoutingDecision:
        """路由任务到最适合的模型"""
        self.usage_stats["total_requests"] += 1

        # 1. 检查任务类型规则
        decision = self._apply_task_type_rules(task)

        # 2. 优先选择GLM-4
        if self._can_use_glm4(task):
            decision.selected_model = self.models["glm-4"]
            decision.confidence = 0.95
            decision.reasoning = "GLM-4是包月服务,优先使用以最大化性价比"
            self.usage_stats["glm_4_usage"] += 1
        else:
            # 3. 选择备用模型
            decision = self._select_fallback_model(task)

        # 4. 优化参数
        decision.selected_model = self._optimize_model_parameters(decision.selected_model, task)

        # 5. 准备备用选项
        decision.fallback_options = self._prepare_fallback_options(decision.selected_model)

        self.logger.info(
            f"路由决策: {task.id} -> {decision.selected_model.name} ({decision.confidence:.2f})"
        )

        return decision

    def _can_use_glm4(self, task: TaskRequest) -> bool:
        """判断是否可以使用GLM-4"""
        # GLM-4可以处理所有类型的任务
        return True

    def _apply_task_type_rules(self, task: TaskRequest) -> RoutingDecision:
        """应用任务类型规则"""
        rules = self.priority_config.get("model_selection_rules", {})

        # 根据任务类型选择配置
        if task.task_type == TaskType.PATENT_ANALYSIS:
            rule = rules.get("patent_tasks", {})
        elif task.task_type == TaskType.LEGAL_ANALYSIS:
            rule = rules.get("legal_tasks", {})
        elif task.task_type == TaskType.CODE_GENERATION:
            rule = rules.get("code_generation", {})
        elif task.task_type == TaskType.CONTENT_CREATION:
            rule = rules.get("creative_tasks", {})
        elif task.task_type == TaskType.DATA_ANALYSIS:
            rule = rules.get("data_analysis", {})
        elif task.task_type == TaskType.GENERAL_CHAT:
            rule = rules.get("conversation", {})
        else:
            rule = rules.get("default_rule", {})

        model_name = rule.get("selected_model", "glm-4")
        model = self.models.get(model_name, self.models["glm-4"])

        return RoutingDecision(
            selected_model=model,
            confidence=rule.get("confidence", 0.95),
            reasoning=rule.get("description", "规则匹配"),
        )

    def _select_fallback_model(self, task: TaskRequest) -> RoutingDecision:
        """选择备用模型"""
        self.usage_stats["fallback_count"] += 1

        # 选择最高优先级的可用模型
        available_models = [
            model
            for model in self.models.values()
            if model.name != "glm-4" and self._is_model_available(model)
        ]

        if available_models:
            selected = min(available_models, key=lambda m: m.priority)
            return RoutingDecision(
                selected_model=selected,
                confidence=0.7,
                reasoning=f"GLM-4不可用,使用备用模型: {selected.name}",
            )

        # 最后的选择
        return RoutingDecision(
            selected_model=self.models["qwen:7b"], confidence=0.5, reasoning="使用默认备用模型"
        )

    def _optimize_model_parameters(self, model: ModelConfig, task: TaskRequest) -> ModelConfig:
        """根据任务优化模型参数"""
        # 创建副本避免修改原配置
        optimized = ModelConfig(
            name=model.name,
            provider=model.provider,
            api_endpoint=model.api_endpoint,
            priority=model.priority,
            monthly_cost=model.monthly_cost,
            capabilities=model.capabilities,
        )

        # 根据任务类型调整参数
        if task.task_type in [TaskType.PATENT_ANALYSIS, TaskType.LEGAL_ANALYSIS]:
            optimized.temperature = 0.3  # 低温度保证严谨性
            optimized.max_tokens = 2500  # 需要详细分析
        elif task.task_type == TaskType.CODE_GENERATION:
            optimized.temperature = 0.1  # 代码生成需要精确
            optimized.max_tokens = 3000  # 代码可能较长
        elif task.task_type in [TaskType.CONTENT_CREATION, TaskType.CREATIVE_WRITING]:
            optimized.temperature = 0.8  # 创意需要高温度
            optimized.max_tokens = 1500  # 适中的长度
        elif task.task_type == TaskType.DATA_ANALYSIS:
            optimized.temperature = 0.4  # 分析需要平衡
            optimized.max_tokens = 2000  # 足够的分析长度
        elif task.task_type in [TaskType.GENERAL_CHAT, TaskType.QA]:
            optimized.temperature = 0.7  # 对话需要自然
            optimized.max_tokens = 1000  # 对话不宜过长
        else:
            optimized.temperature = model.temperature
            optimized.max_tokens = model.max_tokens

        return optimized

    def _prepare_fallback_options(self, primary_model: ModelConfig) -> list[ModelConfig]:
        """准备备用选项"""
        fallbacks = []

        # 按优先级添加备用模型
        for model in sorted(self.models.values(), key=lambda m: m.priority):
            if model.name != primary_model.name and self._is_model_available(model):
                fallbacks.append(model)
                if len(fallbacks) >= 2:  # 最多2个备用选项
                    break

        return fallbacks

    def _is_model_available(self, model: ModelConfig) -> bool:
        """检查模型是否可用"""
        # 简化实现,实际应该检查健康状态
        return True

    async def batch_route(self, tasks: list[TaskRequest]) -> list[RoutingDecision]:
        """批量路由任务"""
        decisions = []

        # 优先使用GLM-4处理批量任务
        can_use_glm4 = all(self._can_use_glm4(task) for task in tasks)

        if can_use_glm4:
            # 批量使用GLM-4
            for task in tasks:
                decision = await self.route_task(task)
                decisions.append(decision)
        else:
            # 分别处理
            for task in tasks:
                decision = await self.route_task(task)
                decisions.append(decision)

        return decisions

    def get_usage_statistics(self) -> dict[str, Any]:
        """获取使用统计"""
        glm4_ratio = self.usage_stats["glm_4_usage"] / max(self.usage_stats["total_requests"], 1)

        return {
            "total_requests": self.usage_stats["total_requests"],
            "glm4_usage": self.usage_stats["glm_4_usage"],
            "glm4_ratio": glm4_ratio,
            "fallback_count": self.usage_stats["fallback_count"],
            "cost_savings": self._calculate_cost_savings(),
            "efficiency_score": glm4_ratio * 100,  # GLM-4使用率作为效率分数
        }

    def _calculate_cost_savings(self) -> float:
        """计算节省的成本"""
        # 假设每次GLM-4调用节省$0.01
        return self.usage_stats["glm_4_usage"] * 0.01

    def get_optimization_suggestions(self) -> list[str]:
        """获取优化建议"""
        suggestions = []
        stats = self.get_usage_statistics()

        if stats["glm4_ratio"] < 0.8:
            suggestions.append("GLM-4使用率较低,建议调整路由策略优先使用GLM-4")

        if stats["fallback_count"] / stats["total_requests"] > 0.1:
            suggestions.append("备用模型使用率较高,建议检查GLM-4的可用性")

        if stats["efficiency_score"] > 95:
            suggestions.append("GLM-4使用率优秀,继续保持!")

        return suggestions


# 导出主类
__all__ = ["ModelConfig", "RoutingDecision", "TaskRequest", "TaskType", "XiaonuoModelRouter"]

