+++
title = "52. 期权定价与Greeks详解"
date = 2026-02-02
weight = 52000
description = "期权定价模型：Black-Scholes、二叉树、Greeks、对冲策略"
[taxonomies]
tags = ["HFT", "期权", "Greeks", "Black-Scholes", "衍生品"]
+++

# 期权定价与 Greeks 详解

本文深入讲解期权定价理论，包括 Black-Scholes 模型、二叉树模型、Greeks 计算和对冲策略。

---

## 一、期权基础

### 1.1 期权类型

| 类型 | 描述 | 收益（到期时） |
|------|------|----------------|
| 欧式看涨 | 到期日买入标的 | max(S - K, 0) |
| 欧式看跌 | 到期日卖出标的 | max(K - S, 0) |
| 美式期权 | 任意时间行权 | 更复杂 |
| 亚式期权 | 平均价格 | 取决于路径 |
| 障碍期权 | 触碰障碍失效/生效 | 路径依赖 |

### 1.2 期权价值分解

```mermaid
graph TD
    subgraph "期权价值"
        VALUE[期权价值]
        INTRINSIC[内在价值<br/>max(S-K, 0)]
        TIME[时间价值<br/>期权价值 - 内在价值]
    end
    
    VALUE --> INTRINSIC
    VALUE --> TIME
    
    subgraph "影响因素"
        S[标的价格 S]
        K[执行价 K]
        T[到期时间 T]
        R[无风险利率 r]
        SIGMA[波动率 σ]
        D[股息 q]
    end
    
    S --> VALUE
    K --> VALUE
    T --> VALUE
    R --> VALUE
    SIGMA --> VALUE
    D --> VALUE
```

---

## 二、Black-Scholes 模型

### 2.1 模型假设

1. 标的价格服从几何布朗运动
2. 无风险利率恒定
3. 无交易成本和税收
4. 可以连续交易
5. 无套利机会
6. 波动率恒定

### 2.2 Black-Scholes 公式

$$
C = S_0 N(d_1) - K e^{-rT} N(d_2)
$$

$$
P = K e^{-rT} N(-d_2) - S_0 N(-d_1)
$$

其中：

$$
d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}
$$

$$
d_2 = d_1 - \sigma\sqrt{T}
$$

### 2.3 实现代码

```cpp
#include <cmath>
#include <algorithm>

class BlackScholes {
public:
    // 标准正态分布 CDF
    static double norm_cdf(double x) {
        return 0.5 * std::erfc(-x / std::sqrt(2.0));
    }
    
    // 标准正态分布 PDF
    static double norm_pdf(double x) {
        return std::exp(-0.5 * x * x) / std::sqrt(2.0 * M_PI);
    }
    
    // 计算 d1 和 d2
    static std::pair<double, double> calc_d1_d2(
        double S, double K, double r, double q, double sigma, double T) {
        
        double d1 = (std::log(S / K) + (r - q + 0.5 * sigma * sigma) * T) /
                    (sigma * std::sqrt(T));
        double d2 = d1 - sigma * std::sqrt(T);
        
        return {d1, d2};
    }
    
    // 欧式看涨期权价格
    static double call_price(double S, double K, double r, double q,
                            double sigma, double T) {
        if (T <= 0) return std::max(S - K, 0.0);
        
        auto [d1, d2] = calc_d1_d2(S, K, r, q, sigma, T);
        
        return S * std::exp(-q * T) * norm_cdf(d1) -
               K * std::exp(-r * T) * norm_cdf(d2);
    }
    
    // 欧式看跌期权价格
    static double put_price(double S, double K, double r, double q,
                           double sigma, double T) {
        if (T <= 0) return std::max(K - S, 0.0);
        
        auto [d1, d2] = calc_d1_d2(S, K, r, q, sigma, T);
        
        return K * std::exp(-r * T) * norm_cdf(-d2) -
               S * std::exp(-q * T) * norm_cdf(-d1);
    }
    
    // Put-Call 平价验证
    static bool verify_put_call_parity(double C, double P, double S,
                                       double K, double r, double q, double T) {
        double lhs = C - P;
        double rhs = S * std::exp(-q * T) - K * std::exp(-r * T);
        return std::abs(lhs - rhs) < 1e-10;
    }
};
```

