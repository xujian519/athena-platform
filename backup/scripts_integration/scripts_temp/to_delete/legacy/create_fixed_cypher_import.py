#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建修复版Cypher导入脚本
Create Fixed Cypher Import Script

根据已有的知识图谱JSON数据生成语法正确的Cypher导入脚本
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class FixedCypherGenerator:
    """修复版Cypher脚本生成器"""

    def __init__(self):
        self.project_root = Path('/Users/xujian/Athena工作平台')
        self.kg_json_path = self.project_root / 'data/fixed_legal_knowledge_graph/fixed_legal_knowledge_graph.json'
        self.output_cypher_path = self.project_root / 'data/fixed_legal_knowledge_graph/clean_legal_kg_import.cypher'

    def clean_string_for_cypher(self, text):
        """清理字符串以符合Cypher语法"""
        if not text:
            return ''

        # 移除换行符和多余空白
        text = str(text).strip()
        text = re.sub(r'\s+', ' ', text)

        # 移除可能导致语法错误的字符
        text = re.sub(r"['\']', '', text)

        # 限制长度
        if len(text) > 200:
            text = text[:200] + '...'

        return text

    def generate_cypher_script(self):
        """生成Cypher脚本"""
        # 读取知识图谱数据
        if not self.kg_json_path.exists():
            logger.info(f"❌ 知识图谱文件不存在: {self.kg_json_path}")
            return False

        with open(self.kg_json_path, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)

        entities = kg_data.get('entities', [])
        relations = kg_data.get('relations', [])

        logger.info(f"📊 处理 {len(entities)} 个实体和 {len(relations)} 个关系")

        # 生成Cypher脚本
        cypher_content = f"""-- 清理版法律知识图谱TuGraph导入脚本
-- 生成时间: {datetime.now().isoformat()}
-- 实体数量: {len(entities)}
-- 关系数量: {len(relations)}

-- 清理现有图（可选）
-- MATCH (n) DETACH DELETE n;

-- 创建节点约束
CREATE CONSTRAINT FOR n:LegalEntity REQUIRE n.name NoneUNIQUE;

-- 创建节点索引
CREATE INDEX ON :LegalEntity(name);
CREATE INDEX ON :LegalEntity(entity_type);

-- 创建法律实体节点
"""

        # 按实体类型分组
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get('type', '未知')
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # 为每种实体类型创建节点
        for entity_type, type_entities in entities_by_type.items():
            cypher_content += f"\n-- 创建{entity_type}实体\n"

            for i, entity in enumerate(type_entities):
                name = self.clean_string_for_cypher(entity.get('name', ''))
                source = self.clean_string_for_cypher(entity.get('source', ''))
                confidence = entity.get('confidence', 0.8)

                if name:  # 只创建有名称的实体
                    # 清理实体类型标签
                    clean_type = self.clean_string_for_cypher(entity_type).replace(' ', '_')
                    cypher_content += f'MERGE (n:{clean_type} {{name: '{name}', entity_type: '{entity_type}''

                    if source:
                        cypher_content += f', source: '{source}''
                    if confidence:
                        cypher_content += f', confidence: {confidence}'

                    cypher_content += '});\n'

        # 创建关系
        cypher_content += "\n-- 创建关系\n"

        for i, relation in enumerate(relations):
            source_name = self.clean_string_for_cypher(relation.get('source', ''))
            target_name = self.clean_string_for_cypher(relation.get('target', ''))
            rel_type = self.clean_string_for_cypher(relation.get('type', 'RELATED_TO'))

            if source_name and target_name and rel_type:
                # 清理关系类型
                clean_rel_type = re.sub(r'[^a-zA-Z0-9_]', '_', rel_type).upper()
                cypher_content += f'MATCH (a), (b) WHERE a.name = '{source_name}' AND b.name = '{target_name}'\n'
                cypher_content += f'MERGE (a)-[r:{clean_rel_type}]->(b);\n\n'

        # 添加一些示例查询
        cypher_content += """
-- 示例查询
-- 查看所有实体类型
// MATCH (n) RETURN DISTINCT n.entity_type, COUNT(n) ORDER BY COUNT(n) DESC;

-- 查看核心法律实体
// MATCH (n) WHERE n.name CONTAINS '法' RETURN n.name, n.entity_type LIMIT 20;

-- 查看关系网络
// MATCH (a)-[r]->(b) RETURN a.name, type(r), b.name LIMIT 20;
"""

        # 保存脚本
        with open(self.output_cypher_path, 'w', encoding='utf-8') as f:
            f.write(cypher_content)

        logger.info(f"✅ 修复版Cypher脚本已生成: {self.output_cypher_path}")
        logger.info(f"📝 脚本大小: {len(cypher_content)} 字符")
        return True

    def validate_cypher_syntax(self):
        """验证Cypher语法"""
        try:
            with open(self.output_cypher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查基本语法问题
            issues = []
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('--'):
                    continue

                # 检查未闭合的引号
                if line.count('"') % 2 != 0:
                    issues.append(f"第{i}行: 未闭合的引号 - {line[:50]}...")

                # 检查MERGE语句的基本格式
                if line.startswith('MERGE') and '{' in line and '}' not in line:
                    issues.append(f"第{i}行: MERGE语句可能未闭合 - {line[:50]}...")

            if issues:
                logger.info('⚠️ 发现潜在语法问题:')
                for issue in issues[:10]:  # 只显示前10个问题
                    logger.info(f"  - {issue}")
                return False
            else:
                logger.info('✅ Cypher语法检查通过')
                return True

        except Exception as e:
            logger.info(f"❌ 语法验证异常: {str(e)}")
            return False

    def run_generation(self):
        """运行完整生成流程"""
        logger.info('🔧 创建修复版Cypher导入脚本')
        logger.info(str('='*60))

        # 1. 生成脚本
        if not self.generate_cypher_script():
            logger.info('❌ 脚本生成失败')
            return False

        # 2. 验证语法
        if not self.validate_cypher_syntax():
            logger.info('⚠️ 脚本存在语法问题，但已生成')

        logger.info(str('='*60))
        logger.info('🎉 修复版Cypher脚本生成完成!')
        logger.info(f"📄 输出文件: {self.output_cypher_path}")
        logger.info("\n下一步操作:")
        logger.info('1. 检查生成的Cypher脚本')
        logger.info('2. 使用修复版脚本重新导入到TuGraph')
        logger.info('3. 验证导入结果')

        return True

def main():
    """主函数"""
    logger.info('🛠️ 修复版Cypher脚本生成器')
    logger.info('根据法律知识图谱JSON生成语法正确的TuGraph导入脚本')
    logger.info(str('='*60))

    # 创建生成器
    generator = FixedCypherGenerator()

    # 运行生成
    success = generator.run_generation()

    if success:
        logger.info("\n✅ 修复版脚本生成成功！")
        logger.info('💡 建议使用新脚本重新导入数据')
    else:
        logger.info("\n❌ 脚本生成失败")

if __name__ == '__main__':
    main()