/**
 * Athena API网关 - 高级安全中间件
 * Advanced Security Middleware for Athena API Gateway
 * 
 * 实现八大安全子系统的核心逻辑
 */

const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const crypto = require('crypto');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const winston = require('winston');

/**
 * 零信任安全中间件
 * Zero Trust Security Middleware
 */
class ZeroTrustMiddleware {
  constructor(config) {
    this.config = config.security.zeroTrust;
    this.policyEngine = null;
    this.contextAnalyzer = null;
    this.riskScoring = null;
    this.initializeServices();
  }

  async initializeServices() {
    // 初始化策略引擎
    this.policyEngine = new PolicyEngine(this.config.policyEngine);
    this.contextAnalyzer = new ContextAnalyzer();
    this.riskScoring = new RiskScoring();
  }

  middleware() {
    return async (req, res, next) => {
      try {
        // 1. 身份验证
        const identity = await this.verifyIdentity(req);
        
        // 2. 设备信任评估
        const deviceTrust = await this.assessDevice(req);
        
        // 3. 位置风险评估
        const locationRisk = await this.assessLocation(req);
        
        // 4. 行为异常检测
        const behaviorRisk = await this.analyzeBehavior(req);
        
        // 5. 综合风险评分
        const riskScore = await this.riskScoring.calculate({
          identity, deviceTrust, locationRisk, behaviorRisk
        });
        
        // 6. 策略决策
        const decision = await this.policyEngine.decide(riskScore, req);
        
        // 7. 执行决策
        if (decision.allowed) {
          req.securityContext = {
            identity,
            riskScore,
            decision,
            trustLevel: this.calculateTrustLevel(riskScore)
          };
          next();
        } else {
          res.status(403).json({
            error: 'Access denied',
            reason: decision.reason,
            riskScore: riskScore.score
          });
        }
      } catch (error) {
        winston.error('Zero trust middleware error:', error);
        res.status(500).json({ error: 'Security check failed' });
      }
    };
  }

  async verifyIdentity(req) {
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    if (!token) {
      throw new Error('No authentication token provided');
    }

    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      
      // 验证令牌是否在吊销列表中
      const isRevoked = await this.checkTokenRevocation(decoded.jti);
      if (isRevoked) {
        throw new Error('Token has been revoked');
      }

      return {
        userId: decoded.sub,
        username: decoded.username,
        roles: decoded.roles,
        sessionId: decoded.jti,
        issuedAt: decoded.iat,
        expiresAt: decoded.exp
      };
    } catch (error) {
      throw new Error('Invalid authentication token');
    }
  }

  async assessDevice(req) {
    const deviceFingerprint = this.generateDeviceFingerprint(req);
    
    // 检查设备是否在信任列表中
    const trustedDevice = await this.checkTrustedDevice(deviceFingerprint);
    
    return {
      fingerprint: deviceFingerprint,
      isTrusted: trustedDevice.isTrusted,
      trustScore: trustedDevice.score,
      deviceInfo: this.extractDeviceInfo(req)
    };
  }

  generateDeviceFingerprint(req) {
    const userAgent = req.headers['user-agent'] || '';
    const acceptLanguage = req.headers['accept-language'] || '';
    const acceptEncoding = req.headers['accept-encoding'] || '';
    
    return crypto.createHash('sha256')
      .update(userAgent + acceptLanguage + acceptEncoding)
      .digest('hex');
  }

  async assessLocation(req) {
    const clientIP = req.ip || req.connection.remoteAddress;
    
    // IP地理位置检查
    const geoInfo = await this.getGeoLocation(clientIP);
    
    // 检查是否为已知恶意IP
    const isMalicious = await this.checkMaliciousIP(clientIP);
    
    return {
      ip: clientIP,
      country: geoInfo.country,
      region: geoInfo.region,
      isMalicious,
      riskScore: this.calculateLocationRisk(geoInfo, isMalicious)
    };
  }

  async analyzeBehavior(req) {
    const userId = req.securityContext?.identity?.userId;
    
    if (!userId) {
      return { riskScore: 0.8, anomalyDetected: true };
    }

    // 获取用户历史行为模式
    const behaviorProfile = await this.getUserBehaviorProfile(userId);
    
    // 分析当前请求行为
    const currentBehavior = this.extractBehaviorFeatures(req);
    
    // 异常检测
    const anomalyScore = this.detectAnomalies(behaviorProfile, currentBehavior);
    
    return {
      currentBehavior,
      historicalProfile: behaviorProfile,
      anomalyScore,
      riskLevel: this.categorizeRisk(anomalyScore)
    };
  }

  calculateTrustLevel(riskScore) {
    if (riskScore.score < 30) return 'high';
    if (riskScore.score < 60) return 'medium';
    if (riskScore.score < 80) return 'low';
    return 'minimal';
  }
}

