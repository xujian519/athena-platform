#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认知状态管理器
Cognitive State Manager

管理和维护认知系统的状态，包括状态转换、异常处理和恢复机制

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CognitiveState(Enum):
    """认知状态枚举"""
    INITIALIZING = 'initializing'        # 初始化中
    IDLE = 'idle'                       # 空闲
    PROCESSING = 'processing'           # 处理中
    REASONING = 'reasoning'             # 推理中
    LEARNING = 'learning'               # 学习中
    MEMORY_CONSOLIDATION = 'memory_consolidation'  # 记忆巩固
    ERROR_RECOVERY = 'error_recovery'   # 错误恢复
    SHUTTING_DOWN = 'shutting_down'     # 关闭中
    TERMINATED = 'terminated'           # 已终止

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 'low'                         # 低级错误
    MEDIUM = 'medium'                   # 中级错误
    HIGH = 'high'                       # 高级错误
    CRITICAL = 'critical'               # 严重错误

@dataclass
class CognitiveMetrics:
    """认知指标"""
    processing_count: int = 0
    success_count: int = 0
    error_count: int = 0
    average_processing_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    confidence_score: float = 0.0
    learning_rate: float = 0.0

@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    severity: ErrorSeverity
    stack_trace: str
    context: Dict[str, Any]
    recovery_action: Optional[str] = None
    recovery_success: bool = False

@dataclass
class StateTransition:
    """状态转换记录"""
    transition_id: str
    from_state: CognitiveState
    to_state: CognitiveState
    timestamp: datetime
    trigger: str
    context: Dict[str, Any] = field(default_factory=dict)

