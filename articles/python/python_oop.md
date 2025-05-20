Python 的 **面向对象编程（OOP）** 包含 **4 大核心特性**：  
**封装（Encapsulation）、继承（Inheritance）、多态（Polymorphism）、抽象（Abstraction）**。  

下面分别解释它们的 **概念、作用、代码示例**，并用生活例子辅助理解。

---

## **1. 封装（Encapsulation）**
### **（1）概念**
将 **数据（属性）** 和 **操作数据的方法（行为）** 绑定在一起，并 **隐藏内部细节**，只暴露必要的接口。  
✅ **核心思想**：**“黑箱”设计**，使用者无需关心内部实现，只需调用接口。

### **（2）代码示例**
```python
class BankAccount:
    def __init__(self, balance=0):
        self.__balance = balance  # 私有属性（用双下划线隐藏）

    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount

    def withdraw(self, amount):
        if 0 < amount <= self.__balance:
            self.__balance -= amount

    def get_balance(self):  # 提供公共方法访问私有数据
        return self.__balance

account = BankAccount(1000)
account.deposit(500)
account.withdraw(200)
print(account.get_balance())  # 输出：1300
# print(account.__balance)  # 报错！无法直接访问私有属性
```
**📌 关键点**：
- 用 `__`（双下划线）表示 **私有属性/方法**（外部无法直接访问）。
- 提供 **公共方法（如 `get_balance()`）** 控制对数据的访问。

### **（3）生活例子**
- **ATM 机**：你只需要插入卡、输入密码、取钱，无需知道机器内部如何验密、出钞。

---

## **2. 继承（Inheritance）**
### **（1）概念**
子类 **继承父类的属性和方法**，并可以 **扩展或修改** 它们。  
✅ **核心思想**：**代码复用** + **层次化设计**。

### **（2）代码示例**
```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        raise NotImplementedError("子类必须实现 speak()")

class Dog(Animal):
    def speak(self):
        return "汪汪！"

class Cat(Animal):
    def speak(self):
        return "喵喵~"

dog = Dog("阿黄")
cat = Cat("小白")
print(dog.speak())  # 输出：汪汪！
print(cat.speak())  # 输出：喵喵~
```
**📌 关键点**：
- 子类 **自动拥有父类的属性和方法**（如 `name`）。
- 可以 **重写（Override）** 父类方法（如 `speak()`）。

### **（3）生活例子**
- **交通工具**：  
  - 父类：`Vehicle`（有 `run()` 方法）  
  - 子类：`Car`、`Bike`、`Plane`（各自实现不同的 `run()` 方式）。

---

## **3. 多态（Polymorphism）**
### **（1）概念**
**同一方法** 在不同类中有 **不同的实现**，使得 **不同对象可以响应相同的调用方式**。  
✅ **核心思想**：**“接口一致，实现不同”**。

### **（2）代码示例**
```python
def animal_sound(animal):
    print(animal.speak())  # 只要对象有 speak() 方法就能调用

dog = Dog("阿黄")
cat = Cat("小白")
animal_sound(dog)  # 输出：汪汪！
animal_sound(cat)  # 输出：喵喵~
```
**📌 关键点**：
- **不关心对象的具体类型**，只要它有 `speak()` 方法。
- 适用于 **函数参数、列表存储不同子类对象** 等场景。

### **（3）生活例子**
- **USB 接口**：  
  - U 盘、鼠标、键盘插到 USB 口都能工作，但具体功能不同。

---

## **4. 抽象（Abstraction）**
### **（1）概念**
**隐藏复杂逻辑**，只暴露 **关键功能**。在 Python 中通过 **抽象基类（ABC）** 实现。  
✅ **核心思想**：**“定义规范，强制子类实现”**。

### **（2）代码示例**
```python
from abc import ABC, abstractmethod

class Shape(ABC):  # 抽象基类
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):  # 必须实现抽象方法
        return 3.14 * self.radius ** 2

# shape = Shape()  # 报错！不能实例化抽象类
circle = Circle(5)
print(circle.area())  # 输出：78.5
```
**📌 关键点**：
- 用 `@abstractmethod` 声明 **抽象方法**（子类必须实现）。
- 抽象类 **不能直接实例化**，只能被继承。

### **（3）生活例子**
- **电路开关**：  
  - 你只需要知道“按开关能通电”，无需了解内部电路如何工作。

---

## **总结：四大特性对比**
| 特性 | 核心思想 | 代码表现 | 生活例子 |
|------|---------|---------|---------|
| **封装** | 隐藏细节，暴露接口 | 私有属性 `__var` + 公共方法 | ATM 机 |
| **继承** | 代码复用 + 扩展 | `class Child(Parent):` | 交通工具分类 |
| **多态** | 同一接口，不同实现 | 子类重写方法 + 统一调用 | USB 设备 |
| **抽象** | 定义规范，强制实现 | `ABC` + `@abstractmethod` | 电路开关 |

---

## **附加：Python 面向对象其他概念**
1. **组合（Composition）**  
   - 通过 **包含其他类的对象** 实现功能（比继承更灵活）。  
   - 例如：`Car` 类包含 `Engine` 和 `Wheel` 对象。

2. **魔术方法（Magic Methods）**  
   - 如 `__init__`、`__str__`、`__add__`，用于自定义类的行为。

3. **类变量 vs 实例变量**  
   - **类变量**：所有实例共享（如 `ClassName.var`）。  
   - **实例变量**：每个实例独立（如 `self.var`）。

---

## **面试常见问题**
❓ **Q1：Python 如何实现私有属性？**  
👉 用双下划线 `__var`，但实际上通过 `_ClassName__var` 仍可访问（伪私有）。  

❓ **Q2：多态和重载（Overload）的区别？**  
👉 Python 不支持方法重载（同名不同参），但支持多态（子类重写方法）。  

❓ **Q3：什么时候用抽象类？什么时候用接口？**  
👉 Python 没有接口，抽象类用于定义规范（如 `ABC`），而接口通常用 **协议（Protocol）** 或 **鸭子类型** 实现。  

掌握这些概念后，你的 Python 面向对象编程能力会大幅提升！ 🚀