/**
 * 高级认证中间件
 * Advanced Authentication Middleware
 */
class AdvancedAuthenticationMiddleware {
  constructor(config) {
    this.config = config.security.authentication;
    this.riskAnalyzer = new RiskAnalyzer();
    this.factorRegistry = new Map();
    this.setupAuthenticationFactors();
  }

  setupAuthenticationFactors() {
    this.factorRegistry.set('password', new PasswordFactor());
    this.factorRegistry.set('totp', new TOTPFactor());
    this.factorRegistry.set('push', new PushFactor());
    this.factorRegistry.set('biometric', new BiometricFactor());
    this.factorRegistry.set('hardware-key', new HardwareKeyFactor());
  }

  middleware() {
    return async (req, res, next) => {
      try {
        // 1. 风险评估
        const riskProfile = await this.riskAnalyzer.assess(req);
        
        // 2. 动态因子选择
        const requiredFactors = this.selectFactors(riskProfile);
        
        // 3. 验证因子
        const authResult = await this.authenticateFactors(req, requiredFactors);
        
        // 4. 适应性响应
        if (authResult.success) {
          req.authContext = {
            riskProfile,
            verifiedFactors: authResult.verifiedFactors,
            trustLevel: authResult.trustLevel
          };
          next();
        } else {
          res.status(401).json({
            error: 'Authentication failed',
            reason: authResult.reason,
            requiredFactors: requiredFactors.map(f => f.type)
          });
        }
      } catch (error) {
        winston.error('Advanced authentication middleware error:', error);
        res.status(500).json({ error: 'Authentication service unavailable' });
      }
    };
  }

  selectFactors(riskProfile) {
    const baseFactors = ['password'];
    
    if (riskProfile.score > 30) baseFactors.push('totp');
    if (riskProfile.score > 60) baseFactors.push('push');
    if (riskProfile.score > 80) baseFactors.push('biometric');
    
    return baseFactors.map(type => ({
      type,
      factor: this.factorRegistry.get(type),
      strength: this.getFactorStrength(type)
    }));
  }

  async authenticateFactors(req, requiredFactors) {
    const results = [];
    
    for (const { type, factor, strength } of requiredFactors) {
      try {
        const result = await factor.verify(req);
        results.push({
          type,
          success: result.success,
          strength,
          details: result
        });
      } catch (error) {
        results.push({
          type,
          success: false,
          strength,
          error: error.message
        });
      }
    }

    return this.evaluateAuthResults(results);
  }
}

/**
 * API安全防护中间件
 * API Security Protection Middleware
 */
class APISecurityMiddleware {
  constructor(config) {
    this.config = config.security.apiSecurity;
    this.wafEngine = new WAFEngine(this.config.owasp);
    this.inputValidator = new InputValidator(this.config.inputValidation);
    this.rateLimiter = this.setupRateLimiting();
  }

  middleware() {
    return async (req, res, next) => {
      try {
        // 1. WAF防护
        const wafResult = await this.wafEngine.processRequest(req);
        if (!wafResult.allowed) {
          return res.status(403).json({
            error: 'Request blocked by WAF',
            reason: wafResult.reason,
            ruleId: wafResult.ruleId
          });
        }

        // 2. 输入验证
        const validationResult = await this.inputValidator.validate(req);
        if (!validationResult.valid) {
          return res.status(400).json({
            error: 'Invalid input',
            details: validationResult.errors
          });
        }

        // 3. 限流检查 (由express-rate-limit自动处理)
        
        req.securityChecks = {
          waf: wafResult,
          inputValidation: validationResult
        };
        
        next();
      } catch (error) {
        winston.error('API security middleware error:', error);
        res.status(500).json({ error: 'Security check failed' });
      }
    };
  }

  setupRateLimiting() {
    return rateLimit({
      windowMs: this.config.rateLimit.global.window,
      max: this.config.rateLimit.global.max,
      message: {
        error: 'Rate limit exceeded',
        retryAfter: Math.ceil(this.config.rateLimit.global.window / 1000)
      },
      standardHeaders: true,
      legacyHeaders: false,
      keyGenerator: (req) => {
        // 根据用户和IP组合限制
        const userId = req.authContext?.identity?.userId || req.ip;
        return `user:${userId}:ip:${req.ip}`;
      }
    });
  }
}

