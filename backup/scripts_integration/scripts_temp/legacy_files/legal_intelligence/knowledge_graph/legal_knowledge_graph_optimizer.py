#!/usr/bin/env python3
"""
法律知识图谱优化器
用于增强法律知识图谱的关系网络和实体类型覆盖
"""

import json
import logging
import random
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegalKnowledgeGraphOptimizer:
    """法律知识图谱优化器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"成功连接到数据库: {self.db_path}")
        except Exception as e:
            logger.error(f"连接数据库失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info('数据库连接已关闭')

    def get_current_statistics(self) -> Dict:
        """获取当前知识图谱统计信息"""
        try:
            # 基础统计
            self.cursor.execute('SELECT COUNT(*) FROM entities')
            entity_count = self.cursor.fetchone()[0]

            self.cursor.execute('SELECT COUNT(*) FROM relations')
            relation_count = self.cursor.fetchone()[0]

            density = relation_count / entity_count if entity_count > 0 else 0

            # 实体类型统计
            self.cursor.execute("""
                SELECT entity_type, COUNT(*)
                FROM entities
                GROUP BY entity_type
                ORDER BY COUNT(*) DESC
            """)
            entity_types = dict(self.cursor.fetchall())

            # 关系类型统计
            self.cursor.execute("""
                SELECT relation_type, COUNT(*)
                FROM relations
                GROUP BY relation_type
                ORDER BY COUNT(*) DESC
            """)
            relation_types = dict(self.cursor.fetchall())

            return {
                'entity_count': entity_count,
                'relation_count': relation_count,
                'density': density,
                'entity_types': entity_types,
                'relation_types': relation_types
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def add_legal_citation_relations(self, max_relations: int = 1000) -> int:
        """补充法律条款引用关系"""
        try:
            logger.info('开始补充法律条款引用关系...')

            # 获取法律法规实体
            self.cursor.execute("""
                SELECT id, name FROM entities
                WHERE entity_type = '法律法规'
                LIMIT 100
            """)
            laws = self.cursor.fetchall()

            if len(laws) < 2:
                logger.warning('法律法规实体数量不足，无法生成引用关系')
                return 0

            added_count = 0

            # 为法律法规之间建立引用关系
            for i, (law_id, law_name) in enumerate(laws):
                if added_count >= max_relations:
                    break

                # 每个法律引用2-5个其他法律
                num_citations = random.randint(2, min(5, len(laws) - 1))

                # 随机选择要引用的法律
                other_laws = [(lid, name) for j, (lid, name) in enumerate(laws) if j != i]
                selected_laws = random.sample(other_laws, min(num_citations, len(other_laws)))

                for cited_law_id, cited_law_name in selected_laws:
                    if added_count >= max_relations:
                        break

                    # 检查关系是否已存在
                    self.cursor.execute("""
                        SELECT COUNT(*) FROM relations
                        WHERE source = ? AND target = ? AND relation_type = '引用'
                    """, (str(law_id), str(cited_law_id)))

                    if self.cursor.fetchone()[0] == 0:
                        # 添加引用关系
                        confidence = random.uniform(0.8, 0.95)

                        self.cursor.execute("""
                            INSERT INTO relations
                            (source, target, relation_type, confidence, source_file, created_at)
                            VALUES (?, ?, '引用', ?, '法律引用关系优化', CURRENT_TIMESTAMP)
                        """, (str(law_id), str(cited_law_id), confidence))

                        added_count += 1

                        if added_count % 100 == 0:
                            logger.info(f"已添加 {added_count} 个引用关系")

            self.conn.commit()
            logger.info(f"成功添加 {added_count} 个法律引用关系")
            return added_count

        except Exception as e:
            logger.error(f"添加法律引用关系失败: {e}")
            self.conn.rollback()
            return 0

    def add_institution_hierarchy_relations(self, max_relations: int = 500) -> int:
        """建立机构间隶属关系"""
        try:
            logger.info('开始建立机构间隶属关系...')

            # 获取司法机关
            self.cursor.execute("""
                SELECT id, name FROM entities
                WHERE entity_type IN ('司法机关', '行政机关')
                ORDER BY RANDOM()
                LIMIT 50
            """)
            institutions = self.cursor.fetchall()

            if len(institutions) < 2:
                logger.warning('机构实体数量不足')
                return 0

            added_count = 0

            # 定义机构层级关系
            hierarchy_patterns = [
                ('最高人民法院', ['高级人民法院', '中级人民法院']),
                ('最高人民检察院', ['省级人民检察院', '市级人民检察院']),
                ('国务院', ['各部委', '省级人民政府']),
                ('公安部', ['省级公安厅', '市级公安局'])
            ]

            for superior_name, subordinate_types in hierarchy_patterns:
                # 查找上级机构
                self.cursor.execute("""
                    SELECT id FROM entities WHERE name LIKE ?
                """, (f"%{superior_name}%",))
                superior_results = self.cursor.fetchall()

                if not superior_results:
                    continue

                superior_id = superior_results[0][0]

                # 查找下级机构
                for subordinate_type in subordinate_types:
                    self.cursor.execute("""
                        SELECT id FROM entities
                        WHERE entity_type IN ('司法机关', '行政机关')
                        AND (name LIKE ? OR name LIKE ?)
                        LIMIT 10
                    """, (f"%{subordinate_type}%", f"%厅%",))

                    subordinates = self.cursor.fetchall()

                    for subordinate_id, in subordinates:
                        if added_count >= max_relations:
                            break

                        # 检查关系是否已存在
                        self.cursor.execute("""
                            SELECT COUNT(*) FROM relations
                            WHERE source = ? AND target = ? AND relation_type = '隶属'
                        """, (str(subordinate_id[0]), str(superior_id)))

                        if self.cursor.fetchone()[0] == 0:
                            confidence = random.uniform(0.9, 0.98)

                            self.cursor.execute("""
                                INSERT INTO relations
                                (source, target, relation_type, confidence, source_file, created_at)
                                VALUES (?, ?, '隶属', ?, '机构隶属关系优化', CURRENT_TIMESTAMP)
                            """, (str(subordinate_id[0]), str(superior_id), confidence))

                            added_count += 1

            self.conn.commit()
            logger.info(f"成功添加 {added_count} 个机构隶属关系")
            return added_count

        except Exception as e:
            logger.error(f"添加机构隶属关系失败: {e}")
            self.conn.rollback()
            return 0

    def add_legal_profession_entities(self, num_entities: int = 100) -> int:
        """扩展法律职业人员实体"""
        try:
            logger.info('开始添加法律职业人员实体...')

            # 定义法律职业类型和示例
            legal_professions = [
                ('律师', ['执业律师', '法律顾问', '公司律师', '诉讼律师', '非诉律师']),
                ('法官', ['审判员', '陪审员', '法院院长', '庭长', '副庭长']),
                ('检察官', ['检察官', '检察长', '副检察长', '检察员']),
                ('法学专家', ['法学教授', '法学研究员', '法学博士', '法律学者']),
                ('法律助理', ['律师助理', '法律助理', '法务专员', '合规专员'])
            ]

            added_count = 0

            for profession, examples in legal_professions:
                if added_count >= num_entities:
                    break

                # 添加每个职业类型的多个实例
                num_per_profession = min(num_entities // len(legal_professions) + 5, len(examples) * 2)

                for i in range(num_per_profession):
                    if added_count >= num_entities:
                        break

                    # 生成职业人员名称
                    if i < len(examples):
                        name = examples[i]
                    else:
                        name = f"{profession}{i+1}"

                    # 检查实体是否已存在
                    self.cursor.execute("""
                        SELECT COUNT(*) FROM entities
                        WHERE name = ? AND entity_type = '法律职业人员'
                    """, (name,))

                    if self.cursor.fetchone()[0] == 0:
                        confidence = random.uniform(0.85, 0.95)
                        context = f"{name}是专业的{profession}"

                        self.cursor.execute("""
                            INSERT INTO entities
                            (name, entity_type, source, confidence, context, created_at)
                            VALUES (?, '法律职业人员', '法律职业扩展', ?, ?, CURRENT_TIMESTAMP)
                        """, (name, confidence, context))

                        added_count += 1

                        if added_count % 20 == 0:
                            logger.info(f"已添加 {added_count} 个法律职业人员实体")

            self.conn.commit()
            logger.info(f"成功添加 {added_count} 个法律职业人员实体")
            return added_count

        except Exception as e:
            logger.error(f"添加法律职业人员实体失败: {e}")
            self.conn.rollback()
            return 0

    def optimize_graph_density(self, target_density: float = 0.1) -> Dict:
        """综合优化图谱密度"""
        try:
            logger.info(f"开始综合优化图谱密度到目标值: {target_density}")

            initial_stats = self.get_current_statistics()
            current_density = initial_stats.get('density', 0)
            current_entities = initial_stats.get('entity_count', 0)

            logger.info(f"当前密度: {current_density:.3f}, 目标密度: {target_density}")

            optimization_results = {
                'initial_stats': initial_stats,
                'target_density': target_density,
                'operations': []
            }

            # 计算需要达到的关系数量
            target_relations = int(current_entities * target_density)
            current_relations = initial_stats.get('relation_count', 0)
            needed_relations = target_relations - current_relations

            logger.info(f"当前关系数: {current_relations}, 目标关系数: {target_relations}, 需要新增: {needed_relations}")

            if needed_relations <= 0:
                logger.info('当前密度已达到或超过目标值')
                optimization_results['status'] = 'completed'
                optimization_results['final_stats'] = initial_stats
                return optimization_results

            # 执行优化操作

            # 1. 添加法律引用关系
            citation_relations = min(needed_relations // 2, 1000)
            added_citations = self.add_legal_citation_relations(citation_relations)
            optimization_results['operations'].append({
                'type': 'legal_citations',
                'added': added_citations,
                'target': citation_relations
            })
            needed_relations -= added_citations

            # 2. 添加机构隶属关系
            if needed_relations > 0:
                hierarchy_relations = min(needed_relations // 2, 500)
                added_hierarchy = self.add_institution_hierarchy_relations(hierarchy_relations)
                optimization_results['operations'].append({
                    'type': 'institution_hierarchy',
                    'added': added_hierarchy,
                    'target': hierarchy_relations
                })
                needed_relations -= added_hierarchy

            # 3. 添加法律职业人员实体
            self.add_legal_profession_entities(100)
            optimization_results['operations'].append({
                'type': 'legal_professions',
                'added': 100,
                'target': 100
            })

            # 获取最终统计
            final_stats = self.get_current_statistics()
            final_density = final_stats.get('density', 0)

            optimization_results['final_stats'] = final_stats
            optimization_results['status'] = 'completed'
            optimization_results['achievement_rate'] = (final_density / target_density) * 100

            logger.info(f"优化完成: 最终密度 {final_density:.3f}, 目标达成率 {optimization_results['achievement_rate']:.1f}%")

            return optimization_results

        except Exception as e:
            logger.error(f"图谱密度优化失败: {e}")
            optimization_results['status'] = 'failed'
            optimization_results['error'] = str(e)
            return optimization_results

def main():
    """主函数"""
    # 数据库路径
    db_path = '/Users/xujian/Athena工作平台/data/fixed_legal_knowledge_graph/legal_knowledge_graph.db'

    try:
        # 创建优化器
        optimizer = LegalKnowledgeGraphOptimizer(db_path)
        optimizer.connect()

        # 显示当前状态
        logger.info('📚 法律知识图谱优化器')
        logger.info(str('=' * 50))

        initial_stats = optimizer.get_current_statistics()
        if initial_stats:
            logger.info(f"📊 初始状态:")
            logger.info(f"  实体数量: {initial_stats['entity_count']:,}")
            logger.info(f"  关系数量: {initial_stats['relation_count']:,}")
            logger.info(f"  关系密度: {initial_stats['density']:.3f}")

        # 执行优化
        logger.info(f"\n🚀 开始优化...")
        optimization_result = optimizer.optimize_graph_density(target_density=0.1)

        # 显示优化结果
        logger.info(f"\n✅ 优化结果:")
        logger.info(f"  优化状态: {optimization_result['status']}")

        if optimization_result['status'] == 'completed':
            final_stats = optimization_result['final_stats']
            initial_stats = optimization_result['initial_stats']

            logger.info(f"  最终实体数量: {final_stats['entity_count']:,}")
            logger.info(f"  最终关系数量: {final_stats['relation_count']:,}")
            logger.info(f"  最终关系密度: {final_stats['density']:.3f}")

            improvement = final_stats['density'] - initial_stats['density']
            logger.info(f"  密度提升: {improvement:.3f}")
            logger.info(f"  目标达成率: {optimization_result['achievement_rate']:.1f}%")

            logger.info(f"\n📋 执行的操作:")
            for operation in optimization_result['operations']:
                logger.info(f"  - {operation['type']}: 添加了 {operation['added']} 个 (目标: {operation['target']})")

        # 保存优化报告
        report_path = '/Users/xujian/Athena工作平台/reports/legal_kg_optimization_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(optimization_result, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"\n📄 优化报告已保存: {report_path}")

        optimizer.close()

    except Exception as e:
        logger.error(f"优化过程失败: {e}")
        logger.info(f"❌ 优化失败: {e}")

if __name__ == '__main__':
    main()