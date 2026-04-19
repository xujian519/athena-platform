/**
 * 交底书理解工具
 * 用于深入分析技术交底书，提取发明的核心要素
 */

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import { readFile } from "fs/promises";
import { join } from "path";

export const understandDisclosureTool: Tool = {
  name: "understand_disclosure",
  description: `深入分析技术交底书，提取发明的核心要素，包括：
- 发明基本信息（名称、技术领域、应用场景）
- 核心技术方案（技术问题、技术方案、技术效果）
- 现有技术对比
- 关键术语定义
- 实施例梳理
- 保护范围建议

输出结构化的发明理解结果，为后续专利撰写提供基础。`,
  inputSchema: {
    type: "object",
    properties: {
      disclosure_text: {
        type: "string",
        description: "技术交底书全文内容",
      },
      disclosure_type: {
        type: "string",
        enum: ["technical", "brief", "detailed"],
        description:
          "交底书类型：technical(技术文档)、brief(简报)、detailed(详细交底书)",
      },
      focus_areas: {
        type: "array",
        items: {
          type: "string",
          enum: ["innovation", "implementation", "comparison", "all"],
        },
        description:
          "重点关注领域：innovation(创新点)、implementation(实施方式)、comparison(对比分析)、all(全部)",
      },
    },
    required: ["disclosure_text"],
  },
};

interface UnderstandDisclosureInput {
  disclosure_text: string;
  disclosure_type?: "technical" | "brief" | "detailed";
  focus_areas?: string[];
}

interface UnderstandDisclosureOutput {
  basic_info: {
    title: string;
    technical_field: string;
    application_scenario: string;
  };
  core_solution: {
    technical_problem: string;
    technical_solution: {
      architecture: string;
      key_features: string[];
      implementation_path: string;
      innovations: string[];
    };
    technical_effects: string[];
  };
  prior_art_comparison: {
    current_status: string;
    differences: string[];
    improvements: string[];
  };
  terminology: Record<string, string>;
  embodiments: string[];
  protection_suggestions: {
    core_protection: string[];
    extension_directions: string[];
    circumvention_risks: string[];
  };
}

/**
 * 执行交底书理解
 */
export async function executeUnderstandDisclosure(
  input: UnderstandDisclosureInput,
): Promise<UnderstandDisclosureOutput> {
  const promptPath = join(
    process.cwd(),
    "src/prompts/disclosure-understanding.md",
  );
  const promptTemplate = await readFile(promptPath, "utf-8");

  const fullPrompt = `${promptTemplate}

## 技术交底书内容

${input.disclosure_text}

## 分析要求

交底书类型：${input.disclosure_type || "detailed"}
重点关注：${input.focus_areas?.join(", ") || "all"}

请按照上述要求，对技术交底书进行全面分析，并以JSON格式输出结果。`;

  // 这里应该调用本地LLM API
  // 由于不调用外部API，这里返回一个占位符结构
  // 实际使用时需要集成本地LLM

  const result: UnderstandDisclosureOutput = {
    basic_info: {
      title: "待分析的发明名称",
      technical_field: "待确定的技术领域",
      application_scenario: "待分析的应用场景",
    },
    core_solution: {
      technical_problem: "待提取的技术问题",
      technical_solution: {
        architecture: "待分析的整体架构",
        key_features: ["待提取的特征1", "待提取的特征2"],
        implementation_path: "待分析的实现路径",
        innovations: ["待识别的创新点1", "待识别的创新点2"],
      },
      technical_effects: ["待分析的效果1", "待分析的效果2", "待分析的效果3"],
    },
    prior_art_comparison: {
      current_status: "待分析的现有技术现状",
      differences: ["待分析的差异1", "待分析的差异2"],
      improvements: ["待分析的改进1", "待分析的改进2"],
    },
    terminology: {
      术语1: "定义1",
      术语2: "定义2",
    },
    embodiments: ["实施例1待提取", "实施例2待提取"],
    protection_suggestions: {
      core_protection: ["核心保护点1", "核心保护点2"],
      extension_directions: ["扩展方向1", "扩展方向2"],
      circumvention_risks: ["规避风险1", "规避风险2"],
    },
  };

  return result;
}
