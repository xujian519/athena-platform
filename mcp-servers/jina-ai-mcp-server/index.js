#!/usr/bin/env node
/**
 * Athena工作平台 - Jina AI MCP工具服务器
 * Athena Work Platform - Jina AI MCP Tools Server
 *
 * 集成Jina AI的各种功能，为Athena工作平台提供AI增强的外部工具能力
 * 控制者: 小诺 & Athena
 * 创建时间: 2025年12月11日
 * 版本: 1.0.0
 */

const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} = require("@modelcontextprotocol/sdk/types.js");
const axios = require('axios');
const path = require('path');
require('dotenv').config();

// Jina AI 配置
const JINA_API_KEY = process.env.JINA_API_KEY || '';

// 创建日志记录器
const logger = {
    info: (message) => console.log(`[INFO] ${new Date().toISOString()} - ${message}`),
    error: (message) => console.error(`[ERROR] ${new Date().toISOString()} - ${message}`),
    warn: (message) => console.warn(`[WARN] ${new Date().toISOString()} - ${message}`)
};

/**
 * Jina AI工具类
 */
class JinaAITools {
    constructor() {
        this.baseUrl = 'https://api.jina.ai/v1';
        this.apiKey = JINA_API_KEY;
        this.name = 'Jina AI';
    }

    /**
     * Web Reader - 提取网页内容
     */
    async readWebContent(url, options = {}) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/r.jina.ai/http://`,
                {
                    url: url,
                    ...options
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 30000
                }
            );

            return {
                success: true,
                data: response.data,
                title: response.data.title || '',
                content: response.data.data?.content || response.data.content || '',
                url: response.data.url || url,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            logger.error(`Web读取失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                url,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Web Search - 网络搜索
     */
    async webSearch(query, options = {}) {
        try {
            // 使用Jina的搜索API
            const response = await axios.post(
                'https://s.jina.ai/http://',
                {
                    q: query,
                    num: options.limit || 10,
                    ...options
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 30000
                }
            );

            return {
                success: true,
                data: response.data,
                query: query,
                results: response.data.results || [],
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            logger.error(`网络搜索失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                query,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Vector Search - 向量搜索
     */
    async vectorSearch(query, documents, options = {}) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/search`,
                {
                    q: query,
                    documents: documents,
                    ...options
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 30000
                }
            );

            return {
                success: true,
                data: response.data,
                query: query,
                results: response.data.results || [],
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            logger.error(`向量搜索失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                query,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Rerank - 结果重排序
     */
    async rerank(query, documents, options = {}) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/rerank`,
                {
                    query: query,
                    documents: documents,
                    top_n: options.top_n || 10,
                    ...options
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 30000
                }
            );

            return {
                success: true,
                data: response.data,
                query: query,
                results: response.data.results || [],
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            logger.error(`结果重排序失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                query,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Embedding - 文本嵌入
     */
    async embedding(texts, options = {}) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/embeddings`,
                {
                    input: texts,
                    model: options.model || 'jina-embeddings-v2',
                    ...options
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 30000
                }
            );

            return {
                success: true,
                data: response.data,
                embeddings: response.data.embeddings || [],
                dimensions: response.data.dim || [],
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            logger.error(`文本嵌入失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }
}

/**
 * 创建Jina AI MCP工具
 */
const jinaTools = new JinaAITools();

/**
 * 创建服务器实例
 */
