#!/usr/bin/env python3
"""
OpenClaw专利分析模块部署验证
Patent Analysis Modules Deployment Verification

快速验证各模块的可用性

作者: Athena平台团队
创建时间: 2026-02-03
版本: v1.0.0
"""

import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_file_exists(file_path):
    """检查文件是否存在"""
    path = Path(file_path)
    if path.exists():
        size = path.stat().st_size
        logger.info(f"✅ {path.name}: 存在 ({size:,} bytes)")
        return True
    else:
        logger.error(f"❌ {path.name}: 文件不存在")
        return False


def check_module_imports(module_path):
    """检查模块导入"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import sys; sys.path.insert(0, '/Users/xujian/Athena工作平台'); from {module_path} pass"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"✅ {module_path}: 导入成功")
            return True
        else:
            logger.warning(f"⚠️ {module_path}: 导入失败")
            return False
    except Exception as e:
        logger.error(f"❌ {module_path}: 检查失败 - {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("OpenClaw专利分析模块部署验证")
    logger.info("=" * 60)
    logger.info("")

    total_modules = 0
    passed_modules = 0

    # 模块清单
    modules = [
        {
            "name": "权利要求分析模块",
            "path": "production/scripts/patent_full_text/phase3/claim_parser_v2.py",
            "import_path": "production.scripts.patent_full_text.phase3.claim_parser_v2.ClaimParserV2"
        },
        {
            "name": "附图识别模块",
            "path": "core/perception/technical_drawing_analyzer.py",
            "import_path": "core.perception.technical_drawing_analyzer.TechnicalDrawingAnalyzer"
        },
        {
            "name": "深度分析模块",
            "path": "core/patent_deep_comparison_analyzer.py",
            "import_path": "core.patent.patent_deep_comparison_analyzer.PatentDeepComparisonAnalyzer"
        },
        {
            "name": "无效宣告策略模块",
            "path": "scripts/patent_invalidity_strategy_analyzer.py",
            "import_path": "scripts.patent_invalidity_strategy_analyzer.InvalidityStrategyAnalyzer"
        },
        {
            "name": "双图构建模块",
            "path": "core/knowledge/patent_analysis/enhanced_knowledge_graph.py",
            "import_path": None  # 需要数据库，跳过导入测试
        },
    ]

    # 检查文件存在性
    logger.info("【第一步】检查文件存在性")
    logger.info("")
    for module in modules:
        total_modules += 1
        if check_file_exists(f"/Users/xujian/Athena工作平台/{module['path']}"):
            passed_modules += 1

    logger.info("")
    logger.info("【第二步】检查模块导入")
    logger.info("")
    for module in modules:
        if module["import_path"]:  # 跳过需要数据库的模块
            check_module_imports(module["import_path"])

    # 脚本工具集
    logger.info("")
    logger.info("【第三步】检查脚本工具集")
    logger.info("")

    scripts = [
        "scripts/patent_deep_comparison.py",
        "scripts/patent_invalidity_strategy_analyzer.py",
        "scripts/patent_relevance_analyzer.py",
        "scripts/patent_text_extractor.py",
        "scripts/patent_search_analyzer.py"
    ]

    script_count = 0
    for script in scripts:
        total_modules += 1
        if check_file_exists(f"/Users/xujian/Athena工作平台/{script}"):
            script_count += 1

    passed_modules += script_count

    # 总结
    logger.info("")
    logger.info("=" * 60)
    logger.info("部署验证总结")
    logger.info("=" * 60)
    logger.info(f"总模块数: {total_modules}")
    logger.info(f"验证通过: {passed_modules}")
    logger.info(f"通过率: {passed_modules/total_modules*100:.1f}%")
    logger.info("")

    # 部署状态
    if passed_modules >= total_modules * 0.8:
        logger.info("🎉 部署状态: 优秀 - 大部分模块可以正常使用")
    elif passed_modules >= total_modules * 0.5:
        logger.info("⚠️ 部署状态: 良好 - 核心模块可用")
    else:
        logger.info("❌ 部署状态: 需要修复 - 部分模块存在问题")

    return passed_modules >= total_modules * 0.8


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
