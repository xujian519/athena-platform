#!/usr/bin/env python3
"""
网关能力选择器训练脚本
Gateway Capability Selector Training Script

基于18个网关能力的智能选择器训练
修复版:使用扁平化特征避免TypeError

作者: Athena平台团队
版本: v2.0.0 "网关能力选择器"
"""

from __future__ import annotations
import os
from datetime import datetime
from typing import Any

import jieba
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# ==================== 18个网关能力定义 ====================

GATEWAY_CAPABILITIES = [
    # 基础能力(4种)
    "daily_chat",
    "platform_controller",
    "coding_assistant",
    "life_assistant",
    # 专业能力(2种)
    "patent",
    "legal",
    # 高级能力(4种)
    "nlp",
    "knowledge_graph",
    "memory",
    "optimization",
    # Phase 3能力(3种)
    "multimodal",
    "agent_fusion",
    "autonomous",
    # Phase 4能力(3种)
    "enterprise",
    "quantization",
    "federated",
    # 智能体能力(1种)
    "xiaochen",
]

# ==================== 平衡训练数据集 ====================

# 每个能力50个样本,总计900个样本
BALANCED_TRAINING_DATA = {
    "daily_chat": [
        # 问候类(10个)
        "你好",
        "早上好",
        "晚上好",
        "你好吗",
        "在吗",
        "哈喽",
        "嗨",
        "早上好呀",
        "下午好",
        "晚安",
        # 情感交流(10个)
        "心情不太好",
        "今天很开心",
        "感到有些焦虑",
        "很孤独",
        "需要鼓励",
        "被你感动了",
        "感觉很温暖",
        "想找人聊天",
        "心情很激动",
        "难过时想说话",
        # 聊天话题(10个)
        "聊聊天气",
        "随便聊聊",
        "讲个笑话",
        "推荐首歌",
        "想看电影",
        "无聊了",
        "放松一下",
        "闲聊",
        "说说话",
        "解闷",
        # 生活问题(10个)
        "天气怎么样",
        "今天星期几",
        "现在几点",
        "有什么新闻",
        "讲个故事",
        "推荐美食",
        "好玩的地方",
        "最近流行什么",
        "娱乐新闻",
        "体育新闻",
        # 搜索查询(10个)
        "搜索一下",
        "查查信息",
        "找点资料",
        "网上查查",
        "百度一下",
        "想知道",
        "了解一下",
        "搜索信息",
        "查找资料",
        "网络搜索",
    ],
    "platform_controller": [
        # 系统控制(10个)
        "启动服务",
        "停止程序",
        "重启系统",
        "关闭服务",
        "暂停运行",
        "恢复服务",
        "启动应用",
        "停止应用",
        "重启服务",
        "关闭系统",
        # 系统检查(10个)
        "检查系统状态",
        "查看服务状态",
        "健康检查",
        "系统诊断",
        "监控状态",
        "服务状态",
        "运行状态",
        "系统健康",
        "性能检查",
        "状态检查",
        # 配置管理(10个)
        "更新配置",
        "修改设置",
        "系统配置",
        "参数设置",
        "环境配置",
        "配置文件",
        "设置参数",
        "调整配置",
        "配置管理",
        "系统设置",
        # 监控告警(10个)
        "查看监控",
        "系统监控",
        "性能监控",
        "日志监控",
        "资源监控",
        "监控数据",
        "告警信息",
        "系统日志",
        "运行日志",
        "监控告警",
        # 系统操作(10个)
        "清理缓存",
        "备份数据",
        "恢复数据",
        "系统维护",
        "清理系统",
        "优化系统",
        "系统升级",
        "部署应用",
        "系统部署",
        "运维操作",
    ],
    "coding_assistant": [
        # 代码分析(10个)
        "分析代码",
        "代码审查",
        "检查代码质量",
        "代码优化",
        "重构代码",
        "代码诊断",
        "静态分析",
        "代码检查",
        "代码规范",
        "代码质量",
        # 编程问题(10个)
        "如何编程",
        "写个函数",
        "代码实现",
        "算法实现",
        "数据结构",
        "编程问题",
        "代码问题",
        "写代码",
        "程序设计",
        "代码逻辑",
        # API测试(10个)
        "测试API",
        "接口测试",
        "API调试",
        "接口调试",
        "测试接口",
        "API文档",
        "接口文档",
        "API调用",
        "接口调用",
        "HTTP请求",
        # 性能优化(10个)
        "性能分析",
        "性能优化",
        "代码性能",
        "程序性能",
        "优化性能",
        "性能测试",
        "性能调优",
        "代码效率",
        "程序效率",
        "性能问题",
        # 调试问题(10个)
        "调试代码",
        "代码错误",
        "程序bug",
        "修复bug",
        "代码调试",
        "错误排查",
        "问题排查",
        "代码异常",
        "程序错误",
        "debug",
    ],
    "life_assistant": [
        # 日程管理(10个)
        "安排日程",
        "制定计划",
        "时间管理",
        "日程提醒",
        "日程安排",
        "今日计划",
        "周计划",
        "月计划",
        "时间表",
        "日程表",
        # 提醒事项(10个)
        "设置提醒",
        "提醒我",
        "闹钟设置",
        "备忘录",
        "记事本",
        "待办事项",
        "任务提醒",
        "事项提醒",
        "重要提醒",
        "定时提醒",
        # 生活建议(10个)
        "生活建议",
        "健康建议",
        "饮食建议",
        "运动建议",
        "作息建议",
        "生活习惯",
        "健康生活",
        "养生建议",
        "生活方式",
        "生活技巧",
        # 家庭事务(10个)
        "家庭安排",
        "家务管理",
        "家庭计划",
        "家庭事务",
        "家庭管理",
        "家务分工",
        "家庭活动",
        "家庭聚会",
        "家庭日程",
        "家庭提醒",
        # 个人助理(10个)
        "个人助理",
        "私人助理",
        "帮我安排",
        "协助管理",
        "智能助理",
        "助理服务",
        "秘书服务",
        "个人助手",
        "智能助手",
        "助理功能",
    ],
    "patent": [
        # 专利检索(10个)
        "专利检索",
        "搜索专利",
        "专利查询",
        "查找专利",
        "专利搜索",
        "专利信息",
        "专利数据库",
        "专利文献",
        "专利查找",
        "专利调研",
        # 专利分析(10个)
        "专利分析",
        "专利评估",
        "专利价值",
        "专利技术",
        "专利布局",
        "专利地图",
        "专利挖掘",
        "专利情报",
        "专利统计",
        "专利报告",
        # 专利申请(10个)
        "专利申请",
        "申请专利",
        "专利申请流程",
        "专利撰写",
        "专利文件",
        "专利代理",
        "专利申请书",
        "专利提交",
        "专利申请要求",
        "专利申请材料",
        # 专利法律(10个)
        "专利侵权",
        "专利诉讼",
        "专利法律",
        "专利权利",
        "专利保护",
        "专利纠纷",
        "专利无效",
        "专利许可",
        "专利转让",
        "专利有效期",
        # 专利策略(10个)
        "专利策略",
        "专利布局",
        "专利组合",
        "专利管理",
        "专利规划",
        "专利战略",
        "专利布局策略",
        "专利组合管理",
        "专利运营",
        "专利商业化",
    ],
    "legal": [
        # 法律检索(10个)
        "法律检索",
        "搜索法律",
        "法律查询",
        "查找法律",
        "法律搜索",
        "法律信息",
        "法律数据库",
        "法律文献",
        "法律查找",
        "法律调研",
        # 法律分析(10个)
        "法律分析",
        "法律咨询",
        "法律建议",
        "法律意见",
        "法律解读",
        "法律适用",
        "法律条款",
        "法律规定",
        "法律条文",
        "法律解释",
        # 案例检索(10个)
        "案例检索",
        "搜索案例",
        "查找案例",
        "案例查询",
        "案例搜索",
        "法律案例",
        "判例检索",
        "案例库",
        "案例研究",
        "案例参考",
        # 法律文书(10个)
        "法律文书",
        "合同审查",
        "法律文件",
        "法律合同",
        "法律条款",
        "起草合同",
        "审查合同",
        "法律协议",
        "法律起草",
        "文书撰写",
        # 法律问题(10个)
        "法律问题",
        "法律纠纷",
        "法律诉讼",
        "法律维权",
        "法律援助",
        "法律帮助",
        "法律咨询",
        "法律顾问",
        "法律解答",
        "法律服务",
    ],
    "nlp": [
        # 文本处理(10个)
        "文本分析",
        "文本处理",
        "文本挖掘",
        "文本提取",
        "文本识别",
        "文本分类",
        "文本标注",
        "文本聚类",
        "文本理解",
        "文本生成",
        # 语义分析(10个)
        "语义分析",
        "语义理解",
        "语义提取",
        "语义相似度",
        "语义搜索",
        "语义推理",
        "语义标注",
        "语义解析",
        "语义识别",
        "语义匹配",
        # 文档处理(10个)
        "文档解析",
        "文档分析",
        "文档提取",
        "文档摘要",
        "文档理解",
        "文档分类",
        "文档检索",
        "文档理解",
        "文档处理",
        "文档分析",
        # 内容摘要(10个)
        "文本摘要",
        "内容总结",
        "摘要提取",
        "关键信息",
        "要点提取",
        "自动摘要",
        "智能摘要",
        "内容概要",
        "文档摘要",
        "摘要生成",
        # 情感分析(10个)
        "情感分析",
        "情绪识别",
        "情感提取",
        "情感分类",
        "情感理解",
        "情绪分析",
        "情感检测",
        "情感判断",
        "情感识别",
        "情感计算",
    ],
    "knowledge_graph": [
        # 知识图谱(10个)
        "知识图谱",
        "图谱查询",
        "图谱分析",
        "图谱检索",
        "图谱搜索",
        "知识图谱查询",
        "知识图谱分析",
        "知识图谱检索",
        "知识图谱搜索",
        "知识图谱数据库",
        # 实体识别(10个)
        "实体识别",
        "实体抽取",
        "实体提取",
        "实体链接",
        "实体消歧",
        "命名实体识别",
        "实体关系",
        "实体类型",
        "实体标注",
        "实体分析",
        # 关系抽取(10个)
        "关系抽取",
        "关系提取",
        "关系识别",
        "关系分析",
        "关系推理",
        "实体关系",
        "关系类型",
        "关系分类",
        "关系抽取",
        "关系发现",
        # 知识推理(10个)
        "知识推理",
        "逻辑推理",
        "推理分析",
        "推理计算",
        "推理引擎",
        "智能推理",
        "自动推理",
        "推理系统",
        "推理模型",
        "推理算法",
        # 图谱可视化(10个)
        "图谱可视化",
        "知识图谱展示",
        "图谱展示",
        "图谱浏览",
        "图谱探索",
        "图谱导航",
        "图谱查看",
        "图谱呈现",
        "图谱界面",
        "图谱操作",
    ],
    "memory": [
        # 记忆存储(10个)
        "记住这个",
        "保存记忆",
        "存储信息",
        "记录信息",
        "保存信息",
        "记忆存储",
        "信息存储",
        "数据记忆",
        "内容记忆",
        "记忆保存",
        # 记忆检索(10个)
        "回忆一下",
        "查看记忆",
        "搜索记忆",
        "记忆查询",
        "记忆检索",
        "我的记忆",
        "记忆内容",
        "记忆搜索",
        "记忆查找",
        "记忆回顾",
        # 记忆管理(10个)
        "管理记忆",
        "删除记忆",
        "更新记忆",
        "修改记忆",
        "记忆编辑",
        "记忆管理",
        "记忆清理",
        "记忆整理",
        "记忆更新",
        "记忆维护",
        # 上下文记忆(10个)
        "记住上下文",
        "记住对话",
        "对话记忆",
        "上下文记忆",
        "会话记忆",
        "记忆上下文",
        "对话历史",
        "会话历史",
        "历史记录",
        "聊天记录",
        # 记忆查询(10个)
        "你记得吗",
        "还记得吗",
        "记得什么",
        "记录了什么",
        "保存了什么",
        "记忆查询",
        "记忆读取",
        "记忆获取",
        "记忆提取",
        "记忆回顾",
    ],
    "optimization": [
        # 性能优化(10个)
        "性能优化",
        "系统优化",
        "优化性能",
        "提升性能",
        "性能提升",
        "加速",
        "性能调优",
        "优化系统",
        "系统调优",
        "性能改进",
        # 资源优化(10个)
        "资源优化",
        "优化资源",
        "资源分配",
        "资源管理",
        "资源调度",
        "资源利用",
        "资源配置",
        "资源优化",
        "资源规划",
        "资源策略",
        # 决策优化(10个)
        "决策优化",
        "智能决策",
        "优化决策",
        "决策分析",
        "决策建议",
        "最优决策",
        "决策支持",
        "决策系统",
        "决策模型",
        "决策算法",
        # 流程优化(10个)
        "流程优化",
        "优化流程",
        "工作流优化",
        "业务流程",
        "流程改进",
        "流程管理",
        "流程分析",
        "流程设计",
        "流程重组",
        "流程自动化",
        # 效率提升(10个)
        "提升效率",
        "效率优化",
        "提高效率",
        "工作效率",
        "优化效率",
        "效率提升",
        "效率改进",
        "效率分析",
        "效率管理",
        "效率工具",
    ],
    "multimodal": [
        # 图像处理(10个)
        "图片分析",
        "图像识别",
        "图片理解",
        "图像处理",
        "图像分析",
        "看图",
        "识别图片",
        "图片描述",
        "图像理解",
        "视觉识别",
        # 语音处理(10个)
        "语音识别",
        "语音转文字",
        "语音分析",
        "语音理解",
        "语音处理",
        "听写",
        "语音输入",
        "语音转文本",
        "声音识别",
        "音频识别",
        # 视频处理(10个)
        "视频分析",
        "视频理解",
        "视频处理",
        "视频识别",
        "视频内容",
        "看视频",
        "视频描述",
        "视频摘要",
        "视频理解",
        "视频分析",
        # 多模态融合(10个)
        "多模态",
        "多模态融合",
        "图文理解",
        "音视频理解",
        "跨模态",
        "多模态分析",
        "多模态理解",
        "多模态处理",
        "多模态识别",
        "多模态搜索",
        # 视觉问答(10个)
        "看图问答",
        "图片问答",
        "视觉问答",
        "图像问答",
        "看图回答",
        "图片问题",
        "图像问题",
        "视觉问题",
        "图片提问",
        "图像提问",
    ],
    "agent_fusion": [
        # 智能体协作(10个)
        "智能体协作",
        "多智能体",
        "智能体协作",
        "agent协作",
        "智能体团队",
        "多agent",
        "agent团队",
        "智能体群",
        "智能体系统",
        "agent系统",
        # 智能体调度(10个)
        "智能体调度",
        "agent调度",
        "智能体分配",
        "agent分配",
        "智能体编排",
        "agent编排",
        "智能体管理",
        "agent管理",
        "智能体控制",
        "agent控制",
        # 融合推理(10个)
        "融合推理",
        "协同推理",
        "联合推理",
        "综合推理",
        "集成推理",
        "推理融合",
        "协同分析",
        "联合分析",
        "综合分析",
        "集成分析",
        # 任务协作(10个)
        "任务协作",
        "协同任务",
        "联合任务",
        "协作工作",
        "团队任务",
        "任务协调",
        "任务分配",
        "任务协同",
        "协作完成",
        "联合完成",
        # 智能体通信(10个)
        "智能体通信",
        "agent通信",
        "智能体对话",
        "agent对话",
        "智能体交互",
        "agent交互",
        "智能体消息",
        "agent消息",
        "智能体协议",
        "agent协议",
    ],
    "autonomous": [
        # 自主学习(10个)
        "自主学习",
        "自动学习",
        "智能学习",
        "机器学习",
        "深度学习",
        "学习系统",
        "学习模型",
        "学习算法",
        "学习框架",
        "学习平台",
        # 自主决策(10个)
        "自主决策",
        "自动决策",
        "智能决策",
        "自主判断",
        "自动判断",
        "自主系统",
        "自主agent",
        "自主控制",
        "自主管理",
        "自主运行",
        # 自主适应(10个)
        "自主适应",
        "自动适应",
        "智能适应",
        "自适应",
        "环境适应",
        "适应系统",
        "适应算法",
        "适应模型",
        "适应机制",
        "适应策略",
        # 自主优化(10个)
        "自主优化",
        "自动优化",
        "智能优化",
        "自我优化",
        "持续优化",
        "优化学习",
        "优化改进",
        "优化提升",
        "优化调整",
        "优化更新",
        # 自主监控(10个)
        "自主监控",
        "自动监控",
        "智能监控",
        "自我监控",
        "持续监控",
        "监控系统",
        "监控模型",
        "监控算法",
        "监控框架",
        "监控平台",
    ],
    "enterprise": [
        # 企业管理(10个)
        "企业管理",
        "公司管理",
        "组织管理",
        "企业管理系统",
        "企业管理平台",
        "企业管理软件",
        "企业管理工具",
        "企业管理方案",
        "企业管理服务",
        "企业管理咨询",
        # 多租户(10个)
        "多租户",
        "租户管理",
        "租户隔离",
        "租户配置",
        "租户数据",
        "租户权限",
        "租户设置",
        "租户系统",
        "租户平台",
        "租户架构",
        # 企业协作(10个)
        "企业协作",
        "团队协作",
        "部门协作",
        "协作系统",
        "协作平台",
        "协作工具",
        "协作软件",
        "协作方案",
        "协作服务",
        "协作管理",
        # 企业数据(10个)
        "企业数据",
        "公司数据",
        "数据管理",
        "数据治理",
        "数据安全",
        "数据保护",
        "数据隐私",
        "数据合规",
        "数据存储",
        "数据处理",
        # 企业应用(10个)
        "企业应用",
        "企业软件",
        "企业系统",
        "企业平台",
        "企业服务",
        "企业解决方案",
        "企业信息化",
        "企业数字化",
        "企业智能化",
        "企业云化",
    ],
    "quantization": [
        # 模型量化(10个)
        "模型量化",
        "量化训练",
        "量化推理",
        "模型压缩",
        "模型优化",
        "量化算法",
        "量化方法",
        "量化技术",
        "量化工具",
        "量化框架",
        # 精度优化(10个)
        "精度优化",
        "精度提升",
        "精度调优",
        "精度分析",
        "精度评估",
        "精度测试",
        "精度验证",
        "精度比较",
        "精度选择",
        "精度配置",
        # 性能加速(10个)
        "性能加速",
        "推理加速",
        "训练加速",
        "加速优化",
        "加速技术",
        "加速算法",
        "加速方法",
        "加速工具",
        "加速框架",
        "加速方案",
        # 压缩优化(10个)
        "压缩优化",
        "模型压缩",
        "压缩算法",
        "压缩方法",
        "压缩技术",
        "压缩工具",
        "压缩框架",
        "压缩方案",
        "压缩策略",
        "压缩比",
        # 量化部署(10个)
        "量化部署",
        "部署优化",
        "部署加速",
        "部署方案",
        "部署策略",
        "部署工具",
        "部署平台",
        "部署框架",
        "部署系统",
        "部署环境",
    ],
    "federated": [
        # 联邦学习(10个)
        "联邦学习",
        "分布式学习",
        "协同学习",
        "隐私保护学习",
        "联邦训练",
        "联邦算法",
        "联邦模型",
        "联邦框架",
        "联邦平台",
        "联邦系统",
        # 分布式训练(10个)
        "分布式训练",
        "分布式计算",
        "分布式系统",
        "分布式架构",
        "分布式部署",
        "分布式算法",
        "分布式优化",
        "分布式推理",
        "分布式存储",
        "分布式通信",
        # 隐私保护(10个)
        "隐私保护",
        "数据隐私",
        "隐私计算",
        "隐私增强",
        "隐私技术",
        "隐私算法",
        "隐私方案",
        "隐私框架",
        "隐私平台",
        "隐私系统",
        # 联邦推理(10个)
        "联邦推理",
        "分布式推理",
        "协同推理",
        "联合推理",
        "隐私推理",
        "推理聚合",
        "推理融合",
        "推理优化",
        "推理加速",
        "推理部署",
        # 联邦协作(10个)
        "联邦协作",
        "协同协作",
        "联合协作",
        "协作训练",
        "协作学习",
        "协作优化",
        "协作聚合",
        "协作同步",
        "协作通信",
        "协作管理",
    ],
    "xiaochen": [
        # 小晨智能体(10个)
        "小晨",
        "xiaochen",
        "小晨智能体",
        "小晨助手",
        "小晨服务",
        "小晨功能",
        "小晨能力",
        "小晨系统",
        "小晨平台",
        "小晨工具",
        # 小晨对话(10个)
        "小晨对话",
        "和小晨聊天",
        "小晨聊天",
        "小晨交流",
        "小晨沟通",
        "小晨问答",
        "小晨咨询",
        "小晨回复",
        "小晨应答",
        "小晨响应",
        # 小晨分析(10个)
        "小晨分析",
        "小晨诊断",
        "小晨评估",
        "小晨检测",
        "小晨监控",
        "小晨优化",
        "小晨改进",
        "小晨提升",
        "小晨建议",
        "小晨推荐",
        # 小晨协作(10个)
        "小晨协作",
        "小晨配合",
        "小晨协同",
        "小晨联动",
        "小晨集成",
        "小晨融合",
        "小晨互通",
        "小晨连接",
        "小晨对接",
        "小晨合作",
        # 小晨管理(10个)
        "小晨管理",
        "小晨配置",
        "小晨设置",
        "小晨控制",
        "小晨调度",
        "小晨监控",
        "小晨运维",
        "小晨部署",
        "小晨维护",
        "小晨更新",
    ],
}

