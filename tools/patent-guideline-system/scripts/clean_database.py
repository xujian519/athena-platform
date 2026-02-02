#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分批清理Neo4j数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
import time

# 连接Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

print("开始清理数据库...")

with driver.session() as session:
    # 获取所有节点类型
    result = session.run("CALL db.labels()")
    labels = [record["label"] for record in result]
    print(f"发现标签: {labels}")

    # 分批删除
    for label in labels:
        print(f"\n删除标签 {label} 的节点...")
        batch_size = 1000
        deleted = 0
        while True:
            result = session.run(f"MATCH (n:{label}) WITH n LIMIT {batch_size} DETACH DELETE n RETURN count(n) as deleted")
            count = result.single()
            if count and count["deleted"] > 0:
                deleted += count["deleted"]
                print(f"  批次删除: {count['deleted']} 个节点")
                time.sleep(0.1)  # 短暂暂停
            else:
                break
        print(f"  标签 {label} 总共删除: {deleted} 个节点")

    print("\n✅ 数据库清理完成")

driver.close()