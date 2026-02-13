+++
title = "45. HFT笔试题-策略回测"
date = 2026-02-02
weight = 45000
description = "HFT笔试：回测框架、事件驱动、滑点模型、性能指标"
[taxonomies]
tags = ["HFT", "笔试", "回测", "策略", "量化"]
+++

# HFT 笔试题 - 策略回测

本文汇总 HFT 笔试中关于策略回测系统的编程题目。

---

## 题目 1：事件驱动回测引擎

**题目**：实现一个事件驱动的回测引擎框架。

**解答**：

```cpp
#include <queue>
#include <functional>
#include <memory>

// 事件基类
struct Event {
    enum Type { MarketData, Signal, Order, Fill, Timer };
    Type type;
    uint64_t timestamp;
    
    virtual ~Event() = default;
    
    bool operator>(const Event& other) const {
        return timestamp > other.timestamp;
    }
};

struct MarketDataEvent : Event {
    std::string symbol;
    double bid, ask;
    int bid_size, ask_size;
    double last_price;
    int last_size;
};

struct SignalEvent : Event {
    std::string symbol;
    double signal_value;  // 正=买, 负=卖
    double confidence;
};

struct OrderEvent : Event {
    uint64_t order_id;
    std::string symbol;
    Side side;
    double price;
    int quantity;
    OrderType order_type;
};

struct FillEvent : Event {
    uint64_t order_id;
    std::string symbol;
    Side side;
    double price;
    int quantity;
    double commission;
};

// 回测引擎
class BacktestEngine {
public:
    using EventPtr = std::shared_ptr<Event>;
    using EventHandler = std::function<void(const EventPtr&)>;
    
    void register_handler(Event::Type type, EventHandler handler) {
        handlers_[type].push_back(handler);
    }
    
    void push_event(EventPtr event) {
        event_queue_.push(event);
    }
    
    void run() {
        while (!event_queue_.empty()) {
            auto event = event_queue_.top();
            event_queue_.pop();
            
            current_time_ = event->timestamp;
            
            // 分发事件
            auto it = handlers_.find(event->type);
            if (it != handlers_.end()) {
                for (auto& handler : it->second) {
                    handler(event);
                }
            }
        }
    }
    
    uint64_t current_time() const { return current_time_; }
    
private:
    std::priority_queue<EventPtr, std::vector<EventPtr>,
        std::function<bool(const EventPtr&, const EventPtr&)>> event_queue_{
            [](const EventPtr& a, const EventPtr& b) {
                return a->timestamp > b->timestamp;
            }
        };
    
    std::unordered_map<Event::Type, std::vector<EventHandler>> handlers_;
    uint64_t current_time_ = 0;
};

// 策略基类
class Strategy {
public:
    virtual ~Strategy() = default;
    
    void attach(BacktestEngine& engine) {
        engine.register_handler(Event::MarketData,
            [this](const auto& e) {
                on_market_data(std::static_pointer_cast<MarketDataEvent>(e));
            });
        engine.register_handler(Event::Fill,
            [this](const auto& e) {
                on_fill(std::static_pointer_cast<FillEvent>(e));
            });
        engine_ = &engine;
    }
    
    virtual void on_market_data(std::shared_ptr<MarketDataEvent> event) = 0;
    virtual void on_fill(std::shared_ptr<FillEvent> event) = 0;
    
protected:
    void send_order(const std::string& symbol, Side side, 
                   double price, int quantity) {
        auto order = std::make_shared<OrderEvent>();
        order->type = Event::Order;
        order->timestamp = engine_->current_time();
        order->order_id = next_order_id_++;
        order->symbol = symbol;
        order->side = side;
        order->price = price;
        order->quantity = quantity;
        
        engine_->push_event(order);
    }
    
private:
    BacktestEngine* engine_ = nullptr;
    uint64_t next_order_id_ = 1;
};
```

---

## 题目 2：订单执行模拟器

**题目**：实现考虑市场冲击的订单执行模拟器。

**解答**：

