#!/usr/bin/env python3
"""
商标审查指南PDF大文件切割处理器
将84MB的商标审查审理指南.pdf切割成20份分别处理

作者: 小诺·双鱼座（Athena平台AI智能体）
创建时间: 2025-12-26
"""

from __future__ import annotations
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class TrademarkGuidelineSplitter:
    """商标审查指南切割处理器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.source_file = Path("/Volumes/AthenaData/语料/商标相关法律法规/商标审查审理指南.pdf")
        self.output_dir = self.base_dir / "production/data/trademark_rules/splits"

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("商标审查指南切割处理器初始化完成")
        logger.info(f"源文件: {self.source_file}")
        logger.info(f"输出目录: {self.output_dir}")

    def get_file_size(self, file_path: Path) -> dict[str, Any]:
        """获取文件大小信息"""
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        return {
            "path": str(file_path),
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "size_gb": size_mb / 1024
        }

    def split_by_pages(self, num_parts: int = 20) -> list[dict[str, Any]]:
        """按页数切割PDF"""
        logger.info("=" * 60)
        logger.info(f"📄 开始切割PDF文件为 {num_parts} 份")
        logger.info("=" * 60)

        # 检查源文件
        if not self.source_file.exists():
            logger.error(f"❌ 源文件不存在: {self.source_file}")
            return []

        # 显示文件信息
        file_info = self.get_file_size(self.source_file)
        logger.info("📊 文件信息:")
        logger.info(f"   大小: {file_info['size_mb']:.2f} MB ({file_info['size_gb']:.2f} GB)")

        # 打开PDF
        try:
            pdf_document = fitz.open(str(self.source_file))
            total_pages = pdf_document.page_count
            pdf_document.close()

            logger.info(f"   总页数: {total_pages}")

        except Exception as e:
            logger.error(f"❌ 无法打开PDF文件: {e}")
            return []

        # 计算每份的页数
        pages_per_part = total_pages // num_parts
        remainder = total_pages % num_parts

        logger.info("📊 切分计划:")
        logger.info(f"   切分份数: {num_parts}")
        logger.info(f"   每份页数: {pages_per_part}")
        logger.info(f"   最后一份: {pages_per_part + remainder}页")

        # 开始切割
        split_files = []

        try:
            pdf_document = fitz.open(str(self.source_file))

            for i in range(num_parts):
                # 计算当前份的页数
                if i == num_parts - 1:
                    # 最后一份包含所有剩余页数
                    current_pages = pages_per_part + remainder
                else:
                    current_pages = pages_per_part

                # 计算页码范围
                start_page = i * pages_per_part
                end_page = start_page + current_pages

                logger.info(f"📄 处理第 {i+1}/{num_parts} 份: 第{start_page+1}-{end_page}页")

                # 创建新PDF
                new_pdf = fitz.open()

                # 复制页面
                for page_num in range(start_page, end_page):
                    page = pdf_document[page_num]
                    new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)

                # 保存切割后的文件
                output_filename = f"商标审查审理指南_part{i+1:02d}_of_{num_parts:02d}.pdf"
                output_path = self.output_dir / output_filename

                new_pdf.save(str(output_path))
                new_pdf.close()

                # 记录文件信息
                split_info = {
                    "part_number": i + 1,
                    "filename": output_filename,
                    "output_path": str(output_path),
                    "start_page": start_page + 1,
                    "end_page": end_page,
                    "page_count": current_pages,
                    "file_size": self.get_file_size(output_path)
                }

                split_files.append(split_info)

                logger.info(f"   ✅ 已保存: {output_filename}")
                logger.info(f"      页数: {current_pages}")
                logger.info(f"      大小: {split_info['file_size']['size_mb']:.2f} MB")

            pdf_document.close()

            logger.info("=" * 60)
            logger.info(f"✅ 切割完成！共生成 {len(split_files)} 个文件")
            logger.info(f"📁 输出目录: {self.output_dir}")

            return split_files

        except Exception as e:
            logger.error(f"❌ 切割过程出错: {e}")
            return []

    def generate_batch_script(self, split_files: list[dict[str, Any]]) -> str:
        """生成批量处理脚本"""
        logger.info("📝 生成批量处理脚本...")

        script_path = self.output_dir / "process_all_splits.sh"

        script_content = f"""#!/bin/bash
