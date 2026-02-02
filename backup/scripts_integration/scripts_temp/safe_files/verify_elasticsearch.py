#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证Elasticsearch服务
Verify Elasticsearch Service

验证Elasticsearch是否正常运行并可访问

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import subprocess
import json
import time

def check_docker_container():
    """检查Docker容器状态"""
    print("📋 检查Docker容器状态...")

    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "table", "--filter", "name=athena-elasticsearch"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and "athena-elasticsearch" in result.stdout:
            print("✅ Elasticsearch容器正在运行")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # 跳过标题行
                if "athena-elasticsearch" in line:
                    print(f"   📦 {line}")
                    return True

        print("❌ Elasticsearch容器未运行")
        return False

    except Exception as e:
        print(f"❌ 检查容器失败: {str(e)}")
        return False

def check_http_endpoint():
    """检查HTTP端点"""
    print("\n🌐 检查HTTP端点...")

    # 等待服务启动
    print("⏳ 等待服务完全启动...")
    time.sleep(5)

    try:
        # 使用curl检查健康状态
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:9200/_cluster/health"],
            capture_output=True,
            text=True
        )

        if result.stdout == "200":
            print("✅ HTTP端点可访问 (状态码: 200)")

            # 获取集群健康信息
            health_result = subprocess.run(
                ["curl", "-s", "http://localhost:9200/_cluster/health"],
                capture_output=True,
                text=True
            )

            if health_result.returncode == 0:
                health_data = json.loads(health_result.stdout)
                print(f"   🏥 集群名称: {health_data.get('cluster_name', 'Unknown')}")
                print(f"   💚 状态: {health_data.get('status', 'Unknown')}")
                print(f"   📊 节点数: {health_data.get('number_of_nodes', 0)}")
                print(f"   💾 数据节点: {health_data.get('number_of_data_nodes', 0)}")

                return True
        else:
            print(f"❌ HTTP端点不可访问 (状态码: {result.stdout})")

    except Exception as e:
        print(f"❌ 检查端点失败: {str(e)}")

    return False

def check_elasticsearch_info():
    """检查Elasticsearch信息"""
    print("\n📋 检查Elasticsearch详细信息...")

    try:
        # 获取节点信息
        nodes_result = subprocess.run(
            ["curl", "-s", "http://localhost:9200/_nodes/stats"],
            capture_output=True,
            text=True
        )

        if nodes_result.returncode == 0:
            nodes_data = json.loads(nodes_result.stdout)
            nodes = nodes_data.get('nodes', {})

            for node_id, node_info in nodes.items():
                print(f"   🖥️  节点: {node_info.get('name', 'Unknown')}")
                print(f"      版本: {node_info.get('version', 'Unknown')}")
                print(f"      JVM堆内存: {node_info.get('jvm', {}).get('mem', {}).get('heap_used_percent', 'N/A')}%")

        # 获取索引信息
        indices_result = subprocess.run(
            ["curl", "-s", "http://localhost:9200/_cat/indices?format=json"],
            capture_output=True,
            text=True
        )

        if indices_result.returncode == 0:
            indices = json.loads(indices_result.stdout)
            if indices:
                print(f"   📚 现有索引数: {len(indices)}")
                for index in indices[:3]:  # 只显示前3个
                    print(f"      - {index.get('index', 'Unknown')} ({index.get('docs.count', 0)} 文档)")

        return True

    except Exception as e:
        print(f"❌ 获取信息失败: {str(e)}")
        return False

def test_basic_search():
    """测试基本搜索功能"""
    print("\n🔍 测试基本搜索功能...")

    # 创建测试索引
    test_index = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"}
            }
        }
    }

    try:
        # 创建索引
        create_result = subprocess.run([
            "curl", "-X", "PUT",
            "http://localhost:9200/test_index",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(test_index)
        ], capture_output=True, text=True)

        if create_result.returncode == 0 and "acknowledged" in create_result.stdout:
            print("   ✅ 测试索引创建成功")

            # 插入测试数据
            doc = {
                "title": "人工智能专利",
                "content": "这是一份关于人工智能技术的专利文档"
            }

            insert_result = subprocess.run([
                "curl", "-X", "POST",
                "http://localhost:9200/test_index/_doc",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(doc)
            ], capture_output=True, text=True)

            if insert_result.returncode == 0:
                print("   ✅ 测试数据插入成功")

                # 刷新索引
                subprocess.run(["curl", "-X", "POST", "http://localhost:9200/test_index/_refresh"],
                           capture_output=True)

                # 搜索测试
                search_result = subprocess.run([
                    "curl", "-s", "http://localhost:9200/test_index/_search",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps({"query": {"match": {"title": "人工智能"}}})
                ], capture_output=True, text=True)

                if search_result.returncode == 0:
                    search_data = json.loads(search_result.stdout)
                    hits = search_data.get('hits', {}).get('hits', [])
                    if hits:
                        print(f"   ✅ 搜索成功，找到 {len(hits)} 条结果")
                        for hit in hits[:1]:
                            source = hit['_source']
                            print(f"      📄 标题: {source.get('title', '')}")
                            print(f"      📝 内容: {source.get('content', '')[:50]}...")

                # 清理测试数据
                subprocess.run(["curl", "-X", "DELETE", "http://localhost:9200/test_index"],
                           capture_output=True)

                return True

        print("   ❌ 测试失败")
        return False

    except Exception as e:
        print(f"   ❌ 测试异常: {str(e)}")
        return False

def main():
    """主函数"""
    print("="*80)
    print("🔍 Elasticsearch服务验证")
    print("="*80)
    print(f"⏰ 验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    success_count = 0
    total_checks = 4

    # 1. 检查容器
    if check_docker_container():
        success_count += 1

    # 2. 检查HTTP端点
    if check_http_endpoint():
        success_count += 1

    # 3. 检查详细信息
    if check_elasticsearch_info():
        success_count += 1

    # 4. 测试搜索功能
    if test_basic_search():
        success_count += 1

    # 总结
    print("\n" + "="*80)
    print("📊 验证结果总结")
    print("="*80)

    print(f"✅ 成功项: {success_count}/{total_checks}")
    print(f"❌ 失败项: {total_checks - success_count}/{total_checks}")
    print(f"📈 成功率: {success_count/total_checks*100:.0f}%")

    if success_count == total_checks:
        print("\n🎉 Elasticsearch服务完全正常运行！")
        print("✅ 迭代式搜索模块已准备就绪")
        print("✅ 可以开始进行专利搜索和数据分析")
    else:
        print(f"\n⚠️ 部分功能未正常，请检查错误信息")

    print("\n💡 使用建议:")
    print("1. 迭代式搜索服务现在可以与ES集成")
    print("2. 可以实现高性能的专利全文搜索")
    print("3. 支持复杂的搜索查询和聚合分析")
    print("4. 为LLM智能分析提供强大的数据基础")

if __name__ == "__main__":
    main()