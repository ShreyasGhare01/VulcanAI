"""Agent and AI operation framework abstract base classes as defined in Phase 0 design rules."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class Task(BaseModel):
    """Data model representing a discrete unit of execution assigned to agents/planners."""

    id: str
    name: str
    description: str
    status: str = "pending"
    context: dict[str, Any] = {}
    dependencies: list[str] = []


class ITool(ABC):
    """Abstract interface defining modular, callable tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Globally unique tool name identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Verbose description for the planner/agent showing how to use the tool."""
        pass

    @abstractmethod
    def execute(self, arguments: dict[str, Any]) -> Any:
        """Synchronously execute the tool logic."""
        pass


class ISkill(ABC):
    """Abstract interface for high-level grouped capabilities/tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def tools(self) -> list[ITool]:
        """Provides internal tools encapsulated in this skill package."""
        pass


class IPlanner(ABC):
    """Abstract interface defining the scheduler/planning strategies."""

    @abstractmethod
    def create_plan(self, objective: str, context: dict[str, Any]) -> list[Task]:
        """Generates a structured plan sequence to achieve a given user objective."""
        pass


class IAgent(ABC):
    """Abstract interface defining the fundamental Agent characteristics."""

    @property
    @abstractmethod
    def agent_id(self) -> str:
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        pass

    @abstractmethod
    def assign_task(self, task: Task) -> None:
        """Assigns a structured task to the agent."""
        pass

    @abstractmethod
    def execute_next(self) -> Any:
        """Executes the next step of the assigned task sequence."""
        pass