---

## 三、Greeks

### 3.1 Greeks 定义

| Greek | 符号 | 定义 | 含义 |
|-------|------|------|------|
| Delta | Δ | ∂V/∂S | 标的价格变化敏感度 |
| Gamma | Γ | ∂²V/∂S² | Delta 的变化率 |
| Theta | Θ | ∂V/∂t | 时间衰减 |
| Vega | ν | ∂V/∂σ | 波动率敏感度 |
| Rho | ρ | ∂V/∂r | 利率敏感度 |

### 3.2 Greeks 公式

**看涨期权**：

$$
\Delta_c = e^{-qT} N(d_1)
$$

$$
\Gamma = \frac{e^{-qT} N'(d_1)}{S \sigma \sqrt{T}}
$$

$$
\Theta_c = -\frac{S \sigma e^{-qT} N'(d_1)}{2\sqrt{T}} - rKe^{-rT}N(d_2) + qSe^{-qT}N(d_1)
$$

$$
\nu = S e^{-qT} N'(d_1) \sqrt{T}
$$

$$
\rho_c = KT e^{-rT} N(d_2)
$$

### 3.3 Greeks 实现

```cpp
struct Greeks {
    double delta;
    double gamma;
    double theta;
    double vega;
    double rho;
    
    // 高阶 Greeks
    double vanna;    // ∂Delta/∂σ
    double volga;    // ∂²V/∂σ² (Vomma)
    double charm;    // ∂Delta/∂t
    double speed;    // ∂Gamma/∂S
};

class GreeksCalculator {
public:
    static Greeks calculate(double S, double K, double r, double q,
                           double sigma, double T, bool is_call) {
        Greeks g;
        
        auto [d1, d2] = BlackScholes::calc_d1_d2(S, K, r, q, sigma, T);
        
        double sqrt_T = std::sqrt(T);
        double exp_qT = std::exp(-q * T);
        double exp_rT = std::exp(-r * T);
        double n_d1 = BlackScholes::norm_cdf(d1);
        double n_d2 = BlackScholes::norm_cdf(d2);
        double nprime_d1 = BlackScholes::norm_pdf(d1);
        
        // Delta
        if (is_call) {
            g.delta = exp_qT * n_d1;
        } else {
            g.delta = -exp_qT * BlackScholes::norm_cdf(-d1);
        }
        
        // Gamma（Call 和 Put 相同）
        g.gamma = exp_qT * nprime_d1 / (S * sigma * sqrt_T);
        
        // Theta
        double common_theta = -S * sigma * exp_qT * nprime_d1 / (2 * sqrt_T);
        if (is_call) {
            g.theta = common_theta - r * K * exp_rT * n_d2 + q * S * exp_qT * n_d1;
        } else {
            g.theta = common_theta + r * K * exp_rT * BlackScholes::norm_cdf(-d2) -
                     q * S * exp_qT * BlackScholes::norm_cdf(-d1);
        }
        g.theta /= 365.0;  // 每日 theta
        
        // Vega（Call 和 Put 相同）
        g.vega = S * exp_qT * nprime_d1 * sqrt_T / 100.0;  // 1% 波动率变化
        
        // Rho
        if (is_call) {
            g.rho = K * T * exp_rT * n_d2 / 100.0;  // 1% 利率变化
        } else {
            g.rho = -K * T * exp_rT * BlackScholes::norm_cdf(-d2) / 100.0;
        }
        
        // 高阶 Greeks
        g.vanna = -exp_qT * nprime_d1 * d2 / sigma;
        g.volga = S * exp_qT * nprime_d1 * sqrt_T * d1 * d2 / sigma;
        g.charm = q * exp_qT * n_d1 - exp_qT * nprime_d1 *
                  (2 * (r - q) * T - d2 * sigma * sqrt_T) / (2 * T * sigma * sqrt_T);
        g.speed = -g.gamma / S * (d1 / (sigma * sqrt_T) + 1);
        
        return g;
    }
    
    // 数值 Greeks（用于验证或复杂期权）
    static Greeks calculate_numerical(
        std::function<double(double, double, double, double, double, double)> pricer,
        double S, double K, double r, double q, double sigma, double T,
        double dS = 0.01, double dSigma = 0.01, double dT = 1.0/365, double dR = 0.01) {
        
        Greeks g;
        
        double V = pricer(S, K, r, q, sigma, T);
        double V_up = pricer(S + dS, K, r, q, sigma, T);
        double V_down = pricer(S - dS, K, r, q, sigma, T);
        
        // Delta（中心差分）
        g.delta = (V_up - V_down) / (2 * dS);
        
        // Gamma
        g.gamma = (V_up - 2 * V + V_down) / (dS * dS);
        
        // Theta
        double V_T = pricer(S, K, r, q, sigma, T - dT);
        g.theta = (V_T - V) / dT;
        
        // Vega
        double V_sigma_up = pricer(S, K, r, q, sigma + dSigma, T);
        double V_sigma_down = pricer(S, K, r, q, sigma - dSigma, T);
        g.vega = (V_sigma_up - V_sigma_down) / (2 * dSigma) / 100.0;
        
        // Rho
        double V_r_up = pricer(S, K, r + dR, q, sigma, T);
        double V_r_down = pricer(S, K, r - dR, q, sigma, T);
        g.rho = (V_r_up - V_r_down) / (2 * dR) / 100.0;
        
        return g;
    }
};
```

---

## 四、二叉树模型

### 4.1 CRR 模型

Cox-Ross-Rubinstein 二叉树：

```cpp
class BinomialTree {
public:
    // 欧式期权
    static double european_option(double S, double K, double r, double q,
                                  double sigma, double T, int steps, bool is_call) {
        double dt = T / steps;
        double u = std::exp(sigma * std::sqrt(dt));  // 上涨因子
        double d = 1.0 / u;                          // 下跌因子
        double p = (std::exp((r - q) * dt) - d) / (u - d);  // 风险中性概率
        double discount = std::exp(-r * dt);
        
        // 构建到期时的价格树
        std::vector<double> prices(steps + 1);
        for (int i = 0; i <= steps; i++) {
            double ST = S * std::pow(u, steps - i) * std::pow(d, i);
            if (is_call) {
                prices[i] = std::max(ST - K, 0.0);
            } else {
                prices[i] = std::max(K - ST, 0.0);
            }
        }
        
        // 向后归纳
        for (int step = steps - 1; step >= 0; step--) {
            for (int i = 0; i <= step; i++) {
                prices[i] = discount * (p * prices[i] + (1 - p) * prices[i + 1]);
            }
        }
        
        return prices[0];
    }
    
    // 美式期权
    static double american_option(double S, double K, double r, double q,
                                  double sigma, double T, int steps, bool is_call) {
        double dt = T / steps;
        double u = std::exp(sigma * std::sqrt(dt));
        double d = 1.0 / u;
        double p = (std::exp((r - q) * dt) - d) / (u - d);
        double discount = std::exp(-r * dt);
        
        // 构建价格树
        std::vector<std::vector<double>> stock_tree(steps + 1);
        for (int i = 0; i <= steps; i++) {
            stock_tree[i].resize(i + 1);
            for (int j = 0; j <= i; j++) {
                stock_tree[i][j] = S * std::pow(u, i - j) * std::pow(d, j);
            }
        }
        
        // 期权价值树
        std::vector<double> option_tree(steps + 1);
        for (int j = 0; j <= steps; j++) {
            double ST = stock_tree[steps][j];
            option_tree[j] = is_call ? std::max(ST - K, 0.0) : std::max(K - ST, 0.0);
        }
        
        // 向后归纳，考虑提前行权
        for (int i = steps - 1; i >= 0; i--) {
            for (int j = 0; j <= i; j++) {
                double continuation = discount * (p * option_tree[j] + (1 - p) * option_tree[j + 1]);
                double exercise = is_call ? 
                    std::max(stock_tree[i][j] - K, 0.0) :
                    std::max(K - stock_tree[i][j], 0.0);
                option_tree[j] = std::max(continuation, exercise);
            }
        }
        
        return option_tree[0];
    }
    
    // 计算 Greeks
    static Greeks calculate_greeks(double S, double K, double r, double q,
                                   double sigma, double T, int steps, bool is_call) {
        Greeks g;
        
        double dS = S * 0.01;
        double dSigma = 0.01;
        double dT = T / steps;
        
        double V = european_option(S, K, r, q, sigma, T, steps, is_call);
        double V_up = european_option(S + dS, K, r, q, sigma, T, steps, is_call);
        double V_down = european_option(S - dS, K, r, q, sigma, T, steps, is_call);
        
        g.delta = (V_up - V_down) / (2 * dS);
        g.gamma = (V_up - 2 * V + V_down) / (dS * dS);
        
        double V_sigma = european_option(S, K, r, q, sigma + dSigma, T, steps, is_call);
        g.vega = (V_sigma - V) / dSigma / 100.0;
        
        double V_T = european_option(S, K, r, q, sigma, T - dT, steps - 1, is_call);
        g.theta = (V_T - V) / dT / 365.0;
        
        return g;
    }
};
```

---

## 五、隐含波动率

### 5.1 Newton-Raphson 方法

```cpp
class ImpliedVolatility {
public:
    // Newton-Raphson 求解隐含波动率
    static double calculate(double market_price, double S, double K,
                           double r, double q, double T, bool is_call,
                           double initial_guess = 0.2, int max_iter = 100,
                           double tolerance = 1e-8) {
        double sigma = initial_guess;
        
        for (int i = 0; i < max_iter; i++) {
            double price = is_call ?
                BlackScholes::call_price(S, K, r, q, sigma, T) :
                BlackScholes::put_price(S, K, r, q, sigma, T);
            
            double diff = price - market_price;
            
            if (std::abs(diff) < tolerance) {
                return sigma;
            }
            
            // Vega
            auto [d1, d2] = BlackScholes::calc_d1_d2(S, K, r, q, sigma, T);
            double vega = S * std::exp(-q * T) * BlackScholes::norm_pdf(d1) * std::sqrt(T);
            
            if (std::abs(vega) < 1e-10) {
                break;  // Vega 太小，无法继续
            }
            
            sigma -= diff / vega;
            
            // 确保 sigma 在合理范围
            sigma = std::max(0.001, std::min(sigma, 5.0));
        }
        
        return sigma;
    }
    
    // Brent 方法（更稳健）
    static double calculate_brent(double market_price, double S, double K,
                                  double r, double q, double T, bool is_call,
                                  double sigma_low = 0.001, double sigma_high = 5.0,
                                  double tolerance = 1e-8) {
        auto f = [&](double sigma) {
            double price = is_call ?
                BlackScholes::call_price(S, K, r, q, sigma, T) :
                BlackScholes::put_price(S, K, r, q, sigma, T);
            return price - market_price;
        };
        
        double a = sigma_low, b = sigma_high;
        double fa = f(a), fb = f(b);
        
        if (fa * fb > 0) {
            return -1;  // 无解
        }
        
        if (std::abs(fa) < std::abs(fb)) {
            std::swap(a, b);
            std::swap(fa, fb);
        }
        
        double c = a, fc = fa;
        bool mflag = true;
        double d = 0;
        
        while (std::abs(b - a) > tolerance) {
            double s;
            
            if (fa != fc && fb != fc) {
                // 逆二次插值
                s = a * fb * fc / ((fa - fb) * (fa - fc)) +
                    b * fa * fc / ((fb - fa) * (fb - fc)) +
                    c * fa * fb / ((fc - fa) * (fc - fb));
            } else {
                // 割线法
                s = b - fb * (b - a) / (fb - fa);
            }
            
            // 检查是否使用二分法
            bool cond1 = (s < (3 * a + b) / 4 || s > b);
            bool cond2 = mflag && std::abs(s - b) >= std::abs(b - c) / 2;
            bool cond3 = !mflag && std::abs(s - b) >= std::abs(c - d) / 2;
            bool cond4 = mflag && std::abs(b - c) < tolerance;
            bool cond5 = !mflag && std::abs(c - d) < tolerance;
            
            if (cond1 || cond2 || cond3 || cond4 || cond5) {
                s = (a + b) / 2;
                mflag = true;
            } else {
                mflag = false;
            }
            
            double fs = f(s);
            d = c;
            c = b;
            fc = fb;
            
            if (fa * fs < 0) {
                b = s;
                fb = fs;
            } else {
                a = s;
                fa = fs;
            }
            
            if (std::abs(fa) < std::abs(fb)) {
                std::swap(a, b);
                std::swap(fa, fb);
            }
        }
        
        return b;
    }
};
```

---

## 六、Delta 对冲

### 6.1 Delta 中性策略

```cpp
class DeltaHedger {
public:
    struct Position {
        double option_quantity;
        double stock_quantity;
        double cash;
        double pnl;
    };
    
    // 初始化对冲组合
    Position initialize(double option_qty, double S, double delta) {
        Position pos;
        pos.option_quantity = option_qty;
        pos.stock_quantity = -option_qty * delta;  // 对冲
        pos.cash = 0;  // 假设自筹资金
        pos.pnl = 0;
        return pos;
    }
    
    // 再平衡
    void rebalance(Position& pos, double S_old, double S_new,
                   double delta_old, double delta_new, double dt, double r) {
        // 计算需要调整的股票数量
        double target_stock = -pos.option_quantity * delta_new;
        double stock_to_trade = target_stock - pos.stock_quantity;
        
        // 交易股票
        double trade_cost = stock_to_trade * S_new;
        pos.stock_quantity = target_stock;
        pos.cash -= trade_cost;
        
        // 现金利息
        pos.cash *= std::exp(r * dt);
    }
    
    // 计算 P&L
    double calculate_pnl(const Position& pos, double S,
                        double option_price_init, double option_price_now) {
        double option_value = pos.option_quantity * option_price_now;
        double stock_value = pos.stock_quantity * S;
        double total = option_value + stock_value + pos.cash;
        
        return total - pos.option_quantity * option_price_init;
    }
    
    // 模拟 Delta 对冲
    std::vector<double> simulate_hedge(
        double S0, double K, double r, double q, double sigma, double T,
        int rebalance_freq, int num_paths) {
        
        std::vector<double> hedge_errors;
        std::mt19937_64 rng(42);
        std::normal_distribution<double> norm(0, 1);
        
        double dt = T / rebalance_freq;
        
        for (int path = 0; path < num_paths; path++) {
            double S = S0;
            double t = 0;
            
            double init_price = BlackScholes::call_price(S, K, r, q, sigma, T);
            Greeks greeks = GreeksCalculator::calculate(S, K, r, q, sigma, T, true);
            Position pos = initialize(1, S, greeks.delta);
            pos.cash = -init_price + greeks.delta * S;
            
            for (int i = 0; i < rebalance_freq; i++) {
                // 模拟股价变动
                double dW = norm(rng) * std::sqrt(dt);
                double dS = S * ((r - q) * dt + sigma * dW);
                double S_new = S + dS;
                
                t += dt;
                double T_remain = T - t;
                
                if (T_remain > 0) {
                    Greeks new_greeks = GreeksCalculator::calculate(
                        S_new, K, r, q, sigma, T_remain, true);
                    rebalance(pos, S, S_new, greeks.delta, new_greeks.delta, dt, r);
                    greeks = new_greeks;
                }
                
                S = S_new;
            }
            
            // 到期结算
            double payoff = std::max(S - K, 0.0);
            double final_value = pos.stock_quantity * S + pos.cash;
            double hedge_error = final_value + payoff - init_price * std::exp(r * T);
            
            hedge_errors.push_back(hedge_error);
        }
        
        return hedge_errors;
    }
};
```

---

## 七、奇异期权

### 7.1 亚式期权（蒙特卡洛）

```cpp
class AsianOption {
public:
    // 算术平均亚式期权
    static double price_arithmetic(double S, double K, double r, double q,
                                   double sigma, double T, int num_avg_points,
                                   int num_paths, bool is_call) {
        std::mt19937_64 rng(42);
        std::normal_distribution<double> norm(0, 1);
        
        double dt = T / num_avg_points;
        double drift = (r - q - 0.5 * sigma * sigma) * dt;
        double diffusion = sigma * std::sqrt(dt);
        
        double sum_payoff = 0;
        
        for (int path = 0; path < num_paths; path++) {
            double S_t = S;
            double sum_S = 0;
            
            for (int i = 0; i < num_avg_points; i++) {
                S_t *= std::exp(drift + diffusion * norm(rng));
                sum_S += S_t;
            }
            
            double avg_S = sum_S / num_avg_points;
            double payoff = is_call ? std::max(avg_S - K, 0.0) : std::max(K - avg_S, 0.0);
            sum_payoff += payoff;
        }
        
        return std::exp(-r * T) * sum_payoff / num_paths;
    }
};
```

### 7.2 障碍期权

```cpp
class BarrierOption {
public:
    enum BarrierType { DOWN_AND_OUT, DOWN_AND_IN, UP_AND_OUT, UP_AND_IN };
    
    static double price(double S, double K, double H, double r, double q,
                       double sigma, double T, BarrierType type, bool is_call,
                       int num_steps, int num_paths) {
        std::mt19937_64 rng(42);
        std::normal_distribution<double> norm(0, 1);
        
        double dt = T / num_steps;
        double drift = (r - q - 0.5 * sigma * sigma) * dt;
        double diffusion = sigma * std::sqrt(dt);
        
        double sum_payoff = 0;
        
        for (int path = 0; path < num_paths; path++) {
            double S_t = S;
            bool knocked = false;
            
            for (int i = 0; i < num_steps; i++) {
                S_t *= std::exp(drift + diffusion * norm(rng));
                
                // 检查障碍
                switch (type) {
                    case DOWN_AND_OUT:
                    case DOWN_AND_IN:
                        if (S_t <= H) knocked = true;
                        break;
                    case UP_AND_OUT:
                    case UP_AND_IN:
                        if (S_t >= H) knocked = true;
                        break;
                }
            }
            
            double payoff = 0;
            bool is_active = false;
            
            switch (type) {
                case DOWN_AND_OUT:
                case UP_AND_OUT:
                    is_active = !knocked;
                    break;
                case DOWN_AND_IN:
                case UP_AND_IN:
                    is_active = knocked;
                    break;
            }
            
            if (is_active) {
                payoff = is_call ? std::max(S_t - K, 0.0) : std::max(K - S_t, 0.0);
            }
            
            sum_payoff += payoff;
        }
        
        return std::exp(-r * T) * sum_payoff / num_paths;
    }
};
```

---

## 八、面试常见问题

**Q: 解释 Gamma 风险和 Gamma Scalping？**

**A**: 
- **Gamma 风险**：标的大幅波动时，Delta 快速变化导致的对冲成本
- **Gamma Scalping**：做多 Gamma（买入期权），频繁 Delta 对冲获利

| 市场状态 | Gamma 多头 | Gamma 空头 |
|----------|------------|------------|
| 高波动 | 盈利 | 亏损 |
| 低波动 | 亏损（Theta） | 盈利（Theta） |

**Q: 为什么 Vega 对 ATM 期权最大？**

**A**: ATM 期权的时间价值最高，对波动率变化最敏感。OTM/ITM 期权主要由内在价值决定。

**Q: 美式期权何时提前行权？**

**A**:
- **看涨期权**：除权日前（获取股息）
- **看跌期权**：深度 ITM 时（获取利息）

---

## 相关文章

- [波动率建模与曲面](@/articles/hft/hft-53-波动率建模与曲面.md)
- [量化数学-随机过程与时间序列](@/articles/hft/hft-49-量化数学-随机过程与时间序列.md)
- [HFT策略类型全景](@/articles/hft/hft-39-HFT策略类型全景.md)
