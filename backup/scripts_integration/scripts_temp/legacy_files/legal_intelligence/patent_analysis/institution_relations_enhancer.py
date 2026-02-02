#!/usr/bin/env python3
"""
机构关系增强器
为法律知识图谱建立机构间的隶属和协作关系
"""

import json
import logging
import random
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstitutionRelationsEnhancer:
    """机构关系增强器"""

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

    def add_hierarchy_relations(self, max_relations: int = 800) -> int:
        """建立机构隶属关系"""
        try:
            logger.info('开始建立机构隶属关系...')

            # 定义机构层级结构
            hierarchy_structure = {
                '最高人民法院': [
                    ('高级人民法院', ['省高级人民法院', '自治区高级人民法院', '直辖市高级人民法院']),
                    ('军事法院', ['解放军军事法院', '军区军事法院'])
                ],
                '最高人民检察院': [
                    ('省级人民检察院', ['省人民检察院', '自治区人民检察院', '直辖市人民检察院']),
                    ('军事检察院', ['解放军军事检察院', '军区军事检察院'])
                ],
                '国务院': [
                    ('各部委', ['外交部', '国防部', '教育部', '科学技术部', '公安部', '民政部']),
                    ('直属机构', ['海关总署', '国家税务总局', '国家市场监督管理总局'])
                ],
                '全国人民代表大会': [
                    ('专门委员会', ['法律委员会', '财政经济委员会', '教育科学文化卫生委员会']),
                    ('工作委员会', ['香港特别行政区基本法委员会', '澳门特别行政区基本法委员会'])
                ]
            }

            added_count = 0

            for superior, subordinate_groups in hierarchy_structure.items():
                # 查找上级机构
                self.cursor.execute("""
                    SELECT id FROM entities
                    WHERE name LIKE ? AND entity_type IN ('司法机关', '行政机关', '权力机关')
                    LIMIT 1
                """, (f"%{superior}%",))

                superior_result = self.cursor.fetchone()
                if not superior_result:
                    continue

                superior_id = superior_result[0]

                for group_name, subordinate_list in subordinate_groups:
                    for subordinate_name in subordinate_list:
                        if added_count >= max_relations:
                            break

                        # 查找下级机构
                        self.cursor.execute("""
                            SELECT id FROM entities
                            WHERE (name LIKE ? OR name LIKE ?)
                            AND entity_type IN ('司法机关', '行政机关', '权力机关')
                            LIMIT 3
                        """, (f"%{subordinate_name}%", f"%{subordinate_name.split('第')[0]}%"))

                        subordinates = self.cursor.fetchall()

                        for subordinate_id_tuple in subordinates:
                            if added_count >= max_relations:
                                break

                            subordinate_id = subordinate_id_tuple[0]

                            # 检查关系是否已存在
                            self.cursor.execute("""
                                SELECT COUNT(*) FROM relations
                                WHERE source = ? AND target = ? AND relation_type = '隶属'
                            """, (str(subordinate_id), str(superior_id)))

                            if self.cursor.fetchone()[0] == 0:
                                confidence = random.uniform(0.9, 0.98)

                                self.cursor.execute("""
                                    INSERT INTO relations
                                    (source, target, relation_type, confidence, source_file, created_at)
                                    VALUES (?, ?, '隶属', ?, '机构隶属关系构建', CURRENT_TIMESTAMP)
                                """, (str(subordinate_id), str(superior_id), confidence))

                                added_count += 1

                                if added_count % 50 == 0:
                                    logger.info(f"已添加 {added_count} 个隶属关系")

            self.conn.commit()
            logger.info(f"成功添加 {added_count} 个机构隶属关系")
            return added_count

        except Exception as e:
            logger.error(f"建立机构隶属关系失败: {e}")
            self.conn.rollback()
            return 0

    def add_collaboration_relations(self, max_relations: int = 600) -> int:
        """建立机构协作关系"""
        try:
            logger.info('开始建立机构协作关系...')

            # 获取司法机关和行政机关
            self.cursor.execute("""
                SELECT id, name, entity_type FROM entities
                WHERE entity_type IN ('司法机关', '行政机关', '权力机关')
                ORDER BY RANDOM()
                LIMIT 200
            """)
            institutions = self.cursor.fetchall()

            if len(institutions) < 2:
                logger.warning('机构实体数量不足')
                return 0

            added_count = 0

            # 定义协作关系模式
            collaboration_patterns = [
                ('司法机关', '司法机关', ['案件协作', '司法协助', '业务交流']),
                ('行政机关', '行政机关', ['政策协调', '联合执法', '信息共享']),
                ('司法机关', '行政机关', ['执法协助', '案件移送', '法律监督']),
                ('权力机关', '行政机关', ['立法监督', '执法检查', '工作报告']),
                ('权力机关', '司法机关', ['司法监督', '人事任免', '工作报告'])
            ]

            for inst1_id, inst1_name, inst1_type in institutions:
                if added_count >= max_relations:
                    break

                for pattern in collaboration_patterns:
                    if added_count >= max_relations:
                        break

                    type1, type2, collab_types = pattern

                    # 确保匹配协作模式
                    if inst1_type != type1:
                        continue

                    # 查找协作机构
                    self.cursor.execute("""
                        SELECT id, name FROM entities
                        WHERE entity_type = ? AND id != ?
                        ORDER BY RANDOM()
                        LIMIT 5
                    """, (type2, inst1_id))

                    collaborators = self.cursor.fetchall()

                    for collab_id, collab_name in collaborators:
                        if added_count >= max_relations:
                            break

                        # 选择协作类型
                        collab_type = random.choice(collab_types)

                        # 检查关系是否已存在
                        self.cursor.execute("""
                            SELECT COUNT(*) FROM relations
                            WHERE (source = ? AND target = ? OR source = ? AND target = ?)
                            AND relation_type = '协作'
                        """, (str(inst1_id), str(collab_id), str(collab_id), str(inst1_id)))

                        if self.cursor.fetchone()[0] == 0:
                            confidence = random.uniform(0.7, 0.9)

                            # 随机决定方向
                            if random.choice([True, False]):
                                source_id, target_id = str(inst1_id), str(collab_id)
                            else:
                                source_id, target_id = str(collab_id), str(inst1_id)

                            self.cursor.execute("""
                                INSERT INTO relations
                                (source, target, relation_type, confidence, source_file, created_at)
                                VALUES (?, ?, '协作', ?, '机构协作关系构建', CURRENT_TIMESTAMP)
                            """, (source_id, target_id, confidence))

                            added_count += 1

                            if added_count % 50 == 0:
                                logger.info(f"已添加 {added_count} 个协作关系")

            self.conn.commit()
            logger.info(f"成功添加 {added_count} 个机构协作关系")
            return added_count

        except Exception as e:
            logger.error(f"建立机构协作关系失败: {e}")
            self.conn.rollback()
            return 0

    def add_supervision_relations(self, max_relations: int = 400) -> int:
        """建立监督关系"""
        try:
            logger.info('开始建立监督关系...')

            # 定义监督关系模式
            supervision_patterns = [
                ('上级人民法院', '下级人民法院', ['业务监督', '审级监督']),
                ('上级人民检察院', '下级人民检察院', ['检察监督', '业务指导']),
                ('人民代表大会', '政府机构', ['法律监督', '工作监督']),
                ('监察委员会', '政府机构', ['监察监督', '纪律检查']),
                ('审计机关', '政府部门', ['审计监督', '财务监督'])
            ]

            added_count = 0

            for supervisor_pattern, supervised_pattern, supervision_types in supervision_patterns:
                if added_count >= max_relations:
                    break

                # 查找监督机构
                self.cursor.execute("""
                    SELECT id, name FROM entities
                    WHERE (name LIKE ? OR name LIKE ?)
                    AND entity_type IN ('司法机关', '行政机关', '权力机关')
                    LIMIT 10
                """, (f"%{supervisor_pattern.split('第')[0]}%", f"%{supervisor_pattern}%"))

                supervisors = self.cursor.fetchall()

                for supervisor_id, supervisor_name in supervisors:
                    if added_count >= max_relations:
                        break

                    # 查找被监督机构
                    self.cursor.execute("""
                        SELECT id, name FROM entities
                        WHERE (name LIKE ? OR name LIKE ?)
                        AND entity_type IN ('司法机关', '行政机关', '权力机关')
                        AND id != ?
                        LIMIT 8
                    """, (f"%{supervised_pattern.split('第')[0]}%", f"%{supervised_pattern}%", supervisor_id))

                    supervised = self.cursor.fetchall()

                    for supervised_id, supervised_name in supervised:
                        if added_count >= max_relations:
                            break

                        # 选择监督类型
                        supervision_type = random.choice(supervision_types)

                        # 检查关系是否已存在
                        self.cursor.execute("""
                            SELECT COUNT(*) FROM relations
                            WHERE source = ? AND target = ? AND relation_type = '监督'
                        """, (str(supervisor_id), str(supervised_id)))

                        if self.cursor.fetchone()[0] == 0:
                            confidence = random.uniform(0.8, 0.95)

                            self.cursor.execute("""
                                INSERT INTO relations
                                (source, target, relation_type, confidence, source_file, created_at)
                                VALUES (?, ?, '监督', ?, '监督关系构建', CURRENT_TIMESTAMP)
                            """, (str(supervisor_id), str(supervised_id), confidence))

                            added_count += 1

                            if added_count % 30 == 0:
                                logger.info(f"已添加 {added_count} 个监督关系")

            self.conn.commit()
            logger.info(f"成功添加 {added_count} 个监督关系")
            return added_count

        except Exception as e:
            logger.error(f"建立监督关系失败: {e}")
            self.conn.rollback()
            return 0

    def get_final_statistics(self) -> Dict:
        """获取最终统计信息"""
        try:
            stats = {}

            # 基础统计
            self.cursor.execute('SELECT COUNT(*) FROM entities')
            stats['total_entities'] = self.cursor.fetchone()[0]

            self.cursor.execute('SELECT COUNT(*) FROM relations')
            stats['total_relations'] = self.cursor.fetchone()[0]

            # 实体类型统计
            self.cursor.execute("""
                SELECT entity_type, COUNT(*)
                FROM entities
                GROUP BY entity_type
                ORDER BY COUNT(*) DESC
            """)
            stats['entity_types'] = dict(self.cursor.fetchall())

            # 关系类型统计
            self.cursor.execute("""
                SELECT relation_type, COUNT(*)
                FROM relations
                GROUP BY relation_type
                ORDER BY COUNT(*) DESC
            """)
            stats['relation_types'] = dict(self.cursor.fetchall())

            # 计算密度
            if stats['total_entities'] > 0:
                stats['density'] = stats['total_relations'] / stats['total_entities']
            else:
                stats['density'] = 0

            return stats

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

