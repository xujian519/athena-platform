#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过交互式方式导入数据到JanusGraph BerkeleyDB
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

def execute_import():
    """执行导入"""
    logger.info("🚀 开始导入数据...")

    # 创建导入命令
    commands = [
        # 打开BerkeleyDB图
        'import org.apache.commons.configuration.BaseConfiguration\n'
        'conf = new BaseConfiguration()\n'
        'conf.setProperty("storage.backend", "berkeleyje")\n'
        'conf.setProperty("storage.directory", "/opt/janusgraph/db/patent")\n'
        'conf.setProperty("cache.db-cache", "true")\n'
        'graph = JanusGraphFactory.open(conf)\n'
        'g = graph.traversal()\n'

        # 开始事务
        'g.tx().open()\n'

        # 创建测试数据
        'v1 = g.addV("Patent").property("patent_number", "CN202312345678A").property("title", "深度学习图像识别方法").next()\n'
        'v2 = g.addV("Company").property("name", "AI创新科技有限公司").property("industry", "人工智能").next()\n'
        'v3 = g.addV("Inventor").property("name", "张伟").property("organization", "清华大学").next()\n'

        # 创建关系
        'v1.addEdge("OWNED_BY", v2)\n'
        'v1.addEdge("INVENTED_BY", v3)\n'

        # 提交事务
        'g.tx().commit()\n'

        # 验证
        'vertex_count = g.V().count().next()\n'
        'edge_count = g.E().count().next()\n'
        'println("顶点数: " + vertex_count)\n'
        'println("边数: " + edge_count)\n'

        # 关闭图
        'graph.close()\n'
        'println("导入完成!")\n'
        'exit\n'
    ]

    # 通过管道执行
    process = subprocess.Popen(
        ["docker", "exec", "-i", "janusgraph-kg", "/opt/janusgraph/bin/gremlin.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 发送命令
    stdout, stderr = process.communicate(input=''.join(commands), timeout=60)

    # 提取结果
    print("\n" + "="*60)
    print("📊 导入结果")
    print("="*60)

    # 查找关键输出
    lines = stdout.split('\n')
    for line in lines:
        if any(keyword in line for keyword in ["顶点数:", "边数:", "导入完成"]):
            print(line)

    return "导入完成" in stdout

def check_berkeley_files():
    """检查BerkeleyDB文件"""
    print("\n📁 检查BerkeleyDB数据文件...")

    result = subprocess.run(
        ["docker", "exec", "janusgraph-kg", "ls", "-la", "/opt/janusgraph/db/patent/"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        files = result.stdout.strip().split('\n')[1:]  # 跳过第一行
        db_files = [f for f in files if f and not f.startswith('total')]

        if db_files:
            print("✅ 找到数据文件:")
            for f in db_files[:5]:  # 只显示前5个文件
                print(f"  {f}")
            return True
        else:
            print("❌ 数据目录为空")
            return False
    else:
        print("❌ 无法访问数据目录")
        return False

def verify_data_persistence():
    """验证数据持久化"""
    print("\n🔍 验证数据持久化...")

    # 重新打开图并查询
    commands = [
        'import org.apache.commons.configuration.BaseConfiguration\n'
        'conf = new BaseConfiguration()\n'
        'conf.setProperty("storage.backend", "berkeleyje")\n'
        'conf.setProperty("storage.directory", "/opt/janusgraph/db/patent")\n'
        'graph = JanusGraphFactory.open(conf)\n'
        'g = graph.traversal()\n'

        'count = g.V().count().next()\n'
        'println("持久化顶点数: " + count)\n'

        'g.V().label().dedup().each { println("节点类型: " + it) }\n'

        'graph.close()\n'
        'exit\n'
    ]

    process = subprocess.Popen(
        ["docker", "exec", "-i", "janusgraph-kg", "/opt/janusgraph/bin/gremlin.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate(input=''.join(commands), timeout=30)

    # 显示结果
    for line in stdout.split('\n'):
        if "持久化顶点数" in line or "节点类型" in line:
            print(line)

    return "持久化顶点数" in stdout

def main():
    """主函数"""
    logger.info("🚀 开始JanusGraph BerkeleyDB数据导入...")
    print("\n" + "="*60)

    # 1. 执行导入
    success = execute_import()

    # 2. 检查数据文件
    has_files = check_berkeley_files()

    # 3. 验证持久化
    persistent = verify_data_persistence()

    # 总结
    print("\n" + "="*60)
    print("✅ 导入总结")
    print("="*60)

    if success and has_files and persistent:
        print("🎉 数据导入成功并已持久化到BerkeleyDB!")
        print("\n💡 数据详情:")
        print("  - 存储位置: /opt/janusgraph/db/patent/")
        print("  - 包含数据: 专利、公司、发明人")
        print("  - 关系类型: OWNED_BY, INVENTED_BY")
        print("\n🔗 API服务: http://localhost:8080/docs")
    else:
        print("⚠️ 导入可能存在问题")
        print(f"  - 导入执行: {'✅' if success else '❌'}")
        print(f"  - 数据文件: {'✅' if has_files else '❌'}")
        print(f"  - 数据持久化: {'✅' if persistent else '❌'}")

if __name__ == "__main__":
    main()