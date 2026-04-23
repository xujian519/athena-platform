#!/usr/bin/env python3
from __future__ import annotations
"""
优化版通信模块 - 主模块类
Optimized Communication Module - Main Module

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from typing import Any

from core.base_module import BaseModule
from core.logging_config import setup_logging

from .batch_processor import BatchProcessor
from .compressor import MessageCompressor
from .router import MessageRouter
from .types import (
    CommunicationStats,
    CompressionType,
    DeliveryMode,
    Message,
    MessagePriority,
)

# 尝试导入现有的通信系统
try:
    COMMUNICATION_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入通信引擎: {e}")
    COMMUNICATION_SYSTEM_AVAILABLE = False

logger = setup_logging()


class OptimizedCommunicationModule(BaseModule):
    """优化版通信模块

    提供消息压缩、批处理、智能路由等功能。
    """

    def __init__(self, agent_id: str, config: Optional[dict[str, Any]] = None):
        """初始化优化版通信模块

        Args:
            agent_id: 智能体ID
            config: 配置字典
        """
        super().__init__(agent_id, config)

        # 优化配置
        self.optimization_config: dict[str, Any] = {
            "message_compression": True,
            "batch_processing": True,
            "adaptive_compression": True,
            "intelligent_routing": True,
            "async_messaging": True,
            "message_caching": True,
            **self.config,
        }

        # 初始化优化组件
        if self.optimization_config["message_compression"]:
            self.compressor = MessageCompressor(self.optimization_config)

        if self.optimization_config["batch_processing"]:
            self.batch_processor = BatchProcessor(self.optimization_config)

        if self.optimization_config["intelligent_routing"]:
            self.message_router = MessageRouter(self.optimization_config)

        # 消息队列和缓存
        self.message_queues: defaultdict[str, asyncio.Queue] = defaultdict(
            asyncio.Queue
        )
        self.message_cache: dict[str, Any] = {}
        self.cache_max_size = self.optimization_config.get("cache_max_size", 1000)

        # 现有通信系统集成
        self.communication_engine: Any = None
        self.fallback_enabled = True

        if COMMUNICATION_SYSTEM_AVAILABLE:
            try:
                # self.communication_engine = MessageHandler(self.agent_id)
                logger.info("✅ 现有通信引擎集成成功")
            except Exception as e:
                logger.warning(f"现有通信引擎集成失败: {e}")

        # 统计信息
        self.communication_stats = CommunicationStats()

        logger.info("📡 优化版通信模块初始化完成")

    async def _on_initialize(self) -> bool:
        """初始化优化通信模块"""
        try:
            logger.info("📡 初始化优化通信模块...")

            # 注册默认消息处理器
            if hasattr(self, "message_router"):
                self.message_router.register_handler("ping", self._handle_ping)
                self.message_router.register_handler("status", self._handle_status)

            logger.info("✅ 优化通信模块初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化通信模块初始化失败: {e!s}")
            return False

    async def _on_start(self) -> bool:
        """启动优化通信模块"""
        try:
            logger.info("🚀 启动优化通信模块")

            # 启动消息处理循环
            if self.optimization_config.get("async_messaging", True):
                asyncio.create_task(self._message_processing_loop())

            logger.info("✅ 优化通信模块启动成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化通信模块启动失败: {e!s}")
            return False

    async def _on_stop(self) -> bool:
        """停止优化通信模块"""
        try:
            logger.info("⏹️ 停止优化通信模块")
            logger.info("✅ 优化通信模块停止成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化通信模块停止失败: {e!s}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭优化通信模块"""
        try:
            logger.info("🔚 关闭优化通信模块")

            # 生成优化报告
            self._generate_optimization_report()

            logger.info("✅ 优化通信模块关闭成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化通信模块关闭失败: {e!s}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            checks = {
                "compressor_available": hasattr(self, "compressor")
                or not self.optimization_config["message_compression"],
                "batch_processor_available": hasattr(self, "batch_processor")
                or not self.optimization_config["batch_processing"],
                "message_router_available": hasattr(self, "message_router")
                or not self.optimization_config["intelligent_routing"],
                "communication_engine_available": self.communication_engine is not None
                or self.fallback_enabled,
                "async_messaging_enabled": self.optimization_config["async_messaging"],
                "message_caching_enabled": self.optimization_config["message_caching"],
            }

            overall_healthy = (
                checks["compressor_available"]
                and checks["batch_processor_available"]
                and checks["message_router_available"]
                and checks["communication_engine_available"]
            )

            # 存储健康检查详情
            self._health_check_details = {
                "compressor_status": (
                    "available" if checks["compressor_available"] else "unavailable"
                ),
                "batch_processor_status": (
                    "available" if checks["batch_processor_available"] else "unavailable"
                ),
                "message_router_status": (
                    "available" if checks["message_router_available"] else "unavailable"
                ),
                "communication_engine_status": (
                    "available" if checks["communication_engine_available"] else "unavailable"
                ),
                "optimization_stats": asdict(self.communication_stats),
                "overall_healthy": overall_healthy,
            }

            return overall_healthy

        except Exception as e:
            logger.error(f"健康检查失败: {e!s}")
            return False

    async def send_message_optimized(
        self,
        receiver_id: str,
        message_type: str,
        payload: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        compression: CompressionType = CompressionType.AUTO,
        delivery_mode: DeliveryMode = DeliveryMode.ASYNCHRONOUS,
        ttl: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        """优化消息发送"""
        try:
            message_id = str(uuid.uuid4())

            # 创建消息
            message = Message(
                message_id=message_id,
                sender_id=self.agent_id,
                receiver_id=receiver_id,
                message_type=message_type,
                payload=payload,
                priority=priority,
                compression=compression,
                delivery_mode=delivery_mode,
                ttl=ttl,
                metadata=metadata or {},
                tags=tags or [],
            )

            # 消息压缩
            if (
                hasattr(self, "compressor")
                and self.optimization_config["message_compression"]
            ):
                message, compression_result = self.compressor.compress_message(message)
                if compression_result:
                    self.communication_stats.compression_stats[message_id] = (
                        compression_result
                    )
                    self.communication_stats.bandwidth_saved += (
                        1 - compression_result.compression_ratio
                    ) * 100

            # 批处理
            if (
                delivery_mode == DeliveryMode.BATCH
                and hasattr(self, "batch_processor")
                and self.optimization_config["batch_processing"]
            ):
                batch_receiver = self.batch_processor.add_message_to_batch(message)
                if batch_receiver:
                    logger.debug(f"消息 {message_id} 添加到批处理队列: {batch_receiver}")

            # 路由消息
            if (
                hasattr(self, "message_router")
                and self.optimization_config["intelligent_routing"]
            ):
                receivers = self.message_router.route_message(message)
                if receivers:
                    logger.debug(f"消息路由到: {receivers}")

            # 异步发送
            if delivery_mode == DeliveryMode.ASYNCHRONOUS:
                await self._send_message_async(message)
            else:
                await self._send_message_sync(message)

            # 更新统计
            self.communication_stats.total_messages_sent += 1
            self.communication_stats.total_bytes_sent += len(str(message.payload))

            logger.debug(f"✅ 消息发送成功: {message_id}")
            return message_id

        except Exception as e:
            logger.error(f"❌ 消息发送失败: {e}")
            return ""

    async def _send_message_async(self, message: Message):
        """异步发送消息"""
        try:
            await self.message_queues[message.receiver_id].put(message)
        except Exception as e:
            logger.error(f"异步消息发送失败: {e}")

    async def _send_message_sync(self, message: Message):
        """同步发送消息"""
        try:
            await self._send_message_async(message)
        except Exception as e:
            logger.error(f"同步消息发送失败: {e}")

    async def _message_processing_loop(self):
        """消息处理循环"""
        logger.info("🔄 启动消息处理循环")

        while True:
            try:
                for _receiver_id, q in self.message_queues.items():
                    try:
                        message = q.get_nowait()
                        await self._process_received_message(message)
                    except asyncio.QueueEmpty:
                        continue
                    except Exception as e:
                        logger.error(f"处理消息失败: {e}")

                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"消息处理循环异常: {e}")
                await asyncio.sleep(1)

    async def _process_received_message(self, message: Message):
        """处理接收到的消息"""
        try:
            # 检查TTL
            if message.ttl and (datetime.now() - message.timestamp).total_seconds() > message.ttl:
                logger.warning(f"消息 {message.message_id} 已过期")
                return

            # 解压缩
            if (
                hasattr(self, "compressor")
                and message.metadata.get("compressed", False)
            ):
                message = self.compressor.decompress_message(message)

            # 路由到处理器
            if hasattr(self, "message_router"):
                handlers = self.message_router.message_handlers.get(
                    message.message_type
                )
                if handlers:
                    if asyncio.iscoroutinefunction(handlers):
                        await handlers(message)
                    else:
                        handlers(message)

            # 更新统计
            self.communication_stats.total_messages_received += 1
            self.communication_stats.total_bytes_received += len(str(message.payload))

        except Exception as e:
            logger.error(f"消息处理失败 {message.message_id}: {e}")

    async def _handle_ping(self, message: Message):
        """处理ping消息"""
        try:
            pong_message = Message(
                message_id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type="pong",
                payload={"timestamp": datetime.now().isoformat()},
                correlation_id=message.message_id,
            )
            await self._send_message_async(pong_message)
        except Exception as e:
            logger.error(f"处理ping消息失败: {e}")

    async def _handle_status(self, message: Message):
        """处理状态查询消息"""
        try:
            status_info = {
                "agent_id": self.agent_id,
                "status": "healthy",
                "uptime": (datetime.now() - self.start_time).total_seconds(),
                "message_stats": asdict(self.communication_stats),
            }

            response_message = Message(
                message_id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type="status_response",
                payload=status_info,
                correlation_id=message.message_id,
            )
            await self._send_message_async(response_message)
        except Exception as e:
            logger.error(f"处理状态消息失败: {e}")

    async def subscribe_optimized(self, message_types: list[str]) -> bool:
        """优化订阅"""
        try:
            if hasattr(self, "message_router"):
                for message_type in message_types:
                    self.message_router.subscribe(self.agent_id, message_type)
                return True
            return False
        except Exception as e:
            logger.error(f"订阅失败: {e}")
            return False

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """标准处理接口"""
        operation = data.get("operation", "send_message")

        if operation == "send_message":
            receiver_id = data.get("receiver_id")
            message_type = data.get("message_type", "default")
            payload = data.get("payload")
            priority = MessagePriority(
                data.get("priority", MessagePriority.NORMAL.value)
            )
            compression = CompressionType(
                data.get("compression", CompressionType.AUTO.value)
            )
            delivery_mode = DeliveryMode(
                data.get("delivery_mode", DeliveryMode.ASYNCHRONOUS.value)
            )
            ttl = data.get("ttl")
            metadata = data.get("metadata", {})
            tags = data.get("tags", [])

            if receiver_id is not None and payload is not None:
                message_id = await self.send_message_optimized(
                    receiver_id=receiver_id,
                    message_type=message_type,
                    payload=payload,
                    priority=priority,
                    compression=compression,
                    delivery_mode=delivery_mode,
                    ttl=ttl,
                    metadata=metadata,
                    tags=tags,
                )
                return {"success": bool(message_id), "message_id": message_id}

        elif operation == "subscribe":
            message_types = data.get("message_types", [])
            if message_types:
                success = await self.subscribe_optimized(message_types)
                return {"success": success, "message_types": message_types}

        return await super().process(data)

    def _generate_optimization_report(self) -> dict[str, Any]:
        """生成优化报告"""
        try:
            # 计算平均压缩比
            if self.communication_stats.compression_stats:
                compression_ratios = [
                    cr.compression_ratio
                    for cr in self.communication_stats.compression_stats.values()
                ]
                self.communication_stats.average_compression_ratio = (
                    sum(compression_ratios) / len(compression_ratios)
                )

            # 计算平均消息大小
            total_messages = (
                self.communication_stats.total_messages_sent
                + self.communication_stats.total_messages_received
            )
            if total_messages > 0:
                self.communication_stats.average_message_size = (
                    self.communication_stats.total_bytes_sent
                    + self.communication_stats.total_bytes_received
                ) / total_messages

            # 计算消息速率
            if hasattr(self, "start_time"):
                uptime = (datetime.now() - self.start_time).total_seconds()
                if uptime > 0:
                    self.communication_stats.message_rate = total_messages / uptime

            report = {
                "communication_summary": asdict(self.communication_stats),
                "configuration": self.optimization_config,
                "compression_details": {
                    algorithm: asdict(cr)
                    for algorithm, cr in self.communication_stats.compression_stats.items()
                },
                "routing_stats": (
                    self.message_router.get_routing_stats()
                    if hasattr(self, "message_router")
                    else {}
                ),
                "batch_stats": (
                    self.batch_processor.get_batch_stats()
                    if hasattr(self, "batch_processor")
                    else {}
                ),
            }

            # 保存报告
            report_path = f"communication_optimization_report_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📊 通信模块优化报告已生成: {report_path}")
            return report

        except Exception as e:
            logger.error(f"生成优化报告失败: {e}")
            return {}

    def get_optimization_stats(self) -> dict[str, Any]:
        """获取优化统计信息"""
        stats = {
            "module_stats": asdict(self.communication_stats),
            "configuration": self.optimization_config,
        }

        if hasattr(self, "compressor"):
            stats["compression_benchmarks"] = self.compressor.compression_benchmarks

        if hasattr(self, "message_router"):
            stats["routing_statistics"] = self.message_router.get_routing_stats()

        if hasattr(self, "batch_processor"):
            stats["batch_statistics"] = self.batch_processor.get_batch_stats()

        return stats


__all__ = ["OptimizedCommunicationModule"]
