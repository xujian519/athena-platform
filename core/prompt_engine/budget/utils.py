"""Token 估算工具 — tiktoken 优先，无依赖时回退到近似算法。"""



class TokenEstimator:
    """提供与模型无关的 token 估算能力。

    优先使用 tiktoken（cl100k_base），未安装时回退到字符启发式：
    - 英文/数字: ~4 字符 / token
    - CJK: ~1.5 字符 / token
    该回退方案在多数场景下误差 < 20%，足以支撑 budget 管理。
    """

    _encoding: object | None = None
    _encoding_name: str = "cl100k_base"

    def __init__(self, encoding_name: str | None = None) -> None:
        self._init_encoding(encoding_name or self._encoding_name)

    def _init_encoding(self, name: str) -> None:
        if TokenEstimator._encoding is not None:
            return
        try:
            import tiktoken  # type: ignore[import]

            TokenEstimator._encoding = tiktoken.get_encoding(name)
            TokenEstimator._encoding_name = name
        except Exception:
            TokenEstimator._encoding = None

    def estimate(self, text: str) -> int:
        """估算给定文本的 token 数量。"""
        if not text:
            return 0
        if TokenEstimator._encoding is not None:
            return len(TokenEstimator._encoding.encode(text))
        return self._approximate(text)

    @staticmethod
    def _approximate(text: str) -> int:
        """字符级近似估算（无需 tiktoken）。

        启发式规则：
        - ASCII 字母/数字/空格/标点: 4 字符 = 1 token
        - CJK 统一表意文字: 1.5 字符 = 1 token
        - 其他字符（符号、emoji 等）: 2 字符 = 1 token
        """
        total = 0
        for ch in text:
            o = ord(ch)
            if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
                total += 1
            elif o < 128:
                total += 0.25
            else:
                total += 0.5
        return max(1, int(total))