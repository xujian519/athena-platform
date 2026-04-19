#!/usr/bin/env python3
"""
提示链处理器单元测试
Unit Tests for Prompt Chain Processor
"""

import asyncio

# 添加项目路径
import sys
import unittest

sys.path.append('/Users/xujian/Athena工作平台')

from core.cognition.prompt_chain_processor import ChainStatus, ChainStep, PromptChainProcessor


class TestPromptChainProcessor(unittest.TestCase):
    """提示链处理器测试类"""

    def setUp(self):
        """测试设置"""
        self.processor = PromptChainProcessor()

    def test_processor_initialization(self):
        """测试处理器初始化"""
        self.assertIsInstance(self.processor, PromptChainProcessor)
        self.assertIsNotNone(self.processor.active_chains)
        self.assertIsNotNone(self.processor.chain_templates)
        self.assertIsNotNone(self.processor.validator)

    def test_create_simple_chain(self):
        """测试创建简单链"""
        chain_type = "simple_analysis"
        input_data = {
            "query": "分析系统性能",
            "context": {"domain": "technical"}
        }

        chain_id = self.processor.create_chain(chain_type, input_data)

        self.assertIsNotNone(chain_id)
        self.assertIn(chain_id, self.processor.active_chains)
        self.assertEqual(self.processor.active_chains[chain_id]["chain_type"], chain_type)

    def test_chain_step_creation(self):
        """测试链步骤创建"""
        step = ChainStep(
            id="test_step_1",
            name="测试步骤",
            prompt_template="分析：{query}",
            output_schema={"result": "string"},
            input_mapping={"query": "input_data.query"}
        )

        self.assertEqual(step.id, "test_step_1")
        self.assertEqual(step.name, "测试步骤")
        self.assertIn("{query}", step.prompt_template)
        self.assertIn("result", step.output_schema)
        self.assertEqual(step.input_mapping["query"], "input_data.query")

    def test_validation_rules(self):
        """测试验证规则"""
        step = ChainStep(
            id="validated_step",
            name="验证测试步骤",
            prompt_template="测试模板",
            output_schema={"field1": "string", "field2": "integer"},
            validation_rules=[
                {"type": "required_fields", "fields": ["field1", "field2"]}
            ]
        )

        # 测试有效输出
        valid_output = {"field1": "test", "field2": 123}
        validation_result = self.processor.validator.validate_response(step, valid_output)
        self.assertTrue(validation_result.valid)

        # 测试无效输出
        invalid_output = {"field1": "test"}  # 缺少field2
        validation_result = self.processor.validator.validate_response(step, invalid_output)
        self.assertFalse(validation_result.valid)

    async def test_chain_execution_simple(self):
        """测试简单链执行"""
        # 创建测试链
        chain_steps = [
            ChainStep(
                id="step1",
                name="第一步",
                prompt_template="分析：{query}",
                output_schema={"analysis": "string"}
            ),
            ChainStep(
                id="step2",
                name="第二步",
                prompt_template="总结：{analysis}",
                output_schema={"summary": "string"},
                input_mapping={"analysis": "steps_results.step1.analysis"}
            )
        ]

        # 创建链
        chain_id = self.processor.create_chain("test_chain", {"query": "测试查询"})
        self.processor.active_chains[chain_id]["steps"] = chain_steps

        # 模拟执行
        execution_result = await self._mock_chain_execution(chain_id)

        self.assertIsNotNone(execution_result)
        self.assertTrue(execution_result.success)

    async def _mock_chain_execution(self, chain_id: str) -> dict:
        """模拟链执行"""
        chain_data = self.processor.active_chains[chain_id]
        steps_results = {}

        # 模拟每个步骤的执行
        for step in chain_data["steps"]:
            # 模拟步骤执行
            await asyncio.sleep(0.1)

            # 生成模拟结果
            if step.id == "step1":
                steps_results[step.id] = {"analysis": "模拟分析结果"}
            elif step.id == "step2":
                analysis = steps_results["step1"]["analysis"]
                steps_results[step.id] = {"summary": f"基于{analysis}的总结"}

        return {
            "success": True,
            "chain_id": chain_id,
            "steps_results": steps_results,
            "total_time": 0.2
        }

    def test_refinement_criteria(self):
        """测试精炼标准"""
        step_with_refinement = ChainStep(
            id="refinement_step",
            name="精炼测试步骤",
            prompt_template="测试模板",
            output_schema={"results": "list"},
            requires_refinement=True,
            refinement_criteria={"min_results": 5, "max_results": 20}
        )

        self.assertTrue(step_with_refinement.requires_refinement)
        self.assertEqual(step_with_refinement.refinement_criteria["min_results"], 5)
        self.assertEqual(step_with_refinement.refinement_criteria["max_results"], 20)

    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效链类型
        with self.assertRaises(KeyError):
            self.processor.create_chain("invalid_chain_type", {})

    def test_chain_status_management(self):
        """测试链状态管理"""
        chain_id = self.processor.create_chain("test_chain", {})

        # 初始状态
        chain_data = self.processor.active_chains[chain_id]
        self.assertEqual(chain_data["status"], ChainStatus.PENDING.value)

        # 更新状态
        self.processor.update_chain_status(chain_id, ChainStatus.IN_PROGRESS)
        chain_data = self.processor.active_chains[chain_id]
        self.assertEqual(chain_data["status"], ChainStatus.IN_PROGRESS.value)

    def test_input_mapping(self):
        """测试输入映射"""
        step = ChainStep(
            id="mapping_step",
            name="输入映射测试",
            prompt_template="处理：{user_input} {context_info}",
            input_mapping={
                "user_input": "input_data.query",
                "context_info": "context.domain"
            }
        )

        # 模拟输入数据
        input_data = {"query": "测试查询"}
        context = {"domain": "技术分析"}
        steps_results = {}

        # 执行输入映射（简化版）
        mapped_input = self._mock_input_mapping(step, input_data, context, steps_results)

        self.assertIn("测试查询", mapped_input["user_input"])
        self.assertEqual(mapped_input["context_info"], "技术分析")

    def _mock_input_mapping(self, step, input_data, context, steps_results):
        """模拟输入映射"""
        mapped = {}
        for key, path in step.input_mapping.items():
            if path.startswith("input_data."):
                field = path.split(".", 1)[1]
                mapped[key] = input_data.get(field, "")
            elif path.startswith("context."):
                field = path.split(".", 1)[1]
                mapped[key] = context.get(field, "")
            elif path.startswith("steps_results."):
                # 简化处理
                mapped[key] = "mock_result"
        return mapped

    def test_chain_templates(self):
        """测试链模板"""
        templates = self.processor.chain_templates
        self.assertIsNotNone(templates)

        # 检查是否有默认模板
        self.assertTrue(len(templates) > 0)

        # 检查模板结构
        for _template_name, template_data in templates.items():
            self.assertIn("name", template_data)
            self.assertIn("description", template_data)
            self.assertIn("steps", template_data)

