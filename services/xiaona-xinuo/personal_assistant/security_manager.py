#!/usr/bin/env python3
"""
个人信息安全管理器
Personal Information Security Manager
"""

import os
from core.async_main import async_main
import sys
import json
import logging
from core.logging_config import setup_logging
import hashlib
import getpass
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
from cryptography.fernet import Fernet
import base64

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class PersonalSecurityManager:
    """个人信息安全管理器"""

    def __init__(self):
        self.storage_dir = Path("/Users/xujian/Athena工作平台/personal_secure_storage")
        self.db_path = self.storage_dir / "personal_info.db"
        self.access_log_path = self.storage_dir / "access_attempts.log"

        # 初始化加密
        self.init_encryption()

        # 设置访问日志
        self.setup_logging()

    def init_encryption(self):
        """初始化加密"""
        key_path = self.storage_dir / ".encryption_key"

        if key_path.exists():
            with open(key_path, 'rb') as f:
                key = f.read()
                # 密钥文件直接存储原始二进制数据
        else:
            raise FileNotFoundError("加密密钥不存在！")

        self.cipher = Fernet(key)

    def setup_logging(self):
        """设置访问日志"""
        logging.basicConfig(
            filename=str(self.access_log_path),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def verify_access(self, password: str) -> bool:
        """验证访问密码"""
        # 使用固定密码（实际应用中应该更安全）
        stored_hash = "f9e9f77d5e8b2e3c2e7be8e0a1f0a9a1b0c9d8e8a5e2c3"
        input_hash = hashlib.sha256(password.encode()).hexdigest()

        is_valid = input_hash == stored_hash

        # 记录访问尝试
        self.log_access_attempt("密码验证", is_valid)

        return is_valid

    def log_access_attempt(self, purpose: str, success: bool):
        """记录访问尝试"""
        log_entry = f"{datetime.now().isoformat()} - {purpose} - {'成功' if success else '失败'}"

        try:
            with open(self.access_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            logger.error(f"记录访问日志失败: {e}")

    def get_secure_info(self, category: str = None, search_term: str = None):
        """安全获取信息"""
        # 验证访问权限
        password = getpass.getpass("请输入访问密码: ")
        if not self.verify_access(password):
            print("❌ 密码错误！")
            return None

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            if category:
                cursor.execute("""
                    SELECT title, content, created_at
                    FROM personal_info
                    WHERE category = ?
                    ORDER BY created_at DESC
                """, (category,))
            elif search_term:
                cursor.execute("""
                    SELECT title, content, created_at
                    FROM personal_info
                    WHERE tags LIKE ? OR title LIKE ?
                    ORDER BY created_at DESC
                """, (f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("""
                    SELECT category, title, created_at
                    FROM personal_info
                    ORDER BY created_at DESC
                    LIMIT 10
                """)

            results = cursor.fetchall()
            conn.close()

            # 解密并返回结果
            decrypted_results = []
            for result in results:
                try:
                    if len(result) == 3:  # category查询
                        category, title, created_at = result
                        decrypted_results.append({
                            "category": category,
                            "title": title,
                            "created_at": created_at
                        })
                    elif len(result) == 3:  # content查询
                        title, encrypted_content, created_at = result
                        if encrypted_content.startswith('g_aaaa'):  # 加密内容
                            content = self.cipher.decrypt(encrypted_content.encode()).decode()
                        else:
                            content = encrypted_content
                        decrypted_results.append({
                            "title": title,
                            "content": content[:200] + "..." if len(content) > 200 else content,
                            "created_at": created_at,
                            "is_encrypted": encrypted_content.startswith('g_aaaa')
                        })
                except Exception as e:
                    logger.error(f"解密失败: {e}")

            return decrypted_results

        except Exception as e:
            logger.error(f"查询失败: {e}")
            conn.close()
            return None

    def add_secure_note(self, category: str, title: str, content: str, is_sensitive: bool = False):
        """添加安全笔记"""
        # 验证访问权限
        password = getpass.getpass("请输入访问密码: ")
        if not self.verify_access(password):
            print("❌ 密码错误！")
            return False

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 加密敏感内容
        if is_sensitive:
            content = self.cipher.encrypt(content.encode()).decode()
            content_type = "encrypted"
        else:
            content_type = "text"

        cursor.execute("""
            INSERT INTO personal_info
            (category, title, content, content_type, sensitivity_level, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            category,
            title,
            content,
            content_type,
            3 if is_sensitive else 1,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        # 记录操作
        self.log_access_attempt(f"添加笔记 - {title}", True)

        print(f"✅ 笔记已保存: {title}")
        return True

    def backup_data(self, backup_path: str = None):
        """备份数据"""
        # 验证访问权限
        password = getpass.getpass("请输入访问密码以备份数据: ")
        if not self.verify_access(password):
            print("❌ 密码错误！")
            return False

        if not backup_path:
            backup_path = self.storage_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        import zipfile

        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 添加数据库
                zf.write(self.db_path, "personal_info.db")

                # 添加备份文件
                backup_files_dir = self.storage_dir / "file_backups"
                if backup_files_dir.exists():
                    for file in backup_files_dir.rglob("*"):
                        if file.is_file():
                            zf.write(file, str(file.relative_to(backup_files_dir)))

                # 添加密钥文件（重要！）
                key_file = self.storage_dir / ".encryption_key"
                if key_file.exists():
                    zf.write(key_file, ".encryption_key")

            print(f"✅ 数据已备份到: {backup_path}")

            # 记录备份操作
            self.log_access_attempt("数据备份", True)

        except Exception as e:
            logger.error(f"备份失败: {e}")
            return False

        return True

    def restore_data(self, backup_path: str):
        """恢复数据"""
        # 验证访问权限
        password = getpass.getpass("请输入访问密码以恢复数据: ")
        if not self.verify_access(password):
            print("❌ 密码错误！")
            return False

        import zipfile

        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                # 恢复数据库
                zf.extract("personal_info.db", path=str(self.storage_dir))

                # 恢复密钥文件
                if ".encryption_key" in zf.namelist():
                    zf.extract(".encryption_key", path=str(self.storage_dir))

            print(f"✅ 数据已从备份恢复: {backup_path}")

            # 重新初始化加密
            self.init_encryption()

            # 记录恢复操作
            self.log_access_attempt("数据恢复", True)

        except Exception as e:
            logger.error(f"恢复失败: {e}")
            return False

        return True

    def show_status(self):
        """显示系统状态"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 统计信息
        cursor.execute("SELECT COUNT(*) FROM personal_info")
        total_records = cursor.fetchone()[0]

        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM personal_info
            GROUP BY category
        """)
        categories = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) as encrypted_count
            FROM personal_info
            WHERE content_type = 'encrypted'
        """)
        encrypted_count = cursor.fetchone()[0]

        conn.close()

        print("\n🔐 个人信息安全状态")
        print("=" * 50)
        print(f"📊 总记录数: {total_records}")
        print(f"🔒 加密记录数: {encrypted_count}")
        print("")
        print("📋 分类统计:")
        for category, count in categories:
            print(f"  - {category}: {count} 条")
        print("")

        # 检查最近访问
        try:
            with open(self.access_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print("🕒 最近访问记录:")
                    for line in lines[-5:]:  # 显示最后5条
                        print(f"  {line.strip()}")
        except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

        print("")
        print("📍 数据位置:")
        print(f"  - 数据库: {self.db_path}")
        print(f"  - 备份文件: {self.storage_dir}/backup_*.zip")
        print(f"  - 访问日志: {self.access_log_path}")

def main():
    """主函数"""
    print("\n🔐 爸爸个人信息安全管理器")
    print("=" * 50)
    print("1. 查看信息  2. 添加笔记 3. 备份数据 4. 恢复数据 5. 系统状态")
    print("")

    manager = PersonalSecurityManager()

    while True:
        print("\n请选择操作:")
        choice = input("请输入选项 (1-5): ").strip()

        if choice == "1":
            # 查看信息
            search = input("搜索关键词 (留空查看所有): ").strip()
            category = input("分类 (留空查看所有): ").strip()

            results = manager.get_secure_info(category if category else None, search if search else None)

            if results:
                print("\n📄 查询结果:")
                for result in results:
                    if 'category' in result:
                        print(f"\n📁 {result['category']}")
                    print(f"📄 {result['title']}")
                    if 'content' in result:
                        print(f"📝 {result['content']}")
                    if 'created_at' in result:
                        print(f"⏰ 创建时间: {result['created_at']}")
                    if result.get('is_encrypted'):
                        print("🔒 (已加密)")
            else:
                print("\n未找到相关信息")

        elif choice == "2":
            # 添加笔记
            category = input("分类: ").strip()
            title = input("标题: ").strip()
            content = input("内容 (支持多行): ").strip()
            is_sensitive = input("是否敏感信息 (y/N): ").strip().lower() == 'y'

            manager.add_secure_note(category, title, content, is_sensitive)

        elif choice == "3":
            # 备份数据
            backup_path = input("备份路径 (留空使用默认): ").strip()
            manager.backup_data(backup_path if backup_path else None)

        elif choice == "4":
            # 恢复数据
            backup_path = input("备份文件路径: ").strip()
            if backup_path and Path(backup_path).exists():
                manager.restore_data(backup_path)
            else:
                print("❌ 备份文件不存在")

        elif choice == "5":
            # 系统状态
            manager.show_status()

        elif choice == "q" or choice == "Q":
            print("\n👋 退出系统")
            break

        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main()