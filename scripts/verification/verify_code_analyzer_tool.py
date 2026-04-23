#!/usr/bin/env python3
"""
code_analyzer工具验证脚本

验证code_analyzer工具的功能和性能，包括：
1. Python代码分析
2. JavaScript代码分析
3. 复杂度计算
4. 问题检测
5. 详细模式vs基础模式对比
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.tool_implementations import code_analyzer_handler


# 测试代码样本
PYTHON_CODE_SIMPLE = """
def hello_world():
    print("Hello, World!")

hello_world()
"""

PYTHON_CODE_COMPLEX = """
class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.processed = False

    def process(self):
        if not self.data:
            return None
        elif len(self.data) > 100:
            for item in self.data:
                try:
                    result = self.transform(item)
                    if result:
                        self.save(result)
                except Exception as e:
                    print(f"Error: {e}")
        else:
            return self.data

    def transform(self, item):
        return item.upper()

    def save(self, result):
        with open("output.txt", "a") as f:
            f.write(str(result))

# 使用示例
processor = DataProcessor([1, 2, 3])
processor.process()
"""

JAVASCRIPT_CODE = """
class UserService {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.users = [];
    }

    async fetchUsers() {
        try {
            const response = await this.apiClient.get('/users');
            if (response.status === 200) {
                this.users = response.data;
                console.log('Users fetched:', this.users.length);
                return this.users;
            } else {
                console.error('Failed to fetch users');
                return [];
            }
        } catch (error) {
            console.error('Error:', error);
            return [];
        }
    }

    filterActiveUsers() {
        return this.users.filter(user => user.active);
    }
}

// 使用示例
const service = new UserService(apiClient);
service.fetchUsers();
"""

TYPESCRIPT_CODE = """
interface User {
    id: number;
    name: string;
    email: string;
    active: boolean;
}

class UserManager {
    private users: Map<number, User> = new Map();

    constructor(private database: DatabaseService) {}

    async addUser(user: User): Promise<void> {
        if (this.users.has(user.id)) {
            throw new Error(`User ${user.id} already exists`);
        }

        await this.database.save(user);
        this.users.set(user.id, user);
    }

    getUser(id: number): User | undefined {
        return this.users.get(id);
    }

    getAllActiveUsers(): User[] {
        return Array.from(this.users.values())
            .filter(user => user.active);
    }
}
"""


def print_section(title: str):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


async def test_python_analysis():
    """测试Python代码分析"""
    print_section("测试1: Python代码分析")

    # 简单Python代码
    print("\n【简单Python代码】")
    result = await code_analyzer_handler(
        params={
            "code": PYTHON_CODE_SIMPLE,
            "language": "python",
            "style": "detailed"
        },
        context={}
    )

    print(f"语言: {result['language']}")
    print(f"总行数: {result['statistics']['total_lines']}")
    print(f"代码行数: {result['statistics']['code_lines']}")
    print(f"注释行数: {result['statistics']['comment_lines']}")
    print(f"注释比例: {result['statistics']['comment_ratio']}")
    print(f"复杂度分数: {result['complexity']['score']}")
    print(f"复杂度等级: {result['complexity']['level']}")
    print(f"检测到的问题: {result['issues']}")
    print(f"建议: {[s for s in result['suggestions'] if s]}")

    # 复杂Python代码
    print("\n【复杂Python代码】")
    result = await code_analyzer_handler(
        params={
            "code": PYTHON_CODE_COMPLEX,
            "language": "python",
            "style": "detailed"
        },
        context={}
    )

    print(f"总行数: {result['statistics']['total_lines']}")
    print(f"代码行数: {result['statistics']['code_lines']}")
    print(f"复杂度分数: {result['complexity']['score']}")
    print(f"复杂度等级: {result['complexity']['level']}")
    print(f"检测到的问题: {result['issues']}")
    print(f"建议: {[s for s in result['suggestions'] if s]}")


async def test_javascript_analysis():
    """测试JavaScript/TypeScript代码分析"""
    print_section("测试2: JavaScript/TypeScript代码分析")

    # JavaScript代码
    print("\n【JavaScript代码】")
    result = await code_analyzer_handler(
        params={
            "code": JAVASCRIPT_CODE,
            "language": "javascript",
            "style": "detailed"
        },
        context={}
    )

    print(f"语言: {result['language']}")
    print(f"总行数: {result['statistics']['total_lines']}")
    print(f"代码行数: {result['statistics']['code_lines']}")
    print(f"注释行数: {result['statistics']['comment_lines']}")
    print(f"复杂度分数: {result['complexity']['score']}")
    print(f"复杂度等级: {result['complexity']['level']}")
    print(f"检测到的问题: {result['issues']}")
    print(f"建议: {[s for s in result['suggestions'] if s]}")

    # TypeScript代码
    print("\n【TypeScript代码】")
    result = await code_analyzer_handler(
        params={
            "code": TYPESCRIPT_CODE,
            "language": "typescript",
            "style": "detailed"
        },
        context={}
    )

    print(f"总行数: {result['statistics']['total_lines']}")
    print(f"代码行数: {result['statistics']['code_lines']}")
    print(f"复杂度分数: {result['complexity']['score']}")
    print(f"复杂度等级: {result['complexity']['level']}")


async def test_complexity_calculation():
    """测试复杂度计算"""
    print_section("测试3: 复杂度计算准确性")

    # 测试不同复杂度的代码
    test_cases = [
        ("简单", "x = 1\ny = 2\nprint(x + y)"),
        ("中等", PYTHON_CODE_SIMPLE),
        ("复杂", PYTHON_CODE_COMPLEX),
    ]

    for name, code in test_cases:
        result = await code_analyzer_handler(
            params={"code": code, "language": "python"},
            context={}
        )
        print(f"\n{name}代码:")
        print(f"  复杂度分数: {result['complexity']['score']}")
        print(f"  复杂度等级: {result['complexity']['level']}")


async def test_issue_detection():
    """测试问题检测"""
    print_section("测试4: 问题检测功能")

    # 包含问题的Python代码
    problematic_code = """
