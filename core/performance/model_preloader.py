from __future__ import annotations
"""
模型预加载策略 - 启动时加载常用模型
用于减少首次调用延迟,提升响应速度
"""

import json
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any


class ModelPreloader:
    """模型预加载管理器"""

    def __init__(self, preload_config_path: str | None = None, max_workers: int = 3):
        """
        初始化预加载器

        Args:
            preload_config_path: 预加载配置文件路径
            max_workers: 最大并发加载线程数
        """
        self.config_path = (
            Path(preload_config_path)
            if preload_config_path
            else Path(__file__).parent.parent.parent / "config" / "model_preload.json"
        )

        self.preload_dir = Path(__file__).parent.parent.parent / "models" / "preloaded"
        self.preload_dir.mkdir(parents=True, exist_ok=True)

        self.max_workers = max_workers
        self.loaded_models: dict[str, dict[str, Any]] = {}
        self.preload_tasks: list[threading.Thread] = []
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # 加载状态
        self.load_status = {
            "loading": False,
            "completed": False,
            "failed": [],
            "success": [],
            "start_time": None,
            "end_time": None,
        }

        # 加载配置
        self.config = self._load_config()

        # 预定义的常用模型
        self.common_models = {
            "text_embedding": {
                "name": "BGE文本嵌入模型",
                "type": "embedding",
                "priority": "high",
                "load_script": "python3 -c \"from sentence_transformers import SentenceTransformer; model = SentenceTransformer('BAAI/bge-base-zh')\"",
                "memory_estimate": "1.5GB",
                "load_time_estimate": 10,
            },
            "chat_gpt": {
                "name": "对话生成模型",
                "type": "generation",
                "priority": "high",
                "load_script": "echo 'Simulating ChatGPT model loading...'",
                "memory_estimate": "4GB",
                "load_time_estimate": 15,
            },
            "patent_classifier": {
                "name": "专利分类模型",
                "type": "classification",
                "priority": "medium",
                "load_script": "echo 'Simulating patent classifier loading...'",
                "memory_estimate": "800MB",
                "load_time_estimate": 5,
            },
            "bge_reranker": {
                "name": "BGE重排序模型",
                "type": "reranking",
                "priority": "medium",
                "load_script": "echo 'Simulating BGE reranker loading...'",
                "memory_estimate": "2GB",
                "load_time_estimate": 8,
            },
        }

    def _load_config(self) -> dict:
        """加载预加载配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding="utf-8") as f:
                    config = json.load(f)
                    print(f"加载预加载配置: {self.config_path}")
                    return config
            else:
                # 创建默认配置
                default_config = {
                    "enabled": True,
                    "preload_on_startup": True,
                    "models": list(self.common_models.keys()),
                    "custom_models": {},
                    "preload_strategy": "parallel",  # parallel, sequential, priority
                    "max_concurrent_loads": 3,
                    "timeout_seconds": 300,
                    "retry_failed_loads": True,
                    "cache_preloaded_models": True,
                }
                self._save_config(default_config)
                return default_config
        except Exception as e:
            print(f"加载预加载配置失败: {e}")
            return {}

    def _save_config(self, config: dict) -> None:
        """保存预加载配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存预加载配置失败: {e}")

    def start_preload(self) -> None:
        """开始预加载"""
        if not self.config.get("enabled", True):
            print("预加载功能已禁用")
            return

        if self.load_status["loading"]:
            print("预加载正在进行中...")
            return

        self.load_status.update(
            {
                "loading": True,
                "completed": False,
                "failed": [],
                "success": [],
                "start_time": time.time(),
            }
        )

        print("🚀 开始预加载模型...")

        if self.config.get("preload_strategy", "parallel") == "parallel":
            self._preload_parallel()
        elif self.config.get("preload_strategy") == "sequential":
            self._preload_sequential()
        else:
            self._preload_priority()

    def _preload_parallel(self) -> None:
        """并行预加载"""
        models_to_load = self.config.get("models", list(self.common_models.keys()))

        def load_model_task(model_key: str) -> Any | None:
            try:
                self._load_single_model(model_key)
            except Exception as e:
                print(f"加载模型 {model_key} 失败: {e}")
                self.load_status["failed"].append(model_key)

        # 创建并启动加载线程
        for model_key in models_to_load:
            if model_key in self.common_models:
                thread = threading.Thread(target=load_model_task, args=(model_key,))
                thread.start()
                self.preload_tasks.append(thread)

        # 等待所有线程完成
        for thread in self.preload_tasks:
            thread.join(timeout=self.config.get("timeout_seconds", 300))

        self._finalize_preload()

    def _preload_sequential(self) -> None:
        """顺序预加载"""
        models_to_load = self.config.get("models", list(self.common_models.keys()))

        for model_key in models_to_load:
            if model_key in self.common_models:
                try:
                    self._load_single_model(model_key)
                except Exception as e:
                    print(f"加载模型 {model_key} 失败: {e}")
                    self.load_status["failed"].append(model_key)

        self._finalize_preload()

    def _preload_priority(self) -> None:
        """按优先级预加载"""
        models_to_load = self.config.get("models", list(self.common_models.keys()))

        # 按优先级排序
        sorted_models = sorted(
            [model for model in models_to_load if model in self.common_models],
            key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(
                self.common_models[x].get("priority", "low"), 1
            ),
            reverse=True,
        )

        # 高优先级先并行加载
        high_priority_models = [
            m for m in sorted_models if self.common_models[m].get("priority") == "high"
        ]

        if high_priority_models:
            self._load_models_batch(high_priority_models)

        # 中低优先级顺序加载
        remaining_models = [
            m for m in sorted_models if self.common_models[m].get("priority") != "high"
        ]

        for model_key in remaining_models:
            try:
                self._load_single_model(model_key)
            except Exception as e:
                print(f"加载模型 {model_key} 失败: {e}")
                self.load_status["failed"].append(model_key)

        self._finalize_preload()

    def _load_models_batch(self, model_keys: list[str]) -> None:
        """批量加载模型"""

        def load_model_task(model_key: str) -> Any | None:
            try:
                self._load_single_model(model_key)
            except Exception as e:
                print(f"批量加载模型 {model_key} 失败: {e}")
                self.load_status["failed"].append(model_key)

        threads = []
        for model_key in model_keys:
            thread = threading.Thread(target=load_model_task, args=(model_key,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join(timeout=self.config.get("timeout_seconds", 300))

    def _load_single_model(self, model_key: str) -> None:
        """加载单个模型"""
        if model_key in self.loaded_models:
            print(f"模型 {model_key} 已加载")
            return

        model_info = self.common_models.get(model_key, {})
        model_name = model_info.get("name", model_key)

        print(f"🔄 正在加载模型: {model_name}")
        start_time = time.time()

        try:
            # 执行加载脚本
            load_script = model_info.get("load_script", f"echo 'Loading {model_key}...'")

            # 这里模拟模型加载过程
            # 实际使用时,替换为真实的模型加载代码
            process = subprocess.Popen(
                load_script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # 模拟加载时间
            estimated_time = model_info.get("load_time_estimate", 5)
            time.sleep(estimated_time / 10)  # 快速模拟

            _stdout, stderr = process.communicate(timeout=self.config.get("timeout_seconds", 300))

            if process.returncode == 0:
                load_time = time.time() - start_time

                # 记录加载信息
                load_info = {
                    "model_key": model_key,
                    "model_name": model_name,
                    "model_type": model_info.get("type", "unknown"),
                    "load_time": load_time,
                    "load_timestamp": datetime.now().isoformat(),
                    "memory_estimate": model_info.get("memory_estimate", "unknown"),
                    "load_script": load_script,
                    "status": "loaded",
                }

                self.loaded_models[model_key] = load_info
                self.load_status["success"].append(model_key)

                print(f"✅ 模型 {model_name} 加载完成 ({load_time:.2f}s)")

                # 保存加载信息
                self._save_load_info(model_key, load_info)

            else:
                raise Exception(f"加载失败: {stderr}")

        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("模型加载超时") from None
        except Exception as e:
            print(f"❌ 模型 {model_name} 加载失败: {e}")
            raise

    def _save_load_info(self, model_key: str, load_info: dict) -> None:
        """保存模型加载信息"""
        try:
            info_file = self.preload_dir / f"{model_key}_load_info.json"
            with open(info_file, "w", encoding="utf-8") as f:
                json.dump(load_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存加载信息失败 {model_key}: {e}")

    def _finalize_preload(self) -> None:
        """完成预加载"""
        self.load_status.update({"loading": False, "completed": True, "end_time": time.time()})

        total_time = self.load_status["end_time"] - self.load_status["start_time"]
        success_count = len(self.load_status["success"])
        failed_count = len(self.load_status["failed"])

        print("\\n🎉 预加载完成!")
        print(f"   成功: {success_count} 个模型")
        print(f"   失败: {failed_count} 个模型")
        print(f"   总用时: {total_time:.2f} 秒")

        if self.load_status["failed"]:
            print(f"   失败模型: {', '.join(self.load_status['failed'])}")

    def is_model_loaded(self, model_key: str) -> bool:
        """检查模型是否已加载"""
        return model_key in self.loaded_models

    def get_model_info(self, model_key: str) -> dict | None:
        """获取模型信息"""
        return self.loaded_models.get(model_key)

    def get_all_loaded_models(self) -> dict[str, dict]:
        """获取所有已加载的模型信息"""
        return self.loaded_models.copy()

    def get_load_status(self) -> dict:
        """获取预加载状态"""
        return self.load_status.copy()

    def reload_model(self, model_key: str) -> bool:
        """重新加载模型"""
        try:
            if model_key in self.loaded_models:
                del self.loaded_models[model_key]

            self._load_single_model(model_key)
            return True
        except Exception as e:
            print(f"重新加载模型 {model_key} 失败: {e}")
            return False

    def unload_model(self, model_key: str) -> bool:
        """卸载模型"""
        if model_key in self.loaded_models:
            del self.loaded_models[model_key]

            # 删除加载信息文件
            info_file = self.preload_dir / f"{model_key}_load_info.json"
            info_file.unlink(missing_ok=True)

            print(f"模型 {model_key} 已卸载")
            return True
        return False

    def get_memory_usage(self) -> dict:
        """获取内存使用情况"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            total_memory = 0
            for model_info in self.loaded_models.values():
                memory_str = model_info.get("memory_estimate", "0GB")
                if memory_str.endswith("GB"):
                    total_memory += float(memory_str[:-2])
                elif memory_str.endswith("MB"):
                    total_memory += float(memory_str[:-2]) / 1024

            return {
                "process_memory_mb": memory_info.rss / 1024 / 1024,
                "estimated_models_memory_gb": total_memory,
                "loaded_models_count": len(self.loaded_models),
                "available_memory_gb": psutil.virtual_memory().available / 1024**3,
            }
        except ImportError:
            return {"error": "psutil not available"}

    def cleanup(self) -> None:
        """清理资源"""
        # 关闭线程池
        self.executor.shutdown(wait=True)

        # 清理预加载任务
        for thread in self.preload_tasks:
            if thread.is_alive():
                thread.join(timeout=1)


# 全局预加载器实例
_global_preloader: ModelPreloader | None = None


def get_preloader() -> ModelPreloader:
    """获取全局预加载器实例"""
    global _global_preloader
    if _global_preloader is None:
        _global_preloader = ModelPreloader()
    return _global_preloader


# 启动时自动预加载
def auto_preload_on_startup() -> Any:
    """启动时自动预加载"""
    preloader = get_preloader()
    if preloader.config.get("preload_on_startup", True):
        print("🚀 启动时自动预加载模型...")
        preloader.start_preload()


# 示例使用
if __name__ == "__main__":
    # 创建预加载器
    preloader = ModelPreloader()

    # 开始预加载
    preloader.start_preload()

    # 等待预加载完成
    while not preloader.load_status["completed"]:
        time.sleep(1)

    # 查看加载状态
    status = preloader.get_load_status()
    print(f"\\n预加载状态: {status}")

    # 查看已加载模型
    loaded_models = preloader.get_all_loaded_models()
    print(f"\\n已加载模型: {list(loaded_models.keys())}")

    # 查看内存使用
    memory_usage = preloader.get_memory_usage()
    print(f"\\n内存使用: {memory_usage}")
