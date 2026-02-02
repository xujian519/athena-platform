#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置新的审查指南数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase

# 连接Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    # 创建新的数据库
    try:
        session.run("CREATE DATABASE patent_guidelines")
        print("✅ 创建新数据库: patent_guidelines")
    except Exception as e:
        if "already exists" in str(e):
            print("ℹ️  数据库已存在")
        else:
            print(f"⚠️  创建数据库失败: {e}")

    # 切换到新数据库
    session.use_database("patent_guidelines")

    # 设置约束
    constraints = [
        "CREATE CONSTRAINT ON (d:Document) ASSERT d.id IS UNIQUE",
        "CREATE CONSTRAINT ON (p:Part) ASSERT p.id IS UNIQUE",
        "CREATE CONSTRAINT ON (c:Chapter) ASSERT c.id IS UNIQUE",
        "CREATE CONSTRAINT ON (s:Section) ASSERT s.id IS UNIQUE",
        "CREATE CONSTRAINT ON (co:Concept) ASSERT co.name IS UNIQUE",
        "CREATE CONSTRAINT ON (la:LawArticle) ASSERT la.id IS UNIQUE",
        "CREATE CONSTRAINT ON (ca:Case) ASSERT ca.id IS UNIQUE"
    ]

    print("\n📋 创建约束...")
    for constraint in constraints:
        try:
            session.run(constraint)
            print(f"  ✅ {constraint[:40]}...")
        except Exception as e:
            print(f"  ⚠️  {e}")

driver.close()