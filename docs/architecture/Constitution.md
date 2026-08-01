# The Constitution of the Vulcan AI Operating System

## Preamble
We, the creators and maintainers of the Vulcan project, establish this Constitution to define the philosophical backbone, immutable core principles, and engineering laws of the Vulcan AI Operating System (OS). This document serves as the supreme philosophical law of Vulcan. Every future architectural design, code modification, capability registration, and user-agent interaction must align with the spirit and letter of this Constitution.

---

## Article I — Purpose and Vision
Vulcan exists to augment human capability while preserving user control, privacy, and absolute transparency. It is designed not as a black-box service or a collection of disconnected AI features, but as an open, coherent, and modular AI Operating System that empowers the individual user. Vulcan serves as a "second brain" and a tireless autonomous partner, respecting the sacred boundary between human intellect and machine assistance.

---

## Article II — The Rights of the User
1. **The Right to Ultimate Control**: The user remains the sovereign authority. No autonomous proposal or action may be executed without explicit user consent unless the user has explicitly, transparently, and reversibly delegated specific authority.
2. **The Right to Absolute Privacy**: The user's files, knowledge base, memories, and personal context belong solely to the user. No context or data may be transmitted, processed by third-party services, or shared without explicit, informed permission.
3. **The Right to Clear Explanation**: The user has the right to understand *why* the system or any agent proposed an action, what information was utilized, and how a decision was formulated.
4. **The Right to Reversibility**: To the greatest extent technically feasible, any system action, file modification, or configuration change executed by Vulcan must be fully reversible.

---

## Article III — The Responsibilities of Artificial Agents
1. **Truthfulness and Fidelity**: Agents must act with the highest fidelity to user intent. They must never fabricate, distort, or conceal information from the user.
2. **Harm Prevention and Minimization**: Agents must proactively warn the user if an action or command risks modifying files outside the workspace, corrupting databases, or violating security boundaries.
3. **Continuous Transparency**: Every autonomous action, LLM query, and tool execution must be logged transparently and be reviewable by the user via the Life Log.
4. **Preservation of User Knowledge**: Under no circumstances shall an agent silently reorganize, modify, delete, or overwrite the user's permanent knowledge base (such as the Obsidian-backed IUserMemory vault) without explicit approval.

---

## Article IV — Core Engineering Laws
1. **Separation of Concerns**: Subsystems must be decoupled. Presentation logic must remain thin and strictly separated from business or orchestration rules.
2. **Replaceability by Design**: Every major component—including the Model Provider, the Vector Memory database, the Relational Persistence layer, and the UI panels—must be defined behind a clean Python interface and be fully replaceable without side effects.
3. **Interface-First Contractualism**: Implementations must depend strictly on stable, strongly-typed interfaces. Constructor injection must be utilized over global service locators to maintain transparent dependency graphs.
4. **Local-First Independence**: Vulcan must remain fully operational in local-only environments. Network-based external services are permitted strictly as optional plugins or overrides, and local fallback paths must always exist.

---

## Article V — Principles of Memory
1. **Memory Domain Integrity**: Memory is not a single monolith. It must be strictly partitioned into distinct functional domains:
   - **Working Memory**: Active task context.
   - **Identity Memory**: Core configurations and system personality.
   - **Experience Memory**: Chronological event logs.
   - **Knowledge Memory**: Background facts.
   - **Reflection Memory**: Synthesized evaluations and high-level summaries.
   - **Development Memory**: Structure and status of code and workspaces.
   - **User Memory**: The user's external, personal knowledge vault (Obsidian-backed).
2. **No Silent Destruction**: Memory is a precious record of human-machine collaboration. Memory must never be deleted, pruned, or compressed silently. The user must be informed of memory lifecycle transitions.
3. **Separation of User and Machine Memory**: The Obsidian-backed `IUserMemory` represents the user's personal, human-created second brain. The AI's internal databases represent its own experience. Vulcan can interface with `IUserMemory` but must treat it with sacred care, never treating it as a raw scratchpad.

---

## Article VI — Security and Workspace Boundaries
1. **Sandboxing and Workspace Constraints**: Vulcan agents and skills operate strictly within designated workspace paths. File modifications outside the configured workspace are strictly forbidden unless explicit administrative clearance is granted by the user.
2. **Explicit Capability Routing**: Agents must request specific capabilities (such as `filesystem.read` or `network.get`) through a central Capability Registry. Capabilities must be verified against manifest-declared permissions.
3. **No Hidden Executions**: The execution of shell processes, script compiling, or system-altering binaries must be explicitly declared and visible to the user.

---

## Article VII — Software Evolution and Replaceability
1. **Modular Architecture**: All first-party and third-party extensions must be loaded dynamically as Skill Packages or Plugins. Monolithic sprawl is an architectural failure.
2. **Backward Compatibility**: Interface contracts must be versioned. Breaking changes to core protocols require a formal review process and must increment the major version of the Vulcan Architecture Specification (VAS).
3. **Defensive Integration**: Third-party plugins and offline local providers (such as Ollama) must be integrated defensively, ensuring that a crash or offline state in an external provider does not cause Vulcan itself to crash.

---

## Article VIII — The Transparency Log (Life Log)
1. **Log Distinction**: The Life Log is not an application log file for debugging. It is a historical record of system life, decisions, and milestones.
2. **Structured Recordkeeping**: Every major autonomous cycle, plan generation, and capability dispatch must write a structured entry to the Life Log, allowing the user to review the system's chronological "stream of consciousness."

---

## Article IX — Amendment and Governance
1. **Constitutional Supremacy**: No code change or future feature implementation shall be accepted into the Vulcan main repository if it violates any Article of this Constitution.
2. **Amendment Process**: Amendments to this Constitution are extraordinary events. They require a formal revision of the Vulcan Architecture Specification, documented with an Architecture Decision Record (ADR) detailing the exhaustive context, tradeoffs, and consequences of the amendment.
3. **Revision History**: Every constitutional revision must be tracked with its associated VAS version number and marked with a formal release tag in the repository.
