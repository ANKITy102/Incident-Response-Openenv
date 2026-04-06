# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Grading system for the Mini Incident Response Copilot Environment.

This module implements deterministic graders for each task that return scores
between 0.0 and 1.0. The graders evaluate agent performance based on
accuracy, efficiency, and quality of actions taken.
"""

from typing import List, Set, Dict, Any
import math

try:
    from .models import (
        IncidentObservation,
        TriageResult,
        DiagnosisResult,
        ResolutionResult,
        IncidentType,
        AlertSeverity,
        ServiceStatus,
    )
except ImportError:
    from models import (
        IncidentObservation,
        TriageResult,
        DiagnosisResult,
        ResolutionResult,
        IncidentType,
        AlertSeverity,
        ServiceStatus,
    )


class BaseGrader:
    """Base class for all graders."""
    
    def grade(self, observation: IncidentObservation, expected: Any) -> float:
        """
        Grade the agent's performance.
        
        Args:
            observation: Current observation from the environment
            expected: Expected result for this specific incident
            
        Returns:
            Score between 0.0 and 1.0
        """
        raise NotImplementedError
    
    def _normalize_score(self, score: float) -> float:
        """Normalize score to [0.0, 1.0] range."""
        return max(0.0, min(1.0, score))


class TriageGrader(BaseGrader):
    """Grader for the triage task."""
    
    def grade(self, observation: IncidentObservation, expected: TriageResult) -> float:
        """
        Grade triage performance based on service identification, incident type, and severity.
        
        Scoring:
        - Service identification: 50% of total score
        - Incident type identification: 30% of total score  
        - Severity assessment: 20% of total score
        """
        # Grade service identification
        services_score = self._grade_service_identification(
            observation.identified_services, 
            expected.affected_services
        )
        
        # Grade incident type identification
        type_score = self._grade_incident_type_identification(
            observation.incident_type, 
            expected.incident_type
        )
        
        # Grade severity assessment
        severity_score = self._grade_severity_assessment(
            observation.severity, 
            expected.severity
        )
        
        # Weighted combination
        total_score = (
            services_score * 0.5 + 
            type_score * 0.3 + 
            severity_score * 0.2
        )
        
        return self._normalize_score(total_score)
    
    def _grade_service_identification(self, identified: List[str], expected: List[str]) -> float:
        """Grade service identification accuracy."""
        if not expected:
            return 1.0 if not identified else 0.0
        
        expected_set = set(expected)
        identified_set = set(identified)
        
        # True positives
        true_positives = len(expected_set.intersection(identified_set))
        
        # False positives
        false_positives = len(identified_set - expected_set)
        
        # False negatives
        false_negatives = len(expected_set - identified_set)
        
        # Precision and recall
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        
        # F1 score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return f1
    
    def _grade_incident_type_identification(self, identified: IncidentType, expected: IncidentType) -> float:
        """Grade incident type identification."""
        if identified is None:
            return 0.0
        return 1.0 if identified == expected else 0.0
    
    def _grade_severity_assessment(self, identified: AlertSeverity, expected: AlertSeverity) -> float:
        """Grade severity assessment with partial credit for close assessments."""
        if identified is None:
            return 0.0
        
        if identified == expected:
            return 1.0
        
        # Partial credit for severity levels that are close
        severity_order = [AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        
        try:
            identified_idx = severity_order.index(identified)
            expected_idx = severity_order.index(expected)
            
            # Distance-based scoring
            distance = abs(identified_idx - expected_idx)
            max_distance = len(severity_order) - 1
            
            return max(0.0, 1.0 - (distance / max_distance))
        except ValueError:
            return 0.0


class DiagnosisGrader(BaseGrader):
    """Grader for the diagnosis task."""
    
    def grade(self, observation: IncidentObservation, expected: DiagnosisResult) -> float:
        """
        Grade diagnosis performance based on root cause identification and evidence quality.
        
        Scoring:
        - Root cause identification: 60% of total score
        - Evidence quality: 40% of total score
        """
        # Grade root cause identification
        root_cause_score = self._grade_root_cause_identification(
            observation.root_cause, 
            expected.root_cause
        )
        
        # Grade evidence quality
        evidence_score = self._grade_evidence_quality(
            observation.evidence, 
            expected.evidence
        )
        
        # Weighted combination
        total_score = root_cause_score * 0.6 + evidence_score * 0.4
        
        return self._normalize_score(total_score)
    
    def _grade_root_cause_identification(self, identified: str, expected: str) -> float:
        """Grade root cause identification using semantic similarity."""
        if identified is None:
            return 0.0
        
        # Exact match
        if identified.lower().strip() == expected.lower().strip():
            return 1.0
        
        # Keyword-based similarity
        identified_words = set(identified.lower().split())
        expected_words = set(expected.lower().split())
        
        # Jaccard similarity
        intersection = len(identified_words.intersection(expected_words))
        union = len(identified_words.union(expected_words))
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # Boost for key technical terms
        key_terms = {"crash", "performance", "degradation", "dependency", "resource", "exhaustion", "deployment", "memory", "database", "service"}
        identified_key_terms = len(identified_words.intersection(key_terms))
        expected_key_terms = len(expected_words.intersection(key_terms))
        
        if expected_key_terms > 0:
            key_term_ratio = identified_key_terms / expected_key_terms
            jaccard_similarity = min(1.0, jaccard_similarity + (key_term_ratio * 0.2))
        
        return jaccard_similarity
    
    def _grade_evidence_quality(self, identified: List[str], expected: List[str]) -> float:
        """Grade evidence quality based on relevance and completeness."""
        if not identified:
            return 0.0
        
        # Grade based on evidence types
        evidence_types = {
            "logs": 0,
            "metrics": 0,
            "dependency": 0,
            "service": 0,
        }
        
        for evidence in identified:
            evidence_lower = evidence.lower()
            if "log" in evidence_lower:
                evidence_types["logs"] += 1
            if "metric" in evidence_lower:
                evidence_types["metrics"] += 1
            if "dependenc" in evidence_lower:
                evidence_types["dependency"] += 1
            if "service" in evidence_lower:
                evidence_types["service"] += 1
        
        # Score based on diversity of evidence
        diversity_score = sum(1 for count in evidence_types.values() if count > 0) / len(evidence_types)
        
        # Score based on quantity (with diminishing returns)
        quantity_score = min(1.0, len(identified) / 5.0)  # 5 pieces of evidence is good
        
        # Score based on relevance (contains key terms)
        relevance_score = 0.0
        for evidence in identified:
            if any(term in evidence.lower() for term in ["error", "warning", "high", "low", "failed", "timeout"]):
                relevance_score += 1
        relevance_score = min(1.0, relevance_score / len(identified)) if identified else 0.0
        
        # Combined evidence score
        evidence_score = (diversity_score * 0.4 + quantity_score * 0.3 + relevance_score * 0.3)
        
        return evidence_score


class ResolutionGrader(BaseGrader):
    """Grader for the resolution task."""
    
    def grade(self, observation: IncidentObservation, expected: ResolutionResult) -> float:
        """
        Grade resolution performance based on action correctness, recovery time, and system health.
        
        Scoring:
        - Correct action: 40% of total score
        - Recovery time: 40% of total score
        - System health: 20% of total score
        """
        # Grade action correctness
        action_score = self._grade_action_correctness(
            observation.applied_action, 
            expected.optimal_action
        )
        
        # Grade recovery time
        recovery_time_score = self._grade_recovery_time(
            observation.recovery_time_seconds, 
            expected.expected_recovery_time
        )
        
        # Grade system health
        health_score = self._grade_system_health(observation)
        
        # Weighted combination
        total_score = (
            action_score * 0.4 + 
            recovery_time_score * 0.4 + 
            health_score * 0.2
        )
        
        return self._normalize_score(total_score)
    
    def _grade_action_correctness(self, applied: str, optimal: str) -> float:
        """Grade action correctness."""
        if applied is None:
            return 0.0
        
        # Exact match
        if applied == optimal:
            return 1.0
        
        # Partial credit for reasonable actions
        reasonable_actions = {
            "restart_service": ["restart", "reboot", "reset"],
            "scale_service": ["scale", "resize", "replicate"],
            "rollback_deployment": ["rollback", "revert", "undo"],
        }
        
        for action_type, keywords in reasonable_actions.items():
            if optimal == action_type:
                for keyword in keywords:
                    if keyword in applied.lower():
                        return 0.7  # Partial credit for reasonable action
        
        # Small credit for any action vs no action
        return 0.2 if applied else 0.0
    
    def _grade_recovery_time(self, actual: int, expected: int) -> float:
        """Grade recovery time efficiency."""
        if actual is None:
            return 0.0
        
        # Perfect score if faster than expected
        if actual <= expected:
            return 1.0
        
        # Linear penalty for slower recovery
        max_acceptable_time = expected * 3  # 3x expected time is worst case
        
        if actual >= max_acceptable_time:
            return 0.0
        
        # Linear interpolation
        penalty = (actual - expected) / (max_acceptable_time - expected)
        return 1.0 - penalty
    
    def _grade_system_health(self, observation: IncidentObservation) -> float:
        """Grade system health after resolution."""
        if not observation.services:
            return 0.0
        
        healthy_count = 0
        total_count = len(observation.services)
        
        for service_info in observation.services.values():
            if service_info.status == ServiceStatus.HEALTHY:
                healthy_count += 1
            elif service_info.status == ServiceStatus.DEGRADED:
                healthy_count += 0.5  # Partial credit for degraded
        
        return healthy_count / total_count


class GraderManager:
    """Manages all graders and provides unified grading interface."""
    
    def __init__(self):
        self.graders = {
            "triage": TriageGrader(),
            "diagnosis": DiagnosisGrader(),
            "resolution": ResolutionGrader(),
        }
    
    def grade_task(self, task_name: str, observation: IncidentObservation, expected: Any) -> float:
        """
        Grade a specific task.
        
        Args:
            task_name: Name of the task ("triage", "diagnosis", "resolution")
            observation: Current observation from the environment
            expected: Expected result for this specific incident
            
        Returns:
            Score between 0.0 and 1.0
        """
        if task_name not in self.graders:
            raise ValueError(f"Unknown task: {task_name}")
        
        return self.graders[task_name].grade(observation, expected)
    
    def grade_all_tasks(self, observations: Dict[str, IncidentObservation], expected_results: Dict[str, Any]) -> Dict[str, float]:
        """
        Grade all tasks.
        
        Args:
            observations: Observations for each task
            expected_results: Expected results for each task
            
        Returns:
            Dictionary mapping task names to scores
        """
        scores = {}
        
        for task_name in self.graders.keys():
            if task_name in observations and task_name in expected_results:
                scores[task_name] = self.grade_task(task_name, observations[task_name], expected_results[task_name])
            else:
                scores[task_name] = 0.0
        
        return scores
    
    def get_overall_score(self, task_scores: Dict[str, float]) -> float:
        """
        Calculate overall score across all tasks.
        
        Args:
            task_scores: Individual task scores
            
        Returns:
            Overall score between 0.0 and 1.0
        """
        if not task_scores:
            return 0.0
        
        # Weight tasks by difficulty
        weights = {
            "triage": 0.2,      # Easy
            "diagnosis": 0.3,    # Medium  
            "resolution": 0.5,    # Hard
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for task_name, score in task_scores.items():
            weight = weights.get(task_name, 0.0)
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight == 0.0:
            return 0.0
        
        return weighted_sum / total_weight


# Global grader manager instance
grader_manager = GraderManager()
