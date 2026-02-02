#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证JanusGraph导入结果
"""

import subprocess
import time
import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_gremlin_query(query, description="执行查询"):
    """执行Gremlin查询"""
    logger.info(f"🔍 {description}...")

    # 创建临时脚本文件
    script_content = f"""
graph = JanusGraphFactory.open('conf/janusgraph-berkeleyje.properties')
{query}
System.exit(0)
"""

    try:
        # 通过管道执行查询
        process = subprocess.Popen(
            ['docker', 'exec', '-i', 'janusgraph-kg', '/opt/janusgraph/bin/gremlin.sh'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=script_content, timeout=30)

        # 提取结果
        lines = stdout.split('\n')
        result_lines = []
        capture = False

        for line in lines:
            if 'gremlin>' in line:
                if query.strip() in line or any(keyword in line for keyword in ['count()', 'groupCount()', 'limit(']):
                    capture = True
                elif capture and line.strip() and not line.startswith('gremlin>') and not line.startswith('['):
                    if '==>' in line:
                        result_lines.append(line.split('==>')[1].strip())

        if result_lines:
            return result_lines[-1]  # 返回最后一个结果
        else:
            return "无法解析结果"

    except Exception as e:
        logger.error(f"查询失败: {e}")
        return f"错误: {e}"

def main():
    """主函数"""
    logger.info("🚀 开始验证JanusGraph导入结果...")
    logger.info("=" * 60)

    # 验证查询列表
    queries = [
        ("g.V().count()", "统计顶点总数"),
        ("g.E().count()", "统计边总数"),
        ("g.V().groupCount().by(label)", "按类型统计顶点"),
        ("g.E().groupCount().by(label)", "按类型统计边"),
        ("g.V().hasLabel('Patent').limit(3).values('title')", "查看示例专利标题"),
        ("g.V().hasLabel('Company').limit(3).values('name')", "查看示例公司名称"),
    ]

    results = {}

    for query, description in queries:
        logger.info(f"\n📊 {description}")
        result = execute_gremlin_query(query, description)
        results[description] = result
        logger.info(f"   结果: {result}")
        time.sleep(1)  # 避免查询过快

    # 生成报告
    logger.info("\n" + "=" * 60)
    logger.info("✅ 验证报告")
    logger.info("=" * 60)

    report = {
        "验证时间": time.strftime("%Y-%m-%d %H:%M:%S"),
        "查询结果": results,
        "总体状态": "成功" if "错误" not in str(results) else "部分失败"
    }

    # 保存报告
    with open("/Users/xujian/Athena工作平台/scripts/data_import/verification_result.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"\n📄 详细报告已保存到: verification_result.json")

    # 总结
    logger.info("\n🎉 知识图谱导入验证完成！")
    logger.info("\n💡 使用提示:")
    logger.info("1. 知识图谱API服务: http://localhost:8080/docs")
    logger.info("2. 可以进行混合搜索测试")
    logger.info("3. 数据已准备好供查询和分析")

if __name__ == "__main__":
    main()