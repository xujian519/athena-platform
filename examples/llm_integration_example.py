#!/usr/bin/env python3
"""
小娜智能体LLM集成示例

演示如何在BaseXiaonaComponent中使用LLM功能
"""

import asyncio
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentStatus,
    AgentExecutionContext,
    AgentExecutionResult
)


class PatentAnalyzerWithLLM(BaseXiaonaComponent):
    """
    带LLM集成的专利分析器示例

    演示如何：
    1. 在子类中使用LLM功能
    2. 配置LLM参数
    3. 调用LLM并处理响应
    4. 使用降级机制
    """

    def _initialize(self) -> None:
        """初始化专利分析器"""
        self._register_capabilities([
            AgentCapability(
                name="patent_analysis",
                description="专利创造性分析",
                input_types=["patent_text", "prior_art"],
                output_types=["analysis_report"],
                estimated_time=30.0
            ),
            AgentCapability(
                name="novelty_search",
                description="新颖性检索",
                input_types=["patent_claims"],
                output_types=["search_results"],
                estimated_time=60.0
            )
        ])

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """
你是一位资深的专利分析专家，擅长：
1. 专利创造性分析（步骤问题、显著性进步）
2. 新颖性检索（对比文件查找）
3. 权利要求解释
4. 技术方案理解

请以专业、严谨的态度进行专利分析。
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行专利分析任务

        演示如何在execute方法中使用LLM
        """
        try:
            # 获取输入数据
            patent_text = context.input_data.get("patent_text", "")
            analysis_type = context.input_data.get("analysis_type", "creativity")

            # 构建提示词
            if analysis_type == "creativity":
                prompt = f"""
请分析以下专利的创造性：

专利内容：
{patent_text}

请从以下几个方面进行分析：
1. 技术领域和技术问题
2. 技术方案的创新点
3. 与现有技术的区别
4. 显著性进步的判断
5. 创造性结论（高/中/低）
"""
                task_type = "patent_analysis"
            else:
                prompt = f"请分析专利：{patent_text}"
                task_type = "general"

            # 调用LLM（使用带降级的版本）
            try:
                llm_response = await self._call_llm_with_fallback(
                    prompt=prompt,
                    task_type=task_type,
                    fallback_prompt=f"简要分析：{patent_text}"  # 简化的降级提示词
                )

                # 返回结果
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.COMPLETED,
                    output_data={
                        "analysis": llm_response,
                        "analysis_type": analysis_type,
                        "patent_length": len(patent_text)
                    },
                    execution_time=0.0
                )

            except Exception as llm_error:
                # LLM调用失败，返回错误结果
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message=f"LLM调用失败: {str(llm_error)}",
                    execution_time=0.0
                )

        except Exception as e:
            # 其他错误
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=f"执行失败: {str(e)}",
                execution_time=0.0
            )


async def main():
    """主函数：演示LLM集成功能"""
    print("=" * 60)
    print("小娜智能体LLM集成示例")
    print("=" * 60)

    # 1. 创建分析器实例
    print("\n1. 创建专利分析器...")
    analyzer = PatentAnalyzerWithLLM(
        agent_id="patent_analyzer_llm_demo",
        config={
            # 可以自定义LLM配置
            "llm_config": {
                "temperature": 0.6,
                "max_tokens": 4096
            }
        }
    )
    print(f"✅ 分析器创建成功: {analyzer.agent_id}")

    # 2. 查看能力
    print("\n2. 查看分析器能力...")
    capabilities = analyzer.get_capabilities()
    for cap in capabilities:
        print(f"   - {cap.name}: {cap.description}")

    # 3. 检查LLM初始化状态
    print("\n3. 检查LLM状态...")
    analyzer._ensure_llm_initialized()
    if analyzer._llm_manager:
        print("✅ LLM管理器已初始化")
    else:
        print("⚠️  LLM管理器未初始化（这是正常的，如果LLM模块不可用）")

    # 4. 执行分析任务（如果LLM可用）
    if analyzer._llm_manager:
        print("\n4. 执行专利分析任务...")
        context = AgentExecutionContext(
            session_id="demo_session",
            task_id="demo_task",
            input_data={
                "patent_text": """
一种基于深度学习的图像识别方法，包括以下步骤：
1. 收集训练数据集
2. 构建卷积神经网络模型
3. 使用训练数据集训练模型
4. 使用训练好的模型进行图像识别
""",
                "analysis_type": "creativity"
            },
            config={},
            metadata={}
        )

        result = await analyzer._execute_with_monitoring(context)

        print(f"\n执行状态: {result.status.value}")
        if result.status == AgentStatus.COMPLETED:
            print(f"✅ 分析完成，耗时: {result.execution_time:.2f}秒")
            print(f"\n分析结果:")
            print(result.output_data.get("analysis", "无结果"))
        else:
            print(f"❌ 分析失败: {result.error_message}")
    else:
        print("\n4. 跳过分析任务（LLM不可用）")

    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
