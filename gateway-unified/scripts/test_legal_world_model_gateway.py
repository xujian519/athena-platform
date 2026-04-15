#!/usr/bin/env python3
"""
法律世界模型Gateway接入测试脚本
Test Legal World Model Service Gateway Integration

测试法律世界模型服务是否成功接入Gateway

用法:
    python test_legal_world_model_gateway.py

作者: Athena平台团队
版本: 1.0.0
"""

import sys

import requests

# =============================================================================
# 配置
# =============================================================================

GATEWAY_BASE_URL = "http://localhost:8005"
LEGAL_WORLD_MODEL_DIRECT_URL = "http://localhost:8020"


# =============================================================================
# 测试函数
# =============================================================================

def print_section(title: str):
    """打印测试章节标题"""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()


def test_gateway_health() -> bool:
    """测试Gateway健康状态"""
    print_section("测试1: Gateway健康检查")

    try:
        response = requests.get(f"{GATEWAY_BASE_URL}/health", timeout=5)
        data = response.json()

        print(f"✅ Gateway状态: {data.get('status', 'UNKNOWN')}")
        print(f"   实例数: {data.get('instances', 0)}")
        print(f"   路由数: {data.get('routes', 0)}")

        return response.status_code == 200
    except Exception as e:
        print(f"❌ Gateway健康检查失败: {e}")
        return False


def test_service_registration() -> bool:
    """测试服务注册状态"""
    print_section("测试2: 服务注册状态")

    try:
        response = requests.get(f"{GATEWAY_BASE_URL}/api/services/instances", timeout=5)
        data = response.json()

        if not data.get("success"):
            print("❌ 查询服务实例失败")
            return False

        instances = data.get("data", [])
        lwm_instances = [i for i in instances if i.get("service_name") == "legal-world-model"]

        if not lwm_instances:
            print("❌ 未找到法律世界模型服务实例")
            return False

        print(f"✅ 找到 {len(lwm_instances)} 个法律世界模型服务实例:")
        for inst in lwm_instances:
            print(f"   - ID: {inst.get('id')}")
            print(f"     地址: {inst.get('host')}:{inst.get('port')}")
            print(f"     状态: {inst.get('status')}")
            print(f"     权重: {inst.get('weight')}")

        return True

    except Exception as e:
        print(f"❌ 服务注册检查失败: {e}")
        return False


def test_routes() -> bool:
    """测试路由配置"""
    print_section("测试3: 路由配置检查")

    try:
        response = requests.get(f"{GATEWAY_BASE_URL}/api/routes", timeout=5)
        data = response.json()

        if not data.get("success"):
            print("❌ 查询路由失败")
            return False

        routes = data.get("data", [])
        lwm_routes = [r for r in routes if r.get("target_service") == "legal-world-model"]

        if not lwm_routes:
            print("❌ 未找到法律世界模型路由")
            return False

        print(f"✅ 找到 {len(lwm_routes)} 条法律世界模型路由:")
        for route in lwm_routes:
            print(f"   - {route.get('methods')} {route.get('path')}")

        return True

    except Exception as e:
        print(f"❌ 路由检查失败: {e}")
        return False


def test_dependencies() -> bool:
    """测试服务依赖"""
    print_section("测试4: 服务依赖检查")

    try:
        response = requests.get(
            f"{GATEWAY_BASE_URL}/api/dependencies/legal-world-model",
            timeout=5
        )
        data = response.json()

        if not data.get("success"):
            print("⚠️  未设置服务依赖")
            return True  # 依赖不是必需的

        dep_data = data.get("data", {})
        depends_on = dep_data.get("dependencies", [])

        print(f"✅ 服务依赖: {', '.join(depends_on) if depends_on else '无'}")

        return True

    except Exception as e:
        print(f"⚠️  依赖检查失败（可能未设置）: {e}")
        return True  # 依赖不是必需的


