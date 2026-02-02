#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的GraphRAG流水线
Test full GraphRAG pipeline
"""

import json
import logging
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_parsing():
    """测试PDF解析"""
    logger.info(str("\n" + '='*60))
    logger.info('第一步：PDF解析测试')
    logger.info(str('='*60))

    from src.parsers.pdf_parser import PatentGuidelineParser

    pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '专利审查指南（最新版）.pdf')

    if not os.path.exists(pdf_path):
        logger.info(f"❌ PDF文件不存在: {pdf_path}")
        return False

    try:
        parser = PatentGuidelineParser(pdf_path)
        data = parser.parse()

        # 保存解析结果
        output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed', 'test_parse_result.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 解析成功！")
        logger.info(f"   文档标题: {data['document_info']['title']}")
        logger.info(f"   总页数: {data['document_info']['total_pages']}")
        logger.info(f"   章节数: {data['document_info']['total_sections']}")
        logger.info(f"   引用数: {len(data['references'])}")
        logger.info(f"   结果已保存到: {output_path}")

        return True

    except Exception as e:
        logger.info(f"❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vectorization():
    """测试向量化"""
    logger.info(str("\n" + '='*60))
    logger.info('第二步：向量化测试')
    logger.info(str('='*60))

    from src.vectorization.embedder import PatentGuidelineEmbedder

    try:
        # 加载解析数据
        json_path = '/Users/xujian/Athena工作平台/patent_guideline_system/data/processed/test_parse_result.json'
        if not os.path.exists(json_path):
            logger.info(f"❌ 解析数据不存在，请先运行解析")
            return False

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 创建向量化器
        embedder = PatentGuidelineEmbedder()

        # 选择部分章节进行测试
        test_sections = data['structure'][:10]  # 只处理前10个章节

        logger.info(f"开始向量化 {len(test_sections)} 个章节...")
        embedded_sections = embedder.embed_sections(test_sections)

        # 保存向量化结果
        output_path = '/Users/xujian/Athena工作平台/patent_guideline_system/data/embeddings/test_embeddings.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        embedder.save_embeddings(embedded_sections, output_path)

        logger.info(f"✅ 向量化成功！")
        logger.info(f"   处理章节数: {len(embedded_sections)}")
        logger.info(f"   向量维度: {1024}")
        logger.info(f"   结果已保存到: {output_path}")

        # 显示示例
        logger.info("\n向量化示例：")
        for i, section in enumerate(embedded_sections[:3], 1):
            metadata = section['metadata']
            logger.info(f"\n{i}. [{metadata.get('section_number', 'N/A')}] {metadata.get('section_title', '无标题')}")
            logger.info(f"   关键词: {metadata.get('keywords', [])}")
            logger.info(f"   概念: {metadata.get('concepts', [])}")
            logger.info(f"   向量预览: {section['vector'][:5]}...")

        return True

    except Exception as e:
        logger.info(f"❌ 向量化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_neo4j_import():
    """测试Neo4j导入"""
    logger.info(str("\n" + '='*60))
    logger.info('第三步：Neo4j知识图谱导入测试')
    logger.info(str('='*60))

    from scripts.import_to_neo4j import GuidelineImporter

    try:
        json_path = '/Users/xujian/Athena工作平台/patent_guideline_system/data/processed/test_parse_result.json'
        if not os.path.exists(json_path):
            logger.info(f"❌ 解析数据不存在，请先运行解析")
            return False

        # 创建导入器
        importer = GuidelineImporter()

        # 执行导入
        importer.import_from_json(json_path)

        logger.info(f"✅ 导入成功！")
        logger.info(f"   导入的概念数: {len(importer.concept_cache)}")
        logger.info(f"   导入的法条数: {len(importer.law_cache)}")
        logger.info(f"   导入的案例数: {len(importer.case_cache)}")

        # 验证导入
        with importer.schema_manager.session as session:
            # 统计节点数
            result = session.run('MATCH (n) RETURN COUNT(n) as count')
            node_count = result.single()['count']
            logger.info(f"   总节点数: {node_count}")

            # 统计关系数
            result = session.run('MATCH ()-[r]->() RETURN COUNT(r) as count')
            rel_count = result.single()['count']
            logger.info(f"   总关系数: {rel_count}")

        importer.close()
        return True

    except Exception as e:
        logger.info(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graphrag_retrieval():
    """测试GraphRAG检索"""
    logger.info(str("\n" + '='*60))
    logger.info('第四步：GraphRAG检索测试')
    logger.info(str('='*60))

    try:
        from src.retrieval.graphrag_retriever import GraphRAGRetriever

        # 创建检索器
        retriever = GraphRAGRetriever()

        # 测试查询
        test_queries = [
            '什么是专利的新颖性？',
            '创造性的判断标准是什么？',
            '哪些情况会被驳回？',
            '如何申请专利？'
        ]

        for query in test_queries:
            logger.info(f"\n查询: {query}")
            logger.info(str('-' * 50))

            # 执行检索
            results = retriever.search(
                query=query,
                top_k=3,
                use_vector=True,
                use_graph=True,
                use_bm25=True,
                alpha=0.5
            )

            # 显示结果
            logger.info(f"找到 {len(results['combined_results'])} 个结果")

            for i, result in enumerate(results['combined_results'][:3], 1):
                logger.info(f"\n{i}. 相关度: {result['final_score']:.3f}")
                logger.info(f"   向量分数: {result['vector_score']:.3f}")
                logger.info(f"   图分数: {result['graph_score']:.3f}")
                logger.info(f"   BM25分数: {result['bm25_score']:.3f}")

                metadata = result.get('metadata', {})
                if metadata.get('title'):
                    logger.info(f"   标题: {metadata['title']}")

                content = result.get('content', '')
                if content:
                    preview = content[:150].replace('\n', ' ')
                    logger.info(f"   预览: {preview}...")

                # 获取解释
                explanation = retriever.get_explanation(query, result)
                logger.info(f"   {explanation}")

        retriever.close()
        logger.info("\n✅ GraphRAG检索测试成功！")
        return True

    except Exception as e:
        logger.info(f"❌ GraphRAG检索失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dynamic_prompt_generation():
    """测试动态提示词生成"""
    logger.info(str("\n" + '='*60))
    logger.info('第五步：动态提示词生成测试')
    logger.info(str('='*60))

    try:
        from src.retrieval.graphrag_retriever import GraphRAGRetriever

        retriever = GraphRAGRetriever()

        # 模拟用户问题
        user_question = '我的发明是一种新的电池技术，请问我需要满足哪些条件才能获得专利？'

        logger.info(f"用户问题: {user_question}\n")

        # 1. 检索相关规则
        logger.info('1. 检索相关审查指南...')
        results = retriever.search(
            query=user_question,
            top_k=5,
            use_vector=True,
            use_graph=True,
            use_bm25=True
        )

        # 2. 提取关键信息
        logger.info("\n2. 提取关键规则...")
        relevant_rules = []
        for result in results['combined_results'][:3]:
            metadata = result.get('metadata', {})
            rule_info = {
                'section': metadata.get('section_title', ''),
                'content': result.get('content', '')[:300],
                'relevance': result['final_score']
            }
            relevant_rules.append(rule_info)
            logger.info(f"   - {metadata.get('section_title', '')} (相关度: {result['final_score']:.3f})")

        # 3. 生成动态提示词
        logger.info("\n3. 生成动态提示词...")
        prompt_template = f"""你是一位专业的专利审查员，请基于以下审查指南规则回答用户的问题。

