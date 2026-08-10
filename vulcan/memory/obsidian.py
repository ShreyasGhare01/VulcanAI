"""Obsidian Vault helper to initialize and write structured Markdown files."""

import os
import re
import time
from typing import Any, cast


class ObsidianVault:
    """Helper class to manage and manipulate the human-readable Obsidian Vault."""

    def __init__(self, vault_path: str):
        self.vault_path = os.path.abspath(os.path.expanduser(vault_path))

    def initialize_vault(self) -> None:
        """Initializes the structure folders for standard Obsidian storage."""
        folders = [
            "Users",
            "System",
            "LifeLog",
            "Reflections",
            "Templates",
            "Attachments",
            ".history",
        ]
        for f in folders:
            os.makedirs(os.path.join(self.vault_path, f), exist_ok=True)

    def write_markdown(
        self, relative_path: str, frontmatter: dict[str, Any], content_body: str
    ) -> str:
        """Writes a Markdown file with YAML frontmatter, managing versioned backup under .history/."""
        full_path = os.path.join(self.vault_path, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 1. Manage Version and backups
        if os.path.exists(full_path):
            current_version = frontmatter.get("version", 1)
            # Create a history copy
            history_dir = os.path.join(self.vault_path, ".history")
            os.makedirs(history_dir, exist_ok=True)

            base_name = os.path.basename(relative_path).replace(".md", "")
            history_filename = f"{base_name}_v{current_version}.md"
            history_full_path = os.path.join(history_dir, history_filename)

            # Move active file to history path
            try:
                os.rename(full_path, history_full_path)
            except Exception:
                # Fallback to copy if rename across mount fails
                with (
                    open(full_path, encoding="utf-8") as src,
                    open(history_full_path, "w", encoding="utf-8") as dest,
                ):
                    dest.write(src.read())

            # Update the version in frontmatter
            frontmatter["version"] = current_version + 1

        # 2. Build YAML Frontmatter block
        yaml_lines = ["---"]
        for k, v in frontmatter.items():
            if isinstance(v, list):
                yaml_lines.append(f"{k}:")
                for item in v:
                    if isinstance(item, dict):
                        # format dict items cleanly (e.g. relations)
                        dict_str = ", ".join(f"{dk}: {dv}" for dk, dv in item.items())
                        yaml_lines.append(f"  - {{ {dict_str} }}")
                    else:
                        yaml_lines.append(f"  - {item}")
            elif isinstance(v, dict):
                yaml_lines.append(f"{k}:")
                for sk, sv in v.items():
                    yaml_lines.append(f"  {sk}: {sv}")
            else:
                yaml_lines.append(f"{k}: {v}")
        yaml_lines.append("---")
        yaml_block = "\n".join(yaml_lines)

        full_content = f"{yaml_block}\n\n{content_body}"

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        return full_path

    def delete_markdown(self, relative_path: str, archive_only: bool = False) -> None:
        """Deletes or archives the Markdown file in the vault."""
        full_path = os.path.join(self.vault_path, relative_path)
        if os.path.exists(full_path):
            if archive_only:
                # Copy to .history
                history_dir = os.path.join(self.vault_path, ".history")
                os.makedirs(history_dir, exist_ok=True)
                base_name = os.path.basename(relative_path).replace(".md", "")
                history_filename = f"{base_name}_archived_{int(time.time())}.md"
                history_full_path = os.path.join(history_dir, history_filename)
                try:
                    os.rename(full_path, history_full_path)
                except Exception:
                    with open(full_path, "r", encoding="utf-8") as src, open(
                        history_full_path, "w", encoding="utf-8"
                    ) as dest:
                        dest.write(src.read())
                    os.remove(full_path)
            else:
                os.remove(full_path)

    def read_markdown(self, relative_path: str) -> tuple[dict[str, Any], str]:
        """Reads a Markdown file and parses its YAML frontmatter and body."""
        full_path = os.path.join(self.vault_path, relative_path)
        if not os.path.exists(full_path):
            return {}, ""

        with open(full_path, encoding="utf-8") as f:
            content = f.read()

        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if not match:
            return {}, content

        frontmatter_str = match.group(1)
        body = match.group(2)

        frontmatter: dict[str, Any] = {}
        # Simple parser for frontmatter to avoid external pyyaml dependency if strict
        # (Though we can use pyyaml since it's installed via dependencies)
        try:
            import yaml

            frontmatter = cast(dict[str, Any], yaml.safe_load(frontmatter_str) or {})
        except Exception:
            # simple key-value parser fallback
            for line in frontmatter_str.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip()

        return frontmatter, body
