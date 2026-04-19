#!/usr/bin/env python3
"""
Rust缓存性能验证脚本

测试真实场景下的缓存命中率和性能
"""

import sys
import time
import random
import string
from pathlib import Path

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from athena_cache import TieredCache

print("=" * 70)
print("🔍 Rust缓存 - 性能验证测试")
print("=" * 70)

# 创建缓存实例
llm_cache = TieredCache(hot_size=10000, warm_size=100000)
search_cache = TieredCache(hot_size=5000, warm_size=50000)

# ==================== 测试1: LLM缓存场景 ====================

print("\n[测试1] LLM缓存命中率测试")
print("-" * 70)

# 模拟100个常见问题
common_questions = [
    "什么是专利法？",
    "如何申请专利？",
    "专利保护期限是多久？",
    "发明专利的实质条件是什么？",
    "实用新型和发明的区别？",
    "外观设计专利怎么申请？",
    "专利侵权如何判定？",
    "专利申请流程是什么？",
    "专利费用是多少？",
    "国际专利申请怎么办？"
]

# 预生成一些响应
for question in common_questions:
    response = f"这是关于'{question}'的专业回答..."
    llm_cache.put(question, response)

# 测试缓存命中率
print("执行100次查询（包含重复问题）...")
start = time.time()

hits = 0
misses = 0

for i in range(100):
    # 70%概率问常见问题，30%随机问题
    if random.random() < 0.7:
        question = random.choice(common_questions)
    else:
        question = f"随机问题{i}: {''.join(random.choices(string.ascii_letters + string.digits, k=20))}"

    result = llm_cache.get(question)
    if result is not None:
        hits += 1
    else:
        misses += 1
        # 存入缓存
        response = f"这是关于'{question}'的回答..."
        llm_cache.put(question, response)

duration = time.time() - start
hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0

print(f"✅ 测试完成")
print(f"   总查询: {hits + misses}")
print(f"   缓存命中: {hits}")
print(f"   缓存未命中: {misses}")
print(f"   命中率: {hit_rate:.2%}")
print(f"   耗时: {duration*1000:.2f}ms")
print(f"   QPS: {(hits + misses)/duration:,.0f} requests/s")

# ==================== 测试2: 搜索缓存场景 ====================

print("\n[测试2] 搜索缓存命中率测试")
print("-" * 70)

# 模拟常见搜索查询
common_searches = [
    "机器学习专利",
    "人工智能算法",
    "深度学习模型",
    "神经网络架构",
    "自然语言处理",
    "计算机视觉",
    "数据挖掘技术",
    "知识图谱构建",
]

# 预生成搜索结果
for query in common_searches:
    results = [{"id": f"CN{random.randint(100000, 999999)}", "title": f"{query}相关专利", "score": random.uniform(0.8, 0.95)}]
    search_cache.put(query, str(results))

# 测试缓存命中率
print("执行100次搜索（包含重复查询）...")
start = time.time()

hits = 0
misses = 0

for i in range(100):
    # 60%概率搜常见查询，40%随机查询
    if random.random() < 0.6:
        query = random.choice(common_searches)
    else:
        query = f"随机搜索{i}: {''.join(random.choices(string.ascii_letters + string.digits, k=10))}"

    result = search_cache.get(query)
    if result is not None:
        hits += 1
    else:
        misses += 1
        # 存入缓存
        results = [{"id": f"CN{random.randint(100000, 999999)}", "title": f"{query}相关专利", "score": random.uniform(0.8, 0.95)}]
        search_cache.put(query, str(results))

duration = time.time() - start
hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0

print(f"✅ 测试完成")
print(f"   总搜索: {hits + misses}")
print(f"   缓存命中: {hits}")
print(f"   缓存未命中: {misses}")
print(f"   命中率: {hit_rate:.2%}")
print(f"   耗时: {duration*1000:.2f}ms")
print(f"   QPS: {(hits + misses)/duration:,.0f} requests/s")

# ==================== 测试3: 混合场景 ====================

print("\n[测试3] 混合场景测试")
print("-" * 70)

# 模拟实际使用场景：读写混合
print("执行1000次混合操作（70%读，30%写）...")
start = time.time()

for i in range(1000):
    if i < 700:  # 读操作
        if random.random() < 0.5:
            question = random.choice(common_questions)
            result = llm_cache.get(question)
        else:
            query = random.choice(common_searches)
            result = search_cache.get(query)
    else:  # 写操作
        if random.random() < 0.5:
            question = f"新问题{i}"
            response = f"这是关于'{question}'的回答..."
            llm_cache.put(question, response)
        else:
            query = f"新搜索{i}"
            results = [{"id": f"CN{random.randint(100000, 999999)}", "title": f"{query}相关专利", "score": random.uniform(0.8, 0.95)}]
            search_cache.put(query, str(results))

duration = time.time() - start

print(f"✅ 测试完成")
print(f"   总操作: 1000")
print(f"   耗时: {duration*1000:.2f}ms")
print(f"   QPS: {1000/duration:,.0f} operations/s")

# ==================== 总结 ====================

print("\n" + "=" * 70)
print("✅ 性能验证测试完成！")
print("=" * 70)

print("\n📊 性能总结:")
print(f"  LLM缓存命中率: {hit_rate:.2%} (测试1)")
print(f"  搜索缓存命中率: 类似表现 (测试2)")
print(f"  混合场景QPS: {1000/duration:,.0f} ops/s (测试3)")

print("\n💡 优化建议:")
if hit_rate > 0.6:
    print("  ✅ 命中率良好，当前配置合适")
elif hit_rate > 0.4:
    print("  ⚠️  命中率中等，可适当增加缓存大小")
else:
    print("  ❌ 命中率偏低，建议增加warm_size配置")

print("\n🚀 生产环境建议:")
print("  1. 根据实际负载调整hot_size和warm_size")
print("  2. 监控Prometheus指标: curl http://localhost:8000/metrics")
print("  3. 配置Grafana仪表板查看实时数据")
print("  4. 设置告警规则（命中率 < 50%时告警）")
