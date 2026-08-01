# ADR-0006: SQLite Data Layer

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
We need a robust relational database to store configuration data, conversation logs, and experience timelines locally. Heavy Object-Relational Mappers (ORMs) like SQLAlchemy can introduce significant configuration sprawl, complex migrations, performance overhead, and dependency bloat.

### Decision
We choose the standard library `sqlite3` module directly for all relational data persistence.
*   We forbid SQLAlchemy or any other external heavyweight ORMs.
*   We implement a lightweight, custom repository and migration layer directly inside the codebase to manage SQL queries and database updates cleanly.

### Alternatives Considered
*   **SQLAlchemy / SQLModel**: Highly robust but adds substantial library dependencies, is prone to tricky performance issues (lazy loading overhead), and is unnecessarily complex for Vulcan's local database requirements.
*   **PostgreSQL / MySQL**: Rejected because they require a separate running system service, violating our "local-first, easy setup" core law.

### Consequences
*   **Easier**: Zero external package dependencies, instant database boot, extremely low file footprint, and explicit control over SQL execution.
*   **Harder**: We must write raw SQL queries and coordinate migrations manually using lightweight scripts.

### Tradeoffs
We trade off the automatic table generation and ORM convenience in exchange for absolute, low-overhead database control, zero setup overhead for the user, and high reliability.

### Future Considerations
If Vulcan needs to scale to multi-user cloud servers in the distant future, the SQL queries can be refactored behind repository interfaces (`IRepository`), maintaining clean replaceability.

### Related ADRs
*   ADR-0002: Layered Architecture

### References
*   `vulcan/config/__init__.py` (SQLiteConfig)
