#!/usr/bin/env python3

"""
小诺输入验证和安全检查器
Xiaonuo Input Validator and Security Checker

提供全面的输入验证和安全检查功能

功能:
1. 输入格式验证
2. 安全威胁检测
3. 内容过滤
4. 长度和复杂度检查
5. 恶意代码检测

作者: 小诺AI团队
日期: 2025-12-18
"""

import ast
import base64
import hashlib
import html
import json
import os
import re
import sys
import threading
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from core.logging_config import setup_logging

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class ValidationLevel(Enum):
    """验证级别"""
    PERMISSIVE = "permissive"      # 宽松验证
    STANDARD = "standard"         # 标准验证
    STRICT = "strict"            # 严格验证
    PARANOID = "paranoid"        # 偏执验证

class ThreatLevel(Enum):
    """威胁等级"""
    NONE = "none"                # 无威胁
    LOW = "low"                  # 低威胁
    MEDIUM = "medium"            # 中等威胁
    HIGH = "high"                # 高威胁
    CRITICAL = "critical"        # 严重威胁

class ValidationStatus(Enum):
    """验证状态"""
    VALID = "valid"              # 有效
    WARNING = "warning"          # 警告
    INVALID = "invalid"          # 无效
    BLOCKED = "blocked"          # 被阻止

