#!/usr/bin/env python3
"""
法律文件结构分析器
Legal Document Structure Analyzer

分析法律文件的结构，识别条款、章节等元素

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LegalArticle:
    """法律条款"""
    article_id: str
    article_number: str
    title: str
    content: str
    chapter: str = ""
    section: str = ""
    keywords: list[str] | None = None

@dataclass
class LegalEntity:
    """法律实体"""
    entity_id: str
    entity_type: str  # 机构、地点、人物、时间、金额等
    entity_name: str
    context: str
    article_id: str

@dataclass
class LegalRelation:
    """法律关系"""
    relation_id: str
    relation_type: str  # 引用、修改、废止、依据等
    source_article: str
    target_article: str
    description: str

class LegalStructureAnalyzer:
    """法律文件结构分析器"""

    def __init__(self):
        # 条款编号正则表达式
        self.article_patterns = [
            r'第([一二三四五六七八九十百千万\d]+)条[：:\s]*([^第\n]*)',  # 第X条：标题
            r'第([一二三四五六七八九十百千万\d]+)条\s*\n([^第\n]{0,100})',  # 第X条换行标题
            r'Article\s*(\d+)[\.:：\s]*([^\n]*)',  # 英文条款
        ]

        # 章节正则表达式
        self.chapter_patterns = [
            r'第([一二三四五六七八九十百千万\d]+)章[：:\s]*([^\n]+)',
            r'第([一二三四五六七八九十百千万\d]+)节[：:\s]*([^\n]+)',
            r'第([一二三四五六七八九十百千万\d]+)编[：:\s]*([^\n]+)',
            r'Chapter\s*(\d+)[\.:：\s]*([^\n]+)',
        ]

        # 实体识别正则表达式
        self.entity_patterns = {
            "机构": [
                r'([国务院]|[\u4e00-\u9fff]*部|[\u4e00-\u9fff]*委员会|[\u4e00-\u9fff]*局|[\u4e00-\u9fff]*院|[\u4e00-\u9fff]*署|[\u4e00-\u9fff]*办公室)',
                r'([最高人民法院]|[\u4e00-\u9fff]*人民法院|[\u4e00-\u9fff]*检察院)',
                r'([省市区县]*人民政府)',
            ],
            "地点": [
                r'([\u4e00-\u9fff]{2,4}省|[\u4e00-\u9fff]{2,4}市|[\u4e00-\u9fff]{2,4}区|[\u4e00-\u9fff]{2,4}县)',
                r'(全国|全省|全市|全县)',
            ],
            "时间": [
                r'(\d{4}年)',
                r'(\d{1,2}月\d{1,2}日)',
                r'([一二三四五六七八九十]+年[一二三四五六七八九十]+月[一二三四五六七八九十]+日)',
                r'(自本条例施行之日起|自发布之日起|施行之日起)',
            ],
            "金额": [
                r'(\d+元|\d+万元|\d+亿元)',
                r'([一二三四五六七八九十百千万\d]+元以上)',
            ],
            "法律文件": [
                r'(《[^》]+法》)',
                r'(《[^》]+条例》)',
                r'(《[^》]+规定》)',
                r'(《[^》]+办法》)',
                r'(《[^》]+解释》)',
            ]
        }

        # 关系识别模式
        self.relation_patterns = {
            "引用": [
                r'根据([《][^》]+[》])',
                r'按照([《][^》]+[》])',
                r'依据([《][^》]+[》])',
            ],
            "修改": [
                r'修改([《][^》]+[》])',
                r'修订([《][^》]+[》])',
            ],
            "废止": [
                r'废止([《][^》]+[》])',
                r'取消([《][^》]+[》])',
                r'不再适用([《][^》]+[》])',
            ],
            "解释": [
                r'对([《][^》]+[》])的解释',
                r'([《][^》]+[》])的释义',
            ]
        }

    def analyze_file_structure(self, file_path: Path) -> dict:
        """分析单个法律文件的结构"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return {"articles": [], "entities": [], "relations": [], "error": str(e)}

        # 提取标题
        title_match = re.search(r'^#\s*(.+)', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem

        # 识别条款
        articles = self.extract_articles(content, title)

        # 提取实体
        entities = self.extract_entities(articles)

        # 识别关系
        relations = self.extract_relations(content, articles)

        return {
            "file_path": str(file_path),
            "title": title,
            "articles": articles,
            "entities": entities,
            "relations": relations,
            "statistics": {
                "article_count": len(articles),
                "entity_count": len(entities),
                "relation_count": len(relations)
            }
        }

    def extract_articles(self, content: str, document_title: str) -> list[LegalArticle]:
        """提取法律条款"""
        articles = []
        current_chapter = ""
        current_section = ""

        # 先提取章节
        chapters = []
        for pattern in self.chapter_patterns:
            for match in re.finditer(pattern, content):
                chapters.append({
                    "position": match.start(),
                    "type": "chapter" if "章" in match.group(0) else "section",
                    "number": match.group(1),
                    "title": match.group(2).strip()
                })

        # 按位置排序
        chapters.sort(key=lambda x: x["position"])

        # 提取条款
        article_positions = []
        for pattern in self.article_patterns:
            for match in re.finditer(pattern, content):
                article_positions.append({
                    "position": match.start(),
                    "number": match.group(1),
                    "title": match.group(2).strip() if len(match.groups()) > 1 else "",
                    "pattern": pattern
                })

        # 按位置排序
        article_positions.sort(key=lambda x: x["position"])

        # 构建条款对象
        for i, article_pos in enumerate(article_positions):
            # 确定所属章节
            chapter = ""
            section = ""
            for ch in reversed(chapters):
                if ch["position"] < article_pos["position"]:
                    if ch["type"] == "chapter":
                        chapter = f'第{ch["number"]}章 {ch["title"]}'
                    else:
                        section = f'第{ch["number"]}节 {ch["title"]}'
                    break

            # 提取条款内容
            start_pos = article_pos["position"]
            end_pos = article_positions[i + 1]["position"] if i + 1 < len(article_positions) else len(content)

            article_content = content[start_pos:end_pos].strip()

            # 清理内容
            article_content = re.sub(r'^第[一二三四五六七八九十百千万\d]+条[：:\s]*', '', article_content)
            article_content = article_content[:2000]  # 限制长度

            # 生成条款ID
            article_id = f"{document_title}_{article_pos['number']}"

            # 提取关键词
            keywords = self.extract_keywords(article_content)

            article = LegalArticle(
                article_id=article_id,
                article_number=article_pos["number"],
                title=article_pos["title"],
                content=article_content,
                chapter=chapter,
                section=section,
                keywords=keywords
            )

            articles.append(article)

        return articles

    def extract_entities(self, articles: list[LegalArticle]) -> list[LegalEntity]:
        """从条款中提取实体"""
        entities = []
        entity_counter = 0

        for article in articles:
            text = f"{article.title} {article.content}"

            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        entity_name = match.group(1) or match.group(0)

                        # 避免重复
                        if not any(e.entity_name == entity_name and e.article_id == article.article_id
                                 for e in entities):
                            entity = LegalEntity(
                                entity_id=f"ent_{entity_counter:04d}",
                                entity_type=entity_type,
                                entity_name=entity_name,
                                context=text[max(0, match.start()-20):match.end()+20],
                                article_id=article.article_id
                            )
                            entities.append(entity)
                            entity_counter += 1

        return entities

    def extract_relations(self, content: str, articles: list[LegalArticle]) -> list[LegalRelation]:
        """提取法律关系"""
        relations = []
        relation_counter = 0

        # 构建条款索引
        article_index = {a.article_number: a.article_id for a in articles}

        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # 提取相关法律文件
                    law_name = match.group(1) if match.groups() else match.group(0)

                    # 查找上下文中的条款编号
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(content), match.end() + 100)
                    context = content[context_start:context_end]

                    # 查找条款引用
                    cited_articles = re.findall(r'第([一二三四五六七八九十百千万\d]+)条', context)

                    for cited_num in cited_articles:
                        relation = LegalRelation(
                            relation_id=f"rel_{relation_counter:04d}",
                            relation_type=relation_type,
                            source_article=articles[0].article_id if articles else "unknown",
                            target_article=f"{law_name}_{cited_num}",
                            description=f"在上下文中{relation_type}了{law_name}的第{cited_num}条"
                        )
                        relations.append(relation)
                        relation_counter += 1

        return relations

    def extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 法律专业关键词
        legal_keywords = [
            "应当", "必须", "可以", "不得", "禁止", "违反", "处罚", "责任",
            "权利", "义务", "责任", "赔偿", "补偿", "申请", "审批", "备案",
            "监督管理", "检查", "执法", "行政诉讼", "行政复议", "诉讼",
            "民事", "刑事", "行政", "经济", "合同", "侵权", "物权", "债权"
        ]

        # 提取包含法律关键词的短语
        keywords = []
        for keyword in legal_keywords:
            if keyword in text:
                # 提取包含关键词的短语
                pattern = rf'.{{0,20}}{keyword}.{{0,20}}'
                matches = re.findall(pattern, text)
                keywords.extend(matches[:2])  # 最多2个

        # 提取编号事项
        numbered_items = re.findall(r'[（(]\d+[)）][^。；；]*', text)
        keywords.extend(numbered_items[:5])  # 最多5个

        return list(set(keywords))[:10]  # 最多返回10个

    def analyze_batch(self, data_dir: Path) -> dict:
        """批量分析法律文件"""
        logger.info(f"\n📚 批量分析法律文件: {data_dir}")

        md_files = list(data_dir.rglob("*.md"))
        logger.info(f"找到 {len(md_files)} 个法律文件")

        all_results = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(md_files),
            "reports/reports/results": [],
            "statistics": {
                "total_articles": 0,
                "total_entities": 0,
                "total_relations": 0,
                "entity_types": {},
                "relation_types": {}
            }
        }

        for i, file_path in enumerate(md_files[:10]):  # 限制处理数量作为演示
            logger.info(f"处理 {i+1}/{len(md_files)}: {file_path.name}")

            result = self.analyze_file_structure(file_path)
            all_results["reports/reports/results"].append(result)

            # 更新统计
            if "error" not in result:
                all_results["statistics"]["total_articles"] += result["statistics"]["article_count"]
                all_results["statistics"]["total_entities"] += result["statistics"]["entity_count"]
                all_results["statistics"]["total_relations"] += result["statistics"]["relation_count"]

        logger.info("\n📊 分析完成:")
        logger.info(f"  总文件数: {all_results['total_files']}")
        logger.info(f"  总条款数: {all_results['statistics']['total_articles']}")
        logger.info(f"  总实体数: {all_results['statistics']['total_entities']}")
        logger.info(f"  总关系数: {all_results['statistics']['total_relations']}")

        return all_results