const server = new Server(
    {
        name: "jina-ai-mcp-server",
        version: "1.0.0",
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// 列出可用工具
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "read_web",
                description: "使用Jina AI读取网页内容",
                inputSchema: {
                    type: "object",
                    properties: {
                        url: {
                            type: "string",
                            description: "要读取的网页URL"
                        },
                        options: {
                            type: "object",
                            description: "可选参数",
                            properties: {}
                        }
                    },
                    required: ["url"]
                }
            },
            {
                name: "web_search",
                description: "使用Jina AI进行网络搜索",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: {
                            type: "string",
                            description: "搜索查询"
                        },
                        limit: {
                            type: "number",
                            description: "结果数量限制",
                            default: 10
                        },
                        options: {
                            type: "object",
                            description: "可选参数",
                            properties: {}
                        }
                    },
                    required: ["query"]
                }
            },
            {
                name: "vector_search",
                description: "使用Jina AI进行向量搜索",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: {
                            type: "string",
                            description: "搜索查询"
                        },
                        documents: {
                            type: "array",
                            items: {
                                type: "string"
                            },
                            description: "要搜索的文档数组"
                        },
                        options: {
                            type: "object",
                            description: "可选参数",
                            properties: {}
                        }
                    },
                    required: ["query", "documents"]
                }
            },
            {
                name: "rerank",
                description: "使用Jina AI对文档进行重排序",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: {
                            type: "string",
                            description: "查询文本"
                        },
                        documents: {
                            type: "array",
                            items: {
                                type: "string"
                            },
                            description: "要重排序的文档数组"
                        },
                        top_n: {
                            type: "number",
                            description: "返回前N个结果",
                            default: 10
                        },
                        options: {
                            type: "object",
                            description: "可选参数",
                            properties: {}
                        }
                    },
                    required: ["query", "documents"]
                }
            },
            {
                name: "embedding",
                description: "使用Jina AI生成文本嵌入",
                inputSchema: {
                    type: "object",
                    properties: {
                        texts: {
                            type: "array",
                            items: {
                                type: "string"
                            },
                            description: "要生成嵌入的文本数组"
                        },
                        model: {
                            type: "string",
                            description: "嵌入模型",
                            default: "jina-embeddings-v2"
                        },
                        options: {
                            type: "object",
                            description: "可选参数",
                            properties: {}
                        }
                    },
                    required: ["texts"]
                }
            },
            {
                name: "get_system_info",
                description: "获取Jina AI MCP服务器系统信息",
                inputSchema: {
                    type: "object",
                    properties: {}
                }
            }
        ]
    };
});