def test_health_routing() -> bool:
    """测试健康检查路由"""
    print_section("测试5: 健康检查路由")

    # 通过Gateway访问
    try:
        response = requests.get(
            f"{GATEWAY_BASE_URL}/api/legal-world-model/health",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Gateway健康检查路由成功")
            print(f"   状态: {data.get('overall_status', 'UNKNOWN')}")
            print(f"   Neo4j: {data.get('components', {}).get('neo4j', {}).get('status', 'UNKNOWN')}")
            print(f"   PostgreSQL: {data.get('components', {}).get('postgres', {}).get('status', 'UNKNOWN')}")
            return True
        else:
            print(f"❌ Gateway健康检查路由失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Gateway健康检查路由异常: {e}")
        return False


def test_scenarios_routing() -> bool:
    """测试场景列表路由"""
    print_section("测试6: 场景列表路由")

    # 通过Gateway访问
    try:
        response = requests.get(
            f"{GATEWAY_BASE_URL}/api/legal-world-model/v1/scenarios",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            scenarios = data.get("scenarios", {})
            print("✅ Gateway场景列表路由成功")
            print(f"   领域数: {data.get('total_domains', 0)}")

            for domain, task_types in list(scenarios.items())[:3]:
                print(f"   - {domain}: {len(task_types)} 个场景")

            return True
        else:
            print(f"❌ Gateway场景列表路由失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Gateway场景列表路由异常: {e}")
        return False


def test_generate_prompt_routing() -> bool:
    """测试生成提示词路由"""
    print_section("测试7: 生成提示词路由")

    # 通过Gateway访问
    try:
        payload = {
            "business_context": "请帮我分析一个生物技术专利的创造性",
            "user_domain": "patent",
            "max_rules": 5
        }

        response = requests.post(
            f"{GATEWAY_BASE_URL}/api/legal-world-model/v1/generate-prompt",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            prompt = data.get("prompt", "")
            print("✅ Gateway生成提示词路由成功")
            print(f"   提示词长度: {len(prompt)} 字符")
            print(f"   匹配规则: {len(data.get('matched_rules', []))} 条")

            # 打印提示词片段
            if prompt:
                lines = prompt.split('\n')
                print("   提示词预览:")
                for line in lines[:5]:
                    if line.strip():
                        print(f"     {line.strip()[:60]}...")

            return True
        else:
            print(f"❌ Gateway生成提示词路由失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Gateway生成提示词路由异常: {e}")
        return False


def test_direct_service() -> bool:
    """测试直接访问服务（对比）"""
    print_section("测试8: 直接访问服务（对比验证）")

    try:
        # 直接访问健康检查
        response = requests.get(
            f"{LEGAL_WORLD_MODEL_DIRECT_URL}/health",
            timeout=5
        )

        if response.status_code == 200:
            print("✅ 直接访问服务成功")
            print("   这证明服务本身运行正常")
            return True
        else:
            print(f"❌ 直接访问服务失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 直接访问服务异常: {e}")
        return False


# =============================================================================
# 主函数
# =============================================================================

def main():
    print()
    print("=" * 60)
    print("  法律世界模型Gateway接入测试")
    print("  Legal World Model Service Gateway Integration Test")
    print("=" * 60)
    print()
    print(f"Gateway地址: {GATEWAY_BASE_URL}")
    print(f"服务地址: {LEGAL_WORLD_MODEL_DIRECT_URL}")
    print()

    # 执行所有测试
    tests = [
        ("Gateway健康检查", test_gateway_health),
        ("服务注册状态", test_service_registration),
        ("路由配置检查", test_routes),
        ("服务依赖检查", test_dependencies),
        ("健康检查路由", test_health_routing),
        ("场景列表路由", test_scenarios_routing),
        ("生成提示词路由", test_generate_prompt_routing),
        ("直接访问服务", test_direct_service),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 测试异常: {name} - {e}")
            results.append((name, False))

    # 汇总结果
    print_section("测试结果汇总")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print()
    print(f"总计: {passed}/{total} 通过")

    if passed == total:
        print()
        print("🎉 所有测试通过！法律世界模型服务已成功接入Gateway！")
        print()
        return 0
    else:
        print()
        print("⚠️  部分测试失败，请检查服务配置")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
