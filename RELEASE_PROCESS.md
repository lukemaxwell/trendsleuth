# Release Process

This document describes how to release a new version of TrendSleuth to PyPI.

## Automated Release (Recommended)

The project uses GitHub Actions to automatically publish to PyPI when a new release is created.

### Prerequisites

1. PyPI API token configured in GitHub secrets (see `PYPI_SETUP.md` for one-time setup)
2. All changes committed and pushed to `main` branch
3. All tests passing locally

### Release Steps

1. **Update version in `pyproject.toml`**
   ```toml
   [project]
   version = "0.1.4"  # Update this
   ```

2. **Update CHANGELOG.md**
   - Move changes from `[Unreleased]` to a new version section
   - Add release date: `## [0.1.4] - YYYY-MM-DD`
   - Follow [Keep a Changelog](https://keepachangelog.com/) format

3. **Run tests locally**
   ```bash
   uv run pytest
   uv run mypy src/
   ```

4. **Commit version bump**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.1.4"
   git push origin main
   ```

5. **Create GitHub Release**
   - Go to https://github.com/lukemaxwell/trendsleuth/releases/new
   - Tag version: `v0.1.4` (note the `v` prefix)
   - Release title: `TrendSleuth v0.1.4 - <Brief Description>`
   - Description: Copy relevant sections from CHANGELOG.md
   - Click "Publish release"

6. **Wait for Automation**
   - GitHub Actions will automatically:
     - Run all tests
     - Build the package
     - Publish to PyPI
   - Monitor progress at: https://github.com/lukemaxwell/trendsleuth/actions

7. **Verify Release**
   - Check PyPI: https://pypi.org/project/trendsleuth/
   - Verify version number and release date
   - Test installation: `pip install trendsleuth==0.1.4`

## Manual Release (Backup)

If automated release fails, you can publish manually:

1. **Install build tools**
   ```bash
   uv pip install build twine
   ```

2. **Build package**
   ```bash
   python -m build
   ```

3. **Check package**
   ```bash
   twine check dist/*
   ```

4. **Upload to PyPI**
   ```bash
   twine upload dist/*
   ```
   - Enter `__token__` as username
   - Paste PyPI API token as password

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.2.0): New features, backwards compatible
- **PATCH** (0.1.1): Bug fixes, backwards compatible

Examples:
- `0.1.3` → `0.1.4`: Bug fixes or minor improvements
- `0.1.3` → `0.2.0`: New features added
- `0.9.0` → `1.0.0`: First stable release or breaking changes

## Release Checklist

- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated with release notes
- [ ] All tests passing (`uv run pytest`)
- [ ] Type checking passing (`uv run mypy src/`)
- [ ] Changes committed and pushed to main
- [ ] GitHub release created with correct tag (e.g., `v0.1.4`)
- [ ] GitHub Actions workflow completed successfully
- [ ] New version visible on PyPI
- [ ] Installation tested: `pip install trendsleuth==<version>`

## Troubleshooting

### Workflow fails at "Publish to PyPI"
- Check that `PYPI_API_TOKEN` secret is set correctly
- Verify token hasn't expired in PyPI settings
- Check PyPI for rate limits or outages

### Version already exists on PyPI
- Cannot overwrite existing versions
- Must bump version number and create new release
- Delete the GitHub release and tag, fix version, try again

### Tests fail in CI
- Run tests locally first: `uv run pytest`
- Check GitHub Actions logs for specific failure
- Fix issues, commit, and push before creating release

## Release Notes Template

When creating a GitHub release, use this template:

```markdown
## What's New

[Brief 1-2 sentence summary of the release]

### Added
- Feature 1
- Feature 2

### Changed
- Change 1
- Change 2

### Fixed
- Bug fix 1
- Bug fix 2

### Technical
- Technical improvement 1
- Technical improvement 2

## Installation

```bash
pip install trendsleuth==0.1.4
```

## Full Changelog

See [CHANGELOG.md](https://github.com/lukemaxwell/trendsleuth/blob/main/CHANGELOG.md) for complete details.
```

## Post-Release

1. **Update documentation** if needed
2. **Announce release** on relevant channels
3. **Monitor issues** for any problems with new version
4. **Start next version** by adding `[Unreleased]` section to CHANGELOG.md
