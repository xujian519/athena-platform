#!/usr/bin/env python3
"""
小娜LLM集成服务 v2.3
支持GLM和DeepSeek API，智能模型选择策略

作者: 小诺·双鱼公主
版本: v2.3.0
"""

from __future__ import annotations
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

try:
    import requests
    from openai import OpenAI
except ImportError:
    requests = None
    OpenAI = None


class LLMProvider(Enum):
    """LLM提供商"""
    GLM = "glm"
    DEEPSEEK = "deepseek"


class ModelTier(Enum):
    """模型等级"""
    FLASH = "flash"      # 快速、低成本
    AIR = "air"          # 性价比
    PLUS = "plus"        # 高质量
    FULL = "full"        # 旗舰级


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    provider: LLMProvider
    model: str
    tier: ModelTier
    tokens_used: int
    latency_ms: int
    success: bool
    error: str | None = None


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    tier: ModelTier
    max_tokens: int
    cost_per_million: float  # 元/百万tokens


# GLM模型配置
GLM_MODELS_CONFIG = {
    "glm-4-flash": {"tier": ModelTier.FLASH, "max_tokens": 128000, "cost": 0.1},
    "glm-4-air": {"tier": ModelTier.AIR, "max_tokens": 128000, "cost": 1.0},
    "glm-4-plus": {"tier": ModelTier.PLUS, "max_tokens": 128000, "cost": 5.0},
    "glm-4": {"tier": ModelTier.FULL, "max_tokens": 128000, "cost": 10.0},
}

# DeepSeek模型配置
DEEPSEEK_MODELS_CONFIG = {
    "deepseek-chat": {"tier": ModelTier.AIR, "max_tokens": 64000, "cost": 1.0},
    "deepseek-coder": {"tier": ModelTier.AIR, "max_tokens": 64000, "cost": 1.0},
}


class ComplexityAssessor:
    """复杂度评估器"""

    # 复杂查询关键词
    COMPLEX_KEYWORDS = [
        "创造性分析", "三步法", "技术启示",
        "无效宣告", "无效策略", "无效分析",
        "权利要求修改", "答复策略",
        "多法条关联", "法条关系",
        "对比文件分析", "区别特征",
        "最接近现有技术", "实际解决技术问题",
        "显而易见", "常规手段", "公知常识"
    ]

    # 简单查询关键词
    SIMPLE_KEYWORDS = [
        "什么是", "是什么", "如何定义",
        "法条查询", "查询法条",
        "简单解释", "简述",
        "流程", "步骤", "时间"
    ]

    @classmethod
    def assess(cls, query: str, intent: str = None, scenario: str = None) -> ModelTier:
        """
        评估查询复杂度

        Args:
            query: 用户查询
            intent: 意图（可选）
            scenario: 业务场景（可选）

        Returns:
            推荐的模型等级
        """
        query_lower = query.lower()

        # 1. 检查复杂查询关键词
        if any(kw in query for kw in cls.COMPLEX_KEYWORDS):
            return ModelTier.PLUS

        # 2. 检查特定场景
        complex_scenarios = ["office_action", "invalid_strategy"]
        if scenario in complex_scenarios:
            return ModelTier.PLUS

        # 3. 检查简单查询关键词
        if any(kw in query for kw in cls.SIMPLE_KEYWORDS):
            return ModelTier.FLASH

        # 4. 检查特定意图
        if intent in ["law_query", "concept_explain"]:
            return ModelTier.FLASH

        # 5. 检查查询长度
        if len(query) > 200:
            return ModelTier.AIR

        # 6. 检查是否包含多个问题
        if query.count('?') > 1 or query.count('？') > 1:
            return ModelTier.AIR

        # 7. 默认中等复杂度
        return ModelTier.FLASH


