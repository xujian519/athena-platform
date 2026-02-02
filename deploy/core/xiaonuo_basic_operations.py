#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺基础操作模块
Xiaonuo Basic Operations - 实现小诺直接控制的基础操作
"""

import json
import sqlite3
import os
import shutil
import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from pathlib import Path

# 尝试导入PostgreSQL支持
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logging.warning("PostgreSQL support not available. Install with: pip install psycopg2-binary")

# 导入PostgreSQL配置
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.postgresql_config import POSTGRESQL_CONFIG, TABLE_CONFIG, SQL_TEMPLATES

logger = logging.getLogger(__name__)

class PostgreSQLManager:
    """PostgreSQL管理器 - 处理PostgreSQL数据库操作"""

    def __init__(self, config: Dict | None = None):
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("PostgreSQL support not available")

        self.config = config or POSTGRESQL_CONFIG["main"]
        self.connection = None

    def get_connection(self):
        """获取PostgreSQL连接"""
        if not self.connection or self.connection.closed:
            try:
                self.connection = psycopg2.connect(
                    host=self.config["host"],
                    port=self.config["port"],
                    database=self.config["database"],
                    user=self.config["user"],
                    password=self.config.get("password", "")
                )
                logger.info(f"PostgreSQL连接成功: {self.config['database']}")
            except Exception as e:
                logger.error(f"PostgreSQL连接失败: {e}")
                raise
        return self.connection

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询语句"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []
        finally:
            conn.close()

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """执行更新语句"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"更新失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

