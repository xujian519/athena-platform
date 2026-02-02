"""
MimeMultipart兼容层
Compatibility layer for MimeMultipart
"""

from typing import Any, Dict, List, Optional


class MimeMultipart:
    """MimeMultipart兼容类"""

    def __init__(self):
        self.parts = []

    def add_part(self, content: str, content_type: str = "text/plain") -> None:
        """添加部分"""
        self.parts.append({"content": content, "content_type": content_type})

    def get_parts(self) -> list[dict[str, Any]]:
        """获取所有部分"""
        return self.parts

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {"parts": self.parts, "count": len(self.parts)}
