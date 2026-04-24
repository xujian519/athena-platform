"""
审计日志管理器

记录系统中的所有敏感操作，提供完整的安全审计追踪。
支持日志查询、导出和完整性验证。

Author: SecurityAgent
Date: 2026-04-24
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import ActionType, AuditLogEntry, OperationResult


class AuditLogger:
    """
    审计日志管理器

    记录系统中所有敏感操作，用于:
    - 安全审计
    - 合规检查
    - 事件调查
    - 行为分析

    Features:
    - 完整的操作日志记录
    - 日志防篡改（HMAC签名）
    - 灵活的查询接口
    - 日志导出（JSON/CSV）
    - 线程安全
    """

    # 默认数据库路径
    DEFAULT_DB_PATH = Path.home() / ".athena" / "audit_logs.db"

    # HMAC密钥（生产环境应从安全配置加载）
    HMAC_KEY = b"athena_audit_log_hmac_key_change_in_production"

    def __init__(
        self,
        db_path: Optional[Path | str] = None,
        hmac_key: Optional[bytes] = None,
        auto_init: bool = True,
    ):
        """
        初始化审计日志管理器

        Args:
            db_path: 数据库路径
            hmac_key: HMAC签名密钥
            auto_init: 是否自动初始化数据库
        """
        self._db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self._hmac_key = hmac_key if hmac_key else self.HMAC_KEY
        self._lock = threading.Lock()
        self._local = threading.local()

        # 确保目录存在
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        if auto_init:
            self._init_database()

    @property
    def _conn(self) -> sqlite3.Connection:
        """获取线程本地数据库连接"""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(self._db_path))
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            # 审计日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    result TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT,
                    hmac TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
                ON audit_logs(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_user
                ON audit_logs(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_action
                ON audit_logs(action)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_resource
                ON audit_logs(resource_type, resource_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_result
                ON audit_logs(result)
            """)

            conn.commit()

    def _compute_hmac(self, data: dict[str, Any]) -> str:
        """
        计算日志条目的HMAC签名

        Args:
            data: 日志数据

        Returns:
            HMAC签名的十六进制字符串
        """
        # 创建规范化字符串
        normalized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hmac.new(self._hmac_key, normalized.encode(), hashlib.sha256).hexdigest()

    def _verify_hmac(self, entry: AuditLogEntry) -> bool:
        """
        验证日志条目的HMAC签名

        Args:
            entry: 审计日志条目

        Returns:
            签名是否有效
        """
        # 获取存储的HMAC
        stored_hmac = entry.details.get("_hmac", "")
        if not stored_hmac:
            return False

        # 计算HMAC时移除details中的_hmac字段
        data = entry.to_dict()
        if "details" in data and "_hmac" in data["details"]:
            data["details"] = {k: v for k, v in data["details"].items() if k != "_hmac"}

        computed_hmac = self._compute_hmac(data)

        return hmac.compare_digest(computed_hmac, stored_hmac)

    # ========== 日志记录 ==========

    def log(
        self,
        action: ActionType | str,
        user_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        result: OperationResult | str = OperationResult.SUCCESS,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditLogEntry:
        """
        记录审计日志

        Args:
            action: 操作类型
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            result: 操作结果
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
            session_id: 会话ID

        Returns:
            审计日志条目
        """
        if isinstance(action, str):
            try:
                action = ActionType(action)
            except ValueError:
                action = ActionType.SYSTEM

        if isinstance(result, str):
            try:
                result = OperationResult(result)
            except ValueError:
                result = OperationResult.SUCCESS

        entry = AuditLogEntry(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )

        return self._save_entry(entry)

    def _save_entry(self, entry: AuditLogEntry) -> AuditLogEntry:
        """保存日志条目到数据库"""
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            # 计算HMAC（基于原始数据，不包含_hmac）
            data = entry.to_dict()
            hmac_value = self._compute_hmac(data)

            # 保存到数据库（details保持原样，不添加_hmac）
            cursor.execute(
                """
                INSERT INTO audit_logs
                (id, timestamp, user_id, action, resource_type, resource_id,
                 result, details, ip_address, user_agent, session_id, hmac)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.timestamp.isoformat(),
                    entry.user_id,
                    entry.action.value if isinstance(entry.action, ActionType) else entry.action,
                    entry.resource_type,
                    entry.resource_id,
                    entry.result.value if isinstance(entry.result, OperationResult) else entry.result,
                    json.dumps(entry.details),
                    entry.ip_address,
                    entry.user_agent,
                    entry.session_id,
                    hmac_value,
                ),
            )

            conn.commit()

            # 返回entry的副本，不修改原始entry的details
            return entry

    # 便捷方法
    def log_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        success: bool = True,
        **kwargs,
    ) -> AuditLogEntry:
        """记录访问操作"""
        return self.log(
            action=ActionType.ACCESS,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            result=OperationResult.SUCCESS if success else OperationResult.DENIED,
            **kwargs,
        )

    def log_permission_change(
        self,
        user_id: str,
        target_user_id: str,
        permission: str,
        granted: bool,
        **kwargs,
    ) -> AuditLogEntry:
        """记录权限变更"""
        details = kwargs.get("details", {})
        details.update({
            "target_user_id": target_user_id,
            "permission": permission,
            "change_type": "grant" if granted else "revoke",
        })

        return self.log(
            action=ActionType.GRANT_PERMISSION if granted else ActionType.REVOKE_PERMISSION,
            user_id=user_id,
            details=details,
            **kwargs,
        )

    def log_operation(
        self,
        user_id: str,
        operation: str,
        resource_type: str = "",
        resource_id: str = "",
        success: bool = True,
        **kwargs,
    ) -> AuditLogEntry:
        """记录通用操作"""
        return self.log(
            action=ActionType(operation) if operation in ActionType.__members__ else ActionType.SYSTEM,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            result=OperationResult.SUCCESS if success else OperationResult.FAILURE,
            **kwargs,
        )

    # ========== 日志查询 ==========

    def query_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[ActionType | str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: Optional[OperationResult | str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        """
        查询审计日志

        Args:
            user_id: 用户ID过滤
            action: 操作类型过滤
            resource_type: 资源类型过滤
            resource_id: 资源ID过滤
            result: 结果过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            审计日志条目列表
        """
        conn = self._conn
        cursor = conn.cursor()

        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if action:
            action_value = action.value if isinstance(action, ActionType) else action
            query += " AND action = ?"
            params.append(action_value)

        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)

        if resource_id:
            query += " AND resource_id = ?"
            params.append(resource_id)

        if result:
            result_value = result.value if isinstance(result, OperationResult) else result
            query += " AND result = ?"
            params.append(result_value)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)

        entries = []
        for row in cursor.fetchall():
            details = json.loads(row["details"]) if row["details"] else {}
            # 将HMAC存储到details中用于验证
            if row["hmac"]:
                details["_hmac"] = row["hmac"]

            entry = AuditLogEntry.from_dict({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "user_id": row["user_id"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "result": row["result"],
                "details": details,
                "ip_address": row["ip_address"],
                "user_agent": row["user_agent"],
                "session_id": row["session_id"],
            })
            entries.append(entry)

        return entries

    def get_user_activity(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """
        获取用户活动日志

        Args:
            user_id: 用户ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制

        Returns:
            用户活动日志列表
        """
        return self.query_logs(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """
        获取资源操作历史

        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            limit: 返回数量限制

        Returns:
            资源操作历史列表
        """
        return self.query_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )

    def get_failed_attempts(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """
        获取失败的操作记录

        Args:
            user_id: 用户ID过滤
            start_time: 开始时间
            limit: 返回数量限制

        Returns:
            失败操作列表
        """
        return self.query_logs(
            user_id=user_id,
            result=OperationResult.FAILURE,
            start_time=start_time,
            limit=limit,
        )

    # ========== 日志导出 ==========

    def export_json(
        self,
        output_path: Path | str,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        导出日志为JSON格式

        Args:
            output_path: 输出文件路径
            user_id: 用户ID过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            导出的日志条目数量
        """
        entries = self.query_logs(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000000,  # 大量导出
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([entry.to_dict() for entry in entries], f, indent=2, ensure_ascii=False)

        return len(entries)

    def export_csv(
        self,
        output_path: Path | str,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        导出日志为CSV格式

        Args:
            output_path: 输出文件路径
            user_id: 用户ID过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            导出的日志条目数量
        """
        entries = self.query_logs(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000000,
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # 写入表头
            writer.writerow([
                "ID",
                "Timestamp",
                "User ID",
                "Action",
                "Resource Type",
                "Resource ID",
                "Result",
                "IP Address",
                "User Agent",
                "Session ID",
            ])

            # 写入数据
            for entry in entries:
                writer.writerow([
                    entry.id,
                    entry.timestamp.isoformat(),
                    entry.user_id,
                    entry.action.value if isinstance(entry.action, ActionType) else entry.action,
                    entry.resource_type,
                    entry.resource_id,
                    entry.result.value if isinstance(entry.result, OperationResult) else entry.result,
                    entry.ip_address or "",
                    entry.user_agent or "",
                    entry.session_id or "",
                ])

        return len(entries)

    # ========== 完整性验证 ==========

    def verify_integrity(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        验证审计日志的完整性

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            验证结果字典
        """
        entries = self.query_logs(
            start_time=start_time,
            end_time=end_time,
            limit=1000000,
        )

        valid_count = 0
        invalid_count = 0
        invalid_entries = []

        for entry in entries:
            if self._verify_hmac(entry):
                valid_count += 1
            else:
                invalid_count += 1
                invalid_entries.append(entry.id)

        return {
            "total": len(entries),
            "valid": valid_count,
            "invalid": invalid_count,
            "invalid_entries": invalid_entries,
            "integrity_rate": valid_count / len(entries) if entries else 1.0,
        }

    # ========== 统计信息 ==========

    def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        获取审计日志统计信息

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息字典
        """
        conn = self._conn
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM audit_logs WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        cursor.execute(query, params)
        total = cursor.fetchone()[0]

        # 按操作类型统计
        cursor.execute(
            "SELECT action, COUNT(*) FROM audit_logs GROUP BY action ORDER BY COUNT(*) DESC"
        )
        action_stats = {row[0]: row[1] for row in cursor.fetchall()}

        # 按结果统计
        cursor.execute(
            "SELECT result, COUNT(*) FROM audit_logs GROUP BY result"
        )
        result_stats = {row[0]: row[1] for row in cursor.fetchall()}

        # 按用户统计（前10）
        cursor.execute(
            """
            SELECT user_id, COUNT(*) as count
            FROM audit_logs
            WHERE user_id != ''
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
            """
        )
        user_stats = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "total_entries": total,
            "by_action": action_stats,
            "by_result": result_stats,
            "top_users": user_stats,
        }

    # ========== 清理 ==========

    def cleanup_old_logs(
        self,
        before: datetime,
        keep_failed: bool = True,
    ) -> int:
        """
        清理旧日志

        Args:
            before: 清除此时间之前的日志
            keep_failed: 是否保留失败的日志

        Returns:
            清理的日志数量
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            query = "DELETE FROM audit_logs WHERE timestamp < ?"
            params = [before.isoformat()]

            if keep_failed:
                query += " AND result != ?"
                params.append(OperationResult.FAILURE.value)

            cursor.execute(query, params)
            conn.commit()

            return cursor.rowcount

    def close(self) -> None:
        """关闭数据库连接"""
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            delattr(self._local, "conn")
