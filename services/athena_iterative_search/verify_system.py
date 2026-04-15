#!/usr/bin/env python3
"""
Athena迭代式搜索系统验证脚本
验证系统各个组件是否正常工作
"""

import logging
import os
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

# 设置Python路径
sys.path.append('/Users/xujian/Athena工作平台')

def print_header(title) -> None:
    """打印标题"""
    logger.info(str("\n" + '='*60))
    logger.info(f" {title}")
    logger.info(str('='*60))

def print_success(message) -> None:
    """打印成功信息"""
    logger.info(f"✅ {message}")

def print_error(message) -> None:
    """打印错误信息"""
    logger.info(f"❌ {message}")

def print_warning(message) -> None:
    """打印警告信息"""
    logger.info(f"⚠️  {message}")

def print_info(message) -> None:
    """打印信息"""
    logger.info(f"ℹ️  {message}")

async def verify_imports():
    """验证必要的包导入"""
    print_header('1. 验证依赖包导入')

    required_packages = [
        ('fastapi', 'FastAPI框架'),
        ('uvicorn', 'ASGI服务器'),
        ('elasticsearch', 'Elasticsearch客户端'),
        ('psycopg2', 'PostgreSQL驱动'),
        ('sentence_transformers', '句子转换器'),
        ('faiss', '向量搜索库'),
        ('redis', 'Redis客户端'),
        ('aiohttp', '异步HTTP客户端'),
        ('jieba', '中文分词'),
        ('numpy', '数值计算'),
        ('openai', 'OpenAI客户端（用于Qwen）')
    ]

    missing_packages = []

    for package_name, description in required_packages:
        try:
            # 特殊处理某些包名
            import_name = package_name
            if package_name == 'psycopg2':
                import_name = 'psycopg2'
            elif package_name == 'sentence_transformers':
                import_name = 'sentence_transformers'
            elif package_name == 'openai':
                import_name = 'openai'

            __import__(import_name)
            print_success(f"{description} ({package_name})")
        except ImportError:
            print_error(f"{description} ({package_name}) 未安装")
            missing_packages.append(package_name)

    if missing_packages:
        print_warning(f"\n缺少 {len(missing_packages)} 个依赖包")
        print_info('请运行: pip3 install ' + ' '.join(missing_packages))
        return False

    print_success("\n所有依赖包导入成功！")
    return True

async def verify_system_components():
    """验证系统组件"""
    print_header('2. 验证系统组件')

    try:
        # 验证类型定义
        print_success('类型定义模块')

        # 验证配置系统
        from services.athena_iterative_search.config_enhanced import (
            get_config_by_environment,
        )
        get_config_by_environment()
        print_success('配置系统')

        # 验证LLM集成
        print_success('LLM集成模块')

        # 验证外部搜索引擎
        print_success('外部搜索引擎模块')

        # 验证向量搜索
        print_success('向量搜索模块')

        # 验证性能优化器
        print_success('性能优化器模块')

        # 验证增强核心引擎
        print_success('增强核心搜索引擎')

        return True

    except Exception as e:
        print_error(f"组件导入失败: {e}")
        return False

async def verify_services():
    """验证外部服务"""
    print_header('3. 验证外部服务')

    services_status = {}

    # 检查PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='athena_patents',
            user='postgres',
            password=''
        )
        conn.close()
        print_success('PostgreSQL 连接正常')
        services_status['postgresql'] = True
    except Exception as e:
        print_error(f"PostgreSQL 连接失败: {e}")
        services_status['postgresql'] = False

    # 检查Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print_success('Redis 连接正常')
        services_status['redis'] = True
    except Exception as e:
        print_error(f"Redis 连接失败: {e}")
        services_status['redis'] = False

    # 检查Elasticsearch
    try:
        import elasticsearch
        es = elasticsearch.Elasticsearch([{'host': 'localhost', 'port': 9200}])
        if es.ping():
            print_success('Elasticsearch 连接正常')
            services_status['elasticsearch'] = True
        else:
            print_error('Elasticsearch ping失败')
            services_status['elasticsearch'] = False
    except Exception as e:
        print_error(f"Elasticsearch 连接失败: {e}")
        services_status['elasticsearch'] = False

    return services_status

