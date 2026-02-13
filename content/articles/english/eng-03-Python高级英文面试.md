+++
title = "03. Python高级知识英文面试"
slug = "eng-Py高级知识英文面试"
weight = 3000
+++

# eng Py高级知识英文面试

Here are 45 advanced Python Q&A pairs tailored for technical interviews, using accurate and natural English:

### Core Python Concepts
1. **Q: Explain Python's GIL and its impact on multi-threading.**  
A: The Global Interpreter Lock (GIL) is a mutex that allows only one thread to execute Python bytecode at a time. While it simplifies memory management, it limits true parallel execution in CPU-bound multi-threaded programs, making multi-processing preferable for CPU-intensive tasks.
2. **Q: How does Python's memory management work?**  
A: Python uses private heaps with an automatic garbage collector (reference counting + generational GC). The `__del__` method provides finalization, but cyclic references require the generational collector which uses mark-and-sweep.
3. **Q: Compare **`__new__`** vs **`__init__`** in Python.**  
A: `__new__` is a static method responsible for object creation (returns instance), while `__init__` initializes the created instance (returns None). `__new__` is called before `__init__`.

### Advanced Language Features
4. **Q: What are Python's metaclasses and when would you use them?**  
A: Metaclasses (subclasses of `type`) control class creation. Used for API enforcement, ORM development, or automatic method generation. Example: `class Meta(type):` then `class Foo(metaclass=Meta):`
5. **Q: Explain Python's descriptor protocol.**  
A: Descriptors (`__get__`, `__set__`, `__delete__`) enable managed attributes. Used in `@property`, class methods, and ORM fields. Example: A descriptor can validate values before assignment.
6. **Q: How do context managers work under the hood?**  
A: They implement `__enter__` and `__exit__` methods. The `with` statement calls `__enter__` for setup and guarantees `__exit__` execution (even during exceptions) for cleanup.

### Concurrency & Performance
7. **Q: Compare threading vs multiprocessing vs asyncio.**  
A: Threading uses OS threads (GIL-limited). Multiprocessing uses separate processes (true parallelism). Asyncio uses single-threaded cooperative multitasking with async/await syntax for IO-bound tasks.
8. **Q: How would you optimize Python performance?**  
A: Profile with cProfile, use built-in functions, leverage C extensions (Cython), implement hot paths in C, use generators for memory efficiency, and consider PyPy for JIT compilation.
9. **Q: Explain how asyncio's event loop works.**  
A: The event loop manages an asynchronous queue of coroutines, executing them when their awaited operations complete. It uses cooperative scheduling via `await` points and selectors for IO readiness.

### OOP & Design Patterns
10. **Q: Implement the Singleton pattern in Python.**  
A: 

```python
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

11. **Q: How would you implement an immutable class?**  
A: Override `__setattr__` and `__delattr__` to raise AttributeError, use `__slots__`, and return copies of mutable attributes. Inherit from `typing.NamedTuple` for simple cases.
12. **Q: Explain the MRO (Method Resolution Order) in Python.**  
A: MRO determines method lookup order in inheritance hierarchies using the C3 linearization algorithm. Viewable via `Class.__mro__`. Ensures monotonicity and respects superclass order.

### Advanced Techniques
13. **Q: What are Python's weak references?**  
A: `weakref` references don't prevent garbage collection. Useful for caches, observer patterns, or avoiding circular references. Example: `weakref.proxy(obj)`.
14. **Q: How would you implement a custom sequence type?**  
A: Implement the sequence protocol: `__getitem__`, `__len__`, and optionally `__contains__`, `__reversed__`. For mutable sequences, add `__setitem__`, `__delitem__`.
15. **Q: Explain monkey patching in Python.**  
A: Dynamically modifying classes/modules at runtime (e.g., adding methods). Powerful but risky as it breaks encapsulation. Common in testing (mocks) or fixing third-party code.

### Decorators & Metaprogramming
16. **Q: Create a parameterized decorator that retries failed functions.**  
A: 

```python
def retry(max_tries):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    pass
            raise RuntimeError("Max retries exceeded")
        return wrapper
    return decorator
```

17. **Q: How would you implement a class decorator?**  
A: A class decorator accepts a class and returns a modified class:

```python
def debug_methods(cls):
    for name, method in cls.__dict__.items():
        if callable(method):
            setattr(cls, name, debug_wrapper(method))
    return cls
```

### Testing & Debugging
18. **Q: How do you mock in Python tests?**  
A: Use `unittest.mock`:

```python
with patch('module.ClassName') as MockClass:
    instance = MockClass.return_value
    instance.method.return_value = False
    assert not module.function_under_test()
```

19. **Q: Explain how to debug memory leaks in Python.**  
A: Use `tracemalloc` to track allocations, `gc` module to inspect reference cycles, and `objgraph` to visualize object references. Check for unclosed resources and caches.

### Data Structures & Algorithms
20. **Q: Implement an LRU cache from scratch.**  
A: Combine a doubly-linked list (for order) with a dictionary (for O(1) access):

```python
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.head, self.tail = DLinkedNode(), DLinkedNode()
        self.head.next, self.tail.prev = self.tail, self.head
