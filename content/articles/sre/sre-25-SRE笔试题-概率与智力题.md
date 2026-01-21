+++
title = "25.SRE笔试题-概率与智力题"
date = 2026-01-21
description = "SRE/Quant面试概率与智力题：马尔可夫链、期望值计算、动态决策、经典智力题，详细解答"
[taxonomies]
tags = ["SRE", "面试", "概率", "智力题", "Quant"]
+++

## 概述

HFT公司（Jump Trading、Citadel、Two Sigma等）的SRE/Infra岗位常考概率和智力题，考察逻辑思维和数学建模能力。

**难度标记**：⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 困难

---

# 一、期望值计算

## 1. 掷骰子最大值期望 ⭐⭐

**题目**：掷n个骰子，求最大值的期望。

**解法**：

设 $X$ 为n个骰子的最大值，$P(X \leq k) = (\frac{k}{6})^n$

$$E[X] = \sum_{k=1}^{6} k \cdot P(X=k) = \sum_{k=1}^{6} k \cdot [P(X \leq k) - P(X \leq k-1)]$$

$$= \sum_{k=1}^{6} k \cdot [(\frac{k}{6})^n - (\frac{k-1}{6})^n]$$

**另一种方法**（更简洁）：
$$E[X] = \sum_{k=0}^{5} P(X > k) = \sum_{k=0}^{5} [1 - (\frac{k}{6})^n]$$

**Python计算**：
```python
def expected_max_dice(n, sides=6):
    """n个骰子最大值的期望"""
    total = 0
    for k in range(sides):
        # P(X > k) = 1 - P(X <= k) = 1 - (k/sides)^n
        total += 1 - (k / sides) ** n
    return total

# n=2: 4.472, n=3: 4.958, n=10: 5.666
```

**要点**：利用 $E[X] = \sum_{k=0}^{\infty} P(X > k)$ 对于非负整数随机变量。

---

## 2. 收集优惠券问题（Coupon Collector） ⭐⭐⭐

**题目**：有n种不同的优惠券，每次随机获得一张，期望多少次能集齐所有种类？

**解法**：

**核心思路**：将过程分解为n个阶段，每个阶段是独立的几何分布。

设已有 $i$ 种时，获得新种类的概率为 $p_i = \frac{n-i}{n}$

第 $i$ 阶段（从有 $i$ 种到有 $i+1$ 种）服从几何分布 $Geom(p_i)$

几何分布期望 = $\frac{1}{p_i} = \frac{n}{n-i}$

**总期望推导**：

$$E[T] = \sum_{i=0}^{n-1} \frac{n}{n-i} = \frac{n}{n} + \frac{n}{n-1} + \frac{n}{n-2} + ... + \frac{n}{1}$$

$$= n \cdot \left(\frac{1}{n} + \frac{1}{n-1} + ... + \frac{1}{1}\right) = n \sum_{j=1}^{n} \frac{1}{j} = n \cdot H_n$$

其中 $H_n = 1 + \frac{1}{2} + \frac{1}{3} + ... + \frac{1}{n}$ 是调和级数

**渐近近似**：$H_n \approx \ln(n) + \gamma$，其中 $\gamma \approx 0.5772$ 是欧拉常数

所以 $E[T] \approx n \ln(n) + 0.5772n$

**方差计算**：

各阶段独立，方差可加：
$$Var(T) = \sum_{i=0}^{n-1} \frac{1-p_i}{p_i^2} = \sum_{i=0}^{n-1} \frac{i \cdot n}{(n-i)^2} = n^2 \sum_{j=1}^{n} \frac{1}{j^2} - n \cdot H_n$$

$$\approx n^2 \cdot \frac{\pi^2}{6} \approx 1.645 n^2$$

**直觉理解**：
- 前几种很快：获得第1种只需1次
- 最后几种很慢：集齐最后1种期望需要n次
- 这就是为什么集卡游戏"最后一张总是集不齐"

**Python计算**：
```python
import math
import random

def coupon_collector_expected(n):
    """收集n种优惠券的期望次数"""
    return n * sum(1/i for i in range(1, n+1))

def coupon_collector_variance(n):
    """方差"""
    Hn = sum(1/i for i in range(1, n+1))
    Hn2 = sum(1/i**2 for i in range(1, n+1))
    return n**2 * Hn2 - n * Hn

def simulate_coupon_collector(n, trials=10000):
    """蒙特卡洛模拟验证"""
    results = []
    for _ in range(trials):
        collected = set()
        count = 0
        while len(collected) < n:
            collected.add(random.randint(0, n-1))
            count += 1
        results.append(count)
    return sum(results)/len(results), (sum((x-sum(results)/len(results))**2 for x in results)/len(results))

# n=10: E≈29.29次, Var≈122
# n=52: E≈236次 (收集扑克牌)
# n=100: E≈518.7次
```