/**
 * 数据保护中间件
 * Data Protection Middleware
 */
class DataProtectionMiddleware {
  constructor(config) {
    this.config = config.security.dataProtection;
    this.encryptionService = new EncryptionService(this.config.encryption);
    this.dlpEngine = new DLPEngine(this.config.dataLossPrevention);
    this.dataClassifier = new DataClassifier();
  }

  middleware() {
    return async (req, res, next) => {
      try {
        // 1. 数据分类
        if (req.body) {
          const classification = await this.dataClassifier.classify(req.body);
          req.dataClassification = classification;
        }

        // 2. DLP扫描
        if (req.body) {
          const dlpResult = await this.dlpEngine.scan(req.body);
          if (dlpResult.violations.length > 0) {
            return res.status(403).json({
              error: 'Data policy violation',
              violations: dlpResult.violations
            });
          }
        }

        // 3. 响应数据保护
        const originalJson = res.json;
        res.json = async (data) => {
          if (data) {
            // 数据保护处理
            const protectedData = await this.protectResponseData(data, req);
            return originalJson.call(res, protectedData);
          }
          return originalJson.call(res, data);
        };

        next();
      } catch (error) {
        winston.error('Data protection middleware error:', error);
        res.status(500).json({ error: 'Data protection failed' });
      }
    };
  }

  async protectResponseData(data, req) {
    // 敏感数据脱敏
    if (req.dataClassification?.level === 'sensitive') {
      return this.sanitizeSensitiveData(data);
    }

    // PII检测和处理
    const piiData = await this.dlpEngine.detectPII(data);
    if (piiData.found) {
      return this.maskPIIData(data, piiData.locations);
    }

    return data;
  }
}

/**
 * 威胁情报中间件
 * Threat Intelligence Middleware
 */
class ThreatIntelligenceMiddleware {
  constructor(config) {
    this.config = config.security.threatIntelligence;
    this.threatFeeds = new Map();
    this.mlDetector = new MLThreatDetector(this.config.mlDetection);
    this.behaviorAnalyzer = new BehaviorAnalyzer(this.config.behaviorAnalysis);
    this.initializeThreatFeeds();
  }

  async initializeThreatFeeds() {
    for (const feed of this.config.feeds) {
      this.threatFeeds.set(feed.name, new ThreatFeed(feed));
    }
  }

  middleware() {
    return async (req, res, next) => {
      try {
        // 1. 威胁情报检查
        const threatMatches = await this.checkThreatFeeds(req);
        
        // 2. ML威胁检测
        const mlThreats = await this.mlDetector.detect(req);
        
        // 3. 行为分析
        const behaviorAnalysis = await this.behaviorAnalyzer.analyze(req);
        
        // 4. 威胁评分
        const threatScore = this.calculateThreatScore(
          threatMatches, mlThreats, behaviorAnalysis
        );

        req.threatAssessment = {
          threatScore,
          threatMatches,
          mlThreats,
          behaviorAnalysis,
          isBlocked: threatScore.score > 0.8
        };

        if (req.threatAssessment.isBlocked) {
          return res.status(403).json({
            error: 'Request blocked due to threat detection',
            threatScore: threatScore.score,
            reasons: threatScore.reasons
          });
        }

        next();
      } catch (error) {
        winston.error('Threat intelligence middleware error:', error);
        res.status(500).json({ error: 'Threat detection failed' });
      }
    };
  }

  async checkThreatFeeds(req) {
    const clientIP = req.ip;
    const userAgent = req.headers['user-agent'] || '';
    const hostname = req.hostname;

    const matches = [];
    
    for (const [name, feed] of this.threatFeeds) {
      const match = await feed.check({
        ip: clientIP,
        userAgent,
        hostname,
        url: req.url,
        method: req.method
      });
      
      if (match.isMatch) {
        matches.push({
          feedName: name,
          type: feed.type,
          severity: match.severity,
          details: match.details
        });
      }
    }

    return matches;
  }

