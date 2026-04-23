#!/usr/bin/env python3
from __future__ import annotations
"""
审查意见答复集成服务
Office Action Response Integration Service

整合所有模块，提供统一的接口:
- 文档解析
- 人机交互
- 智能答复
- 结果生成

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 导入各模块
try:
    from core.patents.oa_document_parser import OfficeActionParser, ParsedOfficeAction
    from core.patents.oa_human_interaction import (
        HumanInteractionWorkflow,
        InteractionStep,
        get_oa_interaction,
    )
    from core.patents.smart_oa_responder import (
        ResponsePlan,
        SmartOfficeActionResponder,
        get_smart_oa_responder,
    )
    HAS_ALL_MODULES = True
except ImportError as e:
    HAS_ALL_MODULES = False
    logger = logging.getLogger(__name__)
    logger.error(f"模块导入失败: {e}")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class OAProcessingResult:
    """审查意见处理结果"""

    success: bool
    oa_id: str
    stage: str  # 当前阶段

    # 各阶段数据
    parsed_data: Optional[dict[str, Any]] = None
    user_modifications: dict[str, Any] = field(default_factory=dict)
    response_plan: Optional[dict[str, Any]] = None

    # 元数据
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    error: str = ""

    # 统计
    parsing_confidence: float = 0.0
    user_interactions: int = 0


class OAIntegrationService:
    """
    审查意见答复集成服务

    核心功能:
    1. 一站式处理接口
    2. 模块间协调
    3. 状态管理
    4. 结果导出
    """

    def __init__(self):
        """初始化集成服务"""
        self.name = "审查意见答复集成服务"
        self.version = "v0.1.2"

        if not HAS_ALL_MODULES:
            raise RuntimeError("必需的模块未全部导入")

        # 初始化各模块
        self.parser = OfficeActionParser()
        self.interaction = get_oa_interaction()
        self.responder = get_smart_oa_responder()

        # 处理历史
        self.history: list[OAProcessingResult] = []

        logger.info(f"🔗 {self.name} ({self.version}) 初始化完成")

    async def process_with_interaction(
        self, document_path: str, enable_interaction: bool = True
    ) -> OAProcessingResult:
        """
        带人机交互的完整处理流程

        Args:
            document_path: 审查意见文档路径
            enable_interaction: 是否启用人机交互

        Returns:
            处理结果
        """
        logger.info(f"🚀 开始处理审查意见: {document_path}")

        result = OAProcessingResult(
            success=False, oa_id="", stage="init", started_at=datetime.now().isoformat()
        )

        try:
            # 阶段1: 文档解析
            logger.info("📄 阶段1: 文档解析")
            parsed_oa = self.parser.parse_document(document_path)
            result.oa_id = parsed_oa.oa_id
            result.parsed_data = parsed_oa.to_dict()
            result.parsing_confidence = parsed_oa.confidence
            result.stage = "parsed"

            # 阶段2: 人机交互确认
            if enable_interaction:
                logger.info("🤝 阶段2: 人机交互确认")
                self.interaction.state.parsed_oa = parsed_oa

                # 生成确认消息（实际应用中会等待用户确认）
                await self.interaction._step_parse_confirm()

                # 应用用户修改（如果有）
                if self.interaction.state.user_modifications:
                    parsed_oa = self._apply_modifications(
                        parsed_oa, self.interaction.state.user_modifications
                    )
                    result.user_modifications = self.interaction.state.user_modifications
                    result.user_interactions = len(self.interaction.state.user_modifications)

            # 阶段3: 生成答复方案
            logger.info("🎯 阶段3: 生成答复方案")
            response_plan = await self.responder.create_response_plan(
                office_action=parsed_oa.to_dict()
            )
            result.response_plan = {
                "plan_id": response_plan.plan_id,
                "recommended_strategy": response_plan.recommended_strategy.value,
                "strategy_rationale": response_plan.strategy_rationale,
                "arguments": response_plan.arguments,
                "claim_modifications": response_plan.claim_modifications,
                "success_probability": response_plan.success_probability,
                "confidence": response_plan.confidence,
            }
            result.stage = "completed"
            result.success = True

            logger.info(f"✅ 处理完成: {result.oa_id}")

        except Exception as e:
            logger.error(f"❌ 处理失败: {e}")
            result.success = False
            result.error = str(e)
            result.stage = "failed"

        finally:
            result.completed_at = datetime.now().isoformat()
            self.history.append(result)

        return result

    async def process_auto(self, document_path: str) -> OAProcessingResult:
        """
        自动处理模式（无人机交互）

        Args:
            document_path: 审查意见文档路径

        Returns:
            处理结果
        """
        return await self.process_with_interaction(document_path, enable_interaction=False)

    def _apply_modifications(self, parsed_oa: ParsedOfficeAction, modifications: dict[str, Any]) -> ParsedOfficeAction:
        """应用用户修改"""
        for field_name, value in modifications.items():
            if hasattr(parsed_oa, field_name):
                setattr(parsed_oa, field_name, value)
        return parsed_oa

    def export_result(self, result: OAProcessingResult, format: str = "json") -> str:
        """
        导出处理结果

        Args:
            result: 处理结果
            format: 导出格式 (json/markdown)

        Returns:
            导出的内容
        """
        if format == "json":
            return self._export_json(result)
        elif format == "markdown":
            return self._export_markdown(result)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def _export_json(self, result: OAProcessingResult) -> str:
        """导出JSON格式"""
        import json

        return json.dumps(
            {
                "oa_id": result.oa_id,
                "success": result.success,
                "stage": result.stage,
                "parsed_data": result.parsed_data,
                "user_modifications": result.user_modifications,
                "response_plan": result.response_plan,
                "parsing_confidence": result.parsing_confidence,
                "user_interactions": result.user_interactions,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "error": result.error,
            },
            ensure_ascii=False,
            indent=2,
        )

    def _export_markdown(self, result: OAProcessingResult) -> str:
        """导出Markdown格式"""
        md = []
        md.append("# 📋 审查意见处理报告\n")
        md.append(f"**ID**: {result.oa_id}")
        md.append(f"**状态**: {'✅ 成功' if result.success else '❌ 失败'}")
        md.append(f"**阶段**: {result.stage}")
        md.append(f"**处理时间**: {result.started_at} ~ {result.completed_at}\n")

        if result.parsed_data:
            md.append("## 📄 解析结果")
            md.append(f"- **驳回类型**: {result.parsed_data.get('rejection_type', 'N/A')}")
            md.append(f"- **置信度**: {result.parsing_confidence:.1%}")
            md.append(f"- **对比文件**: {len(result.parsed_data.get('prior_art_references', []))} 个")
            md.append(f"- **权利要求**: {len(result.parsed_data.get('cited_claims', []))} 个\n")

        if result.user_modifications:
            md.append("## ✏️ 用户修改")
            for field, value in result.user_modifications.items():
                md.append(f"- {field}: {value}")
            md.append("")

        if result.response_plan:
            md.append("## 🎯 答复方案")
            md.append(f"- **策略**: {result.response_plan.get('recommended_strategy', 'N/A')}")
            md.append(f"- **成功概率**: {result.response_plan.get('success_probability', 0):.1%}")
            md.append(f"- **置信度**: {result.response_plan.get('confidence', 0):.1%}\n")

        if result.error:
            md.append(f"## ❌ 错误信息\n{result.error}\n")

        return "\n".join(md)

    def get_statistics(self) -> dict[str, Any]:
        """获取处理统计"""
        total = len(self.history)
        if total == 0:
            return {"message": "暂无处理记录"}

        success_count = sum(1 for r in self.history if r.success)
        avg_confidence = sum(r.parsing_confidence for r in self.history) / total
        total_interactions = sum(r.user_interactions for r in self.history)

        return {
            "total_processed": total,
            "success_count": success_count,
            "success_rate": success_count / total,
            "avg_parsing_confidence": avg_confidence,
            "total_user_interactions": total_interactions,
            "avg_interactions_per_case": total_interactions / total if total > 0 else 0,
        }


# 全局单例
_oa_integration_instance = None


def get_oa_integration_service() -> OAIntegrationService:
    """获取集成服务单例"""
    global _oa_integration_instance
    if _oa_integration_instance is None:
        _oa_integration_instance = OAIntegrationService()
    return _oa_integration_instance


# 测试代码
async def main():
    """测试集成服务"""

    print("\n" + "=" * 60)
    print("🔗 审查意见答复集成服务测试")
    print("=" * 60 + "\n")

    try:
        service = get_oa_integration_service()

        # 测试: 自动处理模式
        print("📝 测试: 自动处理模式")

        # 使用测试数据（模拟文档）
        test_content = """
        审查意见通知书

        申请号: 202310000001.X
        收到日期: 2024-01-15
        答复期限: 2024-04-15

        驳回理由:
        权利要求1不具备新颖性。对比文件D1(CN112345678A)公开了权利要求1的全部技术特征。

        审查员认为:
        1. D1公开了基于卷积神经网络的图像识别方法
        2. D1也使用了注意力机制

        对比文件:
        - D1: CN112345678A
        - D2: US2023001234A1

        结论: 权利要求1-3不具备新颖性。
        """

        # 创建临时测试文件
        test_file = Path("/tmp/test_oa.txt")
        test_file.write_text(test_content, encoding="utf-8")

        # 处理
        result = await service.process_auto(str(test_file))

        # 输出结果
        print("📊 处理结果:")
        print(service.export_result(result, format="json"))

        print("\n📄 Markdown报告:")
        print(service.export_result(result, format="markdown"))

        # 统计
        stats = service.get_statistics()
        print("\n📈 统计信息:")
        print(f"总处理数: {stats['total_processed']}")
        print(f"成功率: {stats['success_rate']:.1%}")
        print(f"平均置信度: {stats['avg_parsing_confidence']:.1%}")

        # 清理
        test_file.unlink()

        print("\n✅ 测试完成!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("提示: 请确保所有依赖模块都已正确安装")


# 入口点: @async_main装饰器已添加到main函数
