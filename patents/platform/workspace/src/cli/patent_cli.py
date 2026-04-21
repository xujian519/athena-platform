#!/usr/bin/env python3
"""
Athena专利代理CLI工具
专业专利分析、撰写和审查的命令行界面
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PatentCLI:
    """专利代理CLI主类"""

    def __init__(self):
        self.workspace = Path('.')  # 当前工作目录
        self.tasks_dir = self.workspace / 'tasks'
        self.data_dir = self.workspace / 'data'

    def init_task(self, title: str, description: str = '') -> str:
        """初始化新的专利任务"""
        task_id = f"PAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task_dir = self.tasks_dir / task_id

        # 创建任务目录结构
        os.makedirs(task_dir / 'raw', exist_ok=True)
        os.makedirs(task_dir / 'novelty', exist_ok=True)
        os.makedirs(task_dir / 'creative', exist_ok=True)
        os.makedirs(task_dir / 'writing', exist_ok=True)
        os.makedirs(task_dir / 'check', exist_ok=True)
        os.makedirs(task_dir / 'response', exist_ok=True)

        # 创建任务状态文件
        task_info = {
            'task_id': task_id,
            'title': title,
            'description': description,
            'status': 'initialized',
            'created_at': datetime.now().isoformat(),
            'current_stage': 'ready',
            'stages': {
                'novelty': {'status': 'pending', 'started_at': None, 'completed_at': None},
                'creative': {'status': 'pending', 'started_at': None, 'completed_at': None},
                'writing': {'status': 'pending', 'started_at': None, 'completed_at': None},
                'check': {'status': 'pending', 'started_at': None, 'completed_at': None},
                'response': {'status': 'pending', 'started_at': None, 'completed_at': None}
            }
        }

        with open(task_dir / 'task.json', 'w', encoding='utf-8') as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 任务创建成功: {task_id}")
        logger.info(f"📁 任务目录: {task_dir}")
        return task_id

    def list_tasks(self) -> List[Dict]:
        """列出所有任务"""
        tasks = []
        for task_dir in self.tasks_dir.iterdir():
            if task_dir.is_dir():
                task_file = task_dir / 'task.json'
                if task_file.exists():
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task_info = json.load(f)
                        tasks.append(task_info)
        return tasks

    def show_task(self, task_id: str) -> Dict | None:
        """显示任务详情"""
        task_file = self.tasks_dir / task_id / 'task.json'
        if task_file.exists():
            with open(task_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def get_status(self, task_id: str = None):
        """获取任务状态"""
        if task_id:
            task_info = self.show_task(task_id)
            if task_info:
                logger.info(f"任务ID: {task_info['task_id']}")
                logger.info(f"标题: {task_info['title']}")
                logger.info(f"状态: {task_info['status']}")
                logger.info(f"当前阶段: {task_info['current_stage']}")
                logger.info(f"创建时间: {task_info['created_at']}")

                logger.info("\n📋 各阶段状态:")
                for stage, info in task_info['stages'].items():
                    status_icon = '✅' if info['status'] == 'completed' else '🔄' if info['status'] == 'running' else '⏳'
                    logger.info(f"  {status_icon} {stage}: {info['status']}")
            else:
                logger.info(f"❌ 任务 {task_id} 不存在")
        else:
            tasks = self.list_tasks()
            if tasks:
                logger.info(f"📋 共有 {len(tasks)} 个任务:")
                for task in tasks:
                    logger.info(f"  📄 {task['task_id']}: {task['title']} ({task['status']})")
            else:
                logger.info('📭 暂无任务')

    def execute_novelty_analysis(self, task_id: str):
        """执行新颖性分析（切片1）"""
        import os
        import sys

        # 添加src目录到Python路径
        src_path = os.path.join(os.getcwd(), 'src', 'models')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        import asyncio

        from novelty_analyzer import NoveltyAnalyzer

        # 检查任务是否存在
        task_info = self.show_task(task_id)
        if not task_info:
            logger.info(f"❌ 任务 {task_id} 不存在")
            return

        # 检查技术交底书是否存在
        task_dir = self.tasks_dir / task_id
        disclosure_file = task_dir / 'raw' / 'disclosure.md'

        # 如果目录不存在，创建它
        if not task_dir.exists():
            logger.info(f"❌ 任务目录不存在：{task_dir}")
            return

        os.makedirs(task_dir / 'raw', exist_ok=True)

        # 调试信息
        logger.info(f"🔍 查找技术交底书：{disclosure_file}")
        logger.info(f"📁 文件是否存在：{disclosure_file.exists()}")

        if not disclosure_file.exists():
            logger.info(f"❌ 技术交底书不存在：{disclosure_file}")
            logger.info('请先将技术交底书放入 raw 目录')
            logger.info(f"   路径：{disclosure_file}")
            # 列出raw目录内容
            raw_dir = task_dir / 'raw'
            if raw_dir.exists():
                files = os.listdir(raw_dir)
                logger.info(f"   raw目录内容：{files}")
            return

        # 读取技术交底书
        with open(disclosure_file, 'r', encoding='utf-8') as f:
            disclosure_text = f.read()

        logger.info(f"🔍 开始执行任务 {task_id} 的新颖性分析...")

        # 更新任务状态
        self.update_task_stage(task_id, 'novelty', 'running')

        try:
            # 执行新颖性分析
            analyzer = NoveltyAnalyzer()

            # 创建新的事件循环执行分析
            import nest_asyncio
            nest_asyncio.apply()

            # 同步执行异步函数
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(analyzer.analyze_novelty(task_id, disclosure_text))
            finally:
                loop.close()

            # 保存结果
            analyzer.save_result(task_id, result)

            # 更新任务状态
            self.update_task_stage(task_id, 'novelty', 'completed')

            # 显示结果
            logger.info(f"\n🎯 新颖性分析完成")
            logger.info(f"结果：{'✅ 具备新颖性' if result.overall_novelty else '❌ 不具备新颖性'}")
            logger.info(f"新颖性分数：{result.novelty_score:.2f}")
            logger.info(f"区别技术特征：{len(result.distinguishing_features)} 个")
            if result.closest_prior_art:
                logger.info(f"最接近现有技术：{result.closest_prior_art.title}")
            logger.info(f"\n💡 建议：{result.recommendation}")

            # HITL检查提示
            logger.info(f"\n⚠️  请人工确认分析结果：")
            logger.info(f"   查看：{self.tasks_dir / task_id / 'novelty' / 'analysis_result.json'}")
            logger.info(f"   确认命令：patent verify {task_id} --stage novelty")

        except Exception as e:
            logger.info(f"❌ 新颖性分析失败：{str(e)}")
            self.update_task_stage(task_id, 'novelty', 'failed')

    def update_task_stage(self, task_id: str, stage: str, status: str):
        """更新任务阶段状态"""
        task_file = self.tasks_dir / task_id / 'task.json'
        if task_file.exists():
            with open(task_file, 'r', encoding='utf-8') as f:
                task_info = json.load(f)

            from datetime import datetime
            now = datetime.now().isoformat()

            task_info['stages'][stage]['status'] = status
            if status == 'running':
                task_info['stages'][stage]['started_at'] = now
                task_info['current_stage'] = stage
                task_info['status'] = 'in_progress'
            elif status == 'completed':
                task_info['stages'][stage]['completed_at'] = now
                # 检查是否所有阶段都完成
                all_completed = all(
                    s['status'] == 'completed' for s in task_info['stages'].values()
                )
                if all_completed:
                    task_info['status'] = 'completed'
                    task_info['current_stage'] = 'finished'
            elif status == 'failed':
                task_info['status'] = 'failed'
                task_info['current_stage'] = 'error'

            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_info, f, ensure_ascii=False, indent=2)

def main():
    """CLI主函数"""
    parser = argparse.ArgumentParser(
        description='Athena专利代理CLI工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  patent init '智能机器人控制系统' '一种基于AI的机器人控制系统'
  patent status
  patent status PAT_20241205_001
  patent list
  patent show PAT_20241205_001
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # init命令
    parser_init = subparsers.add_parser('init', help='初始化新任务')
    parser_init.add_argument('title', help='专利标题')
    parser_init.add_argument('--description', '-d', default='', help='专利描述')

    # status命令
    parser_status = subparsers.add_parser('status', help='查看任务状态')
    parser_status.add_argument('task_id', nargs='?', help='任务ID（可选）')

    # list命令
    subparsers.add_parser('list', help='列出所有任务')

    # show命令
    parser_show = subparsers.add_parser('show', help='显示任务详情')
    parser_show.add_argument('task_id', help='任务ID')

    # novelty命令（切片1）
    parser_novelty = subparsers.add_parser('novelty', help='执行新颖性分析（切片1）')
    parser_novelty.add_argument('task_id', help='任务ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = PatentCLI()

    if args.command == 'init':
        cli.init_task(args.title, args.description)

    elif args.command == 'status':
        cli.get_status(args.task_id)

    elif args.command == 'list':
        tasks = cli.list_tasks()
        if tasks:
            logger.info(f"📋 共有 {len(tasks)} 个任务:")
            for task in tasks:
                logger.info(f"  📄 {task['task_id']}: {task['title']} ({task['status']})")
        else:
            logger.info('📭 暂无任务')

    elif args.command == 'show':
        task_info = cli.show_task(args.task_id)
        if task_info:
            print(json.dumps(task_info, ensure_ascii=False, indent=2))
        else:
            logger.info(f"❌ 任务 {args.task_id} 不存在")

    elif args.command == 'novelty':
        cli.execute_novelty_analysis(args.task_id)

if __name__ == '__main__':
    main()