@dataclass
class ValidationResult:
    """验证结果"""
    status: ValidationStatus
    threat_level: ThreatLevel
    issues: list[str]            # 发现的问题
    warnings: list[str]          # 警告信息
    security_issues: list[dict[str, Any]  # 安全问题
    metrics: dict[str, Any]      # 指标信息
    sanitized_input: str  # 清理后的输入
    metadata: dict[str, Any]     # 元数据

@dataclass
class SecurityThreat:
    """安全威胁"""
    threat_type: str
    description: str
    severity: ThreatLevel
    pattern: str
    location: tuple[int, int]  # (start, end)
    mitigation: str

class InputValidator:
    """输入验证器"""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """初始化验证器"""
        self.validation_level = validation_level

        # XSS攻击模式
        self.xss_patterns = {
            'script_injection': [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'onclick\s*=',
                r'onload\s*=',
                r'onerror\s*=',
                r'eval\s*\(',
                r'alert\s*\(',
                r'document\.cookie',
                r'window\.location',
            ],
            'event_handlers': [
                r'on\w+\s*=\s*["\'][^"\']*["\']',
                r'on\w+\s*=\s*[^"\'\s>]+',
            ],
            'dangerous_tags': [
                r'<iframe[^>]*>',
                r'<object[^>]*>',
                r'<embed[^>]*>',
                r'<link[^>]*>',
                r'<meta[^>]*>',
            ],
        }

        # SQL注入模式
        self.sql_injection_patterns = {
            'union_select': [
                r'UNION\s+SELECT',
                r'union\s+select',
            ],
            'comment_based': [
                r'--',
                r'/\*.*\*/',
                r'#',
            ],
            'boolean_blind': [
                r'\s+AND\s+1\s*=\s*1',
                r'\s+OR\s+1\s*=\s*1',
                r'\s+AND\s+1\s*=\s*2',
            ],
            'time_based': [
                r'SLEEP\s*\(',
                r'WAITFOR\s+DELAY',
                r'BENCHMARK\s*\(',
            ],
            'stacked_queries': [
                r';\s*(DROP|DELETE|UPDATE|INSERT)',
                r';\s*(ALTER|CREATE|EXEC)',
            ],
        }

        # 命令注入模式
        self.command_injection_patterns = {
            'shell_commands': [
                r';\s*(ls|dir|cat|type)',
                r';\s*(rm|del|mv|copy)',
                r';\s*(ping|nslookup|netstat)',
                r'&\s*(ls|dir|cat|type)',
                r'\|\s*(ls|dir|cat|type)',
            ],
            'backticks': [
                r'`[^`]*`',
            ],
            'variable_expansion': [
                r'\$\([^)]*\)',
                r'\$\{[^}]*\}',
            ],
        }

        # 路径遍历模式
        self.path_traversal_patterns = [
            r'\.\.[\\/]',
            r'%2e%2e[\\/]',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
            r'\.\.%2f',
            r'\.\.%5c',
            r'\.\.\/',
            r'\.\.\\',
        ]

        # 恶意文件模式
        self.malicious_file_patterns = [
            r'\.exe$',
            r'\.bat$',
            r'\.cmd$',
            r'\.com$',
            r'\.pif$',
            r'\.scr$',
            r'\.vbs$',
            r'\.js$',
            r'\.jar$',
            r'\.php$',
            r'\.asp$',
            r'\.aspx$',
            r'\.jsp$',
        ]

        # 输入长度限制
        self.length_limits = {
            ValidationLevel.PERMISSIVE: {'min': 0, 'max': 100000},
            ValidationLevel.STANDARD: {'min': 1, 'max': 10000},
            ValidationLevel.STRICT: {'min': 2, 'max': 1000},
            ValidationLevel.PARANOID: {'min': 3, 'max': 500},
        }

        # 允许的字符集
        self.allowed_chars = {
            ValidationLevel.PERMISSIVE: None,  # 允许所有字符
            ValidationLevel.STANDARD: r'[\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,!?;:()[\]{}"\'-]',  # 基本字符+中文+标点
            ValidationLevel.STRICT: r'[\w\s\u4e00-\u9fff.,!?;:()[\]{}"\'-]',  # 限制字符
            ValidationLevel.PARANOID: r'[a-z_a-Z0-9\u4e00-\u9fff\s]',  # 仅字母数字中文空格
        }

        # 禁用词列表
        self.blocked_words = {
            # 敏感政治词汇
            '政治', '敏感', '抗议', '示威', '革命', '暴动',
            # 暴力词汇
            '杀', '死', '爆炸', '袭击', '恐怖', '武器',
            # 色情词汇
            '色情', '裸体', '性交', '做爱',
            # 违法词汇
            '毒品', '赌博', '诈骗', '洗钱',
        }

        # 统计信息
        self.validation_stats = {
            'total_validations': 0,
            'status_distribution': Counter(),
            'threat_distribution': Counter(),
            'common_issues': Counter(),
            'blocked_inputs': 0,
        }

        # 缓存
        self.validation_cache: dict[str, Any] = {}
        self.cache_lock = threading.Lock()

        logger.info(f"🚀 输入验证器初始化完成 (级别: {validation_level.value})")

    def validate_input(self, input_text: str, context: Optional[dict[str, Any]] = None) -> ValidationResult:
        """验证输入"""
        start_time = datetime.now()

        try:
            # 基础检查
            if input_text is None:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    threat_level=ThreatLevel.HIGH,
                    issues=["输入为空"],
                    warnings=[],
                    security_issues=[],
                    metrics={},
                    sanitized_input=None,
                    metadata={"processing_time_ms": 0}
                )

            # 检查缓存
            cache_key = self._get_validation_cache_key(input_text, context)
            if cache_key in self.validation_cache:
                cached_result = self.validation_cache[cache_key]
                cached_result.metadata["processing_time_ms"] = (
                    (datetime.now() - start_time).total_seconds() * 1000
                )
                return cached_result

            # 初始化结果
            issues = []
            warnings = []
            security_issues = []
            metrics = {}
            sanitized_input = input_text
            metadata = {}

            # 1. 长度验证
            length_result = self._validate_length(input_text)
            issues.extend(length_result['issues'])
            warnings.extend(length_result['warnings'])
            metrics['length'] = len(input_text)

            # 2. 字符集验证
            charset_result = self._validate_charset(input_text)
            issues.extend(charset_result['issues'])
            warnings.extend(charset_result['warnings'])

            # 3. 内容安全检查
            content_result = self._validate_content(input_text)
            issues.extend(content_result['issues'])
            warnings.extend(content_result['warnings'])

            # 4. 安全威胁检测
            security_result = self._detect_security_threats(input_text)
            security_issues.extend(security_result['threats'])

            # 5. 恶意代码检测
            code_result = self._detect_malicious_code(input_text)
            security_issues.extend(code_result['threats'])

            # 6. 输入清理
            if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.PARANOID]:
                sanitized_input = self._sanitize_input(input_text)

            # 7. 复杂度分析
            complexity_result = self._analyze_complexity(input_text)
            metrics.update(complexity_result)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            metadata['processing_time_ms'] = processing_time
            metadata['validation_level'] = self.validation_level.value
            metadata['cache_key'] = cache_key

            # 确定验证状态
            status = self._determine_status(issues, warnings, security_issues)

            # 确定威胁等级
            threat_level = self._determine_threat_level(security_issues)

            # 构建结果
            result = ValidationResult(
                status=status,
                threat_level=threat_level,
                issues=issues,
                warnings=warnings,
                security_issues=security_issues,
                metrics=metrics,
                sanitized_input=sanitized_input,
                metadata=metadata
            )

            # 更新统计
            self._update_stats(result)

            # 缓存结果(仅缓存安全的输入)
            if status in [ValidationStatus.VALID, ValidationStatus.WARNING]:
                with self.cache_lock:
                    if len(self.validation_cache) < 1000:
                        self.validation_cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"❌ 验证过程出错: {e}")
            return ValidationResult(
                status=ValidationStatus.INVALID,
                threat_level=ThreatLevel.HIGH,
                issues=[f"验证器内部错误: {e!s}"],
                warnings=[],
                security_issues=[],
                metrics={},
                sanitized_input=None,
                metadata={"error": str(e)}
            )

    def _validate_length(self, text: str) -> dict[str, list[str]]:
        """验证输入长度"""
        issues = []
        warnings = []

        limits = self.length_limits[self.validation_level]
        length = len(text)

        if length < limits['min']:
            issues.append(f"输入长度过短: {length} < {limits['min']}")
        elif length > limits['max']:
            issues.append(f"输入长度过长: {length} > {limits['max']}")

        # 警告级别
        if length > limits['max'] * 0.8:
            warnings.append("输入长度接近上限")

        return {'issues': issues, 'warnings': warnings}

    def _validate_charset(self, text: str) -> dict[str, list[str]]:
        """验证字符集"""
        issues = []
        warnings = []

        allowed_pattern = self.allowed_chars[self.validation_level]
        if allowed_pattern:
            pattern = re.compile(allowed_pattern)
            invalid_chars = [c for c in text if not pattern.match(c)]

            if invalid_chars:
                unique_invalid = set(invalid_chars)
                issues.append(f"包含不允许的字符: {', '.join(unique_invalid)}")

        # Unicode字符检查
        try:
            text.encode('utf-8')
        except UnicodeEncodeError:
            issues.append("包含无效的Unicode字符")

        # 控制字符检查
        control_chars = [c for c in text if ord(c) < 32 and c not in '\t\n\r']
        if control_chars:
            warnings.append(f"包含控制字符: {len(control_chars)}个")

        return {'issues': issues, 'warnings': warnings}

    def _validate_content(self, text: str) -> dict[str, list[str]]:
        """验证内容安全性"""
        issues = []
        warnings = []

        # 禁用词检查
        lower_text = text.lower()
        found_blocked = [word for word in self.blocked_words if word in lower_text]

        if found_blocked:
            if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.PARANOID]:
                issues.append(f"包含敏感词汇: {', '.join(found_blocked)}")
            else:
                warnings.append(f"可能包含敏感词汇: {', '.join(found_blocked)}")

        # 重复字符检查
        if len(set(text)) < len(text) * 0.1:  # 字符多样性过低
            warnings.append("字符多样性过低,可能为垃圾输入")

        # 空白字符比例检查
        whitespace_count = sum(1 for c in text if c.isspace())
        if whitespace_count > len(text) * 0.5:
            warnings.append("空白字符比例过高")

        return {'issues': issues, 'warnings': warnings}

    def _detect_security_threats(self, text: str) -> dict[str, list[SecurityThreat]]:
        """检测安全威胁"""
        threats = []

        # XSS检测
        for category, patterns in self.xss_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    threats.append(SecurityThreat(
                        threat_type="xss",
                        description=f"检测到XSS攻击模式: {category}",
                        severity=ThreatLevel.HIGH,
                        pattern=pattern,
                        location=(match.start(), match.end()),
                        mitigation="移除或转义HTML特殊字符"
                    ))

        # SQL注入检测
        for category, patterns in self.sql_injection_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    threats.append(SecurityThreat(
                        threat_type="sql_injection",
                        description=f"检测到SQL注入模式: {category}",
                        severity=ThreatLevel.CRITICAL,
                        pattern=pattern,
                        location=(match.start(), match.end()),
                        mitigation="使用参数化查询和输入验证"
                    ))

        # 命令注入检测
        for category, patterns in self.command_injection_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    threats.append(SecurityThreat(
                        threat_type="command_injection",
                        description=f"检测到命令注入模式: {category}",
                        severity=ThreatLevel.CRITICAL,
                        pattern=pattern,
                        location=(match.start(), match.end()),
                        mitigation="避免直接执行用户输入"
                    ))

        # 路径遍历检测
        for pattern in self.path_traversal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                threats.append(SecurityThreat(
                    threat_type="path_traversal",
                    description="检测到路径遍历攻击",
                    severity=ThreatLevel.HIGH,
                    pattern=pattern,
                    location=(match.start(), match.end()),
                    mitigation="验证和规范化文件路径"
                ))

        return {'threats': threats}

    def _detect_malicious_code(self, text: str) -> dict[str, list[SecurityThreat]]:
        """检测恶意代码"""
        threats = []

        # Python代码检测
        try:
            ast.parse(text)
            # 如果能够解析为Python代码,可能是恶意的
            if any(keyword in text.lower() for keyword in ['import', 'exec', 'eval', '__import__']):
                threats.append(SecurityThreat(
                    threat_type="malicious_code",
                    description="检测到可疑的Python代码",
                    severity=ThreatLevel.MEDIUM,
                    pattern="Python AST",
                    location=None,
                    mitigation="避免执行用户提供的代码"
                ))
        except Exception:
            pass  # 不是有效的Python代码

        # JavaScript代码检测
        js_keywords = ['function', 'var', 'let', 'const', 'eval', 'set_timeout', 'set_interval']
        if sum(1 for keyword in js_keywords if keyword in text) > 2:
            threats.append(SecurityThreat(
                threat_type="malicious_code",
                description="检测到可疑的JavaScript代码",
                severity=ThreatLevel.MEDIUM,
                pattern="JavaScript keywords",
                location=None,
                mitigation="避免执行用户提供的脚本"
            ))

        # Shell脚本检测
        shell_keywords = ['#!/bin/bash', 'sudo', 'chmod', 'chown', 'rm -rf']
        if any(keyword in text for keyword in shell_keywords):
            threats.append(SecurityThreat(
                threat_type="malicious_code",
                description="检测到可疑的Shell命令",
                severity=ThreatLevel.HIGH,
                pattern="Shell commands",
                location=None,
                mitigation="避免执行用户提供的Shell命令"
            ))

        # Base64编码的可疑内容
        base64_pattern = re.compile(r'[A-Za-z0-9+/]{40,}={0,2}')
        for match in base64_pattern.finditer(text):
            try:
                decoded = base64.b64decode(match.group()).decode('utf-8')
                # 检查解码后是否包含可疑内容
                if any(pattern in decoded.lower() for pattern in ['script', 'eval', 'exec']):
                    threats.append(SecurityThreat(
                        threat_type="malicious_code",
                        description="检测到Base64编码的可疑内容",
                        severity=ThreatLevel.MEDIUM,
                        pattern="Base64 encoded suspicious content",
                        location=(match.start(), match.end()),
                        mitigation="解码并验证Base64内容"
                    ))
            except Exception as e:
                logger.warning(f'操作失败: {e}')

        return {'threats': threats}

    def _sanitize_input(self, text: str) -> str:
        """清理输入"""
        # HTML转义
        sanitized = html.escape(text)

        # 移除控制字符
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)

        # 标准化空白字符
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # 移除零宽字符
        sanitized = re.sub(r'[\u200b-\u200f\u2060-\u206f]', '', sanitized)

        return sanitized

    def _analyze_complexity(self, text: str) -> dict[str, Any]:
        """分析输入复杂度"""
        metrics = {}

        # 字符统计
        metrics['char_count'] = len(text)
        metrics['unique_char_count'] = len(set(text))
        metrics['char_diversity'] = metrics['unique_char_count'] / metrics['char_count'] if text else 0

        # 单词统计
        words = re.findall(r'\b\w+\b', text)
        metrics['word_count'] = len(words)
        metrics['unique_word_count'] = len(set(words))
        metrics['word_diversity'] = metrics['unique_word_count'] / metrics['word_count'] if words else 0

        # 句子统计
        sentences = re.split(r'[.!?。!?]+', text)
        metrics['sentence_count'] = len([s for s in sentences if s.strip()])

        # 语言检测(简单版本)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-z_a-Z]', text))
        total_chars = metrics['char_count']

        if total_chars > 0:
            metrics['chinese_ratio'] = chinese_chars / total_chars
            metrics['english_ratio'] = english_chars / total_chars
        else:
            metrics['chinese_ratio'] = 0
            metrics['english_ratio'] = 0

        return metrics

    def _determine_status(self, issues: list[list[str], warnings: list[list[str] = None, security_issues: list[list[str] = None) -> ValidationStatus]]]:
        """确定验证状态"""
        if security_issues is None:
            security_issues = []
        if warnings is None:
            warnings = []

        # 严重安全问题
        critical_threats = [issue for issue in security_issues
                           if hasattr(issue, 'severity') and issue.severity == ThreatLevel.CRITICAL]
        if critical_threats:
            return ValidationStatus.BLOCKED

        # 高威胁安全问题
        high_threats = [issue for issue in security_issues
                       if hasattr(issue, 'severity') and issue.severity == ThreatLevel.HIGH]
        if high_threats:
            return ValidationStatus.INVALID

        # 基础验证问题
        if issues:
            return ValidationStatus.INVALID

        # 警告
        if warnings:
            return ValidationStatus.WARNING

        # 通过
        return ValidationStatus.VALID

    def _determine_threat_level(self, security_issues: list[Any]) -> ThreatLevel:
        """确定威胁等级"""
        if not security_issues:
            return ThreatLevel.NONE

        # 检查最高威胁等级
        max_severity = ThreatLevel.NONE
        for issue in security_issues:
            if hasattr(issue, 'severity') and issue.severity.value > max_severity.value:
                max_severity = issue.severity

        return max_severity

    def _get_validation_cache_key(self, text: str, context: Optional[dict[str, Any]] = None) -> str:
        """生成验证缓存键"""
        content = text + json.dumps(context or {}, sort_keys=True)
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

    def _update_stats(self, result: ValidationResult):
        """更新统计信息"""
        self.validation_stats['total_validations'] += 1
        self.validation_stats['status_distribution'][result.status.value] += 1
        self.validation_stats['threat_distribution'][result.threat_level.value] += 1

        if result.status == ValidationStatus.BLOCKED:
            self.validation_stats['blocked_inputs'] += 1

        # 记录常见问题
        for issue in result.issues[:5]:  # 只记录前5个
            self.validation_stats['common_issues'][issue] += 1

    def batch_validate(self, inputs: list[str]) -> list[ValidationResult]:
        """批量验证"""
        return [self.validate_input(text) for text in inputs]

    def get_validation_stats(self) -> dict[str, Any]:
        """获取验证统计"""
        return {
            'stats': self.validation_stats.copy(),
            'cache_size': len(self.validation_cache),
            'validation_level': self.validation_level.value,
            'timestamp': datetime.now().isoformat()
        }

    def clear_cache(self):
        """清理缓存"""
        with self.cache_lock:
            self.validation_cache.clear()
        logger.info("🧹 验证缓存已清理")

    def is_safe(self, text: str) -> bool:
        """快速安全检查"""
        result = self.validate_input(text)
        return result.status in [ValidationStatus.VALID, ValidationStatus.WARNING]

    def sanitize_and_validate(self, text: str) -> tuple[str, ValidationResult]:
        """清理并验证输入"""
        # 先清理
        sanitized = self._sanitize_input(text)
        # 再验证
        result = self.validate_input(sanitized)
        return sanitized, result

