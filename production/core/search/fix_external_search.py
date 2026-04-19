#!/usr/bin/env python3
"""
修复外部搜索引擎问题脚本
Fix External Search Engine Issues

修复从xiaoxi平台复制的搜索引擎中的各种问题

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

from __future__ import annotations
import json
import logging
import sys
from pathlib import Path

from core.logging_config import setup_logging

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

async def check_external_search_status():
    """检查外部搜索引擎状态"""
    logger.info('🔍 检查外部搜索引擎状态')
    logger.info(str('=' * 50))

    issues = []
    recommendations = []

    # 1. 检查文件存在性
    files_to_check = [
        '/core/search/external/web_search_engines.py',
        '/core/search/external/search_manager.py',
        '/core/search/tools/real_web_search_adapter.py',
        '/core/search/tools/adapted_web_search_manager.py'
    ]

    logger.info("\n📁 文件存在性检查:")
    for file_path in files_to_check:
        full_path = project_root / file_path[1:]  # 移除开头的 /
        if full_path.exists():
            logger.info(f"   ✅ {file_path}")
        else:
            logger.info(f"   ❌ {file_path} - 文件不存在")
            issues.append(f"文件不存在: {file_path}")

    # 2. 检查API密钥配置
    logger.info("\n🔑 API密钥配置检查:")
    config_file = project_root / 'core/search/config/search_api_config.json'

    try:
        with open(config_file, encoding='utf-8') as f:
            config = json.load(f)

        api_keys = config.get('search_api_keys', {})
        enabled_count = 0
        for service, service_config in api_keys.items():
            if service_config.get('enabled') and service_config.get('api_key'):
                enabled_count += 1
                logger.info(f"   ✅ {service}: 已配置")
            else:
                logger.info(f"   ❌ {service}: 未配置")

        if enabled_count >= 2:
            logger.info(f"\n   📊 已配置 {enabled_count} 个搜索引擎,系统可用")
        else:
            logger.info(f"\n   ⚠️ 仅配置了 {enabled_count} 个搜索引擎,建议配置更多")

    except Exception as e:
        logger.info(f"   ❌ 无法读取配置文件: {e}")
        issues.append('API配置文件读取失败')

    # 3. 检查导入问题
    logger.info("\n📦 导入路径检查:")
    import_checks = [
        ('aiohttp', '异步HTTP库'),
        ('core.search.standards.base_search_tool', '搜索工具基类'),
        ('core.search.config.api_key_manager', 'API密钥管理器')
    ]

    for module_name, _description in import_checks:
        try:
            __import__(module_name)
            logger.info(f"   ✅ {module_name}: 可导入")
        except ImportError as e:
            logger.info(f"   ❌ {module_name}: 导入失败 - {e}")
            issues.append(f"导入失败: {module_name}")

    # 4. 检查安全问题
    logger.info("\n🔒 安全性检查:")
    web_search_file = project_root / 'core/search/external/web_search_engines.py'

    try:
        with open(web_search_file, encoding='utf-8') as f:
            content = f.read()

        security_issues = []

        # 检查硬编码API密钥
        if 'tvly-dev-' in content:
            security_issues.append('发现硬编码的Tavily API密钥')
        if 'sk-' in content and 'api-key-' in content:
            security_issues.append('发现硬编码的API密钥')

        # 检查SSL配置
        if 'ssl=False' in content:
            security_issues.append('发现禁用SSL验证的代码')

        if security_issues:
            for issue in security_issues:
                logger.info(f"   🔴 {issue}")
            recommendations.append('使用安全版本的搜索引擎实现')
        else:
            logger.info('   ✅ 未发现明显的安全问题')

    except Exception as e:
        logger.info(f"   ❌ 安全检查失败: {e}")

    return issues, recommendations

async def create_fixed_imports():
    """创建修复的导入文件"""
    logger.info("\n🔧 创建修复的导入文件")
    logger.info(str('-' * 40))

    # 创建__init__.py文件
    init_file = project_root / 'core/search/external/__init__.py'

    try:
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('"""\n')
            f.write('外部搜索引擎模块\n')
            f.write('External Search Engines Module\n')
            f.write('"""\n\n')
            f.write('from .web_search_engines_secure import SecureUnifiedWebSearchManager\n')
            f.write('from .web_search_engines_secure import SearchResult\n')
            f.write('from .search_manager import ExternalSearchManager\n\n')
            f.write('__all__ = [\n')
            f.write("    'SecureUnifiedWebSearchManager',\n")
            f.write("    'SearchResult',\n")
            f.write("    'ExternalSearchManager'\n")
            f.write(']\n')

        logger.info(f"   ✅ 创建 {init_file}")
    except Exception as e:
        logger.info(f"   ❌ 创建 __init__.py 失败: {e}")

    # 更新适配器导入
    adapter_file = project_root / 'core/search/tools/real_web_search_adapter.py'

    try:
        with open(adapter_file, encoding='utf-8') as f:
            content = f.read()

        # 修复导入路径
        if 'from ...external.web_search_engines import' in content:
            content = content.replace(
                'from ...external.web_search_engines import',
                'from ..external.web_search_engines_secure import'
            )

            with open(adapter_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"   ✅ 修复 {adapter_file} 导入路径")

    except Exception as e:
        logger.info(f"   ❌ 修复适配器导入失败: {e}")

