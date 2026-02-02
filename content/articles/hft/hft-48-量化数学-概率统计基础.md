+++
title = "48.量化数学-概率统计基础"
date = 2026-02-02
description = "量化基础：概率论、统计推断、假设检验、回归分析"
[taxonomies]
tags = ["HFT", "量化", "概率", "统计", "数学"]
+++

# 量化数学 - 概率统计基础

本文介绍量化交易中必备的概率论和统计学基础，包括概率分布、统计推断、假设检验和回归分析。

---

## 一、概率论基础

### 1.1 随机变量与分布

**离散随机变量**：

| 分布 | PMF | 期望 | 方差 | 应用 |
|------|-----|------|------|------|
| 伯努利 | P(X=1)=p | p | p(1-p) | 单次成功/失败 |
| 二项 | C(n,k)p^k(1-p)^(n-k) | np | np(1-p) | n 次试验成功次数 |
| 泊松 | e^(-λ)λ^k/k! | λ | λ | 订单到达 |
| 几何 | (1-p)^(k-1)p | 1/p | (1-p)/p² | 首次成功 |

**连续随机变量**：

| 分布 | PDF | 期望 | 方差 | 应用 |
|------|-----|------|------|------|
| 均匀 | 1/(b-a) | (a+b)/2 | (b-a)²/12 | 随机采样 |
| 正态 | (1/√2πσ)e^(-(x-μ)²/2σ²) | μ | σ² | 收益率 |
| 指数 | λe^(-λx) | 1/λ | 1/λ² | 到达时间间隔 |
| 对数正态 | (1/xσ√2π)e^(-(lnx-μ)²/2σ²) | e^(μ+σ²/2) | - | 价格 |

### 1.2 概率分布实现

```cpp
#include <random>
#include <cmath>

class Distributions {
public:
    Distributions(uint64_t seed = 42) : rng_(seed) {}
    
    // 正态分布
    double normal(double mean, double std) {
        std::normal_distribution<double> dist(mean, std);
        return dist(rng_);
    }
    
    // 对数正态分布
    double lognormal(double mean, double std) {
        std::lognormal_distribution<double> dist(mean, std);
        return dist(rng_);
    }
    
    // 泊松分布
    int poisson(double lambda) {
        std::poisson_distribution<int> dist(lambda);
        return dist(rng_);
    }
    
    // 指数分布
    double exponential(double lambda) {
        std::exponential_distribution<double> dist(lambda);
        return dist(rng_);
    }
    
    // 均匀分布
    double uniform(double a, double b) {
        std::uniform_real_distribution<double> dist(a, b);
        return dist(rng_);
    }
    
    // 标准正态 CDF
    static double normal_cdf(double x) {
        return 0.5 * (1 + std::erf(x / std::sqrt(2)));
    }
    
    // 标准正态 PDF
    static double normal_pdf(double x) {
        return std::exp(-0.5 * x * x) / std::sqrt(2 * M_PI);
    }
    
    // 标准正态逆 CDF（近似）
    static double normal_inv_cdf(double p) {
        // Abramowitz and Stegun 近似
        if (p <= 0) return -INFINITY;
        if (p >= 1) return INFINITY;
        
        if (p < 0.5) {
            return -rational_approx(std::sqrt(-2 * std::log(p)));
        } else {
            return rational_approx(std::sqrt(-2 * std::log(1 - p)));
        }
    }
    
private:
    static double rational_approx(double t) {
        const double c0 = 2.515517;
        const double c1 = 0.802853;
        const double c2 = 0.010328;
        const double d1 = 1.432788;
        const double d2 = 0.189269;
        const double d3 = 0.001308;
        
        return t - (c0 + c1*t + c2*t*t) / 
               (1 + d1*t + d2*t*t + d3*t*t*t);
    }
    
    std::mt19937_64 rng_;
};
```

### 1.3 期望与方差

