#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建高级知识图谱关系
创建复杂的业务逻辑关联
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedKnowledgeGraphBuilder:
    """高级知识图谱构建器"""

    def __init__(self):
        self.output_dir = Path("/Users/xujian/Athena工作平台/data/advanced_kg")
        self.output_dir.mkdir(exist_ok=True)

    def build_patent_landscape_graph(self):
        """构建专利景观知识图谱"""
        logger.info("🌐 构建专利景观知识图谱...")

        # 定义专利景观节点
        landscape_nodes = {
            "patents": [
                {
                    "id": "AI_patent_001",
                    "title": "深度学习专利分析方法",
                    "technology": "深度学习",
                    "industry": "人工智能",
                    "applicant": "Athena AI公司",
                    "inventors": ["张教授", "李博士", "王工程师"],
                    "priority": "高",
                    "market_potential": "巨大"
                },
                {
                    "id": "legal_tech_001",
                    "title": "智能合同审查系统",
                    "technology": "NLP",
                    "industry": "法律科技",
                    "applicant": "LegalTech创新",
                    "inventors": ["赵律师", "钱算法专家"],
                    "priority": "中",
                    "market_potential": "良好"
                },
                {
                    "id": "blockchain_001",
                    "title": "专利区块链存证方法",
                    "technology": "区块链",
                    "industry": "金融科技",
                    "applicant": "BlockPatent公司",
                    "inventors": ["孙架构师", "李开发者"],
                    "priority": "高",
                    "market_potential": "巨大"
                }
            ],
            "technologies": [
                {
                    "id": "deep_learning",
                    "name": "深度学习",
                    "category": "机器学习",
                    "maturity": "成熟",
                    "trend": "上升",
                    "applications": ["图像识别", "自然语言处理", "推荐系统"]
                },
                {
                    "id": "nlp",
                    "name": "自然语言处理",
                    "category": "人工智能",
                    "maturity": "发展期",
                    "trend": "快速上升",
                    "applications": ["文本分析", "机器翻译", "问答系统"]
                },
                {
                    "id": "blockchain",
                    "name": "区块链",
                    "category": "分布式技术",
                    "maturity": "成长期",
                    "trend": "稳定",
                    "applications": ["供应链", "金融服务", "知识产权"]
                }
            ],
            "industries": [
                {
                    "id": "ai_industry",
                    "name": "人工智能产业",
                    "market_size": "万亿级",
                    "growth_rate": "30%+",
                    "key_players": ["Google", "Microsoft", "OpenAI", "Athena AI"]
                },
                {
                    "id": "legal_tech",
                    "name": "法律科技产业",
                    "market_size": "千亿级",
                    "growth_rate": "20%+",
                    "key_players": ["LegalTech创新", "LawGeex", "Kira Systems"]
                },
                {
                    "id": "fintech",
                    "name": "金融科技产业",
                    "market_size": "万亿级",
                    "growth_rate": "25%+",
                    "key_players": ["蚂蚁集团", "BlockPatent", "Stripe"]
                }
            ],
            "companies": [
                {
                    "id": "athena_ai",
                    "name": "Athena AI公司",
                    "type": "AI企业",
                    "location": "北京",
                    "founded": "2018",
                    "focus_area": "专利分析、AI研发",
                    "market_cap": "10亿",
                    "competitiveness": "强"
                },
                {
                    "id": "legaltech_innovation",
                    "name": "LegalTech创新",
                    "type": "法律科技企业",
                    "location": "上海",
                    "founded": "2019",
                    "focus_area": "合同审查、法律AI",
                    "market_cap": "5亿",
                    "competitiveness": "中"
                },
                {
                    "id": "blockpatent",
                    "name": "BlockPatent公司",
                    "type": "区块链企业",
                    "location": "深圳",
                    "founded": "2020",
                    "focus_area": "专利保护、区块链存证",
                    "market_cap": "8亿",
                    "competitiveness": "强"
                }
            ]
        }

        # 定义复杂关系
        landscape_relationships = [
            {
                "source": "AI_patent_001",
                "target": "deep_learning",
                "type": "IMPLEMENTS_TECHNOLOGY",
                "properties": {
                    "technology_level": "核心技术",
                    "innovation_degree": "高度创新",
                    "commercial_value": "高"
                }
            },
            {
                "source": "legal_tech_001",
                "target": "nlp",
                "type": "IMPLEMENTS_TECHNOLOGY",
                "properties": {
                    "technology_level": "应用技术",
                    "innovation_degree": "中度创新",
                    "commercial_value": "中"
                }
            },
            {
                "source": "AI_patent_001",
                "target": "ai_industry",
                "type": "BELONGS_TO_INDUSTRY",
                "properties": {
                    "industry_role": "技术引领者",
                    "market_position": "领先",
                    "competitive_advantage": "技术壁垒"
                }
            },
            {
                "source": "deep_learning",
                "target": "ai_industry",
                "type": "SUPPORTS_INDUSTRY",
                "properties": {
                    "support_level": "关键技术",
                    "impact_scope": "全行业",
                    "future_potential": "巨大"
                }
            },
            {
                "source": "athena_ai",
                "target": "AI_patent_001",
                "type": "OWNS_PATENT",
                "properties": {
                    "ownership_type": "全资拥有",
                    "protection_scope": "全球",
                    "licensing_model": "专有"
                }
            },
            {
                "source": "athena_ai",
                "target": "ai_industry",
                "type": "COMPETES_IN",
                "properties": {
                    "market_share": "5%",
                    "competitive_strategy": "技术领先",
                    "growth_potential": "高"
                }
            },
            {
                "source": "AI_patent_001",
                "target": "blockchain_001",
                "type": "SYNERGY_WITH",
                "properties": {
                    "synergy_type": "技术互补",
                    "cooperation_model": "专利交叉许可",
                    "joint_development": "可能"
                }
            }
        ]

        # 生成Gremlin脚本
        script = self._generate_gremlin_script(
            landscape_nodes,
            landscape_relationships,
            "patent_landscape"
        )

        # 保存脚本
        script_path = self.output_dir / "patent_landscape_kg.gremlin"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)

        logger.info(f"✅ 专利景观知识图谱已生成: {script_path}")
        return {
            "nodes": sum(len(nodes) for nodes in landscape_nodes.values()),
            "relationships": len(landscape_relationships)
        }

    def build_competitor_analysis_graph(self):
        """构建竞争对手分析知识图谱"""
        logger.info("🔍 构建竞争对手分析知识图谱...")

        # 定义竞争分析节点
        competitor_nodes = {
            "companies": [
                {
                    "id": "athena",
                    "name": "Athena公司",
                    "industry": "专利分析",
                    "product": "AI专利分析平台",
                    "market_share": "15%",
                    "strengths": ["AI技术", "数据优势", "用户体验"],
                    "weaknesses": ["品牌知名度", "市场份额", "国际化"]
                },
                {
                    "id": "patentics",
                    "name": "Patentics公司",
                    "industry": "专利分析",
                    "product": "专利分析工具",
                    "market_share": "25%",
                    "strengths": ["品牌影响力", "客户基础", "技术积累"],
                    "weaknesses": ["创新速度", "AI集成", "响应速度"]
                },
                {
                    "id": "innography",
                    "name": "Innography公司",
                    "industry": "专利分析",
                    "product": "企业IP管理平台",
                    "market_share": "20%",
                    "strengths": ["企业客户", "全面功能", "全球服务"],
                    "weaknesses": ["价格昂贵", "操作复杂", "更新慢"]
                }
            ],
            "products": [
                {
                    "id": "athena_platform",
                    "name": "Athena AI专利平台",
                    "company": "athena",
                    "features": ["智能检索", "自动分析", "预测评分"],
                    "price": "中等",
                    "target_users": ["中小企业", "专利代理", "研究机构"]
                },
                {
                    "id": "patentics_tool",
                    "name": "Patentics分析工具",
                    "company": "patentics",
                    "features": ["大数据分析", "可视化", "报告生成"],
                    "price": "高",
                    "target_users": ["大型企业", "律师事务所"]
                }
            ],
            "markets": [
                {
                    "id": "sme_market",
                    "name": "中小企业市场",
                    "size": "千亿级",
                    "growth_rate": "25%",
                    "key_needs": ["成本控制", "易用性", "快速部署"]
                },
                {
                    "id": "enterprise_market",
                    "name": "企业级市场",
                    "size": "万亿级",
                    "growth_rate": "15%",
                    "key_needs": ["功能全面", "数据安全", "定制服务"]
                }
            ]
        }

        # 定义竞争关系
        competitor_relationships = [
            {
                "source": "athena",
                "target": "patentics",
                "type": "COMPETES_WITH",
                "properties": {
                    "competition_level": "直接竞争",
                    "competition_area": ["AI专利分析", "中小企业市场"],
                    "competitive_advantage": "技术创新",
                    "market_pressure": "高"
                }
            },
            {
                "source": "athena_platform",
                "target": "sme_market",
                "type": "TARGETS_MARKET",
                "properties": {
                    "market_penetration": "15%",
                    "growth_strategy": "产品差异化",
                    "customer_satisfaction": "90%"
                }
            },
            {
                "source": "patentics",
                "target": "enterprise_market",
                "type": "TARGETS_MARKET",
                "properties": {
                    "market_penetration": "30%",
                    "growth_strategy": "品牌优势",
                    "customer_satisfaction": "85%"
                }
            },
            {
                "source": "athena",
                "target": "innography",
                "type": "LEARNS_FROM",
                "properties": {
                    "learning_area": ["企业客户管理", "国际化经验"],
                    "strategic_implication": "潜在合作"
                }
            }
        ]

        # 生成Gremlin脚本
        script = self._generate_gremlin_script(
            competitor_nodes,
            competitor_relationships,
            "competitor_analysis"
        )

        # 保存脚本
        script_path = self.output_dir / "competitor_analysis_kg.gremlin"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)

        logger.info(f"✅ 竞争对手分析知识图谱已生成: {script_path}")
        return {
            "nodes": sum(len(nodes) for nodes in competitor_nodes.values()),
            "relationships": len(competitor_relationships)
        }

    def build_technology_evolution_graph(self):
        """构建技术演进知识图谱"""
        logger.info("🔄 构建技术演进知识图谱...")

        # 定义技术演进节点
        evolution_nodes = {
            "technologies": [
                {
                    "id": "traditional_search",
                    "name": "传统专利检索",
                    "period": "1990-2010",
                    "characteristics": ["关键词匹配", "布尔逻辑", "人工筛选"],
                    "efficiency": "低",
                    "accuracy": "中等"
                },
                {
                    "id": "machine_learning_search",
                    "name": "机器学习专利检索",
                    "period": "2010-2018",
                    "characteristics": ["文本分类", "相似度计算", "自动标注"],
                    "efficiency": "中等",
                    "accuracy": "较高"
                },
                {
                    "id": "ai_powered_search",
                    "name": "AI智能专利分析",
                    "period": "2018-现在",
                    "characteristics": ["深度学习", "语义理解", "预测分析"],
                    "efficiency": "高",
                    "accuracy": "很高"
                }
            ],
            "milestones": [
                {
                    "id": "patent_databases",
                    "name": "专利数据库建立",
                    "year": "1995",
                    "impact": "数字化基础",
                    "technology": "traditional_search"
                },
                {
                    "id": "google_patents",
                    "name": "Google Patents上线",
                    "year": "2006",
                    "impact": "开放访问",
                    "technology": "traditional_search"
                },
                {
                    "id": "deep_learning_breakthrough",
                    "name": "深度学习突破",
                    "year": "2018",
                    "impact": "范式转变",
                    "technology": "ai_powered_search"
                }
            ],
            "companies": [
                {
                    "id": "search_pioneers",
                    "name": "检索先驱公司",
                    "era": "1990-2010",
                    "technology": "traditional_search",
                    "success_factors": ["数据积累", "用户习惯"]
                },
                {
                    "id": "ai_leaders",
                    "name": "AI领导者公司",
                    "era": "2018-现在",
                    "technology": "ai_powered_search",
                    "success_factors": ["算法创新", "算力提升"]
                }
            ]
        }

        # 定义演进关系
        evolution_relationships = [
            {
                "source": "traditional_search",
                "target": "machine_learning_search",
                "type": "EVOLVED_TO",
                "properties": {
                    "evolution_driver": "技术进步",
                    "improvement_area": ["效率", "准确率"],
                    "transition_period": "5-8年"
                }
            },
            {
                "source": "machine_learning_search",
                "target": "ai_powered_search",
                "type": "EVOLVED_TO",
                "properties": {
                    "evolution_driver": "算法突破",
                    "improvement_area": ["智能化", "预测能力"],
                    "transition_period": "3-5年"
                }
            },
            {
                "source": "deep_learning_breakthrough",
                "target": "ai_powered_search",
                "type": "ENABLED",
                "properties": {
                    "contribution": "核心技术",
                    "time_lag": "1-2年",
                    "impact_level": "革命性"
                }
            }
        ]

        # 生成Gremlin脚本
        script = self._generate_gremlin_script(
            evolution_nodes,
            evolution_relationships,
            "technology_evolution"
        )

        # 保存脚本
        script_path = self.output_dir / "technology_evolution_kg.gremlin"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)

        logger.info(f"✅ 技术演进知识图谱已生成: {script_path}")
        return {
            "nodes": sum(len(nodes) for nodes in evolution_nodes.values()),
            "relationships": len(evolution_relationships)
        }

    def _generate_gremlin_script(self, nodes, relationships, graph_name):
        """生成Gremlin导入脚本"""
        script = []
        script.append(f"// {graph_name} 知识图谱")
        script.append(f"// 生成时间: {datetime.now().isoformat()}")
        script.append("")

        # 创建节点
        for node_type, node_list in nodes.items():
            script.append(f"// 创建 {node_type} 节点")
            for node in node_list:
                vertex_type = node_type.capitalize()
                script.append(f"g.addV('{vertex_type}').property('id', '{node['id']}')")

                # 添加属性
                for key, value in node.items():
                    if key != 'id':
                        if isinstance(value, list):
                            value_str = str(value).replace("'", "\\'")
                        else:
                            value_str = str(value).replace("'", "\\'")
                        script.append(f" .property('{key}', '{value_str}')")

                script.append(";")
            script.append("")

        # 创建关系
        script.append("// 创建关系")
        for rel in relationships:
            script.append(f"g.V('{rel['source']}').addE('{rel['type']}').to(g.V('{rel['target']}'))")

            # 添加关系属性
            for key, value in rel.get('properties', {}).items():
                value_str = str(value).replace("'", "\\'")
                script.append(f" .property('{key}', '{value_str}')")

            script.append(";")

        # 添加查询示例
        script.append("""
// 查询示例
// 1. 查看所有节点数量
g.V().count()

// 2. 查看所有关系数量
g.E().count()

// 3. 查看节点类型
g.V().label().dedup()

// 4. 查看关系类型
g.E().label().dedup()
""")

        return '\n'.join(script)

    def generate_analysis_queries(self):
        """生成高级分析查询"""
        logger.info("📊 生成高级分析查询...")

        queries = {
            "patent_landscape_analysis": [
                {
                    "name": "技术专利分布",
                    "gremlin": "g.V().hasLabel('Patents').group().by('technology').by(count()).order().by(values, dec)",
                    "description": "统计各技术领域的专利数量"
                },
                {
                    "name": "公司专利竞争力",
                    "gremlin": "g.V().hasLabel('Companies').as('c').out('OWNS_PATENT').where(__.out('IMPLEMENTS_TECHNOLOGY').has('trend', '上升')).count().as('hot_patents').select('c', 'hot_patents').order().by('hot_patents', dec)",
                    "description": "分析公司持有的热门技术专利"
                },
                {
                    "name": "技术关联分析",
                    "gremlin": "g.V().hasLabel('Technologies').as('tech1').both('IMPLEMENTS_TECHNOLOGY').both('IMPLEMENTS_TECHNOLOGY').where(neq('tech1')).group().by('name').by(count()).order().by(values, dec).limit(10)",
                    "description": "查找技术关联度最高的技术组合"
                }
            ],
            "competitor_analysis": [
                {
                    "name": "市场竞争格局",
                    "gremlin": "g.V().hasLabel('Companies').as('c').out('TARGETS_MARKET').as('market').group().by('market').by(select('c').fold()).order().by(select(keys))",
                    "description": "分析各市场的竞争格局"
                },
                {
                    "name": "产品功能对比",
                    "gremlin": "g.V().hasLabel('Products').as('p').out('BELONGS_TO').as('c').where(__.out('COMPETES_WITH')).path()",
                    "description": "查找竞争产品的功能对比"
                }
            ],
            "technology_evolution": [
                {
                    "name": "技术演进路径",
                    "gremlin": "g.V().hasLabel('Technologies').as('t').repeat(__.out('EVOLVED_TO')).emit().path().by('name')",
                    "description": "展示技术演进路径"
                },
                {
                    "name": "关键里程碑影响",
                    "gremlin": "g.V().hasLabel('Milestones').as('m').out('ENABLED').as('tech').select('m', 'tech')",
                    "description": "分析关键里程碑对技术发展的影响"
                }
            ]
        }

        # 保存查询文档
        doc_content = "# 高级知识图谱分析查询\n\n"
        doc_content += f"生成时间: {datetime.now().isoformat()}\n\n"

        for category, category_queries in queries.items():
            doc_content += f"## {category.replace('_', ' ').title()}\n\n"
            for query in category_queries:
                doc_content += f"### {query['name']}\n"
                doc_content += f"**用途**: {query['description']}\n"
                doc_content += f"**查询**: ```gremlin\n{query['gremlin']}\n``\n\n"

        doc_path = self.output_dir / "advanced_analysis_queries.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)

        logger.info(f"✅ 高级分析查询已保存: {doc_path}")
        return queries

    def run(self):
        """执行完整的构建流程"""
        logger.info("🚀 开始构建高级知识图谱...")
        logger.info("=" * 60)

        stats = {}

        # 1. 构建专利景观图谱
        stats["patent_landscape"] = self.build_patent_landscape_graph()

        # 2. 构建竞争对手分析图谱
        stats["competitor_analysis"] = self.build_competitor_analysis_graph()

        # 3. 构建技术演进图谱
        stats["technology_evolution"] = self.build_technology_evolution_graph()

        # 4. 生成高级分析查询
        queries = self.generate_analysis_queries()

        # 5. 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("✅ 高级知识图谱构建完成！")
        logger.info("\n📊 构建统计:")

        total_nodes = sum(stat["nodes"] for stat in stats.values())
        total_relationships = sum(stat["relationships"] for stat in stats.values())

        for graph_type, stat in stats.items():
            logger.info(f"  {graph_type}: {stat['nodes']} 节点, {stat['relationships']} 关系")

        logger.info(f"\n📈 总计: {total_nodes} 节点, {total_relationships} 关系")
        logger.info(f"🔍 分析查询: {sum(len(queries) for queries in queries.values())} 个")

        logger.info("\n📋 生成的文件:")
        logger.info("  1. patent_landscape_kg.gremlin - 专利景观图谱")
        logger.info("  2. competitor_analysis_kg.gremlin - 竞争分析图谱")
        logger.info("  3. technology_evolution_kg.gremlin - 技术演进图谱")
        logger.info("  4. advanced_analysis_queries.md - 高级分析查询")

        return True

def main():
    """主函数"""
    builder = AdvancedKnowledgeGraphBuilder()
    success = builder.run()

    if success:
        print("\n🎉 高级知识图谱构建成功！")
        print("\n💡 使用说明:")
        print("  1. 连接Gremlin控制台")
        print("  2. 分别导入3个知识图谱脚本")
        print("  3. 使用分析查询进行深度分析")
        print("  4. 可视化分析结果")
    else:
        print("\n❌ 高级知识图谱构建失败")

if __name__ == "__main__":
    main()