  calculateThreatScore(threatMatches, mlThreats, behaviorAnalysis) {
    const threatScore = {
      score: 0,
      reasons: []
    };

    // 威胁情报评分 (权重: 40%)
    if (threatMatches.length > 0) {
      const feedScore = threatMatches.reduce((sum, match) => {
        const severityMap = { low: 0.2, medium: 0.5, high: 0.8, critical: 1.0 };
        return sum + (severityMap[match.severity] || 0);
      }, 0) / threatMatches.length;
      
      threatScore.score += feedScore * 0.4;
      threatScore.reasons.push(`Threat intelligence matches: ${threatMatches.length}`);
    }

    // ML检测评分 (权重: 35%)
    if (mlThreats.isThreat) {
      threatScore.score += mlThreats.confidence * 0.35;
      threatScore.reasons.push(`ML threat detection: ${mlThreats.confidence}`);
    }

    // 行为分析评分 (权重: 25%)
    if (behaviorAnalysis.isSuspicious) {
      threatScore.score += behaviorAnalysis.anomalyScore * 0.25;
      threatScore.reasons.push(`Behavioral anomaly: ${behaviorAnalysis.anomalyScore}`);
    }

    return threatScore;
  }
}

/**
 * 合规性中间件
 * Compliance Middleware
 */
class ComplianceMiddleware {
  constructor(config) {
    this.config = config.security.compliance;
    this.gdprEngine = new GDPRComplianceEngine(this.config.gdpr);
    this.soc2Checker = new SOC2Checker(this.config.soc2);
    this.auditLogger = new AuditLogger();
  }

  middleware() {
    return async (req, res, next) => {
      try {
        // 1. GDPR合规检查
        const gdprResult = await this.gdprEngine.checkCompliance(req);
        
        // 2. SOC2合规检查
        const soc2Result = await this.soc2Checker.checkCompliance(req);
        
        // 3. 审计日志记录
        await this.auditLogger.log({
          timestamp: new Date(),
          request: this.sanitizeRequest(req),
          compliance: { gdpr: gdprResult, soc2: soc2Result },
          user: req.authContext?.identity?.userId,
          ip: req.ip
        });

        req.complianceCheck = {
          gdpr: gdprResult,
          soc2: soc2Result,
          isCompliant: gdprResult.compliant && soc2Result.compliant
        };

        if (!req.complianceCheck.isCompliant) {
          return res.status(403).json({
            error: 'Compliance violation',
            gdpr: gdprResult.violations,
            soc2: soc2Result.violations
          });
        }

        next();
      } catch (error) {
        winston.error('Compliance middleware error:', error);
        res.status(500).json({ error: 'Compliance check failed' });
      }
    };
  }

  sanitizeRequest(req) {
    return {
      method: req.method,
      url: req.url,
      headers: {
        'user-agent': req.headers['user-agent'],
        'content-type': req.headers['content-type']
      },
      bodySize: JSON.stringify(req.body || {}).length,
      timestamp: new Date()
    };
  }
}

/**
 * 安全编排引擎
 * Security Orchestration Engine
 */
class SecurityOrchestrationEngine {
  constructor(config) {
    this.config = config;
    this.middlewares = [];
    this.setupSecurityPipeline();
  }

  setupSecurityPipeline() {
    // 按优先级加载安全中间件
    this.middlewares = [
      { name: 'zeroTrust', middleware: new ZeroTrustMiddleware(this.config).middleware() },
      { name: 'advancedAuth', middleware: new AdvancedAuthenticationMiddleware(this.config).middleware() },
      { name: 'apiSecurity', middleware: new APISecurityMiddleware(this.config).middleware() },
      { name: 'dataProtection', middleware: new DataProtectionMiddleware(this.config).middleware() },
      { name: 'threatIntelligence', middleware: new ThreatIntelligenceMiddleware(this.config).middleware() },
      { name: 'compliance', middleware: new ComplianceMiddleware(this.config).middleware() }
    ];
  }

  getMiddlewareChain() {
    return this.middlewares.map(m => m.middleware);
  }

  async executeSecurityChecks(req) {
    const results = {};
    
    for (const { name, middleware } of this.middlewares) {
      try {
        // 创建模拟的res对象来收集中间件结果
        const mockRes = {
          status: () => ({ json: () => {} }),
          json: () => {}
        };
        
        await middleware(req, mockRes, () => {});
        
        results[name] = {
          success: true,
          context: req[`${name}Context`] || req[`${name}Check`]
        };
      } catch (error) {
        results[name] = {
          success: false,
          error: error.message
        };
      }
    }
    
    return results;
  }
}

// 导出主要类
module.exports = {
  SecurityOrchestrationEngine,
  ZeroTrustMiddleware,
  AdvancedAuthenticationMiddleware,
  APISecurityMiddleware,
  DataProtectionMiddleware,
  ThreatIntelligenceMiddleware,
  ComplianceMiddleware
};