```cpp
class Statistics {
public:
    // 均值
    static double mean(const std::vector<double>& data) {
        if (data.empty()) return 0;
        return std::accumulate(data.begin(), data.end(), 0.0) / data.size();
    }
    
    // 方差（样本方差）
    static double variance(const std::vector<double>& data) {
        if (data.size() < 2) return 0;
        double m = mean(data);
        double sum_sq = 0;
        for (double x : data) {
            sum_sq += (x - m) * (x - m);
        }
        return sum_sq / (data.size() - 1);
    }
    
    // 标准差
    static double std_dev(const std::vector<double>& data) {
        return std::sqrt(variance(data));
    }
    
    // 协方差
    static double covariance(const std::vector<double>& x,
                            const std::vector<double>& y) {
        if (x.size() != y.size() || x.size() < 2) return 0;
        
        double mean_x = mean(x);
        double mean_y = mean(y);
        double sum = 0;
        
        for (size_t i = 0; i < x.size(); i++) {
            sum += (x[i] - mean_x) * (y[i] - mean_y);
        }
        
        return sum / (x.size() - 1);
    }
    
    // 相关系数
    static double correlation(const std::vector<double>& x,
                             const std::vector<double>& y) {
        double cov = covariance(x, y);
        double std_x = std_dev(x);
        double std_y = std_dev(y);
        
        if (std_x == 0 || std_y == 0) return 0;
        return cov / (std_x * std_y);
    }
    
    // 偏度（Skewness）
    static double skewness(const std::vector<double>& data) {
        double m = mean(data);
        double s = std_dev(data);
        if (s == 0) return 0;
        
        double sum = 0;
        for (double x : data) {
            sum += std::pow((x - m) / s, 3);
        }
        
        return sum * data.size() / ((data.size() - 1) * (data.size() - 2));
    }
    
    // 峰度（Kurtosis）
    static double kurtosis(const std::vector<double>& data) {
        double m = mean(data);
        double s = std_dev(data);
        if (s == 0) return 0;
        
        double sum = 0;
        for (double x : data) {
            sum += std::pow((x - m) / s, 4);
        }
        
        size_t n = data.size();
        return (n * (n + 1) * sum / ((n - 1) * (n - 2) * (n - 3))) -
               3 * (n - 1) * (n - 1) / ((n - 2) * (n - 3));
    }
    
    // 分位数
    static double quantile(std::vector<double> data, double q) {
        if (data.empty()) return 0;
        std::sort(data.begin(), data.end());
        
        double idx = q * (data.size() - 1);
        size_t lo = static_cast<size_t>(idx);
        size_t hi = lo + 1;
        
        if (hi >= data.size()) return data.back();
        
        double frac = idx - lo;
        return data[lo] * (1 - frac) + data[hi] * frac;
    }
};
```

---

## 二、统计推断

### 2.1 参数估计

**点估计**：

```cpp
struct ParameterEstimates {
    double estimate;
    double std_error;
    double confidence_lower;
    double confidence_upper;
};

class Estimation {
public:
    // 均值的置信区间
    static ParameterEstimates mean_confidence_interval(
        const std::vector<double>& data,
        double confidence = 0.95) {
        
        double m = Statistics::mean(data);
        double s = Statistics::std_dev(data);
        double n = data.size();
        
        double std_error = s / std::sqrt(n);
        
        // t 分布临界值（近似，大样本用正态）
        double z = Distributions::normal_inv_cdf((1 + confidence) / 2);
        
        return {
            m,
            std_error,
            m - z * std_error,
            m + z * std_error
        };
    }
    
    // 最大似然估计 - 正态分布
    static std::pair<double, double> mle_normal(const std::vector<double>& data) {
        double mu = Statistics::mean(data);
        double sigma_sq = 0;
        
        for (double x : data) {
            sigma_sq += (x - mu) * (x - mu);
        }
        sigma_sq /= data.size();  // MLE 用 n 而非 n-1
        
        return {mu, std::sqrt(sigma_sq)};
    }
    
    // Bootstrap 置信区间
    static ParameterEstimates bootstrap_ci(
        const std::vector<double>& data,
        std::function<double(const std::vector<double>&)> statistic,
        int num_bootstrap = 1000,
        double confidence = 0.95) {
        
        std::vector<double> bootstrap_stats;
        std::mt19937 rng(42);
        std::uniform_int_distribution<size_t> dist(0, data.size() - 1);
        
        for (int b = 0; b < num_bootstrap; b++) {
            std::vector<double> sample;
            for (size_t i = 0; i < data.size(); i++) {
                sample.push_back(data[dist(rng)]);
            }
            bootstrap_stats.push_back(statistic(sample));
        }
        
        std::sort(bootstrap_stats.begin(), bootstrap_stats.end());
        
        double alpha = (1 - confidence) / 2;
        size_t lo_idx = static_cast<size_t>(alpha * num_bootstrap);
        size_t hi_idx = static_cast<size_t>((1 - alpha) * num_bootstrap);
        
        return {
            statistic(data),
            Statistics::std_dev(bootstrap_stats),
            bootstrap_stats[lo_idx],
            bootstrap_stats[hi_idx]
        };
    }
};
```

