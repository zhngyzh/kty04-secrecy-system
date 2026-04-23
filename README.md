# KTY04 Secrecy System

This project provides a management system for classified document workflows based on the KTY04 group signature scheme. It supports anonymous signing, signer tracing (open), claim generation, claim verification, and full audit trails.

## Documentation

- Project usage, installation, permissions, testing, and API map: [README.md](README.md)

## Features

- Group creation and key initialization (`grpkey`, `mgrkey`, `gml`)
- Member onboarding via JOIN protocol and member key distribution
- Classified document creation, signing, verification, and archiving
- Anonymous group signatures with optional signer opening by administrators
- Claim generation and claim verification flow
- Audit logging and dashboard statistics

## Role Model

| Capability | Admin | User |
|---|---|---|
| Create groups | Yes | No |
| Add members | Yes | No |
| Open/trace signatures | Yes | No |
| View audit logs | Yes | No |
| Manage system users | Yes | No |
| Sign documents (group signature) | Optional | Yes |
| Verify signatures | Yes | Yes |
| Generate claim | Yes | Yes |
| Verify claim | Yes | Yes |

Regular users only see signing-related features in the UI. Group administration, member management, audit pages, and system user management are hidden from non-admin users.

## Tech Stack

- Backend: Flask (Python)
- Frontend: HTML + JavaScript + Bootstrap 5
- Storage: SQLite + JSON files
- Group signature library: libgroupsig / pygroupsig

## Quick Start

### 1. Prerequisites

- Python 3.10 or newer
- `uv` for dependency and virtual environment management

### 2. Sync dependencies

```bash
uv sync
```

### 3. Start the system

Recommended:

```bash
bash start.sh
```

Manual start:

```bash
uv run python backend/app.py
```

Then open http://localhost:5000 in your browser.

### 4. Basic troubleshooting

If `pygroupsig` import fails:

```bash
uv sync --reinstall
```

If runtime errors occur:

```bash
uv run python --version
uv pip list --python .venv/bin/python | grep -E "Flask|cffi|pygroupsig"
```

## Project Structure

```text
kty04-secrecy-system/
|- backend/
|  |- app.py
|  |- api/
|  |- utils/
|- data/
|  |- groups/
|  |- members/
|  |- signatures/
|- frontend/
|  |- index.html
|  |- css/
|  |- js/
|- pyproject.toml
```

## Authorization Model

### Roles

| Capability | Admin | User |
|---|---|---|
| Create groups | Yes | No |
| Add members | Yes | No |
| Open/trace signatures | Yes | No |
| View audit logs | Yes | No |
| Manage system users | Yes | No |
| Sign documents (group signature) | Optional | Yes |
| Verify signatures | Yes | Yes |
| Generate claim | Yes | Yes |
| Verify claim | Yes | Yes |

### Request authentication headers

- `X-User-ID`
- `X-Token`

### Enforcement boundaries

- `POST /api/groups`: admin only
- `POST /api/members`: admin only
- `POST /api/documents/<id>/signatures/<sig_id>/trace`: admin only
- `GET /api/audit/logs`: admin only
- `POST /api/documents/<id>/sign`: authenticated user and target-group membership required

Regular users should not access system management or audit capabilities.

## Core Workflow

1. An admin creates a group and the system generates group key material.
2. The admin adds members and completes JOIN protocol steps.
3. A user signs a document anonymously with a group signature.
4. A verifier checks signature validity without learning signer identity.
5. If accountability is required, an admin opens the signature.
6. A signer can generate a claim and a verifier can validate it.

## Testing (pytest)

The test suite is organized by purpose:

```text
tests/
|- conftest.py
|- functional/
|  |- test_auth_and_permissions.py
|  |- test_document_flow.py
|- performance/
   |- test_api_performance.py
```

Start the backend before running tests:

```bash
uv run python backend/app.py
```

Run functional tests:

```bash
uv run pytest tests/functional
```

Run performance tests (opt-in):

```bash
uv run pytest tests/performance --run-performance
```

If the database is not empty and admin-only assertions are needed:

```bash
uv run pytest tests/functional --admin-username <admin> --admin-password <password>
uv run pytest tests/performance --run-performance --admin-username <admin> --admin-password <password>
```

## API Overview

### Authentication and users

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/users` (admin)
- `PUT /api/auth/users/<id>/role` (admin)

### Group management

- `GET /api/groups`
- `POST /api/groups` (admin)
- `GET /api/groups/<id>`

### Member management

- `GET /api/members` (admin)
- `POST /api/members` (admin)
- `GET /api/members/<id>` (admin)

### Document workflows

- `GET /api/documents`
- `POST /api/documents` (admin)
- `GET /api/documents/<id>`
- `POST /api/documents/<id>/sign`
- `POST /api/documents/<id>/verify`
- `POST /api/documents/<id>/signatures/<sig_id>/trace` (admin)
- `PUT /api/documents/<id>/status` (admin)

### Signature endpoints

- `GET /api/signatures`
- `POST /api/signatures`
- `POST /api/signatures/<id>/verify`
- `POST /api/signatures/<id>/claim`
- `POST /api/signatures/<id>/claim/verify`
- `POST /api/signatures/<id>/open` (admin)

### Audit

- `GET /api/audit/logs` (admin)
- `GET /api/audit/stats`

## Notes

- Key material and runtime data are stored under `data/`; handle them securely.
- This project documentation focuses on management workflows; for low-level library internals, refer to the upstream libgroupsig repository.
