#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import dotenv from "dotenv";
import logger from "./utils/logger.js";
import knowledgeService from "./services/knowledge.js";

dotenv.config();

const server = new Server(
  {
    name: "ip-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      // 工具列表将由其他任务添加
      // 这里只提供框架，不实现具体业务工具
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  logger.info("Tool called", { toolName: name, args });

  try {
    // 工具处理逻辑将由其他任务实现
    // 这里只提供框架

    throw new Error(`工具 "${name}" 尚未实现`);
  } catch (error) {
    logger.error("Tool execution failed", {
      toolName: name,
      error: error instanceof Error ? error.message : String(error),
    });

    return {
      content: [
        {
          type: "text",
          text: `错误: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
    };
  }
});

async function main() {
  logger.info("Starting IP MCP Server...");

  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info("IP MCP Server started successfully");

  // 优雅关闭
  process.on("SIGINT", async () => {
    logger.info("Shutting down IP MCP Server...");
    await knowledgeService.cleanup();
    process.exit(0);
  });

  process.on("SIGTERM", async () => {
    logger.info("Shutting down IP MCP Server...");
    await knowledgeService.cleanup();
    process.exit(0);
  });
}

main().catch((error) => {
  logger.error("Server startup failed", { error });
  process.exit(1);
});