class CognitiveStateManager:
    """认知状态管理器"""

    def __init__(self, state_change_callbacks: Optional[List[Callable]] = None):
        # 状态管理
        self._current_state = CognitiveState.INITIALIZING
        self._previous_state = None
        self._state_lock = Lock()
        self._state_change_callbacks = state_change_callbacks or []

        # 指标跟踪
        self.metrics = CognitiveMetrics()
        self.state_history: List[StateTransition] = []
        self.error_history: List[ErrorRecord] = []

        # 错误处理配置
        self.error_handlers: Dict[str, Callable] = {}
        self.recovery_strategies: Dict[ErrorSeverity, List[Callable]] = {
            ErrorSeverity.LOW: [],
            ErrorSeverity.MEDIUM: [],
            ErrorSeverity.HIGH: [],
            ErrorSeverity.CRITICAL: []
        }

        # 状态转换规则
        self.transition_rules = self._initialize_transition_rules()

        # 性能监控
        self.performance_thresholds = {
            'max_processing_time': 30.0,  # 最大处理时间（秒）
            'max_memory_usage': 0.8,     # 最大内存使用率
            'max_cpu_usage': 0.9,        # 最大CPU使用率
            'min_confidence_score': 0.6  # 最小置信度
        }

        # 错误恢复配置
        self.max_retry_attempts = 3
        self.retry_delays = [1, 2, 5]  # 重试延迟（秒）

        logger.info('🧠 认知状态管理器初始化完成')

    def _initialize_transition_rules(self) -> Dict[CognitiveState, List[CognitiveState]]:
        """初始化状态转换规则"""
        return {
            CognitiveState.INITIALIZING: [
                CognitiveState.IDLE,
                CognitiveState.ERROR_RECOVERY,
                CognitiveState.SHUTTING_DOWN
            ],
            CognitiveState.IDLE: [
                CognitiveState.PROCESSING,
                CognitiveState.REASONING,
                CognitiveState.LEARNING,
                CognitiveState.MEMORY_CONSOLIDATION,
                CognitiveState.SHUTTING_DOWN
            ],
            CognitiveState.PROCESSING: [
                CognitiveState.IDLE,
                CognitiveState.REASONING,
                CognitiveState.ERROR_RECOVERY
            ],
            CognitiveState.REASONING: [
                CognitiveState.PROCESSING,
                CognitiveState.LEARNING,
                CognitiveState.IDLE,
                CognitiveState.ERROR_RECOVERY
            ],
            CognitiveState.LEARNING: [
                CognitiveState.IDLE,
                CognitiveState.MEMORY_CONSOLIDATION,
                CognitiveState.ERROR_RECOVERY
            ],
            CognitiveState.MEMORY_CONSOLIDATION: [
                CognitiveState.IDLE,
                CognitiveState.ERROR_RECOVERY
            ],
            CognitiveState.ERROR_RECOVERY: [
                CognitiveState.IDLE,
                CognitiveState.SHUTTING_DOWN,
                CognitiveState.TERMINATED
            ],
            CognitiveState.SHUTTING_DOWN: [
                CognitiveState.TERMINATED
            ],
            CognitiveState.TERMINATED: []
        }

    def get_current_state(self) -> CognitiveState:
        """获取当前状态"""
        with self._state_lock:
            return self._current_state

    def can_transition_to(self, target_state: CognitiveState) -> bool:
        """检查是否可以转换到目标状态"""
        with self._state_lock:
            if self._current_state == CognitiveState.TERMINATED:
                return False
            return target_state in self.transition_rules.get(self._current_state, [])

    async def transition_to(self,
                           target_state: CognitiveState,
                           trigger: str = 'manual',
                           context: Optional[Dict[str, Any]] = None) -> bool:
        """转换到目标状态"""
        context = context or {}

        with self._state_lock:
            if not self.can_transition_to(target_state):
                logger.warning(f"⚠️ 非法状态转换: {self._current_state.value} -> {target_state.value}")
                return False

            # 记录状态转换
            self._previous_state = self._current_state
            transition_id = str(uuid.uuid4())

            transition = StateTransition(
                transition_id=transition_id,
                from_state=self._current_state,
                to_state=target_state,
                timestamp=datetime.now(),
                trigger=trigger,
                context=context
            )

            self.state_history.append(transition)

            # 执行状态转换
            old_state = self._current_state
            self._current_state = target_state

            logger.info(f"🔄 状态转换: {old_state.value} -> {target_state.value} (触发: {trigger})")

        # 调用状态转换回调
        await self._notify_state_change(old_state, target_state, context)

        # 清理旧的历史记录（保留最近1000条）
        if len(self.state_history) > 1000:
            self.state_history = self.state_history[-1000:]

        return True

    async def _notify_state_change(self,
                                  old_state: CognitiveState,
                                  new_state: CognitiveState,
                                  context: Dict[str, Any]):
        """通知状态变化"""
        for callback in self._state_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_state, new_state, context)
                else:
                    callback(old_state, new_state, context)
            except Exception as e:
                logger.error(f"❌ 状态变化回调执行失败: {e}")

    def register_error_handler(self, error_type: str, handler: Callable):
        """注册错误处理器"""
        self.error_handlers[error_type] = handler
        logger.info(f"📝 已注册错误处理器: {error_type}")

    def register_recovery_strategy(self,
                                  severity: ErrorSeverity,
                                  strategy: Callable):
        """注册恢复策略"""
        self.recovery_strategies[severity].append(strategy)
        logger.info(f"🛡️ 已注册恢复策略: {severity.value}")

    async def handle_error(self,
                          error: Exception,
                          context: Optional[Dict[str, Any]] = None) -> bool:
        """处理错误"""
        context = context or {}

        # 创建错误记录
        error_id = str(uuid.uuid4())
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()

        # 确定错误严重程度
        severity = self._classify_error(error)

        error_record = ErrorRecord(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            stack_trace=stack_trace,
            context=context
        )

        self.error_history.append(error_record)

        logger.error(f"❌ 认知系统错误 [{severity.value}]: {error_type}: {error_message}")

        # 更新指标
        self.metrics.error_count += 1

        # 执行错误处理
        recovery_success = await self._execute_error_handling(error, error_record)

        # 更新错误记录
        for record in self.error_history:
            if record.error_id == error_id:
                record.recovery_success = recovery_success
                break

        # 清理旧的错误记录（保留最近500条）
        if len(self.error_history) > 500:
            self.error_history = self.error_history[-500:]

        return recovery_success

    def _classify_error(self, error: Exception) -> ErrorSeverity:
        """分类错误严重程度"""
        error_type = type(error).__name__

        # 严重错误
        if error_type in ['SystemExit', 'KeyboardInterrupt', 'MemoryError']:
            return ErrorSeverity.CRITICAL

        # 高级错误
        elif error_type in ['RuntimeError', 'AttributeError', 'ImportError']:
            return ErrorSeverity.HIGH

        # 中级错误
        elif error_type in ['ValueError', 'KeyError', 'IndexError']:
            return ErrorSeverity.MEDIUM

        # 低级错误
        else:
            return ErrorSeverity.LOW

    async def _execute_error_handling(self,
                                     error: Exception,
                                     error_record: ErrorRecord) -> bool:
        """执行错误处理"""
        error_type = type(error).__name__

        # 尝试类型特定的错误处理器
        if error_type in self.error_handlers:
            try:
                handler = self.error_handlers[error_type]
                if asyncio.iscoroutinefunction(handler):
                    await handler(error, error_record)
                else:
                    handler(error, error_record)
                return True
            except Exception as e:
                logger.error(f"❌ 错误处理器执行失败: {e}")

        # 尝试基于严重程度的恢复策略
        severity = error_record.severity
        for strategy in self.recovery_strategies[severity]:
            try:
                recovery_action = f"执行恢复策略: {strategy.__name__}"
                error_record.recovery_action = recovery_action

                if asyncio.iscoroutinefunction(strategy):
                    result = await strategy(error, error_record)
                else:
                    result = strategy(error, error_record)

                if result:
                    logger.info(f"✅ 错误恢复成功: {recovery_action}")
                    return True

            except Exception as e:
                logger.error(f"❌ 恢复策略执行失败: {e}")

        # 默认恢复策略
        return await self._default_recovery_strategy(error, error_record)

    async def _default_recovery_strategy(self,
                                        error: Exception,
                                        error_record: ErrorRecord) -> bool:
        """默认恢复策略"""
        try:
            # 转换到错误恢复状态
            if self.get_current_state() != CognitiveState.ERROR_RECOVERY:
                await self.transition_to(
                    CognitiveState.ERROR_RECOVERY,
                    trigger='error_recovery',
                    context={'error_id': error_record.error_id}
                )

            # 等待一段时间后尝试恢复到空闲状态
            await asyncio.sleep(2)

            # 检查系统状态
            if await self._system_health_check():
                await self.transition_to(CognitiveState.IDLE, trigger='recovery_complete')
                return True
            else:
                logger.warning('⚠️ 系统健康检查失败，无法恢复')
                return False

        except Exception as e:
            logger.error(f"❌ 默认恢复策略失败: {e}")
            return False

    async def _system_health_check(self) -> bool:
        """系统健康检查"""
        try:
            # 检查各项指标是否在阈值范围内
            if (self.metrics.memory_usage > self.performance_thresholds['max_memory_usage'] or
                self.metrics.cpu_usage > self.performance_thresholds['max_cpu_usage']):
                return False

            return True

        except Exception as e:
            logger.error(f"❌ 系统健康检查失败: {e}")
            return False

    async def execute_with_retry(self,
                                func: Callable,
                                *args,
                                max_retries: Optional[int] = None,
                                context: Optional[Dict[str, Any]] = None,
                                **kwargs) -> Any:
        """带重试机制的函数执行"""
        max_retries = max_retries or self.max_retry_attempts
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.retry_delays[min(attempt - 1, len(self.retry_delays) - 1)]
                    logger.info(f"🔄 重试第 {attempt} 次，延迟 {delay} 秒...")
                    await asyncio.sleep(delay)

                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 成功执行
                if attempt > 0:
                    logger.info(f"✅ 重试成功 (第 {attempt + 1} 次尝试)")

                self.metrics.success_count += 1
                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ 执行失败 (第 {attempt + 1} 次尝试): {e}")

                # 记录错误
                await self.handle_error(e, context)

                if attempt == max_retries:
                    logger.error(f"❌ 达到最大重试次数 ({max_retries})，放弃执行")

        self.metrics.error_count += 1
        raise last_exception

    def update_metrics(self, **kwargs):
        """更新认知指标"""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)

        # 更新处理时间平均值
        if 'processing_time' in kwargs:
            current_avg = self.metrics.average_processing_time
            count = self.metrics.processing_count

            if count > 0:
                new_avg = (current_avg * (count - 1) + kwargs['processing_time']) / count
                self.metrics.average_processing_time = new_avg

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'current_state': self._current_state.value,
            'previous_state': self._previous_state.value if self._previous_state else None,
            'metrics': asdict(self.metrics),
            'state_transitions': len(self.state_history),
            'error_count': len(self.error_history),
            'error_rate': self.metrics.error_count / max(self.metrics.processing_count, 1),
            'success_rate': self.metrics.success_count / max(self.metrics.processing_count, 1),
            'recent_errors': [
                {
                    'error_type': error.error_type,
                    'message': error.error_message,
                    'severity': error.severity.value,
                    'timestamp': error.timestamp.isoformat()
                }
                for error in self.error_history[-10:]
            ]
        }

    def export_state_history(self, file_path: str, limit: Optional[int] = None):
        """导出状态历史"""
        history_to_export = self.state_history[-limit:] if limit else self.state_history

        exported_data = []
        for transition in history_to_export:
            exported_data.append({
                'transition_id': transition.transition_id,
                'from_state': transition.from_state.value,
                'to_state': transition.to_state.value,
                'timestamp': transition.timestamp.isoformat(),
                'trigger': transition.trigger,
                'context': transition.context
            })

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 状态历史已导出到: {file_path}")

    def get_error_analysis(self) -> Dict[str, Any]:
        """获取错误分析"""
        if not self.error_history:
            return {'total_errors': 0}

        # 按类型分组
        error_types = {}
        for error in self.error_history:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1

        # 按严重程度分组
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = sum(
                1 for error in self.error_history
                if error.severity == severity
            )

        # 恢复成功率
        recovery_success_rate = sum(
            1 for error in self.error_history
            if error.recovery_success
        ) / len(self.error_history)

        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'severity_distribution': severity_counts,
            'recovery_success_rate': recovery_success_rate,
            'most_common_error': max(error_types, key=error_types.get) if error_types else None
        }

    async def shutdown(self):
        """关闭状态管理器"""
        logger.info('🛑 关闭认知状态管理器...')

        if self._current_state != CognitiveState.TERMINATED:
            await self.transition_to(CognitiveState.SHUTTING_DOWN, trigger='shutdown')
            await self.transition_to(CognitiveState.TERMINATED, trigger='shutdown_complete')

        logger.info('✅ 认知状态管理器已关闭')

