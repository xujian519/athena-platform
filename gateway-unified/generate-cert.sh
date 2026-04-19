#!/bin/bash
# 生成自签名SSL证书（用于测试/开发环境）

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${SCRIPT_DIR}/certs"
CERT_FILE="${CERT_DIR}/gateway.crt"
KEY_FILE="${CERT_DIR}/gateway.key"

echo -e "${YELLOW}生成自签名SSL证书...${NC}"

# 创建证书目录
mkdir -p "${CERT_DIR}"

# 生成私钥和证书
openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "${KEY_FILE}" \
    -out "${CERT_FILE}" \
    -days 365 \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=Athena/CN=gateway.local" \
    -addext "subjectAltName=DNS:gateway.local,DNS:localhost,IP:127.0.0.1"

echo -e "${GREEN}✅ 证书生成成功!${NC}"
echo ""
echo "证书文件: ${CERT_FILE}"
echo "私钥文件: ${KEY_FILE}"
echo ""
echo -e "${YELLOW}配置示例:${NC}"
echo "server:"
echo "  tls:"
echo "    enabled: true"
echo "    cert_file: ${CERT_FILE}"
echo "    key_file: ${KEY_FILE}"
echo ""
echo -e "${YELLOW}⚠️  警告: 此证书仅用于测试/开发环境，生产环境请使用正式的SSL证书!${NC}"
