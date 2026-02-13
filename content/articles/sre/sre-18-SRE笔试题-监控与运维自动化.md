+++
title = "SRE笔试题-监控与运维自动化"
date = 2026-01-21
weight = 18000
description = "SRE面试笔试题精选：监控指标处理、告警逻辑、自动化脚本、配置管理、故障检测，Python3完整解答"
[taxonomies]
tags = ["SRE", "面试", "Python", "笔试", "监控", "自动化"]
+++

## 概述

监控与自动化是SRE的核心职责。本文收录与监控数据处理、告警逻辑、自动化运维相关的笔试题目，涵盖实际工作中的典型场景。

**难度标记**：⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 困难

---

## 题目1：实现指标聚合器 ⭐⭐

### 题目描述

实现一个时间序列指标聚合器，支持：
- 接收带时间戳的指标数据点
- 按时间窗口聚合（sum, avg, max, min, count）
- 查询指定时间范围的聚合结果

### 场景应用
- Prometheus风格的指标聚合
- 监控Dashboard数据源

### Python3 解答

```python
from collections import defaultdict
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time

class AggregationType(Enum):
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    COUNT = "count"
    P50 = "p50"
    P90 = "p90"
    P99 = "p99"


@dataclass
class DataPoint:
    timestamp: float
    value: float
    labels: Dict[str, str] = None


class MetricAggregator:
    """
    时间序列指标聚合器
    """
    
    def __init__(self, window_seconds: int = 60, retention_windows: int = 60):
        """
        window_seconds: 聚合窗口大小（秒）
        retention_windows: 保留多少个窗口
        """
        self.window_seconds = window_seconds
        self.retention_windows = retention_windows
        # metric_name -> window_start -> [values]
        self.data: Dict[str, Dict[int, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
    
    def _get_window(self, timestamp: float) -> int:
        """计算时间戳所属的窗口"""
        return int(timestamp // self.window_seconds) * self.window_seconds
    
    def record(self, metric_name: str, value: float, timestamp: float = None):
        """记录数据点"""
        timestamp = timestamp or time.time()
        window = self._get_window(timestamp)
        self.data[metric_name][window].append(value)
        
        # 清理过期窗口
        self._cleanup(metric_name)
    
    def _cleanup(self, metric_name: str):
        """清理过期数据"""
        current_window = self._get_window(time.time())
        min_window = current_window - (self.retention_windows * self.window_seconds)
        
        expired = [w for w in self.data[metric_name] if w < min_window]
        for w in expired:
            del self.data[metric_name][w]
    
    def query(
        self, 
        metric_name: str, 
        start_time: float, 
        end_time: float,
        aggregation: AggregationType = AggregationType.AVG
    ) -> List[tuple]:
        """
        查询时间范围内的聚合数据
        返回: [(window_start, aggregated_value), ...]
        """
        if metric_name not in self.data:
            return []
        
        start_window = self._get_window(start_time)
        end_window = self._get_window(end_time)
        
        result = []
        current = start_window
        
        while current <= end_window:
            values = self.data[metric_name].get(current, [])
            if values:
                agg_value = self._aggregate(values, aggregation)
                result.append((current, agg_value))
            current += self.window_seconds
        
        return result
    
    def _aggregate(self, values: List[float], agg_type: AggregationType) -> float:
        """执行聚合计算"""
        if not values:
            return 0.0
        
        if agg_type == AggregationType.SUM:
            return sum(values)
        elif agg_type == AggregationType.AVG:
            return sum(values) / len(values)
        elif agg_type == AggregationType.MAX:
            return max(values)
        elif agg_type == AggregationType.MIN:
            return min(values)
        elif agg_type == AggregationType.COUNT:
            return len(values)
        elif agg_type in (AggregationType.P50, AggregationType.P90, AggregationType.P99):
            return self._percentile(values, agg_type)
        
        return 0.0
    
    def _percentile(self, values: List[float], agg_type: AggregationType) -> float:
        """计算百分位数"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        percentiles = {
            AggregationType.P50: 50,
            AggregationType.P90: 90,
            AggregationType.P99: 99,
        }
        p = percentiles[agg_type]
        
        idx = (n - 1) * p / 100
        lower = int(idx)
        upper = lower + 1
        
        if upper >= n:
            return sorted_values[-1]
        
        weight = idx - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    def rate(self, metric_name: str, duration_seconds: int) -> float:
        """
        计算速率（每秒增长量）
        适用于Counter类型指标
        """
        end_time = time.time()
        start_time = end_time - duration_seconds
        
        data = self.query(metric_name, start_time, end_time, AggregationType.SUM)
        if len(data) < 2:
            return 0.0
        
        first_sum = data[0][1]
        last_sum = data[-1][1]
        
        return (last_sum - first_sum) / duration_seconds


class LabeledMetricAggregator:
    """
    支持标签的指标聚合器
    类似Prometheus的数据模型
    """
    
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        # metric_name -> label_hash -> window -> [values]
        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    def _label_hash(self, labels: Dict[str, str]) -> str:
        """计算标签哈希"""
        if not labels:
            return ""
        sorted_items = sorted(labels.items())
        return ",".join(f"{k}={v}" for k, v in sorted_items)
    
    def record(
        self, 
        metric_name: str, 
        value: float, 
        labels: Dict[str, str] = None,
        timestamp: float = None
    ):
        """记录带标签的数据点"""
        timestamp = timestamp or time.time()
        window = int(timestamp // self.window_seconds) * self.window_seconds
        label_hash = self._label_hash(labels or {})
        
        self.data[metric_name][label_hash][window].append(value)
    
    def query_by_labels(
        self,
        metric_name: str,
        labels: Dict[str, str],
        start_time: float,
        end_time: float,
        aggregation: AggregationType = AggregationType.AVG
    ) -> List[tuple]:
        """按标签查询"""
        label_hash = self._label_hash(labels or {})
        
        if metric_name not in self.data:
            return []
        if label_hash not in self.data[metric_name]:
            return []
        
        windows_data = self.data[metric_name][label_hash]
        result = []
        
        start_window = int(start_time // self.window_seconds) * self.window_seconds
        end_window = int(end_time // self.window_seconds) * self.window_seconds
        
        current = start_window
        while current <= end_window:
            values = windows_data.get(current, [])
            if values:
                agg_value = self._aggregate(values, aggregation)
                result.append((current, agg_value))
            current += self.window_seconds
        
        return result
    
    def _aggregate(self, values: List[float], agg_type: AggregationType) -> float:
        if not values:
            return 0.0
        
        if agg_type == AggregationType.SUM:
            return sum(values)
        elif agg_type == AggregationType.AVG:
            return sum(values) / len(values)
        elif agg_type == AggregationType.MAX:
            return max(values)
        elif agg_type == AggregationType.MIN:
            return min(values)
        elif agg_type == AggregationType.COUNT:
            return len(values)
        
        return 0.0
```

