+++
title = "49. 量化数学-随机过程与时间序列"
date = 2026-02-02
weight = 49000
description = "量化进阶：随机过程、布朗运动、时间序列分析、ARIMA、GARCH"
[taxonomies]
tags = ["HFT", "量化", "随机过程", "时间序列", "GARCH"]
+++

# 量化数学 - 随机过程与时间序列

本文深入讲解量化交易中的随机过程理论和时间序列分析方法，包括布朗运动、马尔可夫过程、ARIMA、GARCH 等模型。

---

## 一、随机过程基础

### 1.1 随机过程定义

**随机过程**：随时间变化的随机变量族 {X(t), t ∈ T}

| 类型 | 时间 | 状态 | 示例 |
|------|------|------|------|
| 离散时间、离散状态 | 离散 | 离散 | 随机游走 |
| 离散时间、连续状态 | 离散 | 连续 | 股票日收益率 |
| 连续时间、离散状态 | 连续 | 离散 | 泊松过程 |
| 连续时间、连续状态 | 连续 | 连续 | 布朗运动 |

### 1.2 马尔可夫过程

**马尔可夫性**：给定当前状态，未来与过去独立。

$$
P(X_{t+1} | X_t, X_{t-1}, ..., X_0) = P(X_{t+1} | X_t)
$$

```cpp
class MarkovChain {
public:
    MarkovChain(const std::vector<std::vector<double>>& transition_matrix)
        : P_(transition_matrix), n_states_(transition_matrix.size()) {}
    
    // 模拟路径
    std::vector<int> simulate(int initial_state, int steps, uint64_t seed = 42) {
        std::mt19937_64 rng(seed);
        std::uniform_real_distribution<double> uniform(0, 1);
        
        std::vector<int> path;
        path.push_back(initial_state);
        
        int current = initial_state;
        
        for (int t = 0; t < steps; t++) {
            double u = uniform(rng);
            double cumsum = 0;
            
            for (int j = 0; j < n_states_; j++) {
                cumsum += P_[current][j];
                if (u <= cumsum) {
                    current = j;
                    break;
                }
            }
            
            path.push_back(current);
        }
        
        return path;
    }
    
    // 平稳分布
    std::vector<double> stationary_distribution(int iterations = 1000) {
        std::vector<double> pi(n_states_, 1.0 / n_states_);
        
        for (int iter = 0; iter < iterations; iter++) {
            std::vector<double> new_pi(n_states_, 0);
            
            for (int j = 0; j < n_states_; j++) {
                for (int i = 0; i < n_states_; i++) {
                    new_pi[j] += pi[i] * P_[i][j];
                }
            }
            
            pi = new_pi;
        }
        
        return pi;
    }
    
    // 首达时间期望
    double expected_hitting_time(int from, int to) {
        if (from == to) return 0;
        
        // 解方程 h_i = 1 + sum_{j != to} P_{ij} * h_j
        // 使用迭代法
        std::vector<double> h(n_states_, 0);
        
        for (int iter = 0; iter < 1000; iter++) {
            std::vector<double> new_h = h;
            
            for (int i = 0; i < n_states_; i++) {
                if (i == to) continue;
                
                double sum = 1;
                for (int j = 0; j < n_states_; j++) {
                    if (j != to) {
                        sum += P_[i][j] * h[j];
                    }
                }
                new_h[i] = sum;
            }
            
            h = new_h;
        }
        
        return h[from];
    }
    
private:
    std::vector<std::vector<double>> P_;
    int n_states_;
};
```

### 1.3 泊松过程

**性质**：
- 独立增量
- 平稳增量
- N(t) ~ Poisson(λt)
- 到达间隔 ~ Exponential(λ)

