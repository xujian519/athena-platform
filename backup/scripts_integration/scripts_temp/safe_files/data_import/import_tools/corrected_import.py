#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用正确配置重新导入数据到JanusGraph
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

def create_berkeley_graph():
    """创建BerkeleyDB图并导入数据"""
    logger.info("🚀 开始使用BerkeleyDB导入数据...")

    # 创建完整的导入脚本
    import_script = """
// BerkeleyDB配置
conf = new BaseConfiguration()
conf.setProperty("storage.backend", "berkeleyje")
conf.setProperty("storage.directory", "/opt/janusgraph/db/patent")
conf.setProperty("cache.db-cache", "true")
conf.setProperty("cache.db-cache-time", "180000")
conf.setProperty("cache.db-cache-size", "0.5")

// 打开图
graph = JanusGraphFactory.open(conf)
g = graph.traversal()

// 创建索引
mgmt = graph.openManagement()
try {
    if (!mgmt.containsPropertyKey('entity_id')) {
        entity_id = mgmt.makePropertyKey('entity_id').dataType(String.class).make()
        mgmt.buildIndex('byEntityId', Vertex.class).addKey(entity_id).buildCompositeIndex()
    }

    if (!mgmt.containsPropertyKey('patent_number')) {
        patent_number = mgmt.makePropertyKey('patent_number').dataType(String.class).make()
        mgmt.buildIndex('byPatentNumber', Vertex.class).addKey(patent_number).buildCompositeIndex()
    }

    mgmt.commit()
    println("✅ 索引创建成功")
} catch (e) {
    mgmt.rollback()
    println("⚠️ 索引可能已存在")
}

// 开始事务
g.tx().open()

// 导入专利数据
println("\\n📚 导入专利数据...")
(1..10).each { i ->
    g.addV('Patent')
        .property('entity_id', 'patent_' + i)
        .property('patent_number', 'CN' + String.format('%09d', i) + 'A')
        .property('title', '深度学习专利 ' + i + ': 创新的算法架构')
        .property('abstract', '本专利涉及深度学习技术，提供了创新的解决方案。')
        .property('inventors', '发明人' + (i % 5 + 1))
        .property('assignee', '科技公司' + (i % 3 + 1))
        .property('application_date', '2023-' + String.format('%02d', i % 12 + 1) + '-01')
        .next()
}
println("专利导入完成")

// 导入公司数据
println("\\n🏢 导入公司数据...")
(1..5).each { i ->
    g.addV('Company')
        .property('entity_id', 'company_' + i)
        .property('name', 'AI科技公司' + i)
        .property('industry', '人工智能')
        .property('location', '北京市海淀区')
        .property('founded_date', '2010-' + String.format('%02d', i % 12 + 1) + '-01')
        .next()
}
println("公司导入完成")

// 导入发明人数据
println("\\n👥 导入发明人数据...")
surnames = ['张', '李', '王', '刘', '陈']
names = ['伟', '芳', '娜', '敏', '静']
(1..8).each { i ->
    surname = surnames[i % 5]
    name = names[i % 5]
    g.addV('Inventor')
        .property('entity_id', 'inventor_' + i)
        .property('name', surname + name)
        .property('organization', '清华大学')
        .property('specialization', '深度学习')
        .property('patent_count', (i % 5) + 1)
        .next()
}
println("发明人导入完成")

// 创建关系
println("\\n🔗 创建关系...")
// 专利-公司关系
(1..10).each { i ->
    patent_id = (i % 10) + 1
    company_id = (i % 5) + 1

    p = g.V().has('entity_id', 'patent_' + patent_id).next()
    c = g.V().has('entity_id', 'company_' + company_id).next()
    p.addEdge('OWNED_BY', c)
}

// 专利-发明人关系
(1..15).each { i ->
    patent_id = (i % 10) + 1
    inventor_id = (i % 8) + 1

    p = g.V().has('entity_id', 'patent_' + patent_id).next()
    inv = g.V().has('entity_id', 'inventor_' + inventor_id).next()
    p.addEdge('INVENTED_BY', inv).property('contribution_type', 'main')
}
println("关系创建完成")

// 提交事务
g.tx().commit()

// 验证导入
println("\\n📊 验证导入结果...")
vertex_count = g.V().count().next()
edge_count = g.E().count().next()
patent_count = g.V().hasLabel('Patent').count().next()
company_count = g.V().hasLabel('Company').count().next()
inventor_count = g.V().hasLabel('Inventor').count().next()

println("\\n=== 导入统计 ===")
println("顶点总数: " + vertex_count)
println("边总数: " + edge_count)
println("专利数: " + patent_count)
println("公司数: " + company_count)
println("发明人数: " + inventor_count)

// 查看示例数据
println("\\n📝 示例专利:")
g.V().hasLabel('Patent').limit(3).valueMap('patent_number', 'title').each { patent ->
    num = patent.get('patent_number')[0]
    title = patent.get('title')[0]
    println("  " + num + " - " + title)
}

println("\\n🏢 示例公司:")
g.V().hasLabel('Company').limit(3).values('name').each { name ->
    println("  " + name)
}

println("\\n👥 示例发明人:")
g.V().hasLabel('Inventor').limit(3).values('name').each { name ->
    println("  " + name)
}

// 关闭图
graph.close()
println("\\n✅ 导入完成！")
"""

    # 保存脚本
    script_path = "/tmp/corrected_import.gremlin"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(import_script)

    # 复制到容器
    subprocess.run(
        ["docker", "cp", script_path, "janusgraph-kg:/tmp/corrected_import.gremlin"],
        check=True
    )

    # 执行导入
    logger.info("🔄 执行数据导入...")
    result = subprocess.run(
        ["docker", "exec", "janusgraph-kg", "/opt/janusgraph/bin/gremlin.sh", "-e", ":load /tmp/corrected_import.gremlin"],
        capture_output=True,
        text=True,
        timeout=60
    )

    # 输出结果
    print("\n" + "="*60)
    print("📊 导入执行结果")
    print("="*60)

    # 提取关键信息
    lines = result.stdout.split('\n')
    for line in lines:
        if any(keyword in line for keyword in ["索引创建", "导入完成", "验证导入", "导入统计", "示例专利", "示例公司", "示例发明人", "顶点总数", "边总数"]):
            print(line)

    if result.stderr:
        print("\n⚠️ 警告信息:")
        # 只显示重要错误
        errors = [line for line in result.stderr.split('\n')
                 if line and 'SLF4J' not in line and 'log4j' not in line
                 and 'Hadoop' not in line and 'htrace' not in line]
        for error in errors[:5]:  # 只显示前5个错误
            print(f"  {error}")

    # 清理
    import os
    os.remove(script_path)

    return "导入统计" in result.stdout