```cpp
class ExecutionSimulator {
public:
    struct SimConfig {
        double latency_mean_us = 100;      // 平均延迟
        double latency_std_us = 20;        // 延迟标准差
        double fill_rate = 0.8;            // 成交概率
        double partial_fill_rate = 0.3;    // 部分成交概率
        double slippage_bps = 1.0;         // 滑点 (基点)
    };
    
    ExecutionSimulator(BacktestEngine& engine, SimConfig config = {})
        : engine_(engine), config_(config) {
        
        engine.register_handler(Event::Order,
            [this](const auto& e) {
                process_order(std::static_pointer_cast<OrderEvent>(e));
            });
    }
    
    void set_orderbook(const std::string& symbol, 
                       double bid, double ask, int bid_size, int ask_size) {
        orderbooks_[symbol] = {bid, ask, bid_size, ask_size};
    }
    
private:
    void process_order(std::shared_ptr<OrderEvent> order) {
        auto& book = orderbooks_[order->symbol];
        
        // 模拟延迟
        uint64_t latency = simulate_latency();
        uint64_t fill_time = engine_.current_time() + latency;
        
        // 检查是否能成交
        bool can_fill = false;
        double fill_price = 0;
        int fill_qty = 0;
        
        if (order->side == Side::Buy) {
            if (order->order_type == OrderType::Market ||
                order->price >= book.ask) {
                can_fill = true;
                fill_price = book.ask + calculate_slippage(order->quantity, book.ask_size);
                fill_qty = simulate_fill_quantity(order->quantity, book.ask_size);
            }
        } else {
            if (order->order_type == OrderType::Market ||
                order->price <= book.bid) {
                can_fill = true;
                fill_price = book.bid - calculate_slippage(order->quantity, book.bid_size);
                fill_qty = simulate_fill_quantity(order->quantity, book.bid_size);
            }
        }
        
        if (can_fill && fill_qty > 0) {
            auto fill = std::make_shared<FillEvent>();
            fill->type = Event::Fill;
            fill->timestamp = fill_time;
            fill->order_id = order->order_id;
            fill->symbol = order->symbol;
            fill->side = order->side;
            fill->price = fill_price;
            fill->quantity = fill_qty;
            fill->commission = calculate_commission(fill_qty, fill_price);
            
            engine_.push_event(fill);
            
            // 如果部分成交，可能有后续成交
            if (fill_qty < order->quantity) {
                schedule_partial_fill(order, fill_qty);
            }
        }
    }
    
    double calculate_slippage(int quantity, int available) {
        // 线性冲击模型
        double participation = static_cast<double>(quantity) / available;
        return config_.slippage_bps * participation * 0.0001;
    }
    
    int simulate_fill_quantity(int requested, int available) {
        std::uniform_real_distribution<double> dist(0, 1);
        
        if (dist(rng_) > config_.fill_rate) {
            return 0;  // 未成交
        }
        
        int max_fill = std::min(requested, available);
        
        if (dist(rng_) < config_.partial_fill_rate) {
            // 部分成交
            std::uniform_int_distribution<int> qty_dist(1, max_fill);
            return qty_dist(rng_);
        }
        
        return max_fill;
    }
    
    uint64_t simulate_latency() {
        std::normal_distribution<double> dist(config_.latency_mean_us, 
                                              config_.latency_std_us);
        return std::max(1.0, dist(rng_)) * 1000;  // 转为纳秒
    }
    
    double calculate_commission(int quantity, double price) {
        return quantity * price * 0.0001;  // 1 bps
    }
    
    struct OrderBookState {
        double bid, ask;
        int bid_size, ask_size;
    };
    
    BacktestEngine& engine_;
    SimConfig config_;
    std::unordered_map<std::string, OrderBookState> orderbooks_;
    std::mt19937 rng_{42};
};
```

---

## 题目 3：性能指标计算

**题目**：实现策略性能指标计算器，包括 Sharpe、Sortino、最大回撤等。

**解答**：

