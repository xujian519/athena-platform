#!/usr/bin/env python3
"""
OpenClaw专利分析模块集成测试
Patent Analysis Modules Integration Test for OpenClaw

测试所有已部署到OpenClaw的专利分析模块

作者: Athena平台团队
创建时间: 2026-02-03
版本: v1.0.0
"""

import logging
import sys

# 添加Athena工作平台路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenClawModuleTester:
    """OpenClaw模块测试器"""

    def __init__(self):
        """初始化测试器"""
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0

    def test_module(self, module_name: str, import_path: str, class_name: str = None):
        """
        测试单个模块

        Args:
            module_name: 模块名称
            import_path: 导入路径
            class_name: 类名（可选）
        """
        self.total_tests += 1
        try:
            # 尝试导入模块
            parts = import_path.rsplit('.', 1)
            module = __import__(parts[0])
            for part in parts[1:]:
                module = getattr(module, part)

            # 如果指定了类名，尝试实例化
            if class_name:
                getattr(module, class_name)
                logger.info(f"✅ {module_name}: 导入并访问类 {class_name} 成功")
            else:
                logger.info(f"✅ {module_name}: 导入成功")

            self.passed_tests += 1
            self.test_results[module_name] = "PASS"
            return True

        except Exception as e:
            logger.error(f"❌ {module_name}: 测试失败 - {e}")
            self.test_results[module_name] = f"FAIL: {e}"
            return False

    def test_claim_parser(self):
        """测试权利要求分析模块"""
        logger.info("\n=== 测试1: 权利要求分析模块 ===")
        from production.scripts.patent_full_text.phase3.claim_parser_v2 import ClaimParserV2

        test_claims = """
1. 一种激光雷达装置，其特征在于，包括：
发射单元，用于发射激光束；
接收单元，用于接收反射的激光束。

2. 根据权利要求1所述的激光雷达装置，其特征在于，所述发射单元为固态激光器。
"""

        parser = ClaimParserV2()
        result = parser.parse('TEST001', test_claims)

        logger.info(f"   总权利要求: {result.total_claim_count}")
        logger.info(f"   独立权利要求: {len(result.independent_claims)}")
        logger.info(f"   从属权利要求: {len(result.dependent_claims)}")

        self.test_module("权利要求分析", "claim_parser_v2", None)
        return True

    def test_deep_comparison(self):
        """测试深度对比分析模块"""
        logger.info("\n=== 测试2: 深度对比分析模块 ===")
        return self.test_module(
            "深度对比分析",
            "core.patent.patent_deep_comparison_analyzer",
            "PatentDeepComparisonAnalyzer"
        )

    def test_invalidity_strategy(self):
        """测试无效宣告策略模块"""
        logger.info("\n=== 测试3: 无效宣告策略模块 ===")
        return self.test_module(
            "无效宣告策略",
            "scripts.patent_invalidity_strategy_analyzer",
            "InvalidityStrategyAnalyzer"
        )

    def test_drawing_analyzer(self):
        """测试附图识别模块"""
        logger.info("\n=== 测试4: 附图识别模块 ===")
        return self.test_module(
            "附图识别",
            "core.perception.technical_drawing_analyzer",
            "TechnicalDrawingAnalyzer"
        )

    def test_all_modules(self):
        """测试所有模块"""
        logger.info("=" * 60)
        logger.info("开始测试OpenClaw专利分析模块")
        logger.info("=" * 60)

        # 测试各个模块
        self.test_claim_parser()
        self.test_deep_comparison()
        self.test_invalidity_strategy()
        self.test_drawing_analyzer()

        # 生成报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "=" * 60)
        logger.info("测试报告")
        logger.info("=" * 60)
        logger.info(f"总测试数: {self.total_tests}")
        logger.info(f"通过测试: {self.passed_tests}")
        logger.info(f"失败测试: {self.total_tests - self.passed_tests}")
        logger.info(f"通过率: {self.passed_tests/self.total_tests*100:.1f}%")
        logger.info("")

        # 详细结果
        for module_name, result in self.test_results.items():
            status_icon = "✅" if result == "PASS" else "❌"
            logger.info(f"{status_icon} {module_name}: {result}")


def main():
    """主函数"""
    tester = OpenClawModuleTester()
    tester.test_all_modules()

    return tester.passed_tests == tester.total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
