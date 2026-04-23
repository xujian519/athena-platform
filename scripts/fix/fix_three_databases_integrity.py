#!/usr/bin/env python3
"""
法律世界模型三库完整性修复主脚本
Master Script to Fix Three-Database Integrity

执行顺序:
1. 同步司法案例数据（Qdrant → Neo4j）
2. 导入无效决定数据（Qdrant/文件 → PostgreSQL）
3. 构建知识图谱关系（Neo4j内部）
4. 验证数据完整性

作者: Athena平台团队
版本: v1.0.0
日期: 2026-01-27
"""

import logging
import subprocess
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_script(script_path: str, description: str) -> bool:
    """运行脚本并返回是否成功"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 {description}")
    logger.info(f"{'='*60}")

    try:
        result = subprocess.run(
            ["python3", script_path],
            cwd="/Users/xujian/Athena工作平台",
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        # 输出结果
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(line)

        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.warning(line)

        if result.returncode == 0:
            logger.info(f"✅ {description} - 完成")
            return True
        else:
            logger.error(f"❌ {description} - 失败 (退出码: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ {description} - 超时")
        return False
    except Exception as e:
        logger.error(f"❌ {description} - 错误: {e}")
        return False


def main():
    """主函数"""
    logger.info("""
╔═══════════════════════════════════════════════════════════╗
║     法律世界模型三库完整性修复程序                          ║
║     Legal World Model Three-Database Integrity Fix          ║
╠═══════════════════════════════════════════════════════════╣
║  版本: v1.0.0                                              ║
║  日期: 2026-01-27                                          ║
║  作者: Athena平台团队                                       ║
╚═══════════════════════════════════════════════════════════╝
    """)

    start_time = datetime.now()

    # 定义要执行的脚本
    scripts = [
        {
            "path": "scripts/sync_judgment_data_to_kg.py",
            "description": "步骤1/3: 同步司法案例数据 (Qdrant → Neo4j)"
        },
        {
            "path": "scripts/import_invalidation_decisions.py",
            "description": "步骤2/3: 导入无效决定数据 (→ PostgreSQL)"
        },
        {
            "path": "scripts/build_legal_knowledge_graph_relations.py",
            "description": "步骤3/3: 构建知识图谱关系 (Neo4j)"
        }
    ]

    results = []

    for script in scripts:
        success = run_script(script["path"], script["description"])
        results.append({
            "script": script["description"],
            "success": success
        })

        if not success:
            logger.warning(f"\n⚠️ {script['description']} 失败，是否继续？")
            response = input("继续执行下一步？(y/n): ").lower()
            if response != 'y':
                logger.info("⏹️ 用户中断执行")
                break

    # 总结
    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(f"""
╔═══════════════════════════════════════════════════════════╗
║                   执行结果汇总                              ║
╠═══════════════════════════════════════════════════════════╣
    """)

    for result in results:
        status = "✅ 成功" if result["success"] else "❌ 失败"
        logger.info(f"{status} - {result['script']}")

    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)

    logger.info(f"""
╠═══════════════════════════════════════════════════════════╣
║  总计: {success_count}/{total_count} 成功                                     ║
║  耗时: {elapsed:.2f} 秒                                            ║
╚═══════════════════════════════════════════════════════════╝
    """)

    if success_count == total_count:
        logger.info("🎉 所有任务完成！三库数据已修复！")
        return 0
    else:
        logger.warning("⚠️ 部分任务失败，请检查日志")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ 执行出错: {e}")
        sys.exit(1)