def verify_data_in_db():
    """验证数据实际写入BerkeleyDB"""
    logger.info("\n🔍 验证BerkeleyDB数据文件...")

    # 检查数据目录
    result = subprocess.run(
        ["docker", "exec", "janusgraph-kg", "ls", "-la", "/opt/janusgraph/db/patent/"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and result.stdout:
        print("\n✅ BerkeleyDB数据文件:")
        print(result.stdout)
        return True
    else:
        print("\n❌ BerkeleyDB数据目录为空或不存在")
        return False

def verify_via_api():
    """通过API验证数据"""
    logger.info("\n🌐 通过API验证数据...")

    # 测试API健康状态
    try:
        response = subprocess.run(
            ["curl", "-s", "http://localhost:8080/health"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if response.status_code == 0:
            data = json.loads(response.stdout)
            if data.get("database") == "connected":
                print("✅ API服务已连接到数据库")
                return True
            else:
                print("⚠️ API服务可能连接到空数据库")
    except:
        print("❌ 无法通过API验证")

    return False

def main():
    """主函数"""
    logger.info("🚀 开始正确的数据导入流程...")
    print("\n" + "="*60)

    success = False

    # 1. 执行导入
    try:
        success = create_berkeley_graph()
    except Exception as e:
        logger.error(f"导入失败: {e}")

    # 2. 验证数据文件
    verify_data_in_db()

    # 3. 验证API连接
    verify_via_api()

    # 总结
    print("\n" + "="*60)
    if success:
        print("✅ 数据导入成功！")
        print("\n💡 使用提示:")
        print("1. 数据已存储在BerkeleyDB: /opt/janusgraph/db/patent/")
        print("2. API服务: http://localhost:8080/docs")
        print("3. 可以进行专利查询和图遍历")
    else:
        print("❌ 数据导入可能失败")
        print("\n🔧 故障排查:")
        print("1. 检查JanusGraph日志")
        print("2. 验证BerkeleyDB权限")
        print("3. 重新执行导入脚本")

    print("="*60)

if __name__ == "__main__":
    main()