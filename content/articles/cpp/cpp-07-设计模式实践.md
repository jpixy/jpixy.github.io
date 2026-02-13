+++
title = "Design Patterns in C++"
date = 2026-01-19
weight = 7000
description = "C++设计模式：创建型、结构型、行为型模式的现代C++实现"
[taxonomies]
tags = ["C++", "设计模式", "架构"]
+++

## 创建型模式

### 单例模式

**线程安全的现代C++实现**：

```cpp
class Singleton {
public:
    static Singleton& getInstance() {
        static Singleton instance;  // C++11保证线程安全
        return instance;
    }
    
    void doSomething() { }
    
    // 禁止拷贝和赋值
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
    
private:
    Singleton() = default;
    ~Singleton() = default;
};

// 使用
Singleton::getInstance().doSomething();
```

### 工厂模式

**简单工厂**：

```cpp
class Product {
public:
    virtual ~Product() = default;
    virtual void use() = 0;
};

class ConcreteProductA : public Product {
public:
    void use() override { std::cout << "Product A" << std::endl; }
};

class ConcreteProductB : public Product {
public:
    void use() override { std::cout << "Product B" << std::endl; }
};

class Factory {
public:
    static std::unique_ptr<Product> create(const std::string& type) {
        if (type == "A") return std::make_unique<ConcreteProductA>();
        if (type == "B") return std::make_unique<ConcreteProductB>();
        return nullptr;
    }
};
```

**工厂方法**：

```cpp
class Creator {
public:
    virtual ~Creator() = default;
    virtual std::unique_ptr<Product> createProduct() = 0;
    
    void doSomething() {
        auto product = createProduct();
        product->use();
    }
};

class ConcreteCreatorA : public Creator {
public:
    std::unique_ptr<Product> createProduct() override {
        return std::make_unique<ConcreteProductA>();
    }
};
```

### 建造者模式

```cpp
class Computer {
public:
    std::string cpu;
    std::string memory;
    std::string storage;
    
    void show() {
        std::cout << cpu << ", " << memory << ", " << storage << std::endl;
    }
};

class ComputerBuilder {
    Computer computer;
public:
    ComputerBuilder& setCPU(const std::string& cpu) {
        computer.cpu = cpu;
        return *this;
    }
    
    ComputerBuilder& setMemory(const std::string& memory) {
        computer.memory = memory;
        return *this;
    }
    
    ComputerBuilder& setStorage(const std::string& storage) {
        computer.storage = storage;
        return *this;
    }
    
    Computer build() {
        return computer;
    }
};

// 使用
auto computer = ComputerBuilder()
    .setCPU("Intel i9")
    .setMemory("32GB")
    .setStorage("1TB SSD")
    .build();
```

---

## 结构型模式

### 适配器模式

```cpp
// 目标接口
class Target {
public:
    virtual ~Target() = default;
    virtual void request() = 0;
};

// 被适配的类
class Adaptee {
public:
    void specificRequest() {
        std::cout << "Specific request" << std::endl;
    }
};

// 适配器
class Adapter : public Target {
    Adaptee adaptee;
public:
    void request() override {
        adaptee.specificRequest();
    }
};
```

### 装饰器模式

```cpp
class Coffee {
public:
    virtual ~Coffee() = default;
    virtual double cost() = 0;
    virtual std::string description() = 0;
};

class SimpleCoffee : public Coffee {
public:
    double cost() override { return 10.0; }
    std::string description() override { return "Coffee"; }
};

class CoffeeDecorator : public Coffee {
protected:
    std::unique_ptr<Coffee> coffee;
public:
    CoffeeDecorator(std::unique_ptr<Coffee> c) : coffee(std::move(c)) {}
};

class MilkDecorator : public CoffeeDecorator {
public:
    using CoffeeDecorator::CoffeeDecorator;
    
    double cost() override { return coffee->cost() + 2.0; }
    std::string description() override { 
        return coffee->description() + " + Milk"; 
    }
};

// 使用
auto coffee = std::make_unique<SimpleCoffee>();
auto milkCoffee = std::make_unique<MilkDecorator>(std::move(coffee));
```

### 代理模式

```cpp
class Image {
public:
    virtual ~Image() = default;
    virtual void display() = 0;
};

class RealImage : public Image {
    std::string filename;
public:
    RealImage(const std::string& f) : filename(f) {
        loadFromDisk();
    }
    
    void loadFromDisk() {
        std::cout << "Loading " << filename << std::endl;
    }
    
    void display() override {
        std::cout << "Displaying " << filename << std::endl;
    }
};

class ProxyImage : public Image {
    std::string filename;
    std::unique_ptr<RealImage> realImage;
public:
    ProxyImage(const std::string& f) : filename(f) {}
    
    void display() override {
        if (!realImage) {
            realImage = std::make_unique<RealImage>(filename);
        }
        realImage->display();
    }
};
```

---

## 行为型模式

### 观察者模式

