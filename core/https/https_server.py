"""
HTTPS服务器配置
提供SSL/TLS支持和安全配置
"""

import logging
import os
import ssl
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from core.async_main import async_main
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class SecurityConfig:
    """安全配置"""

    # SSL/TLS配置
    ssl_version: int = ssl.PROTOCOL_TLS_SERVER
    ssl_options: int = ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    ssl_ciphers: str = (
        "ECDHE-ECDSA-AES128-GCM-SHA256:"
        "ECDHE-RSA-AES128-GCM-SHA256:"
        "ECDHE-ECDSA-AES256-GCM-SHA384:"
        "ECDHE-RSA-AES256-GCM-SHA384:"
        "ECDHE-ECDSA-CHACHA20-POLY1305:"
        "ECDHE-RSA-CHACHA20-POLY1305"
    )

    # 安全头配置
    security_headers = {
        "Strict-Transport-Security": "max-age=31536000; include_sub_domains; preload",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' wss: https:; "
            "frame-ancestors 'none';"
        ),
    }

    # 信任的主机
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "*.example.com"]

    # 速率限制
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # 秒


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    def __init__(self, app: FastAPI, config: SecurityConfig):
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next):
        """添加安全头"""
        response = await call_next(request)

        # 添加安全头
        for header, value in self.config.security_headers.items():
            response.headers[header] = value

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""

    def __init__(self, app: FastAPI, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        """速率限制检查"""
        # 获取客户端IP
        client_ip = self._get_client_ip(request)

        # 检查速率限制
        current_time = time.time()
        window_start = current_time - self.config.rate_limit_window

        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []

        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.config.rate_limit_requests:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁,请稍后再试",
                headers={"Retry-After": str(self.config.rate_limit_window)},
            )

        # 记录当前请求
        self.requests[client_ip].append(current_time)

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制头
        response.headers["X-RateLimit-Limit"] = str(self.config.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.config.rate_limit_requests - len(self.requests[client_ip]))
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(window_start + self.config.rate_limit_window)
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 返回直连IP
        return request.client.host


