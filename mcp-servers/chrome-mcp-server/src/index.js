#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import puppeteer from 'puppeteer-core';

const server = new Server(
  {
    name: 'chrome-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

// 存储浏览器实例
let browser = null;
let page = null;

// 工具定义
const TOOLS = [
  {
    name: 'chrome_navigate',
    description: 'Navigate to a URL in Chrome browser',
    inputSchema: {
      type: 'object',
      properties: {
        url: {
          type: 'string',
          description: 'URL to navigate to',
        },
        waitUntil: {
          type: 'string',
          enum: ['load', 'domcontentloaded', 'networkidle0'],
          description: 'When to consider navigation complete',
          default: 'load',
        },
      },
      required: ['url'],
    },
  },
  {
    name: 'chrome_click',
    description: 'Click on an element on the page',
    inputSchema: {
      type: 'object',
      properties: {
        selector: {
          type: 'string',
          description: 'CSS selector of the element to click',
        },
        waitForSelector: {
          type: 'boolean',
          description: 'Whether to wait for the selector before clicking',
          default: true,
        },
      },
      required: ['selector'],
    },
  },
  {
    name: 'chrome_type',
    description: 'Type text into an input field',
    inputSchema: {
      type: 'object',
      properties: {
        selector: {
          type: 'string',
          description: 'CSS selector of the input field',
        },
        text: {
          type: 'string',
          description: 'Text to type',
        },
        clear: {
          type: 'boolean',
          description: 'Whether to clear the field before typing',
          default: true,
        },
      },
      required: ['selector', 'text'],
    },
  },
  {
    name: 'chrome_screenshot',
    description: 'Take a screenshot of the page',
    inputSchema: {
      type: 'object',
      properties: {
        fullPage: {
          type: 'boolean',
          description: 'Whether to take a full page screenshot',
          default: false,
        },
        selector: {
          type: 'string',
          description: 'CSS selector to capture a specific element',
        },
      },
    },
  },
  {
    name: 'chrome_get_text',
    description: 'Get text content of elements',
    inputSchema: {
      type: 'object',
      properties: {
        selector: {
          type: 'string',
          description: 'CSS selector of elements to get text from',
        },
        waitForSelector: {
          type: 'boolean',
          description: 'Whether to wait for the selector',
          default: true,
        },
      },
      required: ['selector'],
    },
  },
  {
    name: 'chrome_evaluate',
    description: 'Execute JavaScript in the page context',
    inputSchema: {
      type: 'object',
      properties: {
        script: {
          type: 'string',
          description: 'JavaScript code to execute',
        },
      },
      required: ['script'],
    },
  },
  {
    name: 'chrome_wait_for_selector',
    description: 'Wait for a selector to appear on the page',
    inputSchema: {
      type: 'object',
      properties: {
        selector: {
          type: 'string',
          description: 'CSS selector to wait for',
        },
        timeout: {
          type: 'number',
          description: 'Timeout in milliseconds',
          default: 30000,
        },
      },
      required: ['selector'],
    },
  },
  {
    name: 'chrome_scroll',
    description: 'Scroll the page',
    inputSchema: {
      type: 'object',
      properties: {
        direction: {
          type: 'string',
          enum: ['down', 'up'],
          description: 'Scroll direction',
          default: 'down',
        },
        pixels: {
          type: 'number',
          description: 'Number of pixels to scroll',
          default: 500,
        },
      },
    },
  },
];

// 注册工具
for (const tool of TOOLS) {
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === tool.name) {
      try {
        const result = await handleToolCall(request.params.name, request.params.arguments);
        return {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        return {
          content: [{ type: 'text', text: `Error: ${error.message}` }],
          isError: true,
        };
      }
    }
    throw new Error(`Unknown tool: ${request.params.name}`);
  });
}

// 处理工具调用
async function handleToolCall(toolName, args) {
  if (!browser) {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    page = await browser.newPage();
  }

  switch (toolName) {
    case 'chrome_navigate':
      return await navigate(args);
    case 'chrome_click':
      return await click(args);
    case 'chrome_type':
      return await typeText(args);
    case 'chrome_screenshot':
      return await screenshot(args);
    case 'chrome_get_text':
      return await getText(args);
    case 'chrome_evaluate':
      return await evaluate(args);
    case 'chrome_wait_for_selector':
      return await waitForSelector(args);
    case 'chrome_scroll':
      return await scroll(args);
    default:
      throw new Error(`Unknown tool: ${toolName}`);
  }
}

// 工具实现函数
async function navigate({ url, waitUntil = 'load' }) {
  const response = await page.goto(url, { waitUntil });
  return {
    url: response.url(),
    status: response.status(),
    ok: response.ok(),
  };
}

async function click({ selector, waitForSelector = true }) {
  if (waitForSelector) {
    await page.waitForSelector(selector);
  }
  await page.click(selector);
  return { success: true, selector };
}

async function typeText({ selector, text, clear = true }) {
  await page.waitForSelector(selector);
  if (clear) {
    await page.click(selector, { clickCount: 3 });
  }
  await page.type(selector, text);
  return { success: true, selector, text };
}

async function screenshot({ fullPage = false, selector }) {
  if (selector) {
    const element = await page.$(selector);
    if (!element) {
      throw new Error(`Element not found: ${selector}`);
    }
    const screenshot = await element.screenshot();
    return {
      type: 'element',
      selector,
      screenshot: screenshot.toString('base64'),
    };
  } else {
    const screenshot = await page.screenshot({ fullPage });
    return {
      type: fullPage ? 'full_page' : 'viewport',
      screenshot: screenshot.toString('base64'),
    };
  }
}

async function getText({ selector, waitForSelector = true }) {
  if (waitForSelector) {
    await page.waitForSelector(selector);
  }
  const elements = await page.$$(selector);
  const texts = await Promise.all(
    elements.map(element => page.evaluate(el => el.textContent, element))
  );
  return {
    selector,
    count: elements.length,
    texts: texts.filter(text => text && text.trim()),
  };
}

async function evaluate({ script }) {
  const result = await page.evaluate(script);
  return { result };
}

async function waitForSelector({ selector, timeout = 30000 }) {
  await page.waitForSelector(selector, { timeout });
  return { success: true, selector };
}

async function scroll({ direction = 'down', pixels = 500 }) {
  if (direction === 'down') {
    await page.evaluate(pixels => window.scrollBy(0, pixels), pixels);
  } else {
    await page.evaluate(pixels => window.scrollBy(0, -pixels), pixels);
  }
  return { success: true, direction, pixels };
}

// 错误处理
process.on('uncaughtException', async (error) => {
  console.error('Uncaught exception:', error);
  if (browser) {
    await browser.close();
  }
  process.exit(1);
});

// 优雅关闭
process.on('SIGINT', async () => {
  console.log('Received SIGINT, shutting down gracefully...');
  if (browser) {
    await browser.close();
  }
  process.exit(0);
});

// 启动服务器
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Chrome MCP Server running on stdio');
}

main().catch(console.error);