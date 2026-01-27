+++
title = "57.Python双下划线变量详解"
description = "Python模块级双下划线变量详解：__name__、__main__、__file__、__all__等核心概念"
date = 2026-01-27
draft = false
[taxonomies]
tags = ["Python", "Module", "Dunder", "Best Practice"]
+++

# Python 双下划线变量详解

Python 中以双下划线开头和结尾的名称（如 `__name__`）被称为 **dunder**（double underscore 的缩写）。它们分为两大类：**类的魔术方法**和**模块级变量**。本文专注于后者。

---

## 一、`__name__` 与 `if __name__ == '__main__':`

### 1.1 `__name__` 是什么

`__name__` 是每个 Python 模块自动拥有的变量，表示模块的名称。

```python
# example.py
print(__name__)
```

**关键规则**：
- 当模块被**直接运行**时：`__name__ == '__main__'`
- 当模块被**import导入**时：`__name__ == '模块名'`

```bash
# 直接运行
$ python example.py
__main__

# 作为模块导入
$ python -c "import example"
example
```

### 1.2 为什么需要 `if __name__ == '__main__':`

这是 Python 的**入口点惯用法**，用于区分"直接运行"和"被导入"两种场景。

```python
# calculator.py

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

# 只有直接运行时才执行的代码
if __name__ == '__main__':
    # 测试代码
    print(add(2, 3))      # 5
    print(subtract(5, 2)) # 3
```

**好处**：
1. **可复用**：其他模块可以安全 `import calculator`，不会触发测试代码
2. **可测试**：直接运行 `python calculator.py` 可以执行测试
3. **清晰的入口**：明确标识程序入口点

### 1.3 实际应用场景

**场景1：命令行工具**
```python
# cli_tool.py
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    print(f"Hello, {args.name}!")

if __name__ == '__main__':
    main()
```

**场景2：模块自测试**
```python
# utils.py
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

if __name__ == '__main__':
    # 简单测试
    assert factorial(5) == 120
    assert factorial(0) == 1
    print("All tests passed!")
```

**场景3：多进程必须使用**
```python
# multiprocess_example.py
from multiprocessing import Pool

def worker(x):
    return x * x

if __name__ == '__main__':  # 多进程必须在这里面
    with Pool(4) as p:
        results = p.map(worker, range(10))
        print(results)
```

> ⚠️ **Windows 上多进程代码必须放在 `if __name__ == '__main__':` 中**，否则会报错。

### 1.4 `-m` 参数运行

使用 `python -m module_name` 运行时，`__name__` 仍然是 `'__main__'`：

```bash
$ python -m calculator
# __name__ == '__main__'
```

这是运行包中模块的标准方式：

```bash
$ python -m pytest           # 运行 pytest
$ python -m http.server 8000 # 启动 HTTP 服务器
$ python -m venv myenv       # 创建虚拟环境
```

---

## 二、`__file__` - 文件路径

### 2.1 基本用法

`__file__` 是当前文件的路径（可能是相对路径或绝对路径）。

```python
# /home/user/project/mymodule.py
print(__file__)  # /home/user/project/mymodule.py
```

### 2.2 获取文件所在目录

```python
import os
from pathlib import Path

# 方法1：os.path
current_dir = os.path.dirname(os.path.abspath(__file__))

# 方法2：pathlib（推荐）
current_dir = Path(__file__).parent.resolve()

print(current_dir)  # /home/user/project
```

### 2.3 常见应用

**加载同目录下的配置文件**：
```python
from pathlib import Path
import json

# 获取当前脚本所在目录
BASE_DIR = Path(__file__).parent.resolve()

# 加载配置文件
config_path = BASE_DIR / 'config.json'
with open(config_path) as f:
    config = json.load(f)
```

**添加父目录到 Python 路径**：
```python
import sys
from pathlib import Path

# 将父目录添加到路径，方便导入
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### 2.4 注意事项

```python
# 交互式环境中 __file__ 不存在
>>> __file__
NameError: name '__file__' is not defined

# 使用 __file__ 前最好检查
if '__file__' in dir():
    base_dir = Path(__file__).parent
else:
    base_dir = Path.cwd()
```

---

## 三、`__doc__` - 文档字符串

### 3.1 基本用法

`__doc__` 存储模块、类、函数的文档字符串（docstring）。

```python
"""这是模块的文档字符串"""

