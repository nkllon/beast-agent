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

### PyPI Publishing

**`PYPI_API_TOKEN`** (Required for PyPI publishing workflow)
- Description: PyPI API token for publishing packages
- How to obtain:
  1. Go to https://pypi.org
  2. Log in to your account
  3. Go to Account Settings → API tokens
  4. Create a new API token (or use existing)
  5. Copy the token (format: `pypi-...`)
- How to add in GitHub:
  1. Go to repository Settings → Secrets and variables → Actions
  2. Click "New repository secret"
  3. Name: `PYPI_API_TOKEN`
  4. Value: Paste the PyPI API token
  5. Click "Add secret"
- Usage: Used by `.github/workflows/publish.yml` to publish releases to PyPI

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
3. Verify `PYPI_API_TOKEN` appears in the list
4. Check that `GITHUB_TOKEN` is shown as "automatically available"

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

