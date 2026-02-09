#!/usr/bin/env python3
"""
Agent CLI - 多Agent协作系统命令行工具

用法:
    python scripts/agent_tools/agent_cli.py status
    python scripts/agent_tools/agent_cli.py lock <task_id> <agent_id>
    python scripts/agent_tools/agent_cli.py unlock <task_id> <agent_id>
    python scripts/agent_tools/agent_cli.py heartbeat <task_id> <agent_id> [progress]
    python scripts/agent_tools/agent_cli.py tasks
    python scripts/agent_tools/agent_cli.py add-task <id> <title> <description>
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.agent_tools.lock_manager import LockManager
from scripts.agent_tools.task_queue import TaskQueue


def cmd_status(args):
    """显示当前锁状态"""
    lm = LockManager()
    locks = lm.get_status()

    print("=" * 60)
    print("🔒 当前任务锁状态")
    print("=" * 60)

    if not locks:
        print("  (无活跃锁)")
    else:
        for task_id, info in locks.items():
            last_hb = datetime.fromisoformat(info["last_heartbeat"])
            elapsed = (datetime.now() - last_hb).total_seconds()
            status = "⚠️ 超时" if elapsed > 900 else "✅ 活跃"

            print(f"\n  任务: {task_id}")
            print(f"  Agent: {info['agent_id']}")
            print(f"  锁定时间: {info['locked_at']}")
            print(f"  最后心跳: {info['last_heartbeat']} ({status})")
            if "progress" in info:
                print(f"  进度: {info['progress']}")

    # 检查超时锁
    stale = lm.check_stale_locks()
    if stale:
        print("\n⚠️ 发现超时锁:")
        for task_id, agent_id, elapsed in stale:
            print(f"  - {task_id} (Agent: {agent_id}, 超时: {elapsed/60:.1f}分钟)")

    print()


def cmd_tasks(args):
    """显示任务队列"""
    tq = TaskQueue()
    data = tq.get_all_tasks()

    print("=" * 60)
    print("📋 任务队列")
    print("=" * 60)

    print("\n待执行/进行中:")
    if not data["tasks"]:
        print("  (无任务)")
    else:
        for task in data["tasks"]:
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
            }.get(task["status"], "❓")
            print(f"  {status_icon} [{task['priority']}] {task['id']}: {task['title']}")
            if task.get("assigned_to"):
                print(f"      分配给: {task['assigned_to']}")

    print("\n已完成:")
    if not data["completed"]:
        print("  (无)")
    else:
        for task in data["completed"][-5:]:  # 只显示最近5个
            status_icon = "✅" if task["status"] == "completed" else "❌"
            print(f"  {status_icon} {task['id']}: {task['title']}")

    print()


def cmd_lock(args):
    """领取任务锁"""
    lm = LockManager()
    success = lm.acquire_lock(args.task_id, args.agent_id)

    if success:
        print(f"✅ 成功锁定任务: {args.task_id}")
        print(f"   Agent: {args.agent_id}")
    else:
        print(f"❌ 无法锁定任务: {args.task_id} (可能已被其他Agent锁定)")
        sys.exit(1)


def cmd_unlock(args):
    """释放任务锁"""
    lm = LockManager()
    success = lm.release_lock(args.task_id, args.agent_id)

    if success:
        print(f"✅ 成功释放任务锁: {args.task_id}")
    else:
        print(f"❌ 无法释放锁: {args.task_id} (锁不存在或无权释放)")
        sys.exit(1)


def cmd_heartbeat(args):
    """更新心跳"""
    lm = LockManager()
    progress = args.progress if hasattr(args, "progress") else ""
    success = lm.update_heartbeat(args.task_id, args.agent_id, progress)

    if success:
        print(f"💓 心跳已更新: {args.task_id}")
        if progress:
            print(f"   进度: {progress}")
    else:
        print(f"❌ 无法更新心跳: {args.task_id}")
        sys.exit(1)


def cmd_add_task(args):
    """添加新任务"""
    tq = TaskQueue()
    try:
        task = tq.add_task(
            task_id=args.task_id,
            title=args.title,
            description=args.description,
            priority=args.priority,
        )
        print(f"✅ 任务已创建: {task['id']}")
        print(f"   标题: {task['title']}")
        print(f"   优先级: {task['priority']}")
    except ValueError as e:
        print(f"❌ 创建失败: {e}")
        sys.exit(1)


def cmd_force_unlock(args):
    """强制释放锁（管理Agent专用）"""
    lm = LockManager()
    success = lm.force_release(args.task_id)

    if success:
        print(f"⚠️ 已强制释放锁: {args.task_id}")
    else:
        print(f"❌ 锁不存在: {args.task_id}")
        sys.exit(1)


def cmd_force_complete(args):
    """强制标记任务完成（管理Agent专用，绕过锁检查）"""
    tq = TaskQueue()
    data = tq._read_tasks()

    # 在任务列表中查找
    for i, task in enumerate(data["tasks"]):
        if task["id"] == args.task_id:
            task["status"] = "completed"
            task["result"] = args.result if hasattr(args, "result") else "手动标记完成"
            task["completed_at"] = datetime.now().isoformat()
            task["completed_by"] = "manager (force)"
            data["completed"].append(data["tasks"].pop(i))
            tq._write_tasks(data)
            print(f"✅ 已强制标记任务完成: {args.task_id}")
            return

    print(f"❌ 任务不存在: {args.task_id}")
    sys.exit(1)


def cmd_start(args):
    """开始任务（验证 + 锁定 + 显示详情）"""
    tq = TaskQueue()
    lm = LockManager()
    
    # 1. 验证任务存在
    task = tq.get_task(args.task_id)
    if not task:
        print(f"❌ 任务不存在: {args.task_id}")
        print("运行 'agent_cli.py tasks' 查看可用任务")
        sys.exit(1)
    
    if task.get("status") == "completed":
        print(f"❌ 任务已完成: {args.task_id}")
        sys.exit(1)
    
    # 2. 检查是否已被锁定
    locks = lm.get_status()
    if args.task_id in locks:
        lock_info = locks[args.task_id]
        print(f"❌ 任务已被锁定")
        print(f"   锁定者: {lock_info['agent_id']}")
        print(f"   锁定时间: {lock_info['locked_at']}")
        sys.exit(1)
    
    # 3. 锁定任务
    success = lm.acquire_lock(args.task_id, args.agent_id)
    if not success:
        print(f"❌ 无法锁定任务: {args.task_id}")
        sys.exit(1)
    
    # 4. 更新任务状态
    tq.assign_task(args.task_id, args.agent_id)
    
    # 5. 显示任务详情
    print("=" * 60)
    print(f"✅ 任务开始: {args.task_id}")
    print("=" * 60)
    print(f"Agent: {args.agent_id}")
    print(f"标题: {task.get('title', 'N/A')}")
    print(f"描述: {task.get('description', 'N/A')}")
    print()
    print("📋 下一步:")
    print("  1. 阅读 docs/current_task.md 了解详情")
    print("  2. 长任务使用 tmux")
    print("  3. 每 10 分钟更新心跳:")
    print(f"     agent_cli.py heartbeat {args.task_id} {args.agent_id} \"进度\"")
    print("  4. 完成后运行:")
    print(f"     agent_cli.py finish {args.task_id} {args.agent_id} \"结果\"")


def cmd_finish(args):
    """完成任务（释放锁 + 标记完成 + 提示更新文档）"""
    tq = TaskQueue()
    lm = LockManager()
    
    # 1. 检查锁
    locks = lm.get_status()
    if args.task_id not in locks:
        print(f"⚠️ 任务未被锁定: {args.task_id}")
        print("继续标记完成...")
    elif locks[args.task_id]["agent_id"] != args.agent_id:
        print(f"❌ 任务被其他 Agent 锁定: {locks[args.task_id]['agent_id']}")
        sys.exit(1)
    else:
        # 释放锁
        lm.release_lock(args.task_id, args.agent_id)
    
    # 2. 标记任务完成
    data = tq._read_tasks()
    for i, task in enumerate(data["tasks"]):
        if task["id"] == args.task_id:
            task["status"] = "completed"
            task["result"] = args.result
            task["completed_at"] = datetime.now().isoformat()
            task["completed_by"] = args.agent_id
            data["completed"].append(data["tasks"].pop(i))
            tq._write_tasks(data)
            break
    
    # 3. 提示更新文档
    print("=" * 60)
    print(f"✅ 任务完成: {args.task_id}")
    print("=" * 60)
    print(f"结果: {args.result}")
    print()
    print("📝 请立即更新以下文档:")
    print("  1. development_record.md - 添加修改记录")
    print("  2. lang.md - 更新进度状态")
    print()
    print("模板 (development_record.md):")
    print(f"# <Antigravity {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}>")
    print("## 修改目的")
    print(f"[描述 {args.task_id} 的目的]")
    print("## 修改内容摘要")
    print("[列出具体修改]")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent 协作系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # status
    subparsers.add_parser("status", help="显示当前锁状态")

    # tasks
    subparsers.add_parser("tasks", help="显示任务队列")

    # lock
    p_lock = subparsers.add_parser("lock", help="领取任务锁")
    p_lock.add_argument("task_id", help="任务ID")
    p_lock.add_argument("agent_id", help="Agent标识")

    # unlock
    p_unlock = subparsers.add_parser("unlock", help="释放任务锁")
    p_unlock.add_argument("task_id", help="任务ID")
    p_unlock.add_argument("agent_id", help="Agent标识")

    # heartbeat
    p_hb = subparsers.add_parser("heartbeat", help="更新心跳")
    p_hb.add_argument("task_id", help="任务ID")
    p_hb.add_argument("agent_id", help="Agent标识")
    p_hb.add_argument("progress", nargs="?", default="", help="进度说明")

    # add-task
    p_add = subparsers.add_parser("add-task", help="添加新任务")
    p_add.add_argument("task_id", help="任务ID")
    p_add.add_argument("title", help="任务标题")
    p_add.add_argument("description", help="任务描述")
    p_add.add_argument("-p", "--priority", type=int, default=1, help="优先级")

    # force-unlock
    p_force = subparsers.add_parser("force-unlock", help="强制释放锁（管理Agent）")
    p_force.add_argument("task_id", help="任务ID")

    # force-complete
    p_complete = subparsers.add_parser("force-complete", help="强制标记任务完成（管理Agent）")
    p_complete.add_argument("task_id", help="任务ID")
    p_complete.add_argument("--result", default="手动标记完成", help="完成结果说明")

    # start (推荐)
    p_start = subparsers.add_parser("start", help="开始任务（推荐）")
    p_start.add_argument("task_id", help="任务ID")
    p_start.add_argument("agent_id", help="Agent标识")

    # finish (推荐)
    p_finish = subparsers.add_parser("finish", help="完成任务（推荐）")
    p_finish.add_argument("task_id", help="任务ID")
    p_finish.add_argument("agent_id", help="Agent标识")
    p_finish.add_argument("result", help="完成结果说明")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "tasks":
        cmd_tasks(args)
    elif args.command == "lock":
        cmd_lock(args)
    elif args.command == "unlock":
        cmd_unlock(args)
    elif args.command == "heartbeat":
        cmd_heartbeat(args)
    elif args.command == "add-task":
        cmd_add_task(args)
    elif args.command == "force-unlock":
        cmd_force_unlock(args)
    elif args.command == "force-complete":
        cmd_force_complete(args)
    elif args.command == "start":
        cmd_start(args)
    elif args.command == "finish":
        cmd_finish(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
