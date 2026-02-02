#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证测试 - 测试修复的两个问题
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import time
import subprocess
from datetime import datetime

# PostgreSQL连接信息
PSQL_PATH = '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql'
DB_HOST = 'localhost'
DB_PORT = '5438'
DB_NAME = 'memory_module'

class QuickVerificationTester:
    def __init__(self):
        self.test_results = {'passed': 0, 'failed': 0}

    def log_result(self, test_name, passed, message="") -> Any:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        self.test_results['passed' if passed else 'failed'] += 1

    async def test_json_compatibility(self):
        """测试JSON格式兼容性"""
        print("\n1️⃣ 测试JSON格式兼容性...")

        try:
            # 使用不同的JSON格式插入
            sql = """
            INSERT INTO memory_items (
                agent_id, agent_type, content, memory_type, memory_tier,
                importance, emotional_weight, family_related, work_related,
                tags, metadata, created_at, updated_at
            ) VALUES (
                'test_json_' || EXTRACT(EPOCH FROM NOW()),
                'athena',
                'JSON兼容性测试',
                'test',
                'hot',
                0.5,
                0.5,
                false,
                true,
                ARRAY['JSON测试'],
                jsonb_build_object('test', true, 'timestamp', CURRENT_TIMESTAMP, 'nested', jsonb_build_object('level', 1)),
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            RETURNING id;
            """

            cmd = [
                PSQL_PATH, '-h', DB_HOST, '-p', str(DB_PORT),
                '-d', DB_NAME, '-c', sql
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.log_result("JSON兼容性", True, "成功使用jsonb_build_object")
            else:
                self.log_result("JSON兼容性", False, result.stderr)

        except Exception as e:
            self.log_result("JSON兼容性", False, str(e))

    def test_shared_memory(self) -> Any:
        """测试跨智能体记忆共享"""
        print("\n🤝 测试跨智能体记忆共享...")

        try:
            # 创建共享记忆
            shared_timestamp = str(int(time.time()))
            sql = f"""
            INSERT INTO memory_items (
                agent_id, agent_type, content, memory_type, memory_tier,
                importance, related_agents, created_at, updated_at
            ) VALUES (
                'shared_source',
                'athena',
                '跨智能体共享测试_{shared_timestamp}',
                'knowledge',
                'eternal',
                1.0,
                ARRAY['athena', 'xiaona', 'yunxi', 'xiaochen', 'xiaonuo'],
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            RETURNING id;
            """

            cmd = [
                PSQL_PATH, '-h', DB_HOST, '-p', str(DB_PORT),
                '-d', DB_NAME, '-c', sql
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.log_result("共享记忆创建", True)

                # 验证所有智能体能访问
                agents = ['athena', 'xiaona', 'yunxi', 'xiaochen', 'xiaonuo']
                all_can_see = True

                for agent in agents:
                    verify_sql = f"""
                    SELECT COUNT(*) FROM memory_items
                    WHERE content = '跨智能体共享测试_{shared_timestamp}'
                    AND '{agent}' = ANY(related_agents);
                    """

                    verify_cmd = [
                        PSQL_PATH, '-h', DB_HOST, '-p', str(DB_PORT),
                        '-d', DB_NAME, '-c', verify_sql
                    ]

                    verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)

                    if verify_result.returncode == 0:
                        lines = verify_result.stdout.strip().split('\n')
                        if len(lines) >= 3:
                            try:
                                count = int(lines[2].strip())
                                if count == 0:
                                    all_can_see = False
                                    print(f"    ⚠️ {agent} 无法访问")
                                    break
                            except:
                                all_can_see = False
                                break

                if all_can_see:
                    self.log_result("跨智能体共享", True, "所有智能体都能访问")
                else:
                    self.log_result("跨智能体共享", False, "部分智能体无法访问")
            else:
                self.log_result("共享记忆创建", False, result.stderr)

        except Exception as e:
            self.log_result("跨智能体共享", False, str(e))

    async def run_tests(self):
        """运行所有测试"""
        print("\n🧪 快速验证测试...")
        print("=" * 60)

        await self.test_json_compatibility()
        self.test_shared_memory()

        # 总结
        total = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / max(total, 1)) * 100

        print("\n" + "=" * 60)
        print(f"✅ 通过: {self.test_results['passed']}")
        print(f"❌ 失败: {self.test_results['failed']}")
        print(f"📈 成功率: {success_rate:.1f}%")

        if self.test_results['failed'] == 0:
            print("\n🎉 所有测试通过！问题已修复。")
        else:
            print("\n⚠️ 仍有问题需要解决。")

async def main():
    tester = QuickVerificationTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())