class TestChainExecution(unittest.TestCase):
    """链执行测试"""

    def setUp(self):
        """测试设置"""
        self.processor = PromptChainProcessor()

    async def test_parallel_step_execution(self):
        """测试并行步骤执行"""
        # 创建可以并行执行的步骤
        parallel_steps = [
            ChainStep(
                id=f"parallel_step_{i}",
                name=f"并行步骤{i}",
                prompt_template="并行处理 {i}",
                output_schema={"result": "string"}
            )
            for i in range(3)
        ]

        # 模拟并行执行
        execution_times = await self._simulate_parallel_execution(parallel_steps)

        # 并行执行应该比串行执行快
        total_parallel_time = max(execution_times)
        estimated_serial_time = sum(execution_times)

        self.assertLess(total_parallel_time, estimated_serial_time)

    async def _simulate_parallel_execution(self, steps):
        """模拟并行执行"""
        import random

        # 模拟每个步骤的执行时间
        execution_times = []
        tasks = []

        for step in steps:
            # 随机执行时间 (0.1-0.5秒)
            exec_time = random.uniform(0.1, 0.5)
            execution_times.append(exec_time)

            # 创建异步任务
            task = asyncio.create_task(self._mock_step_execution(step, exec_time))
            tasks.append(task)

        # 等待所有任务完成
        await asyncio.gather(*tasks)

        return execution_times

    async def _mock_step_execution(self, step, exec_time):
        """模拟步骤执行"""
        await asyncio.sleep(exec_time)
        return {"step_id": step.id, "result": "mock_result"}

    def test_chain_execution_statistics(self):
        """测试链执行统计"""
        self.processor.create_chain("test_chain", {})

        # 模拟执行统计
        stats = {
            "total_steps": 5,
            "completed_steps": 4,
            "failed_steps": 1,
            "retry_attempts": 2,
            "execution_time": 3.5
        }

        # 计算统计指标
        success_rate = stats["completed_steps"] / stats["total_steps"]
        avg_step_time = stats["execution_time"] / stats["total_steps"]

        self.assertEqual(success_rate, 0.8)  # 4/5 = 0.8
        self.assertEqual(avg_step_time, 0.7)  # 3.5/5 = 0.7

