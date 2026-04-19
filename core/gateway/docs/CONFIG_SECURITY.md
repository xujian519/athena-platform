# Athena API Gateway - 配置管理安全指南

> **版本**: 1.0  
> **更新日期**: 2026-02-20  
> **适用范围**: 生产环境配置安全管理

---

## 🎯 概述

本文档提供Athena API网关配置管理的安全最佳实践，确保敏感信息安全，防止配置泄露，并符合生产环境的安全要求。

---

## 🔒 核心安全原则

### 1. 最小权限原则
- 配置文件和密钥文件权限设置为 `600` (仅所有者可读写)
- 运行服务使用非特权用户
- 最小化环境变量的访问范围

### 2. 分离原则
- 开发/测试/生产环境配置完全分离
- 敏感信息永不硬编码在配置文件中
- 使用不同的配置管理策略处理不同环境

### 3. 加密原则
- 传输过程中的配置数据必须加密
- 静态配置文件存储在安全位置
- 密钥管理系统用于高敏感度信息

---

## 🚨 立即安全风险

### 当前发现的问题

1. **JWT密钥硬编码** 
   - 位置: `configs/config.yaml:32`
   - 风险: 高 - 可能导致认证绕过
   - 状态: 🔴 严重

2. **CSRF密钥缺失验证**
   - 位置: `configs/config.yaml:123`
   - 风险: 中 - CSRF攻击风险
   - 状态: 🟡 中等

3. **Redis密码为空**
   - 位置: `configs/config.yaml:21`
   - 风险: 低 - 仅影响开发环境
   - 状态: 🟡 中等

---

## ✅ 安全强化措施

### 1. 环境变量迁移

#### 已完成
- ✅ `config.prod.yaml` 使用环境变量获取敏感信息
- ✅ 配置验证器增强，检查不安全的默认值
- ✅ 生产配置验证脚本 `scripts/validate-config.sh`

#### 待完成
- ⏳ 所有环境配置迁移到环境变量
- ⏳ Kubernetes Secrets集成
- ⏳ 密钥轮换机制

### 2. 配置验证增强

#### 新增验证规则
```go
// 检查不安全的默认值
unsafeDefaults := []string{
    "athena-gateway-jwt-secret-key-change-in-production",
    "athena-gateway-dev-jwt-secret-not-for-production",
    "your-secret-key-change-in-production",
    "test-secret",
    "dev-secret",
    "default-secret",
}

for _, unsafe := range unsafeDefaults {
    if cfg.JWTSecret == unsafe {
        return fmt.Errorf("JWT_SECRET appears to be using an unsafe default value: %s", unsafe)
    }
}
```

#### 密钥强度检查
- JWT_SECRET: 最少32字符
- CSRF_SECRET: 最少16字符
- 包含大小写字母、数字、特殊字符

### 3. 访问控制

#### 文件权限
```bash
# 设置配置文件权限
chmod 600 configs/config.prod.yaml
chmod 700 scripts/validate-config.sh

# 设置所有者
chown athena:athena configs/config.prod.yaml
```

#### 目录结构
```
configs/
├── config.yaml          # 开发环境 (包含警告注释)
├── config.dev.yaml      # 开发环境
├── config.prod.yaml     # 生产环境 (仅环境变量)
├── config.staging.yaml  # 预发布环境
└── .env.example       # 环境变量模板 (不包含真实密钥)
```

---

## 🔧 实施指南

### 1. 环境变量设置

#### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: athena-gateway-secrets
type: Opaque
data:
  JWT_SECRET: <base64-encoded-jwt-secret>
  REDIS_PASSWORD: <base64-encoded-redis-password>
  CSRF_SECRET: <base64-encoded-csrf-secret>
```

#### Docker Compose
```yaml
services:
  gateway:
    environment:
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
      - REDIS_PASSWORD_FILE=/run/secrets/redis_password
    secrets:
      - jwt_secret
      - redis_password
```

#### 系统环境变量
```bash
# /etc/environment
JWT_SECRET=your-super-secure-jwt-secret-here
REDIS_PASSWORD=your-redis-password-here
CSRF_SECRET=your-csrf-secret-here
LOG_LEVEL=info
```

### 2. 配置验证流程

#### 部署前检查
```bash
# 1. 运行验证脚本
./scripts/validate-config.sh

# 2. 检查退出码
if [ $? -eq 0 ]; then
    echo "✅ 配置验证通过"
else
    echo "❌ 配置验证失败"
    exit 1
fi
```

#### CI/CD集成
```yaml
# .github/workflows/deploy.yml
- name: Validate Configuration
  run: |
    chmod +x scripts/validate-config.sh
    ./scripts/validate-config.sh
```

---

## 📋 安全检查清单

### 部署前检查 ✅
- [ ] 环境变量已设置 (`./scripts/validate-config.sh`)
- [ ] 配置文件权限正确 (`chmod 600`)
- [ ] 敏感信息不在代码仓库中
- [ ] 使用生产配置文件 (`config.prod.yaml`)
- [ ] Kubernetes Secrets已创建
- [ ] 密钥轮换计划已制定

### 运行时检查 ✅
- [ ] 配置热重载正常工作
- [ ] 日志中不包含敏感信息
- [ ] 健康检查端点正常
- [ ] 监控指标正常收集
- [ ] 错误日志不包含密钥

---

## 🔄 密钥轮换策略

### 轮换周期
- **JWT_SECRET**: 每90天轮换
- **CSRF_SECRET**: 每180天轮换
- **REDIS_PASSWORD**: 每120天轮换

### 轮换流程
1. 生成新密钥
2. 更新Kubernetes Secrets
3. 重启相关服务
4. 验证新密钥生效
5. 监控异常访问

### 应急响应
- 发现密钥泄露 → 立即轮换所有密钥
- 异常访问模式 → 启用增强监控
- 配置文件损坏 → 使用备份恢复

---

## 📞 监控和告警

### 安全监控指标
- JWT验证失败率
- 配置加载错误次数
- 敏感信息访问尝试
- 密钥轮换状态

### 告警规则
```yaml
# Prometheus告警规则
groups:
  - name: athena-gateway-security
    rules:
      - alert: GatewayJWTValidationFailure
        expr: rate(gateway_jwt_validation_failures_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
```

---

## 📚 参考资源

- [12-Factor App Methodology](https://12factor.net/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [OWASP Configuration Security](https://owasp.org/www-project-configuration-security/)
- [Go Configuration Best Practices](https://github.com/spf13/viper)

---

**📞 联系方式**: 如有安全问题，请联系安全团队
**🔄 更新频率**: 每季度审查和更新