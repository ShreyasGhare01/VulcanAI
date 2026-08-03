"""Assembles complete prompts sequentially from distinct, testable sections using PromptDocument."""

from pydantic import BaseModel, Field

from vulcan.cognition.context import ContextPiece
from vulcan.cognition.models import Message, MessageRole


class PromptSection(BaseModel):
    """A distinct component of a generated system prompt."""

    name: str
    content: str


class PromptDocument(BaseModel):
    """A strongly typed structured prompt model ready for provider serialization."""

    sections: list[PromptSection] = Field(default_factory=list)

    def add_section(self, name: str, content: str) -> None:
        """Appends a new formatted section."""
        self.sections.append(PromptSection(name=name, content=content))

    def serialize(self) -> str:
        """Converts structured sections into flat string representations."""
        parts = []
        for sec in self.sections:
            parts.append(f"=== {sec.name.upper()} ===\n{sec.content}\n")
        return "\n".join(parts)


class PromptBuilder:
    """Deterministic prompt assembler ensuring section replaceability and structured layouts."""

    def build_prompt_document(
        self,
        context_pieces: list[ContextPiece],
        conversation_history: list[Message],
        current_user_input: str,
    ) -> PromptDocument:
        """Sequential assembly of the structured PromptDocument."""
        _ = conversation_history
        doc = PromptDocument()

        # 1. Identity section (extracted from Identity Context)
        identity_piece = next((p for p in context_pieces if p.type == "identity"), None)
        if identity_piece:
            identity_data = identity_piece.content
            doc.add_section(
                "Identity",
                f"Name: {identity_data.name}\n"
                f"Philosophy/Constitution:\n{identity_data.constitution_summary}",
            )
        else:
            doc.add_section("Identity", "Name: Vulcan AI OS")

        # 2. Operating Rules (extracted from Identity Context)
        if identity_piece:
            rules_str = "\n".join(f"- {rule}" for rule in identity_piece.content.operating_rules)
            doc.add_section("Operating Rules", rules_str)

        # 3. Current Session Metadata
        session_piece = next((p for p in context_pieces if p.type == "session_metadata"), None)
        if session_piece:
            meta = session_piece.content
            doc.add_section(
                "Session Metadata",
                f"Session ID: {meta.get('session_id')}\n"
                f"Active Model: {meta.get('active_model')}\n"
                f"Total Tokens Dispatched: {meta.get('total_tokens')}",
            )

        # 4. Context Providers (Other assembled pieces)
        other_pieces: list[str] = []
        for piece in context_pieces:
            if piece.type in ("identity", "session_metadata"):
                continue
            other_pieces.append(f"[{piece.source.upper()}] ({piece.type}): {piece.content}")
        if other_pieces:
            doc.add_section("System Context", "\n".join(other_pieces))

        # 5. Active Task
        task_piece = next((p for p in context_pieces if p.type == "task"), None)
        if task_piece:
            doc.add_section("Active Task", str(task_piece.content))

        # 6. Available Capabilities
        cap_piece = next((p for p in context_pieces if p.type == "capabilities"), None)
        if cap_piece:
            cap_str = ""
            for cap_name, providers in cap_piece.content.items():
                cap_str += f"- {cap_name} (provided by: {', '.join(providers)})\n"
            doc.add_section("Available Capabilities", cap_str)

        # 7. User Input / Prompt Goal
        doc.add_section("User Input", f"The user says: {current_user_input}")

        return doc

    def build_prompt_sequence(
        self,
        context_pieces: list[ContextPiece],
        conversation_history: list[Message],
        current_user_input: str,
    ) -> str:
        """Legacy helper to support flat string generation, delegating to PromptDocument."""
        doc = self.build_prompt_document(context_pieces, conversation_history, current_user_input)
        return doc.serialize()

    def format_messages_for_provider(
        self,
        system_prompt: str,
        conversation_history: list[Message],
        current_user_input: str,
    ) -> list[dict[str, str]]:
        """Maps conversation objects to raw message dictionaries for direct Provider consumption."""
        _ = system_prompt
        messages: list[dict[str, str]] = []
        for msg in conversation_history:
            messages.append({"role": msg.role.value, "content": msg.content})

        # Append latest turn user input
        messages.append({"role": MessageRole.USER.value, "content": current_user_input})
        return messages
