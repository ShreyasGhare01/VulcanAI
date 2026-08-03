"""Generic modular pipeline stage contracts for the Cognitive Core."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class PipelineStage[InputT, OutputT](ABC):
    """Represents a discrete, validation-supported step in an execution pipeline."""

    @abstractmethod
    def validate(self, data: InputT) -> bool:
        """Validates that input data conforms to expectations."""
        pass

    @abstractmethod
    def execute(self, data: InputT) -> OutputT:
        """Performs the main logic of this pipeline stage."""
        pass

    def post_process(self, output: OutputT) -> OutputT:
        """Provides optional post-processing or mutation logic after execution."""
        return output


class Validator[InputT](ABC):
    """Abstraction for validation checks on operational inputs."""

    @abstractmethod
    def validate(self, data: InputT) -> bool:
        """Verifies rules on input packages."""
        pass


class Transformer[InputT, OutputT](ABC):
    """Abstraction for mapping input formats into customized target formats."""

    @abstractmethod
    def transform(self, data: InputT) -> OutputT:
        """Maps or formats data."""
        pass


class Pipeline[InputT, OutputT]:
    """Composes multiple sequential PipelineStage components."""

    def __init__(self) -> None:
        self._stages: list[PipelineStage[Any, Any]] = []

    def add_stage(self, stage: PipelineStage[Any, Any]) -> None:
        """Appends a processing step to the execution pipeline."""
        self._stages.append(stage)

    def process(self, data: InputT) -> OutputT:
        """Sequentially triggers all validation and execution blocks."""
        current: Any = data
        for stage in self._stages:
            if not stage.validate(current):
                raise ValueError(f"Pipeline stage {stage.__class__.__name__} validation failed.")
            result = stage.execute(current)
            current = stage.post_process(result)
        return current  # type: ignore[no-any-return]
