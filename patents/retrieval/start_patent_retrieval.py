#!/usr/bin/env python3
"""
专利检索系统启动脚本
Patent Retrieval System Startup Script
用于启动修复后的专利混合检索系统
"""

import argparse
import asyncio
import logging
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("patent_retrieval.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║    🚀 专利混合检索系统 - 修复版本                                                              ║
║    Patent Hybrid Retrieval System - Fixed Version                                             ║
║                                                                                                  ║
║    📊 支持: BM25全文搜索 + 向量语义检索 + 知识图谱检索                                         ║
║    🗄️ 数据库: PostgreSQL (200G+ 真实专利数据)                                                     ║
║    🔍 特性: 动态权重配置 + 实时融合排序 + 多语言支持                                            ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def check_environment():
    """检查运行环境"""
    logger.info("🔧 检查运行环境...")

    # 检查Python版本
    python_version = sys.version_info
    logger.info(
        f"   Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    # 检查必需的环境变量
    required_vars = [
        "PATENT_DB_HOST",
        "PATENT_DB_PORT",
        "PATENT_DB_NAME",
        "PATENT_DB_USER",
        "PATENT_DB_PASSWORD",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.warning(f"   ⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        logger.info("   💡 请确保 .env 文件包含正确的数据库配置")
        return False

    logger.info("   ✅ 环境变量配置完整")

    # 测试数据库连接
    try:
        from config.database import test_patent_database

        if test_patent_database():
            logger.info("   ✅ 数据库连接正常")
            return True
        else:
            logger.error("   ❌ 数据库连接失败")
            return False
    except Exception as e:
        logger.error(f"   ❌ 数据库连接测试出错: {e}")
        return False


async def test_basic_functionality():
    """测试基础功能"""
    logger.info("🧪 测试基础功能...")

    try:
        # 测试numpy兼容性
        from config.numpy_compatibility import array, zeros

        array([1, 2, 3])
        zeros(3)
        logger.info("   ✅ numpy兼容性测试通过")

        # 测试数据库配置
        from config.database import get_patent_db_config

        get_patent_db_config()
        logger.info("   ✅ 数据库配置测试通过")

        # 测试关键词提取
        from patents.retrieval.real_patent_hybrid_retrieval import RealPatentHybridRetrieval

        retrieval_system = RealPatentHybridRetrieval()
        keywords = retrieval_system._extract_keywords("深度学习图像识别技术")
        logger.info(f"   ✅ 关键词提取测试通过: {keywords}")

        return True

    except Exception as e:
        logger.error(f"   ❌ 基础功能测试失败: {e}")
        return False


async def start_demo_system():
    """启动演示系统"""
    logger.info("🚀 启动专利检索演示系统...")

    try:
        from patents.retrieval.real_patent_hybrid_retrieval import RealPatentHybridRetrieval

        # 创建检索系统实例
        retrieval_system = RealPatentHybridRetrieval()

        # 获取系统统计
        stats = retrieval_system.get_system_stats()
        logger.info("📊 系统统计信息:")
        for key, value in stats.items():
            if key != "config":  # 配置太详细，跳过
                logger.info(f"   {key}: {value}")

        # 演示查询
        demo_queries = ["深度学习图像识别", "区块链数据存储", "人工智能专利", "自然语言处理"]

        logger.info("\n🔍 开始演示查询...")
        for i, query in enumerate(demo_queries, 1):
            logger.info(f"\n--- 查询 {i}: {query} ---")

            try:
                results = await retrieval_system.search(query, top_k=3)

                if results:
                    logger.info(f"✅ 找到 {len(results)} 条结果:")
                    for j, result in enumerate(results, 1):
                        logger.info(f"   {j}. {result.patent_id}")
                        logger.info(f"      标题: {result.title[:50]}...")
                        logger.info(f"      评分: {result.score:.4f}")
                        logger.info(f"      来源: {result.metadata['sources']}")
                else:
                    logger.warning("⚠️ 暂无相关结果")

            except Exception as e:
                logger.error(f"❌ 查询失败: {e}")

        logger.info("\n✅ 演示完成！")

    except Exception as e:
        logger.error(f"❌ 演示系统启动失败: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def start_interactive_mode():
    """启动交互模式"""
    logger.info("💬 启动交互模式...")

    try:
        from patents.retrieval.real_patent_hybrid_retrieval import RealPatentHybridRetrieval

        retrieval_system = RealPatentHybridRetrieval()

        print("\n" + "=" * 80)
        print("🎯 专利检索交互模式已启动")
        print("💡 输入查询关键词，输入 'quit' 或 'exit' 退出")
        print("📝 示例查询: 深度学习图像识别")
        print("=" * 80)

        while True:
            try:
                query = input("\n🔍 请输入查询关键词: ").strip()

                if query.lower() in ["quit", "exit", "退出", "q"]:
                    print("👋 再见！")
                    break

                if len(query) < 2:
                    print("⚠️ 查询长度过短，请输入至少2个字符")
                    continue

                print(f"\n🔄 正在检索: {query}")
                results = await retrieval_system.search(query, top_k=5)

                if results:
                    print(f"✅ 找到 {len(results)} 条结果:\n")
                    for i, result in enumerate(results, 1):
                        print(f"{i}. 【{result.patent_id}】")
                        print(f"   标题: {result.title}")
                        print(f"   摘要: {result.abstract[:100]}...")
                        print(f"   评分: {result.score:.4f}")
                        print(f"   来源: {', '.join(result.metadata['sources'])}")
                        print(f"   证据: {result.evidence[:150]}...")
                        print()
                else:
                    print("⚠️ 暂无相关结果\n")

            except KeyboardInterrupt:
                print("\n👋 用户中断，退出...")
                break
            except Exception as e:
                print(f"❌ 检索出错: {e}")

    except Exception as e:
        logger.error(f"❌ 交互模式启动失败: {e}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="专利检索系统启动脚本")
    parser.add_argument(
        "--mode", choices=["check", "demo", "interactive"], default="check", help="运行模式"
    )
    parser.add_argument("--query", type=str, help="查询关键词（仅demo模式）")

    args = parser.parse_args()

    # 打印横幅
    print_banner()

    # 检查环境
    if not await check_environment():
        logger.error("❌ 环境检查失败，请修复后重试")
        return

    # 根据模式执行
    if args.mode == "check":
        logger.info("🔧 仅执行环境检查模式")
        if await test_basic_functionality():
            logger.info("✅ 所有检查通过，系统可正常运行")
        else:
            logger.error("❌ 基础功能测试失败")

    elif args.mode == "demo":
        logger.info("🎯 执行演示模式")
        await test_basic_functionality()
        await start_demo_system()

    elif args.mode == "interactive":
        logger.info("💬 执行交互模式")
        await test_basic_functionality()
        await start_interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 用户中断，退出...")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