async def test_secure_search():
    """测试安全搜索功能"""
    logger.info("\n🧪 测试安全搜索功能")
    logger.info(str('-' * 40))

    try:
        # 导入API密钥管理器
        from core.search.config.api_key_manager import get_api_key_manager

        manager = get_api_key_manager()

        # 获取配置的API密钥
        api_config = {
            'api_keys': {
                'tavily': manager.get_api_key('tavily') and [manager.get_api_key('tavily')] or [],
                'serper': manager.get_api_key('serper') and [manager.get_api_key('serper')] or [],
                'bocha': manager.get_api_key('bocha') and [manager.get_api_key('bocha')] or []
            }
        }

        # 导入安全搜索引擎
        from core.search.external.web_search_engines_secure import (
            SecureUnifiedWebSearchManager,
        )

        logger.info('   🔍 初始化安全搜索管理器...')

        async with SecureUnifiedWebSearchManager(api_config) as search_manager:
            # 健康检查
            logger.info('   🏥 执行健康检查...')
            health = await search_manager.health_check()

            logger.info(f"   📊 系统状态: {health['overall_status']}")

            available_engines = []
            for engine, status in health['engines'].items():
                if status['available']:
                    available_engines.append(engine)
                    logger.info(f"   ✅ {engine}: 可用")
                else:
                    logger.info(f"   ❌ {engine}: 不可用")

            if available_engines:
                logger.info("\n   🔍 测试搜索功能...")
                results = await search_manager.search(
                    'Python编程语言',
                    engines=available_engines[:2],  # 使用前两个可用引擎
                    max_results=3
                )

                if results['success']:
                    logger.info("   ✅ 搜索成功")
                    logger.info(f"   📊 找到 {results['total_results']} 个结果")
                    logger.info(f"   ⏱️ 耗时 {results['search_time']:.2f}s")
                    logger.info(f"   🛠️ 使用引擎: {', '.join(results['engines_used'])}")

                    return True
                else:
                    logger.info(f"   ❌ 搜索失败: {results['error']}")
                    return False
            else:
                logger.info('   ⚠️ 没有可用的搜索引擎')
                return False

    except Exception as e:
        logger.info(f"   ❌ 测试失败: {e}")
        logger.error(f"安全搜索测试失败: {e}", exc_info=True)
        return False

async def generate_status_report():
    """生成状态报告"""
    logger.info("\n📊 生成状态报告")
    logger.info(str('-' * 30))

    report = {
        'timestamp': '2025-12-05T00:00:00Z',
        'external_search_status': 'checked',
        'issues': [],
        'recommendations': [],
        'configuration': {
            'configured_engines': 0,
            'available_engines': 0
        }
    }

    # 检查配置
    try:
        from core.search.config.api_key_manager import get_api_key_manager
        manager = get_api_key_manager()
        validation_report = manager.get_validation_report()

        report['configuration']['configured_engines'] = validation_report['valid_services']
        report['configuration']['available_engines'] = validation_report['enabled_services']

    except Exception as e:
        report['issues'].append(f"配置检查失败: {str(e)}")

    # 测试功能
    test_success = await test_secure_search()
    if not test_success:
        report['issues'].append('安全搜索测试失败')
        report['recommendations'].append('检查API密钥配置和网络连接')

    # 保存报告
    report_file = project_root / 'core/search/external_search_status.json'
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"   📄 状态报告已保存: {report_file}")
    except Exception as e:
        logger.info(f"   ❌ 保存报告失败: {e}")

    return report

async def main():
    """主函数"""
    logger.info('🔧 外部搜索引擎修复工具')
    logger.info('检查和修复从xiaoxi平台复制的搜索引擎问题')
    logger.info(str('=' * 60))

    # 1. 检查状态
    issues, recommendations = await check_external_search_status()

    # 2. 修复导入
    await create_fixed_imports()

    # 3. 测试功能
    test_result = await test_secure_search()

    # 4. 生成报告
    await generate_status_report()

    # 总结
    logger.info(str("\n" + '=' * 60))
    logger.info('📋 修复总结')
    logger.info(str('=' * 60))

    if issues:
        logger.info(f"\n⚠️ 发现 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            logger.info(f"   {i}. {issue}")
    else:
        logger.info("\n✅ 未发现明显问题")

    if recommendations:
        logger.info("\n💡 建议:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"   {i}. {rec}")

    if test_result:
        logger.info("\n🎉 外部搜索引擎修复成功,系统可以正常使用!")
        logger.info("\n🚀 下一步:")
        logger.info('   1. 使用交互式搜索: python3 core/search/start_with_real_tools.py --interactive')
        logger.info("   2. 执行单次搜索: python3 core/search/start_with_real_tools.py --query '搜索内容'")
    else:
        logger.info("\n⚠️ 外部搜索引擎仍有问题,需要进一步调试")

# 入口点: @async_main装饰器已添加到main函数