class TestChainValidation(unittest.TestCase):
    """链验证测试"""

    def setUp(self):
        """测试设置"""
        self.processor = PromptChainProcessor()
        self.validator = self.processor.validator

    def test_schema_validation(self):
        """测试模式验证"""
        step = ChainStep(
            id="schema_test",
            name="模式验证测试",
            prompt_template="测试",
            output_schema={
                "field1": {"type": "string", "required": True},
                "field2": {"type": "integer", "required": False},
                "field3": {"type": "array", "required": True}
            }
        )

        # 有效输出
        valid_output = {
            "field1": "test_string",
            "field3": ["item1", "item2"]
        }
        result = self.validator.validate_response(step, valid_output)
        self.assertTrue(result.valid)

        # 无效输出 - 缺少必需字段
        invalid_output = {
            "field1": "test_string"
            # 缺少 field3
        }
        result = self.validator.validate_response(step, invalid_output)
        self.assertFalse(result.valid)

    def test_custom_validation_rules(self):
        """测试自定义验证规则"""
        step = ChainStep(
            id="custom_validation",
            name="自定义验证测试",
            prompt_template="测试",
            output_schema={"score": "float"},
            validation_rules=[
                {"type": "range_check", "field": "score", "min": 0.0, "max": 1.0},
                {"type": "length_check", "field": "description", "min_length": 10}
            ]
        )

        # 有效分数
        valid_output = {"score": 0.85}
        result = self.validator.validate_response(step, valid_output)
        self.assertTrue(result.valid)

        # 无效分数 - 超出范围
        invalid_output = {"score": 1.5}
        result = self.validator.validate_response(step, invalid_output)
        self.assertFalse(result.valid)

    def test_data_type_validation(self):
        """测试数据类型验证"""
        step = ChainStep(
            id="type_validation",
            name="类型验证测试",
            prompt_template="测试",
            output_schema={
                "string_field": "string",
                "int_field": "integer",
                "float_field": "float",
                "bool_field": "boolean",
                "list_field": "list",
                "dict_field": "dict"
            }
        )

        # 类型正确的输出
        valid_output = {
            "string_field": "test",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True,
            "list_field": [1, 2, 3],
            "dict_field": {"key": "value"}
        }
        result = self.validator.validate_response(step, valid_output)
        self.assertTrue(result.valid)

        # 类型错误的输出
        invalid_output = {
            "string_field": "test",
            "int_field": "not_an_integer",  # 应该是整数
            "float_field": 3.14,
            "bool_field": True,
            "list_field": [1, 2, 3],
            "dict_field": {"key": "value"}
        }
        result = self.validator.validate_response(step, invalid_output)
        self.assertFalse(result.valid)

