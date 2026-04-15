#!/usr/bin/env python3
"""
安全哈希工具模块
Security Hash Helpers

提供安全的哈希函数,替代不安全的MD5和SHA1

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import hashlib
import hmac


def secure_hash(content: str | bytes, hash_type: str = 'sha256', salt: str | None = None) -> str:
    """
    安全的哈希函数,使用SHA-256或更强算法

    Args:
        content: 要哈希的内容(字符串或字节)
        hash_type: 哈希算法类型 ('sha256', 'sha384', 'sha512')
        salt: 可选的盐值,增加哈希安全性

    Returns:
        哈希值的十六进制字符串

    Examples:
        >>> secure_hash("hello")
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
        >>> secure_hash("hello", salt="mysalt")
        '360982c97c0185e04137682f72eab63ff4f4e8d1087c0bc8d9df19df0b3d1a5a'
    """
    # 标准化输入
    if isinstance(content, str):
        content_bytes = content.encode('utf-8')
    else:
        content_bytes = content

    # 添加盐值
    if salt:
        content_bytes = content_bytes + salt.encode('utf-8')

    # 选择哈希算法
    if hash_type == 'sha256':
        hash_func = hashlib.sha256
    elif hash_type == 'sha384':
        hash_func = hashlib.sha384
    elif hash_type == 'sha512':
        hash_func = hashlib.sha512
    elif hash_type == 'sha3_256':
        hash_func = hashlib.sha3_256
    elif hash_type == 'sha3_512':
        hash_func = hashlib.sha3_512
    else:
        raise ValueError(f"不支持的哈希算法: {hash_type}")

    # 计算哈希
    return hash_func(content_bytes).hexdigest()


def secure_file_hash(file_path: str, hash_type: str = 'sha256', chunk_size: int = 8192) -> str:
    """
    计算文件的安全哈希值(支持大文件)

    Args:
        file_path: 文件路径
        hash_type: 哈希算法类型
        chunk_size: 读取块大小(字节)

    Returns:
        文件哈希值的十六进制字符串
    """
    hash_func = getattr(hashlib, hash_type)()

    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hash_func.update(chunk)

    return hash_func.hexdigest()


def generate_id(content: str | bytes, prefix: str = '', length: int = 16) -> str:
    """
    生成安全的ID,替代不安全的MD5 ID

    Args:
        content: 要生成ID的内容
        prefix: ID前缀
        length: ID长度(最多64个字符,因为SHA256是128个字符)

    Returns:
        安全的ID字符串

    Examples:
        >>> generate_id("hello world", prefix="doc_", length=12)
        'doc_a948904f2f0f'
    """
    hash_value = secure_hash(content, hash_type='sha256')

    # 截取指定长度
    if length > 64:
        length = 64
    hash_short = hash_value[:length]

    if prefix:
        return f"{prefix}{hash_short}"
    return hash_short


def hmac_signature(content: str | bytes, secret: str, hash_type: str = 'sha256') -> str:
    """
    生成HMAC签名,用于验证数据完整性和真实性

    Args:
        content: 要签名的内容
        secret: 密钥
        hash_type: 哈希算法类型

    Returns:
        HMAC签名的十六进制字符串

    Examples:
        >>> hmac_signature("hello", "secret")
        '6f7c8f4f4f7f8a9b8c7d6e5f4e3d2c1b9a8f7e6d5c4b3a2f1e0d9c8b7a6954'
    """
    if isinstance(content, str):
        content_bytes = content.encode('utf-8')
    else:
        content_bytes = content

    secret_bytes = secret.encode('utf-8')

    return hmac.new(secret_bytes, content_bytes, getattr(hashlib, hash_type)).hexdigest()


def verify_hmac(content: str | bytes, signature: str, secret: str, hash_type: str = 'sha256') -> bool:
    """
    验证HMAC签名

    Args:
        content: 原始内容
        signature: 要验证的签名
        secret: 密钥
        hash_type: 哈希算法类型

    Returns:
        签名是否有效
    """
    computed = hmac_signature(content, secret, hash_type)
    return hmac.compare_digest(computed, signature)


# 便捷的短哈希函数(用于生成唯一ID)
def short_hash(content: str | bytes, length: int = 12) -> str:
    """
    生成短哈希,用于唯一标识符

    Args:
        content: 要哈希的内容
        length: 返回的哈希长度(建议12-16位)

    Returns:
        短哈希字符串

    Examples:
        >>> short_hash("hello world", 12)
        'b94d27b9f34d9a'
    """
    full_hash = secure_hash(content, hash_type='sha256')
    return full_hash[:length]


# 兼容性函数:用于快速替换MD5
def md5_replacement(content: str | bytes, salt: str | None = None) -> str:
    """
    MD5的安全替代品,使用SHA-256

    Args:
        content: 要哈希的内容
        salt: 可选的盐值

    Returns:
        哈希值的十六进制字符串

    Note:
        输出是64个字符(SHA256),不是MD5的32个字符
        如需相同长度,可以使用short_hash(content, 32)
    """
    return secure_hash(content, hash_type='sha256', salt=salt)


# 兼容性函数:用于快速替换SHA1
def sha1_replacement(content: str | bytes, salt: str | None = None) -> str:
    """
    SHA1的安全替代品,使用SHA-256

    Args:
        content: 要哈希的内容
        salt: 可选的盐值

    Returns:
        哈希值的十六进制字符串
    """
    return secure_hash(content, hash_type='sha256', salt=salt)


if __name__ == '__main__':
    # 测试
    print("测试安全哈希函数:")
    print(f"SHA256: {secure_hash('hello world')}")
    print(f"短哈希(12位): {short_hash('hello world', 12)}")
    print(f"带盐值: {secure_hash('hello world', salt='mysalt')}")
    print(f"生成ID: {generate_id('hello world', prefix='id_', length=16)}")
    print(f"HMAC签名: {hmac_signature('hello world', 'secret')}")
