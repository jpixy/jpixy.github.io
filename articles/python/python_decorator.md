Python 装饰器（Decorator）是一种非常强大的功能，它允许你在不修改原始函数代码的情况下，增加函数的新功能。装饰器本质上是一个函数，它接收一个函数作为参数，并返回一个新的函数。

### 装饰器的基本用法

#### 1. **简单装饰器**
装饰器的核心是定义一个外层函数，它接收一个函数作为参数，并返回一个新的函数。这个新函数可以添加额外的逻辑。

```python
def my_decorator(func):
    def wrapper():
        print("Something is happening before the function is called.")
        func()
        print("Something is happening after the function is called.")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()
```

输出：
```
Something is happening before the function is called.
Hello!
Something is happening after the function is called.
```

#### 2. **带参数的装饰器**
如果被装饰的函数有参数，装饰器的内部函数需要接收这些参数。

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Something is happening before the function is called.")
        result = func(*args, **kwargs)
        print("Something is happening after the function is called.")
        return result
    return wrapper

@my_decorator
def add(a, b):
    return a + b

print(add(3, 5))
```

输出：
```
Something is happening before the function is called.
Something is happening after the function is called.
8
```

#### 3. **带参数的装饰器**
如果装饰器本身也需要参数，可以再嵌套一层函数。

```python
def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def say_hello():
    print("Hello!")

say_hello()
```

输出：
```
Hello!
Hello!
Hello!
```

### 装饰器的使用场景

#### 1. **日志记录**
装饰器可以用来记录函数的调用情况，包括参数、返回值等。

```python
import logging

def log_decorator(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling function {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"Function {func.__name__} returned {result}")
        return result
    return wrapper

@log_decorator
def add(a, b):
    return a + b

logging.basicConfig(level=logging.INFO)
print(add(3, 5))
```

#### 2. **性能测试**
装饰器可以用来测量函数的执行时间。

```python
import time

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

@timer_decorator
def compute(x):
    time.sleep(x)
    return x

compute(2)
```

#### 3. **权限验证**
装饰器可以用来检查用户是否有权限执行某个操作。

```python
def auth_decorator(func):
    def wrapper(*args, **kwargs):
        user = kwargs.get("user")
        if user != "admin":
            raise PermissionError("You do not have permission to perform this action")
        return func(*args, **kwargs)
    return wrapper

@auth_decorator
def delete_data(user):
    print("Data deleted")

delete_data(user="admin")
```

#### 4. **缓存结果**
装饰器可以用来缓存函数的结果，避免重复计算。

```python
from functools import lru_cache

@lru_cache(maxsize=32)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(10))
```

#### 5. **事务管理**
在数据库操作中，装饰器可以用来管理事务。

```python
def transaction_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            print("Committing transaction")
            return result
        except Exception as e:
            print("Rolling back transaction")
            raise e
    return wrapper

@transaction_decorator
def update_database():
    print("Updating database")
    # Simulate an error
    raise ValueError("Something went wrong")

try:
    update_database()
except ValueError as e:
    print(e)
```

### 装饰器的高级用法

#### 1. **使用 `functools.wraps`**
当使用装饰器时，原始函数的元信息（如函数名、文档字符串等）会被覆盖。为了避免这个问题，可以使用 `functools.wraps`。

```python
import functools

def my_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("Something is happening before the function is called.")
        result = func(*args, **kwargs)
        print("Something is happening after the function is called.")
        return result
    return wrapper

@my_decorator
def say_hello():
    """This function says hello."""
    print("Hello!")

print(say_hello.__name__)  # 输出: say_hello
print(say_hello.__doc__)   # 输出: This function says hello.
```

#### 2. **类装饰器**
装饰器不仅可以用于函数，还可以用于类。

```python
def class_decorator(cls):
    class Wrapper:
        def __init__(self, *args, **kwargs):
            self._instance = cls(*args, **kwargs)
        
        def __getattr__(self, name):
            return getattr(self._instance, name)
    
    return Wrapper

@class_decorator
class MyClass:
    def __init__(self, value):
        self.value = value

    def show(self):
        print(f"Value: {self.value}")

obj = MyClass(10)
obj.show()
```

### 总结

装饰器是 Python 中一个非常强大的功能，它可以用来扩展函数或类的功能，而无需修改原始代码。常见的使用场景包括日志记录、性能测试、权限验证、缓存结果和事务管理等。通过合理使用装饰器，可以使代码更加简洁、可维护性更高。
