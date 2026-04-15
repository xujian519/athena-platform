#!/usr/bin/env python3
"""
知识图谱三元组更新脚本
Knowledge Graph Triple Update Script

将提取的三元组数据导入NebulaGraph知识图谱
"""

from __future__ import annotations
import json
import logging
from pathlib import Path

from nebula3.Config import Config

# nebula3
from nebula3.gclient.net import ConnectionPool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NebulaGraph配置
NEBULA_HOSTS = [('127.0.0.1', 9669)]
NEBULA_SPACE = 'patent_kg'
NEBULA_USER = 'root'
NEBULA_PASSWORD = 'nebula'

# 数据目录
TRIPLES_DIR = Path("/Users/xujian/Athena工作平台/apps/apps/patents/processed/triples")


def escape_string(s: str) -> str:
    """转义NGQL字符串"""
    if not s:
        return '""'
    # 先处理换行符和制表符
    text = str(s).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # 替换反斜杠和双引号
    escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    # 截断过长字符串
    if len(escaped) > 500:
        escaped = escaped[:500]
    return f'"{escaped}"'


def init_graph_schema(session):
    """初始化图谱Schema"""
    logger.info("初始化知识图谱Schema...")

    statements = [
        # 创建技术问题TAG
        "CREATE TAG IF NOT EXISTS technical_problem("
        "id string, "
        "description string, "
        "problem_type string, "
        "source_section string, "
        "severity double"
        ")",

        # 创建技术特征TAG
        "CREATE TAG IF NOT EXISTS technical_feature("
        "id string, "
        "description string, "
        "feature_category string, "
        "feature_type string, "
        "importance double"
        ")",

        # 创建技术效果TAG
        "CREATE TAG IF NOT EXISTS technical_effect("
        "id string, "
        "description string, "
        "effect_type string, "
        "quantifiable bool, "
        "metrics string"
        ")",

        # 创建SOLVES边 (特征 -> 问题)
        "CREATE EDGE IF NOT EXISTS SOLVES("
        "confidence double"
        ")",

        # 创建ACHIEVES边 (特征 -> 效果)
        "CREATE EDGE IF NOT EXISTS ACHIEVES("
        "confidence double"
        ")",

        # 创建RELATES_TO边 (特征 -> 特征)
        "CREATE EDGE IF NOT EXISTS RELATES_TO("
        "relation_type string, "
        "strength double, "
        "description string"
        ")",
    ]

    for stmt in statements:
        try:
            result = session.execute(stmt)
            if not result.is_succeeded():
                logger.warning(f"Schema创建警告: {result.error_msg()}")
        except Exception as e:
            logger.error(f"Schema创建失败: {e}\n  语句: {stmt}")


def build_problem_vertex_ngql(problem: dict, patent_number: str) -> str:
    """构建技术问题顶点NGQL"""
    pid = problem['id']
    props = [
        escape_string(pid),
        escape_string(problem['description']),
        escape_string(problem.get('problem_type', 'technical')),
        escape_string(problem.get('source_section', 'unknown')),
        str(problem.get('severity', 0.5))
    ]
    return f'INSERT VERTEX technical_problem(id, description, problem_type, source_section, severity) VALUES "{pid}": ({", ".join(props)});'


def build_feature_vertex_ngql(feature: dict, patent_number: str) -> str:
    """构建技术特征顶点NGQL"""
    fid = feature['id']
    props = [
        escape_string(fid),
        escape_string(feature['description']),
        escape_string(feature.get('feature_category', 'structural')),
        escape_string(feature.get('feature_type', 'component')),
        str(feature.get('importance', 0.5))
    ]
    return f'INSERT VERTEX technical_feature(id, description, feature_category, feature_type, importance) VALUES "{fid}": ({", ".join(props)});'


def build_effect_vertex_ngql(effect: dict, patent_number: str) -> str:
    """构建技术效果顶点NGQL"""
    eid = effect['id']
    props = [
        escape_string(eid),
        escape_string(effect['description']),
        escape_string(effect.get('effect_type', 'direct')),
        str(effect.get('quantifiable', False)).lower(),
        escape_string(effect.get('metrics', ''))
    ]
    return f'INSERT VERTEX technical_effect(id, description, effect_type, quantifiable, metrics) VALUES "{eid}": ({", ".join(props)});'