**应用场景**：
- 估计随机采样覆盖率
- 负载均衡均匀性评估（多久所有服务器都被访问过）
- 集卡游戏期望花费
- 哈希表填充率分析

---

## 3. 连续成功问题 ⭐⭐

**题目**：抛硬币，期望多少次能连续出现k次正面？

**解法**：

设 $E_k$ 为达到连续k次正面的期望次数。

递推关系：
- 第一次如果是反面（概率1/2），浪费1次，重新开始
- 第一次是正面（概率1/2），继续，需要连续k-1次

$$E_k = \frac{1}{2}(1 + E_k) + \frac{1}{2}(1 + E_{k-1}')$$

其中 $E_{k-1}'$ 是已有1次正面后再连续k-1次的期望。

**完整推导**：

设 $E_k$ = 期望次数达到连续k次正面

$$E_k = 2 + 2E_{k-1} + ... = 2^{k+1} - 2$$

**验证**：
- k=1: $E_1 = 2$（期望2次出现一个正面，因为有一半是反面）
- k=2: $E_2 = 6$
- k=3: $E_3 = 14$

**通用公式**（成功概率为p）：
$$E_k = \frac{1-p^k}{p^k(1-p)}$$

对于公平硬币 p=0.5：$E_k = 2(2^k - 1) = 2^{k+1} - 2$

---

# 二、马尔可夫链

## 4. 醉汉回家问题 ⭐⭐

**题目**：醉汉从位置0出发，每步等概率向左(-1)或向右(+1)。问：
- 回到原点0的概率是多少？
- 期望多少步回到原点？

**解法**：

**a) 回到原点的概率**

一维随机游走，回到原点概率 = 1（必然回到）

**证明**：设从位置1回到0的概率为p，由对称性，从-1回到0也是p。
从0出发，$P(\text{回到0}) = \frac{1}{2} \cdot p + \frac{1}{2} \cdot p = p$

从1出发回到0：$p = \frac{1}{2} \cdot 1 + \frac{1}{2} \cdot p^2$（要么先到0，要么到2再回）

解得 $p = 1$

**b) 期望步数**

回到原点的期望步数 = **无穷大**

虽然概率为1会回来，但期望时间是无限的。

---

## 5. 蜜蜂蜂巢问题 ⭐⭐⭐

**题目**：蜜蜂在蜂巢中心，每步20%前进、50%不动、30%后退。问在蜂巢中的时间占比？

**解法**：

这是一个马尔可夫链问题，需要求稳态分布。

设位置为 $i = 0, 1, 2, ...$（0为中心/蜂巢）

转移概率：
- $P(i \to i+1) = 0.2$（前进）
- $P(i \to i) = 0.5$（不动）
- $P(i \to i-1) = 0.3$（后退），当 $i > 0$
- $P(0 \to 0) = 0.5 + 0.3 = 0.8$（在原点时不能后退）

**稳态方程**：
$\pi_i = 0.2\pi_{i-1} + 0.5\pi_i + 0.3\pi_{i+1}$

简化：$0.5\pi_i = 0.2\pi_{i-1} + 0.3\pi_{i+1}$

设 $\pi_i = \pi_0 \cdot r^i$，代入得：
$0.5r = 0.2 + 0.3r^2$

$0.3r^2 - 0.5r + 0.2 = 0$

$r = \frac{0.5 \pm \sqrt{0.25 - 0.24}}{0.6} = \frac{0.5 \pm 0.1}{0.6}$

$r = 1$ 或 $r = \frac{2}{3}$

取 $r = \frac{2}{3}$（保证概率和收敛）

$\pi_i = \pi_0 \cdot (\frac{2}{3})^i$

归一化：$\sum_{i=0}^{\infty} \pi_i = \pi_0 \cdot \frac{1}{1-2/3} = 3\pi_0 = 1$

$\pi_0 = \frac{1}{3}$

**答案**：蜜蜂在蜂巢中心的时间占比约 **33.3%**

---

## 6. 赌徒破产问题 ⭐⭐⭐

**题目**：赌徒有a元，每局赢1元概率p，输1元概率q=1-p。赢到N元或输光停止。求输光概率？

