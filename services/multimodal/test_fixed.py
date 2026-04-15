#!/usr/bin/env python3
"""
Athena多模态文件系统 - 完整功能测试脚本
Complete Functional Test Script for Athena Multimodal File System

测试内容：
1. 服务连接测试
2. 文件上传测试
3. 文件列表查询测试
4. 文件信息查询测试
5. 统计信息测试
6. 文件删除测试

Author: Athena Team
Date: 2026-02-24
Version: 2.1.0
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import requests
from PIL import Image, ImageDraw, ImageFont

# ==================== 配置 ====================
SERVICE_URL = "http://localhost:8021"
TIMEOUT = 10

# ==================== 工具函数 ====================
def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_success(message: str):
    """打印成功消息"""
    print(f"✅ {message}")

def print_error(message: str):
    """打印错误消息"""
    print(f"❌ {message}")

def print_info(message: str):
    """打印信息消息"""
    print(f"ℹ️  {message}")

def create_test_image(size=(400, 300), text="测试图片", color="white"):
    """创建测试图片"""
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)

    # 绘制边框
    draw.rectangle([10, 10, size[0]-10, size[1]-10], outline="blue", width=3)

    # 绘制文本
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except Exception:
        font = ImageFont.load_default()

    # 获取文本边界
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 居中绘制文本
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(position, text, fill="black", font=font)

    return img

def create_test_document(content: str = "这是测试文档内容"):
    """创建测试文本文档"""
    return content.encode('utf-8')

# ==================== 测试类 ====================
class MultimodalServiceTester:
    """多模态服务测试器"""

    def __init__(self, base_url: str = SERVICE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_file_id = None

    def test_health_check(self) -> bool:
        """测试健康检查"""
        print_section("1. 健康检查测试")

        try:
            response = self.session.get(f"{self.base_url}/health", timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "healthy":
                print_success("健康检查通过")
                print(f"   版本: {data.get('version')}")
                print(f"   端口: {data.get('port')}")
                print(f"   存储: {data.get('storage')}")
                print(f"   运行时间: {data.get('uptime', 0):.1f}秒")
                return True
            else:
                print_error("健康状态异常")
                return False

        except Exception as e:
            print_error(f"健康检查失败: {e}")
            return False

    def test_root_endpoint(self) -> bool:
        """测试根端点"""
        print_section("2. 根端点测试")

        try:
            response = self.session.get(f"{self.base_url}/", timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            print_success("根端点访问成功")
            print(f"   服务: {data.get('service')}")
            print(f"   版本: {data.get('version')}")
            print(f"   状态: {data.get('status')}")

            features = data.get('features', [])
            if features:
                print(f"   功能数量: {len(features)}")

            return True

        except Exception as e:
            print_error(f"根端点测试失败: {e}")
            return False

    def test_file_upload(self) -> bool:
        """测试文件上传"""
        print_section("3. 文件上传测试")

        # 创建测试图片
        print_info("创建测试图片...")
        img = create_test_image(text="测试上传", color="lightblue")

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            img.save(temp_path)

        try:
            print_info("上传测试图片...")
            with open(temp_path, 'rb') as f:
                files = {'file': ('test_upload.png', f, 'image/png')}
                data = {
                    'tags': 'test,upload,automated',
                    'category': 'test'
                }
                response = self.session.post(
                    f"{self.base_url}/api/files/upload",
                    files=files,
                    data=data,
                    timeout=TIMEOUT
                )

            response.raise_for_status()
            result = response.json()

            if result.get('success'):
                self.test_file_id = result.get('file_id')
                print_success("文件上传成功")
                print(f"   文件ID: {self.test_file_id}")
                print(f"   原始文件名: {result.get('filename')}")
                print(f"   文件类型: {result.get('file_type')}")
                print(f"   文件大小: {result.get('file_size')} 字节")
                return True
            else:
                print_error(f"上传失败: {result.get('message')}")
                return False

        except Exception as e:
            print_error(f"文件上传测试失败: {e}")
            return False

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_list(self) -> bool:
        """测试文件列表"""
        print_section("4. 文件列表测试")

        try:
            response = self.session.get(
                f"{self.base_url}/api/files/list",
                params={'page': 1, 'page_size': 10},
                timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                print_success("文件列表获取成功")
                files = data.get('files', [])
                total = data.get('total', 0)

                print(f"   总文件数: {total}")
                print(f"   当前页文件数: {len(files)}")

                if files:
                    print("   最新文件:")
                    for i, f in enumerate(files[:3], 1):
                        print(f"     {i}. {f.get('original_filename')} - {f.get('file_type')}")

                return True
            else:
                print_error("获取文件列表失败")
                return False

        except Exception as e:
            print_error(f"文件列表测试失败: {e}")
            return False

    def test_file_info(self) -> bool:
        """测试文件信息查询"""
        print_section("5. 文件信息查询测试")

        if not self.test_file_id:
            print_info("跳过（没有可用的测试文件）")
            return True

        try:
            response = self.session.get(
                f"{self.base_url}/api/files/{self.test_file_id}",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                file_info = data.get('file', {})
                print_success("文件信息获取成功")
                print(f"   文件ID: {file_info.get('id')}")
                print(f"   原始文件名: {file_info.get('original_filename')}")
                print(f"   文件类型: {file_info.get('file_type')}")
                print(f"   文件大小: {file_info.get('file_size_formatted')}")
                print(f"   上传时间: {file_info.get('upload_time')}")
                print(f"   已处理: {file_info.get('processed')}")
                print(f"   标签: {file_info.get('tags')}")
                return True
            else:
                print_error("获取文件信息失败")
                return False

        except Exception as e:
            print_error(f"文件信息查询测试失败: {e}")
            return False

    def test_statistics(self) -> bool:
        """测试统计信息"""
        print_section("6. 统计信息测试")

        try:
            response = self.session.get(
                f"{self.base_url}/api/stats",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                print_success("统计信息获取成功")
                print(f"   总文件数: {data.get('total_files')}")
                print(f"   总大小: {data.get('total_size')} 字节")
                print(f"   已处理文件: {data.get('processed_files')}")
                print(f"   处理率: {data.get('processing_rate', 0):.1f}%")

                by_type = data.get('by_type', {})
                if by_type:
                    print("   按类型统计:")
                    for file_type, stats in by_type.items():
                        print(f"     {file_type}: {stats.get('count')} 个文件")

                return True
            else:
                print_error("获取统计信息失败")
                return False

        except Exception as e:
            print_error(f"统计信息测试失败: {e}")
            return False

    def test_file_delete(self) -> bool:
        """测试文件删除"""
        print_section("7. 文件删除测试")

        if not self.test_file_id:
            print_info("跳过（没有可用的测试文件）")
            return True

        try:
            response = self.session.delete(
                f"{self.base_url}/api/files/{self.test_file_id}",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                print_success("文件删除成功")
                print(f"   已删除文件ID: {self.test_file_id}")
                self.test_file_id = None
                return True
            else:
                print_error("文件删除失败")
                return False

        except Exception as e:
            print_error(f"文件删除测试失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("  🧪 Athena多模态文件系统 - 完整功能测试")
        print("=" * 60)
        print(f"📍 服务地址: {self.base_url}")
        print(f"⏱️  超时设置: {TIMEOUT}秒")
        print("=" * 60)

        start_time = time.time()

        # 执行测试
        tests = [
            ("健康检查", self.test_health_check),
            ("根端点", self.test_root_endpoint),
            ("文件上传", self.test_file_upload),
            ("文件列表", self.test_file_list),
            ("文件信息", self.test_file_info),
            ("统计信息", self.test_statistics),
            ("文件删除", self.test_file_delete),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print_error(f"{test_name}测试异常: {e}")
                results.append((test_name, False))

            # 测试之间稍作等待
            time.sleep(0.5)

        # 汇总结果
        elapsed = time.time() - start_time
        print_section("测试结果汇总")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status}  {test_name}")

        print("\n" + "=" * 60)
        print(f"📊 测试统计: {passed}/{total} 通过")
        print(f"⏱️  总耗时: {elapsed:.2f}秒")
        print("=" * 60)

        if passed == total:
            print("\n🎉 所有测试通过！")
            return 0
        else:
            print(f"\n⚠️  {total - passed} 个测试失败")
            return 1

# ==================== 主函数 ====================
def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Athena多模态文件系统测试")
    parser.add_argument(
        "--url",
        default=SERVICE_URL,
        help="服务URL地址"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT,
        help="请求超时时间（秒）"
    )

    args = parser.parse_args()

    # 检查服务是否运行
    print(f"🔍 检查服务状态: {args.url}")
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务运行中\n")
        else:
            print(f"⚠️  服务响应异常: {response.status_code}\n")
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}\n")
        print("💡 请先启动服务:")
        print("   bash services/multimodal/start_fixed.sh start\n")
        return 1

    # 运行测试
    tester = MultimodalServiceTester(base_url=args.url)
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
