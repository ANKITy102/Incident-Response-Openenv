#!/usr/bin/env python3
"""
Baseline inference script for the Mini Incident Response Copilot Environment.

This script runs an LLM agent through all three tasks and produces reproducible scores.
It follows the strict logging format required by the hackathon evaluation.

Usage:
    python inference.py
    
Environment Variables:
    API_BASE_URL: OpenAI API base URL (required)
    MODEL_NAME: Model name to use (required)
    HF_TOKEN: Hugging Face token (required)
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Any, Optional

import openai
from openenv.core import EnvClient

# Import our environment
try:
    from incident_response import (
        IncidentResponseEnv, 
        IncidentAction, 
        IncidentObservation,
        ActionType,
        MetricType,
        task_manager,
        grader_manager,
        get_task_for_incident
    )
except ImportError:
    # Fallback for local development
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from __init__ import (
        IncidentResponseEnv, 
        IncidentAction, 
        IncidentObservation,
        ActionType,
        MetricType,
        task_manager,
        grader_manager,
        get_task_for_incident
    )


class IncidentResponseAgent:
    """LLM agent for incident response tasks."""
    
    def __init__(self, client: openai.OpenAI, model_name: str):
        self.client = client
        self.model_name = model_name
        self.conversation_history = []
    
    def get_action(self, observation: IncidentObservation, task_instructions: str) -> IncidentAction:
        """Get the next action from the LLM based on current observation."""
        
        # Create system prompt
        system_prompt = f"""
You are a junior SRE responding to a production incident. You must follow these rules:

1. Always respond with a valid JSON object containing the action to take
2. Available action types: {', '.join([action.value for action in ActionType])}
3. Only include fields that are relevant to the action
4. Be decisive and specific in your actions
5. Focus on efficiency - every step counts

Current task: {observation.current_task}
Task progress: {observation.task_progress:.1%}

{task_instructions}

Current system state:
- Alerts: {len(observation.alerts)} active alerts
- Services: {len([s for s in observation.services.values() if s.status.value != 'healthy'])} unhealthy services
- Available actions: {', '.join([action.value for action in observation.available_actions])}

Recent timeline:
{chr(10).join(observation.incident_timeline[-5:])}

