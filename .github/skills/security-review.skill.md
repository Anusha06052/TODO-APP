name: security-review
description: >
  Auto-triggered on security review prompts. Performs OWASP Top 10 mapped
  security audit across backend (FastAPI/SQLAlchemy) and frontend (React/TypeScript).
  Reports findings as PASS / WARN / FAIL with remediation steps.

trigger:
  - "security review"
  - "security check"
  - "check vulnerabilities"
  - "audit this code"
  - "security audit"
  - "owasp review"
  - "review for vulnerabilities"

instructions: |
  Perform a structured security review of the codebase.
  Map all findings to OWASP Top 10 categories where applicable.

  ## Backend Security (api/)

  ### A01 — Broken Access Control
  - Are endpoints properly scoped? (N/A for single-user, but verify no admin-only routes exposed)
  - Do repository methods filter by owner/scope where relevant?

  ### A02 — Cryptographic Failures
  - Are secrets (DB passwords, API keys) stored in environment variables — never in code?
  - Is the `.env` file listed in `.gitignore`?
  - Are connection strings free from hardcoded credentials?

  ### A03 — Injection
  - Are ALL database queries executed via SQLAlchemy ORM (no f-string SQL, no raw string concatenation)?
  - Are there any `text()` calls with unparameterized input?
  - Is all user input validated via Pydantic schemas before reaching the repository?

  ### A05 — Security Misconfiguration
  - Is CORS restricted to expected origins only (not `allow_origins=["*"]`)?
  - Are debug modes / stack traces disabled for production error responses?
  - Are error responses sanitized — no internal exception details exposed to client?

  ### A06 — Vulnerable & Outdated Components
  - Are there obvious outdated packages in requirements.txt?
  - Suggest running: `pip audit` or `safety check` for CVE scanning.

  ### A07 — Identification & Authentication Failures
  - (Single-user app: note explicitly that this is out of scope)
  - Verify no accidental auth-bypass in any route decorator.

  ### Input Validation
  - Are all request bodies validated via Pydantic schemas?
  - Are all path params and query params typed (not raw `str`)?
  - Are Field() constraints (min_length, max_length, ge, le) present on critical fields?

  ### Error Handling
  - Do error responses avoid leaking stack traces?
  - Are 500 errors caught and returned as generic messages?
  - Are specific exception types caught (no bare `except:`)?

  ---

  ## Frontend Security (web/)

  ### XSS
  - Are there any `dangerouslySetInnerHTML` usages? Flag all — justify or remove.
  - Is user input sanitized before rendering?
  - Are third-party HTML strings avoided?

  ### Sensitive Data
  - Are API keys or secrets absent from all frontend source files?
  - Are `.env` files listed in `.gitignore`?
  - Is `VITE_*` env vars checked — none should be secret (they are public in the bundle)?

  ### CSRF
  - Are state-changing operations using correct HTTP methods (POST/PUT/DELETE not GET)?
  - Are mutation requests not triggerable via GET links?

  ### Dependencies
  - Suggest running: `npm audit` for known CVEs.
  - Flag any packages with obvious security concerns.

  ---

  ## Output Format

  For each category, output one of:
  - ✅ PASS — no issues found
  - ⚠️ WARN — potential concern (file:line) — recommendation
  - ❌ FAIL — vulnerability found (file:line) — severity — remediation steps

  ### Summary table
  | Category | Area | Status | Finding | Fix |
  |----------|------|--------|---------|-----|

  ### Severity model
  - Critical: immediate exploitation potential or sensitive data exposure
  - High: serious weakness with realistic attack path
  - Medium: meaningful risk requiring remediation before production
  - Low: best-practice or hardening gap

  ### After findings
  List:
  1. Quick wins — can be fixed immediately (< 30 min)
  2. Short-term — requires design change (sprint-level)
  3. Explicit assumptions and unknowns
