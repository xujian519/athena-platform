/**
 * 专利撰写工具集
 * 整合所有专利撰写相关的MCP工具
 */

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import {
  understandDisclosureTool,
  executeUnderstandDisclosure,
} from "./disclosure-understanding.js";
import {
  draftSpecificationTool,
  executeDraftSpecification,
} from "./specification-generator.js";
import {
  generateClaimsTool,
  draftAbstractTool,
  executeGenerateClaims,
  executeDraftAbstract,
} from "./claim-generator.js";
import {
  searchPriorArtTool,
  executeSearchPriorArt,
} from "./prior-art-search.js";

export const patentDraftingTools: Tool[] = [
  understandDisclosureTool,
  searchPriorArtTool,
  draftSpecificationTool,
  generateClaimsTool,
  draftAbstractTool,
];

export const patentDraftingExecutors = {
  understand_disclosure: executeUnderstandDisclosure,
  search_prior_art: executeSearchPriorArt,
  draft_specification: executeDraftSpecification,
  generate_claims: executeGenerateClaims,
  draft_abstract: executeDraftAbstract,
};

export {
  understandDisclosureTool,
  searchPriorArtTool,
  draftSpecificationTool,
  generateClaimsTool,
  draftAbstractTool,
  executeUnderstandDisclosure,
  executeSearchPriorArt,
  executeDraftSpecification,
  executeGenerateClaims,
  executeDraftAbstract,
};
