#!/usr/bin/env python3
from __future__ import annotations
"""
审查意见答复人机交互流程
Office Action Human-in-the-Loop Workflow

提供用户友好的交互界面，包括:
1. 解析结果确认
2. 信息修正
3. 逐步引导
4. 进度追踪

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 导入审查意见解析器
try:
    from core.patents.oa_document_parser import (
        OfficeActionParser,
        ParsedOfficeAction,
        RejectionType,
    )
    HAS_PARSER = True
except ImportError:
    HAS_PARSER = False

from core.patents.smart_oa_responder import get_smart_oa_responder

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class InteractionStep(Enum):
    """交互步骤"""

    DOCUMENT_UPLOAD = "document_upload"  # 文档上传
    PARSE_CONFIRM = "parse_confirm"  # 解析确认
    DOCUMENT_COMPLETENESS_CHECK = "document_completeness_check"  # 文档完整性检查
    DOWNLOAD_MISSING = "download_missing"  # 下载缺失文档（可选）
    ANALYSIS_PLAN_CONFIRM = "analysis_plan_confirm"  # 分析计划确认
    STRATEGY_REVIEW = "strategy_review"  # 策略审查
    FINAL_CONFIRM = "final_confirm"  # 最终确认
    GENERATION = "generation"  # 生成答复


class UserResponse(Enum):
    """用户响应"""

    CONFIRM = "confirm"  # 确认
    MODIFY = "modify"  # 修改
    CANCEL = "cancel"  # 取消
    BACK = "back"  # 返回上一步


@dataclass
class InteractionState:
    """交互状态"""

    current_step: InteractionStep
    parsed_oa: ParsedOfficeAction | None = None
    user_modifications: dict[str, Any] = field(default_factory=dict)
    history: list[InteractionStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 新增: 完整性检查相关
    completeness_report: Optional[dict[str, Any]] = None
    download_result: Optional[dict[str, Any]] = None
    analysis_plan: Optional[dict[str, Any]] = None
    analysis_result: Optional[dict[str, Any]] = None  # 步骤2智能分析结果


class HumanInteractionWorkflow:
    """
    人机交互工作流程

    核心功能:
    1. 引导式流程
    2. 友好的用户界面
    3. 灵活的修改机制
    4. 完整的状态追踪
    """

    def __init__(self):
        """初始化交互流程"""
        self.name = "审查意见答复人机交互系统"
        self.version = "v0.1.2"

        # 初始化解析器
        if HAS_PARSER:
            self.parser = OfficeActionParser()
        else:
            self.parser = None
            logger.error("审查意见解析器未找到")

        # 初始化答复系统
        self.responder = get_smart_oa_responder()

        # 初始化新模块
        self._init_new_modules()

        # 当前状态
        self.state = InteractionState(current_step=InteractionStep.DOCUMENT_UPLOAD)

        logger.info(f"🤝 {self.name} ({self.version}) 初始化完成")

    def _init_new_modules(self):
        """初始化新模块"""
        # 文档完整性检查器
        try:
            from core.patents.document_completeness_checker import (
                get_document_completeness_checker,
            )

            self.completeness_checker = get_document_completeness_checker()
            logger.info("✅ 文档完整性检查器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 文档完整性检查器初始化失败: {e}")
            self.completeness_checker = None

        # 专利下载管理器
        try:
            from core.patents.patent_download_manager import get_patent_download_manager

            self.download_manager = get_patent_download_manager()
            logger.info("✅ 专利下载管理器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 专利下载管理器初始化失败: {e}")
            self.download_manager = None

        # 分析计划生成器
        try:
            from core.patents.analysis_plan_generator import get_analysis_plan_generator

            self.plan_generator = get_analysis_plan_generator()
            logger.info("✅ 分析计划生成器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 分析计划生成器初始化失败: {e}")
            self.plan_generator = None

    async def start_workflow(self, document_path: Optional[str] = None) -> dict[str, Any]:
        """
        启动人机交互工作流程

        Args:
            document_path: 审查意见文档路径

        Returns:
            工作流程结果
        """
        logger.info("🚀 启动人机交互工作流程")

        # 步骤1: 文档上传
        if document_path:
            result = await self._step_document_upload(document_path)
            if not result["success"]:
                return result

        # 步骤2: 解析确认
        result = await self._step_parse_confirm()
        if not result["proceed"]:
            return {"cancelled": True, "step": "parse_confirm"}

        # 步骤3: 文档完整性检查
        result = await self._step_document_completeness_check()
        if not result["proceed"]:
            return {"cancelled": True, "step": "document_completeness_check"}

        # 步骤4: 下载缺失文档（如果需要）
        if result.get("need_download"):
            download_result = await self._step_download_missing()
            if not download_result.get("proceed"):
                return {"cancelled": True, "step": "download_missing"}

        # 步骤5: 分析计划确认
        result = await self._step_analysis_plan_confirm()
        if not result["proceed"]:
            return {"cancelled": True, "step": "analysis_plan_confirm"}

        # 步骤6: 智能分析执行（新增）
        result = await self._step_intelligent_analysis()
        if not result.get("proceed"):
            return {"cancelled": True, "step": "intelligent_analysis"}

        # 步骤7: 策略审查
        result = await self._step_strategy_review()
        if not result["proceed"]:
            return {"cancelled": True, "step": "strategy_review"}

        # 步骤8: 最终确认
        result = await self._step_final_confirm()
        if not result["proceed"]:
            return {"cancelled": True, "step": "final_confirm"}

        # 步骤9: 生成答复
        result = await self._step_generation()

        logger.info("✅ 人机交互工作流程完成")
        return result

    async def _step_document_upload(self, document_path: str) -> dict[str, Any]:
        """步骤1: 文档上传和解析"""
        logger.info("📄 步骤1: 文档上传和解析")

        if not self.parser:
            return {"success": False, "error": "解析器未初始化"}

        try:
            # 解析文档
            parsed_oa = self.parser.parse_document(document_path)

            # 保存解析结果
            self.state.parsed_oa = parsed_oa
            self.state.current_step = InteractionStep.PARSE_CONFIRM

            logger.info(f"✅ 文档解析完成 (置信度: {parsed_oa.confidence:.1%})")

            return {"success": True, "parsed_oa": parsed_oa}

        except Exception as e:
            logger.error(f"❌ 文档解析失败: {e}")
            return {"success": False, "error": str(e)}

    async def _step_parse_confirm(self) -> dict[str, Any]:
        """步骤2: 解析结果确认"""
        logger.info("👀 步骤2: 解析结果确认")

        if not self.state.parsed_oa:
            return {"proceed": False, "error": "无解析结果"}

        # 生成确认消息
        confirm_message = self._generate_parse_confirm_message()

        # 这里应该通过UI显示给用户，等待用户响应
        # 为演示目的，我们返回确认消息和指导
        return {
            "proceed": True,  # 在实际应用中，这里会等待用户确认
            "step": "parse_confirm",
            "confirm_message": confirm_message,
            "parsed_data": self.state.parsed_oa.to_dict(),
            "guidance": {
                "action": "请审查以上解析结果",
                "options": [
                    "输入 '确认' 或 'confirm' 继续",
                    "输入 '修改' 或 'modify' 进入修正模式",
                    "输入 '取消' 或 'cancel' 取消流程",
                ],
            },
        }

    async def _step_document_completeness_check(self) -> dict[str, Any]:
        """步骤3: 文档完整性检查"""
        logger.info("🔍 步骤3: 文档完整性检查")

        if not self.completeness_checker:
            logger.warning("⚠️ 文档完整性检查器未初始化，跳过检查")
            return {"proceed": True, "need_download": False}

        if not self.state.parsed_oa:
            return {"proceed": False, "error": "无审查意见数据"}

        try:
            # 准备对比文件列表
            prior_art_references = []
            if hasattr(self.state.parsed_oa, "prior_art_details"):
                for detail in self.state.parsed_oa.prior_art_details:
                    prior_art_references.append(detail)
            elif self.state.parsed_oa.prior_art_references:
                for ref in self.state.parsed_oa.prior_art_references:
                    prior_art_references.append({"publication_number": ref})

            # 执行完整性检查
            report = self.completeness_checker.check_completeness(
                target_application_number=self.state.parsed_oa.target_application_number or "",
                prior_art_references=prior_art_references,
            )

            # 保存报告
            self.state.completeness_report = report.__dict__

            self.state.current_step = InteractionStep.DOCUMENT_COMPLETENESS_CHECK

            # 生成完整性检查消息
            completeness_message = report.to_markdown()

            return {
                "proceed": True,
                "need_download": not report.is_complete,
                "step": "document_completeness_check",
                "completeness_report": self.state.completeness_report,
                "completeness_message": completeness_message,
                "is_complete": report.is_complete,
                "guidance": {
                    "action": "请检查文档完整性",
                    "options": (
                        [
                            "输入 '确认' 或 'confirm' 继续分析",
                            "输入 '下载' 自动下载缺失文档",
                            "输入 '跳过' 使用现有文档继续",
                            "输入 '取消' 中止流程",
                        ]
                        if not report.is_complete
                        else [
                            "输入 '确认' 或 'confirm' 继续分析",
                            "输入 '取消' 中止流程",
                        ]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"❌ 文档完整性检查失败: {e}")
            return {"proceed": False, "error": str(e)}

    async def _step_download_missing(self) -> dict[str, Any]:
        """步骤4: 下载缺失文档（可选）"""
        logger.info("📥 步骤4: 下载缺失文档")

        if not self.download_manager:
            logger.warning("⚠️ 下载管理器未初始化")
            return {"proceed": True, "downloaded": False}

        if not self.state.completeness_report:
            return {"proceed": True, "downloaded": False}

        try:
            # 获取下载建议
            recommendations = self.state.completeness_report.get(
                "download_recommendations", []
            )

            if not recommendations:
                return {"proceed": True, "downloaded": False}

            # 执行下载
            download_result = self.download_manager.check_and_download_missing(
                recommendations
            )

            # 保存下载结果
            self.state.download_result = download_result.__dict__

            self.state.current_step = InteractionStep.DOWNLOAD_MISSING

            # 生成下载报告消息
            download_message = download_result.to_markdown()

            return {
                "proceed": True,
                "step": "download_missing",
                "download_result": self.state.download_result,
                "download_message": download_message,
                "downloaded": True,
                "guidance": {
                    "action": "下载完成，请查看结果",
                    "options": [
                        "输入 '确认' 或 'confirm' 继续分析",
                        "输入 '重新检查' 再次检查完整性",
                        "输入 '跳过' 使用现有文档继续",
                        "输入 '取消' 中止流程",
                    ],
                },
            }

        except Exception as e:
            logger.error(f"❌ 下载失败: {e}")
            return {"proceed": False, "error": str(e)}

    async def _step_analysis_plan_confirm(self) -> dict[str, Any]:
        """步骤5: 分析计划确认"""
        logger.info("🎯 步骤5: 分析计划确认")

        if not self.plan_generator:
            logger.warning("⚠️ 分析计划生成器未初始化")
            return {"proceed": True, "analysis_plan": None}

        if not self.state.parsed_oa:
            return {"proceed": False, "error": "无审查意见数据"}

        try:
            # 生成分析计划
            plan = self.plan_generator.generate_plan(
                target_application_number=self.state.parsed_oa.target_application_number
                or "",
                target_patent_title=self.state.parsed_oa.target_patent_title or "",
                examination_opinions=[],
                prior_art_count=len(self.state.parsed_oa.prior_art_references),
            )

            # 保存计划
            self.state.analysis_plan = plan.__dict__

            self.state.current_step = InteractionStep.ANALYSIS_PLAN_CONFIRM

            # 生成分析计划消息
            plan_message = plan.to_markdown()

            return {
                "proceed": True,
                "step": "analysis_plan_confirm",
                "analysis_plan": self.state.analysis_plan,
                "plan_message": plan_message,
                "guidance": {
                    "action": "请审查分析计划",
                    "options": [
                        "输入 '确认' 或 'confirm' 开始智能分析",
                        "输入 '修改' 调整分析计划",
                        "输入 '取消' 中止流程",
                    ],
                },
            }

        except Exception as e:
            logger.error(f"❌ 分析计划生成失败: {e}")
            return {"proceed": False, "error": str(e)}

    async def _step_intelligent_analysis(self) -> dict[str, Any]:
        """步骤6: 智能分析执行"""
        logger.info("🔬 步骤6: 智能分析执行")

        # 初始化步骤2执行器
        try:
            from core.patents.step2_analysis_executor import (
                AnalysisExecutionResult,
                get_step2_executor,
            )
        except ImportError:
            logger.warning("⚠️ 步骤2执行器未找到，跳过智能分析")
            return {"proceed": True, "executed": False}

        if not self.state.parsed_oa:
            return {"proceed": False, "error": "无审查意见数据"}

        try:
            executor = get_step2_executor()

            # 准备对比文件信息
            prior_art_refs = []
            if hasattr(self.state.parsed_oa, "prior_art_details"):
                prior_art_refs = self.state.parsed_oa.prior_art_details
            elif self.state.parsed_oa.prior_art_references:
                for ref in self.state.parsed_oa.prior_art_references:
                    prior_art_refs.append({"publication_number": ref})

            # 准备目标专利信息
            target_info = {
                "application_number": self.state.parsed_oa.target_application_number
                or "",
                "title": self.state.parsed_oa.target_patent_title or "",
            }

            # 执行完整分析
            analysis_result = await executor.execute_full_analysis(
                target_patent_info=target_info,
                prior_art_references=prior_art_refs,
                examination_opinions=[],
            )

            self.state.current_step = InteractionStep.STRATEGY_REVIEW

            # 保存分析结果到state
            self.state.analysis_result = analysis_result.__dict__

            # 生成执行报告
            execution_report = analysis_result.to_markdown()

            return {
                "proceed": True,
                "executed": True,
                "step": "intelligent_analysis",
                "analysis_result": analysis_result.__dict__,
                "execution_report": execution_report,
                "json_report": analysis_result.json_report_path,
                "markdown_report": analysis_result.markdown_report_path,
                "guidance": {
                    "action": "智能分析已完成",
                    "options": [
                        "查看详细分析报告",
                        "继续策略审查",
                        "重新执行分析",
                    ],
                },
            }

        except Exception as e:
            logger.error(f"❌ 智能分析执行失败: {e}")
            return {"proceed": False, "error": str(e)}

    async def _step_info_correct(self) -> dict[str, Any]:
        """步骤7: 信息修正（可选，保留用于兼容性）"""
        logger.info("✏️ 步骤7: 信息修正（可选）")

        # 如果有用户修改，应用修改
        if self.state.user_modifications:
            self._apply_user_modifications()

        # 显示最终确认的消息
        final_message = self._generate_final_check_message()

        self.state.current_step = InteractionStep.STRATEGY_REVIEW

        return {
            "proceed": True,
            "step": "info_correct",
            "final_check_message": final_message,
            "guidance": {
                "action": "请确认修正后的信息",
                "options": [
                    "输入 '确认' 或 'confirm' 继续生成策略",
                    "输入 '返回' 或 'back' 重新修改",
                ],
            },
        }

    async def _step_strategy_review(self) -> dict[str, Any]:
        """步骤4: 策略审查"""
        logger.info("🎯 步骤4: 策略审查")

        if not self.state.parsed_oa:
            return {"proceed": False, "error": "无审查意见数据"}

        try:
            # 生成答复方案
            response_plan = await self.responder.create_response_plan(
                office_action=self.state.parsed_oa.to_dict()
            )

            # 生成策略审查消息
            strategy_message = self._generate_strategy_review_message(response_plan)

            self.state.current_step = InteractionStep.FINAL_CONFIRM

            return {
                "proceed": True,
                "step": "strategy_review",
                "response_plan": response_plan,
                "strategy_message": strategy_message,
                "guidance": {
                    "action": "请审查推荐的答复策略",
                    "options": [
                        "输入 '确认' 或 'confirm' 接受策略",
                        "输入 '修改' 或 'modify' 调整策略",
                        "输入 '返回' 或 'back' 返回上一步",
                    ],
                },
            }

        except Exception as e:
            logger.error(f"❌ 策略生成失败: {e}")
            return {"proceed": False, "error": str(e)}

    async def _step_final_confirm(self) -> dict[str, Any]:
        """步骤5: 最终确认"""
        logger.info("✅ 步骤5: 最终确认")

        final_summary = self._generate_final_summary()

        self.state.current_step = InteractionStep.GENERATION

        return {
            "proceed": True,
            "step": "final_confirm",
            "final_summary": final_summary,
            "guidance": {
                "action": "最终确认",
                "options": [
                    "输入 '确认' 或 'confirm' 开始生成答复",
                    "输入 '取消' 或 'cancel' 放弃",
                ],
            },
        }

    async def _step_generation(self) -> dict[str, Any]:
        """步骤6: 生成答复"""
        logger.info("📝 步骤6: 生成答复")

        try:
            # 这里可以扩展为生成完整的答复文档
            # 目前返回关键信息

            result = {
                "success": True,
                "step": "generation",
                "oa_data": self.state.parsed_oa.to_dict() if self.state.parsed_oa else {},
                "modifications": self.state.user_modifications,
                "generated_at": datetime.now().isoformat(),
                "message": "答复方案已生成，可以开始撰写答复文档",
            }

            logger.info("✅ 答复生成完成")
            return result

        except Exception as e:
            logger.error(f"❌ 答复生成失败: {e}")
            return {"success": False, "error": str(e)}

    def apply_user_modification(self, field: str, value: Any) -> None:
        """
        应用用户修改

        Args:
            field: 字段名称
            value: 新值
        """
        if not self.state.parsed_oa:
            logger.warning("无解析结果，无法应用修改")
            return

        # 记录修改
        self.state.user_modifications[field] = value

        # 应用修改
        if hasattr(self.state.parsed_oa, field):
            setattr(self.state.parsed_oa, field, value)
            logger.info(f"✅ 已应用修改: {field} = {value}")

    def _apply_user_modifications(self) -> None:
        """应用所有用户修改"""
        if not self.state.parsed_oa:
            return

        for field_name, value in self.state.user_modifications.items():
            if hasattr(self.state.parsed_oa, field_name):
                setattr(self.state.parsed_oa, field_name, value)

        logger.info(f"✅ 已应用 {len(self.state.user_modifications)} 个修改")

    def _generate_parse_confirm_message(self) -> str:
        """生成解析确认消息"""
        if not self.state.parsed_oa:
            return "无解析结果"

        return self.state.parsed_oa.to_markdown()

    def _generate_final_check_message(self) -> str:
        """生成最终检查消息"""
        md = []
        md.append("# ✅ 审查意见信息最终确认\n")
        md.append("---\n")

        if self.state.parsed_oa:
            md.append("## 📋 关键信息")
            md.append(f"- **驳回类型**: {self.state.parsed_oa.rejection_type or '未识别'}")
            md.append(f"- **对比文件**: {', '.join(self.state.parsed_oa.prior_art_references) or '无'}")
            md.append(f"- **权利要求**: {', '.join(map(str, self.state.parsed_oa.cited_claims)) or '无'}")
            md.append(f"- **答复期限**: {self.state.parsed_oa.response_deadline or '未提取'}\n")

        if self.state.user_modifications:
            md.append("## ✏️ 已应用的修改")
            for field, value in self.state.user_modifications.items():
                md.append(f"- {field}: {value}")
            md.append("")

        return "\n".join(md)

    def _generate_strategy_review_message(self, response_plan) -> str:
        """生成策略审查消息"""
        md = []
        md.append("# 🎯 推荐答复策略\n")
        md.append("---\n")

        if response_plan:
            md.append(f"## 策略: {response_plan.recommended_strategy.value}")
            md.append(f"**成功概率**: {response_plan.success_probability:.1%}")
            md.append(f"**置信度**: {response_plan.confidence:.1%}\n")

            md.append("### 策略理由")
            md.append(f"{response_plan.strategy_rationale}\n")

            if response_plan.arguments:
                md.append("### 争辩论点")
                for i, arg in enumerate(response_plan.arguments, 1):
                    md.append(f"{i}. {arg}")
                md.append("")

            if response_plan.claim_modifications:
                md.append("### 修改建议")
                for i, mod in enumerate(response_plan.claim_modifications, 1):
                    md.append(f"{i}. {mod}")
                md.append("")

        return "\n".join(md)

    def _generate_final_summary(self) -> str:
        """生成最终摘要"""
        md = []
        md.append("# 📊 最终确认摘要\n")
        md.append("---\n")

        md.append("## 审查意见信息")
        if self.state.parsed_oa:
            oa = self.state.parsed_oa
            md.append(f"- 驳回类型: {oa.rejection_type or '未识别'}")
            md.append(f"- 对比文件: {len(oa.prior_art_references)} 个")
            md.append(f"- 权利要求: {len(oa.cited_claims)} 个")
            md.append(f"- 审查员论点: {len(oa.examiner_arguments)} 条\n")

        md.append("## 用户修改")
        if self.state.user_modifications:
            md.append(f"- 应用了 {len(self.state.user_modifications)} 个修改")
        else:
            md.append("- 无修改")
        md.append("")

        md.append("## 下一步")
        md.append("确认后将开始生成完整的答复文档。")
        md.append("")

        return "\n".join(md)

    def get_workflow_state(self) -> dict[str, Any]:
        """获取当前工作流状态"""
        return {
            "current_step": self.state.current_step.value,
            "parsed_oa": self.state.parsed_oa.to_dict() if self.state.parsed_oa else None,
            "user_modifications": self.state.user_modifications,
            "history": [step.value for step in self.state.history],
        }


# 全局单例
_oa_interaction_instance = None


def get_oa_interaction() -> HumanInteractionWorkflow:
    """获取人机交互工作流单例"""
    global _oa_interaction_instance
    if _oa_interaction_instance is None:
        _oa_interaction_instance = HumanInteractionWorkflow()
    return _oa_interaction_instance


# 测试代码
async def main():
    """测试人机交互工作流程"""

    print("\n" + "=" * 60)
    print("🤝 审查意见答复人机交互流程测试")
    print("=" * 60 + "\n")

    workflow = get_oa_interaction()

    # 测试: 模拟完整流程
    print("📝 测试: 完整工作流程")

    # 步骤1: 文档上传（使用测试数据）
    test_oa = ParsedOfficeAction(
        oa_id="OA_20240115001",
        document_source="test_oa.txt",
        rejection_type="novelty",
        rejection_reason="对比文件D1公开了权利要求1的全部技术特征",
        prior_art_references=["CN112345678A", "US2023001234A1"],
        cited_claims=[1, 2, 3],
        examiner_arguments=[
            "D1公开了基于卷积神经网络的图像识别方法",
            "D1也使用了注意力机制",
        ],
        missing_features=["特殊的损失函数", "特征金字塔的具体结构"],
        received_date="2024-01-15",
        response_deadline="2024-04-15",
        raw_text="测试文本...",
        confidence=0.85,
    )

    workflow.state.parsed_oa = test_oa

    # 步骤2: 解析确认
    result = await workflow._step_parse_confirm()
    print("📋 解析确认消息:")
    print(result.get("confirm_message", "")[:500])
    print("...\n")

    # 步骤3: 应用修改
    workflow.apply_user_modification("rejection_type", "inventiveness")
    print("✅ 已应用修改: rejection_type = inventiveness\n")

    # 步骤4: 策略审查
    result = await workflow._step_strategy_review()
    print("🎯 策略审查消息:")
    print(result.get("strategy_message", "")[:500])
    print("...\n")

    # 步骤5: 最终确认
    result = await workflow._step_final_confirm()
    print("📊 最终摘要:")
    print(result.get("final_summary", ""))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
