# GitHub Secrets Configuration

This document lists the secrets that need to be configured in GitHub repository settings for CI/CD workflows.

## Required Secrets

### SonarCloud Integration

**`SONAR_TOKEN`** (Required for SonarCloud workflow)
- Description: SonarCloud authentication token
- How to obtain:
  1. Go to https://sonarcloud.io
  2. Log in with GitHub account
  3. Navigate to: My Account → Security → Generate Token
  4. Copy the token
- How to add in GitHub:
  1. Go to repository Settings → Secrets and variables → Actions
  2. Click "New repository secret"
  3. Name: `SONAR_TOKEN`
  4. Value: Paste the token from SonarCloud
  5. Click "Add secret"
- **Or using GitHub CLI:**
  ```bash
  gh secret set SONAR_TOKEN
  # Paste the token when prompted
  ```

### PyPI Publishing (Trusted Publishing - Recommended)

**No API Token Required** - Using Trusted Publishing (OIDC)

The workflow uses PyPI Trusted Publishing, which is more secure and doesn't require storing API tokens.

**How to Set Up Trusted Publishing:**

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Configure:
   - **PyPI project name:** `beast-agent`
   - **Owner:** `louspringer` (your PyPI username)
   - **Workflow filename:** `.github/workflows/publish.yml`
   - **GitHub repository:** `nkllon/beast-agent`
   - **Environment name:** (leave blank or use `production`)
4. Click "Add pending publisher"
5. The publisher will be active after the first successful publish

**Benefits:**
- ✅ No API tokens to manage
- ✅ More secure (OIDC-based)
- ✅ Automatically works for all future releases
- ✅ Recommended by PyPI

**Note:** The project must be registered on PyPI first (either manually or via first publish). For first publish, you may need to create the project manually on PyPI or use an account-scoped API token for the initial publish.

**Alternative (API Token Method - Not Recommended):**
If you prefer using API tokens:
- Create account-scoped token from https://pypi.org/manage/account/token/
- Set as `PYPI_API_TOKEN` secret
- Update workflow to use token instead of Trusted Publishing

### Automatic Secrets (No Action Needed)

**`GITHUB_TOKEN`** (Automatically provided by GitHub Actions)
- Description: GitHub authentication token for repository access
- Status: Automatically injected by GitHub Actions
- Usage: Used for SonarCloud GitHub integration

## Verification

After adding secrets, verify they're configured:

**Using GitHub CLI:**
```bash
gh secret list
```

**Using GitHub UI:**
1. Go to repository Settings → Secrets and variables → Actions
2. Verify `SONAR_TOKEN` appears in the list
3. Check that `GITHUB_TOKEN` is shown as "automatically available"

**Note:** Secrets should be configured as part of the initial repository setup, not just documented. Use `gh secret set` to configure them programmatically.

## Testing

To test if secrets are working:

1. Create a new release (with a tag)
2. The workflows will automatically trigger
3. Check workflow logs for any authentication errors
4. Verify SonarCloud analysis runs successfully

## Notes

- Secrets are encrypted and only accessible to GitHub Actions
- Secrets are never exposed in logs (GitHub automatically masks them)
- If a secret is missing, workflows will fail with an authentication error
- Secrets can be updated at any time without affecting running workflows
