# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Mini Incident Response Copilot Environment Implementation.

This environment simulates a real-world SaaS incident management scenario where an AI agent
acts like a junior SRE. The environment presents alerts, logs, metrics, and service
dependencies, and the agent has to investigate the issue, identify the root cause,
and take the correct action.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import (
        IncidentAction,
        IncidentObservation,
        Alert,
        ServiceStatusInfo,
        LogEntry,
        MetricData,
        ActionType,
        AlertSeverity,
        ServiceStatus,
        LogLevel,
        IncidentType,
        MetricType,
    )
except ImportError:
    from models import (
        IncidentAction,
        IncidentObservation,
        Alert,
        ServiceStatusInfo,
        LogEntry,
        MetricData,
        ActionType,
        AlertSeverity,
        ServiceStatus,
        LogLevel,
        IncidentType,
        MetricType,
    )


class IncidentResponseEnvironment(Environment):
    """
    A sophisticated incident response environment that simulates real-world SaaS operations.
    
    This environment maintains a realistic microservices architecture with 5 core services:
    - auth: Authentication service
    - payments: Payment processing service  
    - api: API gateway service
    - database: Database service
    - cache: Redis cache service
    
    The environment generates realistic incidents and provides the agent with alerts,
    logs, metrics, and dependency information to investigate and resolve issues.
    """

    # Enable concurrent WebSocket sessions
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the incident response environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count = 0
        
        # Initialize services
        self._initialize_services()
        
        # Current incident state
        self._current_incident = None
        self._incident_start_time = None
        self._recovery_start_time = None
        
        # Task state
        self._current_task = None
        self._task_progress = 0.0
        self._identified_services = []
        self._incident_type = None
        self._severity = None
        self._root_cause = None
        self._evidence = []
        self._applied_action = None
        self._incident_timeline = []

    def _initialize_services(self):
        """Initialize all services with healthy baseline state."""
        self.services = {
            "auth": ServiceStatusInfo(
                name="auth",
                status=ServiceStatus.HEALTHY,
                replicas=3,
                last_deployed=datetime.now() - timedelta(hours=2),
                version="v1.2.3"
            ),
            "payments": ServiceStatusInfo(
                name="payments",
                status=ServiceStatus.HEALTHY,
                replicas=2,
                last_deployed=datetime.now() - timedelta(hours=1),
                version="v2.1.0"
            ),
            "api": ServiceStatusInfo(
                name="api",
                status=ServiceStatus.HEALTHY,
                replicas=4,
                last_deployed=datetime.now() - timedelta(minutes=30),
                version="v3.0.1"
            ),
            "database": ServiceStatusInfo(
                name="database",
                status=ServiceStatus.HEALTHY,
                replicas=1,
                last_deployed=datetime.now() - timedelta(days=1),
                version="postgres-14.5"
            ),
            "cache": ServiceStatusInfo(
                name="cache",
                status=ServiceStatus.HEALTHY,
                replicas=1,
                last_deployed=datetime.now() - timedelta(hours=6),
                version="redis-7.0"
            ),
        }
        
        # Service dependencies
        self.dependencies = {
            "auth": ["database", "cache"],
            "payments": ["database", "cache"],
            "api": ["auth", "payments"],
            "database": [],
            "cache": [],
        }
        
        # Initialize logs and metrics
        self.logs = {service: [] for service in self.services}
        self.metrics = {service: [] for service in self.services}
        self.alerts = []
        
        # Generate baseline logs and metrics
        self._generate_baseline_data()

    def _generate_baseline_data(self):
        """Generate realistic baseline logs and metrics."""
        now = datetime.now()
        
        for service_name in self.services:
            # Generate baseline logs
            for i in range(50):
                timestamp = now - timedelta(minutes=i*2)
                level = random.choices(
                    [LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR],
                    weights=[0.8, 0.15, 0.05]
                )[0]
                
                if level == LogLevel.INFO:
                    messages = [
                        f"Request processed successfully",
                        f"Health check passed",
                        f"Cache hit for key",
                        f"Database query executed",
                    ]
                elif level == LogLevel.WARN:
                    messages = [
                        f"Slow query detected",
                        f"Cache miss for key",
                        f"High memory usage warning",
                    ]
                else:
                    messages = [
                        f"Connection timeout",
                        f"Database connection failed",
                        f"Memory allocation failed",
                    ]
                
                log_entry = LogEntry(
                    timestamp=timestamp,
                    level=level,
                    service=service_name,
                    message=random.choice(messages)
                )
                self.logs[service_name].append(log_entry)
            
            # Generate baseline metrics
            for i in range(20):
                timestamp = now - timedelta(minutes=i*5)
                
                # Latency metrics
                latency = MetricData(
                    name="latency",
                    value=random.uniform(50, 200),  # 50-200ms
                    unit="ms",
                    timestamp=timestamp
                )
                
                # Error rate metrics
                error_rate = MetricData(
                    name="error_rate",
                    value=random.uniform(0.0, 2.0),  # 0-2%
                    unit="percent",
                    timestamp=timestamp
                )
                
                # CPU usage metrics
                cpu_usage = MetricData(
                    name="cpu_usage",
                    value=random.uniform(20, 60),  # 20-60%
                    unit="percent",
                    timestamp=timestamp
                )
                
                # Memory usage metrics
                memory_usage = MetricData(
                    name="memory_usage",
                    value=random.uniform(30, 70),  # 30-70%
                    unit="percent",
                    timestamp=timestamp
                )
                
                self.metrics[service_name].extend([latency, error_rate, cpu_usage, memory_usage])

    def _generate_incident(self):
        """Generate a random incident."""
        incident_types = list(IncidentType)
        self._current_incident = random.choice(incident_types)
        self._incident_start_time = datetime.now()
        
        # Clear previous incident data
        self.alerts.clear()
        self._incident_timeline.clear()
        self._identified_services = []
        self._evidence = []
        self._root_cause = None
        self._applied_action = None
        
        if self._current_incident == IncidentType.SERVICE_CRASH:
            self._generate_service_crash()
        elif self._current_incident == IncidentType.PERFORMANCE_DEGRADATION:
            self._generate_performance_degradation()
        elif self._current_incident == IncidentType.DEPENDENCY_FAILURE:
            self._generate_dependency_failure()
        elif self._current_incident == IncidentType.RESOURCE_EXHAUSTION:
            self._generate_resource_exhaustion()
        elif self._current_incident == IncidentType.BAD_DEPLOYMENT:
            self._generate_bad_deployment()

    def _generate_service_crash(self):
        """Generate a service crash incident."""
        # Pick a random service to crash
        crashed_service = random.choice(["auth", "payments", "api"])
        self.services[crashed_service].status = ServiceStatus.CRASHED
        self.services[crashed_service].replicas = 0
        
        # Generate alerts
        alert = Alert(
            id=str(uuid4()),
            severity=AlertSeverity.CRITICAL,
            service=crashed_service,
            message=f"Service {crashed_service} has crashed and is not responding",
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        
        # Generate error logs
        for i in range(10):
            log_entry = LogEntry(
                timestamp=datetime.now() - timedelta(minutes=i),
                level=LogLevel.ERROR,
                service=crashed_service,
                message=f"Service failed to start: Connection refused"
            )
            self.logs[crashed_service].append(log_entry)
        
        # Generate error metrics
        for i in range(5):
            error_metric = MetricData(
                name="error_rate",
                value=100.0,  # 100% error rate
                unit="percent",
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            self.metrics[crashed_service].append(error_metric)
        
        # Set severity
        self._severity = AlertSeverity.CRITICAL

    def _generate_performance_degradation(self):
        """Generate a performance degradation incident."""
        affected_service = random.choice(["api", "payments"])
        self.services[affected_service].status = ServiceStatus.DEGRADED
        
        # Generate alerts
        alert = Alert(
            id=str(uuid4()),
            severity=AlertSeverity.HIGH,
            service=affected_service,
            message=f"High latency detected in {affected_service} service",
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        
        # Generate high latency logs
        for i in range(8):
            log_entry = LogEntry(
                timestamp=datetime.now() - timedelta(minutes=i),
                level=LogLevel.WARN,
                service=affected_service,
                message=f"Slow request: {random.uniform(1000, 5000)}ms"
            )
            self.logs[affected_service].append(log_entry)
        
        # Generate high latency metrics
        for i in range(5):
            latency_metric = MetricData(
                name="latency",
                value=random.uniform(1000, 3000),  # 1-3 seconds
                unit="ms",
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            self.metrics[affected_service].append(latency_metric)
        
        self._severity = AlertSeverity.HIGH

    def _generate_dependency_failure(self):
        """Generate a dependency failure incident."""
        # Database failure affects auth and payments
        self.services["database"].status = ServiceStatus.UNHEALTHY
        self.services["auth"].status = ServiceStatus.DEGRADED
        self.services["payments"].status = ServiceStatus.DEGRADED
        
        # Generate alerts
        for service in ["database", "auth", "payments"]:
            alert = Alert(
                id=str(uuid4()),
                severity=AlertSeverity.HIGH,
                service=service,
                message=f"Service {service} experiencing connectivity issues",
                timestamp=datetime.now()
            )
            self.alerts.append(alert)
        
        # Generate connection error logs
        for service in ["auth", "payments"]:
            for i in range(6):
                log_entry = LogEntry(
                    timestamp=datetime.now() - timedelta(minutes=i),
                    level=LogLevel.ERROR,
                    service=service,
                    message="Database connection timeout after 30 seconds"
                )
                self.logs[service].append(log_entry)
        
        self._severity = AlertSeverity.HIGH

    def _generate_resource_exhaustion(self):
        """Generate a resource exhaustion incident."""
        affected_service = random.choice(["api", "payments"])
        self.services[affected_service].status = ServiceStatus.UNHEALTHY
        
        # Generate alerts
        alert = Alert(
            id=str(uuid4()),
            severity=AlertSeverity.MEDIUM,
            service=affected_service,
            message=f"High memory usage detected in {affected_service}",
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        
        # Generate memory-related logs
        for i in range(5):
            log_entry = LogEntry(
                timestamp=datetime.now() - timedelta(minutes=i),
                level=LogLevel.WARN,
                service=affected_service,
                message=f"Memory usage at {random.uniform(85, 95)}%"
            )
            self.logs[affected_service].append(log_entry)
        
        # Generate high memory metrics
        for i in range(5):
            memory_metric = MetricData(
                name="memory_usage",
                value=random.uniform(85, 95),  # 85-95% memory usage
                unit="percent",
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            self.metrics[affected_service].append(memory_metric)
        
        self._severity = AlertSeverity.MEDIUM

    def _generate_bad_deployment(self):
        """Generate a bad deployment incident."""
        affected_service = random.choice(["auth", "payments"])
        old_version = self.services[affected_service].version
        new_version = f"v{random.randint(1,4)}.{random.randint(0,9)}.{random.randint(0,9)}-bad"
        
        self.services[affected_service].version = new_version
        self.services[affected_service].last_deployed = datetime.now()
        self.services[affected_service].status = ServiceStatus.UNHEALTHY
        
        # Generate alerts
        alert = Alert(
            id=str(uuid4()),
            severity=AlertSeverity.HIGH,
            service=affected_service,
            message=f"Deployment of {new_version} causing service instability",
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        
        # Generate deployment-related logs
        for i in range(7):
            log_entry = LogEntry(
                timestamp=datetime.now() - timedelta(minutes=i),
                level=LogLevel.ERROR,
                service=affected_service,
                message=f"Deployment {new_version} failed to initialize properly"
            )
            self.logs[affected_service].append(log_entry)
        
        self._severity = AlertSeverity.HIGH

    def reset(self) -> IncidentObservation:
        """
        Reset the environment for a new episode.
        
        Returns:
            IncidentObservation with initial state
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count += 1
        
        # Reset services
        self._initialize_services()
        
        # Generate new incident
        self._generate_incident()
        
        # Reset task state
        self._current_task = "triage"
        self._task_progress = 0.0
        
        # Create observation
        observation = self._create_observation()
        
        return observation

    def step(self, action: IncidentAction) -> IncidentObservation:
        """
        Execute a step in the environment.
        
        Args:
            action: IncidentAction to execute
            
        Returns:
            IncidentObservation with updated state
        """
        self._state.step_count += 1
        
        # Add action to timeline
        action_str = f"Step {self._state.step_count}: {action.action_type.value}"
        if action.service_name:
            action_str += f" on {action.service_name}"
        self._incident_timeline.append(action_str)
        
        # Process action
        reward = self._process_action(action)
        
        # Update task progress
        self._update_task_progress(action)
        
        # Create observation
        observation = self._create_observation()
        observation.reward = reward
        
        # Check if episode is done
        observation.done = self._is_episode_done()
        
        return observation

    def _process_action(self, action: IncidentAction) -> float:
        """Process the action and return reward."""
        base_reward = 0.0
        
        if action.action_type == ActionType.INSPECT_LOGS:
            if action.service_name and action.service_name in self.services:
                base_reward = 0.1
                # Add relevant logs to evidence if service is affected
                if self._is_service_affected(action.service_name):
                    relevant_logs = [
                        log for log in self.logs[action.service_name][-10:]
                        if log.level in [LogLevel.ERROR, LogLevel.WARN, LogLevel.FATAL]
                    ]
                    if relevant_logs:
                        self._evidence.extend([f"Log from {action.service_name}: {log.message}" for log in relevant_logs[:3]])
                        base_reward += 0.1
        
        elif action.action_type == ActionType.CHECK_METRICS:
            if action.service_name and action.service_name in self.services:
                base_reward = 0.1
                # Add relevant metrics to evidence if service is affected
                if self._is_service_affected(action.service_name):
                    relevant_metrics = self.metrics[action.service_name][-5:]
                    if relevant_metrics:
                        self._evidence.append(f"Metrics from {action.service_name}: {len(relevant_metrics)} data points")
                        base_reward += 0.1
        
        elif action.action_type == ActionType.RESTART_SERVICE:
            if action.service_name and action.service_name in self.services:
                if self.services[action.service_name].status in [ServiceStatus.CRASHED, ServiceStatus.UNHEALTHY]:
                    # Restart successful
                    self.services[action.service_name].status = ServiceStatus.HEALTHY
                    self.services[action.service_name].replicas = max(1, self.services[action.service_name].replicas)
                    base_reward = 0.3
                    self._applied_action = f"restart_{action.service_name}"
                    
                    # Start recovery timer
                    if not self._recovery_start_time:
                        self._recovery_start_time = datetime.now()
                else:
                    # Restart on healthy service - small penalty
                    base_reward = -0.05
        
        elif action.action_type == ActionType.SCALE_SERVICE:
            if action.service_name and action.service_name in self.services and action.replicas:
                old_replicas = self.services[action.service_name].replicas
                self.services[action.service_name].replicas = action.replicas
                
                # Reward for scaling up under load
                if action.replicas > old_replicas and self._is_service_affected(action.service_name):
                    base_reward = 0.2
                else:
                    base_reward = 0.05
        
        elif action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
            if action.service_name and action.service_name in self.services:
                if self._current_incident == IncidentType.BAD_DEPLOYMENT and self._is_service_affected(action.service_name):
                    # Rollback successful
                    old_version = self.services[action.service_name].version
                    self.services[action.service_name].version = f"v{random.randint(1,4)}.{random.randint(0,9)}.{random.randint(0,9)}"
                    self.services[action.service_name].status = ServiceStatus.HEALTHY
                    base_reward = 0.4
                    self._applied_action = f"rollback_{action.service_name}"
                    
                    # Start recovery timer
                    if not self._recovery_start_time:
                        self._recovery_start_time = datetime.now()
                else:
                    base_reward = -0.05
        
        elif action.action_type == ActionType.CHECK_DEPENDENCIES:
            base_reward = 0.05
            # Add dependency info to evidence
            if action.service_name and action.service_name in self.dependencies:
                deps = self.dependencies[action.service_name]
                self._evidence.append(f"{action.service_name} depends on: {', '.join(deps)}")
        
        elif action.action_type == ActionType.ESCALATE_INCIDENT:
            base_reward = -0.1  # Escalation is generally a last resort
        
        # System health bonus
        health_score = self._calculate_system_health()
        base_reward += health_score * 0.1
        
        # Step penalty (encourages efficiency)
        step_penalty = -0.01
        base_reward += step_penalty
        
        return base_reward

    def _is_service_affected(self, service_name: str) -> bool:
        """Check if a service is affected by the current incident."""
        return self.services[service_name].status != ServiceStatus.HEALTHY

    def _calculate_system_health(self) -> float:
        """Calculate overall system health score."""
        healthy_count = sum(1 for service in self.services.values() if service.status == ServiceStatus.HEALTHY)
        total_count = len(self.services)
        return healthy_count / total_count

    def _update_task_progress(self, action: IncidentAction):
        """Update task progress based on action."""
        if self._current_task == "triage":
            # Progress based on identifying affected services
            newly_identified = []
            for service_name in self.services:
                if self._is_service_affected(service_name) and service_name not in self._identified_services:
                    if action.action_type in [ActionType.INSPECT_LOGS, ActionType.CHECK_METRICS] and action.service_name == service_name:
                        newly_identified.append(service_name)
            
            self._identified_services.extend(newly_identified)
            
            # Update incident type and severity based on evidence
            if len(self._identified_services) >= 2:
                if self._current_incident == IncidentType.DEPENDENCY_FAILURE:
                    self._incident_type = IncidentType.DEPENDENCY_FAILURE
                else:
                    self._incident_type = self._current_incident
                self._severity = self._severity
            
            # Calculate progress
            total_affected = sum(1 for service_name, service_info in self.services.items() if self._is_service_affected(service_name))
            if total_affected > 0:
                self._task_progress = len(self._identified_services) / total_affected
        
        elif self._current_task == "diagnosis":
            # Progress based on gathering evidence
            if action.action_type in [ActionType.INSPECT_LOGS, ActionType.CHECK_METRICS, ActionType.CHECK_DEPENDENCIES]:
                if len(self._evidence) >= 3:
                    self._task_progress = min(1.0, len(self._evidence) / 5.0)
                    
                    # Set root cause based on incident type
                    if not self._root_cause and self._task_progress >= 0.6:
                        self._root_cause = self._get_root_cause_description()
        
        elif self._current_task == "resolution":
            # Progress based on system recovery
            health_score = self._calculate_system_health()
            self._task_progress = health_score

    def _get_root_cause_description(self) -> str:
        """Get root cause description based on incident type."""
        if self._current_incident == IncidentType.SERVICE_CRASH:
            return "Service crash due to memory leak"
        elif self._current_incident == IncidentType.PERFORMANCE_DEGRADATION:
            return "Performance degradation due to high database load"
        elif self._current_incident == IncidentType.DEPENDENCY_FAILURE:
            return "Database connectivity issues causing upstream service failures"
        elif self._current_incident == IncidentType.RESOURCE_EXHAUSTION:
            return "Memory exhaustion due to inefficient resource management"
        elif self._current_incident == IncidentType.BAD_DEPLOYMENT:
            return "Faulty deployment causing service instability"
        return "Unknown root cause"

    def _is_episode_done(self) -> bool:
        """Check if the episode is done."""
        # Episode is done when all services are healthy
        all_healthy = all(service.status == ServiceStatus.HEALTHY for service in self.services.values())
        
        # Or if we've taken too many steps
        max_steps = 50
        if self._state.step_count >= max_steps:
            return True
        
        return all_healthy

    def _create_observation(self) -> IncidentObservation:
        """Create the current observation."""
        # Determine available actions
        available_actions = list(ActionType)
        
        return IncidentObservation(
            alerts=self.alerts.copy(),
            services={name: ServiceStatusInfo(**service.dict()) for name, service in self.services.items()},
            logs={service: logs[-20:] for service, logs in self.logs.items()},  # Last 20 logs
            metrics={service: metrics[-10:] for service, metrics in self.metrics.items()},  # Last 10 metrics
            dependencies=self.dependencies.copy(),
            incident_timeline=self._incident_timeline.copy(),
            available_actions=available_actions,
            current_task=self._current_task,
            task_progress=self._task_progress,
            identified_services=self._identified_services.copy(),
            incident_type=self._incident_type,
            severity=self._severity,
            root_cause=self._root_cause,
            evidence=self._evidence.copy(),
            applied_action=self._applied_action,
            recovery_time_seconds=int((datetime.now() - self._recovery_start_time).total_seconds()) if self._recovery_start_time else None,
            done=False,
            reward=0.0,
        )

    @property
    def state(self) -> State:
        """
        Get the current environment state.
        
        Returns:
            Current State with episode_id and step_count
        """
        return self._state
