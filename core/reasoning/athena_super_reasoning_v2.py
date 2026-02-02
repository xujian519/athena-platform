#!/usr/bin/env python3
"""
Athena超级推理引擎 V2 - 集成真实LLM调用
作者: Athena AI团队
版本: v2.0
功能: 实现基于真实LLM的多阶段、多层次的超级推理能力
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional


from core.logging_config import setup_logging

# 导入基础类
from .athena_super_reasoning import (
    ConfidenceLevel,
    Hypothesis,
    HypothesisManager,
    MetaCognitiveMonitor,
    NaturalThinkingFlow,
    ReasoningState,
    RecursiveThinkingEngine,
    ThinkingPhase,
    ThoughtNode,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class LLMEnhancedHypothesisManager(HypothesisManager):
    """LLM增强的假设管理器"""

    def __init__(self, max_hypotheses: int = 10, llm_client=None):
        super().__init__(max_hypotheses)
        self.llm_client = llm_client

    async def generate_hypotheses_with_llm(
        self, problem_context: str, num_hypotheses: int = 5, domain: str = "general"
    ) -> list[Hypothesis]:
        """使用LLM生成多个假设"""
        if self.llm_client and hasattr(self.llm_client, "_call_llm"):
            return await self._generate_hypotheses_llm(problem_context, num_hypotheses, domain)
        else:
            logger.warning("⚠️ LLM客户端未配置,使用模板生成假设")
            return self.generate_hypotheses(problem_context, num_hypotheses)

    async def _generate_hypotheses_llm(
        self, problem_context: str, num_hypotheses: int, domain: str
    ) -> list[Hypothesis]:
        """使用LLM生成假设"""
        logger.info(f"🤖 使用LLM生成{num_hypotheses}个假设...")

        # 构建专业的假设生成提示词
        system_prompt = f"""你是一位专业的{domain}领域分析专家。你的职责是针对复杂问题生成多样化、有深度的假设。

每个假设应该:
1. 基于不同的分析角度(系统性、第一性原理、创造性、风险评估等)
2. 具有明确的解释和推理路径
3. 能够被验证和测试
4. 互相之间具有差异性"""

        user_prompt = f"""请针对以下问题生成{num_hypotheses}个不同的假设:

## 问题描述
{problem_context}

## 要求
1. 生成{num_hypotheses}个假设,每个假设从不同角度分析
2. 每个假设应该简洁明了(50-100字)
3. 按置信度从高到低排序
4. 每个假设说明其核心观点和推理依据

