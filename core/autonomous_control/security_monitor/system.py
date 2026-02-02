#!/usr/bin/env python3
"""
安全监控 - 主系统
Security Monitor - Main System

作者: Athena AI系统
创建时间: 2025-11-15
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import ipaddress
import json
import logging
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any

from core.logging_config import setup_logging

from .types import (
    ActionType,
    AlertType,
    AccessPattern,
    BehaviorProfile,
    SecurityEvent,
    SecurityLevel,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class SecurityMonitor:
    """安全监控器

    提供全面的安全防护、风险监控和异常检测能力
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """初始化安全监控器

        Args:
            config: 配置字典
        """
        # 配置参数
        self.config = {
            "max_failed_attempts": 5,
            "lockout_duration": timedelta(minutes=15),
            "anomaly_threshold": 0.7,
            "risk_threshold": 0.8,
            "monitoring_window": timedelta(hours=24),
            "alert_cooldown": timedelta(minutes=5),
            "decision_review_interval": timedelta(minutes=10),
        }
        if config:
            self.config.update(config)

        # 数据存储
        self.security_events = deque(maxlen=10000)
        self.access_patterns = defaultdict(dict)
        self.behavior_profiles: dict[str, BehaviorProfile] = {}
        self.active_alerts: dict[str, SecurityEvent] = {}
        self.quarantined_entities = set()
        self.blocked_ips = set()

        # 监控指标
        self.metrics = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_level": defaultdict(int),
            "false_positives": 0,
            "true_positives": 0,
            "response_times": deque(maxlen=100),
            "blocked_attempts": 0,
        }

        # 威胁模式库
        self.threat_patterns = self._initialize_threat_patterns()

        # 安全规则
        self.security_rules = self._initialize_security_rules()

        # 监控任务
        self.monitoring_tasks: list[asyncio.Task] = []
        self.is_monitoring = False

    def _initialize_threat_patterns(self) -> dict[str, dict[str, Any]]:
        """初始化威胁模式库"""
        return {
            "brute_force": {
                "pattern": "multiple_failed_attempts",
                "threshold": 5,
                "window": timedelta(minutes=15),
                "severity": SecurityLevel.HIGH,
            },
            "ddos": {
                "pattern": "high_request_rate",
                "threshold": 1000,
                "window": timedelta(minutes=1),
                "severity": SecurityLevel.CRITICAL,
            },
            "injection": {
                "pattern": "sql_injection_attempt",
                "indicators": ["'", "--", "OR 1=1", "DROP TABLE"],
                "severity": SecurityLevel.HIGH,
            },
            "xss": {
                "pattern": "xss_attempt",
                "indicators": ["<script>", "javascript:", "onerror="],
                "severity": SecurityLevel.MEDIUM,
            },
        }

    def _initialize_security_rules(self) -> list[dict[str, Any]]:
        """初始化安全规则"""
        return [
            {
                "id": "rate_limiting",
                "type": "access_control",
                "enabled": True,
                "params": {"max_requests_per_minute": 100},
            },
            {
                "id": "ip_blacklist",
                "type": "access_control",
                "enabled": True,
                "params": {"blacklist_file": "config/ip_blacklist.json"},
            },
            {
                "id": "behavior_anomaly_detection",
                "type": "monitoring",
                "enabled": True,
                "params": {"threshold": 0.7},
            },
        ]

    async def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            logger.warning("⚠️  监控已在运行")
            return

        logger.info("🚀 启动安全监控...")
        self.is_monitoring = True

        # 启动各项监控任务
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_access_patterns()),
            asyncio.create_task(self._monitor_behavior_anomalies()),
            asyncio.create_task(self._monitor_decision_integrity()),
            asyncio.create_task(self._monitor_system_health()),
            asyncio.create_task(self._periodic_security_scan()),
        ]

        logger.info("✅ 安全监控已启动")

    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return

        logger.info("🛑 停止安全监控...")
        self.is_monitoring = False

        # 取消所有监控任务
        for task in self.monitoring_tasks:
            if not task.done():
                task.cancel()

        # 等待任务完成
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()

        logger.info("✅ 安全监控已停止")

    async def _monitor_access_patterns(self):
        """监控访问模式"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次

                # 检查所有IP的访问模式
                for ip_address, patterns in list(self.access_patterns.items()):
                    if not patterns:
                        continue

                    pattern = list(patterns.values())[0]
                    risk = self._calculate_access_risk(pattern)

                    if risk > self.config["risk_threshold"]:
                        await self._handle_suspicious_access(ip_address, pattern)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 访问模式监控错误: {e}")

    async def _monitor_behavior_anomalies(self):
        """监控行为异常"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次

                for entity_id, profile in list(self.behavior_profiles.items()):
                    if self._detect_behavior_anomaly(profile):
                        await self._handle_behavior_anomaly(entity_id, profile)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 行为异常监控错误: {e}")

    async def _monitor_decision_integrity(self):
        """监控决策系统完整性"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(
                    self.config["decision_review_interval"].total_seconds()
                )
                await self._check_decision_system_integrity()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 决策完整性监控错误: {e}")

    async def _monitor_system_health(self):
        """监控系统健康状态"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(60)
                resource_status = await self._check_system_resources()

                # 检查资源耗尽
                if any(v > 0.9 for v in resource_status.values()):
                    await self._handle_resource_exhaustion(resource_status)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 系统健康监控错误: {e}")

    async def _periodic_security_scan(self):
        """定期安全扫描"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(300)  # 每5分钟扫描一次
                scan_results = await self._perform_security_scan()

                # 处理发现的安全问题
                for issue in scan_results.get("issues", []):
                    await self._handle_security_issue(issue)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 安全扫描错误: {e}")

    def record_access(
        self,
        ip_address: str,
        user_agent: str,
        success: bool,
        endpoint: str,
        timestamp: datetime | None = None,
    ):
        """记录访问

        Args:
            ip_address: IP地址
            user_agent: 用户代理
            success: 是否成功
            endpoint: 端点
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()

        # 获取或创建访问模式
        if ip_address not in self.access_patterns:
            self.access_patterns[ip_address] = {}

        key = f"{user_agent}:{endpoint}"
        if key not in self.access_patterns[ip_address]:
            self.access_patterns[ip_address][key] = AccessPattern(
                ip_address=ip_address,
                user_agent=user_agent,
                request_count=0,
                failed_attempts=0,
                last_access=timestamp,
            )

        pattern = self.access_patterns[ip_address][key]
        pattern.request_count += 1
        if not success:
            pattern.failed_attempts += 1
        pattern.last_access = timestamp

        # 更新风险评分
        pattern.risk_score = self._calculate_access_risk(pattern)

        # 检查是否可疑
        if self._is_suspicious_access(pattern):
            asyncio.create_task(self._handle_suspicious_access(ip_address, pattern))

    def _calculate_access_risk(self, pattern: AccessPattern) -> float:
        """计算访问风险评分

        Args:
            pattern: 访问模式

        Returns:
            风险评分 (0.0-1.0)
        """
        risk = 0.0

        # 失败尝试风险
        failure_rate = pattern.failed_attempts / max(pattern.request_count, 1)
        risk += failure_rate * 0.4

        # 请求频率风险
        if pattern.request_count > 100:
            risk += 0.3

        # 可疑指示器风险
        risk += len(pattern.suspicious_indicators) * 0.1

        return min(risk, 1.0)

    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """检查是否为可疑IP

        Args:
            ip_address: IP地址

        Returns:
            是否可疑
        """
        try:
            ip = ipaddress.ip_address(ip_address)

            # 检查是否为私有IP
            if ip.is_private:
                return False

            # 检查是否在阻止列表中
            if ip_address in self.blocked_ips:
                return True

            # 检查是否为已知恶意IP范围
            # 这里可以添加更多的检查逻辑
            return False

        except ValueError:
            return True  # 无效IP视为可疑

    def _is_suspicious_access(self, pattern: AccessPattern) -> bool:
        """检查访问是否可疑

        Args:
            pattern: 访问模式

        Returns:
            是否可疑
        """
        return (
            pattern.failed_attempts >= self.config["max_failed_attempts"]
            or pattern.risk_score >= self.config["risk_threshold"]
            or len(pattern.suspicious_indicators) > 0
        )

    async def _handle_suspicious_access(
        self, ip_address: str, pattern: AccessPattern
    ):
        """处理可疑访问

        Args:
            ip_address: IP地址
            pattern: 访问模式
        """
        logger.warning(f"⚠️  检测到可疑访问: {ip_address}")

        # 创建安全事件
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            event_type=AlertType.UNAUTHORIZED_ACCESS,
            security_level=SecurityLevel.HIGH
            if pattern.failed_attempts >= self.config["max_failed_attempts"]
            else SecurityLevel.MEDIUM,
            description=f"检测到来自 {ip_address} 的可疑访问",
            source="security_monitor",
            timestamp=datetime.now(),
            details={
                "ip_address": ip_address,
                "failed_attempts": pattern.failed_attempts,
                "request_count": pattern.request_count,
                "user_agent": pattern.user_agent,
            },
        )

        await self._record_security_event(event)

        # 根据风险等级采取行动
        if event.security_level == SecurityLevel.HIGH:
            await self._block_ip(ip_address)

    async def _block_ip(self, ip_address: str):
        """阻止IP地址

        Args:
            ip_address: IP地址
        """
        logger.warning(f"🚫 阻止IP: {ip_address}")
        self.blocked_ips.add(ip_address)
        self.metrics["blocked_attempts"] += 1

        # 设置自动解封任务
        asyncio.create_task(
            self._auto_unblock_ip(
                ip_address, self.config["lockout_duration"].total_seconds()
            )
        )

    async def _auto_unblock_ip(self, ip_address: str, delay: float):
        """自动解封IP

        Args:
            ip_address: IP地址
            delay: 延迟时间(秒)
        """
        await asyncio.sleep(delay)
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            logger.info(f"✅ 自动解封IP: {ip_address}")

    def record_behavior(
        self,
        entity_id: str,
        entity_type: str,
        behavior_data: dict[str, Any],    ):
        """记录行为

        Args:
            entity_id: 实体ID
            entity_type: 实体类型
            behavior_data: 行为数据
        """
        # 获取或创建行为档案
        if entity_id not in self.behavior_profiles:
            self.behavior_profiles[entity_id] = BehaviorProfile(
                entity_id=entity_id,
                entity_type=entity_type,
                normal_behavior=behavior_data.copy(),
            )

        profile = self.behavior_profiles[entity_id]
        profile.current_behavior = behavior_data
        profile.last_updated = datetime.now()

        # 检测异常
        if self._detect_behavior_anomaly(profile):
            asyncio.create_task(self._handle_behavior_anomaly(entity_id, profile))

    def _detect_behavior_anomaly(self, profile: BehaviorProfile) -> bool:
        """检测行为异常

        Args:
            profile: 行为档案

        Returns:
            是否异常
        """
        # 简化实现:检查信任分数
        if profile.trust_score < self.config["anomaly_threshold"]:
            return True

        # 检查异常计数
        if profile.anomalies_detected > 3:
            return True

        return False

    async def _handle_behavior_anomaly(
        self, entity_id: str, profile: BehaviorProfile
    ):
        """处理行为异常

        Args:
            entity_id: 实体ID
            profile: 行为档案
        """
        logger.warning(f"⚠️  检测到行为异常: {entity_id}")

        profile.anomalies_detected += 1
        profile.trust_score -= 0.1

        # 创建安全事件
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            event_type=AlertType.ANOMALOUS_BEHAVIOR,
            security_level=SecurityLevel.MEDIUM,
            description=f"实体 {entity_id} 表现出异常行为",
            source="security_monitor",
            timestamp=datetime.now(),
            details={
                "entity_id": entity_id,
                "entity_type": profile.entity_type,
                "trust_score": profile.trust_score,
                "anomalies_detected": profile.anomalies_detected,
            },
        )

        await self._record_security_event(event)

    async def _check_decision_system_integrity(self):
        """检查决策系统完整性"""
        # 简化实现
        pass

    async def _check_system_resources(self) -> dict[str, float]:
        """检查系统资源

        Returns:
            资源状态字典
        """
        return {
            "cpu": 0.5,
            "memory": 0.6,
            "disk": 0.4,
        }

    async def _handle_resource_exhaustion(self, resource_status: dict[str, float]):
        """处理资源耗尽

        Args:
            resource_status: 资源状态
        """
        logger.warning(f"⚠️  资源使用率过高: {resource_status}")

        event = SecurityEvent(
            id=str(uuid.uuid4()),
            event_type=AlertType.RESOURCE_ABUSE,
            security_level=SecurityLevel.HIGH,
            description="系统资源耗尽",
            source="security_monitor",
            timestamp=datetime.now(),
            details={"resource_status": resource_status},
        )

        await self._record_security_event(event)

    async def _handle_performance_degradation(self):
        """处理性能下降"""
        logger.warning("⚠️  检测到性能下降")

        event = SecurityEvent(
            id=str(uuid.uuid4()),
            event_type=AlertType.PERFORMANCE_DEGRADATION,
            security_level=SecurityLevel.MEDIUM,
            description="系统性能下降",
            source="security_monitor",
            timestamp=datetime.now(),
        )

        await self._record_security_event(event)

    async def _perform_security_scan(self) -> dict[str, Any]:
        """执行安全扫描

        Returns:
            扫描结果
        """
        issues = []

        # 检查阻止的IP
        if self.blocked_ips:
            issues.append(
                {
                    "type": "blocked_ips",
                    "count": len(self.blocked_ips),
                    "severity": "medium",
                }
            )

        # 检查隔离的实体
        if self.quarantined_entities:
            issues.append(
                {
                    "type": "quarantined_entities",
                    "count": len(self.quarantined_entities),
                    "severity": "high",
                }
            )

        return {"issues": issues, "scan_time": datetime.now()}

    async def _handle_security_issue(self, issue: dict[str, Any]):
        """处理安全问题

        Args:
            issue: 安全问题
        """
        logger.info(f"🔍 处理安全问题: {issue.get('type')}")

    async def _record_security_event(self, event: SecurityEvent):
        """记录安全事件

        Args:
            event: 安全事件
        """
        self.security_events.append(event)
        self.metrics["total_events"] += 1
        self.metrics["events_by_type"][event.event_type] += 1
        self.metrics["events_by_level"][event.security_level] += 1

        # 发送警报
        await self._send_alert(event)

    async def _send_alert(self, event: SecurityEvent):
        """发送警报

        Args:
            event: 安全事件
        """
        self.active_alerts[event.id] = event
        logger.warning(
            f"🚨 安全警报: [{event.security_level.value}] {event.description}"
        )

    def _build_alert_message(self, event: SecurityEvent) -> str:
        """构建警报消息

        Args:
            event: 安全事件

        Returns:
            警报消息
        """
        return f"""
安全警报
--------
级别: {event.security_level.value}
类型: {event.event_type.value}
描述: {event.description}
时间: {event.timestamp}
详情: {json.dumps(event.details, ensure_ascii=False)}
        """

    async def _emergency_response(self, event: SecurityEvent):
        """紧急响应

        Args:
            event: 安全事件
        """
        logger.critical(f"🆘 紧急响应: {event.description}")

        # 执行缓解措施
        for action in event.mitigation_actions:
            if action == ActionType.SHUTDOWN:
                logger.critical("执行紧急关闭")
                # 实际关闭逻辑
            elif action == ActionType.QUARANTINE:
                logger.warning("执行系统隔离")
                self.quarantined_entities.add(event.source)
            elif action == ActionType.ESCALATE:
                logger.warning("上报安全事件")
                # 上报逻辑

    def _cleanup_expired_patterns(self):
        """清理过期模式"""
        cutoff = datetime.now() - self.config["monitoring_window"]

        for ip_address in list(self.access_patterns.keys()):
            for key, pattern in list(self.access_patterns[ip_address].items()):
                if pattern.last_access < cutoff:
                    del self.access_patterns[ip_address][key]

            if not self.access_patterns[ip_address]:
                del self.access_patterns[ip_address]

    def get_security_status(self) -> dict[str, Any]:
        """获取安全状态

        Returns:
            安全状态字典
        """
        return {
            "monitoring_active": self.is_monitoring,
            "total_events": len(self.security_events),
            "active_alerts": len(self.active_alerts),
            "blocked_ips": len(self.blocked_ips),
            "quarantined_entities": len(self.quarantined_entities),
            "monitored_entities": len(self.behavior_profiles),
            "metrics": dict(self.metrics),
        }

    async def generate_security_report(self) -> dict[str, Any]:
        """生成安全报告

        Returns:
            安全报告
        """
        # 转换为列表以便JSON序列化
        events_list = list(self.security_events)

        return {
            "report_time": datetime.now(),
            "monitoring_period": self.config["monitoring_window"],
            "summary": {
                "total_events": len(events_list),
                "events_by_type": dict(self.metrics["events_by_type"]),
                "events_by_level": dict(self.metrics["events_by_level"]),
                "false_positive_rate": self._calculate_false_positive_rate(),
            },
            "events": events_list[-100:],  # 最近100个事件
            "recommendations": self._generate_security_recommendations(events_list),
        }

    def _calculate_false_positive_rate(self) -> float:
        """计算假阳性率

        Returns:
            假阳性率
        """
        total = self.metrics["false_positives"] + self.metrics["true_positives"]
        if total == 0:
            return 0.0
        return self.metrics["false_positives"] / total

    def _generate_security_recommendations(
        self, events: list[SecurityEvent]
    ) -> list[str]:
        """生成安全建议

        Args:
            events: 安全事件列表

        Returns:
            建议列表
        """
        recommendations = []

        # 基于事件类型生成建议
        event_types = defaultdict(int)
        for event in events:
            event_types[event.event_type] += 1

        if event_types[AlertType.UNAUTHORIZED_ACCESS] > 10:
            recommendations.append("考虑加强访问控制和身份验证机制")

        if event_types[AlertType.ANOMALOUS_BEHAVIOR] > 10:
            recommendations.append("建议优化异常检测算法和阈值")

        if event_types[AlertType.RESOURCE_ABUSE] > 5:
            recommendations.append("建议实施更严格的速率限制")

        return recommendations


__all__ = ["SecurityMonitor"]