# ==================== 特征提取(修复版)====================


def extract_flat_features(text: str) -> dict[str, float]:
    """
    提取扁平化数值特征
    修复TypeError: 所有特征值都是数值类型(int/float)

    Returns:
        dict[str, float]: 扁平化的数值特征字典
    """
    words = list(jieba.cut(text))
    word_count = len(words)
    char_count = len(text)

    # 基础特征(数值)
    features: dict[str, float] = {
        "word_count": float(word_count),
        "char_count": float(char_count),
        "avg_word_length": float(char_count / max(word_count, 1)),
        "has_question": (
            1.0 if any(q in text for q in ["?", "?", "什么", "怎么", "如何", "为什么"]) else 0.0
        ),
        "has_command": (
            1.0 if any(c in text for c in ["启动", "停止", "开始", "结束", "执行", "运行"]) else 0.0
        ),
        "urgency": 1.0 if any(u in text for u in ["紧急", "马上", "立即", "快", "急"]) else 0.0,
    }

    # 能力关键词特征(数值分数)
    capability_keywords = {
        # 基础能力关键词
        "daily_chat_keywords": [
            "你好",
            "心情",
            "聊天",
            "无聊",
            "放松",
            "天气",
            "新闻",
            "娱乐",
            "搜索",
        ],
        "platform_controller_keywords": [
            "启动",
            "停止",
            "重启",
            "系统",
            "服务",
            "监控",
            "配置",
            "部署",
            "运维",
        ],
        "coding_assistant_keywords": [
            "代码",
            "程序",
            "API",
            "函数",
            "算法",
            "bug",
            "调试",
            "优化",
            "性能",
        ],
        "life_assistant_keywords": [
            "日程",
            "提醒",
            "计划",
            "时间",
            "安排",
            "备忘",
            "待办",
            "助理",
            "助手",
        ],
        # 专业能力关键词
        "patent_keywords": [
            "专利",
            "申请专利",
            "专利检索",
            "专利分析",
            "专利侵权",
            "专利法律",
            "专利申请",
        ],
        "legal_keywords": [
            "法律",
            "法规",
            "诉讼",
            "合同",
            "法律咨询",
            "法律文书",
            "案例分析",
            "合规",
        ],
        # 高级能力关键词
        "nlp_keywords": ["文本", "语义", "情感", "摘要", "分析", "提取", "理解", "识别", "分类"],
        "knowledge_graph_keywords": [
            "知识图谱",
            "实体",
            "关系",
            "图谱",
            "推理",
            "链接",
            "节点",
            "可视化",
        ],
        "memory_keywords": ["记住", "回忆", "保存", "记忆", "存储", "记录", "历史", "上下文"],
        "optimization_keywords": ["优化", "提升", "改进", "效率", "性能", "决策", "资源", "流程"],
        # Phase 3能力关键词
        "multimodal_keywords": ["图片", "图像", "语音", "视频", "视觉", "音频", "多模态", "看图"],
        "agent_fusion_keywords": [
            "智能体",
            "agent",
            "协作",
            "融合",
            "多智能体",
            "协同",
            "编排",
            "调度",
        ],
        "autonomous_keywords": ["自主", "自动", "学习", "适应", "自我", "智能", "独立", "自动化"],
        # Phase 4能力关键词
        "enterprise_keywords": ["企业", "公司", "租户", "组织", "多租户", "管理", "协作", "数据"],
        "quantization_keywords": ["量化", "压缩", "精度", "加速", "模型", "推理", "训练", "优化"],
        "federated_keywords": ["联邦", "分布式", "隐私", "协同", "联合", "隐私保护", "协作学习"],
        # 智能体能力关键词
        "xiaochen_keywords": ["小晨", "xiaochen", "小晨智能体", "小晨助手"],
    }

    # 计算每个能力的关键词匹配分数(数值)
    for feature_name, keywords in capability_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        features[feature_name] = float(score)

    return features


