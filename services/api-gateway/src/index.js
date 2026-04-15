#!/usr/bin/env node

/**
 * Athena智能工作平台 - API网关服务
 * API Gateway for Athena Intelligent Platform
 *
 * 功能说明:
 * - 统一API入口点
 * - 路由转发和负载均衡
 * - 身份验证和授权
 * - 请求限流和监控
 * - 日志记录和分析
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');
const winston = require('winston');
const DailyRotateFile = require('winston-daily-rotate-file');
require('dotenv').config();

// 配置常量
const PORT = process.env.PORT || 8080;
const NODE_ENV = process.env.NODE_ENV || 'development';

// 创建日志记录器
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'api-gateway' },
  transports: [
    new DailyRotateFile({
      filename: 'logs/gateway-error-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      level: 'error',
      maxSize: '20m',
      maxFiles: '14d'
    }),
    new DailyRotateFile({
      filename: 'logs/gateway-combined-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '14d'
    })
  ]
});

// 开发环境添加控制台输出
if (NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

// 创建Express应用
const app = express();

// 安全中间件
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));

// CORS配置
const corsOptions = {
  origin: function (origin, callback) {
    // 允许的域名列表
    const allowedOrigins = [
      'http://localhost:3000',
      'http://localhost:8080',
      'https://athena.example.com'
    ];

    // 开发环境允许所有来源
    if (NODE_ENV === 'development') {
      return callback(null, true);
    }

    if (allowedOrigins.indexOf(origin) !== -1 || !origin) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key']
};

app.use(cors(corsOptions));

// 限流配置
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 1000, // 限制每个IP每15分钟最多1000个请求
  message: {
    error: '请求过于频繁，请稍后再试',
    retryAfter: '15分钟'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use(limiter);

// 基础中间件
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 日志中间件
app.use(morgan('combined', {
  stream: {
    write: (message) => logger.info(message.trim())
  }
}));

// 健康检查端点
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: NODE_ENV,
    version: process.env.npm_package_version || '1.0.0',
    services: {
      'patent-analysis': 'http://localhost:8081',
      'knowledge-graph': 'http://localhost:8082',
      'deepseek-service': 'http://localhost:8020',
      'vector-search': 'http://localhost:8001'
    }
  });
});

// 服务路由配置
const services = {
  '/api/v1/patents': {
    target: process.env.PATENT_SERVICE_URL || 'http://localhost:8081',
    changeOrigin: true,
    pathRewrite: {
      '^/api/v1/patents': ''
    }
  },
  '/api/v1/knowledge': {
    target: process.env.KNOWLEDGE_SERVICE_URL || 'http://localhost:8082',
    changeOrigin: true,
    pathRewrite: {
      '^/api/v1/knowledge': '/api/v1'
    }
  },
  '/api/v1/ai': {
    target: process.env.AI_SERVICE_URL || 'http://localhost:8020',
    changeOrigin: true,
    pathRewrite: {
      '^/api/v1/ai': '/api/v1'
    }
  },
  '/api/v1/llm': {
    target: process.env.LLM_SERVICE_URL || 'http://localhost:8003',
    changeOrigin: true,
    pathRewrite: {
      '^/api/v1/llm': ''
    }
  },
  '/api/v1/search': {
    target: process.env.SEARCH_SERVICE_URL || 'http://localhost:8001',
    changeOrigin: true,
    pathRewrite: {
      '^/api/v1/search': '/api/v1'
    }
  }
};

// 注册代理中间件
Object.entries(services).forEach(([path, config]) => {
  app.use(path, createProxyMiddleware({
    ...config,
    onError: (err, req, res) => {
      logger.error(`代理错误 ${path}:`, err);
      res.status(502).json({
        error: '服务暂时不可用',
        message: '后端服务连接失败',
        path: path
      });
    },
    onProxyReq: (proxyReq, req, res) => {
      // 添加请求头
      proxyReq.setHeader('X-Gateway-Request-ID', req.headers['x-request-id'] || generateRequestId());
      proxyReq.setHeader('X-Gateway-Timestamp', new Date().toISOString());

      logger.info(`转发请求: ${req.method} ${path} -> ${config.target}`);
    },
    onProxyRes: (proxyRes, req, res) => {
      // 添加响应头
      proxyRes.headers['X-Gateway-Response-Time'] = new Date().toISOString();

      logger.info(`响应状态: ${path} -> ${proxyRes.statusCode}`);
    }
  }));
});

// API信息端点
app.get('/api/info', (req, res) => {
  res.json({
    name: 'Athena API Gateway',
    version: '1.0.0',
    description: 'Athena智能工作平台统一API网关',
    endpoints: Object.keys(services),
    documentation: '/api/docs',
    health: '/health'
  });
});

// 404处理
app.use('*', (req, res) => {
  res.status(404).json({
    error: '接口不存在',
    message: `路径 ${req.originalUrl} 未找到`,
    availableEndpoints: Object.keys(services)
  });
});

// 全局错误处理
app.use((err, req, res, next) => {
  logger.error('网关错误:', err);

  res.status(err.status || 500).json({
    error: NODE_ENV === 'production' ? '内部服务器错误' : err.message,
    message: err.details || '请求处理失败',
    timestamp: new Date().toISOString(),
    requestId: req.headers['x-request-id']
  });
});

// 生成请求ID
function generateRequestId() {
  return 'gw_' + Math.random().toString(36).substr(2, 9);
}

// 优雅关闭处理
process.on('SIGTERM', () => {
  logger.info('收到SIGTERM信号，正在优雅关闭...');
  server.close(() => {
    logger.info('HTTP服务器已关闭');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('收到SIGINT信号，正在优雅关闭...');
  server.close(() => {
    logger.info('HTTP服务器已关闭');
    process.exit(0);
  });
});

// 启动服务器
const server = app.listen(PORT, '0.0.0.0', () => {
  logger.info(`🚀 Athena API网关启动成功`);
  logger.info(`📍 服务地址: http://localhost:${PORT}`);
  logger.info(`🌍 环境: ${NODE_ENV}`);
  logger.info(`⏰ 启动时间: ${new Date().toISOString()}`);

  console.log(`
╔══════════════════════════════════════════════════════════════╗
║                    Athena API Gateway                        ║
╠══════════════════════════════════════════════════════════════╣
║  🚀 服务地址: http://localhost:${PORT}                           ║
║  📊 健康检查: http://localhost:${PORT}/health                    ║
║  📋 API信息:  http://localhost:${PORT}/api/info                  ║
║  🌍 运行环境: ${NODE_ENV}                                         ║
║  ⏰ 启动时间: ${new Date().toLocaleString('zh-CN')}              ║
╚══════════════════════════════════════════════════════════════╝
  `);
});

module.exports = app;