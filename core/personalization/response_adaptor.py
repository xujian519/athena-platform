from __future__ import annotations
"""
个性化响应模块 - Personalized Response

根据用户偏好自适应调整响应风格:
1. 响应详细程度自适应
2. 技术深度自适应
3. 语言风格选择
4. 输出格式定制
5. 用户偏好学习
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ResponseDetail(Enum):
    """响应详细程度"""

    BRIEF = "brief"  # 简洁 - 只给关键信息
    MEDIUM = "medium"  # 中等 - 适量信息
    DETAILED = "detailed"  # 详细 - 完整信息
    COMPREHENSIVE = "comprehensive"  # 全面 - 所有相关信息


class TechnicalDepth(Enum):
    """技术深度"""

    BASIC = "basic"  # 基础 - 通俗易懂
    INTERMEDIATE = "intermediate"  # 中级 - 适度专业
    ADVANCED = "advanced"  # 高级 - 高度专业
    EXPERT = "expert"  # 专家 - 极度专业


class LanguageStyle(Enum):
    """语言风格"""

    CASUAL = "casual"  # 随意 - 轻松友好
    PROFESSIONAL = "professional"  # 专业 - 正式规范
    FORMAL = "formal"  # 正式 - 严谨庄重
    FRIENDLY = "friendly"  # 友好 - 亲切热情


class OutputFormat(Enum):
    """输出格式"""

    TEXT = "text"  # 纯文本
    MARKDOWN = "markdown"  # Markdown格式
    JSON = "json"  # JSON格式
    BULLET_POINTS = "bullet_points"  # 要点列表
    TABLE = "table"  # 表格


@dataclass
class UserPreference:
    """用户偏好"""

    user_id: str  # 用户ID
    response_detail: ResponseDetail  # 响应详细程度
    technical_depth: TechnicalDepth  # 技术深度
    language_style: LanguageStyle  # 语言风格
    output_format: OutputFormat  # 输出格式
    preferred_capabilities: list[str] = field(default_factory=list)  # 偏好的智能体
    avoided_topics: list[str] = field(default_factory=list)  # 避免的话题
    custom_prompts: dict[str, str] = field(default_factory=dict)  # 自定义提示词
    created_at: float = field(default_factory=time.time)  # 创建时间
    updated_at: float = field(default_factory=time.time)  # 更新时间

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "response_detail": self.response_detail.value,
            "technical_depth": self.technical_depth.value,
            "language_style": self.language_style.value,
            "output_format": self.output_format.value,
            "preferred_capabilities": self.preferred_capabilities,
            "avoided_topics": self.avoided_topics,
            "custom_prompts": self.custom_prompts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserPreference":
        """从字典创建"""
        return cls(
            user_id=data["user_id"],
            response_detail=ResponseDetail(data.get("response_detail", "medium")),
            technical_depth=TechnicalDepth(data.get("technical_depth", "intermediate")),
            language_style=LanguageStyle(data.get("language_style", "professional")),
            output_format=OutputFormat(data.get("output_format", "text")),
            preferred_capabilities=data.get("preferred_capabilities", []),
            avoided_topics=data.get("avoided_topics", []),
            custom_prompts=data.get("custom_prompts", {}),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


class ResponseAdapter:
    """
    响应适配器

    根据用户偏好调整响应
    """

    def __init__(self, db_path: str = "data/user_preferences.db"):
        """
        初始化响应适配器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._init_db()
        logger.info("✅ 响应适配器初始化完成")

    def _init_db(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                response_detail TEXT DEFAULT 'medium',
                technical_depth TEXT DEFAULT 'intermediate',
                language_style TEXT DEFAULT 'professional',
                output_format TEXT DEFAULT 'text',
                preferred_capabilities TEXT DEFAULT '[]',
                avoided_topics TEXT DEFAULT '[]',
                custom_prompts TEXT DEFAULT '{}',
                created_at REAL DEFAULT 0,
                updated_at REAL DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def get_user_preference(self, user_id: str) -> UserPreference:
        """
        获取用户偏好

        Args:
            user_id: 用户ID

        Returns:
            用户偏好
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return UserPreference(
                user_id=row[0],
                response_detail=ResponseDetail(row[1]),
                technical_depth=TechnicalDepth(row[2]),
                language_style=LanguageStyle(row[3]),
                output_format=OutputFormat(row[4]),
                preferred_capabilities=json.loads(row[5]),
                avoided_topics=json.loads(row[6]),
                custom_prompts=json.loads(row[7]),
                created_at=row[8],
                updated_at=row[9],
            )
        else:
            # 返回默认偏好
            return UserPreference(
                user_id=user_id,
                response_detail=ResponseDetail.MEDIUM,
                technical_depth=TechnicalDepth.INTERMEDIATE,
                language_style=LanguageStyle.PROFESSIONAL,
                output_format=OutputFormat.TEXT,
            )

    def save_user_preference(self, preference: UserPreference) -> None:
        """
        保存用户偏好

        Args:
            preference: 用户偏好
        """
        preference.updated_at = time.time()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO user_preferences
            (user_id, response_detail, technical_depth, language_style, output_format,
             preferred_capabilities, avoided_topics, custom_prompts, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                preference.user_id,
                preference.response_detail.value,
                preference.technical_depth.value,
                preference.language_style.value,
                preference.output_format.value,
                json.dumps(preference.preferred_capabilities),
                json.dumps(preference.avoided_topics),
                json.dumps(preference.custom_prompts),
                preference.created_at,
                preference.updated_at,
            ),
        )

        conn.commit()
        conn.close()

        logger.debug(f"保存用户偏好: {preference.user_id}")

    def adapt_response(
        self, user_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        根据用户偏好适配响应

        Args:
            user_id: 用户ID
            content: 原始内容
            metadata: 元数据

        Returns:
            适配后的响应
        """
        preference = self.get_user_preference(user_id)

        result = {
            "content": content,
            "format": preference.output_format.value,
            "metadata": metadata or {},
        }

        # 根据详细程度调整内容
        if preference.response_detail == ResponseDetail.BRIEF:
            result["content"] = self._summarize(content, level="brief")
        elif preference.response_detail == ResponseDetail.DETAILED:
            result["content"] = self._expand(content, level="detailed")
        elif preference.response_detail == ResponseDetail.COMPREHENSIVE:
            result["content"] = self._expand(content, level="comprehensive")

        # 根据输出格式调整
        result = self._format_output(result, preference.output_format)

        # 添加语言风格提示(供LLM使用)
        result["style_hints"] = {
            "technical_depth": preference.technical_depth.value,
            "language_style": preference.language_style.value,
        }

        return result

    def _summarize(self, content: str, level: str = "brief") -> str:
        """总结内容"""
        # 这里是简化实现,实际应该使用LLM
        lines = content.split("\n")
        if level == "brief":
            # 只保留前30%的内容
            return "\n".join(lines[: max(1, len(lines) // 3)])
        return content

    def _expand(self, content: str, level: str = "detailed") -> str:
        """扩展内容"""
        # 这里是简化实现,实际应该使用LLM
        return content

    def _format_output(
        self, response: dict[str, Any], output_format: OutputFormat
    ) -> dict[str, Any]:
        """格式化输出"""
        content = response["content"]

        if output_format == OutputFormat.MARKDOWN:
            # 转换为Markdown
            response["content"] = self._to_markdown(content)
        elif output_format == OutputFormat.JSON:
            # 转换为JSON
            response["content"] = json.dumps({"response": content}, ensure_ascii=False)
        elif output_format == OutputFormat.BULLET_POINTS:
            # 转换为要点列表
            response["content"] = self._to_bullet_points(content)
        elif output_format == OutputFormat.TABLE:
            # 尝试转换为表格
            response["content"] = self._to_table(content)

        return response

    def _to_markdown(self, content: str) -> str:
        """转换为Markdown"""
        # 简化实现:添加基本格式
        if not content.startswith("#"):
            content = "# 响应\n\n" + content
        return content

    def _to_bullet_points(self, content: str) -> str:
        """转换为要点列表"""
        lines = content.split("\n")
        bullets = []
        for line in lines:
            line = line.strip()
            if line:
                bullets.append(f"• {line}")
        return "\n".join(bullets)

    def _to_table(self, content: str) -> str:
        """转换为表格"""
        # 简化实现:尝试检测表格格式
        if "|" in content:
            return content  # 已经是表格格式
        return f"| 内容 |\n|------|\n| {content} |"

    def learn_from_feedback(
        self, user_id: str, feedback: str, context: dict[str, Any] | None = None
    ) -> None:
        """
        从反馈中学习

        Args:
            user_id: 用户ID
            feedback: 反馈内容
            context: 上下文
        """
        preference = self.get_user_preference(user_id)

        # 简化的学习逻辑
        feedback_lower = feedback.lower()

        if "太详细" in feedback_lower or "简单" in feedback_lower:
            if preference.response_detail != ResponseDetail.BRIEF:
                # 降低详细程度
                levels = list(ResponseDetail)
                current_idx = levels.index(preference.response_detail)
                if current_idx > 0:
                    preference.response_detail = levels[current_idx - 1]

        elif "太简单" in feedback_lower or "详细" in feedback_lower:
            if preference.response_detail != ResponseDetail.COMPREHENSIVE:
                # 提高详细程度
                levels = list(ResponseDetail)
                current_idx = levels.index(preference.response_detail)
                if current_idx < len(levels) - 1:
                    preference.response_detail = levels[current_idx + 1]

        elif "太专业" in feedback_lower or "不懂" in feedback_lower:
            # 降低技术深度
            levels = list(TechnicalDepth)
            current_idx = levels.index(preference.technical_depth)
            if current_idx > 0:
                preference.technical_depth = levels[current_idx - 1]

        elif "不够专业" in feedback_lower or "更深入" in feedback_lower:
            # 提高技术深度
            levels = list(TechnicalDepth)
            current_idx = levels.index(preference.technical_depth)
            if current_idx < len(levels) - 1:
                preference.technical_depth = levels[current_idx + 1]

        self.save_user_preference(preference)
        logger.info(f"从反馈中学习: {user_id}")


# 全局单例
_response_adapter: ResponseAdapter | None = None


def get_response_adapter() -> ResponseAdapter:
    """获取响应适配器单例"""
    global _response_adapter
    if _response_adapter is None:
        _response_adapter = ResponseAdapter()
    return _response_adapter


# 便捷函数
def get_user_preference(user_id: str) -> UserPreference:
    """获取用户偏好"""
    return get_response_adapter().get_user_preference(user_id)


def save_user_preference(preference: UserPreference) -> None:
    """保存用户偏好"""
    get_response_adapter().save_user_preference(preference)


def adapt_response(
    user_id: str, content: str, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """适配响应"""
    return get_response_adapter().adapt_response(user_id, content, metadata)


def learn_from_feedback(
    user_id: str, feedback: str, context: dict[str, Any] | None = None
) -> None:
    """从反馈中学习"""
    get_response_adapter().learn_from_feedback(user_id, feedback, context)