**解法**：

设 $P_i$ = 从i元开始最终输光的概率

**边界条件**：
- $P_0 = 1$（已经输光）
- $P_N = 0$（已经达标，不会输光）

**递推方程**：
$$P_i = p \cdot P_{i+1} + q \cdot P_{i-1}$$

（本局赢了变成i+1元，输了变成i-1元）

**求解过程**：

重排方程：$p \cdot P_{i+1} - P_i + q \cdot P_{i-1} = 0$

这是二阶线性差分方程。设 $P_i = r^i$，代入得特征方程：
$$p \cdot r^2 - r + q = 0$$

由于 $p + q = 1$：
$$p \cdot r^2 - r + (1-p) = 0$$

解得：$r_1 = 1$，$r_2 = \frac{q}{p}$

**Case 1: $p \neq q$（$r_1 \neq r_2$）**

通解：$P_i = A \cdot 1^i + B \cdot (\frac{q}{p})^i = A + B \cdot (\frac{q}{p})^i$

由边界条件：
- $P_0 = 1$：$A + B = 1$
- $P_N = 0$：$A + B \cdot (\frac{q}{p})^N = 0$

解得：
$$A = \frac{-(\frac{q}{p})^N}{1 - (\frac{q}{p})^N}, \quad B = \frac{1}{1 - (\frac{q}{p})^N}$$

$$P_i = \frac{(\frac{q}{p})^i - (\frac{q}{p})^N}{1 - (\frac{q}{p})^N}$$

**Case 2: $p = q = 0.5$（$r_1 = r_2 = 1$）**

重根情况，通解：$P_i = A + B \cdot i$

由边界条件：
- $P_0 = 1$：$A = 1$
- $P_N = 0$：$1 + B \cdot N = 0$ → $B = -\frac{1}{N}$

$$P_i = 1 - \frac{i}{N} = \frac{N - i}{N}$$

**数值例子**：

| 初始资金a | 目标N | p | 输光概率 |
|-----------|-------|---|----------|
| 10 | 100 | 0.50 | 90.0% |
| 10 | 100 | 0.51 | 66.6% |
| 10 | 100 | 0.49 | 98.3% |
| 50 | 100 | 0.50 | 50.0% |
| 90 | 100 | 0.50 | 10.0% |

**直觉理解**：
- 公平游戏(p=0.5)：输光概率 = (N-a)/N，即距离目标越远越容易输光
- 不公平游戏(p<0.5)：即使赢面只差1%，长期必输
- 这就是为什么赌场永远赢（庄家优势）

```python
import random

def gambler_ruin_prob(a, N, p=0.5):
    """从a元开始，目标N元，赢概率p，输光概率"""
    if abs(p - 0.5) < 1e-10:
        return (N - a) / N
    else:
        q = 1 - p
        r = q / p
        return (r**a - r**N) / (1 - r**N)

def simulate_gambler_ruin(a, N, p=0.5, trials=10000):
    """蒙特卡洛模拟验证"""
    ruins = 0
    for _ in range(trials):
        money = a
        while 0 < money < N:
            if random.random() < p:
                money += 1
            else:
                money -= 1
        if money == 0:
            ruins += 1
    return ruins / trials

def expected_duration(a, N, p=0.5):
    """期望游戏持续回合数"""
    if abs(p - 0.5) < 1e-10:
        return a * (N - a)
    else:
        q = 1 - p
        r = q / p
        return (a/(q-p)) - (N/(q-p)) * (1 - r**a) / (1 - r**N)

# 验证
# simulate_gambler_ruin(10, 100, 0.5) ≈ 0.90
```

**应用**：
- 交易系统风险管理：设定止损和止盈
- 凯利公式的理论基础
- 理解"长期来看庄家必赢"的数学原理

---

# 三、经典智力题

## 7. 生日悖论 ⭐⭐

**题目**：n个人中至少两人生日相同的概率是多少？多少人时概率超过50%？

**解法**：

所有人生日不同的概率：
$$P(\text{不同}) = \frac{365}{365} \cdot \frac{364}{365} \cdot \frac{363}{365} \cdots \frac{365-n+1}{365}$$

$$= \frac{365!}{(365-n)! \cdot 365^n}$$

至少两人相同：$P = 1 - P(\text{不同})$

```python
def birthday_paradox(n, days=365):
    """n人中有重复生日的概率"""
    if n > days:
        return 1.0
    prob_diff = 1.0
    for i in range(n):
        prob_diff *= (days - i) / days
    return 1 - prob_diff

# n=23: 50.7%
# n=50: 97%
# n=70: 99.9%
```

