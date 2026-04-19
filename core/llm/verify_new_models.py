#!/usr/bin/env python3
from __future__ import annotations
"""
LLM模型验证脚本（国内模型版）
验证所有国内模型适配器是否正确集成

作者: Claude Code
日期: 2026-01-27
版本: v2.0.0（仅国内模型）
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm.model_registry import get_model_registry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ModelIntegrationVerifier:
    """模型集成验证器"""

    def __init__(self):
        self.registry = get_model_registry()
        self.results = {
            "total_models": 0,
            "available_models": 0,
            "unavailable_models": 0,
            "model_details": [],
        }

    async def verify_all(self):
        """验证所有模型"""
        logger.info("=" * 80)
        logger.info("🔍 开始LLM模型验证（国内模型版）")
        logger.info("=" * 80)

        # 1. 验证模型注册表
        await self._verify_registry()

        # 2. 验证智谱AI模型
        await self._verify_zhipuai_models()

        # 3. 验证DeepSeek模型
        await self._verify_deepseek_models()

        # 4. 验证通义千问模型
        await self._verify_qwen_models()

        # 5. 验证本地模型
        await self._verify_local_models()

        # 生成报告
        self._generate_report()

    async def _verify_registry(self):
        """验证模型注册表"""
        logger.info("\n[1] 验证模型注册表...")
        logger.info("-" * 80)

        all_models = self.registry.list_all_models()
        self.results["total_models"] = len(all_models)

        # 按类型分组
        by_type = {}
        for model_id in all_models:
            cap = self.registry.get_capability(model_id)
            if cap:
                type_name = cap.model_type.value
                by_type[type_name] = by_type.get(type_name, 0) + 1

        logger.info(f"✅ 注册表中共有 {len(all_models)} 个模型:")
        for model_type, count in sorted(by_type.items()):
            logger.info(f"   - {model_type}: {count}个")

        # 检查国内模型
        domestic_models = [
            "glm-4-plus",
            "glm-4-flash",
            "deepseek-chat",
            "deepseek-reasoner",
            "deepseek-coder-v2",
            "qwen-vl-max",
            "qwen-vl-plus",
            "qwen2.5-7b-instruct-gguf",
            "starcoder2-15b",
        ]

        logger.info("\n✅ 国内模型检查:")
        for model_id in domestic_models:
            cap = self.registry.get_capability(model_id)
            if cap:
                logger.info(f"   ✅ {model_id}: {cap.model_type.value}")
            else:
                logger.warning(f"   ⚠️ {model_id}: 未注册")

    async def _verify_zhipuai_models(self):
        """验证智谱AI模型"""
        logger.info("\n[2] 验证智谱AI模型...")
        logger.info("-" * 80)

        zhipuai_models = ["glm-4-plus", "glm-4-flash"]

        for model_id in zhipuai_models:
            try:
                cap = self.registry.get_capability(model_id)
                if not cap:
                    logger.warning(f"   ⚠️ {model_id}: 未在注册表中找到")
                    self.results["unavailable_models"] += 1
                    continue

                logger.info(f"   ✅ {model_id}: 已注册")
                logger.info(f"      类型: {cap.model_type.value}")
                logger.info(f"      质量评分: {cap.quality_score}")
                logger.info(f"      成本: ¥{cap.cost_per_1k_tokens}/1K tokens")
                logger.info(f"      最大上下文: {cap.max_context} tokens")

                self.results["available_models"] += 1
                self.results["model_details"].append({
                    "model_id": model_id,
                    "provider": "zhipuai",
                    "type": cap.model_type.value,
                    "status": "registered",
                    "quality": cap.quality_score,
                    "cost": cap.cost_per_1k_tokens,
                })

            except Exception as e:
                logger.error(f"   ❌ {model_id}: {e}")
                self.results["unavailable_models"] += 1

    async def _verify_deepseek_models(self):
        """验证DeepSeek模型"""
        logger.info("\n[3] 验证DeepSeek模型...")
        logger.info("-" * 80)

        deepseek_models = ["deepseek-chat", "deepseek-reasoner", "deepseek-coder-v2"]

        for model_id in deepseek_models:
            try:
                cap = self.registry.get_capability(model_id)
                if not cap:
                    logger.warning(f"   ⚠️ {model_id}: 未在注册表中找到")
                    self.results["unavailable_models"] += 1
                    continue

                logger.info(f"   ✅ {model_id}: 已注册")
                logger.info(f"      类型: {cap.model_type.value}")
                logger.info(f"      质量评分: {cap.quality_score}")
                logger.info(f"      成本: ¥{cap.cost_per_1k_tokens}/1K tokens")

                self.results["available_models"] += 1
                self.results["model_details"].append({
                    "model_id": model_id,
                    "provider": "deepseek",
                    "type": cap.model_type.value,
                    "status": "registered",
                    "quality": cap.quality_score,
                    "cost": cap.cost_per_1k_tokens,
                })

            except Exception as e:
                logger.error(f"   ❌ {model_id}: {e}")
                self.results["unavailable_models"] += 1

    async def _verify_qwen_models(self):
        """验证通义千问模型"""
        logger.info("\n[4] 验证通义千问模型...")
        logger.info("-" * 80)

        qwen_models = ["qwen-vl-max", "qwen-vl-plus", "qwen2.5-7b-instruct-gguf"]

        for model_id in qwen_models:
            try:
                cap = self.registry.get_capability(model_id)
                if not cap:
                    logger.warning(f"   ⚠️ {model_id}: 未在注册表中找到")
                    self.results["unavailable_models"] += 1
                    continue

                logger.info(f"   ✅ {model_id}: 已注册")
                logger.info(f"      类型: {cap.model_type.value}")
                logger.info(f"      部署方式: {cap.deployment.value}")
                logger.info(f"      质量评分: {cap.quality_score}")

                self.results["available_models"] += 1
                self.results["model_details"].append({
                    "model_id": model_id,
                    "provider": "qwen",
                    "type": cap.model_type.value,
                    "status": "registered",
                    "quality": cap.quality_score,
                    "deployment": cap.deployment.value,
                })

            except Exception as e:
                logger.error(f"   ❌ {model_id}: {e}")
                self.results["unavailable_models"] += 1

    async def _verify_local_models(self):
        """验证本地模型"""
        logger.info("\n[5] 验证本地模型...")
        logger.info("-" * 80)

        local_models = ["starcoder2-15b"]

        for model_id in local_models:
            try:
                cap = self.registry.get_capability(model_id)
                if not cap:
                    logger.warning(f"   ⚠️ {model_id}: 未在注册表中找到")
                    self.results["unavailable_models"] += 1
                    continue

                logger.info(f"   ✅ {model_id}: 已注册")
                logger.info(f"      类型: {cap.model_type.value}")
                logger.info(f"      部署方式: {cap.deployment.value}")
                logger.info(f"      模型路径: {cap.model_path if hasattr(cap, 'model_path') else 'N/A'}")

                self.results["available_models"] += 1
                self.results["model_details"].append({
                    "model_id": model_id,
                    "provider": "local",
                    "type": cap.model_type.value,
                    "status": "registered",
                    "deployment": cap.deployment.value,
                })

            except Exception as e:
                logger.error(f"   ❌ {model_id}: {e}")
                self.results["unavailable_models"] += 1

    def _generate_report(self):
        """生成验证报告"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 验证报告")
        logger.info("=" * 80)

        logger.info(f"\n总模型数: {self.results['total_models']}")
        logger.info(f"已注册模型: {self.results['available_models']}")
        logger.info(f"未注册模型: {self.results['unavailable_models']}")

        if self.results['total_models'] > 0:
            availability_rate = (self.results['available_models'] / self.results['total_models']) * 100
            logger.info(f"注册率: {availability_rate:.1f}%")

        # 按提供商统计
        by_provider = {}
        for detail in self.results["model_details"]:
            provider = detail["provider"]
            if provider not in by_provider:
                by_provider[provider] = {"available": 0, "models": []}
            by_provider[provider]["available"] += 1
            by_provider[provider]["models"].append(detail["model_id"])

        logger.info("\n按提供商统计:")
        for provider, data in sorted(by_provider.items()):
            logger.info(f"  - {provider}: {data['available']}个模型 {data['models']}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ 验证完成")
        logger.info("=" * 80)

        # 保存报告到JSON文件
        report_file = Path(__file__).parent.parent.parent / "docs" / "03-reports" / "2026-01" / "LLM_MODELS_VERIFICATION_REPORT.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_models": self.results["total_models"],
                    "available_models": self.results["available_models"],
                    "unavailable_models": self.results["unavailable_models"],
                },
                "by_provider": by_provider,
                "model_details": self.results["model_details"],
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 详细报告已保存到: {report_file}")


async def main():
    """主函数"""
    verifier = ModelIntegrationVerifier()
    await verifier.verify_all()


if __name__ == "__main__":
    asyncio.run(main())
