#!/usr/bin/env python3
"""
检查 Enhanced Xiaonuo 依赖模块
Check Enhanced Xiaonuo Dependencies

作者: Athena AI System
创建时间: 2026-04-18
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """检查依赖模块"""
    print("=" * 80)
    print("🔍 Enhanced Xiaonuo 依赖检查".center(80))
    print("=" * 80)

    # 定义需要检查的模块
    dependencies = [
        ("core.async_main", "异步主函数装饰器"),
        ("core.logging_config", "日志配置"),
        ("core.agents.xiaonuo.unified_xiaonuo_agent", "统一小诺智能体"),
        ("core.memory.unified_agent_memory_system", "统一记忆系统"),
        ("core.intelligence.reflection_engine_v5", "反思引擎v5"),
        ("core.learning.enhanced_meta_learning", "增强元学习引擎"),
        ("core.learning.memory_consolidation_system", "记忆整合系统"),
    ]

    print("\n📋 依赖模块检查:\n")

    missing = []
    existing = []

    for module_name, description in dependencies:
        try:
            module = __import__(module_name, fromlist=[""])
            print(f"✅ {description:30s} ({module_name})")
            existing.append(module_name)
        except ImportError as e:
            print(f"❌ {description:30s} ({module_name})")
            print(f"   错误: {e}")
            missing.append((module_name, description, str(e)))

    # 统计
    print("\n" + "-" * 80)
    print(f"📊 统计:")
    print(f"  ✅ 已存在: {len(existing)} 个")
    print(f"  ❌ 缺失: {len(missing)} 个")

    # 详细分析
    if missing:
        print(f"\n⚠️  缺失模块详情:")
        for module_name, description, error in missing:
            print(f"\n  模块: {description} ({module_name})")
            print(f"  错误: {error}")

            # 提供解决方案
            print(f"  💡 解决方案:")

            if "unified_agent_memory_system" in module_name:
                print(f"     - 检查 core/memory/ 目录")
                print(f"     - 可能需要从 production 复制或创建简化版本")
            elif "enhanced_meta_learning" in module_name:
                print(f"     - 检查 core/learning/ 目录")
                print(f"     - 可能需要创建基础实现")
            elif "memory_consolidation_system" in module_name:
                print(f"     - 检查 core/learning/ 目录")
                print(f"     - 可能需要创建基础实现")

    # 测试实际导入
    print("\n" + "-" * 80)
    print("🔍 测试 Enhanced Xiaonuo 实际导入:\n")

    try:
        from core.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo
        print("✅ Enhanced Xiaonuo 导入成功!")
        print(f"   - 类名: {EnhancedXiaonuo.__name__}")
        print(f"   - 模块: {EnhancedXiaonuo.__module__}")

        # 检查类属性
        print(f"\n📋 类属性:")
        if hasattr(EnhancedXiaonuo, '__init__'):
            print(f"   ✅ __init__ 方法")
        if hasattr(EnhancedXiaonuo, 'reflection_engine_v5'):
            print(f"   ✅ reflection_engine_v5 属性")

    except ImportError as e:
        print(f"❌ Enhanced Xiaonuo 导入失败: {e}")

        # 提供详细的修复建议
        print(f"\n💡 修复建议:")

        if missing:
            print(f"\n1. 创建缺失的依赖模块:")
            for module_name, description, _ in missing:
                print(f"   - {description}")

            print(f"\n2. 或者在 enhanced_xiaonuo.py 中添加备用实现:")
            print(f"   ```python")
            print(f"   # 添加备用类")
            print(f"   try:")
            print(f"       from core.memory.unified_agent_memory_system import ...")
            print(f"   except ImportError:")
            print(f"       class UnifiedAgentMemorySystem:")
            print(f"           # 备用实现")
            print(f"           pass")
            print(f"   ```")

            print(f"\n3. 或者简化 enhanced_xiaonuo.py:")
            print(f"   ```python")
            print(f"   # 临时注释掉非核心依赖")
            print(f"   # from core.memory... import ...")
            print(f"   ```")

    print("\n" + "=" * 80)

    return len(missing) == 0


def create_stub_modules():
    """创建备用模块（如果需要）"""
    print("\n🔧 是否创建备用模块? (y/n): ", end="")

    try:
        response = input().strip().lower()
        if response not in ['y', 'yes']:
            print("跳过创建备用模块")
            return False
    except (EOFError, KeyboardInterrupt):
        print("\n跳过创建备用模块")
        return False

    print("\n🔨 创建备用模块...")

    # 创建备用模块的目录和文件
    stubs = {
        "core/memory/unified_agent_memory_system.py": """
#!/usr/bin/env python3
\"\"\"统一记忆系统 - 备用实现\"\"\"

class UnifiedAgentMemorySystem:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def store(self, key, value):
        pass

    async def retrieve(self, key):
        return None
""",
        "core/learning/enhanced_meta_learning.py": """
#!/usr/bin/env python3
\"\"\"增强元学习引擎 - 备用实现\"\"\"

class EnhancedMetaLearningEngine:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def learn(self, experience):
        pass
""",
        "core/learning/memory_consolidation_system.py": """
#!/usr/bin/env python3
\"\"\"记忆整合系统 - 备用实现\"\"\"

class MemoryConsolidationSystem:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def consolidate(self):
        pass
""",
    }

    created = 0
    for file_path, content in stubs.items():
        full_path = project_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if not full_path.exists():
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 创建: {file_path}")
            created += 1
        else:
            print(f"⚠️  已存在: {file_path}")

    if created > 0:
        print(f"\n✅ 成功创建 {created} 个备用模块")
        print("💡 现在可以尝试导入 Enhanced Xiaonuo")
        return True
    else:
        print("\n⚠️  所有模块都已存在")
        return False


if __name__ == "__main__":
    # 检查依赖
    all_exists = check_dependencies()

    if not all_exists:
        print("\n" + "=" * 80)
        print("💡 检测到缺失模块")
        print("=" * 80)
        print("\n您可以:")
        print("1. 手动创建缺失的模块")
        print("2. 运行此脚本并选择创建备用模块")
        print("3. 修改 enhanced_xiaonuo.py 以适应现有模块")
        print("\n是否现在创建备用模块?")

        create_stub_modules()

    print("\n🏁 检查完成!")
    print("\n下一步:")
    print("1. 如果创建了备用模块，再次运行此脚本验证")
    print("2. 或者运行修复脚本:")
    print("   bash scripts/fix_known_limitations.sh")
    print("3. 最后运行验证脚本:")
    print("   python3 tests/evaluation_reflection_final_verification.py")