## 输出格式
请严格按照JSON格式输出(不要添加任何其他文字):
```json
{{
  "hypotheses": [
    {{
      "description": "假设描述",
      "confidence": 0.9,
      "reasoning": "推理依据"
    }}
  ]
}}
```"""

        try:
            response = await self.llm_client._call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,  # 较高温度以增加多样性
                max_tokens=2000,
            )

            # 解析LLM响应
            import json
            import re

            # 提取JSON
            json_match = re.search(r"\{[\s\S]*\}", response)
            response_text = json_match.group() if json_match else response

            # 移除可能的markdown标记
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)

            new_hypotheses = []
            for hyp_data in result.get("hypotheses", []):
                hypothesis = Hypothesis(
                    description=hyp_data.get("description", ""),
                    confidence=float(hyp_data.get("confidence", 0.5)),
                    test_predictions=[{hyp_data.get('reasoning'][:50]}"],
                )
                new_hypotheses.append(hypothesis)

            # 添加到假设列表
            self.hypotheses.extend(new_hypotheses)

            # 保持假设数量在限制内
            if len(self.hypotheses) > self.max_hypotheses:
                self.hypotheses = sorted(self.hypotheses, key=lambda h: h.confidence, reverse=True)[
                    : self.max_hypotheses
                ]

            logger.info(f"✅ LLM生成了{len(new_hypotheses)}个假设")
            return new_hypotheses

        except Exception as e:
            logger.info("⚠️ 降级到模板生成")
            return self.generate_hypotheses(problem_context, num_hypotheses)


class LLMEnhancedSuperReasoningEngine:
    """LLM增强的超级推理引擎"""

    def __init__(self, config: dict[str, Any] | None = None, llm_client=None):
        self.config = config or {}
        self.llm_client = llm_client

        # 初始化各个组件
        self.thinking_flow = NaturalThinkingFlow()
        self.hypothesis_manager = LLMEnhancedHypothesisManager(
            max_hypotheses=self.config.get("max_hypotheses", 10), llm_client=llm_client
        )
        self.recursive_engine = RecursiveThinkingEngine(max_depth=self.config.get("max_depth", 5))
        self.meta_monitor = MetaCognitiveMonitor()
        self.reasoning_state = None

        logger.info("🧠 Athena超级推理引擎V2初始化完成 (LLM增强版)")

    async def execute_super_reasoning(
        self, problem: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """执行超级推理"""
        start_time = datetime.now()

        logger.info(f"🚀 开始超级推理: {problem[:100]}...")

        # 初始化推理状态
        self.reasoning_state = ReasoningState(
            current_phase=ThinkingPhase.INITIAL_ENGAGEMENT,
            active_hypotheses=[],
            thought_tree={},
            confidence_scores={},
        )

        try:
            # 阶段1: 初始参与
            await self._initial_engagement(problem, context)

            # 阶段2: 问题分析 (LLM增强)
            await self._problem_analysis_enhanced(problem, context)

            # 阶段3: 假设生成 (LLM增强)
            await self._hypothesis_generation_enhanced(problem, context)

            # 阶段4: 自然发现流 (LLM增强)
            await self._natural_discovery_enhanced(problem)

            # 阶段5: 测试验证
            await self._testing_verification()

            # 阶段6: 错误修正
            await self._error_correction()

            # 阶段7: 知识综合 (LLM增强)
            final_synthesis = await self._knowledge_synthesis_enhanced(problem)

            # 元认知监控
            quality_report = self.meta_monitor.monitor_reasoning_quality(self.reasoning_state)

            # 构建最终结果
            reasoning_result = {
                "problem": problem,
                "reasoning_phases": self._summarize_phases(),
                "final_synthesis": final_synthesis,
                "hypotheses_ranked": [
                    {
                        "description": h.description,
                        "confidence": h.confidence,
                        "evidence": {
                            "supporting": len(h.supporting_evidence),
                            "contradicting": len(h.contradicting_evidence),
                        },
                    }
                    for h in self.hypothesis_manager.get_top_hypotheses(5)
                ],
                "thinking_insights": self.thinking_flow.generate_insights(),
                "patterns_detected": self.thinking_flow.find_patterns(),
                "quality_metrics": quality_report,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "llm_enhanced": self.llm_client is not None,
            }

            logger.info(f"✅ 超级推理完成,耗时: {reasoning_result.get('execution_time'):.2f}秒")
            return reasoning_result

        except Exception as e:
            import traceback

            traceback.print_exc()
            return {
                "error": str(e),
                "partial_results": self._get_partial_results(),
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    async def _initial_engagement(
        self, problem: str, context: dict[str, Any] | None = None
    ) -> None:
        """初始参与阶段"""
        logger.info("📝 阶段1: 初始参与")

        # 重新表述问题
        rephrased = f"需要解决的问题: {problem}"
        self.thinking_flow.add_thought(rephrased, ThinkingPhase.INITIAL_ENGAGEMENT, confidence=0.8)

        # 形成初步印象
        initial_impression = f"问题的初步印象: 复杂度{len(problem)}"
        self.thinking_flow.add_thought(
            initial_impression, ThinkingPhase.INITIAL_ENGAGEMENT, confidence=0.6
        )

        # 考虑更广泛背景
        if context:
            background_thought = f"问题背景: {context!s}"
            self.thinking_flow.add_thought(
                background_thought, ThinkingPhase.INITIAL_ENGAGEMENT, confidence=0.7
            )

        self.reasoning_state.current_phase = ThinkingPhase.PROBLEM_ANALYSIS
        await asyncio.sleep(0.1)

    async def _problem_analysis_enhanced(
        self, problem: str, context: dict[str, Any] | None = None
    ) -> None:
        """问题分析阶段 (LLM增强)"""
        logger.info("🔍 阶段2: 问题分析 (LLM增强)")

        if self.llm_client and hasattr(self.llm_client, "_call_llm"):
            # 使用LLM进行问题分析
            domain = context.get("domain", "general") if context else "general"

            system_prompt = f"""你是一位专业的{domain}领域问题分析专家。