def greet(name):
    """
    向用户打招呼
    
    Args:
        name: 用户名
    
    Returns:
        问候语字符串
    """
    return f"Hello, {name}!"

class Person:
    """表示一个人"""
    pass

# 访问文档
print(__doc__)          # 这是模块的文档字符串
print(greet.__doc__)    # 向用户打招呼...
print(Person.__doc__)   # 表示一个人
```

### 3.2 与 help() 的关系

```python
help(greet)
# 输出：
# Help on function greet in module __main__:
#
# greet(name)
#     向用户打招呼
#     ...
```

### 3.3 文档风格

**Google 风格**（推荐）：
```python
def fetch_data(url, timeout=30):
    """从 URL 获取数据
    
    Args:
        url: 目标 URL
        timeout: 超时时间（秒），默认 30
    
    Returns:
        响应内容的字节串
    
    Raises:
        TimeoutError: 请求超时时抛出
        ValueError: URL 格式无效时抛出
    """
    pass
```

**NumPy 风格**：
```python
def calculate(x, y):
    """
    计算两数之和
    
    Parameters
    ----------
    x : int
        第一个数
    y : int
        第二个数
    
    Returns
    -------
    int
        两数之和
    """
    return x + y
```

---

## 四、`__all__` - 导出控制

### 4.1 作用

`__all__` 定义了 `from module import *` 时导出的名称列表。

```python
# mymodule.py

__all__ = ['public_func', 'PublicClass']

def public_func():
    """会被导出"""
    pass

def _private_func():
    """不会被导出（单下划线）"""
    pass

def internal_func():
    """不在 __all__ 中，* 导入时不会导出"""
    pass

class PublicClass:
    """会被导出"""
    pass
```

```python
# 使用
from mymodule import *

public_func()       # ✓ 可用
PublicClass()       # ✓ 可用
internal_func()     # ✗ NameError
_private_func()     # ✗ NameError

# 但显式导入仍然可以
from mymodule import internal_func  # ✓ 仍然可以
```

### 4.2 包的 `__init__.py` 中使用

```python
# mypackage/__init__.py

from .module_a import func_a
from .module_b import func_b, ClassB

__all__ = ['func_a', 'func_b', 'ClassB']
```

### 4.3 最佳实践

```python
# 推荐：在模块开头定义 __all__
__all__ = [
    'Connection',
    'Query',
    'execute',
]

# 然后定义这些内容
class Connection:
    pass

class Query:
    pass

def execute():
    pass
```

---

## 五、`__dict__` - 属性字典

### 5.1 模块的 `__dict__`

```python
# 查看模块的所有属性
import math
print(math.__dict__.keys())
# dict_keys(['__name__', '__doc__', 'pi', 'e', 'sin', 'cos', ...])
```

### 5.2 对象的 `__dict__`

```python
class Person:
    species = 'human'  # 类属性
    
    def __init__(self, name, age):
        self.name = name  # 实例属性
        self.age = age

p = Person('Alice', 30)

# 实例的 __dict__：只包含实例属性
print(p.__dict__)
# {'name': 'Alice', 'age': 30}

# 类的 __dict__：包含类属性和方法
print(Person.__dict__.keys())
# dict_keys(['__module__', '__dict__', '__weakref__', '__doc__', 
#            'species', '__init__'])
```

### 5.3 动态添加属性

```python
class Dynamic:
    pass

obj = Dynamic()
obj.__dict__['x'] = 10
obj.__dict__['y'] = 20

print(obj.x, obj.y)  # 10 20
```

### 5.4 `__slots__` 与 `__dict__`

使用 `__slots__` 的类没有 `__dict__`：

```python
class Optimized:
    __slots__ = ['x', 'y']
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

obj = Optimized(1, 2)
print(obj.__dict__)  # AttributeError: 'Optimized' object has no attribute '__dict__'
```

---

## 六、其他模块级变量

### 6.1 `__package__`

表示模块所属的包名。

```python
# mypackage/submodule.py
print(__package__)  # mypackage

# 顶层脚本
print(__package__)  # None 或 ''
```

### 6.2 `__spec__`

模块的导入规范（Python 3.4+）。

```python
import json
print(json.__spec__)
# ModuleSpec(name='json', loader=<...>, origin='/.../json/__init__.py', 
#            submodule_search_locations=[...])

