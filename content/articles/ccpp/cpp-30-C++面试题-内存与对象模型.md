+++
title = "30.C++面试题-内存与对象模型"
date = 2026-01-21
description = "C++内存管理与对象模型面试题汇总，包括内存布局、构造析构、虚函数表、继承等核心概念"
[taxonomies]
tags = ["C++", "面试题", "内存管理", "对象模型"]
+++

## 一、内存管理

### Q1: 栈和堆的区别？

| 特性 | 栈（Stack） | 堆（Heap） |
|------|-------------|------------|
| 管理方式 | 自动 | 手动 |
| 分配速度 | 快（移动指针） | 慢（查找空闲块） |
| 大小限制 | 小（1-8MB） | 大（受系统限制） |
| 碎片 | 无 | 可能有 |
| 访问速度 | 快（局部性好） | 较慢 |

```cpp
void example() {
    int stackVar = 10;      // 栈上
    int* heapVar = new int(20);  // 堆上
    
    // stackVar在函数返回时自动销毁
    delete heapVar;  // 必须手动释放
}
```

### Q2: new/delete和malloc/free的区别？

| 特性 | new/delete | malloc/free |
|------|------------|-------------|
| 类型 | 运算符 | 函数 |
| 构造/析构 | 调用 | 不调用 |
| 类型安全 | 是 | 否 |
| 返回值 | 类型指针 | void* |
| 失败行为 | 抛异常 | 返回NULL |
| 重载 | 可以 | 不能 |

```cpp
// malloc/free
int* p1 = (int*)malloc(sizeof(int) * 10);
free(p1);

// new/delete
int* p2 = new int(42);      // 调用构造函数
delete p2;                   // 调用析构函数

int* p3 = new int[10];      // 数组
delete[] p3;                 // 必须用delete[]

// 类对象
class MyClass { /*...*/ };
MyClass* obj = (MyClass*)malloc(sizeof(MyClass));  // 不调用构造函数！
free(obj);  // 不调用析构函数！

MyClass* obj2 = new MyClass();  // 调用构造函数
delete obj2;  // 调用析构函数
```

### Q3: 内存泄漏如何检测和避免？

```cpp
// 避免内存泄漏的方法：
// 1. 使用智能指针
std::unique_ptr<int> p1 = std::make_unique<int>(42);
std::shared_ptr<int> p2 = std::make_shared<int>(42);

// 2. RAII模式
class Resource {
    int* data;
public:
    Resource() : data(new int[100]) {}
    ~Resource() { delete[] data; }
};

// 3. 检测工具
// - Valgrind: valgrind --leak-check=full ./app
// - AddressSanitizer: g++ -fsanitize=address
// - Visual Studio内置检测
```

---

## 二、对象生命周期

### Q4: 构造函数和析构函数的调用顺序？

```cpp
class Base {
public:
    Base() { std::cout << "Base ctor\n"; }
    virtual ~Base() { std::cout << "Base dtor\n"; }
};

class Derived : public Base {
    Member member_;
public:
    Derived() : member_() { std::cout << "Derived ctor\n"; }
    ~Derived() { std::cout << "Derived dtor\n"; }
};

// 构造顺序：基类 → 成员 → 派生类
// 析构顺序：派生类 → 成员 → 基类

Derived d;
// 输出：
// Base ctor
// Member ctor（假设有）
// Derived ctor
// Derived dtor
// Member dtor
// Base dtor
```

### Q5: 为什么析构函数要是virtual？

```cpp
class Base {
public:
    ~Base() { std::cout << "Base dtor\n"; }  // 非虚
};

class Derived : public Base {
public:
    ~Derived() { std::cout << "Derived dtor\n"; }
};

Base* p = new Derived();
delete p;  // 只调用Base析构函数！内存泄漏

// 解决：基类析构函数声明为virtual
class Base {
public:
    virtual ~Base() { std::cout << "Base dtor\n"; }
};

// 现在delete p会正确调用Derived析构函数
```

### Q6: 拷贝构造函数什么时候调用？

```cpp
class MyClass {
public:
    MyClass() { std::cout << "default ctor\n"; }
    MyClass(const MyClass&) { std::cout << "copy ctor\n"; }
    MyClass& operator=(const MyClass&) { 
        std::cout << "copy assign\n"; 
        return *this; 
    }
};

// 1. 用同类型对象初始化
MyClass a;
MyClass b = a;  // 拷贝构造

// 2. 按值传递
void func(MyClass obj);
func(a);  // 拷贝构造

// 3. 按值返回
MyClass createObj() {
    MyClass obj;
    return obj;  // 可能拷贝构造（但RVO可能优化掉）
}

// 4. 赋值（不是拷贝构造）
MyClass c;
c = a;  // 拷贝赋值运算符
```

---

## 三、对象内存布局

### Q7: 空类的大小是多少？为什么？