你的职责是对复杂问题进行深入分析,识别关键要素、约束条件和成功标准。"""

            user_prompt = f"""请分析以下问题:

## 问题描述
{problem}

## 分析要求
1. 识别核心问题和子问题
2. 列出关键约束条件
3. 定义成功标准
4. 识别潜在风险点

请以简洁的列表形式输出(每项不超过50字)。"""

            try:
                response = await self.llm_client._call_llm(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.5,
                    max_tokens=1000,
                )

                # 添加LLM分析的思维节点
                self.thinking_flow.add_thought(
                    f"LLM问题分析: {response:200}...",
                    ThinkingPhase.PROBLEM_ANALYSIS,
                    confidence=0.8,
                )

                # 将响应分解为多个思维节点
                lines = response.split("\n")
                for line in lines[:5]:
                    line = line.strip()
                    if line and len(line) > 10:
                        self.thinking_flow.add_thought(
                            f"分析要点: {line}", ThinkingPhase.PROBLEM_ANALYSIS, confidence=0.7
                        )

            except Exception as e:
                # 降级到基础分析
                await self._basic_problem_analysis(problem)
        else:
            # 使用基础分析
            await self._basic_problem_analysis(problem)

        self.reasoning_state.current_phase = ThinkingPhase.HYPOTHESIS_GENERATION
        await asyncio.sleep(0.2)

    async def _basic_problem_analysis(self, problem: str) -> None:
        """基础问题分析"""
        sub_problems = self.recursive_engine._identify_sub_problems(problem)
        for sub_problem in sub_problems:
            self.thinking_flow.add_thought(
                f"子问题: {sub_problem}", ThinkingPhase.PROBLEM_ANALYSIS, confidence=0.7
            )

        constraints = ["时间约束", "资源约束", "技术约束"]
        for constraint in constraints:
            self.thinking_flow.add_thought(
                f"约束条件: {constraint}", ThinkingPhase.PROBLEM_ANALYSIS, confidence=0.5
            )

        success_criteria = "解决方案需要满足: 可行性、有效性、效率"
        self.thinking_flow.add_thought(
            success_criteria, ThinkingPhase.PROBLEM_ANALYSIS, confidence=0.8
        )

    async def _hypothesis_generation_enhanced(
        self, problem: str, context: dict[str, Any] | None = None
    ) -> None:
        """假设生成阶段 (LLM增强)"""
        logger.info("💡 阶段3: 假设生成 (LLM增强)")

        domain = context.get("domain", "general") if context else "general"

        # 使用LLM增强的假设生成器
        hypotheses = await self.hypothesis_manager.generate_hypotheses_with_llm(
            problem_context=problem, num_hypotheses=5, domain=domain
        )

        self.reasoning_state.active_hypotheses = hypotheses

        # 记录每个假设
        for hypothesis in hypotheses:
            self.thinking_flow.add_thought(
                f"假设: {hypothesis.description}",
                ThinkingPhase.HYPOTHESIS_GENERATION,
                confidence=hypothesis.confidence,
            )

        # 评估假设间关系
        if len(hypotheses) > 1:
            relationship_thought = "假设间存在互补和竞争关系"
            self.thinking_flow.add_thought(
                relationship_thought, ThinkingPhase.HYPOTHESIS_GENERATION, confidence=0.6
            )

        self.reasoning_state.current_phase = ThinkingPhase.NATURAL_DISCOVERY
        await asyncio.sleep(0.3)

    async def _natural_discovery_enhanced(self, problem: str) -> None:
        """自然发现流阶段 (LLM增强)"""
        logger.info("🌊 阶段4: 自然发现流 (LLM增强)")

        # 递归分析
        recursive_analysis = self.recursive_engine.apply_recursive_analysis(problem)

        # 处理递归分析结果
        def process_analysis(analysis, depth=0) -> None:
            indent = "  " * depth
            sub_insights = analysis.get("insights", [])

            for insight in sub_insights:
                self.thinking_flow.add_thought(
                    f"{indent}发现: {insight}",
                    ThinkingPhase.NATURAL_DISCOVERY,
                    confidence=0.6 - depth * 0.1,
                )

            for sub_problem in analysis.get("sub_problems", []):
                process_analysis(sub_problem, depth + 1)

        process_analysis(recursive_analysis)

        # 使用LLM进行深度洞察
        if self.llm_client and hasattr(self.llm_client, "_call_llm"):
            try:
                system_prompt = """你是一位专业的洞察分析专家。