```cpp
class PerformanceCalculator {
public:
    struct Metrics {
        double total_return;
        double annualized_return;
        double volatility;
        double sharpe_ratio;
        double sortino_ratio;
        double max_drawdown;
        double max_drawdown_duration_days;
        double win_rate;
        double profit_factor;
        double avg_win;
        double avg_loss;
        int total_trades;
        double calmar_ratio;
    };
    
    void add_daily_return(double daily_return) {
        returns_.push_back(daily_return);
        
        // 更新累积收益
        if (cumulative_returns_.empty()) {
            cumulative_returns_.push_back(1 + daily_return);
        } else {
            cumulative_returns_.push_back(
                cumulative_returns_.back() * (1 + daily_return));
        }
        
        // 更新最大回撤
        if (cumulative_returns_.back() > peak_value_) {
            peak_value_ = cumulative_returns_.back();
            peak_idx_ = cumulative_returns_.size() - 1;
        }
        
        double drawdown = (peak_value_ - cumulative_returns_.back()) / peak_value_;
        if (drawdown > max_drawdown_) {
            max_drawdown_ = drawdown;
            max_drawdown_end_idx_ = cumulative_returns_.size() - 1;
            max_drawdown_start_idx_ = peak_idx_;
        }
    }
    
    void add_trade(double pnl) {
        trades_.push_back(pnl);
    }
    
    Metrics calculate(double risk_free_rate = 0.02) {
        Metrics m;
        
        // 总收益
        m.total_return = cumulative_returns_.empty() ? 0 :
            cumulative_returns_.back() - 1;
        
        // 年化收益 (假设 252 交易日)
        int days = returns_.size();
        m.annualized_return = std::pow(1 + m.total_return, 252.0 / days) - 1;
        
        // 波动率
        m.volatility = calculate_std(returns_) * std::sqrt(252);
        
        // Sharpe Ratio
        double daily_rf = risk_free_rate / 252;
        double excess_return = calculate_mean(returns_) - daily_rf;
        double daily_std = calculate_std(returns_);
        m.sharpe_ratio = (daily_std > 0) ? 
            excess_return / daily_std * std::sqrt(252) : 0;
        
        // Sortino Ratio (只考虑下行波动)
        double downside_std = calculate_downside_std(returns_, daily_rf);
        m.sortino_ratio = (downside_std > 0) ?
            excess_return / downside_std * std::sqrt(252) : 0;
        
        // 最大回撤
        m.max_drawdown = max_drawdown_;
        m.max_drawdown_duration_days = max_drawdown_end_idx_ - max_drawdown_start_idx_;
        
        // 交易统计
        calculate_trade_stats(m);
        
        // Calmar Ratio
        m.calmar_ratio = (m.max_drawdown > 0) ?
            m.annualized_return / m.max_drawdown : 0;
        
        return m;
    }
    
    void print_report(const Metrics& m) {
        printf("=== Performance Report ===\n");
        printf("Total Return:        %.2f%%\n", m.total_return * 100);
        printf("Annualized Return:   %.2f%%\n", m.annualized_return * 100);
        printf("Volatility:          %.2f%%\n", m.volatility * 100);
        printf("Sharpe Ratio:        %.2f\n", m.sharpe_ratio);
        printf("Sortino Ratio:       %.2f\n", m.sortino_ratio);
        printf("Max Drawdown:        %.2f%%\n", m.max_drawdown * 100);
        printf("Calmar Ratio:        %.2f\n", m.calmar_ratio);
        printf("\n=== Trade Statistics ===\n");
        printf("Total Trades:        %d\n", m.total_trades);
        printf("Win Rate:            %.2f%%\n", m.win_rate * 100);
        printf("Profit Factor:       %.2f\n", m.profit_factor);
        printf("Avg Win:             %.2f\n", m.avg_win);
        printf("Avg Loss:            %.2f\n", m.avg_loss);
    }
    
private:
    double calculate_mean(const std::vector<double>& v) {
        if (v.empty()) return 0;
        return std::accumulate(v.begin(), v.end(), 0.0) / v.size();
    }
    
    double calculate_std(const std::vector<double>& v) {
        if (v.size() < 2) return 0;
        double mean = calculate_mean(v);
        double sq_sum = 0;
        for (double x : v) {
            sq_sum += (x - mean) * (x - mean);
        }
        return std::sqrt(sq_sum / (v.size() - 1));
    }
    
    double calculate_downside_std(const std::vector<double>& v, double threshold) {
        std::vector<double> downside;
        for (double x : v) {
            if (x < threshold) {
                downside.push_back(x - threshold);
            }
        }
        return calculate_std(downside);
    }
    
    void calculate_trade_stats(Metrics& m) {
        m.total_trades = trades_.size();
        if (m.total_trades == 0) return;
        
        double total_profit = 0, total_loss = 0;
        int wins = 0;
        
        for (double pnl : trades_) {
            if (pnl > 0) {
                wins++;
                total_profit += pnl;
            } else {
                total_loss += std::abs(pnl);
            }
        }
        
        m.win_rate = static_cast<double>(wins) / m.total_trades;
        m.profit_factor = (total_loss > 0) ? total_profit / total_loss : 0;
        m.avg_win = (wins > 0) ? total_profit / wins : 0;
        m.avg_loss = (m.total_trades - wins > 0) ? 
            total_loss / (m.total_trades - wins) : 0;
    }
    
    std::vector<double> returns_;
    std::vector<double> cumulative_returns_;
    std::vector<double> trades_;
    double peak_value_ = 1;
    double max_drawdown_ = 0;
    size_t peak_idx_ = 0;
    size_t max_drawdown_start_idx_ = 0;
    size_t max_drawdown_end_idx_ = 0;
};
```

