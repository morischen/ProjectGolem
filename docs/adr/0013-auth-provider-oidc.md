# 0013. Auth provider: API keys now, OIDC for humans later

- **Status:** Proposed
- **Date:** 2026-06-21
- **Deciders:** Project lead
- **Related:** Gateway auth (`web/api-gateway/src/auth.ts`), admin portal A4 (managed `KeyStore`); CLAUDE.md §3 (INV-OVERRIDE attribution); ARCHITECTURE.md §8; blueprint §22

## Context
The gateway enforces API-key scopes (`read`/`write`/`admin`), and A4 added a managed
`KeyStore` (hashed keys, admin CRUD, audited). That is sufficient for service-to-service
calls and a small operator set, but it is not a real human-identity system: no SSO, no
MFA, no per-person identity for reviewers (INV-OVERRIDE wants *who* overrode a verdict,
not just "an admin key"), and key rotation is manual. We need to decide the human-auth
direction without rebuilding the working API-key layer.

## Decision
**Keep API keys for service-to-service auth; adopt OIDC for human/operator auth** when
the human surface (admin portal, reviewers, appeals triage) graduates beyond a handful
of keys. The gateway remains the single enforcement point: it will validate OIDC ID/
access tokens (standard provider — e.g. Auth0/Keycloak/Cognito-class, chosen at
implementation) and map verified claims to the same internal scopes, so downstream
services and the scope model are unchanged. Reviewer actions will carry the OIDC
subject as the audited actor (sharpening INV-OVERRIDE attribution). The current
`KeyStore` is the bridge: it stays for machine clients and as the dev/default path, and
its hashed-secret + audit pattern foreshadows the token-introspection flow. MFA is a
provider configuration concern, not bespoke code.

## Consequences
- Real per-person identity and SSO/MFA for operators without touching the engines or
  the scope model — the gateway absorbs the change.
- Audit/override attribution becomes a verified human subject, not an opaque key.
- Cost: a provider dependency, token validation/refresh, and session handling in the
  gateway/admin app; deferred until the operator set justifies it.
- Distributed rate-limiting (blueprint §22) is a separate, related backlog item — the
  current in-memory limiter is per-instance.

## Alternatives considered
- **API keys only, forever** — no SSO/MFA, weak human attribution, manual rotation;
  doesn't scale to a real review team. Rejected as the end state.
- **Build a custom user/password + session system** — reinvents auth, owns password
  storage and MFA; higher risk than delegating to an OIDC provider. Rejected.
- **OIDC for everything (incl. service calls)** — heavyweight for machine-to-machine;
  API keys are simpler there. Kept both, split by caller type.
