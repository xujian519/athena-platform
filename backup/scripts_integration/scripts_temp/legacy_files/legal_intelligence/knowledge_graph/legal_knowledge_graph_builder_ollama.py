#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高质量法律知识图谱构建器 - Ollama版本
Legal Knowledge Graph Builder with Ollama Enhancement

基于Ollama本地大模型构建高质量TuGraph法律知识图谱
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/documentation/logs/legal_kg_builder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LegalEntity:
    """法律实体数据类"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any]
    source: str
    confidence: float = 0.0

@dataclass
class LegalRelation:
    """法律关系数据类"""
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any]
    confidence: float = 0.0

class OllamaEnhancer:
    """Ollama语义增强器"""

    def __init__(self):
        # Ollama API配置
        self.api_base = 'http://localhost:11434/api'
        self.model_name = 'qwen:7b'  # 使用现有的qwen:7b模型
        self.session = requests.Session()

    def enhance_legal_entity(self, entity: LegalEntity, context: str) -> Dict[str, Any]:
        """使用Ollama增强法律实体"""
        try:
            prompt = f"""
作为中国法律专家，请分析以下法律实体并提供详细的法律理解：

实体名称：{entity.name}
实体类型：{entity.type}
当前语境：{context[:500]}

请提供JSON格式的详细分析：
{{
    'legal_definition': '精确的法律定义',
    'scope_of_application': '适用范围和条件',
    'related_laws': ['相关的具体法律条文'],
    'synonyms': ['同义词或近义词'],
    'legal_classification': '法律分类',
    'key_elements': ['关键要素'],
    'exceptions': '例外情况或限制',
    'practical_applications': '实际应用场景'
}}

请严格按照JSON格式回答，不要包含其他文字。
"""

            response = self.session.post(
                f"{self.api_base}/generate",
                json={
                    'model': self.model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.3,
                        'num_predict': 1000
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '{}')

                # 尝试解析JSON
                try:
                    enhanced_info = json.loads(content)
                    return enhanced_info
                except json.JSONDecodeError:
                    # 如果解析失败，返回基本信息
                    return {
                        'legal_definition': f"{entity.name}的法律实体",
                        'scope_of_application': '适用于相关法律场景',
                        'related_laws': [],
                        'synonyms': [],
                        'legal_classification': entity.type,
                        'key_elements': [],
                        'exceptions': '',
                        'practical_applications': ''
                    }
            else:
                logger.warning(f"Ollama API请求失败: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"增强法律实体失败 {entity.name}: {str(e)}")
            return {}

    def extract_legal_relations(self, text: str, entities: List[LegalEntity]) -> List[Dict[str, Any]]:
        """从文本中提取法律关系"""
        try:
            entity_names = [e.name for e in entities]
            entity_dict = {e.name: e for e in entities}

            prompt = f"""
作为法律关系分析专家，请从以下法律文本中提取实体间的法律关系：

法律文本：
{text[:800]}

涉及的实体：
{', '.join(entity_names)}

请提取法律关系，以JSON格式返回：
{{
    'relations': [
        {{
            'source_entity': '源实体名称',
            'target_entity': '目标实体名称',
            'relation_type': '关系类型（如：规范、约束、适用、包含等）',
            'description': '关系描述',
            'legal_basis': '法律依据',
            'confidence': 0.9
        }}
    ]
}}

