"""
Workflow management for Pixora AI agents.

This module handles workflow state, progress tracking, and step management.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from ..utils.logger import get_logger

logger = get_logger(__name__)

class WorkflowStatus(Enum):
    """Workflow status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    """Step status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    id: str
    name: str
    description: str
    status: StepStatus = StepStatus.PENDING
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowState:
    """Represents the current state of a workflow."""
    workflow_id: str
    user_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    steps: List[WorkflowStep] = field(default_factory=list)
    progress: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class WorkflowManager:
    """
    Manages workflow execution and state tracking.
    
    This class handles workflow lifecycle, step progression, and state management.
    """
    
    def __init__(self):
        """Initialize the workflow manager."""
        self.logger = logger
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.workflow_history: Dict[str, WorkflowState] = {}
    
    def create_workflow(self, user_id: str, steps: List[Dict[str, Any]]) -> str:
        """
        Create a new workflow for a user.
        
        Args:
            user_id: The user's ID
            steps: List of step definitions
            
        Returns:
            The workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        # Create workflow steps
        workflow_steps = []
        for step_def in steps:
            step = WorkflowStep(
                id=str(uuid.uuid4()),
                name=step_def.get("name", "Unknown Step"),
                description=step_def.get("description", ""),
                metadata=step_def.get("metadata", {})
            )
            workflow_steps.append(step)
        
        # Create workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            user_id=user_id,
            steps=workflow_steps
        )
        
        self.active_workflows[workflow_id] = workflow_state
        self.logger.info(f"Created workflow {workflow_id} for user {user_id}")
        
        return workflow_id
    
    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get the current state of a workflow."""
        return self.active_workflows.get(workflow_id)
    
    def update_step_status(self, workflow_id: str, step_id: str, 
                          status: StepStatus, output_data: Optional[Any] = None,
                          error: Optional[str] = None) -> bool:
        """
        Update the status of a workflow step.
        
        Args:
            workflow_id: The workflow ID
            step_id: The step ID
            status: The new status
            output_data: Output data from the step
            error: Error message if the step failed
            
        Returns:
            True if the update was successful, False otherwise
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            self.logger.warning(f"Workflow {workflow_id} not found")
            return False
        
        # Find the step
        step = None
        for s in workflow.steps:
            if s.id == step_id:
                step = s
                break
        
        if not step:
            self.logger.warning(f"Step {step_id} not found in workflow {workflow_id}")
            return False
        
        # Update step status
        step.status = status
        if status == StepStatus.RUNNING:
            step.start_time = datetime.now()
        elif status in [StepStatus.COMPLETED, StepStatus.FAILED]:
            step.end_time = datetime.now()
            step.output_data = output_data
            step.error = error
        
        # Update workflow progress
        self._update_workflow_progress(workflow)
        
        # Update workflow status
        self._update_workflow_status(workflow)
        
        self.logger.info(f"Updated step {step_id} in workflow {workflow_id} to {status}")
        return True
    
    def _update_workflow_progress(self, workflow: WorkflowState):
        """Update the overall progress of a workflow."""
        if not workflow.steps:
            workflow.progress = 0.0
            return
        
        completed_steps = sum(1 for step in workflow.steps 
                            if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED])
        total_steps = len(workflow.steps)
        workflow.progress = (completed_steps / total_steps) * 100.0
    
    def _update_workflow_status(self, workflow: WorkflowState):
        """Update the overall status of a workflow."""
        if workflow.status == WorkflowStatus.CANCELLED:
            return
        
        # Check if all steps are completed
        all_completed = all(step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] 
                           for step in workflow.steps)
        
        # Check if any steps failed
        any_failed = any(step.status == StepStatus.FAILED for step in workflow.steps)
        
        if any_failed:
            workflow.status = WorkflowStatus.FAILED
            workflow.end_time = datetime.now()
        elif all_completed:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.end_time = datetime.now()
        elif workflow.status == WorkflowStatus.PENDING:
            workflow.status = WorkflowStatus.RUNNING
    
    def complete_workflow(self, workflow_id: str):
        """Mark a workflow as completed and move it to history."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return
        
        workflow.end_time = datetime.now()
        workflow.status = WorkflowStatus.COMPLETED
        
        # Move to history
        self.workflow_history[workflow_id] = workflow
        del self.active_workflows[workflow_id]
        
        self.logger.info(f"Completed workflow {workflow_id}")
    
    def fail_workflow(self, workflow_id: str, error: str):
        """Mark a workflow as failed and move it to history."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return
        
        workflow.end_time = datetime.now()
        workflow.status = WorkflowStatus.FAILED
        workflow.metadata["error"] = error
        
        # Move to history
        self.workflow_history[workflow_id] = workflow
        del self.active_workflows[workflow_id]
        
        self.logger.info(f"Failed workflow {workflow_id}: {error}")
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return False
        
        if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            return False
        
        workflow.status = WorkflowStatus.CANCELLED
        workflow.end_time = datetime.now()
        
        # Cancel any running steps
        for step in workflow.steps:
            if step.status == StepStatus.RUNNING:
                step.status = StepStatus.FAILED
                step.error = "Workflow cancelled"
                step.end_time = datetime.now()
        
        self.logger.info(f"Cancelled workflow {workflow_id}")
        return True
    
    def get_user_workflows(self, user_id: str) -> List[WorkflowState]:
        """Get all workflows for a specific user."""
        user_workflows = []
        
        # Check active workflows
        for workflow in self.active_workflows.values():
            if workflow.user_id == user_id:
                user_workflows.append(workflow)
        
        # Check history
        for workflow in self.workflow_history.values():
            if workflow.user_id == user_id:
                user_workflows.append(workflow)
        
        return user_workflows
    
    def cleanup_old_workflows(self, max_age_hours: int = 24):
        """Clean up old completed workflows from history."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        workflows_to_remove = []
        for workflow_id, workflow in self.workflow_history.items():
            if workflow.end_time and workflow.end_time.timestamp() < cutoff_time:
                workflows_to_remove.append(workflow_id)
        
        for workflow_id in workflows_to_remove:
            del self.workflow_history[workflow_id]
        
        if workflows_to_remove:
            self.logger.info(f"Cleaned up {len(workflows_to_remove)} old workflows")
