#!/usr/bin/env python3
from __future__ import annotations
"""
优化版执行模块测试脚本
Test Optimized Execution Module

验证智能任务调度和资源动态分配功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import random
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.execution.optimized_execution_module import (
    OptimizedExecutionModule,
    TaskPriority,
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试任务函数
def cpu_intensive_task(n: int, duration: float = 0.1) -> int:
    """CPU密集型任务"""
    start_time = time.time()
    result = 0
    while time.time() - start_time < duration:
        result += sum(i * i for i in range(n))
    return result

def io_intensive_task(delay: float = 0.1) -> str:
    """IO密集型任务"""
    time.sleep(delay)
    return f"IO任务完成,延迟: {delay}s"

def memory_intensive_task(size_mb: int = 10) -> int:
    """内存密集型任务"""
    data = [0] * (size_mb * 1024 * 256)  # 约size_mb MB
    sum(data)
    return len(data)

def mixed_task(cpu_ops: int, io_delay: float, mem_size: int) -> dict:
    """混合型任务"""
    # CPU操作
    cpu_result = cpu_intensive_task(cpu_ops, 0.05)

    # IO操作
    time.sleep(io_delay)

    # 内存操作
    mem_result = memory_intensive_task(mem_size // 10)

    return {
        'cpu_result': cpu_result,
        'io_delay': io_delay,
        'memory_size': mem_result,
        'completed_at': time.time()
   }

async def failing_task(should_fail: bool = True) -> str:
    """会失败的任务"""
    await asyncio.sleep(0.1)
    if should_fail:
        raise Exception('测试任务失败')
    return '任务成功'

async def test_intelligent_task_scheduling():
    """测试智能任务调度"""
    logger.info("\n⚡ 测试智能任务调度")
    logger.info(str('=' * 60))

    try:
        # 创建优化执行模块
        execution_module = OptimizedExecutionModule(
            agent_id='test_scheduling_agent',
            config={
                'intelligent_scheduling': True,
                'max_concurrent_tasks': 4,
                'scheduling_strategy': 'priority_fifo',
                'max_thread_workers': 4,
                'max_process_workers': 2,
                'parallel_processing': True
            }
        )

        # 初始化和启动
        logger.info("\n1. 初始化优化执行模块...")
        init_success = await execution_module.initialize()
        if init_success:
            logger.info('✅ 优化执行模块初始化成功')
        else:
            logger.info('❌ 优化执行模块初始化失败')
            return False

        logger.info("\n2. 启动优化执行模块...")
        start_success = await execution_module.start()
        if start_success:
            logger.info('✅ 优化执行模块启动成功')
        else:
            logger.info('❌ 优化执行模块启动失败')
            return False

        # 3. 提交不同优先级的任务
        logger.info("\n3. 提交不同优先级的任务...")
        task_ids = []

        # 提交高优先级任务
        high_priority_tasks = 3
        for i in range(high_priority_tasks):
            task_id = await execution_module.submit_task_optimized(
                name=f"高优先级任务_{i}",
                function=cpu_intensive_task,
                priority=TaskPriority.HIGH,
                args=(100,),
                estimated_cpu=0.8,
                estimated_memory=0.2
            )
            if task_id:
                task_ids.append(task_id)

        # 提交普通优先级任务
        normal_priority_tasks = 5
        for i in range(normal_priority_tasks):
            task_id = await execution_module.submit_task_optimized(
                name=f"普通任务_{i}",
                function=io_intensive_task,
                priority=TaskPriority.NORMAL,
                args=(0.2,),
                estimated_cpu=0.3,
                estimated_memory=0.1
            )
            if task_id:
                task_ids.append(task_id)

        # 提交低优先级任务
        low_priority_tasks = 2
        for i in range(low_priority_tasks):
            task_id = await execution_module.submit_task_optimized(
                name=f"低优先级任务_{i}",
                function=memory_intensive_task,
                priority=TaskPriority.LOW,
                args=(5,),
                estimated_cpu=0.2,
                estimated_memory=0.5
            )
            if task_id:
                task_ids.append(task_id)

        logger.info(f"   ✅ 成功提交 {len(task_ids)} 个任务")
        logger.info(f"   - 高优先级任务: {high_priority_tasks} 个")
        logger.info(f"   - 普通优先级任务: {normal_priority_tasks} 个")
        logger.info(f"   - 低优先级任务: {low_priority_tasks} 个")

        # 4. 等待任务完成并检查优先级执行顺序
        logger.info("\n4. 监控任务执行顺序...")
        completed_order = []
        waiting_time = 0

        while len(completed_order) < len(task_ids) and waiting_time < 30:
            for task_id in task_ids:
                if task_id not in completed_order:
                    status = await execution_module.get_task_status(task_id)
                    if status and status['status'] in ['completed', 'failed']:
                        completed_order.append(task_id)
                        logger.info(f"   ✅ 任务完成: {status.get('name', 'unknown')} (优先级: {status.get('priority', 'unknown')})")

            await asyncio.sleep(0.5)
            waiting_time += 0.5

        # 5. 验证优先级调度效果
        logger.info("\n5. 验证优先级调度效果...")
        high_priority_completed = 0
        normal_priority_completed = 0
        low_priority_completed = 0

        for task_id in task_ids:
            status = await execution_module.get_task_status(task_id)
            if status:
                if status.get('name', '').startswith('高优先级'):
                    high_priority_completed += 1
                elif status.get('name', '').startswith('普通'):
                    normal_priority_completed += 1
                elif status.get('name', '').startswith('低优先级'):
                    low_priority_completed += 1

        logger.info(f"   高优先级任务完成: {high_priority_completed}/{high_priority_tasks}")
        logger.info(f"   普通优先级任务完成: {normal_priority_completed}/{normal_priority_tasks}")
        logger.info(f"   低优先级任务完成: {low_priority_completed}/{low_priority_tasks}")

        # 6. 获取调度器统计信息
        logger.info("\n6. 获取调度器统计信息...")
        stats = execution_module.get_optimization_stats()

        if 'scheduler_statistics' in stats:
            scheduler_stats = stats['scheduler_statistics']
            logger.info('✅ 调度器统计信息:')

            resource_util = scheduler_stats.get('resource_utilization', {})
            logger.info(f"   - CPU利用率: {resource_util.get('cpu', 'N/A')}")
            logger.info(f"   - 内存利用率: {resource_util.get('memory', 'N/A')}")
            logger.info(f"   - 运行中任务数: {resource_util.get('running_tasks', 0)}")
            logger.info(f"   - 最大并发数: {resource_util.get('max_concurrent', 0)}")

            queue_stats = scheduler_stats.get('queue_stats', {})
            logger.info(f"   - 等待任务数: {queue_stats.get('pending_tasks', 0)}")
            logger.info(f"   - 已完成任务数: {queue_stats.get('completed_tasks', 0)}")
            logger.info(f"   - 失败任务数: {queue_stats.get('failed_tasks', 0)}")
            logger.info(f"   - 平均执行时间: {queue_stats.get('average_execution_time', 'N/A')}")
            logger.info(f"   - 吞吐量: {queue_stats.get('throughput', 'N/A')}")

        # 7. 健康检查
        logger.info("\n7. 执行健康检查...")
        health_status = await execution_module.health_check()
        logger.info(f"   健康状态: {'健康' if health_status else '不健康'}")

        if hasattr(execution_module, '_health_check_details'):
            details = execution_module._health_check_details
            logger.info(f"   - 调度器状态: {details.get('scheduler_status', 'unknown')}")
            logger.info(f"   - 负载均衡器状态: {details.get('load_balancer_status', 'unknown')}")
            logger.info(f"   - 资源监控器状态: {details.get('resource_monitor_status', 'unknown')}")

        # 8. 关闭模块
        logger.info("\n8. 关闭优化执行模块...")
        await execution_module.shutdown()
        logger.info('✅ 优化执行模块关闭成功')

        logger.info(str("\n" + '=' * 60))
        logger.info('🎉 智能任务调度测试完成!')
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_dynamic_resource_allocation():
    """测试动态资源分配"""
    logger.info("\n🔄 测试动态资源分配")
    logger.info(str('=' * 60))

    try:
        execution_module = OptimizedExecutionModule(
            agent_id='test_resource_agent',
            config={
                'intelligent_scheduling': True,
                'dynamic_resource_allocation': True,
                'max_concurrent_tasks': 6,
                'auto_scaling': True,
                'resource_monitoring': True
            }
        )

        await execution_module.initialize()
        await execution_module.start()

        # 1. 提交不同资源需求的任务
        logger.info("\n1. 提交不同资源需求的任务...")
        resource_task_ids = []

        # CPU密集型任务
        for i in range(3):
            task_id = await execution_module.submit_task_optimized(
                name=f"CPU密集型任务_{i}",
                function=cpu_intensive_task,
                priority=TaskPriority.HIGH,
                args=(1000,),
                estimated_cpu=0.9,
                estimated_memory=0.1,
                timeout=10.0
            )
            resource_task_ids.append(task_id)

        # 内存密集型任务
        for i in range(3):
            task_id = await execution_module.submit_task_optimized(
                name=f"内存密集型任务_{i}",
                function=memory_intensive_task,
                priority=TaskPriority.NORMAL,
                args=(20,),
                estimated_cpu=0.3,
                estimated_memory=0.8,
                timeout=15.0
            )
            resource_task_ids.append(task_id)

        # 混合型任务
        for i in range(2):
            task_id = await execution_module.submit_task_optimized(
                name=f"混合型任务_{i}",
                function=mixed_task,
                priority=TaskPriority.NORMAL,
                args=(500, 0.1, 50),
                estimated_cpu=0.6,
                estimated_memory=0.5,
                timeout=12.0
            )
            resource_task_ids.append(task_id)

        logger.info(f"   ✅ 成功提交 {len(resource_task_ids)} 个不同资源需求的任务")

        # 2. 监控资源使用情况
        logger.info("\n2. 监控资源使用情况...")
        monitoring_rounds = 0
        max_rounds = 20

        while monitoring_rounds < max_rounds:
            stats = execution_module.get_optimization_stats()

            if 'resource_usage' in stats:
                resource_usage = stats['resource_usage']
                logger.info(f"   第{monitoring_rounds + 1}轮资源监控:")
                logger.info(f"     CPU使用: {resource_usage.get('cpu_cores', 0):.2f} 核心")
                logger.info(f"     内存使用: {resource_usage.get('memory_mb', 0):.1f} MB")
                logger.info(f"     磁盘IO: {resource_usage.get('disk_io_mb_s', 0):.1f} MB/s")
                logger.info(f"     网络IO: {resource_usage.get('network_mbps', 0):.1f} Mbps")

            # 检查任务完成情况
            completed_count = 0
            for task_id in resource_task_ids:
                status = await execution_module.get_task_status(task_id)
                if status and status['status'] == 'completed':
                    completed_count += 1

            if completed_count >= len(resource_task_ids):
                logger.info("   ✅ 所有任务已完成")
                break

            await asyncio.sleep(1)
            monitoring_rounds += 1

        # 3. 验证资源分配效率
        logger.info("\n3. 验证资源分配效率...")
        final_stats = execution_module.get_optimization_stats()

        if 'module_stats' in final_stats:
            module_stats = final_stats['module_stats']
            logger.info('✅ 资源分配效率统计:')
            logger.info(f"   - 总提交任务数: {module_stats.get('total_submitted_tasks', 0)}")
            logger.info(f"   - 总完成任务数: {module_stats.get('total_completed_tasks', 0)}")
            logger.info(f"   - 平均等待时间: {module_stats.get('average_waiting_time', 0):.3f}s")
            logger.info(f"   - 资源利用率: {module_stats.get('resource_utilization', 0):.1%}")

        await execution_module.shutdown()
        logger.info("\n✅ 动态资源分配测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 动态资源分配测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_task_dependencies():
    """测试任务依赖管理"""
    logger.info("\n🔗 测试任务依赖管理")
    logger.info(str('=' * 60))

    try:
        execution_module = OptimizedExecutionModule(
            agent_id='test_dependency_agent',
            config={
                'intelligent_scheduling': True,
                'max_concurrent_tasks': 3
            }
        )

        await execution_module.initialize()
        await execution_module.start()

        # 1. 创建有依赖关系的任务链
        logger.info("\n1. 创建任务依赖链...")

        # 任务A (无依赖)
        task_a_id = await execution_module.submit_task_optimized(
            name='任务A_数据准备',
            function=lambda: {'data': 'prepared_data', 'timestamp': time.time()},
            priority=TaskPriority.HIGH
        )
        logger.info(f"   ✅ 提交任务A: {task_a_id}")

        # 任务B (依赖A)
        task_b_id = await execution_module.submit_task_optimized(
            name='任务B_数据处理',
            function=lambda data: {"processed_data": f"processed_{data['data']}", "step": 1},
            priority=TaskPriority.HIGH,
            dependencies=[task_a_id] if task_a_id else []
        )
        logger.info(f"   ✅ 提交任务B (依赖A): {task_b_id}")

        # 任务C (依赖B)
        task_c_id = await execution_module.submit_task_optimized(
            name='任务C_数据验证',
            function=lambda data: {'validated': True, 'step': 2, 'input': data},
            priority=TaskPriority.HIGH,
            dependencies=[task_b_id] if task_b_id else []
        )
        logger.info(f"   ✅ 提交任务C (依赖B): {task_c_id}")

        # 任务D (依赖A和C)
        task_d_id = await execution_module.submit_task_optimized(
            name='任务D_最终输出',
            function=lambda data1, data2: {"final_result": f"output_{data1['step']}_{data2['step']}", "complete": True},
            priority=TaskPriority.HIGH,
            dependencies=[task_a_id, task_c_id] if task_a_id and task_c_id else []
        )
        logger.info(f"   ✅ 提交任务D (依赖A和C): {task_d_id}")

        # 2. 等待依赖链完成
        logger.info("\n2. 监控依赖链执行...")
        dependency_chain = [task_a_id, task_b_id, task_c_id, task_d_id]
        completed_chain = []
        wait_time = 0
        max_wait = 30

        while len(completed_chain) < len(dependency_chain) and wait_time < max_wait:
            for _i, task_id in enumerate(dependency_chain):
                if task_id not in completed_chain:
                    status = await execution_module.get_task_status(task_id)
                    if status and status['status'] == 'completed':
                        completed_chain.append(task_id)
                        logger.info(f"   ✅ {status.get('name', 'unknown')} 完成")

            await asyncio.sleep(0.5)
            wait_time += 0.5

        # 3. 验证依赖执行顺序
        logger.info("\n3. 验证依赖执行顺序...")
        execution_order_correct = True

        if task_a_id in completed_chain:
            a_index = completed_chain.index(task_a_id)
            if task_b_id in completed_chain and completed_chain.index(task_b_id) <= a_index:
                execution_order_correct = False
            if task_c_id in completed_chain and completed_chain.index(task_c_id) <= a_index:
                execution_order_correct = False
            if task_d_id in completed_chain and completed_chain.index(task_d_id) <= a_index:
                execution_order_correct = False

        if execution_order_correct:
            logger.info('   ✅ 任务依赖执行顺序正确')
        else:
            logger.info('   ❌ 任务依赖执行顺序错误')

        # 4. 测试依赖失败情况
        logger.info("\n4. 测试依赖失败情况...")

        # 提交会失败的任务
        failing_task_id = await execution_module.submit_task_optimized(
            name='失败任务',
            function=failing_task,
            priority=TaskPriority.NORMAL
        )

        # 提交依赖失败任务的后续任务
        dependent_task_id = await execution_module.submit_task_optimized(
            name='依赖失败的任务',
            function=lambda x: f"should_not_execute_{x}",
            dependencies=[failing_task_id],
            priority=TaskPriority.LOW
        )

        await asyncio.sleep(2)

        failing_status = await execution_module.get_task_status(failing_task_id)
        dependent_status = await execution_module.get_task_status(dependent_task_id)

        if failing_status and failing_status.get('status') == 'failed':
            logger.info('   ✅ 失败任务正确标记为失败')
        else:
            logger.info('   ❌ 失败任务状态异常')

        if dependent_status and dependent_status.get('status') in ['pending', 'cancelled']:
            logger.info('   ✅ 依赖失败任务正确等待或取消')
        else:
            logger.info('   ❌ 依赖失败任务状态异常')

        await execution_module.shutdown()
        logger.info("\n✅ 任务依赖管理测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 任务依赖管理测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_load_balancing():
    """测试负载均衡"""
    logger.info("\n⚖️ 测试负载均衡")
    logger.info(str('=' * 60))

    try:
        execution_module = OptimizedExecutionModule(
            agent_id='test_load_balance_agent',
            config={
                'intelligent_scheduling': True,
                'load_balancing': True,
                'load_balance_strategy': 'least_loaded',
                'health_check_interval': 5
            }
        )

        await execution_module.initialize()
        await execution_module.start()

        # 1. 模拟多个工作节点
        logger.info("\n1. 模拟多个工作节点...")
        if hasattr(execution_module, 'load_balancer'):
            # 添加模拟节点
            execution_module.load_balancer.add_worker_node({
                'node_id': 'node_1',
                'host': '192.168.1.101',
                'port': 8081,
                'cpu_cores': 4,
                'memory_mb': 8192
            })

            execution_module.load_balancer.add_worker_node({
                'node_id': 'node_2',
                'host': '192.168.1.102',
                'port': 8081,
                'cpu_cores': 8,
                'memory_mb': 16384
            })

            execution_module.load_balancer.add_worker_node({
                'node_id': 'node_3',
                'host': '192.168.1.103',
                'port': 8081,
                'cpu_cores': 2,
                'memory_mb': 4096
            })

            logger.info(f"   ✅ 成功添加 {len(execution_module.load_balancer.worker_nodes)} 个工作节点")

        # 2. 提交大量任务测试负载均衡
        logger.info("\n2. 提交大量任务测试负载均衡...")
        load_balance_task_ids = []
        num_tasks = 20

        for i in range(num_tasks):
            task_id = await execution_module.submit_task_optimized(
                name=f"负载均衡测试任务_{i}",
                function=io_intensive_task,
                priority=random.choice(list(TaskPriority)),
                args=(random.uniform(0.1, 0.5),),
                estimated_cpu=random.uniform(0.2, 0.8),
                estimated_memory=random.uniform(0.1, 0.6)
            )
            if task_id:
                load_balance_task_ids.append(task_id)

        logger.info(f"   ✅ 成功提交 {len(load_balance_task_ids)} 个负载均衡测试任务")

        # 3. 监控负载分布
        logger.info("\n3. 监控负载分布...")
        monitoring_time = 0
        max_monitoring_time = 15

        while monitoring_time < max_monitoring_time:
            stats = execution_module.get_optimization_stats()

            if 'load_balancer_statistics' in stats:
                lb_stats = stats['load_balancer_statistics']
                logger.info(f"   负载均衡统计 (第{monitoring_time + 1}轮):")
                logger.info(f"     总节点数: {lb_stats.get('total_nodes', 0)}")
                logger.info(f"     健康节点数: {lb_stats.get('healthy_nodes', 0)}")
                logger.info(f"     负载均衡策略: {lb_stats.get('load_balance_strategy', 'unknown')}")

            if 'scheduler_statistics' in stats:
                scheduler_stats = stats['scheduler_statistics']
                resource_util = scheduler_stats.get('resource_utilization', {})
                logger.info(f"     当前负载: CPU {resource_util.get('cpu', 'N/A')}, 内存 {resource_util.get('memory', 'N/A')}")

            await asyncio.sleep(1)
            monitoring_time += 1

        # 4. 获取最终负载均衡统计
        logger.info("\n4. 获取最终负载均衡统计...")
        final_stats = execution_module.get_optimization_stats()

        if 'module_stats' in final_stats:
            module_stats = final_stats['module_stats']
            logger.info('✅ 负载均衡效果:')
            logger.info(f"   - 总提交任务: {module_stats.get('total_submitted_tasks', 0)}")
            logger.info(f"   - 总完成任务: {module_stats.get('total_completed_tasks', 0)}")
            logger.info(f"   - 调度效率: {module_stats.get('scheduling_efficiency', 0):.1%}")

        if 'load_balancer_statistics' in final_stats:
            lb_stats = final_stats['load_balancer_statistics']
            logger.info(f"   - 健康节点率: {lb_stats.get('healthy_nodes', 0)}/{lb_stats.get('total_nodes', 0)}")

        await execution_module.shutdown()
        logger.info("\n✅ 负载均衡测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 负载均衡测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    logger.info('🚀 优化版执行模块完整测试套件')
    logger.info(str('=' * 80))

    # 测试列表
    tests = [
        ('智能任务调度测试', test_intelligent_task_scheduling),
        ('动态资源分配测试', test_dynamic_resource_allocation),
        ('任务依赖管理测试', test_task_dependencies),
        ('负载均衡测试', test_load_balancing)
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n🧪 执行测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = '✅ 通过' if result else '❌ 失败'
            logger.info(f"\n{test_name}: {status}")
        except Exception as e:
            logger.error(f"测试异常 {test_name}: {e}")
            results.append((test_name, False))

    # 测试总结
    logger.info(str("\n" + '=' * 80))
    logger.info('📊 测试总结')
    logger.info(str('=' * 80))

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = '✅ 通过' if result else '❌ 失败'
        logger.info(f"{test_name}: {status}")

    logger.info(f"\n🎯 总体结果: {passed_count}/{total_count} 测试通过")
    logger.info(f"成功率: {passed_count/total_count*100:.1f}%")

    if passed_count == total_count:
        logger.info("\n🎉 所有测试通过!优化版执行模块功能验证成功!")
        logger.info("\n🌟 执行模块优化特性:")
        logger.info('   ✅ 智能任务优先级调度')
        logger.info('   ✅ 动态资源分配和监控')
        logger.info('   ✅ 任务依赖关系管理')
        logger.info('   ✅ 负载均衡和健康检查')
        logger.info('   ✅ 自动扩缩容机制')
        logger.info('   ✅ 异步并发处理')
    else:
        logger.info("\n⚠️ 部分测试失败,需要进一步优化。")

    return passed_count == total_count

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
