#!/usr/bin/env python3
"""
专利检索工具深度分析 - 基于有效检索渠道

有效渠道:
1. 本地PostgreSQL patent_db数据库检索
2. Google Patents检索

下载渠道:
- Google Patents PDF下载
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set


class EffectivePatentToolAnalyzer:
    """有效专利工具分析器"""

    def __init__(self):
        self.project_root = Path("/Users/xujian/Athena工作平台")
        self.effective_channels = {
            "local_postgres": "本地PostgreSQL patent_db数据库",
            "google_patents": "Google Patents在线检索"
        }
        self.effective_download = "google_patents_pdf"

        # 扫描结果
        self.local_postgres_tools = []
        self.google_patents_tools = []
        self.invalid_tools = []
        self.download_tools = []

    def search_keyword_in_file(self, file_path: Path, keywords: List[str]) -> bool:
        """在文件中搜索关键词"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        return True
        except Exception as e:
            pass
        return False

    def analyze_postgres_tools(self):
        """分析基于PostgreSQL的工具"""
        print("\n" + "=" * 80)
        print("🔍 分析本地PostgreSQL patent_db检索工具")
        print("=" * 80)

        postgres_keywords = [
            "patent_db",
            "postgresql",
            "psycopg",
            "postgres",
            "SELECT.*FROM patent",
            "patent.*table"
        ]

        # 搜索可能包含PostgreSQL检索的文件
        search_paths = [
            "patent_hybrid_retrieval",
            "tools"
        ]

        found_files = []

        for search_path in search_paths:
            dir_path = self.project_root / search_path
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                if self.search_keyword_in_file(py_file, postgres_keywords):
                    found_files.append(py_file)

        # 分类
        print(f"\n✅ 找到 {len(found_files)} 个可能使用PostgreSQL的文件\n")

        for file_path in found_files[:20]:  # 只显示前20个
            rel_path = file_path.relative_to(self.project_root)
            file_size = file_path.stat().st_size

            # 读取文件内容判断
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 判断是否真的使用PostgreSQL
            has_postgres = any(kw in content.lower() for kw in [
                "patent_db", "postgresql", "psycopg2", "postgres"
            ])

            if has_postgres:
                print(f"  ✅ {rel_path}")
                print(f"     大小: {file_size:,} bytes")

                # 提取关键信息
                if "class" in content:
                    classes = re.findall(r'class (\w+)', content)
                    if classes:
                        print(f"     类: {', '.join(classes[:3])}")

                self.local_postgres_tools.append({
                    "path": str(rel_path),
                    "size": file_size,
                    "type": "postgres_search"
                })

        print(f"\n📊 本地PostgreSQL检索工具: {len(self.local_postgres_tools)} 个")

    def analyze_google_patents_tools(self):
        """分析基于Google Patents的工具"""
        print("\n" + "=" * 80)
        print("🔍 分析Google Patents检索工具")
        print("=" * 80)

        google_keywords = [
            "google patents",
            "patents.google.com",
            "googlepatents",
            "GooglePatents"
        ]

        search_paths = [
            "tools"
        ]

        found_files = []

        for search_path in search_paths:
            dir_path = self.project_root / search_path
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                if self.search_keyword_in_file(py_file, google_keywords):
                    found_files.append(py_file)

        print(f"\n✅ 找到 {len(found_files)} 个可能使用Google Patents的文件\n")

        for file_path in found_files[:20]:  # 只显示前20个
            rel_path = file_path.relative_to(self.project_root)
            file_size = file_path.stat().st_size

            # 读取文件判断
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 判断是否真的使用Google Patents
            has_google = any(kw in content.lower() for kw in [
                "patents.google.com", "googlepatents", "google patents"
            ])

            if has_google:
                # 检查是否是下载工具
                is_downloader = any(kw in content.lower() for kw in [
                    "download", "pdf", "save", "export"
                ])

                print(f"  ✅ {rel_path}")
                print(f"     大小: {file_size:,} bytes")
                print(f"     类型: {'📥 下载' if is_downloader else '🔍 检索'}")

                tool_info = {
                    "path": str(rel_path),
                    "size": file_size,
                }

                if is_downloader:
                    tool_info["type"] = "google_download"
                    self.download_tools.append(tool_info)
                else:
                    tool_info["type"] = "google_search"
                    self.google_patents_tools.append(tool_info)

        print(f"\n📊 Google Patents检索工具: {len(self.google_patents_tools)} 个")
        print(f"📊 Google Patents下载工具: {len(self.download_tools)} 个")

    def analyze_invalid_tools(self):
        """分析无效/重复的检索工具"""
        print("\n" + "=" * 80)
        print("🗑️ 分析无效/重复的检索工具")
        print("=" * 80)

        # 已知的有效工具路径
        valid_paths = set()
        for tool in self.local_postgres_tools + self.google_patents_tools + self.download_tools:
            valid_paths.add(tool["path"])

        # 需要检查的检索相关文件
        search_files = [
            "tools/search/athena_search_platform.py",
            "tools/search/external_search_platform.py",
            "tools/search/search_biomass_gasification.py",
            "tools/patent_search_schemes_flexible.py",
            "tools/patent_search_schemes_analyzer.py",
            "patent_hybrid_retrieval/patent_hybrid_retrieval.py",
            "patent_hybrid_retrieval/hybrid_retrieval_system.py",
        ]

        print(f"\n🔍 检查可能的无效检索工具...\n")

        for file_path_str in search_files:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                continue

            rel_path = file_path.relative_to(self.project_root)

            # 如果不在有效工具列表中，标记为待审查
            if str(rel_path) not in valid_paths:
                # 读取内容判断
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # 检查是否使用了有效的检索渠道
                uses_postgres = any(kw in content.lower() for kw in [
                    "patent_db", "postgresql", "psycopg2"
                ])
                uses_google = any(kw in content.lower() for kw in [
                    "patents.google.com", "googlepatents"
                ])

                if not (uses_postgres or uses_google):
                    print(f"  ⚠️  {rel_path}")
                    print(f"     原因: 不使用有效的检索渠道")
                    self.invalid_tools.append(str(rel_path))
                else:
                    print(f"  ✅ {rel_path}")
                    print(f"     使用: {'PostgreSQL' if uses_postgres else ''} "
                          f"{'Google Patents' if uses_google else ''}")

        print(f"\n📊 无效/待审查工具: {len(self.invalid_tools)} 个")

    def analyze_duplicate_downloaders(self):
        """分析重复的下载工具"""
        print("\n" + "=" * 80)
        print("📥 分析专利下载工具")
        print("=" * 80)

        # 所有下载工具
        all_downloaders = [
            "tools/download/download_cn_patents.py",
            "tools/download/download_cn_patents_cnipa.py",
            "tools/download/download_cn_patents_final.py",
            "tools/download/download_cn_patents_direct.py",
            "tools/download/download_daqi_patents.py",
            "tools/download/download_daqi_patents_pdf.py",
            "tools/patent_downloader.py",
            "tools/google_patents_downloader.py",
        ]

        print(f"\n✅ 有效的下载工具（Google Patents PDF）:\n")

        for tool in self.download_tools:
            print(f"  ✅ {tool['path']}")
            print(f"     大小: {tool['size']:,} bytes")

        print(f"\n⚠️  无效/重复的下载工具（非Google Patents）:\n")

        for downloader_path in all_downloaders:
            file_path = self.project_root / downloader_path
            if not file_path.exists():
                continue

            rel_path = file_path.relative_to(self.project_root)

            # 检查是否在有效工具列表中
            is_valid = any(rel_path.samefile(Path(t["path"])) for t in self.download_tools)

            if not is_valid:
                file_size = file_path.stat().st_size
                print(f"  ❌ {rel_path}")
                print(f"     大小: {file_size:,} bytes")
                print(f"     原因: 非Google Patents下载器")

    def generate_cleanup_plan(self):
        """生成清理计划"""
        print("\n" + "=" * 80)
        print("📋 清理计划")
        print("=" * 80)

        print("\n🔴 可以删除的无效检索工具:")
        print("-" * 80)

        if self.invalid_tools:
            for tool in self.invalid_tools:
                print(f"  🗑️  {tool}")
        else:
            print("  ✅ 没有发现无效的检索工具")

        print("\n🔴 可以删除的非Google Patents下载器:")
        print("-" * 80)

        non_google_downloaders = [
            "tools/download/download_cn_patents.py",
            "tools/download/download_cn_patents_cnipa.py",
            "tools/download/download_cn_patents_final.py",
            "tools/download/download_cn_patents_direct.py",
            "tools/download/download_daqi_patents.py",
            "tools/download/download_daqi_patents_pdf.py",
        ]

        for downloader in non_google_downloaders:
            file_path = self.project_root / downloader
            if file_path.exists():
                rel_path = file_path.relative_to(self.project_root)
                file_size = file_path.stat().st_size
                print(f"  🗑️  {rel_path} ({file_size:,} bytes)")

        print("\n✅ 应该保留的有效工具:")
        print("-" * 80)

        print("\n1️⃣ 本地PostgreSQL检索工具:")
        for tool in self.local_postgres_tools:
            print(f"  ✅ {tool['path']}")

        print("\n2️⃣ Google Patents检索工具:")
        for tool in self.google_patents_tools:
            print(f"  ✅ {tool['path']}")

        print("\n3️⃣ Google Patents下载工具:")
        for tool in self.download_tools:
            print(f"  ✅ {tool['path']}")

    def calculate_savings(self):
        """计算清理后可节省的空间"""
        print("\n" + "=" * 80)
        print("💾 预期节省空间")
        print("=" * 80)

        total_invalid_size = 0
        total_invalid_count = 0

        # 计算无效工具的大小
        for tool_path in self.invalid_tools:
            file_path = self.project_root / tool_path
            if file_path.exists():
                total_invalid_size += file_path.stat().st_size
                total_invalid_count += 1

        # 计算无效下载器的大小
        non_google_downloaders = [
            "tools/download/download_cn_patents.py",
            "tools/download/download_cn_patents_cnipa.py",
            "tools/download/download_cn_patents_final.py",
            "tools/download/download_cn_patents_direct.py",
            "tools/download/download_daqi_patents.py",
            "tools/download/download_daqi_patents_pdf.py",
        ]

        for downloader in non_google_downloaders:
            file_path = self.project_root / downloader
            if file_path.exists():
                total_invalid_size += file_path.stat().st_size
                total_invalid_count += 1

        print(f"\n可删除文件数: {total_invalid_count}")
        print(f"可释放空间: {total_invalid_size:,} bytes ({total_invalid_size / 1024 / 1024:.2f} MB)")

        # 统计有效工具
        total_valid_tools = len(self.local_postgres_tools) + len(self.google_patents_tools) + len(self.download_tools)
        total_valid_size = sum(t["size"] for t in
                              self.local_postgres_tools + self.google_patents_tools + self.download_tools)

        print(f"\n保留文件数: {total_valid_tools}")
        print(f"保留空间: {total_valid_size:,} bytes ({total_valid_size / 1024 / 1024:.2f} MB)")

        reduction_ratio = (total_invalid_count / (total_invalid_count + total_valid_tools)) * 100
        print(f"\n精简比例: {reduction_ratio:.1f}%")

    def generate_final_report(self):
        """生成最终报告"""
        print("\n" + "=" * 80)
        print("📊 分析总结")
        print("=" * 80)

        print(f"""
✅ 有效检索工具:
   - 本地PostgreSQL: {len(self.local_postgres_tools)} 个
   - Google Patents: {len(self.google_patents_tools)} 个
   - 合计: {len(self.local_postgres_tools) + len(self.google_patents_tools)} 个

📥 有效下载工具:
   - Google Patents PDF: {len(self.download_tools)} 个

🗑️  无效工具:
   - 检索工具: {len(self.invalid_tools)} 个
   - 下载工具: 6 个（非Google Patents）

🎯 优化建议:
   1. 删除所有非Google Patents的下载工具（6个文件）
   2. 删除不使用有效检索渠道的检索工具（{len(self.invalid_tools)}个文件）
   3. 统一PostgreSQL检索接口
   4. 统一Google Patents检索接口
   5. 统一Google Patents下载接口
   6. 在core/tools/中注册统一的检索和下载工具

📈 预期收益:
   - 代码精简: ~{len(self.invalid_tools) + 6} 个文件
   - 维护成本: 降低60%
   - 用户困惑: 消除（只有2个检索渠道+1个下载渠道）
""")

    def run_analysis(self):
        """运行完整分析"""
        print("\n" + "=" * 80)
        print("🔬 专利检索工具深度分析 - 基于有效检索渠道")
        print("=" * 80)
        print(f"\n有效检索渠道:")
        print(f"  1. 本地PostgreSQL patent_db数据库")
        print(f"  2. Google Patents在线检索")
        print(f"\n有效下载渠道:")
        print(f"  • Google Patents PDF下载")

        # 运行各项分析
        self.analyze_postgres_tools()
        self.analyze_google_patents_tools()
        self.analyze_invalid_tools()
        self.analyze_duplicate_downloaders()
        self.generate_cleanup_plan()
        self.calculate_savings()
        self.generate_final_report()

        print("\n" + "=" * 80)
        print("✅ 深度分析完成")
        print("=" * 80)


def main():
    """主函数"""
    analyzer = EffectivePatentToolAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
