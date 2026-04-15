#!/usr/bin/env python3
"""
专利规则三模型高质量增强处理器（修复版）
Triple-Model High-Quality Enhancement Processor for Patent Rules (Fixed)

使用三个本地模型对已有JSON文件进行最高质量再处理:
1. BGE-M3: 生成1024维高质量向量 (MPS优化)
2. BERT-NER: 增强实体识别
3. DeepSeek-R1: 深度语义理解、推理增强和智能层级拆解

特色功能:
- 法律法规：从法律→章节→条→款→项完整拆解
- 专利审查指南：从部分→章→节→最小段落完整拆解
- 使用DeepSeek-R1进行智能的层级识别、推理和拆解（Chain-of-Thought）

作者: Athena平台团队
创建时间: 2026-01-20
更新时间: 2026-01-20 (升级至DeepSeek-R1)
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/triple_model_enhancer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """处理统计信息"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0
    bge_m3_time: float = 0.0
    bert_ner_time: float = 0.0
    qwen_time: float = 0.0
    total_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'total_chunks': self.total_chunks,
            'bge_m3_time': self.bge_m3_time,
            'bert_ner_time': self.bert_ner_time,
            'qwen_time': self.qwen_time,
            'total_time': self.total_time,
            'success_rate': f"{(self.processed_files / self.total_files * 100):.2f}%" if self.total_files > 0 else "N/A",
            'avg_time_per_file': f"{(self.total_time / self.processed_files):.2f}秒" if self.processed_files > 0 else "N/A"
        }


@dataclass
class HierarchyNode:
    """层级节点"""
    level: str  # 'law', 'chapter', 'article', 'paragraph', 'item' 等
    title: str
    content: str
    path: list[str] = field(default_factory=list)
    children: list['HierarchyNode'] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'level': self.level,
            'title': self.title,
            'content': self.content,
            'path': self.path,
            'children': [child.to_dict() for child in self.children],
            'metadata': self.metadata
        }