# 商标审查指南切割文件批量处理脚本
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 生成者: 小诺·双鱼座

BASE_DIR="/Users/xujian/Athena工作平台"
SPLIT_DIR="$BASE_DIR/production/data/trademark_rules/splits"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/trademark_split_process_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

echo "========================================"
echo "商标审查指南切割文件批量处理"
echo "========================================"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 处理每个切割文件
count=0
total={len(split_files)}

for split_file in "$SPLIT_DIR"/*.pdf; do
    if [ -f "$split_file" ]; then
        count=$((count + 1))
        filename=$(basename "$split_file")
        echo "[$count/$total] 处理文件: $filename"
        echo "========================================"

        # 调用full_laws_processor处理单个文件
        # 注意: 需要修改full_laws_processor支持单文件模式
        python3 "$BASE_DIR/production/scripts/patent_guideline/full_laws_processor.py" \\
            --single-file "$split_file" \\
            --collection "trademark_laws" \\
            --space "trademark_rules" \\
            >> "$LOG_FILE" 2>&1

        if [ $? -eq 0 ]; then
            echo "   ✅ 处理成功: $filename"
        else
            echo "   ❌ 处理失败: $filename"
            echo "   查看日志: $LOG_FILE"
        fi
        echo ""
    fi
done

echo "========================================"
echo "处理完成！"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "日志文件: $LOG_FILE"
echo "========================================"
"""

        # 保存脚本
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 设置执行权限
        os.chmod(script_path, 0o755)

        logger.info(f"✅ 批量处理脚本已生成: {script_path}")

        return str(script_path)

    def generate_manifest(self, split_files: list[dict[str, Any]]) -> str:
        """生成清单文件"""
        logger.info("📋 生成切割清单...")

        manifest_path = self.output_dir / "MANIFEST.md"

        manifest_content = f"""# 商标审查指南切割清单

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**生成者**: 小诺·双鱼座 (Athena平台)
**源文件**: {self.source_file.name}
**切割份数**: {len(split_files)}

---

## 📊 文件信息

- **文件名**: {self.source_file.name}
- **文件大小**: {self.get_file_size(self.source_file)['size_mb']:.2f} MB
- **切割策略**: 按页数均分
- **切割份数**: {len(split_files)}

---

## 📄 切割文件列表

| 序号 | 文件名 | 页码范围 | 页数 | 文件大小 |
|-----|--------|---------|-----|---------|
"""

        for split_info in split_files:
            manifest_content += f"| {split_info['part_number']} | {split_info['filename']} | 第{split_info['start_page']}-{split_info['end_page']}页 | {split_info['page_count']} | {split_info['file_size']['size_mb']:.2f} MB |\n"

        manifest_content += f"""
---

## 🚀 使用方法

### 方式1: 单独处理某个文件

```bash
python3 /Users/xujian/Athena工作平台/production/scripts/patent_guideline/full_laws_processor.py \\
    --single-file {self.output_dir}/商标审查审理指南_part01_of_20.pdf
```

### 方式2: 批量处理所有文件

```bash
cd {self.output_dir}
bash process_all_splits.sh
```

### 方式3: 并发处理（高级）

```bash
# 使用GNU parallel并发处理
ls {self.output_dir}/*.pdf | parallel -j 4 \\
    'python3 /Users/xujian/Athena工作平台/production/scripts/patent_guideline/full_laws_processor.py --single-file {{}}'
```

---

## 📊 预期结果

处理完成后，您将拥有:

- **Qdrant集合**: trademark_laws
  - 向量数量: 预计10,000-20,000个
  - 向量维度: 1024维 (BGE-large-zh-v1.5)
  - 相似度检索: 支持

- **NebulaGraph空间**: trademark_rules
  - 节点数量: 预计5,000-10,000个
  - 关系数量: 预计3,000-6,000条
  - 节点类型: 6-8种
  - 关系类型: 6-8种

---

## ⚠️ 注意事项

1. **内存管理**
   - 每个文件约4-5MB，可以单独处理
   - 建议逐个处理，避免并发过多导致内存溢出

2. **时间估算**
   - 单个文件处理时间: 约10-20分钟
   - 总处理时间: 约3-6小时
   - 建议使用批量脚本夜间处理

3. **错误处理**
   - 如果某个文件处理失败，可以单独重试
   - 查看日志文件定位问题

4. **质量验证**
   - 处理完成后随机抽查验证
   - 检查向量检索质量
   - 检查图谱查询质量

---

**清单版本**: v1.0
**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # 保存清单
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)

        logger.info(f"✅ 切割清单已生成: {manifest_path}")

        return str(manifest_path)

    def run(self, num_parts: int = 20) -> None:
        """执行切割流程"""
        logger.info("🚀 开始执行切割流程...")

        # 步骤1: 切割文件
        split_files = self.split_by_pages(num_parts)

        if not split_files:
            logger.error("❌ 切割失败，流程终止")
            return False

        # 步骤2: 生成批量处理脚本
        script_path = self.generate_batch_script(split_files)

        # 步骤3: 生成清单文件
        manifest_path = self.generate_manifest(split_files)

        # 显示总结
        logger.info("=" * 60)
        logger.info("✅ 切割流程全部完成！")
        logger.info(f"📁 输出目录: {self.output_dir}")
        logger.info(f"📄 切割文件: {len(split_files)}个")
        logger.info(f"📜 批量脚本: {script_path}")
        logger.info(f"📋 清单文件: {manifest_path}")
        logger.info("=" * 60)

        # 显示文件大小分布
        logger.info("📊 文件大小分布:")
        total_size = sum(f['file_size']['size_mb'] for f in split_files)
        avg_size = total_size / len(split_files)

        logger.info(f"   总大小: {total_size:.2f} MB")
        logger.info(f"   平均大小: {avg_size:.2f} MB")
        logger.info(f"   最小: {min(f['file_size']['size_mb'] for f in split_files):.2f} MB")
        logger.info(f"   最大: {max(f['file_size']['size_mb'] for f in split_files):.2f} MB")

        return True


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='商标审查指南PDF切割处理器')
    parser.add_argument(
        '--parts',
        type=int,
        default=20,
        help='切割份数（默认20）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行，不实际切割'
    )

    args = parser.parse_args()

    # 创建切割器
    splitter = TrademarkGuidelineSplitter()

    if args.dry_run:
        logger.info("🔍 试运行模式 - 将显示切割计划但不实际切割")

        # 只显示计划
        if splitter.source_file.exists():
            try:
                pdf_document = fitz.open(str(splitter.source_file))
                total_pages = pdf_document.page_count
                pdf_document.close()
            except Exception as e:
                logger.error(f"❌ 无法打开PDF文件: {e}")
                sys.exit(1)

            pages_per_part = total_pages // args.parts
            remainder = total_pages % args.parts

            print("\n📊 切割计划:")
            print(f"   源文件: {splitter.source_file.name}")
            print(f"   总页数: {total_pages}")
            print(f"   切分份数: {args.parts}")
            print(f"   每份页数: {pages_per_part}")
            print(f"   最后一份: {pages_per_part + remainder}页")
            print(f"\n输出目录: {splitter.output_dir}")
    else:
        # 实际执行切割
        success = splitter.run(args.parts)

        if success:
            print("\n💖 切割完成！您现在可以:")
            print(f"   1. 查看清单: cat {splitter.output_dir}/MANIFEST.md")
            print(f"   2. 运行批量处理: cd {splitter.output_dir} && bash process_all_splits.sh")
            print("   3. 或单独处理某个文件")
        else:
            print("\n❌ 切割失败，请检查日志")
            sys.exit(1)


if __name__ == "__main__":
    main()