class CertificateGenerator:
    """SSL证书生成器"""

    @staticmethod
    def generate_self_signed_cert(
        cert_file: str, key_file: str, domains: list[str] | None = None, valid_days: int = 365
    ) -> bool:
        """生成自签名证书"""
        try:
            import ipaddress

            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.x509.oid import NameOID

            domains = domains or ["localhost", "127.0.0.1"]

            # 生成私钥
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

            # 创建证书
            subject = issuer = x509.Name(
                [
                    x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
                    x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
                    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Athena Platform"),
                    x509.NameAttribute(NameOID.COMMON_NAME, domains[0]),
                ]
            )

            # 构建SAN扩展
            san_names = []
            for domain in domains:
                try:
                    # 尝试解析为IP地址
                    ip = ipaddress.ip_address(domain)
                    san_names.append(x509.IPAddress(ip))
                except ValueError:
                    # 不是IP地址,作为域名处理
                    san_names.append(x509.DNSName(domain))

            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(private_key.public_key())
                .add_extension(x509.SubjectAlternativeName(san_names), critical=False)
                .not_valid_before(datetime.datetime.utcnow())
                .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=valid_days))
                .sign(private_key, hashes.SHA256())
            )

            # 确保目录存在
            os.makedirs(os.path.dirname(cert_file), exist_ok=True)
            os.makedirs(os.path.dirname(key_file), exist_ok=True)

            # 写入证书文件
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            # 写入私钥文件
            with open(key_file, "wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

            logger.info(f"自签名证书已生成: {cert_file}, {key_file}")
            return True

        except ImportError:
            logger.error("需要安装cryptography库: pip install cryptography")
            return False
        except Exception as e:
            logger.error(f"生成证书失败: {e}")
            return False


class HTTPSServer:
    """HTTPS服务器"""

    def __init__(self, app: FastAPI, config: SecurityConfig | None = None):
        self.app = app
        self.config = config or SecurityConfig()

    def configure_security(self) -> Any:
        """配置安全设置"""
        # 添加HTTPS重定向中间件
        self.app.add_middleware(HTTPSRedirectMiddleware)

        # 添加受信任主机中间件
        self.app.add_middleware(TrustedHostMiddleware, allowed_hosts=self.config.trusted_hosts)

        # 添加安全头中间件
        self.app.add_middleware(SecurityHeadersMiddleware, config=self.config)

        # 添加速率限制中间件
        self.app.add_middleware(RateLimitMiddleware, config=self.config)

    def create_ssl_context(self, cert_file: str, key_file: str) -> ssl.SSLContext:
        """创建SSL上下文"""
        context = ssl.create_context(proto=self.config.ssl_version)

        # 设置SSL选项
        context.options |= self.config.ssl_options

        # 设置密码套件
        context.set_ciphers(self.config.ssl_ciphers)

        # 加载证书和私钥
        context.load_cert_chain(cert_file, key_file)

        # 验证证书
        logger.info(f"SSL证书已加载: {cert_file}")
        logger.info(f"SSL私钥已加载: {key_file}")

        return context

    async def run(
        self,
        host: str = "0.0.0.0",
        http_port: int = 8000,
        https_port: int = 8443,
        cert_file: str = "certs/server.crt",
        key_file: str = "certs/server.key",
        auto_generate_cert: bool = True,
    ):
        """运行HTTPS服务器"""
        # 配置安全设置
        self.configure_security()

        # 检查证书文件
        cert_path = Path(cert_file)
        key_path = Path(key_file)

        if not cert_path.exists() or not key_path.exists():
            if auto_generate_cert:
                logger.info("证书文件不存在,生成自签名证书...")
                if not CertificateGenerator.generate_self_signed_cert(cert_file, key_file):
                    raise RuntimeError("无法生成SSL证书")
            else:
                raise FileNotFoundError(f"证书文件不存在: {cert_file} 或 {key_file}")

        # 创建SSL上下文
        ssl_context = self.create_ssl_context(cert_file, key_file)

        # 配置HTTP服务器(重定向到HTTPS)
        http_config = uvicorn.Config(app=self.app, host=host, port=http_port, log_level="info")

        # 配置HTTPS服务器
        https_config = uvicorn.Config(
            app=self.app, host=host, port=https_port, ssl=ssl_context, log_level="info"
        )

        # 创建服务器实例
        http_server = uvicorn.Server(http_config)
        https_server = uvicorn.Server(https_config)

        logger.info(f"启动HTTP服务器(重定向到HTTPS): http://{host}:{http_port}")
        logger.info(f"启动HTTPS服务器: https://{host}:{https_port}")

        # 并发运行两个服务器
        import asyncio

        async def serve():
            await asyncio.gather(http_server.serve(), https_server.serve())

        asyncio.run(serve())


def create_https_app(
    title: str = "Athena HTTPS Server", config: SecurityConfig | None = None
) -> FastAPI:
    """创建HTTPS应用"""
    app = FastAPI(title=title)

    # 添加健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "https_enabled": True,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }

    @app.get("/security-info")
    async def security_info():
        """安全信息"""
        return {
            "security_headers": (
                config.security_headers if config else SecurityConfig.security_headers
            ),
            "trusted_hosts": config.trusted_hosts if config else SecurityConfig.trusted_hosts,
            "rate_limit": {
                "requests": (
                    config.rate_limit_requests if config else SecurityConfig.rate_limit_requests
                ),
                "window": config.rate_limit_window if config else SecurityConfig.rate_limit_window,
            },
        }

    return app


# 使用示例
@async_main
async def main():
    """主函数"""
    # 创建安全配置
    security_config = SecurityConfig()
    security_config.trusted_hosts = ["localhost", "127.0.0.1"]

    # 创建应用
    app = create_https_app("Athena融合平台", security_config)

    # 创建HTTPS服务器
    https_server = HTTPSServer(app, security_config)

    # 运行服务器
    await https_server.run(
        host="0.0.0.0",
        http_port=8000,
        https_port=8443,
        cert_file="certs/server.crt",
        key_file="certs/server.key",
    )


if __name__ == "__main__":
    import datetime
    import time

    logger.info("启动HTTPS服务器...")
    asyncio.run(main())
