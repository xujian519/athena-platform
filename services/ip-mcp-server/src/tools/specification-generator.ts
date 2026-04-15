/**
 * 说明书生成工具
 * 用于生成符合《专利审查指南》要求的专利说明书
 */

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import { readFile } from "fs/promises";
import { join } from "path";

export const draftSpecificationTool: Tool = {
  name: "draft_specification",
  description: `基于技术交底书和发明理解，生成符合《专利审查指南》要求的专利说明书，包括：
- 技术领域（50-100字）
- 背景技术（300-500字）
- 发明内容（800-1500字）
- 具体实施方式（1500-3000字）

输出标准格式的说明书文本，可直接用于专利申请。`,
  inputSchema: {
    type: "object",
    properties: {
      invention_understanding: {
        type: "object",
        description: "发明理解结果（来自understand_disclosure工具）",
        properties: {
          basic_info: { type: "object" },
          core_solution: { type: "object" },
          prior_art_comparison: { type: "object" },
          terminology: { type: "object" },
          embodiments: { type: "array" },
        },
      },
      specification_type: {
        type: "string",
        enum: ["product", "method", "system", "compound"],
        description:
          "专利类型：product(产品)、method(方法)、system(系统)、compound(化合物)",
      },
      detail_level: {
        type: "string",
        enum: ["brief", "standard", "detailed"],
        description: "详细程度：brief(简略)、standard(标准)、detailed(详细)",
      },
      include_embodiments: {
        type: "boolean",
        description: "是否包含多个实施例",
        default: true,
      },
    },
    required: ["invention_understanding"],
  },
};

interface DraftSpecificationInput {
  invention_understanding: {
    basic_info: any;
    core_solution: any;
    prior_art_comparison: any;
    terminology: any;
    embodiments: string[];
  };
  specification_type?: "product" | "method" | "system" | "compound";
  detail_level?: "brief" | "standard" | "detailed";
  include_embodiments?: boolean;
}

interface DraftSpecificationOutput {
  technical_field: string;
  background_art: string;
  invention_content: {
    purpose: string;
    technical_solution: string;
    beneficial_effects: string[];
  };
  brief_description_of_drawings?: string;
  detailed_description: string;
  full_text: string;
}

/**
 * 执行说明书生成
 */
export async function executeDraftSpecification(
  input: DraftSpecificationInput,
): Promise<DraftSpecificationOutput> {
  const promptPath = join(
    process.cwd(),
    "src/prompts/specification-generation.md",
  );
  const promptTemplate = await readFile(promptPath, "utf-8");

  const fullPrompt = `${promptTemplate}

## 发明理解信息

\`\`\`json
${JSON.stringify(input.invention_understanding, null, 2)}
\`\`\`

## 撰写要求

专利类型：${input.specification_type || "product"}
详细程度：${input.detail_level || "standard"}
包含多个实施例：${input.include_embodiments !== false}

请根据上述信息，生成符合规范的专利说明书。`;

  // 这里应该调用本地LLM API
  // 由于不调用外部API，这里返回一个占位符结构
  // 实际使用时需要集成本地LLM

  const result: DraftSpecificationOutput = {
    technical_field: "技术领域内容待生成",
    background_art: "背景技术内容待生成",
    invention_content: {
      purpose: "发明目的待生成",
      technical_solution: "技术方案待生成",
      beneficial_effects: ["有益效果1待生成", "有益效果2待生成"],
    },
    detailed_description: "具体实施方式待生成",
    full_text: `## 技术领域

技术领域内容待生成

## 背景技术

背景技术内容待生成

## 发明内容

### 发明目的

发明目的待生成

### 技术方案

技术方案待生成

### 有益效果

有益效果待生成

## 具体实施方式

具体实施方式待生成`,
  };

  return result;
}