```cpp
class Observer {
public:
    virtual ~Observer() = default;
    virtual void update(int value) = 0;
};

class Subject {
    std::vector<std::shared_ptr<Observer>> observers;
    int state = 0;
public:
    void attach(std::shared_ptr<Observer> obs) {
        observers.push_back(obs);
    }
    
    void setState(int s) {
        state = s;
        notify();
    }
    
    void notify() {
        for (auto& obs : observers) {
            obs->update(state);
        }
    }
};

class ConcreteObserver : public Observer {
    std::string name;
public:
    ConcreteObserver(const std::string& n) : name(n) {}
    
    void update(int value) override {
        std::cout << name << " received: " << value << std::endl;
    }
};
```

### 策略模式

```cpp
class SortStrategy {
public:
    virtual ~SortStrategy() = default;
    virtual void sort(std::vector<int>& data) = 0;
};

class QuickSort : public SortStrategy {
public:
    void sort(std::vector<int>& data) override {
        std::sort(data.begin(), data.end());
    }
};

class BubbleSort : public SortStrategy {
public:
    void sort(std::vector<int>& data) override {
        // 冒泡排序实现
    }
};

class Sorter {
    std::unique_ptr<SortStrategy> strategy;
public:
    void setStrategy(std::unique_ptr<SortStrategy> s) {
        strategy = std::move(s);
    }
    
    void sort(std::vector<int>& data) {
        strategy->sort(data);
    }
};

// 使用
Sorter sorter;
sorter.setStrategy(std::make_unique<QuickSort>());
sorter.sort(data);
```

### 命令模式

```cpp
class Command {
public:
    virtual ~Command() = default;
    virtual void execute() = 0;
    virtual void undo() = 0;
};

class Light {
public:
    void on() { std::cout << "Light on" << std::endl; }
    void off() { std::cout << "Light off" << std::endl; }
};

class LightOnCommand : public Command {
    Light& light;
public:
    LightOnCommand(Light& l) : light(l) {}
    void execute() override { light.on(); }
    void undo() override { light.off(); }
};

class RemoteControl {
    std::vector<std::unique_ptr<Command>> history;
public:
    void executeCommand(std::unique_ptr<Command> cmd) {
        cmd->execute();
        history.push_back(std::move(cmd));
    }
    
    void undoLast() {
        if (!history.empty()) {
            history.back()->undo();
            history.pop_back();
        }
    }
};
```

### 模板方法模式

```cpp
class DataProcessor {
public:
    // 模板方法
    void process() {
        loadData();
        processData();
        saveResult();
    }
    
protected:
    virtual void loadData() = 0;
    virtual void processData() = 0;
    virtual void saveResult() {
        std::cout << "Saving to default location" << std::endl;
    }
};

class CSVProcessor : public DataProcessor {
protected:
    void loadData() override {
        std::cout << "Loading CSV" << std::endl;
    }
    
    void processData() override {
        std::cout << "Processing CSV" << std::endl;
    }
};
```

---

## 现代C++模式

### CRTP（奇异递归模板模式）

```cpp
template<typename Derived>
class Counter {
    static int count;
public:
    Counter() { count++; }
    ~Counter() { count--; }
    static int getCount() { return count; }
};

template<typename Derived>
int Counter<Derived>::count = 0;

class Widget : public Counter<Widget> {};
class Gadget : public Counter<Gadget> {};

// Widget和Gadget有独立的计数器
```

### 类型擦除

```cpp
class AnyCallable {
    struct Concept {
        virtual ~Concept() = default;
        virtual void call() = 0;
    };
    
    template<typename F>
    struct Model : Concept {
        F func;
        Model(F f) : func(std::move(f)) {}
        void call() override { func(); }
    };
    
    std::unique_ptr<Concept> ptr;
    
public:
    template<typename F>
    AnyCallable(F f) : ptr(std::make_unique<Model<F>>(std::move(f))) {}
    
    void operator()() { ptr->call(); }
};

// 使用
AnyCallable a = []() { std::cout << "Lambda" << std::endl; };
a();
```

---

## 总结

| 类别 | 模式 | 用途 |
|------|------|------|
| 创建型 | 单例 | 全局唯一实例 |
| 创建型 | 工厂 | 对象创建解耦 |
| 创建型 | 建造者 | 复杂对象构建 |
| 结构型 | 适配器 | 接口转换 |
| 结构型 | 装饰器 | 动态添加功能 |
| 结构型 | 代理 | 访问控制 |
| 行为型 | 观察者 | 事件通知 |
| 行为型 | 策略 | 算法替换 |
| 行为型 | 命令 | 操作封装 |
| 行为型 | 模板方法 | 算法骨架 |

现代C++可以利用智能指针、Lambda、模板等特性实现更简洁的设计模式。

---

## 相关文章

- [上一篇：STL Containers and Algorithms](@/articles/cpp/cpp-06-STL容器与算法.md)
- [下一篇：Project Practices and Toolchain](@/articles/cpp/cpp-08-项目实践与工具链.md)
