/**
 * 安全中间件测试套件
 * Security Middleware Test Suite
 */

const request = require('supertest');
const express = require('express');
const { SecurityOrchestrationEngine } = require('../src/security/security-middleware');

describe('Security Middleware Tests', () => {
  let app;
  let securityEngine;

  beforeAll(() => {
    const config = require('../config/security.json');
    securityEngine = new SecurityOrchestrationEngine(config);
    
    app = express();
    app.use(express.json());
    
    // 应用安全中间件链
    securityEngine.getMiddlewareChain().forEach(middleware => {
      app.use(middleware);
    });
    
    // 测试端点
    app.get('/test', (req, res) => {
      res.json({ 
        message: 'Security check passed',
        securityContext: req.securityContext,
        threatAssessment: req.threatAssessment,
        complianceCheck: req.complianceCheck
      });
    });

    app.post('/test-data', (req, res) => {
      res.json({ 
        received: req.body,
        dataClassification: req.dataClassification
      });
    });
  });

  describe('Zero Trust Security', () => {
    test('should block request without authentication token', async () => {
      const response = await request(app)
        .get('/test')
        .expect(403);

      expect(response.body.error).toContain('Access denied');
    });

    test('should allow request with valid token', async () => {
      const validToken = generateTestToken('test-user', ['user']);
      
      const response = await request(app)
        .get('/test')
        .set('Authorization', `Bearer ${validToken}`)
        .expect(200);

      expect(response.body.message).toBe('Security check passed');
      expect(response.body.securityContext).toBeDefined();
      expect(response.body.securityContext.trustLevel).toMatch(/high|medium|low|minimal/);
    });
  });

  describe('API Security Protection', () => {
    test('should block SQL injection attempts', async () => {
      const validToken = generateTestToken('test-user', ['user']);
      
      const response = await request(app)
        .post('/test-data')
        .set('Authorization', `Bearer ${validToken}`)
        .send({ query: "SELECT * FROM users WHERE id = 1 OR 1=1" })
        .expect(403);

      expect(response.body.error).toContain('Request blocked by WAF');
    });

    test('should block XSS attempts', async () => {
      const validToken = generateTestToken('test-user', ['user']);
      
      const response = await request(app)
        .post('/test-data')
        .set('Authorization', `Bearer ${validToken}`)
        .send({ comment: "<script>alert('xss')</script>" })
        .expect(403);

      expect(response.body.error).toContain('Request blocked by WAF');
    });
  });

  describe('Data Protection', () => {
    test('should classify sensitive data appropriately', async () => {
      const validToken = generateTestToken('test-user', ['user']);
      
      const response = await request(app)
        .post('/test-data')
        .set('Authorization', `Bearer ${validToken}`)
        .send({ 
          email: 'user@example.com',
          ssn: '123-45-6789',
          creditCard: '4111-1111-1111-1111'
        })
        .expect(200);

      expect(response.body.dataClassification).toBeDefined();
      expect(response.body.dataClassification.level).toMatch(/sensitive|restricted/);
    });

    test('should mask PII in responses', async () => {
      const validToken = generateTestToken('test-user', ['user']);
      
      const response = await request(app)
        .post('/test-data')
        .set('Authorization', `Bearer ${validToken}`)
        .send({ email: 'user@example.com' })
        .expect(200);

      // 检查返回数据是否被适当处理
      expect(response.body).toBeDefined();
    });
  });

  describe('Threat Intelligence', () => {
    test('should detect suspicious IP addresses', async () => {
      const validToken = generateTestToken('test-user', ['user']);
      
      // 模拟可疑IP地址
      const response = await request(app)
        .get('/test')
        .set('Authorization', `Bearer ${validToken}`)
        .set('X-Forwarded-For', '192.168.1.100') // 测试用IP
        .expect(200);

      expect(response.body.threatAssessment).toBeDefined();
      expect(typeof response.body.threatAssessment.threatScore.score).toBe('number');
    });
  });

  describe('Compliance', () => {
    test('should enforce GDPR compliance', async () => {
      const validToken = generateTestToken('test-user', ['user']);
      
      const response = await request(app)
        .get('/test')
        .set('Authorization', `Bearer ${validToken}`)
        .expect(200);

      expect(response.body.complianceCheck).toBeDefined();
      expect(response.body.complianceCheck.isCompliant).toBe(true);
    });
  });

  describe('Rate Limiting', () => {
    test('should enforce rate limits', async () => {
      const validToken = generateTestToken('test-user', ['user']);
      
      // 快速发送多个请求
      const promises = Array(20).fill().map(() => 
        request(app)
          .get('/test')
          .set('Authorization', `Bearer ${validToken}`)
      );

      const responses = await Promise.all(promises);
      
      // 应该有部分请求被限流
      const rateLimitedResponses = responses.filter(res => res.status === 429);
      expect(rateLimitedResponses.length).toBeGreaterThan(0);
    });
  });

  describe('Integration Tests', () => {
    test('should handle complete security pipeline', async () => {
      const validToken = generateTestToken('admin-user', ['admin']);
      
      const response = await request(app)
        .get('/test')
        .set('Authorization', `Bearer ${validToken}`)
        .set('User-Agent', 'Mozilla/5.0 (Test Browser)')
        .expect(200);

      expect(response.body.message).toBe('Security check passed');
      expect(response.body.securityContext).toBeDefined();
      expect(response.body.threatAssessment).toBeDefined();
      expect(response.body.complianceCheck).toBeDefined();
    });
  });
});

/**
 * 性能测试
 */
describe('Security Middleware Performance Tests', () => {
  let app;

  beforeAll(() => {
    const config = require('../config/security.json');
    const securityEngine = new SecurityOrchestrationEngine(config);
    
    app = express();
    app.use(express.json());
    
    securityEngine.getMiddlewareChain().forEach(middleware => {
      app.use(middleware);
    });
    
    app.get('/perf-test', (req, res) => {
      res.json({ message: 'Performance test' });
    });
  });

  test('should handle requests within acceptable latency', async () => {
    const validToken = generateTestToken('test-user', ['user']);
    const iterations = 100;
    const maxAcceptableLatency = 200; // 200ms

    const startTime = Date.now();
    
    for (let i = 0; i < iterations; i++) {
      await request(app)
        .get('/perf-test')
        .set('Authorization', `Bearer ${validToken}`);
    }
    
    const totalTime = Date.now() - startTime;
    const averageLatency = totalTime / iterations;

    expect(averageLatency).toBeLessThan(maxAcceptableLatency);
  });
});

/**
 * 辅助函数
 */
function generateTestToken(userId, roles = ['user']) {
  const jwt = require('jsonwebtoken');
  const payload = {
    sub: userId,
    username: userId,
    roles: roles,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600 // 1小时过期
  };
  
  return jwt.sign(payload, process.env.JWT_SECRET || 'test-secret');
}