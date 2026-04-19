#!/usr/bin/env python3
from __future__ import annotations
"""
工具中文标签映射
Tool Chinese Labels Mapping

为工具添加中文描述标签,提高中文查询的匹配率

使用方法:
    from core.governance.tool_labels_zh import TOOL_LABELS_ZH

    tool_id = "service.IntegratedPatentService"
    labels = TOOL_LABELS_ZH.get(tool_id, [])
    print(labels)  # ['专利', '搜索', '集成', '服务']
"""

# 工具中文标签映射表
# 格式: {tool_id: [中文标签列表]}

TOOL_LABELS_ZH = {
    # ==================== 专利相关工具 ====================
    "service.IntegratedPatentService": ["专利", "搜索", "集成", "服务", "知识产权"],
    "service.AthenaPatentWritingTool": ["专利", "写作", "生成", "文档", "创建"],
    "domain.PatentKnowledgeGraphService": ["专利", "知识", "图谱", "关系", "分析"],
    "domain.PatentVectorSearchService": ["专利", "向量", "搜索", "语义", "相似度"],
    "agent.PatentCrawlerAgent": ["专利", "爬虫", "抓取", "采集", "数据"],
    "service.PatentOCRService": ["专利", "OCR", "识别", "图片", "文字"],
    "service.PatentAnalysisService": ["专利", "分析", "评估", "价值", "报告"],
    # ==================== 法律相关工具 ====================
    "domain.LegalKnowledgeGraphService": ["法律", "知识", "图谱", "法规", "条例"],
    "service.LegalDocumentService": ["法律", "文档", "合同", "协议", "模板"],
    "service.CaseSearchService": ["案例", "搜索", "判决", "裁定", "案例库"],
    "agent.LegalAnalysisAgent": ["法律", "分析", "合规", "审查", "检查"],
    # ==================== 搜索相关工具 ====================
    "service.ExternalSearchServiceManager": ["搜索", "外部", "引擎", "管理", "服务"],
    "service.BingSearchService": ["搜索", "Bing", "必应", "微软", "网页"],
    "service.GoogleSearchService": ["搜索", "Google", "谷歌", "网页"],
    "agent.WebCrawlerAgent": ["爬虫", "抓取", "网页", "采集", "数据"],
    # ==================== 文档处理工具 ====================
    "service.DocumentProcessor": ["文档", "处理", "解析", "提取", "分析"],
    "service.PDFExtractor": ["PDF", "提取", "文档", "解析", "文字"],
    "service.DocumentGenerator": ["文档", "生成", "创建", "写作", "自动"],
    "service.DocumentConverter": ["文档", "转换", "格式", "变换"],
    # ==================== 数据分析工具 ====================
    "service.DataAnalyzer": ["数据", "分析", "统计", "报表", "可视化"],
    "service.StatisticsService": ["统计", "分析", "计算", "数据", "指标"],
    "service.VisualizationService": ["可视化", "图表", "展示", "图形"],
    # ==================== 向量和嵌入工具 ====================
    "service.EmbeddingService": ["嵌入", "向量", "embedding", "语义", "转换"],
    "service.VectorSearchService": ["向量", "搜索", "相似度", "匹配", "检索"],
    "service.SemanticSearchService": ["语义", "搜索", "理解", "智能", "匹配"],
    # ==================== 知识图谱工具 ====================
    "service.KnowledgeGraphService": ["知识", "图谱", "关系", "实体", "连接"],
    "service.GraphQueryService": ["图谱", "查询", "检索", "遍历", "路径"],
    "service.GraphBuilder": ["图谱", "构建", "创建", "生成", "建立"],
    # ==================== 智能体工具 ====================
    "service.AthenaIterativeSearchAgent": ["智能体", "搜索", "迭代", "优化", "Athena"],
    "agent.AthenaWisdomAgent": ["智能体", "Athena", "智慧", "女神", "助手"],
    "agent.XiaonuoPiscesAgent": ["智能体", "小诺", "双鱼", "协调", "调度"],
    "agent.AthenaXiaonaAgent": ["智能体", "小娜", "天秤", "法律", "专家"],
    # ==================== MCP服务工具 ====================
    "mcp.jina-ai": ["Jina", "AI", "内容", "提取", "网页"],
    "mcp.bing-cn-search": ["Bing", "中文", "搜索", "网页", "国内"],
    "mcp.amap-mcp": ["高德", "地图", "位置", "导航", "路径"],
    "mcp.academic-search": ["学术", "搜索", "论文", "研究", "文献"],
    # ==================== 系统管理工具 ====================
    "service.run_service": ["运行", "服务", "启动", "执行", "系统"],
    "service.stop_service": ["停止", "服务", "关闭", "终止"],
    "service.SystemMonitor": ["监控", "系统", "状态", "性能", "资源"],
    "service.LogService": ["日志", "记录", "监控", "分析", "查询"],
    # ==================== 配置管理工具 ====================
    "service.ConfigManager": ["配置", "管理", "设置", "参数"],
    "service.UpdateService": ["更新", "升级", "版本", "发布"],
    "service.BackupService": ["备份", "恢复", "存档", "保护"],
    # ==================== 通信工具 ====================
    "service.NotificationService": ["通知", "消息", "提醒", "告警"],
    "service.MessageService": ["消息", "通信", "发送", "推送"],
    "service.EmailService": ["邮件", "发送", "通知", "通信"],
    # ==================== 存储工具 ====================
    "service.DatabaseService": ["数据库", "存储", "查询", "管理"],
    "service.CacheService": ["缓存", "存储", "加速", "临时"],
    "service.FileStorageService": ["文件", "存储", "保存", "读写"],
    # ==================== 测试工具 ====================
    "service.TestRunner": ["测试", "运行", "执行", "验证"],
    "service.TestTools": ["测试", "工具", "辅助", "调试"],
    "service.BenchmarkService": ["基准", "测试", "性能", "评估"],
    # ==================== 通用工具 ====================
    "service.UtilityTools": ["工具", "实用", "辅助", "通用"],
    "service.HelperFunctions": ["辅助", "函数", "工具", "帮助"],
    "service.CommonUtils": ["通用", "工具", "函数", "方法"],
}