请严格按照JSON格式回答，只返回relations数组。
"""

            response = self.session.post(
                f"{self.api_base}/generate",
                json={
                    'model': self.model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.2,
                        'num_predict': 800
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '{}')

                try:
                    relations_data = json.loads(content)
                    return relations_data.get('relations', [])
                except json.JSONDecodeError:
                    logger.warning('法律关系JSON解析失败')
                    return []
            else:
                logger.warning(f"关系提取API请求失败: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"提取法律关系失败: {str(e)}")
            return []

class LegalKnowledgeGraphBuilder:
    """法律知识图谱构建器"""

    def __init__(self):
        self.project_root = Path('/Users/xujian/Athena工作平台')
        self.legal_project_path = self.project_root / 'projects/Laws-1.0.0'
        self.output_dir = self.project_root / 'data/legal_knowledge_graph_enhanced'
        self.tugraph_output_dir = self.project_root / 'data/tugraph_knowledge_graphs'

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tugraph_output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化Ollama增强器
        self.enhancer = OllamaEnhancer()

        # 数据存储
        self.entities: List[LegalEntity] = []
        self.relations: List[LegalRelation] = []

        # 法律实体类型映射
        self.entity_types = {
            '法律法规': ['law', 'regulation', 'statute'],
            '法律概念': ['legal_concept', 'term', 'definition'],
            '法律主体': ['legal_entity', 'person', 'organization'],
            '权利义务': ['right', 'obligation', 'duty'],
            '法律程序': ['procedure', 'process', 'litigation'],
            '法律责任': ['liability', 'responsibility', 'penalty'],
            '法律文书': ['document', 'contract', 'agreement'],
            '司法机构': 'court',
            '法律职业': 'profession'
        }

    def scan_legal_documents(self) -> List[Path]:
        """扫描法律文档"""
        logger.info('开始扫描法律文档...')

        legal_files = []

        # 扫描不同类型的法律文件
        patterns = [
            '**/*.txt',    # 法律条文文本
            '**/*.md',     # Markdown文档
            '**/*.json',   # JSON格式法律数据
            '**/*.py',     # 法律相关的Python代码（注释可能包含法律信息）
            '**/法律*',
            '**/law*',
            '**/regulation*'
        ]

        for pattern in patterns:
            files = list(self.legal_project_path.rglob(pattern))
            legal_files.extend(files)

        # 去重
        legal_files = list(set(legal_files))
        logger.info(f"发现 {len(legal_files)} 个法律相关文件")

        return legal_files

    def extract_entities_from_text(self, text: str, source_file: str) -> List[LegalEntity]:
        """从文本中提取法律实体"""
        entities = []

        # 法律实体识别规则
        legal_patterns = {
            '法律法规': [
                r'《([^》]+)》',
                r'([^(《]*法[^(》]*)',
                r'([^(《]*条例[^(》]*)',
                r'([^(《]*规定[^(》]*)',
                r'([^(《]*办法[^(》]*)'
            ],
            '法律概念': [
                r'([\u4e00-\u9fff]*(?:权利|义务|责任| liability|right|obligation)[\u4e00-\u9fff]*)',
                r'([\u4e00-\u9fff]*(?:管辖|管辖权| jurisdiction)[\u4e00-\u9fff]*)',
                r'([\u4e00-\u9fff]*(?:诉讼|起诉| litigation|lawsuit)[\u4e00-\u9fff]*)'
            ],
            '法律主体': [
                r'([\u4e00-\u9fff]*(?:人民法院|检察院|公安机关|司法局)[\u4e00-\u9fff]*)',
                r'([\u4e00-\u9fff]*(?:当事人|原告|被告|第三人)[\u4e00-\u9fff]*)',
                r'([\u4e00-\u9fff]*(?:律师|法官|检察官|公证员)[\u4e00-\u9fff]*)'
            ]
        }

        for entity_type, patterns in legal_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity_name = match.group(1).strip()
                    if len(entity_name) >= 2 and len(entity_name) <= 50:
                        entity_id = hashlib.md5(
                            f"{entity_name}_{entity_type}_{source_file}".encode('utf-8', usedforsecurity=False)
                        ).hexdigest()[:16]

                        entity = LegalEntity(
                            id=entity_id,
                            name=entity_name,
                            type=entity_type,
                            properties={
                                'source_file': source_file,
                                'extracted_pattern': pattern,
                                'context': text[max(0, match.start()-50):match.end()+50]
                            },
                            source=source_file,
                            confidence=0.7
                        )
                        entities.append(entity)

        return entities

    def process_documents(self):
        """处理法律文档"""
        logger.info('开始处理法律文档...')

        # 扫描文档
        legal_files = self.scan_legal_documents()

        if not legal_files:
            logger.error('未找到法律文档文件')
            return False

        processed_count = 0

        for file_path in legal_files:
            try:
                # 跳过过大的文件
                if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                    logger.warning(f"跳过过大文件: {file_path}")
                    continue

                # 读取文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='gbk') as f:
                            content = f.read()
                    except:
                        logger.warning(f"无法读取文件: {file_path}")
                        continue

                # 跳过空文件
                if not content.strip():
                    continue

                logger.info(f"处理文件: {file_path.name}")

                # 提取实体
                entities = self.extract_entities_from_text(content, str(file_path))

                # 使用Ollama增强实体
                enhanced_entities = []
                for entity in entities:
                    context = content[max(0, content.find(entity.name)-100):content.find(entity.name)+100]
                    enhanced_info = self.enhancer.enhance_legal_entity(entity, context)

                    if enhanced_info:
                        # 更新实体属性
                        entity.properties.update(enhanced_info)
                        entity.confidence = 0.9

                    enhanced_entities.append(entity)

                self.entities.extend(enhanced_entities)

                # 提取关系
                relations_data = self.enhancer.extract_legal_relations(content, enhanced_entities)
                for rel_data in relations_data:
                    relation_id = hashlib.md5(
                        f"{rel_data['source_entity']}_{rel_data['target_entity']}_{rel_data['relation_type']}".encode('utf-8', usedforsecurity=False)
                    ).hexdigest()[:16]

                    relation = LegalRelation(
                        id=relation_id,
                        source=rel_data['source_entity'],
                        target=rel_data['target_entity'],
                        type=rel_data['relation_type'],
                        properties={
                            'description': rel_data.get('description', ''),
                            'legal_basis': rel_data.get('legal_basis', ''),
                            'source_file': str(file_path)
                        },
                        confidence=rel_data.get('confidence', 0.7)
                    )
                    self.relations.append(relation)

                processed_count += 1

                # 限制处理的文件数量以避免过长处理时间
                if processed_count >= 20:
                    logger.info('达到最大文件处理数量限制')
                    break

            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {str(e)}")
                continue

        logger.info(f"文档处理完成，共处理 {processed_count} 个文件")
        logger.info(f"提取 {len(self.entities)} 个法律实体")
        logger.info(f"提取 {len(self.relations)} 个法律关系")

        return True

    def save_knowledge_graph(self):
        """保存知识图谱数据"""
        logger.info('保存知识图谱数据...')

        # 保存实体数据
        entities_data = []
        for entity in self.entities:
            entities_data.append({
                'id': entity.id,
                'name': entity.name,
                'type': entity.type,
                'properties': entity.properties,
                'source': entity.source,
                'confidence': entity.confidence
            })

        # 保存关系数据
        relations_data = []
        for relation in self.relations:
            relations_data.append({
                'id': relation.id,
                'source': relation.source,
                'target': relation.target,
                'type': relation.type,
                'properties': relation.properties,
                'confidence': relation.confidence
            })

        # 保存为JSON格式
        kg_data = {
            'entities': entities_data,
            'relations': relations_data,
            'metadata': {
                'created_time': datetime.now().isoformat(),
                'total_entities': len(entities_data),
                'total_relations': len(relations_data),
                'model_used': 'qwen:7b',
                'enhancement_method': 'ollama_api'
            }
        }

        output_file = self.output_dir / 'legal_knowledge_graph_enhanced.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(kg_data, f, ensure_ascii=False, indent=2)

        logger.info(f"知识图谱已保存到: {output_file}")

        # 生成统计报告
        self.generate_statistics_report()

        return output_file

    def generate_statistics_report(self):
        """生成统计报告"""
        logger.info('生成统计报告...')

        # 统计实体类型分布
        entity_type_count = {}
        for entity in self.entities:
            entity_type_count[entity.type] = entity_type_count.get(entity.type, 0) + 1

        # 统计关系类型分布
        relation_type_count = {}
        for relation in self.relations:
            relation_type_count[relation.type] = relation_type_count.get(relation.type, 0) + 1

        # 统计置信度分布
        confidence_ranges = {'0.5-0.6': 0, '0.6-0.7': 0, '0.7-0.8': 0, '0.8-0.9': 0, '0.9-1.0': 0}
        for entity in self.entities + self.relations:
            confidence = entity.confidence
            if 0.5 <= confidence < 0.6:
                confidence_ranges['0.5-0.6'] += 1
            elif 0.6 <= confidence < 0.7:
                confidence_ranges['0.6-0.7'] += 1
            elif 0.7 <= confidence < 0.8:
                confidence_ranges['0.7-0.8'] += 1
            elif 0.8 <= confidence < 0.9:
                confidence_ranges['0.8-0.9'] += 1
            elif 0.9 <= confidence <= 1.0:
                confidence_ranges['0.9-1.0'] += 1

        report = {
            '生成时间': datetime.now().isoformat(),
            '模型信息': {
                '使用的模型': 'qwen:7b',
                'API服务': 'Ollama',
                '增强方法': '语义理解和关系提取'
            },
            '实体统计': {
                '总数量': len(self.entities),
                '类型分布': entity_type_count
            },
            '关系统计': {
                '总数量': len(self.relations),
                '类型分布': relation_type_count
            },
            '质量评估': {
                '置信度分布': confidence_ranges,
                '平均置信度': np.mean([e.confidence for e in self.entities + self.relations])
            }
        }

        report_file = self.output_dir / 'legal_kg_statistics_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"统计报告已保存到: {report_file}")

    def generate_tugraph_import_script(self):
        """生成TuGraph导入脚本"""
        logger.info('生成TuGraph导入脚本...')

        # 创建TuGraph Cypher脚本
        cypher_script = f"-- 法律知识图谱TuGraph导入脚本\n"
        cypher_script += f"-- 生成时间: {datetime.now().isoformat()}\n"
        cypher_script += f"-- 数据来源: Laws-1.0.0项目\n"
        cypher_script += f"-- 模型增强: qwen:7b via Ollama\n\n"

        # 创建标签
        cypher_script += "-- 创建实体标签\n"
        entity_types = set(entity.type for entity in self.entities)
        for entity_type in entity_types:
            cypher_script += f"CREATE TAG IF NOT EXISTS {entity_type.replace(' ', '_')} (id STRING, name STRING, type STRING, properties STRING, source STRING, confidence FLOAT);\n"

        cypher_script += "\n-- 创建关系类型\n"
        relation_types = set(relation.type for relation in self.relations)
        for rel_type in relation_types:
            cypher_script += f"CREATE EDGE IF NOT EXISTS {rel_type.replace(' ', '_')} (type STRING, properties STRING, confidence FLOAT);\n"

        cypher_script += "\n-- 插入实体数据\n"
        for entity in self.entities:
            escaped_name = entity.name.replace('"', '\\"')
            escaped_properties = json.dumps(entity.properties, ensure_ascii=False).replace('"', '\\"')
            cypher_script += f'INSERT VERTEX INTO {entity.type.replace(' ', '_')} VALUES ('{entity.id}', '{escaped_name}', '{entity.type}', '{escaped_properties}', '{entity.source}', {entity.confidence});\n'

        cypher_script += "\n-- 插入关系数据\n"
        for relation in self.relations:
            escaped_properties = json.dumps(relation.properties, ensure_ascii=False).replace('"', '\\"')
            cypher_script += f'INSERT EDGE INTO {relation.type.replace(' ', '_')} VALUES ('{relation.source}' -> '{relation.target}', ('{relation.type}', '{escaped_properties}', {relation.confidence}));\n'

        # 保存TuGraph脚本
        tugraph_script_file = self.tugraph_output_dir / 'legal_kg_import_enhanced.cypher'
        with open(tugraph_script_file, 'w', encoding='utf-8') as f:
            f.write(cypher_script)

        logger.info(f"TuGraph导入脚本已保存到: {tugraph_script_file}")

        return tugraph_script_file

    def run(self):
        """运行完整的构建流程"""
        logger.info('🚀 开始构建高质量法律知识图谱')
        logger.info('='*60)

        try:
            # 第一阶段：文档扫描和处理
            logger.info('📄 第一阶段：处理法律文档...')
            if not self.process_documents():
                logger.error('文档处理失败')
                return False

            # 第二阶段：保存知识图谱
            logger.info('💾 第二阶段：保存知识图谱数据...')
            kg_file = self.save_knowledge_graph()

            # 第三阶段：生成TuGraph导入脚本
            logger.info('📝 第三阶段：生成TuGraph导入脚本...')
            tugraph_script = self.generate_tugraph_import_script()

            # 生成最终报告
            final_report = {
                '构建时间': datetime.now().isoformat(),
                '项目信息': {
                    '源数据路径': str(self.legal_project_path),
                    '输出目录': str(self.output_dir),
                    '使用模型': 'qwen:7b (Ollama)',
                    '增强方法': '语义理解+关系提取'
                },
                '构建结果': {
                    '实体总数': len(self.entities),
                    '关系总数': len(self.relations),
                    '知识图谱文件': str(kg_file),
                    'TuGraph脚本': str(tugraph_script)
                },
                '下一步操作': [
                    '1. 验证生成的知识图谱质量',
                    '2. 使用TuGraph导入脚本导入数据',
                    '3. 配置TuGraph服务和API',
                    '4. 测试知识图谱查询功能'
                ]
            }

            report_file = self.output_dir / 'construction_final_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, ensure_ascii=False, indent=2)

            logger.info('='*60)
            logger.info('🎉 法律知识图谱构建完成!')
            logger.info(f"📊 构建结果: {len(self.entities)} 个实体, {len(self.relations)} 个关系")
            logger.info(f"📁 输出目录: {self.output_dir}")
            logger.info(f"📝 最终报告: {report_file}")

            return True

        except Exception as e:
            logger.error(f"构建过程失败: {str(e)}")
            return False

def main():
    """主函数"""
    logger.info('🏛️ 高质量法律知识图谱构建器 (Ollama版本)')
    logger.info('基于Laws-1.0.0项目和qwen:7b模型')
    logger.info(str('='*60))

    # 确保Ollama服务运行
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code != 200:
            logger.info('❌ Ollama服务未运行，请先启动Ollama')
            logger.info('   启动命令: ollama serve')
            return
    except:
        logger.info('❌ 无法连接到Ollama服务')
        logger.info('   请确保Ollama已安装并运行: ollama serve')
        return

    # 检查qwen:7b模型
    models = response.json().get('models', [])
    qwen_available = any(model['name'] == 'qwen:7b' for model in models)
    if not qwen_available:
        logger.info('❌ qwen:7b模型未找到，请先下载:')
        logger.info('   下载命令: ollama pull qwen:7b')
        return

    logger.info('✅ Ollama服务检查通过')
    logger.info('✅ qwen:7b模型可用')
    print()

    # 创建构建器
    builder = LegalKnowledgeGraphBuilder()

    # 运行构建流程
    success = builder.run()

    if success:
        logger.info("\n🎯 下一步操作建议:")
        logger.info('1. 检查生成的知识图谱文件')
        logger.info('2. 使用TuGraph导入脚本导入数据库')
        logger.info('3. 启动TuGraph服务')
        logger.info('4. 测试知识图谱查询功能')
    else:
        logger.info("\n❌ 构建失败，请检查日志文件获取详细信息")

if __name__ == '__main__':
    main()