def build_solves_edge_ngql(triple: dict) -> str:
    """构建SOLVES边NGQL (特征 -> 问题)"""
    if triple['relation'] != 'SOLVES':
        return None
    subject = triple['subject']  # feature_id
    obj = triple['object']  # problem_id
    confidence = str(triple.get('confidence', 0.6))
    return f'INSERT EDGE SOLVES(confidence) VALUES "{subject}"->"{obj}": ({confidence});'


def build_achieves_edge_ngql(triple: dict) -> str:
    """构建ACHIEVES边NGQL (特征 -> 效果)"""
    if triple['relation'] != 'ACHIEVES':
        return None
    subject = triple['subject']  # feature_id
    obj = triple['object']  # effect_id
    confidence = str(triple.get('confidence', 0.6))
    return f'INSERT EDGE ACHIEVES(confidence) VALUES "{subject}"->"{obj}": ({confidence});'


def build_relates_to_edge_ngql(relation: dict) -> str:
    """构建RELATES_TO边NGQL (特征 -> 特征)"""
    from_feature = relation['from_feature']
    to_feature = relation['to_feature']
    props = [
        escape_string(relation.get('relation_type', 'combinational')),
        str(relation.get('strength', 0.5)),
        escape_string(relation.get('description', ''))
    ]
    return f'INSERT EDGE RELATES_TO(relation_type, strength, description) VALUES "{from_feature}"->"{to_feature}": ({", ".join(props)});'


def process_patent_triples(session, patent_number: str, triple_data: dict):
    """处理单个专利的三元组数据"""
    logger.info(f"\n{'='*60}")
    logger.info(f"处理专利: {patent_number}")
    logger.info(f"{'='*60}")

    triple_result = triple_data.get('triple_extraction', {})

    # 统计
    problems_inserted = 0
    features_inserted = 0
    effects_inserted = 0
    edges_inserted = 0

    # 1. 插入技术问题顶点
    problems = triple_result.get('problems', [])
    if problems:
        logger.info(f"  插入 {len(problems)} 个技术问题...")
        for problem in problems:
            ngql = build_problem_vertex_ngql(problem, patent_number)
            result = session.execute(ngql)
            if result.is_succeeded():
                problems_inserted += 1
            else:
                # 安全的错误消息处理
                try:
                    error_msg = result.error_msg()
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
                    error_msg = "Unknown error"
                logger.debug(f"    问题插入失败: {error_msg}")
        logger.info(f"    ✅ 技术问题: {problems_inserted}/{len(problems)}")

    # 2. 插入技术特征顶点
    features = triple_result.get('features', [])
    if features:
        logger.info(f"  插入 {len(features)} 个技术特征...")
        for feature in features:
            ngql = build_feature_vertex_ngql(feature, patent_number)
            result = session.execute(ngql)
            if result.is_succeeded():
                features_inserted += 1
            else:
                try:
                    error_msg = result.error_msg() if hasattr(result, 'error_msg') else "Unknown error"
                except Exception:
                    error_msg = "Unknown error"
                logger.debug(f"    特征插入失败: {error_msg}")
        logger.info(f"    ✅ 技术特征: {features_inserted}/{len(features)}")

    # 3. 插入技术效果顶点
    effects = triple_result.get('effects', [])
    if effects:
        logger.info(f"  插入 {len(effects)} 个技术效果...")
        for effect in effects:
            ngql = build_effect_vertex_ngql(effect, patent_number)
            result = session.execute(ngql)
            if result.is_succeeded():
                effects_inserted += 1
            else:
                try:
                    error_msg = result.error_msg() if hasattr(result, 'error_msg') else "Unknown error"
                except Exception:
                    error_msg = "Unknown error"
                logger.debug(f"    效果插入失败: {error_msg}")
        logger.info(f"    ✅ 技术效果: {effects_inserted}/{len(effects)}")

    # 4. 插入三元组边
    triples = triple_result.get('triples', [])
    if triples:
        logger.info(f"  插入 {len(triples)} 个三元组边...")
        for triple in triples:
            if triple['relation'] == 'SOLVES':
                ngql = build_solves_edge_ngql(triple)
            elif triple['relation'] == 'ACHIEVES':
                ngql = build_achieves_edge_ngql(triple)
            else:
                continue

            if ngql:
                result = session.execute(ngql)
                if result.is_succeeded():
                    edges_inserted += 1
        logger.info(f"    ✅ 三元组边: {edges_inserted}/{len(triples)}")

    # 5. 插入特征关系边
    feature_relations = triple_result.get('feature_relations', [])
    if feature_relations:
        logger.info(f"  插入 {len(feature_relations)} 个特征关系边...")
        relation_edges = 0
        for relation in feature_relations:
            ngql = build_relates_to_edge_ngql(relation)
            result = session.execute(ngql)
            if result.is_succeeded():
                relation_edges += 1
                edges_inserted += 1
        logger.info(f"    ✅ 特征关系边: {relation_edges}/{len(feature_relations)}")

    logger.info(f"\n  📊 {patent_number} 汇总:")
    logger.info(f"     问题: {problems_inserted}")
    logger.info(f"     特征: {features_inserted}")
    logger.info(f"     效果: {effects_inserted}")
    logger.info(f"     边: {edges_inserted}")

    return {
        'patent_number': patent_number,
        'problems': problems_inserted,
        'features': features_inserted,
        'effects': effects_inserted,
        'edges': edges_inserted
    }


