#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL数据库配置
PostgreSQL Database Configuration for Hybrid Architecture
"""

# PostgreSQL连接配置
POSTGRESQL_CONFIG = {
    # 主数据库连接
    "main": {
        "host": "localhost",
        "port": 5432,
        "database": "yunpat",
        "user": "postgres",
        "password": "",
        "schema": "public"
    },

    # 其他可用数据库
    "available_databases": [
        "yunpat",          # 主要业务数据库
        "athena_db",       # Athena知识数据库
        "patent_db",       # 专利数据库
        "patent_insight",  # 专利洞察数据库
        "xiaonuo_learning" # 小诺学习数据库
    ]
}

# 客户管理相关表配置
TABLE_CONFIG = {
    "customers": {
        "table_name": "clients",
        "primary_key": "id",
        "fields": {
            "id": "UUID",
            "name": "VARCHAR(255)",
            "type": "VARCHAR(50)",
            "address": "TEXT",
            "contact_person": "VARCHAR(255)",
            "contact_title": "VARCHAR(100)",
            "contact_phone": "VARCHAR(50)",
            "contact_email": "VARCHAR(255)",
            "source": "VARCHAR(100)",
            "salesperson": "VARCHAR(100)",
            "credit_rating": "VARCHAR(20)",
            "notes": "TEXT",
            "tenant_id": "VARCHAR(100)",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP"
        }
    },

    "projects": {
        "table_name": "projects",
        "primary_key": "id",
        "fields": {
            "id": "UUID",
            "name": "VARCHAR(255)",
            "client_id": "UUID",
            "status": "VARCHAR(50)",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP"
        }
    },

    "cases": {
        "table_name": "cases",
        "primary_key": "id",
        "fields": {
            "id": "UUID",
            "client_id": "UUID",
            "title": "VARCHAR(255)",
            "status": "VARCHAR(50)",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP"
        }
    }
}

# SQL查询模板
SQL_TEMPLATES = {
    "customers": {
        "select_all": "SELECT * FROM {table} ORDER BY created_at DESC",
        "select_by_id": "SELECT * FROM {table} WHERE id = %s",
        "select_by_name": "SELECT * FROM {table} WHERE name LIKE %s ORDER BY created_at DESC",
        "insert": """
            INSERT INTO {table} (id, name, type, contact_person, contact_phone,
                                contact_email, source, tenant_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """,
        "update": """
            UPDATE {table} SET name = %s, contact_person = %s, contact_phone = %s,
                               contact_email = %s, updated_at = NOW()
            WHERE id = %s
        """,
        "delete": "DELETE FROM {table} WHERE id = %s",
        "count": "SELECT COUNT(*) FROM {table}"
    },

    "projects": {
        "select_by_client": "SELECT * FROM {table} WHERE client_id = %s ORDER BY created_at DESC",
        "insert": """
            INSERT INTO {table} (id, name, client_id, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """
    }
}