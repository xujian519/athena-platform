/**
 * 权利要求生成工具
 * 用于生成保护范围合理、层次分明的权利要求书
 */

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import { readFile } from "fs/promises";
import { join } from "path";

export const generateClaimsTool: Tool = {
  name: "generate_claims",
  description: `基于技术交底书和发明理解，生成保护范围合理、层次分明的权利要求书，包括：
- 独立权利要求（保护范围最宽）
- 从属权利要求（多层次保护）
- 10项左右的完整权利要求体系

输出符合《专利审查指南》要求的权利要求书。`,
  inputSchema: {
    type: "object",
    properties: {
      invention_understanding: {
        type: "object",
        description: "发明理解结果（来自understand_disclosure工具）",
        properties: {
          basic_info: { type: "object" },
          core_solution: { type: "object" },
          protection_suggestions: { type: "object" },
        },
      },
      claim_type: {
        type: "string",
        enum: ["product", "method", "system", "use"],
        description:
          "权利要求类型：product(产品)、method(方法)、system(系统)、use(用途)",
      },
      protection_strategy: {
        type: "string",
        enum: ["broad", "balanced", "narrow"],
        description: "保护策略：broad(宽泛)、balanced(平衡)、narrow(窄)",
      },
      claim_count: {
        type: "number",
        description: "权利要求数量（5-15项）",
        minimum: 5,
        maximum: 15,
        default: 10,
      },
    },
    required: ["invention_understanding"],
  },
};

interface GenerateClaimsInput {
  invention_understanding: {
    basic_info: any;
    core_solution: any;
    protection_suggestions: any;
  };
  claim_type?: "product" | "method" | "system" | "use";
  protection_strategy?: "broad" | "balanced" | "narrow";
  claim_count?: number;
}

interface Claim {
  number: number;
  type: "independent" | "dependent";
  text: string;
  depends_on?: number[];
}

interface GenerateClaimsOutput {
  claims: Claim[];
  full_text: string;
  protection_analysis: {
    scope: string;
    key_features: string[];
    fallback_positions: string[];
  };
}

/**
 * 执行权利要求生成
 */
export async function executeGenerateClaims(
  input: GenerateClaimsInput,
): Promise<GenerateClaimsOutput> {
  const promptPath = join(process.cwd(), "src/prompts/claim-generation.md");
  const promptTemplate = await readFile(promptPath, "utf-8");

  const fullPrompt = `${promptTemplate}

## 发明理解信息

\`\`\`json
${JSON.stringify(input.invention_understanding, null, 2)}
\`\`\`

## 撰写要求

权利要求类型：${input.claim_type || "product"}
保护策略：${input.protection_strategy || "balanced"}
权利要求数量：${input.claim_count || 10}

请根据上述信息，生成符合规范的权利要求书。`;

  // 这里应该调用本地LLM API
  // 由于不调用外部API，这里返回一个占位符结构
  // 实际使用时需要集成本地LLM

  const claims: Claim[] = [
    {
      number: 1,
      type: "independent",
      text: "一种[发明名称]，其特征在于，包括：[必要技术特征]；",
    },
    {
      number: 2,
      type: "dependent",
      text: "根据权利要求1所述的[发明名称]，其特征在于，[进一步限定]。",
      depends_on: [1],
    },
    {
      number: 3,
      type: "dependent",
      text: "根据权利要求1或2所述的[发明名称]，其特征在于，[进一步限定]。",
      depends_on: [1, 2],
    },
  ];

  const result: GenerateClaimsOutput = {
    claims,
    full_text: `## 权利要求书

1. 一种[发明名称]，其特征在于，包括：
   [必要技术特征1]；
   [必要技术特征2]。

2. 根据权利要求1所述的[发明名称]，其特征在于，[进一步限定]。

3. 根据权利要求1或2所述的[发明名称]，其特征在于，[进一步限定]。`,
    protection_analysis: {
      scope: "保护范围待分析",
      key_features: ["核心技术特征1", "核心技术特征2"],
      fallback_positions: ["退守位置1", "退守位置2"],
    },
  };

  return result;
}

export const draftAbstractTool: Tool = {
  name: "draft_abstract",
  description: `基于专利说明书，生成符合要求的专利摘要（150-300字），包括：
- 发明名称
- 技术领域
- 技术方案要点
- 主要用途

输出简洁、准确的摘要文本。`,
  inputSchema: {
    type: "object",
    properties: {
      specification: {
        type: "object",
        description: "说明书内容",
        properties: {
          technical_field: { type: "string" },
          invention_content: { type: "object" },
        },
      },
      abstract_type: {
        type: "string",
        enum: ["standard", "detailed", "brief"],
        description: "摘要类型：standard(标准)、detailed(详细)、brief(简略)",
      },
    },
    required: ["specification"],
  },
};

/**
 * 执行摘要生成
 */
export async function executeDraftAbstract(input: any): Promise<any> {
  return {
    title: "发明名称待生成",
    abstract: "摘要内容待生成（150-300字）",
    keywords: ["关键词1", "关键词2", "关键词3"],
  };
}
