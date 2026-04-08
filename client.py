# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""My Env Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import (
    IncidentAction, 
    IncidentObservation,
    Alert,
    ServiceStatusInfo,
    LogEntry,
    MetricData,
    ActionType,
    AlertSeverity,
    IncidentType,
)


class IncidentResponseEnv(
    EnvClient[IncidentAction, IncidentObservation, State]
):
    """
    Client for the Incident Response Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with IncidentResponseEnv(base_url="http://localhost:7860") as client:
        ...     result = client.reset()
        ...     print(result.observation.alerts)
        ...
        ...     result = client.step(IncidentAction(action_type=ActionType.INSPECT_LOGS, service_name="auth"))
        ...     print(result.observation.logs)

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = IncidentResponseEnv.from_docker_image("incident_response-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(IncidentAction(action_type=ActionType.RESTART_SERVICE, service_name="payments"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: IncidentAction) -> Dict:
        """
        Convert IncidentAction to JSON payload for step message.

        Args:
            action: IncidentAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        payload = {
            "action_type": action.action_type,
        }
        
        # Add optional fields if they exist
        if action.service_name is not None:
            payload["service_name"] = action.service_name
        if action.time_range is not None:
            payload["time_range"] = action.time_range
        if action.metric_type is not None:
            payload["metric_type"] = action.metric_type
        if action.replicas is not None:
            payload["replicas"] = action.replicas
        if action.version is not None:
            payload["version"] = action.version
        if action.reason is not None:
            payload["reason"] = action.reason
            
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[IncidentObservation]:
        """
        Parse server response into StepResult[IncidentObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with IncidentObservation
        """
        obs_data = payload.get("observation", {})
        
        # Parse alerts
        alerts = []
        for alert_data in obs_data.get("alerts", []):
            alerts.append(Alert(**alert_data))
        
        # Parse services
        services = {}
        for service_name, service_data in obs_data.get("services", {}).items():
            services[service_name] = ServiceStatusInfo(**service_data)
        
        # Parse logs
        logs = {}
        for service_name, log_entries in obs_data.get("logs", {}).items():
            logs[service_name] = [LogEntry(**entry) for entry in log_entries]
        
        # Parse metrics
        metrics = {}
        for service_name, metric_entries in obs_data.get("metrics", {}).items():
            metrics[service_name] = [MetricData(**entry) for entry in metric_entries]
        
        observation = IncidentObservation(
            alerts=alerts,
            services=services,
            logs=logs,
            metrics=metrics,
            dependencies=obs_data.get("dependencies", {}),
            incident_timeline=obs_data.get("incident_timeline", []),
            available_actions=[ActionType(action) for action in obs_data.get("available_actions", [])],
            current_task=obs_data.get("current_task"),
            task_progress=obs_data.get("task_progress", 0.0),
            identified_services=obs_data.get("identified_services", []),
            incident_type=IncidentType(obs_data["incident_type"]) if obs_data.get("incident_type") else None,
            severity=AlertSeverity(obs_data["severity"]) if obs_data.get("severity") else None,
            root_cause=obs_data.get("root_cause"),
            evidence=obs_data.get("evidence", []),
            applied_action=obs_data.get("applied_action"),
            recovery_time_seconds=obs_data.get("recovery_time_seconds"),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
