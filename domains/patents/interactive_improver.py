from __future__ import annotations

"""
交互式专利权利要求质量改进器

基于论文3的质量评估框架和论文2的生成技术，实现多轮交互式改进。
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .quality_assessor import (
    ClaimQualityAssessor,
    QualityAssessment,
    QualityDimension,
)


class ImprovementStrategy(Enum):
    """改进策略"""
    CONSERVATIVE = "conservative"  # 保守：只修复严重问题
    BALANCED = "balanced"  # 平衡：修复重要问题，考虑建议
    AGGRESSIVE = "aggressive"  # 激进：最大化所有维度得分


@dataclass
class ImprovementAction:
    """改进动作"""
    iteration: int
    dimension: QualityDimension
    action_type: str  # "modify", "add", "remove", "restructure"
    description: str
    original_text: str
    modified_text: str
    reasoning: str
    expected_improvement: float  # 预期提升的分数


@dataclass
class ImprovementSession:
    """改进会话"""
    session_id: str
    initial_claim: str
    description: str  # 说明书描述
    current_claim: str
    iterations: list[ImprovementAction] = field(default_factory=list)
    current_assessment: QualityAssessment | None = None
    user_feedback: list[dict] = field(default_factory=list)
    started_at: datetime
    strategy: ImprovementStrategy = ImprovementStrategy.BALANCED
    max_iterations: int = 3

    @property
    def iteration_count(self) -> int:
        return len(self.iterations)

    @property
    def is_complete(self) -> bool:
        """检查是否完成（达到质量目标或最大迭代次数）"""
        if self.current_assessment and self.current_assessment.can_file:
            return True
        if self.iteration_count >= self.max_iterations:
            return True
        return False

    def get_progress_summary(self) -> str:
        """获取进度摘要"""
        return f"""
改进会话进度
{'='*60}
会话ID: {self.session_id}
开始时间: {self.started_at.strftime('%Y-%m-%d %H:%M')}
当前迭代: {self.iteration_count}/{self.max_iterations}
当前策略: {self.strategy.value}
完成状态: {'✅ 是' if self.is_complete else '⏳ 进行中'}

