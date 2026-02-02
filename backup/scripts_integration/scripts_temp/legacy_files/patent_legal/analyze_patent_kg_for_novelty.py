#!/usr/bin/env python3
"""
分析专利知识图谱中的新颖性规则
Analyze Novelty Rules in Patent Knowledge Graph

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import sqlite3
import json
import re
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentNoveltyAnalyzer:
    """专利新颖性分析器"""

    def __init__(self, db_path: str):
        """初始化"""
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        logger.info(f"连接到数据库: {self.db_path}")

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()

    def search_novelty_entities(self) -> List[Dict]:
        """搜索包含新颖性的实体"""
        novelty_keywords = [
            "新颖性", "现有技术", "公知技术", "公开使用", "出版物",
            "申请日", "优先权日", "抵触申请", "不属于现有技术",
            "技术方案", "技术效果", "对比文件", "区别特征",
            "A22.5", "A22.1", "A22.2", "A22.3", "A22.4"
        ]

        # 构建查询条件
        conditions = []
        for keyword in novelty_keywords:
            conditions.append(f"(name LIKE '%{keyword}%' OR value LIKE '%{keyword}%')")

        query = f"""
        SELECT id, entity_id, patent_id, entity_type, name, value, properties
        FROM patent_entities
        WHERE {' OR '.join(conditions)}
        ORDER BY entity_type, name
        LIMIT 5000
        """

        cursor = self.conn.cursor()
        cursor.execute(query)
        results = []

        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'entity_id': row[1],
                'patent_id': row[2],
                'entity_type': row[3],
                'name': row[4],
                'value': row[5],
                'properties': json.loads(row[6]) if row[6] else {}
            })

        logger.info(f"找到 {len(results)} 个与新颖性相关的实体")
        return results

    def extract_novelty_rules(self, entities: List[Dict]) -> List[Dict]:
        """提取新颖性规则"""
        rules = []

        # 新颖性规则模式
        rule_patterns = {
            "definition": [
                r"新颖性是指",
                r"新颖性.*定义",
                r".*属于现有技术.*",
                r".*不属于现有技术.*"
            ],
            "exclusion": [
                r".*不属于现有技术.*",
                r".*不构成公开.*",
                r".*保密状态.*",
                r".*尚未公开.*"
            ],
            "assessment": [
                r"判断.*新颖性",
                r"审查.*新颖性",
                r"新颖性.*审查",
                r"新颖性.*判断"
            ],
            "time_criteria": [
                r"申请日.*前",
                r"优先权日.*前",
                r"申请.*时",
                r"公开.*日"
            ],
            "exceptions": [
                r"抵触申请",
                r"首次公开",
                r"科学实验",
                r"非商业性使用"
            ]
        }

        for entity in entities:
            text = f"{entity['name']} {entity.get('value', '')}"

            # 提取规则
            for rule_type, patterns in rule_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        # 获取匹配上下文
                        start = max(0, match.start() - 100)
                        end = min(len(text), match.end() + 100)
                        context = text[start:end].strip()

                        rule = {
                            'rule_type': rule_type,
                            'pattern': pattern,
                            'matched_text': match.group(),
                            'context': context,
                            'source': {
                                'entity_name': entity['name'],
                                'entity_type': entity['entity_type'],
                                'patent_id': entity['patent_id']
                            }
                        }
                        rules.append(rule)

        # 去重
        unique_rules = []
        seen = set()
        for rule in rules:
            key = (rule['rule_type'], rule['matched_text'])
            if key not in seen:
                seen.add(key)
                unique_rules.append(rule)

        return unique_rules

    def analyze_novelty_relations(self) -> List[Dict]:
        """分析新颖性相关的关系"""
        # 查找与新颖性相关的法律条款关系
        query = """
        SELECT pr.relation_type, pe1.name as source_name, pe2.name as target_name,
               pe1.value as source_value, pe2.value as target_value
        FROM patent_relations pr
        JOIN patent_entities pe1 ON pr.source_entity_id = pe1.entity_id
        JOIN patent_entities pe2 ON pr.target_entity_id = pe2.entity_id
        WHERE (pe1.name LIKE '%新颖性%' OR pe1.value LIKE '%新颖性%' OR
               pe2.name LIKE '%新颖性%' OR pe2.value LIKE '%新颖ity%')
        LIMIT 1000
        """

        cursor = self.conn.cursor()
        cursor.execute(query)
        relations = []

        for row in cursor.fetchall():
            relations.append({
                'relation_type': row[0],
                'source_name': row[1],
                'target_name': row[2],
                'source_value': row[3],
                'target_value': row[4]
            })

        return relations

    def categorize_rules(self, rules: List[Dict]) -> Dict[str, List[Dict]]:
        """分类规则"""
        categorized = defaultdict(list)

        for rule in rules:
            rule_type = rule['rule_type']

            # 进一步细分
            if 'A22.' in rule['matched_text']:
                rule['category'] = '法条引用'
            elif '申请日' in rule['context']:
                rule['category'] = '时间标准'
            elif '不属于现有技术' in rule['matched_text']:
                rule['category'] = '例外情形'
            elif '审查' in rule['context']:
                rule['category'] = '审查标准'
            else:
                rule['category'] = '一般规定'

            categorized[rule_type].append(rule)

        return dict(categorized)

    def generate_report(self, entities: List[Dict], rules: List[Dict], relations: List[Dict]):
        """生成分析报告"""
        # 统计信息
        stats = {
            'total_entities': len(entities),
            'total_rules': len(rules),
            'total_relations': len(relations),
            'entity_types': Counter(e['entity_type'] for e in entities),
            'rule_categories': Counter(r.get('category', '未分类') for r in rules)
        }

        print("\n" + "="*80)
        print("📊 专利知识图谱新颖性分析报告")
        print("="*80)

        print(f"\n📈 基础统计:")
        print(f"  相关实体数: {stats['total_entities']:,}")
        print(f"  提取规则数: {stats['total_rules']:,}")
        print(f"  关系数目: {stats['total_relations']:,}")

        print(f"\n📋 实体类型分布:")
        for entity_type, count in stats['entity_types'].most_common():
            print(f"  - {entity_type}: {count:,}")

        print(f"\n📝 规则分类:")
        categorized_rules = self.categorize_rules(rules)
        for rule_type, rule_list in categorized_rules.items():
            print(f"\n  {rule_type.upper()} ({len(rule_list)} 条):")

            # 按子类别统计
            sub_categories = Counter(r.get('category', '未分类') for r in rule_list)
            for sub_cat, count in sub_categories.most_common():
                print(f"    - {sub_cat}: {count} 条")

        print(f"\n🔍 重要规则示例:")
        print("-"*60)

        # 显示各类重要规则
        for rule_type, rule_list in categorized_rules.items():
            if rule_list:
                print(f"\n【{rule_type}】示例:")
                for i, rule in enumerate(rule_list[:3]):
                    print(f"  {i+1}. {rule['matched_text']}")
                    print(f"     来源: {rule['source']['entity_name']}")
                    if rule['context'] != rule['matched_text']:
                        print(f"     上下文: {rule['context'][:100]}...")

        return stats

    def export_rules_to_file(self, rules: List[Dict], output_path: str):
        """导出规则到文件"""
        # 按类型分组导出
        categorized_rules = self.categorize_rules(rules)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 专利新颖性规则提取报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for rule_type, rule_list in categorized_rules.items():
                f.write(f"## {rule_type.upper()} ({len(rule_list)} 条)\n\n")

                for i, rule in enumerate(rule_list, 1):
                    f.write(f"### 规则 {i}\n\n")
                    f.write(f"**类型**: {rule['rule_type']}\n")
                    f.write(f"**匹配**: {rule['matched_text']}\n")
                    f.write(f"**分类**: {rule.get('category', '未分类')}\n")
                    f.write(f"**来源**: {rule['source']['entity_name']} ({rule['source']['entity_type']})\n")
                    f.write(f"**上下文**: {rule['context']}\n\n")
                    f.write("---\n\n")

        logger.info(f"规则已导出到: {output_path}")

def main():
    """主函数"""
    db_path = "/Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db"

    analyzer = PatentNoveltyAnalyzer(db_path)
    analyzer.connect()

    try:
        # 1. 搜索新颖性相关实体
        logger.info("搜索新颖性相关实体...")
        entities = analyzer.search_novelty_entities()

        # 2. 提取规则
        logger.info("提取新颖性规则...")
        rules = analyzer.extract_novelty_rules(entities)

        # 3. 分析关系
        logger.info("分析新颖性相关关系...")
        relations = analyzer.analyze_novelty_relations()

        # 4. 生成报告
        stats = analyzer.generate_report(entities, rules, relations)

        # 5. 导出规则
        output_dir = "/Users/xujian/Athena工作平台/data/patent_legal_novelty_analysis"
        os.makedirs(output_dir, exist_ok=True)

        # 导出JSON
        rules_json_path = f"{output_dir}/novelty_rules.json"
        with open(rules_json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': stats,
                'entities': entities,
                'rules': rules,
                'relations': relations
            }, f, ensure_ascii=False, indent=2)

        # 导出Markdown报告
        rules_md_path = f"{output_dir}/novelty_rules_report.md"
        analyzer.export_rules_to_file(rules, rules_md_path)

        print(f"\n📁 输出文件:")
        print(f"  JSON数据: {rules_json_path}")
        print(f"  Markdown报告: {rules_md_path}")

    finally:
        analyzer.close()

if __name__ == "__main__":
    import os
    from datetime import datetime
    main()