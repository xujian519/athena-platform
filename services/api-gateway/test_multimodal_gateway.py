#!/usr/bin/env python3
"""
Athena Gateway - 多模态文件处理系统集成测试
Test Multimodal File Processing System Integration via Gateway
"""

import asyncio
import logging

import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultimodalGatewayTester:
    """多模态网关集成测试器"""

    def __init__(self, gateway_url: str = "http://localhost:8081"):
        self.gateway_url = gateway_url
        self.test_file_id = None
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_gateway_health(self) -> bool:
        """测试网关健康状态"""
        try:
            url = f"{self.gateway_url}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 网关健康检查通过: {data.get('status')}")
                    return True
                else:
                    logger.error(f"❌ 网关健康检查失败: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ 网关健康检查异常: {e}")
            return False

    async def test_multimodal_health_via_gateway(self) -> bool:
        """通过网关测试多模态服务健康状态"""
        try:
            url = f"{self.gateway_url}/api/v1/multimodal/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 多模态服务健康检查通过: {data.get('status')}")
                    logger.info(f"   版本: {data.get('multimodal_service', {}).get('version')}")
                    return True
                else:
                    logger.error(f"❌ 多模态服务健康检查失败: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ 多模态服务健康检查异常: {e}")
            return False

    async def test_file_upload_via_gateway(self) -> bool:
        """通过网关测试文件上传"""
        try:
            # 创建测试图片内容 (1x1 PNG)
            test_image_data = (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0'
                b'\x00\x00\x00\x03\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
            )

            url = f"{self.gateway_url}/api/v1/multimodal/upload"

            # 准备表单数据
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                test_image_data,
                filename='test_gateway.png',
                content_type='image/png'
            )
            form_data.add_field('tags', 'test,gateway')
            form_data.add_field('category', 'test')

            async with self.session.post(url, data=form_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        self.test_file_id = data.get('file_id')
                        logger.info(f"✅ 文件上传成功: {self.test_file_id}")
                        logger.info(f"   文件名: {data.get('filename')}")
                        logger.info(f"   大小: {data.get('file_size')} bytes")
                        return True
                    else:
                        logger.error(f"❌ 文件上传失败: {data.get('message')}")
                        return False
                else:
                    logger.error(f"❌ 文件上传失败: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ 文件上传异常: {e}")
            return False

    async def test_file_list_via_gateway(self) -> bool:
        """通过网关测试文件列表"""
        try:
            url = f"{self.gateway_url}/api/v1/multimodal/files?limit=5"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 文件列表获取成功，共 {data.get('total', 0)} 个文件")
                    return True
                else:
                    logger.error(f"❌ 文件列表获取失败: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ 文件列表获取异常: {e}")
            return False

    async def test_file_stats_via_gateway(self) -> bool:
        """通过网关测试统计信息"""
        try:
            url = f"{self.gateway_url}/api/v1/multimodal/stats"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ 统计信息获取成功")
                    logger.info(f"   总文件数: {data.get('total_files', 0)}")
                    logger.info(f"   总大小: {data.get('total_size', 0)} bytes")
                    return True
                else:
                    logger.error(f"❌ 统计信息获取失败: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ 统计信息获取异常: {e}")
            return False

    async def test_file_delete_via_gateway(self) -> bool:
        """通过网关测试文件删除"""
        if not self.test_file_id:
            logger.warning("⚠️ 没有可删除的文件ID")
            return False

        try:
            url = f"{self.gateway_url}/api/v1/multimodal/files/{self.test_file_id}"
            async with self.session.delete(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        logger.info(f"✅ 文件删除成功: {self.test_file_id}")
                        return True
                    else:
                        logger.error(f"❌ 文件删除失败: {data.get('message')}")
                        return False
                else:
                    logger.error(f"❌ 文件删除失败: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ 文件删除异常: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始多模态文件处理系统 - 网关集成测试")
        logger.info("=" * 60)
        logger.info("")

        results = {}

        # 测试1: 网关健康检查
        logger.info("【测试1】网关健康检查")
        results['gateway_health'] = await self.test_gateway_health()
        logger.info("")

        # 测试2: 多模态服务健康检查
        logger.info("【测试2】多模态服务健康检查（通过网关）")
        results['multimodal_health'] = await self.test_multimodal_health_via_gateway()
        logger.info("")

        # 测试3: 文件上传
        logger.info("【测试3】文件上传（通过网关）")
        results['file_upload'] = await self.test_file_upload_via_gateway()
        logger.info("")

        # 测试4: 文件列表
        logger.info("【测试4】文件列表（通过网关）")
        results['file_list'] = await self.test_file_list_via_gateway()
        logger.info("")

        # 测试5: 统计信息
        logger.info("【测试5】统计信息（通过网关）")
        results['file_stats'] = await self.test_file_stats_via_gateway()
        logger.info("")

        # 测试6: 文件删除
        logger.info("【测试6】文件删除（通过网关）")
        results['file_delete'] = await self.test_file_delete_via_gateway()
        logger.info("")

        # 打印测试结果汇总
        logger.info("=" * 60)
        logger.info("测试结果汇总")
        logger.info("=" * 60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")

        logger.info("")
        logger.info(f"总计: {passed}/{total} 测试通过")

        if passed == total:
            logger.info("🎉 所有测试通过！网关集成成功！")
        else:
            logger.warning(f"⚠️ {total - passed} 个测试失败")

        logger.info("=" * 60)

        return passed == total


async def main():
    """主函数"""
    async with MultimodalGatewayTester() as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