**关键结论**：只需23人，概率就超过50%

**近似公式**：$P \approx 1 - e^{-n^2/(2 \cdot 365)}$

---

## 8. 四球翻转问题 ⭐⭐⭐

**题目**：4个球，2黑2白。随机选2个翻转颜色，重复直到4球同色。期望次数？

**解法**：

**状态定义**：
- 状态A：2黑2白（初始状态）
- 状态B：4同色（终止状态）

从状态A选2个球：
- 选2黑：概率 $\frac{C_2^2}{C_4^2} = \frac{1}{6}$，翻转后变4白 → 状态B
- 选2白：概率 $\frac{1}{6}$，翻转后变4黑 → 状态B
- 选1黑1白：概率 $\frac{4}{6} = \frac{2}{3}$，翻转后仍是2黑2白 → 状态A

设 $E$ = 从状态A到达状态B的期望次数

$$E = 1 + \frac{1}{6} \cdot 0 + \frac{1}{6} \cdot 0 + \frac{2}{3} \cdot E$$

$$E = 1 + \frac{2}{3}E$$

$$\frac{1}{3}E = 1$$

$$E = 3$$

**答案**：期望 **3次**

---

## 9. 发牌问题（最优停止） ⭐⭐⭐

**题目**：52张牌（26红26黑），逐张发牌，可随时叫停。停止后翻开下一张牌，红牌赢黑牌输。最优策略是什么？期望赢的概率？

**解法**：

**状态定义**：$V(r, b)$ = 剩余r张红牌、b张黑牌时，采用最优策略的期望赢概率

**边界条件**：
- $V(r, 0) = 1$：只剩红牌，下一张必红，必赢
- $V(0, b) = 0$：只剩黑牌，下一张必黑，必输

**递推方程**：

在状态(r, b)时有两个选择：
1. **立即停止**：赢的概率 = $\frac{r}{r+b}$
2. **继续等待**：翻开一张牌
   - 概率 $\frac{r}{r+b}$ 翻到红牌，状态变为(r-1, b)
   - 概率 $\frac{b}{r+b}$ 翻到黑牌，状态变为(r, b-1)

$$V(r, b) = \max\left(\frac{r}{r+b}, \frac{r}{r+b} \cdot V(r-1, b) + \frac{b}{r+b} \cdot V(r, b-1)\right)$$

**最优策略推导**：

应该停止当且仅当：$\frac{r}{r+b} > \frac{r}{r+b} \cdot V(r-1, b) + \frac{b}{r+b} \cdot V(r, b-1)$

**关键定理**：当 $r > b$ 时应该停止，当 $r \leq b$ 时应该继续。

**证明思路**：
- 当 $r > b$：现在红牌比例高于50%，翻牌只会"平均化"比例
- 当 $r < b$：等待黑牌被消耗，比例会改善
- 当 $r = b$：停止和继续期望相同（对称性）

**策略表**（部分）：

| 红牌r | 黑牌b | 停止价值 | 继续价值 | 决策 |
|-------|-------|----------|----------|------|
| 3 | 1 | 0.750 | 0.708 | 停止 |
| 2 | 2 | 0.500 | 0.500 | 随意 |
| 1 | 3 | 0.250 | 0.292 | 继续 |
| 2 | 1 | 0.667 | 0.611 | 停止 |
| 1 | 2 | 0.333 | 0.389 | 继续 |

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def card_game_value(r, b):
    """剩余r红b黑时，最优策略的期望赢概率"""
    if b == 0:
        return 1.0
    if r == 0:
        return 0.0
    
    stop_now = r / (r + b)
    continue_play = (r / (r + b)) * card_game_value(r - 1, b) + \
                    (b / (r + b)) * card_game_value(r, b - 1)
    
    return max(stop_now, continue_play)

def optimal_decision(r, b):
    """返回最优决策"""
    if b == 0:
        return "STOP (WIN)"
    if r == 0:
        return "STOP (LOSE)"
    
    stop_value = r / (r + b)
    continue_value = (r / (r + b)) * card_game_value(r - 1, b) + \
                     (b / (r + b)) * card_game_value(r, b - 1)
    
    if stop_value > continue_value + 0.0001:
        return f"STOP (stop={stop_value:.3f} > cont={continue_value:.3f})"
    elif continue_value > stop_value + 0.0001:
        return f"CONTINUE (cont={continue_value:.3f} > stop={stop_value:.3f})"
    else:
        return f"INDIFFERENT ({stop_value:.3f})"

