# Security policy and boundaries

Do not include credentials or raw store data in public issues. Agree a private reporting channel with the repository owner. This fork has no independently verified response-time SLA. The historical upstream contact is crushxue@outlook.com; it is not a support commitment by this fork.

The application is self-hosted. An administrator has access to powerful local tools, so administrator access must be treated as machine access. Session authentication, role checks, Origin checks and scoped MCP tokens address different boundaries and are not substitutes for one another.

Keep a stable `IVYEA_OPS_SECRET`, protect environment/data files, bind to loopback behind an authenticated HTTPS proxy when remote access is required, and review any LAN exposure. Windows eMAG credentials are stored separately as a Generic Credential. The browser does not receive the password through the eMAG APIs.

Third-party skills, MCP servers and provider tools execute with their configured permissions. They have not all been audited by this fork. Do not assume that a catalog entry is safe because it is listed.

Some configured secrets are encrypted by the application's secrets layer. This does not protect against an attacker who controls the host or an authorized administrator. Backups, logs and custom integrations still require review. Inspect dependency-audit results in the maintenance report; compatibility checks are not security scans.
