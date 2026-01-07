# Python 单例模式实现
单例模式是一种常用的设计模式，确保一个类只有一个实例，并提供一个全局访问点。以下是几种在 Python 中实现单例模式的方法：

## 方法1：使用模块
Python 的模块本身就是天然的单例模式，因为模块在第一次导入时会生成 `.pyc` 文件，第二次导入时直接加载 `.pyc` 文件而不会再次执行模块代码。

```python
# singleton.py
class Singleton:
    def __init__(self):
        self.value = None
    
    def do_something(self):
        print("Doing something with value:", self.value)

singleton_instance = Singleton()

# 在其他文件中使用
from singleton import singleton_instance
```

## 方法2：使用装饰器
```python
def singleton(cls):
    instances = {}
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance

@singleton
class MyClass:
    def __init__(self):
        self.value = None
    
    def do_something(self):
        print("Doing something with value:", self.value)

# 使用
a = MyClass()
b = MyClass()
print(a is b)  # 输出: True
```

## 方法3：使用类方法
```python
class Singleton:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self.value = None
    
    def do_something(self):
        print("Doing something with value:", self.value)

# 使用
a = Singleton()
b = Singleton()
print(a is b)  # 输出: True
```

## 方法4：使用元类
```python
class SingletonMeta(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(metaclass=SingletonMeta):
    def __init__(self):
        self.value = None
    
    def do_something(self):
        print("Doing something with value:", self.value)

# 使用
a = Singleton()
b = Singleton()
print(a is b)  # 输出: True
```

## 方法5：线程安全的单例
```python
from threading import Lock

class Singleton:
    _instance = None
    _lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self.value = None
    
    def do_something(self):
        print("Doing something with value:", self.value)

# 使用
a = Singleton()
b = Singleton()
print(a is b)  # 输出: True
```

以上方法中，最简单的是使用模块方式，最常用的是装饰器或类方法方式，如果需要线程安全则使用最后一种方法。