```cpp
class PoissonProcess {
public:
    PoissonProcess(double lambda, uint64_t seed = 42)
        : lambda_(lambda), rng_(seed), exp_dist_(lambda) {}
    
    // 模拟到时间 T
    std::vector<double> simulate_until(double T) {
        std::vector<double> arrivals;
        double t = 0;
        
        while (true) {
            double inter_arrival = exp_dist_(rng_);
            t += inter_arrival;
            
            if (t > T) break;
            arrivals.push_back(t);
        }
        
        return arrivals;
    }
    
    // 模拟 n 次到达
    std::vector<double> simulate_n_arrivals(int n) {
        std::vector<double> arrivals;
        double t = 0;
        
        for (int i = 0; i < n; i++) {
            t += exp_dist_(rng_);
            arrivals.push_back(t);
        }
        
        return arrivals;
    }
    
    // 非齐次泊松过程
    std::vector<double> simulate_nhpp(std::function<double(double)> intensity,
                                      double lambda_max, double T) {
        // Thinning 算法
        std::vector<double> arrivals;
        std::uniform_real_distribution<double> uniform(0, 1);
        
        double t = 0;
        std::exponential_distribution<double> exp_max(lambda_max);
        
        while (t < T) {
            t += exp_max(rng_);
            
            if (t > T) break;
            
            double u = uniform(rng_);
            if (u <= intensity(t) / lambda_max) {
                arrivals.push_back(t);
            }
        }
        
        return arrivals;
    }
    
private:
    double lambda_;
    std::mt19937_64 rng_;
    std::exponential_distribution<double> exp_dist_;
};
```

---

## 二、布朗运动

### 2.1 标准布朗运动

**性质**：
- W(0) = 0
- 独立增量
- W(t) - W(s) ~ N(0, t-s)
- 连续路径

```cpp
class BrownianMotion {
public:
    BrownianMotion(uint64_t seed = 42) : rng_(seed), normal_(0, 1) {}
    
    // 模拟标准布朗运动
    std::vector<double> simulate(double T, int steps) {
        std::vector<double> path(steps + 1);
        path[0] = 0;
        
        double dt = T / steps;
        double sqrt_dt = std::sqrt(dt);
        
        for (int i = 1; i <= steps; i++) {
            path[i] = path[i-1] + sqrt_dt * normal_(rng_);
        }
        
        return path;
    }
    
    // 几何布朗运动
    std::vector<double> geometric_bm(double S0, double mu, double sigma,
                                     double T, int steps) {
        std::vector<double> path(steps + 1);
        path[0] = S0;
        
        double dt = T / steps;
        double drift = (mu - 0.5 * sigma * sigma) * dt;
        double diffusion = sigma * std::sqrt(dt);
        
        for (int i = 1; i <= steps; i++) {
            double dW = normal_(rng_);
            path[i] = path[i-1] * std::exp(drift + diffusion * dW);
        }
        
        return path;
    }
    
    // Ornstein-Uhlenbeck 过程（均值回复）
    std::vector<double> ornstein_uhlenbeck(double X0, double theta, double mu,
                                           double sigma, double T, int steps) {
        std::vector<double> path(steps + 1);
        path[0] = X0;
        
        double dt = T / steps;
        
        for (int i = 1; i <= steps; i++) {
            double dW = std::sqrt(dt) * normal_(rng_);
            path[i] = path[i-1] + theta * (mu - path[i-1]) * dt + sigma * dW;
        }
        
        return path;
    }
    
    // CIR 过程（利率模型）
    std::vector<double> cir_process(double r0, double kappa, double theta,
                                    double sigma, double T, int steps) {
        std::vector<double> path(steps + 1);
        path[0] = r0;
        
        double dt = T / steps;
        
        for (int i = 1; i <= steps; i++) {
            double dW = std::sqrt(dt) * normal_(rng_);
            double dr = kappa * (theta - path[i-1]) * dt +
                       sigma * std::sqrt(std::max(path[i-1], 0.0)) * dW;
            path[i] = std::max(path[i-1] + dr, 0.0);
        }
        
        return path;
    }
    
private:
    std::mt19937_64 rng_;
    std::normal_distribution<double> normal_;
};
```

### 2.2 伊藤引理

对于 $dX_t = \mu dt + \sigma dW_t$，若 $f(X_t, t)$，则：

$$
df = \left(\frac{\partial f}{\partial t} + \mu \frac{\partial f}{\partial x} + \frac{1}{2}\sigma^2 \frac{\partial^2 f}{\partial x^2}\right)dt + \sigma \frac{\partial f}{\partial x}dW_t
$$

