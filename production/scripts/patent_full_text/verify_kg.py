#!/usr/bin/env python3
"""
知识图谱验证脚本
"""

from __future__ import annotations
from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

pool = ConnectionPool()
config = Config()
pool.init([('127.0.0.1', 9669)], config)
session = pool.get_session('root', 'nebula')
session.execute('USE patent_kg;')

print('='*70)
print('NebulaGraph知识图谱验证')
print('='*70)

# 统计
print('\n📊 知识图谱统计:')
print('-'*70)

queries = [
    ('专利顶点', 'MATCH (v:patent) RETURN count(v)'),
    ('技术问题顶点', 'MATCH (v:technical_problem) RETURN count(v)'),
    ('技术特征顶点', 'MATCH (v:technical_feature) RETURN count(v)'),
    ('技术效果顶点', 'MATCH (v:technical_effect) RETURN count(v)'),
    ('SOLVES边', 'MATCH ()-[e:SOLVES]->() RETURN count(e)'),
    ('ACHIEVES边', 'MATCH ()-[e:ACHIEVES]->() RETURN count(e)'),
    ('RELATES_TO边', 'MATCH ()-[e:RELATES_TO]->() RETURN count(e)'),
]

total_v = 0
total_e = 0
for desc, q in queries:
    r = session.execute(q)
    if r.is_succeeded() and r.row_size() > 0:
        c = r.row_values(0)[0].as_int()
        print(f'  {desc:20s}: {c:6d}')
        if '顶点' in desc: total_v += c
        elif '边' in desc: total_e += c

print('-'*70)
print(f'  总顶点数: {total_v}')
print(f'  总边数: {total_e}')
print(f'  总元素数: {total_v + total_e}')

# 示例查询
print('\n🔍 示例查询 - 技术特征:')
print('-'*70)
r = session.execute('MATCH (v:technical_feature) RETURN v LIMIT 3')
if r.is_succeeded():
    for row in r.row_values():
        node = row[0].as_node()
        props = node.properties
        vid = props.get('id', 'N/A')
        desc = props.get('description', 'N/A')
        print(f'  [{vid}] {desc[:60]}...')

print('\n🔗 示例查询 - 特征解决问题:')
print('-'*70)
r = session.execute('MATCH (f:technical_feature)-[e:SOLVES]->(p:technical_problem) RETURN f.id, p.id LIMIT 5')
if r.is_succeeded():
    for row in r.row_values():
        fid = row[0].as_string()
        pid = row[1].as_string()
        print(f'  {fid} --[SOLVES]--> {pid}')

session.release()
pool.close()
print('\n✅ 验证完成')
