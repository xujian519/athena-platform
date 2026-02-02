#!/usr/bin/env python3
"""
测试云熙记忆系统
Test YunPat Memory System
"""

import requests
import json
import time
from datetime import datetime, timedelta

# 测试配置
BASE_URL = "http://localhost:8087"
API_BASE = f"{BASE_URL}/api/v1/memory"


class MemorySystemTester:
    def __init__(self):
        self.test_results = []

    def log(self, message, success=True):
        """记录测试结果"""
        status = "✅" if success else "❌"
        self.test_results.append(f"{status} {message}")
        print(f"{status} {message}")

    def test_memory_types(self):
        """测试记忆类型"""
        print("\n📋 测试记忆类型...")
        try:
            response = requests.get(f"{API_BASE}/types")
            if response.status_code == 200:
                types = response.json()
                self.log(f"获取记忆类型成功，共{len(types)}种类型")
                for memory_type, description in types.items():
                    print(f"  • {memory_type}: {description}")
                return True
            else:
                self.log(f"获取记忆类型失败: HTTP {response.status_code}", False)
        except Exception as e:
            self.log(f"记忆类型测试失败: {str(e)}", False)

    def test_save_memory(self):
        """测试保存记忆"""
        print("\n💾 测试保存记忆...")

        test_memories = [
            {
                "content": "这是测试长期记忆的内容，云熙会永久保存",
                "type": "long",
                "importance": 0.8,
                "tags": ["测试", "长期"],
                "metadata": {"source": "test", "timestamp": datetime.now().isoformat()}
            },
            {
                "content": "这是一条短期记忆，会话结束后可能被清理",
                "type": "short",
                "importance": 0.3,
                "tags": ["测试", "短期"]
            },
            {
                "content": "专利检索的最佳实践和注意事项",
                "type": "work",
                "importance": 0.7,
                "tags": ["专利", "检索", "工作"]
            }
        ]

        saved_ids = []
        for memory in test_memories:
            try:
                response = requests.post(
                    f"{API_BASE}/save",
                    json=memory
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        saved_ids.append(result["memory_id"])
                        self.log(f"保存{memory['type']}记忆成功")
                    else:
                        self.log(f"保存{memory['type']}记忆失败: {result.get('message')}", False)
                else:
                    self.log(f"保存{memory['type']}记忆失败: HTTP {response.status_code}", False)

            except Exception as e:
                self.log(f"保存{memory['type']}记忆失败: {str(e)}", False)

        return saved_ids

    def test_recall_memory(self):
        """测试回忆记忆"""
        print("\n🔍 测试回忆记忆...")

        test_queries = ["测试", "专利", "云熙", "记忆"]

        for query in test_queries:
            try:
                response = requests.get(
                    f"{API_BASE}/recall",
                    params={
                        "query": query,
                        "limit": 5
                    }
                )

                if response.status_code == 200:
                    memories = response.json()
                    self.log(f"搜索'{query}'找到{len(memories)}条记忆")
                    if memories:
                        print(f"  第一条: {memories[0]['content'][:50]}...")
                else:
                    print(f"  未找到相关记忆")
                else:
                    self.log(f"搜索'{query}'失败: HTTP {response.status_code}", False)

            except Exception as e:
                self.log(f"搜索'{query}'失败: {str(e)}", False)

    def test_similar_search(self):
        """测试相似度搜索"""
        print("\n🧠 测试相似度搜索...")

        try:
            response = requests.post(
                f"{API_BASE}/search",
                json={
                    "query": "专利申请流程",
                    "similarity_threshold": 0.6,
                    "limit": 3
                }
            )

            if response.status_code == 200:
                memories = response.json()
                self.log(f"相似度搜索找到{len(memories)}条记忆")
                for memory in memories:
                    similarity = memory.get("similarity_score", "N/A")
                    print(f"  相似度 {similarity}: {memory['content'][:50]}...")
            else:
                self.log(f"相似度搜索失败: HTTP {response.status_code}", False)

        except Exception as e:
            self.log(f"相似度搜索失败: {str(e)}", False)

    def test_list_memories(self):
        """测试按类型列出记忆"""
        print("\n📝 测试列出记忆...")

        for memory_type in ["short", "long", "work"]:
            try:
                response = requests.get(
                    f"{API_BASE}/list",
                    params={
                        "type": memory_type,
                        "limit": 10
                    }
                )

                if response.status_code == 200:
                    memories = response.json()
                    self.log(f"列出{memory_type}记忆: {len(memories)}条")
                else:
                    self.log(f"列出{memory_type}记忆失败: HTTP {response.status_code}", False)

            except Exception as e:
                self.log(f"列出{memory_type}记忆失败: {str(e)}", False)

    def test_auto_save(self):
        """测试自动保存对话"""
        print("\�💾 测试自动保存对话...")

        conversation = [
            {
                "role": "user",
                "content": "云熙，请帮我分析这个专利",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "主人，我来帮您分析这个专利...",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "谢谢云熙，你的服务很棒！",
                "timestamp": datetime.now().isoformat()
            }
        ]

        try:
            response = requests.post(
                f"{API_BASE}/auto-save",
                json={
                    "conversation": conversation,
                    "user_id": "test_user"
                }
            )

            if response.status_code == 200:
                result = response.json()
                saved_count = result.get("saved_count", 0)
                self.log(f"自动保存{len(conversation)}条对话，保存{saved_count}条记忆")
            else:
                self.log(f"自动保存失败: HTTP {response.status_code}", False)

        except Exception as e:
            self.log(f"自动保存失败: {str(e)}", False)

    def test_memory_stats(self):
        """测试记忆统计"""
        print("\n📊 测试记忆统计...")

        try:
            response = requests.get(
                f"{API_BASE}/stats",
                params={"user_id": "test_user"}
            )

            if response.status_code == 200:
                stats = response.json()
                summary = stats.get("summary", {})
                self.log("获取记忆统计成功")
                print(f"  总记忆数: {summary.get('total_memories', 'N/A')}")
                print(f"  最常见类型: {summary.get('most_common_type', 'N/A')}")
                print(f"  平均重要性: {summary.get('avg_importance', 'N/A')}")
            else:
                self.log(f"获取统计失败: HTTP {response.status_code}", False)

        except Exception as e:
            self.log(f"获取统计失败: {str(e)}", False)

    def test_insights(self):
        """测试记忆洞察"""
        print("\n💡 测试记忆洞察...")

        try:
            response = requests.get(
                f"{API_BASE}/insights",
                params={
                    "user_id": "test_user",
                    "days": 7
                }
            )

            if response.status_code == 200:
                insights = response.json()
                self.log("获取记忆洞察成功")

                by_type = insights.get("by_type", {})
                print(f"  各类型记忆统计:")
                for mem_type, stats in by_type.items():
                    print(f"    {mem_type}: {stats.get('count', 0)}条")

                top_tags = insights.get("top_tags", [])
                if top_tags:
                    print(f"  热门标签:")
                    for i, tag in enumerate(top_tags[:3]):
                        print(f"    {i+1}. {tag['tag']}: {tag['count']}次")

                return True
            else:
                self.log(f"获取洞察失败: HTTP {response.status_code}", False)

        except Exception as e:
            self.log(f"获取洞察失败: {str(e)}", False)

    def test_update_memory(self):
        """测试更新记忆"""
        print("\n✏️ 测试更新记忆...")

        # 首先保存一条记忆
        save_response = requests.post(
            f"{API_BASE}/save",
            json={
                "content": "这是要更新的测试记忆",
                "type": "long",
                "importance": 0.5
            }
        )

        if save_response.status_code == 200:
            memory_id = save_response.json()["memory_id"]

            # 更新记忆
            try:
                update_response = requests.put(
                    f"{API_BASE}/{memory_id}",
                    json={
                        "content": "这是更新后的测试记忆内容",
                        "importance": 0.8,
                        "metadata": {"updated": True}
                    }
                )

                if update_response.status_code == 200:
                    self.log(f"更新记忆成功: {memory_id[:8]}")
                    return True
                else:
                    self.log(f"更新记忆失败: HTTP {update_response.status_code}", False)

            except Exception as e:
                self.log(f"更新记忆失败: {str(e)}", False)
        else:
            self.log("无法获取记忆ID进行更新测试", False)

    def test_delete_memory(self):
        """测试删除记忆"""
        print("\n🗑️ 测试删除记忆...")

        # 创建测试记忆
        save_response = requests.post(
            f"{API_BASE}/save",
            json={
                "content": "这是要删除的测试记忆",
                "type": "short",
                "importance": 0.2
            }
        )

        if save_response.status_code == 200:
            memory_id = save_response.json()["memory_id"]

            # 删除记忆
            try:
                delete_response = requests.delete(f"{API_BASE}/{memory_id}")

                if delete_response.status_code == 200:
                    self.log(f"删除记忆成功: {memory_id[:8]}")
                    return True
                else:
                    self.log(f"删除记忆失败: HTTP {delete_response.status_code}", False)

            except Exception as e:
                self.log(f"删除记忆失败: {str(e)}", False)
        else:
            self.log("无法获取记忆ID进行删除测试", False)

    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("🧪 云熙记忆系统测试")
        print("="*60)
        print()

        tests = [
            ("记忆类型", self.test_memory_types),
            ("保存记忆", self.test_save_memory),
            ("回忆记忆", self.test_recall_memory),
            ("相似度搜索", self.test_similar_search),
            ("列出记忆", self.test_list_memories),
            ("自动保存", self.test_auto_save),
            ("记忆统计", self.test_memory_stats),
            ("记忆洞察", self.test_insights),
            ("更新记忆", self.test_update_memory),
            ("删除记忆", self.test_delete_memory)
        ]

        passed = 0
        for test_name, test_func in tests:
            if test_func():
                passed += 1

        print("\n" + "="*60)
        print("📊 测试结果总结")
        print("="*60)
        print(f"总测试数: {len(tests)}")
        print(f"通过数: {passed}")
        print(f"通过率: {passed/len(tests)*100:.1f}%")
        print()

        # 保存测试结果
        with open("memory_system_test_results.txt", "w", encoding="utf-8") as f:
            f.write("云熙记忆系统测试结果\n")
            f.write("="*60 + "\n")
            f.write(f"测试时间: {datetime.now().isoformat()}\n")
            f.write(f"总测试数: {len(tests)}\n")
            f.write(f"通过数: {passed}\n")
            f.write(f"通过率: {passed/len(tests)*100:.1f}%\n")
            f.write("\n详细结果:\n")
            for result in self.test_results:
                f.write(f"{result}\n")

        if passed / len(tests) >= 0.9:
            print("🎉 云熙记忆系统功能完整！")
        elif passed / len(tests) >= 0.7:
            print("✨ 云熙记忆系统基本可用！")
        else:
            print("⚠️ 云熙记忆系统需要修复！")

        return passed / len(tests) >= 0.7


def main():
    """主函数"""
    # 先检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/v2/health")
        if response.status_code != 200:
            print("❌ YunPat服务未运行，请先启动服务")
            print("  命令: python3 services/yunpat-agent/api_service.py")
            return
    except:
        print("❌ 无法连接到YunPat服务")
        return

    tester = MemorySystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()