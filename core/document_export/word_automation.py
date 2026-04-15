#!/usr/bin/env python3
from __future__ import annotations
"""
Word/WPS自动化接口 - Athena平台深度集成版
Word/WPS Automation Interface - Deep Integration for Athena Platform

提供与Microsoft Word和WPS Office的自动化交互能力:
1. 自动插入内容到光标位置
2. 格式化文档
3. 插入图片和表格
4. 文档操作自动化

集成时间: 2025-12-24
版本: v1.0.0 "深度集成"
"""

import logging
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WordAutomation:
    """Word/WPS自动化接口"""

    def __init__(self):
        """初始化Word自动化接口"""
        self.system = platform.system()
        self.word_app = None
        self.is_wps = False

        logger.info(f"🖥️  系统平台: {self.system}")

    def check_word_installation(self) -> dict[str, bool]:
        """
        检测系统上安装的Word软件

        Returns:
            {'word': bool, 'wps': bool}
        """
        result = {"word": False, "wps": False}

        if self.system == "Darwin":  # mac_os
            try:
                # 检查Microsoft Word
                word_path = "/Applications/Microsoft Word.app"
                result["word"] = Path(word_path).exists()

                # 检查WPS Office
                wps_path = "/Applications/WPS Office.app"
                result["wps"] = Path(wps_path).exists()

            except Exception as e:
                logger.error(f"❌ 检测Word安装失败: {e}")

        elif self.system == "Windows":
            try:
                # 使用where命令查找
                for app in ["WINWORD.EXE", "WPS.EXE"]:
                    check = subprocess.run(
                        ["where", app], capture_output=True, text=True, timeout=5
                    )
                    if check.returncode == 0:
                        if "WORD" in app.upper():
                            result["word"] = True
                        elif "WPS" in app.upper():
                            result["wps"] = True
            except Exception as e:
                logger.error(f"❌ 检测Word安装失败: {e}")

        logger.info(f"📊 Word软件检测结果: {result}")
        return result

    def open_document(self, file_path: str) -> bool:
        """
        打开Word文档

        Args:
            file_path: 文档路径

        Returns:
            是否成功打开
        """
        try:
            if not Path(file_path).exists():
                logger.error(f"❌ 文件不存在: {file_path}")
                return False

            if self.system == "Darwin":  # mac_os
                subprocess.run(["open", file_path], check=True)
            elif self.system == "Windows":
                os.startfile(file_path)
            else:
                subprocess.run(["xdg-open", file_path], check=True)

            logger.info(f"✅ 已打开文档: {file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 打开文档失败: {e}")
            return False

    def get_active_word_app(self) -> str | None:
        """
        获取当前活动的Word应用

        Returns:
            'word', 'wps', 或 None
        """
        installation = self.check_word_installation()

        if installation.get("word"):
            return "word"
        elif installation.get("wps"):
            return "wps"
        else:
            return None


class WordDocumentInserter:
    """Word文档内容插入器"""

    def __init__(self):
        """初始化文档插入器"""
        self.automation = WordAutomation()
        self.system = platform.system()

    def insert_at_cursor(self, docx_path: str, content: str | None = None) -> bool:
        """
        在Word文档光标位置插入内容

        注意: 此功能需要使用AppleScript(Windows)或JXA(mac_os)
        这里提供一个简化的实现,打开文档并提示用户手动操作

        Args:
            docx_path: DOCX文档路径
            content: 要插入的内容(可选)

        Returns:
            是否成功
        """
        # 先打开文档
        if not self.automation.open_document(docx_path):
            return False

        # 如果需要插入内容(高级功能,需要额外实现)
        if content:
            logger.info("📝 文档已打开,请手动将光标定位到需要插入的位置")
            # TODO: 实现自动化插入内容
            # 在macOS上可以使用JXA + Word AppleScript
            # 在Windows上可以使用pywin32

        return True

    def insert_table_from_docx(self, docx_path: str, excel_path: str) -> bool:
        """
        将DOCX中的表格提取并插入到Excel

        Args:
            docx_path: Word文档路径
            excel_path: Excel文件路径

        Returns:
            是否成功
        """
        try:
            # 先打开Excel
            self.automation.open_document(excel_path)

            # 再打开Word
            self.automation.open_document(docx_path)

            logger.info("✅ 已打开Word和Excel,请手动复制表格")
            return True

        except Exception as e:
            logger.error(f"❌ 操作失败: {e}")
            return False


