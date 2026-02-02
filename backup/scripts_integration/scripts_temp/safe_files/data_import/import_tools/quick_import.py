#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速导入测试数据到JanusGraph
"""

import subprocess
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_gremlin(query, description="执行查询"):
    """执行Gremlin查询"""
    logger.info(f"🔧 {description}")

    # 创建临时脚本
    script_content = f"""
gremlin.graph=org.janusgraph.core.JanusGraph
storage.backend=berkeleyje
storage.directory=db/patent
cache.db-cache=true
cache.db-cache-time=180000
cache.db-cache-size=0.5

// 打开图
graph = JanusGraphFactory.open()

// 设置遍历
g = graph.traversal()

{query}

// 提交事务
g.tx().commit()

println('执行完成')
"""

    # 创建临时文件
    script_path = "/tmp/quick_import.gremlin"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)

    try:
        # 复制到容器
        subprocess.run(
            ["docker", "cp", script_path, "janusgraph-kg:/tmp/quick_import.gremlin"],
            check=True,
            capture_output=True
        )

        # 执行查询
        result = subprocess.run(
            ["docker", "exec", "janusgraph-kg", "/opt/janusgraph/bin/gremlin.sh", "-e", ":load /tmp/quick_import.gremlin"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # 清理临时文件
        os.remove(script_path)

        if "执行完成" in result.stdout:
            logger.info(f"✅ {description} - 成功")
            return True
        else:
            logger.warning(f"⚠️ {description} - 可能失败")
            if result.stderr:
                logger.error(f"错误: {result.stderr[-200:]}")
            return False

    except Exception as e:
        logger.error(f"执行失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始快速导入测试数据...")
    logger.info("=" * 60)

    # 1. 创建几个测试节点
    logger.info("\n📝 创建测试数据...")

    # 创建专利
    patent_query = """
// 创建专利节点
v1 = g.addV('Patent').property('patent_number', 'CN202312345678A')
    .property('title', '深度学习图像识别方法')
    .property('abstract', '本发明提供了一种基于深度学习的图像识别方法...')
    .next()

v2 = g.addV('Patent').property('patent_number', 'CN202312345679A')
    .property('title', '自然语言处理优化技术')
    .property('abstract', '本发明涉及自然语言处理领域...')
    .next()
"""

    execute_gremlin(patent_query, "创建专利节点")

    # 创建公司
    company_query = """
// 创建公司节点
c1 = g.addV('Company').property('name', 'AI创新科技有限公司')
    .property('industry', '人工智能')
    .property('location', '北京市海淀区')
    .next()

c2 = g.addV('Company').property('name', '智能算法研究院')
    .property('industry', '算法研发')
    .property('location', '上海市浦东新区')
    .next()
"""

    execute_gremlin(company_query, "创建公司节点")

    # 创建发明人
    inventor_query = """
// 创建发明人节点
i1 = g.addV('Inventor').property('name', '张伟')
    .property('organization', '清华大学')
    .property('specialization', '计算机视觉')
    .next()

i2 = g.addV('Inventor').property('name', '李娜')
    .property('organization', '北京大学')
    .property('specialization', '自然语言处理')
    .next()
"""

    execute_gremlin(inventor_query, "创建发明人节点")

    # 创建关系
    relation_query = """
// 创建关系
g.V().has('patent_number', 'CN202312345678A').as('p')
    .V().has('name', 'AI创新科技有限公司').as('c')
    .addE('OWNED_BY').from('p').to('c').next()

g.V().has('patent_number', 'CN202312345679A').as('p')
    .V().has('name', '智能算法研究院').as('c')
    .addE('OWNED_BY').from('p').to('c').next()

g.V().has('patent_number', 'CN202312345678A').as('p')
    .V().has('name', '张伟').as('i')
    .addE('INVENTED_BY').from('p').to('i').next()

g.V().has('patent_number', 'CN202312345679A').as('p')
    .V().has('name', '李娜').as('i')
    .addE('INVENTED_BY').from('p').to('i').next()
"""

    execute_gremlin(relation_query, "创建关系")

    # 2. 验证数据
    logger.info("\n📊 验证数据...")

    verify_query = """
println("\\n=== 数据验证 ===")
vertex_count = g.V().count().next()
println("顶点总数: " + vertex_count)

edge_count = g.E().count().next()
println("边总数: " + edge_count)

patent_count = g.V().hasLabel('Patent').count().next()
println("专利数: " + patent_count)

company_count = g.V().hasLabel('Company').count().next()
println("公司数: " + company_count)

inventor_count = g.V().hasLabel('Inventor').count().next()
println("发明人数: " + inventor_count)
"""

    execute_gremlin(verify_query, "验证数据")

    logger.info("\n" + "=" * 60)
    logger.info("✅ 快速导入完成！")
    logger.info("\n💡 数据已导入到JanusGraph BerkeleyDB")
    logger.info("📁 数据位置: /opt/janusgraph/db/patent/")
    logger.info("🔍 API服务: http://localhost:8080/docs")

if __name__ == "__main__":
    import os
    main()