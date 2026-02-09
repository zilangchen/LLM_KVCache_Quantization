"""
任务队列管理器 - 工业级多Agent协作系统

管理任务的添加、领取、完成状态。
任务存储在 docs/.agent_state/tasks.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskQueue:
    """任务队列管理器"""

    def __init__(self, state_dir: Optional[str] = None):
        """
        初始化任务队列

        Args:
            state_dir: 状态文件目录，默认为 docs/.agent_state/
        """
        if state_dir is None:
            project_root = Path(__file__).parent.parent.parent
            state_dir = project_root / "docs" / ".agent_state"

        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.state_dir / "tasks.json"

        if not self.tasks_file.exists():
            self._write_tasks({"tasks": [], "completed": []})

    def _read_tasks(self) -> dict:
        """读取任务数据"""
        if not self.tasks_file.exists():
            return {"tasks": [], "completed": []}
        with open(self.tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_tasks(self, data: dict):
        """写入任务数据"""
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_task(
        self,
        task_id: str,
        title: str,
        description: str,
        priority: int = 1,
        estimated_minutes: int = 30,
    ) -> dict:
        """
        添加新任务到队列

        Args:
            task_id: 任务唯一ID
            title: 任务标题
            description: 任务描述
            priority: 优先级 (0=最高)
            estimated_minutes: 预计完成时间

        Returns:
            创建的任务对象
        """
        data = self._read_tasks()

        # 检查是否已存在
        for task in data["tasks"]:
            if task["id"] == task_id:
                raise ValueError(f"Task {task_id} already exists")

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "estimated_minutes": estimated_minutes,
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "assigned_to": None,
            "result": None,
        }

        data["tasks"].append(task)
        # 按优先级排序
        data["tasks"].sort(key=lambda x: x["priority"])
        self._write_tasks(data)

        return task

    def get_next_task(self) -> Optional[dict]:
        """
        获取下一个待执行的任务

        Returns:
            待执行任务对象，无任务返回None
        """
        data = self._read_tasks()

        for task in data["tasks"]:
            if task["status"] == TaskStatus.PENDING.value:
                return task

        return None

    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """
        分配任务给Agent

        Args:
            task_id: 任务ID
            agent_id: Agent标识

        Returns:
            True 成功分配
        """
        data = self._read_tasks()

        for task in data["tasks"]:
            if task["id"] == task_id:
                if task["status"] != TaskStatus.PENDING.value:
                    return False
                task["status"] = TaskStatus.IN_PROGRESS.value
                task["assigned_to"] = agent_id
                task["started_at"] = datetime.now().isoformat()
                self._write_tasks(data)
                return True

        return False

    def complete_task(
        self, task_id: str, agent_id: str, result: str, success: bool = True
    ) -> bool:
        """
        标记任务完成

        Args:
            task_id: 任务ID
            agent_id: Agent标识
            result: 执行结果摘要
            success: 是否成功

        Returns:
            True 成功标记
        """
        data = self._read_tasks()

        for i, task in enumerate(data["tasks"]):
            if task["id"] == task_id:
                if task["assigned_to"] != agent_id:
                    return False

                task["status"] = (
                    TaskStatus.COMPLETED.value
                    if success
                    else TaskStatus.FAILED.value
                )
                task["result"] = result
                task["completed_at"] = datetime.now().isoformat()

                # 移动到已完成列表
                data["completed"].append(data["tasks"].pop(i))
                self._write_tasks(data)
                return True

        return False

    def get_all_tasks(self) -> dict:
        """获取所有任务"""
        return self._read_tasks()

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取指定任务"""
        data = self._read_tasks()

        for task in data["tasks"] + data["completed"]:
            if task["id"] == task_id:
                return task

        return None

    def update_task_file(self, task_id: str, file_path: str):
        """
        关联任务详情文件

        Args:
            task_id: 任务ID
            file_path: 任务详情文件路径
        """
        data = self._read_tasks()

        for task in data["tasks"]:
            if task["id"] == task_id:
                task["detail_file"] = file_path
                self._write_tasks(data)
                return

    def clear_completed(self):
        """清空已完成任务"""
        data = self._read_tasks()
        data["completed"] = []
        self._write_tasks(data)


if __name__ == "__main__":
    # 简单测试
    tq = TaskQueue()
    print("Tasks:", json.dumps(tq.get_all_tasks(), indent=2))
