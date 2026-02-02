#!/usr/bin/env node
/**
 * GitHub MCP服务器
 * 提供GitHub仓库管理功能
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { Octokit } from '@octokit/rest';
import dotenv from 'dotenv';

dotenv.config();

// 创建MCP服务器
const server = new Server(
  {
    name: 'github-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 初始化GitHub客户端
const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

// 定义工具列表
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'create_pull_request',
        description: '创建Pull Request',
        inputSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: '仓库所有者' },
            repo: { type: 'string', description: '仓库名称' },
            title: { type: 'string', description: 'PR标题' },
            head: { type: 'string', description: '源分支' },
            base: { type: 'string', description: '目标分支' },
            body: { type: 'string', description: 'PR描述' },
          },
          required: ['owner', 'repo', 'title', 'head', 'base'],
        },
      },
      {
        name: 'list_issues',
        description: '列出Issues',
        inputSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: '仓库所有者' },
            repo: { type: 'string', description: '仓库名称' },
            state: { type: 'string', enum: ['open', 'closed', 'all'], default: 'open' },
          },
          required: ['owner', 'repo'],
        },
      },
      {
        name: 'list_pull_requests',
        description: '列出Pull Requests',
        inputSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: '仓库所有者' },
            repo: { type: 'string', description: '仓库名称' },
            state: { type: 'string', enum: ['open', 'closed', 'all'], default: 'open' },
          },
          required: ['owner', 'repo'],
        },
      },
      {
        name: 'get_file_content',
        description: '获取文件内容',
        inputSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: '仓库所有者' },
            repo: { type: 'string', description: '仓库名称' },
            path: { type: 'string', description: '文件路径' },
            ref: { type: 'string', description: '分支或提交SHA', default: 'main' },
          },
          required: ['owner', 'repo', 'path'],
        },
      },
      {
        name: 'create_issue',
        description: '创建Issue',
        inputSchema: {
          type: 'object',
          properties: {
            owner: { type: 'string', description: '仓库所有者' },
            repo: { type: 'string', description: '仓库名称' },
            title: { type: 'string', description: 'Issue标题' },
            body: { type: 'string', description: 'Issue描述' },
            labels: { type: 'array', items: { type: 'string' }, description: '标签列表' },
          },
          required: ['owner', 'repo', 'title'],
        },
      },
    ],
  };
});

// 处理工具调用
server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'create_pull_request':
        const pr = await octokit.pulls.create({
          owner: args.owner,
          repo: args.repo,
          title: args.title,
          head: args.head,
          base: args.base,
          body: args.body,
        });
        return {
          content: [
            {
              type: 'text',
              text: `Pull Request已创建：${pr.data.html_url}`,
            },
          ],
        };

      case 'list_issues':
        const issues = await octokit.issues.listForRepo({
          owner: args.owner,
          repo: args.repo,
          state: args.state || 'open',
        });
        const issuesList = issues.data.map(issue =>
          `#${issue.number} ${issue.title} (${issue.state})`
        ).join('\n');
        return {
          content: [
            {
              type: 'text',
              text: `Issues列表：\n${issuesList}`,
            },
          ],
        };

      case 'list_pull_requests':
        const prs = await octokit.pulls.list({
          owner: args.owner,
          repo: args.repo,
          state: args.state || 'open',
        });
        const prsList = prs.data.map(pr =>
          `#${pr.number} ${pr.title} (${pr.state})`
        ).join('\n');
        return {
          content: [
            {
              type: 'text',
              text: `Pull Requests列表：\n${prsList}`,
            },
          ],
        };

      case 'get_file_content':
        const file = await octokit.repos.getContent({
          owner: args.owner,
          repo: args.repo,
          path: args.path,
          ref: args.ref || 'main',
        });
        const content = Buffer.from(file.data.content, 'base64').toString();
        return {
          content: [
            {
              type: 'text',
              text: `文件内容：\n${content}`,
            },
          ],
        };

      case 'create_issue':
        const issue = await octokit.issues.create({
          owner: args.owner,
          repo: args.repo,
          title: args.title,
          body: args.body,
          labels: args.labels || [],
        });
        return {
          content: [
            {
              type: 'text',
              text: `Issue已创建：${issue.data.html_url}`,
            },
          ],
        };

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `错误：${error.message}`,
        },
      ],
    };
  }
});

// 启动服务器
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('GitHub MCP服务器已启动');
}

main().catch((error) => {
  console.error('服务器启动失败:', error);
  process.exit(1);
});