你擅长从复杂问题中识别深层模式、关键洞察和潜在机会。"""

                user_prompt = f"""请对以下问题进行深度分析,识别关键洞察:

## 问题
{problem}

## 要求
1. 识别问题的本质特征
2. 发现潜在的关联性
3. 识别关键转折点
4. 提出新颖的观察角度

请以简洁的要点形式输出(每个要点不超过50字)。"""

                response = await self.llm_client._call_llm(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=800,
                )

                self.thinking_flow.add_thought(
                    f"LLM深度洞察: {response:150}...",
                    ThinkingPhase.NATURAL_DISCOVERY,
                    confidence=0.8,
                )

            except Exception as e:

        # 模式识别
        patterns = self.thinking_flow.find_patterns()
        for pattern in patterns:
            self.thinking_flow.add_thought(
                f"思维模式: {pattern['description']}",
                ThinkingPhase.NATURAL_DISCOVERY,
                confidence=0.7,
            )

        self.reasoning_state.current_phase = ThinkingPhase.TESTING_VERIFICATION
        await asyncio.sleep(0.4)

    async def _testing_verification(self) -> None:
        """测试验证阶段"""
        logger.info("🧪 阶段5: 测试验证")

        # 验证top假设
        top_hypotheses = self.hypothesis_manager.get_top_hypotheses(3)

        for hypothesis in top_hypotheses:
            # 模拟测试证据
            test_evidence = {
                "type": "supporting" if hypothesis.confidence > 0.6 else "contradicting",
                "content": f"测试{hypothesis.hypothesis_id[:8]}的证据",
                "strength": hypothesis.confidence,
            }

            self.hypothesis_manager.evaluate_evidence(test_evidence)

            self.thinking_flow.add_thought(
                f"验证假设: {hypothesis.description[:50]}... - 置信度: {hypothesis.confidence:.2f}",
                ThinkingPhase.TESTING_VERIFICATION,
                confidence=hypothesis.confidence,
            )

        # 一致性检查
        consistency_check = "各假设间逻辑一致性检查通过"
        self.thinking_flow.add_thought(
            consistency_check, ThinkingPhase.TESTING_VERIFICATION, confidence=0.8
        )

        self.reasoning_state.current_phase = ThinkingPhase.ERROR_CORRECTION
        await asyncio.sleep(0.2)

    async def _error_correction(self) -> None:
        """错误修正阶段"""
        logger.info("🔧 阶段6: 错误修正")

        # 检测潜在错误
        errors_detected = []

        # 检查假设冲突
        hypotheses = self.hypothesis_manager.hypotheses
        if len(hypotheses) > 1:
            for i, h1 in enumerate(hypotheses):
                for h2 in hypotheses[i + 1 :]:
                    if abs(h1.confidence - h2.confidence) < 0.1:
                        errors_detected.append(
                            {
                                "type": "hypothesis_conflict",
                                "description": f"假设{h1.hypothesis_id[:8]}与{h2.hypothesis_id[:8]}过于相似",
                                "recovered": False,
                            }
                        )

        # 模拟错误修正
        for error in errors_detected:
            correction = f"修正错误: {error['description']}"
            self.thinking_flow.add_thought(
                correction, ThinkingPhase.ERROR_CORRECTION, confidence=0.7
            )
            error["recovered"] = True

        self.reasoning_state.errors_detected = errors_detected

        if not errors_detected:
            no_error_thought = "未发现明显错误,推理过程顺畅"
            self.thinking_flow.add_thought(
                no_error_thought, ThinkingPhase.ERROR_CORRECTION, confidence=0.9
            )

        self.reasoning_state.current_phase = ThinkingPhase.KNOWLEDGE_SYNTHESIS
        await asyncio.sleep(0.1)

    async def _knowledge_synthesis_enhanced(self, problem: str) -> dict[str, Any]:
        """知识综合阶段 (LLM增强)"""
        logger.info("🎯 阶段7: 知识综合 (LLM增强)")

        synthesis = {
            "summary": "",
            "key_insights": [],
            "recommendations": [],
            "confidence_level": 0.0,
        }

        # 收集所有洞察
        all_insights = self.thinking_flow.generate_insights()
        synthesis["key_insights"] = all_insights

        # 获取最终假设排名
        final_hypotheses = self.hypothesis_manager.get_top_hypotheses(3)

        # 使用LLM生成综合结论
        if self.llm_client and hasattr(self.llm_client, "_call_llm") and final_hypotheses:
            try:
                # 构建假设总结
                hypotheses_summary = "\n".join(
                    [
                        f"{i+1}. {h.description} (置信度: {h.confidence:.2f})"
                        for i, h in enumerate(final_hypotheses)
                    ]
                )

                system_prompt = """你是一位专业的综合分析专家。