### 2.2 假设检验

```cpp
struct HypothesisTestResult {
    double statistic;
    double p_value;
    bool reject_null;
    std::string conclusion;
};

class HypothesisTests {
public:
    // 单样本 t 检验
    static HypothesisTestResult one_sample_t_test(
        const std::vector<double>& data,
        double mu_0,
        double alpha = 0.05) {
        
        double m = Statistics::mean(data);
        double s = Statistics::std_dev(data);
        double n = data.size();
        
        double t_stat = (m - mu_0) / (s / std::sqrt(n));
        
        // 双尾 p 值（大样本近似）
        double p_value = 2 * (1 - Distributions::normal_cdf(std::abs(t_stat)));
        
        bool reject = p_value < alpha;
        
        return {
            t_stat,
            p_value,
            reject,
            reject ? "Reject H0" : "Fail to reject H0"
        };
    }
    
    // 双样本 t 检验（Welch's t-test）
    static HypothesisTestResult two_sample_t_test(
        const std::vector<double>& x,
        const std::vector<double>& y,
        double alpha = 0.05) {
        
        double m_x = Statistics::mean(x);
        double m_y = Statistics::mean(y);
        double s_x = Statistics::std_dev(x);
        double s_y = Statistics::std_dev(y);
        double n_x = x.size();
        double n_y = y.size();
        
        double se = std::sqrt(s_x*s_x/n_x + s_y*s_y/n_y);
        double t_stat = (m_x - m_y) / se;
        
        double p_value = 2 * (1 - Distributions::normal_cdf(std::abs(t_stat)));
        
        return {
            t_stat,
            p_value,
            p_value < alpha,
            p_value < alpha ? "Means are significantly different" : 
                             "No significant difference"
        };
    }
    
    // 配对 t 检验
    static HypothesisTestResult paired_t_test(
        const std::vector<double>& before,
        const std::vector<double>& after,
        double alpha = 0.05) {
        
        std::vector<double> diff;
        for (size_t i = 0; i < before.size(); i++) {
            diff.push_back(after[i] - before[i]);
        }
        
        return one_sample_t_test(diff, 0, alpha);
    }
    
    // 正态性检验（Jarque-Bera）
    static HypothesisTestResult jarque_bera_test(
        const std::vector<double>& data,
        double alpha = 0.05) {
        
        double n = data.size();
        double s = Statistics::skewness(data);
        double k = Statistics::kurtosis(data);
        
        // JB = n/6 * (S^2 + (K-3)^2/4)
        double jb = n / 6 * (s*s + (k*k) / 4);
        
        // JB ~ chi-squared(2)
        // 使用近似 p 值
        double p_value = std::exp(-jb / 2);  // 简化近似
        
        return {
            jb,
            p_value,
            p_value < alpha,
            p_value < alpha ? "Non-normal distribution" : "Normal distribution"
        };
    }
    
    // ADF 检验（单位根，平稳性）
    static HypothesisTestResult adf_test(
        const std::vector<double>& data,
        int lags = 1) {
        
        // 简化版 ADF
        std::vector<double> diff;
        for (size_t i = 1; i < data.size(); i++) {
            diff.push_back(data[i] - data[i-1]);
        }
        
        std::vector<double> lagged;
        for (size_t i = 0; i < diff.size() - 1; i++) {
            lagged.push_back(data[i]);
        }
        
        // 回归 diff[t] = alpha + beta * lagged[t] + epsilon
        auto [alpha, beta] = Regression::simple_linear(lagged, 
            std::vector<double>(diff.begin() + 1, diff.end()));
        
        // 检验 beta 是否显著为负
        // 临界值约 -2.86 (5%)
        bool stationary = beta < -2.86;
        
        return {
            beta,
            0,  // p 值需要查表
            stationary,
            stationary ? "Stationary" : "Non-stationary (unit root)"
        };
    }
};
```

---

## 三、回归分析

### 3.1 线性回归

