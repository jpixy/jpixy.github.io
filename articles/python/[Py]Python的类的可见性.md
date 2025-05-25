# Python 类的可见性详解
Python 中的类成员可见性与 Java/C++ 等语言有所不同，它没有严格的 `private`、`protected`、`public` 关键字，而是通过命名约定和一些特殊机制来实现可见性控制。

## 1. 公有成员 (Public)
Python 中所有成员默认都是公有的，可以直接访问。

```python
class MyClass:
    def __init__(self):
        self.public_var = "I'm public"
    
    def public_method(self):
        return "Public method"

obj = MyClass()
print(obj.public_var)      # 可以直接访问
print(obj.public_method()) # 可以直接调用
```

## 2. 受保护成员 (Protected)
Python 中使用单下划线 `_` 前缀表示受保护成员，这是一种约定，告诉开发者"这个成员仅供内部使用"，但 Python 并不会阻止外部访问。

```python
class MyClass:
    def __init__(self):
        self._protected_var = "I'm protected"
    
    def _protected_method(self):
        return "Protected method"

obj = MyClass()
print(obj._protected_var)      # 仍然可以访问（不推荐）
print(obj._protected_method()) # 仍然可以调用（不推荐）
```

## 3. 私有成员 (Private)
Python 中使用双下划线 `__` 前缀表示私有成员，这会触发名称修饰 (name mangling)，Python 解释器会修改成员名称以防止意外覆盖。

```python
class MyClass:
    def __init__(self):
        self.__private_var = "I'm private"
    
    def __private_method(self):
        return "Private method"

obj = MyClass()
# print(obj.__private_var)      # 直接访问会报错
# print(obj.__private_method()) # 直接调用会报错

# 但实际上可以通过修饰后的名称访问（但不应该这样做）
print(obj._MyClass__private_var)      # 可以访问
print(obj._MyClass__private_method()) # 可以调用
```

## 4. 名称修饰 (Name Mangling) 规则
当成员以双下划线开头但不以双下划线结尾时，Python 会进行名称修饰：

+ 原始名称 `__var` 会被修改为 `_ClassName__var`
+ 这主要是为了避免子类意外覆盖父类的私有成员

## 5. 特殊成员
双下划线开头和结尾的成员是 Python 的特殊方法，不会触发名称修饰：

```python
class MyClass:
    def __init__(self):
        self.__special__ = "I'm special"

obj = MyClass()
print(obj.__special__)  # 可以直接访问
```

## 6. 属性装饰器 (@property)
Python 提供了 `@property` 装饰器来实现更精细的属性访问控制：

```python
class MyClass:
    def __init__(self):
        self._internal_var = 0
    
    @property
    def value(self):
        return self._internal_var
    
    @value.setter
    def value(self, new_value):
        if new_value < 0:
            raise ValueError("Value cannot be negative")
        self._internal_var = new_value

obj = MyClass()
obj.value = 10     # 调用 setter
print(obj.value)   # 调用 getter
# obj.value = -5   # 会抛出 ValueError
```

## 7. 最佳实践
1. 公有成员：无前缀，可以在任何地方访问
2. 受保护成员：单下划线前缀，表示内部使用，但子类可以访问
3. 私有成员：双下划线前缀，表示真正私有，子类也不应访问
4. 特殊方法：双下划线前缀和后缀，用于操作符重载等

## 8. 总结
Python 的可见性控制主要依靠约定而非强制：

+ 没有真正的私有成员，但通过名称修饰增加了访问难度
+ 开发者应遵守约定，不随意访问带下划线的成员
+ 使用 `@property` 可以实现更复杂的访问控制逻辑

记住 Python 的哲学："我们都是成年人"，它相信开发者会明智地使用这些约定，而不是强制限制访问。

