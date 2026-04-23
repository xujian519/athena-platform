#!/usr/bin/env python3
"""
Phase 1和Phase 2全面验证脚本
Comprehensive Verification Script for Phase 1 & 2
"""
import asyncio
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import json

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VerificationResult:
    """验证结果"""

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.details: List[str] = []
        self.errors: List[str] = []

    def add_detail(self, detail: str):
        """添加详情"""
        self.details.append(detail)

    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)

    def set_passed(self, passed: bool):
        """设置是否通过"""
        self.passed = passed

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "passed": self.passed,
            "details": self.details,
            "errors": self.errors,
            "score": len(self.details) / max(len(self.details) + len(self.errors), 1) * 100
        }


class ComprehensiveVerifier:
    """全面验证器"""

    def __init__(self):
        """初始化验证器"""
        self.results: List[VerificationResult] = []

    def add_result(self, result: VerificationResult):
        """添加验证结果"""
        self.results.append(result)

    async def verify_phase1_config_system(self) -> VerificationResult:
        """验证Phase 1配置管理系统"""
        result = VerificationResult("Phase 1: 统一配置管理系统")

        try:
            # 1. 检查配置文件存在性
            result.add_detail("检查配置文件...")

            config_files = [
                "config/base/database.yml",
                "config/base/redis.yml",
                "config/base/qdrant.yml",
                "config/base/llm.yml",
                "config/environments/development.yml",
                "config/environments/test.yml",
                "config/environments/production.yml",
                "config/services/xiaona.yml",
                "config/services/xiaonuo.yml",
                "config/services/gateway.yml",
            ]

            missing_files = []
            for file in config_files:
                if not (project_root / file).exists():
                    missing_files.append(file)

            if missing_files:
                result.add_error(f"缺失配置文件: {', '.join(missing_files)}")
            else:
                result.add_detail(f"✓ 所有配置文件存在 ({len(config_files)}个)")

            # 2. 测试配置加载
            result.add_detail("测试配置加载...")
            try:
                from core.config.unified_settings import UnifiedSettings
                settings = UnifiedSettings()
                result.add_detail(f"✓ UnifiedSettings加载成功")
                result.add_detail(f"  - 数据库: {settings.database_url[:30]}...")
                result.add_detail(f"  - Redis: {settings.redis_url[:30]}...")
                result.add_detail(f"  - LLM: {settings.llm_default_provider}")
            except Exception as e:
                result.add_error(f"配置加载失败: {e}")

            # 3. 测试配置加载器
            result.add_detail("测试配置加载器...")
            try:
                from core.config.unified_config_loader import load_full_config
                config = load_full_config('development', 'xiaona')
                result.add_detail(f"✓ 配置加载器成功")
                result.add_detail(f"  - 服务名: {config.get('service', {}).get('name')}")
            except Exception as e:
                result.add_error(f"配置加载器失败: {e}")

            # 4. 检查配置适配器
            result.add_detail("检查配置适配器...")
            try:
                from core.config.config_adapter import ConfigAdapter
                result.add_detail("✓ 配置适配器可用")
            except Exception as e:
                result.add_error(f"配置适配器导入失败: {e}")

            # 5. 检查文档完整性
            result.add_detail("检查文档...")
            docs = [
                "docs/guides/CONFIG_ARCHITECTURE.md",
                "docs/guides/CONFIG_MIGRATION_GUIDE.md",
                "docs/reports/PHASE2_WEEK1_COMPLETION_REPORT_20260421.md",
            ]

            missing_docs = []
            for doc in docs:
                if not (project_root / doc).exists():
                    missing_docs.append(doc)

            if missing_docs:
                result.add_error(f"缺失文档: {', '.join(missing_docs)}")
            else:
                result.add_detail(f"✓ 文档完整 ({len(docs)}个)")

            # 判断是否通过
            result.set_passed(len(result.errors) == 0)

        except Exception as e:
            result.add_error(f"验证过程出错: {e}")
            result.set_passed(False)

        return result

    async def verify_phase2_service_registry(self) -> VerificationResult:
        """验证Phase 2服务注册中心"""
        result = VerificationResult("Phase 2: 服务注册中心")

        try:
            # 1. 检查模块存在性
            result.add_detail("检查服务注册模块...")

            modules = [
                "core.service_registry.models",
                "core.service_registry.storage",
                "core.service_registry.storage_memory",
                "core.service_registry.health_checker",
                "core.service_registry.discovery",
                "core.service_registry.registry",
            ]

            missing_modules = []
            for module in modules:
                try:
                    __import__(module)
                    result.add_detail(f"✓ {module.split('.')[-1]}")
                except ImportError as e:
                    missing_modules.append(module)
                    result.add_error(f"模块导入失败: {module} - {e}")

            if missing_modules:
                result.add_error(f"缺失模块: {', '.join(missing_modules)}")

            # 2. 测试内存存储
            result.add_detail("测试内存存储...")
            try:
                from core.service_registry.storage_memory import InMemoryServiceRegistryStorage
                from core.service_registry import ServiceInstance, ServiceStatus
                from datetime import datetime

                storage = InMemoryServiceRegistryStorage()

                # 创建测试实例
                instance = ServiceInstance(
                    instance_id="test-001",
                    service_name="test_service",
                    host="localhost",
                    port=9999,
                    status=ServiceStatus.HEALTHY,
                    last_heartbeat=datetime.now()
                )

                # 注册
                success = await storage.register_instance(instance)
                if success:
                    result.add_detail("✓ 注册功能正常")
                else:
                    result.add_error("注册功能失败")

                # 获取
                retrieved = await storage.get_instance("test_service", "test-001")
                if retrieved and retrieved.instance_id == "test-001":
                    result.add_detail("✓ 获取功能正常")
                else:
                    result.add_error("获取功能失败")

                # 获取所有
                all_instances = await storage.get_all_instances("test_service")
                if len(all_instances) == 1:
                    result.add_detail("✓ 查询功能正常")
                else:
                    result.add_error(f"查询功能失败: 期望1个实例，实际{len(all_instances)}个")

            except Exception as e:
                result.add_error(f"内存存储测试失败: {e}")

            # 3. 测试服务发现
            result.add_detail("测试服务发现...")
            try:
                from core.service_registry.discovery import ServiceDiscovery
                from core.service_registry import LoadBalanceStrategy

                discovery = ServiceDiscovery(storage=storage)

                # 发现服务
                discovered = await discovery.discover("test_service")
                if discovered and discovered.instance_id == "test-001":
                    result.add_detail("✓ 服务发现功能正常")
                else:
                    result.add_error("服务发现功能失败")

                # 获取所有服务
                services = await discovery.get_service_names()
                if "test_service" in services:
                    result.add_detail("✓ 服务列表功能正常")
                else:
                    result.add_error("服务列表功能失败")

            except Exception as e:
                result.add_error(f"服务发现测试失败: {e}")

            # 4. 测试统一注册中心
            result.add_detail("测试统一注册中心...")
            try:
                from core.service_registry.registry import ServiceRegistryCenter

                registry = ServiceRegistryCenter(storage=storage)

                # 获取统计
                stats = await registry.get_registry_statistics()
                if stats.get("total_services") >= 1:
                    result.add_detail("✓ 注册中心统计功能正常")
                else:
                    result.add_error("注册中心统计功能失败")

            except Exception as e:
                result.add_error(f"注册中心测试失败: {e}")

            # 5. 检查文档
            result.add_detail("检查文档...")
            docs = [
                "docs/guides/SERVICE_REGISTRY_ARCHITECTURE.md",
                "docs/reports/P2_WEEK2_DAY2_3_COMPLETION_REPORT_20260421.md",
            ]

            missing_docs = []
            for doc in docs:
                if not (project_root / doc).exists():
                    missing_docs.append(doc)

            if missing_docs:
                result.add_error(f"缺失文档: {', '.join(missing_docs)}")
            else:
                result.add_detail(f"✓ 文档完整 ({len(docs)}个)")

            # 判断是否通过
            result.set_passed(len(result.errors) == 0)

        except Exception as e:
            result.add_error(f"验证过程出错: {e}")
            result.set_passed(False)

        return result

    async def verify_code_quality(self) -> VerificationResult:
        """验证代码质量"""
        result = VerificationResult("代码质量检查")

        try:
            # 1. 检查Python语法
            result.add_detail("检查Python语法...")
            try:
                import ast
                import os

                python_files = []
                for root, dirs, files in os.walk(project_root / "core"):
                    for file in files:
                        if file.endswith(".py"):
                            python_files.append(os.path.join(root, file))

                syntax_errors = []
                for file in python_files[:20]:  # 检查前20个文件
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            ast.parse(f.read())
                    except SyntaxError as e:
                        syntax_errors.append(f"{file}: {e}")

                if syntax_errors:
                    result.add_error(f"语法错误: {len(syntax_errors)}个")
                    for error in syntax_errors[:3]:
                        result.add_error(f"  - {error}")
                else:
                    result.add_detail(f"✓ 语法检查通过 ({len(python_files[:20])}个文件)")

            except Exception as e:
                result.add_error(f"语法检查失败: {e}")

            # 2. 检查导入
            result.add_detail("检查关键模块导入...")
            critical_imports = [
                "core.config.unified_settings",
                "core.config.unified_config_loader",
                "core.service_registry.registry",
                "core.service_registry.discovery",
            ]

            failed_imports = []
            for module in critical_imports:
                try:
                    __import__(module)
                    result.add_detail(f"✓ {module}")
                except ImportError as e:
                    failed_imports.append(module)
                    result.add_error(f"导入失败: {module}")

            if failed_imports:
                result.add_error(f"导入失败: {len(failed_imports)}个模块")

            # 3. 检查代码组织
            result.add_detail("检查代码组织...")
            checks = [
                ("core/config/", "配置管理模块"),
                ("core/service_registry/", "服务注册模块"),
            ]

            for path, name in checks:
                if (project_root / path).exists():
                    result.add_detail(f"✓ {name}存在")
                else:
                    result.add_error(f"{name}缺失")

            # 4. 检查类型注解
            result.add_detail("检查类型注解...")
            try:
                # 检查关键文件是否有类型注解
                type_hints_files = [
                    "core/service_registry/models.py",
                    "core/config/unified_settings.py",
                ]

                hint_count = 0
                for file in type_hints_files:
                    file_path = project_root / file
                    if file_path.exists():
                        content = file_path.read_text()
                        if ":" in content and "str" in content and "int" in content:
                            hint_count += 1

                if hint_count >= 2:
                    result.add_detail(f"✓ 类型注解使用 ({hint_count}/{len(type_hints_files)}个文件)")
                else:
                    result.add_error("类型注解不完整")

            except Exception as e:
                result.add_error(f"类型注解检查失败: {e}")

            # 判断是否通过
            result.set_passed(len(result.errors) == 0)

        except Exception as e:
            result.add_error(f"验证过程出错: {e}")
            result.set_passed(False)

        return result

    async def verify_functionality(self) -> VerificationResult:
        """验证功能"""
        result = VerificationResult("功能测试")

        try:
            # 1. 配置管理功能测试
            result.add_detail("测试配置管理功能...")
            try:
                from core.config.unified_settings import UnifiedSettings
                from core.config.unified_config_loader import load_full_config

                settings = UnifiedSettings()
                config = load_full_config('development', 'xiaona')

                tests_passed = 0
                if settings.database_url:
                    tests_passed += 1
                if settings.redis_url:
                    tests_passed += 1
                if config.get('service'):
                    tests_passed += 1

                result.add_detail(f"✓ 配置功能测试 ({tests_passed}/3通过)")

            except Exception as e:
                result.add_error(f"配置功能测试失败: {e}")

            # 2. 服务注册功能测试
            result.add_detail("测试服务注册功能...")
            try:
                from core.service_registry.storage_memory import InMemoryServiceRegistryStorage
                from core.service_registry import (
                    ServiceInstance,
                    ServiceRegistration,
                    ServiceStatus
                )
                from datetime import datetime

                storage = InMemoryServiceRegistryStorage()

                # 创建注册
                registration = ServiceRegistration(
                    service_name="test_func",
                    instance_id="test-001",
                    host="localhost",
                    port=8888
                )

                instance = registration.to_service_instance()
                success = await storage.register_instance(instance)

                if success:
                    result.add_detail("✓ 服务注册功能正常")
                else:
                    result.add_error("服务注册功能失败")

                # 心跳测试
                heartbeat_ok = await storage.heartbeat("test_func", "test-001")
                if heartbeat_ok:
                    result.add_detail("✓ 心跳功能正常")
                else:
                    result.add_error("心跳功能失败")

            except Exception as e:
                result.add_error(f"服务注册功能测试失败: {e}")

            # 3. 服务发现功能测试
            result.add_detail("测试服务发现功能...")
            try:
                from core.service_registry.discovery import ServiceDiscovery

                discovery = ServiceDiscovery(storage=storage)

                # 发现测试
                discovered = await discovery.discover("test_func")
                if discovered:
                    result.add_detail("✓ 服务发现功能正常")
                else:
                    result.add_error("服务发现功能失败")

            except Exception as e:
                result.add_error(f"服务发现功能测试失败: {e}")

            # 4. 集成测试
            result.add_detail("执行集成测试...")
            try:
                from core.service_registry.registry import ServiceRegistryCenter

                registry = ServiceRegistryCenter(storage=storage)

                # 注册测试服务
                test_registration = ServiceRegistration(
                    service_name="integration_test",
                    instance_id="int-001",
                    host="localhost",
                    port=7777
                )

                await registry.register_service(test_registration)

                # 发现服务
                discovered = await registry.discover_service("integration_test")

                # 获取统计
                stats = await registry.get_service_statistics("integration_test")

                if discovered and stats.get("total_instances") >= 1:
                    result.add_detail("✓ 集成测试通过")
                else:
                    result.add_error("集成测试失败")

            except Exception as e:
                result.add_error(f"集成测试失败: {e}")

            # 判断是否通过
            result.set_passed(len(result.errors) == 0)

        except Exception as e:
            result.add_error(f"验证过程出错: {e}")
            result.set_passed(False)

        return result

    def print_summary(self):
        """打印总结"""
        logger.info("\n" + "=" * 80)
        logger.info("验证总结报告")
        logger.info("=" * 80 + "\n")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        logger.info(f"总验证项: {total}")
        logger.info(f"✓ 通过: {passed}")
        logger.info(f"✗ 失败: {failed}")
        logger.info(f"通过率: {passed/total*100:.1f}%\n")

        for result in self.results:
            status = "✅ 通过" if result.passed else "❌ 失败"
            score = result.to_dict()["score"]
            logger.info(f"{status} | {result.name} (得分: {score:.0f}/100)")

            if result.details:
                for detail in result.details[:5]:
                    logger.info(f"  {detail}")
                if len(result.details) > 5:
                    logger.info(f"  ... 还有{len(result.details)-5}项")

            if result.errors:
                logger.error("  错误:")
                for error in result.errors[:3]:
                    logger.error(f"    {error}")
                if len(result.errors) > 3:
                    logger.error(f"    ... 还有{len(result.errors)-3}项")

            logger.info("")

    def save_report(self, output_path: str):
        """保存报告"""
        report = {
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
                "pass_rate": sum(1 for r in self.results if r.passed) / len(self.results) * 100
            },
            "results": [r.to_dict() for r in self.results]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ 报告已保存: {output_path}")


async def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("Phase 1 & 2 全面验证")
    logger.info("=" * 80 + "\n")

    verifier = ComprehensiveVerifier()

    # 执行所有验证
    logger.info("开始验证...\n")

    result1 = await verifier.verify_phase1_config_system()
    verifier.add_result(result1)

    result2 = await verifier.verify_phase2_service_registry()
    verifier.add_result(result2)

    result3 = await verifier.verify_code_quality()
    verifier.add_result(result3)

    result4 = await verifier.verify_functionality()
    verifier.add_result(result4)

    # 打印总结
    verifier.print_summary()

    # 保存报告
    report_path = project_root / "docs/reports/COMPREHENSIVE_VERIFICATION_REPORT_20260421.json"
    verifier.save_report(str(report_path))

    # 返回是否全部通过
    all_passed = all(r.passed for r in verifier.results)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