当前质量水平: {self.current_assessment.quality_level if self.current_assessment else 'N/A'}
当前总分: {f'{self.current_assessment.overall_score:.1f}/10' if self.current_assessment else 'N/A'}
可提交: {'✅ 是' if self.current_assessment and self.current_assessment.can_file else '❌ 否'}
{'='*60}
已执行的改进:
{self._format_improvements()}
        """.strip()

    def _format_improvements(self) -> str:
        """格式化改进历史"""
        if not self.iterations:
            return "  （暂无）"

        lines = []
        for i, action in enumerate(self.iterations, 1):
            arrow = "→" if action.original_text != action.modified_text else "•"
            lines.append(
                f"  迭代{i}: [{action.dimension.value}] {action.description} {arrow}"
            )
            lines.append(f"    预期改进: +{action.expected_improvement:.1f}分")

        return "\n".join(lines)


class InteractiveQualityImprover:
    """
    交互式专利权利要求质量改进器

    实现基于论文3的多轮交互式改进流程：
    1. 评估当前版本
    2. 生成改进建议
    3. 应用改进（自动或用户确认）
    4. 重新评估
    5. 重复直到达到质量目标
    """

    def __init__(self,
                 llm_client=None,
                 quality_assessor: ClaimQualityAssessor | None = None):
        """
        初始化改进器

        Args:
            llm_client: LLM客户端
            quality_assessor: 质量评估器（可选，默认创建新的）
        """
        self.llm = llm_client
        self.assessor = quality_assessor or ClaimQualityAssessor(llm_client)
        self.sessions: dict[str, ImprovementSession] = {}

    def create_session(self,
                    initial_claim: str,
                    description: str,
                    strategy: ImprovementStrategy = ImprovementStrategy.BALANCED,
                    max_iterations: int = 3) -> ImprovementSession:
        """
        创建新的改进会话

        Args:
            initial_claim: 初始权利要求文本
            description: 说明书描述
            strategy: 改进策略
            max_iterations: 最大迭代次数

        Returns:
            ImprovementSession: 改进会话对象
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 初始评估
        initial_assessment = self.assessor.assess(
            claim_text=initial_claim,
            description=description
        )

        session = ImprovementSession(
            session_id=session_id,
            initial_claim=initial_claim,
            description=description,
            current_claim=initial_claim,
            current_assessment=initial_assessment,
            started_at=datetime.now(),
            strategy=strategy,
            max_iterations=max_iterations
        )

        self.sessions[session_id] = session
        return session

    def improve(self,
               session: ImprovementSession,
               auto_apply: bool = True,
               user_preferences: dict | None = None) -> ImprovementSession:
        """
        执行改进流程

        Args:
            session: 改进会话
            auto_apply: 是否自动应用改进（False则等待用户确认）
            user_preferences: 用户偏好（如优先改进的维度）

        Returns:
            ImprovementSession: 更新后的会话
        """
        while not session.is_complete:
            # 步骤1: 生成改进建议
            suggestions = self._generate_improvement_suggestions(
                session,
                user_preferences
            )

            if not suggestions:
                print("  ✅ 质量已达标，无需进一步改进")
                break

            # 步骤2: 展示改进选项
            if not auto_apply:
                print(f"\n{'='*60}")
                print(f"迭代 {session.iteration_count + 1}: 改进建议")
                print(f"{'='*60}")
                print(suggestions.get_summary())

                # 等待用户选择
                choice = input("\n选择改进选项 (输入数字或'skip'跳过, 'done'完成): ").strip()
                if choice.lower() == 'done':
                    break
                elif choice.lower() == 'skip':
                    continue
                else:
                    try:
                        action = suggestions.select_action(int(choice))
                    except (ValueError, IndexError):
                        print("  ⚠️ 无效选择，请重试")
                        continue
            else:
                # 自动应用最佳改进
                action = suggestions.get_best_action()

            # 步骤3: 应用改进
            session.current_claim = action.modified_text
            session.iterations.append(action)

            # 记录用户反馈
            if user_preferences:
                session.user_feedback.append({
                    "iteration": session.iteration_count,
                    "action": action.description,
                    "user_confirmed": auto_apply
                })

            # 步骤4: 重新评估
            new_assessment = self.assessor.assess(
                claim_text=session.current_claim,
                description=session.description
            )

            # 步骤5: 显示进度
            improvement = new_assessment.overall_score - session.current_assessment.overall_score
            print(f"\n  ✅ 改进已应用: {action.description}")
            print(f"  📊 质量变化: {session.current_assessment.overall_score:.1f} → {new_assessment.overall_score:.1f} (+{improvement:.1f})")
            print(f"  📈 质量等级: {session.current_assessment.quality_level} → {new_assessment.quality_level}")

            session.current_assessment = new_assessment

            # 检查是否完成
            if session.is_complete:
                print("\n  🎉 改进完成！质量已达标。")
                break

        return session

    def _generate_improvement_suggestions(self,
                                     session: ImprovementSession,
                                     user_preferences: dict | None) -> ImprovementSuggestions:
        """生成改进建议"""
        assessment = session.current_assessment
        priority_dims = assessment.improvement_priority

        suggestions = ImprovementSuggestions()

        # 为每个需改进的维度生成建议
        for dimension in priority_dims:
            dim_score = assessment.dimension_scores[dimension]

            # 跳过已经达标的维度
            if dim_score.score >= 8.5:
                continue

            # 生成具体建议
            actions = self._generate_dimension_actions(
                dimension,
                dim_score,
                session.current_claim,
                session.description,
                session.strategy
            )

            for action in actions:
                suggestions.add_action(action)

        return suggestions

    def _generate_dimension_actions(self,
                                dimension: QualityDimension,
                                dim_score,
                                current_claim: str,
                                description: str,
                                strategy: ImprovementStrategy) -> list[ImprovementAction]:
        """为特定维度生成改进动作"""
        actions = []

        # 构建提示词
        prompt = self._build_improvement_prompt(
            dimension, dim_score, current_claim, description, strategy
        )

        # 调用LLM生成改进
        response = self.llm.generate(prompt)

        # 解析响应
        try:
            data = json.loads(response)
            for suggestion_data in data.get("suggestions", []):
                action = ImprovementAction(
                    iteration=0,  # 稍后设置
                    dimension=dimension,
                    action_type=suggestion_data.get("type", "modify"),
                    description=suggestion_data.get("description", ""),
                    original_text=current_claim,
                    modified_text=suggestion_data.get("modified_claim", current_claim),
                    reasoning=suggestion_data.get("reasoning", ""),
                    expected_improvement=suggestion_data.get("expected_score", 0.5)
                )
                actions.append(action)
        except json.JSONDecodeError:
            # 解析失败，生成通用建议
            action = ImprovementAction(
                iteration=0,
                dimension=dimension,
                action_type="modify",
                description=f"改进{dimension.value}",
                original_text=current_claim,
                modified_text=current_claim,
                reasoning="LLM响应解析失败",
                expected_improvement=0.3
            )
            actions.append(action)

        return actions

    def _build_improvement_prompt(self,
                                dimension: QualityDimension,
                                dim_score,
                                current_claim: str,
                                description: str,
                                strategy: ImprovementStrategy) -> str:
        """构建改进提示词"""
        strategy_instruction = {
            ImprovementStrategy.CONSERVATIVE: "只修复严重错误，不要大幅修改",
            ImprovementStrategy.BALANCED: "在保持核心内容的前提下优化质量",
            ImprovementStrategy.AGGRESSIVE: "积极优化以最大化所有维度得分"
        }

        dimension_names = {
            QualityDimension.NOVELTY: "新颖性",
            QualityDimension.CLARITY: "清晰性",
            QualityDimension.COMPLETENESS: "完整性",
            QualityDimension.SUPPORT: "支持性",
            QualityDimension.SCOPE_APPROPRIATENESS: "范围恰当性",
            QualityDimension.LEGAL_COMPLIANCE: "法律规范性"
        }

        return f"""
你是一位资深专利代理人。当前有以下权利要求需要改进：

【当前权利要求】
{current_claim}

【说明书描述】
{description}

【需要改进的维度】
维度: {dimension_names.get(dimension, dimension.value)}
当前得分: {dim_score:.1f}/10

【改进策略】
{strategy_instruction.get(strategy, strategy.value)}

请生成具体的改进建议，以JSON格式返回：
{{
    "analysis": "<当前问题的分析>",
    "suggestions": [
        {{
            "type": "<modify/add/remove/restructure>",
            "description": "<改进描述>",
            "reasoning": "<改进理由>",
            "modified_claim": "<修改后的权利要求>",
            "expected_score": "<预期得分>"
        }}
    ]
}}

注意：
1. 修改后的权利要求必须保持技术准确性
2. 不能添加说明书中未公开的内容
3. 遵循标准专利法术语和格式
4. 保持前序部分和引用结构正确
        """.strip()

    def get_session(self, session_id: str) -> ImprovementSession | None:
        """获取会话"""
        return self.sessions.get(session_id)

    def list_sessions(self) -> list[str]:
        """列出所有会话ID"""
        return list(self.sessions.keys())

    def close_session(self, session_id: str) -> ImprovementSession | None:
        """关闭会话"""
        return self.sessions.pop(session_id, None)


