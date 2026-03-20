import time
import functools
from datetime import datetime

from core.settings import settings

# Включение/выключение декораторов через переменную окружения
ENABLE_TIME_DECORATOR = settings.app.enable_time_reports


def time_all_methods(decorator):
    """Декоратор класса: применяет указанный декоратор ко всем методам."""
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and not attr.startswith("__"):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


def async_timed_report():
    def decorator(func):
        if not ENABLE_TIME_DECORATOR:
            return func
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] {func.__name__} | {duration:.4f} сек.")
        return wrapper
    return decorator

def sync_timed_report():
    def decorator(func):
        if not ENABLE_TIME_DECORATOR:
            return func
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] {func.__name__} | {duration:.4f} сек.")
        return wrapper
    return decorator

if __name__ == "__main__":
    @sync_timed_report()
    def heavy_computation():
        print("Выполняю сложные расчеты...")
        time.sleep(1.2)
        return "Расчет окончен"

    res = heavy_computation()
    print(res)
