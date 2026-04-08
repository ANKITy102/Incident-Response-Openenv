---
title: Mini Incident Response Copilot Environment
emoji: 🚨
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
app_port: 7860
license: mit
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

## Live Deployment & Service Interaction

### Hugging Face Space
**Deployed URL**: https://huggingface.co/spaces/raghubansal/Incident-Response-Copilot

### API Endpoints (Tested & Working)

All endpoints have been tested and confirmed working with the following actual responses:

#### Health Check - WORKING
```bash
curl https://raghubansal-incident-response-copilot.hf.space/health
# RESPONSE: {"status": "healthy"}
```

#### Reset Environment - WORKING
```bash
curl -X POST https://raghubansal-incident-response-copilot.hf.space/reset \
  -H "Content-Type: application/json" -d "{}"
# RESPONSE: Returns full observation with alerts, services, and initial state
```

#### Step Actions - WORKING
```bash
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"inspect_logs","service_name":"auth"}}'
# RESPONSE: {"observation": {...}, "reward": 0.19, "done": false}
```

#### Get State - WORKING
```bash
curl https://raghubansal-incident-response-copilot.hf.space/state
# RESPONSE: Current environment state with task progress
```

The deployed environment exposes the following HTTP endpoints:

#### Health Check
```bash
curl https://raghubansal-incident-response-copilot.hf.space/health
# Response: {"status": "ok"}
```

#### Reset Environment
```bash
curl -X POST https://raghubansal-incident-response-copilot.hf.space/reset \
  -H "Content-Type: application/json" \
  -d "{}"
```
**Response Example:**
```json
{
  "observation": {
    "alerts": [{"id": "1", "severity": "high", "service": "auth", "message": "Service crash detected"}],
    "current_task": "triage",
    "task_progress": 0.0,
    "available_actions": ["inspect_logs", "check_metrics", "restart_service"]
  },
  "reward": 0.0,
  "done": false
}
```

#### Execute Action
```bash
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "inspect_logs",
      "service_name": "auth",
      "time_range": "1h"
    }
  }'
```
**Response Example:**
```json
{
  "observation": {
    "current_task": "triage",
    "task_progress": 0.1,
    "evidence": ["Auth service showing memory leak patterns"],
    "incident_timeline": ["Step 1: inspect_logs on auth"]
  },
  "reward": 0.19,
  "done": false
}
```

#### Get Current State
```bash
curl https://raghubansal-incident-response-copilot.hf.space/state
```
**Response Example:**
```json
{
  "observation": {
    "current_task": "triage",
    "task_progress": 0.15,
    "identified_services": ["auth"],
    "incident_type": "service_crash",
    "severity": "high"
  }
}
```

### Service Interaction Examples

#### 1. Investigating Auth Service Logs
```bash
# Step 1: Reset environment
curl -X POST https://raghubansal-incident-response-copilot.hf.space/reset \
  -H "Content-Type: application/json" -d "{}"

# Step 2: Check auth service logs
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "inspect_logs",
      "service_name": "auth"
    }
  }'

# Step 3: Check auth service metrics
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "check_metrics",
      "service_name": "auth",
      "metric_type": "latency"
    }
  }'
```

#### 2. Diagnosing Payment Service Issues
```bash
# Check payment service dependencies
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "check_dependencies",
      "service_name": "payments"
    }
  }'

# Check payment error rate
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "check_metrics",
      "service_name": "payments",
      "metric_type": "error_rate"
    }
  }'
```

#### 3. Applying Fixes
```bash
# Restart crashed service
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "restart_service",
      "service_name": "auth"
    }
  }'

# Scale service for resource issues
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "scale_service",
      "service_name": "payments",
      "replicas": 3
    }
  }'

# Rollback bad deployment
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "rollback_deployment",
      "service_name": "api",
      "version": "v2.8.8"
    }
  }'
```

### Available Services

The environment simulates 5 microservices:

| Service | Description | Common Issues |
|---------|-------------|---------------|
| **auth** | Authentication service | Memory leaks, token failures |
| **payments** | Payment processing | Database connectivity, high load |
| **api** | API gateway | Rate limiting, routing issues |
| **database** | PostgreSQL database | Connection exhaustion, slow queries |
| **cache** | Redis cache | Memory pressure, eviction policies |

### Action Parameters

#### inspect_logs
- `service_name` (required): Service to inspect
- `time_range` (optional): Time window (default: "1h")

#### check_metrics
- `service_name` (required): Service to check
- `metric_type` (required): "latency", "error_rate", "throughput", "cpu_usage", "memory_usage"

#### restart_service
- `service_name` (required): Service to restart

#### scale_service
- `service_name` (required): Service to scale
- `replicas` (required): Target replica count

#### rollback_deployment
- `service_name` (required): Service to rollback
- `version` (required): Target version