---

## 题目 4：市场冲击模型

**题目**：实现多种市场冲击模型。

**解答**：

```cpp
class MarketImpactModel {
public:
    virtual ~MarketImpactModel() = default;
    virtual double calculate_impact(double quantity, double adv, 
                                    double volatility, double price) = 0;
};

// 平方根模型
class SqrtImpactModel : public MarketImpactModel {
public:
    SqrtImpactModel(double eta = 0.1) : eta_(eta) {}
    
    double calculate_impact(double quantity, double adv, 
                           double volatility, double price) override {
        double participation = quantity / adv;
        return eta_ * volatility * std::sqrt(participation) * price;
    }
    
private:
    double eta_;
};

// Almgren-Chriss 模型
class AlmgrenChrissModel : public MarketImpactModel {
public:
    AlmgrenChrissModel(double gamma = 0.1, double eta = 0.05)
        : gamma_(gamma), eta_(eta) {}
    
    double calculate_impact(double quantity, double adv,
                           double volatility, double price) override {
        double participation = quantity / adv;
        
        // 临时冲击
        double temp_impact = gamma_ * volatility * 
                            std::sqrt(participation) * price;
        
        // 永久冲击
        double perm_impact = eta_ * participation * price;
        
        return temp_impact + perm_impact;
    }
    
    // 最优执行轨迹
    std::vector<double> optimal_trajectory(double total_quantity, 
                                           int num_periods,
                                           double risk_aversion) {
        std::vector<double> trajectory(num_periods);
        
        // 简化的线性轨迹
        double remaining = total_quantity;
        for (int i = 0; i < num_periods; i++) {
            int periods_left = num_periods - i;
            double trade_size = remaining / periods_left;
            trajectory[i] = trade_size;
            remaining -= trade_size;
        }
        
        return trajectory;
    }
    
private:
    double gamma_;  // 临时冲击系数
    double eta_;    // 永久冲击系数
};

// 订单流冲击模型 (Kyle Lambda)
class KyleLambdaModel : public MarketImpactModel {
public:
    void calibrate(const std::vector<double>& prices,
                   const std::vector<double>& signed_volumes) {
        // 回归: ΔP = λ * signed_volume
        double sum_xy = 0, sum_xx = 0;
        
        for (size_t i = 1; i < prices.size(); i++) {
            double dp = prices[i] - prices[i-1];
            double sv = signed_volumes[i];
            sum_xy += dp * sv;
            sum_xx += sv * sv;
        }
        
        lambda_ = sum_xy / sum_xx;
    }
    
    double calculate_impact(double quantity, double adv,
                           double volatility, double price) override {
        return lambda_ * quantity;
    }
    
    double lambda() const { return lambda_; }
    
private:
    double lambda_ = 0.0001;
};
```

