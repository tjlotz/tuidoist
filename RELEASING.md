# Releasing

Tuidoist is published to [PyPI](https://pypi.org/project/tuidoist/). Releases are automated via GitHub Actions on tag push, using PyPI [trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC). No API tokens are stored in the repo.

## Cutting a release

1. Bump the version in `pyproject.toml`. The package exposes `tuidoist.__version__` via `importlib.metadata`, so no other file needs to change.
2. Commit the bump:
   ```
   git commit -am "chore: bump version to vX.Y.Z"
   ```
3. Tag and push:
   ```
   git tag vX.Y.Z
   git push origin main --tags
   ```
4. Watch the [Release workflow](https://github.com/tjlotz/tuidoist/actions/workflows/release.yml). It will:
   - Build the sdist and wheel
   - Publish to TestPyPI
   - Publish to PyPI
   - Create a GitHub Release with auto-generated notes and the built artifacts attached

5. Verify the install works from a clean environment:
   ```
   uv tool install tuidoist
   tuidoist
   ```

## Dry-run via TestPyPI

To publish to TestPyPI without cutting a real release, trigger the **Release** workflow manually from the Actions tab and select `testpypi` as the target. This skips the PyPI publish and GitHub Release steps.

Verify a TestPyPI install:
```
uv tool install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tuidoist
```

## First-time setup

The release workflow authenticates to PyPI and TestPyPI via OIDC trusted publishers. These are configured once on each registry:

- PyPI: https://pypi.org/manage/account/publishing/
- TestPyPI: https://test.pypi.org/manage/account/publishing/

For each, register a publisher with:

- PyPI project name: `tuidoist`
- Owner: `tjlotz`
- Repository: `tuidoist`
- Workflow filename: `release.yml`
- Environment: `pypi` (on PyPI) or `testpypi` (on TestPyPI)

The matching GitHub Environments (`pypi`, `testpypi`) are referenced by the workflow and will be created on first use.
