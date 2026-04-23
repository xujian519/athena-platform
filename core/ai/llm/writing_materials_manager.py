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
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class WritingMaterialsManager:
    """
    法律写作素材库管理器

    功能:
    1. 素引平台已有的专利无效宣告决定
    2. 索引判决文书
    3. 索引司法解释和法律条文
    4. 提供智能检索功能
    5. 为写作能力提供参考素材
    """

    def __init__(self, materials_path: Optional[Path] = None):
        """
        初始化素材库管理器

        Args:
            materials_path: 素材路径(默认为/Users/xujian/语料)
        """
        if materials_path is None:
            materials_path = Path("/Users/xujian/语料")

        self.materials_path = materials_path

        # 子路径
        self.patent_judgments_path = materials_path / "专利无效宣告决定"  # 专利无效宣告决定
        self.court_judgments_path = materials_path / "判决文书"  # 判决文书
        self.judicial_interpretations_path = materials_path / "司法解释"  # 司法解释
        self.laws_regulations_path = materials_path / "法律法规"  # 法律法规

        # 索引文件
        self.index_path = materials_path / "legal_writing_materials_index.json"
        self.index = self._load_or_create_index()

        logger.info("✅ 写作素材库管理器初始化完成")
        logger.info(f"   素材路径: {self.materials_path}")
        logger.info(f"   无效复审决定: {self.patent_judgments_path}")
        logger.info(f"   判决文书: {self.court_judgments_path}")
        logger.info(f"   司法解释: {self.judicial_interpretations_path}")
        logger.info(f"   法律法规: {self.laws_regulations_path}")

    def _load_or_create_index(self) -> dict[str, Any]:
        """加载或创建索引"""
        if self.index_path.exists():
            try:
                with open(self.index_path, encoding='utf-8') as f:
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
                "court_judgments": [],
                "judicial_interpretations": [],
                "laws_regulations": []
            },
            "statistics": {
                "total_count": 0,
                "by_category": {},
                "by_year": {},
                "by_topic": {}
            }
        }

        # 扫描素材并构建索引
        index = self._scan_materials(index)
        self._save_index(index)

        return index

    def _scan_materials(self, index: dict[str, Any]) -> dict[str, Any]:
        """扫描素材文件"""
        logger.info("   开始扫描素材文件...")

        # 1. 扫描专利无效宣告决定
        if self.patent_judgments_path.exists():
            self._scan_patent_judgments(index)

        # 2. 扫描法律书籍
        if self.legal_books_path.exists():
            self._scan_legal_books(index)

        # 3. 扫描法律知识库
        if self.laws_path.exists():
            self._scan_legal_knowledge(index)

        # 更新统计信息
        total = len(index["materials"])
        index["statistics"]["total_count"] = total
        index["last_updated"] = datetime.now().isoformat()

        logger.info(f"   扫描完成: {total} 条素材")

        return index

    def _scan_patent_judgments(self, index: dict[str, Any]):
        """扫描专利无效宣告决定"""
        logger.info("   扫描专利判决书...")

        processed_path = self.patent_judgments_path / "processed"
        if not processed_path.exists():
            return

        count = 0
        for item in processed_path.iterdir():
            if item.is_dir():
                try:
                    # 从目录名提取决定号
                    decision_id = item.name

                    # 查找目录中的文件
                    files = list(item.glob("*.docx")) + list(item.glob("*.txt"))
                    if files:
                        material = {
                            "id": f"patent_{decision_id}",
                            "category": "patent_invalidation",
                            "type": "专利无效宣告决定",
                            "decision_id": decision_id,
                            "title": self._extract_decision_title(decision_id),
                            "file_path": str(files[0]),
                            "file_count": len(files),
                            "indexed_date": datetime.now().isoformat()
                        }

                        index["materials"].append(material)
                        index["categories"]["patent_invalidation"].append(decision_id)
                        count += 1

                        if count >= 100:  # 限制初始索引数量
                            logger.info(f"   已索引 {count} 条专利判决书(限制)")
                            break

                except Exception as e:
                    logger.warning(f"   处理目录失败 {item.name}: {e}")

        logger.info(f"   专利判决书扫描完成: {count} 条")

    def _scan_legal_books(self, index: dict[str, Any]):
        """扫描法律书籍"""
        logger.info("   扫描法律书籍...")

        for item in self.legal_books_path.iterdir():
            if item.is_file() and item.suffix in ['.md', '.pdf', '.txt', '.docx']:
                material = {
                    "id": f"book_{item.stem}",
                    "category": "court_judgments",
                    "type": "法律书籍",
                    "title": item.stem,
                    "file_path": str(item),
                    "indexed_date": datetime.now().isoformat()
                }

                index["materials"].append(material)
                index["categories"]["court_judgments"].append(item.stem)

        logger.info("   法律书籍扫描完成")

    def _scan_legal_knowledge(self, index: dict[str, Any]):
        """扫描法律知识库"""
        logger.info("   扫描法律知识库...")

        # 扫描司法解释
        interpretations_path = self.laws_path / "司法解释"
        if interpretations_path.exists():
            for item in interpretations_path.glob("*.md"):
                material = {
                    "id": f"interpretation_{item.stem}",
                    "category": "judicial_interpretations",
                    "type": "司法解释",
                    "title": item.stem,
                    "file_path": str(item),
                    "indexed_date": datetime.now().isoformat()
                }

                index["materials"].append(material)
                index["categories"]["judicial_interpretations"].append(item.stem)

        logger.info("   法律知识库扫描完成")

    def _extract_decision_title(self, decision_id: str) -> str:
        """从决定号提取标题"""
        # 尝试解析决定号
        match = re.search(r'(\d{4,})号', decision_id)
        if match:
            return f"第{match.group(1)}号无效宣告请求审查决定"
        return decision_id

    def _save_index(self, index: dict[str, Any]):
        """保存索引"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def search_materials(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
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

        for material in self.index["materials"]:
            # 类别过滤
            if category and material["category"] != category:
                continue

            # 关键词匹配
            score = 0
            query_lower = query.lower()

            # 标题匹配
            if "title" in material:
                if query_lower in material["title"].lower():
                    score += 10
                if query_lower in material.get("decision_id", "").lower():
                    score += 5

            # 内容匹配(简化版,实际可以读取文件内容)
            # 这里可以扩展为真正的全文搜索

            if score > 0:
                results.append({
                    **material,
                    "relevance_score": score
                })

        # 按相关性排序
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return results[:top_k]

    def get_sample_materials(
        self,
        category: str,
        count: int = 3
    ) -> list[dict[str, Any]]:
        """
        获取示例素材

        Args:
            category: 素材类别
            count: 返回数量

        Returns:
            示例素材列表
        """
        # 过滤指定类别
        category_materials = [
            m for m in self.index["materials"]
            if m["category"] == category
        ]

        # 随机选择(或按某种规则选择)
        import random
        selected = random.sample(
            category_materials,
            min(count, len(category_materials))
        )

        return selected

    def get_material_content(self, material_id: str) -> Optional[str]:
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
            if file_path.suffix == '.md':
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
            elif file_path.suffix == '.txt':
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
            else:
                # 对于其他格式(如docx),返回提示
                content = f"[文件: {file_path.name}]"

            return content

        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            return None

    def get_writing_examples(
        self,
        doc_type: str = "research_report"
    ) -> dict[str, list[str]]:
        """
        获取写作示例

        Args:
            doc_type: 文档类型

        Returns:
            按章节组织的示例
        """
        examples = {
            "summary": [],  # 摘要示例
            "legal_basis": [],  # 法律依据示例
            "case_analysis": [],  # 案例分析示例
            "reasoning": [],  # 推理论证示例
            "conclusion": []  # 结论示例
        }

        # 从专利无效宣告决定中提取示例
        patent_materials = self.get_sample_materials("patent_invalidation", count=5)

        for material in patent_materials:
            content = self.get_material_content(material["id"])
            if content:
                # 提取关键段落作为示例
                # 这里可以添加更智能的提取逻辑
                if len(content) > 500:
                    examples["case_analysis"].append(content[:500] + "...")

        return examples

    async def search_relevant_examples(
        self,
        topic: str,
        section: str,
        top_k: int = 3
    ) -> list[str]:
        """
        搜索相关的写作示例

        Args:
            topic: 主题
            section: 章节名称
            top_k: 返回数量

        Returns:
            相关示例列表
        """
        # 构建搜索查询
        search_query = f"{topic} {section}"

        # 搜索相关素材
        materials = self.search_materials(
            query=search_query,
            top_k=top_k * 2  # 多搜索一些,然后筛选
        )

        examples = []
        for material in materials:
            content = self.get_material_content(material["id"])
            if content:
                # 提取相关段落
                # 这里可以添加更智能的相关性计算
                if len(content) > 200:
                    # 截取相关段落
                    relevant_part = content[:800]
                    examples.append(f"## 来源: {material.get('title', material['id'])}\n\n{relevant_part}\n\n")

                if len(examples) >= top_k:
                    break

        return examples


# 全局单例
_materials_manager_instance = None


def get_materials_manager(base_path: Optional[Path] = None) -> WritingMaterialsManager:
    """获取素材库管理器单例"""
    global _materials_manager_instance

    if _materials_manager_instance is None:
        _materials_manager_instance = WritingMaterialsManager(base_path)

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

        # 测试获取示例
        print("\n📝 获取写作示例...")
        examples = manager.get_writing_examples("research_report")
        for key, value in examples.items():
            print(f"   {key}: {len(value)} 条")

        # 测试搜索相关示例
        print("\n🔍 搜索相关示例: 专利 全面覆盖")
        relevant_examples = await manager.search_relevant_examples("专利全面覆盖", "法理基础", top_k=2)
        for i, example in enumerate(relevant_examples, 1):
            print(f"   示例 {i}: {len(example)} 字符")

    asyncio.run(test())