---

## 题目 5：回测数据管理

**题目**：实现高效的历史数据加载和管理。

**解答**：

```cpp
class DataManager {
public:
    struct Bar {
        uint64_t timestamp;
        double open, high, low, close;
        int64_t volume;
    };
    
    struct Tick {
        uint64_t timestamp;
        double bid, ask;
        int bid_size, ask_size;
        double last, last_size;
    };
    
    // 加载 CSV 数据
    void load_csv(const std::string& symbol, const std::string& filepath) {
        std::ifstream file(filepath);
        std::string line;
        
        std::vector<Bar> bars;
        std::getline(file, line);  // 跳过 header
        
        while (std::getline(file, line)) {
            Bar bar = parse_bar(line);
            bars.push_back(bar);
        }
        
        bar_data_[symbol] = std::move(bars);
    }
    
    // 内存映射大文件
    void mmap_binary(const std::string& symbol, const std::string& filepath) {
        int fd = open(filepath.c_str(), O_RDONLY);
        struct stat sb;
        fstat(fd, &sb);
        
        void* mapped = mmap(nullptr, sb.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
        close(fd);
        
        MappedData data;
        data.ptr = mapped;
        data.size = sb.st_size;
        data.count = sb.st_size / sizeof(Tick);
        
        mmap_data_[symbol] = data;
    }
    
    // 迭代器接口
    class TickIterator {
    public:
        TickIterator(const Tick* ptr, size_t count)
            : ptr_(ptr), count_(count), index_(0) {}
        
        bool has_next() const { return index_ < count_; }
        
        const Tick& next() { return ptr_[index_++]; }
        
        void seek(uint64_t timestamp) {
            // 二分查找
            size_t lo = index_, hi = count_;
            while (lo < hi) {
                size_t mid = (lo + hi) / 2;
                if (ptr_[mid].timestamp < timestamp) {
                    lo = mid + 1;
                } else {
                    hi = mid;
                }
            }
            index_ = lo;
        }
        
    private:
        const Tick* ptr_;
        size_t count_;
        size_t index_;
    };
    
    TickIterator get_tick_iterator(const std::string& symbol) {
        auto& data = mmap_data_[symbol];
        return TickIterator(static_cast<const Tick*>(data.ptr), data.count);
    }
    
    // 多品种同步迭代
    class SyncIterator {
    public:
        void add_symbol(const std::string& symbol, TickIterator iter) {
            iterators_[symbol] = iter;
        }
        
        std::pair<std::string, Tick> next() {
            std::string next_symbol;
            uint64_t min_ts = UINT64_MAX;
            
            for (auto& [symbol, iter] : iterators_) {
                if (iter.has_next()) {
                    const Tick& tick = peek(iter);
                    if (tick.timestamp < min_ts) {
                        min_ts = tick.timestamp;
                        next_symbol = symbol;
                    }
                }
            }
            
            auto& iter = iterators_[next_symbol];
            return {next_symbol, iter.next()};
        }
        
        bool has_next() const {
            for (const auto& [symbol, iter] : iterators_) {
                if (iter.has_next()) return true;
            }
            return false;
        }
        
    private:
        std::unordered_map<std::string, TickIterator> iterators_;
    };
    
private:
    struct MappedData {
        void* ptr;
        size_t size;
        size_t count;
    };
    
    Bar parse_bar(const std::string& line);
    
    std::unordered_map<std::string, std::vector<Bar>> bar_data_;
    std::unordered_map<std::string, MappedData> mmap_data_;
};
```

