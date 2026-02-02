#!/usr/bin/env python3
"""
将专利数据备份移动到外接硬盘
释放本地存储空间
"""

import logging
import os
import shutil
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/backup_move.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupMover:
    """备份移动器"""

    def __init__(self):
        self.source_dir = Path('/Users/xujian/Athena工作平台/data/patents/backup/20251209')
        # 常见的外接硬盘路径
        self.external_paths = [
            Path('/Volumes'),
            Path('/media'),
            Path('/mnt')
        ]
        self.target_dir = None

    def find_external_drive(self):
        """查找外接硬盘"""
        logger.info("\n🔍 查找外接硬盘...")

        available_drives = []

        # 扫描Volumes目录（macOS）
        volumes_dir = Path('/Volumes')
        if volumes_dir.exists():
            for item in volumes_dir.iterdir():
                if item.is_dir() and item.name not in ['Macintosh HD', 'MacHD', 'Preboot', 'Recovery', 'VM']:
                    # 检查可用空间
                    stat = shutil.disk_usage(str(item))
                    free_gb = stat.free / (1024**3)

                    if free_gb > 100:  # 至少需要100GB空间
                        available_drives.append({
                            'path': item,
                            'name': item.name,
                            'free_gb': free_gb
                        })
                        logger.info(f"  发现外接硬盘: {item.name} (可用空间: {free_gb:.1f}GB)")

        if not available_drives:
            logger.error("\n❌ 未找到合适的外接硬盘")
            logger.info('请确保:')
            logger.info('1. 外接硬盘已连接')
            logger.info('2. 硬盘已格式化为macOS兼容格式')
            logger.info('3. 硬盘有足够的可用空间')
            return None

        # 选择可用空间最大的硬盘
        best_drive = max(available_drives, key=lambda x: x['free_gb'])
        logger.info(f"\n✅ 选择硬盘: {best_drive['name']} (可用空间: {best_drive['free_gb']:.1f}GB)")

        return best_drive['path']

    def calculate_backup_size(self):
        """计算备份大小"""
        if not self.source_dir.exists():
            logger.error(f"源目录不存在: {self.source_dir}")
            return 0

        total_size = 0
        for root, dirs, files in os.walk(str(self.source_dir)):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)

        total_gb = total_size / (1024**3)
        logger.info(f"\n📦 备份大小: {total_gb:.2f}GB")

        return total_size

    def move_backup(self, target_drive):
        """移动备份到外接硬盘"""
        # 创建目标目录
        timestamp = time.strftime('%Y%m%d')
        self.target_dir = target_drive / f"Patent_Backup_{timestamp}"

        logger.info(f"\n🚀 开始移动备份...")
        logger.info(f"源目录: {self.source_dir}")
        logger.info(f"目标目录: {self.target_dir}")

        # 确认移动
        response = input("\n确认移动备份到外接硬盘? (y/n): ")
        if response.lower() != 'y':
            logger.info('移动已取消')
            return False

        # 创建目标目录
        self.target_dir.mkdir(parents=True, exist_ok=True)

        # 开始复制
        start_time = time.time()
        moved_files = 0
        total_size = 0

        logger.info("\n📋 复制文件...")

        for root, dirs, files in os.walk(str(self.source_dir)):
            # 计算相对路径
            rel_path = Path(root).relative_to(self.source_dir)
            target_subdir = self.target_dir / rel_path

            # 创建子目录
            target_subdir.mkdir(parents=True, exist_ok=True)

            # 复制文件
            for file in files:
                source_file = Path(root) / file
                target_file = target_subdir / file

                if source_file.exists():
                    file_size = source_file.stat().st_size

                    # 显示进度
                    moved_files += 1
                    total_size += file_size
                    total_mb = total_size / (1024**2)

                    if moved_files % 10 == 0:
                        logger.info(f"  已复制 {moved_files} 个文件, {total_mb:.1f}MB")

                    # 复制文件
                    shutil.copy2(str(source_file), str(target_file))

        elapsed_time = time.time() - start_time
        total_gb = total_size / (1024**3)

        logger.info(f"\n✅ 复制完成!")
        logger.info(f"  复制文件: {moved_files} 个")
        logger.info(f"  复制大小: {total_gb:.2f}GB")
        logger.info(f"  耗时: {elapsed_time:.1f}秒")

        # 验证
        logger.info("\n🔍 验证备份...")
        if self.verify_backup():
            logger.info('✅ 验证成功!')

            # 询问是否删除原始备份
            delete_response = input("\n是否删除原始备份以释放空间? (y/n): ")
            if delete_response.lower() == 'y':
                self.delete_original_backup()

            return True
        else:
            logger.error('❌ 验证失败!')
            return False

    def verify_backup(self):
        """验证备份完整性"""
        logger.info('  检查文件数量...')

        source_files = 0
        target_files = 0

        for root, dirs, files in os.walk(str(self.source_dir)):
            source_files += len(files)

        for root, dirs, files in os.walk(str(self.target_dir)):
            target_files += len(files)

        logger.info(f"  源文件数: {source_files}")
        logger.info(f"  目标文件数: {target_files}")

        return source_files == target_files

    def delete_original_backup(self):
        """删除原始备份"""
        logger.info("\n🗑️ 删除原始备份...")

        try:
            shutil.rmtree(str(self.source_dir))
            logger.info('✅ 原始备份已删除')

            # 计算释放的空间
            freed_space = self.calculate_backup_size()
            logger.info(f"释放空间: {freed_space:.2f}GB")

        except Exception as e:
            logger.error(f"删除失败: {e}")

    def create_symlink(self):
        """创建符号链接以便访问"""
        if not self.target_dir:
            return

        link_path = Path('/Users/xujian/Athena工作平台/data/patents/backup/external')

        # 删除现有链接
        if link_path.exists():
            if link_path.is_symlink():
                link_path.unlink()
            else:
                logger.warning(f"目标路径存在但不是符号链接: {link_path}")
                return

        # 创建符号链接
        try:
            link_path.symlink_to(self.target_dir)
            logger.info(f"\n🔗 创建符号链接: {link_path} -> {self.target_dir}")
        except Exception as e:
            logger.error(f"创建符号链接失败: {e}")

def main():
    """主函数"""
    mover = BackupMover()

    # 计算备份大小
    backup_size = mover.calculate_backup_size()
    if backup_size == 0:
        logger.error('没有找到需要备份的文件')
        return

    # 查找外接硬盘
    external_drive = mover.find_external_drive()
    if not external_drive:
        return

    # 移动备份
    if mover.move_backup(external_drive):
        # 创建符号链接
        mover.create_symlink()

        logger.info("\n✅ 备份移动完成!")
        logger.info('您可以通过以下方式访问备份:')
        logger.info('1. 直接访问外接硬盘')
        logger.info('2. 通过符号链接: /Users/xujian/Athena工作平台/data/patents/backup/external')

if __name__ == '__main__':
    main()