/**
 * IP智能体MCP Server类型定义
 * 定义专利分析和撰写所需的核心数据结构
 */

// ==================== 发明理解相关类型 ====================

/**
 * 技术特征
 */
export interface TechnicalFeature {
  /** 特征名称 */
  name: string;
  /** 特征描述 */
  description: string;
  /** 是否为必要特征 */
  isEssential: boolean;
}

/**
 * 发明理解结果
 */
export interface InventionUnderstanding {
  /** 发明标题 */
  title: string;
  /** 技术领域 */
  technicalField: string;
  /** 核心创新点 */
  coreInnovation: string;
  /** 解决的技术问题 */
  technicalProblem: string;
  /** 技术方案 */
  technicalSolution: string;
  /** 技术效果列表 */
  technicalEffects: string[];
  /** 必要技术特征 */
  essentialFeatures: TechnicalFeature[];
  /** 可选技术特征 */
  optionalFeatures: TechnicalFeature[];
  /** 置信度评分 (0-1) */
  confidenceScore: number;
}

// ==================== 权利要求相关类型 ====================

/**
 * 权利要求类型
 */
export type ClaimType = "independent" | "dependent";

/**
 * 权利要求
 */
export interface Claim {
  /** 权利要求编号 */
  number: number;
  /** 权利要求类型 */
  type: ClaimType;
  /** 权利要求内容 */
  claims: string[];
  /** 依赖的权利要求编号（从属权利要求） */
  dependsOn?: number[];
}

/**
 * 权利要求修改
 */
export interface ClaimModification {
  /** 原始权利要求 */
  originalClaim: string;
  /** 修改后的权利要求 */
  modifiedClaim: string;
  /** 修改依据 */
  basis: string;
}

// ==================== 说明书相关类型 ====================

/**
 * 说明书草稿
 */
export interface SpecificationDraft {
  /** 技术领域 */
  technicalField: string;
  /** 背景技术 */
  background: string;
  /** 发明内容 */
  inventionContent: string;
  /** 具体实施方式 */
  detailedDescription: string;
  /** 附图说明（可选） */
  drawings?: string[];
}

// ==================== 审查意见答复相关类型 ====================

/**
 * 审查意见答复
 */
export interface OAResponse {
  /** 驳回类型 */
  rejectionType: string;
  /** 审查员论点 */
  examinerArguments: string[];
  /** 申请人论点 */
  applicantArguments: string[];
  /** 权利要求修改列表 */
  claimModifications: ClaimModification[];
}

// ==================== 检索相关类型 ====================

/**
 * 检索条件
 */
export interface SearchQuery {
  /** 检索关键词 */
  keywords: string[];
  /** 技术领域（可选） */
  technicalField?: string;
  /** 申请人（可选） */
  applicant?: string;
  /** 发明人（可选） */
  inventor?: string;
  /** 申请日期范围（可选） */
  dateRange?: {
    start: string;
    end: string;
  };
  /** 检索数据库（可选） */
  databases?: string[];
}

/**
 * 检索结果
 */
export interface SearchResult {
  /** 专利号 */
  patentNumber: string;
  /** 标题 */
  title: string;
  /** 摘要 */
  abstract: string;
  /** 申请人 */
  applicant: string;
  /** 申请日 */
  filingDate: string;
  /** 公开日 */
  publicationDate: string;
  /** 相似度得分 (0-1) */
  similarityScore: number;
  /** 法律状态（可选） */
  legalStatus?: string;
}

// ==================== 知识库相关类型 ====================

/**
 * 法条画像
 */
export interface LegalProvision {
  /** 法条编号 */
  code: string;
  /** 法条标题 */
  title: string;
  /** 法条内容 */
  content: string;
  /** 适用场景 */
  applicableScenarios: string[];
  /** 相关案例 */
  relatedCases: string[];
  /** 向量嵌入（内部使用） */
  embedding?: number[];
}

/**
 * 知识库条目
 */
export interface KnowledgeEntry {
  /** 条目ID */
  id: string;
  /** 条目标题 */
  title: string;
  /** 条目内容 */
  content: string;
  /** 条目类型 */
  type: "patent" | "legal" | "technical" | "case";
  /** 元数据 */
  metadata: Record<string, unknown>;
  /** 向量嵌入（内部使用） */
  embedding?: number[];
}

// ==================== LLM服务相关类型 ====================

/**
 * LLM调用选项
 */
export interface LLMOptions {
  /** 模型名称 */
  model?: string;
  /** 温度参数 (0-1) */
  temperature?: number;
  /** 最大token数 */
  maxTokens?: number;
  /** 是否流式响应 */
  stream?: boolean;
  /** 系统提示词 */
  systemPrompt?: string;
}

/**
 * LLM响应
 */
export interface LLMResponse {
  /** 响应文本 */
  text: string;
  /** 使用的token数 */
  tokensUsed?: number;
  /** 模型名称 */
  model: string;
  /** 完成原因 */
  finishReason: string;
}

// ==================== MCP工具相关类型 ====================

/**
 * MCP工具定义
 */
export interface MCPToolDefinition {
  /** 工具名称 */
  name: string;
  /** 工具描述 */
  description: string;
  /** 输入参数schema */
  inputSchema: Record<string, unknown>;
}

/**
 * MCP工具调用结果
 */
export interface MCPToolResult {
  /** 是否成功 */
  success: boolean;
  /** 结果内容 */
  content: string | Record<string, unknown>;
  /** 错误信息（如果失败） */
  error?: string;
}
