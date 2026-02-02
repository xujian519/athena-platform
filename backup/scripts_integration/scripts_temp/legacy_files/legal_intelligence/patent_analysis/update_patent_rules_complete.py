#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利规则向量库和知识图谱完整更新系统
Complete Patent Rules Vector and Knowledge Graph Update System

集成向量库和知识图谱更新功能，按照专利规则构建方法，
将指定目录中的法律文件更新到系统中，包含去重处理

作者: Athena AI系统
创建时间: 2025-12-05
版本: 2.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

from core.knowledge.patent_rules_graph_builder import PatentRulesGraphBuilder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Users/xujian/Athena工作平台/documentation/logs/patent_rules_complete_update.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class PatentRule:
    """专利规则数据类"""
    
    def __init__(self, text: str, source_file: str, metadata: Dict[str, Any] = None):
        self.text = text.strip()
        self.source_file = source_file
        self.metadata = metadata or {}
        self.text_hash = self._compute_text_hash()
        
    def _compute_text_hash(self) -> str:
        """计算文本哈希值用于去重"""
        return hashlib.md5(self.text.encode('utf-8'), usedforsecurity=False).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'text': self.text,
            'source_file': self.source_file,
            'text_hash': self.text_hash,
            'metadata': self.metadata,
            'import_time': datetime.now().isoformat()
        }

