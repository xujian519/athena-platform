#!/usr/bin/env python3
"""
集成测试脚本
测试小诺法律智能支持系统的各项功能
作者: 小诺·双鱼座
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegalSystemTester:
    """法律系统测试器"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.test_results = []
        self.performance_metrics = {}

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行集成测试...")

        # 基础功能测试
        await self.test_health_check()
        await self.test_legal_search()
        await self.test_legal_qa()
        await self.test_prompt_generation()
        await self.test_rule_basis()
        await self.test_related_laws()

        # 高级功能测试
        await self.test_agent_support()
        await self.test_batch_query()
        await self.test_complex_queries()

        # 性能测试
        await self.test_performance()

        # 生成测试报告
        self.generate_test_report()

    async def test_health_check(self):
        """测试健康检查"""
        logger.info("✨ 测试健康检查接口...")

        try:
            response = requests.get(f"{self.api_base_url}/health")

            if response.status_code == 200:
                data = response.json()
                self._record_test_result("健康检查", True, "服务正常响应")
                logger.info(f"✅ 健康检查通过: {data}")
            else:
                self._record_test_result("健康检查", False, f"状态码: {response.status_code}")
                logger.error(f"❌ 健康检查失败: {response.status_code}")

        except Exception as e:
            self._record_test_result("健康检查", False, str(e))
            logger.error(f"❌ 健康检查异常: {e}")

    async def test_legal_search(self):
        """测试法律搜索"""
        logger.info("✨ 测试法律搜索功能...")

        test_cases = [
            {"query": "离婚财产分割", "search_type": "hybrid"},
            {"query": "劳动合同", "search_type": "vector"},
            {"query": "民法典", "search_type": "graph"}
        ]

        for case in test_cases:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.api_base_url}/api/v1/search",
                    json=case
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    self._record_test_result(
                        f"法律搜索({case['search_type']})",
                        True,
                        f"返回{data['total']}个结果，耗时{response_time:.2f}秒"
                    )
                    self._record_performance("search", response_time, data["total"])
                    logger.info(f"✅ 搜索测试通过: {case['query']} - {data['total']}个结果")
                else:
                    self._record_test_result(
                        f"法律搜索({case['search_type']})",
                        False,
                        f"状态码: {response.status_code}"
                    )
                    logger.error(f"❌ 搜索测试失败: {response.status_code}")

            except Exception as e:
                self._record_test_result(f"法律搜索({case['search_type']})", False, str(e))
                logger.error(f"❌ 搜索测试异常: {e}")

    async def test_legal_qa(self):
        """测试法律问答"""
        logger.info("✨ 测试法律问答功能...")

        test_questions = [
            "离婚时财产如何分割？",
            "劳动合同解除需要什么条件？",
            "租赁合同的违约责任有哪些？",
            "如何申请劳动仲裁？"
        ]

        for question in test_questions:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.api_base_url}/api/v1/qa",
                    json={
                        "query": question,
                        "agent_id": "test_agent",
                        "session_id": "test_session"
                    }
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    self._record_test_result(
                        "法律问答",
                        True,
                        f"置信度: {data['confidence']:.2f}，耗时{response_time:.2f}秒"
                    )
                    self._record_performance("qa", response_time, data["confidence"])
                    logger.info(f"✅ 问答测试通过: {question[:20]}... - 置信度{data['confidence']:.2f}")
                else:
                    self._record_test_result("法律问答", False, f"状态码: {response.status_code}")
                    logger.error(f"❌ 问答测试失败: {response.status_code}")

            except Exception as e:
                self._record_test_result("法律问答", False, str(e))
                logger.error(f"❌ 问答测试异常: {e}")

    async def test_prompt_generation(self):
        """测试提示词生成"""
        logger.info("✨ 测试提示词生成功能...")

        test_cases = [
            {"query": "合同违约如何处理？", "query_type": "法律咨询"},
            {"query": "解释民法典第一条", "query_type": "条文解释"},
            {"query": "起诉流程", "query_type": "程序指导"}
        ]

        for case in test_cases:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.api_base_url}/api/v1/prompt",
                    json=case
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    prompt_length = len(data["prompt"])
                    self._record_test_result(
                        "提示词生成",
                        True,
                        f"生成{prompt_length}字符的提示词，耗时{response_time:.2f}秒"
                    )
                    self._record_performance("prompt", response_time, prompt_length)
                    logger.info(f"✅ 提示词生成成功: {data['type']} - {prompt_length}字符")
                else:
                    self._record_test_result("提示词生成", False, f"状态码: {response.status_code}")
                    logger.error(f"❌ 提示词生成失败: {response.status_code}")

            except Exception as e:
                self._record_test_result("提示词生成", False, str(e))
                logger.error(f"❌ 提示词生成异常: {e}")

    async def test_rule_basis(self):
        """测试规则依据查询"""
        logger.info("✨ 测试规则依据查询...")

        test_rules = [
            "劳动合同",
            "房屋买卖",
            "离婚程序"
        ]

        for rule in test_rules:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.api_base_url}/api/v1/rules",
                    params={"query": rule}
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    self._record_test_result(
                        "规则依据查询",
                        True,
                        f"找到{data['summary']['total_rules']}条规则，耗时{response_time:.2f}秒"
                    )
                    logger.info(f"✅ 规则查询成功: {rule} - {data['summary']['total_rules']}条")
                else:
                    self._record_test_result("规则依据查询", False, f"状态码: {response.status_code}")
                    logger.error(f"❌ 规则查询失败: {response.status_code}")

            except Exception as e:
                self._record_test_result("规则依据查询", False, str(e))
                logger.error(f"❌ 规则查询异常: {e}")

    async def test_related_laws(self):
        """测试相关法律查询"""
        logger.info("✨ 测试相关法律查询...")

        test_laws = [
            "民法典",
            "劳动合同法",
            "刑法"
        ]

        for law in test_laws:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{self.api_base_url}/api/v1/related-laws/{law}"
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    self._record_test_result(
                        "相关法律查询",
                        True,
                        f"找到{data['count']}个相关法律，耗时{response_time:.2f}秒"
                    )
                    logger.info(f"✅ 相关法律查询成功: {law} - {data['count']}个")
                else:
                    self._record_test_result("相关法律查询", False, f"状态码: {response.status_code}")
                    logger.error(f"❌ 相关法律查询失败: {response.status_code}")

            except Exception as e:
                self._record_test_result("相关法律查询", False, str(e))
                logger.error(f"❌ 相关法律查询异常: {e}")

    async def test_agent_support(self):
        """测试智能体支持"""
        logger.info("✨ 测试智能体支持功能...")

        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/agent/support",
                json={
                    "query": "如何处理合同纠纷？",
                    "agent_id": "test_agent_001",
                    "context": {"user_type": "individual"}
                }
            )

            if response.status_code == 200:
                data = response.json()
                self._record_test_result(
                    "智能体支持",
                    True,
                    f"提供增强支持，置信度: {data.get('confidence', 0):.2f}"
                )
                logger.info("✅ 智能体支持测试通过")
            else:
                self._record_test_result("智能体支持", False, f"状态码: {response.status_code}")
                logger.error(f"❌ 智能体支持测试失败: {response.status_code}")

        except Exception as e:
            self._record_test_result("智能体支持", False, str(e))
            logger.error(f"❌ 智能体支持测试异常: {e}")

    async def test_batch_query(self):
        """测试批量查询"""
        logger.info("✨ 测试批量查询功能...")

        test_queries = [
            "什么是诉讼时效？",
            "合同无效的情形有哪些？",
            "如何申请专利？",
            "房产证办理流程",
            "交通事故赔偿标准"
        ]

        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base_url}/api/v1/batch/query",
                json=test_queries
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                avg_time = response_time / len(test_queries)
                self._record_test_result(
                    "批量查询",
                    True,
                    f"处理{len(test_queries)}个查询，平均耗时{avg_time:.2f}秒/个"
                )
                self._record_performance("batch", response_time, len(test_queries))
                logger.info(f"✅ 批量查询成功: {data['total']}个查询")
            else:
                self._record_test_result("批量查询", False, f"状态码: {response.status_code}")
                logger.error(f"❌ 批量查询失败: {response.status_code}")

        except Exception as e:
            self._record_test_result("批量查询", False, str(e))
            logger.error(f"❌ 批量查询异常: {e}")

    async def test_complex_queries(self):
        """测试复杂查询"""
        logger.info("✨ 测试复杂查询场景...")

        complex_scenarios = [
            {
                "name": "多条件查询",
                "request": {
                    "query": "买卖合同",
                    "search_type": "hybrid",
                    "filters": {
                        "source": ["vector_search"],
                        "min_similarity": 0.7
                    }
                }
            },
            {
                "name": "对话上下文查询",
                "request": {
                    "query": "那具体需要什么材料？",
                    "conversation_history": [
                        {"role": "user", "content": "如何办理离婚？"},
                        {"role": "assistant", "content": "需要准备结婚证、身份证等材料..."}
                    ]
                }
            }
        ]

        for scenario in complex_scenarios:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.api_base_url}/api/v1/qa",
                    json=scenario["request"]
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    self._record_test_result(
                        f"复杂查询({scenario['name']})",
                        True,
                        f"置信度: {data['confidence']:.2f}，耗时{response_time:.2f}秒"
                    )
                    logger.info(f"✅ {scenario['name']}测试通过")
                else:
                    self._record_test_result(
                        f"复杂查询({scenario['name']})",
                        False,
                        f"状态码: {response.status_code}"
                    )
                    logger.error(f"❌ {scenario['name']}测试失败: {response.status_code}")

            except Exception as e:
                self._record_test_result(f"复杂查询({scenario['name']})", False, str(e))
                logger.error(f"❌ {scenario['name']}测试异常: {e}")

    async def test_performance(self):
        """测试性能"""
        logger.info("✨ 运行性能测试...")

        # 并发测试
        concurrent_requests = 10
        queries = ["法律咨询"] * concurrent_requests

        try:
            start_time = time.time()
            tasks = []
            for i, query in enumerate(queries):
                task = self._make_request("/api/v1/qa", {
                    "query": f"{query} {i}",
                    "agent_id": f"perf_test_{i}"
                })
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            success_count = sum(1 for r in results if not isinstance(r, Exception))
            avg_time = total_time / concurrent_requests

            self._record_test_result(
                "并发性能测试",
                success_count == concurrent_requests,
                f"成功{success_count}/{concurrent_requests}，平均耗时{avg_time:.2f}秒"
            )
            self._record_performance("concurrent", avg_time, concurrent_requests)

            logger.info(f"✅ 并发测试完成: {success_count}/{concurrent_requests}成功")

        except Exception as e:
            self._record_test_result("并发性能测试", False, str(e))
            logger.error(f"❌ 并发测试异常: {e}")

    async def _make_request(self, endpoint: str, data: dict):
        """异步请求"""
        return requests.post(f"{self.api_base_url}{endpoint}", json=data)

    def _record_test_result(self, test_name: str, success: bool, details: str):
        """记录测试结果"""
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })

    def _record_performance(self, operation: str, time_taken: float, metric_value: Any):
        """记录性能指标"""
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = []

        self.performance_metrics[operation].append({
            "time": time_taken,
            "value": metric_value,
            "timestamp": time.time()
        })

    def generate_test_report(self):
        """生成测试报告"""
        logger.info("\n" + "="*80)
        logger.info("📊 小诺法律智能支持系统 - 集成测试报告")
        logger.info("="*80)

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        logger.info("\n📋 测试统计:")
        logger.info(f"  • 总测试数: {total_tests}")
        logger.info(f"  • 通过: {passed_tests}")
        logger.info(f"  • 失败: {failed_tests}")
        logger.info(f"  • 成功率: {success_rate:.1f}%")

        # 详细结果
        logger.info("\n📝 详细结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"  {status} {result['test_name']}: {result['details']}")

        # 性能指标
        logger.info("\n⚡ 性能指标:")
        for operation, metrics in self.performance_metrics.items():
            if metrics:
                avg_time = sum(m["time"] for m in metrics) / len(metrics)
                min_time = min(m["time"] for m in metrics)
                max_time = max(m["time"] for m in metrics)
                logger.info(f"  {operation}:")
                logger.info(f"    • 平均耗时: {avg_time:.2f}秒")
                logger.info(f"    • 最快: {min_time:.2f}秒")
                logger.info(f"    • 最慢: {max_time:.2f}秒")
                logger.info(f"    • 执行次数: {len(metrics)}")

        # 生成JSON报告文件
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate
            },
            "test_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "timestamp": time.time()
        }

        report_path = Path("test_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 详细报告已保存到: {report_path}")
        logger.info("\n" + "="*80)

        # 根据测试结果给出建议
        if success_rate >= 90:
            logger.info("🎉 系统表现优秀，可以投入使用！")
        elif success_rate >= 70:
            logger.info("⚠️ 系统基本可用，建议优化失败项。")
        else:
            logger.info("🚨 系统存在问题，需要进一步调试和优化。")


# 主函数
async def main():
    """运行测试"""
    tester = LegalSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
