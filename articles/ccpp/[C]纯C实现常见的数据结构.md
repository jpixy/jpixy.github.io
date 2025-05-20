# 纯C实现常见的数据结构
在C语言中实现数据结构如数组、队列、链表、栈、堆、二叉树、平衡二叉树、红黑树和B+树是一个涉及多个层面的任务。由于篇幅限制，我将为每个数据结构提供一个简单的初始化函数的示例代码。请注意，这些示例仅用于演示目的，实际应用中可能需要更完整的错误处理和功能实现。

1. **数组**

```c
#define SIZE 10

int array[SIZE];
void initArray() {
    for (int i = 0; i < SIZE; i++) {
        array[i] = 0;
    }
}
```

2. **队列**

```c
#include <stdio.h>

#define MAX_SIZE 10

int queue[MAX_SIZE];
int front = 0;
int rear = -1;

void initQueue() {
    front = 0;
    rear = -1;
}
```

3. **单链表**

```c
struct Node {
    int data;
    struct Node* next;
};

struct Node* initSingleLinkedList() {
    return NULL;
}
```

4. **双链表**

```c
struct Node {
    int data;
    struct Node* prev;
    struct Node* next;
};

struct Node* initDoubleLinkedList() {
    return NULL;
}
```

5. **栈**

```c
#include <stdio.h>

#define MAX_SIZE 10

int stack[MAX_SIZE];
int top = -1;

void initStack() {
    top = -1;
}
```

6. **堆**

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int *array;
    int size;
    int capacity;
} MinHeap;

MinHeap* createMinHeap(int capacity) {
    MinHeap* minHeap = (MinHeap*)malloc(sizeof(MinHeap));
    minHeap->capacity = capacity;
    minHeap->size = 0;
    minHeap->array = (int*)malloc(minHeap->capacity * sizeof(int));
    return minHeap;
}

void initHeap(MinHeap* minHeap) {
    minHeap->size = 0;
}
```

7. **二叉树**

```c
struct TreeNode {
    int data;
    struct TreeNode *left, *right;
};

struct TreeNode* initBinaryTree() {
    return NULL;
}
```

8. **平衡二叉树（AVL树）**

```c
struct AVLNode {
    int data;
    struct AVLNode *left, *right;
    int height;
};

struct AVLNode* initAVLTree() {
    return NULL;
}
```

9. **红黑树**

```c
// 红黑树的实现相对复杂，通常需要定义颜色、旋转和重新着色的函数。
// 这里只提供一个结构体定义和初始化函数的框架。
typedef enum { RED, BLACK } Color;

struct RBTreeNode {
    int data;
    struct RBTreeNode *left, *right, *parent;
    Color color;
};

struct RBTreeNode* initRBTree() {
    return NULL;
}
```

10. **B+树**

```c
// B+树的实现非常复杂，涉及到节点的分裂和合并。
// 这里只提供一个结构体定义和初始化函数的框架。
#define MAX_KEYS 100

typedef struct Node {
    int keys[MAX_KEYS];
    struct Node *children[MAX_KEYS + 1];
    int n;
    int leaf;
} Node;

Node* initBPlusTree() {
    return NULL;
}
```

请注意，这些代码只是初始化函数的框架，实际的数据结构实现需要更多的函数来处理插入、删除、查找等操作，并且需要考虑内存分配、错误处理和边界条件。对于红黑树和B+树，由于它们的实现相对复杂，通常需要更多的辅助函数和复杂的逻辑来维护树的平衡和性质。

