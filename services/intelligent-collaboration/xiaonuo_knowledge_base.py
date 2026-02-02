#!/usr/bin/env python3
"""
小诺知识库 - Xiaonuo Knowledge Base
存储和管理专利、知识产权、开发等专业知识
"""

import json
from core.async_main import async_main
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re

class XiaonuoKnowledgeBase:
    """小诺知识库 - 帮助诺诺更好地为爸爸服务"""

    def __init__(self):
        self.project_root = Path("/Users/xujian/Athena工作平台")
        self.db_path = self.project_root / "data" / "xiaonuo_knowledge.db"
        self.init_database()

        # 预定义知识分类
        self.knowledge_categories = {
            "专利法": ["专利法第26条", "新颖性", "创造性", "实用性", "权利要求书"],
            "专利实务": ["专利撰写", "审查答复", "复审无效", "专利申请", "专利检索"],
            "知识产权管理": ["案卷管理", "客户管理", "项目管理", "期限管理", "费用管理"],
            "技术开发": ["Python", "FastAPI", "PostgreSQL", "API设计", "系统架构"],
            "宝宸事务所": ["业务流程", "收费标准", "客户服务", "质量标准", "团队协作"]
        }

        # 初始化核心知识
        self.init_core_knowledge()

    def init_database(self) -> Any:
        """初始化知识库数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 知识条目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                content TEXT NOT NULL,
                keywords TEXT,
                importance INTEGER DEFAULT 3,
                confidence REAL DEFAULT 1.0,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        ''')

        # 知识关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id1 INTEGER,
                item_id2 INTEGER,
                relation_type TEXT,
                strength REAL DEFAULT 1.0,
                FOREIGN KEY (item_id1) REFERENCES knowledge_items (id),
                FOREIGN KEY (item_id2) REFERENCES knowledge_items (id)
            )
        ''')

        # 查询历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                matched_items TEXT,
                context TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON knowledge_items (category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords ON knowledge_items (keywords)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_importance ON knowledge_items (importance)")

        conn.commit()
        conn.close()

    def init_core_knowledge(self) -> Any:
        """初始化核心知识"""
        core_knowledge = {
            "专利法": [
                {
                    "title": "专利法第26条 - 说明书要求",
                    "content": "说明书应当对发明作出清楚、完整的说明，以所属技术领域的技术人员能够实现为准。必要的技术方案、技术效果和实施方式都需要详细说明。",
                    "keywords": "第26条,说明书,清楚完整,技术人员能够实现",
                    "importance": 5
                },
                {
                    "title": "创造性判断标准",
                    "content": "创造性是指与现有技术相比，该发明有突出的实质性特点和显著的进步。判断时考虑：1）是否容易想到；2）是否产生预料不到的技术效果；3）是否克服了技术偏见。",
                    "keywords": "创造性,实质性特点,显著进步,现有技术",
                    "importance": 5
                }
            ],
            "专利实务": [
                {
                    "title": "专利撰写要点",
                    "content": "1）技术问题要准确；2）技术方案要完整；3）技术效果要明确；4）实施例要具体；5）权利要求要清楚、简洁、完整。",
                    "keywords": "专利撰写,技术问题,技术方案,实施例,权利要求",
                    "importance": 5
                },
                {
                    "title": "审查意见答复策略",
                    "content": "1）认真理解审查意见；2）针对性修改文件；3）充分陈述意见；4）提供对比实验；5）保持专业态度。",
                    "keywords": "审查意见,答复,修改文件,陈述意见,对比实验",
                    "importance": 4
                }
            ],
            "宝宸事务所": [
                {
                    "title": "宝宸知识产权服务理念",
                    "content": "专业、高效、贴心。为每一位客户提供最优质的知识产权服务，保护创新成果，助力企业发展。",
                    "keywords": "宝宸,知识产权,服务理念,专业高效",
                    "importance": 5
                }
            ]
        }

        # 保存核心知识
        for category, items in core_knowledge.items():
            for item in items:
                self.add_knowledge(
                    title=item["title"],
                    category=category,
                    content=item["content"],
                    keywords=item["keywords"],
                    importance=item.get("importance", 3)
                )

    def add_knowledge(self, title: str, category: str, content: str,
                     keywords: str = "", subcategory: str = None,
                     importance: int = 3, source: str = "") -> int:
        """添加知识条目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO knowledge_items
            (title, category, subcategory, content, keywords, importance, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, category, subcategory, content, keywords, importance, source))

        knowledge_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return knowledge_id

    def search_knowledge(self, query: str, category: str = None,
                        limit: int = 10) -> List[Dict]:
        """搜索知识"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 记录查询
        cursor.execute(
            "INSERT INTO query_history (query, context) VALUES (?, ?)",
            (query, category or "")
        )

        # 构建搜索查询
        sql = '''
            SELECT id, title, category, subcategory, content, keywords,
                   importance, confidence, access_count
            FROM knowledge_items
            WHERE 1=1
        '''
        params = []

        if category:
            sql += " AND category = ?"
            params.append(category)

        # 模糊匹配
        query_words = query.split()
        for word in query_words:
            sql += " AND (content LIKE ? OR title LIKE ? OR keywords LIKE ?)"
            params.extend([f"%{word}%", f"%{word}%", f"%{word}%"])

        # 按重要性和匹配度排序
        sql += '''
            ORDER BY
                importance DESC,
                confidence DESC,
                access_count DESC
            LIMIT ?
        '''
        params.append(limit)

        cursor.execute(sql, params)
        results = cursor.fetchall()

        # 更新访问次数
        for row in results:
            cursor.execute(
                "UPDATE knowledge_items SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
                (row[0],)
            )

        conn.commit()
        conn.close()

        # 转换为字典列表
        knowledge_list = []
        for row in results:
            knowledge_list.append({
                "id": row[0],
                "title": row[1],
                "category": row[2],
                "subcategory": row[3],
                "content": row[4],
                "keywords": row[5],
                "importance": row[6],
                "confidence": row[7],
                "access_count": row[8]
            })

        return knowledge_list

    def get_related_knowledge(self, knowledge_id: int, limit: int = 5) -> List[Dict]:
        """获取相关知识"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取当前知识信息
        cursor.execute("SELECT category, keywords FROM knowledge_items WHERE id = ?", (knowledge_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return []

        category, keywords = result

        # 搜索同类别的相关知识
        sql = '''
            SELECT id, title, content, keywords
            FROM knowledge_items
            WHERE category = ? AND id != ?
            ORDER BY importance DESC, access_count DESC
            LIMIT ?
        '''

        cursor.execute(sql, (category, knowledge_id, limit))
        results = cursor.fetchall()

        conn.close()

        related_list = []
        for row in results:
            related_list.append({
                "id": row[0],
                "title": row[1],
                "content": row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                "keywords": row[3]
            })

        return related_list

    def get_knowledge_summary(self, category: str = None) -> Dict:
        """获取知识库摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if category:
            cursor.execute(
                "SELECT COUNT(*), AVG(importance) FROM knowledge_items WHERE category = ?",
                (category,)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*), AVG(importance) FROM knowledge_items"
            )

        total_items, avg_importance = cursor.fetchone()

        # 获取分类统计
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM knowledge_items
            GROUP BY category
            ORDER BY count DESC
        ''')

        category_stats = cursor.fetchall()

        # 获取热门知识
        cursor.execute('''
            SELECT title, access_count
            FROM knowledge_items
            WHERE access_count > 0
            ORDER BY access_count DESC
            LIMIT 5
        ''')

        popular_items = cursor.fetchall()

        conn.close()

        return {
            "total_items": total_items,
            "average_importance": round(avg_importance or 0, 2),
            "category_stats": dict(category_stats),
            "popular_items": popular_items
        }

    def learn_from_interaction(self, query: str, response: str,
                            feedback: str = "good") -> None:
        """从交互中学习"""
        # 提取关键信息
        keywords = self._extract_keywords(query + " " + response)

        # 如果反馈好，考虑保存为知识
        if feedback == "good" and len(response) > 50:
            # 判断是否已有类似知识
            existing = self.search_knowledge(query, limit=1)
            if not existing:
                # 自动分类
                category = self._auto_categorize(query)

                self.add_knowledge(
                    title=f"问答: {query[:30]}...",
                    category=category,
                    content=response,
                    keywords=",".join(keywords[:5]),
                    importance=2,
                    source="交互学习"
                )

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        keywords = []

        # 专业术语
        patent_terms = ["专利", "发明", "权利要求", "说明书", "审查", "答复",
                       "新颖性", "创造性", "实用性", "现有技术", "技术方案"]
        for term in patent_terms:
            if term in text:
                keywords.append(term)

        # 技术词汇
        tech_terms = ["API", "数据库", "系统", "架构", "开发", "代码", "Python"]
        for term in tech_terms:
            if term.lower() in text.lower():
                keywords.append(term)

        return list(set(keywords))

    def _auto_categorize(self, text: str) -> str:
        """自动分类"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["专利", "发明", "申请", "审查"]):
            if any(word in text_lower for word in ["法", "条款", "规定"]):
                return "专利法"
            else:
                return "专利实务"
        elif any(word in text_lower for word in ["管理", "项目", "客户", "案卷"]):
            return "知识产权管理"
        elif any(word in text_lower for word in ["代码", "开发", "系统", "API"]):
            return "技术开发"
        elif "宝宸" in text:
            return "宝宸事务所"
        else:
            return "其他"

    def export_knowledge(self, file_path: str, category: str = None) -> None:
        """导出知识库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        sql = "SELECT * FROM knowledge_items"
        params = []

        if category:
            sql += " WHERE category = ?"
            params.append(category)

        cursor.execute(sql, params)
        results = cursor.fetchall()

        conn.close()

        # 转换为JSON格式
        knowledge_export = []
        for row in results:
            knowledge_export.append({
                "id": row[0],
                "title": row[1],
                "category": row[2],
                "subcategory": row[3],
                "content": row[4],
                "keywords": row[5],
                "importance": row[6],
                "confidence": row[7],
                "source": row[8],
                "created_at": row[9],
                "access_count": row[10]
            })

        # 保存到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_export, f, ensure_ascii=False, indent=2)

        print(f"知识库已导出到: {file_path}")

    def import_knowledge(self, file_path: str) -> int:
        """导入知识库"""
        with open(file_path, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)

        imported_count = 0
        for item in knowledge_data:
            self.add_knowledge(
                title=item["title"],
                category=item["category"],
                content=item["content"],
                keywords=item.get("keywords", ""),
                subcategory=item.get("subcategory"),
                importance=item.get("importance", 3),
                source=f"导入: {item.get('source', '')}"
            )
            imported_count += 1

        print(f"已导入 {imported_count} 条知识")
        return imported_count

    def update_knowledge_confidence(self, knowledge_id: int, feedback: str) -> None:
        """更新知识置信度"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 根据反馈调整置信度
        if feedback == "helpful":
            cursor.execute(
                "UPDATE knowledge_items SET confidence = MIN(confidence + 0.1, 1.0) WHERE id = ?",
                (knowledge_id,)
            )
        elif feedback == "not_helpful":
            cursor.execute(
                "UPDATE knowledge_items SET confidence = MAX(confidence - 0.1, 0.1) WHERE id = ?",
                (knowledge_id,)
            )

        conn.commit()
        conn.close()

# 使用示例
def main() -> None:
    """主函数示例"""
    kb = XiaonuoKnowledgeBase()

    # 搜索专利法相关知识
    print("🔍 搜索专利法相关知识:")
    results = kb.search_knowledge("专利法第26条", category="专利法")
    for item in results:
        print(f"\n📚 {item['title']}")
        print(f"   {item['content'][:100]}...")
        print(f"   关键词: {item['keywords']}")

    # 获取知识库摘要
    print("\n📊 知识库摘要:")
    summary = kb.get_knowledge_summary()
    print(f"总条目: {summary['total_items']}")
    print(f"平均重要性: {summary['average_importance']}")
    print("\n分类统计:")
    for cat, count in summary['category_stats'].items():
        print(f"  {cat}: {count}条")

    # 从交互学习
    kb.learn_from_interaction(
        "如何提高专利授权率？",
        "提高专利授权率的方法：1）做好现有技术检索；2）突出创新点；3）完善实施例；4）合理撰写权利要求。",
        feedback="good"
    )

    # 导出知识库
    kb.export_knowledge("/tmp/xiaonuo_knowledge_backup.json")

if __name__ == "__main__":
    main()