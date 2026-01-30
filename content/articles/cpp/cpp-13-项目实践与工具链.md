+++
title = "13.C++项目实践与工具链"
date = 2026-01-19
description = "C++工程实践：CMake构建、单元测试、代码质量、包管理、CI/CD"
[taxonomies]
tags = ["C++", "CMake", "工程"]
+++

## CMake构建系统

### 基本结构

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

# 设置C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 添加可执行文件
add_executable(myapp 
    src/main.cpp
    src/utils.cpp
)

# 添加库
add_library(mylib STATIC
    src/lib.cpp
)

# 链接库
target_link_libraries(myapp PRIVATE mylib)
```

### 目录结构

```
project/
├── CMakeLists.txt
├── src/
│   ├── main.cpp
│   └── utils.cpp
├── include/
│   └── myproject/
│       └── utils.h
├── tests/
│   ├── CMakeLists.txt
│   └── test_utils.cpp
├── cmake/
│   └── FindXXX.cmake
└── build/
```

### 常用命令

```cmake
# 头文件路径
target_include_directories(myapp PUBLIC include)

# 编译选项
target_compile_options(myapp PRIVATE -Wall -Wextra)

# 编译定义
target_compile_definitions(myapp PRIVATE DEBUG_MODE)

# 查找包
find_package(Threads REQUIRED)
target_link_libraries(myapp PRIVATE Threads::Threads)

# 子目录
add_subdirectory(src)
add_subdirectory(tests)

# 安装
install(TARGETS myapp DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
```

### 构建命令

```bash
mkdir build && cd build
cmake ..
cmake --build .

# 指定构建类型
cmake -DCMAKE_BUILD_TYPE=Release ..

# 指定编译器
cmake -DCMAKE_CXX_COMPILER=clang++ ..

# 并行构建
cmake --build . -j8
```

---

## 单元测试

### Google Test

```cmake
# CMakeLists.txt
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.12.1
)
FetchContent_MakeAvailable(googletest)

add_executable(tests test_main.cpp)
target_link_libraries(tests gtest_main)

include(GoogleTest)
gtest_discover_tests(tests)
```

```cpp
// test_main.cpp
#include <gtest/gtest.h>

int add(int a, int b) { return a + b; }

TEST(AddTest, PositiveNumbers) {
    EXPECT_EQ(add(2, 3), 5);
    EXPECT_EQ(add(0, 0), 0);
}

TEST(AddTest, NegativeNumbers) {
    EXPECT_EQ(add(-1, -1), -2);
    EXPECT_EQ(add(-1, 1), 0);
}

// 测试夹具
class VectorTest : public ::testing::Test {
protected:
    void SetUp() override {
        v.push_back(1);
        v.push_back(2);
    }
    std::vector<int> v;
};

TEST_F(VectorTest, Size) {
    EXPECT_EQ(v.size(), 2);
}
```

### Catch2

```cpp
#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>

TEST_CASE("Vector operations", "[vector]") {
    std::vector<int> v;
    
    SECTION("push_back increases size") {
        v.push_back(1);
        REQUIRE(v.size() == 1);
    }
    
    SECTION("clear empties the vector") {
        v.push_back(1);
        v.clear();
        REQUIRE(v.empty());
    }
}
```

---

## 代码质量工具

### 静态分析

**clang-tidy**：
```bash
clang-tidy src/*.cpp -- -I include

# 配置文件 .clang-tidy
Checks: 'clang-analyzer-*,cppcoreguidelines-*,modernize-*'
```

**cppcheck**：
```bash
cppcheck --enable=all --std=c++17 src/
```

### 代码格式化

**clang-format**：
```bash
clang-format -i src/*.cpp

# 配置文件 .clang-format
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 100
```

### 地址检测

```bash
# AddressSanitizer
g++ -fsanitize=address -g program.cpp -o program

# ThreadSanitizer
g++ -fsanitize=thread -g program.cpp -o program

# UndefinedBehaviorSanitizer
g++ -fsanitize=undefined -g program.cpp -o program
```

### 代码覆盖率

```bash
# 编译时启用覆盖率
g++ --coverage -g program.cpp -o program

# 运行程序
./program

# 生成报告
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

---

## 包管理

### vcpkg

```bash
# 安装vcpkg
git clone https://github.com/Microsoft/vcpkg.git
./vcpkg/bootstrap-vcpkg.sh

# 安装包
./vcpkg install fmt nlohmann-json

# CMake集成
cmake -DCMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake ..
```

### Conan

```bash
# 安装conan
pip install conan

# conanfile.txt
[requires]
fmt/9.1.0
nlohmann_json/3.11.2

[generators]
cmake

# 安装依赖
conan install .
```

### FetchContent

```cmake
include(FetchContent)

FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0
)
FetchContent_MakeAvailable(fmt)

target_link_libraries(myapp PRIVATE fmt::fmt)
```

---

## 调试技巧

### GDB

```bash
# 编译时加-g
g++ -g program.cpp -o program

# 启动调试
gdb ./program

# 常用命令
(gdb) break main       # 设置断点
(gdb) run              # 运行
(gdb) next             # 下一步（不进入函数）
(gdb) step             # 下一步（进入函数）
(gdb) print var        # 打印变量
(gdb) backtrace        # 调用栈
(gdb) continue         # 继续执行
(gdb) watch var        # 监视变量
```

### 日志

```cpp
#include <spdlog/spdlog.h>

spdlog::info("Hello, {}!", "World");
spdlog::warn("This is a warning");
spdlog::error("Error: {}", error_code);

// 设置级别
spdlog::set_level(spdlog::level::debug);
```

---

## CI/CD配置

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure
      run: cmake -B build -DCMAKE_BUILD_TYPE=Release
    
    - name: Build
      run: cmake --build build -j$(nproc)
    
    - name: Test
      run: ctest --test-dir build --output-on-failure
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test

build:
  stage: build
  script:
    - cmake -B build
    - cmake --build build
  artifacts:
    paths:
      - build/

test:
  stage: test
  script:
    - cd build && ctest
```

---

## 项目模板

### 推荐结构

```
project/
├── CMakeLists.txt
├── README.md
├── LICENSE
├── .clang-format
├── .clang-tidy
├── .github/
│   └── workflows/
│       └── ci.yml
├── cmake/
│   └── ProjectConfig.cmake
├── include/
│   └── project/
│       ├── module1.hpp
│       └── module2.hpp
├── src/
│   ├── CMakeLists.txt
│   ├── module1.cpp
│   └── module2.cpp
├── tests/
│   ├── CMakeLists.txt
│   └── test_module1.cpp
├── examples/
│   └── example1.cpp
└── docs/
    └── README.md
```

### 根CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(BUILD_TESTS "Build tests" ON)
option(BUILD_EXAMPLES "Build examples" ON)

add_subdirectory(src)

if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()
```

---

## 总结

| 类别 | 工具 | 用途 |
|------|------|------|
| 构建 | CMake | 跨平台构建 |
| 测试 | GTest/Catch2 | 单元测试 |
| 分析 | clang-tidy | 静态分析 |
| 格式 | clang-format | 代码格式化 |
| 检测 | Sanitizers | 运行时检测 |
| 包管理 | vcpkg/Conan | 依赖管理 |
| 调试 | GDB | 调试器 |
| CI/CD | GitHub Actions | 持续集成 |

现代C++项目应该重视工程化，利用好这些工具提高代码质量和开发效率。
