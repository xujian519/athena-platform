#!/bin/bash
# NebulaGraph导入脚本 - relations

echo "导入relations到NebulaGraph..."

# 使用nebula-console导入
nebula-console -addr localhost -port 9669 -u root -p nebula -f /Users/xujian/Athena工作平台/production/data/knowledge_graph/relations_ngql_20251220_214101.ngql

echo "导入完成"
