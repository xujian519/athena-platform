#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查JanusGraph中的实际数据状态
"""

import subprocess
import time
import logging
import json
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_check_script():
    """创建数据检查的Gremlin脚本"""
    script_content = """
// 打开图
graph = JanusGraphFactory.open('conf/janusgraph-cassandra.properties')

// 检查图是否已打开
if (graph == null) {
    // 尝试其他配置
    try {
        graph = JanusGraphFactory.open('conf/janusgraph-berkeleyje.properties')
    } catch (e) {
        println("无法打开图: " + e.message)
        System.exit(1)
    }
}

// 设置遍历对象
g = graph.traversal()

// 统计信息
println("\\n=== JanusGraph 数据状态报告 ===")
println("检查时间: " + new Date())

// 1. 顶点总数
try {
    vertex_count = g.V().count().next()
    println("\\n✅ 顶点总数: " + vertex_count)
} catch (e) {
    println("\\n❌ 无法获取顶点总数: " + e.message)
}

// 2. 边总数
try {
    edge_count = g.E().count().next()
    println("✅ 边总数: " + edge_count)
} catch (e) {
    println("❌ 无法获取边总数: " + e.message)
}

// 3. 按类型统计顶点
try {
    vertex_types = g.V().groupCount().by(label).next()
    if (vertex_types && vertex_types.size() > 0) {
        println("\\n📋 顶点类型分布:")
        vertex_types.each { label, count ->
            println("  " + label + ": " + count + " 个")
        }
    } else {
        println("\\n⚠️ 没有找到顶点数据")
    }
} catch (e) {
    println("\\n❌ 无法统计顶点类型: " + e.message)
}

// 4. 按类型统计边
try {
    edge_types = g.E().groupCount().by(label).next()
    if (edge_types && edge_types.size() > 0) {
        println("\\n📋 边类型分布:")
        edge_types.each { label, count ->
            println("  " + label + ": " + count + " 条")
        }
    } else {
        println("\\n⚠️ 没有找到边数据")
    }
} catch (e) {
    println("\\n❌ 无法统计边类型: " + e.message)
}

// 5. 示例数据查看
try {
    // 查看专利示例
    patents = g.V().hasLabel('Patent').limit(3).valueMap('patent_number', 'title').toList()
    if (patents && patents.size() > 0) {
        println("\\n📝 示例专利:")
        patents.eachWithIndex { idx, patent ->
            patent_number = patent.get('patent_number') ? patent.get('patent_number')[0] : 'N/A'
            title = patent.get('title') ? patent.get('title')[0] : 'N/A'
            println("  " + (idx + 1) + ". " + patent_number + " - " + title)
        }
    }
} catch (e) {
    println("\\n⚠️ 无法查看专利示例: " + e.message)
}

try {
    // 查看公司示例
    companies = g.V().hasLabel('Company').limit(3).valueMap('name', 'industry').toList()
    if (companies && companies.size() > 0) {
        println("\\n🏢 示例公司:")
        companies.eachWithIndex { idx, company ->
            name = company.get('name') ? company.get('name')[0] : 'N/A'
            industry = company.get('industry') ? company.get('industry')[0] : 'N/A'
            println("  " + (idx + 1) + ". " + name + " (" + industry + ")")
        }
    }
} catch (e) {
    println("\\n⚠️ 无法查看公司示例: " + e.message)
}

try {
    // 查看发明人示例
    inventors = g.V().hasLabel('Inventor').limit(3).valueMap('name', 'organization').toList()
    if (inventors && inventors.size() > 0) {
        println("\\n👥 示例发明人:")
        inventors.eachWithIndex { idx, inventor ->
            name = inventor.get('name') ? inventor.get('name')[0] : 'N/A'
            org = inventor.get('organization') ? inventor.get('organization')[0] : 'N/A'
            println("  " + (idx + 1) + ". " + name + " - " + org)
        }
    }
} catch (e) {
    println("\\n⚠️ 无法查看发明人示例: " + e.message)
}

// 关闭图
graph.close()

println("\\n=== 检查完成 ===")
"""

    # 保存到临时文件
    temp_path = "/tmp/check_data.gremlin"
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(script_content)

    return temp_path

def check_janusgraph_data():
    """检查JanusGraph数据状态"""
    logger.info("🔍 开始检查JanusGraph数据状态...")

    # 创建检查脚本
    script_path = create_check_script()

    try:
        # 复制脚本到容器
        subprocess.run(
            ["docker", "cp", script_path, "janusgraph-kg:/tmp/check_data.gremlin"],
            check=True
        )

        # 执行检查脚本
        logger.info("📊 执行数据检查...")
        result = subprocess.run(
            ["docker", "exec", "janusgraph-kg", "/opt/janusgraph/bin/gremlin.sh", "-e", ":load /tmp/check_data.gremlin"],
            capture_output=True,
            text=True,
            timeout=60
        )

        # 输出结果
        if result.stdout:
            # 提取有用的信息
            lines = result.stdout.split('\n')
            print("\n" + "="*60)
            print("📊 JanusGraph 数据状态报告")
            print("="*60)

            for line in lines:
                if any(keyword in line for keyword in ["顶点总数", "边总数", "类型分布", "示例专利", "示例公司", "示例发明人", "检查时间", "没有找到", "无法"]):
                    print(line)

        if result.stderr and "SLF4J" not in result.stderr and "log4j" not in result.stderr:
            logger.warning(f"警告信息: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("执行超时")
    except subprocess.CalledProcessError as e:
        logger.error(f"执行失败: {e}")
    except Exception as e:
        logger.error(f"检查失败: {e}")
    finally:
        # 清理临时文件
        if os.path.exists(script_path):
            os.remove(script_path)

def check_storage_backend():
    """检查存储后端"""
    logger.info("\n🗄️ 检查存储后端配置...")

    try:
        # 检查Cassandra
        result = subprocess.run(
            ["docker", "exec", "janusgraph-kg", "cqlsh", "-e", "DESCRIBE KEYSPACES", "cassandra"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if "janusgraph" in result.stdout.lower():
            print("✅ Cassandra存储后端正常，存在janusgraph相关键空间")
        else:
            print("⚠️ 未发现janusgraph键空间")

    except:
        print("⚠️ 无法连接Cassandra，可能使用其他存储后端")

    # 检查数据目录
    try:
        result = subprocess.run(
            ["docker", "exec", "janusgraph-kg", "ls", "-la", "/var/lib/janusgraph/"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ 找到JanusGraph数据目录")
        else:
            print("⚠️ 默认数据目录不存在")

    except:
        print("⚠️ 无法检查数据目录")

def main():
    """主函数"""
    logger.info("🚀 开始全面检查JanusGraph数据状态...")
    print("\n" + "="*60)

    # 1. 检查容器状态
    print("1️⃣ 检查容器状态")
    subprocess.run(["docker", "ps", "--filter", "name=janusgraph-kg"], check=False)

    # 2. 检查存储后端
    print("\n2️⃣ 检查存储后端")
    check_storage_backend()

    # 3. 检查数据内容
    print("\n3️⃣ 检查数据内容")
    check_janusgraph_data()

    # 4. 总结
    print("\n" + "="*60)
    print("✅ 检查完成！")
    print("\n💡 建议:")
    print("1. 如果没有数据，请重新运行导入脚本")
    print("2. 如果有数据但无法查询，可能是权限或配置问题")
    print("3. 可以通过API服务 http://localhost:8080/docs 进行查询测试")

if __name__ == "__main__":
    main()