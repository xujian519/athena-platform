"""
Obsidian 写入器
将执行结果写入 Obsidian 仓库
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..core.command_parser import AgentType, TaskType
from ..core.command_router import ExecutionResult

logger = logging.getLogger(__name__)


class ObsidianWriter:
    """
    Obsidian 写入器

    职责：
    1. 将执行结果格式化为 Markdown
    2. 按任务类型组织文件结构
    3. 写入 Obsidian 仓库
    """

    def __init__(
        self,
        vault_path: str,
        organize_by: str = "task_type"
    ):
        """
        初始化 Obsidian 写入器

        Args:
            vault_path: Obsidian 仓库路径
            organize_by: 组织方式 (task_type | date | agent)
        """
        self.vault_path = Path(vault_path)
        self.organize_by = organize_by

        # 确保仓库存在
        if not self.vault_path.exists():
            raise ValueError(f"Obsidian vault not found: {vault_path}")

        # 创建任务目录映射
        self._setup_directories()

    def _setup_directories(self) -> None:
        """设置目录结构"""
        # 任务类型目录
        self.task_type_dirs = {
            TaskType.PATENT_SEARCH: "📊 专利检索",
            TaskType.PATENT_ANALYSIS: "📈 专利分析",
            TaskType.INFO_QUERY: "📞 信息查询",
            TaskType.COMPLEX_ANALYSIS: "🧠 Athena对话",
            TaskType.REMINDER: "⏰ 提醒事项"
        }

        # 智能体目录
        self.agent_dirs = {
            AgentType.XIAONUO: "💖 小诺对话",
            AgentType.ATHENA: "🧠 Athena对话"
        }

    async def write_result(
        self,
        result: ExecutionResult,
        command_text: str
    ) -> str:
        """
        将执行结果写入 Obsidian

        Args:
            result: 执行结果
            command_text: 原始命令文本

        Returns:
            写入的文件路径（相对路径）
        """
        try:
            # 确定目标目录
            target_dir = self._get_target_directory(result)
            target_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            filename = self._generate_filename(result)
            file_path = target_dir / filename

            # 格式化内容
            content = self._format_content(result, command_text)

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Written to Obsidian: {file_path}")

            # 返回相对路径（用于显示）
            relative_path = file_path.relative_to(self.vault_path)
            return str(relative_path)

        except Exception as e:
            logger.error(f"Failed to write to Obsidian: {e}")
            return ""

    def _get_target_directory(self, result: ExecutionResult) -> Path:
        """
        获取目标目录

        Args:
            result: 执行结果

        Returns:
            目标目录路径
        """
        if self.organize_by == "task_type":
            # 按任务类型组织
            # 还需要根据具体的任务类型来确定子目录
            # 我们需要从 result 中获取任务类型信息
            # 由于 ExecutionResult 中没有直接存储任务类型，我们需要从 details 中推断

            # 获取当前日期目录
            today = datetime.now().strftime("%Y-%m-%d")
            task_dir = self.vault_path / today

            # 尝试从 details 中推断任务类型
            # 这是一种简化处理，实际应该从 ExecutionResult 中获取 task_type
            return task_dir

        elif self.organize_by == "date":
            # 按日期组织
            today = datetime.now().strftime("%Y-%m-%d")
            return self.vault_path / today

        elif self.organize_by == "agent":
            # 按智能体组织
            agent_dir_name = self.agent_dirs.get(
                result.agent,
                "📦 其他"
            )
            today = datetime.now().strftime("%Y-%m-%d")
            return self.vault_path / agent_dir_name / today

        else:
            # 默认：根目录
            return self.vault_path

    def _generate_filename(self, result: ExecutionResult) -> str:
        """
        生成文件名

        Args:
            result: 执行结果

        Returns:
            文件名
        """
        # 使用任务ID和时间戳
        timestamp = datetime.now().strftime("%H%M%S")
        safe_task_id = result.task_id.replace(":", "_")

        # 从摘要中提取简短标题
        title = self._extract_title(result.summary)

        filename = f"{timestamp}_{title}_{safe_task_id}.md"
        return filename

    def _extract_title(self, summary: str) -> str:
        """
        从摘要中提取标题

        Args:
            summary: 摘要文本

        Returns:
            标题
        """
        # 移除表情符号和换行
        title = summary
        for char in ["✅", "❌", "🔄", "\n"]:
            title = title.replace(char, "")

        # 取前20个字符
        title = title.strip()[:20]
        # 移除不安全字符
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in unsafe_chars:
            title = title.replace(char, "_")

        return title.strip()

    def _format_content(
        self,
        result: ExecutionResult,
        command_text: str
    ) -> str:
        """
        格式化内容为 Markdown

        Args:
            result: 执行结果
            command_text: 原始命令文本

        Returns:
            Markdown 内容
        """
        agent_name = "小诺" if result.agent == AgentType.XIAONUO else "Athena"

        content = f"# {self._extract_title(result.summary)}\n\n"

        # 元数据区块
        content += "---\n"
        content += f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"智能体: {agent_name}\n"
        content += f"任务ID: {result.task_id}\n"
        content += f"状态: {result.status.value}\n"
        content += f"执行时长: {result.duration:.2f}秒\n"
        if result.obsidian_file:
            content += f"关联文件: {result.obsidian_file}\n"
        content += "---\n\n"

        # 原始命令
        content += "## 📝 原始命令\n\n"
        content += f"```\n{command_text}\n```\n\n"

        # 执行摘要
        content += "## 📋 执行摘要\n\n"
        content += f"{result.summary}\n\n"

        # 详细结果
        if result.details:
            content += "## 📊 详细结果\n\n"

            # 根据不同类型格式化详情
            if "patents" in result.details:
                content += self._format_patents(result.details)
            elif "creativity_score" in result.details:
                content += self._format_patent_analysis(result.details)
            elif "name" in result.details and "phone" in result.details:
                content += self._format_contact_info(result.details)
            elif "analysis_result" in result.details:
                content += self._format_complex_analysis(result.details)
            else:
                # 通用格式
                content += self._format_generic_details(result.details)

            content += "\n"

        # 元数据
        content += "## 🔧 元数据\n\n"
        content += f"- 任务ID: `{result.task_id}`\n"
        content += f"- 执行时长: {result.duration:.2f}秒\n"
        content += f"- 状态: **{result.status.value}**\n"
        if result.error:
            content += f"- 错误: `{result.error}`\n"

        # 标签
        content += "\n## 🏷️ 标签\n\n"
        content += f"#智能体/{agent_name} #任务/{result.status.value}\n"

        return content

    def _format_patents(self, details: Dict[str, Any]) -> str:
        """格式化专利列表"""
        content = f"**检索关键词**: {details.get('query', '')}\n\n"
        content += f"**结果数量**: {details.get('result_count', 0)} 件\n\n"

        patents = details.get("patents", [])
        if patents:
            content += "### 前5件专利\n\n"
            for i, patent in enumerate(patents, 1):
                content += f"{i}. **{patent.get('title', '未知标题')}**\n"
                content += f"   - 专利号: `{patent.get('patent_number', '')}`\n"
                content += f"   - 摘要: {patent.get('abstract', '')}\n\n"

        return content

    def _format_patent_analysis(self, details: Dict[str, Any]) -> str:
        """格式化专利分析"""
        content = f"**专利号**: `{details.get('patent_number', '')}`\n\n"
        content += f"**创造性评分**: {details.get('creativity_score', 0)}/100\n\n"

        innovation_points = details.get("innovation_points", [])
        if innovation_points:
            content += "### 主要创新点\n\n"
            for i, point in enumerate(innovation_points, 1):
                content += f"{i}. {point}\n"

        return content + "\n"

    def _format_contact_info(self, details: Dict[str, Any]) -> str:
        """格式化联系信息"""
        content = f"- **姓名**: {details.get('name', '')}\n"
        content += f"- **电话**: {details.get('phone', '无')}\n"
        content += f"- **邮箱**: {details.get('email', '无')}\n"

        return content + "\n"

    def _format_complex_analysis(self, details: Dict[str, Any]) -> str:
        """格式化复杂分析"""
        content = f"**分析主题**: {details.get('query', '')}\n\n"
        content += f"**置信度**: {details.get('confidence', 0)}%\n\n"

        key_findings = details.get("key_findings", [])
        if key_findings:
            content += "### 关键发现\n\n"
            for i, finding in enumerate(key_findings, 1):
                content += f"{i}. {finding}\n"

        sources = details.get("sources", [])
        if sources:
            content += "\n### 数据来源\n\n"
            for source in sources:
                content += f"- {source}\n"

        return content + "\n"

    def _format_generic_details(self, details: Dict[str, Any]) -> str:
        """格式化通用详情"""
        content = "```json\n"
        import json
        content += json.dumps(details, ensure_ascii=False, indent=2)
        content += "\n```\n"
        return content


# 测试代码
async def test_obsidian_writer():
    """测试 Obsidian 写入器"""
    from ..core.command_router import ExecutionResult, ExecutionStatus
    from ..core.command_parser import AgentType

    writer = ObsidianWriter(
        vault_path="/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/Athena",
        organize_by="task_type"
    )

    # 创建测试结果
    result = ExecutionResult(
        task_id="task_1234567890_1",
        status=ExecutionStatus.COMPLETED,
        agent=AgentType.XIAONUO,
        summary="✅ 专利检索完成\n关键词：人工智能\n结果：找到 23 件相关专利",
        details={
            "query": "人工智能",
            "result_count": 23,
            "patents": [
                {
                    "title": "基于人工智能的专利分析方法",
                    "patent_number": "CN202310123456.7",
                    "abstract": "本发明公开了一种基于人工智能的专利分析方法..."
                }
            ]
        },
        obsidian_file=None,
        duration=3.5
    )

    # 写入结果
    file_path = await writer.write_result(
        result,
        "小诺，帮我检索关于人工智能的专利"
    )

    print(f"Written to: {file_path}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_obsidian_writer())
