# Azure AD Configuration for Davinci Document Creator

## App Registration Details
- **Application Name:** Davinci Document Creator
- **Client ID:** fec8fc31-50a9-4cf1-8bf9-ccd3f3b94d9c
- **Tenant ID:** 953021b0-d492-4cc9-8551-e0b35080b03a
- **Redirect URIs:**
  - http://docs.davincisolutions.ai/auth/callback
  - http://localhost:5001/auth/callback

## Current Status
- ✅ App Registration created
- ✅ Client Secret generated
- ✅ Kubernetes secret created
- ✅ Deployment configured with Azure AD credentials
- ⚠️ **Authentication is currently DISABLED** (REQUIRE_AUTH=false)

## To Enable Azure AD Authentication

1. Update the deployment to enable auth:
```bash
kubectl set env deployment/davinci-backend -n doc-generator REQUIRE_AUTH=true
```

2. Or edit k8s/deployment.yaml and change:
```yaml
- name: REQUIRE_AUTH
  value: "true"  # Changed from false
```

Then apply:
```bash
kubectl apply -f k8s/deployment.yaml
```

## How It Works
When enabled, users will:
1. Visit http://docs.davincisolutions.ai
2. Be redirected to Microsoft login
3. Authenticate with their Davinci AI Solutions account
4. Be redirected back to the app with access

## Testing
The app currently works WITHOUT authentication at:
http://docs.davincisolutions.ai

## Notes
- The client secret expires in 2 years (2027)
- Only users in the Davinci AI Solutions tenant can login
- The app has User.Read permission to get basic user info