```cpp
class Regression {
public:
    struct LinearResult {
        double intercept;
        double slope;
        double r_squared;
        double std_error;
        std::vector<double> residuals;
    };
    
    // 简单线性回归
    static LinearResult simple_linear(const std::vector<double>& x,
                                      const std::vector<double>& y) {
        double n = x.size();
        double sum_x = 0, sum_y = 0, sum_xy = 0, sum_xx = 0;
        
        for (size_t i = 0; i < n; i++) {
            sum_x += x[i];
            sum_y += y[i];
            sum_xy += x[i] * y[i];
            sum_xx += x[i] * x[i];
        }
        
        double mean_x = sum_x / n;
        double mean_y = sum_y / n;
        
        double slope = (sum_xy - n * mean_x * mean_y) / 
                       (sum_xx - n * mean_x * mean_x);
        double intercept = mean_y - slope * mean_x;
        
        // 计算 R²
        double ss_tot = 0, ss_res = 0;
        std::vector<double> residuals;
        
        for (size_t i = 0; i < n; i++) {
            double y_pred = intercept + slope * x[i];
            double resid = y[i] - y_pred;
            residuals.push_back(resid);
            ss_res += resid * resid;
            ss_tot += (y[i] - mean_y) * (y[i] - mean_y);
        }
        
        double r_squared = 1 - ss_res / ss_tot;
        double std_error = std::sqrt(ss_res / (n - 2));
        
        return {intercept, slope, r_squared, std_error, residuals};
    }
    
    // 多元线性回归（使用正规方程）
    static std::vector<double> multiple_linear(
        const std::vector<std::vector<double>>& X,
        const std::vector<double>& y) {
        
        size_t n = X.size();
        size_t p = X[0].size();
        
        // 构建 X^T X 和 X^T y
        std::vector<std::vector<double>> XtX(p, std::vector<double>(p, 0));
        std::vector<double> Xty(p, 0);
        
        for (size_t i = 0; i < n; i++) {
            for (size_t j = 0; j < p; j++) {
                Xty[j] += X[i][j] * y[i];
                for (size_t k = 0; k < p; k++) {
                    XtX[j][k] += X[i][j] * X[i][k];
                }
            }
        }
        
        // 求解 (X^T X) beta = X^T y
        return solve_linear_system(XtX, Xty);
    }
    
    // 岭回归（L2 正则化）
    static std::vector<double> ridge_regression(
        const std::vector<std::vector<double>>& X,
        const std::vector<double>& y,
        double lambda) {
        
        size_t n = X.size();
        size_t p = X[0].size();
        
        std::vector<std::vector<double>> XtX(p, std::vector<double>(p, 0));
        std::vector<double> Xty(p, 0);
        
        for (size_t i = 0; i < n; i++) {
            for (size_t j = 0; j < p; j++) {
                Xty[j] += X[i][j] * y[i];
                for (size_t k = 0; k < p; k++) {
                    XtX[j][k] += X[i][j] * X[i][k];
                }
            }
        }
        
        // 添加正则化项
        for (size_t j = 0; j < p; j++) {
            XtX[j][j] += lambda;
        }
        
        return solve_linear_system(XtX, Xty);
    }
    
private:
    static std::vector<double> solve_linear_system(
        std::vector<std::vector<double>> A,
        std::vector<double> b) {
        
        size_t n = b.size();
        
        // 高斯消元
        for (size_t i = 0; i < n; i++) {
            // 选主元
            size_t max_row = i;
            for (size_t k = i + 1; k < n; k++) {
                if (std::abs(A[k][i]) > std::abs(A[max_row][i])) {
                    max_row = k;
                }
            }
            std::swap(A[i], A[max_row]);
            std::swap(b[i], b[max_row]);
            
            // 消元
            for (size_t k = i + 1; k < n; k++) {
                double factor = A[k][i] / A[i][i];
                for (size_t j = i; j < n; j++) {
                    A[k][j] -= factor * A[i][j];
                }
                b[k] -= factor * b[i];
            }
        }
        
        // 回代
        std::vector<double> x(n);
        for (int i = n - 1; i >= 0; i--) {
            x[i] = b[i];
            for (size_t j = i + 1; j < n; j++) {
                x[i] -= A[i][j] * x[j];
            }
            x[i] /= A[i][i];
        }
        
        return x;
    }
};
```

### 3.2 金融应用

