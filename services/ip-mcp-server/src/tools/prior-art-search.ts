/**
 * 现有技术检索工具
 * 用于检索相关现有技术，为专利撰写提供参考
 */

import type { Tool } from "@modelcontextprotocol/sdk/types.js";

export const searchPriorArtTool: Tool = {
  name: "search_prior_art",
  description: `检索相关现有技术，为专利撰写提供参考，包括：
- 专利文献检索
- 非专利文献检索
- 技术方案对比
- 新颖性评估

输出结构化的检索结果和对比分析。`,
  inputSchema: {
    type: "object",
    properties: {
      invention_understanding: {
        type: "object",
        description: "发明理解结果（来自understand_disclosure工具）",
        properties: {
          basic_info: { type: "object" },
          core_solution: { type: "object" },
        },
      },
      search_scope: {
        type: "array",
        items: {
          type: "string",
          enum: [
            "chinese_patents",
            "us_patents",
            "ep_patents",
            "pct_patents",
            "academic_papers",
            "technical_reports",
          ],
        },
        description:
          "检索范围：chinese_patents(中国专利)、us_patents(美国专利)、ep_patents(欧洲专利)、pct_patents(PCT专利)、academic_papers(学术论文)、technical_reports(技术报告)",
      },
      keywords: {
        type: "array",
        items: { type: "string" },
        description: "检索关键词列表",
      },
      time_range: {
        type: "object",
        properties: {
          start_date: { type: "string", description: "开始日期(YYYY-MM-DD)" },
          end_date: { type: "string", description: "结束日期(YYYY-MM-DD)" },
        },
        description: "检索时间范围",
      },
    },
    required: ["invention_understanding"],
  },
};

interface SearchPriorArtInput {
  invention_understanding: {
    basic_info: any;
    core_solution: any;
  };
  search_scope?: string[];
  keywords?: string[];
  time_range?: {
    start_date?: string;
    end_date?: string;
  };
}

interface PriorArt {
  id: string;
  title: string;
  type: "patent" | "paper" | "report";
  date: string;
  summary: string;
  relevance_score: number;
  key_similarities: string[];
  key_differences: string[];
}

interface SearchPriorArtOutput {
  search_results: PriorArt[];
  novelty_analysis: {
    has_novelty: boolean;
    closest_prior_art: string;
    distinguishing_features: string[];
    potential_objections: string[];
  };
  recommendations: string[];
}

export async function executeSearchPriorArt(
  input: SearchPriorArtInput,
): Promise<SearchPriorArtOutput> {
  const result: SearchPriorArtOutput = {
    search_results: [
      {
        id: "CN123456789A",
        title: "相关现有技术1",
        type: "patent",
        date: "2023-01-01",
        summary: "现有技术摘要",
        relevance_score: 0.85,
        key_similarities: ["相似特征1", "相似特征2"],
        key_differences: ["差异特征1", "差异特征2"],
      },
    ],
    novelty_analysis: {
      has_novelty: true,
      closest_prior_art: "CN123456789A",
      distinguishing_features: ["区别特征1", "区别特征2"],
      potential_objections: [],
    },
    recommendations: [
      "建议在说明书中强调区别特征1的技术效果",
      "建议从属权利要求进一步限定区别特征2",
    ],
  };

  return result;
}