def get_tool_labels(tool_id: str) -> list:
    """
    获取工具的中文标签

    Args:
        tool_id: 工具ID

    Returns:
        中文标签列表
    """
    return TOOL_LABELS_ZH.get(tool_id, [])


def add_tool_labels(tool_metadata_dict: dict) -> dict:
    """
    为工具元数据添加中文标签

    Args:
        tool_metadata_dict: 工具元数据字典

    Returns:
        添加了中文标签的工具元数据字典
    """
    # 为每个工具添加中文标签
    for tool_id, labels in TOOL_LABELS_ZH.items():
        if tool_id in tool_metadata_dict:
            metadata = tool_metadata_dict[tool_id]

            # 将中文标签添加到描述中
            if metadata.description:
                original_desc = metadata.description
                # 添加中文标签到描述
                label_str = " ".join(labels)
                metadata.description = f"{original_desc} [{label_str}]"

    return tool_metadata_dict


def get_all_label_keywords() -> set:
    """
    获取所有中文标签关键词

    Returns:
        中文标签集合
    """
    keywords = set()
    for labels in TOOL_LABELS_ZH.values():
        keywords.update(labels)
    return keywords


def get_tools_by_label(label: str, tool_labels: dict | None = None) -> list:
    """
    根据中文标签查找工具

    Args:
        label: 中文标签
        tool_labels: 工具标签字典(默认使用TOOL_LABELS_ZH)

    Returns:
        匹配的工具ID列表
    """
    if tool_labels is None:
        tool_labels = TOOL_LABELS_ZH

    matched_tools = []
    for tool_id, labels in tool_labels.items():
        if label in labels:
            matched_tools.append(tool_id)

    return matched_tools
