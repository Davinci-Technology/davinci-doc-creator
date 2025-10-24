# DocuSign Integration Setup Guide

This guide walks you through setting up DocuSign eSignature integration for the Davinci Document Creator.

## Overview

The DocuSign integration allows users to send generated PDFs directly for electronic signature with a sequential signing workflow:
1. **External recipient** signs first (Order 1)
2. **Ian Strom** (Davinci AI Solutions) counter-signs (Order 2)

## Features

- **Anchor-based field positioning**: Signature fields automatically position themselves using invisible markers in the PDF
- **Sequential routing**: Ensures proper signing order
- **Email customization**: Optional custom subject and message for recipients
- **Status tracking**: Monitor signing progress via API
- **Webhook support**: Receive real-time updates when documents are signed

## Prerequisites

1. DocuSign Developer Account (free for sandbox/testing)
2. RSA key pair for JWT authentication
3. Access to Kubernetes secrets (for staging/production deployment)

## Step 1: Create DocuSign Developer Account

1. Visit [https://developers.docusign.com/](https://developers.docusign.com/)
2. Click **"Get a Developer Account"** (free)
3. Complete registration and verify your email
4. Log in to the **Admin Console**

## Step 2: Create an Integration Key (Application)

1. In the DocuSign Admin Console, go to **"Settings" → "Apps and Keys"**
2. Click **"Add App and Integration Key"**
3. Enter application details:
   - **App Name**: `Davinci Document Creator`
   - **Redirect URI**: `https://staging-docs.davincisolutions.ai/api/auth/callback` (not used for JWT, but required)
4. Click **"Create App"**
5. **Save the Integration Key** (you'll need this later)

## Step 3: Generate RSA Key Pair for JWT Authentication

1. In the same app configuration, scroll to **"Authentication"**
2. Under **"Service Integration"**, click **"Generate RSA"**
3. A dialog appears with your RSA key pair
4. **Download and save the private key** (`private.key`)
   - **IMPORTANT**: Store this securely - you cannot retrieve it later!
5. DocuSign automatically stores the public key

## Step 4: Grant Consent for JWT Authentication

JWT apps require one-time user consent:

1. In the app configuration, under **"Service Integration"**, click **"Generate RSA"** section
2. Copy the **consent URL** (it looks like):
   ```
   https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature%20impersonation&client_id=YOUR_INTEGRATION_KEY&redirect_uri=https://developers.docusign.com
   ```
3. Open this URL in your browser **while logged in as the user**
4. Click **"Allow Access"** to grant consent
5. You should see a success message

## Step 5: Get Your User ID and Account ID

### User ID (GUID):
1. In DocuSign Admin Console, click your profile icon (top right)
2. Go to **"My Account Settings" → "API and Keys"**
3. Your **User ID** (GUID) is displayed under "API Username"
   - Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### Account ID:
1. Same page as above
2. Your **Account ID** is displayed under "Account ID"
   - Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

## Step 6: Configure Environment Variables

### For Local Development (`.env` file):

Create a `.env` file in the project root:

```bash
# DocuSign Configuration
DOCUSIGN_INTEGRATION_KEY=your-integration-key-from-step-2
DOCUSIGN_USER_ID=your-user-guid-from-step-5
DOCUSIGN_ACCOUNT_ID=your-account-id-from-step-5
DOCUSIGN_PRIVATE_KEY_PATH=/path/to/private.key
DOCUSIGN_BASE_PATH=https://demo.docusign.net/restapi
DOCUSIGN_OAUTH_HOST=account-d.docusign.com
```

### For Kubernetes Staging Deployment:

1. Create a Kubernetes secret with your DocuSign credentials:

```bash
# First, base64 encode your private key (keep newlines intact)
cat private.key | base64

# Create the secret
kubectl create secret generic davinci-doc-secrets-staging \
  --namespace=doc-generator-staging \
  --from-literal=docusign-integration-key='your-integration-key' \
  --from-literal=docusign-user-id='your-user-guid' \
  --from-literal=docusign-account-id='your-account-id' \
  --from-literal=docusign-base-path='https://demo.docusign.net/restapi' \
  --from-literal=docusign-oauth-host='account-d.docusign.com' \
  --from-literal=docusign-private-key="$(cat private.key)"
```

2. Or update the existing secret:

```bash
kubectl create secret generic davinci-doc-secrets-staging \
  --namespace=doc-generator-staging \
  --from-literal=docusign-integration-key='your-integration-key' \
  --from-literal=docusign-user-id='your-user-guid' \
  --from-literal=docusign-account-id='your-account-id' \
  --from-literal=docusign-base-path='https://demo.docusign.net/restapi' \
  --from-literal=docusign-oauth-host='account-d.docusign.com' \
  --from-literal=docusign-private-key="$(cat private.key)" \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Step 7: Test the Integration

### Local Testing:

1. Start the backend:
   ```bash
   cd backend
   export $(cat ../.env | xargs)
   python app.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm start
   ```

3. Open `http://localhost:3000`
4. Create a document and click **"Send for Signature"**
5. Enter recipient details (use your own email for testing)
6. Check your email for the DocuSign signing request

### Staging Environment Testing:

1. Ensure secrets are configured (Step 6)
2. Deploy to staging:
   ```bash
   git push origin staging
   ```
3. Wait for GitHub Actions to complete deployment
4. Visit `https://staging-docs.davincisolutions.ai`
5. Test the "Send for Signature" workflow

## Step 8: Monitor Envelopes

You can monitor signing progress in several ways:

### DocuSign Admin Console:
1. Log in to [https://appdemo.docusign.com/](https://appdemo.docusign.com/)
2. View all envelopes in **"Manage" → "Sent"**

### Via API (Status Endpoint):
```bash
# Get envelope status
curl https://staging-docs.davincisolutions.ai/api/docusign/envelope/{envelope_id}/status
```

### Backend Logs:
```bash
# View logs in Kubernetes
kubectl logs -f deployment/davinci-backend-staging -n doc-generator-staging
```

## Step 9: Production Deployment

Once tested in staging, promote to production:

1. Create production secrets:
   ```bash
   kubectl create secret generic davinci-doc-secrets \
     --namespace=doc-generator \
     --from-literal=docusign-integration-key='your-integration-key' \
     --from-literal=docusign-user-id='your-user-guid' \
     --from-literal=docusign-account-id='your-account-id' \
     --from-literal=docusign-base-path='https://na3.docusign.net/restapi' \
     --from-literal=docusign-oauth-host='account.docusign.com' \
     --from-literal=docusign-private-key="$(cat private.key)"
   ```

2. **Note**: For production, use production API endpoints:
   - `DOCUSIGN_BASE_PATH=https://na3.docusign.net/restapi` (or your region)
   - `DOCUSIGN_OAUTH_HOST=account.docusign.com`

3. Update production deployment YAML if needed

4. Deploy:
   ```bash
   git push origin main
   ```

## Troubleshooting

### "Authentication failed" Error

**Cause**: JWT token request failed

**Solutions**:
1. Verify consent was granted (Step 4)
2. Check private key is correct and accessible
3. Ensure User ID and Integration Key match
4. Check that RSA key pair was generated correctly

### "Private key not found" Error

**Cause**: Private key file not accessible

**Solutions**:
1. Verify `DOCUSIGN_PRIVATE_KEY_PATH` is correct
2. Check file permissions
3. In Kubernetes, ensure secret is mounted correctly
4. Verify secret contains the private key:
   ```bash
   kubectl get secret davinci-doc-secrets-staging -n doc-generator-staging -o yaml
   ```

### "Invalid recipient_email format" Error

**Cause**: Email validation failed

**Solution**: Ensure email format is valid (e.g., `user@example.com`)

### Anchor Tags Not Found

**Cause**: DocuSign cannot find the anchor strings in the PDF

**Solutions**:
1. Verify signature page is included in PDF
2. Check that anchor tags are present (they're invisible white text)
3. Regenerate PDF and inspect in a text editor for anchor strings like `/ds_recipient_signature/`

## API Reference

### Send for Signature

**Endpoint**: `POST /api/docusign/send-for-signature`

**Request Body**:
```json
{
  "markdown": "# Document content...",
  "recipient_name": "John Doe",
  "recipient_email": "john@example.com",
  "document_name": "My Document",
  "email_subject": "Please sign: My Document",
  "email_message": "Please review and sign.",
  "company": "Davinci AI Solutions",
  "includeTitlePage": true
}
```

**Response**:
```json
{
  "success": true,
  "envelope_id": "abc123-def456-...",
  "status": "sent",
  "recipient": {
    "name": "John Doe",
    "email": "john@example.com",
    "routing_order": 1
  },
  "counter_signer": {
    "name": "Ian Strom",
    "email": "ian.strom@davincisolutions.ai",
    "routing_order": 2
  }
}
```

### Get Envelope Status

**Endpoint**: `GET /api/docusign/envelope/{envelope_id}/status`

**Response**:
```json
{
  "envelope_id": "abc123-def456-...",
  "status": "completed",
  "created_date_time": "2025-01-15T10:00:00Z",
  "sent_date_time": "2025-01-15T10:01:00Z",
  "completed_date_time": "2025-01-15T11:30:00Z",
  "signers": [
    {
      "name": "John Doe",
      "email": "john@example.com",
      "status": "completed",
      "routing_order": 1,
      "signed_date_time": "2025-01-15T10:15:00Z"
    },
    {
      "name": "Ian Strom",
      "email": "ian.strom@davincisolutions.ai",
      "status": "completed",
      "routing_order": 2,
      "signed_date_time": "2025-01-15T11:30:00Z"
    }
  ]
}
```

## Security Best Practices

1. **Private Key Protection**:
   - Never commit private keys to git
   - Store in Kubernetes secrets with proper RBAC
   - Use separate keys for staging and production

2. **API Rate Limiting**:
   - Default: 10 requests per hour per IP
   - Configured via `flask-limiter`
   - Adjust in `backend/app.py` if needed

3. **Webhook Verification**:
   - TODO: Implement HMAC verification for webhook events
   - DocuSign can sign webhook payloads for security

4. **Environment Separation**:
   - Use **demo/sandbox** environment for staging
   - Use **production** environment only for real documents

## Support Resources

- **DocuSign Developer Center**: [https://developers.docusign.com/](https://developers.docusign.com/)
- **API Documentation**: [https://developers.docusign.com/docs/esign-rest-api/](https://developers.docusign.com/docs/esign-rest-api/)
- **Support Portal**: [https://support.docusign.com/](https://support.docusign.com/)

## Next Steps

- [ ] Set up webhook endpoint for real-time signing notifications
- [ ] Implement envelope download after completion
- [ ] Add support for multiple counter-signers
- [ ] Create admin dashboard for envelope management
- [ ] Add DocuSign branding customization