```cpp
// 资本资产定价模型 (CAPM)
class CAPM {
public:
    struct Result {
        double alpha;       // Jensen's alpha
        double beta;        // 系统性风险
        double r_squared;
        double tracking_error;
    };
    
    static Result estimate(const std::vector<double>& asset_returns,
                          const std::vector<double>& market_returns,
                          double risk_free_rate = 0) {
        // 计算超额收益
        std::vector<double> excess_asset, excess_market;
        
        for (size_t i = 0; i < asset_returns.size(); i++) {
            excess_asset.push_back(asset_returns[i] - risk_free_rate);
            excess_market.push_back(market_returns[i] - risk_free_rate);
        }
        
        auto reg = Regression::simple_linear(excess_market, excess_asset);
        
        return {
            reg.intercept,
            reg.slope,
            reg.r_squared,
            reg.std_error
        };
    }
};

// Fama-French 三因子模型
class FamaFrench {
public:
    struct Factors {
        std::vector<double> mkt_rf;  // 市场超额收益
        std::vector<double> smb;     // 小盘 - 大盘
        std::vector<double> hml;     // 高 B/M - 低 B/M
    };
    
    struct Result {
        double alpha;
        double beta_mkt;
        double beta_smb;
        double beta_hml;
        double r_squared;
    };
    
    static Result estimate(const std::vector<double>& returns,
                          const Factors& factors) {
        std::vector<std::vector<double>> X;
        
        for (size_t i = 0; i < returns.size(); i++) {
            X.push_back({1.0, factors.mkt_rf[i], factors.smb[i], factors.hml[i]});
        }
        
        auto betas = Regression::multiple_linear(X, returns);
        
        // 计算 R²
        double ss_tot = 0, ss_res = 0;
        double mean_y = Statistics::mean(returns);
        
        for (size_t i = 0; i < returns.size(); i++) {
            double y_pred = betas[0] + betas[1]*factors.mkt_rf[i] +
                           betas[2]*factors.smb[i] + betas[3]*factors.hml[i];
            ss_res += (returns[i] - y_pred) * (returns[i] - y_pred);
            ss_tot += (returns[i] - mean_y) * (returns[i] - mean_y);
        }
        
        return {
            betas[0], betas[1], betas[2], betas[3],
            1 - ss_res / ss_tot
        };
    }
};
```

---

## 四、风险度量

### 4.1 VaR 和 CVaR

```cpp
class RiskMetrics {
public:
    // Value at Risk（历史模拟法）
    static double var_historical(const std::vector<double>& returns,
                                 double confidence = 0.95) {
        std::vector<double> sorted = returns;
        std::sort(sorted.begin(), sorted.end());
        
        size_t idx = static_cast<size_t>((1 - confidence) * sorted.size());
        return -sorted[idx];  // VaR 通常表示为正数
    }
    
    // Value at Risk（参数法，假设正态）
    static double var_parametric(const std::vector<double>& returns,
                                 double confidence = 0.95) {
        double mu = Statistics::mean(returns);
        double sigma = Statistics::std_dev(returns);
        
        double z = Distributions::normal_inv_cdf(1 - confidence);
        return -(mu + z * sigma);
    }
    
    // Conditional VaR (Expected Shortfall)
    static double cvar(const std::vector<double>& returns,
                       double confidence = 0.95) {
        std::vector<double> sorted = returns;
        std::sort(sorted.begin(), sorted.end());
        
        size_t cutoff = static_cast<size_t>((1 - confidence) * sorted.size());
        
        double sum = 0;
        for (size_t i = 0; i < cutoff; i++) {
            sum += sorted[i];
        }
        
        return -sum / cutoff;
    }
    
    // 最大回撤
    static double max_drawdown(const std::vector<double>& prices) {
        double peak = prices[0];
        double max_dd = 0;
        
        for (double price : prices) {
            if (price > peak) {
                peak = price;
            }
            double dd = (peak - price) / peak;
            max_dd = std::max(max_dd, dd);
        }
        
        return max_dd;
    }
    
    // Sharpe Ratio
    static double sharpe_ratio(const std::vector<double>& returns,
                               double risk_free_rate = 0,
                               int annualization_factor = 252) {
        double mean_excess = Statistics::mean(returns) - risk_free_rate / annualization_factor;
        double vol = Statistics::std_dev(returns);
        
        return mean_excess / vol * std::sqrt(annualization_factor);
    }
    
    // Sortino Ratio
    static double sortino_ratio(const std::vector<double>& returns,
                                double target = 0,
                                int annualization_factor = 252) {
        double mean_excess = Statistics::mean(returns) - target / annualization_factor;
        
        // 下行标准差
        double sum_sq = 0;
        int count = 0;
        
        for (double r : returns) {
            if (r < target / annualization_factor) {
                sum_sq += (r - target / annualization_factor) * 
                         (r - target / annualization_factor);
                count++;
            }
        }
        
        double downside_std = count > 0 ? std::sqrt(sum_sq / count) : 0;
        
        return downside_std > 0 ? 
               mean_excess / downside_std * std::sqrt(annualization_factor) : 0;
    }
};
```

