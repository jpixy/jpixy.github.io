+++
title = "Go语言基础"
date = 2026-01-19
weight = 1000
description = "Go语言入门：语法基础、数据类型、控制结构、函数、包管理"
[taxonomies]
tags = ["Go", "基础", "入门"]
+++

## Go语言特点

### 设计理念

- **简洁**：语法简单，关键字少
- **高效**：编译快，执行快
- **并发**：goroutine和channel原生支持
- **安全**：类型安全、垃圾回收
- **工具链**：格式化、测试、文档一体化

### 适用场景

- 云原生应用（Docker、Kubernetes）
- 微服务
- 网络服务
- 命令行工具
- 分布式系统

---

## 基本语法

### Hello World

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
```

### 变量声明

```go
// var声明
var name string = "Go"
var age int = 10
var isReady bool  // 零值：false

// 短变量声明（推荐，只能在函数内）
name := "Go"
age := 10

// 多变量声明
var x, y int = 1, 2
a, b := 1, 2

// 常量
const Pi = 3.14159
const (
    StatusOK = 200
    StatusNotFound = 404
)

// iota枚举
const (
    Sunday = iota  // 0
    Monday         // 1
    Tuesday        // 2
)
```

### 基本类型

```go
// 整数
int8, int16, int32, int64
uint8, uint16, uint32, uint64
int, uint  // 平台相关
byte  // uint8别名
rune  // int32别名，表示Unicode码点

// 浮点
float32, float64

// 复数
complex64, complex128

// 布尔
bool

// 字符串
string  // 不可变，UTF-8编码
```

### 零值

```go
var i int       // 0
var f float64   // 0.0
var b bool      // false
var s string    // ""
var p *int      // nil
var slice []int // nil
var m map[string]int // nil
```

---

## 复合类型

### 数组

```go
// 固定长度
var arr [5]int
arr := [5]int{1, 2, 3, 4, 5}
arr := [...]int{1, 2, 3}  // 编译器推断长度

// 访问
arr[0] = 10
len(arr)  // 长度
```

### 切片

```go
// 动态数组
var slice []int
slice := []int{1, 2, 3}
slice := make([]int, 5)      // len=5, cap=5
slice := make([]int, 0, 10)  // len=0, cap=10

// 操作
slice = append(slice, 4, 5)  // 追加
slice[1:3]                   // 切片
len(slice)                   // 长度
cap(slice)                   // 容量
copy(dst, src)               // 复制
```

### Map

```go
// 键值对
var m map[string]int
m := make(map[string]int)
m := map[string]int{"a": 1, "b": 2}

// 操作
m["c"] = 3              // 添加/更新
value := m["a"]         // 获取
value, ok := m["a"]     // 检查存在
delete(m, "a")          // 删除
len(m)                  // 长度
```

### 结构体

```go
type Person struct {
    Name string
    Age  int
}

// 创建
p := Person{Name: "Alice", Age: 30}
p := Person{"Alice", 30}
p := new(Person)  // 返回指针

// 访问
p.Name = "Bob"

// 匿名字段（嵌入）
type Employee struct {
    Person  // 嵌入
    Title string
}
e := Employee{Person{"Alice", 30}, "Engineer"}
e.Name  // 可以直接访问嵌入字段
```

---

## 控制结构

### if

```go
if x > 0 {
    // ...
} else if x < 0 {
    // ...
} else {
    // ...
}

// 带初始化语句
if err := doSomething(); err != nil {
    return err
}
```

### for

```go
// 基本for
for i := 0; i < 10; i++ {
    // ...
}

// while形式
for x > 0 {
    x--
}

// 无限循环
for {
    // ...
}

// range遍历
for i, v := range slice {
    fmt.Println(i, v)
}

for key, value := range m {
    fmt.Println(key, value)
}

for i, char := range "hello" {
    fmt.Println(i, char)  // char是rune
}
```

### switch

```go
switch x {
case 1:
    // ...
case 2, 3:
    // ...
default:
    // ...
}

// 无条件switch
switch {
case x > 0:
    // ...
case x < 0:
    // ...
}

// 类型switch
switch v := x.(type) {
case int:
    // ...
case string:
    // ...
}
```

---

## 函数

### 基本语法

```go
func add(a, b int) int {
    return a + b
}

// 多返回值
func divide(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

// 命名返回值
func split(sum int) (x, y int) {
    x = sum * 4 / 9
    y = sum - x
    return  // 裸return
}

// 可变参数
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}
sum(1, 2, 3, 4)
```

### 函数作为值

```go
// 函数类型
type Operation func(int, int) int

// 函数作为参数
func apply(op Operation, a, b int) int {
    return op(a, b)
}

// 匿名函数
add := func(a, b int) int { return a + b }

// 闭包
func counter() func() int {
    count := 0
    return func() int {
        count++
        return count
    }
}
c := counter()
c()  // 1
c()  // 2
```

### defer

```go
func readFile() {
    f, err := os.Open("file.txt")
    if err != nil {
        return
    }
    defer f.Close()  // 函数返回前执行
    
    // 使用文件...
}

// 多个defer按LIFO顺序执行
defer fmt.Println("1")
defer fmt.Println("2")
defer fmt.Println("3")
// 输出: 3, 2, 1
```

---

## 错误处理

### error接口

```go
type error interface {
    Error() string
}

// 创建错误
err := errors.New("something went wrong")
err := fmt.Errorf("invalid value: %d", value)

// 检查错误
if err != nil {
    return err
}
```

### 错误包装（Go 1.13+）

```go
// 包装错误
err := fmt.Errorf("failed to process: %w", originalErr)

// 解包错误
if errors.Is(err, os.ErrNotExist) {
    // 是文件不存在错误
}

var pathError *os.PathError
if errors.As(err, &pathError) {
    // 是PathError类型
}
```

### panic和recover

```go
// panic：致命错误
func mustDo() {
    panic("unexpected situation")
}

// recover：捕获panic
func safeCall() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered:", r)
        }
    }()
    mustDo()
}
```

---

## 包管理

### 包结构

```
myproject/
├── go.mod
├── main.go
└── pkg/
    └── utils/
        └── utils.go
```

### go.mod

```go
module github.com/user/myproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
)
```

### 常用命令

```bash
go mod init github.com/user/project  # 初始化模块
go mod tidy                           # 整理依赖
go get github.com/pkg/errors          # 添加依赖
go build                              # 编译
go run main.go                        # 运行
go test ./...                         # 测试
go fmt ./...                          # 格式化
```

---

## 总结

| 特性 | 说明 |
|------|------|
| 变量 | var声明或:=短声明 |
| 类型 | 静态类型，有零值 |
| 切片 | 动态数组，最常用 |
| Map | 内置哈希表 |
| 函数 | 多返回值、闭包 |
| 错误 | error接口、显式处理 |
| 包 | go mod管理依赖 |

Go语言简洁高效，是云原生时代的首选语言之一。

---

## 相关文章

- [下一篇：接口与面向对象](@/articles/golang/go-02-接口与面向对象.md)