// 处理工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        if (name === "read_web") {
            const { url, options = {} } = args;

            if (!url) {
                throw new McpError(ErrorCode.InvalidParams, "URL参数是必需的");
            }

            logger.info(`读取网页: ${url}`);
            const result = await jinaTools.readWebContent(url, options);

            return {
                content: [{
                    type: "text",
                    text: result.success ?
                        `成功读取网页内容:\n\n标题: ${result.title}\n内容: ${result.content}` :
                        `读取失败: ${result.error}`
                }]
            };
        }

        if (name === "web_search") {
            const { query, limit = 10, options = {} } = args;

            if (!query) {
                throw new McpError(ErrorCode.InvalidParams, "查询参数是必需的");
            }

            logger.info(`网络搜索: ${query} (限制: ${limit})`);
            const result = await jinaTools.webSearch(query, { limit, ...options });

            if (result.success && result.results && result.results.length > 0) {
                const searchResults = result.results.slice(0, limit).map((item, index) => ({
                    index: index + 1,
                    title: item.title || `搜索结果 ${index + 1}`,
                    url: item.url || item.link || '',
                    snippet: item.snippet || item.description || '',
                    score: item.score || 0
                }));

                return {
                    content: [{
                        type: "text",
                        text: `找到 ${searchResults.length} 个搜索结果:\n\n` +
                               searchResults.map(r =>
                                   `${r.index}. ${r.title}\n   链接: ${r.url}\n   摘要: ${r.snippet}\n   相关性: ${r.score}\n`
                               ).join('\n')
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `搜索完成，但未找到相关结果` :
                            `搜索失败: ${result.error}`
                    }]
                };
            }
        }

        if (name === "vector_search") {
            const { query, documents, options = {} } = args;

            if (!query) {
                throw new McpError(ErrorCode.InvalidParams, "查询参数是必需的");
            }

            if (!documents || !Array.isArray(documents)) {
                throw new McpError(ErrorCode.InvalidParams, "文档参数是必需的，必须是数组");
            }

            logger.info(`向量搜索: "${query}" (${documents.length}个文档)`);
            const result = await jinaTools.vectorSearch(query, documents, options);

            if (result.success && result.results && result.results.length > 0) {
                const searchResults = result.results.map((item, index) => ({
                    index: index + 1,
                    score: item.score || 0,
                    document: item.document || item.text || ''
                }));

                return {
                    content: [{
                        type: "text",
                        text: `向量搜索完成，找到 ${searchResults.length} 个相关文档:\n\n` +
                               searchResults.map(r =>
                                   `${r.index}. 相关性: ${r.score.toFixed(3)}\n   文档: ${r.document}\n`
                               ).join('\n')
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `向量搜索完成，但未找到相关文档` :
                            `向量搜索失败: ${result.error}`
                    }]
                };
            }
        }

        if (name === "rerank") {
            const { query, documents, top_n = 10, options = {} } = args;

            if (!query) {
                throw new McpError(ErrorCode.InvalidParams, "查询参数是必需的");
            }

            if (!documents || !Array.isArray(documents)) {
                throw new McpError(ErrorCode.InvalidParams, "文档参数是必需的，必须是数组");
            }

            logger.info(`重排序: "${query}" (${documents.length}个文档, 取前${top_n}个)`);
            const result = await jinaTools.rerank(query, documents, { top_n, ...options });

            if (result.success && result.results && result.results.length > 0) {
                const rerankedResults = result.results.map((item, index) => ({
                    index: index + 1,
                    relevance_score: item.relevance_score || item.score || 0,
                    document: item.document || item.text || ''
                }));

                return {
                    content: [{
                        type: "text",
                        text: `重排序完成，已重新排序${rerankedResults.length}个文档:\n\n` +
                               rerankedResults.map(r =>
                                   `${r.index}. 相关性: ${r.relevance_score.toFixed(3)}\n   文档: ${r.document}\n`
                               ).join('\n')
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `重排序完成，但处理结果异常` :
                            `重排序失败: ${result.error}`
                    }]
                };
            }
        }

        if (name === "embedding") {
            const { texts, model = "jina-embeddings-v2", options = {} } = args;

            if (!texts || !Array.isArray(texts)) {
                throw new McpError(ErrorCode.InvalidParams, "文本参数是必需的，必须是数组");
            }

            logger.info(`文本嵌入: ${texts.length}个文本 (模型: ${model})`);
            const result = await jinaTools.embedding(texts, { model, ...options });

            if (result.success && result.embeddings && result.embeddings.length > 0) {
                const dimensions = result.dimensions;
                const firstEmbedding = result.embeddings[0];

                return {
                    content: [{
                        type: "text",
                        text: `文本嵌入成功:\n\n` +
                               `模型: ${model}\n` +
                               `向量维度: ${dimensions}\n` +
                               `嵌入数量: ${result.embeddings.length}\n` +
                               `示例向量长度: ${firstEmbedding.length}\n` +
                               `前5个值: [${firstEmbedding.slice(0, 5).map(v => v.toFixed(6)).join(', ')}...]`
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `文本嵌入失败` :
                            `文本嵌入异常: ${result.error}`
                    }]
                };
            }
        }

        if (name === "get_system_info") {
            const info = {
                name: "Jina AI MCP服务器",
                version: "1.0.0",
                description: "Athena工作平台的Jina AI MCP工具服务器",
                capabilities: [
                    "Web内容读取",
                    "网络搜索",
                    "向量搜索",
                    "结果重排序",
                    "文本嵌入"
                ],
                apiKey: JINA_API_KEY ? "已配置" : "未配置",
                timestamp: new Date().toISOString(),
                authors: ["小诺", "Athena"]
            };

            return {
                content: [{
                    type: "text",
                    text: `Jina AI MCP服务器信息:\n\n` +
                           `名称: ${info.name}\n` +
                           `版本: ${info.version}\n` +
                           `描述: ${info.description}\n` +
                           `功能: ${info.capabilities.join(', ')}\n` +
                           `API密钥: ${info.apiKey}\n` +
                           `时间: ${info.timestamp}\n` +
                           `控制者: ${info.authors.join(', ')}`
                }]
            };
        }

        throw new McpError(ErrorCode.MethodNotFound, `未知工具: ${name}`);

    } catch (error) {
        logger.error(`工具执行错误: ${error.message}`);
        throw new McpError(ErrorCode.InternalError, `工具执行失败: ${error.message}`);
    }
});

/**
 * 启动服务器
 */
async function main() {
    const transport = new StdioServerTransport();

    try {
        logger.info("启动Jina AI MCP服务器...");
        logger.info(`API密钥状态: ${JINA_API_KEY ? "已配置" : "未配置"}`);

        await server.connect(transport);
        logger.info("Jina AI MCP服务器启动成功！");

        // 保持服务器运行
        logger.info("服务器正在运行，等待请求...");

    } catch (error) {
        logger.error(`启动服务器失败: ${error}`);
        process.exit(1);
    }
}

// 处理程序退出
process.on('SIGINT', () => {
    logger.info("正在关闭Jina AI MCP服务器...");
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info("正在关闭Jina AI MCP服务器...");
    process.exit(0);
});

// 启动服务器
main().catch((error) => {
    logger.error(`程序执行失败: ${error}`);
    process.exit(1);
});