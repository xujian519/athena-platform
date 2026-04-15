#!/usr/bin/env python3
"""
专利规则知识图谱与向量库数据规模验证脚本
"""

from __future__ import annotations
import json
from pathlib import Path

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

print('='*70)
print('专利规则知识图谱与向量库数据规模验证')
print('='*70)

# ========== 1. NebulaGraph知识图谱统计 ==========
print('\n【1】NebulaGraph知识图谱统计')
print('-'*70)

pool = ConnectionPool()
config = Config()
pool.init([('127.0.0.1', 9669)], config)
session = pool.get_session('root', 'nebula')
session.execute('USE patent_kg;')

# 获取所有TAG和EDGE类型
schema_result = session.execute('SHOW TAGS;')
tags = [schema_result.row_values(i)[0].as_string() for i in range(schema_result.row_size())]

edge_result = session.execute('SHOW EDGES;')
edges = [edge_result.row_values(i)[0].as_string() for i in range(edge_result.row_size())]

print(f'TAG类型 ({len(tags)}个): {tags}')
print(f'EDGE类型 ({len(edges)}个): {edges}')

# 统计顶点和边
total_vertices = 0
total_edges = 0

print('\n顶点统计:')
for tag in tags:
    query = f'MATCH (v:{tag}) RETURN count(v)'
    result = session.execute(query)
    if result.is_succeeded() and result.row_size() > 0:
        count = result.row_values(0)[0].as_int()
        total_vertices += count
        print(f'  {tag:25s}: {count:6d}')

print(f'  总顶点数: {total_vertices}')

print('\n边统计:')
for edge in edges:
    query = f'MATCH ()-[e:{edge}]->() RETURN count(e)'
    result = session.execute(query)
    if result.is_succeeded() and result.row_size() > 0:
        count = result.row_values(0)[0].as_int()
        total_edges += count
        print(f'  {edge:25s}: {count:6d}')

print(f'  总边数: {total_edges}')
print(f'  图元素总数: {total_vertices + total_edges}')

session.release()
pool.close()

# ========== 2. 向量库统计 ==========
print('\n【2】向量库统计')
print('-'*70)

vectors_dir = Path('/Users/xujian/Athena工作平台/apps/apps/patents/processed/vectors')

if vectors_dir.exists():
    # 读取metadata
    metadata_file = vectors_dir / 'metadata.json'
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)

        print(f'向量模型: {metadata.get("model", "unknown")}')
        print(f'向量维度: {metadata.get("vector_dim", "unknown")}')
        print(f'编码长度: {metadata.get("encoding_length", "unknown")}')
        print(f'处理专利数: {len(metadata.get("patent_numbers", []))}')
        print(f'生成时间: {metadata.get("timestamp", "unknown")}')

        # 专利列表
        patents = metadata.get('patent_numbers', [])
        print('\n已向量化的专利:')
        for p in patents:
            print(f'  - {p}')
    else:
        print('⚠️  metadata.json 不存在')

    # 读取统计信息
    stats_file = vectors_dir / 'statistics.json'
    if stats_file.exists():
        with open(stats_file) as f:
            stats = json.load(f)
        print(f'\n平均文本长度: {stats.get("avg_text_length", 0):.0f} 字符')
        print(f'最大文本长度: {stats.get("max_text_length", 0)} 字符')
        print(f'最小文本长度: {stats.get("min_text_length", 0)} 字符')

    # 文件大小
    npy_file = vectors_dir / 'patent_vectors.npy'
    json_file = vectors_dir / 'patent_vectors.json'

    if npy_file.exists():
        size_mb = npy_file.stat().st_size / (1024 * 1024)
        print('\n向量文件大小:')
        print(f'  NumPy格式: {size_mb:.2f} MB')

    if json_file.exists():
        size_kb = json_file.stat().st_size / 1024
        print(f'  JSON格式: {size_kb:.2f} KB')
else:
    print('⚠️  向量目录不存在')

# ========== 3. 三元组数据统计 ==========
print('\n【3】三元组提取数据统计')
print('-'*70)

triples_dir = Path('/Users/xujian/Athena工作平台/apps/apps/patents/processed/triples')
summary_file = triples_dir / 'extraction_summary.json'

if summary_file.exists():
    with open(summary_file) as f:
        summary = json.load(f)

    print(f'提取时间: {summary.get("timestamp", "unknown")[:19]}')
    print(f'处理专利数: {summary.get("total_patents", 0)}')
    print(f'成功提取: {summary.get("successful", 0)}')
    print(f'提取失败: {summary.get("failed", 0)}')

    print('\n提取元素统计:')
    print(f'  技术问题: {summary.get("total_problems", 0)}')
    print(f'  技术特征: {summary.get("total_features", 0)}')
    print(f'  技术效果: {summary.get("total_effects", 0)}')
    print(f'  三元组: {summary.get("total_triples", 0)}')
    print(f'  特征关系: {summary.get("total_feature_relations", 0)}')

    # 各专利详情
    results = summary.get('reports/reports/results', [])
    print('\n各专利三元组提取详情:')
    for r in results:
        pn = r.get('patent_number', 'unknown')
        probs = len(r.get('problems', []))
        feats = len(r.get('features', []))
        effs = len(r.get('effects', []))
        triples = len(r.get('triples', []))
        relations = len(r.get('feature_relations', []))
        conf = r.get('extraction_confidence', 0)
        print(f'  {pn:20s}: Q{probs} F{feats} E{effs} T{triples} R{relations} (置信度: {conf:.2f})')
else:
    print('⚠️  三元组摘要文件不存在')

# ========== 4. 处理的专利文件统计 ==========
print('\n【4】已处理专利文件统计')
print('-'*70)

processed_dir = Path('/Users/xujian/Athena工作平台/apps/apps/patents/processed')
patent_files = list(processed_dir.glob('[A-Z]*.json'))
patent_files = [f for f in patent_files if 'processing_report' not in f.name]

print(f'已处理专利数量: {len(patent_files)}')
print('\n专利文件列表:')

total_text_length = 0
for pf in sorted(patent_files):
    with open(pf) as f:
        data = json.load(f)
    pn = data.get('patent_number', 'unknown')
    length = data.get('text_length', 0)
    method = data.get('extraction_method', 'unknown')
    pages = data.get('pages_processed', 0)
    total_text_length += length
    print(f'  {pn:20s}: {length:7,} 字符 | {method:18s} | {pages:2d} 页')

print(f'\n总文本长度: {total_text_length:,} 字符')
print(f'平均文本长度: {total_text_length // len(patent_files):,} 字符')

print('\n' + '='*70)
print('验证完成')
print('='*70)
