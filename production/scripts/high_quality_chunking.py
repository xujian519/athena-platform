#!/usr/bin/env python3
"""
高质量法律文档分块器
High-Quality Legal Document Chunker

实现递归Markdown分块 + 语义优化，保留法律结构完整性

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """文档块"""
    chunk_id: str
    content: str
    metadata: dict
    tokens: int
    overlap_tokens: int
    structural_info: dict

class HighQualityChunker:
    """高质量文档分块器"""

    def __init__(self):
        # 分块配置
        self.chunk_size = 800  # tokens
        self.overlap_ratio = 0.25  # 25%重叠
        self.min_chunk_size = 100  # 最小块大小

        # Markdown结构分隔符（优先级从高到低）
        self.markdown_separators = [
            ("# ", "H1"),
            ("## ", "H2"),
            ("### ", "H3"),
            ("#### ", "H4"),
            ("##### ", "H5"),
            ("###### ", "H6"),
            ("第[一二三四五六七八九十百千万\d]+条", "ARTICLE"),
            ("第[一二三四五六七八九十百千万\d]+节", "SECTION"),
            ("第[一二三四五六七八九十百千万\d]+章", "CHAPTER"),
            ("第[一二三四五六七八九十百千万\d]+编", "PART"),
            ("\n\n", "PARAGRAPH")
        ]

        # 法律专用模式
        self.legal_patterns = {
            "article": r'第([一二三四五六七八九十百千万\d]+)条[：:\s]*([^\n]*)',
            "law_reference": r'《([^》]+(?:法|条例|规定|办法|细则|解释))》',
            "date": r'(\d{4}年\d{1,2}月\d{1,2}日)',
            "institution": r'(国务院|全国人民代表大会|最高人民法院|最高人民检察院)'
        }

    def estimate_tokens(self, text: str) -> int:
        """估算token数量（中文按1.5字符≈1token估算）"""
        # 英文按单词，中文按字符
        english_words = len(re.findall(r'[a-z_a-Z]+', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return int(english_words + chinese_chars / 1.5)

    def clean_text(self, text: str) -> str:
        """清洗文本"""
        # 移除页眉页脚
        text = re.sub(r'^.*?第.*?页.*?$', '', text, flags=re.MULTILINE)

        # 标准化空白
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行合并
        text = re.sub(r' {2,}', ' ', text)  # 多个空格合并

        # 移除Markdown元数据（如<!-- -->）
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

        return text.strip()

    def extract_structural_info(self, text: str, chunk_start: int) -> dict:
        """提取结构信息"""
        info = {
            "level": "unknown",
            "title": "",
            "article_number": "",
            "law_name": "",
            "section_info": ""
        }

        # 检查法律条款
        article_match = re.search(self.legal_patterns["article"], text[:50])
        if article_match:
            info["article_number"] = article_match.group(1)
            info["title"] = article_match.group(2).strip()
            info["level"] = "article"

        # 检查Markdown标题
        for _i, (sep, level) in enumerate(self.markdown_separators[:7]):  # 只检查标题级别
            if sep in text[:50]:
                title_match = re.search(f'{re.escape(sep)}([^\n]+)', text)
                if title_match:
                    info["title"] = title_match.group(1).strip()
                    info["level"] = level
                    break

        return info

    def create_chunk(self, content: str, chunk_start: int, metadata: dict) -> DocumentChunk:
        """创建文档块"""
        chunk_id = str(uuid.uuid4())
        tokens = self.estimate_tokens(content)

        # 提取结构信息
        structural_info = self.extract_structural_info(content, chunk_start)

        # 计算重叠token数（如果有前一个块）
        overlap_tokens = 0
        if metadata.get("previous_chunk_content"):
            # 找出重叠部分
            overlap_length = min(int(self.chunk_size * self.overlap_ratio), len(content) // 2)
            overlap_content = content[:overlap_length]
            overlap_tokens = self.estimate_tokens(overlap_content)

        return DocumentChunk(
            chunk_id=chunk_id,
            content=content,
            metadata={
                **metadata,
                "structural_info": structural_info,
                "word_count": len(content),
                "character_count": len(content.encode('utf-8')),
                "created_at": datetime.now().isoformat()
            },
            tokens=tokens,
            overlap_tokens=overlap_tokens,
            structural_info=structural_info
        )

    def split_by_markdown_structure(self, text: str, metadata: dict) -> list[DocumentChunk]:
        """按Markdown结构分块"""
        chunks = []
        lines = text.split('\n')
        current_chunk_lines = []
        current_tokens = 0
        chunk_start = 0

        for i, line in enumerate(lines):
            line_tokens = self.estimate_tokens(line)

            # 检查是否遇到分隔符
            separator_found = False
            for sep, _level in self.markdown_separators:
                if re.match(f'^{re.escape(sep)}', line):
                    separator_found = True
                    break

            # 如果当前块非空且遇到分隔符，或者块已达到最大大小，则保存当前块
            if (current_chunk_lines and separator_found) or \
               (current_tokens >= self.chunk_size and line.strip()):

                if current_chunk_lines:
                    chunk_content = '\n'.join(current_chunk_lines)
                    chunk_start = sum(len(l) + 1 for l in lines[:i - len(current_chunk_lines)])

                    # 添加前一个块的内容用于计算重叠
                    if chunks:
                        metadata["previous_chunk_content"] = chunks[-1].content

                    chunk = self.create_chunk(chunk_content, chunk_start, metadata)
                    chunks.append(chunk)

                    # 重置
                    current_chunk_lines = [line]
                    current_tokens = line_tokens
                else:
                    current_chunk_lines.append(line)
                    current_tokens += line_tokens
            else:
                current_chunk_lines.append(line)
                current_tokens += line_tokens

        # 处理最后一个块
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            if chunks:
                metadata["previous_chunk_content"] = chunks[-1].content

            chunk_start = sum(len(l) + 1 for l in lines[:len(lines) - len(current_chunk_lines)])
            chunk = self.create_chunk(chunk_content, chunk_start, metadata)
            chunks.append(chunk)

        # 后处理：检查块大小，过小的块需要合并
        chunks = self.merge_small_chunks(chunks)

        return chunks

    def merge_small_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """合并过小的块"""
        if not chunks:
            return chunks

        merged_chunks = [chunks[0]]

        for chunk in chunks[1:]:
            last_chunk = merged_chunks[-1]

            # 如果最后一个块太小，合并
            if (last_chunk.tokens < self.min_chunk_size and
                last_chunk.tokens + chunk.tokens <= self.chunk_size * 1.5):

                # 合并内容
                combined_content = last_chunk.content + '\n\n' + chunk.content

                # 创建新块
                new_chunk = self.create_chunk(
                    combined_content,
                    0,  # 重新计算位置
                    chunk.metadata
                )

                # 保留重叠信息
                new_chunk.overlap_tokens = chunk.overlap_tokens

                # 替换最后一个块
                merged_chunks[-1] = new_chunk
            else:
                merged_chunks.append(chunk)

        return merged_chunks

    def semantic_chunk_optimization(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """语义块优化（简化版，实际应使用向量模型）"""
        # 这里简化处理，实际应该：
        # 1. 计算每个块的向量
        # 2. 计算相邻块的相似度
        # 3. 如果相似度高且都较小，合并
        # 4. 如果块太大且包含多个主题，分割

        optimized_chunks = chunks

        logger.info(f"语义优化: {len(chunks)} -> {len(optimized_chunks)} 块")

        return optimized_chunks

    def add_legal_metadata(self, chunks: list[DocumentChunk], file_path: Path) -> list[DocumentChunk]:
        """添加法律专属元数据"""
        file_name = file_path.name

        # 从文件名提取信息
        metadata = {
            "source_file": str(file_path),
            "file_name": file_name,
            "file_hash": short_hash(file_name.encode()),
            "document_type": self.identify_document_type(file_name),
            "effective_date": self.extract_date_from_filename(file_name)
        }

        # 为每个块添加文件级元数据
        enhanced_chunks = []
        for chunk in chunks:
            chunk.metadata.update(metadata)

            # 添加块特定的法律信息
            legal_info = self.extract_legal_info_from_chunk(chunk.content)
            chunk.metadata.update(legal_info)

            enhanced_chunks.append(chunk)

        return enhanced_chunks

    def identify_document_type(self, filename: str) -> str:
        """识别文档类型"""
        if "宪法" in filename:
            return "宪法"
        elif "法" in filename and "条例" not in filename:
            return "法律"
        elif "条例" in filename:
            return "行政法规"
        elif "规定" in filename or "办法" in filename:
            return "部门规章"
        elif "解释" in filename:
            return "司法解释"
        else:
            return "其他"

    def extract_date_from_filename(self, filename: str) -> str | None:
        """从文件名提取日期"""
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        return date_match.group(1) if date_match else None

    def extract_legal_info_from_chunk(self, content: str) -> dict:
        """从块内容提取法律信息"""
        info = {
            "references": [],
            "subjects": [],
            "obligations": [],
            "rights": [],
            "penalties": []
        }

        # 提取法律引用
        refs = re.findall(r'《([^》]+(?:法|条例|规定|办法|细则|解释))》', content)
        info["references"] = refs

        # 提取主体（简化版）
        institutions = re.findall(self.legal_patterns["institution"], content)
        info["subjects"] = institutions

        # 提取义务条款
        if any(word in content for word in ["应当", "必须", "有义务"]):
            info["obligations"].append("义务条款")

        # 提取权利条款
        if any(word in content for word in ["有权", "可以", "享有"]):
            info["rights"].append("权利条款")

        # 提取处罚条款
        if any(word in content for word in ["处罚", "罚款", "没收"]):
            info["penalties"].append("处罚条款")

        return info

    def process_document(self, file_path: Path) -> list[DocumentChunk]:
        """处理单个文档"""
        logger.info(f"\n📄 处理文档: {file_path.name}")

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return []

        # 清洗文本
        content = self.clean_text(content)

        # 基础元数据
        base_metadata = {
            "chunking_strategy": "markdown_recursive",
            "chunk_size": self.chunk_size,
            "overlap_ratio": self.overlap_ratio
        }

        # 按Markdown结构分块
        chunks = self.split_by_markdown_structure(content, base_metadata)

        # 语义优化
        chunks = self.semantic_chunk_optimization(chunks)

        # 添加法律元数据
        chunks = self.add_legal_metadata(chunks, file_path)

        logger.info(f"  ✅ 生成 {len(chunks)} 个块")

        return chunks

    def process_batch(self, data_dir: Path, limit: int = 100) -> dict:
        """批量处理文档"""
        logger.info(f"\n🚀 批量处理法律文档（限制: {limit}个）")

        md_files = [f for f in data_dir.rglob("*.md") if not f.name.startswith("_")]
        logger.info(f"找到 {len(md_files)} 个文件")

        all_chunks = []
        file_stats = {}

        for i, file_path in enumerate(md_files[:limit]):
            logger.info(f"\n进度: {i+1}/{min(limit, len(md_files))}")

            chunks = self.process_document(file_path)
            all_chunks.extend(chunks)

            file_stats[file_path.name] = {
                "chunks": len(chunks),
                "total_tokens": sum(c.tokens for c in chunks),
                "avg_chunk_size": sum(c.tokens for c in chunks) / len(chunks) if chunks else 0
            }

        # 统计信息
        total_tokens = sum(c.tokens for c in all_chunks)
        avg_chunk_size = total_tokens / len(all_chunks) if all_chunks else 0

        stats = {
            "timestamp": datetime.now().isoformat(),
            "processed_files": len(file_stats),
            "total_chunks": len(all_chunks),
            "total_tokens": total_tokens,
            "avg_chunk_size": avg_chunk_size,
            "chunking_config": {
                "target_chunk_size": self.chunk_size,
                "overlap_ratio": self.overlap_ratio,
                "min_chunk_size": self.min_chunk_size
            },
            "file_statistics": file_stats,
            "chunk_types": self.analyze_chunk_types(all_chunks)
        }

        logger.info("\n📊 处理统计:")
        logger.info(f"  处理文件: {stats['processed_files']}")
        logger.info(f"  总块数: {stats['total_chunks']}")
        logger.info(f"  总tokens: {stats['total_tokens']:,}")
        logger.info(f"  平均块大小: {stats['avg_chunk_size']:.1f}")

        return {
            "chunks": all_chunks,
            "statistics": stats
        }

    def analyze_chunk_types(self, chunks: list[DocumentChunk]) -> dict:
        """分析块类型分布"""
        type_stats = {}

        for chunk in chunks:
            chunk_type = chunk.structural_info.get("level", "unknown")
            if chunk_type not in type_stats:
                type_stats[chunk_type] = {
                    "count": 0,
                    "total_tokens": 0,
                    "avg_tokens": 0
                }

            type_stats[chunk_type]["count"] += 1
            type_stats[chunk_type]["total_tokens"] += chunk.tokens

        # 计算平均值
        for chunk_type, stats in type_stats.items():
            if stats["count"] > 0:
                stats["avg_tokens"] = stats["total_tokens"] / stats["count"]

        return type_stats

    def save_chunks(self, chunks: list[DocumentChunk], stats: dict) -> None:
        """保存分块结果"""
        # 转换为可序列化格式
        serializable_chunks = []
        for chunk in chunks:
            serializable_chunks.append({
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "tokens": chunk.tokens,
                "overlap_tokens": chunk.overlap_tokens,
                "structural_info": chunk.structural_info
            })

        # 保存分块数据
        chunks_file = Path("/Users/xujian/Athena工作平台/production/data/processed") / \
                       f"legal_chunks_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        chunks_file.parent.mkdir(parents=True, exist_ok=True)

        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                "chunks": serializable_chunks,
                "statistics": stats
            }, f, ensure_ascii=False, indent=2)

        # 保存统计报告
        stats_file = Path("/Users/xujian/Athena工作平台/production/data/metadata") / \
                     f"chunking_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        stats_file.parent.mkdir(parents=True, exist_ok=True)

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info("\n💾 结果已保存:")
        logger.info(f"  分块数据: {chunks_file}")
        logger.info(f"  统计报告: {stats_file}")

def main() -> None:
    """主函数"""
    print("="*100)
    print("📚 高质量法律文档分块器 📚")
    print("="*100)

    chunker = HighQualityChunker()

    # 处理文档
    data_dir = Path("/Users/xujian/Athena工作平台/dev/tools/Laws-1.0.0")
    result = chunker.process_batch(data_dir, limit=200)

    # 保存结果
    chunker.save_chunks(result["chunks"], result["statistics"])

    # 显示示例
    print("\n📋 分块示例:")
    for i, chunk in enumerate(result["chunks"][:3]):
        print(f"\n块 {i+1} ({chunk.structural_info.get('level', 'unknown')}):")
        print(f"  ID: {chunk.chunk_id[:8]}...")
        print(f"  Tokens: {chunk.tokens}")
        print(f"  内容预览: {chunk.content[:100]}...")
        print(f"  法律引用: {chunk.metadata.get('references', [])}")

if __name__ == "__main__":
    main()
