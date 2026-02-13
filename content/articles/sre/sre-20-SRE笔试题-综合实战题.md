+++
title = "SRE笔试题-综合实战题"
date = 2026-01-21
weight = 20000
description = "SRE面试笔试题精选：接近真实场景的综合题目，故障排查、系统设计、自动化脚本，Python3完整解答"
[taxonomies]
tags = ["SRE", "面试", "Python", "笔试", "实战", "系统设计"]
+++

## 概述

本文收录接近真实工作场景的综合实战题，考察候选人将多种技能结合解决实际问题的能力。这类题目通常出现在SRE面试的后期轮次，难度较高。

**难度标记**：⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 困难

---

## 题目1：设计服务健康评分系统 ⭐⭐⭐

### 题目描述

设计并实现一个服务健康评分系统，根据多个指标计算服务的综合健康分数（0-100分）。

**要求**：
1. 支持多种指标类型（可用性、延迟、错误率、资源使用率）
2. 不同指标有不同权重
3. 支持告警阈值配置
4. 能够追踪分数变化趋势

### Python3 完整实现

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
import math

class MetricType(Enum):
    AVAILABILITY = "availability"      # 可用性 (0-100%)
    LATENCY_P99 = "latency_p99"        # P99延迟 (ms)
    ERROR_RATE = "error_rate"          # 错误率 (0-100%)
    CPU_USAGE = "cpu_usage"            # CPU使用率 (0-100%)
    MEMORY_USAGE = "memory_usage"      # 内存使用率 (0-100%)
    SATURATION = "saturation"          # 饱和度 (0-100%)


@dataclass
class MetricConfig:
    """指标配置"""
    metric_type: MetricType
    weight: float                      # 权重 (0-1)
    good_threshold: float              # 良好阈值
    bad_threshold: float               # 差阈值
    higher_is_better: bool = True      # True: 越高越好, False: 越低越好
    
    def calculate_score(self, value: float) -> float:
        """
        计算单个指标的分数 (0-100)
        使用线性映射
        """
        if self.higher_is_better:
            # 可用性等：越高越好
            if value >= self.good_threshold:
                return 100.0
            elif value <= self.bad_threshold:
                return 0.0
            else:
                return (value - self.bad_threshold) / (self.good_threshold - self.bad_threshold) * 100
        else:
            # 延迟、错误率等：越低越好
            if value <= self.good_threshold:
                return 100.0
            elif value >= self.bad_threshold:
                return 0.0
            else:
                return (self.bad_threshold - value) / (self.bad_threshold - self.good_threshold) * 100


@dataclass
class HealthScore:
    """健康分数"""
    service: str
    total_score: float
    metric_scores: Dict[str, float]
    timestamp: datetime
    status: str  # healthy, degraded, unhealthy
    
    @staticmethod
    def status_from_score(score: float) -> str:
        if score >= 80:
            return "healthy"
        elif score >= 50:
            return "degraded"
        else:
            return "unhealthy"


class HealthScoreCalculator:
    """
    服务健康评分计算器
    """
    
    # 默认指标配置
    DEFAULT_CONFIGS = {
        MetricType.AVAILABILITY: MetricConfig(
            metric_type=MetricType.AVAILABILITY,
            weight=0.30,
            good_threshold=99.9,
            bad_threshold=95.0,
            higher_is_better=True
        ),
        MetricType.LATENCY_P99: MetricConfig(
            metric_type=MetricType.LATENCY_P99,
            weight=0.25,
            good_threshold=100,    # ms
            bad_threshold=1000,    # ms
            higher_is_better=False
        ),
        MetricType.ERROR_RATE: MetricConfig(
            metric_type=MetricType.ERROR_RATE,
            weight=0.25,
            good_threshold=0.1,    # %
            bad_threshold=5.0,     # %
            higher_is_better=False
        ),
        MetricType.CPU_USAGE: MetricConfig(
            metric_type=MetricType.CPU_USAGE,
            weight=0.10,
            good_threshold=60,     # %
            bad_threshold=90,      # %
            higher_is_better=False
        ),
        MetricType.MEMORY_USAGE: MetricConfig(
            metric_type=MetricType.MEMORY_USAGE,
            weight=0.10,
            good_threshold=70,     # %
            bad_threshold=95,      # %
            higher_is_better=False
        ),
    }
    
    def __init__(self, configs: Dict[MetricType, MetricConfig] = None):
        self.configs = configs or self.DEFAULT_CONFIGS.copy()
        self._validate_weights()
    
    def _validate_weights(self):
        """验证权重总和为1"""
        total_weight = sum(c.weight for c in self.configs.values())
        if abs(total_weight - 1.0) > 0.001:
            # 归一化权重
            for config in self.configs.values():
                config.weight /= total_weight
    
    def calculate(
        self, 
        service: str, 
        metrics: Dict[MetricType, float]
    ) -> HealthScore:
        """
        计算服务健康分数
        """
        metric_scores = {}
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_type, value in metrics.items():
            if metric_type in self.configs:
                config = self.configs[metric_type]
                score = config.calculate_score(value)
                metric_scores[metric_type.value] = round(score, 2)
                weighted_sum += score * config.weight
                total_weight += config.weight
        
        # 如果只提供了部分指标，按已有权重归一化
        if total_weight > 0:
            total_score = weighted_sum / total_weight
        else:
            total_score = 0.0
        
        total_score = round(total_score, 2)
        
        return HealthScore(
            service=service,
            total_score=total_score,
            metric_scores=metric_scores,
            timestamp=datetime.now(),
            status=HealthScore.status_from_score(total_score)
        )


