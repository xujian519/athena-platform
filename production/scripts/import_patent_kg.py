#!/usr/bin/env python3
"""
导入专利知识图谱
Import Patent Knowledge Graph

将专利实体和关系导入到NebulaGraph

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "patent_rules_system"))

from nebula_graph_builder_integrated import NebulaGraphBuilderIntegrated
from patent_entity_extractor_pro import PatentEntityExtractorPro

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentKnowledgeGraphImporter:
    """专利知识图谱导入器"""

    def __init__(self):
        self.extractor = PatentEntityExtractorPro()
        self.graph_builder = NebulaGraphBuilderIntegrated(use_real_nebula=True)
        self.data_path = Path("/Users/xujian/Athena工作平台/production/data/patent_rules")
        self.entities = []
        self.relations = []

    async def load_sample_data(self):
        """加载示例数据"""
        # 专利相关的示例实体和关系
        test_entities = [
            {
                'name': '发明专利',
                'type': 'PATENT_TYPE',
                'properties': {
                    'definition': '对产品、方法或者其改进所提出的新的技术方案',
                    'category': '专利类型',
                    'confidence': 0.95,
                    'source': '专利法第二条',
                    'protection_period': '20年'
                }
            },
            {
                'name': '实用新型专利',
                'type': 'PATENT_TYPE',
                'properties': {
                    'definition': '对产品的形状、构造或者其结合所提出的适于实用的新的技术方案',
                    'category': '专利类型',
                    'confidence': 0.95,
                    'source': '专利法第二条',
                    'protection_period': '10年'
                }
            },
            {
                'name': '外观设计专利',
                'type': 'PATENT_TYPE',
                'properties': {
                    'definition': '对产品的形状、图案或者其结合以及色彩与形状、图案的结合所作出的富有美感并适于工业应用的新设计',
                    'category': '专利类型',
                    'confidence': 0.95,
                    'source': '专利法第二条',
                    'protection_period': '15年'
                }
            },
            {
                'name': '专利法',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '调整因发明创造而产生的各种社会关系的法律规范',
                    'category': '法律法规',
                    'confidence': 0.98,
                    'source': '全国人大',
                    'enacted_date': '1984-03-12'
                }
            },
            {
                'name': '专利法实施细则',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '对专利法的具体规定进行细化的行政法规',
                    'category': '行政法规',
                    'confidence': 0.98,
                    'source': '国务院'
                }
            },
            {
                'name': '专利审查指南',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '国家知识产权局制定的专利审查标准和程序',
                    'category': '部门规章',
                    'confidence': 0.95,
                    'source': '国家知识产权局'
                }
            },
            {
                'name': '新颖性',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '该发明或者实用新型不属于现有技术',
                    'category': '专利授权条件',
                    'confidence': 0.95,
                    'source': '专利法第二十二条'
                }
            },
            {
                'name': '创造性',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '与现有技术相比，该发明有突出的实质性特点和显著的进步',
                    'category': '专利授权条件',
                    'confidence': 0.95,
                    'source': '专利法第二十二条'
                }
            },
            {
                'name': '实用性',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '该发明或者实用新型能够制造或者使用，并且能够产生积极效果',
                    'category': '专利授权条件',
                    'confidence': 0.95,
                    'source': '专利法第二十二条'
                }
            },
            {
                'name': '现有技术',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '申请日以前在国内外为公众所知的技术',
                    'category': '专利术语',
                    'confidence': 0.95,
                    'source': '专利法第二十二条'
                }
            },
            {
                'name': '权利要求书',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '说明要求专利保护范围的文件',
                    'category': '专利申请文件',
                    'confidence': 0.98,
                    'source': '专利法第二十六条'
                }
            },
            {
                'name': '说明书',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '清楚、完整地描述发明或者实用新型的技术内容的文件',
                    'category': '专利申请文件',
                    'confidence': 0.98,
                    'source': '专利法第二十六条'
                }
            },
            {
                'name': '优先权',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '申请人就其发明创造第一次在某国提出专利申请后，在法定期限内就相同主题在他国提出专利申请的权限',
                    'category': '专利制度',
                    'confidence': 0.95,
                    'source': '专利法第二十九条'
                }
            },
            {
                'name': '专利侵权',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '未经专利权人许可，实施其专利的行为',
                    'category': '专利法律',
                    'confidence': 0.95,
                    'source': '专利法第十一条'
                }
            },
            {
                'name': '专利无效宣告',
                'type': 'LEGAL_TERM',
                'properties': {
                    'definition': '自专利局公告授予专利权之日起，任何单位或者个人认为该专利权的授予不符合本法有关规定的，可以请求专利复审委员会宣告该专利权无效',
                    'category': '专利法律程序',
                    'confidence': 0.95,
                    'source': '专利法第四十五条'
                }
            }
        ]

        test_relations = [
            {
                'subject': '专利法',
                'object': '发明专利',
                'relation': 'regulates',
                'properties': {
                    'scope': '保护范围',
                    'confidence': 0.9,
                    'article': '第二条'
                }
            },
            {
                'subject': '专利法',
                'object': '实用新型专利',
                'relation': 'regulates',
                'properties': {
                    'scope': '保护范围',
                    'confidence': 0.9,
                    'article': '第二条'
                }
            },
            {
                'subject': '专利法',
                'object': '外观设计专利',
                'relation': 'regulates',
                'properties': {
                    'scope': '保护范围',
                    'confidence': 0.9,
                    'article': '第二条'
                }
            },
            {
                'subject': '专利法',
                'object': '新颖性',
                'relation': 'defines',
                'properties': {
                    'article': '第二十二条',
                    'confidence': 0.95
                }
            },
            {
                'subject': '专利法',
                'object': '创造性',
                'relation': 'defines',
                'properties': {
                    'article': '第二十二条',
                    'confidence': 0.95
                }
            },
            {
                'subject': '专利法',
                'object': '实用性',
                'relation': 'defines',
                'properties': {
                    'article': '第二十二条',
                    'confidence': 0.95
                }
            },
            {
                'subject': '专利法实施细则',
                'object': '专利法',
                'relation': 'interprets',
                'properties': {
                    'relationship_type': '实施细则',
                    'confidence': 0.9
                }
            },
            {
                'subject': '发明专利',
                'object': '新颖性',
                'relation': 'requires',
                'properties': {
                    'requirement_type': '授权条件',
                    'confidence': 0.9
                }
            },
            {
                'subject': '发明专利',
                'object': '创造性',
                'relation': 'requires',
                'properties': {
                    'requirement_type': '授权条件',
                    'confidence': 0.9
                }
            },
            {
                'subject': '发明专利',
                'object': '实用性',
                'relation': 'requires',
                'properties': {
                    'requirement_type': '授权条件',
                    'confidence': 0.9
                }
            },
            {
                'subject': '权利要求书',
                'object': '说明书',
                'relation': 'related_to',
                'properties': {
                    'relationship_type': '配套文件',
                    'confidence': 0.95,
                    'article': '第二十六条'
                }
            },
            {
                'subject': '现有技术',
                'object': '新颖性',
                'relation': 'determines',
                'properties': {
                    'determination_type': '判断标准',
                    'confidence': 0.9
                }
            },
            {
                'subject': '专利侵权',
                'object': '专利法',
                'relation': 'governed_by',
                'properties': {
                    'legal_basis': '第十一条',
                    'confidence': 0.95
                }
            },
            {
                'subject': '专利无效宣告',
                'object': '专利法',
                'relation': 'provided_by',
                'properties': {
                    'legal_basis': '第四十五条',
                    'confidence': 0.95
                }
            },
            {
                'subject': '专利审查指南',
                'object': '专利法实施细则',
                'relation': 'implements',
                'properties': {
                    'implementation_type': '执行细则',
                    'confidence': 0.9
                }
            },
            {
                'subject': '优先权',
                'object': '专利法',
                'relation': 'granted_by',
                'properties': {
                    'legal_basis': '第二十九条',
                    'confidence': 0.95
                }
            }
        ]

        self.entities = test_entities
        self.relations = test_relations

        logger.info(f"✅ 加载了 {len(self.entities)} 个实体和 {len(self.relations)} 个关系")

    async def import_to_graph(self):
        """导入到知识图谱"""
        logger.info("🕸️ 开始导入到知识图谱...")

        # 初始化图空间
        success = await self.graph_builder.initialize_space()
        if not success:
            logger.error("❌ 初始化图空间失败")
            return False

        # 导入实体
        if self.entities:
            logger.info(f"📊 导入 {len(self.entities)} 个实体...")
            entity_ids = await self.graph_builder.add_entities(self.entities)
            logger.info(f"✅ 成功导入 {len(entity_ids)} 个实体")

        # 导入关系
        if self.relations:
            logger.info(f"🔗 导入 {len(self.relations)} 个关系...")
            relation_ids = await self.graph_builder.add_relations(self.relations)
            logger.info(f"✅ 成功导入 {len(relation_ids)} 个关系")

        # 构建示例子图
        if self.entities:
            sample_entities = [e['name'] for e in self.entities[:5] if 'name' in e]
            if sample_entities:
                logger.info("🎯 构建示例子图...")
                await self.graph_builder.build_subgraph(sample_entities, depth=2)

        # 获取统计信息
        stats = self.graph_builder.get_statistics()
        logger.info("\n📊 知识图谱统计:")
        logger.info(f"  模式: {stats.get('mode', 'unknown')}")
        logger.info(f"  实体总数: {stats.get('total_entities', 0)}")
        logger.info(f"  关系总数: {stats.get('total_relations', 0)}")

        if 'entities' in stats:
            logger.info("\n  实体类型分布:")
            for etype, count in stats['entities'].items():
                logger.info(f"    - {etype}: {count}")

        if 'relations' in stats:
            logger.info("\n  关系类型分布:")
            for rtype, count in stats['relations'].items():
                logger.info(f"    - {rtype}: {count}")

        # 保存统计报告
        report_file = self.data_path / f"patent_kg_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'import_time': datetime.now().isoformat(),
                'statistics': stats,
                'entities_count': len(self.entities),
                'relations_count': len(self.relations),
                'data_source': '专利法律法规',
                'version': 'v1.0.0'
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 导入报告已保存: {report_file}")
        return True

    async def run(self):
        """运行导入流程"""
        logger.info("🚀 启动专利知识图谱导入器")
        logger.info("="*60)

        # 加载示例数据
        await self.load_sample_data()

        # 导入到知识图谱
        success = await self.import_to_graph()

        if success:
            logger.info("\n✅ 专利知识图谱导入完成！")
            logger.info("💡 图谱包含了专利法律法规的核心概念和关系")
            logger.info("🎯 可用于智能问答、专利检索、侵权分析等场景")
            logger.info("="*60)
        else:
            logger.error("\n❌ 专利知识图谱导入失败！")


async def main():
    """主函数"""
    importer = PatentKnowledgeGraphImporter()
    await importer.run()


if __name__ == "__main__":
    asyncio.run(main())