```cpp
// Black-Scholes 公式（伊藤引理推导）
class BlackScholes {
public:
    // 欧式看涨期权价格
    static double call_price(double S, double K, double r, double sigma, double T) {
        double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / 
                   (sigma * std::sqrt(T));
        double d2 = d1 - sigma * std::sqrt(T);
        
        return S * Distributions::normal_cdf(d1) - 
               K * std::exp(-r * T) * Distributions::normal_cdf(d2);
    }
    
    // 欧式看跌期权价格
    static double put_price(double S, double K, double r, double sigma, double T) {
        double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / 
                   (sigma * std::sqrt(T));
        double d2 = d1 - sigma * std::sqrt(T);
        
        return K * std::exp(-r * T) * Distributions::normal_cdf(-d2) - 
               S * Distributions::normal_cdf(-d1);
    }
    
    // Greeks
    struct Greeks {
        double delta;
        double gamma;
        double theta;
        double vega;
        double rho;
    };
    
    static Greeks calculate_greeks(double S, double K, double r, double sigma,
                                   double T, bool is_call) {
        double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / 
                   (sigma * std::sqrt(T));
        double d2 = d1 - sigma * std::sqrt(T);
        
        Greeks g;
        
        double n_d1 = Distributions::normal_cdf(d1);
        double n_d2 = Distributions::normal_cdf(d2);
        double phi_d1 = Distributions::normal_pdf(d1);
        
        if (is_call) {
            g.delta = n_d1;
            g.theta = -S * phi_d1 * sigma / (2 * std::sqrt(T)) -
                     r * K * std::exp(-r * T) * n_d2;
            g.rho = K * T * std::exp(-r * T) * n_d2;
        } else {
            g.delta = n_d1 - 1;
            g.theta = -S * phi_d1 * sigma / (2 * std::sqrt(T)) +
                     r * K * std::exp(-r * T) * (1 - n_d2);
            g.rho = -K * T * std::exp(-r * T) * (1 - n_d2);
        }
        
        g.gamma = phi_d1 / (S * sigma * std::sqrt(T));
        g.vega = S * phi_d1 * std::sqrt(T);
        
        return g;
    }
    
    // 隐含波动率
    static double implied_volatility(double market_price, double S, double K,
                                     double r, double T, bool is_call) {
        // Newton-Raphson
        double sigma = 0.2;  // 初始猜测
        
        for (int i = 0; i < 100; i++) {
            double price = is_call ? call_price(S, K, r, sigma, T) :
                                    put_price(S, K, r, sigma, T);
            double vega = calculate_greeks(S, K, r, sigma, T, is_call).vega;
            
            double diff = price - market_price;
            
            if (std::abs(diff) < 1e-8) break;
            
            sigma -= diff / vega;
            sigma = std::max(0.001, std::min(sigma, 5.0));
        }
        
        return sigma;
    }
};
```

---

## 三、时间序列模型

### 3.1 自回归模型（AR）

$$
X_t = c + \sum_{i=1}^{p} \phi_i X_{t-i} + \epsilon_t
$$

```cpp
class ARModel {
public:
    // 估计 AR(p) 模型（Yule-Walker 方程）
    static std::vector<double> estimate(const std::vector<double>& data, int p) {
        int n = data.size();
        double mean = Statistics::mean(data);
        
        // 计算自相关函数
        std::vector<double> acf(p + 1);
        for (int k = 0; k <= p; k++) {
            double sum = 0;
            for (int t = k; t < n; t++) {
                sum += (data[t] - mean) * (data[t-k] - mean);
            }
            acf[k] = sum / n;
        }
        
        // 构建 Yule-Walker 矩阵
        std::vector<std::vector<double>> R(p, std::vector<double>(p));
        std::vector<double> r(p);
        
        for (int i = 0; i < p; i++) {
            r[i] = acf[i + 1];
            for (int j = 0; j < p; j++) {
                R[i][j] = acf[std::abs(i - j)];
            }
        }
        
        // 解方程 R * phi = r
        return solve_linear_system(R, r);
    }
    
    // 预测
    static double forecast(const std::vector<double>& data,
                          const std::vector<double>& phi,
                          double c) {
        int p = phi.size();
        double pred = c;
        
        for (int i = 0; i < p; i++) {
            pred += phi[i] * data[data.size() - 1 - i];
        }
        
        return pred;
    }
    
    // 模拟
    static std::vector<double> simulate(const std::vector<double>& phi,
                                        double c, double sigma,
                                        int n, uint64_t seed = 42) {
        std::mt19937_64 rng(seed);
        std::normal_distribution<double> normal(0, sigma);
        
        int p = phi.size();
        std::vector<double> data(n);
        
        // 初始化
        for (int i = 0; i < p; i++) {
            data[i] = normal(rng);
        }
        
        for (int t = p; t < n; t++) {
            data[t] = c;
            for (int i = 0; i < p; i++) {
                data[t] += phi[i] * data[t - 1 - i];
            }
            data[t] += normal(rng);
        }
        
        return data;
    }
};
```

