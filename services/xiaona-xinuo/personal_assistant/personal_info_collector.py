#!/usr/bin/env python3
"""
个人信息收集和保护系统
Personal Information Collection and Protection System
"""

import os
from core.async_main import async_main
import sys
import json
import logging
from core.logging_config import setup_logging
from pathlib import Path
from datetime import datetime
import hashlib
import base64
from cryptography.fernet import Fernet
from typing import Dict, List, Any
import sqlite3
import shutil

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class PersonalInfoCollector:
    """个人信息收集和保护器"""

    def __init__(self):
        self.source_dir = Path("/Users/xujian/Nutstore Files/13-Markdown/05个人")
        self.storage_dir = Path("/Users/xujian/Athena工作平台/personal_secure_storage")
        self.db_path = self.storage_dir / "personal_info.db"

        # 创建存储目录
        self.storage_dir.mkdir(exist_ok=True)

        # 初始化加密
        self.init_encryption()

        # 初始化数据库
        self.init_database()

    def init_encryption(self) -> Any:
        """初始化加密系统"""
        # 生成或加载加密密钥
        key_path = self.storage_dir / ".encryption_key"

        if key_path.exists():
            with open(key_path, 'rb') as f:
                key = f.read()
                # 密钥文件直接存储原始二进制数据
        else:
            # 生成新密钥
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)  # 直接存储二进制，不进行base64编码
            logger.info("🔑 生成新的加密密钥")

        self.cipher = Fernet(key)
        logger.info("✅ 加密系统初始化完成")

    def init_database(self) -> Any:
        """初始化数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 创建表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personal_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                content_type TEXT DEFAULT 'text',
                sensitivity_level INTEGER DEFAULT 1,  -- 1:普通 2:敏感 3:高度敏感
                encryption_type TEXT DEFAULT 'fernet',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purpose TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info("✅ 数据库初始化完成")

    def collect_files(self) -> Any:
        """收集个人信息文件"""
        logger.info(f"📁 扫描个人信息目录: {self.source_dir}")

        if not self.source_dir.exists():
            logger.error(f"❌ 目录不存在: {self.source_dir}")
            return {}

        collected_info = {}

        # 遍历所有文件
        for item in self.source_dir.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(self.source_dir)
                file_type = self.detect_file_type(item)

                # 读取文件内容
                try:
                    content = self.read_file_content(item)
                    if content:
                        collected_info[str(relative_path)] = {
                            "file_path": str(item),
                            "file_name": item.name,
                            "file_type": file_type,
                            "content": content,
                            "size": item.stat().st_size,
                            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        }
                        logger.info(f"  📄 收集: {relative_path} ({item.stat().st_size} bytes)")
                except Exception as e:
                    logger.error(f"  ❌ 读取失败 {relative_path}: {e}")

        logger.info(f"✅ 共收集 {len(collected_info)} 个文件")
        return collected_info

    def detect_file_type(self, file_path: Path) -> str:
        """检测文件类型"""
        if "密码" in file_path.name or "password" in file_path.name.lower():
            return "password"
        elif "SN" in file_path.name or "serial" in file_path.name.lower():
            return "serial_number"
        elif "银行" in file_path.name or "bank" in file_path.name.lower():
            return "banking"
        elif "账号" in file_path.name or "account" in file_path.name.lower():
            return "account"
        elif "简介" in file_path.name or "profile" in file_path.name.lower():
            return "profile"
        else:
            return "general"

    def read_file_content(self, file_path: Path) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except (FileNotFoundError, PermissionError, OSError):
                return ""

    def process_and_store(self, collected_info: Dict) -> Any | None:
        """处理并存储信息"""
        logger.info("🔒 开始处理和存储个人信息...")

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        processed_count = 0

        for path, info in collected_info.items():
            # 分类处理
            if info['file_type'] == 'password':
                self.process_password_info(cursor, info, path)
            elif info['file_type'] == 'serial_number':
                self.process_serial_info(cursor, info, path)
            elif info['file_type'] == 'banking':
                self.process_banking_info(cursor, info, path)
            else:
                self.process_general_info(cursor, info, path)

            processed_count += 1

            # 保存原始文件副本到安全位置
            self.backup_file(info['file_path'])

        conn.commit()
        conn.close()

        logger.info(f"✅ 处理完成 {processed_count} 条记录")

    def process_password_info(self, cursor, info: Dict, path: str) -> None:
        """处理密码信息"""
        sensitivity = 3  # 高度敏感

        # 提取密码信息
        lines = info['content'].split('\n')
        passwords = []

        for line in lines:
            line = line.strip()
            if line and (':' in line or '密码' in line or 'Password' in line):
                passwords.append(line)

        content = json.dumps({
            "extracted_info": passwords,
            "full_content": info['content'][:500]  # 只保存前500字符
        })

        # 加密存储
        encrypted_content = self.encrypt_data(content)

        cursor.execute("""
            INSERT INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "passwords",
            info['file_name'],
            encrypted_content,
            "encrypted",
            sensitivity,
            json.dumps({"original_path": path, "count": len(passwords)}),
            json.dumps({"file_size": info['size'], "modified": info['modified']})
        ))

        logger.info(f"  🔐 处理密码文件: {info['file_name']} (找到 {len(passwords)} 条)")

    def process_serial_info(self, cursor, info: Dict, path: str) -> None:
        """处理SN信息"""
        sensitivity = 2  # 敏感

        # 提取SN信息
        lines = info['content'].split('\n')
        serials = []

        for line in lines:
            line = line.strip()
            if line and any(keyword in line.upper() for keyword in ['SN', 'SERIAL', '序列号', '编号']):
                serials.append(line)

        content = json.dumps({
            "extracted_serials": serials,
            "summary": f"文件包含 {len(serials)} 个序列号信息"
        })

        encrypted_content = self.encrypt_data(content)

        cursor.execute("""
            INSERT INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "serial_numbers",
            info['file_name'],
            encrypted_content,
            "encrypted",
            sensitivity,
            json.dumps({"file_type": info['file_type']}),
            json.dumps({"original_path": path, "serial_count": len(serials)})
        ))

        logger.info(f"  🔢 处理SN文件: {info['file_name']} (找到 {len(serials)} 个)")

    def process_banking_info(self, cursor, info: Dict, path: str) -> None:
        """处理银行信息"""
        sensitivity = 3  # 高度敏感

        encrypted_content = self.encrypt_data(info['content'])

        cursor.execute("""
            INSERT INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "banking",
            info['file_name'],
            encrypted_content,
            "encrypted",
            sensitivity,
            json.dumps({"original_path": path}),
            json.dumps({"file_size": info['size'], "modified": info['modified']})
        ))

        logger.info(f"  🏦 处理银行文件: {info['file_name']}")

    def process_general_info(self, cursor, info: Dict, path: str) -> None:
        """处理一般信息"""
        sensitivity = 1  # 普通

        cursor.execute("""
            INSERT INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "general",
            info['file_name'],
            info['content'],
            "text",
            sensitivity,
            json.dumps({"file_type": info['file_type']}),
            json.dumps({"original_path": path})
        ))

    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()

    def backup_file(self, source_path: str) -> Any:
        """备份文件到安全位置"""
        try:
            source = Path(source_path)
            backup_dir = self.storage_dir / "file_backups"
            backup_dir.mkdir(exist_ok=True)

            # 保持相对路径结构
            relative_path = Path(*source.parts[-2:])  # 最后两个部分
            backup_path = backup_dir / relative_path

            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup_path)

            logger.info(f"  💾 备份到: {backup_path}")
        except Exception as e:
            logger.error(f"  ❌ 备份失败 {source_path}: {e}")

    def create_summary_report(self) -> Any:
        """创建汇总报告"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 统计各类信息
        cursor.execute("""
            SELECT category, COUNT(*) as count,
                   AVG(sensitivity_level) as avg_sensitivity
            FROM personal_info
            GROUP BY category
        """)

        stats = cursor.fetchall()

        report = []
        report.append("=" * 60)
        report.append("爸爸个人信息保护系统 - 汇总报告")
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("📊 信息分类统计:")
        report.append("-" * 40)
        for category, count, avg_sens in stats:
            emoji = "🔐" if avg_sens >= 2.5 else "📋"
            report.append(f"{emoji} {category}: {count} 条记录 (敏感度: {avg_sens:.1f})")

        report.append("")

        # 记录访问日志
        cursor.execute("INSERT INTO access_log (purpose, ip_address) VALUES (?, ?)",
                   ("生成汇总报告", "local"))

        conn.commit()
        conn.close()

        # 保存报告
        report_path = self.storage_dir / "personal_info_summary.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        return '\n'.join(report)

    def main(self) -> None:
        """主函数"""
        print("\n🔐 爸爸个人信息保护系统")
        print("=" * 60)
        print("正在扫描和收集您的个人信息...")
        print("")

        # 收集文件
        collected_info = self.collect_files()

        if not collected_info:
            print("❌ 未找到任何个人信息文件")
            return

        # 处理和存储
        self.process_and_store(collected_info)

        # 生成报告
        report = self.create_summary_report()

        print("\n✅ 处理完成！")
        print("")
        print("📍 数据已加密存储在:")
        print(f"   - 数据库: {self.db_path}")
        print(f"   - 备份: {self.storage_dir}/file_backups")
        print(f"   - 加密密钥: {self.storage_dir}/.encryption_key")
        print("")
        print("⚠️  安全提示:")
        print("   1. 请妥善保管加密密钥文件")
        print("   2. 定期备份您的数据")
        print("   3. 不要将密钥文件上传到云端")
        print("")
        print(report)

if __name__ == "__main__":
    collector = PersonalInfoCollector()
    collector.main()