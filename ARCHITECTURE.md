# Architecture & System Design

## Overview
Davinci Document Creator is a full-stack web application designed to convert Markdown documents into professionally branded PDFs. It features Azure AD authentication for security and integrates with DocuSign for automated signature workflows. The system is containerized for deployment on Azure Kubernetes Service (AKS).

## Technology Stack

### Frontend
- **Framework:** React 18 (TypeScript)
- **UI Library:** Material-UI (MUI) v5
- **State Management:** React Hooks (Context/State)
- **Build Tool:** Create React App (CRA)
- **Communication:** Axios for REST API consumption

### Backend
- **Framework:** Flask (Python 3.11+)
- **Server:** Gunicorn (WSGI)
- **PDF Engine:** ReportLab (Programmatic PDF generation)
- **Markdown Parsing:** `markdown2` with custom HTML-to-ReportLab translation
- **Authentication:** `msal` (Microsoft Authentication Library) for Azure AD
- **Integrations:** `docusign-esign` SDK

### Infrastructure
- **Containerization:** Docker (Multi-stage builds)
- **Orchestration:** Kubernetes (AKS)
- **Ingress:** NGINX (Reverse proxy for frontend static files and API routing)
- **Registry:** Azure Container Registry (ACR)

## Data Flow

### 1. PDF Generation Flow
1.  **User Input:** User writes Markdown in the React frontend.
2.  **Request:** Frontend sends POST request to `/api/convert` with Markdown content + Branding Config (Base64 Logo, Company Details).
3.  **Processing (Backend):
    *   Authentication check (Azure AD session or API Key).
    *   Input validation and sanitization.
    *   Markdown $\rightarrow$ HTML conversion (`markdown2`).
    *   HTML $\rightarrow$ ReportLab Flowables (Custom Parser).
    *   PDF Drawing (Custom `NumberedCanvas` handles headers, footers, and page numbering).
4.  **Response:** Backend returns binary PDF stream with `Content-Disposition` header.
5.  **Client Action:** Browser triggers file download.

### 2. DocuSign Workflow
1.  **Initiation:** User clicks "Send for Signature" in React.
2.  **Request:** Frontend sends payload to `/api/docusign/send-for-signature`.
3.  **Envelope Creation:**
    *   Backend generates the PDF (same process as above).
    *   `docusign_client.py` authenticates via JWT Grant.
    *   Envelope created with two signers: External Recipient (Order 1) and Internal Counter-Signer (Order 2).
    *   Anchor tags (e.g., `/ds_recipient_signature/`) in the PDF are mapped to DocuSign tabs.
4.  **Transmission:** DocuSign sends emails to signers.
5.  **Status:** Webhooks (TODO) or polling tracks envelope status.

## Component Architecture

### Backend (`/backend`)
*   **`app.py`:** Main entry point. Handles routing, request parsing, and orchestrates the PDF generation pipeline.
*   **`auth.py`:** Encapsulates Azure AD logic, token validation, and login decorators.
*   **`docusign_client.py`:** Wrapper around the DocuSign eSignature REST API. Handles JWT auth and Envelope definitions.
*   **`assets/`:** Contains static resources (fonts, default logos) required for PDF generation.

### Frontend (`/frontend`)
*   **`App.tsx`:** Main application controller. Manages state for Markdown content, configuration, and user session.
*   **`ConfigDialog.tsx`:** Modal for editing company details and branding.
*   **`DocuSignDialog.tsx`:** Form for specifying recipient details for signature requests.

## Security

*   **Authentication:**
    *   **Production:** Azure AD (OIDC/OAuth2).
    *   **API Access:** API Key support for automated testing/health checks.
*   **Rate Limiting:** `flask-limiter` protects endpoints (e.g., 10 DocuSign requests/hour).
*   **Input Sanitization:** `markdown2` safe mode (partial) and file upload validation (logo size/type).
*   **Secrets:** Managed via Environment Variables. **Critical:** `SECRET_KEY` must be set in production to prevent session tampering.

## Deployment Architecture

The application follows a standard microservices-like pattern within a single pod or split across pods in K8s:

```mermaid
graph LR
    Client[Browser] --> Ingress[K8s Ingress / NGINX]
    Ingress -->|/| Frontend[React App (Static)]
    Ingress -->|/api| Backend[Flask API]
    Backend -->|Auth| AzureAD[Azure Active Directory]
    Backend -->|Sign| DocuSign[DocuSign API]
```

## Known Risks & Roadmap

1.  **Synchronous Processing:** PDF generation happens in the request thread. Heavy load could starve Gunicorn workers.
    *   *Mitigation:* Move PDF generation to a Celery task queue (Redis/RabbitMQ).
2.  **Secret Management:** Hardcoded fallbacks for secrets exist in code.
    *   *Fix:* Enforce environment variable presence on startup; fail fast if missing.
3.  **Hardcoded Logic:** Specific user names (e.g., "Ian Strom") are hardcoded as counter-signers.
    *   *Fix:* Move these configurations to database or environment variables.