### 3.2 移动平均模型（MA）

$$
X_t = \mu + \epsilon_t + \sum_{i=1}^{q} \theta_i \epsilon_{t-i}
$$

### 3.3 ARIMA 模型

```cpp
class ARIMA {
public:
    // 差分
    static std::vector<double> difference(const std::vector<double>& data, int d) {
        std::vector<double> result = data;
        
        for (int i = 0; i < d; i++) {
            std::vector<double> diff;
            for (size_t t = 1; t < result.size(); t++) {
                diff.push_back(result[t] - result[t-1]);
            }
            result = diff;
        }
        
        return result;
    }
    
    // 逆差分
    static std::vector<double> integrate(const std::vector<double>& diff_data,
                                         const std::vector<double>& original,
                                         int d) {
        std::vector<double> result = diff_data;
        
        for (int i = 0; i < d; i++) {
            std::vector<double> integrated;
            double cumsum = original[d - 1 - i];
            
            for (double val : result) {
                cumsum += val;
                integrated.push_back(cumsum);
            }
            result = integrated;
        }
        
        return result;
    }
    
    struct ARIMAModel {
        int p, d, q;
        std::vector<double> ar_params;
        std::vector<double> ma_params;
        double constant;
        double sigma;
    };
    
    // 简化的 ARIMA 估计
    static ARIMAModel fit(const std::vector<double>& data, int p, int d, int q) {
        // 差分
        auto diff_data = difference(data, d);
        
        // 估计 AR 部分
        auto ar_params = ARModel::estimate(diff_data, p);
        
        // MA 部分需要更复杂的估计（此处简化）
        std::vector<double> ma_params(q, 0);
        
        // 计算残差
        double mean = Statistics::mean(diff_data);
        double variance = Statistics::variance(diff_data);
        
        return {p, d, q, ar_params, ma_params, mean, std::sqrt(variance)};
    }
    
    // 预测
    static std::vector<double> forecast(const std::vector<double>& data,
                                        const ARIMAModel& model,
                                        int steps) {
        auto diff_data = difference(data, model.d);
        
        std::vector<double> predictions;
        auto extended = diff_data;
        
        for (int s = 0; s < steps; s++) {
            double pred = model.constant;
            
            for (int i = 0; i < model.p; i++) {
                pred += model.ar_params[i] * extended[extended.size() - 1 - i];
            }
            
            predictions.push_back(pred);
            extended.push_back(pred);
        }
        
        // 逆差分
        return integrate(predictions, data, model.d);
    }
};
```

### 3.4 GARCH 模型

$$
\sigma_t^2 = \omega + \sum_{i=1}^{q} \alpha_i \epsilon_{t-i}^2 + \sum_{j=1}^{p} \beta_j \sigma_{t-j}^2
$$

