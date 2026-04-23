"""Jinja2 提示词模板渲染器。"""

from jinja2 import BaseLoader, Environment, StrictUndefined


class PromptRenderer:
    """基于 Jinja2 的提示词模板渲染器。

    特性：
    - StrictUndefined: 缺失变量直接抛异常，不静默通过
    - 自定义过滤器: default, truncate
    - 不启用 autoescape（由 Sanitizer 负责注入防护）
    """

    def __init__(self) -> None:
        self.env = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined,
            autoescape=False,
        )
        self.env.filters["default"] = self._default_filter
        self.env.filters["truncate"] = self._truncate_filter

    def render(self, template: str, variables: dict) -> str:
        """渲染模板。

        Args:
            template: Jinja2 模板字符串
            variables: 变量字典

        Returns:
            渲染后的字符串

        Raises:
            jinja2.exceptions.UndefinedError: 缺失变量时抛出
        """
        jinja_template = self.env.from_string(template)
        return jinja_template.render(**variables)

    @staticmethod
    def _default_filter(value, default_value=""):
        return value if value is not None else default_value

    @staticmethod
    def _truncate_filter(value, length: int = 100):
        s = str(value) if value is not None else ""
        return s[:length] + "..." if len(s) > length else s
