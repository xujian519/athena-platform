#!/usr/bin/env node
/**
 * Athena工作平台 - 学术搜索MCP服务器
 * Athena Work Platform - Academic Search MCP Server
 *
 * 提供学术论文和期刊搜索功能
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
const cheerio = require('cheerio');
require('dotenv').config();

// 学术API配置
const ACADEMIC_API_KEY = process.env.ACADEMIC_API_KEY || '';
const SEMANTIC_SCHOLAR_API_KEY = process.env.SEMANTIC_SCHOLAR_API_KEY || '';
const PUBMED_API_KEY = process.env.PUBMED_API_KEY || '';

// 创建日志记录器
const logger = {
    info: (message) => console.log(`[INFO] ${new Date().toISOString()} - ${message}`),
    error: (message) => console.error(`[ERROR] ${new Date().toISOString()} - ${message}`),
    warn: (message) => console.warn(`[WARN] ${new Date().toISOString()} - ${message}`)
};

/**
 * 学术搜索工具类
 */
class AcademicSearchTools {
    constructor() {
        this.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
        this.name = '学术搜索';
    }

    /**
     * 搜索学术论文 - 使用Google Scholar
     */
    async searchPapers(query, options = {}) {
        try {
            const limit = options.limit || 10;
            const year = options.year || '';
            const field = options.field || '';

            // 构建Google Scholar搜索URL
            let searchUrl = 'https://scholar.google.com/scholar';
            const params = {
                q: query,
                hl: 'zh-CN',
                num: limit,
                as_sdt: '1,5'  // 包含引用和专利
            };

            if (year) {
                params.as_ylo = year;
                params.as_yhi = year;
            }

            const response = await axios.get(searchUrl, {
                params: params,
                headers: {
                    'User-Agent': this.userAgent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                },
                timeout: 30000
            });

            const $ = cheerio.load(response.data);
            const results = [];

            $('.gs_r.gs_or.gs_scl').each((index, element) => {
                if (results.length >= limit) return false;

                const $element = $(element);
                const $title = $element.find('.gs_rt a');
                const $snippet = $element.find('.gs_rs');
                const $author = $element.find('.gs_a');
                const $year = $element.find('.gs_a');

                if ($title.length > 0) {
                    const result = {
                        index: results.length + 1,
                        title: $title.text().trim(),
                        url: $title.attr('href') || '',
                        snippet: $snippet.text().trim(),
                        authors: this.extractAuthors($author.text()),
                        publication: this.extractPublication($author.text()),
                        year: this.extractYear($author.text()),
                        citations: this.extractCitations($element),
                        pdfLink: this.extractPdfLink($element)
                    };

                    results.push(result);
                }
            });

            return {
                success: true,
                query: query,
                results: results,
                totalResults: results.length,
                searchUrl: searchUrl + '?' + new URLSearchParams(params).toString(),
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            logger.error(`学术论文搜索失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                query: query,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 使用Semantic Scholar API搜索论文
     */
    async searchSemanticScholar(query, options = {}) {
        try {
            const limit = options.limit || 10;
            const fields = options.fields || ['title', 'authors', 'year', 'venue', 'url', 'abstract', 'citationCount'];

            const apiUrl = 'https://api.semanticscholar.org/graph/v1/paper/search';
            const params = {
                query: query,
                limit: limit,
                fields: fields.join(',')
            };

            const response = await axios.get(apiUrl, {
                params: params,
                timeout: 30000,
                headers: SEMANTIC_SCHOLAR_API_KEY ? {
                    'x-api-key': SEMANTIC_SCHOLAR_API_KEY
                } : {}
            });

            const results = response.data.data.map((paper, index) => ({
                index: index + 1,
                title: paper.title,
                authors: paper.authors ? paper.authors.map(a => a.name).join(', ') : '',
                year: paper.year || '',
                venue: paper.venue || '',
                url: paper.url || '',
                abstract: paper.abstract || '',
                citations: paper.citationCount || 0,
                paperId: paper.paperId
            }));

            return {
                success: true,
                query: query,
                results: results,
                totalResults: response.data.total || results.length,
                source: 'Semantic Scholar',
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            logger.error(`Semantic Scholar搜索失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                query: query,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 获取论文详细信息
     */
    async getPaperMetadata(paperId, source = 'semantic-scholar') {
        try {
            let paperInfo = null;

            if (source === 'semantic-scholar') {
                const apiUrl = `https://api.semanticscholar.org/graph/v1/paper/${paperId}`;
                const fields = ['title', 'authors', 'year', 'venue', 'url', 'abstract', 'citationCount', 'references', 'citations'];

                const response = await axios.get(apiUrl, {
                    params: { fields: fields.join(',') },
                    timeout: 30000,
                    headers: SEMANTIC_SCHOLAR_API_KEY ? {
                        'x-api-key': SEMANTIC_SCHOLAR_API_KEY
                    } : {}
                });

                const paper = response.data;
                paperInfo = {
                    title: paper.title,
                    authors: paper.authors ? paper.authors.map(a => a.name).join(', ') : '',
                    year: paper.year || '',
                    venue: paper.venue || '',
                    url: paper.url || '',
                    abstract: paper.abstract || '',
                    citations: paper.citationCount || 0,
                    references: paper.references ? paper.references.length : 0,
                    citingPapers: paper.citations ? paper.citations.length : 0,
                    paperId: paper.paperId
                };
            }

            return {
                success: true,
                paperId: paperId,
                source: source,
                metadata: paperInfo,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            logger.error(`获取论文元数据失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                paperId: paperId,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 按作者搜索论文
     */
    async searchByAuthor(authorName, options = {}) {
        try {
            const limit = options.limit || 10;

            // 使用Semantic Scholar API按作者搜索
            const apiUrl = 'https://api.semanticscholar.org/graph/v1/author/search';
            const params = {
                query: authorName,
                limit: limit
            };

            const response = await axios.get(apiUrl, {
                params: params,
                timeout: 30000,
                headers: SEMANTIC_SCHOLAR_API_KEY ? {
                    'x-api-key': SEMANTIC_SCHOLAR_API_KEY
                } : {}
            });

            const results = [];

            for (const author of response.data.data.slice(0, limit)) {
                // 获取作者的论文
                const papersUrl = `https://api.semanticscholar.org/graph/v1/author/${author.authorId}/papers`;
                const papersResponse = await axios.get(papersUrl, {
                    params: { limit: 5 },
                    timeout: 30000,
                    headers: SEMANTIC_SCHOLAR_API_KEY ? {
                        'x-api-key': SEMANTIC_SCHOLAR_API_KEY
                    } : {}
                });

                const papers = papersResponse.data.data.map(paper => ({
                    title: paper.title,
                    year: paper.year || '',
                    venue: paper.venue || '',
                    citationCount: paper.citationCount || 0,
                    url: paper.url || ''
                }));

                results.push({
                    authorId: author.authorId,
                    name: author.name,
                    url: author.url || '',
                    paperCount: author.paperCount || 0,
                    citationCount: author.citationCount || 0,
                    hIndex: author.hIndex || 0,
                    papers: papers
                });
            }

            return {
                success: true,
                authorName: authorName,
                results: results,
                totalResults: results.length,
                source: 'Semantic Scholar',
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            logger.error(`按作者搜索失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                authorName: authorName,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 获取引用关系
     */
    async getCitations(paperId, options = {}) {
        try {
            const limit = options.limit || 20;

            const apiUrl = `https://api.semanticscholar.org/graph/v1/paper/${paperId}/citations`;
            const fields = ['title', 'authors', 'year', 'venue', 'url', 'abstract'];

            const response = await axios.get(apiUrl, {
                params: {
                    limit: limit,
                    fields: fields.join(',')
                },
                timeout: 30000,
                headers: SEMANTIC_SCHOLAR_API_KEY ? {
                    'x-api-key': SEMANTIC_SCHOLAR_API_KEY
                } : {}
            });

            const citations = response.data.data.map((citation, index) => ({
                index: index + 1,
                title: citation.title,
                authors: citation.authors ? citation.authors.map(a => a.name).join(', ') : '',
                year: citation.year || '',
                venue: citation.venue || '',
                url: citation.url || '',
                abstract: citation.abstract || '',
                citingPaper: {
                    paperId: citation.citingPaper.paperId,
                    title: citation.citingPaper.title
                }
            }));

            return {
                success: true,
                paperId: paperId,
                citations: citations,
                totalCitations: citations.length,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            logger.error(`获取引用关系失败: ${error.message}`);
            return {
                success: false,
                error: error.message,
                paperId: paperId,
                timestamp: new Date().toISOString()
            };
        }
    }

    // 辅助方法
    extractAuthors(authorText) {
        const match = authorText.match(/^([^,-]*)/);
        return match ? match[1].trim() : '';
    }

    extractPublication(authorText) {
        const match = authorText.match(/-([^,-]*?)(\s*-\s*\d{4})?$/);
        return match ? match[1].trim() : '';
    }

    extractYear(authorText) {
        const match = authorText.match(/(\d{4})/);
        return match ? match[1] : '';
    }

    extractCitations(element) {
        const $citationLink = element.find('.gs_fl a:contains("被引用")');
        if ($citationLink.length > 0) {
            const text = $citationLink.text();
            const match = text.match(/被引用\s*(\d+)/);
            return match ? parseInt(match[1]) : 0;
        }
        return 0;
    }

    extractPdfLink(element) {
        const $pdfLink = element.find('.gs_ggs a');
        return $pdfLink.length > 0 ? $pdfLink.attr('href') : '';
    }
}

/**
 * 创建学术搜索MCP工具
 */
const academicTools = new AcademicSearchTools();

/**
 * 创建服务器实例
 */
const server = new Server(
    {
        name: "academic-search-mcp-server",
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
                name: "search_papers",
                description: "搜索学术论文",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: {
                            type: "string",
                            description: "搜索查询关键词"
                        },
                        limit: {
                            type: "number",
                            description: "返回结果数量，默认10",
                            default: 10
                        },
                        year: {
                            type: "string",
                            description: "限定年份，如2023"
                        },
                        field: {
                            type: "string",
                            description: "研究领域"
                        }
                    },
                    required: ["query"]
                }
            },
            {
                name: "search_semantic_scholar",
                description: "使用Semantic Scholar API搜索论文",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: {
                            type: "string",
                            description: "搜索查询关键词"
                        },
                        limit: {
                            type: "number",
                            description: "返回结果数量，默认10",
                            default: 10
                        },
                        fields: {
                            type: "array",
                            items: {
                                type: "string"
                            },
                            description: "返回字段，默认包括基本信息"
                        }
                    },
                    required: ["query"]
                }
            },
            {
                name: "get_paper_metadata",
                description: "获取论文详细信息",
                inputSchema: {
                    type: "object",
                    properties: {
                        paper_id: {
                            type: "string",
                            description: "论文ID"
                        },
                        source: {
                            type: "string",
                            description: "数据源，默认semantic-scholar",
                            default: "semantic-scholar"
                        }
                    },
                    required: ["paper_id"]
                }
            },
            {
                name: "search_by_author",
                description: "按作者搜索论文",
                inputSchema: {
                    type: "object",
                    properties: {
                        author_name: {
                            type: "string",
                            description: "作者姓名"
                        },
                        limit: {
                            type: "number",
                            description: "返回结果数量，默认10",
                            default: 10
                        }
                    },
                    required: ["author_name"]
                }
            },
            {
                name: "get_citations",
                description: "获取论文的引用关系",
                inputSchema: {
                    type: "object",
                    properties: {
                        paper_id: {
                            type: "string",
                            description: "论文ID"
                        },
                        limit: {
                            type: "number",
                            description: "返回引用数量，默认20",
                            default: 20
                        }
                    },
                    required: ["paper_id"]
                }
            },
            {
                name: "get_system_info",
                description: "获取学术搜索MCP服务器系统信息",
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
        if (name === "search_papers") {
            const { query, limit = 10, year = '', field = '' } = args;

            if (!query) {
                throw new McpError(ErrorCode.InvalidParams, "查询参数是必需的");
            }

            logger.info(`学术论文搜索: "${query}" (限制: ${limit})`);
            const result = await academicTools.searchPapers(query, { limit, year, field });

            if (result.success && result.results.length > 0) {
                const searchResults = result.results.map(r => ({
                    index: r.index,
                    title: r.title,
                    authors: r.authors,
                    publication: r.publication,
                    year: r.year,
                    citations: r.citations,
                    url: r.url,
                    snippet: r.snippet
                }));

                return {
                    content: [{
                        type: "text",
                        text: `找到 ${searchResults.length} 篇学术论文:\n\n` +
                               searchResults.map(r =>
                                   `${r.index}. ${r.title}\n   作者: ${r.authors}\n   发表: ${r.publication} (${r.year})\n   引用: ${r.citations}\n   链接: ${r.url}\n   摘要: ${r.snippet}\n`
                               ).join('\n') +
                               `\n搜索URL: ${result.searchUrl}`
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `搜索完成，但未找到相关论文` :
                            `搜索失败: ${result.error}`
                    }]
                };
            }
        }

        if (name === "search_semantic_scholar") {
            const { query, limit = 10, fields = [] } = args;

            if (!query) {
                throw new McpError(ErrorCode.InvalidParams, "查询参数是必需的");
            }

            logger.info(`Semantic Scholar搜索: "${query}" (限制: ${limit})`);
            const result = await academicTools.searchSemanticScholar(query, { limit, fields });

            if (result.success && result.results.length > 0) {
                const searchResults = result.results.map(r => ({
                    index: r.index,
                    title: r.title,
                    authors: r.authors,
                    year: r.year,
                    venue: r.venue,
                    citations: r.citations,
                    url: r.url,
                    abstract: r.abstract ? r.abstract.substring(0, 200) + '...' : ''
                }));

                return {
                    content: [{
                        type: "text",
                        text: `从 ${result.source} 找到 ${searchResults.length} 篇论文:\n\n` +
                               searchResults.map(r =>
                                   `${r.index}. ${r.title}\n   作者: ${r.authors}\n   发表: ${r.venue} (${r.year})\n   引用: ${r.citations}\n   链接: ${r.url}\n   摘要: ${r.abstract}\n`
                               ).join('\n')
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `Semantic Scholar搜索完成，但未找到相关论文` :
                            `Semantic Scholar搜索失败: ${result.error}`
                    }]
                };
            }
        }

        if (name === "get_paper_metadata") {
            const { paper_id, source = "semantic-scholar" } = args;

            if (!paper_id) {
                throw new McpError(ErrorCode.InvalidParams, "论文ID是必需的");
            }

            logger.info(`获取论文元数据: ${paper_id} (来源: ${source})`);
            const result = await academicTools.getPaperMetadata(paper_id, source);

            if (result.success && result.metadata) {
                const metadata = result.metadata;

                return {
                    content: [{
                        type: "text",
                        text: `论文详细信息:\n\n` +
                               `标题: ${metadata.title}\n` +
                               `作者: ${metadata.authors}\n` +
                               `发表: ${metadata.venue} (${metadata.year})\n` +
                               `引用数: ${metadata.citations}\n` +
                               `参考文献: ${metadata.references}\n` +
                               `被引用数: ${metadata.citingPapers}\n` +
                               `链接: ${metadata.url}\n` +
                               `摘要: ${metadata.abstract}\n` +
                               `论文ID: ${metadata.paperId}`
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `未找到论文信息: ${paper_id}` :
                            `获取论文信息失败: ${result.error}`
                    }]
                };
            }
        }

        if (name === "search_by_author") {
            const { author_name, limit = 10 } = args;

            if (!author_name) {
                throw new McpError(ErrorCode.InvalidParams, "作者姓名是必需的");
            }

            logger.info(`按作者搜索: "${author_name}" (限制: ${limit})`);
            const result = await academicTools.searchByAuthor(author_name, { limit });

            if (result.success && result.results.length > 0) {
                const authorResults = result.results.map(r => ({
                    name: r.name,
                    paperCount: r.paperCount,
                    citationCount: r.citationCount,
                    hIndex: r.hIndex,
                    recentPapers: r.papers.slice(0, 3).map(p => `${p.title} (${p.year})`).join('; ')
                }));

                return {
                    content: [{
                        type: "text",
                        text: `找到 ${authorResults.length} 位作者:\n\n` +
                               authorResults.map(r =>
                                   `👤 ${r.name}\n   论文数: ${r.paperCount}\n   引用数: ${r.citationCount}\n   H指数: ${r.hIndex}\n   近期论文: ${r.recentPapers}\n`
                               ).join('\n')
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `未找到作者: ${author_name}` :
                            `按作者搜索失败: ${result.error}`
                    }]
                };
            }
        }

        if (name === "get_citations") {
            const { paper_id, limit = 20 } = args;

            if (!paper_id) {
                throw new McpError(ErrorCode.InvalidParams, "论文ID是必需的");
            }

            logger.info(`获取引用关系: ${paper_id} (限制: ${limit})`);
            const result = await academicTools.getCitations(paper_id, { limit });

            if (result.success && result.citations.length > 0) {
                const citationResults = result.citations.slice(0, 5).map(r => ({
                    index: r.index,
                    title: r.title,
                    authors: r.authors,
                    year: r.year,
                    venue: r.venue
                }));

                return {
                    content: [{
                        type: "text",
                        text: `论文 ${paper_id} 被引用 ${result.totalCitations} 次\n\n` +
                               `前5个引用论文:\n` +
                               citationResults.map(r =>
                                   `${r.index}. ${r.title}\n   作者: ${r.authors}\n   发表: ${r.venue} (${r.year})\n`
                               ).join('\n') +
                               (result.totalCitations > 5 ? `\n... 还有 ${result.totalCitations - 5} 个引用` : '')
                    }]
                };
            } else {
                return {
                    content: [{
                        type: "text",
                        text: result.success ?
                            `论文 ${paper_id} 没有引用记录` :
                            `获取引用关系失败: ${result.error}`
                    }]
                };
            }
        }

        if (name === "get_system_info") {
            const info = {
                name: "学术搜索MCP服务器",
                version: "1.0.0",
                description: "Athena工作平台的学术搜索MCP服务器",
                capabilities: [
                    "Google Scholar搜索",
                    "Semantic Scholar API搜索",
                    "论文元数据获取",
                    "作者搜索",
                    "引用关系分析"
                ],
                apiKeys: {
                    academic: ACADEMIC_API_KEY ? "已配置" : "未配置",
                    semanticScholar: SEMANTIC_SCHOLAR_API_KEY ? "已配置" : "未配置",
                    pubmed: PUBMED_API_KEY ? "已配置" : "未配置"
                },
                timestamp: new Date().toISOString(),
                authors: ["小诺", "Athena"]
            };

            return {
                content: [{
                    type: "text",
                    text: `学术搜索MCP服务器信息:\n\n` +
                           `名称: ${info.name}\n` +
                           `版本: ${info.version}\n` +
                           `描述: ${info.description}\n` +
                           `功能: ${info.capabilities.join(', ')}\n` +
                           `API密钥状态: 学术(${info.apiKeys.academic}), Semantic Scholar(${info.apiKeys.semanticScholar}), PubMed(${info.apiKeys.pubmed})\n` +
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
        logger.info("启动学术搜索MCP服务器...");
        logger.info(`API密钥状态: 学术(${ACADEMIC_API_KEY ? "已配置" : "未配置"}), Semantic Scholar(${SEMANTIC_SCHOLAR_API_KEY ? "已配置" : "未配置"})`);

        await server.connect(transport);
        logger.info("学术搜索MCP服务器启动成功！");

        // 保持服务器运行
        logger.info("服务器正在运行，等待请求...");

    } catch (error) {
        logger.error(`启动服务器失败: ${error}`);
        process.exit(1);
    }
}

// 处理程序退出
process.on('SIGINT', () => {
    logger.info("正在关闭学术搜索MCP服务器...");
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info("正在关闭学术搜索MCP服务器...");
    process.exit(0);
});

// 启动服务器
main().catch((error) => {
    logger.error(`程序执行失败: ${error}`);
    process.exit(1);
});