### 考察点
- 时间序列数据模型
- 聚合算法
- 标签系统设计

---

## 题目2：实现告警规则引擎 ⭐⭐⭐

### 题目描述

实现一个告警规则引擎，支持：
- 定义告警规则（阈值、持续时间）
- 评估指标是否触发告警
- 告警状态机（pending -> firing -> resolved）
- 告警抑制和静默

### Python3 解答

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import time

class AlertState(Enum):
    INACTIVE = "inactive"
    PENDING = "pending"
    FIRING = "firing"


class Operator(Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NE = "!="


@dataclass
class AlertRule:
    name: str
    metric_name: str
    operator: Operator
    threshold: float
    for_duration: int = 0  # 持续多少秒才告警
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    rule_name: str
    state: AlertState
    value: float
    started_at: float
    fired_at: Optional[float] = None
    resolved_at: Optional[float] = None
    labels: Dict[str, str] = field(default_factory=dict)


class AlertManager:
    """
    告警规则引擎
    """
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.silences: List[Dict] = []
        self.handlers: List[Callable[[Alert], None]] = []
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        self.rules.pop(rule_name, None)
        self.alerts.pop(rule_name, None)
    
    def add_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self.handlers.append(handler)
    
    def add_silence(
        self, 
        matchers: Dict[str, str], 
        start_time: float, 
        end_time: float
    ):
        """添加静默规则"""
        self.silences.append({
            'matchers': matchers,
            'start_time': start_time,
            'end_time': end_time
        })
    
    def _is_silenced(self, alert: Alert) -> bool:
        """检查告警是否被静默"""
        now = time.time()
        
        for silence in self.silences:
            if silence['start_time'] <= now <= silence['end_time']:
                matchers = silence['matchers']
                if all(
                    alert.labels.get(k) == v 
                    for k, v in matchers.items()
                ):
                    return True
        return False
    
    def _evaluate_condition(
        self, 
        value: float, 
        operator: Operator, 
        threshold: float
    ) -> bool:
        """评估条件"""
        ops = {
            Operator.GT: lambda v, t: v > t,
            Operator.GTE: lambda v, t: v >= t,
            Operator.LT: lambda v, t: v < t,
            Operator.LTE: lambda v, t: v <= t,
            Operator.EQ: lambda v, t: v == t,
            Operator.NE: lambda v, t: v != t,
        }
        return ops[operator](value, threshold)
    
    def evaluate(self, metrics: Dict[str, float]):
        """
        评估所有规则
        metrics: {metric_name: current_value}
        """
        now = time.time()
        
        for rule_name, rule in self.rules.items():
            if rule.metric_name not in metrics:
                continue
            
            value = metrics[rule.metric_name]
            is_triggered = self._evaluate_condition(
                value, rule.operator, rule.threshold
            )
            
            current_alert = self.alerts.get(rule_name)
            
            if is_triggered:
                if current_alert is None:
                    # 新告警 -> pending
                    self.alerts[rule_name] = Alert(
                        rule_name=rule_name,
                        state=AlertState.PENDING,
                        value=value,
                        started_at=now,
                        labels=rule.labels.copy()
                    )
                elif current_alert.state == AlertState.PENDING:
                    # 检查是否满足持续时间
                    if now - current_alert.started_at >= rule.for_duration:
                        current_alert.state = AlertState.FIRING
                        current_alert.fired_at = now
                        current_alert.value = value
                        self._fire_alert(current_alert)
                elif current_alert.state == AlertState.FIRING:
                    # 更新值
                    current_alert.value = value
            else:
                if current_alert and current_alert.state in (AlertState.PENDING, AlertState.FIRING):
                    # 告警恢复
                    if current_alert.state == AlertState.FIRING:
                        current_alert.resolved_at = now
                        self._resolve_alert(current_alert)
                    del self.alerts[rule_name]
    
    def _fire_alert(self, alert: Alert):
        """触发告警"""
        if self._is_silenced(alert):
            return
        
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Handler error: {e}")
    
    def _resolve_alert(self, alert: Alert):
        """告警恢复"""
        alert.state = AlertState.INACTIVE
        
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Handler error: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """获取所有活跃告警"""
        return [
            a for a in self.alerts.values() 
            if a.state in (AlertState.PENDING, AlertState.FIRING)
        ]


# 告警聚合器
class AlertGrouper:
    """
    告警聚合
    相同标签的告警聚合在一起发送
    """
    
    def __init__(self, group_by: List[str], group_wait: int = 30):
        """
        group_by: 按哪些标签聚合
        group_wait: 聚合等待时间（秒）
        """
        self.group_by = group_by
        self.group_wait = group_wait
        self.groups: Dict[str, List[Alert]] = {}
        self.group_times: Dict[str, float] = {}
    
    def add_alert(self, alert: Alert):
        """添加告警到组"""
        group_key = self._get_group_key(alert)
        
        if group_key not in self.groups:
            self.groups[group_key] = []
            self.group_times[group_key] = time.time()
        
        self.groups[group_key].append(alert)
    
    def _get_group_key(self, alert: Alert) -> str:
        """计算告警的分组key"""
        values = [alert.labels.get(k, "") for k in self.group_by]
        return ",".join(values)
    
    def get_ready_groups(self) -> List[List[Alert]]:
        """获取可以发送的告警组"""
        now = time.time()
        ready = []
        
        for group_key, alerts in list(self.groups.items()):
            if now - self.group_times[group_key] >= self.group_wait:
                ready.append(alerts)
                del self.groups[group_key]
                del self.group_times[group_key]
        
        return ready


# 使用示例
def send_alert(alert: Alert):
    print(f"[{alert.state.value}] {alert.rule_name}: {alert.value}")

manager = AlertManager()
manager.add_handler(send_alert)

# 添加规则
manager.add_rule(AlertRule(
    name="high_cpu",
    metric_name="cpu_usage",
    operator=Operator.GT,
    threshold=80,
    for_duration=60,
    labels={"severity": "warning"}
))

# 评估
manager.evaluate({"cpu_usage": 85})
```

### 考察点
- 告警状态机
- 规则引擎设计
- 告警聚合与抑制

---

## 题目3：实现自动扩缩容策略 ⭐⭐⭐

### 题目描述

实现一个HPA（Horizontal Pod Autoscaler）风格的自动扩缩容决策器。

### Python3 解答

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import time
import math

class ScaleDirection(Enum):
    UP = "up"
    DOWN = "down"
    NONE = "none"


@dataclass
class ScaleDecision:
    direction: ScaleDirection
    current_replicas: int
    desired_replicas: int
    reason: str


@dataclass 
class HPAConfig:
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_percent: float = 50.0
    scale_up_stabilization: int = 0  # 秒
    scale_down_stabilization: int = 300  # 秒
    scale_up_step: int = 4  # 单次最多扩容数
    scale_down_step: int = 1  # 单次最多缩容数


class HorizontalPodAutoscaler:
    """
    水平Pod自动扩缩容
    """
    
    def __init__(self, config: HPAConfig):
        self.config = config
        self.scale_up_history: List[tuple] = []  # (timestamp, desired)
        self.scale_down_history: List[tuple] = []
    
    def calculate_desired_replicas(
        self, 
        current_replicas: int, 
        current_cpu_percent: float
    ) -> ScaleDecision:
        """
        计算期望的副本数
        公式: desired = ceil(current * (currentMetric / targetMetric))
        """
        if current_replicas == 0:
            return ScaleDecision(
                direction=ScaleDirection.UP,
                current_replicas=0,
                desired_replicas=self.config.min_replicas,
                reason="No replicas running"
            )
        
        # 计算期望副本数
        ratio = current_cpu_percent / self.config.target_cpu_percent
        raw_desired = math.ceil(current_replicas * ratio)
        
        # 应用边界限制
        desired = max(self.config.min_replicas, 
                     min(self.config.max_replicas, raw_desired))
        
        # 确定方向
        if desired > current_replicas:
            direction = ScaleDirection.UP
            # 限制单次扩容幅度
            max_scale_up = current_replicas + self.config.scale_up_step
            desired = min(desired, max_scale_up)
            reason = f"CPU {current_cpu_percent}% > target {self.config.target_cpu_percent}%"
        elif desired < current_replicas:
            direction = ScaleDirection.DOWN
            # 限制单次缩容幅度
            min_scale_down = current_replicas - self.config.scale_down_step
            desired = max(desired, min_scale_down, self.config.min_replicas)
            reason = f"CPU {current_cpu_percent}% < target {self.config.target_cpu_percent}%"
        else:
            direction = ScaleDirection.NONE
            reason = "CPU within target range"
        
        return ScaleDecision(
            direction=direction,
            current_replicas=current_replicas,
            desired_replicas=desired,
            reason=reason
        )
    
    def should_scale(
        self, 
        current_replicas: int, 
        current_cpu_percent: float
    ) -> Optional[ScaleDecision]:
        """
        考虑稳定窗口后的扩缩容决策
        """
        decision = self.calculate_desired_replicas(
            current_replicas, current_cpu_percent
        )
        now = time.time()
        
        if decision.direction == ScaleDirection.UP:
            # 记录扩容建议
            self.scale_up_history.append((now, decision.desired_replicas))
            self._cleanup_history(self.scale_up_history, 
                                 self.config.scale_up_stabilization)
            
            # 检查稳定窗口
            if self._is_stable(self.scale_up_history, 
                              self.config.scale_up_stabilization):
                # 取窗口内最大值
                max_desired = max(d for _, d in self.scale_up_history)
                decision.desired_replicas = max_desired
                return decision
            
        elif decision.direction == ScaleDirection.DOWN:
            # 记录缩容建议
            self.scale_down_history.append((now, decision.desired_replicas))
            self._cleanup_history(self.scale_down_history,
                                 self.config.scale_down_stabilization)
            
            # 检查稳定窗口
            if self._is_stable(self.scale_down_history,
                              self.config.scale_down_stabilization):
                # 取窗口内最小值（保守缩容）
                min_desired = min(d for _, d in self.scale_down_history)
                decision.desired_replicas = min_desired
                return decision
        
        return None  # 不执行扩缩容
    
    def _cleanup_history(self, history: List[tuple], window: int):
        """清理过期历史"""
        cutoff = time.time() - window
        while history and history[0][0] < cutoff:
            history.pop(0)
    
    def _is_stable(self, history: List[tuple], window: int) -> bool:
        """检查是否在稳定窗口内一致"""
        if not history:
            return False
        
        oldest = history[0][0]
        return time.time() - oldest >= window


class PredictiveAutoscaler:
    """
    预测性自动扩缩容
    基于历史数据预测未来负载
    """
    
    def __init__(self, config: HPAConfig, history_window: int = 3600):
        self.config = config
        self.history_window = history_window
        self.cpu_history: List[tuple] = []  # (timestamp, cpu_percent)
    
    def record_metric(self, cpu_percent: float):
        """记录CPU指标"""
        now = time.time()
        self.cpu_history.append((now, cpu_percent))
        
        # 清理过期数据
        cutoff = now - self.history_window
        while self.cpu_history and self.cpu_history[0][0] < cutoff:
            self.cpu_history.pop(0)
    
    def predict_load(self, future_seconds: int = 300) -> float:
        """
        简单的负载预测
        使用线性回归预测未来CPU
        """
        if len(self.cpu_history) < 10:
            return self.cpu_history[-1][1] if self.cpu_history else 0
        
        # 简单线性回归
        n = len(self.cpu_history)
        now = time.time()
        
        sum_x = sum(t - now for t, _ in self.cpu_history)
        sum_y = sum(v for _, v in self.cpu_history)
        sum_xy = sum((t - now) * v for t, v in self.cpu_history)
        sum_x2 = sum((t - now) ** 2 for t, _ in self.cpu_history)
        
        # 斜率
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2 + 1e-10)
        # 截距
        intercept = (sum_y - slope * sum_x) / n
        
        # 预测
        predicted = intercept + slope * future_seconds
        
        # 限制在合理范围
        return max(0, min(100, predicted))
    
    def calculate_proactive_replicas(
        self, 
        current_replicas: int,
        current_cpu: float
    ) -> int:
        """
        基于预测计算副本数
        """
        # 预测5分钟后的CPU
        predicted_cpu = self.predict_load(300)
        
        # 取当前和预测的较大值
        target_cpu = max(current_cpu, predicted_cpu)
        
        ratio = target_cpu / self.config.target_cpu_percent
        desired = math.ceil(current_replicas * ratio)
        
        return max(self.config.min_replicas, 
                  min(self.config.max_replicas, desired))
```

### 考察点
- HPA算法原理
- 扩缩容稳定窗口
- 预测性扩缩容

---

## 题目4：实现配置热加载 ⭐⭐

### 题目描述

实现一个支持热加载的配置管理器，当配置文件变更时自动重新加载。

### Python3 解答

```python
import json
import yaml
import hashlib
import threading
import time
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

class ConfigLoader(ABC):
    """配置加载器抽象类"""
    
    @abstractmethod
    def load(self, path: str) -> Dict[str, Any]:
        pass


class JSONConfigLoader(ConfigLoader):
    def load(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return json.load(f)


class YAMLConfigLoader(ConfigLoader):
    def load(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return yaml.safe_load(f)


class ConfigManager:
    """
    配置管理器
    支持热加载和变更回调
    """
    
    def __init__(self, config_path: str, auto_reload: bool = True, 
                 reload_interval: int = 5):
        self.config_path = config_path
        self.auto_reload = auto_reload
        self.reload_interval = reload_interval
        
        self.config: Dict[str, Any] = {}
        self.config_hash: str = ""
        self.callbacks: List[Callable[[Dict, Dict], None]] = []
        self.lock = threading.RLock()
        
        # 选择加载器
        if config_path.endswith('.json'):
            self.loader = JSONConfigLoader()
        elif config_path.endswith(('.yml', '.yaml')):
            self.loader = YAMLConfigLoader()
        else:
            raise ValueError(f"Unsupported config format: {config_path}")
        
        # 初始加载
        self._load_config()
        
        # 启动自动重载
        if auto_reload:
            self._start_watcher()
    
    def _compute_hash(self, config: Dict) -> str:
        """计算配置哈希"""
        content = json.dumps(config, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_config(self) -> bool:
        """加载配置，返回是否有变更"""
        try:
            new_config = self.loader.load(self.config_path)
            new_hash = self._compute_hash(new_config)
            
            with self.lock:
                if new_hash != self.config_hash:
                    old_config = self.config.copy()
                    self.config = new_config
                    self.config_hash = new_hash
                    
                    # 触发回调
                    self._notify_callbacks(old_config, new_config)
                    return True
            
            return False
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False
    
    def _notify_callbacks(self, old_config: Dict, new_config: Dict):
        """通知所有回调"""
        for callback in self.callbacks:
            try:
                callback(old_config, new_config)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def _start_watcher(self):
        """启动配置监视线程"""
        def watcher():
            while True:
                time.sleep(self.reload_interval)
                self._load_config()
        
        thread = threading.Thread(target=watcher, daemon=True)
        thread.start()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔的嵌套key"""
        with self.lock:
            value = self.config
            for part in key.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return default
                if value is None:
                    return default
            return value
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        with self.lock:
            return self.config.copy()
    
    def on_change(self, callback: Callable[[Dict, Dict], None]):
        """注册配置变更回调"""
        self.callbacks.append(callback)
    
    def reload(self) -> bool:
        """手动重新加载配置"""
        return self._load_config()


class FeatureFlags:
    """
    特性开关管理
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.overrides: Dict[str, bool] = {}
    
    def is_enabled(self, feature: str, default: bool = False) -> bool:
        """检查特性是否启用"""
        # 先检查覆盖
        if feature in self.overrides:
            return self.overrides[feature]
        
        # 从配置读取
        flags = self.config_manager.get('feature_flags', {})
        return flags.get(feature, default)
    
    def override(self, feature: str, enabled: bool):
        """临时覆盖特性状态"""
        self.overrides[feature] = enabled
    
    def clear_override(self, feature: str):
        """清除覆盖"""
        self.overrides.pop(feature, None)


class ConfigValidator:
    """
    配置验证器
    """
    
    def __init__(self):
        self.rules: Dict[str, Callable[[Any], bool]] = {}
    
    def add_rule(self, key: str, validator: Callable[[Any], bool], 
                 error_message: str = ""):
        """添加验证规则"""
        self.rules[key] = (validator, error_message)
    
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        for key, (validator, message) in self.rules.items():
            value = config
            for part in key.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            
            if value is not None:
                try:
                    if not validator(value):
                        errors.append(message or f"Validation failed for {key}")
                except Exception as e:
                    errors.append(f"Validation error for {key}: {e}")
        
        return errors


# 使用示例
def on_config_change(old: Dict, new: Dict):
    print(f"Config changed!")
    # 重新初始化相关组件

config = ConfigManager('/etc/app/config.yaml')
config.on_change(on_config_change)

# 使用配置
db_host = config.get('database.host', 'localhost')
db_port = config.get('database.port', 5432)
```

### 考察点
- 文件监控
- 配置热加载
- 观察者模式

---

## 题目5：实现健康检查聚合器 ⭐⭐

### 题目描述

实现一个服务健康检查聚合器，支持多种检查类型并计算整体健康状态。

### Python3 解答

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import time
import socket
import urllib.request

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class CheckResult:
    name: str
    status: HealthStatus
    message: str
    latency_ms: float
    timestamp: float


class HealthCheck(ABC):
    """健康检查抽象类"""
    
    def __init__(self, name: str, critical: bool = True):
        self.name = name
        self.critical = critical  # 是否是关键检查
    
    @abstractmethod
    def check(self) -> CheckResult:
        pass


class TCPHealthCheck(HealthCheck):
    """TCP端口健康检查"""
    
    def __init__(self, name: str, host: str, port: int, 
                 timeout: float = 5.0, **kwargs):
        super().__init__(name, **kwargs)
        self.host = host
        self.port = port
        self.timeout = timeout
    
    def check(self) -> CheckResult:
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            latency = (time.time() - start) * 1000
            
            if result == 0:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message=f"Port {self.port} is open",
                    latency_ms=latency,
                    timestamp=time.time()
                )
            else:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Port {self.port} is closed",
                    latency_ms=latency,
                    timestamp=time.time()
                )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(time.time() - start) * 1000,
                timestamp=time.time()
            )


