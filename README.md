---
title: Mini Incident Response Copilot Environment
emoji: 🚨
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - incident-response
  - sre
  - devops
---

# Mini Incident Response Copilot Environment

A sophisticated incident response environment that simulates real-world SaaS operations where an AI agent acts like a junior SRE. The environment presents alerts, logs, metrics, and service dependencies, and the agent has to investigate the issue, identify the root cause, and take the correct action.

## Overview

This environment simulates a microservices architecture with 5 core services:
- **auth**: Authentication service
- **payments**: Payment processing service  
- **api**: API gateway service
- **database**: Database service
- **cache**: Redis cache service

The environment generates realistic incidents including service crashes, performance degradation, dependency failures, resource exhaustion, and bad deployments.

## Tasks

The environment includes three tasks with increasing difficulty:

### Task 1: Triage (Easy)
**Goal**: Identify affected services and incident severity
- Analyze alerts and system state
- Determine incident type and severity
- Identify all affected services

### Task 2: Diagnosis (Medium)
**Goal**: Find root cause through investigation
- Analyze logs for error patterns
- Review metrics for anomalies
- Trace through service dependencies
- Identify specific root cause

### Task 3: Resolution (Hard)
**Goal**: Apply correct fix and verify resolution
- Apply appropriate fix based on diagnosis
- Monitor system recovery
- Verify all services return to healthy state

## Quick Start

The simplest way to use the Incident Response environment is through the `IncidentResponseEnv` class:

```python
from incident_response import IncidentAction, IncidentResponseEnv, ActionType

try:
    # Create environment from Docker image
    env = IncidentResponseEnv.from_docker_image("incident_response-env:latest")

    # Reset environment
    result = env.reset()
    print(f"Alerts: {len(result.observation.alerts)}")
    
    # Investigate incident
    action = IncidentAction(action_type=ActionType.INSPECT_LOGS, service_name="auth")
    result = env.step(action)
    print(f"Reward: {result.reward:.3f}")
    print(f"Evidence: {len(result.observation.evidence)}")

finally:
    # Always clean up
    env.close()
```

## Available Actions

The SRE agent can perform the following actions:

- **inspect_logs(service_name, time_range)**: Check recent log entries
- **check_metrics(service_name, metric_type)**: Review performance metrics
- **restart_service(service_name)**: Restart a crashed service
- **scale_service(service_name, replicas)**: Scale service resources
- **rollback_deployment(service_name, version)**: Rollback to previous version
- **check_dependencies(service_name)**: Examine service dependencies
- **escalate_incident(reason)**: Escalate to senior SRE

## Environment Details

### Observation
**IncidentObservation** contains:
- `alerts`: Active alerts with severity levels
- `services`: Service health states and configuration
- `logs`: Recent log entries from all services
- `metrics`: Performance metrics (latency, error rate, CPU, memory)
- `dependencies`: Service dependency graph
- `incident_timeline`: Action history
- `task_progress`: Current task completion status

### Reward System
The reward system provides:
- **Action-specific rewards**: Higher rewards for correct actions
- **System health bonus**: Rewards for maintaining service availability
- **Step penalties**: Encourages efficient resolution
- **Partial progress signals**: Rewards for moving toward solution

### Grading
Each task has deterministic graders that return scores 0.0-1.0:
- **Triage Grader**: Service identification (50%), incident type (30%), severity (20%)
- **Diagnosis Grader**: Root cause (60%), evidence quality (40%)
- **Resolution Grader**: Correct action (40%), recovery time (40%), system health (20%)

## Building the Docker Image

Before using the environment, you need to build the Docker image:

```bash
# From project root
docker build -t incident_response-env:latest -f server/Dockerfile .
```

## Running Inference

The environment includes a baseline inference script that uses OpenAI models:

```bash
# Set environment variables
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4"
export HF_TOKEN="your_hf_token"

# Run inference
python inference.py
```

The inference script follows the required logging format:
```
[START] task=triage env=incident_response model=gpt-4
[STEP] step=1 action=inspect_logs(auth) reward=0.1 done=false error=
[END] success=0.85 steps=12 rewards=1.23
```

## Deploying to Hugging Face Spaces

Deploy your OpenEnv environment to Hugging Face Spaces:

```bash
# From the environment directory
openenv push

# Or specify options
openenv push --namespace my-org --private
```

## Development & Testing

### Direct Environment Testing

Test the environment logic directly:

```bash
# From the server directory
python3 server/incident_response_environment.py
```

### Running Locally

Run the server locally for development:

```bash
uvicorn server.app:app --reload
```

### Validation

Validate your environment:

```bash
openenv validate
```

## Project Structure

```
incident_response/
├── .dockerignore         # Docker build exclusions
├── __init__.py            # Module exports
├── README.md              # This file
├── openenv.yaml           # OpenEnv manifest
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependencies
├── client.py              # IncidentResponseEnv client
├── models.py              # IncidentAction, IncidentObservation, supporting models
├── tasks.py               # Task definitions (triage, diagnosis, resolution)
├── graders.py             # Grading logic for each task
├── inference.py           # Baseline LLM inference script
└── server/
    ├── __init__.py        # Server module exports
    ├── incident_response_environment.py  # Core environment logic
    ├── app.py             # FastAPI application
    ├── requirements.txt    # Server dependencies
    └── Dockerfile         # Container image definition
```

## License

This source code is licensed under the BSD-style license found in the LICENSE file in the root directory of this source tree.
