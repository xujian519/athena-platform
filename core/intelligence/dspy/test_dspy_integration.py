#!/usr/bin/env python3
from __future__ import annotations
"""
DSPy集成测试脚本
DSPy Integration Test Script for Athena Platform

测试DSPy与Athena平台各组件的集成:
1. LLM后端 (GLM/DeepSeek)
2. 向量检索 (Qdrant)
3. 知识图谱检索 (NebulaGraph)
4. 混合提示词生成器

作者: 小娜·天秤女神
创建时间: 2025-12-29
版本: 1.0.0
"""

import logging
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path("/Users/xujian/Athena工作平台")
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_dspy_installation() -> Any:
    """测试1: 验证DSPy安装"""
    logger.info("=" * 60)
    logger.info("测试1: 验证DSPy安装")
    logger.info("=" * 60)

    try:
        import dspy

        logger.info(f"✅ DSPy导入成功,版本: {dspy.__version__}")
        logger.info(f"DSPy安装路径: {dspy.__file__}")
        return True
    except ImportError as e:
        logger.error(f"❌ DSPy导入失败: {e}")
        return False


def test_llm_backend() -> Any:
    """测试2: LLM后端集成"""
    logger.info("=" * 60)
    logger.info("测试2: LLM后端集成 (AthenaLLMDirect)")
    logger.info("=" * 60)

    try:
        from core.intelligence.dspy.llm_backend import (
            ATHENA_LLM_AVAILABLE,
            get_athena_llm_client,
        )

        logger.info("✅ LLM后端模块导入成功")
        logger.info(f"Athena LLM可用: {ATHENA_LLM_AVAILABLE}")

        # 创建LLM客户端实例
        llm_client = get_athena_llm_client(model_type="patent_analysis")
        logger.info("✅ AthenaLLMDirect实例创建成功")

        # 测试直接LLM调用
        test_prompt = "什么是专利?请简要回答。"
        logger.info(f"发送测试提示词: {test_prompt}")

        try:
            response = llm_client.generate(test_prompt)
            logger.info("✅ LLM调用成功")
            logger.info(f"提示词: {test_prompt}")
            logger.info(f"响应: {response[:200]}...")

            return True

        except Exception as e:
            logger.warning(f"⚠️ LLM调用失败(可能需要LLM服务运行): {e}")
            logger.info("提示: 请确保Athena LLM服务正在运行")
            return False

    except Exception as e:
        logger.error(f"❌ LLM后端测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_vector_retriever() -> Any:
    """测试3: 向量检索器"""
    logger.info("=" * 60)
    logger.info("测试3: 向量检索器 (AthenaVectorRetriever)")
    logger.info("=" * 60)

    try:
        from core.intelligence.dspy.retrievers import AthenaVectorRetriever

        # 创建向量检索器
        retriever = AthenaVectorRetriever(k=3)
        logger.info("✅ AthenaVectorRetriever实例创建成功")

        # 测试检索
        test_query = "专利的新颖性判断标准"
        logger.info(f"执行测试查询: {test_query}")

        try:
            results = retriever(test_query)
            logger.info(f"✅ 向量检索成功,返回 {len(results)} 个结果")

            for i, result in enumerate(results):
                logger.info(f"  结果{i+1}: {result.text[:50]}...")

            return True

        except Exception as e:
            logger.warning(f"⚠️ 向量检索失败(可能需要Qdrant服务运行): {e}")
            logger.info("提示: 请确保Qdrant服务正在运行")
            return False

    except Exception as e:
        logger.error(f"❌ 向量检索器测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_graph_retriever() -> Any:
    """测试4: 知识图谱检索器"""
    logger.info("=" * 60)
    logger.info("测试4: 知识图谱检索器 (AthenaGraphRetriever)")
    logger.info("=" * 60)

    try:
        from core.intelligence.dspy.retrievers import AthenaGraphRetriever

        # 创建图谱检索器
        retriever = AthenaGraphRetriever(k=3)
        logger.info("✅ AthenaGraphRetriever实例创建成功")

        # 测试检索
        test_query = "专利法中的创造性标准"
        logger.info(f"执行测试查询: {test_query}")

        try:
            results = retriever(test_query)
            logger.info(f"✅ 图谱检索成功,返回 {len(results)} 个结果")

            for i, result in enumerate(results):
                logger.info(f"  结果{i+1}: {result.text[:50]}...")

            return True

        except Exception as e:
            logger.warning(f"⚠️ 图谱检索失败(可能需要NebulaGraph服务运行): {e}")
            logger.info("提示: 请确保NebulaGraph服务正在运行")
            return False

    except Exception as e:
        logger.error(f"❌ 图谱检索器测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_hybrid_generator() -> Any:
    """测试5: 混合提示词生成器"""
    logger.info("=" * 60)
    logger.info("测试5: 混合提示词生成器 (DSPyHybridPromptGenerator)")
    logger.info("=" * 60)

    try:
        from core.intelligence.dspy.hybrid_generator import (
            DSPyHybridPromptGenerator,
            HybridPromptConfig,
        )

        # 创建配置
        config = HybridPromptConfig(
            use_dspy_optimization=False,  # 先不启用DSPy优化
            base_prompt_layer="L3",
            fallback_to_base=True,
        )

        # 创建生成器
        generator = DSPyHybridPromptGenerator(config)
        logger.info("✅ DSPyHybridPromptGenerator实例创建成功")
        logger.info(f"DSPy启用: {generator.dspy_enabled}")
        logger.info(f"Athena可用: {generator.athena_available}")

        # 测试提示词生成
        test_input = "请分析这个专利案情的创造性"
        logger.info(f"生成提示词,输入: {test_input}")

        try:
            prompt = generator.generate_prompt(
                user_input=test_input,
                task_type="capability_2",
                layer="L3",
                use_dspy=False,  # 先不使用DSPy
            )

            logger.info("✅ 提示词生成成功")
            logger.info(f"生成的提示词长度: {len(prompt)} 字符")
            logger.info(f"提示词预览: {prompt[:200]}...")

            return True

        except Exception as e:
            logger.warning(f"⚠️ 提示词生成失败: {e}")
            return False

    except Exception as e:
        logger.error(f"❌ 混合提示词生成器测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_dspy_with_retrieval() -> Any:
    """测试6: DSPy RAG管道"""
    logger.info("=" * 60)
    logger.info("测试6: DSPy RAG管道 (检索增强生成)")
    logger.info("=" * 60)

    try:
        import dspy

        from core.intelligence.dspy.llm_backend import create_athena_module
        from core.intelligence.dspy.retrievers import AthenaVectorRetriever

        # 定义RAG Signature
        class RAGSignature(dspy.Signature):
            """基于上下文回答问题"""

            context = dspy.InputField(desc="检索到的上下文")
            question = dspy.InputField(desc="用户问题")
            answer = dspy.OutputField(desc="基于上下文的答案")

        # 创建RAG程序
        class RAGProgram(dspy.Module):
            def __init__(self):
                super().__init__()
                self.retrieve = AthenaVectorRetriever(k=3)
                # 使用Athena LLM模块
                self.generate = create_athena_module(RAGSignature, model_type="patent_analysis")

            def forward(self, question) -> None:
                # 检索相关上下文
                context = self.retrieve(question)
                context_text = "\n".join([c.text for c in context])

                # 生成答案
                if not context_text:
                    context_text = "未找到相关上下文"

                prediction = self.generate(context=context_text, question=question)
                return dspy.Prediction(
                    context=context_text,
                    answer=prediction.answer if hasattr(prediction, "answer") else str(prediction),
                )

        # 创建RAG程序实例
        rag = RAGProgram()
        logger.info("✅ RAG程序创建成功")

        # 测试RAG
        test_question = "什么是专利的创造性?"
        logger.info(f"执行RAG测试,问题: {test_question}")

        try:
            result = rag(question=test_question)
            logger.info("✅ RAG执行成功")
            logger.info(f"问题: {test_question}")
            logger.info(f"上下文: {result.context[:100]}...")
            logger.info(
                f"答案: {result.answer[:200] if hasattr(result, 'answer') else str(result)[:200]}"
            )

            return True

        except Exception as e:
            logger.warning(f"⚠️ RAG执行失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"❌ RAG测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main() -> None:
    """主测试函数"""
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 10 + "DSPy集成测试套件" + " " * 30 + "║")
    logger.info("║" + " " * 5 + "Athena Platform DSPy Integration Tests" + " " * 17 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("")

    results = {}

    # 执行所有测试
    tests = [
        ("DSPy安装验证", test_dspy_installation),
        ("LLM后端集成", test_llm_backend),
        ("向量检索器", test_vector_retriever),
        ("知识图谱检索器", test_graph_retriever),
        ("混合提示词生成器", test_hybrid_generator),
        ("DSPy RAG管道", test_dspy_with_retrieval),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result

            if result:
                passed += 1
                logger.info(f"✅ {test_name}: 通过")
            else:
                failed += 1
                logger.warning(f"⚠️ {test_name}: 失败")

        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_name}: 异常 - {e}")
            results[test_name] = False

        logger.info("")

    # 打印总结
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"总计: {len(tests)} 个测试")
    logger.info(f"通过: {passed} ✅")
    logger.info(f"失败: {failed} ❌")
    logger.info(f"跳过: {skipped} ⏭️")
    logger.info(f"成功率: {(passed/len(tests)*100):.1f}%")
    logger.info("")

    # 详细结果
    logger.info("详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")

    logger.info("")
    logger.info("=" * 60)

    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