class HTTPHealthCheck(HealthCheck):
    """HTTP健康检查"""
    
    def __init__(self, name: str, url: str, 
                 expected_status: int = 200,
                 timeout: float = 5.0, **kwargs):
        super().__init__(name, **kwargs)
        self.url = url
        self.expected_status = expected_status
        self.timeout = timeout
    
    def check(self) -> CheckResult:
        start = time.time()
        try:
            request = urllib.request.Request(self.url)
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status_code = response.getcode()
                latency = (time.time() - start) * 1000
                
                if status_code == self.expected_status:
                    return CheckResult(
                        name=self.name,
                        status=HealthStatus.HEALTHY,
                        message=f"HTTP {status_code}",
                        latency_ms=latency,
                        timestamp=time.time()
                    )
                else:
                    return CheckResult(
                        name=self.name,
                        status=HealthStatus.DEGRADED,
                        message=f"Expected {self.expected_status}, got {status_code}",
                        latency_ms=latency,
                        timestamp=time.time()
                    )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(time.time() - start) * 1000,
                timestamp=time.time()
            )


class DiskHealthCheck(HealthCheck):
    """磁盘空间健康检查"""
    
    def __init__(self, name: str, path: str, 
                 warning_threshold: float = 80,
                 critical_threshold: float = 90, **kwargs):
        super().__init__(name, **kwargs)
        self.path = path
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
    
    def check(self) -> CheckResult:
        start = time.time()
        try:
            import shutil
            usage = shutil.disk_usage(self.path)
            used_percent = (usage.used / usage.total) * 100
            latency = (time.time() - start) * 1000
            
            if used_percent >= self.critical_threshold:
                status = HealthStatus.UNHEALTHY
            elif used_percent >= self.warning_threshold:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return CheckResult(
                name=self.name,
                status=status,
                message=f"Disk usage: {used_percent:.1f}%",
                latency_ms=latency,
                timestamp=time.time()
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(time.time() - start) * 1000,
                timestamp=time.time()
            )


