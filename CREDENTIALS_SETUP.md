# Credentials Setup Guide

## GitHub Authentication (Recommended Method)

Your GitHub credentials are now stored **securely in your macOS keychain** via the `gh` CLI tool. This is the industry best practice.

### ✅ Already Configured
You're all set! Your credentials are authenticated as `ianstrom-davinci`.

### Verify Authentication
```bash
gh auth status
```

### Check Deployments
```bash
# List recent workflow runs
gh run list --limit 10

# View specific run details
gh run view <run-id>

# Watch a deployment in real-time
gh run watch

# View logs from a specific job
gh run view --log
```

### Re-authenticate (if needed)
```bash
# Interactive login
gh auth login

# Or with token
echo "YOUR_TOKEN" | gh auth login --with-token
```

### Logout
```bash
gh auth logout
```

---

## Alternative: .env File (Not Recommended)

If you absolutely need to store credentials in a file for scripts/tools that don't support `gh` CLI:

1. Copy the example:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```bash
   GITHUB_TOKEN=ghp_YOUR_TOKEN
   GITHUB_USER=your-username
   ```

3. **Important:** `.env` is already in `.gitignore` so it won't be committed.

---

## Azure Credentials (for local development)

If you want to test Azure AD authentication locally:

1. Get the client secret from your team
2. Add to `.env`:
   ```bash
   AZURE_AD_CLIENT_SECRET=your-secret-here
   REQUIRE_AUTH=true
   ```
3. Run backend:
   ```bash
   cd backend
   export $(cat ../.env | xargs)
   python app.py
   ```

---

## Best Practices

### ✅ DO:
- Use `gh` CLI for GitHub (stores in system keychain)
- Use Kubernetes secrets for production
- Share `.env.example` with team (safe to commit)
- Generate strong random secrets: `openssl rand -hex 32`
- Different credentials for each environment

### ❌ DON'T:
- Commit `.env` to git (already prevented by `.gitignore`)
- Share credentials in Slack/email
- Use the same secret in dev and production
- Hard-code credentials in source code

---

## Troubleshooting

### "gh: command not found"
```bash
brew install gh
```

### "Authentication required"
```bash
gh auth login
```

### "Permission denied"
Check your token has the right scopes:
- `repo` - Full control of repositories
- `workflow` - Update GitHub Actions workflows
- `read:org` - Read org data (if needed)

---

## Security Notes

- Your PAT is stored encrypted in macOS Keychain
- The token shown above has been used and is now active
- To rotate token: Generate new PAT in GitHub → re-run `gh auth login`
- Never paste tokens in public forums/issues

---

## Quick Commands

```bash
# Check latest deployment status
gh run list --limit 1

# Watch current deployment
gh run watch

# View staging deployments
gh run list --workflow="Deploy to Staging"

# View production deployments
gh run list --workflow="Deploy to Production"

# Manual trigger deployment
gh workflow run "Deploy to Staging"
```