class DatabaseManager:
    """数据库管理器 - 处理SQLite数据库操作"""

    def __init__(self, base_path: str = "/Users/xujian/Athena工作平台/deploy/data"):
        self.base_path = Path(base_path)
        self.supported_databases = {
            "xiaonuo_life.db": "小诺生活数据库",
            "xiaonuo_knowledge.db": "小诺知识数据库",
            "performance_metrics.db": "性能指标数据库",
            "baochen_finance.db": "宝辰财务数据库"
        }

    def get_connection(self, db_name: str) -> sqlite3.Connection | None:
        """获取数据库连接"""
        if db_name not in self.supported_databases:
            logger.error(f"不支持的数据库: {db_name}")
            return None

        db_path = self.base_path / db_name
        if not db_path.exists():
            logger.warning(f"数据库文件不存在: {db_path}")
            # 创建新数据库
            conn = sqlite3.connect(str(db_path))
            self._initialize_database(conn, db_name)
            return conn

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # 以字典形式返回结果
            return conn
        except Exception as e:
            logger.error(f"连接数据库失败 {db_name}: {e}")
            return None

    def _initialize_database(self, conn: sqlite3.Connection, db_name: str):
        """初始化数据库表结构"""
        cursor = conn.cursor()

        if db_name == "xiaonuo_life.db":
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT,
                    mood TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 1,
                    due_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')

        elif db_name == "performance_metrics.db":
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_unit TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')

        elif db_name == "baochen_finance.db":
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    service_type TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    amount REAL NOT NULL,
                    payment_type TEXT,
                    payment_date TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customer_records (id)
                )
            ''')

        conn.commit()

    def execute_query(self, db_name: str, query: str, params: tuple = ()) -> List[Dict]:
        """执行查询语句"""
        conn = self.get_connection(db_name)
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []
        finally:
            conn.close()

    def execute_update(self, db_name: str, query: str, params: tuple = ()) -> bool:
        """执行更新语句"""
        conn = self.get_connection(db_name)
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def backup_database(self, db_name: str) -> bool:
        """备份数据库"""
        if db_name not in self.supported_databases:
            return False

        source_path = self.base_path / db_name
        backup_dir = self.base_path / "backup"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{db_name}.backup_{timestamp}"
        backup_path = backup_dir / backup_name

        try:
            shutil.copy2(source_path, backup_path)
            logger.info(f"数据库备份成功: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False

class FileManager:
    """文件管理器 - 处理文件和目录操作"""

    def __init__(self, base_path: str = "/Users/xujian/Athena工作平台/deploy"):
        self.base_path = Path(base_path)

    def list_files(self, directory: str, pattern: str = "*", recursive: bool = False) -> List[Dict[str, Any]]:
        """列出文件"""
        dir_path = self.base_path / directory
        if not dir_path.exists():
            return []

        files = []
        if recursive:
            file_list = list(dir_path.rglob(pattern))
        else:
            file_list = list(dir_path.glob(pattern))

        for file_path in file_list:
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(self.base_path)),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_directory": False
                })
            elif file_path.is_dir():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(self.base_path)),
                    "size": 0,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "is_directory": True
                })

        return files

    def read_file(self, file_path: str) -> str | None:
        """读取文件内容"""
        full_path = self.base_path / file_path
        if not full_path.exists():
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return None

    def write_file(self, file_path: str, content: str, create_dirs: bool = True) -> bool:
        """写入文件内容"""
        full_path = self.base_path / file_path

        if create_dirs:
            full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"写入文件失败 {file_path}: {e}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        full_path = self.base_path / file_path
        if not full_path.exists():
            return False

        try:
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(full_path)
            return True
        except Exception as e:
            logger.error(f"删除失败 {file_path}: {e}")
            return False

    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """复制文件"""
        source = self.base_path / source_path
        dest = self.base_path / dest_path

        if not source.exists():
            return False

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if source.is_file():
                shutil.copy2(source, dest)
            elif source.is_dir():
                shutil.copytree(source, dest, dirs_exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"复制失败 {source_path} -> {dest_path}: {e}")
            return False

class PostgreSQLCustomerManager:
    """PostgreSQL客户资料管理器 - 处理PostgreSQL中的客户数据"""

    def __init__(self):
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("PostgreSQL not available")
        self.pg_manager = PostgreSQLManager()
        self.table_config = TABLE_CONFIG["customers"]

    def query_customers(self, customer_id: str | None = None,
                       customer_name: str | None = None,
                       limit: int = 100) -> List[Dict]:
        """查询客户资料"""
        table = self.table_config["table_name"]

        if customer_id:
            query = SQL_TEMPLATES["customers"]["select_by_id"].format(table=table)
            params = (customer_id,)
        elif customer_name:
            query = SQL_TEMPLATES["customers"]["select_by_name"].format(table=table)
            params = (f"%{customer_name}%",)
        else:
            query = SQL_TEMPLATES["customers"]["select_all"].format(table=table)
            params = ()

        query += f" LIMIT {limit}"
        return self.pg_manager.execute_query(query, params)

    def create_customer(self, customer_data: Dict[str, Any]) -> str | None:
        """创建客户资料"""
        required_fields = ["name"]
        for field in required_fields:
            if field not in customer_data:
                logger.error(f"缺少必需字段: {field}")
                return None

        table = self.table_config["table_name"]
        query = SQL_TEMPLATES["customers"]["insert"].format(table=table)

        # 生成UUID
        customer_id = str(uuid.uuid4())

        params = (
            customer_id,
            customer_data.get("name"),
            customer_data.get("type", "COMPANY"),
            customer_data.get("contact_person"),
            customer_data.get("contact_phone"),
            customer_data.get("contact_email"),
            customer_data.get("source", "manual"),
            customer_data.get("tenant_id", "yunpat-main")
        )

        if self.pg_manager.execute_update(query, params):
            return customer_id
        return None

    def update_customer(self, customer_id: str, update_data: Dict[str, Any]) -> bool:
        """更新客户资料"""
        table = self.table_config["table_name"]
        query = SQL_TEMPLATES["customers"]["update"].format(table=table)

        params = (
            update_data.get("name"),
            update_data.get("contact_person"),
            update_data.get("contact_phone"),
            update_data.get("contact_email"),
            customer_id
        )

        return self.pg_manager.execute_update(query, params)

    def delete_customer(self, customer_id: str) -> bool:
        """删除客户资料"""
        table = self.table_config["table_name"]
        query = SQL_TEMPLATES["customers"]["delete"].format(table=table)

        return self.pg_manager.execute_update(query, (customer_id,))

    def get_customer_projects(self, customer_id: str) -> List[Dict]:
        """获取客户项目"""
        table = TABLE_CONFIG["projects"]["table_name"]
        query = SQL_TEMPLATES["projects"]["select_by_client"].format(table=table)

        return self.pg_manager.execute_query(query, (customer_id,))

    def get_customer_count(self) -> int:
        """获取客户总数"""
        table = self.table_config["table_name"]
        query = SQL_TEMPLATES["customers"]["count"].format(table=table)

        result = self.pg_manager.execute_query(query)
        return result[0]["count"] if result else 0

class CustomerDataManager:
    """客户资料管理器 - 统一处理客户资料数据"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.pg_customer_manager = None

        # 尝试初始化PostgreSQL管理器
        if POSTGRESQL_AVAILABLE:
            try:
                self.pg_customer_manager = PostgreSQLCustomerManager()
                logger.info("PostgreSQL客户管理器已启用")
            except Exception as e:
                logger.warning(f"PostgreSQL客户管理器初始化失败: {e}")

        self.file_manager = FileManager()

    def use_postgresql(self) -> bool:
        """检查是否可以使用PostgreSQL"""
        return self.pg_customer_manager is not None

    def query_customer(self, customer_id: str | None = None,
                      customer_name: str | None = None,
                      phone: str | None = None) -> List[Dict]:
        """查询客户资料"""
        # 优先使用PostgreSQL
        if self.use_postgresql():
            logger.info("使用PostgreSQL查询客户资料")
            return self.pg_customer_manager.query_customers(
                customer_id=customer_id,
                customer_name=customer_name
            )
        else:
            # 回退到SQLite
            logger.info("使用SQLite查询客户资料")
            conditions = []
            params = []

            if customer_id:
                conditions.append("id = ?")
                params.append(customer_id)
            if customer_name:
                conditions.append("customer_name LIKE ?")
                params.append(f"%{customer_name}%")
            if phone:
                conditions.append("phone LIKE ?")
                params.append(f"%{phone}%")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f'''
                SELECT * FROM customer_records
                WHERE {where_clause}
                ORDER BY created_at DESC
            '''

            return self.db_manager.execute_query("baochen_finance.db", query, tuple(params))

    def create_customer(self, customer_data: Dict[str, Any]) -> str | None:
        """创建客户资料"""
        # 优先使用PostgreSQL
        if self.use_postgresql():
            logger.info("使用PostgreSQL创建客户资料")

            # 转换字段名
            pg_data = {}
            if "customer_name" in customer_data:
                pg_data["name"] = customer_data["customer_name"]
            elif "name" in customer_data:
                pg_data["name"] = customer_data["name"]
            else:
                logger.error("缺少必需字段: name")
                return None

            # 映射其他字段
            pg_data["contact_person"] = customer_data.get("contact_person")
            pg_data["contact_phone"] = customer_data.get("phone") or customer_data.get("contact_phone")
            pg_data["contact_email"] = customer_data.get("email") or customer_data.get("contact_email")
            pg_data["type"] = customer_data.get("type", "COMPANY")
            pg_data["source"] = "xiaonuo_hybrid"

            return self.pg_customer_manager.create_customer(pg_data)
        else:
            # 回退到SQLite
            logger.info("使用SQLite创建客户资料")
            required_fields = ["customer_name"]
            for field in required_fields:
                if field not in customer_data:
                    logger.error(f"缺少必需字段: {field}")
                    return None

            query = '''
                INSERT INTO customer_records
                (customer_name, phone, email, service_type, status)
                VALUES (?, ?, ?, ?, ?)
            '''

            params = (
                customer_data.get("customer_name"),
                customer_data.get("phone"),
                customer_data.get("email"),
                customer_data.get("service_type"),
                customer_data.get("status", "active")
            )

            if self.db_manager.execute_update("baochen_finance.db", query, params):
                # 获取新插入的ID
                result = self.db_manager.execute_query("baochen_finance.db", "SELECT last_insert_rowid() as id")
                return result[0]["id"] if result else None

            return None

    def update_customer(self, customer_id: int, update_data: Dict[str, Any]) -> bool:
        """更新客户资料"""
        if not update_data:
            return False

        set_clauses = []
        params = []

        allowed_fields = ["customer_name", "phone", "email", "service_type", "status"]
        for field in allowed_fields:
            if field in update_data:
                set_clauses.append(f"{field} = ?")
                params.append(update_data[field])

        if not set_clauses:
            return False

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(customer_id)

        query = f'''
            UPDATE customer_records
            SET {", ".join(set_clauses)}
            WHERE id = ?
        '''

        return self.db_manager.execute_update("baochen_finance.db", query, tuple(params))

    def delete_customer(self, customer_id: int) -> bool:
        """删除客户资料"""
        # 先删除相关的支付记录
        self.db_manager.execute_update("baochen_finance.db",
                                      "DELETE FROM payment_records WHERE customer_id = ?",
                                      (customer_id,))

        # 删除客户记录
        query = "DELETE FROM customer_records WHERE id = ?"
        return self.db_manager.execute_update("baochen_finance.db", query, (customer_id,))

    def get_customer_file(self, customer_name: str) -> Dict | None:
        """获取客户档案文件"""
        file_pattern = f"客户档案_*{customer_name}*.json"
        files = self.file_manager.list_files("data", file_pattern)

        if files:
            # 返回最新的文件
            files.sort(key=lambda x: x["modified"], reverse=True)
            file_path = files[0]["path"]
            content = self.file_manager.read_file(file_path)
            if content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.error(f"JSON解析失败: {file_path}")
        return None

class PerformanceMonitor:
    """性能监控器 - 收集和分析系统性能数据"""

    def __init__(self):
        self.db_manager = DatabaseManager()

    def record_metric(self, metric_name: str, value: float, unit: str = "",
                     metadata: Dict | None = None):
        """记录性能指标"""
        query = '''
            INSERT INTO system_metrics
            (metric_name, metric_value, metric_unit, metadata)
            VALUES (?, ?, ?, ?)
        '''

        metadata_json = json.dumps(metadata) if metadata else None
        self.db_manager.execute_update("performance_metrics.db", query,
                                      (metric_name, value, unit, metadata_json))

    def get_metrics(self, metric_name: str | None = None,
                   start_time: datetime | None = None,
                   end_time: datetime | None = None,
                   limit: int = 100) -> List[Dict]:
        """获取性能指标"""
        conditions = []
        params = []

        if metric_name:
            conditions.append("metric_name = ?")
            params.append(metric_name)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f'''
            SELECT * FROM system_metrics
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        '''

        params.append(limit)
        return self.db_manager.execute_query("performance_metrics.db", query, tuple(params))

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态概览"""
        # 获取最近的性能指标
        recent_metrics = self.get_metrics(limit=10)

        # 计算系统负载
        cpu_usage = self._get_cpu_usage()
        memory_usage = self._get_memory_usage()
        disk_usage = self._get_disk_usage()

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "recent_metrics": recent_metrics,
            "database_status": self._check_database_status(),
            "agent_status": self._check_agent_status()
        }

    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0

    def _get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "total": memory.total,
                "used": memory.used,
                "percent": memory.percent
            }
        except ImportError:
            return {"total": 0, "used": 0, "percent": 0.0}

    def _get_disk_usage(self) -> Dict[str, float]:
        """获取磁盘使用情况"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                "total": disk.total,
                "used": disk.used,
                "percent": disk.percent
            }
        except ImportError:
            return {"total": 0, "used": 0, "percent": 0.0}

    def _check_database_status(self) -> Dict[str, bool]:
        """检查数据库状态"""
        status = {}
        for db_name in self.db_manager.supported_databases:
            conn = self.db_manager.get_connection(db_name)
            status[db_name] = conn is not None
            if conn:
                conn.close()
        return status

    def _check_agent_status(self) -> Dict[str, str]:
        """检查智能体状态"""
        # 这里应该调用agent_orchestrator来获取实际状态
        # 简化实现，返回模拟状态
        return {
            "xiaonuo": "active",
            "xiaona": "inactive",
            "yunxi": "inactive",
            "athena": "inactive"
        }

class XiaonuoBasicOperations:
    """小诺基础操作管理器 - 统一接口"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.file_manager = FileManager()
        self.customer_manager = CustomerDataManager()
        self.performance_monitor = PerformanceMonitor()

    async def execute_operation(self, operation: str, target: str,
                              data: Dict | None = None) -> Dict[str, Any]:
        """执行基础操作"""
        try:
            # 记录操作开始
            start_time = datetime.now()
            logger.info(f"小诺执行操作: {operation} -> {target}")

            result = None

            # 数据库操作
            if operation == "query":
                if target.startswith("customer:"):
                    # 查询客户
                    customer_id = target.split(":")[1] if ":" in target else None
                    result = self.customer_manager.query_customer(customer_id)
                elif target.startswith("system_status"):
                    result = self.performance_monitor.get_system_status()
                else:
                    # 通用数据库查询
                    result = self.db_manager.execute_query(target, data.get("query", ""))

            elif operation == "create":
                if target == "customer":
                    result = {"customer_id": self.customer_manager.create_customer(data)}
                elif target.startswith("file:"):
                    file_path = target[5:]
                    success = self.file_manager.write_file(file_path, json.dumps(data, indent=2))
                    result = {"success": success}

            elif operation == "update":
                if target.startswith("customer:"):
                    customer_id = int(target.split(":")[1])
                    success = self.customer_manager.update_customer(customer_id, data)
                    result = {"success": success}

            elif operation == "delete":
                if target.startswith("customer:"):
                    customer_id = int(target.split(":")[1])
                    success = self.customer_manager.delete_customer(customer_id)
                    result = {"success": success}
                elif target.startswith("file:"):
                    file_path = target[5:]
                    success = self.file_manager.delete_file(file_path)
                    result = {"success": success}

            elif operation == "list":
                if target.startswith("files:"):
                    directory = target[6:] if ":" in target else ""
                    pattern = data.get("pattern", "*") if data else "*"
                    result = self.file_manager.list_files(directory, pattern)

            elif operation == "backup":
                if target in self.db_manager.supported_databases:
                    success = self.db_manager.backup_database(target)
                    result = {"success": success}

            # 记录性能指标
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self.performance_monitor.record_metric(f"operation_{operation}", duration, "seconds")

            # 返回结果
            return {
                "success": True,
                "operation": operation,
                "target": target,
                "result": result,
                "duration": duration,
                "timestamp": end_time.isoformat(),
                "processor": "xiaonuo_basic"
            }

        except Exception as e:
            logger.error(f"操作执行失败: {e}")
            return {
                "success": False,
                "operation": operation,
                "target": target,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processor": "xiaonuo_basic"
            }

# 全局实例
xiaonuo_operations = XiaonuoBasicOperations()

# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test_operations():
        """测试基础操作"""
        print("🔧 小诺基础操作测试")
        print("=" * 50)

        operations = xiaonuo_operations

        # 测试客户查询
        print("\n📋 测试客户查询...")
        result = await operations.execute_operation("query", "customer:")
        print(f"查询结果: {result}")

        # 测试客户创建
        print("\n➕ 测试客户创建...")
        test_customer = {
            "customer_name": "测试客户",
            "phone": "13800138000",
            "email": "test@example.com",
            "service_type": "专利申请"
        }
        result = await operations.execute_operation("create", "customer", test_customer)
        print(f"创建结果: {result}")

        # 测试系统状态
        print("\n📊 测试系统状态查询...")
        result = await operations.execute_operation("query", "system_status")
        print(f"系统状态: {result}")

        # 测试文件列表
        print("\n📁 测试文件列表...")
        result = await operations.execute_operation("list", "files:data", {"pattern": "*.db"})
        print(f"文件列表: {len(result['result'])} 个文件")

    asyncio.run(test_operations())