class HealthScoreTracker:
    """
    健康分数追踪器
    记录历史分数，支持趋势分析
    """
    
    def __init__(self, history_size: int = 1440):  # 默认保留24小时（每分钟一个点）
        self.calculator = HealthScoreCalculator()
        self.history: Dict[str, deque] = {}  # service -> scores
        self.history_size = history_size
        self.alert_thresholds = {
            'critical': 50,
            'warning': 70
        }
        self.alert_callbacks: List[Callable] = []
    
    def record(self, service: str, metrics: Dict[MetricType, float]) -> HealthScore:
        """记录一次健康分数"""
        score = self.calculator.calculate(service, metrics)
        
        if service not in self.history:
            self.history[service] = deque(maxlen=self.history_size)
        
        self.history[service].append(score)
        
        # 检查告警
        self._check_alerts(score)
        
        return score
    
    def _check_alerts(self, score: HealthScore):
        """检查是否需要告警"""
        if score.total_score < self.alert_thresholds['critical']:
            self._fire_alert(score, 'critical')
        elif score.total_score < self.alert_thresholds['warning']:
            self._fire_alert(score, 'warning')
    
    def _fire_alert(self, score: HealthScore, severity: str):
        """触发告警"""
        for callback in self.alert_callbacks:
            try:
                callback(score, severity)
            except Exception:
                pass
    
    def on_alert(self, callback: Callable):
        """注册告警回调"""
        self.alert_callbacks.append(callback)
    
    def get_trend(self, service: str, duration_minutes: int = 60) -> Dict:
        """
        获取分数趋势
        """
        if service not in self.history:
            return {'available': False}
        
        scores = list(self.history[service])
        if len(scores) < 2:
            return {'available': False}
        
        # 取最近duration_minutes的数据
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_scores = [s for s in scores if s.timestamp >= cutoff_time]
        
        if len(recent_scores) < 2:
            return {'available': False}
        
        values = [s.total_score for s in recent_scores]
        
        # 计算趋势
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 5:
            trend = 'improving'
        elif second_avg < first_avg - 5:
            trend = 'degrading'
        else:
            trend = 'stable'
        
        return {
            'available': True,
            'trend': trend,
            'current': values[-1],
            'avg': round(sum(values) / len(values), 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'change': round(second_avg - first_avg, 2)
        }
    
    def get_dashboard_data(self) -> Dict:
        """
        获取Dashboard展示数据
        """
        services_data = []
        
        for service, scores in self.history.items():
            if scores:
                latest = scores[-1]
                trend = self.get_trend(service, 60)
                
                services_data.append({
                    'service': service,
                    'score': latest.total_score,
                    'status': latest.status,
                    'metrics': latest.metric_scores,
                    'trend': trend.get('trend', 'unknown'),
                    'change_1h': trend.get('change', 0)
                })
        
        # 按分数排序，分数低的在前
        services_data.sort(key=lambda x: x['score'])
        
        return {
            'timestamp': datetime.now().isoformat(),
            'services': services_data,
            'summary': {
                'total': len(services_data),
                'healthy': sum(1 for s in services_data if s['status'] == 'healthy'),
                'degraded': sum(1 for s in services_data if s['status'] == 'degraded'),
                'unhealthy': sum(1 for s in services_data if s['status'] == 'unhealthy')
            }
        }


# 使用示例
tracker = HealthScoreTracker()

# 注册告警回调
def alert_handler(score: HealthScore, severity: str):
    print(f"[{severity.upper()}] {score.service}: {score.total_score}")

tracker.on_alert(alert_handler)

# 记录指标
score = tracker.record("api-gateway", {
    MetricType.AVAILABILITY: 99.95,
    MetricType.LATENCY_P99: 150,
    MetricType.ERROR_RATE: 0.5,
    MetricType.CPU_USAGE: 45,
    MetricType.MEMORY_USAGE: 60
})

print(f"Health Score: {score.total_score} ({score.status})")
print(f"Metric Details: {score.metric_scores}")
```

### 考察点
- 系统设计能力
- 权重计算与归一化
- 时序数据处理
- 告警机制设计

---

## 题目2：实现故障自愈脚本 ⭐⭐⭐

### 题目描述

实现一个故障自愈系统，能够：
1. 检测常见故障（磁盘满、进程挂掉、端口不可用）
2. 自动执行修复操作
3. 记录操作日志
4. 设置修复次数限制，防止无限循环

### Python3 完整实现

```python
import os
import time
import subprocess
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RepairResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    LIMIT_EXCEEDED = "limit_exceeded"


@dataclass
class RepairAction:
    """修复操作记录"""
    problem_type: str
    description: str
    action_taken: str
    result: RepairResult
    timestamp: datetime
    duration_ms: float
    details: Dict = field(default_factory=dict)


class ProblemDetector(ABC):
    """问题检测器抽象类"""
    
    @abstractmethod
    def detect(self) -> Optional[Dict]:
        """检测问题，返回问题详情或None"""
        pass
    
    @abstractmethod
    def repair(self, problem: Dict) -> RepairResult:
        """修复问题"""
        pass
    
    @property
    @abstractmethod
    def problem_type(self) -> str:
        pass


class DiskFullDetector(ProblemDetector):
    """磁盘满检测器"""
    
    def __init__(
        self, 
        path: str = "/",
        warning_threshold: float = 80,
        critical_threshold: float = 90,
        cleanup_paths: List[str] = None
    ):
        self.path = path
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.cleanup_paths = cleanup_paths or [
            "/var/log/*.gz",
            "/tmp/*",
            "/var/cache/apt/archives/*.deb"
        ]
    
    @property
    def problem_type(self) -> str:
        return "disk_full"
    
    def detect(self) -> Optional[Dict]:
        try:
            usage = shutil.disk_usage(self.path)
            used_percent = (usage.used / usage.total) * 100
            
            if used_percent >= self.critical_threshold:
                return {
                    'severity': 'critical',
                    'path': self.path,
                    'used_percent': round(used_percent, 2),
                    'free_gb': round(usage.free / (1024**3), 2)
                }
            elif used_percent >= self.warning_threshold:
                return {
                    'severity': 'warning',
                    'path': self.path,
                    'used_percent': round(used_percent, 2),
                    'free_gb': round(usage.free / (1024**3), 2)
                }
            return None
        except Exception as e:
            logger.error(f"Disk detection failed: {e}")
            return None
    
    def repair(self, problem: Dict) -> RepairResult:
        """清理磁盘空间"""
        freed_space = 0
        
        for pattern in self.cleanup_paths:
            try:
                # 使用find和rm清理
                result = subprocess.run(
                    f"find {pattern} -type f -mtime +7 -delete 2>/dev/null",
                    shell=True,
                    capture_output=True
                )
                logger.info(f"Cleaned up: {pattern}")
            except Exception as e:
                logger.warning(f"Failed to clean {pattern}: {e}")
        
        # 清理journal日志
        try:
            subprocess.run(
                ["journalctl", "--vacuum-time=7d"],
                capture_output=True
            )
        except Exception:
            pass
        
        # 验证修复结果
        new_check = self.detect()
        if new_check is None or new_check['used_percent'] < problem['used_percent']:
            return RepairResult.SUCCESS
        return RepairResult.FAILED


class ProcessDownDetector(ProblemDetector):
    """进程挂掉检测器"""
    
    def __init__(self, processes: Dict[str, str]):
        """
        processes: {process_name: restart_command}
        """
        self.processes = processes
    
    @property
    def problem_type(self) -> str:
        return "process_down"
    
    def detect(self) -> Optional[Dict]:
        down_processes = []
        
        for name, restart_cmd in self.processes.items():
            try:
                # 使用pgrep检查进程
                result = subprocess.run(
                    ["pgrep", "-f", name],
                    capture_output=True
                )
                if result.returncode != 0:
                    down_processes.append({
                        'name': name,
                        'restart_cmd': restart_cmd
                    })
            except Exception as e:
                logger.error(f"Process check failed for {name}: {e}")
        
        if down_processes:
            return {
                'down_processes': down_processes,
                'count': len(down_processes)
            }
        return None
    
    def repair(self, problem: Dict) -> RepairResult:
        """重启挂掉的进程"""
        success_count = 0
        
        for proc in problem['down_processes']:
            try:
                result = subprocess.run(
                    proc['restart_cmd'],
                    shell=True,
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.info(f"Restarted {proc['name']}")
                    success_count += 1
                else:
                    logger.error(f"Failed to restart {proc['name']}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout restarting {proc['name']}")
            except Exception as e:
                logger.error(f"Error restarting {proc['name']}: {e}")
        
        if success_count == len(problem['down_processes']):
            return RepairResult.SUCCESS
        elif success_count > 0:
            return RepairResult.SUCCESS  # 部分成功也算成功
        return RepairResult.FAILED


class PortUnavailableDetector(ProblemDetector):
    """端口不可用检测器"""
    
    def __init__(self, services: Dict[str, Dict]):
        """
        services: {
            "nginx": {"port": 80, "restart_cmd": "systemctl restart nginx"},
            "redis": {"port": 6379, "restart_cmd": "systemctl restart redis"}
        }
        """
        self.services = services
    
    @property
    def problem_type(self) -> str:
        return "port_unavailable"
    
    def _check_port(self, port: int) -> bool:
        """检查端口是否监听"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def detect(self) -> Optional[Dict]:
        unavailable = []
        
        for service_name, config in self.services.items():
            port = config['port']
            if not self._check_port(port):
                unavailable.append({
                    'service': service_name,
                    'port': port,
                    'restart_cmd': config['restart_cmd']
                })
        
        if unavailable:
            return {
                'unavailable_services': unavailable,
                'count': len(unavailable)
            }
        return None
    
    def repair(self, problem: Dict) -> RepairResult:
        """重启服务恢复端口"""
        success_count = 0
        
        for svc in problem['unavailable_services']:
            try:
                result = subprocess.run(
                    svc['restart_cmd'],
                    shell=True,
                    capture_output=True,
                    timeout=60
                )
                
                # 等待服务启动
                time.sleep(3)
                
                # 验证端口是否恢复
                if self._check_port(svc['port']):
                    logger.info(f"Recovered {svc['service']} on port {svc['port']}")
                    success_count += 1
                else:
                    logger.error(f"Failed to recover {svc['service']}")
                    
            except Exception as e:
                logger.error(f"Error recovering {svc['service']}: {e}")
        
        if success_count == len(problem['unavailable_services']):
            return RepairResult.SUCCESS
        return RepairResult.FAILED


class MemoryPressureDetector(ProblemDetector):
    """内存压力检测器"""
    
    def __init__(
        self, 
        threshold: float = 90,
        oom_killer_whitelist: List[str] = None
    ):
        self.threshold = threshold
        self.whitelist = oom_killer_whitelist or ['sshd', 'systemd', 'init']
    
    @property
    def problem_type(self) -> str:
        return "memory_pressure"
    
    def detect(self) -> Optional[Dict]:
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
            
            if used_percent >= self.threshold:
                return {
                    'used_percent': round(used_percent, 2),
                    'available_mb': round(available / 1024, 2)
                }
            return None
        except Exception as e:
            logger.error(f"Memory detection failed: {e}")
            return None
    
    def repair(self, problem: Dict) -> RepairResult:
        """清理内存：清理缓存，必要时杀死高内存进程"""
        try:
            # 1. 清理页面缓存
            subprocess.run(
                "sync; echo 1 > /proc/sys/vm/drop_caches",
                shell=True,
                capture_output=True
            )
            logger.info("Dropped page cache")
            
            # 2. 检查是否缓解
            new_check = self.detect()
            if new_check is None:
                return RepairResult.SUCCESS
            
            # 3. 查找高内存进程
            result = subprocess.run(
                "ps aux --sort=-%mem | head -10",
                shell=True,
                capture_output=True,
                text=True
            )
            
            # 这里可以添加杀死非关键进程的逻辑
            # 但为安全起见，这里只记录
            logger.warning(f"High memory processes:\n{result.stdout}")
            
            return RepairResult.SUCCESS
            
        except Exception as e:
            logger.error(f"Memory repair failed: {e}")
            return RepairResult.FAILED


class SelfHealingSystem:
    """
    故障自愈系统
    """
    
    def __init__(
        self, 
        max_repairs_per_hour: int = 5,
        cooldown_seconds: int = 60
    ):
        self.detectors: List[ProblemDetector] = []
        self.max_repairs_per_hour = max_repairs_per_hour
        self.cooldown_seconds = cooldown_seconds
        
        self.repair_history: List[RepairAction] = []
        self.last_repair_time: Dict[str, datetime] = {}
    
    def add_detector(self, detector: ProblemDetector):
        """添加问题检测器"""
        self.detectors.append(detector)
    
    def _can_repair(self, problem_type: str) -> bool:
        """检查是否可以执行修复"""
        now = datetime.now()
        
        # 检查冷却时间
        last_repair = self.last_repair_time.get(problem_type)
        if last_repair and (now - last_repair).seconds < self.cooldown_seconds:
            logger.info(f"Cooldown active for {problem_type}")
            return False
        
        # 检查每小时修复次数限制
        hour_ago = now - timedelta(hours=1)
        recent_repairs = [
            r for r in self.repair_history
            if r.problem_type == problem_type and r.timestamp >= hour_ago
        ]
        
        if len(recent_repairs) >= self.max_repairs_per_hour:
            logger.warning(f"Repair limit exceeded for {problem_type}")
            return False
        
        return True
    
    def run_once(self) -> List[RepairAction]:
        """执行一次检测和修复"""
        actions = []
        
        for detector in self.detectors:
            problem = detector.detect()
            
            if problem:
                logger.info(f"Detected {detector.problem_type}: {problem}")
                
                if not self._can_repair(detector.problem_type):
                    action = RepairAction(
                        problem_type=detector.problem_type,
                        description=str(problem),
                        action_taken="skipped",
                        result=RepairResult.LIMIT_EXCEEDED,
                        timestamp=datetime.now(),
                        duration_ms=0,
                        details=problem
                    )
                    actions.append(action)
                    continue
                
                # 执行修复
                start_time = time.time()
                try:
                    result = detector.repair(problem)
                    duration = (time.time() - start_time) * 1000
                    
                    action = RepairAction(
                        problem_type=detector.problem_type,
                        description=str(problem),
                        action_taken="repair_attempted",
                        result=result,
                        timestamp=datetime.now(),
                        duration_ms=duration,
                        details=problem
                    )
                    
                    self.last_repair_time[detector.problem_type] = datetime.now()
                    self.repair_history.append(action)
                    actions.append(action)
                    
                    logger.info(f"Repair result for {detector.problem_type}: {result.value}")
                    
                except Exception as e:
                    logger.error(f"Repair failed for {detector.problem_type}: {e}")
                    action = RepairAction(
                        problem_type=detector.problem_type,
                        description=str(problem),
                        action_taken="repair_failed",
                        result=RepairResult.FAILED,
                        timestamp=datetime.now(),
                        duration_ms=(time.time() - start_time) * 1000,
                        details={'error': str(e)}
                    )
                    actions.append(action)
        
        return actions
    
    def run_loop(self, interval_seconds: int = 60):
        """持续运行"""
        logger.info("Starting self-healing system")
        
        while True:
            try:
                actions = self.run_once()
                if actions:
                    logger.info(f"Completed {len(actions)} repair actions")
            except Exception as e:
                logger.error(f"Error in healing loop: {e}")
            
            time.sleep(interval_seconds)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        recent_1h = [r for r in self.repair_history if r.timestamp >= hour_ago]
        recent_24h = [r for r in self.repair_history if r.timestamp >= day_ago]
        
        return {
            'total_repairs': len(self.repair_history),
            'repairs_last_hour': len(recent_1h),
            'repairs_last_24h': len(recent_24h),
            'success_rate_24h': (
                sum(1 for r in recent_24h if r.result == RepairResult.SUCCESS) / 
                len(recent_24h) if recent_24h else 0
            ) * 100,
            'by_problem_type': {
                pt: sum(1 for r in recent_24h if r.problem_type == pt)
                for pt in set(r.problem_type for r in recent_24h)
            }
        }


# 使用示例
healer = SelfHealingSystem(max_repairs_per_hour=3)

# 添加检测器
healer.add_detector(DiskFullDetector(path="/", critical_threshold=90))
healer.add_detector(ProcessDownDetector({
    "nginx": "systemctl restart nginx",
    "redis-server": "systemctl restart redis"
}))
healer.add_detector(PortUnavailableDetector({
    "nginx": {"port": 80, "restart_cmd": "systemctl restart nginx"},
    "redis": {"port": 6379, "restart_cmd": "systemctl restart redis"}
}))
healer.add_detector(MemoryPressureDetector(threshold=90))

# 运行一次
actions = healer.run_once()
for action in actions:
    print(f"{action.problem_type}: {action.result.value}")
```

### 考察点
- 问题检测设计
- 自动修复策略
- 安全保护机制（限流、冷却）
- 日志和审计

---

## 题目3：实现简单的任务调度器 ⭐⭐⭐

### 题目描述

实现一个支持Cron表达式的任务调度器，类似于简化版的Airflow或Celery Beat。

### Python3 完整实现

```python
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import heapq
import re
from abc import ABC, abstractmethod

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskExecution:
    task_id: str
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ScheduledTask:
    task_id: str
    name: str
    func: Callable
    schedule: str  # cron expression or interval
    enabled: bool = True
    timeout: int = 3600  # seconds
    max_retries: int = 0
    retry_delay: int = 60  # seconds
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class CronParser:
    """
    简化版Cron表达式解析器
    支持: minute hour day month weekday
    特殊字符: * (任意), */n (每n), n-m (范围), n,m (列表)
    """
    
    @staticmethod
    def parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """解析单个字段"""
        values = set()
        
        for part in field.split(','):
            if part == '*':
                values.update(range(min_val, max_val + 1))
            elif '/' in part:
                base, step = part.split('/')
                step = int(step)
                if base == '*':
                    start = min_val
                else:
                    start = int(base)
                values.update(range(start, max_val + 1, step))
            elif '-' in part:
                start, end = part.split('-')
                values.update(range(int(start), int(end) + 1))
            else:
                values.add(int(part))
        
        return sorted(values)
    
    @staticmethod
    def parse(expression: str) -> Dict[str, List[int]]:
        """
        解析完整cron表达式
        格式: minute hour day month weekday
        """
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        
        return {
            'minute': CronParser.parse_field(parts[0], 0, 59),
            'hour': CronParser.parse_field(parts[1], 0, 23),
            'day': CronParser.parse_field(parts[2], 1, 31),
            'month': CronParser.parse_field(parts[3], 1, 12),
            'weekday': CronParser.parse_field(parts[4], 0, 6)
        }
    
    @staticmethod
    def get_next_run(expression: str, from_time: datetime = None) -> datetime:
        """
        计算下一次运行时间
        """
        if from_time is None:
            from_time = datetime.now()
        
        schedule = CronParser.parse(expression)
        
        # 从下一分钟开始搜索
        current = from_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # 最多搜索一年
        max_iterations = 366 * 24 * 60
        
        for _ in range(max_iterations):
            if (current.month in schedule['month'] and
                current.day in schedule['day'] and
                current.weekday() in schedule['weekday'] and
                current.hour in schedule['hour'] and
                current.minute in schedule['minute']):
                return current
            
            current += timedelta(minutes=1)
        
        raise ValueError(f"Could not find next run time for: {expression}")


class TaskScheduler:
    """
    任务调度器
    """
    
    def __init__(self, max_workers: int = 4):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.execution_history: List[TaskExecution] = []
        self.max_history = 1000
        
        self.running = False
        self.lock = threading.Lock()
        self.workers = max_workers
        self.executor_pool: List[threading.Thread] = []
        self.task_queue: List[tuple] = []  # heap: (next_run, task_id)
    
    def add_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        schedule: str,
        **kwargs
    ) -> ScheduledTask:
        """添加定时任务"""
        with self.lock:
            task = ScheduledTask(
                task_id=task_id,
                name=name,
                func=func,
                schedule=schedule,
                **kwargs
            )
            
            # 计算下次运行时间
            task.next_run = CronParser.get_next_run(schedule)
            
            self.tasks[task_id] = task
            heapq.heappush(self.task_queue, (task.next_run, task_id))
            
            return task
    
    def remove_task(self, task_id: str):
        """移除任务"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
    
    def enable_task(self, task_id: str, enabled: bool = True):
        """启用/禁用任务"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = enabled
    
    def _execute_task(self, task: ScheduledTask) -> TaskExecution:
        """执行任务"""
        execution = TaskExecution(
            task_id=task.task_id,
            scheduled_time=task.next_run,
            start_time=datetime.now(),
            status=TaskStatus.RUNNING
        )
        
        try:
            # 执行任务函数
            result = task.func()
            
            execution.status = TaskStatus.SUCCESS
            execution.result = str(result) if result else "OK"
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
        
        execution.end_time = datetime.now()
        return execution
    
    def _scheduler_loop(self):
        """调度循环"""
        while self.running:
            now = datetime.now()
            
            with self.lock:
                while self.task_queue:
                    next_run, task_id = self.task_queue[0]
                    
                    if next_run > now:
                        break
                    
                    heapq.heappop(self.task_queue)
                    
                    if task_id not in self.tasks:
                        continue
                    
                    task = self.tasks[task_id]
                    
                    if not task.enabled:
                        # 跳过禁用的任务，但仍需计算下次时间
                        task.next_run = CronParser.get_next_run(task.schedule, now)
                        heapq.heappush(self.task_queue, (task.next_run, task_id))
                        continue
                    
                    # 启动执行线程
                    thread = threading.Thread(
                        target=self._run_task,
                        args=(task,)
                    )
                    thread.start()
                    
                    # 计算下次运行时间
                    task.next_run = CronParser.get_next_run(task.schedule, now)
                    heapq.heappush(self.task_queue, (task.next_run, task_id))
            
            # 短暂休眠
            time.sleep(1)
    
    def _run_task(self, task: ScheduledTask):
        """运行单个任务（在单独线程中）"""
        execution = self._execute_task(task)
        task.last_run = execution.end_time
        
        # 保存执行历史
        with self.lock:
            self.execution_history.append(execution)
            if len(self.execution_history) > self.max_history:
                self.execution_history = self.execution_history[-self.max_history:]
        
        # 记录日志
        if execution.status == TaskStatus.SUCCESS:
            print(f"[SUCCESS] {task.name} completed in {(execution.end_time - execution.start_time).total_seconds():.2f}s")
        else:
            print(f"[FAILED] {task.name}: {execution.error}")
    
    def start(self):
        """启动调度器"""
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("Scheduler started")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if hasattr(self, 'scheduler_thread'):
            self.scheduler_thread.join(timeout=5)
        print("Scheduler stopped")
    
    def get_task_status(self) -> List[Dict]:
        """获取所有任务状态"""
        result = []
        for task_id, task in self.tasks.items():
            # 找最近的执行记录
            recent_executions = [
                e for e in self.execution_history 
                if e.task_id == task_id
            ][-5:]
            
            result.append({
                'task_id': task_id,
                'name': task.name,
                'schedule': task.schedule,
                'enabled': task.enabled,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'recent_status': [
                    {'time': e.start_time.isoformat(), 'status': e.status.value}
                    for e in recent_executions
                ]
            })
        
        return result
    
    def run_task_now(self, task_id: str) -> Optional[TaskExecution]:
        """立即运行任务（手动触发）"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        execution = self._execute_task(task)
        
        with self.lock:
            self.execution_history.append(execution)
        
        return execution


# 使用示例
scheduler = TaskScheduler()

# 添加任务
def cleanup_logs():
    print("Cleaning up old logs...")
    # 清理逻辑
    return "Cleaned 100 files"

def check_health():
    print("Checking service health...")
    # 健康检查逻辑
    return "All services healthy"

def backup_database():
    print("Backing up database...")
    # 备份逻辑
    return "Backup completed"

scheduler.add_task(
    task_id="cleanup_logs",
    name="Log Cleanup",
    func=cleanup_logs,
    schedule="0 2 * * *"  # 每天凌晨2点
)

scheduler.add_task(
    task_id="health_check",
    name="Health Check",
    func=check_health,
    schedule="*/5 * * * *"  # 每5分钟
)

scheduler.add_task(
    task_id="daily_backup",
    name="Database Backup",
    func=backup_database,
    schedule="0 3 * * 0"  # 每周日凌晨3点
)

# 启动调度器
scheduler.start()

# 查看任务状态
for task in scheduler.get_task_status():
    print(f"{task['name']}: next run at {task['next_run']}")
```

### 考察点
- Cron表达式解析
- 调度算法（堆）
- 多线程任务执行
- 状态管理

---

## 题目4：实现日志告警关联分析 ⭐⭐⭐

### 题目描述

实现一个系统，能够：
1. 关联日志和告警
2. 自动识别告警的可能原因
3. 生成故障时间线

### Python3 完整实现

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import re

@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    service: str
    message: str
    trace_id: Optional[str] = None
    extra: Dict = field(default_factory=dict)


@dataclass
class Alert:
    alert_id: str
    timestamp: datetime
    service: str
    severity: str
    title: str
    description: str
    labels: Dict = field(default_factory=dict)


@dataclass
class CorrelatedIncident:
    """关联后的事件"""
    alert: Alert
    related_logs: List[LogEntry]
    probable_causes: List[str]
    timeline: List[Dict]
    affected_services: Set[str]


class LogAlertCorrelator:
    """
    日志告警关联分析器
    """
    
    # 常见错误模式及其可能原因
    ERROR_PATTERNS = [
        {
            'pattern': r'connection\s+(refused|timeout|reset)',
            'cause': '网络连接问题',
            'category': 'network'
        },
        {
            'pattern': r'out\s+of\s+memory|OOM|heap\s+space',
            'cause': '内存不足',
            'category': 'resource'
        },
        {
            'pattern': r'disk\s+(full|space)|no\s+space\s+left',
            'cause': '磁盘空间不足',
            'category': 'resource'
        },
        {
            'pattern': r'timeout|timed?\s+out',
            'cause': '请求超时',
            'category': 'performance'
        },
        {
            'pattern': r'connection\s+pool\s+(exhausted|full)',
            'cause': '连接池耗尽',
            'category': 'resource'
        },
        {
            'pattern': r'rate\s+limit|throttl',
            'cause': '触发限流',
            'category': 'traffic'
        },
        {
            'pattern': r'authentication\s+(failed|error)|unauthorized',
            'cause': '认证失败',
            'category': 'security'
        },
        {
            'pattern': r'certificate\s+(expired|invalid)',
            'cause': '证书问题',
            'category': 'security'
        },
        {
            'pattern': r'database\s+(error|unavailable)|sql\s+error',
            'cause': '数据库问题',
            'category': 'database'
        },
        {
            'pattern': r'deadlock|lock\s+wait\s+timeout',
            'cause': '死锁或锁等待',
            'category': 'database'
        },
    ]
    
    def __init__(
        self,
        time_window_before: int = 300,  # 秒，告警前查找日志的时间窗口
        time_window_after: int = 60     # 秒，告警后
    ):
        self.time_window_before = time_window_before
        self.time_window_after = time_window_after
        self.logs: List[LogEntry] = []
        self.alerts: List[Alert] = []
        self.service_dependencies: Dict[str, Set[str]] = defaultdict(set)
    
    def add_log(self, log: LogEntry):
        """添加日志"""
        self.logs.append(log)
        # 按时间排序
        self.logs.sort(key=lambda x: x.timestamp)
    
    def add_alert(self, alert: Alert):
        """添加告警"""
        self.alerts.append(alert)
        self.alerts.sort(key=lambda x: x.timestamp)
    
    def set_service_dependency(self, service: str, depends_on: List[str]):
        """设置服务依赖关系"""
        self.service_dependencies[service].update(depends_on)
    
    def find_related_logs(
        self, 
        alert: Alert,
        levels: List[str] = None
    ) -> List[LogEntry]:
        """
        查找与告警相关的日志
        """
        levels = levels or ['ERROR', 'WARN', 'CRITICAL', 'FATAL']
        
        start_time = alert.timestamp - timedelta(seconds=self.time_window_before)
        end_time = alert.timestamp + timedelta(seconds=self.time_window_after)
        
        # 相关服务：告警服务 + 其依赖的服务
        related_services = {alert.service}
        related_services.update(self.service_dependencies.get(alert.service, set()))
        
        related_logs = []
        for log in self.logs:
            if start_time <= log.timestamp <= end_time:
                if log.level.upper() in levels:
                    if log.service in related_services:
                        related_logs.append(log)
        
        return related_logs
    
    def identify_causes(self, logs: List[LogEntry]) -> List[str]:
        """
        从日志中识别可能的原因
        """
        causes = set()
        
        for log in logs:
            message = log.message.lower()
            for pattern_info in self.ERROR_PATTERNS:
                if re.search(pattern_info['pattern'], message, re.IGNORECASE):
                    causes.add(pattern_info['cause'])
        
        return list(causes)
    
    def build_timeline(
        self, 
        alert: Alert, 
        logs: List[LogEntry]
    ) -> List[Dict]:
        """
        构建故障时间线
        """
        timeline = []
        
        # 添加相关日志
        for log in logs:
            timeline.append({
                'timestamp': log.timestamp.isoformat(),
                'type': 'log',
                'level': log.level,
                'service': log.service,
                'message': log.message[:200]
            })
        
        # 添加告警
        timeline.append({
            'timestamp': alert.timestamp.isoformat(),
            'type': 'alert',
            'severity': alert.severity,
            'service': alert.service,
            'message': alert.title
        })
        
        # 按时间排序
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    def find_affected_services(
        self, 
        alert: Alert,
        logs: List[LogEntry]
    ) -> Set[str]:
        """
        找出受影响的服务
        """
        affected = {alert.service}
        
        # 从日志中提取服务
        affected.update(log.service for log in logs if log.level.upper() == 'ERROR')
        
        # 查找依赖该服务的其他服务
        for service, deps in self.service_dependencies.items():
            if alert.service in deps:
                affected.add(service)
        
        return affected
    
    def correlate(self, alert: Alert) -> CorrelatedIncident:
        """
        执行关联分析
        """
        related_logs = self.find_related_logs(alert)
        probable_causes = self.identify_causes(related_logs)
        timeline = self.build_timeline(alert, related_logs)
        affected_services = self.find_affected_services(alert, related_logs)
        
        return CorrelatedIncident(
            alert=alert,
            related_logs=related_logs,
            probable_causes=probable_causes,
            timeline=timeline,
            affected_services=affected_services
        )
    
    def correlate_all(self) -> List[CorrelatedIncident]:
        """
        关联所有告警
        """
        return [self.correlate(alert) for alert in self.alerts]
    
    def generate_incident_report(self, incident: CorrelatedIncident) -> str:
        """
        生成事件报告
        """
        report = []
        report.append("=" * 60)
        report.append(f"事件报告: {incident.alert.title}")
        report.append("=" * 60)
        
        report.append(f"\n告警信息:")
        report.append(f"  告警ID: {incident.alert.alert_id}")
        report.append(f"  时间: {incident.alert.timestamp}")
        report.append(f"  服务: {incident.alert.service}")
        report.append(f"  严重程度: {incident.alert.severity}")
        report.append(f"  描述: {incident.alert.description}")
        
        report.append(f"\n可能原因:")
        if incident.probable_causes:
            for cause in incident.probable_causes:
                report.append(f"  - {cause}")
        else:
            report.append("  - 无法自动识别原因")
        
        report.append(f"\n受影响服务:")
        for service in sorted(incident.affected_services):
            report.append(f"  - {service}")
        
        report.append(f"\n相关日志 ({len(incident.related_logs)} 条):")
        for log in incident.related_logs[:10]:
            report.append(f"  [{log.timestamp}] [{log.level}] {log.service}: {log.message[:100]}")
        if len(incident.related_logs) > 10:
            report.append(f"  ... 还有 {len(incident.related_logs) - 10} 条日志")
        
        report.append(f"\n时间线:")
        for event in incident.timeline[:15]:
            icon = "⚠️" if event['type'] == 'alert' else "📝"
            report.append(f"  {icon} {event['timestamp']} | {event['service']} | {event['message'][:50]}")
        
        return "\n".join(report)


class RootCauseAnalyzer:
    """
    根因分析器
    使用简单的规则推理
    """
    
    def __init__(self):
        self.rules = [
            self._rule_upstream_failure,
            self._rule_resource_exhaustion,
            self._rule_deployment_issue,
            self._rule_external_dependency
        ]
    
    def analyze(
        self, 
        incident: CorrelatedIncident,
        recent_deployments: List[Dict] = None
    ) -> Dict:
        """
        分析根因
        """
        findings = []
        
        for rule in self.rules:
            result = rule(incident, recent_deployments)
            if result:
                findings.append(result)
        
        # 按置信度排序
        findings.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return {
            'primary_cause': findings[0] if findings else None,
            'all_findings': findings,
            'recommendation': self._generate_recommendation(findings)
        }
    
    def _rule_upstream_failure(
        self, 
        incident: CorrelatedIncident,
        deployments: List[Dict] = None
    ) -> Optional[Dict]:
        """规则：上游服务故障"""
        # 检查是否有上游服务的错误日志
        upstream_errors = [
            log for log in incident.related_logs
            if log.service != incident.alert.service
            and log.level.upper() in ['ERROR', 'FATAL']
        ]
        
        if upstream_errors:
            first_error = min(upstream_errors, key=lambda x: x.timestamp)
            return {
                'cause_type': 'upstream_failure',
                'description': f"上游服务 {first_error.service} 先于告警出现错误",
                'confidence': 0.8,
                'evidence': {
                    'service': first_error.service,
                    'first_error_time': first_error.timestamp.isoformat(),
                    'error_message': first_error.message[:200]
                }
            }
        return None
    
    def _rule_resource_exhaustion(
        self,
        incident: CorrelatedIncident,
        deployments: List[Dict] = None
    ) -> Optional[Dict]:
        """规则：资源耗尽"""
        resource_keywords = ['memory', 'disk', 'cpu', 'connection', 'thread', 'file descriptor']
        
        for log in incident.related_logs:
            message = log.message.lower()
            for keyword in resource_keywords:
                if keyword in message and ('exhaust' in message or 'full' in message or 'limit' in message):
                    return {
                        'cause_type': 'resource_exhaustion',
                        'description': f"检测到资源耗尽相关错误: {keyword}",
                        'confidence': 0.9,
                        'evidence': {
                            'log_message': log.message,
                            'service': log.service,
                            'timestamp': log.timestamp.isoformat()
                        }
                    }
        return None
    
    def _rule_deployment_issue(
        self,
        incident: CorrelatedIncident,
        deployments: List[Dict] = None
    ) -> Optional[Dict]:
        """规则：部署导致的问题"""
        if not deployments:
            return None
        
        alert_time = incident.alert.timestamp
        
        for deployment in deployments:
            deploy_time = deployment.get('timestamp')
            if deploy_time and (alert_time - deploy_time).total_seconds() < 1800:  # 30分钟内
                return {
                    'cause_type': 'deployment_issue',
                    'description': f"告警发生在 {deployment['service']} 部署后30分钟内",
                    'confidence': 0.7,
                    'evidence': {
                        'deployment': deployment,
                        'time_since_deploy': (alert_time - deploy_time).total_seconds()
                    }
                }
        return None
    
    def _rule_external_dependency(
        self,
        incident: CorrelatedIncident,
        deployments: List[Dict] = None
    ) -> Optional[Dict]:
        """规则：外部依赖问题"""
        external_keywords = ['third-party', 'external', 'api.', 'cdn', 'aws', 'gcp', 'azure']
        
        for log in incident.related_logs:
            message = log.message.lower()
            for keyword in external_keywords:
                if keyword in message and ('error' in message or 'failed' in message):
                    return {
                        'cause_type': 'external_dependency',
                        'description': f"可能是外部依赖问题: {keyword}",
                        'confidence': 0.6,
                        'evidence': {
                            'log_message': log.message
                        }
                    }
        return None
    
    def _generate_recommendation(self, findings: List[Dict]) -> str:
        """生成处理建议"""
        if not findings:
            return "无法自动识别根因，建议人工排查"
        
        primary = findings[0]
        cause_type = primary.get('cause_type')
        
        recommendations = {
            'upstream_failure': "建议检查上游服务状态，联系上游服务负责团队",
            'resource_exhaustion': "建议立即检查资源使用情况，考虑扩容或优化资源使用",
            'deployment_issue': "建议考虑回滚最近的部署，检查部署变更内容",
            'external_dependency': "建议检查外部服务状态，启用降级或备用方案"
        }
        
        return recommendations.get(cause_type, "建议根据日志详细排查")


# 使用示例
correlator = LogAlertCorrelator()

# 设置服务依赖
correlator.set_service_dependency("api-gateway", ["user-service", "order-service"])
correlator.set_service_dependency("order-service", ["payment-service", "inventory-service"])

# 添加日志
from datetime import datetime
base_time = datetime.now()

correlator.add_log(LogEntry(
    timestamp=base_time - timedelta(minutes=5),
    level="ERROR",
    service="payment-service",
    message="Connection refused to database server"
))

correlator.add_log(LogEntry(
    timestamp=base_time - timedelta(minutes=4),
    level="ERROR",
    service="order-service",
    message="Failed to process payment: timeout"
))

correlator.add_log(LogEntry(
    timestamp=base_time - timedelta(minutes=3),
    level="WARN",
    service="api-gateway",
    message="High latency detected for /orders endpoint"
))

# 添加告警
correlator.add_alert(Alert(
    alert_id="alert-001",
    timestamp=base_time,
    service="api-gateway",
    severity="critical",
    title="High Error Rate on API Gateway",
    description="Error rate exceeded 5%"
))

# 执行关联分析
incidents = correlator.correlate_all()
for incident in incidents:
    print(correlator.generate_incident_report(incident))
    
    # 根因分析
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze(incident)
    print(f"\n根因分析结果: {analysis['primary_cause']}")
    print(f"建议: {analysis['recommendation']}")
```

### 考察点
- 日志关联分析
- 模式识别
- 时间线构建
- 根因分析推理

---

## 总结

| 题目 | 难度 | 核心考点 | 实际应用 |
|------|------|----------|----------|
| 健康评分系统 | ⭐⭐⭐ | 指标加权、趋势分析 | 服务治理Dashboard |
| 故障自愈脚本 | ⭐⭐⭐ | 问题检测、自动修复 | 自动化运维 |
| 任务调度器 | ⭐⭐⭐ | Cron解析、调度算法 | 定时任务管理 |
| 告警关联分析 | ⭐⭐⭐ | 日志分析、根因推理 | 故障诊断 |

## 综合题答题技巧

1. **先理解需求再编码**
   - 明确输入输出
   - 识别核心功能
   - 考虑边界情况

2. **分层设计**
   - 将大问题拆分为小模块
   - 每个模块职责单一
   - 模块间接口清晰

3. **考虑生产环境因素**
   - 并发安全
   - 错误处理
   - 日志记录
   - 资源限制

4. **展示SRE思维**
   - 考虑可观测性
   - 考虑失败场景
   - 考虑可扩展性
   - 考虑运维友好性

5. **代码质量**
   - 类型提示
   - 文档字符串
   - 合理的抽象
   - 清晰的命名

---

## 相关文章

- [上一篇：SRE笔试题-SQL与数据库](@/articles/sre/sre-19-SRE笔试题-SQL与数据库.md)
- [下一篇：SRE笔试题-Shell脚本速查](@/articles/sre/sre-21-SRE笔试题-Shell脚本速查.md)