# ==================== 训练主函数 ====================


def train_gateway_capability_selector() -> Any:
    """
    训练网关能力选择器

    Returns:
        float: 模型准确率
    """
    logger.info("🚀 开始训练网关能力选择器...")
    logger.info("=" * 60)

    # 1. 准备训练数据
    logger.info("📚 准备训练数据...")

    training_data = []
    for capability, texts in BALANCED_TRAINING_DATA.items():
        for text in texts:
            training_data.append(
                {"text": text, "capability": capability, "features": extract_flat_features(text)}
            )

    logger.info(f"✅ 训练数据准备完成: {len(training_data)}条样本")

    # 验证数据分布
    capability_counts = {}
    for data in training_data:
        cap = data["capability"]
        capability_counts[cap] = capability_counts.get(cap, 0) + 1

    logger.info("📊 数据分布:")
    for cap, count in sorted(capability_counts.items()):
        logger.info(f"  {cap}: {count}条")

    # 2. 准备特征和标签
    logger.info("\n🔧 特征工程...")

    X_text = [data["text"] for data in training_data]
    y_capabilities = [data["capability"] for data in training_data]

    # 提取特征为列表
    X_features = [data["features"] for data in training_data]

    # 确保所有特征都是数值类型
    logger.info("验证特征类型...")
    for _i, features in enumerate(X_features[:5]):  # 检查前5个
        for key, value in features.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"特征 {key} 的值 {value} 不是数值类型 (类型: {type(value)})")
    logger.info("✅ 所有特征都是数值类型")

    # 3. 文本向量化
    logger.info("📝 文本向量化...")
    vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 3), min_df=1, max_df=0.95)

    X_text_vec = vectorizer.fit_transform(X_text).toarray()
    logger.info(f"✅ 文本特征维度: {X_text_vec.shape[1]}")

    # 4. 特征标准化
    logger.info("⚙️ 特征标准化...")

    # 将特征字典转换为二维数组
    feature_keys = list(X_features[0].keys())
    X_features_array = np.array([[features[k] for k in feature_keys] for features in X_features])

    scaler = StandardScaler()
    X_features_scaled = scaler.fit_transform(X_features_array)
    logger.info(f"✅ 上下文特征维度: {X_features_scaled.shape[1]}")

    # 5. 特征组合
    logger.info("🔗 特征组合...")
    X_combined = np.hstack([X_text_vec, X_features_scaled])
    logger.info(f"✅ 组合特征维度: {X_combined.shape[1]}")

    # 6. 标签编码
    logger.info("🏷️ 标签编码...")
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y_capabilities)
    logger.info(f"✅ 标签数量: {len(label_encoder.classes_)}")

    # 7. 划分训练集和测试集
    logger.info("📂 划分数据集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_combined,
        y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded,  # 分层采样确保类别平衡
    )
    logger.info(f"✅ 训练集: {X_train.shape[0]}条, 测试集: {X_test.shape[0]}条")

    # 8. 训练模型
    logger.info("\n🎯 训练模型...")
    logger.info("=" * 60)

    model = GradientBoostingClassifier(
        n_estimators=300,
        learning_rate=0.1,
        max_depth=6,
        min_samples_split=5,
        min_samples_leaf=2,
        subsample=0.8,
        random_state=42,
        verbose=1,
    )

    model.fit(X_train, y_train)
    logger.info("✅ 模型训练完成")

    # 9. 评估模型
    logger.info("\n📊 模型评估...")
    logger.info("=" * 60)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    logger.info(f"🎯 整体准确率: {accuracy:.4f} ({accuracy * 100:.2f}%)")

    # 详细分类报告
    logger.info("\n📋 详细分类报告:")
    report = classification_report(
        y_test, y_pred, target_names=label_encoder.classes_, zero_division=0
    )
    logger.info("\n" + report)

    # 10. 保存模型
    logger.info("\n💾 保存模型...")
    logger.info("=" * 60)

    model_dir = "models/intelligent_tool_selector"
    os.makedirs(model_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = os.path.join(model_dir, f"capability_selector_{timestamp}.pkl")
    latest_path = os.path.join(model_dir, "latest_capability_selector.pkl")

    model_data = {
        "model": model,
        "vectorizer": vectorizer,
        "scaler": scaler,
        "label_encoder": label_encoder,
        "feature_keys": feature_keys,
        "capabilities": GATEWAY_CAPABILITIES,
        "accuracy": accuracy,
        "timestamp": timestamp,
    }

    # 保存带时间戳的模型
    with open(model_path, "wb") as f:
        import joblib

        joblib.dump(model_data, f)

    # 保存最新模型
    with open(latest_path, "wb") as f:
        import joblib

        joblib.dump(model_data, f)

    logger.info(f"✅ 模型已保存: {model_path}")
    logger.info(f"✅ 最新模型: {latest_path}")

    # 11. 结果总结
    logger.info("\n" + "=" * 60)
    logger.info("🎉 训练完成!")
    logger.info("=" * 60)

    if accuracy >= 0.95:
        logger.info("🏆 模型准确率达到95%+目标!性能优秀!")
    elif accuracy >= 0.90:
        logger.info("👍 模型准确率达到90%+,性能良好!")
    elif accuracy >= 0.80:
        logger.info("📈 模型准确率达到80%+,可以部署测试!")
    else:
        logger.info(f"⚠️ 当前准确率: {accuracy:.4f},建议继续优化")

    logger.info("\n📊 训练数据统计:")
    logger.info(f"  总样本数: {len(training_data)}")
    logger.info(f"  能力数量: {len(GATEWAY_CAPABILITIES)}")
    logger.info(f"  特征维度: {X_combined.shape[1]}")
    logger.info(f"  准确率: {accuracy:.4f}")

    return accuracy


# ==================== 测试函数 ====================


def test_capability_selector() -> Any:
    """测试能力选择器"""
    logger.info("\n🧪 测试能力选择器...")
    logger.info("=" * 60)

    # 加载模型
    model_path = "models/intelligent_tool_selector/latest_capability_selector.pkl"

    if not os.path.exists(model_path):
        logger.error(f"❌ 模型文件不存在: {model_path}")
        logger.info("请先运行训练: python train_gateway_capability_selector.py")
        return

    import joblib

    with open(model_path, "rb") as f:
        model_data = joblib.load(f)

    model = model_data["model"]
    vectorizer = model_data["vectorizer"]
    scaler = model_data["scaler"]
    label_encoder = model_data["label_encoder"]
    feature_keys = model_data["feature_keys"]

    # 测试案例
    test_cases = [
        ("你好,今天心情不错", "daily_chat"),
        ("启动系统监控服务", "platform_controller"),
        ("帮我分析这段Python代码", "coding_assistant"),
        ("提醒我明天开会", "life_assistant"),
        ("搜索专利信息", "patent"),
        ("查询法律规定", "legal"),
        ("分析这段文本的情感", "nlp"),
        ("查询知识图谱", "knowledge_graph"),
        ("记住这个信息", "memory"),
        ("优化系统性能", "optimization"),
        ("识别这张图片", "multimodal"),
        ("启动多智能体协作", "agent_fusion"),
        ("自主学习新知识", "autonomous"),
        ("企业管理系统", "enterprise"),
        ("模型量化优化", "quantization"),
        ("联邦学习训练", "federated"),
        ("小晨智能体对话", "xiaochen"),
    ]

    logger.info("📝 测试结果:")
    correct = 0

    for text, expected_capability in test_cases:
        # 提取特征
        features = extract_flat_features(text)
        features_array = np.array([[features[k] for k in feature_keys]])

        # 文本向量化
        text_vec = vectorizer.transform([text]).toarray()

        # 特征缩放
        features_scaled = scaler.transform(features_array)

        # 组合特征
        combined = np.hstack([text_vec, features_scaled])

        # 预测
        pred_proba = model.predict_proba(combined)[0]
        pred_idx = pred_proba.argmax()
        predicted_capability = label_encoder.classes_[pred_idx]
        confidence = pred_proba[pred_idx]

        is_correct = "✅" if predicted_capability == expected_capability else "❌"
        if predicted_capability == expected_capability:
            correct += 1

        logger.info(f"{is_correct} 输入: {text}")
        logger.info(f"   预期: {expected_capability}")
        logger.info(f"   预测: {predicted_capability} (置信度: {confidence:.4f})")
        logger.info("")

    accuracy = correct / len(test_cases)
    logger.info("=" * 60)
    logger.info(f"🎯 测试准确率: {accuracy:.4f} ({accuracy * 100:.2f}%)")


# ==================== 主函数 ====================


def main() -> None:
    """主函数"""
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "test":
            test_capability_selector()
            return
        elif mode == "train":
            pass  # 继续训练
        else:
            logger.error(f"❌ 未知模式: {mode}")
            logger.info("用法: python train_gateway_capability_selector.py [train|test]")
            return

    # 训练模型
    try:
        accuracy = train_gateway_capability_selector()

        # 如果准确率 >= 80%,自动运行测试
        if accuracy >= 0.80:
            logger.info("\n" + "=" * 60)
            logger.info("🧪 准确率达标,自动运行测试...")
            logger.info("=" * 60)
            test_capability_selector()

    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
