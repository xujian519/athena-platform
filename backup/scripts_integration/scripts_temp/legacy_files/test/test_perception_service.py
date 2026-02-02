#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试感知服务
"""

import json
import logging
import time

import requests

logger = logging.getLogger(__name__)

# 服务地址
BASE_URL = 'http://localhost:8009'

def test_health():
    """测试健康检查"""
    logger.info('🏥 测试健康检查...')
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        logger.info(f"✅ 健康检查: {response.json()}")
        return True
    else:
        logger.info(f"❌ 健康检查失败: {response.status_code}")
        return False

def test_status():
    """测试服务状态"""
    logger.info("\n📊 测试服务状态...")
    response = requests.get(f"{BASE_URL}/status")
    if response.status_code == 200:
        status = response.json()
        logger.info(f"✅ 服务状态:")
        logger.info(f"  - 状态: {status['status']}")
        logger.info(f"  - 处理器数量: {status['processor_count']}")
        logger.info(f"  - 可用处理器: {status['available_processors']}")
        logger.info(f"  - 优化启用: {status['optimization_enabled']}")
        logger.info(f"  - 监控启用: {status['monitoring_enabled']}")
        return True
    else:
        logger.info(f"❌ 服务状态检查失败: {response.status_code}")
        return False

def test_text_processing():
    """测试文本处理"""
    logger.info("\n📝 测试文本处理...")
    data = {
        'text': '这是一个专利技术描述，包含创新点和保护范围。',
        'options': {}
    }

    response = requests.post(f"{BASE_URL}/process/text", json=data)
    if response.status_code == 200:
        result = response.json()
        logger.info(f"✅ 文本处理成功:")
        logger.info(f"  - 输入类型: {result['input_type']}")
        logger.info(f"  - 置信度: {result['confidence']}")
        logger.info(f"  - 处理时间: {result['processing_time']}")
        logger.info(f"  - 特征数量: {len(result['features'])}")
        return True
    else:
        logger.info(f"❌ 文本处理失败: {response.status_code}")
        try:
            error = response.json()
            logger.info(f"  错误信息: {error}")
        except:
            logger.info(f"  错误信息: {response.text}")
        return False

def test_multimodal_processing():
    """测试多模态处理"""
    logger.info("\n🎭 测试多模态处理...")
    data = {
        'data': {
            'text': '专利技术文本',
            'image': 'base64_encoded_image',
            'table': {'rows': 5, 'columns': 3}
        },
        'options': {}
    }

    response = requests.post(f"{BASE_URL}/process/multimodal", json=data)
    if response.status_code == 200:
        result = response.json()
        logger.info(f"✅ 多模态处理成功:")
        logger.info(f"  - 输入类型: {result['input_type']}")
        logger.info(f"  - 置信度: {result['confidence']}")
        logger.info(f"  - 处理时间: {result['processing_time']}")
        logger.info(f"  - 特征数量: {len(result['features'])}")
        return True
    else:
        logger.info(f"❌ 多模态处理失败: {response.status_code}")
        try:
            error = response.json()
            logger.info(f"  错误信息: {error}")
        except:
            logger.info(f"  错误信息: {response.text}")
        return False

def test_batch_processing():
    """测试批量处理"""
    logger.info("\n📦 测试批量处理...")
    data = {
        'items': [
            {'input_type': 'text', 'data': '第一个测试文本'},
            {'input_type': 'text', 'data': '第二个测试文本'},
            {'input_type': 'text', 'data': '第三个测试文本'}
        ],
        'options': {}
    }

    response = requests.post(f"{BASE_URL}/process/batch", json=data)
    if response.status_code == 200:
        results = response.json()
        logger.info(f"✅ 批量处理成功:")
        logger.info(f"  - 处理项目数: {len(results)}")
        logger.info(f"  - 成功处理: {sum(1 for r in results if r['success'])}")
        logger.info(f"  - 失败处理: {sum(1 for r in results if not r['success'])}")
        for i, result in enumerate(results[:3]):  # 显示前3个结果
            logger.info(f"  - 项目{i+1}: 置信度={result['confidence']:.2f}")
        return True
    else:
        logger.info(f"❌ 批量处理失败: {response.status_code}")
        try:
            error = response.json()
            logger.info(f"  错误信息: {error}")
        except:
            logger.info(f"  错误信息: {response.text}")
        return False

def test_performance_dashboard():
    """测试性能仪表板"""
    logger.info("\n📊 测试性能仪表板...")
    response = requests.get(f"{BASE_URL}/performance/dashboard")
    if response.status_code == 200:
        dashboard = response.json()
        logger.info(f"✅ 性能仪表板:")
        logger.info(f"  - 引擎状态: {dashboard.get('engine_status', {}).get('initialized', False)}")
        logger.info(f"  - 优化状态: {bool(dashboard.get('optimization_status'))}")
        logger.info(f"  - 监控状态: {bool(dashboard.get('monitoring_dashboard'))}")
        return True
    else:
        logger.info(f"❌ 性能仪表板获取失败: {response.status_code}")
        return False

def main():
    """主测试函数"""
    logger.info('🧪 测试Athena增强感知服务')
    logger.info(str('=' * 50))

    # 等待服务启动
    logger.info('⏳ 等待服务启动...')
    time.sleep(2)

    # 运行测试
    tests = [
        test_health,
        test_status,
        test_text_processing,
        test_multimodal_processing,
        test_batch_processing,
        test_performance_dashboard
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            logger.info(f"❌ 测试异常: {e}")

    logger.info(str("\n" + '=' * 50))
    logger.info(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        logger.info('🎉 所有测试通过！感知服务运行正常！')
        logger.info("\n🌐 服务访问地址:")
        logger.info(f"  - 🧠 感知服务: {BASE_URL}")
        logger.info(f"  - 📚 API文档: {BASE_URL}/docs")
        logger.info(f"  - 🏥 健康检查: {BASE_URL}/health")
        logger.info(f"  - 📊 服务状态: {BASE_URL}/status")
        logger.info("\n💡 感知服务特性:")
        logger.info('  - ✅ 智能缓存机制')
        logger.info('  - ✅ 批量并发处理')
        logger.info('  - ✅ 错误重试与降级')
        logger.info('  - ✅ 实时性能监控')
        logger.info('  - ✅ 多模态融合处理')
        logger.info('  - ✅ 跨模态推理分析')
    else:
        logger.info(f"⚠️  {total - passed} 个测试失败")

    return passed == total

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)