class ImprovementSuggestions:
    """改进建议集合"""

    def __init__(self):
        self.actions: list[ImprovementAction] = []

    def add_action(self, action: ImprovementAction):
        """添加改进动作"""
        self.actions.append(action)

    def get_best_action(self) -> ImprovementAction:
        """获取最佳改进动作（预期改进最大）"""
        if not self.actions:
            raise ValueError("没有可用的改进建议")

        return max(self.actions, key=lambda a: a.expected_improvement)

    def select_action(self, index: int) -> ImprovementAction:
        """选择特定动作"""
        if 0 < index <= len(self.actions):
            return self.actions[index - 1]
        raise IndexError(f"无效的索引: {index}")

    def get_summary(self) -> str:
        """获取建议摘要"""
        if not self.actions:
            return "  暂无改进建议"

        lines = ["  可用改进选项:\n"]

        for i, action in enumerate(self.actions, 1):
            score_indicator = "🌟" if action.expected_improvement > 1.0 else \
                           "⭐" if action.expected_improvement > 0.5 else "•"

            lines.append(
                f"  [{i}] {score_indicator} {action.description}\n"
                f"      维度: {action.dimension.value}\n"
                f"      预期改进: +{action.expected_improvement:.1f}分\n"
            )

        return "".join(lines)


# 使用示例

def example_usage():
    """使用示例"""
    # 假设有一个LLM客户端
    class MockLLM:
        def generate(self, prompt):
            return """{
                "analysis": "术语使用不一致，范围限定词使用不当",
                "suggestions": [
                    {
                        "type": "modify",
                        "description": "统一技术术语表达",
                        "reasoning": "将'光伏板'统一为'光伏转换模块'",
                        "modified_claim": "1. 一种太阳能装置，包括：光伏转换模块...",
                        "expected_score": 8.5
                    }
                ]
            }"""

    llm = MockLLM()

    # 创建改进器
    improver = InteractiveQualityImprover(llm_client=llm)

    # 创建会话
    initial_claim = "1. 一种太阳能装置，包括光伏板和储能电池。"
    description = "本发明涉及一种太阳能利用装置..."

    session = improver.create_session(
        initial_claim=initial_claim,
        description=description,
        strategy=ImprovementStrategy.BALANCED
    )

    print(session.get_progress_summary())

    # 执行改进（自动模式）
    improved_session = improver.improve(session, auto_apply=True)

    print("\n" + "="*60)
    print("改进完成！")
    print("="*60)
    print("\n最终权利要求:")
    print(improved_session.current_claim)
    print("\n最终评估:")
    print(improved_session.current_assessment.get_summary())


if __name__ == "__main__":
    example_usage()
