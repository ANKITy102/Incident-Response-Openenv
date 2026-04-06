# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Task definitions for the Mini Incident Response Copilot Environment.

This module defines the three required tasks with increasing difficulty:
1. Triage (Easy) - Identify affected services and incident severity
2. Diagnosis (Medium) - Find root cause through investigation
3. Resolution (Hard) - Apply correct fix and verify resolution
"""

from typing import Dict, List, Optional
from enum import Enum

try:
    from .models import (
        IncidentType,
        AlertSeverity,
        ServiceStatus,
        ActionType,
        TriageResult,
        DiagnosisResult,
        ResolutionResult,
    )
except ImportError:
    from models import (
        IncidentType,
        AlertSeverity,
        ServiceStatus,
        ActionType,
        TriageResult,
        DiagnosisResult,
        ResolutionResult,
    )


class TaskType(str, Enum):
    """Types of tasks available in the environment."""
    TRIAGE = "triage"
    DIAGNOSIS = "diagnosis"
    RESOLUTION = "resolution"


class Task:
    """Base class for all tasks."""
    
    def __init__(self, task_type: TaskType, name: str, description: str, difficulty: str):
        self.task_type = task_type
        self.name = name
        self.description = description
        self.difficulty = difficulty
    
    def get_instructions(self) -> str:
        """Get task instructions for the agent."""
        raise NotImplementedError
    
    def get_success_criteria(self) -> str:
        """Get success criteria for the task."""
        raise NotImplementedError
    
    def get_expected_result(self) -> Optional[object]:
        """Get the expected result for grading."""
        raise NotImplementedError


class TriageTask(Task):
    """Task 1: Triage - Identify affected services and incident severity."""
    
    def __init__(self):
        super().__init__(
            task_type=TaskType.TRIAGE,
            name="Incident Triage",
            description="Identify which services are affected and determine the incident type and severity.",
            difficulty="Easy"
        )
    
    def get_instructions(self) -> str:
        return """
        You are a junior SRE responding to a production incident. Your task is to perform initial triage.

        OBJECTIVES:
        1. Identify which services are affected by the incident
        2. Determine the type of incident (service crash, performance degradation, etc.)
        3. Assess the severity level (low, medium, high, critical)

        AVAILABLE ACTIONS:
        - inspect_logs(service_name): Check recent log entries for errors and warnings
        - check_metrics(service_name, metric_type): Review performance metrics
        - check_dependencies(service_name): Examine service dependencies

        APPROACH:
        1. Start by examining alerts to understand the scope
        2. Check logs and metrics for affected services
        3. Look for patterns that indicate incident type
        4. Assess severity based on impact and number of services affected

        Focus on efficient investigation - you have limited time to triage the incident.
        """
    
    def get_success_criteria(self) -> str:
        return """
        Success is achieved when:
        1. All affected services are correctly identified
        2. The incident type is correctly determined
        3. The severity level is accurately assessed
        
        Partial credit is given for partially correct identification.
        """
    
    def get_expected_result(self, affected_services: List[str], incident_type: IncidentType, severity: AlertSeverity) -> TriageResult:
        """Get the expected result for this specific incident."""
        return TriageResult(
            affected_services=affected_services,
            incident_type=incident_type,
            severity=severity
        )


class DiagnosisTask(Task):
    """Task 2: Diagnosis - Find root cause through investigation."""
    
    def __init__(self):
        super().__init__(
            task_type=TaskType.DIAGNOSIS,
            name="Root Cause Analysis",
            description="Investigate the incident to identify the root cause with supporting evidence.",
            difficulty="Medium"
        )
    
    def get_instructions(self) -> str:
        return """
        You are a junior SRE continuing incident response after initial triage. Your task is to diagnose the root cause.

        OBJECTIVES:
        1. Analyze logs for error patterns and anomalies
        2. Review metrics for performance issues and resource problems
        3. Trace through service dependencies to identify failure points
        4. Identify the specific root cause of the incident
        5. Gather evidence to support your diagnosis

        AVAILABLE ACTIONS:
        - inspect_logs(service_name, time_range): Check log entries for specific time periods
        - check_metrics(service_name, metric_type): Review detailed metrics
        - check_dependencies(service_name): Examine upstream/downstream dependencies

        APPROACH:
        1. Start with services identified during triage
        2. Look for correlation between different data sources
        3. Consider timing and sequence of events
        4. Build a comprehensive evidence chain
        5. Formulate a specific root cause hypothesis

        Be thorough in your investigation - accurate diagnosis is critical for effective resolution.
        """
    
    def get_success_criteria(self) -> str:
        return """
        Success is achieved when:
        1. The root cause is correctly identified
        2. Supporting evidence is gathered and relevant
        3. The diagnosis explains all observed symptoms
        
        Partial credit is given for partially correct diagnosis with some evidence.
        """
    
    def get_expected_result(self, root_cause: str, evidence: List[str]) -> DiagnosisResult:
        """Get the expected result for this specific incident."""
        return DiagnosisResult(
            root_cause=root_cause,
            evidence=evidence
        )


class ResolutionTask(Task):
    """Task 3: Resolution - Apply correct fix and verify resolution."""
    
    def __init__(self):
        super().__init__(
            task_type=TaskType.RESOLUTION,
            name="Incident Resolution",
            description="Apply the correct fix to resolve the incident and verify system recovery.",
            difficulty="Hard"
        )
    
    def get_instructions(self) -> str:
        return """
        You are a junior SRE implementing the fix for a diagnosed incident. Your task is to resolve the incident.

        OBJECTIVES:
        1. Apply the appropriate fix based on the root cause
        2. Monitor system recovery in real-time
        3. Verify all services return to healthy state
        4. Ensure minimal downtime and service disruption

        AVAILABLE ACTIONS:
        - restart_service(service_name): Restart a crashed or unhealthy service
        - scale_service(service_name, replicas): Scale service up/down for resource issues
        - rollback_deployment(service_name, version): Rollback to previous stable version
        - check_metrics(service_name, metric_type): Monitor recovery progress
        - inspect_logs(service_name): Verify fix effectiveness

        APPROACH:
        1. Select the most appropriate action based on the diagnosis
        2. Apply the fix decisively
        3. Monitor system response closely
        4. Verify complete recovery
        5. Consider secondary effects and dependencies

        Focus on speed and accuracy - every minute of downtime impacts users.
        """
    
    def get_success_criteria(self) -> str:
        return """
        Success is achieved when:
        1. The correct fix is applied
        2. All services return to healthy state
        3. Recovery time is minimized
        4. No secondary issues are introduced
        
        Partial credit is given for partial recovery or suboptimal fix choices.
        """
    
    def get_expected_result(self, optimal_action: str, expected_recovery_time: int) -> ResolutionResult:
        """Get the expected result for this specific incident."""
        return ResolutionResult(
            optimal_action=optimal_action,
            expected_recovery_time=expected_recovery_time
        )


class TaskManager:
    """Manages task creation and progression."""
    
    def __init__(self):
        self.tasks = {
            TaskType.TRIAGE: TriageTask(),
            TaskType.DIAGNOSIS: DiagnosisTask(),
            TaskType.RESOLUTION: ResolutionTask(),
        }
    
    def get_task(self, task_type: TaskType) -> Task:
        """Get a task by type."""
        return self.tasks[task_type]
    
    def get_all_tasks(self) -> List[Task]:
        """Get all available tasks."""
        return list(self.tasks.values())
    
    def get_task_sequence(self) -> List[Task]:
        """Get tasks in order of difficulty (easy to hard)."""
        return [
            self.tasks[TaskType.TRIAGE],
            self.tasks[TaskType.DIAGNOSIS],
            self.tasks[TaskType.RESOLUTION],
        ]
    
    def get_next_task(self, current_task: TaskType) -> Optional[Task]:
        """Get the next task in the sequence."""
        sequence = self.get_task_sequence()
        current_index = sequence.index(self.tasks[current_task])
        
        if current_index + 1 < len(sequence):
            return sequence[current_index + 1]
        return None


# Global task manager instance
task_manager = TaskManager()


# Helper functions for task execution
def get_task_for_incident(incident_type: IncidentType, affected_services: List[str], severity: AlertSeverity) -> Dict:
    """Get task-specific information for a given incident."""
    
    # Determine optimal actions based on incident type
    optimal_actions = {
        IncidentType.SERVICE_CRASH: "restart_service",
        IncidentType.PERFORMANCE_DEGRADATION: "scale_service",
        IncidentType.DEPENDENCY_FAILURE: "restart_service",  # Restart database
        IncidentType.RESOURCE_EXHAUSTION: "scale_service",
        IncidentType.BAD_DEPLOYMENT: "rollback_deployment",
    }
    
    # Expected recovery times (in seconds)
    recovery_times = {
        IncidentType.SERVICE_CRASH: 60,
        IncidentType.PERFORMANCE_DEGRADATION: 120,
        IncidentType.DEPENDENCY_FAILURE: 90,
        IncidentType.RESOURCE_EXHAUSTION: 180,
        IncidentType.BAD_DEPLOYMENT: 45,
    }
    
    # Root cause descriptions
    root_causes = {
        IncidentType.SERVICE_CRASH: "Service crash due to memory leak",
        IncidentType.PERFORMANCE_DEGRADATION: "Performance degradation due to high database load",
        IncidentType.DEPENDENCY_FAILURE: "Database connectivity issues causing upstream service failures",
        IncidentType.RESOURCE_EXHAUSTION: "Memory exhaustion due to inefficient resource management",
        IncidentType.BAD_DEPLOYMENT: "Faulty deployment causing service instability",
    }
    
    return {
        "triage": TriageResult(
            affected_services=affected_services,
            incident_type=incident_type,
            severity=severity
        ),
        "diagnosis": DiagnosisResult(
            root_cause=root_causes[incident_type],
            evidence=[
                f"Logs show errors in {', '.join(affected_services)}",
                f"Metrics indicate {incident_type.value}",
                f"Dependency analysis reveals upstream/downstream impacts"
            ]
        ),
        "resolution": ResolutionResult(
            optimal_action=optimal_actions[incident_type],
            expected_recovery_time=recovery_times[incident_type]
        )
    }
