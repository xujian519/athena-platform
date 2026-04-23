#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务自动释放功能 - 自动化测试
Automated Test for Service Auto-Release Feature

无需交互，直接运行所有测试

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.session.service_session_manager import (
    ServiceType,
    get_service_session_manager,
)
from core.session.auto_release_config import get_auto_release_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestResults:
    """测试结果收集器"""

    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0

    def add_result(self, test_name: str, passed: bool, message: str = ""):
        """添加测试结果"""
        self.tests.append({
            'name': test_name,
            'passed': passed,
            'message': message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("📊 测试结果摘要")
        print("=" * 60)
        print(f"总测试数: {len(self.tests)}")
        print(f"✅ 通过: {self.passed}")
        print(f"❌ 失败: {self.failed}")
        print(f"成功率: {self.passed / len(self.tests) * 100:.1f}%")
        print("=" * 60)

        if self.failed > 0:
            print("\n❌ 失败的测试:")
            for test in self.tests:
                if not test['passed']:
                    print(f"  - {test['name']}: {test['message']}")


async def test_config_loading(results: TestResults):
    """测试配置加载"""
    print("\n🧪 测试1: 配置加载")
    print("-" * 60)

    try:
        # 测试默认配置
        config = get_auto_release_config()

        enabled = config.is_enabled()
        timeout = config.get_idle_timeout()
        interval = config.get_cleanup_interval()

        print(f"  ✅ 启用状态: {enabled}")
        print(f"  ✅ 超时时间: {timeout}秒")
        print(f"  ✅ 清理间隔: {interval}秒")

        # 验证默认值
        assert enabled == True, "默认应该启用"
        assert timeout == 3600, "默认超时应该是3600秒"
        assert interval == 300, "默认清理间隔应该是300秒"

        results.add_result("配置加载", True)
        print("  ✅ 配置加载测试通过")

    except Exception as e:
        results.add_result("配置加载", False, str(e))
        print(f"  ❌ 配置加载测试失败: {e}")


async def test_session_registration(results: TestResults):
    """测试会话注册"""
    print("\n🧪 测试2: 会话注册")
    print("-" * 60)

    try:
        # 创建管理器
        manager = get_service_session_manager(
            idle_timeout=10,  # 10秒超时
            cleanup_interval=5
        )

        # 注册测试服务
        import os
        session = manager.register_session(
            process_id=os.getpid(),
            service_type=ServiceType.AGENT,
            service_name="测试服务",
            auto_stop=True
        )

        print(f"  ✅ 会话已注册: {session.service_name}")
        print(f"  ✅ 进程ID: {session.process_id}")
        print(f"  ✅ 内存使用: {session.memory_mb:.1f}MB")

        # 验证会话属性
        assert session.service_name == "测试服务"
        assert session.process_id == os.getpid()
        assert session.auto_stop == True

        results.add_result("会话注册", True)
        print("  ✅ 会话注册测试通过")

    except Exception as e:
        results.add_result("会话注册", False, str(e))
        print(f"  ❌ 会话注册测试失败: {e}")


async def test_activity_update(results: TestResults):
    """测试活动更新"""
    print("\n🧪 测试3: 活动更新")
    print("-" * 60)

    try:
        manager = get_service_session_manager(
            idle_timeout=10,
            cleanup_interval=5
        )

        import os
        session = manager.register_session(
            process_id=os.getpid(),
            service_type=ServiceType.AGENT,
            service_name="测试服务",
            auto_stop=True
        )

        # 记录初始空闲时间
        initial_idle = session.idle_time_seconds
        print(f"  ✅ 初始空闲时间: {initial_idle:.1f}秒")

        # 等待1秒
        await asyncio.sleep(1)

        # 更新活动
        manager.update_activity(session.process_id)
        updated_idle = session.idle_time_seconds
        print(f"  ✅ 更新后空闲时间: {updated_idle:.1f}秒")

        # 验证活动时间被重置
        assert updated_idle < initial_idle, "活动时间应该被重置"

        results.add_result("活动更新", True)
        print("  ✅ 活动更新测试通过")

    except Exception as e:
        results.add_result("活动更新", False, str(e))
        print(f"  ❌ 活动更新测试失败: {e}")


async def test_session_expiration(results: TestResults):
    """测试会话过期"""
    print("\n🧪 测试4: 会话过期检测")
    print("-" * 60)

    try:
        manager = get_service_session_manager(
            idle_timeout=2,  # 2秒超时
            cleanup_interval=1
        )

        import os
        # 注册测试会话
        session = manager.register_session(
            process_id=os.getpid(),
            service_type=ServiceType.AGENT,
            service_name="测试服务",
            auto_stop=True
        )

        print(f"  ✅ 会话已注册: PID {os.getpid()}")

        # 立即检查（应该未过期）
        idle_time_0 = session.idle_time_seconds
        is_expired_0 = session.is_expired(2)
        print(f"  ✅ 初始空闲时间: {idle_time_0:.1f}秒, 是否过期: {is_expired_0}")

        # 等待1秒后检查
        await asyncio.sleep(1)
        idle_time_1 = session.idle_time_seconds
        is_expired_1 = session.is_expired(2)
        print(f"  ✅ 1秒后空闲时间: {idle_time_1:.1f}秒, 是否过期: {is_expired_1}")

        # 等待超过超时时间（总共3秒）
        await asyncio.sleep(2)
        idle_time_3 = session.idle_time_seconds
        is_expired_3 = session.is_expired(2)
        print(f"  ✅ 3秒后空闲时间: {idle_time_3:.1f}秒, 是否过期: {is_expired_3}")

        # 验证空闲时间增长
        assert idle_time_3 > idle_time_1, "空闲时间应该增长"

        # 验证过期状态（3秒后应该过期，因为超时是2秒）
        assert is_expired_3 == True, f"会话应该已过期（空闲{idle_time_3:.1f}秒 > 2秒超时）"

        results.add_result("会话过期检测", True)
        print("  ✅ 会话过期检测测试通过")

    except Exception as e:
        results.add_result("会话过期检测", False, str(e))
        print(f"  ❌ 会话过期检测测试失败: {e}")


async def test_service_config(results: TestResults):
    """测试服务配置"""
    print("\n🧪 测试5: 服务配置")
    print("-" * 60)

    try:
        config = get_auto_release_config(
            preset='testing'  # 使用测试预设
        )

        # 测试全局配置
        global_timeout = config.get_idle_timeout()
        print(f"  ✅ 全局超时时间: {global_timeout}秒")

        # 测试服务特定配置
        if hasattr(config, 'get_service_config'):
            xiaona_auto_stop = config.should_auto_stop('xiaona')
            xiaonuo_auto_stop = config.should_auto_stop('xiaonuo')

            print(f"  ✅ 小娜自动停止: {xiaona_auto_stop}")
            print(f"  ✅ 小诺自动停止: {xiaonuo_auto_stop}")

        results.add_result("服务配置", True)
        print("  ✅ 服务配置测试通过")

    except Exception as e:
        results.add_result("服务配置", False, str(e))
        print(f"  ❌ 服务配置测试失败: {e}")


async def test_statistics(results: TestResults):
    """测试统计信息"""
    print("\n🧪 测试6: 统计信息")
    print("-" * 60)

    try:
        manager = get_service_session_manager(
            idle_timeout=10,
            cleanup_interval=5
        )

        import os
        # 注册多个服务
        services = [
            ("Gateway", ServiceType.GATEWAY, False),
            ("小诺", ServiceType.XIAONUO, False),
            ("小娜", ServiceType.XIAONA, True),
            ("缓存", ServiceType.CACHE, True),
        ]

        for name, service_type, auto_stop in services:
            manager.register_session(
                process_id=os.getpid() + len(services),
                service_type=service_type,
                service_name=name,
                auto_stop=auto_stop
            )

        # 获取统计信息
        stats = manager.get_stats()

        print(f"  ✅ 活动会话数: {stats['active_sessions']}")
        print(f"  ✅ 总内存使用: {stats['current_memory_usage_mb']:.1f}MB")
        print(f"  ✅ 会话详情数: {len(stats['sessions'])}")

        # 验证统计信息
        assert stats['active_sessions'] >= 0
        assert 'current_memory_usage_mb' in stats

        results.add_result("统计信息", True)
        print("  ✅ 统计信息测试通过")

    except Exception as e:
        results.add_result("统计信息", False, str(e))
        print(f"  ❌ 统计信息测试失败: {e}")


async def test_preset_configs(results: TestResults):
    """测试预设配置"""
    print("\n🧪 测试7: 预设配置")
    print("-" * 60)

    try:
        presets = ['development', 'testing', 'production', 'long_running']

        for preset in presets:
            config = get_auto_release_config(preset=preset)
            timeout = config.get_idle_timeout()
            print(f"  ✅ {preset:15} - 超时: {timeout:4}秒")

        results.add_result("预设配置", True)
        print("  ✅ 预设配置测试通过")

    except Exception as e:
        results.add_result("预设配置", False, str(e))
        print(f"  ❌ 预设配置测试失败: {e}")


async def run_all_tests():
    """运行所有测试"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║          Athena服务自动释放功能 - 自动化测试                        ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    results = TestResults()

    # 运行所有测试
    await test_config_loading(results)
    await test_session_registration(results)
    await test_activity_update(results)
    await test_session_expiration(results)
    await test_service_config(results)
    await test_statistics(results)
    await test_preset_configs(results)

    # 打印结果摘要
    results.print_summary()

    # 返回测试是否全部通过
    return results.failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ 测试被中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
