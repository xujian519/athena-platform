#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务指标集成示例 - Business Metrics Integration Examples
展示如何在认知与决策模块中集成业务指标装饰器

作者: Athena Platform Team
版本: v1.0
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.monitoring.business_metrics import (
    track_patent_analysis,
    track_intent_recognition,
    track_user_interaction,
    track_reasoning_quality,
    business_metrics,
    update_business_metrics
)


# ============== 示例1: 专利分析服务集成 ==============

@track_patent_analysis(analysis_type='similarity')
def analyze_patent_similarity(patent_id: str, compare_with: list[str]):
    """
    分析专利相似度（集成业务指标）

    自动记录:
    - 请求计数 (成功/失败)
    - 处理延迟
    - 质量评分
    """
    # 模拟专利相似度分析
    print(f"🔍 分析专利 {patent_id} 的相似度...")

    # 模拟处理
    similar_patents = []
    for compare_id in compare_with:
        # 模拟相似度计算
        similarity = hash(compare_id) % 100 / 100
        if similarity > 0.5:
            similar_patents.append({
                'patent_id': compare_id,
                'similarity': similarity
            })

    # 计算质量评分（基于结果数量和质量）
    quality_score = min(100, len(similar_patents) * 20 + 60)

    return {
        'patent_id': patent_id,
        'similar_patents': similar_patents,
        'quality_score': quality_score  # 会被自动记录到指标
    }


@track_patent_analysis(analysis_type='invalidation')
def analyze_patent_invalidation(patent_id: str):
    """
    分析专利无效性（集成业务指标）
    """
    print(f"⚖️ 分析专利 {patent_id} 的无效性...")

    # 模拟无效性分析
    invalidation_risks = [
        {'type': 'novelty', 'risk': 0.3},
        {'type': 'creative_step', 'risk': 0.5},
        {'type': 'prior_art', 'risk': 0.2}
    ]

    # 计算综合风险评分
    quality_score = int((1 - sum(r['risk'] for r in invalidation_risks) / 3) * 100)

    return {
        'patent_id': patent_id,
        'invalidation_risks': invalidation_risks,
        'quality_score': quality_score
    }


# ============== 示例2: 意图识别集成 ==============

@track_intent_recognition(model_type='bge-m3')
def classify_user_query(query: str):
    """
    分类用户查询意图（集成业务指标）

    自动记录:
    - 意图类型
    - 置信度级别
    - 处理延迟
    - 意图分布
    """
    print(f"🤔 分类查询: {query}")

    # 简单的规则分类（实际应使用模型）
    query_lower = query.lower()

    if '专利' in query or '检索' in query:
        intent = 'patent_search'
        confidence = 0.92
    elif '分析' in query or '评估' in query:
        intent = 'patent_analysis'
        confidence = 0.88
    elif '决策' in query or '选择' in query:
        intent = 'decision_support'
        confidence = 0.85
    else:
        intent = 'general_query'
        confidence = 0.70

    return {
        'intent': intent,
        'confidence': confidence,
        'query': query
    }


# ============== 示例3: 用户交互追踪 ==============

@track_user_interaction(interaction_type='query_response')
async def handle_user_query(user_id: str, query: str):
    """
    处理用户查询（集成业务指标）

    自动记录:
    - 响应延迟
    - 用户满意度（如果有）
    """
    print(f"💬 用户 {user_id} 查询: {query}")

    # 模拟查询处理
    response = f"关于 '{query}' 的处理结果..."

    # 可以添加满意度评分
    satisfaction = 8.5  # 从用户反馈获取

    return {
        'response': response,
        'satisfaction': satisfaction,  # 会被自动记录
        'user_id': user_id
    }


# ============== 示例4: 推理质量追踪 ==============

@track_reasoning_quality(reasoning_mode='deep')
async def perform_deep_reasoning(problem: str, context: dict = None):
    """
    执行深度推理（集成业务指标）

    自动记录:
    - 推理步骤数
    - 质量评分
    - 采纳率
    """
    print(f"🧠 深度推理: {problem}")

    # 模拟推理步骤
    reasoning_steps = [
        "问题分解",
        "假设生成",
        "证据收集",
        "逻辑推理",
        "结论生成"
    ]

    # 计算指标
    quality_score = 85
    adoption_rate = 0.82

    return {
        'problem': problem,
        'steps': len(reasoning_steps),
        'reasoning_trace': reasoning_steps,
        'quality_score': quality_score,
        'adoption_rate': adoption_rate
    }


# ============== 示例5: 手动记录业务指标 ==============

def record_patent_retrieval_metrics():
    """手动记录专利检索指标"""
    print("📊 记录专利检索指标...")

    # 方式1: 使用business_metrics实例
    business_metrics.record_patent_retrieval(
        search_type='semantic',
        total=100,
        found=87
    )

    # 方式2: 使用便捷函数
    update_business_metrics({
        'patent_analysis': {
            'search_type': 'keyword',
            'total': 50,
            'found': 32
        }
    })


