#!/usr/bin/env python3
"""
专利规则三模型高质量增强处理器
Triple-Model High-Quality Enhancement Processor for Patent Rules

使用三个本地模型对已有JSON文件进行最高质量再处理:
1. BGE-M3: 生成1024维高质量向量 (MPS优化)
2. BERT-NER: 增强实体识别
3. Qwen 2.5: 深度语义理解和内容增强

作者: Athena平台团队
创建时间: 2026-01-20
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
import time
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


class TripleModelEnhancer:
    """三模型高质量增强处理器"""

    def __init__(self):
        """初始化处理器"""
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.input_dir = Path("/Users/xujian/语料/专利-json")
        self.output_dir = Path("/Users/xujian/语料/专利-json-enhanced")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 模型实例
        self.bge_m3_embedder = None
        self.bert_ner_extractor = None
        self.qwen_generator = None

        # 统计信息
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'total_time': 0,
            'bge_m3_time': 0,
            'bert_ner_time': 0,
            'qwen_time': 0
        }

        logger.info("=" * 80)
        logger.info("🚀 三模型高质量增强处理器初始化")
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
            logger.info("   向量维度: 1024")
            logger.info(f"   设备: {self.bge_m3_embedder.device}")
            logger.info(f"   MPS优化: {'是' if self.bge_m3_embedder.device == 'mps' else '否'}")

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
                model_path=None,  # 使用默认路径
                device='auto'  # 自动检测MPS > CUDA > CPU
            )

            # 初始化
            await self.bert_ner_extractor.initialize()

            logger.info("✅ BERT-NER模型初始化成功")
            logger.info(f"   实体类型: {', '.join(self.bert_ner_extractor.entity_types.values())}")
            logger.info(f"   设备: {self.bert_ner_extractor.device}")

            return True

        except Exception as e:
            logger.error(f"❌ BERT-NER初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def initialize_qwen(self) -> bool:
        """初始化Qwen 2.5模型（文本增强）"""
        logger.info("=" * 80)
        logger.info("🧠 初始化Qwen 2.5模型（深度语义理解）")
        logger.info("=" * 80)

        try:
            # 使用GGUF版本的Qwen 2.5（更轻量，适合本地运行）
            from llama_cpp import Llama

            # 模型路径
            model_path = self.base_dir / "models/converted/Qwen/Qwen2___5-7B-Instruct-GGUF"

            if not model_path.exists():
                logger.warning(f"⚠️ Qwen模型路径不存在: {model_path}")
                logger.info("💡 将跳过Qwen文本增强")
                return False

            # 寻找GGUF文件
            gguf_files = list(model_path.glob("*.gguf"))
            if not gguf_files:
                logger.warning("⚠️ 没有找到GGUF模型文件")
                return False

            # 使用最小的GGUF文件
            model_file = sorted(gguf_files, key=lambda x: x.stat().st_size)[0]

            logger.info(f"🔄 加载Qwen 2.5模型: {model_file.name}")

            # 创建LLaMA实例
            self.qwen_generator = Llama(
                model_path=str(model_file),
                n_ctx=4096,  # 上下文长度
                n_threads=8,  # 线程数
                n_gpu_layers=-1,  # 使用GPU加速（如果可用）
                verbose=False
            )

            logger.info("✅ Qwen 2.5模型初始化成功")
            logger.info("   上下文长度: 4096")
            logger.info(f"   模型文件: {model_file.name}")

            return True

        except Exception as e:
            logger.error(f"❌ Qwen 2.5初始化失败: {e}")
            logger.info("💡 将跳过Qwen文本增强")
            return False

    async def enhance_with_bge_m3(
        self,
        text: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """使用BGE-M3生成高质量向量"""
        start_time = time.time()

        try:
            # 生成向量
            embedding = await self.bge_m3_embedder.embed_text(text)

            elapsed_time = time.time() - start_time
            self.stats['bge_m3_time'] += elapsed_time

            return {
                'embedding': embedding,
                'embedding_dimension': len(embedding),
                'embedding_model': 'bge-m3',
                'embedding_device': self.bge_m3_embedder.device,
                'generation_time': elapsed_time,
                'embedding_quality': 'high'  # 1024维高质量向量
            }

        except Exception as e:
            logger.error(f"❌ BGE-M3向量化失败: {e}")
            return {
                'embedding': None,
                'error': str(e)
            }

    async def enhance_with_bert_ner(
        self,
        text: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """使用BERT-NER增强实体识别"""
        start_time = time.time()

        try:
            # 抽取实体
            entities = await self.bert_ner_extractor.extract_entities(text)

            # 抽取关系
            relations = await self.bert_ner_extractor.extract_relations(text, entities)

            elapsed_time = time.time() - start_time
            self.stats['bert_ner_time'] += elapsed_time

            return {
                'entities': entities,
                'relations': relations,
                'entity_count': len(entities),
                'relation_count': len(relations),
                'extraction_model': 'bert-ner',
                'extraction_device': self.bert_ner_extractor.device,
                'generation_time': elapsed_time
            }

        except Exception as e:
            logger.error(f"❌ BERT-NER实体抽取失败: {e}")
            return {
                'entities': [],
                'relations': [],
                'error': str(e)
            }

    async def enhance_with_qwen(
        self,
        text: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """使用Qwen 2.5进行深度语义理解"""
        if self.qwen_generator is None:
            return {'skipped': True, 'reason': 'Qwen模型未初始化'}

        start_time = time.time()

        try:
            # 构建提示词
            section_id = metadata.get('section_id', '')
            title = metadata.get('title', '')

            prompt = f"""你是一个专利规则专家。请对以下专利审查指南内容进行深度分析和增强。

