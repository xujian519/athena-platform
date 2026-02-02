#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户关系管理器
Customer Relationship Manager - 客户关联数据管理

提供客户与案卷、任务、文档等的完整关联管理功能
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json

from .xiaonuo_basic_operations import PostgreSQLManager, CustomerDataManager

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """关系类型枚举"""
    CUSTOMER_CASES = "customer_cases"
    CUSTOMER_TASKS = "customer_tasks"
    CUSTOMER_DOCUMENTS = "customer_documents"
    CUSTOMER_CONTACTS = "customer_contacts"
    CUSTOMER_FINANCIAL = "customer_financial"


class CustomerRelationshipManager:
    """客户关系管理器 - 处理客户与各业务模块的关联关系"""

    def __init__(self, config: Dict | None = None):
        """
        初始化客户关系管理器

        Args:
            config: 数据库配置
        """
        self.basic_ops = CustomerDataManager()
        self.pg_manager = None

        if self.basic_ops.use_postgresql():
            self.pg_manager = self.basic_ops.pg_customer_manager

    def get_customer_complete_info(self, customer_id: str) -> Dict[str, Any]:
        """
        获取客户完整信息（包含所有关联数据）

        Args:
            customer_id: 客户ID

        Returns:
            客户完整信息字典
        """
        try:
            # 获取基本信息
            customer_info = self._get_customer_basic_info(customer_id)
            if not customer_info:
                return {"error": "客户不存在"}

            # 获取关联数据
            customer_info["cases"] = self._get_customer_cases(customer_id)
            customer_info["tasks"] = self._get_customer_tasks(customer_id)
            customer_info["documents"] = self._get_customer_documents(customer_id)
            customer_info["financial_summary"] = self._get_customer_financial_summary(customer_id)
            customer_info["recent_activities"] = self._get_customer_recent_activities(customer_id)
            customer_info["statistics"] = self._get_customer_statistics(customer_id)

            return customer_info

        except Exception as e:
            logger.error(f"获取客户完整信息失败: {str(e)}")
            return {"error": str(e)}

    def _get_customer_basic_info(self, customer_id: str) -> Dict[str, Any | None]:
        """获取客户基本信息"""
        try:
            if self.pg_manager:
                customers = self.pg_manager.query_customers(customer_id=customer_id)
                return customers[0] if customers else None
            else:
                # SQLite实现
                customers = self.basic_ops.query_customer(customer_id=customer_id)
                return customers[0] if customers else None
        except Exception as e:
            logger.error(f"获取客户基本信息失败: {str(e)}")
            return None

    def _get_customer_cases(self, customer_id: str) -> List[Dict[str, Any]]:
        """获取客户案卷信息"""
        try:
            if not self.pg_manager:
                return []

            query = """
            SELECT
                id as case_id,
                case_number,
                title as case_title,
                type as case_type,
                current_stage as case_status,
                applicant,
                filing_date,
                acceptance_number,
                patent_number,
                created_at,
                updated_at
            FROM cases
            WHERE client_id = %s
            ORDER BY created_at DESC
            """

            return self.pg_manager.execute_query(query, (customer_id,))
        except Exception as e:
            logger.error(f"获取客户案卷失败: {str(e)}")
            return []

    def _get_customer_tasks(self, customer_id: str) -> List[Dict[str, Any]]:
        """获取客户任务信息"""
        try:
            if not self.pg_manager:
                return []

            # 检查任务状态枚举值
            enum_check_query = """
            SELECT unnest(enumlabel) as status_value
            FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'task_status_enum')
            """

            try:
                enum_values = self.pg_manager.execute_query(enum_check_query)
                status_list = [row["status_value"] for row in enum_values]
                logger.info(f"任务状态枚举值: {status_list}")
            except:
                status_list = ['pending', 'in_progress', 'completed', 'cancelled']

            # 使用实际的状态值
            status_placeholder = "'" + "', '".join(status_list) + "'"

            query = f"""
            SELECT
                id as task_id,
                title as task_title,
                description as task_description,
                task_type,
                status as task_status,
                priority,
                assigned_to,
                start_date,
                due_date,
                completed_date,
                created_at,
                updated_at,
                notes
            FROM tasks
            WHERE client_id = %s
            ORDER BY created_at DESC
            """

            return self.pg_manager.execute_query(query, (customer_id,))
        except Exception as e:
            logger.error(f"获取客户任务失败: {str(e)}")
            return []

    def _get_customer_documents(self, customer_id: str) -> List[Dict[str, Any]]:
        """获取客户文档信息"""
        try:
            if not self.pg_manager:
                return []

            query = """
            SELECT
                id as document_id,
                name as document_name,
                type as document_type,
                category as document_category,
                file_name,
                file_size,
                upload_time,
                uploaded_by,
                created_at,
                tags,
                description
            FROM documents
            WHERE client_id = %s
            ORDER BY upload_time DESC
            """

            return self.pg_manager.execute_query(query, (customer_id,))
        except Exception as e:
            logger.error(f"获取客户文档失败: {str(e)}")
            return []

    def _get_customer_financial_summary(self, customer_id: str) -> Dict[str, Any]:
        """获取客户财务汇总"""
        try:
            if not self.pg_manager:
                return {"total_paid": 0, "total_unpaid": 0, "transaction_count": 0}

            query = """
            SELECT
                COALESCE(SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0) as total_expense,
                COUNT(*) as transaction_count
            FROM financial_records
            WHERE client_id = %s
            """

            result = self.pg_manager.execute_query(query, (customer_id,))
            return result[0] if result else {"total_income": 0, "total_expense": 0, "transaction_count": 0}
        except Exception as e:
            logger.error(f"获取客户财务汇总失败: {str(e)}")
            return {"total_income": 0, "total_expense": 0, "transaction_count": 0}

    def _get_customer_recent_activities(self, customer_id: str) -> List[Dict[str, Any]]:
        """获取客户最近活动"""
        try:
            if not self.pg_manager:
                return []

            # 获取最近的任务、案卷、文档更新
            activities = []

            # 最近任务
            task_query = """
            SELECT
                'task' as activity_type,
                title as activity_title,
                status as activity_status,
                updated_at as activity_time,
                assigned_to as activity_person
            FROM tasks
            WHERE client_id = %s
            ORDER BY updated_at DESC
            LIMIT 3
            """

            tasks = self.pg_manager.execute_query(task_query, (customer_id,))
            activities.extend(tasks)

            # 最近案卷
            case_query = """
            SELECT
                'case' as activity_type,
                title as activity_title,
                current_stage as activity_status,
                updated_at as activity_time,
                contact_person as activity_person
            FROM cases
            WHERE client_id = %s
            ORDER BY updated_at DESC
            LIMIT 3
            """

            cases = self.pg_manager.execute_query(case_query, (customer_id,))
            activities.extend(cases)

            # 按时间排序
            activities.sort(key=lambda x: x["activity_time"], reverse=True)

            return activities[:5]  # 返回最近5个活动
        except Exception as e:
            logger.error(f"获取客户最近活动失败: {str(e)}")
            return []

    def _get_customer_statistics(self, customer_id: str) -> Dict[str, Any]:
        """获取客户统计信息"""
        try:
            if not self.pg_manager:
                return {}

            # 获取各项统计数据
            stats = {}

            # 案卷统计
            case_stats_query = """
            SELECT
                COUNT(*) as total_cases,
                COUNT(CASE WHEN current_stage IN ('filing', 'examination', 'review') THEN 1 END) as active_cases,
                COUNT(CASE WHEN patent_number IS NOT NULL THEN 1 END) as granted_cases
            FROM cases
            WHERE client_id = %s
            """

            case_result = self.pg_manager.execute_query(case_stats_query, (customer_id,))
            if case_result:
                stats.update(case_result[0])

            # 任务统计
            task_stats_query = """
            SELECT
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                COUNT(CASE WHEN due_date < CURRENT_DATE AND status != 'completed' THEN 1 END) as overdue_tasks
            FROM tasks
            WHERE client_id = %s
            """

            task_result = self.pg_manager.execute_query(task_stats_query, (customer_id,))
            if task_result:
                stats.update(task_result[0])

            # 文档统计
            doc_stats_query = """
            SELECT
                COUNT(*) as total_documents,
                COUNT(CASE WHEN upload_time >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_documents
            FROM documents
            WHERE client_id = %s
            """

            doc_result = self.pg_manager.execute_query(doc_stats_query, (customer_id,))
            if doc_result:
                stats.update(doc_result[0])

            return stats
        except Exception as e:
            logger.error(f"获取客户统计信息失败: {str(e)}")
            return {}

    def get_customer_overview(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取客户概览列表

        Args:
            limit: 返回记录数限制

        Returns:
            客户概览列表
        """
        try:
            if not self.pg_manager:
                return []

            query = """
            SELECT
                c.id as customer_id,
                c.name,
                c.type as business_type,
                c.contact_phone as phone,
                c.contact_email as email,
                c.created_at,
                c.updated_at,

                -- 案卷统计
                COALESCE(case_stats.total_cases, 0) as total_cases,
                COALESCE(case_stats.active_cases, 0) as active_cases,
                COALESCE(case_stats.granted_cases, 0) as granted_cases,

                -- 任务统计
                COALESCE(task_stats.total_tasks, 0) as total_tasks,
                COALESCE(task_stats.pending_tasks, 0) as pending_tasks,
                COALESCE(task_stats.completed_tasks, 0) as completed_tasks,

                -- 文档统计
                COALESCE(doc_stats.total_documents, 0) as total_documents

            FROM clients c
            LEFT JOIN (
                SELECT
                    client_id,
                    COUNT(*) as total_cases,
                    COUNT(CASE WHEN current_stage IN ('filing', 'examination', 'review') THEN 1 END) as active_cases,
                    COUNT(CASE WHEN patent_number IS NOT NULL THEN 1 END) as granted_cases
                FROM cases
                WHERE client_id IS NOT NULL
                GROUP BY client_id
            ) case_stats ON c.id = case_stats.client_id
            LEFT JOIN (
                SELECT
                    client_id,
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks
                FROM tasks
                WHERE client_id IS NOT NULL
                GROUP BY client_id
            ) task_stats ON c.id = task_stats.client_id
            LEFT JOIN (
                SELECT
                    client_id,
                    COUNT(*) as total_documents
                FROM documents
                WHERE client_id IS NOT NULL
                GROUP BY client_id
            ) doc_stats ON c.id = doc_stats.client_id
            ORDER BY c.updated_at DESC
            LIMIT %s
            """

            return self.pg_manager.execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"获取客户概览失败: {str(e)}")
            return []

    def add_customer_case(self, customer_id: str, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        为客户添加案卷

        Args:
            customer_id: 客户ID
            case_data: 案卷数据

        Returns:
            操作结果
        """
        try:
            if not self.pg_manager:
                return {"error": "PostgreSQL不可用"}

            # 插入案卷记录
            insert_query = """
            INSERT INTO cases (
                client_id, case_number, title, type, applicant,
                current_stage, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """

            case_id = self.pg_manager.execute_query(
                insert_query,
                (
                    customer_id,
                    case_data.get("case_number", ""),
                    case_data.get("title", ""),
                    case_data.get("type", ""),
                    case_data.get("applicant", ""),
                    case_data.get("current_stage", "created"),
                    datetime.now(),
                    datetime.now()
                )
            )[0]["id"]

            return {
                "success": True,
                "case_id": case_id,
                "message": "案卷添加成功"
            }
        except Exception as e:
            logger.error(f"添加客户案卷失败: {str(e)}")
            return {"error": str(e)}

    def add_customer_task(self, customer_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        为客户添加任务

        Args:
            customer_id: 客户ID
            task_data: 任务数据

        Returns:
            操作结果
        """
        try:
            if not self.pg_manager:
                return {"error": "PostgreSQL不可用"}

            # 插入任务记录
            insert_query = """
            INSERT INTO tasks (
                client_id, title, description, task_type, status,
                priority, assigned_to, start_date, due_date, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """

            task_id = self.pg_manager.execute_query(
                insert_query,
                (
                    customer_id,
                    task_data.get("title", ""),
                    task_data.get("description", ""),
                    task_data.get("task_type", ""),
                    task_data.get("status", "pending"),
                    task_data.get("priority", "normal"),
                    task_data.get("assigned_to", ""),
                    task_data.get("start_date"),
                    task_data.get("due_date"),
                    datetime.now(),
                    datetime.now()
                )
            )[0]["id"]

            return {
                "success": True,
                "task_id": task_id,
                "message": "任务添加成功"
            }
        except Exception as e:
            logger.error(f"添加客户任务失败: {str(e)}")
            return {"error": str(e)}

    def add_customer_document(self, customer_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        为客户添加文档

        Args:
            customer_id: 客户ID
            document_data: 文档数据

        Returns:
            操作结果
        """
        try:
            if not self.pg_manager:
                return {"error": "PostgreSQL不可用"}

            # 插入文档记录
            insert_query = """
            INSERT INTO documents (
                client_id, name, type, category, file_name,
                file_size, uploaded_by, upload_time, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """

            doc_id = self.pg_manager.execute_query(
                insert_query,
                (
                    customer_id,
                    document_data.get("name", ""),
                    document_data.get("type", ""),
                    document_data.get("category", ""),
                    document_data.get("file_name", ""),
                    document_data.get("file_size", 0),
                    document_data.get("uploaded_by", ""),
                    datetime.now(),
                    datetime.now()
                )
            )[0]["id"]

            return {
                "success": True,
                "document_id": doc_id,
                "message": "文档添加成功"
            }
        except Exception as e:
            logger.error(f"添加客户文档失败: {str(e)}")
            return {"error": str(e)}

    def search_customers_by_relationship(self,
                                       relationship_type: RelationshipType,
                                       search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据关联关系搜索客户

        Args:
            relationship_type: 关系类型
            search_criteria: 搜索条件

        Returns:
            匹配的客户列表
        """
        try:
            if not self.pg_manager:
                return []

            base_query = """
            SELECT DISTINCT c.id as customer_id, c.name, c.type as business_type,
                   c.contact_phone, c.contact_email, c.created_at
            FROM clients c
            """

            if relationship_type == RelationshipType.CUSTOMER_CASES:
                base_query += """
                JOIN cases ca ON c.id = ca.client_id
                WHERE 1=1
                """
                if "case_type" in search_criteria:
                    base_query += f" AND ca.type = '{search_criteria['case_type']}'"
                if "case_status" in search_criteria:
                    base_query += f" AND ca.current_stage = '{search_criteria['case_status']}'"

            elif relationship_type == RelationshipType.CUSTOMER_TASKS:
                base_query += """
                JOIN tasks t ON c.id = t.client_id
                WHERE 1=1
                """
                if "task_type" in search_criteria:
                    base_query += f" AND t.task_type = '{search_criteria['task_type']}'"
                if "task_status" in search_criteria:
                    base_query += f" AND t.status = '{search_criteria['task_status']}'"
                if "assigned_to" in search_criteria:
                    base_query += f" AND t.assigned_to = '{search_criteria['assigned_to']}'"

            elif relationship_type == RelationshipType.CUSTOMER_DOCUMENTS:
                base_query += """
                JOIN documents d ON c.id = d.client_id
                WHERE 1=1
                """
                if "document_type" in search_criteria:
                    base_query += f" AND d.type = '{search_criteria['document_type']}'"
                if "uploaded_by" in search_criteria:
                    base_query += f" AND d.uploaded_by = '{search_criteria['uploaded_by']}'"

            base_query += " ORDER BY c.updated_at DESC LIMIT 20"

            return self.pg_manager.execute_query(base_query)
        except Exception as e:
            logger.error(f"根据关联关系搜索客户失败: {str(e)}")
            return []

    def get_relationship_summary(self) -> Dict[str, Any]:
        """
        获取关系汇总统计

        Returns:
            关系统计信息
        """
        try:
            if not self.pg_manager:
                return {}

            summary = {}

            # 客户总数
            customer_count = self.pg_manager.execute_query("SELECT COUNT(*) as count FROM clients")
            summary["total_customers"] = customer_count[0]["count"] if customer_count else 0

            # 案卷统计
            case_stats = self.pg_manager.execute_query("""
                SELECT
                    COUNT(*) as total_cases,
                    COUNT(DISTINCT client_id) as customers_with_cases
                FROM cases
                WHERE client_id IS NOT NULL
            """)
            if case_stats:
                summary.update({
                    "total_cases": case_stats[0]["total_cases"],
                    "customers_with_cases": case_stats[0]["customers_with_cases"]
                })

            # 任务统计
            task_stats = self.pg_manager.execute_query("""
                SELECT
                    COUNT(*) as total_tasks,
                    COUNT(DISTINCT client_id) as customers_with_tasks
                FROM tasks
                WHERE client_id IS NOT NULL
            """)
            if task_stats:
                summary.update({
                    "total_tasks": task_stats[0]["total_tasks"],
                    "customers_with_tasks": task_stats[0]["customers_with_tasks"]
                })

            # 文档统计
            doc_stats = self.pg_manager.execute_query("""
                SELECT
                    COUNT(*) as total_documents,
                    COUNT(DISTINCT client_id) as customers_with_documents
                FROM documents
                WHERE client_id IS NOT NULL
            """)
            if doc_stats:
                summary.update({
                    "total_documents": doc_stats[0]["total_documents"],
                    "customers_with_documents": doc_stats[0]["customers_with_documents"]
                })

            return summary
        except Exception as e:
            logger.error(f"获取关系汇总统计失败: {str(e)}")
            return {}