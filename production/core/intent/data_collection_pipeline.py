#!/usr/bin/env python3
"""
意图识别数据收集管道
Intent Recognition Data Collection Pipeline

第一阶段优化:数据收集和管道部署

功能:
1. 收集历史对话数据
2. 收集实时用户反馈
3. 数据质量验证
4. 数据标注和管理

作者: 小诺·双鱼公主
版本: v1.0.0
创建: 2025-12-29
"""

from __future__ import annotations
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class DataCollectionPipeline:
    """数据收集管道"""

    def __init__(self, db_path: str | None = None):
        """初始化数据收集管道

        Args:
            db_path: 数据库路径,默认为 data/intent_recognition/data.db
        """
        if db_path is None:
            db_path = project_root / "data/intent_recognition/data.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

        # 数据质量规则
        self.quality_rules = {
            "min_length": 2,  # 最小字符数
            "max_length": 500,  # 最大字符数
            "min_words": 1,  # 最小词数
            "required_fields": ["text", "intent", "timestamp"],
        }

        logger.info(f"✅ 数据收集管道初始化完成: {self.db_path}")

    def _init_database(self) -> Any:
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建对话数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                text TEXT NOT NULL,
                intent TEXT,
                predicted_intent TEXT,
                confidence REAL,
                context TEXT,
                timestamp TEXT NOT NULL,
                source TEXT,
                validated BOOLEAN DEFAULT 0,
                quality_score REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建意图标注表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intent_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                intent TEXT NOT NULL,
                labeler TEXT,
                confidence REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        # 创建数据质量统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_collected INTEGER DEFAULT 0,
                validated INTEGER DEFAULT 0,
                quality_avg REAL DEFAULT 0.0,
                intent_distribution TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON conversations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_intent ON conversations(intent)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_validated ON conversations(validated)")

        conn.commit()
        conn.close()

        logger.info("✅ 数据库表结构初始化完成")

    def collect_conversation(
        self,
        user_id: str,
        text: str,
        intent: str | None = None,
        predicted_intent: str | None = None,
        confidence: float | None = None,
        context: dict | None = None,
        source: str = "manual",
    ) -> bool:
        """收集对话数据

        Args:
            user_id: 用户ID
            text: 用户输入文本
            intent: 真实意图标签(如果有)
            predicted_intent: 预测的意图
            confidence: 预测置信度
            context: 上下文信息
            source: 数据来源(manual/api/feedback)

        Returns:
            bool: 是否成功收集
        """
        try:
            # 数据质量验证
            quality_score = self._validate_data(text)

            if quality_score < 0.3:
                logger.warning(f"⚠️ 数据质量过低,跳过: {text[:50]}...")
                return False

            # 插入数据
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO conversations
                (user_id, text, intent, predicted_intent, confidence, context, timestamp, source, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    text,
                    intent,
                    predicted_intent,
                    confidence,
                    json.dumps(context) if context else None,
                    datetime.now().isoformat(),
                    source,
                    quality_score,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"✅ 收集对话数据: {text[:50]}...")
            return True

        except Exception as e:
            logger.error(f"❌ 收集对话数据失败: {e}")
            return False

    def collect_from_history(self, history_file: str) -> int:
        """从历史文件收集数据

        Args:
            history_file: 历史数据文件路径

        Returns:
            int: 成功收集的数据条数
        """
        try:
            history_path = Path(history_file)
            if not history_path.exists():
                logger.error(f"❌ 历史文件不存在: {history_file}")
                return 0

            with open(history_path, encoding="utf-8") as f:
                history_data = json.load(f)

            collected = 0
            for item in history_data:
                if self.collect_conversation(
                    user_id=item.get("user_id", "dad"),
                    text=item.get("text", ""),
                    intent=item.get("intent"),
                    predicted_intent=item.get("predicted_intent"),
                    confidence=item.get("confidence"),
                    context=item.get("context"),
                    source="history",
                ):
                    collected += 1

            logger.info(f"✅ 从历史文件收集 {collected} 条数据")
            return collected

        except Exception as e:
            logger.error(f"❌ 从历史文件收集数据失败: {e}")
            return 0

    def collect_feedback(
        self,
        user_id: str,
        text: str,
        predicted_intent: str,
        correct_intent: str,
        was_correct: bool,
        confidence: float,
    ) -> bool:
        """收集用户反馈数据

        Args:
            user_id: 用户ID
            text: 用户输入文本
            predicted_intent: 预测的意图
            correct_intent: 正确的意图
            was_correct: 预测是否正确
            confidence: 预测置信度

        Returns:
            bool: 是否成功收集
        """
        try:
            # 插入反馈数据
            intent = correct_intent if was_correct else None

            return self.collect_conversation(
                user_id=user_id,
                text=text,
                intent=intent,
                predicted_intent=predicted_intent,
                confidence=confidence,
                context={"type": "feedback", "was_correct": was_correct},
                source="feedback",
            )

        except Exception as e:
            logger.error(f"❌ 收集反馈数据失败: {e}")
            return False

    def _validate_data(self, text: str) -> float:
        """验证数据质量

        Args:
            text: 待验证文本

        Returns:
            float: 质量分数 (0-1)
        """
        score = 1.0

        # 长度检查
        text_len = len(text)
        if text_len < self.quality_rules["min_length"]:
            score -= 0.5
        if text_len > self.quality_rules["max_length"]:
            score -= 0.3

        # 词数检查
        words = text.split()
        if len(words) < self.quality_rules["min_words"]:
            score -= 0.3

        # 内容检查
        if not text.strip():
            score -= 0.5

        # 特殊字符检查
        special_chars = sum(
            1 for c in text if not c.isalnum() and not c.isspace() and not "\u4e00" <= c <= "\u9fff"
        )
        if special_chars > len(text) * 0.3:
            score -= 0.2

        return max(0.0, score)

    def get_statistics(self) -> dict[str, Any]:
        """获取数据统计信息

        Returns:
            dict: 统计信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总数据量
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total = cursor.fetchone()[0]

        # 已验证数据量
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE validated = 1")
        validated = cursor.fetchone()[0]

        # 意图分布
        cursor.execute("""
            SELECT intent, COUNT(*) as count
            FROM conversations
            WHERE intent IS NOT NULL
            GROUP BY intent
            ORDER BY count DESC
        """)
        intent_dist = dict(cursor.fetchall())

        # 平均质量分数
        cursor.execute("SELECT AVG(quality_score) FROM conversations")
        avg_quality = cursor.fetchone()[0] or 0.0

        # 数据来源分布
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM conversations
            GROUP BY source
        """)
        source_dist = dict(cursor.fetchall())

        conn.close()

        return {
            "total_collected": total,
            "validated": validated,
            "validation_rate": validated / max(total, 1),
            "intent_distribution": intent_dist,
            "avg_quality_score": avg_quality,
            "source_distribution": source_dist,
        }

    def export_data(self, output_file: str, validated_only: bool = False) -> int:
        """导出数据为JSON格式

        Args:
            output_file: 输出文件路径
            validated_only: 是否只导出已验证的数据

        Returns:
            int: 导出的数据条数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM conversations"
            if validated_only:
                query += " WHERE validated = 1"

            cursor.execute(query)
            rows = cursor.fetchall()

            # 获取列名
            columns = [description[0] for description in cursor.description]

            data = []
            for row in rows:
                item = dict(zip(columns, row, strict=False))
                # 解析context JSON
                if item.get("context"):
                    try:
                        item["context"] = json.loads(item["context"])
                    except Exception as e:
                        logger.debug(f"空except块已触发: {e}")
                        pass
                data.append(item)

            # 保存为JSON
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            conn.close()

            logger.info(f"✅ 导出 {len(data)} 条数据到: {output_file}")
            return len(data)

        except Exception as e:
            logger.error(f"❌ 导出数据失败: {e}")
            return 0


# 全局实例
_pipeline = None


def get_data_pipeline() -> DataCollectionPipeline:
    """获取数据收集管道实例"""
    global _pipeline
    if _pipeline is None:
        _pipeline = DataCollectionPipeline()
    return _pipeline


async def main():
    """主程序 - 演示数据收集管道的使用"""
    print("🎯 意图识别数据收集管道")
    print("=" * 60)

    pipeline = get_data_pipeline()

    # 1. 收集示例数据
    print("\n📝 收集示例数据...")

    sample_data = [
        ("分析这个专利", "PATENT_ANALYSIS"),
        ("帮我写代码", "CODE_GENERATION"),
        ("谢谢爸爸", "EMOTIONAL"),
        ("启动服务", "SYSTEM_CONTROL"),
        ("解释法律条款", "LEGAL_QUERY"),
    ]

    for text, intent in sample_data:
        pipeline.collect_conversation(user_id="dad", text=text, intent=intent, source="demo")

    # 2. 收集反馈数据
    print("\n📝 收集反馈数据...")
    pipeline.collect_feedback(
        user_id="dad",
        text="查一下专利",
        predicted_intent="PATENT_SEARCH",
        correct_intent="PATENT_SEARCH",
        was_correct=True,
        confidence=0.85,
    )

    # 3. 获取统计信息
    print("\n📊 数据统计:")
    stats = pipeline.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # 4. 导出数据
    print("\n💾 导出数据...")
    pipeline.export_data(project_root / "data/intent_recognition/exported_data.json")

    print("\n✅ 数据收集管道演示完成!")


# 入口点: @async_main装饰器已添加到main函数
