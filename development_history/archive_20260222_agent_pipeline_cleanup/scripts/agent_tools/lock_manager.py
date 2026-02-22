"""
文件锁管理器 - 工业级多Agent协作系统核心组件

使用 fcntl.flock() 实现跨进程安全的文件锁。
锁状态存储在 docs/.agent_state/locks.json
"""

import fcntl
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class LockManager:
    """管理任务锁的领取、释放和心跳更新"""

    HEARTBEAT_TIMEOUT = 900  # 15分钟无心跳视为超时

    def __init__(self, state_dir: Optional[str] = None):
        """
        初始化锁管理器

        Args:
            state_dir: 状态文件目录，默认为 docs/.agent_state/
        """
        if state_dir is None:
            project_root = Path(__file__).parent.parent.parent
            state_dir = project_root / "docs" / ".agent_state"

        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.locks_file = self.state_dir / "locks.json"
        self.lock_file = self.state_dir / ".locks.lock"

        # 初始化锁文件
        if not self.locks_file.exists():
            self._write_locks({})

    def _get_file_lock(self):
        """获取文件锁用于原子操作"""
        self.lock_file.touch(exist_ok=True)
        fd = open(self.lock_file, "r+")
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd

    def _release_file_lock(self, fd):
        """释放文件锁"""
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()

    def _read_locks(self) -> dict:
        """读取当前锁状态"""
        if not self.locks_file.exists():
            return {}
        with open(self.locks_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_locks(self, locks: dict):
        """写入锁状态"""
        with open(self.locks_file, "w", encoding="utf-8") as f:
            json.dump(locks, f, indent=2, ensure_ascii=False)

    def acquire_lock(
        self, task_id: str, agent_id: str, estimated_minutes: int = 30
    ) -> bool:
        """
        原子性领取任务锁

        Args:
            task_id: 任务ID
            agent_id: Agent标识
            estimated_minutes: 预计完成时间（分钟）

        Returns:
            True 成功领取，False 任务已被锁定
        """
        fd = self._get_file_lock()
        try:
            locks = self._read_locks()

            # 检查是否已被锁定
            if task_id in locks:
                existing = locks[task_id]
                # 检查是否超时
                last_heartbeat = datetime.fromisoformat(existing["last_heartbeat"])
                elapsed = (datetime.now() - last_heartbeat).total_seconds()
                if elapsed < self.HEARTBEAT_TIMEOUT:
                    return False  # 锁仍然有效

            # 创建新锁
            now = datetime.now()
            locks[task_id] = {
                "agent_id": agent_id,
                "locked_at": now.isoformat(),
                "last_heartbeat": now.isoformat(),
                "estimated_completion": (
                    now.isoformat()
                ),  # 简化处理
                "status": "locked",
            }

            self._write_locks(locks)
            return True
        finally:
            self._release_file_lock(fd)

    def release_lock(self, task_id: str, agent_id: str) -> bool:
        """
        释放任务锁

        Args:
            task_id: 任务ID
            agent_id: Agent标识（必须与锁定者匹配）

        Returns:
            True 成功释放，False 无权释放或锁不存在
        """
        fd = self._get_file_lock()
        try:
            locks = self._read_locks()

            if task_id not in locks:
                return False

            if locks[task_id]["agent_id"] != agent_id:
                return False  # 无权释放他人的锁

            del locks[task_id]
            self._write_locks(locks)
            return True
        finally:
            self._release_file_lock(fd)

    def update_heartbeat(
        self, task_id: str, agent_id: str, progress: str = ""
    ) -> bool:
        """
        更新心跳时间

        Args:
            task_id: 任务ID
            agent_id: Agent标识
            progress: 可选的进度说明

        Returns:
            True 成功更新，False 锁不存在或无权更新
        """
        fd = self._get_file_lock()
        try:
            locks = self._read_locks()

            if task_id not in locks:
                return False

            if locks[task_id]["agent_id"] != agent_id:
                return False

            locks[task_id]["last_heartbeat"] = datetime.now().isoformat()
            if progress:
                locks[task_id]["progress"] = progress

            self._write_locks(locks)
            return True
        finally:
            self._release_file_lock(fd)

    def check_stale_locks(self) -> list:
        """
        检测超时的锁

        Returns:
            超时锁的列表 [(task_id, agent_id, elapsed_seconds), ...]
        """
        locks = self._read_locks()
        stale = []

        for task_id, info in locks.items():
            last_heartbeat = datetime.fromisoformat(info["last_heartbeat"])
            elapsed = (datetime.now() - last_heartbeat).total_seconds()
            if elapsed > self.HEARTBEAT_TIMEOUT:
                stale.append((task_id, info["agent_id"], elapsed))

        return stale

    def force_release(self, task_id: str) -> bool:
        """
        强制释放锁（管理Agent专用）

        Args:
            task_id: 任务ID

        Returns:
            True 成功释放，False 锁不存在
        """
        fd = self._get_file_lock()
        try:
            locks = self._read_locks()

            if task_id not in locks:
                return False

            del locks[task_id]
            self._write_locks(locks)
            return True
        finally:
            self._release_file_lock(fd)

    def get_status(self) -> dict:
        """获取所有锁的当前状态"""
        return self._read_locks()


if __name__ == "__main__":
    # 简单测试
    lm = LockManager()
    print("Current locks:", lm.get_status())