```cpp
class Empty {};
sizeof(Empty);  // 1

// 原因：C++要求每个对象都有唯一的地址
Empty arr[10];
// 如果sizeof(Empty)==0，则所有元素地址相同

// 空基类优化（EBO）
class Derived : public Empty {
    int x;
};
sizeof(Derived);  // 4（不是5），Empty不占用额外空间
```

### Q8: 虚函数表（vtable）和虚函数指针（vptr）？

```cpp
class Base {
public:
    virtual void foo() {}
    virtual void bar() {}
};

class Derived : public Base {
public:
    void foo() override {}  // 覆盖
    // bar()继承自Base
};

sizeof(Base);  // 8（64位系统，一个vptr）

// 内存布局：
// Base对象:
// +0: vptr → Base的vtable
// 
// Base的vtable:
// [0] → &Base::foo
// [1] → &Base::bar
//
// Derived的vtable:
// [0] → &Derived::foo  // 覆盖
// [1] → &Base::bar     // 继承
```

### Q9: 多重继承的内存布局？

```cpp
class A {
    int a;
    virtual void foo() {}
};

class B {
    int b;
    virtual void bar() {}
};

class C : public A, public B {
    int c;
};

// C的内存布局：
// +0:  vptr_A → C's vtable for A
// +8:  int a
// +12: padding
// +16: vptr_B → C's vtable for B
// +24: int b
// +28: int c
// +32: padding

sizeof(C);  // 32（假设64位系统）

// 注意：C有两个vptr！
```

---

## 四、特殊成员函数

### Q10: Rule of Three/Five/Zero？

```cpp
// Rule of Three（C++98）
// 如果定义了以下任一个，通常需要定义全部三个：
// - 析构函数
// - 拷贝构造函数
// - 拷贝赋值运算符

// Rule of Five（C++11）
// 加上：
// - 移动构造函数
// - 移动赋值运算符

class Resource {
    int* data;
public:
    // 1. 析构函数
    ~Resource() { delete data; }
    
    // 2. 拷贝构造函数
    Resource(const Resource& other) : data(new int(*other.data)) {}
    
    // 3. 拷贝赋值运算符
    Resource& operator=(const Resource& other) {
        if (this != &other) {
            delete data;
            data = new int(*other.data);
        }
        return *this;
    }
    
    // 4. 移动构造函数
    Resource(Resource&& other) noexcept : data(other.data) {
        other.data = nullptr;
    }
    
    // 5. 移动赋值运算符
    Resource& operator=(Resource&& other) noexcept {
        if (this != &other) {
            delete data;
            data = other.data;
            other.data = nullptr;
        }
        return *this;
    }
};

// Rule of Zero（推荐）
// 不自定义任何特殊成员函数，使用智能指针
class BetterResource {
    std::unique_ptr<int> data;  // 编译器生成的函数足够
};
```

### Q11: default和delete关键字？

```cpp
class MyClass {
public:
    // 显式使用编译器生成的默认实现
    MyClass() = default;
    MyClass(const MyClass&) = default;
    MyClass& operator=(const MyClass&) = default;
    ~MyClass() = default;
    
    // 禁止某个函数
    MyClass(MyClass&&) = delete;  // 禁止移动
    void* operator new(size_t) = delete;  // 禁止动态分配
};

// 用途：
// 1. 使隐式声明变为显式
// 2. 恢复编译器生成的函数
// 3. 禁止不希望的操作
```

---

## 五、继承与多态

### Q12: 虚继承解决什么问题？

```cpp
// 菱形继承问题
class A { public: int a; };
class B : public A {};
class C : public A {};
class D : public B, public C {};

// D有两份A！
D d;
d.a;  // 歧义：B::a还是C::a？
d.B::a = 1;  // 必须明确

// 虚继承解决
class B : virtual public A {};
class C : virtual public A {};
class D : public B, public C {};

// D只有一份A
d.a = 1;  // OK
```

### Q13: 抽象类和接口？

```cpp
// 抽象类：包含纯虚函数
class AbstractClass {
public:
    virtual void pureVirtual() = 0;  // 纯虚函数
    virtual void normalVirtual() {}   // 普通虚函数
    void nonVirtual() {}              // 非虚函数
};

// 接口：只有纯虚函数（C++没有interface关键字）
class Interface {
public:
    virtual ~Interface() = default;
    virtual void method1() = 0;
    virtual void method2() = 0;
};

// 使用
class Implementation : public Interface {
public:
    void method1() override {}
    void method2() override {}
};
```

---

## 面试技巧

1. **内存管理**：强调智能指针和RAII
2. **对象布局**：理解vptr位置和多重继承的复杂性
3. **构造/析构**：记住调用顺序，基类→成员→派生类
4. **Rule of Five**：推荐Rule of Zero
5. **虚析构**：这是经典面试题，必须掌握