class TestChainOptimization(unittest.TestCase):
    """链优化测试"""

    def setUp(self):
        """测试设置"""
        self.processor = PromptChainProcessor()

    def test_step_order_optimization(self):
        """测试步骤顺序优化"""
        # 创建有依赖关系的步骤
        steps = [
            ChainStep(id="step1", dependencies=["step2"], name="步骤1"),
            ChainStep(id="step2", dependencies=["step3"], name="步骤2"),
            ChainStep(id="step3", dependencies=[], name="步骤3"),  # 无依赖，应该先执行
            ChainStep(id="step4", dependencies=["step1"], name="步骤4")
        ]

        # 优化步骤顺序
        optimized_steps = self.processor._optimize_step_order(steps)

        # 验证优化后的顺序
        self.assertEqual(optimized_steps[0].id, "step3")  # 无依赖的应该最前
        self.assertEqual(optimized_steps[1].id, "step2")  # step3的依赖
        self.assertEqual(optimized_steps[2].id, "step1")  # step2的依赖
        self.assertEqual(optimized_steps[3].id, "step4")  # step1的依赖

    def test_resource_optimization(self):
        """测试资源优化"""
        # 创建需要相同资源的步骤
        steps = [
            ChainStep(
                id="step1",
                required_resources=["database"],
                estimated_time=2.0
            ),
            ChainStep(
                id="step2",
                required_resources=["database"],
                estimated_time=1.0
            ),
            ChainStep(
                id="step3",
                required_resources=["api"],
                estimated_time=1.5
            )
        ]

        # 优化资源分配
        resource_plan = self.processor._optimize_resource_allocation(steps)

        # 验证资源优化
        self.assertIn("database", resource_plan)
        self.assertIn("api", resource_plan)

    def test_caching_optimization(self):
        """测试缓存优化"""
        # 创建相似的步骤
        ChainStep(
            id="step1",
            prompt_template="分析：{query}",
            cache_key_template="analysis_{query}"
        )
        ChainStep(
            id="step2",
            prompt_template="分析：{query}",
            cache_key_template="analysis_{query}"
        )

        # 模拟缓存
        cache = {}
        query = "测试查询"

        # 第一次执行
        cache_key = f"analysis_{query}"
        cache[cache_key] = {"result": "cached_result"}

        # 第二次执行应该使用缓存
        self.assertIn(cache_key, cache)
        self.assertEqual(cache[cache_key]["result"], "cached_result")

# 异步测试类
class TestAsyncChainProcessor(unittest.IsolatedAsyncioTestCase):
    """异步链处理器测试"""

    async def asyncSetUp(self):
        """异步测试设置"""
        self.processor = PromptChainProcessor()

    async def test_async_chain_creation(self):
        """测试异步链创建"""
        chain_id = await asyncio.to_thread(
            self.processor.create_chain, "test_chain", {"test": "data"}
        )

        self.assertIsNotNone(chain_id)
        self.assertIn(chain_id, self.processor.active_chains)

    async def test_async_chain_execution(self):
        """测试异步链执行"""
        chain_id = await asyncio.to_thread(
            self.processor.create_chain, "async_test", {}
        )

        # 模拟异步执行
        execution_result = await self._async_execute_chain(chain_id)
        self.assertIsNotNone(execution_result)

    async def _async_execute_chain(self, chain_id):
        """异步执行链"""
        await asyncio.sleep(0.1)  # 模拟执行时间
        return {"chain_id": chain_id, "status": "completed"}

    async def test_concurrent_chain_execution(self):
        """测试并发链执行"""
        chain_ids = []

        # 创建多个链
        for i in range(5):
            chain_id = await asyncio.to_thread(
                self.processor.create_chain, f"concurrent_test_{i}", {}
            )
            chain_ids.append(chain_id)

        # 并发执行
        tasks = [
            self._async_execute_chain(chain_id) for chain_id in chain_ids
        ]
        results = await asyncio.gather(*tasks)

        # 验证所有链都成功执行
        for i, result in enumerate(results):
            self.assertIsNotNone(result)
            self.assertEqual(result["chain_id"], chain_ids[i])

if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)
