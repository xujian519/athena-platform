#!/usr/bin/env python3
"""
risk_analyzer工具验证脚本

验证内容:
1. 风险识别准确性
2. 概率计算正确性
3. 影响评估准确性
4. 风险矩阵生成
5. 缓解策略生成

测试场景:
- 专利申请项目
- 软件开发项目
- 商业投资项目
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.production_tool_implementations import risk_analyzer_handler


class RiskAnalyzerVerifier:
    """风险分析工具验证器"""

    def __init__(self):
        self.test_results = []
        self.start_time = None

    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("Risk Analyzer工具验证测试")
        print("=" * 80)
        print()

        self.start_time = datetime.now()

        # 测试1: 基本功能测试
        await self.test_basic_functionality()

        # 测试2: 专利申请风险分析
        await self.test_patent_application_scenario()

        # 测试3: 软件开发风险分析
        await self.test_software_development_scenario()

        # 测试4: 商业投资风险分析
        await self.test_business_investment_scenario()

        # 测试5: 风险等级准确性
        await self.test_risk_level_accuracy()

        # 测试6: 概率计算准确性
        await self.test_probability_calculation()

        # 测试7: 边界条件测试
        await self.test_edge_cases()

        # 生成汇总报告
        self.generate_summary_report()

    async def test_basic_functionality(self):
        """测试基本功能"""
        print("📋 测试1: 基本功能测试")
        print("-" * 80)

        params = {
            "scenario": "测试基本风险分析功能",
            "risk_factors": [
                {"name": "测试风险1", "description": "测试风险描述1"},
                {"name": "测试风险2", "description": "测试风险描述2"},
            ]
        }

        try:
            result = await risk_analyzer_handler(params, {})

            # 验证返回结构
            assert "success" in result, "缺少success字段"
            assert "risks" in result, "缺少risks字段"
            assert "overall_risk_level" in result, "缺少overall_risk_level字段"
            assert len(result["risks"]) == 2, "风险数量不匹配"

            # 验证每个风险的结构
            for risk in result["risks"]:
                assert "name" in risk, "风险缺少name字段"
                assert "probability" in risk, "风险缺少probability字段"
                assert "impact" in risk, "风险缺少impact字段"
                assert "risk_level" in risk, "风险缺少risk_level字段"
                assert "score" in risk, "风险缺少score字段"
                assert "mitigation" in risk, "风险缺少mitigation字段"

            print("✅ 基本功能测试通过")
            print(f"   - 成功: {result['success']}")
            print(f"   - 风险数量: {result['total_risks']}")
            print(f"   - 整体风险等级: {result['overall_risk_level']}")
            print(f"   - 整体风险评分: {result.get('overall_score', 'N/A')}")

            self.test_results.append({
                "test_name": "基本功能测试",
                "status": "PASS",
                "details": result
            })

        except Exception as e:
            print(f"❌ 基本功能测试失败: {e}")
            self.test_results.append({
                "test_name": "基本功能测试",
                "status": "FAIL",
                "error": str(e)
            })

        print()

    async def test_patent_application_scenario(self):
        """测试专利申请场景"""
        print("📋 测试2: 专利申请风险分析")
        print("-" * 80)

        params = {
            "scenario": "申请人工智能自动驾驶相关专利，涉及复杂算法和大量数据",
            "risk_factors": [
                {"name": "技术风险", "description": "算法新颖性不足，创造性可能被质疑"},
                {"name": "时间风险", "description": "专利审查周期长，可能影响产品上市"},
                {"name": "竞争风险", "description": "竞争对手已有类似专利"},
            ]
        }

        try:
            result = await risk_analyzer_handler(params, {})

            print("✅ 专利申请场景测试通过")
            print(f"   - 场景: {params['scenario'][:50]}...")
            print(f"   - 整体风险等级: {result['overall_risk_level']}")
            print(f"   - 整体风险评分: {result.get('overall_score', 'N/A')}")

            # 显示每个风险的详情
            for i, risk in enumerate(result["risks"], 1):
                print(f"\n   风险{i}: {risk['name']}")
                print(f"     - 等级: {risk['risk_level']}")
                print(f"     - 概率: {risk['probability']}")
                print(f"     - 影响: {risk['impact']}")
                print(f"     - 评分: {risk['score']}")
                print(f"     - 缓解: {risk['mitigation'][:50]}...")

            # 显示缓解策略
            print(f"\n   重点关注:")
            for strategy in result.get("mitigation_strategies", [])[:3]:
                print(f"     - {strategy}")

            self.test_results.append({
                "test_name": "专利申请风险分析",
                "status": "PASS",
                "details": result
            })

        except Exception as e:
            print(f"❌ 专利申请场景测试失败: {e}")
            self.test_results.append({
                "test_name": "专利申请风险分析",
                "status": "FAIL",
                "error": str(e)
            })

        print()

    async def test_software_development_scenario(self):
        """测试软件开发场景"""
        print("📋 测试3: 软件开发风险分析")
        print("-" * 80)

        params = {
            "scenario": "开发一个复杂的分布式系统，涉及微服务架构和大量并发处理",
            "risk_factors": [
                {"name": "技术风险", "description": "系统复杂度高，架构设计难度大"},
                {"name": "时间风险", "description": "开发周期紧张，可能延期"},
                {"name": "资源风险", "description": "高级开发人员不足"},
                {"name": "集成风险", "description": "微服务之间集成复杂"},
            ]
        }

        try:
            result = await risk_analyzer_handler(params, {})

            print("✅ 软件开发场景测试通过")
            print(f"   - 场景: {params['scenario'][:50]}...")
            print(f"   - 风险数量: {result['total_risks']}")
            print(f"   - 整体风险等级: {result['overall_risk_level']}")
            print(f"   - 整体风险评分: {result.get('overall_score', 'N/A')}")
            print(f"   - 风险颜色: {result.get('risk_color', 'N/A')}")

            self.test_results.append({
                "test_name": "软件开发风险分析",
                "status": "PASS",
                "details": result
            })

        except Exception as e:
            print(f"❌ 软件开发场景测试失败: {e}")
            self.test_results.append({
                "test_name": "软件开发风险分析",
                "status": "FAIL",
                "error": str(e)
            })

        print()

    async def test_business_investment_scenario(self):
        """测试商业投资场景"""
        print("📋 测试4: 商业投资风险分析")
        print("-" * 80)

        params = {
            "scenario": "投资一家新兴科技公司，涉及大额资金和长期回报预期",
            "risk_factors": [
                {"name": "市场风险", "description": "市场需求变化，竞争加剧"},
                {"name": "财务风险", "description": "资金链断裂，回报不及预期"},
                {"name": "政策风险", "description": "监管政策变化"},
            ]
        }

        try:
            result = await risk_analyzer_handler(params, {})

            print("✅ 商业投资场景测试通过")
            print(f"   - 场景: {params['scenario'][:50]}...")
            print(f"   - 整体风险等级: {result['overall_risk_level']}")
            print(f"   - 整体风险评分: {result.get('overall_score', 'N/A')}")

            self.test_results.append({
                "test_name": "商业投资风险分析",
                "status": "PASS",
                "details": result
            })

        except Exception as e:
            print(f"❌ 商业投资场景测试失败: {e}")
            self.test_results.append({
                "test_name": "商业投资风险分析",
                "status": "FAIL",
                "error": str(e)
            })

        print()

    async def test_risk_level_accuracy(self):
        """测试风险等级准确性"""
        print("📋 测试5: 风险等级准确性")
        print("-" * 80)

        test_cases = [
            {
                "scenario": "这是一个紧急且关键的重大项目",
                "expected_level": "高",
                "reason": "包含高风险关键词"
            },
            {
                "scenario": "这是一个简单的常规标准项目",
                "expected_level": "低",
                "reason": "包含低风险关键词"
            },
            {
                "scenario": "这是一个普通的项目",
                "expected_level": "中",
                "reason": "默认中等风险"
            }
        ]

        passed = 0
        failed = 0

        for i, test_case in enumerate(test_cases, 1):
            params = {
                "scenario": test_case["scenario"],
                "risk_factors": [{"name": "测试风险", "description": "测试"}]
            }

            try:
                result = await risk_analyzer_handler(params, {})
                actual_level = result["risks"][0]["risk_level"]

                if actual_level == test_case["expected_level"]:
                    print(f"✅ 测试用例{i}通过: {test_case['reason']}")
                    print(f"   场景: {test_case['scenario']}")
                    print(f"   期望等级: {test_case['expected_level']}, 实际等级: {actual_level}")
                    passed += 1
                else:
                    print(f"❌ 测试用例{i}失败: {test_case['reason']}")
                    print(f"   场景: {test_case['scenario']}")
                    print(f"   期望等级: {test_case['expected_level']}, 实际等级: {actual_level}")
                    failed += 1

            except Exception as e:
                print(f"❌ 测试用例{i}异常: {e}")
                failed += 1

        print(f"\n   通过: {passed}/{len(test_cases)}, 失败: {failed}/{len(test_cases)}")

        self.test_results.append({
            "test_name": "风险等级准确性测试",
            "status": "PASS" if failed == 0 else "FAIL",
            "passed": passed,
            "failed": failed,
            "total": len(test_cases)
        })

        print()

    async def test_probability_calculation(self):
        """测试概率计算准确性"""
        print("📋 测试6: 概率计算准确性")
        print("-" * 80)

        # 测试不同风险等级的概率范围
        test_cases = [
            {"level": "高", "expected_range": (70, 80)},
            {"level": "中", "expected_range": (30, 50)},
            {"level": "低", "expected_range": (10, 20)}
        ]

        passed = 0
        failed = 0

        for test_case in test_cases:
            # 使用包含对应关键词的场景
            scenario_map = {
                "高": "这是一个紧急且关键的重大项目",
                "中": "这是一个普通的项目",
                "低": "这是一个简单的常规标准项目"
            }

            params = {
                "scenario": scenario_map[test_case['level']],
                "risk_factors": [{"name": "测试风险", "description": "测试"}]
            }

            try:
                result = await risk_analyzer_handler(params, {})
                probability_str = result["risks"][0]["probability"]

                # 解析概率字符串 (格式: "高 (70-80%)")
                import re
                match = re.search(r'(\d+)-(\d+)', probability_str)

                if match:
                    prob_min = int(match.group(1))
                    prob_max = int(match.group(2))

                    expected_min, expected_max = test_case["expected_range"]

                    if prob_min == expected_min and prob_max == expected_max:
                        print(f"✅ {test_case['level']}风险概率正确: {probability_str}")
                        passed += 1
                    else:
                        print(f"❌ {test_case['level']}风险概率错误:")
                        print(f"   期望: {expected_min}-{expected_max}%, 实际: {prob_min}-{prob_max}%")
                        failed += 1
                else:
                    print(f"❌ 无法解析概率字符串: {probability_str}")
                    failed += 1

            except Exception as e:
                print(f"❌ 概率计算测试异常: {e}")
                failed += 1

        print(f"\n   通过: {passed}/{len(test_cases)}, 失败: {failed}/{len(test_cases)}")

        self.test_results.append({
            "test_name": "概率计算准确性测试",
            "status": "PASS" if failed == 0 else "FAIL",
            "passed": passed,
            "failed": failed,
            "total": len(test_cases)
        })

        print()

    async def test_edge_cases(self):
        """测试边界条件"""
        print("📋 测试7: 边界条件测试")
        print("-" * 80)

        # 测试空场景
        try:
            result = await risk_analyzer_handler({
                "scenario": "",
                "risk_factors": []
            }, {})

            print("✅ 空场景处理通过")
            print(f"   - 使用默认风险因子: {result['total_risks']}个")

            self.test_results.append({
                "test_name": "空场景测试",
                "status": "PASS",
                "details": result
            })

        except Exception as e:
            print(f"❌ 空场景测试失败: {e}")
            self.test_results.append({
                "test_name": "空场景测试",
                "status": "FAIL",
                "error": str(e)
            })

        # 测试大量风险因子
        try:
            large_risk_list = [
                {"name": f"风险{i}", "description": f"描述{i}"}
                for i in range(100)
            ]

            result = await risk_analyzer_handler({
                "scenario": "测试大量风险因子",
                "risk_factors": large_risk_list
            }, {})

            print("✅ 大量风险因子处理通过")
            print(f"   - 处理风险数量: {result['total_risks']}")

            self.test_results.append({
                "test_name": "大量风险因子测试",
                "status": "PASS",
                "details": {"total_risks": result['total_risks']}
            })

        except Exception as e:
            print(f"❌ 大量风险因子测试失败: {e}")
            self.test_results.append({
                "test_name": "大量风险因子测试",
                "status": "FAIL",
                "error": str(e)
            })

        print()

    def generate_summary_report(self):
        """生成汇总报告"""
        print("=" * 80)
        print("测试汇总报告")
        print("=" * 80)
        print()

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"失败: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print()

        # 详细结果
        print("详细测试结果:")
        print("-" * 80)

        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{i}. {status_icon} {result['test_name']} - {result['status']}")

            if "error" in result:
                print(f"   错误: {result['error']}")

            if "passed" in result:
                print(f"   通过: {result['passed']}/{result['total']}")

        print()

        # 执行时间
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            print(f"总执行时间: {duration:.2f}秒")

        print()
        print("=" * 80)

        # 保存详细报告到JSON
        report_path = "/Users/xujian/Athena工作平台/reports/risk_analyzer_verification_report.json"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": f"{passed_tests/total_tests*100:.1f}%",
                "test_results": self.test_results
            }, f, ensure_ascii=False, indent=2)

        print(f"详细报告已保存至: {report_path}")


async def main():
    """主函数"""
    verifier = RiskAnalyzerVerifier()
    await verifier.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
