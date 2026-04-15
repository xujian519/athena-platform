#!/usr/bin/env python3
"""
多模态系统集成测试
Multimodal System Integration Test

测试统一存储架构与API网关的集成
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from storage_manager import MultimodalStorageManager, ProcessingStatus


class IntegrationTester:
    """集成测试器"""

    def __init__(self):
        self.api_base_url = "http://localhost:8090"
        self.test_results = []
        self.temp_files = []

    def log_result(self, test_name: str, success: bool, message: str, duration: float = 0) -> Any:
        """记录测试结果"""
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })

        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message} ({duration:.2f}s)")

    async def test_storage_manager(self):
        """测试存储管理器"""
        print("\n🔧 测试存储管理器")
        print("=" * 50)

        # 创建测试文件
        start_time = time.time()
        try:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(b"fake image data for testing")
                test_file_path = f.name

            self.temp_files.append(test_file_path)

            # 初始化存储管理器
            storage = MultimodalStorageManager()

            # 测试存储文件
            file_id = await storage.store_file(
                source_path=test_file_path,
                original_filename="test_image.jpg",
                mime_type="image/jpeg"
            )

            if file_id:
                self.log_result(
                    "存储文件",
                    True,
                    f"成功存储文件，ID: {file_id}",
                    time.time() - start_time
                )

                # 测试更新状态
                start_time = time.time()
                await storage.update_processing_status(
                    file_id=file_id,
                    status=ProcessingStatus.COMPLETED,
                    result={"extracted_text": "测试图片", "confidence": 0.95}
                )

                self.log_result(
                    "更新处理状态",
                    True,
                    "成功更新处理状态",
                    time.time() - start_time
                )

                # 测试获取文件信息
                start_time = time.time()
                file_info = await storage.get_file_info(file_id)

                if file_info:
                    self.log_result(
                        "获取文件信息",
                        True,
                        f"成功获取文件信息: {file_info['original_filename']}",
                        time.time() - start_time
                    )
                else:
                    self.log_result(
                        "获取文件信息",
                        False,
                        "未能获取文件信息",
                        time.time() - start_time
                    )

                # 测试存储向量（模拟）
                start_time = time.time()
                vector = [0.1] * 768  # 模拟向量
                vector_id = await storage.store_file_vector(
                    file_id=file_id,
                    vector=vector,
                    vector_metadata={"test": True}
                )

                if vector_id:
                    self.log_result(
                        "存储向量",
                        True,
                        f"成功存储向量，ID: {vector_id}",
                        time.time() - start_time
                    )
                else:
                    self.log_result(
                        "存储向量",
                        False,
                        "向量存储失败（可能是Qdrant未启动）",
                        time.time() - start_time
                    )

                # 测试统计信息
                start_time = time.time()
                stats = await storage.get_statistics()

                self.log_result(
                    "获取统计信息",
                    True,
                    f"系统统计: {stats.get('total_files', 0)} 个文件",
                    time.time() - start_time
                )
            else:
                self.log_result(
                    "存储文件",
                    False,
                    "文件存储失败",
                    time.time() - start_time
                )

        except Exception as e:
            self.log_result(
                "存储管理器测试",
                False,
                f"测试异常: {str(e)}",
                time.time() - start_time
            )

    async def test_api_gateway(self):
        """测试API网关"""
        print("\n🌐 测试API网关")
        print("=" * 50)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 测试健康检查
            start_time = time.time()
            try:
                response = await client.get(f"{self.api_base_url}/api/health")
                if response.status_code == 200:
                    health_data = response.json()
                    self.log_result(
                        "健康检查",
                        True,
                        f"服务状态: {health_data.get('status', 'unknown')}",
                        time.time() - start_time
                    )
                else:
                    self.log_result(
                        "健康检查",
                        False,
                        f"HTTP错误: {response.status_code}",
                        time.time() - start_time
                    )
            except Exception as e:
                self.log_result(
                    "健康检查",
                    False,
                    f"连接失败: {str(e)}",
                    time.time() - start_time
                )

            # 测试文件上传
            start_time = time.time()
            try:
                with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                    f.write(b"This is a test document for OCR recognition.")
                    test_file_path = f.name

                self.temp_files.append(test_file_path)

                with open(test_file_path, 'rb') as f:
                    files = {'file': ('test.txt', f, 'text/plain')}
                    data = {
                        'priority': 'normal',
                        'sensitivity': 'public',
                        'high_quality': True
                    }

                    response = await client.post(
                        f"{self.api_base_url}/api/process",
                        files=files,
                        data=data
                    )

                if response.status_code == 200:
                    result = response.json()
                    self.log_result(
                        "文件上传处理",
                        True,
                        f"处理成功，文件ID: {result.get('file_id')}, 方法: {result.get('method_used')}",
                        time.time() - start_time
                    )

                    # 等待处理完成
                    file_id = result.get('file_id')
                    if file_id:
                        await self.check_processing_status(client, file_id)
                else:
                    self.log_result(
                        "文件上传处理",
                        False,
                        f"处理失败: {response.text}",
                        time.time() - start_time
                    )

            except Exception as e:
                self.log_result(
                    "文件上传处理",
                    False,
                    f"上传异常: {str(e)}",
                    time.time() - start_time
                )

            # 测试统计信息API
            start_time = time.time()
            try:
                response = await client.get(f"{self.api_base_url}/api/statistics")
                if response.status_code == 200:
                    stats = response.json()
                    self.log_result(
                        "统计信息API",
                        True,
                        f"获取统计成功: {stats.get('statistics', {}).get('total_files', 0)} 个文件",
                        time.time() - start_time
                    )
                else:
                    self.log_result(
                        "统计信息API",
                        False,
                        f"HTTP错误: {response.status_code}",
                        time.time() - start_time
                    )
            except Exception as e:
                self.log_result(
                    "统计信息API",
                    False,
                    f"请求异常: {str(e)}",
                    time.time() - start_time
                )

            # 测试向量搜索API
            start_time = time.time()
            try:
                response = await client.get(
                    f"{self.api_base_url}/api/search/vector",
                    params={"query": "测试文档", "limit": 5}
                )
                if response.status_code == 200:
                    search_result = response.json()
                    self.log_result(
                        "向量搜索API",
                        True,
                        f"搜索成功，找到 {len(search_result.get('results', []))} 个结果",
                        time.time() - start_time
                    )
                else:
                    self.log_result(
                        "向量搜索API",
                        False,
                        f"HTTP错误: {response.status_code}",
                        time.time() - start_time
                    )
            except Exception as e:
                self.log_result(
                    "向量搜索API",
                    False,
                    f"搜索异常: {str(e)}",
                    time.time() - start_time
                )

    async def check_processing_status(self, client: httpx.AsyncClient, file_id: int):
        """检查处理状态"""
        max_wait = 30  # 最多等待30秒
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = await client.get(f"{self.api_base_url}/api/file/{file_id}")
                if response.status_code == 200:
                    file_info = response.json()
                    status = file_info.get('processing_status')

                    if status == 'completed':
                        self.log_result(
                            "后台处理完成",
                            True,
                            f"文件处理成功，耗时: {time.time() - start_time:.2f}s",
                            time.time() - start_time
                        )
                        return True
                    elif status == 'failed':
                        error = file_info.get('error_message', '未知错误')
                        self.log_result(
                            "后台处理失败",
                            False,
                            f"文件处理失败: {error}",
                            time.time() - start_time
                        )
                        return False
                    else:
                        # 继续等待
                        await asyncio.sleep(2)
                else:
                    self.log_result(
                        "检查处理状态",
                        False,
                        f"无法获取文件信息: {response.status_code}",
                        time.time() - start_time
                    )
                    return False

            except Exception as e:
                self.log_result(
                    "检查处理状态",
                    False,
                    f"状态检查异常: {str(e)}",
                    time.time() - start_time
                )
                return False

        # 超时
        self.log_result(
            "后台处理",
            False,
            "处理超时",
            time.time() - start_time
        )
        return False

    async def cleanup(self):
        """清理测试文件"""
        print("\n🧹 清理测试文件")
        print("=" * 50)

        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"已删除: {file_path}")
            except Exception as e:
                print(f"删除失败 {file_path}: {str(e)}")

    def generate_report(self) -> Any:
        """生成测试报告"""
        print("\n📊 测试报告")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests / total_tests * 100):.1f}%")

        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")

        # 保存详细报告
        report_path = "integration_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": passed_tests / total_tests * 100,
                    "timestamp": datetime.now().isoformat()
                },
                "details": self.test_results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n📝 详细报告已保存到: {report_path}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始多模态系统集成测试")
        print("=" * 50)
        print(f"API地址: {self.api_base_url}")
        print(f"测试时间: {datetime.now().isoformat()}")
        print("=" * 50)

        try:
            # 测试存储管理器
            await self.test_storage_manager()

            # 测试API网关
            await self.test_api_gateway()

            # 生成报告
            self.generate_report()

        finally:
            # 清理
            await self.cleanup()

async def main():
    """主函数"""
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