```cpp
class GARCH {
public:
    struct GARCHModel {
        double omega;
        std::vector<double> alpha;  // ARCH 参数
        std::vector<double> beta;   // GARCH 参数
        double unconditional_var;
    };
    
    // 估计 GARCH(p, q)
    static GARCHModel fit(const std::vector<double>& returns, int p, int q) {
        // 初始化
        double omega = 0.00001;
        std::vector<double> alpha(q, 0.05);
        std::vector<double> beta(p, 0.9);
        
        // 使用梯度下降或其他优化方法
        // 此处简化为固定参数
        
        // 计算无条件方差
        double sum_ab = 0;
        for (double a : alpha) sum_ab += a;
        for (double b : beta) sum_ab += b;
        
        double uncond_var = omega / (1 - sum_ab);
        
        return {omega, alpha, beta, uncond_var};
    }
    
    // 计算条件方差序列
    static std::vector<double> conditional_variance(const std::vector<double>& returns,
                                                    const GARCHModel& model) {
        int n = returns.size();
        int p = model.beta.size();
        int q = model.alpha.size();
        int start = std::max(p, q);
        
        std::vector<double> sigma_sq(n);
        
        // 初始化
        for (int i = 0; i < start; i++) {
            sigma_sq[i] = model.unconditional_var;
        }
        
        // 递推
        for (int t = start; t < n; t++) {
            sigma_sq[t] = model.omega;
            
            for (int i = 0; i < q; i++) {
                sigma_sq[t] += model.alpha[i] * returns[t-1-i] * returns[t-1-i];
            }
            
            for (int j = 0; j < p; j++) {
                sigma_sq[t] += model.beta[j] * sigma_sq[t-1-j];
            }
        }
        
        return sigma_sq;
    }
    
    // 波动率预测
    static std::vector<double> forecast_volatility(const std::vector<double>& returns,
                                                   const GARCHModel& model,
                                                   int steps) {
        auto sigma_sq = conditional_variance(returns, model);
        double last_sigma_sq = sigma_sq.back();
        double last_return = returns.back();
        
        std::vector<double> forecasts;
        
        for (int h = 1; h <= steps; h++) {
            double pred = model.omega + 
                         (model.alpha[0] + model.beta[0]) * last_sigma_sq;
            
            // 长期预测收敛到无条件方差
            // sigma^2(h) = uncond_var + (alpha + beta)^h * (sigma^2(1) - uncond_var)
            
            forecasts.push_back(std::sqrt(pred));
            last_sigma_sq = pred;
        }
        
        return forecasts;
    }
    
    // 模拟
    static std::pair<std::vector<double>, std::vector<double>> simulate(
        const GARCHModel& model, int n, uint64_t seed = 42) {
        
        std::mt19937_64 rng(seed);
        std::normal_distribution<double> normal(0, 1);
        
        std::vector<double> returns(n);
        std::vector<double> sigma_sq(n);
        
        int p = model.beta.size();
        int q = model.alpha.size();
        int start = std::max(p, q);
        
        // 初始化
        for (int i = 0; i < start; i++) {
            sigma_sq[i] = model.unconditional_var;
            returns[i] = std::sqrt(sigma_sq[i]) * normal(rng);
        }
        
        for (int t = start; t < n; t++) {
            sigma_sq[t] = model.omega;
            
            for (int i = 0; i < q; i++) {
                sigma_sq[t] += model.alpha[i] * returns[t-1-i] * returns[t-1-i];
            }
            
            for (int j = 0; j < p; j++) {
                sigma_sq[t] += model.beta[j] * sigma_sq[t-1-j];
            }
            
            returns[t] = std::sqrt(sigma_sq[t]) * normal(rng);
        }
        
        return {returns, sigma_sq};
    }
};
```

---

## 四、协整与配对交易

### 4.1 协整检验

```cpp
class Cointegration {
public:
    struct EngleGrangerResult {
        double adf_stat;
        bool cointegrated;
        double hedge_ratio;
        std::vector<double> spread;
    };
    
    // Engle-Granger 两步法
    static EngleGrangerResult engle_granger_test(
        const std::vector<double>& y,
        const std::vector<double>& x,
        double significance = 0.05) {
        
        // 第一步：回归
        auto reg = Regression::simple_linear(x, y);
        double hedge_ratio = reg.slope;
        
        // 计算残差（spread）
        std::vector<double> spread;
        for (size_t i = 0; i < y.size(); i++) {
            spread.push_back(y[i] - hedge_ratio * x[i] - reg.intercept);
        }
        
        // 第二步：ADF 检验残差
        auto adf_result = HypothesisTests::adf_test(spread);
        
        // 临界值（5%）约 -3.34 for Engle-Granger
        bool cointegrated = adf_result.statistic < -3.34;
        
        return {adf_result.statistic, cointegrated, hedge_ratio, spread};
    }
    
    // 计算半衰期
    static double half_life(const std::vector<double>& spread) {
        // 回归 spread_diff ~ spread_lag
        std::vector<double> diff, lag;
        
        for (size_t i = 1; i < spread.size(); i++) {
            diff.push_back(spread[i] - spread[i-1]);
            lag.push_back(spread[i-1]);
        }
        
        auto reg = Regression::simple_linear(lag, diff);
        
        // half_life = -log(2) / log(1 + beta)
        // 简化: half_life ≈ -log(2) / beta 当 beta 较小
        if (reg.slope >= 0) {
            return INFINITY;  // 不均值回归
        }
        
        return -std::log(2) / reg.slope;
    }
};
```

