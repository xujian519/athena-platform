#!/usr/bin/env python3
"""
专利知识图谱构建脚本
为已处理的7个专利构建知识图谱
"""

from __future__ import annotations
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 设置路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
PATENT_PROCESSED_DIR = PROJECT_ROOT / "apps/apps/patents" / "processed"
KG_OUTPUT_DIR = PATENT_PROCESSED_DIR / "knowledge_graph"

sys.path.insert(0, str(PROJECT_ROOT / "production/dev/scripts/patent_full_text"))
sys.path.insert(0, str(PROJECT_ROOT / "production/dev/scripts/patent_full_text/phase3"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_processed_patents():
    """加载已处理的专利数据"""
    patent_files = list(PATENT_PROCESSED_DIR.glob("[A-Z]*.json"))
    patents = []

    for patent_file in patent_files:
        if "processing_report" in patent_file.name:
            continue

        try:
            with open(patent_file, encoding='utf-8') as f:
                patent_data = json.load(f)

                # 只处理有文本内容的专利
                if patent_data.get('text_length', 0) > 100:
                    patents.append(patent_data)
                    logger.info(f"加载: {patent_data['patent_number']} ({patent_data['text_length']} 字符)")
        except Exception as e:
            logger.error(f"加载失败 {patent_file.name}: {e}")

    return patents


def build_patent_vertex(patent_data: dict) -> str:
    """
    构建专利顶点的NGQL语句

    Returns:
        NGQL语句
    """
    patent_number = patent_data['patent_number']

    # 转义特殊字符
    def escape_string(s):
        if not s:
            return '""'
        # 转义反斜杠和双引号
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        return '"' + escaped + '"'

    # 属性值 - 字符串需要引号，数字不需要
    prop_values = [
        escape_string(patent_number),  # patent_number - string
        escape_string(patent_data.get("title", "")[:200]),  # title - string，限制长度
        escape_string(patent_data.get("abstract", "")[:500]),  # abstract - string，限制长度
        str(patent_data.get("text_length", 0)),  # text_length - int
        escape_string(patent_data.get("extraction_method", "")),  # extraction_method - string
        str(patent_data.get("pages_processed", 0))  # pages_processed - int
    ]

    # 生成NGQL - INSERT VERTEX格式
    ngql = f'INSERT VERTEX patent(patent_number, title, abstract, text_length, extraction_method, pages_processed) VALUES "{patent_number}": ({", ".join(prop_values)});'

    return ngql


def save_ngql_script(patent_number: str, ngql_statements: list):
    """保存NGQL脚本到文件"""
    KG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = KG_OUTPUT_DIR / f"{patent_number}_kg.ngql"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"-- Patent KG Building Script for {patent_number}\n")
        f.write(f"-- Generated at: {datetime.now().isoformat()}\n")
        f.write("\n")
        f.write("USE patent_kg;\n")
        f.write("\n")
        f.write("-- 1. Create Patent Vertex\n")
        f.write("\n".join(ngql_statements))
        f.write("\n")

    return output_file


def build_kg_for_patent(patent_data: dict) -> dict:
    """
    为单个专利构建知识图谱

    Returns:
        构建结果字典
    """
    patent_number = patent_data['patent_number']
    logger.info(f"\n{'='*60}")
    logger.info(f"构建知识图谱: {patent_number}")
    logger.info(f"{'='*60}")

    result = {
        'patent_number': patent_number,
        'success': False,
        'ngql_file': None,
        'timestamp': datetime.now().isoformat(),
        'vertices': 0,
        'edges': 0,
        'error': None
    }

    try:
        # 1. 构建专利顶点
        logger.info("  1️⃣  构建专利顶点...")
        vertex_ngql = build_patent_vertex(patent_data)
        logger.info(f"     ✅ 专利顶点: {patent_number}")

        # 2. 收集所有NGQL语句
        ngql_statements = [
            vertex_ngql
        ]

        # 3. 保存NGQL脚本
        ngql_file = save_ngql_script(patent_number, ngql_statements)
        result['ngql_file'] = str(ngql_file)
        result['vertices'] = 1
        result['success'] = True

        logger.info("  2️⃣  保存NGQL脚本...")
        logger.info(f"     💾 {ngql_file.name}")

        # 4. 可选：执行NGQL（如果nebula3-python已安装）
        try:
            from nebula3.gclient.net import ConnectionPool

            logger.info("  3️⃣  执行NGQL...")

            # 连接到NebulaGraph
            pool = ConnectionPool()
            pool.init([('127.0.0.1', 9669)], 'patent_full_text_v2', 'root', 'nebula')

            # 执行NGQL
            session = pool.get_session()
            execute_result = session.execute(vertex_ngql)

            if execute_result.is_succeeded():
                logger.info("     ✅ 执行成功")
            else:
                logger.warning(f"     ⚠️  执行失败: {execute_result.error_msg()}")

            session.release()
            pool.close()

        except ImportError:
            logger.info("  ⚠️  nebula3-python未安装，仅生成NGQL脚本")
        except Exception as e:
            logger.warning(f"  ⚠️  执行NGQL失败: {e}")
            logger.info(f"     💡 请手动执行: {ngql_file}")

        logger.info(f"\n  ✅ {patent_number} 知识图谱构建完成")

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"  ❌ 构建失败: {e}")

    return result


def main():
    """主流程"""
    logger.info("="*70)
    logger.info("专利知识图谱构建")
    logger.info("="*70)

    # 加载已处理的专利
    patents = load_processed_patents()

    if not patents:
        logger.warning("没有找到已处理的专利数据")
        return

    logger.info(f"\n共 {len(patents)} 个专利待构建知识图谱")

    # 构建每个专利的知识图谱
    results = []
    for patent in patents:
        result = build_kg_for_patent(patent)
        results.append(result)

    # 保存总结报告
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_patents': len(patents),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'total_vertices': sum(r['vertices'] for r in results),
        'reports/reports/results': results
    }

    summary_file = KG_OUTPUT_DIR / "kg_build_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 打印总结
    logger.info(f"\n{'='*70}")
    logger.info("知识图谱构建完成")
    logger.info(f"{'='*70}")
    logger.info(f"成功: {summary['successful']}/{summary['total_patents']}")
    logger.info(f"总顶点数: {summary['total_vertices']}")
    logger.info(f"NGQL脚本目录: {KG_OUTPUT_DIR}")
    logger.info(f"总结报告: {summary_file}")
    logger.info("")

    if summary['failed'] > 0:
        logger.info("❌ 失败的专利:")
        for result in results:
            if not result['success']:
                logger.info(f"   - {result['patent_number']}: {result.get('error', '未知错误')}")

    logger.info("")

    # 执行说明
    logger.info("💡 如果nebula3-python未安装，请手动执行NGQL脚本:")
    logger.info("   1. 启动NebulaGraph控制台: nebula-console -addr 127.0.0.1 -port 9669")
    logger.info("   2. 执行脚本: source /path/to/patent_kg.ngql")
    logger.info("")


if __name__ == "__main__":
    main()
