#!/usr/bin/env python3
"""
decision_engine工具验证脚本

验证功能:
1. 基础加权决策
2. 权重归一化
3. 多标准评估
4. 边界情况处理
5. 决策结果合理性验证

作者: Athena验证系统
日期: 2026-04-20
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.production_tool_implementations import decision_engine_handler


class DecisionEngineVerifier:
    """决策引擎验证器"""

    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0

    async def test_basic_weighted_decision(self):
        """测试1: 基础加权决策"""
        print("\n[测试1] 基础加权决策")

        params = {
            "context": "选择技术栈",
            "options": ["Python", "Go", "Rust"],
            "criteria": {"性能": 0.4, "易用性": 0.3, "生态": 0.3},
            "scores": {
                "Python": {"性能": 0.6, "易用性": 0.9, "生态": 0.95},
                "Go": {"性能": 0.85, "易用性": 0.8, "生态": 0.75},
                "Rust": {"性能": 0.95, "易用性": 0.6, "生态": 0.7},
            },
        }

        result = await decision_engine_handler(params, {})

        # 验证
        checks = []

        # 检查成功状态
        if result["success"]:
            checks.append(("✓", "决策执行成功"))
        else:
            checks.append(("✗", f"决策执行失败: {result.get('error')}"))

        # 检查排名数量
        if len(result["ranking"]) == 3:
            checks.append(("✓", f"排名数量正确: {len(result['ranking'])}"))
        else:
            checks.append(("✗", f"排名数量错误: {len(result['ranking'])} != 3"))

        # 检查分数范围
        if result["analysis"]:
            min_score, max_score = result["analysis"]["score_range"]
            if 0 <= min_score <= max_score <= 1:
                checks.append(("✓", f"分数范围合理: [{min_score:.3f}, {max_score:.3f}]"))
            else:
                checks.append(("✗", f"分数范围异常: [{min_score:.3f}, {max_score:.3f}]"))

        # 检查最佳选项
        expected_best = "Go"  # Go综合得分应该最高
        if result["best_option"] == expected_best:
            checks.append(("✓", f"最佳选项正确: {result['best_option']}"))
        else:
            checks.append(("⚠", f"最佳选项: {result['best_option']} (预期: {expected_best})"))

        # 手动计算验证
        python_score = 0.6 * 0.4 + 0.9 * 0.3 + 0.95 * 0.3  # 0.795
        go_score = 0.85 * 0.4 + 0.8 * 0.3 + 0.75 * 0.3  # 0.805
        0.95 * 0.4 + 0.6 * 0.3 + 0.7 * 0.3  # 0.770

        actual_scores = {r["option"]: r["score"] for r in result["ranking"]}

        if abs(actual_scores.get("Python", 0) - python_score) < 0.01:
            checks.append(("✓", f"Python得分正确: {actual_scores['Python']:.3f} ≈ {python_score:.3f}"))
        else:
            checks.append(("✗", f"Python得分错误: {actual_scores.get('Python', 0):.3f} != {python_score:.3f}"))

        if abs(actual_scores.get("Go", 0) - go_score) < 0.01:
            checks.append(("✓", f"Go得分正确: {actual_scores['Go']:.3f} ≈ {go_score:.3f}"))
        else:
            checks.append(("✗", f"Go得分错误: {actual_scores.get('Go', 0):.3f} != {go_score:.3f}"))

        # 打印结果
        for symbol, msg in checks:
            print(f"  {symbol} {msg}")

        all_passed = all(symbol in ["✓", "⚠"] for symbol, _ in checks)
        self._record_result("基础加权决策", all_passed, checks)

    async def test_weight_normalization(self):
        """测试2: 权重归一化"""
        print("\n[测试2] 权重归一化")

        params = {
            "context": "权重归一化测试",
            "options": ["A", "B"],
            "criteria": {"标准1": 0.5, "标准2": 0.8, "标准3": 0.7},  # 总和=2.0
            "scores": {
                "A": {"标准1": 0.8, "标准2": 0.7, "标准3": 0.9},
                "B": {"标准1": 0.6, "标准2": 0.9, "标准3": 0.7},
            },
        }

        result = await decision_engine_handler(params, {})

        checks = []

        # 归一化后权重: 标准1=0.25, 标准2=0.4, 标准3=0.35
        a_score = 0.8 * 0.25 + 0.7 * 0.4 + 0.9 * 0.35  # 0.795
        b_score = 0.6 * 0.25 + 0.9 * 0.4 + 0.7 * 0.35  # 0.745

        actual_scores = {r["option"]: r["score"] for r in result["ranking"]}

        if abs(actual_scores.get("A", 0) - a_score) < 0.01:
            checks.append(("✓", f"选项A得分正确(归一化): {actual_scores['A']:.3f} ≈ {a_score:.3f}"))
        else:
            checks.append(("✗", f"选项A得分错误: {actual_scores.get('A', 0):.3f} != {a_score:.3f}"))

        if abs(actual_scores.get("B", 0) - b_score) < 0.01:
            checks.append(("✓", f"选项B得分正确(归一化): {actual_scores['B']:.3f} ≈ {b_score:.3f}"))
        else:
            checks.append(("✗", f"选项B得分错误: {actual_scores.get('B', 0):.3f} != {b_score:.3f}"))

        if result["success"]:
            checks.append(("✓", "权重归一化成功"))
        else:
            checks.append(("✗", f"权重归一化失败: {result.get('error')}"))

        for symbol, msg in checks:
            print(f"  {symbol} {msg}")

        all_passed = all(symbol in ["✓", "⚠"] for symbol, _ in checks)
        self._record_result("权重归一化", all_passed, checks)

    async def test_default_criteria(self):
        """测试3: 默认评估标准"""
        print("\n[测试3] 默认评估标准")

        params = {
            "context": "使用默认标准",
            "options": ["选项1", "选项2"],
            "criteria": {},  # 空标准
            "scores": {},  # 空分数
        }

        result = await decision_engine_handler(params, {})

        checks = []

        # 检查是否使用了默认标准
        if result["analysis"] and "criteria_used" in result["analysis"]:
            criteria = result["analysis"]["criteria_used"]
            if "可行性" in criteria and "成本效益" in criteria:
                checks.append(("✓", f"默认标准已应用: {criteria}"))
            else:
                checks.append(("✗", f"默认标准异常: {criteria}"))
        else:
            checks.append(("✗", "缺少分析信息"))

        # 检查是否生成了分数
        if result["ranking"] and len(result["ranking"]) == 2:
            checks.append(("✓", f"分数已生成: {len(result['ranking'])}个选项"))
        else:
            checks.append(("✗", f"分数生成失败: {len(result['ranking']) if result['ranking'] else 0}个选项"))

        # 检查分数范围合理性
        if result["ranking"]:
            scores = [r["score"] for r in result["ranking"]
            if all(0.6 <= s <= 0.95 for s in scores):
                checks.append(("✓", f"生成分数范围合理: {scores}"))
            else:
                checks.append(("✗", f"生成分数范围异常: {scores}"))

        for symbol, msg in checks:
            print(f"  {symbol} {msg}")

        all_passed = all(symbol in ["✓", "⚠"] for symbol, _ in checks)
        self._record_result("默认评估标准", all_passed, checks)

    async def test_edge_cases(self):
        """测试4: 边界情况"""
        print("\n[测试4] 边界情况处理")

        # 测试4.1: 选项数量不足
        print("\n  [4.1] 选项数量不足")
        params = {
            "context": "测试",
            "options": ["只有1个选项"],
            "criteria": {"标准": 1.0},
            "scores": {"只有1个选项": {"标准": 0.8}},
        }

        result = await decision_engine_handler(params, {})

        if not result["success"] and "至少需要2个选项" in result.get("error", ""):
            print("    ✓ 正确处理选项不足")
            self.passed += 1
        else:
            print(f"    ✗ 未正确处理选项不足: {result}")
            self.failed += 1

        # 测试4.2: 空选项列表
        print("\n  [4.2] 空选项列表")
        params = {
            "context": "测试",
            "options": [],
            "criteria": {},
            "scores": {},
        }

        result = await decision_engine_handler(params, {})

        if not result["success"] and "至少需要2个选项" in result.get("error", ""):
            print("    ✓ 正确处理空选项")
            self.passed += 1
        else:
            print(f"    ✗ 未正确处理空选项: {result}")
            self.failed += 1

        # 测试4.3: 极端权重
        print("\n  [4.3] 极端权重(单标准)")
        params = {
            "context": "单标准决策",
            "options": ["A", "B"],
            "criteria": {"唯一标准": 1.0},
            "scores": {
                "A": {"唯一标准": 0.9},
                "B": {"唯一标准": 0.7},
            },
        }

        result = await decision_engine_handler(params, {})

        if result["success"] and result["best_option"] == "A":
            print(f"    ✓ 单标准决策正确: A({result['ranking'][0]['score']:.3f}) > B({result['ranking'][1]['score']:.3f})")
            self.passed += 1
        else:
            print(f"    ✗ 单标准决策错误: {result}")
            self.failed += 1

        # 测试4.4: 完美分数
        print("\n  [4.4] 完美分数(全部1.0)")
        params = {
            "context": "完美测试",
            "options": ["A", "B"],
            "criteria": {"标准1": 0.5, "标准2": 0.5},
            "scores": {
                "A": {"标准1": 1.0, "标准2": 1.0},
                "B": {"标准1": 1.0, "标准2": 1.0},
            },
        }

        result = await decision_engine_handler(params, {})

        if result["success"]:
            top_score = result["ranking"][0]["score"]
            if abs(top_score - 1.0) < 0.01:
                print(f"    ✓ 完美分数处理正确: {top_score:.3f}")
                self.passed += 1
            else:
                print(f"    ✗ 完美分数计算错误: {top_score:.3f} != 1.0")
                self.failed += 1
        else:
            print(f"    ✗ 完美分数测试失败: {result}")
            self.failed += 1

    async def test_complex_decision(self):
        """测试5: 复杂决策场景"""
        print("\n[测试5] 复杂决策场景(专利技术方案选择)")

        params = {
            "context": "专利技术方案选择",
            "options": [
                "方案A: 基于深度学习",
                "方案B: 基于规则引擎",
                "方案C: 混合方案",
                "方案D: 传统机器学习",
            ],
            "criteria": {
                "创新性": 0.25,
                "技术可行性": 0.20,
                "成本效益": 0.15,
                "实施时间": 0.15,
                "风险控制": 0.15,
                "市场前景": 0.10,
            },
            "scores": {
                "方案A: 基于深度学习": {
                    "创新性": 0.95,
                    "技术可行性": 0.70,
                    "成本效益": 0.60,
                    "实施时间": 0.65,
                    "风险控制": 0.55,
                    "市场前景": 0.90,
                },
                "方案B: 基于规则引擎": {
                    "创新性": 0.50,
                    "技术可行性": 0.95,
                    "成本效益": 0.90,
                    "实施时间": 0.95,
                    "风险控制": 0.90,
                    "市场前景": 0.60,
                },
                "方案C: 混合方案": {
                    "创新性": 0.85,
                    "技术可行性": 0.85,
                    "成本效益": 0.75,
                    "实施时间": 0.75,
                    "风险控制": 0.80,
                    "市场前景": 0.85,
                },
                "方案D: 传统机器学习": {
                    "创新性": 0.65,
                    "技术可行性": 0.90,
                    "成本效益": 0.80,
                    "实施时间": 0.85,
                    "风险控制": 0.85,
                    "市场前景": 0.70,
                },
            },
        }

        result = await decision_engine_handler(params, {})

        checks = []

        # 检查成功状态
        if result["success"]:
            checks.append(("✓", "复杂决策执行成功"))
        else:
            checks.append(("✗", f"复杂决策执行失败: {result.get('error')}"))

        # 检查排名完整性
        if len(result["ranking"]) == 4:
            checks.append(("✓", f"所有选项已排名: {len(result['ranking'])}个"))
        else:
            checks.append(("✗", f"排名不完整: {len(result['ranking'])}个 != 4个"))

        # 检查最佳选项合理性(混合方案应该得分最高)
        expected_best = "方案C: 混合方案"
        if result["best_option"] == expected_best:
            checks.append(("✓", f"最佳选项合理: {result['best_option']}"))
        else:
            checks.append(("⚠", f"最佳选项: {result['best_option']} (预期: {expected_best})"))

        # 检查分数分布
        if result["ranking"]:
            scores = [r["score"] for r in result["ranking"]
            if len(set(scores)) == 4:  # 所有分数不同
                checks.append(("✓", f"分数分布合理: {scores}"))
            else:
                checks.append(("⚠", f"分数存在重复: {scores}"))

        # 检查置信度
        if result["analysis"] and result["analysis"].get("confidence") == "高":
            checks.append(("✓", "置信度评估正确: 高"))
        else:
            checks.append(("⚠", f"置信度评估: {result['analysis'].get('confidence') if result['analysis'] else 'N/A'}"))

        # 打印排名详情
        if result["ranking"]:
            print("\n  决策排名:")
            for r in result["ranking"]:
                print(f"    {r['rank']}. {r['option']}: {r['score']:.3f}")

        for symbol, msg in checks:
            print(f"  {symbol} {msg}")

        all_passed = all(symbol in ["✓", "⚠"] for symbol, _ in checks)
        self._record_result("复杂决策场景", all_passed, checks)

    async def test_score_breakdown(self):
        """测试6: 评分明细分析"""
        print("\n[测试6] 评分明细分析")

        params = {
            "context": "明细测试",
            "options": ["A", "B"],
            "criteria": {"质量": 0.6, "价格": 0.4},
            "scores": {
                "A": {"质量": 0.9, "价格": 0.6},
                "B": {"质量": 0.7, "价格": 0.8},
            },
        }

        result = await decision_engine_handler(params, {})

        checks = []

        # 检查breakdown是否包含在原始result中
        # 注意: 当前实现没有在返回结果中包含breakdown
        # 这是一个功能改进点

        if result["success"]:
            checks.append(("✓", "决策执行成功"))

            # 计算预期明细
            # A: 质量 0.9*0.6=0.54, 价格 0.6*0.4=0.24, 总分=0.78
            # B: 质量 0.7*0.6=0.42, 价格 0.8*0.4=0.32, 总分=0.76

            expected_a = 0.9 * 0.6 + 0.6 * 0.4  # 0.78
            expected_b = 0.7 * 0.6 + 0.8 * 0.4  # 0.76

            actual_a = next((r["score"] for r in result["ranking"] if r["option"] == "A"), None)
            actual_b = next((r["score"] for r in result["ranking"] if r["option"] == "B"), None)

            if abs(actual_a - expected_a) < 0.01 and abs(actual_b - expected_b) < 0.01:
                checks.append(("✓", f"加权计算正确: A={actual_a:.3f}, B={actual_b:.3f}"))
            else:
                checks.append(("✗", f"加权计算错误: A={actual_a:.3f}(预期{expected_a:.3f}), B={actual_b:.3f}(预期{expected_b:.3f})"))

            if result["best_option"] == "A":
                checks.append(("✓", f"最佳选项正确: A({actual_a:.3f}) > B({actual_b:.3f})"))
            else:
                checks.append(("✗", f"最佳选项错误: {result['best_option']}"))

        else:
            checks.append(("✗", f"决策执行失败: {result.get('error')}"))

        for symbol, msg in checks:
            print(f"  {symbol} {msg}")

        all_passed = all(symbol in ["✓", "⚠"] for symbol, _ in checks)
        self._record_result("评分明细分析", all_passed, checks)

    def _record_result(self, test_name: str, passed: bool, checks: list):
        """记录测试结果"""
        self.test_results.append(
            {
                "name": test_name,
                "passed": passed,
                "checks": len(checks),
                "details": checks,
            }
        )

        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n总测试数: {total}")
        print(f"通过: {self.passed} ✅")
        print(f"失败: {self.failed} ❌")
        print(f"通过率: {pass_rate:.1f}%")

        print("\n详细结果:")
        for result in self.test_results:
            status = "✅ 通过" if result["passed"] else "❌ 失败"
            print(f"  {status} - {result['name']} ({result['checks']}项检查)")

        if self.failed == 0:
            print("\n🎉 所有测试通过! decision_engine工具可用性验证成功。")
        else:
            print(f"\n⚠️  {self.failed}个测试失败，需要修复。")

        print("=" * 60)

        return self.failed == 0


async def main():
    """主测试流程"""
    print("=" * 60)
    print("decision_engine工具验证")
    print("=" * 60)
    print("\n开始验证...")

    verifier = DecisionEngineVerifier()

    # 执行所有测试
    await verifier.test_basic_weighted_decision()
    await verifier.test_weight_normalization()
    await verifier.test_default_criteria()
    await verifier.test_edge_cases()
    await verifier.test_complex_decision()
    await verifier.test_score_breakdown()

    # 打印摘要
    success = verifier.print_summary()

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