def debug_function():
    print("Debugging...")
    # 这一行非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的行超过了100字符限制
    for i in range(100):
        print(i)

def helper1():
    pass

def helper2():
    pass

def helper3():
    pass

def helper4():
    pass

def helper5():
    pass

def helper6():
    pass

def helper7():
    pass

def helper8():
    pass

def helper9():
    pass

def helper10():
    pass

def helper11():
    pass
"""

    result = await code_analyzer_handler(
        params={
            "code": problematic_code,
            "language": "python",
            "style": "detailed"
        },
        context={}
    )

    print(f"\n检测到的问题数量: {len(result['issues'])}")
    for i, issue in enumerate(result['issues'], 1):
        print(f"  {i}. {issue}")


async def test_basic_vs_detailed():
    """测试基础模式vs详细模式"""
    print_section("测试5: 基础模式 vs 详细模式")

    code = PYTHON_CODE_COMPLEX

    # 基础模式
    print("\n【基础模式】")
    result_basic = await code_analyzer_handler(
        params={"code": code, "language": "python", "style": "basic"},
        context={}
    )

    print(f"总行数: {result_basic['statistics']['total_lines']}")
    print(f"复杂度: {result_basic['complexity']['level']}")
    print(f"检测到的问题: {result_basic['issues']} (基础模式不检测问题)")
    print(f"建议: {[s for s in result_basic['suggestions'] if s]}")

    # 详细模式
    print("\n【详细模式】")
    result_detailed = await code_analyzer_handler(
        params={"code": code, "language": "python", "style": "detailed"},
        context={}
    )

    print(f"总行数: {result_detailed['statistics']['total_lines']}")
    print(f"复杂度: {result_detailed['complexity']['level']}")
    print(f"检测到的问题: {result_detailed['issues']}")
    print(f"建议: {[s for s in result_detailed['suggestions'] if s]}")


async def test_performance():
    """测试性能"""
    print_section("测试6: 性能测试")

    import time

    code = PYTHON_CODE_COMPLEX * 10  # 放大代码量

    iterations = 100
    start_time = time.time()

    for _ in range(iterations):
        await code_analyzer_handler(
            params={"code": code, "language": "python"},
            context={}
        )

    elapsed = time.time() - start_time
    avg_time = (elapsed / iterations) * 1000  # 转换为毫秒

    print(f"迭代次数: {iterations}")
    print(f"总耗时: {elapsed:.2f}秒")
    print(f"平均耗时: {avg_time:.2f}毫秒/次")
    print(f"吞吐量: {iterations/elapsed:.2f}次/秒")


async def test_edge_cases():
    """测试边界情况"""
    print_section("测试7: 边界情况")

    # 空代码
    print("\n【空代码】")
    result = await code_analyzer_handler(
        params={"code": "", "language": "python"},
        context={}
    )
    print(f"总行数: {result['statistics']['total_lines']}")
    print(f"非空行数: {result['statistics']['non_empty_lines']}")

    # 只有注释
    print("\n【只有注释】")
    result = await code_analyzer_handler(
        params={"code": "# 这是注释\n# 另一行注释", "language": "python"},
        context={}
    )
    print(f"注释行数: {result['statistics']['comment_lines']}")

    # 不支持的语言
    print("\n【不支持的语言】")
    result = await code_analyzer_handler(
        params={"code": "some code", "language": "rust"},
        context={}
    )
    print(f"语言: {result['language']}")
    print(f"复杂度分数: {result['complexity']['score']}")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  code_analyzer工具验证测试")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        await test_python_analysis()
        await test_javascript_analysis()
        await test_complexity_calculation()
        await test_issue_detection()
        await test_basic_vs_detailed()
        await test_performance()
        await test_edge_cases()

        print_section("测试完成")
        print("\n✅ 所有测试通过！")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