---

## 题目 6：参数优化

**题目**：实现策略参数的网格搜索优化。

**解答**：

```cpp
class ParameterOptimizer {
public:
    struct Parameter {
        std::string name;
        double min_val;
        double max_val;
        double step;
    };
    
    struct OptimizationResult {
        std::map<std::string, double> params;
        double sharpe;
        double return_val;
        double max_drawdown;
    };
    
    void add_parameter(const std::string& name, double min_val, 
                       double max_val, double step) {
        params_.push_back({name, min_val, max_val, step});
    }
    
    // 网格搜索
    std::vector<OptimizationResult> grid_search(
        std::function<double(const std::map<std::string, double>&)> objective) {
        
        std::vector<OptimizationResult> results;
        std::map<std::string, double> current_params;
        
        grid_search_recursive(0, current_params, objective, results);
        
        // 按目标值排序
        std::sort(results.begin(), results.end(),
            [](const auto& a, const auto& b) {
                return a.sharpe > b.sharpe;
            });
        
        return results;
    }
    
    // Walk-forward 优化
    std::vector<OptimizationResult> walk_forward_optimization(
        const std::vector<std::pair<uint64_t, uint64_t>>& periods,
        std::function<double(const std::map<std::string, double>&,
                            uint64_t, uint64_t)> objective) {
        
        std::vector<OptimizationResult> results;
        
        for (const auto& [train_end, test_end] : periods) {
            // 在训练期优化
            auto train_objective = [&](const std::map<std::string, double>& p) {
                return objective(p, 0, train_end);
            };
            
            auto train_results = grid_search(train_objective);
            
            if (!train_results.empty()) {
                // 在测试期验证
                auto& best_params = train_results[0].params;
                double test_sharpe = objective(best_params, train_end, test_end);
                
                OptimizationResult r;
                r.params = best_params;
                r.sharpe = test_sharpe;
                results.push_back(r);
            }
        }
        
        return results;
    }
    
private:
    void grid_search_recursive(
        size_t param_idx,
        std::map<std::string, double>& current_params,
        std::function<double(const std::map<std::string, double>&)>& objective,
        std::vector<OptimizationResult>& results) {
        
        if (param_idx >= params_.size()) {
            // 评估当前参数组合
            double sharpe = objective(current_params);
            
            OptimizationResult r;
            r.params = current_params;
            r.sharpe = sharpe;
            results.push_back(r);
            return;
        }
        
        const auto& param = params_[param_idx];
        
        for (double val = param.min_val; val <= param.max_val; val += param.step) {
            current_params[param.name] = val;
            grid_search_recursive(param_idx + 1, current_params, objective, results);
        }
    }
    
    std::vector<Parameter> params_;
};

// 使用示例
void optimize_strategy() {
    ParameterOptimizer optimizer;
    optimizer.add_parameter("fast_period", 5, 20, 5);
    optimizer.add_parameter("slow_period", 20, 60, 10);
    optimizer.add_parameter("threshold", 0.5, 2.0, 0.5);
    
    auto objective = [](const std::map<std::string, double>& params) {
        // 运行回测，返回 Sharpe
        BacktestEngine engine;
        MyStrategy strategy(params);
        strategy.attach(engine);
        // ... 加载数据，运行回测
        return strategy.calculate_sharpe();
    };
    
    auto results = optimizer.grid_search(objective);
    
    std::cout << "Best parameters:\n";
    for (const auto& [name, val] : results[0].params) {
        std::cout << name << " = " << val << "\n";
    }
    std::cout << "Sharpe: " << results[0].sharpe << "\n";
}
```

---

## 相关文章

- [回测系统设计与实现](@/articles/quant/quant-08-回测系统设计与实现.md)
- [HFT策略类型全景](@/articles/hft/hft-39-HFT策略类型全景.md)
- [市场微结构深度解析](@/articles/hft/hft-38-市场微结构深度解析.md)
