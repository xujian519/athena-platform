#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地Ollama大规模法律知识图谱构建器
Local Ollama Large-Scale Legal Knowledge Graph Builder

使用本地Ollama Qwen模型构建大规模法律知识图谱
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
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
        logging.FileHandler(
            '/Users/xujian/Athena工作平台/documentation/logs/ollama_large_scale_legal_kg.log'
        ),
        logging.StreamHandler(),
    ],
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


class OllamaLargeScaleEnhancer:
    """本地Ollama大规模增强器"""

    def __init__(self, min_request_interval: float = 0.5):
        self.api_base = 'http://localhost:11434/api'
        self.model_name = 'qwen:7b'
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = float(
            os.getenv('OLLAMA_MIN_INTERVAL', str(min_request_interval))
        )

    def _rate_limit(self):
        """请求频率控制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def enhance_legal_entity_batch(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量增强法律实体"""
        enhanced_entities = []

        # 将实体按类型分组，分别处理
        entities_by_type = {}
        for entity in entities:
            entity_type = entity['type']
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        for entity_type, type_entities in entities_by_type.items():
            # 对每种类型的实体进行批量增强
            self._rate_limit()

            try:
                # 构建批量提示
                entities_text = "\n".join(
                    [f"- {e['name']}" for e in type_entities[:10]]
                )  # 限制数量

                prompt = f"""
作为中国法律专家，请对以下{entity_type}类型的法律实体进行批量分析：

实体列表：
{entities_text}

请为每个实体提供以下信息，以JSON格式返回：
{{
    'enhanced_entities': [
        {{
            'name': '实体名称',
            'legal_category': '法律分类（如：宪法、民事、刑事、行政等）',
            'legal_level': '法律效力层级（如：根本法、基本法律、行政法规、部门规章等）',
            'applicable_scope': '适用范围和条件',
            'key_points': ['关键要点1', '关键要点2', '关键要点3'],
            'related_laws': ['相关法律条文1', '相关法律条文2'],
            'practical_significance': '实际应用意义'
        }}
    ]
}}

请严格按照JSON格式回答，确保语法正确。
"""

                response = self.session.post(
                    f"{self.api_base}/generate",
                    json={
                        'model': self.model_name,
                        'prompt': prompt,
                        'stream': False,
                        'options': {'temperature': 0.3, 'num_predict': 1500},
                    },
                    timeout=60,
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get('response', '')

                    try:
                        enhanced_data = json.loads(content)
                        enhanced_batch = enhanced_data.get('enhanced_entities', [])

                        # 将增强信息映射回原始实体
                        enhanced_map = {e['name']: e for e in enhanced_batch}

                        for entity in type_entities:
                            if entity['name'] in enhanced_map:
                                enhanced_info = enhanced_map[entity['name']]
                                entity.update(
                                    {
                                        'legal_category': enhanced_info.get(
                                            'legal_category', ''
                                        ),
                                        'legal_level': enhanced_info.get(
                                            'legal_level', ''
                                        ),
                                        'applicable_scope': enhanced_info.get(
                                            'applicable_scope', ''
                                        ),
                                        'key_points': enhanced_info.get(
                                            'key_points', []
                                        ),
                                        'related_laws': enhanced_info.get(
                                            'related_laws', []
                                        ),
                                        'practical_significance': enhanced_info.get(
                                            'practical_significance', ''
                                        ),
                                        'ai_enhanced': True,
                                        'confidence': 0.85,
                                    }
                                )
                            enhanced_entities.append(entity)

                    except json.JSONDecodeError:
                        logger.warning(f"JSON解析失败，使用原始实体: {entity_type}")
                        enhanced_entities.extend(type_entities)

                else:
                    logger.warning(f"Ollama API请求失败: {response.status_code}")
                    enhanced_entities.extend(type_entities)

            except Exception as e:
                logger.error(f"批量增强{entity_type}失败: {str(e)}")
                enhanced_entities.extend(type_entities)

        return enhanced_entities

    def extract_legal_relations_batch(
        self, texts: List[str], entities: List[LegalEntity]
    ) -> List[Dict[str, Any]]:
        """批量提取法律关系"""
        self._rate_limit()

        try:
            entity_names = [e.name for e in entities[:20]]
            entities_text = "\n".join([f"- {e.name} ({e.type})" for e in entities[:20]])

            # 合并文本样本（限制长度）
            combined_text = ' '.join(texts[:5])[:2000]

            prompt = f"""
作为法律关系分析专家，请从以下法律文本和实体列表中提取法律关系：

法律文本样本：
{combined_text}

相关实体：
{entities_text}

请提取法律关系，以JSON格式返回：
{{
    'relations': [
        {{
            'source': '源实体名称',
            'target': '目标实体名称',
            'relation_type': '关系类型',
            'description': '关系描述',
            'legal_basis': '法律依据',
            'confidence': 0.8
        }}
    ]
}}

请只返回JSON格式的关系数组，最多10个关系。
"""

            response = self.session.post(
                f"{self.api_base}/generate",
                json={
                    'model': self.model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {'temperature': 0.2, 'num_predict': 1000},
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '')

                try:
                    relations_data = json.loads(content)
                    return relations_data.get('relations', [])
                except json.JSONDecodeError:
                    return []

            return []

        except Exception as e:
            logger.error(f"批量提取法律关系失败: {str(e)}")
            return []


class VeryLargeScaleLegalKGBuildedr:
    """超大规模法律知识图谱构建器"""

    def __init__(
        self,
        fast_mode: bool = False,
        max_files: int | None = None,
        enable_ai_enhance: bool | None = None,
    ):
        self.project_root = Path('/Users/xujian/Athena工作平台')
        self.legal_project_path = self.project_root / 'projects/Laws-1.0.0'
        self.output_dir = self.project_root / 'data/very_large_scale_legal_kg'
        self.tugraph_output_dir = self.project_root / 'data/tugraph_knowledge_graphs'

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tugraph_output_dir.mkdir(parents=True, exist_ok=True)

        self.fast_mode = fast_mode or (os.getenv('FAST_MODE', '0') == '1')
        self.max_files = (
            max_files if max_files is not None else (100 if self.fast_mode else None)
        )
        self.enable_ai_enhance = (
            enable_ai_enhance
            if enable_ai_enhance is not None
            else (False if self.fast_mode else True)
        )

        self.enhancer = OllamaLargeScaleEnhancer(
            min_request_interval=0.5 if not self.fast_mode else 0.1
        )

        self.entities: List[LegalEntity] = []
        self.relations: List[LegalRelation] = []
        self.processed_files = 0
        self.total_files = 0
        self.error_files = 0

    def scan_all_legal_files(self) -> List[Path]:
        """扫描所有法律文件"""
        logger.info('🔍 开始扫描所有法律文件...')

        legal_files = []

        # 扫描所有法律相关文件
        for ext in ['*.md', '*.txt', '*.json']:
            files = list(self.legal_project_path.rglob(ext))
            legal_files.extend(files)

        # 过滤和法律相关的文件
        legal_files = [f for f in legal_files if self._is_legal_file(f)]

        if self.max_files:
            legal_files = legal_files[: self.max_files]
        self.total_files = len(legal_files)
        logger.info(f"📊 发现 {self.total_files} 个法律相关文件")

        return legal_files

    def _is_legal_file(self, file_path: Path) -> bool:
        """判断是否为法律相关文件"""
        file_name = file_path.name.lower()
        parent_dir = file_path.parent.name.lower()

        # 法律相关目录关键词
        legal_dirs = [
            '宪法',
            '民法',
            '刑法',
            '行政法',
            '经济法',
            '社会法',
            '商法',
            '案例',
            '法律',
            '法规',
            '规章',
            '司法解释',
            '部门规章',
            '合同',
            '侵权',
            '诉讼',
            '仲裁',
            '执行',
            '公证',
            '判决',
            '裁定',
            '调解',
            '检察',
            '审判',
            '执法',
        ]

        # 检查目录名
        if any(keyword in parent_dir for keyword in legal_dirs):
            return True

        # 检查文件名
        legal_keywords = [
            '法',
            '条例',
            '规定',
            '办法',
            '规则',
            '决定',
            '命令',
            '解释',
            '案例',
            '判决',
            '裁定',
            '调解',
            '仲裁',
            '合同',
            '协议',
            '契约',
            '章程',
            '制度',
            '法律',
        ]

        if any(keyword in file_name for keyword in legal_keywords):
            return True

        return False

    def extract_entities_from_text(
        self, text: str, source_file: str
    ) -> List[Dict[str, Any]]:
        """从文本中提取法律实体"""
        entities = []

        # 扩展的法律实体识别模式
        legal_patterns = {
            '法律法规': [
                r"《([^》]*(?:法|条例|规定|办法|细则|规则|解释|决定)[^》]*)》",
                r"中华人民共和国([^）]*(?:法|条例|规定|办法|细则|规则))",
            ],
            '司法机关': [
                r"([^）]*(?:人民法院|人民检察院|公安|司法|法院|检察院))",
                r"最高人民法院",
                r"最高人民检察院",
                r"地方人民法院",
                r"地方人民检察院",
            ],
            '行政机关': [
                r"([^）]*(?:人民政府|部|委员会|局|署|厅))",
                r"国务院",
                r"省人民政府",
                r"市人民法院",
            ],
            '法律程序': [
                r"([^）]*(?:诉讼|仲裁|调解|执行|审判|公诉|检察))",
                r"民事诉讼",
                r"刑事诉讼",
                r"行政诉讼",
                r"仲裁程序",
            ],
            '法律权利': [
                r"([^）]*(?:权利|义务|利益|损害赔偿|补偿))",
                r"民事权利",
                r"人身权利",
                r"财产权利",
            ],
            '法律主体': [
                r"([^）]*(?:当事人|原告|被告|第三人|代理人|律师))",
                r"法人",
                r"自然人",
                r"个体工商户",
            ],
            '法律文书': [
                r"([^）]*(?:判决书|裁定书|调解书|合同|协议|委托书))",
                r"起诉书",
                r"答辩状",
                r"申请书",
            ],
        }

        for entity_type, patterns in legal_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group(1).strip()

                    # 基本验证
                    if len(entity_name) < 2 or len(entity_name) > 100:
                        continue

                    if self._is_valid_entity(entity_name):
                        entity_data = {
                            'name': entity_name,
                            'type': entity_type,
                            'source_file': source_file,
                            'position': match.start(),
                            'context': text[
                                max(0, match.start() - 50) : match.end() + 50
                            ],
                        }
                        entities.append(entity_data)

        return entities

    def _is_valid_entity(self, entity_name: str) -> bool:
        """验证实体是否有效"""
        # 过滤掉明显无效的匹配
        invalid_patterns = [
            '的',
            '和',
            '与',
            '或',
            '等',
            '及',
            '其',
            '该',
            '本',
            '上述',
            '下列',
        ]

        if any(pattern in entity_name for pattern in invalid_patterns):
            return False

        # 检查是否包含中文字符
        if not re.search(r"[\u4e00-\u9fff]", entity_name):
            return False

        return True

    def process_very_large_scale_files(self):
        """处理超大规模法律文件"""
        logger.info('🚀 开始处理超大规模法律文件...')

        # 扫描所有文件
        legal_files = self.scan_all_legal_files()

        if not legal_files:
            logger.error('未找到法律文件')
            return False

        logger.info(f"📈 将处理所有 {len(legal_files)} 个法律文件")

        # 处理所有文件
        batch_size = 100
        all_entities = []
        all_texts = []

        for i in range(0, len(legal_files), batch_size):
            batch_files = legal_files[i : i + batch_size]
            logger.info(f"🔄 处理第 {i//batch_size + 1} 批文件 ({len(batch_files)} 个)")

            batch_entities = []
            batch_texts = []

            for file_path in batch_files:
                try:
                    # 跳过过大的文件
                    if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                        logger.warning(f"跳过过大文件: {file_path.name}")
                        continue

                    # 读取文件内容
                    content = self._read_file_content(file_path)
                    if not content:
                        continue

                    logger.debug(f"📄 处理: {file_path.name}")

                    # 提取实体
                    entities = self.extract_entities_from_text(content, str(file_path))
                    batch_entities.extend(entities)
                    batch_texts.append(content[:1000])  # 保存文本样本用于关系提取

                    self.processed_files += 1

                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {str(e)}")
                    self.error_files += 1
                    continue

            if batch_entities:
                if self.enable_ai_enhance:
                    logger.info(f"🤖 AI增强 {len(batch_entities)} 个实体...")
                    enhanced_entities = self.enhancer.enhance_legal_entity_batch(
                        batch_entities
                    )
                else:
                    enhanced_entities = batch_entities

                # 创建LegalEntity对象
                for entity_data in enhanced_entities:
                    entity_id = hashlib.md5(
                        f"{entity_data['name']}_{entity_data['type']}_{entity_data['source_file']}".encode('utf-8', usedforsecurity=False)
                    ).hexdigest()[:16]

                    entity = LegalEntity(
                        id=entity_id,
                        name=entity_data['name'],
                        type=entity_data['type'],
                        properties=entity_data,
                        source=entity_data['source_file'],
                        confidence=entity_data.get('confidence', 0.7),
                    )
                    all_entities.append(entity)

            if self.enable_ai_enhance and all_entities and len(all_entities) > 50:
                logger.info(f"🔗 提取法律关系...")
                relations_data = self.enhancer.extract_legal_relations_batch(
                    batch_texts, all_entities[-50:]
                )

                for rel_data in relations_data:
                    relation_id = hashlib.md5(
                        f"{rel_data['source']}_{rel_data['target']}_{rel_data['relation_type']}".encode('utf-8', usedforsecurity=False)
                    ).hexdigest()[:16]

                    relation = LegalRelation(
                        id=relation_id,
                        source=rel_data['source'],
                        target=rel_data['target'],
                        type=rel_data['relation_type'],
                        properties={
                            'description': rel_data.get('description', ''),
                            'legal_basis': rel_data.get('legal_basis', ''),
                            'confidence': rel_data.get('confidence', 0.7),
                            'batch_extracted': True,
                        },
                        confidence=rel_data.get('confidence', 0.7),
                    )
                    self.relations.append(relation)

            # 报告进度
            progress = (i + len(batch_files)) / len(legal_files) * 100
            logger.info(
                f"📊 进度: {progress:.1f}% ({i + len(batch_files)}/{len(legal_files)})"
            )
            logger.info(
                f"📋 当前统计: {len(all_entities)} 实体, {len(self.relations)} 关系"
            )

        self.entities = all_entities
        logger.info(f"✅ 超大规模文件处理完成")
        logger.info(
            f"📊 处理统计: {self.processed_files} 成功, {self.error_files} 失败"
        )
        logger.info(f"📋 提取 {len(self.entities)} 个法律实体")
        logger.info(f"🔗 提取 {len(self.relations)} 个法律关系")

        return True

    def _read_file_content(self, file_path: Path) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 限制内容长度
                if len(content) > 5000:
                    content = content[:5000] + "\n...[内容已截断]..."
                return content
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                    if len(content) > 5000:
                        content = content[:5000] + "\n...[内容已截断]..."
                    return content
            except:
                logger.warning(f"无法读取文件: {file_path}")
                return ''
        except Exception as e:
            logger.warning(f"读取文件异常 {file_path}: {str(e)}")
            return ''

    def run(self):
        """运行完整的超大规模构建流程"""
        logger.info('🚀 开始构建超大规模法律知识图谱')
        logger.info('💡 使用本地Ollama Qwen模型进行AI增强')
        logger.info('📊 基于Laws-1.0.0项目的所有法律文件')
        logger.info('=' * 80)

        try:
            # 第一阶段：处理所有法律文件
            logger.info('📚 第一阶段：处理所有法律文件...')
            if not self.process_very_large_scale_files():
                logger.error('文件处理失败')
                return False

            # 保存知识图谱
            logger.info('💾 第二阶段：保存超大规模知识图谱数据...')
            kg_file = self.save_knowledge_graph()

            # 生成TuGraph导入脚本
            logger.info('📝 第三阶段：生成TuGraph导入脚本...')
            tugraph_script = self.generate_tugraph_import_script()

            # 生成最终报告
            final_report = {
                '构建时间': datetime.now().isoformat(),
                '项目信息': {
                    '构建方式': '超大规模法律知识图谱构建',
                    '输出目录': str(self.output_dir),
                    'AI模型': 'Qwen:7b (本地Ollama)',
                    '数据源': 'Laws-1.0.0项目全部文件',
                },
                '构建结果': {
                    '扫描文件总数': self.total_files,
                    '处理文件数量': self.processed_files,
                    '实体总数': len(self.entities),
                    '关系总数': len(self.relations),
                    '知识图谱文件': str(kg_file),
                    'TuGraph脚本': str(tugraph_script),
                },
                '质量指标': {
                    '处理成功率': (
                        f"{(self.processed_files / self.total_files * 100):.1f}%"
                        if self.total_files > 0
                        else '0%'
                    ),
                    '平均每文件实体数': f"{len(self.entities) / max(1, self.processed_files):.1f}",
                    '平均每文件关系数': f"{len(self.relations) / max(1, self.processed_files):.1f}",
                },
                '技术特点': [
                    '✅ 处理所有法律文件（无需筛选）',
                    '✅ 使用本地Ollama AI增强',
                    f"✅ 成功处理 {self.processed_files} 个法律文件",
                    f"✅ 构建 {len(self.entities)} 个法律实体",
                    f"✅ 建立 {len(self.relations)} 个法律关系",
                    '✅ 生成TuGraph导入脚本',
                ],
            }

            report_file = self.output_dir / 'very_large_scale_construction_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, ensure_ascii=False, indent=2)

            logger.info('=' * 80)
            logger.info('🎉 超大规模法律知识图谱构建完成!')
            logger.info(
                f"📊 构建结果: {len(self.entities)} 个实体, {len(self.relations)} 个关系"
            )
            logger.info(f"📁 输出目录: {self.output_dir}")
            logger.info(f"📄 最终报告: {report_file}")

            return True

        except Exception as e:
            logger.error(f"❌ 超大规模构建过程失败: {str(e)}")
            return False

    def save_knowledge_graph(self):
        """保存知识图谱数据"""
        logger.info('💾 保存超大规模知识图谱数据...')

        # 保存实体数据
        entities_data = []
        for entity in self.entities:
            entities_data.append(
                {
                    'id': entity.id,
                    'name': entity.name,
                    'type': entity.type,
                    'properties': entity.properties,
                    'source': entity.source,
                    'confidence': entity.confidence,
                }
            )

        # 保存关系数据
        relations_data = []
        for relation in self.relations:
            relations_data.append(
                {
                    'id': relation.id,
                    'source': relation.source,
                    'target': relation.target,
                    'type': relation.type,
                    'properties': relation.properties,
                    'confidence': relation.confidence,
                }
            )

        # 保存为JSON格式
        kg_data = {
            'entities': entities_data,
            'relations': relations_data,
            'metadata': {
                'created_time': datetime.now().isoformat(),
                'total_entities': len(entities_data),
                'total_relations': len(relations_data),
                'processed_files': self.processed_files,
                'total_files': self.total_files,
                'error_files': self.error_files,
                'model_used': 'qwen:7b-ollama-local',
                'enhancement_method': 'batch_ai_enhancement',
                'build_version': 'very_large_scale_v1.0',
                'description': f"基于{self.processed_files}个法律文件构建的超大规模知识图谱",
            },
        }

        output_file = self.output_dir / 'very_large_scale_legal_knowledge_graph.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(kg_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 超大规模知识图谱已保存到: {output_file}")
        logger.info(f"📊 文件大小: {output_file.stat().st_size / 1024 / 1024:.1f} MB")

        return output_file

    def generate_tugraph_import_script(self):
        """生成TuGraph导入脚本"""
        logger.info('📝 生成超大规模TuGraph导入脚本...')

        # 创建TuGraph Cypher脚本
        cypher_script = f"-- 超大规模法律知识图谱TuGraph导入脚本\n"
        cypher_script += f"-- 生成时间: {datetime.now().isoformat()}\n"
        cypher_script += (
            f"-- 数据来源: Laws-1.0.0项目 ({self.processed_files} 个文件)\n"
        )
        cypher_script += f"-- AI增强: Qwen:7b本地模型\n"
        cypher_script += f"-- 构建版本: very_large_scale_v1.0\n\n"

        # 创建标签
        cypher_script += "-- 创建实体标签\n"
        entity_types = set(entity.type for entity in self.entities)
        for entity_type in sorted(entity_types):
            safe_type = entity_type.replace(' ', '_').replace('(', '').replace(')', '')
            cypher_script += f"CREATE TAG IF NOT EXISTS {safe_type} (id STRING, name STRING, type STRING, properties STRING, source STRING, confidence FLOAT);\n"

        cypher_script += "\n-- 创建关系类型\n"
        relation_types = set(relation.type for relation in self.relations)
        for rel_type in sorted(relation_types):
            safe_type = rel_type.replace(' ', '_').replace('(', '').replace(')', '')
            cypher_script += f"CREATE EDGE IF NOT EXISTS {safe_type} (type STRING, properties STRING, confidence FLOAT);\n"

        cypher_script += "\n-- 插入实体数据\n"
        for entity in self.entities:
            escaped_name = entity.name.replace('"', '\\"')
            escaped_properties = json.dumps(
                entity.properties, ensure_ascii=False
            ).replace('"', '\\"')
            safe_type = entity.type.replace(' ', '_').replace('(', '').replace(')', '')

            cypher_script += f'INSERT VERTEX INTO {safe_type} VALUES ('{entity.id}', '{escaped_name}', '{entity.type}', '{escaped_properties}', '{entity.source}', {entity.confidence});\n'

        cypher_script += "\n-- 插入关系数据\n"
        for relation in self.relations:
            escaped_properties = json.dumps(
                relation.properties, ensure_ascii=False
            ).replace('"', '\\"')
            safe_type = (
                relation.type.replace(' ', '_').replace('(', '').replace(')', '')
            )

            cypher_script += f'INSERT EDGE INTO {safe_type} VALUES ('{relation.source}' -> '{relation.target}', ('{relation.type}', '{escaped_properties}', {relation.confidence}));\n'

        # 保存TuGraph脚本
        tugraph_script_file = (
            self.tugraph_output_dir / 'very_large_scale_legal_kg_import.cypher'
        )
        with open(tugraph_script_file, 'w', encoding='utf-8') as f:
            f.write(cypher_script)

        logger.info(f"📄 超大规模TuGraph导入脚本已保存到: {tugraph_script_file}")
        logger.info(
            f"📊 脚本大小: {tugraph_script_file.stat().st_size / 1024 / 1024:.1f} MB"
        )

        return tugraph_script_file


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--fast', action='store_true')
    parser.add_argument('--max-files', type=int, default=None)
    parser.add_argument('--no-ai', action='store_true')
    args = parser.parse_args()

    logger.info('🚀 超大规模法律知识图谱构建器')
    logger.info('💡 使用本地Ollama Qwen模型进行AI增强')
    logger.info('📊 基于Laws-1.0.0项目的所有法律文件')
    logger.info(str('=' * 80))

    builder = VeryLargeScaleLegalKGBuildedr(
        fast_mode=args.fast,
        max_files=args.max_files,
        enable_ai_enhance=(False if args.no_ai else None),
    )

    success = builder.run()

    if success:
        logger.info("\n🎯 超大规模构建成功完成！下一步操作:")
        logger.info('1. 查看构建统计:')
        logger.info(f"   cat {builder.output_dir}/very_large_scale_construction_report.json")
        logger.info('2. 导入到TuGraph数据库:')
        logger.info('   python3 scripts/import_very_large_scale_kg_tugraph.py')
        logger.info('3. 验证知识图谱质量:')
        logger.info(f"   ls -la {builder.output_dir}/")
        logger.info('4. 开发法律智能应用:')
        logger.info('   - 法律智能问答系统')
        logger.info('   - 法律知识检索引擎')
        logger.info('   - 法律关系分析工具')
        logger.info("\n✅ 超大规模构建成功完成！")
        logger.info('💡 快捷模式与参数已生效')
    else:
        logger.info("\n❌ 超大规模构建失败，请检查日志获取详细信息")


if __name__ == '__main__':
    main()