print(json.__spec__.name)    # json
print(json.__spec__.origin)  # 模块文件路径
```

### 6.3 `__loader__`

加载模块的 loader 对象。

```python
import json
print(json.__loader__)
# <_frozen_importlib_external.SourceFileLoader object at ...>
```

### 6.4 `__cached__`

编译后的字节码缓存文件路径（`.pyc`）。

```python
import json
print(json.__cached__)
# /.../json/__pycache__/__init__.cpython-311.pyc
```

### 6.5 `__annotations__`

类型注解字典。

```python
x: int = 10
y: str = "hello"

def greet(name: str) -> str:
    return f"Hello, {name}"

# 模块级注解
print(__annotations__)
# {'x': <class 'int'>, 'y': <class 'str'>}

# 函数级注解
print(greet.__annotations__)
# {'name': <class 'str'>, 'return': <class 'str'>}
```

---

## 七、`__init__.py` 与 `__main__.py`

### 7.1 `__init__.py` - 包初始化

`__init__.py` 使目录成为 Python 包。

```
mypackage/
├── __init__.py      # 包初始化文件
├── module_a.py
└── module_b.py
```

```python
# mypackage/__init__.py

# 包级别的导入
from .module_a import func_a
from .module_b import func_b

# 包的版本号
__version__ = '1.0.0'

# 控制 * 导入
__all__ = ['func_a', 'func_b']
```

```python
# 使用
from mypackage import func_a  # 直接从包导入
import mypackage
print(mypackage.__version__)  # 1.0.0
```

### 7.2 `__main__.py` - 包的入口点

`__main__.py` 定义使用 `python -m package_name` 运行时的行为。

```
mypackage/
├── __init__.py
├── __main__.py      # 入口点
├── cli.py
└── core.py
```

```python
# mypackage/__main__.py

from .cli import main

if __name__ == '__main__':
    main()
```

```bash
# 运行包
$ python -m mypackage
```

**真实示例**：

```bash
$ python -m pip install requests    # pip 包有 __main__.py
$ python -m pytest                  # pytest 包有 __main__.py
$ python -m json.tool data.json     # json 模块有 __main__.py
```

---

## 八、完整列表汇总

| 变量 | 类型 | 描述 |
|------|------|------|
| `__name__` | str | 模块名，直接运行时为 `'__main__'` |
| `__file__` | str | 模块文件路径 |
| `__doc__` | str | 模块/函数/类的文档字符串 |
| `__all__` | list | `from x import *` 的导出列表 |
| `__dict__` | dict | 对象/模块的属性字典 |
| `__package__` | str | 包名 |
| `__spec__` | ModuleSpec | 模块导入规范 |
| `__loader__` | object | 模块加载器 |
| `__cached__` | str | 编译缓存文件路径 |
| `__annotations__` | dict | 类型注解 |
| `__version__` | str | （约定）版本号 |
| `__author__` | str | （约定）作者 |

---

## 九、最佳实践

### 9.1 模块模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块简短描述

详细描述...
"""

__all__ = ['main_function', 'MainClass']
__version__ = '1.0.0'
__author__ = 'Your Name'

# 标准库导入
import os
import sys
from pathlib import Path

# 第三方库导入
import requests

# 本地导入
from . import utils

# 常量
BASE_DIR = Path(__file__).parent.resolve()


def main_function():
    """主函数"""
    pass


class MainClass:
    """主类"""
    pass


def _private_helper():
    """私有辅助函数"""
    pass


if __name__ == '__main__':
    main_function()
```

### 9.2 包结构模板

```
mypackage/
├── __init__.py          # from .core import *; __version__ = '1.0.0'
├── __main__.py          # 入口点：python -m mypackage
├── core.py              # 核心功能
├── utils.py             # 工具函数
├── cli.py               # 命令行接口
├── config/
│   ├── __init__.py
│   └── settings.py
└── tests/
    ├── __init__.py
    └── test_core.py
```

---

## 概念速查

- [Python核心概念索引](/articles/00-glossary/glossary-06-python-concepts/) - GIL、装饰器、生成器等概念速查
- [Python类特殊方法](/articles/python/py-08-类特殊方法/) - `__init__`、`__str__` 等类魔术方法
- [Python定制类特殊方法大全](/articles/python/py-09-定制类特殊方法/) - 完整的类 dunder 方法列表
