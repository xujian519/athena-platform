#!/usr/bin/env python3
from __future__ import annotations
"""
法律写作素材库管理器 - 数据库版本
Legal Writing Materials Manager - Database Version

利用平台已有的数据库基础设施(PostgreSQL + Qdrant + Neo4j)检索素材,
然后从'/Users/xujian/语料'文件夹获取全文内容。

架构:
1. 通过RAG管理器(Qdrant)进行语义检索
2. 根据检索结果的元数据定位全文文件
3. 从语料文件夹读取完整文档内容
4. 返回写作示例供LLM参考
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WritingMaterialsManagerDB:
    """
    法律写作素材库管理器 - 数据库版本

    功能:
    1. 利用RAG管理器进行语义检索
    2. 从语料文件夹获取全文内容
    3. 提供写作示例增强提示词
    """

    def __init__(self, rag_manager=None, materials_path: Path | None = None):
        """
        初始化素材库管理器

        Args:
            rag_manager: RAG管理器(用于检索)
            materials_path: 素材路径(默认为/Users/xujian/语料)
        """
        self.rag_manager = rag_manager

        if materials_path is None:
            materials_path = Path("/Users/xujian/语料")

        self.materials_path = materials_path

        # 子路径映射(用于根据文档类型定位文件)
        self.collection_paths = {
            "patent_judgments": materials_path / "专利判决",
            "case_data_1024": materials_path / "判决文书",
            "patent_rules_1024": materials_path / "司法解释",
            "patent_legal": materials_path / "Laws-1.0.0",
            # 无效复审决定可能需要单独处理
        }

        logger.info("✅ 写作素材库管理器初始化完成(数据库版本)")
        logger.info(f"   素材路径: {self.materials_path}")
        logger.info(f"   RAG管理器: {'已配置' if rag_manager else '未配置'}")

    async def search_relevant_examples(
        self, topic: str, section: str, role: str = "scholar", top_k: int = 3
    ) -> list[dict[str, str]]:
        """
        搜索相关的写作示例

        Args:
            topic: 主题
            section: 章节名称
            role: 写作角色
            top_k: 返回数量

        Returns:
            相关示例列表,每个包含title、source、content
        """
        examples = []

        if not self.rag_manager:
            logger.warning("RAG管理器未配置,无法检索素材")
            return examples

        try:
            # 1. 根据角色选择任务类型
            task_type = self._role_to_task_type(role)

            # 2. 使用RAG进行语义检索
            search_query = f"{topic} {section}"
            rag_context = await self.rag_manager.retrieve(query=search_query, task_type=task_type)

            # 3. 获取检索结果
            retrieval_results = rag_context.get_top_results(top_k * 2)  # 多检索一些,然后筛选

            # 4. 根据检索结果获取全文内容
            for result in retrieval_results[:top_k]:
                full_content = self._get_full_content(result)

                if full_content and len(full_content) > 200:  # 至少200字
                    examples.append(
                        {
                            "title": result.metadata.get("title", result.source),
                            "source": result.source,
                            "content": (
                                full_content[:1500] + "..."
                                if len(full_content) > 1500
                                else full_content
                            ),
                            "relevance_score": result.score,
                        }
                    )

                if len(examples) >= top_k:
                    break

            logger.info(f"   找到 {len(examples)} 个相关示例")

        except Exception as e:
            logger.warning(f"   检索写作示例失败: {e}")

        return examples

    def _role_to_task_type(self, role: str) -> str:
        """
        将写作角色映射到RAG任务类型

        Args:
            role: 写作角色

        Returns:
            任务类型
        """
        role_task_map = {
            "patent_attorney": "oa_response",  # 专利代理师 -> OA答复
            "lawyer": "tech_analysis",  # 律师 -> 技术分析
            "judge": "patent_search",  # 法官 -> 专利检索
            "scholar": "creativity_analysis",  # 学者 -> 创造性分析
        }
        return role_task_map.get(role, "default")

    def _get_full_content(self, retrieval_result: Any) -> Optional[str]:
        """
        根据检索结果获取全文内容

        Args:
            retrieval_result: 检索结果对象

        Returns:
            文档全文(如果找到)
        """
        metadata = getattr(retrieval_result, "metadata", {})
        source = getattr(retrieval_result, "source", "")

        # 1. 尝试从元数据中获取文件路径
        file_path = metadata.get("file_path") or metadata.get("source_file")

        if file_path:
            full_path = self.materials_path / file_path
            if full_path.exists():
                return self._read_file_content(full_path)

        # 2. 尝试根据source推断路径
        for collection_name, collection_path in self.collection_paths.items():
            if collection_name in source:
                # 在该目录下搜索
                if collection_path.exists():
                    # 尝试根据元数据中的标题或ID查找文件
                    filename = self._infer_filename(metadata)
                    if filename:
                        potential_path = collection_path / filename
                        if potential_path.exists():
                            return self._read_file_content(potential_path)

        # 3. 如果直接在metadata中有内容,直接使用
        content = metadata.get("content") or metadata.get("text")
        if content:
            return content

        return None

    def _infer_filename(self, metadata: dict[str, Any]) -> Optional[str]:
        """
        根据元数据推断文件名

        Args:
            metadata: 元数据字典

        Returns:
            推断的文件名
        """
        # 尝试多种可能的文件名字段
        possible_fields = ["filename", "file_name", "decision_id", "case_id", "document_id"]

        for field in possible_fields:
            value = metadata.get(field)
            if value:
                # 如果没有扩展名,尝试添加
                if not Path(value).suffix:
                    # 尝试常见的扩展名
                    for ext in [".md", ".txt", ".json"]:
                        test_path = value + ext
                        return test_path
                return value

        return None

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容
        """
        try:
            if file_path.suffix in [".md", ".txt"]:
                with open(file_path, encoding="utf-8") as f:
                    return f.read()
            elif file_path.suffix == ".json":
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                # 尝试提取内容字段
                if isinstance(data, dict):
                    return (
                        data.get("content")
                        or data.get("text")
                        or json.dumps(data, ensure_ascii=False, indent=2)
                    )
                return str(data)
            else:
                # 对于其他格式,返回提示
                return f"[文件: {file_path.name}, 类型: {file_path.suffix}]"

        except Exception as e:
            logger.debug(f"读取文件失败 {file_path}: {e}")
            return None

    def build_writing_prompt_with_examples(
        self, topic: str, section: str, role: str, base_style_prompt: str
    ) -> str:
        """
        构建包含示例的写作提示词

        Args:
            topic: 主题
            section: 章节名称
            role: 角色
            base_style_prompt: 基础风格提示词

        Returns:
            增强后的提示词
        """
        # 搜索相关示例
        examples = asyncio.run(
            self.search_relevant_examples(topic=topic, section=section, role=role, top_k=2)
        )

        # 构建示例部分
        examples_section = ""
        if examples:
            examples_section = "\n### 参考示例\n\n"
            examples_section += (
                "以下是从平台真实法律文档中提取的相关示例,供您参考写作风格和结构:\n\n"
            )
            for i, example in enumerate(examples, 1):
                examples_section += f"#### 示例 {i}: {example['title']}\n\n"
                examples_section += f"**来源**: {example['source']}\n\n"
                examples_section += f"```\n{example['content']}\n```\n\n"
        else:
            examples_section = "\n### 参考示例\n\n暂无相关示例。\n"

        # 组合完整提示词
        enhanced_prompt = f"""{base_style_prompt}

## 参考素材

{examples_section}

请参考上述示例的风格和结构,但不要抄袭具体内容。
"""

        return enhanced_prompt

    def search_materials(
        self, query: str, category: Optional[str] = None, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        搜索素材(兼容旧版本接口)

        Args:
            query: 搜索关键词
            category: 素材类别(可选)
            top_k: 返回数量

        Returns:
            匹配的素材列表
        """
        if not self.rag_manager:
            return []

        try:
            # 使用RAG进行检索
            task_type = category or "default"
            rag_context = asyncio.run(self.rag_manager.retrieve(query=query, task_type=task_type))

            # 转换结果格式
            results = []
            for result in rag_context.get_top_results(top_k):
                results.append(
                    {
                        "id": result.source,
                        "title": result.metadata.get("title", result.source),
                        "source": result.source,
                        "content": (
                            result.content[:500] + "..."
                            if len(result.content) > 500
                            else result.content
                        ),
                        "relevance_score": result.score,
                        "metadata": result.metadata,
                    }
                )

            return results

        except Exception as e:
            logger.warning(f"检索失败: {e}")
            return []


# 全局单例
_materials_manager_instance = None


def get_materials_manager_db(
    rag_manager=None, materials_path: Path | None = None
) -> WritingMaterialsManagerDB:
    """获取素材库管理器单例(数据库版本)"""
    global _materials_manager_instance

    if _materials_manager_instance is None:
        _materials_manager_instance = WritingMaterialsManagerDB(
            rag_manager=rag_manager, materials_path=materials_path
        )

    return _materials_manager_instance


if __name__ == "__main__":
    # 测试代码
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from qdrant_client import QdrantClient

    from core.llm.rag_manager import get_rag_manager

    async def test():
        print("法律写作素材库管理器 - 数据库版本测试")
        print("=" * 70)

        # 1. 初始化RAG管理器
        try:
            qdrant_client = QdrantClient(url="http://localhost:6333")
            rag_manager = get_rag_manager(qdrant_client=qdrant_client)
            print("   RAG管理器: 已配置")
        except Exception as e:
            print(f"   RAG管理器: 配置失败 ({e})")
            rag_manager = None

        # 2. 创建素材管理器
        manager = get_materials_manager_db(rag_manager=rag_manager)

        # 3. 测试搜索
        print("\n🔍 搜索测试: 创造性")
        results = manager.search_materials("创造性", top_k=3)
        for result in results:
            print(f"   {result.get('title', 'N/A')}: {result.get('relevance_score', 'N/A')}")

        # 4. 测试搜索相关示例
        if rag_manager:
            print("\n🔍 搜索相关示例: 专利 全面覆盖")
            relevant_examples = await manager.search_relevant_examples(
                "专利全面覆盖", "法理基础", role="scholar", top_k=2
            )
            for i, example in enumerate(relevant_examples, 1):
                print(f"   示例 {i}: {example['title']}")
                print(f"      来源: {example['source']}")
                print(f"      长度: {len(example['content'])} 字符")

        # 5. 测试构建提示词
        if rag_manager:
            print("\n📝 构建增强提示词...")
            enhanced_prompt = manager.build_writing_prompt_with_examples(
                topic="专利全面覆盖原则",
                section="法理基础",
                role="scholar",
                base_style_prompt="## 写作要求\n请撰写专业的法律研究报告。",
            )
            print(f"   提示词长度: {len(enhanced_prompt)} 字符")
            print(f"   包含示例: {'是' if '参考示例' in enhanced_prompt else '否'}")

        print("\n✅ 测试完成!")

    asyncio.run(test())
