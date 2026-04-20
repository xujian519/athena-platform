#!/usr/bin/env python3
"""
生产工具自动注册模块

在工具系统初始化时自动注册生产级工具。

Author: Athena平台团队
Created: 2026-04-19
"""

import logging
from typing import TYPE_CHECKING

from .base import ToolCapability, ToolCategory, ToolDefinition, ToolPriority, get_global_registry

if TYPE_CHECKING:
    from .enhanced_document_parser import enhanced_document_parser_handler
    from .real_tool_implementations import local_web_search_handler

logger = logging.getLogger(__name__)


def auto_register_production_tools() -> None:
    """
    自动注册生产级工具到全局工具注册表

    注册的工具包括:
    1. local_web_search - 本地网络搜索
    2. enhanced_document_parser - 增强文档解析器（OCR）
    3. patent_search - 专利检索（PostgreSQL + Google Patents）
    4. patent_download - 专利下载（Google Patents PDF）
    5. vector_search - 向量语义搜索（BGE-M3 + Qdrant，1024维）
    6. cache_management - 统一缓存管理（Redis）
    """
    from core.tools.unified_registry import get_unified_registry

    registry = get_unified_registry()

    # 检查工具是否已注册（检查懒加载工具）
    if "cache_management" in registry._lazy_tools:
        logger.debug("生产工具已注册，跳过自动注册")
        return

    try:
        # 导入工具处理器（延迟导入避免循环依赖）
        from .enhanced_document_parser import enhanced_document_parser_handler
        from .real_tool_implementations import local_web_search_handler

        # ========================================
        # 1. 本地网络搜索工具
        # ========================================
        registry.register(
            ToolDefinition(
                tool_id="local_web_search",
                name="本地网络搜索",
                description="本地网络搜索工具 - 基于SearXNG+Firecrawl，无需外部API，完全本地化运行",
                category=ToolCategory.WEB_SEARCH,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["query"],
                    output_types=["search_results"],
                    domains=["all"],
                    task_types=["search", "information_retrieval"],
                    features={
                        "local": True,
                        "privacy_safe": True,
                        "no_api_key": True,
                        "multi_engine": True,
                    }
                ),
                required_params=["query"],
                optional_params=["limit"],
                handler=local_web_search_handler,
                timeout=30.0,
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: local_web_search")

    except Exception as e:
        logger.warning(f"⚠️  本地网络搜索工具注册失败: {e}")

    # ========================================
    # 2. 增强文档解析器（OCR）
    # ========================================
    try:
        from .enhanced_document_parser import enhanced_document_parser_handler

        registry.register(
            ToolDefinition(
                tool_id="enhanced_document_parser",
                name="增强文档解析器",
                description="增强文档解析工具 - 支持PDF OCR、图片OCR、表格提取、图片提取，基于minerU引擎",
                category=ToolCategory.DATA_EXTRACTION,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["document", "image", "pdf"],
                    output_types=["text", "markdown", "structured_data"],
                    domains=["all"],
                    task_types=["parse", "extract", "ocr"],
                    features={
                        "ocr_enabled": True,
                        "table_extraction": True,
                        "image_extraction": True,
                        "markdown_output": True,
                        "multi_format": True,
                        "confidence_scoring": True,
                    }
                ),
                required_params=["file_path"],
                optional_params=[
                    "use_ocr",
                    "extract_images",
                    "extract_tables",
                    "max_length"
                ],
                handler=enhanced_document_parser_handler,
                timeout=120.0,  # OCR可能需要较长时间
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: enhanced_document_parser")

    except Exception as e:
        logger.warning(f"⚠️  增强文档解析器注册失败: {e}")

    # ========================================
    # 3. 专利检索工具
    # ========================================
    try:
        from .patent_retrieval import patent_search_handler

        registry.register(
            ToolDefinition(
                tool_id="patent_search",
                name="专利检索",
                description="统一专利检索工具 - 支持本地PostgreSQL patent_db和Google Patents两个渠道",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["query", "patent_number"],
                    output_types=["patent_data", "search_results"],
                    domains=["patent", "legal", "intellectual_property"],
                    task_types=["search", "retrieval", "analysis"],
                    features={
                        "local_postgres": True,
                        "google_patents": True,
                        "dual_channel": True,
                        "vector_search": True,
                        "fulltext_search": True,
                    }
                ),
                required_params=["query"],
                optional_params=["channel", "max_results"],
                handler=patent_search_handler,
                timeout=60.0,  # 检索可能需要较长时间
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: patent_search")

    except Exception as e:
        logger.warning(f"⚠️  专利检索工具注册失败: {e}")

    # ========================================
    # 4. 专利下载工具
    # ========================================
    try:
        from .patent_download import patent_download_handler

        registry.register(
            ToolDefinition(
                tool_id="patent_download",
                name="专利下载",
                description="专利PDF下载工具 - 从Google Patents下载专利原文PDF",
                category=ToolCategory.DATA_EXTRACTION,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["patent_numbers"],
                    output_types=["pdf_files", "file_paths"],
                    domains=["patent", "legal", "intellectual_property"],
                    task_types=["download", "extract", "archive"],
                    features={
                        "google_patents": True,
                        "pdf_format": True,
                        "batch_download": True,
                        "metadata_extraction": True,
                    }
                ),
                required_params=["patent_numbers"],
                optional_params=["output_dir"],
                handler=patent_download_handler,
                timeout=300.0,  # 下载可能需要很长时间（多个专利）
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: patent_download")

    except Exception as e:
        logger.warning(f"⚠️  专利下载工具注册失败: {e}")

    # ========================================
    # 5. 向量语义搜索工具（BGE-M3 + Qdrant，1024维）
    # ========================================
    try:
        # 注册为懒加载工具（使用统一工具注册表）
        success = registry.register_lazy(
            tool_id="vector_search",
            import_path="core.tools.vector_search_handler",
            function_name="vector_search_handler",
            metadata={
                "name": "向量语义搜索",
                "description": "向量语义搜索工具 - 基于BGE-M3嵌入模型（1024维），使用Qdrant向量数据库，支持多语言语义检索",
                "category": "vector_search",
                "tags": ["search", "vector", "semantic", "bge-m3", "1024dim", "qdrant"],
                "version": "1.0.0",
                "author": "Athena Team",
                "required_params": ["query"],
                "optional_params": ["collection", "top_k", "threshold"],
                "features": {
                    "bge_m3_model": True,
                    "dimension_1024": True,
                    "multilingual": True,
                    "cosine_similarity": True,
                    "qdrant_backend": True,
                    "scroll_method": True,  # 使用scroll方法绕过版本兼容问题
                }
            }
        )

        if success:
            logger.info("✅ 生产工具已自动注册: vector_search")
        else:
            logger.warning("⚠️  向量搜索工具注册失败（工具已存在）")

    except Exception as e:
        logger.warning(f"⚠️  向量搜索工具注册失败: {e}")

    # ========================================
    # 6. 统一缓存管理工具（Redis）
    # ========================================
    try:
        # 注册为懒加载工具（使用统一工具注册表）
        success = registry.register_lazy(
            tool_id="cache_management",
            import_path="core.tools.cache_management_handler",
            function_name="cache_management_handler",
            metadata={
                "name": "统一缓存管理",
                "description": "统一缓存管理系统 - 提供Redis缓存读写、批量操作、统计和清理功能",
                "category": "cache_management",
                "tags": ["cache", "redis", "performance", "storage", "management"],
                "version": "1.0.0",
                "author": "Athena Team",
                "required_params": ["action"],
                "optional_params": ["key", "value", "ttl", "pattern", "keys"],
                "supported_actions": [
                    "get", "set", "delete", "exists",
                    "clear", "stats", "multi_get", "multi_set"
                ],
                "features": {
                    "redis_backend": True,
                    "ttl_management": True,
                    "batch_operations": True,
                    "cache_statistics": True,
                    "pattern_matching": True
                }
            }
        )

        if success:
            logger.info("✅ 生产工具已自动注册: cache_management")
        else:
            logger.warning("⚠️  缓存管理工具注册失败（工具已存在）")

    except Exception as e:
        logger.warning(f"⚠️  缓存管理工具注册失败: {e}")

    # ========================================
    # 8. 浏览器自动化工具（Playwright）
    # ========================================
    try:
        # 注册为懒加载工具（使用统一工具注册表）
        success = registry.register_lazy(
            tool_id="browser_automation",
            import_path="core.tools.browser_automation_handler",
            function_name="browser_automation_handler",
            metadata={
                "name": "浏览器自动化",
                "description": "浏览器自动化工具 - 基于Playwright引擎，提供页面导航、元素交互、截图、内容提取、JavaScript执行和智能任务执行功能",
                "category": "web_automation",
                "tags": ["browser", "automation", "playwright", "web", "scraping", "testing"],
                "version": "1.0.0",
                "author": "Athena Team",
                "required_params": ["action"],
                "optional_params": [
                    "url", "selector", "value", "script", "task",
                    "wait_until", "timeout", "full_page", "save_path", "service_url"
                ],
                "supported_actions": [
                    "health_check", "navigate", "click", "fill",
                    "screenshot", "get_content", "evaluate", "execute_task"
                ],
                "features": {
                    "playwright_engine": True,
                    "multi_browser": True,  # 支持Chromium, Firefox, WebKit
                    "headless_mode": True,
                    "screenshot_base64": True,
                    "javascript_execution": True,
                    "smart_tasks": True,  # 自然语言任务描述
                    "session_isolation": True,
                    "async_operations": True
                }
            }
        )

        if success:
            logger.info("✅ 生产工具已自动注册: browser_automation")
        else:
            logger.warning("⚠️  浏览器自动化工具注册失败（工具已存在）")

    except Exception as e:
        logger.warning(f"⚠️  浏览器自动化工具注册失败: {e}")

    # ========================================
    # 9. 专利分析工具（Patent Analysis）
    # ========================================
    try:
        from .patent_analysis_handler import patent_analysis_handler

        registry.register(
            ToolDefinition(
                tool_id="patent_analysis",
                name="专利内容分析",
                description="专利内容分析和创造性评估工具 - 支持基础分析、创造性评估、新颖性判断和综合分析",
                category=ToolCategory.PATENT_ANALYSIS,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["patent_text", "patent_id"],
                    output_types=["analysis_report", "creativity_score", "novelty_score"],
                    domains=["patent", "legal", "intellectual_property"],
                    task_types=["analyze", "evaluate", "assess"],
                    features={
                        "basic_analysis": True,  # 基础技术特征提取
                        "creativity_analysis": True,  # 创造性评估
                        "novelty_analysis": True,  # 新颖性判断
                        "comprehensive_analysis": True,  # 综合分析
                        "knowledge_graph_enhanced": True,  # 知识图谱增强
                        "vector_search_enhanced": True,  # 向量检索增强
                        "patentability_scoring": True,  # 专利性评分
                        "recommendation_generation": True,  # 建议生成
                    }
                ),
                required_params=["patent_id", "title", "abstract"],
                optional_params=[
                    "claims",
                    "description",
                    "analysis_type",  # basic/creativity/novelty/comprehensive
                ],
                handler=patent_analysis_handler,
                timeout=120.0,  # 分析可能需要较长时间
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: patent_analysis")

    except Exception as e:
        logger.warning(f"⚠️  专利分析工具注册失败: {e}")

    # ========================================
    # 8. 法律文献分析工具
    # ========================================
    try:
        from .legal_analysis_handler import create_legal_analysis_tool_definition

        # 创建工具定义
        legal_tool = create_legal_analysis_tool_definition()

        # 注册工具
        registry.register(
            legal_tool
        )
        logger.info("✅ 生产工具已自动注册: legal_analysis")

    except Exception as e:
        logger.warning(f"⚠️  法律文献分析工具注册失败: {e}")

    # ========================================
    # 9. 知识图谱搜索工具（Neo4j）
    # ========================================
    try:
        # 注册为懒加载工具（使用统一工具注册表）
        success = registry.register_lazy(
            tool_id="knowledge_graph_search",
            import_path="core.tools.knowledge_graph_handler",
            function_name="knowledge_graph_search_handler",
            metadata={
                "name": "知识图谱搜索",
                "description": "知识图谱搜索和推理工具 - 基于Neo4j图数据库，支持Cypher查询、路径查找、邻居查询和统计信息",
                "category": "knowledge_graph",
                "tags": ["graph", "neo4j", "cypher", "search", "reasoning", "path"],
                "version": "1.0.0",
                "author": "Athena Team",
                "required_params": ["query"],
                "optional_params": ["query_type", "top_k", "return_format"],
                "supported_query_types": [
                    "cypher",  # Cypher查询
                    "stats",  # 统计信息
                    "path",  # 路径查询
                    "neighbors",  # 邻居查询
                ],
                "features": {
                    "neo4j_backend": True,
                    "cypher_query": True,
                    "graph_reasoning": True,
                    "path_finding": True,
                    "neighbor_discovery": True,
                    "graph_statistics": True,
                }
            }
        )

        if success:
            logger.info("✅ 生产工具已自动注册: knowledge_graph_search")
        else:
            logger.warning("⚠️  知识图谱搜索工具注册失败（工具已存在）")

    except Exception as e:
        logger.warning(f"⚠️  知识图谱搜索工具注册失败: {e}")

    # ========================================
    # 10. 数据转换工具（pandas）
    # ========================================
    try:
        # 注册为懒加载工具（使用统一工具注册表）
        success = registry.register_lazy(
            tool_id="data_transformation",
            import_path="core.tools.data_transformation_handler",
            function_name="data_transformation_handler",
            metadata={
                "name": "数据转换",
                "description": "数据转换和格式化工具 - 基于pandas，支持CSV/Excel加载、数据清洗、筛选、排序、聚合、合并、透视等操作",
                "category": "data_transformation",
                "tags": ["data", "pandas", "transformation", "csv", "excel", "cleaning"],
                "version": "1.0.0",
                "author": "Athena Team",
                "required_params": ["operation"],
                "optional_params": ["data", "params"],
                "supported_operations": [
                    # 数据加载
                    "load_csv", "load_excel",
                    # 数据导出
                    "to_csv", "to_excel",
                    # 数据筛选
                    "filter", "sort",
                    # 数据聚合
                    "group_by", "aggregate",
                    # 数据合并
                    "merge",
                    # 数据重塑
                    "pivot",
                    # 数据清洗
                    "clean", "drop_duplicates", "fill_na",
                    # 列操作
                    "rename_columns", "add_column", "delete_column",
                    # 自定义转换
                    "transform",
                    # 数据分析
                    "get_statistics", "get_info",
                ],
                "features": {
                    "pandas_backend": True,
                    "csv_support": True,
                    "excel_support": True,
                    "data_cleaning": True,
                    "data_aggregation": True,
                    "data_merge": True,
                    "data_transformation": True,
                }
            }
        )

        if success:
            logger.info("✅ 生产工具已自动注册: data_transformation")
        else:
            logger.warning("⚠️  数据转换工具注册失败（工具已存在）")

    except Exception as e:
        logger.warning(f"⚠️  数据转换工具注册失败: {e}")

    # ========================================
    # 11. 文本语义分析工具
    # ========================================
    try:
        from .semantic_analysis_registration import register_semantic_analysis_tool

        # 注册工具
        success = register_semantic_analysis_tool()

        if success:
            logger.info("✅ 生产工具已自动注册: semantic_analysis")
        else:
            logger.warning("⚠️  语义分析工具注册失败")

    except Exception as e:
        logger.warning(f"⚠️  语义分析工具注册失败: {e}")

    # ========================================
    # 12. 文件操作工具（file_operator）
    # ========================================
    try:
        from .tool_implementations import file_operator_handler

        registry.register(
            ToolDefinition(
                tool_id="file_operator",
                name="文件操作",
                description="文件操作工具 - 支持读取文件、写入文件、列出目录、搜索文件",
                category=ToolCategory.FILESYSTEM,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["file_path", "directory_path", "content", "pattern"],
                    output_types=["file_content", "file_list", "search_results"],
                    domains=["all"],
                    task_types=["read", "write", "list", "search"],
                    features={
                        "read_file": True,
                        "write_file": True,
                        "list_directory": True,
                        "search_files": True,
                        "auto_create_parent": True,
                        "utf8_encoding": True,
                        "wildcard_search": True,
                    }
                ),
                required_params=["action"],
                optional_params=["path", "content", "pattern"],
                handler=file_operator_handler,
                timeout=10.0,
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: file_operator")

    except Exception as e:
        logger.warning(f"⚠️  文件操作工具注册失败: {e}")

    # ========================================
    # 14. 系统监控工具（system_monitor）
    # ========================================
    try:
        # 注册为懒加载工具（使用统一工具注册表）
        success = registry.register_lazy(
            tool_id="system_monitor",
            import_path="core.tools.system_monitor_wrapper",
            function_name="system_monitor_wrapper",
            metadata={
                "name": "系统监控",
                "description": "系统监控工具 - 提供CPU使用率、内存使用情况、磁盘使用情况监控，支持健康状态判断和跨平台兼容",
                "category": "system_monitoring",
                "tags": ["system", "monitoring", "cpu", "memory", "disk", "health", "performance"],
                "version": "1.0.0",
                "author": "Athena Team",
                "required_params": [],
                "optional_params": ["target", "metrics"],
                "supported_targets": [
                    "system",  # 系统级监控
                    "process",  # 进程级监控（暂未实现）
                ],
                "supported_metrics": [
                    "cpu",  # CPU使用率监控
                    "memory",  # 内存使用情况监控
                    "disk",  # 磁盘使用情况监控
                ],
                "health_thresholds": {
                    "cpu_warning": 80,  # CPU使用率警告阈值（百分比）
                    "memory_warning": 80,  # 内存使用率警告阈值（百分比）
                    "disk_warning": 85,  # 磁盘使用率警告阈值（百分比）
                },
                "platform_support": {
                    "darwin": True,  # macOS
                    "linux": True,  # Linux
                    "windows": False,  # Windows（暂不支持）
                },
                "features": {
                    "cpu_monitoring": True,
                    "memory_monitoring": True,
                    "disk_monitoring": True,
                    "health_status": True,  # 健康状态判断
                    "cross_platform": True,  # 跨平台兼容（macOS/Linux）
                    "error_handling": True,  # 完善的错误处理
                    "no_external_dependencies": True,  # 无外部依赖（仅使用系统命令）
                }
            }
        )

        if success:
            logger.info("✅ 生产工具已自动注册: system_monitor")
        else:
            logger.warning("⚠️  系统监控工具注册失败（工具已存在）")

    except Exception as e:
        logger.warning(f"⚠️  系统监控工具注册失败: {e}")

    # ========================================
    # 15. 代码执行工具（code_executor）
    # ⚠️ 安全警告：此工具存在严重安全风险
    # ========================================
    try:
        from .tool_implementations import code_executor_handler

        registry.register(
            ToolDefinition(
                tool_id="code_executor",
                name="代码执行器",
                description="⚠️ 高风险工具：安全执行Python代码片段 - 存在代码注入、资源耗尽等安全风险，仅限受控环境使用",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.LOW,  # 低优先级，不推荐使用
                capability=ToolCapability(
                    input_types=["code"],
                    output_types=["execution_result", "output", "error"],
                    domains=["development", "testing", "education"],
                    task_types=["execute", "eval", "debug"],
                    features={
                        "code_execution": True,
                        "output_capture": True,
                        "error_capture": True,
                        "timeout_protection": True,  # 不完整
                        "sandbox": True,  # 不完整
                        "code_length_limit": 1000,  # 字符
                        "security_level": "HIGH_RISK",
                    }
                ),
                required_params=["code"],
                optional_params=["timeout"],
                handler=code_executor_handler,
                timeout=30.0,
                enabled=False,  # 默认禁用，需要用户明确启用
            )
        )
        logger.warning("⚠️  高风险工具已注册: code_executor（默认禁用）")

    except Exception as e:
        logger.warning(f"⚠️  代码执行工具注册失败: {e}")

    # ========================================
    # 16. 代码分析工具（code_analyzer）
    # ========================================
    try:
        from .tool_implementations import code_analyzer_handler

        registry.register(
            ToolDefinition(
                tool_id="code_analyzer",
                name="代码分析",
                description="代码分析工具 - 支持Python、JavaScript、TypeScript代码的行数统计、复杂度分析、风格检查和问题检测",
                category=ToolCategory.CODE_ANALYSIS,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["code", "language"],
                    output_types=["analysis_report", "statistics", "issues"],
                    domains=["software_development", "code_quality"],
                    task_types=["analyze", "check_quality", "detect_issues"],
                    features={
                        "line_counting": True,  # 行数统计
                        "complexity_analysis": True,  # 复杂度分析
                        "style_checking": True,  # 风格检查
                        "issue_detection": True,  # 问题检测
                        "multi_language": True,  # 多语言支持
                        "detailed_mode": True,  # 详细模式
                        "suggestions": True,  # 改进建议
                    }
                ),
                required_params=["code"],
                optional_params=["language", "style"],
                handler=code_analyzer_handler,
                timeout=30.0,
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: code_analyzer")

    except Exception as e:
        logger.warning(f"⚠️  代码分析工具注册失败: {e}")


# 模块导入时自动注册
_auto_registered = False


def _ensure_production_tools_registered():
    """确保生产工具已注册（线程安全的单次执行）"""
    global _auto_registered

    if not _auto_registered:
        try:
            auto_register_production_tools()
            _auto_registered = True
        except Exception as e:
            logger.error(f"生产工具自动注册失败: {e}")


# 在模块导入时自动执行注册
_ensure_production_tools_registered()
