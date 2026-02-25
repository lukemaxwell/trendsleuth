# PyPI Setup Guide

This guide covers the one-time setup required to enable automated PyPI publishing for TrendSleuth.

## Prerequisites

- PyPI account at https://pypi.org
- GitHub repository with admin access
- Package already published to PyPI (for first-time publishing, see Manual Release below)

## Step 1: Create PyPI API Token

1. Log in to PyPI at https://pypi.org
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Configure the token:
   - **Token name**: `github-actions-trendsleuth`
   - **Scope**: "Project: trendsleuth" (recommended) or "Entire account" (less secure)
5. Click "Add token"
6. **IMPORTANT**: Copy the token immediately (starts with `pypi-`)
   - You won't be able to see it again!
   - Store it securely (password manager recommended)

## Step 2: Add Token to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Configure the secret:
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: Paste the token from Step 1 (including the `pypi-` prefix)
5. Click "Add secret"

## Step 3: Verify Setup

The automated publishing workflow (`.github/workflows/publish.yml`) is already configured.

To test the setup:

1. Create a test release with a version like `v0.1.4-test`
2. Check the GitHub Actions tab for the "Publish to PyPI" workflow
3. If successful, the new version will appear on PyPI
4. If needed, you can delete test releases from PyPI

## Security Best Practices

### Token Scope
- **Recommended**: Project-scoped tokens (limits access to just TrendSleuth)
- **Not recommended**: Account-wide tokens (gives access to all your packages)

### Token Rotation
- Rotate tokens periodically (every 6-12 months)
- Revoke old tokens after creating new ones
- Update GitHub secrets with new token

### Access Control
- Only repository admins should have access to secrets
- Use protected branches to require reviews before releases
- Enable two-factor authentication on PyPI account

## Troubleshooting

### "Invalid or expired token"
- Token may have been revoked or expired
- Create a new token and update GitHub secrets

### "Package does not exist"
- For first-time publishing, use manual release (see below)
- Project-scoped tokens only work after first manual publish

### "Permission denied"
- Verify token scope includes the trendsleuth project
- Check that token hasn't been revoked in PyPI settings

## Manual Release (First Time Only)

For the very first PyPI release, you may need to publish manually:

```bash
# Install build tools
uv pip install build twine

# Build the package
python -m build

# Upload to PyPI (will prompt for username/password or token)
twine upload dist/*
```

After the first manual release, automated publishing will work for all future releases.

## Additional Resources

- [PyPI API Token Guide](https://pypi.org/help/#apitoken)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Python Packaging Guide](https://packaging.python.org/)