```

21. **Q: How would you efficiently find duplicates in a large dataset?**  
A: For memory efficiency, use generators and probabilistic data structures like Bloom filters. For speed, use hash sets with chunked processing if memory-constrained.

### Python Internals
22. **Q: How are Python dictionaries implemented?**  
A: As resizable hash tables with open addressing. Since Python 3.6, they maintain insertion order using a hidden array of indices. Average O(1) for lookups.
23. **Q: Explain Python's bytecode compilation process.**  
A: Source → Parse Tree → Abstract Syntax Tree → Control Flow Graph → Bytecode (`.pyc` files). View with `dis` module. Optimizations include constant folding and peephole optimizations.

### Functional Programming
24. **Q: Demonstrate functools.partial usage.**  
A: 

```python
from functools import partial
def power(base, exp): return base ** exp
square = partial(power, exp=2)
square(5)  # 25
```

25. **Q: How would you implement tail recursion in Python?**  
A: Python doesn't optimize tail recursion natively, but you can use a trampoline:

```python
def trampoline(f):
    def wrapped(*args):
        result = f(*args)
        while callable(result):
            result = result()
        return result
    return wrapped
```

### Advanced Libraries
26. **Q: How does NumPy achieve performance with Python?**  
A: By using contiguous memory blocks, vectorized operations in C, and avoiding Python interpreter overhead for inner loops. Broadcasting enables efficient array operations.
27. **Q: Explain how asyncio's Task differs from a coroutine.**  
A: A coroutine is a generator-based async function. A Task wraps a coroutine in the event loop, scheduling its execution and managing its state (pending/running/done).

### Security
28. **Q: What security risks exist in Python's pickle module?**  
A: Pickle can execute arbitrary code during deserialization. Never unpickle untrusted data. Use JSON or other serialization for untrusted sources.
29. **Q: How would you securely handle passwords in Python?**  
A: Use `passlib` or `bcrypt` with proper hashing (PBKDF2, Argon2), never store plaintext, and compare with constant-time functions to prevent timing attacks.

### Advanced Topics
30. **Q: Explain Python's data model and magic methods.**  
A: The data model defines object behavior via special methods (dunder methods). Examples: `__len__` enables `len()`, `__getitem__` enables indexing, `__enter__/__exit__` enable context managers.
31. **Q: How would you implement a Python C extension?**  
A: Using Python's C API or tools like Cython:

```c
#include <Python.h>
static PyObject* spam(PyObject* self) {
    return PyLong_FromLong(42);
}
```

32. **Q: What are Python's variable annotations?**  
A: Type hints introduced in Python 3.6+: `x: int = 5`. Used by static type checkers (mypy) without runtime enforcement. Part of PEP 484 type system.
33. **Q: How does Python's garbage collector handle cycles?**  
A: The generational GC (gc module) periodically runs mark-and-sweep to detect and collect cyclic references unreachable from root objects.
34. **Q: Explain Python's import system.**  
A: The importer searches sys.path for modules. `import` triggers bytecode compilation (`__pycache__`), executes the module body, and creates a namespace. Hooks can customize behavior via importlib.
35. **Q: How would you implement a thread-safe queue?**  
A: Use `queue.Queue` (implements all locking internally) or `collections.deque` with `threading.Lock` for custom implementations.
36. **Q: What are Python's abstract base classes (ABCs)?**  
A: Defined in `collections.abc`, they formalize interfaces (e.g., `Sequence`, `Mapping`). Use `@abstractmethod` to create your own ABCs that enforce method implementation.
37. **Q: Demonstrate a Python coroutine with async/await.**  
A: 

```python
async def fetch(url):
    response = await aiohttp.request('GET', url)
    return await response.text()
```

38. **Q: How would you implement a custom exception hierarchy?**  
A: Derive from Exception or appropriate built-in exceptions:

```python
class AppError(Exception): pass
class ValidationError(AppError): pass
```

39. **Q: Explain Python's buffer protocol.**  
A: Low-level API for memory sharing between objects (e.g., NumPy arrays). Objects expose raw memory through `__buffer__` interface, avoiding copies.
40. **Q: How would you implement a Python WSGI server?**  
A: 

```python
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Hello World']
```

41. **Q: What are Python's slots and when are they useful?**  
A: `__slots__` optimizes memory by pre-declaring attributes (no `__dict__`). Useful when creating many instances. Limits dynamic attributes but reduces memory overhead.
42. **Q: How would you implement a Python iterator?**  
A: Implement `__iter__` (returns self) and `__next__` (returns items or raises StopIteration):

```python
class Count:
    def __init__(self, limit): self.n = 0; self.limit = limit
    def __next__(self):
        if self.n >= self.limit: raise StopIteration
        self.n += 1; return self.n
```

43. **Q: Explain Python's method resolution order (MRO).**  
A: MRO determines the search order for attributes in inheritance hierarchies. For `class D(B, C)`, Python uses C3 linearization: D → B → C → object.
44. **Q: How would you implement a Python generator?**  
A: Use `yield` to produce values while maintaining state between calls:

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
```

45. **Q: What are Python's context variables?**  
A: Introduced in Python 3.7, `contextvars` provide thread-local-like storage that works with asyncio. Each task maintains its own context copy.

These questions cover advanced Python concepts while maintaining natural interview language. They progress from core concepts to specialized topics, testing both theoretical knowledge and practical implementation skills.

---

## 相关文章

- [上一篇：Python基础知识英文面试](@/articles/english/eng-02-Python基础英文面试.md)
- [下一篇：AI相关英文](@/articles/english/eng-04-AI相关英文.md)
