# Gateway HTTPS问题诊断报告

**日期**: 2026-04-23
**问题**: HTTPS连接失败，错误 `tlsv1 alert protocol version`

## 问题现象

```bash
$ curl -sk https://localhost:8005/health
curl: (35) LibreSSL/3.3.6: error:1404B42E:SSL routines:ST_CONNECT:tlsv1 alert protocol version
```

## 已尝试的修复

### 1. 添加TLSConfig到http.Server ✅

在 `cmd/gateway/main.go` 中添加：

```go
server := &http.Server{
    ...
    TLSConfig: &tls.Config{
        MinVersion: tls.VersionTLS12,
        MaxVersion: tls.VersionTLS13,
        CipherSuites: []uint16{
            tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
            tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
            tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
            tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
            tls.TLS_AES_128_GCM_SHA256,
            tls.TLS_AES_256_GCM_SHA384,
            tls.TLS_CHACHA20_POLY1305_SHA256,
        },
        PreferServerCipherSuites: true,
    },
}
```

### 2. 验证证书和私钥 ✅

```bash
# 证书MD5
openssl x509 -noout -modulus -in certs/server.crt | openssl md5
00a45820ef51f2bf9468bb0401e37ab4

# 私钥MD5
openssl rsa -noout -modulus -in certs/server.key | openssl md5
00a45820ef51f2bf9468bb0401e37ab4
```

证书和私钥匹配 ✅

### 3. 证书详情 ✅

```
Issuer: C=CN, ST=Beijing, L=Beijing, O=Athena, CN=athena.local
Subject: C=CN, ST=Beijing, L=Beijing, O=Athena, CN=athena.local
DNS:athena.local, DNS:localhost, IP Address:127.0.0.1
```

证书有效 ✅

### 4. HTTP模式测试 ✅

禁用TLS后，HTTP工作正常：

```bash
$ curl -s http://localhost:8005/health
{"error":"不支持的API版本","success":false,"valid_versions":[],"version":"v1"}
```

## 根本原因分析

错误 `tlsv1 alert protocol version` 通常表示：

1. **客户端和服务器TLS版本不匹配**
   - 客户端支持TLS 1.3
   - 服务器可能配置了不兼容的TLS版本

2. **密码套件不匹配**
   - 服务器配置的密码套件客户端不支持
   - 客户端提议的密码套件服务器不接受

3. **可能的Go TLS配置问题**
   - `tls.Config` 配置可能不完整
   - 缺少必要的字段（如 `ServerName`）

## 待排查的方向

### 1. 检查Go编译时的TLS配置

```bash
# 查看编译后的二进制是否包含TLS配置
strings gateway | grep -i tls
```

### 2. 添加调试日志

在网关启动时添加TLS配置的日志输出：

```go
logging.LogInfo("TLS配置",
    logging.String("min_version", cfg.TLS.MinVersion),
    logging.String("max_version", cfg.TLS.MaxVersion),
)
```

### 3. 检查运行时TLS握手

使用Wireshark或tcpdump捕获TLS握手过程：

```bash
sudo tcpdump -i lo0 -w tls_handshake.pcap port 8005
```

### 4. 尝试简化TLS配置

移除 `CipherSuites` 配置，让Go使用默认值：

```go
TLSConfig: &tls.Config{
    MinVersion: tls.VersionTLS12,
},
```

## 临时解决方案

由于HTTP模式工作正常，建议：

1. **短期**: 使用Nginx反向代理处理TLS
2. **中期**: 深入调试Go TLS配置
3. **长期**: 完善TLS配置并添加测试

## 推荐的下一步

1. 添加TLS配置调试日志
2. 简化TLS配置测试
3. 检查Go版本和tls包版本
4. 考虑使用Let's Encrypt证书

## 相关文件

- 网关主程序: `/Users/xujian/Athena工作平台/gateway-unified/cmd/gateway/main.go`
- TLS配置: `/Users/xujian/Athena工作平台/gateway-unified/config/config.yaml`
- 证书文件: `/Users/xujian/Athena工作平台/gateway-unified/certs/`
- 网关日志: `/Users/xujian/Athena工作平台/gateway-unified/gateway.log`