def main():
    """主流程"""
    logger.info("="*70)
    logger.info("知识图谱三元组更新")
    logger.info("="*70)

    # 连接NebulaGraph
    logger.info(f"\n连接NebulaGraph: {NEBULA_HOSTS[0][0]}:{NEBULA_HOSTS[0][1]}")
    pool = ConnectionPool()
    config = Config()
    pool.init(NEBULA_HOSTS, config)

    session = pool.get_session(NEBULA_USER, NEBULA_PASSWORD)

    # 使用space
    use_result = session.execute(f'USE {NEBULA_SPACE};')
    if not use_result.is_succeeded():
        logger.error(f"USE space失败: {use_result.error_msg()}")
        return
    logger.info(f"✅ 使用space: {NEBULA_SPACE}")

    # 初始化Schema
    init_graph_schema(session)
    logger.info("")

    # 读取三元组数据
    summary_file = TRIPLES_DIR / "extraction_summary.json"
    with open(summary_file, encoding='utf-8') as f:
        summary = json.load(f)

    results_list = summary.get('reports/reports/results', [])

    # 处理每个专利
    all_stats = []
    for result in results_list:
        patent_number = result['patent_number']

        # 读取该专利的三元组文件
        triple_file = TRIPLES_DIR / f"{patent_number}_triples.json"
        if not triple_file.exists():
            logger.warning(f"  ⚠️  三元组文件不存在: {triple_file.name}")
            continue

        with open(triple_file, encoding='utf-8') as f:
            triple_data = json.load(f)

        # 处理
        stats = process_patent_triples(session, patent_number, triple_data)
        all_stats.append(stats)

    # 打印总结
    logger.info(f"\n{'='*70}")
    logger.info("知识图谱更新完成")
    logger.info(f"{'='*70}")

    total_problems = sum(s['problems'] for s in all_stats)
    total_features = sum(s['features'] for s in all_stats)
    total_effects = sum(s['effects'] for s in all_stats)
    total_edges = sum(s['edges'] for s in all_stats)

    logger.info(f"总问题顶点: {total_problems}")
    logger.info(f"总特征顶点: {total_features}")
    logger.info(f"总效果顶点: {total_effects}")
    logger.info(f"总关系边: {total_edges}")
    logger.info("")

    # 验证数据
    logger.info("验证知识图谱数据...")
    check_queries = [
        ("技术问题数量", "MATCH (v:technical_problem) RETURN count(v)"),
        ("技术特征数量", "MATCH (v:technical_feature) RETURN count(v)"),
        ("技术效果数量", "MATCH (v:technical_effect) RETURN count(v)"),
        ("SOLVES边数量", "MATCH ()-[e:SOLVES]->() RETURN count(e)"),
        ("ACHIEVES边数量", "MATCH ()-[e:ACHIEVES]->() RETURN count(e)"),
        ("RELATES_TO边数量", "MATCH ()-[e:RELATES_TO]->() RETURN count(e)"),
    ]

    for desc, query in check_queries:
        result = session.execute(query)
        if result.is_succeeded():
            count = result.row_values(0)[0].as_int()
            logger.info(f"  {desc}: {count}")
        else:
            logger.warning(f"  {desc}: 查询失败")

    # 关闭连接
    session.release()
    pool.close()
    logger.info("\n✅ NebulaGraph连接已关闭")


if __name__ == "__main__":
    main()
