# Architecture & System Design

## Executive Summary
Davinci Document Creator is a full-stack web application designed to convert Markdown documents into professionally formatted, branded PDFs. It utilizes a React frontend and a Python Flask backend. Key features include automated corporate branding, dynamic pagination using a custom ReportLab canvas, and an integrated DocuSign workflow for sequential signatures.

While the core PDF generation logic is robust, the application currently suffers from critical integration gaps in authentication and event handling that must be addressed before production use.

## Technology Stack

### Frontend
- **Framework:** React 18 (TypeScript)
- **UI Library:** Material-UI (MUI) v5
- **State Management:** React Hooks (Context/State)
- **Build Tool:** Create React App (CRA)
- **Communication:** Axios for REST API consumption
- **Hosting:** Served via NGINX (acting as reverse proxy in Docker/K8s)

### Backend
- **Framework:** Flask (Python 3.11+)
- **Server:** Gunicorn (WSGI)
- **PDF Engine:** ReportLab (Programmatic, low-level PDF generation)
- **Markdown Parsing:** `markdown2` $\rightarrow$ Custom `HTMLParser` $\rightarrow$ ReportLab Flowables
- **Authentication:** `msal` (Microsoft Authentication Library) for Azure AD (Incomplete integration)
- **Integrations:** `docusign-esign` SDK for signature workflows

### Infrastructure
- **Containerization:** Docker (Multi-stage builds)
- **Orchestration:** Kubernetes (AKS)
- **Ingress:** NGINX (Reverse proxy for frontend static files and API routing)
- **Registry:** Azure Container Registry (ACR)

## Data Flow

### 1. PDF Generation Flow
1.  **User Input:** User writes Markdown in the React frontend.
2.  **Request:** Frontend sends POST request to `/api/convert` with Markdown content + Branding Config (Base64 Logo, Company Details).
3.  **Processing (Backend):**
    *   **Auth Check:** Verifies Azure AD session or API Key (Note: Session creation flow is currently broken).
    *   **Parsing:** `markdown2` converts Markdown to HTML.
    *   **Transformation:** Custom `HTMLToReportLab` parser converts HTML tags to ReportLab "Flowables".
    *   **Rendering:** `SimpleDocTemplate` builds the PDF. A custom `NumberedCanvas` is used to draw headers, footers, and page numbers *after* flowable layout is calculated.
4.  **Response:** Backend returns binary PDF stream with `Content-Disposition` header.
5.  **Client Action:** Browser triggers file download.

### 2. DocuSign Workflow
1.  **Initiation:** User clicks "Send for Signature" in React.
2.  **Request:** Frontend sends payload to `/api/docusign/send-for-signature`.
3.  **Envelope Creation:**
    *   Backend generates the PDF (reusing the generation logic).
    *   `docusign_client.py` authenticates via JWT Grant (requires private key).
    *   Envelope created with two signers: **External Recipient** (Order 1) $\rightarrow$ **Internal Counter-Signer** (Order 2).
    *   **Anchor Tags:** The PDF generation injects invisible text anchors (e.g., `/ds_recipient_signature/`) which DocuSign uses to place signature tabs.
4.  **Transmission:** DocuSign sends emails to signers.
5.  **Status:** Currently reliant on manual checking; Webhook implementation is pending.

## Component Architecture

### Backend (`/backend`)
*   **`app.py`:** The monolithic controller. It handles API routing, input validation, and contains the custom PDF rendering classes (`NumberedCanvas`, `HTMLToReportLab`).
*   **`auth.py`:** Wrapper for `msal`. Intended to handle Azure AD login/callback, but currently disconnected from the main app routes.
*   **`docusign_client.py`:** Encapsulates DocuSign eSignature REST API interactions, handling JWT authorization and Envelope definitions.
*   **`assets/`:** Contains static resources (fonts, default logos) required for PDF generation.

### Frontend (`/frontend`)
*   **`App.tsx`:** Main application controller. Manages state for Markdown content, configuration, and user session.
*   **`Login.tsx`:** Landing page for unauthenticated users. Redirects to the (missing) backend login route.
*   **`components/`:** Contains dialogs for configuration and DocuSign input.

## Critical Findings & Risk Report

### 1. Broken Authentication Flow (Critical)
The `auth.py` module exists, but **`app.py` is missing the required routes** to handle the authentication lifecycle.
-   **Missing Endpoint:** `GET /api/auth/login` (Initiates OAuth flow)
-   **Missing Endpoint:** `GET /api/auth/callback` (Handles Azure AD redirect code)
-   **Missing Endpoint:** `GET /api/auth/user` (Returns current user session info)
-   **Missing Endpoint:** `GET /api/auth/logout` (Clears session)
*Result:* Users cannot log in. The app functions only if `REQUIRE_AUTH` is set to `false`.

### 2. Security Misconfigurations (High)
-   **CORS:** `CORS(app, origins=["*"])` is overly permissive, allowing any origin to interact with the API.
-   **Secret Management:** Fallback values for `SECRET_KEY` exist in the code.
-   **CSRF:** No CSRF protection is currently enabled beyond the (broken) session requirement.

### 3. Fragile PDF Parsing (Medium)
The conversion from HTML to PDF relies on a custom `HTMLParser` implementation (`HTMLToReportLab` class).
-   It is a manual state machine that may fail on complex or nested HTML structures.
-   It does not support the full Markdown spec (limited set of tags).
-   **Risk:** User input could crash the PDF generation process or result in malformed documents.

### 4. Hardcoded Business Logic (Medium)
-   **DocuSign Workflow:** The routing order and the counter-signer requirement are hardcoded in `docusign_client.py`.
-   **Internal Signer:** The counter-signer's identity relies on environment variables (`DOCUSIGN_COUNTER_SIGNER_EMAIL`), but the workflow structure itself is rigid.

## Deployment Architecture

The application follows a standard microservices-like pattern within a single pod or split across pods in K8s:

```mermaid
graph LR
    Client[Browser] --> Ingress[K8s Ingress / NGINX]
    Ingress -->|/| Frontend[React App (Static)]
    Ingress -->|/api| Backend[Flask API]
    Backend -->|Auth| AzureAD[Azure Active Directory (Broken)]
    Backend -->|Sign| DocuSign[DocuSign API]
```

## Implementation Roadmap

To stabilize the application, the following tasks are prioritized:

1.  **Implement Auth Routes:** Add `/login`, `/callback`, `/user`, and `/logout` to `app.py` using the `auth.py` helper class.
2.  **Secure CORS:** Restrict `Access-Control-Allow-Origin` to the actual frontend domain/container.
3.  **Configurable Workflow:** Move the DocuSign signer workflow configuration (number of signers, routing order) to a configuration file or environment variables.
4.  **Parser Hardening:** Add unit tests with complex Markdown/HTML inputs to verify `HTMLToReportLab` robustness.