用户问题：{user_question}

相关审查指南：
{chr(10).join([f"{i+1}. {rule['section']}: {rule['content'][:200]}..." for i, rule in enumerate(relevant_rules)])}

请根据上述规则，为用户提供专业、准确的解答。
"""

        logger.info("\n动态提示词：")
        logger.info(str('-' * 50))
        logger.info(str(prompt_template[:500] + '...'))
        logger.info(str('-' * 50))

        retriever.close()
        logger.info("\n✅ 动态提示词生成测试成功！")
        return True

    except Exception as e:
        logger.info(f"❌ 动态提示词生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("\n🚀 专利审查指南GraphRAG系统 - 端到端测试")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试步骤
    test_steps = [
        ('PDF解析', test_parsing),
        ('向量化', test_vectorization),
        ('Neo4j导入', test_neo4j_import),
        ('GraphRAG检索', test_graphrag_retrieval),
        ('动态提示词生成', test_dynamic_prompt_generation)
    ]

    # 执行测试
    passed = 0
    failed = 0

    for step_name, test_func in test_steps:
        logger.info(f"\n{'='*60}")
        logger.info(f"执行测试: {step_name}")
        logger.info(f"{'='*60}")

        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {step_name} - 通过")
            else:
                failed += 1
                logger.info(f"❌ {step_name} - 失败")
        except Exception as e:
            failed += 1
            logger.info(f"❌ {step_name} - 异常: {e}")

    # 测试总结
    logger.info(f"\n{'='*60}")
    logger.info('测试总结')
    logger.info(f"{'='*60}")
    logger.info(f"总测试数: {passed + failed}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")

    if failed == 0:
        logger.info("\n🎉 所有测试通过！GraphRAG系统已成功部署。")
        logger.info("\n系统功能：")
        logger.info('1. ✅ PDF文档解析和结构化')
        logger.info('2. ✅ 中文文本向量化（BGE-Large-ZH-v1.5）')
        logger.info('3. ✅ 知识图谱构建（Neo4j）')
        logger.info('4. ✅ GraphRAG混合检索')
        logger.info('5. ✅ 动态提示词生成')
        logger.info("\n下一步：")
        logger.info('1. 将审查指南集成到专利检索系统')
        logger.info('2. 执行性能优化任务（连接真实数据、专业模型集成、缓存和并行处理）')
    else:
        logger.info("\n⚠️ 部分测试失败，请检查错误信息并修复问题。")

if __name__ == '__main__':
    main()