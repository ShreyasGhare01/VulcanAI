"""Configuration settings for filesystem skill."""

from pydantic import BaseModel


class FilesystemConfig(BaseModel):
    """Filesystem config parameters."""

    sandbox_root: str = "./vulcan/workspace"
    allow_absolute_paths: bool = False