### 4.2 配对交易策略

```cpp
class PairsTrading {
public:
    struct Signal {
        double z_score;
        int position;  // -1, 0, 1
        double entry_threshold;
        double exit_threshold;
    };
    
    static Signal generate_signal(const std::vector<double>& spread,
                                  int lookback = 20,
                                  double entry = 2.0,
                                  double exit = 0.5) {
        // 计算 z-score
        std::vector<double> recent(spread.end() - lookback, spread.end());
        double mean = Statistics::mean(recent);
        double std = Statistics::std_dev(recent);
        
        double current = spread.back();
        double z_score = (current - mean) / std;
        
        int position = 0;
        if (z_score > entry) {
            position = -1;  // 做空 spread
        } else if (z_score < -entry) {
            position = 1;   // 做多 spread
        } else if (std::abs(z_score) < exit) {
            position = 0;   // 平仓
        }
        
        return {z_score, position, entry, exit};
    }
    
    // 回测
    static std::vector<double> backtest(const std::vector<double>& y,
                                        const std::vector<double>& x,
                                        double hedge_ratio,
                                        int lookback = 20,
                                        double entry = 2.0,
                                        double exit = 0.5) {
        std::vector<double> returns;
        int position = 0;
        double entry_spread = 0;
        
        for (size_t t = lookback; t < y.size(); t++) {
            // 计算 spread
            std::vector<double> spread;
            for (size_t i = 0; i <= t; i++) {
                spread.push_back(y[i] - hedge_ratio * x[i]);
            }
            
            auto signal = generate_signal(spread, lookback, entry, exit);
            
            // 计算收益
            double spread_return = (y[t] - y[t-1]) - hedge_ratio * (x[t] - x[t-1]);
            double pnl = position * spread_return;
            returns.push_back(pnl);
            
            // 更新仓位
            if (position == 0 && signal.position != 0) {
                position = signal.position;
                entry_spread = spread.back();
            } else if (position != 0 && 
                       std::abs(signal.z_score) < exit) {
                position = 0;
            }
        }
        
        return returns;
    }
};
```

---

## 五、面试常见问题

**Q: 什么是平稳性？为什么重要？**

A: 平稳性指时间序列的统计特性（均值、方差）不随时间变化。重要性：
1. 大多数时间序列模型假设平稳性
2. 非平稳序列可能产生伪回归
3. 需要差分或去趋势使其平稳

**Q: AR 和 MA 模型的区别？**

| 特性 | AR(p) | MA(q) |
|------|-------|-------|
| 依赖 | 历史观测值 | 历史误差项 |
| ACF | 拖尾衰减 | q 阶截尾 |
| PACF | p 阶截尾 | 拖尾衰减 |
| 平稳条件 | 特征根在单位圆内 | 总是平稳 |

**Q: 为什么需要 GARCH 模型？**

A: 金融时间序列的波动率具有聚集性（volatility clustering），GARCH 能够捕捉：
1. 波动率随时间变化
2. 大波动后往往跟随大波动
3. 波动率的持续性

---

## 相关文章

- [量化数学-概率统计基础](@/articles/hft/hft-48-量化数学-概率统计基础.md)
- [市场微结构深度解析](@/articles/hft/hft-38-市场微结构深度解析.md)
- [HFT策略类型全景](@/articles/hft/hft-39-HFT策略类型全景.md)
