#!/usr/bin/env python3
from __future__ import annotations

"""
法律文档JSON导出工具
将PostgreSQL中的法律文档解析为结构化JSON并导出到文件系统
"""

import hashlib
import json

# 添加项目路径
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.append(str(Path(__file__).parent.parent))
from legal_kg.legal_text_parser import LegalTextParser

# ==================== 配置 ====================
# PostgreSQL配置
DB_CONFIG = {
    "host": "localhost",
    "port": 15432,
    "database": "phoenix_prod",
    "user": "phoenix_user",
    "password": "phoenix_secure_password_2024",
}

# 导出目录
EXPORT_DIR = Path("/Users/xujian/语料/laws-json")

# 按重要程度分类的子目录
CATEGORIES = {
    "high": EXPORT_DIR / "01_重要法律_条款项级",
    "medium": EXPORT_DIR / "02_普通法律_条文级",
    "normal": EXPORT_DIR / "03_地方法规_段落级",
}


class LegalDocumentExporter:
    """法律文档导出器"""

    def __init__(self):
        self.parser = LegalTextParser()
        self.stats = {
            "total": 0,
            "high": 0,
            "medium": 0,
            "normal": 0,
            "articles": 0,
            "paragraphs": 0,
            "items": 0,
        }

    def create_directories(self) -> Any:
        """创建导出目录结构"""
        print("📁 创建导出目录结构...")

        # 创建主目录和子目录
        for _category, path in CATEGORIES.items():
            path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {path}")

        print(f"✅ 目录结构创建完成: {EXPORT_DIR}\n")

    def fetch_documents(self) -> list[dict]:
        """从PostgreSQL获取法律文档"""
        print("📥 从PostgreSQL获取法律文档...")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 获取所有法律文档
            cursor.execute("""
                SELECT
                    id,
                    title,
                    category,
                    subcategory,
                    content,
                    file_path,
                    file_size,
                    created_at
                FROM legal_documents
                ORDER BY category, id
            """)

            rows = cursor.fetchall()

            cursor.close()
            conn.close()

            print(f"✅ 获取 {len(rows)} 个法律文档\n")
            return rows

        except Exception as e:
            print(f"❌ 数据库查询失败: {e}\n")
            return []

    def determine_importance(self, title: str, category: str) -> str:
        """判断法律重要程度"""
        # 地方法规直接归类为普通
        if category == "local_regulation":
            return "normal"

        # 使用parser判断
        importance = self.parser.determine_importance(title)
        return importance.value

    def parse_and_export_document(self, doc: dict) -> str | None:
        """解析并导出单个文档"""
        doc_id = doc["id"]
        title = doc["title"]
        category = doc["category"]
        content = doc["content"]

        # 确定重要程度
        importance = self.determine_importance(title, category)

        # 解析法律文本
        parsed = self.parser.parse_law_text(content=content, law_id=str(doc_id), title=title)

        # 添加元数据
        parsed["metadata"] = {
            "doc_id": doc_id,
            "title": title,
            "category": category,
            "subcategory": doc.get("subcategory"),
            "file_path": doc.get("file_path"),
            "file_size": doc.get("file_size"),
            "importance": importance,
            "exported_at": datetime.now().isoformat(),
            "total_articles": len(parsed.get("articles", [])),
            "total_paragraphs": len(parsed.get("paragraphs", [])),
            "total_items": len(parsed.get("items", [])),
        }

        # 生成文件名(使用哈希避免冲突)
        filename = self._generate_filename(doc_id, title, importance)
        filepath = CATEGORIES[importance] / filename

        # 保存为JSON
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)

            # 更新统计
            self.stats["total"] += 1
            self.stats[importance] += 1
            self.stats["articles"] += parsed.get("metadata", {}).get("total_articles", 0)
            self.stats["paragraphs"] += parsed.get("metadata", {}).get("total_paragraphs", 0)
            self.stats["items"] += parsed.get("metadata", {}).get("total_items", 0)

            return str(filepath)

        except Exception as e:
            print(f"❌ 导出失败 [{title}]: {e}")
            return None

    def _generate_filename(self, doc_id: int, title: str, importance: str) -> str:
        """生成文件名"""
        # 清理标题,移除不合法字符
        safe_title = title[:50].replace("/", "-").replace("\\", "-").replace(":", ":")
        safe_title = "".join(c for c in safe_title if c.isalnum() or c in " -_()()[][]《》")

        # 生成哈希后缀(避免重名)
        hash_suffix = hashlib.md5(f"{doc_id}_{title}".encode(), usedforsecurity=False).hexdigest()[:8]

        return f"{doc_id:05d}_{safe_title}_{hash_suffix}.json"

    def export_all_documents(self, documents: list[dict]) -> dict:
        """导出所有文档"""
        print(f"🔄 开始导出 {len(documents)} 个文档...\n")

        export_results = {"success": [], "failed": []}

        for i, doc in enumerate(documents, 1):
            title = doc["title"]

            # 进度提示
            if i % 100 == 0:
                print(f"⏳ 进度: {i}/{len(documents)}")

            # 解析并导出
            filepath = self.parse_and_export_document(doc)
            if filepath:
                export_results["success"].append(
                    {"id": doc["id"], "title": title, "filepath": filepath}
                )
            else:
                export_results["failed"].append({"id": doc["id"], "title": title})

        print("\n✅ 导出完成!")
        return export_results

    def generate_manifest(self) -> Any:
        """生成清单文件"""
        print("📋 生成清单文件...")

        manifest = {
            "export_time": datetime.now().isoformat(),
            "total_documents": self.stats["total"],
            "statistics": self.stats,
            "categories": {},
        }

        # 为每个分类生成清单
        for category, path in CATEGORIES.items():
            if path.exists():
                json_files = list(path.glob("*.json"))
                manifest["categories"][category] = {
                    "path": str(path),
                    "count": len(json_files),
                    "files": [f.name for f in sorted(json_files)],
                }

        # 保存总清单
        manifest_path = EXPORT_DIR / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        print(f"✅ 清单文件已保存: {manifest_path}\n")

        return manifest

    def print_statistics(self) -> Any:
        """打印统计信息"""
        print("=" * 70)
        print("📊 导出统计")
        print("=" * 70)
        print(f"\n总文档数: {self.stats['total']:,}")
        print(f"📁 重要法律(高): {self.stats['high']:,}")
        print(f"📁 普通法律(中): {self.stats['medium']:,}")
        print(f"📁 地方法规(普通): {self.stats['normal']:,}")
        print("\n📄 解析统计:")
        print(f"   总条文数: {self.stats['articles']:,}")
        print(f"   总段落数: {self.stats['paragraphs']:,}")
        print(f"   总项数: {self.stats['items']:,}")
        print()


# ==================== 主程序 ====================
def main() -> None:
    """主程序"""
    print("\n" + "=" * 70)
    print("📖 法律文档JSON导出工具")
    print("=" * 70 + "\n")

    # 初始化导出器
    exporter = LegalDocumentExporter()

    # 创建目录结构
    exporter.create_directories()

    # 从数据库获取文档
    documents = exporter.fetch_documents()

    if not documents:
        print("❌ 没有找到法律文档")
        return

    # 导出所有文档
    results = exporter.export_all_documents(documents)

    # 生成清单
    manifest = exporter.generate_manifest()

    # 打印统计
    exporter.print_statistics()

    # 保存导出结果
    result_path = EXPORT_DIR / f'export_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "manifest": manifest,
                "results": {
                    "success_count": len(results["success"]),
                    "failed_count": len(results["failed"]),
                    "failed_documents": results["failed"][:10],  # 只记录前10个失败的
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"✅ 导出结果已保存: {result_path}")
    print(f"📁 导出目录: {EXPORT_DIR}\n")


if __name__ == "__main__":
    main()