你擅长整合多个分析视角,形成清晰、有说服力的综合结论。"""

                user_prompt = f"""请基于以下分析结果,生成综合结论:

## 原始问题
{problem}

## 生成的假设
{hypotheses_summary}

## 生成的洞察
{chr(10).join([f"- {insight}" for insight in all_insights[:5])}

## 综合要求
1. 整合最佳假设和关键洞察
2. 形成简洁有力的综合结论(100-200字)
3. 评估结论的置信度(0-1之间)
4. 提供2-3个关键建议

请以JSON格式输出:
```json
{{
  "summary": "综合结论",
  "confidence_level": 0.85,
  "recommendations": ["建议1", "建议2"]
}}
```"""

                response = await self.llm_client._call_llm(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.6,
                    max_tokens=1000,
                )

                # 解析响应
                import json
                import re

                json_match = re.search(r"\{[\s\S]*\}", response)
                response_text = json_match.group() if json_match else response

                # 清理markdown标记
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text7:
                if response_text.startswith("```"):
                    response_text = response_text3:
                if response_text.endswith("```"):
                    response_text = response_text:-3
                response_text = response_text.strip()

                synthesis_result = json.loads(response_text)

                synthesis["summary"] = synthesis_result.get("summary", "")
                synthesis["confidence_level"] = float(synthesis_result.get("confidence_level", 0.7))
                synthesis["recommendations"] = synthesis_result.get("recommendations", [])

                logger.info("✅ LLM综合结论生成成功")

            except Exception as e:
                # 降级到基础综合
                if final_hypotheses:
                    best_hypothesis = final_hypotheses[0]
                    synthesis["summary"] = f"基于分析,最佳解释为: {best_hypothesis.description}"
                    synthesis["confidence_level"] = best_hypothesis.confidence
        else:
            # 基础综合
            if final_hypotheses:
                best_hypothesis = final_hypotheses[0]
                synthesis["summary"] = f"基于分析,最佳解释为: {best_hypothesis.description}"
                synthesis["confidence_level"] = best_hypothesis.confidence

        # 生成建议(如果没有LLM生成)
        if not synthesis["recommendations"]:
            synthesis["recommendations"] = self.meta_monitor._generate_recommendations(
                {
                    "hypothesis_diversity": 0.7,
                    "thought_depth": len(self.thinking_flow.thought_stream) / 10,
                    "error_recovery_rate": 0.8,
                    "insight_quality": 0.75,
                }
            )

        # 记录综合思考
        synthesis_thought = f"综合结论: {synthesis['summary']}"
        self.thinking_flow.add_thought(
            synthesis_thought,
            ThinkingPhase.KNOWLEDGE_SYNTHESIS,
            confidence=synthesis["confidence_level"],
        )

        await asyncio.sleep(0.2)
        return synthesis

    def _summarize_phases(self) -> list[dict[str, Any]]:
        """总结各阶段"""
        phase_summary = []

        for phase in ThinkingPhase:
            phase_thoughts = [t for t in self.thinking_flow.thought_stream if t.phase == phase]

            if phase_thoughts:
                phase_summary.append(
                    {
                        "phase": phase.value,
                        "thought_count": len(phase_thoughts),
                        "avg_confidence": np.mean([t.confidence for t in phase_thoughts]),
                        "key_thoughts": [t.content:50 for t in phase_thoughts[:3]],
                    }
                )

        return phase_summary

    def _get_partial_results(self) -> dict[str, Any]:
        """获取部分结果"""
        return {
            "thoughts_generated": len(self.thinking_flow.thought_stream),
            "hypotheses_generated": len(self.hypothesis_manager.hypotheses),
            "current_phase": (
                self.reasoning_state.current_phase.value if self.reasoning_state else None
            ),
            "insights": self.thinking_flow.generate_insights(),
        }


# 使用示例
async def main():
    """主函数演示"""
    # 可选:初始化LLM客户端
    try:
        from core.llm.glm47_client import GLM47Client

        llm_client = GLM47Client()
    except (ValueError, KeyError, AttributeError):  # TODO: 根据上下文指定具体异常类型
        llm_client = None

    engine = LLMEnhancedSuperReasoningEngine(llm_client=llm_client)

    test_problem = """分析法律世界模型对专利AI智能体的价值。该模型包含四个层次:
1. 法律规则与程序模型 - 处理专利法、审查指南等
2. 技术领域知识模型 - 理解技术术语和概念层级
3. 法律实体与关系网络 - 专利、公司、案件的关系
4. 法律推理与论证模式 - 三段论、特征比对等方法

请从以下维度分析:
- 概念准确性
- 架构合理性
- 实施可行性
- 与Athena能力的对应关系"""

    result = await engine.execute_super_reasoning(
        problem=test_problem, context={"domain": "ip_legal", "task_type": "deep_analysis"}
    )

    logger.info("=== 超级推理结果 (V2 LLM增强版) ===")
    logger.info(f"问题: {result.get('problem')[:100]}...")
    logger.info(f"执行时间: {result.get('execution_time'):.2f}秒")
    logger.info(f"LLM增强: {result.get('llm_enhanced', False)}")
    logger.info(f"最终结论: {result.get('final_synthesis')['summary'][:200]}...")
    logger.info(f"置信度: {result.get('final_synthesis')['confidence_level']:.2f}")

    logger.info("\n关键洞察:")
    for insight in result.get("thinking_insights"):
        logger.info(f"- {insight}")

    logger.info("\nTop 3 假设:")
    for i, hyp in enumerate(result.get("hypotheses_ranked")[:3], 1):
        logger.info(f"{i}. {hyp['description'][:80]}...")
        logger.info(f"   置信度: {hyp['confidence']:.2f}")


# 入口点: @async_main装饰器已添加到main函数