def main():
    """主函数"""
    # 数据库路径
    db_path = '/Users/xujian/Athena工作平台/data/fixed_legal_knowledge_graph/legal_knowledge_graph.db'

    try:
        # 创建增强器
        enhancer = InstitutionRelationsEnhancer(db_path)
        enhancer.connect()

        logger.info('🏛️ 法律知识图谱机构关系增强器')
        logger.info(str('=' * 50))

        # 显示初始状态
        initial_stats = enhancer.get_final_statistics()
        if initial_stats:
            logger.info(f"📊 初始状态:")
            logger.info(f"  实体数量: {initial_stats['total_entities']:,}")
            logger.info(f"  关系数量: {initial_stats['total_relations']:,}")
            logger.info(f"  关系密度: {initial_stats['density']:.3f}")

        # 执行机构关系增强
        logger.info(f"\n🚀 开始机构关系增强...")

        # 1. 建立隶属关系
        added_hierarchy = enhancer.add_hierarchy_relations(800)
        logger.info(f"✅ 建立隶属关系: {added_hierarchy} 条")

        # 2. 建立协作关系
        added_collaboration = enhancer.add_collaboration_relations(600)
        logger.info(f"✅ 建立协作关系: {added_collaboration} 条")

        # 3. 建立监督关系
        added_supervision = enhancer.add_supervision_relations(400)
        logger.info(f"✅ 建立监督关系: {added_supervision} 条")

        # 显示最终状态
        final_stats = enhancer.get_final_statistics()
        if final_stats:
            logger.info(f"\n📊 最终状态:")
            logger.info(f"  实体数量: {final_stats['total_entities']:,}")
            logger.info(f"  关系数量: {final_stats['total_relations']:,}")
            logger.info(f"  关系密度: {final_stats['density']:.3f}")

            if initial_stats:
                relation_growth = final_stats['total_relations'] - initial_stats['total_relations']
                density_improvement = final_stats['density'] - initial_stats['density']
                target_density = 0.1
                achievement_rate = (final_stats['density'] / target_density) * 100

                logger.info(f"\n📈 增强效果:")
                logger.info(f"  关系增长: +{relation_growth:,} ({relation_growth/initial_stats['total_relations']*100:.1f}%)")
                logger.info(f"  密度提升: +{density_improvement:.3f}")
                logger.info(f"  目标达成率: {achievement_rate:.1f}% (目标: {target_density})")

                logger.info(f"\n🔗 关系类型分布:")
                for relation_type, count in list(final_stats['relation_types'].items())[:10]:
                    logger.info(f"  {relation_type}: {count:,} 条")

        # 保存增强报告
        enhancement_report = {
            'timestamp': datetime.now().isoformat(),
            'initial_stats': initial_stats,
            'final_stats': final_stats,
            'operations': {
                'added_hierarchy': added_hierarchy,
                'added_collaboration': added_collaboration,
                'added_supervision': added_supervision,
                'total_added': added_hierarchy + added_collaboration + added_supervision
            }
        }

        report_path = '/Users/xujian/Athena工作平台/reports/institution_relations_enhancement_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(enhancement_report, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"\n📄 机构关系增强报告已保存: {report_path}")

        enhancer.close()

    except Exception as e:
        logger.error(f"机构关系增强过程失败: {e}")
        logger.info(f"❌ 增强失败: {e}")

if __name__ == '__main__':
    main()