# 默认恢复策略
async def default_memory_recovery_strategy(error: Exception, error_record: ErrorRecord) -> bool:
    """内存错误恢复策略"""
    if isinstance(error, MemoryError):
        # 触发垃圾回收
        import gc
        gc.collect()
        logger.info('🧹 执行垃圾回收以释放内存')
        return True
    return False

async def default_timeout_recovery_strategy(error: Exception, error_record: ErrorRecord) -> bool:
    """超时错误恢复策略"""
    if 'timeout' in str(error).lower():
        logger.info('⏰ 检测到超时错误，建议调整处理时间限制')
        return True
    return False

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 认知状态管理器测试')
    logger.info(str('='*50))

    # 创建状态管理器
    manager = CognitiveStateManager()

    # 注册默认恢复策略
    manager.register_recovery_strategy(ErrorSeverity.MEDIUM, default_memory_recovery_strategy)
    manager.register_recovery_strategy(ErrorSeverity.LOW, default_timeout_recovery_strategy)

    # 测试状态转换
    logger.info("\n🔄 测试状态转换:")
    await manager.transition_to(CognitiveState.IDLE, trigger='test')
    await manager.transition_to(CognitiveState.PROCESSING, trigger='test')
    await manager.transition_to(CognitiveState.IDLE, trigger='test')

    # 测试错误处理
    logger.info("\n❌ 测试错误处理:")
    try:
        raise ValueError('这是一个测试错误')
    except Exception as e:
        await manager.handle_error(e, {'test': True})

    # 测试重试机制
    logger.info("\n🔄 测试重试机制:")
    attempt_count = 0

    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise RuntimeError('模拟失败')
        return '成功!'

    try:
        result = await manager.execute_with_retry(failing_function)
        logger.info(f"重试结果: {result}")
    except Exception as e:
        logger.info(f"重试失败: {e}")

    # 获取报告
    logger.info("\n📊 性能报告:")
    report = manager.get_performance_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

    logger.info("\n🔍 错误分析:")
    error_analysis = manager.get_error_analysis()
    print(json.dumps(error_analysis, indent=2, ensure_ascii=False))

    # 关闭管理器
    await manager.shutdown()
    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    asyncio.run(main())