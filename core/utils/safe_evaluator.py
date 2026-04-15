from __future__ import annotations
"""
安全表达式求值器

提供安全的条件表达式求值功能，避免 eval() 带来的安全风险。
"""

import ast
import operator
from collections.abc import Callable
from typing import Any


class SafeExpressionEvaluator:
    """安全表达式求值器

    使用 AST 解析和求值，避免代码注入风险。
    """

    # 支持的操作符
    _OPERATORS: dict[type, Callable] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitAnd: operator.and_,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
        ast.Not: lambda a: not a,
        ast.USub: operator.neg,
        ast.UAdd: lambda a: +a,
    }

    # 支持的内置函数
    _BUILTINS: dict[str, Callable] = {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "all": all,
        "any": any,
        "range": range,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
    }

    def __init__(
        self,
        allowed_operators: dict[type, Callable] | None = None,
        allowed_builtins: dict[str, Callable] | None = None,
        max_depth: int = 10
    ):
        """初始化求值器

        Args:
            allowed_operators: 允许的操作符映射
            allowed_builtins: 允许的内置函数映射
            max_depth: 最大递归深度
        """
        self._operators = allowed_operators or self._OPERATORS.copy()
        self._builtins = allowed_builtins or self._BUILTINS.copy()
        self._max_depth = max_depth

    def evaluate(
        self,
        expression: str,
        context: dict[str, Any] | None = None
    ) -> Any:
        """安全地求值表达式

        Args:
            expression: 要求值的表达式字符串
            context: 变量上下文

        Returns:
            Any: 求值结果

        Raises:
            ValueError: 表达式不安全或求值失败
        """
        if context is None:
            context = {}

        try:
            tree = ast.parse(expression, mode='eval')
            return self._eval_node(tree.body, context, depth=0)
        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Invalid expression: {e}") from e
        except Exception as e:
            raise ValueError(f"Evaluation failed: {e}") from e

    def _eval_node(
        self,
        node: ast.AST,
        context: dict[str, Any],
        depth: int
    ) -> Any:
        """递归求值 AST 节点

        Args:
            node: AST 节点
            context: 变量上下文
            depth: 当前递归深度

        Returns:
            Any: 求值结果

        Raises:
            ValueError: 不支持的节点类型或超出最大深度
        """
        # 防止递归过深
        if depth > self._max_depth:
            raise ValueError("Expression too complex (max depth exceeded)")

        # 常量
        if isinstance(node, ast.Constant):
            return node.value

        # 变量名
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            elif node.id in self._builtins:
                return self._builtins[node.id]
            else:
                raise ValueError(f"Undefined variable: {node.id}")

        # 一元操作
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context, depth + 1)
            op_type = type(node.op)
            if op_type in self._operators:
                return self._operators[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")

        # 二元操作
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context, depth + 1)
            right = self._eval_node(node.right, context, depth + 1)
            op_type = type(node.op)
            if op_type in self._operators:
                return self._operators[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type}")

        # 比较操作
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context, depth + 1)
            result = True
            for op, comparator in zip(node.ops, node.comparators, strict=False):
                right = self._eval_node(comparator, context, depth + 1)
                op_type = type(op)
                if op_type in self._operators:
                    op_result = self._operators[op_type](left, right)
                    # 对于链式比较（如 a < b < c），需要特殊处理
                    if not op_result:
                        return False
                    left = right  # 更新 left 为 right
                else:
                    raise ValueError(f"Unsupported comparison operator: {op_type}")
            return result

        # 布尔操作
        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, context, depth + 1) for v in node.values]
            op_type = type(node.op)
            if op_type == ast.And:
                return all(values)
            elif op_type == ast.Or:
                return any(values)
            raise ValueError(f"Unsupported boolean operator: {op_type}")

        # 函数调用
        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func, context, depth + 1)
            args = [self._eval_node(arg, context, depth + 1) for arg in node.args]

            # 检查是否是允许的函数
            if not callable(func):
                raise ValueError(f"Object is not callable: {func}")

            # 限制函数调用（只允许内置安全函数）
            if func not in self._builtins.values():
                raise ValueError(f"Custom function calls not allowed: {func}")

            return func(*args)

        # 列表/元组/集合
        elif isinstance(node, ast.List):
            return [self._eval_node(e, context, depth + 1) for e in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(e, context, depth + 1) for e in node.elts)
        elif isinstance(node, ast.Set):
            return {self._eval_node(e, context, depth + 1) for e in node.elts}

        # 字典
        elif isinstance(node, ast.Dict):
            return {
                self._eval_node(k, context, depth + 1): self._eval_node(v, context, depth + 1)
                for k, v in zip(node.keys, node.values, strict=False)
            }

        # 下标
        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context, depth + 1)
            index = self._eval_node(node.slice, context, depth + 1)
            return value[index]

        # 切片
        elif isinstance(node, ast.Index):
            return self._eval_node(node.value, context, depth + 1)

        # 不支持的节点类型
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    def is_safe_expression(self, expression: str) -> bool:
        """检查表达式是否安全

        Args:
            expression: 要检查的表达式

        Returns:
            bool: 是否安全
        """
        try:
            self.evaluate(expression)
            return True
        except Exception:
            return False


# 默认实例
_default_evaluator = SafeExpressionEvaluator()


def safe_eval(
    expression: str,
    context: dict[str, Any] | None = None
) -> Any:
    """安全求值表达式（便捷函数）

    Args:
        expression: 表达式字符串
        context: 变量上下文

    Returns:
        Any: 求值结果

    Raises:
        ValueError: 表达式不安全或求值失败

    Examples:
        >>> safe_eval("1 + 1")
        2
        >>> safe_eval("x > 5", {"x": 10})
        True
        >>> safe_eval("len(items) > 0", {"items": [1, 2, 3]})
        True
    """
    return _default_evaluator.evaluate(expression, context)


def is_safe_expression(expression: str) -> bool:
    """检查表达式是否安全（便捷函数）

    Args:
        expression: 要检查的表达式

    Returns:
        bool: 是否安全
    """
    return _default_evaluator.is_safe_expression(expression)