---

## 五、蒙特卡洛模拟

```cpp
class MonteCarloSimulation {
public:
    // 几何布朗运动模拟
    static std::vector<std::vector<double>> simulate_gbm(
        double S0,           // 初始价格
        double mu,           // 年化收益率
        double sigma,        // 年化波动率
        double T,            // 时间（年）
        int steps,           // 时间步数
        int paths,           // 路径数
        uint64_t seed = 42) {
        
        std::mt19937_64 rng(seed);
        std::normal_distribution<double> norm(0, 1);
        
        double dt = T / steps;
        double drift = (mu - 0.5 * sigma * sigma) * dt;
        double diffusion = sigma * std::sqrt(dt);
        
        std::vector<std::vector<double>> result(paths, std::vector<double>(steps + 1));
        
        for (int p = 0; p < paths; p++) {
            result[p][0] = S0;
            
            for (int t = 1; t <= steps; t++) {
                double z = norm(rng);
                result[p][t] = result[p][t-1] * std::exp(drift + diffusion * z);
            }
        }
        
        return result;
    }
    
    // 欧式期权定价
    static double price_european_option(
        double S0,           // 现价
        double K,            // 执行价
        double r,            // 无风险利率
        double sigma,        // 波动率
        double T,            // 到期时间
        bool is_call,        // Call or Put
        int num_simulations = 100000) {
        
        auto paths = simulate_gbm(S0, r, sigma, T, 1, num_simulations);
        
        double sum_payoff = 0;
        
        for (int i = 0; i < num_simulations; i++) {
            double ST = paths[i].back();
            double payoff;
            
            if (is_call) {
                payoff = std::max(0.0, ST - K);
            } else {
                payoff = std::max(0.0, K - ST);
            }
            
            sum_payoff += payoff;
        }
        
        return std::exp(-r * T) * sum_payoff / num_simulations;
    }
    
    // VaR 蒙特卡洛
    static double var_monte_carlo(
        const std::vector<double>& weights,
        const std::vector<double>& expected_returns,
        const std::vector<std::vector<double>>& cov_matrix,
        double portfolio_value,
        int horizon_days,
        double confidence,
        int num_simulations = 10000) {
        
        // Cholesky 分解
        auto L = cholesky_decomposition(cov_matrix);
        
        std::mt19937_64 rng(42);
        std::normal_distribution<double> norm(0, 1);
        
        std::vector<double> portfolio_returns;
        size_t n = weights.size();
        
        for (int sim = 0; sim < num_simulations; sim++) {
            // 生成相关的正态随机数
            std::vector<double> z(n);
            for (size_t i = 0; i < n; i++) {
                z[i] = norm(rng);
            }
            
            std::vector<double> correlated(n, 0);
            for (size_t i = 0; i < n; i++) {
                for (size_t j = 0; j <= i; j++) {
                    correlated[i] += L[i][j] * z[j];
                }
            }
            
            // 计算组合收益
            double port_return = 0;
            for (size_t i = 0; i < n; i++) {
                double asset_return = expected_returns[i] * horizon_days / 252 +
                                     correlated[i] * std::sqrt(horizon_days / 252.0);
                port_return += weights[i] * asset_return;
            }
            
            portfolio_returns.push_back(port_return);
        }
        
        return RiskMetrics::var_historical(portfolio_returns, confidence) * portfolio_value;
    }
    
private:
    static std::vector<std::vector<double>> cholesky_decomposition(
        const std::vector<std::vector<double>>& A);
};
```

---

## 六、面试常见问题

**Q: 解释 p 值的含义？**

A: p 值是在原假设为真的条件下，观察到当前或更极端结果的概率。p 值越小，拒绝原假设的证据越强。

**Q: Type I 和 Type II 错误的区别？**

| 错误类型 | 描述 | 概率 |
|----------|------|------|
| Type I | 拒绝了真实的 H0 | α（显著性水平） |
| Type II | 未能拒绝错误的 H0 | β |

**Q: VaR 的局限性？**

1. 不满足次可加性
2. 不反映尾部损失程度
3. 对分布假设敏感
4. 解决方案：使用 CVaR/Expected Shortfall

---

## 相关文章

- [量化数学-随机过程与时间序列](/articles/hft/hft-49-量化数学-随机过程与时间序列/)
- [HFT面试题-智力与概率题](/articles/hft/hft-25-HFT面试题-智力与概率题/)
- [HFT笔试题-策略回测](/articles/hft/hft-45-HFT笔试题-策略回测/)