class MemoryHealthCheck(HealthCheck):
    """内存健康检查"""
    
    def __init__(self, name: str,
                 warning_threshold: float = 80,
                 critical_threshold: float = 90, **kwargs):
        super().__init__(name, **kwargs)
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
    
    def check(self) -> CheckResult:
        start = time.time()
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            meminfo = {}
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = int(parts[1].strip().split()[0])
                    meminfo[key] = value
            
            total = meminfo.get('MemTotal', 1)
            available = meminfo.get('MemAvailable', 0)
            used_percent = ((total - available) / total) * 100
            
            latency = (time.time() - start) * 1000
            
            if used_percent >= self.critical_threshold:
                status = HealthStatus.UNHEALTHY
            elif used_percent >= self.warning_threshold:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return CheckResult(
                name=self.name,
                status=status,
                message=f"Memory usage: {used_percent:.1f}%",
                latency_ms=latency,
                timestamp=time.time()
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(time.time() - start) * 1000,
                timestamp=time.time()
            )


class HealthAggregator:
    """
    健康检查聚合器
    """
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.last_results: Dict[str, CheckResult] = {}
    
    def add_check(self, check: HealthCheck):
        """添加健康检查"""
        self.checks.append(check)
    
    def run_checks(self) -> Dict[str, CheckResult]:
        """运行所有检查"""
        results = {}
        for check in self.checks:
            result = check.check()
            results[check.name] = result
            self.last_results[check.name] = result
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """计算整体健康状态"""
        if not self.last_results:
            return HealthStatus.UNHEALTHY
        
        has_degraded = False
        
        for check in self.checks:
            result = self.last_results.get(check.name)
            if result:
                if result.status == HealthStatus.UNHEALTHY and check.critical:
                    return HealthStatus.UNHEALTHY
                if result.status == HealthStatus.DEGRADED:
                    has_degraded = True
        
        return HealthStatus.DEGRADED if has_degraded else HealthStatus.HEALTHY
    
    def get_health_report(self) -> Dict:
        """获取健康报告"""
        results = self.run_checks()
        overall = self.get_overall_status()
        
        return {
            'status': overall.value,
            'timestamp': time.time(),
            'checks': {
                name: {
                    'status': result.status.value,
                    'message': result.message,
                    'latency_ms': result.latency_ms
                }
                for name, result in results.items()
            }
        }