# 使用示例
if __name__ == "__main__":
    print("🧪 测试输入验证和安全检查器...")

    # 创建不同级别的验证器
    permissive_validator = InputValidator(ValidationLevel.PERMISSIVE)
    strict_validator = InputValidator(ValidationLevel.STRICT)
    paranoid_validator = InputValidator(ValidationLevel.PARANOID)

    # 安全修复: 这些是用于测试安全验证器的恶意输入样本
    # ⚠️ 警告: 这些字符串仅用于测试,严禁在生产环境执行
    # 使用转义和注释明确标注这些是测试数据
    test_inputs = [
        "正常的输入文本,用于测试验证功能",
        "",  # 空输入
        "a" * 5,  # 过短
        "a" * 50000,  # 过长
        "包含<script>alert('xss')</script>的恶意输入",  # XSS测试样本
        "SELECT * FROM users WHERE id = 1 OR 1=1",  # SQL注入测试样本(仅字符串)
        "rm -rf /",  # 命令注入测试样本(仅字符串,不会执行)
        "../../../etc/passwd",  # 路径遍历测试样本(仅字符串)
        "import os; os.system('rm -rf /')",  # 恶意代码测试样本(仅字符串,不会执行)
        "包含敏感词汇的政治内容",
        "JavaScript: alert('xss')",
        "<?php system($_GET['cmd']); ?>",
        "normal text with emoji 😊 and chinese 中文",
        "Text with\tcontrol\ncharacters",
        "Text with   multiple   spaces",
    ]

    # 额外的安全检查:确保这不是在生产环境运行
    import os
    import sys
    if os.environ.get('PYTHON_ENV') == 'production':
        logger.warning("⚠️ 安全测试在生产环境中被禁用")
        sys.exit(0)  # 安全退出,而不是return

    print("\n🔍 测试不同验证级别的结果:")
    for i, text in enumerate(test_inputs):
        print(f"\n📝 测试 {i+1}: {text[:50]!r}")

        # 标准验证
        result = permissive_validator.validate_input(text)
        print(f"   宽松验证: {result.status.value} (威胁: {result.threat_level.value})")
        if result.issues:
            print(f"      问题: {result.issues[:2]}")

        # 严格验证
        result = strict_validator.validate_input(text)
        print(f"   严格验证: {result.status.value} (威胁: {result.threat_level.value})")
        if result.issues:
            print(f"      问题: {result.issues[:2]}")

        # 偏执验证
        result = paranoid_validator.validate_input(text)
        print(f"   偏执验证: {result.status.value} (威胁: {result.threat_level.value})")
        if result.issues:
            print(f"      问题: {result.issues[:2]}")

    # 测试快速安全检查
    print("\n⚡ 快速安全检查测试:")
    safe_inputs = [
        "这是一个安全的输入",
        "包含中英文的安全输入 Safe text",
    ]
    unsafe_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
    ]

    for text in safe_inputs + unsafe_inputs:
        is_safe = permissive_validator.is_safe(text)
        print(f"   {text[:30]!r}: {'✅ 安全' if is_safe else '❌ 不安全'}")

    # 显示统计
    print("\n📊 验证统计:")
    stats = permissive_validator.get_validation_stats()
    print(f"   总验证数: {stats['stats']['total_validations']}")
    print(f"   状态分布: {dict(stats['stats']['status_distribution'])}")
    print(f"   威胁分布: {dict(stats['stats']['threat_distribution'])}")
    print(f"   阻止输入: {stats['stats']['blocked_inputs']}")

    print("\n✅ 输入验证和安全检查器测试完成!")