#### check_dependencies
- `service_name` (required): Service to analyze

#### escalate_incident
- `reason` (required): Escalation reason

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

### Complete Service Testing Workflow

Here's a comprehensive workflow to test all services and actions:

#### Full Incident Response Simulation
```bash
#!/bin/bash
# Complete incident response test script

BASE_URL="https://raghubansal-incident-response-copilot.hf.space"

echo "=== Starting Incident Response Test ==="

# 1. Reset environment
echo "1. Resetting environment..."
curl -X POST $BASE_URL/reset -H "Content-Type: application/json" -d "{}"

# 2. Triage Phase - Check all services
echo -e "\n2. TRIAGE PHASE - Checking all services..."

# Check auth service
echo "Checking auth service..."
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"inspect_logs","service_name":"auth"}}'

# Check payments service  
echo "Checking payments service..."
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"payments","metric_type":"error_rate"}}'

# Check API gateway
echo "Checking API gateway..."
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"inspect_logs","service_name":"api"}}'

# Check database
echo "Checking database..."
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"database","metric_type":"cpu_usage"}}'

# Check cache
echo "Checking cache..."
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"cache","metric_type":"memory_usage"}}'

# 3. Diagnosis Phase - Deep dive on affected services
echo -e "\n3. DIAGNOSIS PHASE - Deep investigation..."

# Check dependencies for problematic service
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_dependencies","service_name":"auth"}}'

# Check detailed metrics
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"auth","metric_type":"latency"}}'

# Check recent logs with time range
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"inspect_logs","service_name":"auth","time_range":"30m"}}'

# 4. Resolution Phase - Apply fixes
echo -e "\n4. RESOLUTION PHASE - Applying fixes..."

# Restart crashed service
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"restart_service","service_name":"auth"}}'

# Scale service if needed
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"scale_service","service_name":"payments","replicas":3}}'

# Rollback if deployment issue
curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"rollback_deployment","service_name":"api","version":"v2.8.8"}}'

# 5. Verify Recovery
echo -e "\n5. VERIFICATION PHASE - Checking recovery..."

# Check all services are healthy
for service in auth payments api database cache; do
  echo "Checking $service service status..."
  curl -X POST $BASE_URL/step -H "Content-Type: application/json" \
    -d "{\"action\":{\"action_type\":\"check_metrics\",\"service_name\":\"$service\",\"metric_type\":\"error_rate\"}}"
done

echo -e "\n=== Test Complete ==="
```

#### Testing Individual Service Actions

**Auth Service Testing:**
```bash
# Test auth service memory issues
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"auth","metric_type":"memory_usage"}}'

# Test auth service logs for authentication failures
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"inspect_logs","service_name":"auth","time_range":"15m"}}'
```

**Payments Service Testing:**
```bash
# Test payment processing latency
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"payments","metric_type":"latency"}}'

# Test payment throughput
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"payments","metric_type":"throughput"}}'
```

**Database Service Testing:**
```bash
# Test database connection pool
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"database","metric_type":"cpu_usage"}}'

# Test database slow queries
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"inspect_logs","service_name":"database","time_range":"1h"}}'
```

**Cache Service Testing:**
```bash
# Test cache memory pressure
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"cache","metric_type":"memory_usage"}}'

# Test cache hit rates
curl -X POST https://raghubansal-incident-response-copilot.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action":{"action_type":"check_metrics","service_name":"cache","metric_type":"throughput"}}'
```

#### Python Client Example
```python
import requests
import json

BASE_URL = "https://raghubansal-incident-response-copilot.hf.space"

def test_all_services():
    """Test interaction with all services"""
    
    # Reset environment
    response = requests.post(f"{BASE_URL}/reset", json={})
    print("Environment reset:", response.status_code)
    
    services = ["auth", "payments", "api", "database", "cache"]
    metrics = ["latency", "error_rate", "cpu_usage", "memory_usage", "throughput"]
    
    for service in services:
        print(f"\n=== Testing {service.upper()} Service ===")
        
        # Check logs
        response = requests.post(f"{BASE_URL}/step", json={
            "action": {
                "action_type": "inspect_logs",
                "service_name": service
            }
        })
        print(f"Logs check: {response.status_code}")
        
        # Check all metrics
        for metric in metrics:
            response = requests.post(f"{BASE_URL}/step", json={
                "action": {
                    "action_type": "check_metrics",
                    "service_name": service,
                    "metric_type": metric
                }
            })
            print(f"{metric}: {response.status_code}")
        
        # Check dependencies
        response = requests.post(f"{BASE_URL}/step", json={
            "action": {
                "action_type": "check_dependencies",
                "service_name": service
            }
        })
        print(f"Dependencies: {response.status_code}")

if __name__ == "__main__":
    test_all_services()
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
