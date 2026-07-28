# Repository conventions

This project uses [release-please](https://github.com/googleapis/release-please) for automated versioning and changelogs. It requires conventional commit messages.

## Commit message format

Every commit message must follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>
```

### Types

| Type | Version bump | Example |
|------|-------------|---------|
| `feat` | Minor (0.1.0 → 0.2.0) | `feat: add pairing support to config flow` |
| `fix` | Patch (0.1.0 → 0.1.1) | `fix: handle transmitter disconnect gracefully` |
| `chore` | None | `chore: update ruff to 0.17` |
| `docs` | None | `docs: add troubleshooting section` |
| `refactor` | None | `refactor: extract frame logic to separate function` |

### Breaking changes

Add `!` after the type or `BREAKING CHANGE:` in the body:

```
feat!: drop support for Home Assistant 2026.4
```

or

```
feat: add new config flow

BREAKING CHANGE: old config entries must be re-created
```

### Scope (optional)

```
feat(config_flow): add address validation
fix(cover): handle rolling code overflow
```