def record_decision_quality_metrics():
    """记录决策质量指标"""
    print("📊 记录决策质量指标...")

    business_metrics.record_decision_metrics(
        decision_type='route_selection',
        accuracy=0.92,
        impact_score=78.0,
        adoption_rate=0.88
    )


def record_model_performance():
    """记录模型性能指标"""
    print("📊 记录模型性能指标...")

    business_metrics.record_model_metrics(
        model_name='intent_classifier_v2',
        accuracy=0.91,
        loss=0.23,
        loss_type='cross_entropy'
    )


def record_knowledge_graph_stats():
    """记录知识图谱统计"""
    print("📊 记录知识图谱统计...")

    business_metrics.record_kg_stats(
        graph_type='patent_knowledge',
        nodes=15234,
        edges=45621
    )


def record_learning_progress():
    """记录学习进度"""
    print("📊 记录学习进度...")

    business_metrics.record_learning_progress(
        sample_type='patent_documents',
        samples=1000,
        convergence_rate=0.85
    )


# ============== 示例6: 综合服务集成示例 ==============

class PatentAnalysisService:
    """专利分析服务（完整集成示例）"""

    def __init__(self):
        self.service_name = "patent_analysis_service"

    @track_patent_analysis(analysis_type='comprehensive')
    def comprehensive_analysis(self, patent_id: str) -> dict:
        """综合分析"""
        print(f"🔬 执行综合分析: {patent_id}")

        # 执行多种分析
        similarity_result = self._analyze_similarity(patent_id)
        invalidation_result = self._analyze_invalidation(patent_id)
        value_result = self._analyze_value(patent_id)

        # 计算综合质量评分
        quality_score = int((
            similarity_result['score'] * 0.4 +
            invalidation_result['score'] * 0.3 +
            value_result['score'] * 0.3
        ))

        return {
            'patent_id': patent_id,
            'similarity': similarity_result,
            'invalidation': invalidation_result,
            'value': value_result,
            'quality_score': quality_score
        }

    def _analyze_similarity(self, patent_id: str):
        # 模拟相似度分析
        return {'score': 85}

    def _analyze_invalidation(self, patent_id: str):
        # 模拟无效性分析
        return {'score': 78}

    def _analyze_value(self, patent_id: str):
        # 模拟价值评估
        return {'score': 82}

    @track_patent_analysis(analysis_type='batch')
    def batch_analyze(self, patent_ids: list[str]) -> dict:
        """批量分析"""
        print(f"📦 批量分析 {len(patent_ids)} 个专利")

        results = []
        for pid in patent_ids:
            result = self.comprehensive_analysis(pid)
            results.append(result)

        # 批量质量评分
        avg_quality = sum(r['quality_score'] for r in results) / len(results)

        return {
            'count': len(patent_ids),
            'results': results,
            'quality_score': avg_quality
        }


# ============== 测试函数 ==============

async def main():
    """主测试函数"""
    print("=" * 60)
    print("📊 业务指标集成示例测试")
    print("=" * 60)

    # 1. 专利分析示例
    print("\n1️⃣  专利分析示例")
    result1 = analyze_patent_similarity(
        "CN123456789A",
        ["CN987654321A", "CN112233445A", "CN998877665A"]
    )
    print(f"✅ 结果: {len(result1['similar_patents'])} 个相似专利")

    # 2. 无效性分析示例
    print("\n2️⃣  无效性分析示例")
    result2 = analyze_patent_invalidation("CN123456789A")
    print(f"✅ 质量评分: {result2['quality_score']}")

    # 3. 意图识别示例
    print("\n3️⃣  意图识别示例")
    result3 = classify_user_query("帮我检索相关专利")
    print(f"✅ 意图: {result3['intent']}, 置信度: {result3['confidence']}")

    # 4. 用户交互示例
    print("\n4️⃣  用户交互示例")
    result4 = await handle_user_query("user123", "如何分析专利价值？")
    print(f"✅ 满意度: {result4['satisfaction']}")

    # 5. 深度推理示例
    print("\n5️⃣  深度推理示例")
    result5 = await perform_deep_reasoning("选择最佳技术方案")
    print(f"✅ 推理步骤: {result5['steps']}, 质量: {result5['quality_score']}")

    # 6. 手动记录指标示例
    print("\n6️⃣  手动记录指标")
    record_patent_retrieval_metrics()
    record_decision_quality_metrics()
    record_model_performance()
    record_knowledge_graph_stats()
    record_learning_progress()
    print("✅ 所有指标已记录")

    # 7. 综合服务示例
    print("\n7️⃣  综合服务示例")
    service = PatentAnalysisService()
    result7 = service.comprehensive_analysis("CN123456789A")
    print(f"✅ 综合质量评分: {result7['quality_score']}")

    print("\n" + "=" * 60)
    print("✅ 所有示例执行完成！")
    print("📊 访问 http://localhost:9100/metrics 查看指标")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