class PatentRulesCompleteUpdater:
    """专利规则完整更新器（向量库 + 知识图谱）"""
    
    def __init__(self):
        self.qdrant_client = QdrantClient(host='localhost', port=6333)
        self.collection_name = 'patent_rules_1024'
        self.existing_hashes: Set[str] = set()
        self.processed_files: Set[str] = set()
        
        # 向量维度
        self.vector_size = 1024
        
        # 知识图谱构建器
        self.graph_builder = PatentRulesGraphBuilder()
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_rules': 0,
            'new_rules': 0,
            'duplicate_rules': 0,
            'updated_vectors': 0,
            'graph_nodes': 0,
            'graph_relations': 0,
            'errors': []
        }
        
    async def initialize(self):
        """初始化更新器"""
        logger.info('🏛️ Athena专利规则完整更新系统初始化...')
        
        # 加载现有的文本哈希
        await self._load_existing_hashes()
        
        logger.info(f"✅ 已加载 {len(self.existing_hashes)} 个现有规则哈希")
        
    async def _load_existing_hashes(self):
        """加载现有的文本哈希"""
        try:
            # 使用scroll API获取所有现有的patent_rules
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # 每次获取1万条
                with_payload=True,
                with_vector=False
            )
            
            points = scroll_result[0]
            while points:
                for point in points:
                    if point.payload and 'text_hash' in point.payload:
                        self.existing_hashes.add(point.payload['text_hash'])
                
                # 继续获取下一批
                scroll_result = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[models.HasIdCondition(has_id=points[-1].id)]
                    ),
                    limit=10000,
                    with_payload=True,
                    with_vector=False
                )
                points = scroll_result[0]
                
                if len(points) == 0:
                    break
                    
        except Exception as e:
            logger.error(f"❌ 加载现有哈希失败: {e}")
            
    async def update_from_directory(self, directory_path: str):
        """从指定目录更新专利规则（向量库 + 知识图谱）"""
        logger.info(f"📁 开始处理目录: {directory_path}")
        
        if not os.path.exists(directory_path):
            logger.error(f"❌ 目录不存在: {directory_path}")
            return
            
        # 获取所有法律文件
        legal_files = self._get_legal_files(directory_path)
        self.stats['total_files'] = len(legal_files)
        
        logger.info(f"📄 发现 {len(legal_files)} 个法律文件")
        
        # 处理每个文件
        all_rules: List[PatentRule] = []
        
        for file_path in legal_files:
            try:
                file_rules = await self._process_legal_file(file_path)
                all_rules.extend(file_rules)
                self.processed_files.add(file_path)
                self.stats['processed_files'] += 1
                
                logger.info(f"✅ 处理完成: {os.path.basename(file_path)} ({len(file_rules)} 条规则)")
                
            except Exception as e:
                error_msg = f"处理文件失败 {file_path}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
        
        # 去重处理
        logger.info('🔄 开始去重处理...')
        unique_rules = self._deduplicate_rules(all_rules)
        
        self.stats['total_rules'] = len(all_rules)
        self.stats['new_rules'] = len(unique_rules)
        self.stats['duplicate_rules'] = len(all_rules) - len(unique_rules)
        
        logger.info(f"📊 去重结果: 总计 {len(all_rules)} 条，唯一 {len(unique_rules)} 条，重复 {len(all_rules) - len(unique_rules)} 条")
        
        # 更新向量库
        if unique_rules:
            await self._update_vectors(unique_rules)
        
        # 构建知识图谱
        if unique_rules:
            await self._build_knowledge_graph(unique_rules)
        
        # 生成报告
        await self._generate_report(directory_path)
        
        logger.info('🎉 专利规则完整更新任务完成！')
        
    def _get_legal_files(self, directory_path: str) -> List[str]:
        """获取所有法律文件"""
        legal_files = []
        directory = Path(directory_path)
        
        # 支持的文件扩展名
        supported_extensions = {'.md', '.txt', '.docx', '.doc', '.pdf'}
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                # 跳过系统文件和隐藏文件
                if not file_path.name.startswith('.') and file_path.stat().st_size > 0:
                    legal_files.append(str(file_path))
        
        return sorted(legal_files)
    
    async def _process_legal_file(self, file_path: str) -> List[PatentRule]:
        """处理单个法律文件"""
        file_name = os.path.basename(file_path)
        logger.debug(f"📖 处理文件: {file_name}")
        
        try:
            # 读取文件内容
            content = await self._read_file_content(file_path)
            
            # 解析文件内容
            rules = await self._parse_legal_content(content, file_name)
            
            return rules
            
        except Exception as e:
            logger.error(f"❌ 处理文件失败 {file_path}: {e}")
            raise
    
    async def _read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.md', '.txt']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
        elif file_ext in ['.docx', '.doc']:
            # 这里需要使用python-docx库，暂时返回空
            logger.warning(f"⚠️ 暂不支持 {file_ext} 格式，跳过文件: {file_path}")
            return ''
        elif file_ext == '.pdf':
            # 这里需要使用PyPDF2或pdfplumber库，暂时返回空
            logger.warning(f"⚠️ 暂不支持 {file_ext} 格式，跳过文件: {file_path}")
            return ''
        else:
            logger.warning(f"⚠️ 不支持的文件格式: {file_ext}")
            return ''
    
    async def _parse_legal_content(self, content: str, file_name: str) -> List[PatentRule]:
        """解析法律内容"""
        rules = []
        
        # 根据文件类型使用不同的解析策略
        if '专利法' in file_name:
            rules = self._parse_patent_law(content, file_name)
        elif '专利法实施细则' in file_name:
            rules = self._parse_patent_law_rules(content, file_name)
        elif '审查指南' in file_name:
            rules = self._parse_examination_guide(content, file_name)
        elif '民法典' in file_name:
            rules = self._parse_civil_code(content, file_name)
        elif '司法解释' in file_name or '最高人民法院' in file_name:
            rules = self._parse_judicial_interpretation(content, file_name)
        else:
            # 通用解析
            rules = self._parse_generic_legal(content, file_name)
        
        logger.debug(f"📋 从 {file_name} 解析出 {len(rules)} 条规则")
        return rules
    
    def _parse_patent_law(self, content: str, file_name: str) -> List[PatentRule]:
        """解析专利法"""
        rules = []
        
        # 按条解析
        article_pattern = r'第[一二三四五六七八九十百千万\d]+条[：:]?\s*(.*?)(?=第[一二三四五六七八九十百千万\d]+条[：:]?|$)'
        articles = re.findall(article_pattern, content, re.DOTALL)
        
        for i, article_text in enumerate(articles, 1):
            if article_text.strip():
                # 提取章节信息
                chapter_match = re.search(r'第[一二三四五六七八九十百千万\d]+章[：:]?\s*(.*?)(?=第[一二三四五六七八九十百千万\d]+章[：:]?|第[一二三四五六七八九十百千万\d]+条|$)', content, re.DOTALL)
                
                metadata = {
                    'chunk_type': 'article',
                    'article_num': f"第{i}条",
                    'source_type': '专利法',
                    'file_name': file_name
                }
                
                if chapter_match:
                    metadata['chapter'] = {
                        'type': 'chapter',
                        'chapter_title': chapter_match.group(1).strip()
                    }
                
                # 分段处理长文章
                if len(article_text) > 500:
                    paragraphs = re.split(r'[。；]\s*', article_text)
                    for para in paragraphs:
                        if para.strip() and len(para.strip()) > 10:
                            rule = PatentRule(
                                text=para.strip() + '。',
                                source_file=file_name,
                                metadata={**metadata, 'paragraph_index': paragraphs.index(para)}
                            )
                            rules.append(rule)
                else:
                    rule = PatentRule(
                        text=article_text.strip(),
                        source_file=file_name,
                        metadata=metadata
                    )
                    rules.append(rule)
        
        return rules
    
    def _parse_patent_law_rules(self, content: str, file_name: str) -> List[PatentRule]:
        """解析专利法实施细则"""
        return self._parse_patent_law(content, file_name)  # 使用相同的解析逻辑
    
    def _parse_examination_guide(self, content: str, file_name: str) -> List[PatentRule]:
        """解析专利审查指南"""
        rules = []
        
        # 按章节和子章节解析
        chapter_pattern = r'第[一二三四五六七八九十百千万\d]+章[：:]?\s*(.*?)(?=第[一二三四五六七八九十百千万\d]+章[：:]?|$)'
        chapters = re.findall(chapter_pattern, content, re.DOTALL)
        
        for i, chapter_content in enumerate(chapters, 1):
            # 进一步按小节解析
            section_pattern = r'第[一二三四五六七八九十百千万\d]+节[：:]?\s*(.*?)(?=第[一二三四五六七八九十百千万\d]+节[：:]?|第[一二三四五六七八九十百千万\d]+章|$)'
            sections = re.findall(section_pattern, chapter_content, re.DOTALL)
            
            if sections:
                for j, section_content in enumerate(sections, 1):
                    if section_content.strip():
                        metadata = {
                            'chunk_type': 'section',
                            'chapter_num': f"第{i}章",
                            'section_num': f"第{j}节",
                            'source_type': '专利审查指南',
                            'file_name': file_name
                        }
                        
                        rule = PatentRule(
                            text=section_content.strip(),
                            source_file=file_name,
                            metadata=metadata
                        )
                        rules.append(rule)
            else:
                # 没有小节，整个章节作为一个规则
                if chapter_content.strip():
                    metadata = {
                        'chunk_type': 'chapter',
                        'chapter_num': f"第{i}章",
                        'source_type': '专利审查指南',
                        'file_name': file_name
                    }
                    
                    rule = PatentRule(
                        text=chapter_content.strip(),
                        source_file=file_name,
                        metadata=metadata
                    )
                    rules.append(rule)
        
        return rules
    
    def _parse_civil_code(self, content: str, file_name: str) -> List[PatentRule]:
        """解析民法典"""
        rules = []
        
        # 民法典通常按条文解析
        article_pattern = r'第[一二三四五六七八九十百千万\d]+条[：:]?\s*(.*?)(?=第[一二三四五六七八九十百千万\d]+条[：:]?|$)'
        articles = re.findall(article_pattern, content, re.DOTALL)
        
        for i, article_text in enumerate(articles, 1):
            if article_text.strip() and len(article_text.strip()) > 20:  # 过滤太短的条文
                metadata = {
                    'chunk_type': 'article',
                    'article_num': f"第{i}条",
                    'source_type': '民法典',
                    'file_name': file_name,
                    'relevance_to_patent': self._assess_patent_relevance(article_text)
                }
                
                rule = PatentRule(
                    text=article_text.strip(),
                    source_file=file_name,
                    metadata=metadata
                )
                rules.append(rule)
        
        return rules
    
    def _parse_judicial_interpretation(self, content: str, file_name: str) -> List[PatentRule]:
        """解析司法解释"""
        rules = []
        
        # 按条款或要点解析
        clause_pattern = r'(?:第[一二三四五六七八九十百千万\d]+条|[一二三四五六七八九十百千万\d]+[、.．])[:：]?\s*(.*?)(?=(?:第[一二三四五六七八九十百千万\d]+条|[一二三四五六七八九十百千万\d]+[、.．])[:：]?|$)'
        clauses = re.findall(clause_pattern, content, re.DOTALL)
        
        for i, clause_text in enumerate(clauses, 1):
            if clause_text.strip() and len(clause_text.strip()) > 15:
                metadata = {
                    'chunk_type': 'clause',
                    'clause_num': f"{i}",
                    'source_type': '司法解释',
                    'file_name': file_name
                }
                
                rule = PatentRule(
                    text=clause_text.strip(),
                    source_file=file_name,
                    metadata=metadata
                )
                rules.append(rule)
        
        return rules
    
    def _parse_generic_legal(self, content: str, file_name: str) -> List[PatentRule]:
        """通用法律文本解析"""
        rules = []
        
        # 按段落解析
        paragraphs = re.split(r'\n\s*\n', content)
        
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50 and not para.startswith('#'):  # 过滤太短的段落和标题
                metadata = {
                    'chunk_type': 'paragraph',
                    'paragraph_index': paragraphs.index(para),
                    'source_type': '法律文本',
                    'file_name': file_name
                }
                
                rule = PatentRule(
                    text=para,
                    source_file=file_name,
                    metadata=metadata
                )
                rules.append(rule)
        
        return rules
    
    def _assess_patent_relevance(self, text: str) -> str:
        """评估文本与专利的相关性"""
        patent_keywords = [
            '专利', '发明', '实用新型', '外观设计', '申请', '审查',
            '授权', '权利要求', '说明书', '新颖性', '创造性', '实用性',
            '侵权', '保护', '期限', '费用', '代理', '异议', '无效'
        ]
        
        relevance_score = sum(1 for keyword in patent_keywords if keyword in text)
        
        if relevance_score >= 3:
            return '高'
        elif relevance_score >= 1:
            return '中'
        else:
            return '低'
    
    def _deduplicate_rules(self, rules: List[PatentRule]) -> List[PatentRule]:
        """去重处理"""
        unique_rules = []
        seen_hashes: Set[str] = set()
        
        for rule in rules:
            if rule.text_hash not in seen_hashes and rule.text_hash not in self.existing_hashes:
                unique_rules.append(rule)
                seen_hashes.add(rule.text_hash)
            elif rule.text_hash in seen_hashes:
                # 本次处理中的重复
                self.stats['duplicate_rules'] += 1
                
        return unique_rules
    
    async def _update_vectors(self, rules: List[PatentRule]):
        """更新向量库"""
        logger.info(f"🔄 开始向量化 {len(rules)} 条新规则...")
        
        # 分批处理
        batch_size = 100
        total_batches = (len(rules) + batch_size - 1) // batch_size
        
        for i in range(0, len(rules), batch_size):
            batch = rules[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 条)")
            
            # 生成向量（这里使用随机向量，实际应该使用embedding模型）
            vectors = []
            points = []
            
            for rule in batch:
                # 生成向量（使用简单的文本哈希到向量，实际应该用embedding模型）
                vector = self._text_to_vector(rule.text)
                
                point = models.PointStruct(
                    id=hash(rule.text_hash) % (2**31),  # 使用哈希作为ID
                    vector=vector,
                    payload=rule.to_dict()
                )
                
                points.append(point)
            
            try:
                # 上传到Qdrant
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                self.stats['updated_vectors'] += len(points)
                logger.info(f"✅ 批次 {batch_num} 上传成功")
                
                # 避免请求过快
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ 批次 {batch_num} 上传失败: {e}")
                self.stats['errors'].append(f"批次 {batch_num} 上传失败: {e}")
    
    async def _build_knowledge_graph(self, rules: List[PatentRule]):
        """构建知识图谱"""
        logger.info(f"🕸️ 开始构建知识图谱，基于 {len(rules)} 条规则...")
        
        try:
            # 将规则转换为字典格式
            rules_dict = [rule.to_dict() for rule in rules]
            
            # 构建知识图谱
            graph_data = self.graph_builder.build_graph_from_rules(rules_dict)
            
            # 更新统计信息
            self.stats['graph_nodes'] = graph_data['statistics']['nodes_count']
            self.stats['graph_relations'] = graph_data['statistics']['relations_count']
            
            # 保存知识图谱
            graph_file = f"/Users/xujian/Athena工作平台/patent_rules_knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.graph_builder.save_graph_to_file(graph_data, graph_file)
            
            logger.info(f"✅ 知识图谱构建完成: {self.stats['graph_nodes']} 节点, {self.stats['graph_relations']} 关系")
            logger.info(f"💾 知识图谱已保存: {graph_file}")
            
        except Exception as e:
            logger.error(f"❌ 知识图谱构建失败: {e}")
            self.stats['errors'].append(f"知识图谱构建失败: {e}")
    
    def _text_to_vector(self, text: str) -> List[float]:
        """文本转向量（简化版本，实际应该使用专业的embedding模型）"""
        # 这里使用简单的哈希方法，实际应该使用BERT等embedding模型
        import hashlib

        # 将文本分割为固定长度的向量
        vector = []
        text_bytes = text.encode('utf-8')
        
        # 使用SHA256哈希生成向量
        hash_obj = hashlib.sha256(text_bytes)
        hash_bytes = hash_obj.digest()
        
        # 将字节转换为浮点数并扩展到1024维
        base_vector = [float(b) / 255.0 for b in hash_bytes]
        
        # 扩展到1024维
        while len(vector) < self.vector_size:
            vector.extend(base_vector)
        
        return vector[:self.vector_size]
    
    async def _generate_report(self, directory_path: str):
        """生成更新报告"""
        report_content = f"""
# 专利规则向量库和知识图谱完整更新报告

## 更新时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 数据源
- 目录: {directory_path}
- 文件总数: {self.stats['total_files']}
- 成功处理: {self.stats['processed_files']}

## 处理结果
- 总规则数: {self.stats['total_rules']}
- 新增规则: {self.stats['new_rules']}
- 重复规则: {self.stats['duplicate_rules']}
- 更新向量: {self.stats['updated_vectors']}
- 知识图谱节点: {self.stats['graph_nodes']}
- 知识图谱关系: {self.stats['graph_relations']}

## 系统状态
- Qdrant集合: {self.collection_name}
- 向量维度: {self.vector_size}
- 现有规则哈希数: {len(self.existing_hashes) + self.stats['new_rules']}

## 错误信息
{chr(10).join(f"- {error}" for error in self.stats['errors']) if self.stats['errors'] else "无错误"}

## 处理的文件
{chr(10).join(f"- {file}" for file in self.processed_files)}

## 技术说明
- 向量化方法: 简化哈希向量（实际应使用专业embedding模型）
- 去重策略: 基于文本MD5哈希
- 知识图谱构建: 包含概念、程序、期限等多层次关系
- 文件格式支持: .md, .txt（其他格式待扩展）
"""
        
        # 保存报告
        report_file = f"/Users/xujian/Athena工作平台/patent_rules_complete_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📄 完整更新报告已保存: {report_file}")
        
        # 保存统计信息
        stats_file = f"/Users/xujian/Athena工作平台/patent_rules_complete_update_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 统计信息已保存: {stats_file}")

async def main():
    """主函数"""
    logger.info('🏛️ Athena专利规则向量库和知识图谱完整更新系统启动')
    
    # 确保日志目录存在
    os.makedirs('/Users/xujian/Athena工作平台/logs', exist_ok=True)
    
    try:
        # 创建更新器
        updater = PatentRulesCompleteUpdater()
        await updater.initialize()
        
        # 设置数据源路径
        data_source = '/Volumes/xujian/开发项目备份/专利相关法律法规'
        
        # 执行更新
        await updater.update_from_directory(data_source)
        
        logger.info('🎉 专利规则完整更新任务完成！')
        
    except Exception as e:
        logger.error(f"❌ 更新任务失败: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())