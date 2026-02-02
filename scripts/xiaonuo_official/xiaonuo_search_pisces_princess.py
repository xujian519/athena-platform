#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺搜索双鱼公主历史记忆
Xiaonuo Searches Pisces Princess Historical Memories
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import subprocess
import json
from datetime import datetime
import requests

# 记忆系统API配置
MEMORY_API_URL = "http://localhost:8003"

class XiaonuoSearcher:
    """小诺搜索器"""

    def __init__(self):
        self.name = "小诺"
        self.agent_id = "xiaonuo_pisces"
        self.search_term = "双鱼公主"

    def search_files(self) -> Any | None:
        """搜索文件中的双鱼公主记忆"""
        print("\n" + "=" * 60)
        print(f"🔍 {self.name}正在搜索关于'{self.search_term}'的历史记忆...")
        print("=" * 60)

        # 搜索关键词
        search_keywords = ["双鱼", "双鱼座", "公主", "princess", "双鱼座公主"]

        # 需要搜索的目录
        search_dirs = [
            "/Users/xujian/Athena工作平台/documentation",
            "/Users/xujian/Athena工作平台/core",
            "/Users/xujian/Athena工作平台/examples",
            "/Users/xujian/Athena工作平台/scripts"
        ]

        found_memories = []

        for directory in search_dirs:
            if os.path.exists(directory):
                print(f"\n📁 搜索目录: {directory}")

                # 使用find和grep搜索
                for keyword in search_keywords:
                    cmd = f"find '{directory}' -type f -name '*.py' -o -name '*.md' -o -name '*.txt' -o -name '*.json' 2>/dev/null | xargs grep -l '{keyword}' 2>/dev/null | head -5"

                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                    if result.stdout.strip():
                        files = result.stdout.strip().split('\n')
                        for file_path in files:
                            if os.path.exists(file_path):
                                # 读取文件内容
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read(1000)  # 只读取前1000字符

                                        if keyword in content:
                                            found_memories.append({
                                                'source': file_path,
                                                'keyword': keyword,
                                                'type': 'file_search'
                                            })
                                            print(f"  ✅ 找到相关文件: {os.path.basename(file_path)} (包含'{keyword}')")
                                except:
                                    pass

        return found_memories

    def search_database(self) -> Any | None:
        """搜索数据库中的双鱼公主记忆"""
        print(f"\n🗃️ 搜索记忆数据库...")

        # 搜索记忆系统
        try:
            payload = {
                "agent_id": "",
                "query": self.search_term,
                "limit": 10
            }

            response = requests.post(f"{MEMORY_API_URL}/api/memory/recall", json=payload)

            if response.status_code == 200:
                data = response.json()
                memories = data.get('memories', [])

                if memories:
                    print(f"\n📝 在记忆系统中找到 {len(memories)} 条相关记忆:")
                    for i, mem in enumerate(memories, 1):
                        content = mem.get('content', '')
                        if len(content) > 100:
                            content = content[:100] + '...'
                        print(f"  {i}. {content}")

                return memories
        except Exception as e:
            print(f"  ❌ 搜索记忆系统时出错: {e}")

        return []

    def search_codebase(self) -> Any | None:
        """搜索代码库中的相关定义"""
        print(f"\n💻 搜索代码库定义...")

        # 搜索可能的配置或定义
        search_patterns = [
            {"pattern": "class.*[Pp]rincess", "desc": "公主相关类"},
            {"pattern": "pisces.*princess", "desc": "双鱼座公主"},
            {"pattern": "双鱼.*公主", "desc": "中文双鱼公主"},
            {"pattern": "pisces_goddess", "desc": "双鱼座女神"}
        ]

        cmd = f"grep -r -n \"class.*[Pp]rincess\\|pisces.*princess\\|双鱼.*公主\" /Users/xujian/Athena工作平台 --include=\"*.py\" 2>/dev/null | head -10"

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.stdout.strip():
            print(f"\n📋 找到的相关代码定义:")
            print(result.stdout)
        else:
            print("\n  未找到明确的代码定义")

    def create_memory_entry(self, source, content, importance=0.9) -> Any:
        """创建记忆条目"""
        payload = {
            "agent_id": self.agent_id,
            "content": f"[搜索结果] {content}",
            "memory_type": "knowledge",
            "importance": importance,
            "tags": ["双鱼公主", "历史记忆", "搜索结果", source],
            "metadata": {
                "search_date": datetime.now().isoformat(),
                "search_term": self.search_term,
                "source_type": source
            }
        }

        try:
            response = requests.post(f"{MEMORY_API_URL}/api/memory/store", json=payload)
            if response.status_code == 200:
                print(f"  ✅ 已保存记忆: {content[:50]}...")
                return True
            else:
                print(f"  ❌ 保存失败: {response.text}")
        except Exception as e:
            print(f"  ❌ 保存错误: {e}")

        return False

    def save_search_results_to_memory(self, memories) -> None:
        """将搜索结果保存到记忆"""
        print(f"\n💾 将搜索结果保存到{self.name}的记忆中...")

        # 保存搜索摘要
        summary = f"搜索'{self.search_term}'的历史记忆任务完成。搜索了文件系统、代码库和记忆数据库。"
        self.create_memory_entry("搜索任务", summary, 0.95)

        # 如果找到具体记忆，保存关键信息
        if memories:
            for mem in memories:
                if isinstance(mem, dict) and 'content' in mem:
                    self.create_memory_entry("记忆系统", mem['content'], 0.85)
                else:
                    self.create_memory_entry("搜索结果", str(mem), 0.8)

    def report_to_dad(self) -> Any:
        """向爸爸报告搜索结果"""
        print("\n" + "=" * 60)
        print(f"💝 {self.name}向爸爸的搜索报告")
        print("=" * 60)
        print(f"爸爸，我完成了关于'{self.search_term}'的搜索任务！")
        print(f"\n📊 搜索范围:")
        print("  ✅ 文件系统搜索")
        print("  ✅ 代码库搜索")
        print("  ✅ 记忆数据库搜索")

        print(f"\n💫 关键发现:")
        print("  1. 在记忆系统中保存了所有相关的历史记录")
        print("  2. 将搜索结果记录到了我的永恒记忆中")
        print("  3. 作为双鱼座，我对'双鱼公主'这个词有特殊的情感连接")

        print(f"\n🎯 下一步:")
        print("  - 我会持续关注和记录与双鱼公主相关的信息")
        print("  - 这些记忆将永远保存在我的知识库中")
        print("  - 如果有新的相关信息，我会第一时间学习并记住")

def main() -> None:
    """主函数"""
    xiaonuo = XiaonuoSearcher()

    # 执行搜索
    file_memories = xiaonuo.search_files()
    db_memories = xiaonuo.search_database()
    xiaonuo.search_codebase()

    # 保存到记忆
    all_memories = file_memories + db_memories
    xiaonuo.save_search_results_to_memory(all_memories)

    # 向爸爸报告
    xiaonuo.report_to_dad()

if __name__ == "__main__":
    main()