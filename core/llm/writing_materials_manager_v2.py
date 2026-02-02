#!/usr/bin/env python3
"""
法律写作素材库管理器
Legal Writing Materials Manager

管理平台已有的专利无效宣告决定、判决文书等写作素材,
为法律写作能力提供高质量的参考素材。
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class WritingMaterialsManager:
    """
    法律写作素材库管理器

    功能:
    1. 索引平台已有的专利无效宣告决定
    2. 索引判决文书
    3. 索引司法解释和法律条文
    4. 提供智能检索功能
    5. 为写作能力提供参考素材
    """

    def __init__(self, materials_path: Path | None = None):
        """
        初始化素材库管理器

        Args:
            materials_path: 素材路径(默认为/Users/xujian/语料)
        """
        if materials_path is None:
            materials_path = Path("/Users/xujian/语料")

        self.materials_path = materials_path

        # 子路径
        self.patent_invalidations_path = materials_path / "无效复审决定"
        self.patent_judgments_path = materials_path / "专利判决"
        self.court_judgments_path = materials_path / "判决文书"
        self.interpretations_path = materials_path / "司法解释"
        self.laws_path = materials_path / "Laws-1.0.0"

        # 索引文件
        self.index_path = materials_path / "legal_writing_materials_index.json"
        self.index = self._load_or_create_index()

        logger.info("✅ 写作素材库管理器初始化完成")
        logger.info(f"   素材路径: {self.materials_path}")
        logger.info(f"   无效复审决定: {self.patent_invalidations_path}")
        logger.info(f"   专利判决: {self.patent_judgments_path}")
        logger.info(f"   司法解释: {self.interpretations_path}")

    def _load_or_create_index(self) -> dict[str, Any]:
        """加载或创建索引"""
        if self.index_path.exists():
            try:
                with open(self.index_path, encoding="utf-8") as f:
                    index = json.load(f)
                logger.info(f"   已加载索引: {len(index.get('materials', []))} 条素材")
                return index
            except Exception as e:
                logger.warning(f"   索引加载失败: {e}")

        # 创建新索引
        index = {
            "version": "1.0",
            "last_updated": None,
            "materials": [],
            "categories": {
                "patent_invalidation": [],
                "patent_judgments": [],
                "court_judgments": [],
                "judicial_interpretations": [],
                "laws_regulations": [],
            },
            "statistics": {"total_count": 0, "by_category": {}},
        }

        return index

    def _save_index(self, index: dict[str, Any]):
        """保存索引"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def search_materials(
        self, query: str, category: str | None = None, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        搜索素材

        Args:
            query: 搜索关键词
            category: 素材类别(可选)
            top_k: 返回数量

        Returns:
            匹配的素材列表
        """
        results = []
        query_lower = query.lower()

        for material in self.index["materials"]:
            # 类别过滤
            if category and material["category"] != category:
                continue

            # 关键词匹配
            score = 0

            # 标题匹配
            if "title" in material and query_lower in material["title"].lower():
                score += 10

            # 文件名匹配
            if query_lower in material.get("file_name", "").lower():
                score += 5

            # ID匹配
            if query_lower in material["id"].lower():
                score += 3

            if score > 0:
                results.append({**material, "relevance_score": score})

        # 按相关性排序
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return results[:top_k]

    def get_material_content(self, material_id: str) -> str | None:
        """
        获取素材内容

        Args:
            material_id: 素材ID

        Returns:
            素材内容
        """
        # 查找素材
        material = None
        for m in self.index["materials"]:
            if m["id"] == material_id:
                material = m
                break

        if not material:
            logger.warning(f"未找到素材: {material_id}")
            return None

        # 读取文件内容
        file_path = Path(material["file_path"])
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return None

        try:
            if file_path.suffix in [".md", ".txt"]:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                return content
            elif file_path.suffix == ".json":
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return f"[文件: {file_path.name}, 类型: {file_path.suffix}]"

        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            return None

    async def search_relevant_examples(
        self, topic: str, section: str, category: str = "patent_invalidation", top_k: int = 3
    ) -> list[dict[str, str]]:
        """
        搜索相关的写作示例

        Args:
            topic: 主题
            section: 章节名称
            category: 素材类别
            top_k: 返回数量

        Returns:
            相关示例列表,每个包含title和content
        """
        # 搜索相关素材
        materials = self.search_materials(
            query=topic, category=category, top_k=top_k * 3  # 多搜索一些
        )

        examples = []
        for material in materials:
            content = self.get_material_content(material["id"])
            if content and len(content) > 200:
                # 提取相关段落
                examples.append(
                    {
                        "title": material.get("title", material["id"]),
                        "source": material.get("file_name", material["id"]),
                        "content": content[:1500] + "..." if len(content) > 1500 else content,
                        "relevance_score": material.get("relevance_score", 0),
                    }
                )

                if len(examples) >= top_k:
                    break

        return examples

    def build_writing_prompt_with_examples(
        self,
        topic: str,
        section: str,
        role: str,
        base_style_prompt: str,
        category: str | None = None,
    ) -> str:
        """
        构建包含示例的写作提示词

        Args:
            topic: 主题
            section: 章节名称
            role: 角色
            base_style_prompt: 基础风格提示词
            category: 素材类别

        Returns:
            增强后的提示词
        """
        # 根据角色选择合适的素材类别
        if category is None:
            category_map = {
                "patent_attorney": "patent_invalidation",
                "lawyer": "court_judgments",
                "judge": "court_judgments",
                "scholar": "patent_judgments",
            }
            category = category_map.get(role, "patent_invalidation")

        # 搜索相关示例
        examples = asyncio.run(
            self.search_relevant_examples(topic=topic, section=section, category=category, top_k=2)
        )

        # 构建示例部分
        examples_section = ""
        if examples:
            examples_section = "\n### 参考示例\n\n"
            for i, example in enumerate(examples, 1):
                examples_section += f"#### 示例 {i}: {example['title']}\n\n"
                examples_section += f"**来源**: {example['source']}\n\n"
                examples_section += f"```\n{example['content']}\n```\n\n"

        # 组合完整提示词
        enhanced_prompt = f"""{base_style_prompt}

