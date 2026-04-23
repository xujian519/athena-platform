"""
专利撰写代理提示词配置

提供优化的提示词模板，支持Few-shot学习和CoT推理。
"""

from typing import Any, Optional


class PatentDraftingPrompts:
    """专利撰写代理提示词配置"""

    # 提示词模板配置（简化版，避免重复）
    PROMPTS_CONFIG: Optional[dict[str, dict[str, Any] = {]]

        "comprehensive": {
            "system_prompt": """你是一位专业的专利撰写专家，具备深厚的专利法知识和丰富的撰写经验。

请以专业、严谨的态度进行工作。
输出必须是严格的JSON格式，不要添加任何额外的文字说明。
""",
            "user_template": "请按照标准流程完成专利申请文件的撰写工作。",
        },
    }

    @classmethod
    def get_prompt(cls, task_type: str = "comprehensive") -> dict[str, Any]:
        """获取提示词配置"""
        return cls.PROMPTS_CONFIG.get(task_type, cls.PROMPTS_CONFIG["comprehensive"])

    @classmethod
    def format_user_prompt(cls, task_type: str, **kwargs) -> str:
        """格式化用户提示词"""
        config = cls.get_prompt(task_type)
        template = config.get("user_template", "")
        return template.format(**kwargs) if template else template
