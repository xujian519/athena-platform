#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律知识图谱数据整合工具
Legal Knowledge Graph Consolidation Tool

整合所有法律知识图谱数据为一个统一版本，清理冗余数据
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

class LegalKnowledgeGraphConsolidator:
    """法律知识图谱整合器"""

    def __init__(self):
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
        self.project_root = PROJECT_ROOT
        self.data_root = self.project_root / 'data'
        self.unified_kg_path = self.data_root / 'unified_legal_knowledge_graph.json'
        self.backup_dir = self.data_root / 'backup_consolidated_kgs'

        # 要整合的知识图谱文件列表
        self.kg_files_to_consolidate = [
            'fixed_legal_knowledge_graph/fixed_legal_knowledge_graph.json',
            'production_legal_knowledge_graph/production_legal_knowledge_graph.json',
            'legal_knowledge_graph_demo/legal_knowledge_graph_demo.json'
        ]

        # 要删除的冗余目录和文件
        self.redundant_paths = [
            'legal_knowledge_graph_enhanced',
            'law_knowledge_graph_new',
            'legal_clause_vector_db_poc',
            'ultra_fast_legal_vector_db',
            'very_large_scale_legal_kg'
        ]

    def create_backup(self):
        """创建数据备份"""
        logger.info('💾 创建数据备份...')

        self.backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        # 备份所有知识图谱文件
        for kg_file in self.kg_files_to_consolidate:
            source_path = self.data_root / kg_file
            if source_path.exists():
                dest_path = backup_path / kg_file
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                logger.info(f"  ✅ 备份: {kg_file}")

        logger.info(f"✅ 备份完成: {backup_path}")
        return backup_path

    def load_all_knowledge_graphs(self):
        """加载所有知识图谱数据"""
        logger.info('📚 加载知识图谱数据...')

        all_entities = []
        all_relations = []
        entity_names = set()
        entity_sources = {}

        kg_stats = {}

        for kg_file in self.kg_files_to_consolidate:
            kg_path = self.data_root / kg_file
            if not kg_path.exists():
                logger.info(f"  📂 跳过不存在的文件: {kg_file}")
                continue

            try:
                with open(kg_path, 'r', encoding='utf-8') as f:
                    kg_data = json.load(f)

                entities = kg_data.get('entities', [])
                relations = kg_data.get('relations', [])

                # 记录统计信息
                kg_stats[kg_file] = {
                    'entities': len(entities),
                    'relations': len(relations),
                    'file_size_mb': round(kg_path.stat().st_size / 1024 / 1024, 2)
                }

                logger.info(f"  📖 加载: {kg_file} ({len(entities)} 实体, {len(relations)} 关系)")

                # 处理实体，去重
                for entity in entities:
                    entity_name = entity.get('name', '').strip()
                    if not entity_name:
                        continue

                    # 如果实体已存在，选择质量更好的版本
                    if entity_name in entity_names:
                        existing_source = entity_sources[entity_name]['source']
                        current_source = kg_file

                        # 优先级：fixed > production > demo
                        priority = {
                            'fixed_legal_knowledge_graph': 3,
                            'production_legal_knowledge_graph': 2,
                            'legal_knowledge_graph_demo': 1
                        }

                        existing_priority = priority.get(existing_source.split('/')[0], 0)
                        current_priority = priority.get(current_source.split('/')[0], 0)

                        if current_priority > existing_priority:
                            # 替换现有实体
                            for i, existing_entity in enumerate(all_entities):
                                if existing_entity.get('name', '').strip() == entity_name:
                                    all_entities[i] = entity
                                    entity_sources[entity_name] = {
                                        'source': kg_file,
                                        'priority': current_priority
                                    }
                                    break
                    else:
                        # 新实体，直接添加
                        all_entities.append(entity)
                        entity_names.add(entity_name)
                        entity_sources[entity_name] = {
                            'source': kg_file,
                            'priority': kg_file
                        }

                # 添加关系
                for relation in relations:
                    # 确保关系的源和目标实体存在
                    source_name = relation.get('source', '').strip()
                    target_name = relation.get('target', '').strip()

                    if source_name in entity_names and target_name in entity_names:
                        all_relations.append(relation)

            except Exception as e:
                logger.info(f"  ❌ 加载失败: {kg_file} - {str(e)}")

        logger.info(f"✅ 加载完成: {len(all_entities)} 实体, {len(all_relations)} 关系")

        # 打印统计信息
        logger.info("\n📊 数据来源统计:")
        for file, stats in kg_stats.items():
            logger.info(f"  - {file}: {stats['entities']} 实体, {stats['relations']} 关系, {stats['file_size_mb']} MB")

        return all_entities, all_relations, kg_stats

    def enhance_entity_quality(self, entities):
        """增强实体数据质量"""
        logger.info('🔧 增强实体数据质量...')

        enhanced_entities = []
        entity_types = {}
        type_distribution = {}

        for entity in entities:
            enhanced_entity = entity.copy()

            # 标准化实体类型
            entity_type = enhanced_entity.get('type', '未知').strip()
            if not entity_type or entity_type == '未知':
                # 根据实体名称推断类型
                name = enhanced_entity.get('name', '').strip()
                if any(keyword in name for keyword in ['法', '条例', '规定', '办法', '规则']):
                    entity_type = '法律法规'
                elif any(keyword in name for keyword in ['法院', '检察院', '公安', '司法']):
                    entity_type = '司法机关'
                elif any(keyword in name for keyword in ['起诉', '审判', '上诉', '执行', '仲裁']):
                    entity_type = '法律程序'
                elif any(keyword in name for keyword in ['律师', '法官', '检察官', '当事人']):
                    entity_type = '法律人员'
                else:
                    entity_type = '法律实体'

            enhanced_entity['type'] = entity_type
            enhanced_entity['entity_type'] = entity_type

            # 添加元数据
            if 'confidence' not in enhanced_entity:
                enhanced_entity['confidence'] = 0.8

            if 'created_at' not in enhanced_entity:
                enhanced_entity['created_at'] = datetime.now().isoformat()

            # 统计类型分布
            type_distribution[entity_type] = type_distribution.get(entity_type, 0) + 1

            enhanced_entities.append(enhanced_entity)

        # 打印类型分布
        logger.info('📋 实体类型分布:')
        for entity_type, count in sorted(type_distribution.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {entity_type}: {count}")

        return enhanced_entities

    def enhance_relation_quality(self, relations):
        """增强关系数据质量"""
        logger.info('🔗 增强关系数据质量...')

        enhanced_relations = []
        relation_types = {}

        for relation in relations:
            enhanced_relation = relation.copy()

            # 标准化关系类型
            relation_type = enhanced_relation.get('type', '').strip()
            if not relation_type:
                relation_type = 'RELATED_TO'

            enhanced_relation['type'] = relation_type

            # 添加元数据
            if 'confidence' not in enhanced_relation:
                enhanced_relation['confidence'] = 0.7

            if 'created_at' not in enhanced_relation:
                enhanced_relation['created_at'] = datetime.now().isoformat()

            # 统计关系类型
            relation_types[relation_type] = relation_types.get(relation_type, 0) + 1

            enhanced_relations.append(enhanced_relation)

        # 打印关系类型分布
        logger.info('🔗 关系类型分布:')
        for rel_type, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {rel_type}: {count}")

        return enhanced_relations

    def build_unified_knowledge_graph(self, entities, relations):
        """构建统一知识图谱"""
        logger.info('🏗️ 构建统一知识图谱...')

        # 增强数据质量
        enhanced_entities = self.enhance_entity_quality(entities)
        enhanced_relations = self.enhance_relation_quality(relations)

        # 构建统一知识图谱数据结构
        unified_kg = {
            'metadata': {
                'name': '统一法律知识图谱',
                'description': '整合所有来源的法律知识图谱数据',
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'source_count': len(self.kg_files_to_consolidate),
                'consolidation_method': '优先级合并 + 质量增强'
            },
            'statistics': {
                'total_entities': len(enhanced_entities),
                'total_relations': len(enhanced_relations),
                'entity_types': len(set(e['type'] for e in enhanced_entities)),
                'relation_types': len(set(r['type'] for r in enhanced_relations))
            },
            'entities': enhanced_entities,
            'relations': enhanced_relations
        }

        return unified_kg

    def save_unified_knowledge_graph(self, unified_kg):
        """保存统一知识图谱"""
        logger.info('💾 保存统一知识图谱...')

        # 保存为JSON文件
        with open(self.unified_kg_path, 'w', encoding='utf-8') as f:
            json.dump(unified_kg, f, ensure_ascii=False, indent=2)

        # 创建统计报告
        stats_report = {
            'consolidation_time': datetime.now().isoformat(),
            'unified_kg_path': str(self.unified_kg_path.relative_to(self.project_root)),
            'statistics': unified_kg['statistics'],
            'metadata': unified_kg['metadata']
        }

        stats_path = self.data_root / 'unified_legal_kg_statistics.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats_report, f, ensure_ascii=False, indent=2)

        file_size_mb = round(self.unified_kg_path.stat().st_size / 1024 / 1024, 2)
        logger.info(f"✅ 统一知识图谱已保存: {self.unified_kg_path}")
        logger.info(f"📊 文件大小: {file_size_mb} MB")
        logger.info(f"📄 统计报告: {stats_path}")

        return self.unified_kg_path, stats_path

    def cleanup_redundant_data(self):
        """清理冗余数据"""
        logger.info('🧹 清理冗余数据...')

        cleaned_count = 0

        # 清理冗余的知识图谱文件
        for kg_file in self.kg_files_to_consolidate:
            kg_path = self.data_root / kg_file
            if kg_path.exists() and kg_path != self.unified_kg_path:
                try:
                    kg_path.unlink()
                    cleaned_count += 1
                    logger.info(f"  🗑️ 删除: {kg_file}")
                except Exception as e:
                    logger.info(f"  ❌ 删除失败: {kg_file} - {str(e)}")

        # 清理冗余目录
        for redundant_path in self.redundant_paths:
            path_to_delete = self.data_root / redundant_path
            if path_to_delete.exists():
                try:
                    if path_to_delete.is_dir():
                        shutil.rmtree(path_to_delete)
                    else:
                        path_to_delete.unlink()
                    cleaned_count += 1
                    logger.info(f"  🗑️ 删除目录: {redundant_path}")
                except Exception as e:
                    logger.info(f"  ❌ 删除失败: {redundant_path} - {str(e)}")

        logger.info(f"✅ 清理完成: {cleaned_count} 个项目")
        return cleaned_count

    def generate_cypher_script(self, unified_kg):
        """生成TuGraph导入脚本"""
        logger.info('📝 生成TuGraph导入脚本...')

        entities = unified_kg['entities']
        relations = unified_kg['relations']

        cypher_content = f"""-- 统一法律知识图谱TuGraph导入脚本
-- 生成时间: {datetime.now().isoformat()}
-- 实体数量: {len(entities)}
-- 关系数量: {len(relations)}

-- 清理现有数据
MATCH (n) DETACH DELETE n;

-- 创建约束和索引
CREATE CONSTRAINT FOR n:LegalEntity REQUIRE n.name NoneUNIQUE;
CREATE INDEX ON :LegalEntity(entity_type);
CREATE INDEX ON :LegalEntity(confidence);

-- 创建实体节点
"""

        # 按类型分组创建实体
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get('type', 'LegalEntity').replace(' ', '_')
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        for entity_type, type_entities in entities_by_type.items():
            cypher_content += f"\n-- 创建{entity_type}实体\n"
            for entity in type_entities:
                name = entity.get('name', '').replace('"', '\\"')
                entity_type_display = entity.get('type', '未知')
                confidence = entity.get('confidence', 0.8)
                source = entity.get('source', '统一知识图谱').replace('"', '\\"')

                cypher_content += f'MERGE (n:{entity_type} {{name: '{name}''
                cypher_content += f', entity_type: '{entity_type_display}''
                cypher_content += f', confidence: {confidence}'
                if source:
                    cypher_content += f', source: '{source}''
                cypher_content += '});\n'

        # 创建关系
        cypher_content += "\n-- 创建关系\n"
        for i, relation in enumerate(relations):
            source = relation.get('source', '').replace('"', '\\"')
            target = relation.get('target', '').replace('"', '\\"')
            rel_type = relation.get('type', 'RELATED_TO').replace(' ', '_').upper()
            confidence = relation.get('confidence', 0.7)

            if source and target:
                cypher_content += f'MATCH (a), (b) WHERE a.name = '{source}' AND b.name = '{target}'\n'
                cypher_content += f'MERGE (a)-[r:{rel_type}]->(b);\n\n'

        # 添加示例查询
        cypher_content += """
-- 示例查询
-- 查看实体类型分布
// MATCH (n) RETURN n.entity_type, COUNT(n) ORDER BY COUNT(n) DESC;

-- 查看核心法律实体
// MATCH (n) WHERE n.name CONTAINS '法' RETURN n LIMIT 20;

-- 查看关系网络
// MATCH (a)-[r]->(b) RETURN a.name, type(r), b.name LIMIT 20;

-- 统计信息
// MATCH (n) RETURN COUNT(n) as total_entities;
// MATCH ()-[r]->() RETURN COUNT(r) as total_relations;
"""

        # 保存Cypher脚本
        cypher_path = self.data_root / 'unified_legal_kg_import.cypher'
        with open(cypher_path, 'w', encoding='utf-8') as f:
            f.write(cypher_content)

        logger.info(f"✅ Cypher脚本已生成: {cypher_path}")
        return cypher_path

    def run_consolidation(self):
        """运行完整整合流程"""
        logger.info('🚀 开始法律知识图谱数据整合')
        logger.info(str('='*60))

        try:
            # 1. 创建备份
            backup_path = self.create_backup()

            # 2. 加载所有知识图谱数据
            entities, relations, kg_stats = self.load_all_knowledge_graphs()

            if not entities:
                logger.info('❌ 没有找到有效的知识图谱数据')
                return False

            # 3. 构建统一知识图谱
            unified_kg = self.build_unified_knowledge_graph(entities, relations)

            # 4. 保存统一知识图谱
            kg_path, stats_path = self.save_unified_knowledge_graph(unified_kg)

            # 5. 生成Cypher导入脚本
            cypher_path = self.generate_cypher_script(unified_kg)

            # 6. 清理冗余数据
            cleaned_count = self.cleanup_redundant_data()

            logger.info(str('='*60))
            logger.info('🎉 法律知识图谱数据整合完成!')
            logger.info(f"📊 统一知识图谱: {unified_kg['statistics']['total_entities']} 实体")
            logger.info(f"🔗 关系数量: {unified_kg['statistics']['total_relations']}")
            logger.info(f"📁 保存路径: {kg_path}")
            logger.info(f"📝 Cypher脚本: {cypher_path}")
            logger.info(f"🧹 清理项目: {cleaned_count} 个")
            logger.info(f"💾 备份位置: {backup_path}")

            return True

        except Exception as e:
            logger.info(f"❌ 整合过程异常: {str(e)}")
            return False

def main():
    """主函数"""
    logger.info('🔗 法律知识图谱数据整合工具')
    logger.info('整合所有法律知识图谱数据为一个统一版本')
    logger.info(str('='*60))

    # 创建整合器
    consolidator = LegalKnowledgeGraphConsolidator()

    # 运行整合
    success = consolidator.run_consolidation()

    if success:
        logger.info("\n✅ 法律知识图谱整合成功完成！")
        logger.info('🎯 下一步操作建议:')
        logger.info('1. 重新导入TuGraph数据库')
        logger.info('2. 修复API服务连接')
        logger.info('3. 验证端到端功能')
    else:
        logger.info("\n❌ 法律知识图谱整合失败")

if __name__ == '__main__':
    main()
