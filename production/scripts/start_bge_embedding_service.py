#!/usr/bin/env python3
"""
BGE嵌入服务启动脚本
用于启动和测试BGE Large ZH v1.5嵌入服务

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/bge_service_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class BGEServiceLauncher:
    """BGE服务启动器"""

    def __init__(self):
        self.service = None
        self.model_path = "/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5"
        self.fallback_model_path = "/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5"

    async def initialize(self):
        """初始化BGE服务"""
        from core.nlp.bge_embedding_service import BGEEmbeddingService

        # 检查模型路径
        if os.path.exists(self.model_path):
            model_path = self.model_path
            logger.info(f"✅ 使用转换后的模型: {model_path}")
        elif os.path.exists(self.fallback_model_path):
            model_path = self.fallback_model_path
            logger.info(f"✅ 使用备用模型路径: {model_path}")
        else:
            logger.warning("⚠️ 模型路径不存在，将使用HuggingFace自动下载")
            model_path = "BAAI/bge-large-zh-v1.5"

        # 配置服务
        config = {
            "model_path": model_path,
            "device": "cpu",  # macOS优化，使用CPU避免MPS问题
            "batch_size": 32,
            "max_length": 512,
            "normalize_embeddings": True,
            "cache_enabled": True,
            "preload": True
        }

        self.service = BGEEmbeddingService(config)
        await self.service.initialize()

        logger.info("🚀 BGE嵌入服务初始化完成")
        return self.service

    async def test_embedding(self, test_texts):
        """测试嵌入功能"""
        logger.info(f"🧪 测试嵌入功能，共{len(test_texts)}个文本...")

        results = []
        for i, text in enumerate(test_texts):
            try:
                result = await self.service.encode(text, task_type="test")
                results.append({
                    "index": i,
                    "text": text[:50] + "..." if len(text) > 50 else text,
                    "dimension": result.dimension,
                    "processing_time": result.processing_time,
                    "success": True
                })
                logger.info(f"✅ 测试 {i+1}/{len(test_texts)}: {result.dimension}维, 耗时{result.processing_time:.3f}秒")
            except Exception as e:
                logger.error(f"❌ 测试 {i+1}/{len(test_texts)} 失败: {e}")
                results.append({
                    "index": i,
                    "text": text[:50] + "..." if len(text) > 50 else text,
                    "error": str(e),
                    "success": False
                })

        return results

    async def generate_vectors_for_chunks(self, chunks_data_path):
        """为文本块生成向量"""
        logger.info(f"📊 开始处理文本块数据: {chunks_data_path}")

        # 读取文本块数据
        if not os.path.exists(chunks_data_path):
            logger.error(f"❌ 文本块数据文件不存在: {chunks_data_path}")
            return {"error": "数据文件不存在"}

        with open(chunks_data_path, encoding='utf-8') as f:
            data = json.load(f)

        chunks = data.get('chunks', [])
        logger.info(f"📦 找到 {len(chunks)} 个文本块")

        if len(chunks) == 0:
            logger.warning("⚠️ 没有找到需要处理的文本块")
            return {"processed": 0, "failed": 0, "vectors": []}

        # 批量生成向量
        batch_size = 32
        all_vectors = []
        processed_count = 0
        failed_count = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [chunk.get('text', '') for chunk in batch]

            try:
                # 批量编码
                result = await self.service.encode(texts, task_type="patent_guideline")

                # 保存向量结果
                for j, (chunk, embedding) in enumerate(zip(batch, result.embeddings, strict=False)):
                    all_vectors.append({
                        "chunk_id": chunk.get('chunk_id', f"{i+j}"),
                        "text": chunk.get('text', '')[:100],  # 只保存前100字符用于调试
                        "embedding_dim": len(embedding) if isinstance(embedding, list) else 1024,
                        "metadata": chunk.get('metadata', {})
                    })

                processed_count += len(batch)
                logger.info(f"✅ 进度: {processed_count}/{len(chunks)} ({processed_count/len(chunks)*100:.1f}%)")

            except Exception as e:
                logger.error(f"❌ 批次 {i//batch_size} 处理失败: {e}")
                failed_count += len(batch)

        logger.info(f"🎉 向量生成完成: {processed_count}成功, {failed_count}失败")

        # 保存结果
        output_path = f'/Users/xujian/Athena工作平台/production/data/patent_rules/vectors/bge_vectors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "total_chunks": len(chunks),
                "processed": processed_count,
                "failed": failed_count,
                "generated_at": datetime.now().isoformat(),
                "vectors": all_vectors[:10]  # 只保存前10个用于调试
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 向量结果已保存: {output_path}")

        return {
            "total_chunks": len(chunks),
            "processed": processed_count,
            "failed": failed_count,
            "output_path": output_path
        }

    def get_statistics(self) -> Any | None:
        """获取服务统计信息"""
        if self.service:
            return self.service.get_statistics()
        return {"error": "服务未初始化"}

    async def health_check(self):
        """健康检查"""
        if self.service:
            return await self.service.health_check()
        return {"status": "uninitialized"}


async def main():
    """主函数"""
    launcher = BGEServiceLauncher()

    try:
        # 1. 初始化服务
        logger.info("=" * 60)
        logger.info("🚀 启动BGE嵌入服务")
        logger.info("=" * 60)

        await launcher.initialize()

        # 2. 健康检查
        logger.info("\n📋 健康检查...")
        health = await launcher.health_check()
        logger.info(f"健康状态: {json.dumps(health, ensure_ascii=False, indent=2)}")

        # 3. 测试嵌入功能
        logger.info("\n🧪 测试嵌入功能...")
        test_texts = [
            "专利审查指南是专利审查的重要依据",
            "创造性是指发明专利同申请日以前已有的技术相比",
            "实用性是指该发明或者实用新型能够制造或者使用",
            "新颖性是指该发明或者实用新型不属于现有技术",
            "专利法规定授予专利权的发明和实用新型应当具备新颖性、创造性和实用性"
        ]
        test_results = await launcher.test_embedding(test_texts)

        # 4. 获取统计信息
        logger.info("\n📊 服务统计信息...")
        stats = launcher.get_statistics()
        logger.info(f"统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")

        # 5. 检查是否有待处理的文本块数据
        chunks_path = '/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents/processed_chunks.json'

        if os.path.exists(chunks_path):
            logger.info("\n📦 发现文本块数据，开始生成向量...")
            vector_results = await launcher.generate_vectors_for_chunks(chunks_path)
            logger.info(f"向量生成结果: {json.dumps(vector_results, ensure_ascii=False, indent=2)}")
        else:
            logger.info(f"\n⚠️ 未找到文本块数据文件: {chunks_path}")
            logger.info("💡 提示: 请先运行文档处理脚本生成文本块数据")

        logger.info("\n" + "=" * 60)
        logger.info("✅ BGE嵌入服务启动完成")
        logger.info("=" * 60)

        return launcher

    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs('/Users/xujian/Athena工作平台/logs', exist_ok=True)
    os.makedirs('/Users/xujian/Athena工作平台/production/data/patent_rules/vectors', exist_ok=True)

    # 启动服务
    launcher = asyncio.run(main())

    if launcher:
        print("\n✅ BGE嵌入服务已成功启动!")
        print(f"📊 统计信息: {json.dumps(launcher.get_statistics(), ensure_ascii=False, indent=2)}")
    else:
        print("\n❌ BGE嵌入服务启动失败")
        sys.exit(1)