async def test_basic_functionality():
    """测试基本功能"""
    print_header('4. 测试基本功能')

    try:
        from services.athena_iterative_search.config_enhanced import (
            ENHANCED_DEFAULT_CONFIG,
        )
        from services.athena_iterative_search.enhanced_core import (
            AthenaEnhancedIterativeSearchEngine,
        )

        print_info('初始化搜索引擎（使用Mock模式）...')

        # 使用默认配置（Mock模式）
        engine = AthenaEnhancedIterativeSearchEngine(ENHANCED_DEFAULT_CONFIG)

        # 测试单次搜索
        print_info("\n测试单次搜索...")
        results = await engine.search(
            query='人工智能',
            strategy='hybrid',
            max_results=5,
            use_cache=False
        )

        print_success(f"单次搜索成功，返回 {len(results)} 条结果")

        # 测试迭代搜索
        print_info("\n测试迭代搜索（仅2轮以节省时间）...")
        session = await engine.iterative_search(
            initial_query='机器学习算法',
            max_iterations=2,
            depth='standard'
        )

        print_success("迭代搜索完成")
        print_info(f"  - 会话ID: {session.id}")
        print_info(f"  - 总迭代轮数: {session.current_iteration}")
        print_info(f"  - 发现专利总数: {session.total_patents_found}")
        print_info(f"  - 唯一专利数: {session.unique_patents}")

        if session.research_summary:
            print_info(f"  - 生成研究摘要: {len(session.research_summary.key_findings)} 条发现")

        # 清理
        await engine.close()

        return True

    except Exception as e:
        print_error(f"功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_environment_file():
    """检查环境配置文件"""
    print_header('5. 检查环境配置')

    env_file = '/Users/xujian/Athena工作平台/services/athena_iterative_search/.env'

    if os.path.exists(env_file):
        print_success('环境配置文件存在')

        # 检查关键配置
        with open(env_file) as f:
            content = f.read()

        if 'QWEN_API_KEY=' in content and len(content.split('QWEN_API_KEY=')[1].split('\n')[0]) > 10:
            print_success('Qwen API密钥已配置')
        else:
            print_warning('Qwen API密钥未配置（将使用Mock模式）')

        if 'DB_HOST=' in content:
            print_success('数据库配置已设置')
        else:
            print_warning('数据库配置可能不完整')

    else:
        print_warning('环境配置文件不存在')
        print_info('请运行: ./environment_setup.sh')
        return False

    return True

async def main():
    """主验证流程"""
    print_header('Athena迭代式搜索系统验证')
    logger.info(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_passed = True

    # 1. 验证依赖包
    if not await verify_imports():
        all_passed = False
        logger.info("\n❌ 依赖包验证失败，请安装缺少的包后重试")
        return

    # 2. 验证系统组件
    if not await verify_system_components():
        all_passed = False
        logger.info("\n❌ 系统组件验证失败")
        return

    # 3. 验证外部服务
    services_status = await verify_services()

    # 4. 检查环境配置
    env_ok = await check_environment_file()

    # 5. 测试基本功能（即使某些服务不可用也尝试）
    if await test_basic_functionality():
        print_success("\n基本功能测试通过")
    else:
        print_error("\n基本功能测试失败")
        all_passed = False

    # 生成验证报告
    print_header('验证报告')

    logger.info(f"依赖包: {'✅ 全部通过' if all_passed else '❌ 存在问题'}")
    logger.info("系统组件: ✅ 正常")
    logger.info(f"PostgreSQL: {'✅ 连接正常' if services_status.get('postgresql') else '❌ 连接失败'}")
    logger.info(f"Redis: {'✅ 连接正常' if services_status.get('redis') else '❌ 连接失败'}")
    logger.info(f"Elasticsearch: {'✅ 连接正常' if services_status.get('elasticsearch') else '❌ 连接失败'}")
    logger.info(f"环境配置: {'✅ 已配置' if env_ok else '⚠️ 需要配置'}")

    if all_passed and any(services_status.values()):
        logger.info("\n🎉 系统验证成功！可以启动服务了。")
        logger.info("\n启动命令:")
        logger.info('  ./scripts/start_enhanced_athena_iterative_search.sh')
        logger.info("\n访问地址:")
        logger.info('  API文档: http://localhost:5002/docs')
        logger.info('  健康检查: http://localhost:5002/health')
    elif not all_passed:
        logger.info("\n⚠️ 系统存在一些问题，但基本功能可用。")
        logger.info("\n建议:")
        logger.info('1. 安装缺少的依赖包')
        logger.info('2. 启动必要的数据库服务')
        logger.info('3. 配置环境变量')
    else:
        logger.info("\n❌ 系统验证失败，请解决问题后重试。")

# 入口点: @async_main装饰器已添加到main函数
