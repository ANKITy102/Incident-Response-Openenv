# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Mini Incident Response Copilot Environment.

The incident_response environment simulates a real-world SaaS incident management
scenario where an AI agent acts like a junior SRE. The environment presents
alerts, logs, metrics, and service dependencies, and the agent has to investigate
the issue, identify the root cause, and take the correct action.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from openenv.core.env_server.types import Action, Observation
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of actions the SRE agent can take."""
    INSPECT_LOGS = "inspect_logs"
    CHECK_METRICS = "check_metrics"
    RESTART_SERVICE = "restart_service"
    SCALE_SERVICE = "scale_service"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    CHECK_DEPENDENCIES = "check_dependencies"
    ESCALATE_INCIDENT = "escalate_incident"


class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRASHED = "crashed"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogLevel(str, Enum):
    """Log entry levels."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class IncidentType(str, Enum):
    """Types of incidents that can occur."""
    SERVICE_CRASH = "service_crash"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DEPENDENCY_FAILURE = "dependency_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    BAD_DEPLOYMENT = "bad_deployment"


class MetricType(str, Enum):
    """Types of metrics available."""
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"


# Supporting Models
class Alert(BaseModel):
    """Represents an alert in the system."""
    id: str = Field(..., description="Unique alert identifier")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    service: str = Field(..., description="Service generating the alert")
    message: str = Field(..., description="Alert message")
    timestamp: datetime = Field(..., description="When the alert was generated")


class ServiceStatusInfo(BaseModel):
    """Status information for a service."""
    name: str = Field(..., description="Service name")
    status: ServiceStatus = Field(..., description="Current service status")
    replicas: int = Field(..., description="Number of replicas")
    last_deployed: datetime = Field(..., description="Last deployment timestamp")
    version: str = Field(..., description="Current version")


class LogEntry(BaseModel):
    """Represents a log entry from a service."""
    timestamp: datetime = Field(..., description="Log entry timestamp")
    level: LogLevel = Field(..., description="Log level")
    service: str = Field(..., description="Service generating the log")
    message: str = Field(..., description="Log message")


class MetricData(BaseModel):
    """Represents metric data for a service."""
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: datetime = Field(..., description="When the metric was recorded")


class IncidentAction(Action):
    """Action for the Incident Response environment."""
    
    action_type: ActionType = Field(..., description="Type of action to perform")
    service_name: Optional[str] = Field(None, description="Target service name")
    time_range: Optional[str] = Field("1h", description="Time range for queries")
    metric_type: Optional[MetricType] = Field(None, description="Type of metric to check")
    replicas: Optional[int] = Field(None, description="Number of replicas for scaling")
    version: Optional[str] = Field(None, description="Version for rollback")
    reason: Optional[str] = Field(None, description="Reason for escalation")


class IncidentObservation(Observation):
    """Observation from the Incident Response environment."""
    
    # Current system state
    alerts: List[Alert] = Field(default_factory=list, description="Active alerts")
    services: Dict[str, ServiceStatusInfo] = Field(default_factory=dict, description="Service health states")
    logs: Dict[str, List[LogEntry]] = Field(default_factory=dict, description="Recent log entries")
    metrics: Dict[str, List[MetricData]] = Field(default_factory=dict, description="Performance metrics")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Service dependency graph")
    
    # Incident information
    incident_timeline: List[str] = Field(default_factory=list, description="Action history")
    available_actions: List[ActionType] = Field(default_factory=list, description="Valid next actions")
    
    # Task-specific information
    current_task: Optional[str] = Field(None, description="Current task being performed")
    task_progress: float = Field(0.0, description="Progress in current task (0.0-1.0)")
    identified_services: List[str] = Field(default_factory=list, description="Services identified as affected")
    incident_type: Optional[IncidentType] = Field(None, description="Type of incident")
    severity: Optional[AlertSeverity] = Field(None, description="Incident severity")
    root_cause: Optional[str] = Field(None, description="Identified root cause")
    evidence: List[str] = Field(default_factory=list, description="Evidence supporting diagnosis")
    applied_action: Optional[str] = Field(None, description="Action taken for resolution")
    recovery_time_seconds: Optional[int] = Field(None, description="Time to recover in seconds")


# Task result models for graders
class TriageResult(BaseModel):
    """Expected result for triage task."""
    affected_services: List[str]
    incident_type: IncidentType
    severity: AlertSeverity


class DiagnosisResult(BaseModel):
    """Expected result for diagnosis task."""
    root_cause: str
    evidence: List[str]


class ResolutionResult(BaseModel):
    """Expected result for resolution task."""
    optimal_action: str
    expected_recovery_time: int