class XiaonaLLMService:
    """小娜LLM服务 v2.3 - 智能模型选择"""

    def __init__(self,
                 glm_api_key: str = None,
                 deepseek_api_key: str = None,
                 primary: LLMProvider = LLMProvider.GLM,
                 fallback: LLMProvider = LLMProvider.DEEPSEEK,
                 auto_fallback: bool = True,
                 max_retries: int = 3,
                 strategy: str = "balanced"):  # cost_first / quality_first / balanced
        """
        初始化LLM服务

        Args:
            glm_api_key: GLM API密钥
            deepseek_api_key: DeepSeek API密钥
            primary: 主要LLM提供商
            fallback: 备用LLM提供商
            auto_fallback: 是否自动回退
            max_retries: 最大重试次数
            strategy: 模型选择策略
        """
        self.primary = primary
        self.fallback = fallback
        self.auto_fallback = auto_fallback
        self.max_retries = max_retries
        self.strategy = strategy

        # 日志
        self.logger = logging.getLogger(__name__)

        # 初始化客户端
        self.glm_client = self._init_glm_client(glm_api_key)
        self.deepseek_client = self._init_deepseek_client(deepseek_api_key)

        # 根据策略配置模型
        self._configure_models_by_strategy()

        # 统计信息
        self.stats = {
            "glm_requests": 0,
            "glm_success": 0,
            "glm_errors": 0,
            "deepseek_requests": 0,
            "deepseek_success": 0,
            "deepseek_errors": 0,
            "fallback_count": 0,
            # 模型使用统计
            "model_usage": {
                "glm-4-flash": 0,
                "glm-4-air": 0,
                "glm-4-plus": 0,
                "glm-4": 0,
                "deepseek-chat": 0
            }
        }

    def _configure_models_by_strategy(self) -> Any:
        """根据策略配置模型"""
        strategies = {
            "cost_first": {  # 成本优先
                ModelTier.FLASH: "glm-4-flash",
                ModelTier.AIR: "glm-4-flash",  # 也用flash
                ModelTier.PLUS: "glm-4-flash",  # 复杂的也用flash
                ModelTier.FULL: "glm-4-flash"
            },
            "quality_first": {  # 质量优先
                ModelTier.FLASH: "glm-4-air",
                ModelTier.AIR: "glm-4-plus",
                ModelTier.PLUS: "glm-4",
                ModelTier.FULL: "glm-4"
            },
            "balanced": {  # 平衡策略 (推荐)
                ModelTier.FLASH: "glm-4-flash",
                ModelTier.AIR: "glm-4-air",
                ModelTier.PLUS: "glm-4-plus",
                ModelTier.FULL: "glm-4"
            }
        }

        self.model_mapping = strategies.get(self.strategy, strategies["balanced"])

        self.logger.info(f"📊 模型选择策略: {self.strategy}")
        self.logger.info(f"   Flash → {self.model_mapping[ModelTier.FLASH]}")
        self.logger.info(f"   Air → {self.model_mapping[ModelTier.AIR]}")
        self.logger.info(f"   Plus → {self.model_mapping[ModelTier.PLUS]}")

    def _init_glm_client(self, api_key: str) -> Any:
        """初始化GLM客户端"""
        if not api_key:
            self.logger.warning("GLM API密钥未配置")
            return None

        try:
            return OpenAI(
                api_key=api_key,
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
        except Exception as e:
            self.logger.error(f"GLM客户端初始化失败: {e}")
            return None

    def _init_deepseek_client(self, api_key: str) -> Any:
        """初始化DeepSeek客户端"""
        if not api_key:
            self.logger.warning("DeepSeek API密钥未配置")
            return None

        try:
            return OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )
        except Exception as e:
            self.logger.error(f"DeepSeek客户端初始化失败: {e}")
            return None

    def select_model(self,
                    query: str,
                    intent: str = None,
                    scenario: str = None) -> str:
        """
        智能选择模型

        Args:
            query: 用户查询
            intent: 意图（可选）
            scenario: 业务场景（可选）

        Returns:
            推荐的模型名称
        """
        # 评估复杂度
        tier = ComplexityAssessor.assess(query, intent, scenario)

        # 映射到具体模型
        model = self.model_mapping.get(tier, "glm-4-flash")

        self.logger.info(f"🎯 智能模型选择: {query[:50]}... → {model} (tier: {tier.value})")

        return model

    def generate(self,
                 system_prompt: str,
                 user_message: str,
                 provider: LLMProvider = None,
                 model: str = None,
                 query: str = None,  # 用于智能选择
                 intent: str = None,
                 scenario: str = None,
                 max_tokens: int = 8000,
                 temperature: float = 0.3) -> LLMResponse:
        """
        生成LLM响应

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            provider: LLM提供商 (None则使用primary)
            model: 模型名称 (None则智能选择)
            query: 原始查询（用于智能选择）
            intent: 意图
            scenario: 业务场景
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            LLMResponse对象
        """
        provider = provider or self.primary

        # 智能模型选择
        if model is None and query:
            model = self.select_model(query, intent, scenario)
        elif model is None:
            model = "glm-4-flash"  # 默认

        # 模型配置
        model_configs = {
            LLMProvider.GLM: {
                "client": self.glm_client,
                "stats_key": "glm_requests"
            },
            LLMProvider.DEEPSEEK: {
                "client": self.deepseek_client,
                "stats_key": "deepseek_requests"
            }
        }

        config = model_configs[provider]
        client = config["client"]

        if not client:
            if provider == self.primary and self.auto_fallback:
                self.logger.warning(f"{provider.value}客户端未初始化，回退到{self.fallback.value}")
                self.stats["fallback_count"] += 1
                return self.generate(system_prompt, user_message,
                                    provider=self.fallback,
                                    model=model,
                                    query=query,
                                    intent=intent,
                                    scenario=scenario,
                                    max_tokens=max_tokens,
                                    temperature=temperature)
            return LLMResponse(
                content="",
                provider=provider,
                model=model,
                tier=ModelTier.FLASH,
                tokens_used=0,
                latency_ms=0,
                success=False,
                error=f"{provider.value}客户端未初始化"
            )

        # 更新统计
        self.stats[config["stats_key"]] += 1
        if model in self.stats["model_usage"]:
            self.stats["model_usage"][model] += 1

        # 调用API
        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            latency_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # 获取模型等级
            tier = self._get_model_tier(model)

            # 更新成功统计
            success_key = "glm_success" if provider == LLMProvider.GLM else "deepseek_success"
            self.stats[success_key] += 1

            self.logger.info(f"{provider.value} 请求成功: {model}, {latency_ms}ms, {tokens_used} tokens")

            return LLMResponse(
                content=content,
                provider=provider,
                model=model,
                tier=tier,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                success=True
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_key = "glm_errors" if provider == LLMProvider.GLM else "deepseek_errors"
            self.stats[error_key] += 1

            self.logger.error(f"{provider.value} 请求失败: {e}")

            # 自动回退
            if provider == self.primary and self.auto_fallback:
                self.logger.info(f"回退到 {self.fallback.value}")
                self.stats["fallback_count"] += 1
                return self.generate(system_prompt, user_message,
                                    provider=self.fallback,
                                    model="deepseek-chat",  # 回退时使用deepseek-chat
                                    query=query,
                                    max_tokens=max_tokens,
                                    temperature=temperature)

            return LLMResponse(
                content="",
                provider=provider,
                model=model,
                tier=self._get_model_tier(model),
                tokens_used=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )

    def _get_model_tier(self, model: str) -> ModelTier:
        """获取模型等级"""
        for tier, tier_model in self.model_mapping.items():
            if tier_model == model:
                return tier

        # 默认
        if "flash" in model:
            return ModelTier.FLASH
        elif "air" in model:
            return ModelTier.AIR
        elif "plus" in model:
            return ModelTier.PLUS
        else:
            return ModelTier.FULL

    def generate_with_retry(self,
                           system_prompt: str,
                           user_message: str,
                           provider: LLMProvider = None,
                           **kwargs) -> LLMResponse:
        """带重试的生成"""
        last_error = None

        for attempt in range(self.max_retries):
            response = self.generate(system_prompt, user_message,
                                    provider=provider, **kwargs)

            if response.success:
                return response

            last_error = response.error
            self.logger.warning(f"第{attempt + 1}次尝试失败: {last_error}")

            # 指数退避
            wait_time = 2 ** attempt
            time.sleep(wait_time)

        # 所有重试都失败
        return LLMResponse(
            content="",
            provider=provider or self.primary,
            model=kwargs.get('model', 'unknown'),
            tier=ModelTier.FLASH,
            tokens_used=0,
            latency_ms=0,
            success=False,
            error=f"重试{self.max_retries}次后仍失败: {last_error}"
        )

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total_requests = self.stats["glm_requests"] + self.stats["deepseek_requests"]
        total_success = self.stats["glm_success"] + self.stats["deepseek_success"]
        total_errors = self.stats["glm_errors"] + self.stats["deepseek_errors"]

        # 计算成本估算
        estimated_cost = 0.0
        for model, count in self.stats["model_usage"].items():
            if model in GLM_MODELS_CONFIG:
                cost = GLM_MODELS_CONFIG[model]["cost"] * count / 1_000_000
                estimated_cost += cost
            elif model in DEEPSEEK_MODELS_CONFIG:
                cost = DEEPSEEK_MODELS_CONFIG[model]["cost"] * count / 1_000_000
                estimated_cost += cost

        return {
            "total_requests": total_requests,
            "total_success": total_success,
            "total_errors": total_errors,
            "success_rate": total_success / total_requests if total_requests > 0 else 0,
            "fallback_count": self.stats["fallback_count"],
            "estimated_cost_yuan": round(estimated_cost, 4),
            "model_usage": self.stats["model_usage"],
            "glm": {
                "requests": self.stats["glm_requests"],
                "success": self.stats["glm_success"],
                "errors": self.stats["glm_errors"],
                "success_rate": self.stats["glm_success"] / self.stats["glm_requests"] if self.stats["glm_requests"] > 0 else 0
            },
            "deepseek": {
                "requests": self.stats["deepseek_requests"],
                "success": self.stats["deepseek_success"],
                "errors": self.stats["deepseek_errors"],
                "success_rate": self.stats["deepseek_success"] / self.stats["deepseek_requests"] if self.stats["deepseek_requests"] > 0 else 0
            }
        }

    def health_check(self) -> dict[str, bool]:
        """健康检查"""
        return {
            "glm_available": self.glm_client is not None,
            "deepseek_available": self.deepseek_client is not None,
            "primary_available": (self.glm_client is not None) if self.primary == LLMProvider.GLM else (self.deepseek_client is not None),
            "fallback_available": (self.glm_client is not None) if self.fallback == LLMProvider.GLM else (self.deepseek_client is not None)
        }


def main() -> None:
    """测试LLM服务"""

    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv("/Users/xujian/Athena工作平台/.env.production.unified")

    print("=" * 60)
    print("小娜LLM服务 v2.3 测试")
    print("=" * 60)

    # 初始化服务
    glm_key = os.getenv("GLM_API_KEY", "test_key")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "test_key")

    service = XiaonaLLMService(
        glm_api_key=glm_key,
        deepseek_api_key=deepseek_key,
        strategy="balanced"  # 平衡策略
    )

    # 测试智能模型选择
    test_queries = [
        ("专利法第22条第3款是什么？", "general", "flash"),
        ("帮我分析这个技术交底书的创新点", "patent_writing", "air"),
        ("审查员认为不具备创造性，使用D1和D2，如何答复？", "office_action", "plus"),
    ]

    print("\n🧪 测试智能模型选择:\n")

    for query, scenario, expected_tier in test_queries:
        print(f"查询: {query}")
        print(f"场景: {scenario}")

        # 选择模型
        model = service.select_model(query, scenario=scenario)

        print(f"✅ 选择模型: {model}")
        print(f"   预期等级: {expected_tier}")
        print()

    # 健康检查
    health = service.health_check()
    print("🔍 健康检查:")
    print(f"   GLM: {'✅' if health['glm_available'] else '❌'}")
    print(f"   DeepSeek: {'✅' if health['deepseek_available'] else '❌'}")


if __name__ == "__main__":
    main()
