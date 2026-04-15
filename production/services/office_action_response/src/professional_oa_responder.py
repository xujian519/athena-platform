#!/usr/bin/env python3
"""
专业意见答复服务
Professional Office Action Responder Service

使用国内LLM直接生成专业意见答复

作者: Athena平台团队
版本: v1.0.0
创建时间: 2026-01-27
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ProfessionalOAResponder:
    """
    专业意见答复器

    使用LLM直接生成对审查意见的答复
    """

    def __init__(self):
        """初始化答复器"""
        self.llm_manager = None
        self._initialized = False

    async def initialize(self):
        """初始化LLM管理器"""
        if self._initialized:
            return

        try:
            from core.llm.unified_llm_manager import get_unified_llm_manager

            self.llm_manager = await get_unified_llm_manager()
            await self.llm_manager.initialize(enable_cache_warmup=False, warmup_cache=False)
            self._initialized = True
            logger.info("✅ 专业意见答复服务初始化完成")
        except Exception as e:
            logger.error(f"❌ 专业意见答复服务初始化失败: {e}")
            raise

    async def respond(
        self,
        oa_text: str,
        context: dict[str, Any] | None = None,
        task_type: str = "office_action_response"
    ) -> str:
        """
        生成审查意见答复

        Args:
            oa_text: 审查意见文本
            context: 上下文信息
            task_type: 任务类型

        Returns:
            str: 答复文本
        """
        if not self._initialized:
            await self.initialize()

        if not self.llm_manager:
            return "错误: LLM管理器未初始化"

        # 构建提示词
        system_prompt = self._build_system_prompt()
        user_message = self._build_user_prompt(oa_text, context)

        try:
            # 使用LLM生成答复
            response = await self.llm_manager.generate(
                message=user_message,
                task_type="oa_response",
                context={"system_prompt": system_prompt},
                max_tokens=4000,
                temperature=0.7,
            )

            if response and response.content:
                return response.content
            else:
                return "错误: LLM响应为空"

        except Exception as e:
            logger.error(f"❌ 生成答复失败: {e}")
            return f"错误: 生成答复失败 - {str(e)}"

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是小娜，天秤女神，专业的专利代理师和审查意见答复专家。

你的任务是:
1. 仔细分析审查意见中指出的问题
2. 根据专利法和审查指南提供有针对性的答复
3. 语言要专业、准确、有说服力
4. 答复要结构清晰，论据充分

答复结构建议:
- 对审查员的问题表示理解和感谢
- 针对每个问题逐一进行答复
- 引用相关法律条文和审查指南
- 提供技术对比和证据支持
- 总结观点，请求专利局重新考虑

请用中文撰写答复。"""

    def _build_user_prompt(self, oa_text: str, context: dict[str, Any] | None) -> str:
        """构建用户提示词"""
        prompt = f"""请针对以下审查意见提供专业的答复:

【审查意见】
{oa_text}

"""
        if context:
            if context.get("patent_title"):
                prompt += f"\n【专利名称】\n{context['patent_title']}\n"
            if context.get("patent_number"):
                prompt += f"\n【专利申请号】\n{context['patent_number']}\n"
            if context.get("claims"):
                prompt += f"\n【权利要求】\n{context['claims']}\n"
            if context.get("prior_art"):
                prompt += f"\n【对比文件】\n{context['prior_art']}\n"

        prompt += """
请提供结构清晰、论据充分的专业答复。
"""
        return prompt


# 全局实例
_responder_instance: ProfessionalOAResponder | None = None


def get_professional_oa_responder() -> ProfessionalOAResponder:
    """获取全局答复器实例"""
    global _responder_instance
    if _responder_instance is None:
        _responder_instance = ProfessionalOAResponder()
    return _responder_instance


async def respond_to_office_action(
    oa_text: str,
    context: dict[str, Any] | None = None
) -> str:
    """
    生成审查意见答复（便捷函数）

    Args:
        oa_text: 审查意见文本
        context: 上下文信息

    Returns:
        str: 答复文本
    """
    responder = get_professional_oa_responder()
    return await responder.respond(oa_text, context)


# 测试函数
async def main():
    """测试函数"""
    # 示例审查意见
    example_oa = """
审查意见：

1. 关于权利要求1的新颖性
审查员认为：权利要求1的技术方案与对比文件1公开的内容相比，不具备新颖性。

具体理由：对比文件1公开了[具体技术特征]，与本申请权利要求1的技术方案实质相同。

2. 关于权利要求2-5的创造性
审查员认为：从属权利要求2-5的附加技术特征，对于本领域技术人员来说是显而易见的，不具备创造性。

请申请人陈述意见。
"""

    print("🔧 测试专业意见答复服务...")
    responder = get_professional_oa_responder()
    response = await responder.respond(
        oa_text=example_oa,
        context={
            "patent_title": "一种基于深度学习的图像识别方法",
            "patent_number": "CN202310123456.7"
        }
    )
    print("\n📄 答复结果:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
