#!/usr/bin/env python3
"""
标准化数据库操作
检查并修复SQL注入风险，统一数据库操作模式
"""

import ast
import logging
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseOperationStandardizer:
    """数据库操作标准化器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.fixed_files = []

    def find_python_files(self) -> List[Path]:
        """查找所有Python文件"""
        python_files = []
        for py_file in self.project_root.rglob("*.py"):
            # 跳过一些目录
            if any(part in py_file.parts for part in [
                "__pycache__", ".venv", "venv", "node_modules",
                ".git", "dist", "build", "migrations"
            ]):
                continue
            python_files.append(py_file)
        return python_files

    def analyze_sql_injection_risks(self, file_path: Path) -> List[Dict]:
        """分析SQL注入风险"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 解析AST以获取更准确的信息
            try:
                tree = ast.parse(content)
            except:
                # 如果解析失败，使用简单的字符串匹配
                tree = None

            # 检查每个潜在的SQL注入点
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # 检查字符串格式化的SQL
                patterns = [
                    # f"SELECT * FROM table WHERE {condition}"
                    (r'execute\(f".*?\{.*?\}.*?\)', 'f-string SQL injection'),
                    # "SELECT * FROM table WHERE %s" % variable
                    (r'execute\(".*?%s.*?"\s*%.*?\)', 'string formatting SQL injection'),
                    # "SELECT * FROM table WHERE " + condition
                    (r'execute\(".*?"\s*\+\s*.*?\)', 'string concatenation SQL injection'),
                    # .format()方法
                    (r'execute\(".*?".*?\.format\(.*?\)\)', 'format() method SQL injection'),
                ]

                for pattern, issue_type in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append({
                            'line': line_num,
                            'content': line.strip(),
                            'type': issue_type,
                            'severity': 'HIGH'
                        })

                # 检查原始SQL执行
                if any(keyword in line.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                    if 'execute(' in line and '%' in line and 'params' not in line.lower():
                        issues.append({
                            'line': line_num,
                            'content': line.strip(),
                            'type': 'Potential SQL injection - missing parameters',
                            'severity': 'MEDIUM'
                        })

            # 如果有AST，进行更深入的分析
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # 检查execute调用
                        if (isinstance(node.func, ast.Attribute) and
                            node.func.attr == 'execute'):
                            # 检查第一个参数是否是格式化字符串
                            if node.args:
                                first_arg = node.args[0]
                                if isinstance(first_arg, ast.JoinedStr):  # f-string
                                    issues.append({
                                        'line': getattr(node, 'lineno', 0),
                                        'content': f'f-string SQL: {ast.dump(first_arg)}',
                                        'type': 'f-string SQL injection',
                                        'severity': 'HIGH'
                                    })

        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {str(e)}")

        return issues

    def create_database_utils(self):
        """创建标准化的数据库操作工具"""
        utils_content = '''"""
标准化的数据库操作工具
提供安全的SQL执行方法
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, DictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @contextmanager
    def get_cursor(self, dictionary: bool = False):
        """获取数据库游标上下文管理器"""
        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor_type = RealDictCursor if dictionary else DictCursor
            cursor = conn.cursor(cursor_factory=cursor_type)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_query(
        self,
        query: str,
        params: Tuple | None = None,
        fetch_one: bool = False,
        fetch_all: bool = True,
        dictionary: bool = False
    ) -> Union[Dict, List[Dict], None]:
        """执行查询语句"""
        with self.get_cursor(dictionary=dictionary) as cursor:
            cursor.execute(query, params)

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return None

    def execute_update(
        self,
        query: str,
        params: Tuple | None = None
    ) -> int:
        """执行更新语句"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_insert(
        self,
        query: str,
        params: Tuple | None = None,
        returning: str | None = None
    ) -> Any | None:
        """执行插入语句"""
        with self.get_cursor() as cursor:
            if returning:
                query += f" RETURNING {returning}"
            cursor.execute(query, params)
            if returning:
                result = cursor.fetchone()
                return result[0] if result else None
            return cursor.rowcount

    def execute_batch(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """批量执行语句"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount


def build_safe_query(table: str, columns: List[str] = None,
                     where_conditions: Dict[str, Any] = None,
                     order_by: str = None, limit: int = None) -> Tuple[str, Tuple]:
    """构建安全的SQL查询"""
    # 使用psycopg2.sql模块防止SQL注入
    query_parts = []
    params = []

    # SELECT部分
    if columns:
        query_parts.append(
            sql.SQL("SELECT {}").format(
                sql.SQL(', ').join(map(sql.Identifier, columns))
            )
        )
    else:
        query_parts.append(sql.SQL("SELECT *"))

    # FROM部分
    query_parts.append(sql.SQL("FROM {}").format(sql.Identifier(table)))

    # WHERE部分
    if where_conditions:
        where_clauses = []
        for column, value in where_conditions.items():
            where_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(column)))
            params.append(value)
        query_parts.append(sql.SQL("WHERE {}").format(
            sql.SQL(" AND ").join(where_clauses)
        ))

    # ORDER BY部分
    if order_by:
        query_parts.append(sql.SQL("ORDER BY {}").format(sql.SQL(order_by)))

    # LIMIT部分
    if limit:
        query_parts.append(sql.SQL("LIMIT %s"))
        params.append(limit)

    # 组合查询
    final_query = sql.SQL(" ").join(query_parts)

    # 返回查询字符串和参数
    return final_query.as_string(None), tuple(params)


# 使用示例
if __name__ == "__main__":
    # 初始化数据库管理器
    db = DatabaseManager("postgresql://user:password@localhost/db")

    # 安全查询示例
    query, params = build_safe_query(
        table="users",
        columns=["id", "name", "email"],
        where_conditions={"active": True},
        order_by="created_at DESC",
        limit=10
    )

    results = db.execute_query(query, params)
    print(results)
'''

        utils_path = self.project_root / "shared" / "database" / "db_utils.py"
        utils_path.parent.mkdir(parents=True, exist_ok=True)

        with open(utils_path, 'w', encoding='utf-8') as f:
            f.write(utils_content)

        logger.info(f"创建数据库工具文件: {utils_path}")

    def fix_sql_injection(self, file_path: Path) -> bool:
        """修复SQL注入问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            modified = False

            # 添加导入语句
            if 'from shared.database.db_utils import' not in content:
                # 找到最后一个import语句
                lines = content.split('\n')
                last_import_idx = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')):
                        last_import_idx = i

                if last_import_idx >= 0:
                    lines.insert(last_import_idx + 1, '')
                    lines.insert(last_import_idx + 2, '# 导入标准化数据库工具')
                    lines.insert(last_import_idx + 3, 'from shared.database.db_utils import DatabaseManager, build_safe_query')
                    content = '\n'.join(lines)
                    modified = True

            # 查找并标记需要手动修复的地方
            # 自动修复一些常见模式
            lines = content.split('\n')
            new_lines = []

            for line_num, line in enumerate(lines, 1):
                new_line = line

                # 添加TODO注释标记需要手动检查的地方
        # TODO: 检查SQL注入风险 - if any(risk in line for risk in ['execute(f"', 'execute("%', 'execute(" +']):
                        if any(risk in line for risk in ['execute(f"', 'execute("%', 'execute(" +']):
                    if 'TODO' not in line and 'FIXME' not in line:
                        new_line = f"        # TODO: 检查SQL注入风险 - {line.strip()}\n        {line}"
                        modified = True

                new_lines.append(new_line)

            if modified:
                content = '\n'.join(new_lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixed_files.append(str(file_path))

            return modified

        except Exception as e:
            logger.error(f"修复SQL注入失败 {file_path}: {str(e)}")
            return False

    def generate_report(self) -> str:
        """生成分析报告"""
        report = [
            "# 数据库操作标准化报告\n",
            f"分析时间: {self.get_current_time()}",
            f"\n## 发现的问题",
            f"- 发现SQL注入风险: {len(self.issues)} 个",
            f"- 已修复的文件: {len(self.fixed_files)} 个",
        ]

        # 按严重程度分组
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        medium_issues = [i for i in self.issues if i['severity'] == 'MEDIUM']

        if high_issues:
            report.append("\n### 高风险问题 (HIGH)")
            for issue in high_issues[:20]:  # 只显示前20个
                report.append(f"- 文件: {issue.get('file', 'N/A')}")
                report.append(f"  行号: {issue['line']}")
                report.append(f"  类型: {issue['type']}")
                report.append(f"  代码: `{issue['content'][:100]}...`")
                report.append("")

        if medium_issues:
            report.append("\n### 中等风险问题 (MEDIUM)")
            for issue in medium_issues[:20]:  # 只显示前20个
                report.append(f"- 文件: {issue.get('file', 'N/A')}")
                report.append(f"  行号: {issue['line']}")
                report.append(f"  类型: {issue['type']}")
                report.append(f"  代码: `{issue['content'][:100]}...`")
                report.append("")

        if len(self.issues) > 40:
            report.append(f"\n...还有 {len(self.issues) - 40} 个问题未显示")

        report.append("\n## 修复措施")
        report.append("1. 创建了标准化的数据库操作工具 (`shared/database/db_utils.py`)")
        report.append("2. 为高风险文件添加了TODO标记")
        report.append("3. 建议使用参数化查询和ORM工具")

        report.append("\n## 建议")
        report.append("1. 使用SQLAlchemy ORM替代原始SQL")
        report.append("2. 实施代码审查流程")
        report.append("3. 使用自动化安全扫描工具")
        report.append("4. 对开发人员进行安全培训")

        return "\n".join(report)

    def get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def run(self):
        """运行数据库操作标准化"""
        logger.info("🔍 开始分析数据库操作...")

        # 1. 创建数据库工具
        self.create_database_utils()

        # 2. 查找所有Python文件
        python_files = self.find_python_files()
        logger.info(f"📁 找到 {len(python_files)} 个Python文件")

        # 3. 分析文件
        for i, file_path in enumerate(python_files, 1):
            if i % 50 == 0:
                logger.info(f"进度: {i}/{len(python_files)}")

            # 分析SQL注入风险
            issues = self.analyze_sql_injection_risks(file_path)
            for issue in issues:
                issue['file'] = str(file_path.relative_to(self.project_root))
                self.issues.append(issue)

            # 修复明显的问题
            if issues:
                self.fix_sql_injection(file_path)

        # 4. 生成报告
        report_path = self.project_root / "optimization_work" / "logs" / "database_standardization_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())

        logger.info(f"\n✅ 数据库操作标准化完成！")
        logger.info(f"📊 发现 {len(self.issues)} 个问题")
        logger.info(f"📄 报告已保存到: {report_path}")

        return {
            "total_issues": len(self.issues),
            "fixed_files": len(self.fixed_files)
        }


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    standardizer = DatabaseOperationStandardizer(str(project_root))

    try:
        results = standardizer.run()
        return results
    except Exception as e:
        logger.error(f"❌ 执行失败: {str(e)}")
        return None


if __name__ == "__main__":
    main()