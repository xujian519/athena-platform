#!/usr/bin/env python3
"""
简化版知识图谱导入
Simple Knowledge Graph Import

演示知识图谱数据的导入流程

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_kg_data() -> Any | None:
    """加载知识图谱数据"""
    # 尝试从备份目录加载
    kg_path = Path("/Users/xujian/Athena工作平台/production/backups/backup_20251220_211522/kg_data")

    entities_file = kg_path / "legal_entities_20251220_210502.json"
    relations_file = kg_path / "legal_relations_20251220_210502.json"

    entities = []
    relations = []

    if entities_file.exists():
        with open(entities_file, encoding='utf-8') as f:
            entities = json.load(f)
        print(f"✅ 加载了 {len(entities)} 个实体")

    if relations_file.exists():
        with open(relations_file, encoding='utf-8') as f:
            relations = json.load(f)
        print(f"✅ 加载了 {len(relations)} 条关系")

    return entities, relations

def analyze_kg_data(entities, relations) -> None:
    """分析知识图谱数据"""
    print("\n📊 知识图谱数据分析:")

    # 实体类型统计
    entity_types = {}
    for entity in entities:
        entity_type = entity.get('type', 'Unknown')
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    print("\n实体类型分布:")
    for etype, count in entity_types.items():
        print(f"  - {etype}: {count} 个")

    # 关系类型统计
    relation_types = {}
    for relation in relations:
        rel_type = relation.get('type', 'Unknown')
        relation_types[rel_type] = relation_types.get(rel_type, 0) + 1

    print("\n关系类型分布:")
    for rtype, count in relation_types.items():
        print(f"  - {rtype}: {count} 条")

    # 示例数据
    print("\n📋 示例数据:")
    print("\n实体示例:")
    for i, entity in enumerate(entities[:3]):
        print(f"  {i+1}. ID: {entity['id'][:16]}...")
        print(f"     类型: {entity['type']}")
        if 'properties' in entity and 'title' in entity['properties']:
            print(f"     标题: {entity['properties']['title'][:50]}...")

    print("\n关系示例:")
    for i, relation in enumerate(relations[:3]):
        source = relation.get('source', relation.get('start', 'N/A'))
        target = relation.get('target', relation.get('end', 'N/A'))
        print(f"  {i+1}. {source[:16]}... -> {target[:16]}...")
        print(f"     类型: {relation['type']}")

def save_kg_summary(entities, relations) -> None:
    """保存知识图谱摘要"""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_entities": len(entities),
            "total_relations": len(relations)
        },
        "entity_types": {},
        "relation_types": {},
        "status": "ready_for_import"
    }

    # 统计类型
    for entity in entities:
        etype = entity.get('type', 'Unknown')
        summary["entity_types"][etype] = summary["entity_types"].get(etype, 0) + 1

    for relation in relations:
        rtype = relation.get('type', 'Unknown')
        summary["relation_types"][rtype] = summary["relation_types"].get(rtype, 0) + 1

    # 保存摘要
    output_path = Path("/Users/xujian/Athena工作平台/production/data/metadata/kg_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n📄 知识图谱摘要已保存: {output_path}")

def main() -> None:
    """主函数"""
    print("="*100)
    print("📚 知识图谱数据分析 📚")
    print("="*100)

    # 加载数据
    entities, relations = load_kg_data()

    if not entities and not relations:
        print("❌ 没有找到知识图谱数据")
        return

    # 分析数据
    analyze_kg_data(entities, relations)

    # 保存摘要
    save_kg_summary(entities, relations)

    # 说明
    print("\n" + "="*100)
    print("📝 说明:")
    print("✅ 知识图谱数据已准备就绪")
    print("⚠️ NebulaGraph连接需要配置（端口9669）")
    print("💾 数据可在NebulaGraph可用后导入")
    print("="*100)

if __name__ == "__main__":
    main()
