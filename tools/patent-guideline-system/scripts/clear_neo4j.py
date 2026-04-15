#!/usr/bin/env python3
"""
清空Neo4j数据库
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase

# 连接Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    # 删除所有节点和关系
    session.run("MATCH (n) DETACH DELETE n")
    print("已清空Neo4j数据库")

driver.close()