def main() -> None:
    """主函数"""
    print("="*100)
    print("🔍 法律文件结构分析器 🔍")
    print("="*100)

    analyzer = LegalStructureAnalyzer()

    # 分析法律文件
    data_dir = Path("/Users/xujian/Athena工作平台/dev/tools/Laws-1.0.0")
    results = analyzer.analyze_batch(data_dir)

    # 保存分析结果
    output_path = Path("/Users/xujian/Athena工作平台/production/output/analysis") / \
                   f"legal_structure_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 转换为可序列化格式
    serializable_results = {
        "timestamp": results["timestamp"],
        "total_files": results["total_files"],
        "statistics": results["statistics"],
        "reports/reports/results": []
    }

    for result in results["reports/reports/results"]:
        if "error" not in result:
            serializable_result = {
                "file_path": result["file_path"],
                "title": result["title"],
                "statistics": result["statistics"],
                "articles": [
                    {
                        "article_id": a.article_id,
                        "article_number": a.article_number,
                        "title": a.title,
                        "content": a.content[:200] + "...",
                        "chapter": a.chapter,
                        "section": a.section,
                        "keywords": a.keywords or []
                    } for a in result["articles"][:5]  # 限制输出
                ],
                "entities": [
                    {
                        "entity_id": e.entity_id,
                        "entity_type": e.entity_type,
                        "entity_name": e.entity_name,
                        "context": e.context
                    } for e in result["entities"][:10]  # 限制输出
                ],
                "relations": [
                    {
                        "relation_id": r.relation_id,
                        "relation_type": r.relation_type,
                        "description": r.description
                    } for r in result["relations"][:5]  # 限制输出
                ]
            }
            serializable_results["reports/reports/results"].append(serializable_result)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 分析完成，结果已保存: {output_path}")

    # 显示示例结果
    if results["reports/reports/results"]:
        print("\n📋 示例分析结果:")
        sample = results["reports/reports/results"][0]
        if "error" not in sample:
            print(f"\n文件: {sample['title']}")
            print(f"  条款数: {sample['statistics']['article_count']}")
            print(f"  实体数: {sample['statistics']['entity_count']}")
            print(f"  关系数: {sample['statistics']['relation_count']}")

            if sample["articles"]:
                print("\n示例条款:")
                article = sample["articles"][0]
                print(f"  {article['article_number']}条: {article['title'][:50]}...")
                print(f"  关键词: {', '.join(article['keywords'][:3])}")

            if sample["entities"]:
                print("\n示例实体:")
                for entity in sample["entities"][:3]:
                    print(f"  {entity['entity_type']}: {entity['entity_name']}")

if __name__ == "__main__":
    main()