def simulate_optimal_strategy(trials=100000):
    """模拟验证最优策略"""
    import random
    wins = 0
    
    for _ in range(trials):
        deck = [1]*26 + [0]*26  # 1=红, 0=黑
        random.shuffle(deck)
        
        r, b = 26, 26
        for i, card in enumerate(deck[:-1]):  # 不能翻最后一张
            if card == 1:
                r -= 1
            else:
                b -= 1
            
            # 最优策略：r > b 时停止
            if r > b:
                # 停止，看下一张
                if deck[i + 1] == 1:
                    wins += 1
                break
        else:
            # 走到最后一张，必须停
            if deck[-1] == 1:
                wins += 1
    
    return wins / trials

# 初始期望
print(f"V(26,26) = {card_game_value(26, 26):.4f}")  # ≈ 0.5000

# 模拟验证
# simulate_optimal_strategy() ≈ 0.50
```

**结论**：
- 初始状态(26,26)的期望赢概率 = 0.5
- 最优策略很简单：红牌多就停，否则继续
- 虽然策略简单，但期望并不比随机停止好（都是0.5）

**变体问题**：如果赢了得1元，输了赔1元，期望收益是多少？
答：$E = 0.5 \times 1 + 0.5 \times (-1) = 0$，这是公平游戏

---

## 10. 帽子问题（Derangement） ⭐⭐

**题目**：n个人随机戴帽子，没人戴对的概率？

**解法**：

错排数公式：$D_n = n! \sum_{k=0}^{n} \frac{(-1)^k}{k!}$

$$P(\text{全错}) = \frac{D_n}{n!} = \sum_{k=0}^{n} \frac{(-1)^k}{k!} \to \frac{1}{e} \approx 0.368$$

```python
import math

def derangement_prob(n):
    """n个人全部戴错的概率"""
    return sum((-1)**k / math.factorial(k) for k in range(n+1))

# n=5: 0.3667, n=10: 0.3679, n→∞: 1/e = 0.3679
```

**结论**：n≥5时，概率约为 $\frac{1}{e} \approx 36.8\%$

---

# 四、条件概率与贝叶斯

## 11. 三门问题（Monty Hall） ⭐

**题目**：三扇门后有一辆车两只羊。你选一扇门，主持人打开另一扇有羊的门，问换门是否有利？

**答案**：**换！** 换的赢概率是 $\frac{2}{3}$，不换是 $\frac{1}{3}$

**直觉理解**：
- 初始选中车的概率 = 1/3
- 初始选中羊的概率 = 2/3
- 如果初始选羊（2/3概率），换门必得车

---

## 12. 两个孩子问题 ⭐⭐

**题目**：已知一家有两个孩子，至少一个是男孩。两个都是男孩的概率？

**解法**：

样本空间：{BB, BG, GB, GG}
已知"至少一个男孩"排除GG
条件样本空间：{BB, BG, GB}

$$P(\text{两男} | \text{至少一男}) = \frac{1}{3}$$

**注意**：如果题目是"大的是男孩"，则：
条件样本空间：{BB, BG}
$$P = \frac{1}{2}$$

---

## 13. 检测问题（贝叶斯） ⭐⭐

**题目**：疾病患病率1%，检测灵敏度99%，假阳率5%。检测阳性时，真正患病概率？

**解法**：

贝叶斯公式：
$$P(病|阳) = \frac{P(阳|病) \cdot P(病)}{P(阳)}$$

$$P(阳) = P(阳|病)P(病) + P(阳|健)P(健)$$
$$= 0.99 \times 0.01 + 0.05 \times 0.99 = 0.0099 + 0.0495 = 0.0594$$

$$P(病|阳) = \frac{0.99 \times 0.01}{0.0594} = \frac{0.0099}{0.0594} \approx 16.7\%$$

**结论**：即使检测阳性，真正患病概率只有约17%

---

# 五、其他经典问题

## 14. 100囚犯与灯泡 ⭐⭐⭐

**题目**：100个囚犯，一个房间有一盏灯（初始状态未知）。每天随机选一人进入房间，可以开/关灯或不操作。在某个时刻，某个囚犯必须宣布"所有人都已进入过房间"。如果宣布时确实如此则全部释放，否则全部处死。设计策略。

**策略1：基础策略（单计数员）**

1. 事先约定：指定1号囚犯为"计数员"，其他99人为"普通人"
2. **灯的初始状态处理**：假设初始为灭（或第一次所有人都不操作，等计数员先确定状态）
3. **普通人规则**：
   - 如果是**第一次**看到灯**灭**→开灯
   - 其他情况不操作
4. **计数员规则**：
   - 如果看到灯**亮**→关灯，计数+1
   - 看到灯灭→不操作
5. **终止条件**：计数员数到99时宣布

**正确性证明**：
- 每个普通人最多开灯1次
- 计数员每次关灯对应一个不同的人开灯
- 数到99意味着99个普通人都至少来过一次
- 计数员自己也来过→100人都来过

**期望时间计算**：

这分为两个阶段：
1. 等待计数员来确定初始状态
2. 等待99个普通人各开灯一次，且计数员来关灯

设 $T$ = 总期望时间

**阶段分析**：
- 等第 $i$ 个新普通人开灯：期望等 $\frac{100}{100-i+1}$ 天（该人来）
- 之后等计数员来关灯：期望 $100$ 天

粗略估计：
$$E[T] \approx 100 \times 99 + 100 \times \ln(99) \times 100 \approx 10000 + 46000 \approx 10000$$

**更精确**：约 **10,417 天**（约28.5年）

**策略2：改进策略（多轮计数）**

1. 第一轮：每人开灯1次，计数员数到99
2. 第二轮：每人再开灯1次，计数员再数到99
3. ...重复直到某轮计数员数到99时自己也来过多次

这可以处理初始状态未知的问题，期望时间约 **10,500 天**

**策略3：更优策略（分层计数）**

指定10个"小计数员"，各负责9个人，再有1个"大计数员"。
- 期望时间可降至约 **3,500 天**

```python
import random

