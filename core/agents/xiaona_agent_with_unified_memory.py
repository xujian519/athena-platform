"""
小娜智能体 - 集成统一记忆系统

示例展示如何在智能体中使用统一记忆系统：
1. 初始化时加载历史学习成果
2. 执行时读取项目上下文
3. 完成后保存工作历史
4. 更新学习成果
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from datetime import datetime

from core.agents.base_agent import BaseAgent
from core.memory.unified_memory_system import (
    get_project_memory,
    MemoryType,
    MemoryCategory
)

logger = logging.getLogger(__name__)


class XiaonaAgentWithMemory(BaseAgent):
    """
    小娜智能体 - 集成统一记忆系统

    核心功能：
    - 自动加载历史学习成果
    - 读取项目上下文和用户偏好
    - 保存分析结果和工作历史
    - 更新学习成果
    """

    def __init__(
        self,
        name: str = "xiaona",
        role: str = "专利法律专家",
        project_path: Optional[str] = None,
        **_kwargs  # noqa: ARG001
    ):
        """
        初始化小娜智能体

        Args:
            name: 智能体名称
            role: 智能体角色
            project_path: 项目路径（用于记忆系统）
            **_kwargs  # noqa: ARG001: 其他参数
        """
        # 初始化基类（包含记忆系统）
        super().__init__(
            name=name,
            role=role,
            project_path=project_path,
            **_kwargs  # noqa: ARG001
        )

        # 学习历史（从记忆系统加载）
        self.learning_history: list[dict[str, Any]] = []

        # 加载历史学习成果
        if self._memory_enabled:
            self._load_learning()

    def _load_learning(self) -> None:
        """加载历史学习成果"""
        try:
            learning_content = self.load_memory(
                MemoryType.GLOBAL,
                MemoryCategory.AGENT_LEARNING,
                f"{self.name}_learning"
            )

            if learning_content:
                # 解析学习历史（假设为JSON格式）
                try:
                    self.learning_history = json.loads(learning_content)
                    logger.info(f"加载学习历史: {len(self.learning_history)} 条记录")
                except json.JSONDecodeError:
                    logger.warning("学习历史格式错误，使用空列表")
                    self.learning_history = []
            else:
                logger.info("未找到历史学习成果，使用空列表")

        except Exception as e:
            logger.error(f"加载学习历史失败: {e}")

    def process(self, input_text: str, **_kwargs) -> str:
        """
        处理用户输入（集成记忆系统）

        Args:
            input_text: 输入文本
            **_kwargs  # noqa: ARG001: 其他参数

        Returns:
            响应文本
        """
        try:
            # 1. 读取项目上下文
            project_context = None
            if self._memory_enabled:
                project_context = self.get_project_context()
                if project_context:
                    logger.debug("已加载项目上下文")

            # 2. 读取用户偏好
            user_preferences = None
            if self._memory_enabled:
                user_preferences = self.get_user_preferences()
                if user_preferences:
                    logger.debug("已加载用户偏好")

            # 3. 构建增强的提示词
            enhanced_input = self._build_enhanced_input(
                input_text,
                project_context,
                user_preferences
            )

            # 4. 执行分析（这里简化处理，实际应调用LLM）
            result = self._perform_analysis(enhanced_input)

            # 5. 保存结果到记忆系统
            if self._memory_enabled:
                self._save_analysis_result(input_text, result)

            # 6. 保存工作历史
            if self._memory_enabled:
                self.save_work_history(
                    task=f"分析: {input_text[:100]}",
                    result=result[:200],
                    status="success"
                )

            return result

        except Exception as e:
            error_msg = f"处理失败: {e}"
            logger.error(error_msg)

            # 保存失败记录
            if self._memory_enabled:
                self.save_work_history(
                    task=f"分析: {input_text[:100]}",
                    result=error_msg,
                    status="failed"
                )

            return error_msg

    def _build_enhanced_input(
        self,
        input_text: str,
        project_context: Optional[str],
        user_preferences: Optional[str]
    ) -> str:
        """构建增强的输入（包含上下文）"""
        parts = [input_text]

        if project_context:
            parts.append(f"\n\n项目上下文：\n{project_context}")

        if user_preferences:
            parts.append(f"\n\n用户偏好：\n{user_preferences}")

        return "\n".join(parts)

    def _perform_analysis(self, input_text: str) -> str:
        """
        执行分析（简化版）

        实际实现中应调用LLM进行分析
        """
        # 这里简化处理，实际应调用LLM
        return f"分析结果：{input_text}"

    def _save_analysis_result(self, task: str, result: str) -> None:
        """保存分析结果到项目记忆"""
        try:
            # 生成唯一键
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"analysis_{timestamp}"

            # 构建Markdown内容
            content = f"""# 小娜分析结果

**时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**任务**: {task}

## 分析结果

{result}

---

*由小娜智能体生成*
"""

            # 保存到法律分析分类
            self.save_memory(
                MemoryType.PROJECT,
                MemoryCategory.LEGAL_ANALYSIS,
                key,
                content,
                metadata={
                    "agent": self.name,
                    "task": task,
                    "timestamp": timestamp
                }
            )

            logger.info(f"分析结果已保存: {key}")

        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")

    def update_insights(
        self,
        insight: str,
        category: str = "general"
    ) -> bool:
        """
        更新学习洞察

        Args:
            insight: 学习洞察
            category: 洞察分类

        Returns:
            是否成功
        """
        try:
            # 添加到学习历史
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "insight": insight,
                "category": category
            }
            self.learning_history.append(learning_entry)

            # 保存到记忆系统
            content = json.dumps(
                self.learning_history,
                ensure_ascii=False,
                indent=2
            )

            return self.update_learning(
                content,
                metadata={
                    "agent": self.name,
                    "entries_count": len(self.learning_history)
                }
            )

        except Exception as e:
            logger.error(f"更新学习洞察失败: {e}")
            return False

    def get_learning_summary(self) -> str:
        """获取学习摘要"""
        if not self.learning_history:
            return "暂无学习记录"

        summary_parts = [f"学习历史（共 {len(self.learning_history)} 条）：\n"]

        for entry in self.learning_history[-10:]:  # 最近10条
            summary_parts.append(
                f"- [{entry['timestamp']}] {entry['category']}: {entry['insight'][:100]}"
            )

        return "\n".join(summary_parts)


# 使用示例
def example_usage():
    """使用示例"""

    # 1. 创建带记忆的小娜智能体
    xiaona = XiaonaAgentWithMemory(
        name="xiaona",
        role="专利法律专家",
        project_path="/Users/xujian/Athena工作平台"
    )

    # 2. 处理任务（自动读取项目上下文和用户偏好）
    result = xiaona.process("分析专利CN123456789A的创造性")
    print(result)

    # 3. 更新学习洞察
    xiaona.update_insights(
        "创造性分析需要考虑对比文件的数量和技术领域的差异",
        category="patent_analysis"
    )

    # 4. 查看学习摘要
    print(xiaona.get_learning_summary())

    # 5. 搜索相关记忆
    memories = xiaona.search_memory("创造性", limit=5)
    print(f"找到 {len(memories)} 条相关记忆")


if __name__ == "__main__":
    example_usage()