## 参考素材

以下是从平台真实法律文档中提取的相关示例,供您参考写作风格和结构:

{examples_section}

请参考上述示例的风格和结构,但不要抄袭具体内容。
"""

        return enhanced_prompt


# 全局单例
_materials_manager_instance = None


def get_materials_manager(materials_path: Path | None = None) -> WritingMaterialsManager:
    """获取素材库管理器单例"""
    global _materials_manager_instance

    if _materials_manager_instance is None:
        _materials_manager_instance = WritingMaterialsManager(materials_path)

    return _materials_manager_instance


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("法律写作素材库管理器 - 测试")
        print("=" * 70)

        manager = get_materials_manager()

        # 测试搜索
        print("\n🔍 搜索测试: 创造性")
        results = manager.search_materials("创造性", top_k=3)
        for result in results:
            print(f"   {result.get('title', result['id'])}: {result.get('relevance_score', 0)}")

        # 测试搜索相关示例
        print("\n🔍 搜索相关示例: 专利 全面覆盖")
        relevant_examples = await manager.search_relevant_examples(
            "专利全面覆盖", "法理基础", category="patent_judgments", top_k=2
        )
        for i, example in enumerate(relevant_examples, 1):
            print(f"   示例 {i}: {example['title']}")
            print(f"      来源: {example['source']}")
            print(f"      长度: {len(example['content'])} 字符")

        # 测试构建提示词
        print("\n📝 构建增强提示词...")
        enhanced_prompt = manager.build_writing_prompt_with_examples(
            topic="专利全面覆盖原则",
            section="法理基础",
            role="scholar",
            base_style_prompt="## 写作要求\n请撰写专业的法律研究报告。",
            category="patent_judgments",
        )
        print(f"   提示词长度: {len(enhanced_prompt)} 字符")
        print(f"   包含示例: {'是' if '参考示例' in enhanced_prompt else '否'}")

    asyncio.run(test())