章节ID: {section_id}
标题: {title}

原文内容:
{text}

请提供以下增强内容（JSON格式）:
{{
    "summary": "简明扼要的内容总结（3-5句话）",
    "key_concepts": ["核心概念1", "核心概念2", ...],
    "practical_guidance": "实际应用指导",
    "related_rules": ["相关规则1", "相关规则2", ...],
    "risk_points": ["风险点1", "风险点2", ...]
}}

请以JSON格式输出，不要包含其他内容:"""

            # 生成响应
            response = self.qwen_generator(
                prompt,
                max_tokens=1024,
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
                    'summary': response_text[:200],
                    'key_concepts': [],
                    'practical_guidance': response_text,
                    'related_rules': [],
                    'risk_points': []
                }

            elapsed_time = time.time() - start_time
            self.stats['qwen_time'] += elapsed_time

            return {
                'enhanced_content': enhanced_content,
                'enhancement_model': 'qwen-2.5',
                'generation_time': elapsed_time
            }

        except Exception as e:
            logger.error(f"❌ Qwen文本增强失败: {e}")
            return {
                'enhanced_content': None,
                'error': str(e)
            }

    async def process_json_file(self, json_file: Path) -> dict[str, Any | None]:
        """处理单个JSON文件"""
        try:
            # 读取原始JSON
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f)

            # 提取文本和元数据
            section_id = data.get('section_id', json_file.stem)
            hierarchy = data.get('hierarchy', {})
            content = data.get('content', {})
            summaries = data.get('summaries', {})

            # 获取主要文本
            text = content.get('raw_text', '')
            if not text:
                text = content.get('enhanced_text', '')

            if not text:
                logger.warning(f"⚠️ 文件没有文本内容: {json_file.name}")
                return None

            # 准备元数据
            metadata = {
                'section_id': section_id,
                'hierarchy': hierarchy,
                'title': content.get('title', ''),
                'file_name': json_file.name
            }

            # 并行执行三个模型的增强
            logger.info(f"🔄 处理文件: {json_file.name}")
            logger.info(f"   文本长度: {len(text)} 字符")

            bge_m3_result, bert_ner_result, qwen_result = await asyncio.gather(
                self.enhance_with_bge_m3(text, metadata),
                self.enhance_with_bert_ner(text, metadata),
                self.enhance_with_qwen(text, metadata),
                return_exceptions=True
            )

            # 处理异常
            if isinstance(bge_m3_result, Exception):
                logger.error(f"❌ BGE-M3处理异常: {bge_m3_result}")
                bge_m3_result = {'embedding': None, 'error': str(bge_m3_result)}

            if isinstance(bert_ner_result, Exception):
                logger.error(f"❌ BERT-NER处理异常: {bert_ner_result}")
                bert_ner_result = {'entities': [], 'error': str(bert_ner_result)}

            if isinstance(qwen_result, Exception):
                logger.error(f"❌ Qwen处理异常: {qwen_result}")
                qwen_result = {'enhanced_content': None, 'error': str(qwen_result)}

            # 构建增强后的数据
            enhanced_data = {
                # 保留原始数据
                'original_data': data,

                # BGE-M3增强
                'bge_m3_embedding': bge_m3_result,

                # BERT-NER增强
                'bert_ner_entities': bert_ner_result,

                # Qwen增强
                'qwen_enhancement': qwen_result,

                # 元数据
                'enhancement_metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'original_file': str(json_file),
                    'section_id': section_id,
                    'models_used': [
                        'bge-m3' if bge_m3_result.get('embedding') else None,
                        'bert-ner' if bert_ner_result.get('entities') is not None else None,
                        'qwen-2.5' if qwen_result.get('enhanced_content') else None
                    ],
                    'processing_stats': {
                        'bge_m3_time': bge_m3_result.get('generation_time', 0),
                        'bert_ner_time': bert_ner_result.get('generation_time', 0),
                        'qwen_time': qwen_result.get('generation_time', 0),
                        'total_time': (
                            bge_m3_result.get('generation_time', 0) +
                            bert_ner_result.get('generation_time', 0) +
                            qwen_result.get('generation_time', 0)
                        )
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
        self.stats['total_files'] = len(json_files)

        logger.info(f"📦 发现 {len(json_files)} 个JSON文件")

        # 批量处理
        batch_size = 10
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

                    self.stats['processed_files'] += 1
                    logger.info(f"✅ 已保存: {output_file.name}")
                else:
                    self.stats['failed_files'] += 1

            # 显示进度
            progress = (i + len(batch)) / len(json_files) * 100
            logger.info(f"📈 进度: {progress:.1f}% ({self.stats['processed_files']}/{len(json_files)})")

    async def run_full_pipeline(self):
        """运行完整管道"""
        logger.info("=" * 80)
        logger.info("🚀 启动三模型高质量增强管道")
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
            logger.info("\n📋 步骤 2/5: 处理guideline目录")
            await self.process_directory("guideline")

            logger.info("\n📋 步骤 3/5: 处理core目录")
            await self.process_directory("core")

            logger.info("\n📋 步骤 4/5: 处理others目录")
            await self.process_directory("others")

            # 3. 生成报告
            logger.info("\n📋 步骤 5/5: 生成处理报告")
            self.stats['total_time'] = time.time() - total_start_time

            report = {
                'completed_at': datetime.now().isoformat(),
                'statistics': self.stats,
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
                'performance_metrics': {
                    'total_files': self.stats['total_files'],
                    'processed_files': self.stats['processed_files'],
                    'failed_files': self.stats['failed_files'],
                    'success_rate': f"{(self.stats['processed_files'] / self.stats['total_files'] * 100):.2f}%" if self.stats['total_files'] > 0 else "N/A",
                    'total_time': f"{self.stats['total_time']:.2f}秒",
                    'avg_time_per_file': f"{(self.stats['total_time'] / self.stats['processed_files']):.2f}秒" if self.stats['processed_files'] > 0 else "N/A",
                    'bge_m3_time': f"{self.stats['bge_m3_time']:.2f}秒",
                    'bert_ner_time': f"{self.stats['bert_ner_time']:.2f}秒",
                    'qwen_time': f"{self.stats['qwen_time']:.2f}秒"
                }
            }

            # 保存报告
            report_file = self.output_dir / f"enhancement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info("=" * 80)
            logger.info("🎉 三模型高质量增强完成！")
            logger.info("=" * 80)
            logger.info(f"📊 处理文件: {self.stats['processed_files']}/{self.stats['total_files']}")
            logger.info(f"⏱️ 总耗时: {self.stats['total_time']:.2f}秒")
            logger.info(f"📄 报告: {report_file}")
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