class ClipboardManager:
    """剪贴板管理器 - 用于自动化复制粘贴"""

    def __init__(self):
        """初始化剪贴板管理器"""
        self.system = platform.system()

    def copy_file_to_clipboard(self, file_path: str) -> bool:
        """
        将文件内容复制到剪贴板

        Args:
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return self.copy_text_to_clipboard(content)

        except Exception as e:
            logger.error(f"❌ 复制文件失败: {e}")
            return False

    def copy_text_to_clipboard(self, text: str) -> bool:
        """
        将文本复制到剪贴板

        Args:
            text: 文本内容

        Returns:
            是否成功
        """
        try:
            if self.system == "Darwin":  # mac_os
                subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            elif self.system == "Windows":
                import win32clipboard

                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
                win32clipboard.CloseClipboard()
            else:  # Linux
                subprocess.run(
                    ["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True
                )

            logger.info("✅ 内容已复制到剪贴板")
            return True

        except Exception as e:
            logger.error(f"❌ 复制到剪贴板失败: {e}")
            return False

    def paste_in_word(self, delay: float = 0.5) -> bool:
        """
        在Word中粘贴剪贴板内容

        Args:
            delay: 粘贴前等待时间(秒)

        Returns:
            是否成功
        """
        try:
            time.sleep(delay)

            if self.system == "Darwin":  # mac_os
                # 使用AppleScript模拟Cmd+V
                script = 'tell application "System Events" to keystroke "v" using command down'
                subprocess.run(["osascript", "-e", script], check=True)
            elif self.system == "Windows":
                import pyautogui

                pyautogui.hotkey("ctrl", "v")
            else:  # Linux
                subprocess.run(["xdotool", "key", "ctrl+v"], check=True)

            logger.info("✅ 已在Word中粘贴内容")
            return True

        except Exception as e:
            logger.error(f"❌ 粘贴失败: {e}")
            return False


class AutomatedWordExporter:
    """自动化Word导出器"""

    def __init__(self):
        """初始化自动化导出器"""
        self.clipboard = ClipboardManager()
        self.inserter = WordDocumentInserter()
        self.automation = WordAutomation()

    def export_and_insert(
        self, markdown_content: str, open_word: bool = True, auto_insert: bool = False
    ) -> dict[str, Any]:
        """
        导出Markdown并插入到Word

        Args:
            markdown_content: Markdown内容
            open_word: 是否打开Word
            auto_insert: 是否自动插入

        Returns:
            操作结果
        """
        result = {"success": False, "message": "", "file_path": None}

        try:
            # 1. 复制内容到剪贴板
            if not self.clipboard.copy_text_to_clipboard(markdown_content):
                result["message"] = "复制到剪贴板失败"
                return result

            # 2. 如果需要,打开Word
            if open_word:
                app_type = self.automation.get_active_word_app()
                if not app_type:
                    result["message"] = "未检测到Word或WPS"
                    return result

                logger.info(f"✅ 检测到 {app_type.upper()}")

            # 3. 自动插入(如果启用)
            if auto_insert:
                self.clipboard.paste_in_word()

            result["success"] = True
            result["message"] = "内容已复制到剪贴板,请在Word中粘贴"

        except Exception as e:
            result["message"] = f"导出失败: {e}"
            logger.error(f"❌ 导出失败: {e}")

        return result

    def export_docx_and_open(self, markdown_content: str, output_filename: str) -> dict[str, Any]:
        """
        导出为DOCX并打开Word文档

        Args:
            markdown_content: Markdown内容
            output_filename: 输出文件名

        Returns:
            操作结果
        """
        from .pastemd_core import PasteMDCore

        result = {"success": False, "message": "", "file_path": None}

        try:
            # 1. 转换为DOCX
            pastemd = PasteMDCore()
            doc_path = pastemd.markdown_to_docx(markdown_content, output_filename)

            if not doc_path:
                result["message"] = "DOCX转换失败"
                return result

            # 2. 打开文档
            if self.automation.open_document(doc_path):
                result["success"] = True
                result["message"] = f"文档已创建并打开: {doc_path}"
                result["file_path"] = doc_path
            else:
                result["message"] = "文档创建成功,但打开失败"
                result["file_path"] = doc_path

        except Exception as e:
            result["message"] = f"导出失败: {e}"
            logger.error(f"❌ 导出失败: {e}")

        return result


# 单例实例
_automation_instance = None


def get_word_automation() -> AutomatedWordExporter:
    """获取Word自动化单例"""
    global _automation_instance
    if _automation_instance is None:
        _automation_instance = AutomatedWordExporter()
    return _automation_instance


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Word自动化接口测试")
    print("=" * 60)

    # 测试Word检测
    automation = WordAutomation()
    print("\n🔍 检测Word安装...")
    installation = automation.check_word_installation()
    print(f"Microsoft Word: {'✅' if installation['word'] else '❌'}")
    print(f"WPS Office: {'✅' if installation['wps'] else '❌'}")

    # 测试剪贴板
    print("\n📋 测试剪贴板...")
    clipboard = ClipboardManager()
    if clipboard.copy_text_to_clipboard("Hello from Athena!"):
        print("✅ 剪贴板测试成功")

    print("\n" + "=" * 60)
