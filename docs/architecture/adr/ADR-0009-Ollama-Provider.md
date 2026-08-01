# ADR-0009: Ollama as Initial Local Model Provider

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
To achieve local-first, privacy-respecting AI capabilities, we need an inference provider to run LLMs on the user's workstation. However, hardcoding direct calls to a specific model provider creates tight coupling and prevents future alternative provider options.

### Decision
We introduce a provider-agnostic interface `IInferenceProvider` in `vulcan/services/inference.py` and select Ollama as our initial local model implementation (`OllamaProvider`).
*   The system configures and queries Ollama locally using `httpx` (never `urllib`).
*   The provider must fail gracefully and report an offline status instead of crashing the application if Ollama is not active or installed on the system.

### Alternatives Considered
*   **OpenAI API / Cloud Models**: Rejected as the primary default due to privacy, cost, and offline limitations, though they may be added as plugins later.
*   **Direct llama.cpp / Transformers integration**: Extremely complex to build, compile, and distribute. Ollama offers a clean, standardized local HTTP API.

### Consequences
*   **Easier**: Clean local model serving, automatic quantization handling, and quick model discovery.
*   **Harder**: Requires users to install Ollama separately on their machine, which we address by failing gracefully and providing configuration tips.

### Tradeoffs
We trade off immediate out-of-the-box model executions (which cloud APIs offer) for complete local privacy, low latency, and zero runtime model costs.

### Future Considerations
We can seamlessly add LM Studio, llama.cpp, or vLLM backends by simply implementing `IInferenceProvider` without modifying any agent or planner code.

### Related ADRs
*   ADR-0002: Layered Architecture

### References
*   `vulcan/services/inference.py`
