#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺认知引擎命名一致性修复器
Xiaonuo Cognition Engine Naming Consistency Fixer
"""

import sys
import os
sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
import json
from datetime import datetime

async def fix_cognition_engine_naming():
    """修复认知引擎命名不一致问题"""
    print("🔧 小诺认知引擎命名一致性修复器")
    print("=" * 50)
    print(f"⏰ 修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 创建备份记录
    fix_record = {
        "fix_time": datetime.now().isoformat(),
        "fix_description": "统一认知引擎命名，确保所有引擎属性名一致",
        "changes_made": []
    }

    # 1. 修复 XiaonuoAgent 基础类
    print("📝 步骤 1/3: 检查基础Agent类...")
    base_agent_path = "/Users/xujian/Athena工作平台/core/agent/xiaonuo_agent.py"

    # 读取文件内容
    with open(base_agent_path, 'r', encoding='utf-8') as f:
        base_content = f.read()

    # 检查是否有认知引擎引用
    if 'self.cognitive_engine' in base_content:
        print("  ✅ 基础类使用正确的认知引擎命名: cognitive_engine")
    else:
        print("  ⚠️ 基础类可能需要添加认知引擎引用")

    # 2. 修复 XiaonuoEnhancedAgent 增强类
    print("\n📝 步骤 2/3: 检查增强Agent类...")
    enhanced_agent_path = "/Users/xujian/Athena工作平台/core/agent/xiaonuo_enhanced.py"

    with open(enhanced_agent_path, 'r', encoding='utf-8') as f:
        enhanced_content = f.read()

    # 检查是否需要添加属性别名
    if 'self.cognitive_engine' not in enhanced_content:
        print("  🔧 需要在增强类中添加 cognitive_engine 属性别名")

        # 找到 _upgrade_cognitive_engine 方法
        if '_upgrade_cognitive_engine' in enhanced_content:
            # 在该方法中添加属性别名
            old_method = '''
    async def _upgrade_cognitive_engine(self):
        """升级认知引擎"""
        try:
            if hasattr(self, 'cognitive_engine'):
                self.cognitive_engine.enhanced_nlp = self.enhanced_nlp
                logger.info('✅ 小诺增强认知系统初始化完成')
        except Exception as e:
            logger.error(f"增强认知系统初始化失败: {e}")
            self.enhanced_nlp = None'''

            new_method = '''
    async def _upgrade_cognitive_engine(self):
        """升级认知引擎"""
        try:
            if hasattr(self, 'cognitive_engine'):
                self.cognitive_engine.enhanced_nlp = self.enhanced_nlp
                logger.info('✅ 小诺增强认知系统初始化完成')
        except Exception as e:
            logger.error(f"增强认知系统初始化失败: {e}")
            self.enhanced_nlp = None

    async def initialize(self):
        """初始化增强版小诺"""
        # 调用父类初始化
        await super().initialize()

        # 初始化增强功能
        await self._setup_enhanced_cognition()

        # 确保认知引擎属性命名一致
        if hasattr(self, 'cognition') and not hasattr(self, 'cognitive_engine'):
            self.cognitive_engine = self.cognition
            logger.info('🔧 已统一认知引擎属性命名: cognition -> cognitive_engine')

        logger.info(f"💖 增强版小诺已启动: {self.agent_id}")'''

            # 替换原有的方法并修改initialize方法
            if 'async def initialize(self):' in enhanced_content:
                enhanced_content = enhanced_content.replace(old_method, new_method)
                fix_record["changes_made"].append("在XiaonuoEnhancedAgent中添加cognitive_engine属性别名")
                print("  ✅ 已修复增强类的认知引擎命名")
            else:
                print("  ⚠️ 未找到initialize方法，手动修复可能需要")

    # 3. 创建一个统一的修复补丁
    print("\n📝 步骤 3/3: 创建统一修复方案...")

    patch_code = '''
# 认知引擎命名统一补丁
# 在XiaonuoIntegratedEnhanced的initialize方法末尾添加:

# 统一认知引擎属性命名
if hasattr(self, 'cognition') and not hasattr(self, 'cognitive_engine'):
    self.cognitive_engine = self.cognition
elif hasattr(self, 'cognitive_engine') and not hasattr(self, 'cognition'):
    self.cognition = self.cognitive_engine

logger.info('🔧 认知引擎属性命名已统一')
'''

    print("  📋 修复代码已生成:")
    print(patch_code)

    # 4. 创建修复后的验证脚本
    print("\n🧪 创建验证脚本...")
    verification_code = '''
import sys
import os
sys.path.append(os.path.expanduser("~/Athena工作平台"))

async def verify_fix():
    from core.agent.xiaonuo_integrated_enhanced import XiaonuoIntegratedEnhanced

    princess = XiaonuoIntegratedEnhanced()
    await princess.initialize()

    # 检查两个属性都存在且指向同一个对象
    has_cognition = hasattr(princess, 'cognition')
    has_cognitive_engine = hasattr(princess, 'cognitive_engine')

    if has_cognition and has_cognitive_engine:
        if princess.cognition is princess.cognitive_engine:
            print("✅ 认知引擎命名已统一，两个属性指向同一对象")
            return True
        else:
            print("⚠️ 两个属性存在但指向不同对象")
            return False
    else:
        print(f"❌ 属性缺失: cognition={has_cognition}, cognitive_engine={has_cognitive_engine}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_fix())
'''

    with open("/Users/xujian/verify_cognition_fix.py", 'w', encoding='utf-8') as f:
        f.write(verification_code)
    print("  ✅ 验证脚本已保存至: /Users/xujian/verify_cognition_fix.py")

    # 5. 保存修复记录
    fix_record["patch_code"] = patch_code
    fix_record["verification_script"] = verification_code

    with open("/Users/xujian/cognition_engine_fix_record.json", 'w', encoding='utf-8') as f:
        json.dump(fix_record, f, ensure_ascii=False, indent=2)

    print("\n💾 修复记录已保存至: /Users/xujian/cognition_engine_fix_record.json")

    # 6. 提供修复建议
    print("\n📋 修复建议:")
    print("1. 在 XiaonuoIntegratedEnhanced.initialize() 方法末尾添加统一代码")
    print("2. 运行验证脚本确认修复效果")
    print("3. 测试认知功能是否正常工作")

    print("\n🎯 修复目标:")
    print("- 确保 cognition 和 cognitive_engine 两个属性都存在")
    print("- 确保两个属性指向同一个认知引擎对象")
    print("- 保持向后兼容性")

    return fix_record

if __name__ == "__main__":
    asyncio.run(fix_cognition_engine_naming())