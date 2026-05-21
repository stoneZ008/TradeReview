"""APScheduler 调度器封装

负责每日自选股信号扫描任务。使用文件锁避免 gunicorn 多 worker 重复启动调度器。
"""
import atexit
import os
import tempfile

_scheduler = None
_LOCK_FILE = os.path.join(tempfile.gettempdir(), 'tradereview_scheduler.lock')


def _acquire_lock():
    """简单 PID 锁，确保只有一个进程启动调度器"""
    try:
        if os.path.exists(_LOCK_FILE):
            with open(_LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip() or '0')
            # 检查老进程是否还在
            if old_pid > 0:
                try:
                    os.kill(old_pid, 0)
                    return False  # 老进程仍存活
                except OSError:
                    pass  # 老进程已死，可以接管
        with open(_LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        print(f"[Scheduler] 获取锁失败: {e}")
        return False


def _release_lock():
    try:
        if os.path.exists(_LOCK_FILE):
            with open(_LOCK_FILE, 'r') as f:
                pid = int(f.read().strip() or '0')
            if pid == os.getpid():
                os.remove(_LOCK_FILE)
    except Exception:
        pass


def init_scheduler():
    """初始化并启动调度器。每个交易日 16:00（北京时间）扫描所有用户自选股。"""
    global _scheduler
    if _scheduler is not None:
        return

    if not _acquire_lock():
        print('[Scheduler] 另有进程已启动调度器，跳过')
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from watchlist_scanner import scan_all_users

        _scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        # 周一至周五 16:00 执行（收盘后 1 小时）
        _scheduler.add_job(
            scan_all_users,
            trigger=CronTrigger(day_of_week='mon-fri', hour=16, minute=0),
            id='watchlist_daily_scan',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        _scheduler.start()
        atexit.register(_shutdown)
        print('[Scheduler] 调度器已启动，每个交易日 16:00 扫描自选股信号')
    except Exception as e:
        print(f'[Scheduler] 启动失败: {e}')
        _release_lock()


def _shutdown():
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None
    _release_lock()
