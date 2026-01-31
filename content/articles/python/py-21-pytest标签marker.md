+++
title = "21.pytest标签marker详解与使用指南"
slug = "py-pytest标签marker详解与使用指南"
+++

# Python pytest 标签(marker)详解与使用指南
pytest 的标记(marker)系统是一个强大的功能，允许你为测试函数或类添加元数据，从而实现对测试的灵活分类、筛选和特殊处理。

## 一、pytest 标记基础
### 1. 基本标记语法
```python
import pytest

@pytest.mark.slow
def test_something_slow():
    pass

@pytest.mark.ui
@pytest.mark.smoke
def test_login_page():
    pass
```

### 2. 内置标记
| 标记 | 用途 |
| --- | --- |
| `@pytest.mark.skip` | 跳过测试 |
| `@pytest.mark.skipif` | 条件跳过 |
| `@pytest.mark.xfail` | 预期失败 |
| `@pytest.mark.parametrize` | 参数化测试 |
| `@pytest.mark.usefixtures` | 使用fixture |


## 二、自定义标记
### 1. 注册自定义标记
在 `pytest.ini` 文件中注册标记以避免警告：

```properties
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    smoke: marks tests as smoke tests
    ui: marks tests that interact with user interface
    network: marks tests that require network access
```

### 2. 使用自定义标记
```python
@pytest.mark.smoke
def test_essential_feature():
    assert True

@pytest.mark.ui
class TestUserInterface:
    def test_button_click(self):
        pass
```

## 三、标记的高级用法
### 1. 组合标记
```python
@pytest.mark.slow
@pytest.mark.network
def test_api_performance():
    pass
```

### 2. 标记与参数化结合
```python
@pytest.mark.parametrize("input,expected", [(1, 2), (3, 4)])
@pytest.mark.fast
def test_increment(input, expected):
    assert input + 1 == expected
```

### 3. 类级别标记
```python
@pytest.mark.integration
class TestIntegration:
    def test_database(self):
        pass
    
    def test_external_service(self):
        pass
```

## 四、基于标记的测试筛选
### 1. 运行特定标记的测试
```bash
pytest -m smoke  # 只运行smoke标记的测试
pytest -m "not slow"  # 运行非slow标记的测试
pytest -m "ui and not slow"  # 运行ui标记但非slow的测试
pytest -m "smoke or ui"  # 运行smoke或ui标记的测试
```

### 2. 列出所有标记
```bash
pytest --markers
```

## 五、标记与fixture结合
```python
@pytest.fixture
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()

@pytest.mark.database
def test_query(db_connection):
    result = db_connection.execute("SELECT 1")
    assert result == 1
```

## 六、标记最佳实践
1. **标记命名**：
    - 使用小写字母和下划线
    - 保持名称简洁但具有描述性
    - 避免使用pytest内置标记名
2. **标记文档**：
    - 在 `pytest.ini` 中为每个标记添加描述
    - 在项目文档中记录标记的使用约定
3. **标记粒度**：
    - 不要过度使用标记
    - 每个标记应有明确的用途
    - 考虑标记的层次结构（如 `smoke` > `api` > `v2`）
4. **CI/CD集成**：

```yaml
# 示例GitHub Actions配置
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        marker: [smoke, ui, integration]
    steps:
      - run: pytest -m ${{ matrix.marker }}
```

## 七、常见问题解决
### 1. 未注册标记警告
```
PytestUnknownMarkWarning: Unknown pytest.mark.slow - is this a typo?
```

**解决**：在 `pytest.ini` 中注册标记

### 2. 标记不生效
**检查**：

+ 确保标记拼写正确
+ 确认测试发现包含目标文件
+ 检查标记筛选表达式是否正确

### 3. 标记冲突
**建议**：建立标记命名规范，如：

+ `fast`/`slow` 表示执行速度
+ `unit`/`integration`/`e2e` 表示测试类型
+ `smoke`/`regression` 表示测试级别

## 八、实际应用示例
### 1. 环境特定测试
```python
@pytest.mark.production_only
def test_production_feature():
    if os.getenv("ENV") != "production":
        pytest.skip("This test runs only in production")
```

### 2. 平台特定测试
```python
@pytest.mark.linux_only
def test_linux_command():
    if sys.platform != "linux":
        pytest.skip("Linux only test")
```

### 3. 测试分类执行
```bash
# 开发时快速运行
pytest -m "not slow and not integration"

# CI完整运行
pytest -m "not nightly"

# 夜间构建
pytest -m nightly
```

pytest 的标记系统为测试组织提供了极大的灵活性，合理使用可以显著提高测试效率和管理能力。通过定义清晰的标记策略，团队可以更有效地控制测试执行流程，适应不同的测试场景和需求。

---

## 相关文章

- [上一篇：Python的高级技巧](/articles/python/py-20-高级技巧/)
- [下一篇：理解编程中的栈和堆](/articles/python/py-22-理解栈和堆/)
