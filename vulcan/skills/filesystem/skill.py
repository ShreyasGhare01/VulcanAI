"""Filesystem interaction skill and manifest blueprint sample."""

from typing import Any

from vulcan.agents.framework import ISkill, ITool


class ReadFileTool(ITool):
    @property
    def name(self) -> str:
        return "filesystem.read"

    @property
    def description(self) -> str:
        return "Reads files securely off the host's directory structure."

    def execute(self, arguments: dict[str, Any]) -> Any:
        path = arguments.get("filepath", "")
        if not path:
            return "Error: Missing 'filepath' parameter."
        try:
            with open(path) as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {path}: {e}"


class FilesystemSkill(ISkill):
    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def tools(self) -> list[ITool]:
        return [ReadFileTool()]