Respond with JSON like:
{{"action_type": "inspect_logs", "service_name": "auth"}}
or
{{"action_type": "check_metrics", "service_name": "payments", "metric_type": "latency"}}
"""
        
        # Create user prompt with observation details
        user_prompt = self._format_observation_for_prompt(observation)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for reproducible results
                max_tokens=200
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            action_data = self._extract_json_from_response(content)
            
            # Create IncidentAction
            return self._create_action_from_dict(action_data)
            
        except Exception as e:
            print(f"[ERROR] Error getting action from LLM: {e}", file=sys.stderr)
            # Return a safe default action
            return IncidentAction(action_type=ActionType.INSPECT_LOGS, service_name="auth")
    
    def _format_observation_for_prompt(self, observation: IncidentObservation) -> str:
        """Format observation for LLM prompt."""
        prompt_parts = []
        
        # Alerts
        if observation.alerts:
            prompt_parts.append("ALERTS:")
            for alert in observation.alerts:
                prompt_parts.append(f"- {alert.severity.value}: {alert.service} - {alert.message}")
        
        # Services
        prompt_parts.append("\nSERVICES:")
        for service_name, service_info in observation.services.items():
            status_emoji = "✅" if service_info.status.value == "healthy" else "❌"
            prompt_parts.append(f"- {status_emoji} {service_name}: {service_info.status.value} (replicas: {service_info.replicas})")
        
        # Recent logs (if available)
        if observation.logs:
            prompt_parts.append("\nRECENT LOGS (sample):")
            for service_name, logs in list(observation.logs.items())[:2]:  # Show first 2 services
                if logs:
                    recent_log = logs[-1]  # Most recent log
                    prompt_parts.append(f"- {service_name}: {recent_log.level.value} - {recent_log.message}")
        
        # Task progress
        if observation.current_task:
            prompt_parts.append(f"\nTASK: {observation.current_task.upper()}")
            prompt_parts.append(f"Progress: {observation.task_progress:.1%}")
            
            if observation.identified_services:
                prompt_parts.append(f"Identified services: {', '.join(observation.identified_services)}")
            
            if observation.incident_type:
                prompt_parts.append(f"Incident type: {observation.incident_type.value}")
            
            if observation.severity:
                prompt_parts.append(f"Severity: {observation.severity.value}")
            
            if observation.root_cause:
                prompt_parts.append(f"Root cause: {observation.root_cause}")
        
        return "\n".join(prompt_parts)
    
    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        # Try to find JSON in the response
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to parse the whole response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Default fallback
        return {"action_type": "inspect_logs", "service_name": "auth"}
    
    def _create_action_from_dict(self, action_data: Dict[str, Any]) -> IncidentAction:
        """Create IncidentAction from dictionary."""
        action_type_str = action_data.get("action_type", "inspect_logs")
        
        # Validate action type
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            action_type = ActionType.INSPECT_LOGS
        
        # Create action with relevant fields
        return IncidentAction(
            action_type=action_type,
            service_name=action_data.get("service_name"),
            time_range=action_data.get("time_range", "1h"),
            metric_type=MetricType(action_data.get("metric_type")) if action_data.get("metric_type") else None,
            replicas=action_data.get("replicas"),
            version=action_data.get("version"),
            reason=action_data.get("reason")
        )


async def run_single_task(env: IncidentResponseEnv, agent: IncidentResponseAgent, task_name: str) -> Dict[str, Any]:
    """Run a single task and return results."""
    
    # Get task
    task = task_manager.get_task(task_name)
    
    # Log task start
    print(f"[START] task={task_name} env=incident_response model={agent.model_name}")
    
    # Reset environment for this task
    result = await env.reset()
    observation = result.observation
    
    # Set current task in environment
    observation.current_task = task_name
    
    # Get task instructions
    instructions = task.get_instructions()
    
    # Track episode
    step_count = 0
    total_reward = 0.0
    start_time = time.time()
    
    try:
        while not observation.done and step_count < 50:  # Max 50 steps per task
            step_count += 1
            
            # Get action from agent
            action = agent.get_action(observation, instructions)
            
            # Execute action
            result = await env.step(action)
            observation = result.observation
            
            total_reward += result.reward or 0.0
            
            # Log step
            action_str = f"{action.action_type.value}"
            if action.service_name:
                action_str += f"({action.service_name})"
            if action.metric_type:
                action_str += f",{action.metric_type.value}"
            if action.replicas:
                action_str += f",replicas={action.replicas}"
            
            print(f"[STEP] step={step_count} action={action_str} reward={result.reward:.3f} done={observation.done} error=")
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
    
    except Exception as e:
        print(f"[ERROR] Error during task execution: {e}", file=sys.stderr)
        print(f"[STEP] step={step_count} action=error reward=0.0 done=true error={str(e)}")
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Log task end
    print(f"[END] success={observation.task_progress:.3f} steps={step_count} rewards={total_reward:.3f}")
    
    return {
        "observation": observation,
        "steps": step_count,
        "total_reward": total_reward,
        "execution_time": execution_time,
        "task_progress": observation.task_progress
    }


async def run_all_tasks() -> Dict[str, Any]:
    """Run all tasks and return comprehensive results."""
    
    # Check environment variables
    api_base_url = os.getenv("API_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    hf_token = os.getenv("HF_TOKEN")
    
    if not api_base_url or not model_name or not hf_token:
        print("[ERROR] Missing required environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN", file=sys.stderr)
        sys.exit(1)
    
    # Initialize OpenAI client
    client = openai.OpenAI(
        base_url=api_base_url,
        api_key=hf_token
    )
    
    # Initialize agent
    agent = IncidentResponseAgent(client, model_name)
    
    # Initialize environment
    try:
        env = IncidentResponseEnv(base_url="http://localhost:7860")
    except Exception as e:
        print(f"[ERROR] Failed to connect to environment: {e}", file=sys.stderr)
        print("[ERROR] Make sure the environment server is running on http://localhost:7860", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Run tasks in sequence
        task_sequence = ["triage", "diagnosis", "resolution"]
        all_results = {}
        
        for task_name in task_sequence:
            print(f"\n{'='*60}")
            print(f"Running task: {task_name.upper()}")
            print(f"{'='*60}")
            
            result = await run_single_task(env, agent, task_name)
            all_results[task_name] = result
            
            # Small delay between tasks
            time.sleep(1)
        
        # Calculate overall scores
        print(f"\n{'='*60}")
        print("CALCULATING SCORES")
        print(f"{'='*60}")
        
        # Get expected results for grading (use a sample incident)
        from incident_response.models import IncidentType, AlertSeverity
        sample_incident = get_task_for_incident(
            incident_type=IncidentType.SERVICE_CRASH,
            affected_services=["auth"],
            severity=AlertSeverity.CRITICAL
        )
        
        # Grade each task
        task_scores = {}
        for task_name, result in all_results.items():
            expected = sample_incident[task_name]
            score = grader_manager.grade_task(task_name, result["observation"], expected)
            task_scores[task_name] = score
            
            print(f"{task_name.capitalize()} score: {score:.3f}")
        
        # Calculate overall score
        overall_score = grader_manager.get_overall_score(task_scores)
        print(f"Overall score: {overall_score:.3f}")
        
        # Summary
        print(f"\n{'='*60}")
        print("EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        total_steps = sum(result["steps"] for result in all_results.values())
        total_reward = sum(result["total_reward"] for result in all_results.values())
        total_time = sum(result["execution_time"] for result in all_results.values())
        
        print(f"Total steps: {total_steps}")
        print(f"Total reward: {total_reward:.3f}")
        print(f"Total time: {total_time:.1f}s")
        print(f"Average steps per task: {total_steps / len(task_sequence):.1f}")
        
        return {
            "task_scores": task_scores,
            "overall_score": overall_score,
            "total_steps": total_steps,
            "total_reward": total_reward,
            "total_time": total_time,
            "task_results": all_results
        }
    
    finally:
        # Clean up environment
        await env.close()


def main():
    """Main entry point."""
    print("Starting Mini Incident Response Copilot Inference")
    print("=" * 60)
    
    try:
        results = asyncio.run(run_all_tasks())
        
        # Final summary
        print(f"\n{'='*60}")
        print("INFERENCE COMPLETE")
        print(f"{'='*60}")
        print(f"Final overall score: {results['overall_score']:.3f}")
        
        # Exit with appropriate code
        if results['overall_score'] >= 0.7:
            print("✅ Performance: GOOD")
            sys.exit(0)
        elif results['overall_score'] >= 0.4:
            print("⚠️  Performance: FAIR")
            sys.exit(0)
        else:
            print("❌ Performance: POOR")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n[INFO] Inference interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Inference failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
