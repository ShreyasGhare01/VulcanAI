"""Permissions matrix for filesystem skill."""


def get_permissions() -> list[str]:
    """Gets list of declared permissions required by filesystem skill."""
    return ["filesystem.read", "filesystem.write"]