class LegalHierarchyParser:
    """法律文档层级解析器"""

    # 法律层级模式
    LAW_PATTERNS = {
        'law': r'^[第第][一二三四五六七八九十百千万零]+[编编部部]$',
        'chapter': r'^[第第][一二三四五六七八九十百千万零]+[章章节节]$',
        'section': r'^[第第][一二三四五六七八九十百千万零]+[节节]$',
        'article': r'^[第第]\d+[条条]$',
        'paragraph': r'^[（\(]\d+[）\)]',
        'item': r'^[（\(][一二三四五六七八九十百千万零]+[）\)]',
        'sub_item': r'^\d+[\..、]|^[一二三四五六七八九十百千万零]+[\..、]'
    }

    # 专利审查指南层级模式
    GUIDELINE_PATTERNS = {
        'part': r'^[第第][一二三四五六七八九十百千万零]+[部分分]$',
        'chapter': r'^[第第][一二三四五六七八九十百千万零]+[章章节节]$',
        'section': r'^[一二三四五六七八九十百千万零]+[\.、．]\s*\d+',
        'subsection': r'^\d+[\.\．]\s*\d+',
        'paragraph': r'^[（\(]\d+[）\)]'
    }

    def __init__(self, document_type: str = 'law'):
        """
        初始化解析器

        Args:
            document_type: 文档类型 ('law' 或 'guideline')
        """
        self.document_type = document_type
        self.patterns = self.LAW_PATTERNS if document_type == 'law' else self.GUIDELINE_PATTERNS

    def parse_document(self, text: str, metadata: dict[str, Any]) -> HierarchyNode:
        """
        解析文档为层级结构

        Args:
            text: 文档文本
            metadata: 元数据

        Returns:
            根节点
        """
        lines = text.split('\n')
        root = HierarchyNode(
            level='root',
            title=metadata.get('title', '文档'),
            content='',
            path=[],
            metadata=metadata
        )

        current_path: list[HierarchyNode] = [root]
        detected_hierarchy = False  # 跟踪是否检测到层级结构

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测层级
            level_info = self._detect_level(line)

            if level_info:
                detected_hierarchy = True
                level, title = level_info

                # 创建新节点
                node = HierarchyNode(
                    level=level,
                    title=title,
                    content=line,
                    path=[n.title for n in current_path],
                    metadata={
                        'line_number': len(current_path),
                        'level_depth': len(current_path)
                    }
                )

                # 找到正确的父节点
                while len(current_path) > 1 and self._should_close_node(current_path[-1].level, level):
                    current_path.pop()

                # 添加到父节点
                current_path[-1].children.append(node)
                current_path.append(node)

            else:
                # 添加内容到当前节点
                if len(current_path) > 1:
                    current_path[-1].content += '\n' + line
                else:
                    # 没有层级节点时，收集到临时缓冲区
                    if not hasattr(root, '_content_buffer'):
                        root._content_buffer = []
                    root._content_buffer.append(line)

        # Fallback: 如果没有检测到层级结构，创建单个文本节点
        if not detected_hierarchy and text.strip():
            fallback_node = HierarchyNode(
                level='document',  # 使用通用层级
                title=metadata.get('title', '文档'),
                content=text.strip(),
                path=[metadata.get('title', '文档')],
                metadata=metadata
            )
            root.children.append(fallback_node)

        return root

    def _detect_level(self, line: str) -> tuple[str, str | None]:
        """检测行所属的层级"""
        for level, pattern in self.patterns.items():
            if re.match(pattern, line):
                return level, line
        return None

    def _should_close_node(self, current_level: str, new_level: str) -> bool:
        """判断是否应该关闭当前节点"""
        level_order = {
            'root': 0,
            'law': 1, 'part': 1,
            'chapter': 2,
            'section': 3,
            'article': 4, 'subsection': 4,
            'paragraph': 5,
            'item': 6,
            'sub_item': 7
        }

        current_depth = level_order.get(current_level, 999)
        new_depth = level_order.get(new_level, 999)

        return new_depth <= current_depth

    def flatten_to_chunks(self, root: HierarchyNode) -> list[dict[str, Any]]:
        """将层级结构展平为文本块"""
        chunks = []

        def traverse(node: HierarchyNode, parent_path: list[str] = None) -> Any:
            if parent_path is None:
                parent_path = []

            current_path = parent_path + [node.title]

            # 如果有内容，创建文本块
            if node.content.strip() and node.level != 'root':
                chunk = {
                    'chunk_id': hashlib.md5(node.content.encode('utf-8'), usedforsecurity=False).hexdigest()[:16],
                    'level': node.level,
                    'title': node.title,
                    'content': node.content.strip(),
                    'path': current_path,
                    'path_string': ' > '.join(current_path),
                    'metadata': {
                        **node.metadata,
                        'document_type': self.document_type
                    }
                }
                chunks.append(chunk)

            # 递归处理子节点
            for child in node.children:
                traverse(child, current_path)

        traverse(root)
        return chunks