def simulate_prisoners(n=100, trials=1000):
    """模拟基础策略"""
    total_days = 0
    
    for _ in range(trials):
        light_on = False
        counter_count = 0
        has_turned_on = [False] * n  # has_turned_on[0]是计数员，不用
        days = 0
        
        while counter_count < n - 1:
            days += 1
            prisoner = random.randint(0, n - 1)
            
            if prisoner == 0:  # 计数员
                if light_on:
                    light_on = False
                    counter_count += 1
            else:  # 普通人
                if not has_turned_on[prisoner] and not light_on:
                    light_on = True
                    has_turned_on[prisoner] = True
        
        total_days += days
    
    return total_days / trials

# simulate_prisoners() ≈ 10417
```

**关键考点**：
- 理解为什么需要"单向通信"（只能通过灯传递信息）
- 分析正确性：计数员如何确保不重复计数
- 估算期望时间的数量级

---

## 15. 称重问题 ⭐⭐

**题目**：8个球，1个较重，用天平称2次找出。

**解法**：

1. 第一次：3个 vs 3个
   - 如果平衡：重球在剩余2个中，再称1次
   - 如果不平衡：重球在重的3个中
   
2. 第二次：从可疑的3个中取1个 vs 1个
   - 平衡：第三个重
   - 不平衡：重的那个

**推广**：n次称重最多区分 $3^n$ 个球

---

## Python模拟验证

```python
import random

def simulate_birthday_paradox(n, trials=10000):
    """模拟验证生日悖论"""
    hits = 0
    for _ in range(trials):
        birthdays = [random.randint(1, 365) for _ in range(n)]
        if len(birthdays) != len(set(birthdays)):
            hits += 1
    return hits / trials

def simulate_four_balls(trials=10000):
    """模拟4球翻转"""
    total_steps = 0
    for _ in range(trials):
        balls = [0, 0, 1, 1]  # 0黑1白
        steps = 0
        while len(set(balls)) > 1:  # 不是全同色
            # 随机选2个位置
            i, j = random.sample(range(4), 2)
            balls[i] = 1 - balls[i]
            balls[j] = 1 - balls[j]
            steps += 1
        total_steps += steps
    return total_steps / trials

# simulate_birthday_paradox(23) ≈ 0.507
# simulate_four_balls() ≈ 3.0
```

---

## 解题技巧总结

| 题型 | 方法 |
|------|------|
| 期望值 | $E[X] = \sum P(X > k)$ 或分解为独立阶段 |
| 马尔可夫链 | 建立状态转移，求稳态或首达时间 |
| 组合概率 | 先求补集或条件概率 |
| 动态决策 | 倒推，比较停止vs继续的期望 |
| 智力题 | 找不变量、对称性、递归结构 |
