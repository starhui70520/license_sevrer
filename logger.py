# logger.py
import logging
import sys
import asyncio
from typing import Optional


class AsyncLogger:
    """异步安全的全局日志器"""
    def __init__(self):
        # 基础同步 logger
        self._logger = logging.getLogger("LicenseServer")
        self._logger.setLevel(logging.INFO)
        if not self._logger.hasHandlers():
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            self._logger.addHandler(handler)

        # 异步队列 & 工作任务
        self._queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        self._worker: Optional[asyncio.Task] = None

    async def start(self):
        """启动日志后台任务（仅调用一次）"""
        if self._worker is None:
            self._worker = asyncio.create_task(self._worker_loop())

    async def stop(self):
        """停止日志任务并等待写入完成"""
        if self._worker:
            await self._queue.join()
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
            self._worker = None

    async def flush(self):
        """等待日志队列清空"""
        await self._queue.join()

    async def _worker_loop(self):
        """日志后台任务"""
        while True:
            level, msg = await self._queue.get()
            try:
                getattr(self._logger, level)(msg)
            finally:
                self._queue.task_done()

    # --- 异步日志接口 ---
    async def log(self, level: str, msg: str):
        await self._queue.put((level, msg))

    async def pDebug(self, msg: str): await self.log("debug", msg)
    async def pInfo(self, msg: str): await self.log("info", msg)
    async def pWarning(self, msg: str): await self.log("warning", msg)
    async def pError(self, msg: str): await self.log("error", msg)
    async def pCritical(self, msg: str): await self.log("critical", msg)


# ---------------- 模块级单例封装 ----------------
_logger_instance: Optional[AsyncLogger] = None

async def get_logger() -> AsyncLogger:
    """异步安全地获取全局日志实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AsyncLogger()
        await _logger_instance.start()
    return _logger_instance

# 可选：提供一个惰性代理，方便同步模块 import 使用
class _LazyLoggerProxy:
    def __getattr__(self, name):
        raise RuntimeError("Logger 未初始化，请在 async 上下文中调用 get_logger()")

logger = _LazyLoggerProxy()