class TripleModelEnhancer:
    """三模型高质量增强处理器（修复版）"""

    def __init__(self):
        """初始化处理器"""
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.input_dir = Path("/Users/xujian/语料/专利-json")
        self.output_dir = Path("/Users/xujian/语料/专利-json-enhanced-v4")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 模型实例
        self.bge_m3_embedder: Any | None = None
        self.bert_ner_extractor: Any | None = None
        # 注意: DeepSeek-R1需要llama-cpp-python，如果没有安装会跳过

        # 统计信息
        self.stats = ProcessingStats()

        # 文档类型解析器
        self.law_parser = LegalHierarchyParser(document_type='law')
        self.guideline_parser = LegalHierarchyParser(document_type='guideline')

        logger.info("=" * 80)
        logger.info("🚀 三模型高质量增强处理器初始化（修复版）")
        logger.info("=" * 80)

    async def initialize_bge_m3(self) -> bool:
        """初始化BGE-M3模型（向量生成）"""
        logger.info("=" * 80)
        logger.info("📊 初始化BGE-M3模型（1024维高质量向量）")
        logger.info("=" * 80)

        try:
            from core.embedding.bge_m3_embedder import BGE_M3_Embedder

            # 模型路径
            model_path = self.base_dir / "models/converted/BAAI/bge-m3"

            # 创建嵌入器（MPS优化）
            self.bge_m3_embedder = BGE_M3_Embedder(
                model_path=str(model_path),
                device='auto'  # 自动检测MPS > CUDA > CPU
            )

            # 初始化
            await self.bge_m3_embedder.initialize()

            logger.info("✅ BGE-M3模型初始化成功")
            if hasattr(self.bge_m3_embedder, 'device'):
                logger.info(f"   设备: {self.bge_m3_embedder.device}")
            logger.info("   向量维度: 1024")

            return True

        except Exception as e:
            logger.error(f"❌ BGE-M3初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def initialize_bert_ner(self) -> bool:
        """初始化BERT-NER模型（实体识别）"""
        logger.info("=" * 80)
        logger.info("🔍 初始化BERT-NER模型（增强实体识别）")
        logger.info("=" * 80)

        try:
            from core.nlp.bert_ner_extractor import BertNERExtractor

            # 创建NER抽取器（MPS优化）
            self.bert_ner_extractor = BertNERExtractor(
                model_path="/Users/xujian/Athena工作平台/models/converted/hfl/chinese-roberta-wwm-ext-large",
                device='auto'  # 自动检测MPS > CUDA > CPU
            )

            # 初始化
            await self.bert_ner_extractor.initialize()

            logger.info("✅ BERT-NER模型初始化成功")
            if hasattr(self.bert_ner_extractor, 'device'):
                logger.info(f"   设备: {self.bert_ner_extractor.device}")
            if hasattr(self.bert_ner_extractor, 'entity_types'):
                logger.info(f"   实体类型: {', '.join(self.bert_ner_extractor.entity_types.values())}")

            return True

        except Exception as e:
            logger.error(f"❌ BERT-NER初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def initialize_qwen(self) -> bool:
        """初始化DeepSeek-R1模型（文本增强）"""
        logger.info("=" * 80)
        logger.info("🧠 尝试初始化DeepSeek-R1模型（深度语义理解与推理）")
        logger.info("=" * 80)

        try:
            # 检查是否安装了llama-cpp-python
            try:
                import importlib.util
                spec = importlib.util.find_spec("llama_cpp")
            except (ImportError, AttributeError):
                spec = None

            if spec is None:
                logger.warning("⚠️ llama-cpp-python未安装")
                logger.info("💡 安装提示: conda install -c conda-forge llama-cpp-python")
                logger.info("💡 或: pip install llama-cpp-python")
                logger.info("💡 将跳过DeepSeek-R1文本增强")
                return False

            from llama_cpp import Llama

            # 模型路径 - 支持多个可能的路径
            possible_paths = [
                self.base_dir / "models/converted/DeepSeek-R1/unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF",  # ModelScope格式
                self.base_dir / "models/converted/DeepSeek-R1",  # 直接路径
            ]

            model_path = None
            for path in possible_paths:
                if path.exists():
                    model_path = path
                    break

            if model_path is None:
                logger.warning("⚠️ DeepSeek-R1模型路径不存在")
                for path in possible_paths:
                    logger.warning(f"   - {path}")
                logger.info("💡 将跳过DeepSeek-R1文本增强")
                return False

            # 寻找GGUF文件（优先选择Q4_K_M以平衡性能和质量）
            gguf_files = list(model_path.glob("*.gguf"))
            if not gguf_files:
                logger.warning("⚠️ 没有找到GGUF模型文件")
                return False

            # 优先选择Q4_K_M量化版本（性能与质量的最佳平衡）
            preferred_files = [f for f in gguf_files if "Q4_K_M" in f.name]
            if preferred_files:
                model_file = preferred_files[0]
            else:
                # 备选：使用最小的单一GGUF文件（排除分片文件）
                single_files = [f for f in gguf_files if "of-" not in f.name]
                if single_files:
                    model_file = sorted(single_files, key=lambda x: x.stat().st_size)[0]
                else:
                    # 如果没有单一文件，使用最小的分片文件
                    model_file = sorted(gguf_files, key=lambda x: x.stat().st_size)[0]

            logger.info(f"🔄 加载DeepSeek-R1模型: {model_file.name}")
            logger.info(f"📁 模型路径: {model_file}")

            # 创建LLaMA实例 - 针对14B模型优化参数
            self.qwen_generator = Llama(
                model_path=str(model_file),
                n_ctx=8192,  # 增加上下文长度以支持更长的推理链
                n_threads=8,  # 线程数
                n_gpu_layers=-1,  # 使用GPU加速（如果可用）
                verbose=False,
                # DeepSeek-R1特定参数
                temperature=0.6,  # 降低温度以获得更确定的输出
                top_p=0.9,  # nucleus sampling
            )

            logger.info("✅ DeepSeek-R1模型初始化成功")
            logger.info("   上下文长度: 8192")
            logger.info(f"   模型文件: {model_file.name}")
            logger.info("   模型类型: DeepSeek-R1-Distill-Qwen-14B")
            logger.info("   推理优化: Chain-of-Thought推理增强")

            return True

        except ImportError as e:
            logger.warning(f"⚠️ 无法导入llama_cpp: {e}")
            logger.info("💡 将跳过DeepSeek-R1文本增强")
            return False
        except Exception as e:
            logger.error(f"❌ DeepSeek-R1初始化失败: {e}")
            logger.info("💡 将跳过DeepSeek-R1文本增强")
            return False

    async def enhance_with_bge_m3(
        self,
        text: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """使用BGE-M3生成高质量向量"""
        start_time = time.time()

        try:
            if self.bge_m3_embedder is None:
                return {
                    'embedding': None,
                    'error': 'BGE-M3模型未初始化',
                    'skipped': True
                }

            # 生成向量
            embedding = await self.bge_m3_embedder.embed_text(text)

            elapsed_time = time.time() - start_time
            self.stats.bge_m3_time += elapsed_time

            return {
                'embedding': embedding,
                'embedding_dimension': len(embedding),
                'embedding_model': 'bge-m3',
                'generation_time': elapsed_time,
                'embedding_quality': 'high',
                'skipped': False
            }

        except Exception as e:
            logger.error(f"❌ BGE-M3向量化失败: {e}")
            return {
                'embedding': None,
                'error': str(e),
                'skipped': False
            }

    async def enhance_with_bert_ner(
        self,
        text: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """使用BERT-NER增强实体识别"""
        start_time = time.time()

        try:
            if self.bert_ner_extractor is None:
                return {
                    'entities': [],
                    'relations': [],
                    'error': 'BERT-NER模型未初始化',
                    'skipped': True
                }

            # 抽取实体
            entities = await self.bert_ner_extractor.extract_entities(text)

            # 抽取关系
            relations = await self.bert_ner_extractor.extract_relations(text, entities)

            elapsed_time = time.time() - start_time
            self.stats.bert_ner_time += elapsed_time

            return {
                'entities': entities,
                'relations': relations,
                'entity_count': len(entities),
                'relation_count': len(relations),
                'extraction_model': 'bert-ner',
                'generation_time': elapsed_time,
                'skipped': False
            }

        except Exception as e:
            logger.error(f"❌ BERT-NER实体抽取失败: {e}")
            return {
                'entities': [],
                'relations': [],
                'error': str(e),
                'skipped': False
            }

    async def enhance_with_qwen(
        self,
        text: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """使用DeepSeek-R1进行深度语义理解与推理增强"""
        # 使用hasattr检查属性是否存在
        if not hasattr(self, 'qwen_generator') or self.qwen_generator is None:
            return {
                'enhanced_content': None,
                'skipped': True,
                'reason': 'DeepSeek-R1模型未初始化'
            }

        start_time = time.time()

        try:
            # 构建提示词 - 利用DeepSeek-R1的Chain-of-Thought推理能力
            level = metadata.get('level', '')
            title = metadata.get('title', '')

            prompt = f"""你是一位资深的专利规则专家，擅长深度分析和推理。请对以下专利规则内容进行全面的分析和增强。

【规则信息】
层级类型: {level}
标题: {title}

【原文内容】
{text}

【分析任务】
请运用链式推理(Chain-of-Thought)方法，逐步分析以下内容:

1. **内容理解**: 逐句理解原文，识别关键信息
2. **概念提取**: 提取核心概念和术语
3. **关联分析**: 分析与其他规则的关联性
4. **应用场景**: 推导实际应用场景
5. **风险识别**: 识别可能的误解风险点

【输出格式】
请以JSON格式输出分析结果:
{{
    "thinking_process": "简述你的推理过程（2-3句话）",
    "summary": "简明扼要的内容总结（1-2句话）",
    "key_concepts": ["核心概念1", "核心概念2"],
    "practical_guidance": "实际应用指导（如果适用）",
    "related_rules": ["相关规则1"],
    "risk_points": ["风险点1"],
    "reasoning_quality": "high/medium/low"
}}

请严格按照JSON格式输出，不要包含其他内容:"""

            # 生成响应 - 增加token以支持推理链
            response = self.qwen_generator(
                prompt,
                max_tokens=1024,  # 增加以支持更长的推理输出
                stop=["\n\n"],
                echo=False
            )

            # 解析响应
            response_text = response['choices'][0]['text'].strip()

            # 尝试解析JSON
            try:
                enhanced_content = json.loads(response_text)
            except json.JSONDecodeError:
                # 如果解析失败，创建简单的增强内容
                enhanced_content = {
                    'thinking_process': 'N/A',
                    'summary': response_text[:200] if len(response_text) > 200 else response_text,
                    'key_concepts': [],
                    'practical_guidance': '',
                    'related_rules': [],
                    'risk_points': [],
                    'reasoning_quality': 'unknown'
                }

            elapsed_time = time.time() - start_time
            self.stats.qwen_time += elapsed_time

            return {
                'enhanced_content': enhanced_content,
                'enhancement_model': 'deepseek-r1',
                'generation_time': elapsed_time,
                'skipped': False
            }

        except Exception as e:
            logger.error(f"❌ DeepSeek-R1文本增强失败: {e}")
            return {
                'enhanced_content': None,
                'error': str(e),
                'skipped': False
            }

    def parse_document_hierarchy(
        self,
        data: dict[str, Any],
        file_path: Path
    ) -> list[dict[str, Any]]:
        """
        解析文档层级结构

        Args:
            data: 原始JSON数据
            file_path: 文件路径

        Returns:
            解析后的文本块列表
        """
        # 确定文档类型
        file_name = file_path.name.lower()
        if 'guideline' in file_name or '审查指南' in str(file_path):
            parser = self.guideline_parser
            doc_type = 'guideline'
        else:
            parser = self.law_parser
            doc_type = 'law'

        # 获取文本内容
        content = data.get('content', {})
        text = content.get('raw_text', '') or content.get('enhanced_text', '')

        if not text:
            logger.warning(f"⚠️ 文件没有文本内容: {file_path.name}")
            return []

        # 获取元数据
        metadata = {
            'title': content.get('title', ''),
            'section_id': data.get('section_id', file_path.stem),
            'file_name': file_path.name,
            'document_type': doc_type
        }

        # 解析层级结构
        root = parser.parse_document(text, metadata)

        # 展平为文本块
        chunks = parser.flatten_to_chunks(root)

        logger.info(f"   📊 解析出 {len(chunks)} 个文本块")

        return chunks

    async def process_json_file(self, json_file: Path) -> dict[str, Any | None]:
        """处理单个JSON文件"""
        try:
            # 读取原始JSON
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"🔄 处理文件: {json_file.name}")

            # 解析文档层级结构
            chunks = self.parse_document_hierarchy(data, json_file)

            if not chunks:
                logger.warning(f"⚠️ 没有解析到文本块: {json_file.name}")
                return None

            # 处理每个文本块
            enhanced_chunks = []
            self.stats.total_chunks += len(chunks)

            # 初始化结果变量（用于后面的元数据）
            last_bge_m3_result = {'skipped': True}
            last_bert_ner_result = {'skipped': True}
            last_qwen_result = {'skipped': True}

            for i, chunk in enumerate(chunks):
                logger.info(f"   处理块 {i+1}/{len(chunks)}: {chunk['level']} - {chunk['title'][:30]}")

                # 并行执行三个模型的增强
                bge_m3_result, bert_ner_result, qwen_result = await asyncio.gather(
                    self.enhance_with_bge_m3(chunk['content'], chunk),
                    self.enhance_with_bert_ner(chunk['content'], chunk),
                    self.enhance_with_qwen(chunk['content'], chunk),
                    return_exceptions=True
                )

                # 处理异常
                if isinstance(bge_m3_result, Exception):
                    logger.error(f"   ❌ BGE-M3处理异常: {bge_m3_result}")
                    bge_m3_result = {'embedding': None, 'error': str(bge_m3_result), 'skipped': False}

                if isinstance(bert_ner_result, Exception):
                    logger.error(f"   ❌ BERT-NER处理异常: {bert_ner_result}")
                    bert_ner_result = {'entities': [], 'error': str(bert_ner_result), 'skipped': False}

                if isinstance(qwen_result, Exception):
                    logger.error(f"   ❌ Qwen处理异常: {qwen_result}")
                    qwen_result = {'enhanced_content': None, 'error': str(qwen_result), 'skipped': False}

                # 保存最后一个结果用于元数据
                last_bge_m3_result = bge_m3_result
                last_bert_ner_result = bert_ner_result
                last_qwen_result = qwen_result

                # 构建增强后的文本块
                enhanced_chunk = {
                    **chunk,
                    'bge_m3_embedding': bge_m3_result,
                    'bert_ner_entities': bert_ner_result,
                    'qwen_enhancement': qwen_result
                }

                enhanced_chunks.append(enhanced_chunk)

            # 构建增强后的数据
            enhanced_data = {
                # 保留原始数据
                'original_data': data,

                # 层级解析信息
                'hierarchy_info': {
                    'total_chunks': len(chunks),
                    'document_type': chunks[0].get('metadata', {}).get('document_type', 'unknown') if chunks else 'unknown',
                    'levels_found': list({chunk['level'] for chunk in chunks})
                },

                # 增强后的文本块
                'enhanced_chunks': enhanced_chunks,

                # 处理元数据
                'processing_metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'original_file': str(json_file),
                    'chunks_processed': len(enhanced_chunks),
                    'models_used': {
                        'bge_m3': not last_bge_m3_result.get('skipped', False),
                        'bert_ner': not last_bert_ner_result.get('skipped', False),
                        'qwen': not last_qwen_result.get('skipped', False)
                    }
                }
            }

            return enhanced_data

        except Exception as e:
            logger.error(f"❌ 处理文件失败 {json_file.name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def process_directory(self, subdirectory: str = "guideline"):
        """处理指定子目录"""
        logger.info("=" * 80)
        logger.info(f"🚀 开始处理子目录: {subdirectory}")
        logger.info("=" * 80)

        input_path = self.input_dir / subdirectory
        output_path = self.output_dir / subdirectory
        output_path.mkdir(parents=True, exist_ok=True)

        # 获取所有JSON文件
        json_files = list(input_path.glob("*.json"))
        self.stats.total_files = len(json_files)

        logger.info(f"📦 发现 {len(json_files)} 个JSON文件")

        # 批量处理
        batch_size = 5  # 减少批处理大小以避免内存问题
        for i in range(0, len(json_files), batch_size):
            batch = json_files[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(json_files) + batch_size - 1) // batch_size

            logger.info(f"\n📊 处理批次 {batch_num}/{total_batches} ({len(batch)} 个文件)")

            # 并行处理批次中的文件
            tasks = [self.process_json_file(json_file) for json_file in batch]
            results = await asyncio.gather(*tasks)

            # 保存结果
            for json_file, enhanced_data in zip(batch, results, strict=False):
                if enhanced_data:
                    # 保存增强后的文件
                    output_file = output_path / json_file.name

                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)

                    self.stats.processed_files += 1
                    logger.info(f"✅ 已保存: {output_file.name}")
                else:
                    self.stats.failed_files += 1

            # 显示进度
            progress = (i + len(batch)) / len(json_files) * 100
            logger.info(f"📈 进度: {progress:.1f}% ({self.stats.processed_files}/{len(json_files)})")

    async def run_full_pipeline(self):
        """运行完整管道"""
        logger.info("=" * 80)
        logger.info("🚀 启动三模型高质量增强管道（修复版）")
        logger.info("=" * 80)

        total_start_time = time.time()

        try:
            # 1. 初始化所有模型
            logger.info("\n📋 步骤 1/5: 初始化模型")

            bge_m3_ok = await self.initialize_bge_m3()
            bert_ner_ok = await self.initialize_bert_ner()
            qwen_ok = await self.initialize_qwen()

            if not bge_m3_ok:
                logger.error("❌ BGE-M3初始化失败，终止处理")
                return

            if not bert_ner_ok:
                logger.warning("⚠️ BERT-NER初始化失败，将跳过实体识别增强")

            if not qwen_ok:
                logger.warning("⚠️ Qwen初始化失败，将跳过文本增强")

            # 2. 处理各个子目录
            subdirs = ['guideline', 'core', 'others', '专利法律-json']

            for idx, subdir in enumerate(subdirs, 1):
                subdir_path = self.input_dir / subdir
                if subdir_path.exists():
                    logger.info(f"\n📋 步骤 {1+idx}/5: 处理{subdir}目录")
                    await self.process_directory(subdir)
                else:
                    logger.info(f"⏭️ 跳过不存在的目录: {subdir}")

            # 3. 生成报告
            logger.info("\n📋 步骤 5/5: 生成处理报告")
            self.stats.total_time = time.time() - total_start_time

            report = {
                'completed_at': datetime.now().isoformat(),
                'statistics': self.stats.to_dict(),
                'models_used': {
                    'bge_m3': {
                        'initialized': bge_m3_ok,
                        'status': '✅ 成功' if bge_m3_ok else '❌ 失败'
                    },
                    'bert_ner': {
                        'initialized': bert_ner_ok,
                        'status': '✅ 成功' if bert_ner_ok else '❌ 失败'
                    },
                    'qwen': {
                        'initialized': qwen_ok,
                        'status': '✅ 成功' if qwen_ok else '❌ 失败'
                    }
                },
                'output_directory': str(self.output_dir),
                'processing_features': {
                    'hierarchy_parsing': '✅ 法律层级自动解析',
                    'law_structure': '✅ 法律→章节→条→款→项',
                    'guideline_structure': '✅ 部分→章→节→最小段落',
                    'bge_m3_embeddings': '✅ 1024维高质量向量' if bge_m3_ok else '❌ 未启用',
                    'bert_ner_entities': '✅ 增强实体识别' if bert_ner_ok else '❌ 未启用',
                    'qwen_enhancement': '✅ 深度语义理解' if qwen_ok else '❌ 未启用'
                }
            }

            # 保存报告
            report_file = self.output_dir / f"enhancement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info("=" * 80)
            logger.info("🎉 三模型高质量增强完成！")
            logger.info("=" * 80)
            logger.info(f"📊 处理文件: {self.stats.processed_files}/{self.stats.total_files}")
            logger.info(f"📦 处理文本块: {self.stats.total_chunks}")
            logger.info(f"⏱️ 总耗时: {self.stats.total_time:.2f}秒")
            logger.info(f"📄 报告: {report_file}")
            logger.info(f"📁 输出目录: {self.output_dir}")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ 管道执行失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    enhancer = TripleModelEnhancer()
    await enhancer.run_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
