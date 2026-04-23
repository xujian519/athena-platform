"""
Hello World 技能实现

一个简单的示例技能，演示如何实现 Athena 技能。
"""

from core.skills import Skill, SkillResult


class Skill(Skill):
    """Hello World 技能

    向指定目标发送问候消息。
    """

    async def execute(self, **kwargs) -> SkillResult:
        """执行技能

        Args:
            name: 要问候的对象名称（必需）
            greeting: 问候语（可选，默认 "Hello"）

        Returns:
            SkillResult: 包含问候消息的结果
        """
        # 获取参数
        name = kwargs.get("name", "World")
        greeting = kwargs.get("greeting", "Hello")

        # 验证参数
        await self.validate(**kwargs)

        # 生成问候消息
        message = f"{greeting}, {name}!"

        return SkillResult(
            success=True,
            data={
                "message": message,
                "greeting": greeting,
                "name": name,
            },
            metadata={
                "skill": "hello_world",
                "version": "1.0.0",
            },
        )
