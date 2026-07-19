# Security model

API keys are service credentials, sent through `X-API-Key` over TLS. Only SHA-256 digests are
stored and comparison is constant-time. Production must provision clients through controlled
administration; environment bootstrap is intended for development initialization only and has no
committed value. Tenant identity always comes from the credential, never a request body.

Secrets must be injected at runtime. Container files are read-only, processes are non-root, and
health responses expose no configuration. Rate limiting and key rotation endpoints are deferred
until the administrative API is designed and threat-modeled.

