"""Generic modular pipeline stage contracts for the Cognitive Core."""

from abc import ABC, abstractmethod
from typing import TypeVar

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
