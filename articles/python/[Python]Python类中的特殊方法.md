在 Python 中，类（`class`）中有一些特殊的方法，它们以双下划线开头和结尾（例如 `__init__`、`__str__`、`__repr__` 等）。这些方法通常被称为“魔法方法”（Magic Methods）或“特殊方法”（Special Methods）。它们在特定的场景下会被自动调用，用于实现特定的功能。

### 1. `__init__()` 方法
`__init__()` 方法是类的初始化方法，通常用于在创建对象时初始化对象的属性。它不是真正的构造函数，因为 Python 的对象创建过程是由 `__new__()` 方法完成的。`__init__()` 的主要作用是初始化对象的状态。

#### 作用：
+ 在对象被创建后，`__init__()` 方法会被自动调用。
+ 它用于设置对象的初始状态，例如初始化属性。

#### 示例：
```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

p = Person("Alice", 30)
print(p.name)  # 输出: Alice
print(p.age)   # 输出: 30
```

### 2. `__new__()` 方法
`__new__()` 是真正的构造函数，它在创建对象时被调用，用于返回类的实例。通常情况下，我们不需要重写 `__new__()`，因为它已经由 Python 的内置机制处理好了。但如果你需要自定义对象的创建过程（例如实现单例模式），可以重写 `__new__()`。

#### 作用：
+ 在对象被创建时，`__new__()` 方法会被调用。
+ 它返回一个类的实例。

#### 示例：
```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance

a = Singleton()
b = Singleton()
print(a is b)  # 输出: True
```

### 3. `__str__()` 方法
`__str__()` 方法用于返回对象的“非正式”字符串表示，通常用于打印对象时的友好输出。

#### 作用：
+ 当使用 `print()` 打印对象时，或者调用 `str()` 函数时，`__str__()` 方法会被调用。
+ 它返回一个易于阅读的字符串表示。

#### 示例：
```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):
        return f"Person(name={self.name}, age={self.age})"

p = Person("Alice", 30)
print(p)  # 输出: Person(name=Alice, age=30)
```

### 4. `__repr__()` 方法
`__repr__()` 方法用于返回对象的“官方”字符串表示，通常用于调试和开发。它应该返回一个可以用来重新创建对象的字符串。

#### 作用：
+ 当调用 `repr()` 函数时，或者在交互式解释器中直接打印对象时，`__repr__()` 方法会被调用。
+ 它返回一个精确的字符串表示，通常可以用来重新创建对象。

#### 示例：
```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"Person(name={self.name!r}, age={self.age})"

p = Person("Alice", 30)
print(repr(p))  # 输出: Person(name='Alice', age=30)
```

### 5. `__del__()` 方法
`__del__()` 方法是析构方法，用于在对象被销毁时执行清理工作。

#### 作用：
+ 当对象被垃圾回收时，`__del__()` 方法会被调用。
+ 它通常用于释放资源，例如关闭文件或数据库连接。

#### 示例：
```python
class FileHandler:
    def __init__(self, filename):
        self.file = open(filename, "w")

    def __del__(self):
        self.file.close()
        print("File closed")

f = FileHandler("example.txt")
del f  # 输出: File closed
```

### 6. `__eq__()` 方法
`__eq__()` 方法用于定义对象的相等性。

#### 作用：
+ 当使用 `==` 比较两个对象时，`__eq__()` 方法会被调用。
+ 它返回一个布尔值，表示两个对象是否相等。

#### 示例：
```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __eq__(self, other):
        if isinstance(other, Person):
            return self.name == other.name and self.age == other.age
        return False

p1 = Person("Alice", 30)
p2 = Person("Alice", 30)
print(p1 == p2)  # 输出: True
```

### 7. `__lt__()`、`__le__()`、`__gt__()`、`__ge__()` 方法
这些方法用于定义对象的比较逻辑，分别对应 `<`、`<=`、`>`、`>=` 操作符。

#### 示例：
```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __lt__(self, other):
        if isinstance(other, Person):
            return self.age < other.age
        return NotImplemented

p1 = Person("Alice", 30)
p2 = Person("Bob", 25)
print(p1 < p2)  # 输出: False
```

### 8. `__add__()` 方法
`__add__()` 方法用于定义对象的加法操作。

#### 示例：
```python
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        return NotImplemented

v1 = Vector(1, 2)
v2 = Vector(3, 4)
v3 = v1 + v2
print(v3.x, v3.y)  # 输出: 4 6
```

### 总结
+ `__init__()` 是初始化方法，用于设置对象的初始状态。
+ `__new__()` 是构造函数，用于创建对象。
+ `__str__()` 和 `__repr__()` 用于定义对象的字符串表示。
+ `__del__()` 用于定义对象的析构逻辑。
+ `__eq__()`、`__lt__()` 等方法用于定义对象的比较逻辑。
+ `__add__()` 等方法用于定义对象的操作符逻辑。

这些特殊方法让 Python 类的行为更加灵活和强大，能够实现类似面向对象语言中的重载等特性。

