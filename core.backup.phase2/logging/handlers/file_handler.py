"""
文件轮转日志处理器
Rotating File Log Handler

支持按大小和时间自动轮转的日志文件处理器
"""
import logging
import os
import gzip
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler as BaseRotatingFileHandler


class RotatingFileHandler(BaseRotatingFileHandler):
    """增强的文件轮转处理器

    在标准RotatingFileHandler基础上增加：
    - 自动创建目录
    - 压缩旧日志文件
    - 基于时间的轮转
    - 清理过期日志
    """

    def __init__(
        self,
        filename: str,
        maxBytes: int = 10 * 1024 * 1024,  # 10MB
        backupCount: int = 5,
        encoding: Optional[str] = "utf-8",
        compress: bool = True,
        max_age_days: Optional[int] = None
    ):
        """初始化文件轮转处理器

        Args:
            filename: 日志文件路径
            maxBytes: 单个文件最大大小（字节）
            backupCount: 保留的备份文件数量
            encoding: 文件编码
            compress: 是否压缩旧日志（gzip）
            max_age_days: 日志最大保留天数（None表示不删除）
        """
        # 确保目录存在
        log_dir = Path(filename).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 初始化父类
        super().__init__(
            filename=filename,
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding=encoding
        )

        self.compress = compress
        self.max_age_days = max_age_days

    def doRollover(self) -> None:
        """执行日志轮转

        重写父类方法，增加压缩和清理功能
        """
        # 先执行父类轮转
        super().doRollover()

        # 压缩旧日志
        if self.compress:
            self._compress_old_logs()

        # 清理过期日志
        if self.max_age_days is not None:
            self._clean_old_logs()

    def _compress_old_logs(self) -> None:
        """压缩旧日志文件"""
        base_path = Path(self.baseFilename)
        log_dir = base_path.parent
        base_name = base_path.name

        # 查找所有备份文件
        for i in range(1, self.backupCount + 1):
            backup_file = log_dir / f"{base_name}.{i}"

            # 如果文件存在且未压缩
            if backup_file.exists() and not backup_file.suffix == ".gz":
                try:
                    # 压缩文件
                    compressed_file = backup_file.with_suffix(f"{backup_file.suffix}.gz")

                    with open(backup_file, "rb") as f_in:
                        with gzip.open(compressed_file, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # 删除原文件
                    backup_file.unlink()

                except Exception as e:
                    # 压缩失败不影响日志轮转
                    print(f"Failed to compress {backup_file}: {e}")

    def _clean_old_logs(self) -> None:
        """清理过期日志文件"""
        base_path = Path(self.baseFilename)
        log_dir = base_path.parent
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

        # 查找所有相关日志文件
        for file_path in log_dir.glob(f"{base_path.name}*"):
            try:
                # 获取文件修改时间
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                # 如果文件过期，删除
                if mtime < cutoff_date:
                    file_path.unlink()

            except Exception as e:
                # 清理失败不影响日志轮转
                print(f"Failed to clean {file_path}: {e}")


class TimeBasedRotatingFileHandler(logging.Handler):
    """基于时间的轮转日志处理器

    按时间间隔轮转日志文件
    """

    def __init__(
        self,
        filename: str,
        when: str = "midnight",  # S, M, H, D, midnight
        interval: int = 1,
        backupCount: int = 7,
        encoding: Optional[str] = "utf-8",
        compress: bool = True
    ):
        """初始化时间轮转处理器

        Args:
            filename: 日志文件路径
            when: 轮转时机（S=秒, M=分, H=时, D=天, midnight=每天午夜）
            interval: 间隔数量
            backupCount: 保留的备份文件数量
            encoding: 文件编码
            compress: 是否压缩旧日志
        """
        super().__init__()

        self.filename = filename
        self.when = when
        self.interval = interval
        self.backupCount = backupCount
        self.encoding = encoding
        self.compress = compress

        # 确保目录存在
        log_dir = Path(filename).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 打开当前日志文件
        self.stream = open(filename, "a", encoding=encoding)

        # 计算下次轮转时间
        self._compute_rollover_time()

    def _compute_rollover_time(self) -> None:
        """计算下次轮转时间"""
        now = datetime.now()

        if self.when == "S":
            self.rollover_time = now + timedelta(seconds=self.interval)
        elif self.when == "M":
            self.rollover_time = now + timedelta(minutes=self.interval)
        elif self.when == "H":
            self.rollover_time = now + timedelta(hours=self.interval)
        elif self.when == "D":
            self.rollover_time = now + timedelta(days=self.interval)
        elif self.when == "midnight":
            # 下一个午夜
            self.rollover_time = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            # 默认：每天
            self.rollover_time = now + timedelta(days=1)

    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录"""
        try:
            # 检查是否需要轮转
            if datetime.now() >= self.rollover_time:
                self.doRollover()

            # 写入日志
            msg = self.format(record)
            self.stream.write(msg + "\n")
            self.stream.flush()

        except Exception:
            self.handleError(record)

    def doRollover(self) -> None:
        """执行日志轮转"""
        # 关闭当前文件
        self.stream.close()

        # 重命名当前文件
        base_path = Path(self.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = base_path.parent / f"{base_path.name}.{timestamp}"

        # 移动文件
        if base_path.exists():
            base_path.rename(backup_file)

            # 压缩
            if self.compress:
                self._compress_file(backup_file)

        # 清理旧日志
        self._clean_old_logs()

        # 打开新文件
        self.stream = open(self.filename, "a", encoding=self.encoding)

        # 重新计算轮转时间
        self._compute_rollover_time()

    def _compress_file(self, file_path: Path) -> None:
        """压缩文件"""
        try:
            compressed_file = file_path.with_suffix(f"{file_path.suffix}.gz")

            with open(file_path, "rb") as f_in:
                with gzip.open(compressed_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 删除原文件
            file_path.unlink()

        except Exception as e:
            print(f"Failed to compress {file_path}: {e}")

    def _clean_old_logs(self) -> None:
        """清理旧日志文件"""
        base_path = Path(self.filename)
        log_dir = base_path.parent

        # 获取所有备份文件
        backup_files = sorted(
            log_dir.glob(f"{base_path.name}.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # 删除超过保留数量的文件
        for old_file in backup_files[self.backupCount:]:
            try:
                old_file.unlink()
            except Exception as e:
                print(f"Failed to delete {old_file}: {e}")

    def close(self) -> None:
        """关闭处理器"""
        self.stream.close()
        super().close()
