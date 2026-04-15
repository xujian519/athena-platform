"""
中间件和技能系统测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_middleware():
    """测试中间件系统"""
    print("\n" + "="*50)
    print("测试中间件系统")
    print("="*50)

    try:
        import sys
        from pathlib import Path

        # 添加 services/api-gateway/src 到路径
        api_gateway_src = Path(__file__).parent.parent / "services" / "api-gateway" / "src"
        if str(api_gateway_src) not in sys.path:
            sys.path.insert(0, str(api_gateway_src))

        from middleware.base import (
            Middleware,
            Pipeline,
        )
        print("✓ 中间件基类导入成功")

        # 创建测试中间件
        class TestMiddleware(Middleware):
            async def process(self, ctx, call_next):
                ctx.set("test", "value")
                return await call_next(ctx)

        # 创建管道
        pipeline = Pipeline()
        pipeline.add(TestMiddleware(name="test"))
        print(f"✓ 管道创建成功: {pipeline}")

        # 列出中间件
        middlewares = pipeline.list()
        print(f"✓ 中间件列表: {middlewares}")

        return True

    except Exception as e:
        print(f"✗ 中间件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_skills():
    """测试技能系统"""
    print("\n" + "="*50)
    print("测试技能系统")
    print("="*50)

    try:
        from core.skills import (
            SkillCategory,
            SkillExecutor,
            SkillManager,
            SkillMetadata,
            SkillRegistry,
        )
        print("✓ 技能系统导入成功")

        # 创建技能注册中心
        registry = SkillRegistry()
        SkillManager(registry=registry)
        executor = SkillExecutor(registry=registry)
        print("✓ 技能管理器创建成功")

        # 创建测试技能
        from core.skills import FunctionSkill

        metadata = SkillMetadata(
            name="test_skill",
            display_name="测试技能",
            description="这是一个测试技能",
            category=SkillCategory.CUSTOM,
        )

        async def test_func(text: str) -> dict:
            return {"result": f"处理: {text}"}

        skill = FunctionSkill(metadata, test_func)
        print("✓ 测试技能创建成功")

        # 注册技能
        await registry.register(skill)
        print("✓ 技能注册成功")

        # 执行技能
        result = await executor.execute("test_skill", text="Hello")
        print(f"✓ 技能执行成功: {result.data}")

        # 获取统计信息
        stats = registry.get_statistics()
        print(f"✓ 注册中心统计: {stats}")

        return True

    except Exception as e:
        print(f"✗ 技能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hello_world_skill():
    """测试 Hello World 技能"""
    print("\n" + "="*50)
    print("测试 Hello World 技能")
    print("="*50)

    try:
        from pathlib import Path

        from core.skills import SkillExecutor, SkillManager, SkillRegistry

        # 创建技能管理器
        registry = SkillRegistry()
        manager = SkillManager(registry=registry)
        executor = SkillExecutor(registry=registry)

        # 加载技能
        skills_dir = Path(__file__).parent.parent / "skills"
        count = await manager.registry.load_from_directory(skills_dir)
        print(f"✓ 加载了 {count} 个技能")

        # 列出可用技能
        available = registry.list_enabled()
        print(f"✓ 可用技能: {available}")

        # 执行 Hello World 技能
        if "hello_world" in available:
            result = await executor.execute("hello_world", name="Athena")
            print(f"✓ Hello World 执行结果: {result.data}")

        return True

    except Exception as e:
        print(f"✗ Hello World 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_skill_mixin():
    """测试技能混入类"""
    print("\n" + "="*50)
    print("测试智能体技能集成")
    print("="*50)

    try:
        from core.agents.skill_mixin import SkillMixin

        # 创建一个简单的测试智能体
        class TestAgent(SkillMixin):
            def __init__(self):
                super().__init__()
                self._initialized = False

            async def initialize(self):
                self._initialized = True
                await self.setup_skills()

        agent = TestAgent()
        await agent.initialize()
        print("✓ 技能化智能体创建成功")

        # 列出可用技能
        skills = agent.list_available_skills()
        print(f"✓ 智能体可用技能: {skills}")

        # 使用技能
        if "hello_world" in skills:
            result = await agent.use_skill("hello_world", name="Agent")
            print(f"✓ 智能体使用技能结果: {result.data}")

        return True

    except Exception as e:
        print(f"✗ 技能混入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Athena 中间件与技能系统测试")
    print("="*60)

    results = {
        "中间件系统": await test_middleware(),
        "技能系统": await test_skills(),
        "Hello World 技能": await test_hello_world_skill(),
        "智能体集成": await test_skill_mixin(),
    }

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
