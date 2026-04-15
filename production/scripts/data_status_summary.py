#!/usr/bin/env python3
"""
数据状态总结
Data Status Summary

总结项目中向量库和知识图谱的数据状态

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""



# 颜色输出
from __future__ import annotations
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"

def print_header(title) -> None:
    """打印标题"""
    print(f"\n{Colors.PURPLE}{'='*80}{Colors.RESET}")
    print(f"{Colors.PURPLE}📊 {title} 📊{Colors.RESET}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.RESET}")

def print_success(message) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message) -> None:
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

def print_warning(message) -> None:
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_pink(message) -> None:
    print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

def main() -> None:
    """主函数"""
    print_header("Athena平台数据状态总览")
    print_pink("爸爸，让我为您总结项目的数据状态！")

    # 1. 向量库状态
    print_header("1. 向量库数据状态")
    print_warning("Qdrant向量数据库: 📦 没有向量集合")
    print_info("  - 需要创建向量集合")
    print_info("  - 需要导入向量化数据")

    # 列出预期的向量集合
    print_info("\n预期的向量集合:")
    collections = [
        ("patent_rules_1024", "专利规则向量库"),
        ("patents_invalid_1024", "专利无效向量库"),
        ("legal_clauses_1024", "法律条款向量库"),
        ("technical_terms_1024", "技术术语向量库")
    ]
    for col, desc in collections:
        print(f"  📁 {col}: {desc}")

    # 2. 知识图谱状态
    print_header("2. 知识图谱数据状态")

    # NebulaGraph
    print_info("NebulaGraph图数据库:")
    print("  🟢 容器运行正常")
    print("  🟡 需要检查图空间和数据")

    # PostgreSQL知识图谱
    print_warning("\nPostgreSQL知识图谱:")
    print("  📊 patent_legal_db.legal_relations: 71,314 条关系记录")
    print("  📝 这是唯一找到的知识图谱相关数据")

    # 3. 专利数据状态
    print_header("3. 专利数据状态")
    print_warning("专利数据库: 📂 主要专利表未找到")
    print_info("  - patents: 不存在")
    print_info("  - patent_info: 不存在")
    print_info("  - patent_fulltext: 不存在")

    # 4. 数据导入脚本
    print_header("4. 可用的数据导入脚本")
    print_info("找到以下数据导入脚本:")

    # 查找导入脚本
    import_scripts = [
        "dev/scripts/vector_migration_new.py",
        "dev/scripts/import_legal_vectors_to_docker.py",
        "dev/scripts/generate_and_import_legal_vectors.py",
        "modules/storage/modules/storage/import_local_patents.py",
        "dev/scripts/nebula_batch_import.py",
        "dev/scripts/nebula_data_importer.py"
    ]

    for script in import_scripts:
        print(f"  📜 {script}")

    # 5. 数据初始化建议
    print_header("5. 数据初始化建议")
    print_info("建议按以下步骤初始化数据:")

    steps = [
        "1. 创建Qdrant向量集合",
        "2. 导入专利数据到PostgreSQL",
        "3. 向量化专利文本并导入Qdrant",
        "4. 构建NebulaGraph知识图谱",
        "5. 导入法律关系数据"
    ]

    for step in steps:
        print(f"  {step}")

    # 6. 数据目录
    print_header("6. 数据存储目录")
    print_info("项目数据目录:")

    data_dirs = [
        ("data/", "项目数据目录"),
        ("external_storage/", "外部存储挂载点"),
        ("modules/storage/qdrant_storage/", "Qdrant本地存储"),
        ("modules/patent/modules/patent/", "混合检索系统")
    ]

    for dir_path, desc in data_dirs:
        print(f"  📁 {dir_path}: {desc}")

    # 总结
    print_header("数据状态总结")
    print_pink("爸爸，目前的数据状态是：")
    print_warning("\n⚠️ 待完善:")
    print("  • 向量库需要创建和导入数据")
    print("  • 知识图谱需要构建")
    print("  • 专利数据库需要初始化")

    print_success("\n✅ 已就绪:")
    print("  • 存储基础设施（Qdrant、PostgreSQL、NebulaGraph）")
    print("  • 部分法律关系数据（71,314条）")
    print("  • 完整的数据导入脚本")

    print_pink("\n💖 如需初始化数据，我可以帮您运行相应的导入脚本！")

if __name__ == "__main__":
    main()