# 使用示例
aggregator = HealthAggregator()
aggregator.add_check(TCPHealthCheck("database", "localhost", 5432))
aggregator.add_check(HTTPHealthCheck("api", "http://localhost:8080/health"))
aggregator.add_check(DiskHealthCheck("disk", "/", critical=False))
aggregator.add_check(MemoryHealthCheck("memory"))

report = aggregator.get_health_report()
print(report)
```

### 考察点
- 健康检查设计
- 策略模式
- 状态聚合逻辑

---

## 题目6：实现批量SSH执行器 ⭐⭐

### 题目描述

实现一个批量SSH命令执行器，支持并发执行和结果收集。

### Python3 解答

```python
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import time

@dataclass
class SSHResult:
    host: str
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    success: bool


class SSHExecutor:
    """
    批量SSH执行器
    使用subprocess调用ssh命令
    """
    
    def __init__(
        self, 
        user: str = "root",
        ssh_key: str = None,
        timeout: int = 30,
        max_workers: int = 10
    ):
        self.user = user
        self.ssh_key = ssh_key
        self.timeout = timeout
        self.max_workers = max_workers
    
    def _build_ssh_command(self, host: str, command: str) -> List[str]:
        """构建SSH命令"""
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no",
                   "-o", "ConnectTimeout=10"]
        
        if self.ssh_key:
            ssh_cmd.extend(["-i", self.ssh_key])
        
        ssh_cmd.append(f"{self.user}@{host}")
        ssh_cmd.append(command)
        
        return ssh_cmd
    
    def execute(self, host: str, command: str) -> SSHResult:
        """在单个主机上执行命令"""
        ssh_cmd = self._build_ssh_command(host, command)
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            return SSHResult(
                host=host,
                command=command,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration,
                success=(result.returncode == 0)
            )
        except subprocess.TimeoutExpired:
            return SSHResult(
                host=host,
                command=command,
                stdout="",
                stderr="Command timed out",
                exit_code=-1,
                duration_ms=self.timeout * 1000,
                success=False
            )
        except Exception as e:
            return SSHResult(
                host=host,
                command=command,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=(time.time() - start_time) * 1000,
                success=False
            )
    
    def execute_batch(
        self, 
        hosts: List[str], 
        command: str,
        callback: Callable[[SSHResult], None] = None
    ) -> Dict[str, SSHResult]:
        """在多个主机上并发执行命令"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_host = {
                executor.submit(self.execute, host, command): host
                for host in hosts
            }
            
            for future in as_completed(future_to_host):
                host = future_to_host[future]
                result = future.result()
                results[host] = result
                
                if callback:
                    callback(result)
        
        return results
    
    def execute_script(
        self, 
        hosts: List[str], 
        script_path: str
    ) -> Dict[str, SSHResult]:
        """执行本地脚本"""
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # 使用bash -s来执行脚本内容
        command = f"bash -s << 'SCRIPT_END'\n{script_content}\nSCRIPT_END"
        
        return self.execute_batch(hosts, command)


class RollingExecutor:
    """
    滚动执行器
    按批次执行，支持失败阈值
    """
    
    def __init__(
        self, 
        ssh_executor: SSHExecutor,
        batch_size: int = 5,
        failure_threshold: float = 0.3,
        pause_between_batches: int = 5
    ):
        self.executor = ssh_executor
        self.batch_size = batch_size
        self.failure_threshold = failure_threshold
        self.pause_between_batches = pause_between_batches
    
    def execute(
        self, 
        hosts: List[str], 
        command: str,
        on_batch_complete: Callable[[List[SSHResult]], bool] = None
    ) -> Dict[str, SSHResult]:
        """
        滚动执行命令
        返回所有结果，如果失败率超过阈值则提前停止
        """
        all_results = {}
        total_hosts = len(hosts)
        failed_count = 0
        
        for i in range(0, total_hosts, self.batch_size):
            batch = hosts[i:i + self.batch_size]
            batch_results = self.executor.execute_batch(batch, command)
            
            all_results.update(batch_results)
            
            # 统计失败
            batch_failures = sum(
                1 for r in batch_results.values() if not r.success
            )
            failed_count += batch_failures
            
            # 检查失败率
            completed = len(all_results)
            failure_rate = failed_count / completed
            
            if failure_rate > self.failure_threshold:
                print(f"Stopping: failure rate {failure_rate:.1%} exceeds threshold")
                break
            
            # 回调
            if on_batch_complete:
                should_continue = on_batch_complete(list(batch_results.values()))
                if not should_continue:
                    break
            
            # 批次间暂停
            if i + self.batch_size < total_hosts:
                time.sleep(self.pause_between_batches)
        
        return all_results


class AnsibleStyleExecutor:
    """
    Ansible风格的执行器
    支持主机分组和变量
    """
    
    def __init__(self, ssh_executor: SSHExecutor):
        self.executor = ssh_executor
        self.inventory: Dict[str, List[str]] = {}  # group -> hosts
        self.host_vars: Dict[str, Dict] = {}  # host -> vars
    
    def add_group(self, name: str, hosts: List[str]):
        """添加主机组"""
        self.inventory[name] = hosts
    
    def set_host_vars(self, host: str, vars: Dict):
        """设置主机变量"""
        self.host_vars[host] = vars
    
    def get_hosts(self, pattern: str) -> List[str]:
        """根据模式获取主机列表"""
        if pattern == "all":
            hosts = set()
            for group_hosts in self.inventory.values():
                hosts.update(group_hosts)
            return list(hosts)
        elif pattern in self.inventory:
            return self.inventory[pattern]
        else:
            # 支持简单的通配符
            import fnmatch
            all_hosts = self.get_hosts("all")
            return [h for h in all_hosts if fnmatch.fnmatch(h, pattern)]
    
    def run_command(
        self, 
        pattern: str, 
        command: str
    ) -> Dict[str, SSHResult]:
        """在匹配的主机上执行命令"""
        hosts = self.get_hosts(pattern)
        
        # 支持变量替换
        results = {}
        for host in hosts:
            vars = self.host_vars.get(host, {})
            host_command = command
            for key, value in vars.items():
                host_command = host_command.replace(f"{{{{ {key} }}}}", str(value))
            
            result = self.executor.execute(host, host_command)
            results[host] = result
        
        return results


# 使用示例
executor = SSHExecutor(user="deploy", ssh_key="/home/deploy/.ssh/id_rsa")

# 批量执行
results = executor.execute_batch(
    hosts=["server1", "server2", "server3"],
    command="uptime"
)

for host, result in results.items():
    print(f"{host}: {'OK' if result.success else 'FAIL'}")
    print(f"  stdout: {result.stdout.strip()}")
```

### 考察点
- SSH命令构建
- 并发执行
- 滚动部署策略
- 失败处理

---

## 题目7：实现服务降级开关 ⭐⭐

### 题目描述

实现一个熔断器（Circuit Breaker），当服务故障率过高时自动降级。

### Python3 解答

```python
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Optional
import time
import threading
from functools import wraps

class CircuitState(Enum):
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class CircuitStats:
    requests: int = 0
    failures: int = 0
    success: int = 0
    last_failure_time: float = 0


class CircuitBreaker:
    """
    熔断器实现
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        timeout: float = 30.0,
        failure_rate_threshold: float = 0.5
    ):
        """
        failure_threshold: 触发熔断的连续失败次数
        success_threshold: 半开状态恢复需要的连续成功次数
        timeout: 熔断状态持续时间
        failure_rate_threshold: 触发熔断的失败率
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.failure_rate_threshold = failure_rate_threshold
        
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self.last_state_change = time.time()
        self.consecutive_successes = 0
        self.lock = threading.Lock()
    
    def _should_trip(self) -> bool:
        """判断是否应该熔断"""
        if self.stats.requests < self.failure_threshold:
            return False
        
        failure_rate = self.stats.failures / self.stats.requests
        return failure_rate >= self.failure_rate_threshold
    
    def _try_reset(self):
        """尝试从OPEN转换到HALF_OPEN"""
        if time.time() - self.last_state_change >= self.timeout:
            self.state = CircuitState.HALF_OPEN
            self.consecutive_successes = 0
            self.last_state_change = time.time()
    
    def record_success(self):
        """记录成功调用"""
        with self.lock:
            self.stats.success += 1
            self.stats.requests += 1
            
            if self.state == CircuitState.HALF_OPEN:
                self.consecutive_successes += 1
                if self.consecutive_successes >= self.success_threshold:
                    # 恢复正常
                    self.state = CircuitState.CLOSED
                    self.stats = CircuitStats()
                    self.last_state_change = time.time()
    
    def record_failure(self):
        """记录失败调用"""
        with self.lock:
            self.stats.failures += 1
            self.stats.requests += 1
            self.stats.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态失败，重新熔断
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()
            elif self.state == CircuitState.CLOSED and self._should_trip():
                # 触发熔断
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()
    
    def allow_request(self) -> bool:
        """判断是否允许请求通过"""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                self._try_reset()
                return self.state == CircuitState.HALF_OPEN
            else:  # HALF_OPEN
                return True
    
    def call(
        self, 
        func: Callable, 
        fallback: Callable = None,
        *args, 
        **kwargs
    ) -> Any:
        """
        通过熔断器调用函数
        """
        if not self.allow_request():
            if fallback:
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpen(f"Circuit {self.name} is open")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            if fallback:
                return fallback(*args, **kwargs)
            raise


class CircuitBreakerOpen(Exception):
    """熔断器打开异常"""
    pass


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: float = 30.0,
    fallback: Callable = None
):
    """
    熔断器装饰器
    """
    breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        timeout=timeout
    )
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, fallback, *args, **kwargs)
        
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


class CircuitBreakerRegistry:
    """
    熔断器注册表
    管理多个熔断器
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.breakers = {}
        return cls._instance
    
    def get_or_create(
        self, 
        name: str, 
        **kwargs
    ) -> CircuitBreaker:
        """获取或创建熔断器"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name, **kwargs)
        return self.breakers[name]
    
    def get_all_status(self) -> dict:
        """获取所有熔断器状态"""
        return {
            name: {
                'state': breaker.state.value,
                'requests': breaker.stats.requests,
                'failures': breaker.stats.failures,
                'failure_rate': breaker.stats.failures / breaker.stats.requests 
                               if breaker.stats.requests > 0 else 0
            }
            for name, breaker in self.breakers.items()
        }


# 使用示例
@circuit_breaker(
    name="payment_service",
    failure_threshold=3,
    timeout=60,
    fallback=lambda *args: {"status": "degraded", "message": "Service unavailable"}
)
def call_payment_service(order_id: str):
    # 调用支付服务
    pass
```

### 考察点
- 熔断器模式
- 状态机设计
- 装饰器
- 降级策略

---

## 题目8：实现任务重试器 ⭐⭐

### 题目描述

实现一个支持指数退避的任务重试器。

### Python3 解答

```python
import time
import random
from typing import Callable, Any, Type, Tuple, Optional
from functools import wraps
from dataclasses import dataclass
import logging

@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: Tuple[Type[Exception], ...] = (Exception,)


class RetryExhausted(Exception):
    """重试次数耗尽"""
    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"Retry exhausted after {attempts} attempts: {last_exception}")


class Retrier:
    """
    任务重试器
    支持指数退避和抖动
    """
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.logger = logging.getLogger(__name__)
    
    def calculate_delay(self, attempt: int) -> float:
        """计算延迟时间（指数退避）"""
        delay = self.config.initial_delay * (
            self.config.exponential_base ** (attempt - 1)
        )
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # 添加随机抖动，避免惊群效应
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def execute(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """执行函数，失败时重试"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except self.config.retry_on as e:
                last_exception = e
                
                if attempt == self.config.max_attempts:
                    break
                
                delay = self.calculate_delay(attempt)
                self.logger.warning(
                    f"Attempt {attempt} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
        
        raise RetryExhausted(self.config.max_attempts, last_exception)


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] = None
):
    """
    重试装饰器
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retry_on=retry_on
    )
    retrier = Retrier(config)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    if attempt == max_attempts:
                        break
                    
                    delay = retrier.calculate_delay(attempt)
                    time.sleep(delay)
            
            raise RetryExhausted(max_attempts, last_exception)
        
        return wrapper
    
    return decorator


class AsyncRetrier:
    """
    异步重试器
    """
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """异步执行函数，失败时重试"""
        import asyncio
        
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except self.config.retry_on as e:
                last_exception = e
                
                if attempt == self.config.max_attempts:
                    break
                
                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)
        
        raise RetryExhausted(self.config.max_attempts, last_exception)
    
    def _calculate_delay(self, attempt: int) -> float:
        delay = self.config.initial_delay * (
            self.config.exponential_base ** (attempt - 1)
        )
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay


# 使用示例
@retry(
    max_attempts=3,
    initial_delay=1,
    retry_on=(ConnectionError, TimeoutError),
    on_retry=lambda attempt, e: print(f"Retry {attempt}: {e}")
)
def fetch_data(url: str):
    # 可能失败的网络请求
    pass
```

### 考察点
- 指数退避算法
- 装饰器模式
- 异常处理
- 抖动（Jitter）

---

## 总结

| 题目 | 难度 | 核心考点 | 实际应用 |
|------|------|----------|----------|
| 指标聚合器 | ⭐⭐ | 时间序列、聚合算法 | Prometheus |
| 告警规则引擎 | ⭐⭐⭐ | 状态机、规则匹配 | AlertManager |
| 自动扩缩容 | ⭐⭐⭐ | HPA算法、稳定窗口 | K8s HPA |
| 配置热加载 | ⭐⭐ | 文件监控、回调 | 配置中心 |
| 健康检查聚合 | ⭐⭐ | 策略模式、状态聚合 | 健康检查 |
| 批量SSH执行 | ⭐⭐ | 并发、滚动执行 | Ansible |
| 熔断器 | ⭐⭐ | 状态机、降级 | Hystrix |
| 任务重试 | ⭐⭐ | 指数退避、装饰器 | 可靠性 |

**SRE自动化核心能力**：
1. 理解分布式系统的故障模式
2. 设计容错和降级机制
3. 编写可靠的自动化脚本
4. 监控和告警的最佳实践

---

## 相关文章

- [上一篇：SRE笔试题-数据结构与算法](@/articles/sre/sre-17-SRE笔试题-数据结构与算法.md)
- [下一篇：SRE笔试题-SQL与数据库](@/articles/sre/sre-19-SRE笔试题-SQL与数据库.md)
