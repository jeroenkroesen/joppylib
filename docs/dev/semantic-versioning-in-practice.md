# Semantic Versioning in Practice

A guide to versioning your software deliberately, covering the universal principles and the ecosystem-specific conventions for Python, Node.js/TypeScript, Rust, and PHP.

---

## 1. The Core Contract

Semantic Versioning (SemVer) uses the format **MAJOR.MINOR.PATCH** — three numbers separated by dots, like `1.4.2`. Each number is a promise to the people who depend on your code:

**PATCH** (1.4.2 → 1.4.3): Internal fixes only. No consumer of your library, API, or tool should need to change anything on their end. The fix is invisible from the outside.

*Examples across languages:*
- Fixing an off-by-one error in a sorting function.
- Correcting a typo in an error message.
- Improving the performance of an existing function without changing its signature or behavior.
- Fixing a CSS rendering bug in a Svelte component that didn't affect its props.

**MINOR** (1.4.3 → 1.5.0): New capabilities that are **backward-compatible**. Everything that worked before still works. You added something but broke nothing. When you bump MINOR, reset PATCH to 0.

*Examples:*
- Adding a new exported function or class.
- Adding a new optional parameter to an existing function, with a sensible default so existing calls are unaffected.
- Adding a new Svelte component to a component library.
- Adding a new subcommand to a CLI tool.

**MAJOR** (1.5.0 → 2.0.0): Breaking changes. Something that worked before may not work now, and your consumers may need to update their code. When you bump MAJOR, reset both MINOR and PATCH to 0.

*Examples:*
- Removing or renaming a public function, method, type, or export.
- Changing a function's return type.
- Changing a required prop on a Svelte/React component.
- Dropping support for a runtime version (Node 18, Python 3.9, PHP 8.0).
- Changing default behavior that existing users rely on.

### The Reset Rule

This trips people up, so to be explicit: when you increment a higher-order number, all lower numbers reset to zero.

```
Bug fix:     1.4.2  →  1.4.3
New feature: 1.4.3  →  1.5.0   (PATCH resets)
Breaking:    1.5.0  →  2.0.0   (MINOR and PATCH reset)
```

---

## 2. The 0.x Phase

While your version starts with `0`, SemVer explicitly says the API is unstable. This is your exploration phase, and it's a genuinely useful tool — not a shortcut or a sign of immaturity.

- **`0.1.0`** — First usable release. It works, but you make no stability promises.
- **`0.1.x`** — Bug fixes within that initial API.
- **`0.2.0`** — You can introduce breaking changes here without jumping to 1.0.0. During 0.x, the MINOR number effectively plays the role of MAJOR.
- **`0.x.y`** — Stay here as long as your API is still taking shape.

**Going to `1.0.0` is a commitment.** You're telling consumers: "This API is stable. From here on, I will follow SemVer strictly — breaking changes only in MAJOR bumps." There's no rush to get there. Many successful, widely-used packages spend months or years in 0.x while the design settles.

A practical signal that you're ready for 1.0.0: other projects depend on yours in production, and you find yourself naturally avoiding breaking changes because you don't want to disrupt them. That instinct means the API has stabilized.

---

## 3. Pre-release Versions

When you want early feedback before committing to a release, use pre-release identifiers. The concept is universal; the syntax varies by ecosystem.

### The SemVer Standard Syntax

SemVer appends a hyphen and dot-separated identifiers:

```
0.3.0-alpha.1    # Early testing — expect breakage
0.3.0-beta.1     # Feature-complete — hunting bugs
0.3.0-rc.1       # Release candidate — believed ready, final validation
0.3.0            # Stable release
```

**Sort order**: alpha < beta < rc < stable. Pre-releases always sort before the release they're attached to. `0.3.0-rc.1` comes before `0.3.0`.

### Ecosystem Variations

Different package managers interpret pre-release syntax in their own way. The important thing is that each ecosystem has a convention and a mechanism to prevent pre-releases from being installed by default.

**Python** (PEP 440) uses a different syntax — no hyphens, letters instead of words:

```
0.3.0a1     # Alpha
0.3.0b1     # Beta
0.3.0rc1    # Release candidate
0.3.0       # Stable
```

pip ignores pre-releases unless the user explicitly opts in (`pip install --pre` or pins the exact version).

**Node.js / npm** follows SemVer syntax directly:

```
0.3.0-alpha.1
0.3.0-beta.1
0.3.0-rc.1
```

npm won't match pre-releases with range specifiers like `^0.3.0`. Users must install them explicitly (`npm install my-package@0.3.0-beta.1`).

**Rust / Cargo** also follows SemVer syntax:

```
0.3.0-alpha.1
0.3.0-beta.1
0.3.0-rc.1
```

Cargo won't resolve pre-release versions unless the dependency requirement specifies the exact pre-release version.

**PHP / Composer** follows SemVer syntax and adds its own aliases:

```
0.3.0-alpha1
0.3.0-beta1
0.3.0-RC1
```

Composer respects a `minimum-stability` setting in `composer.json` that controls whether pre-releases are installable. The default is `"stable"`.

---

## 4. Where the Version Lives

Every ecosystem has a canonical location for the version string. The goal is the same everywhere: **one source of truth**, not multiple files that can drift out of sync.

### Python

In `pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

Expose it at runtime without duplicating the string:

```python
# src/my_package/__init__.py
from importlib.metadata import version
__version__ = version("my-package")
```

Alternatively, derive the version from git tags using a build plugin like `hatch-vcs`, so you never edit a version string manually at all.

### Node.js / TypeScript / SvelteKit

In `package.json`:

```json
{
  "name": "my-package",
  "version": "0.2.0"
}
```

npm provides a built-in bump command: `npm version patch`, `npm version minor`, `npm version major`. This edits `package.json`, creates a git commit, and tags it in one step.

### Rust

In `Cargo.toml`:

```toml
[package]
name = "my-crate"
version = "0.2.0"
```

Tools like `cargo-release` can automate the bump-commit-tag-publish cycle.

### PHP

In `composer.json`:

```json
{
  "name": "vendor/my-package",
  "version": "0.2.0"
}
```

Though notably, Packagist (PHP's package registry) **prefers** reading the version from git tags rather than from `composer.json`. Many PHP packages omit the version field entirely and let tags be the source of truth.

---

## 5. Git Tags as the Release Anchor

Regardless of your language or ecosystem, the most reliable versioning workflow anchors releases to **signed git tags**. Tags are immutable markers in your history — they pair a human-readable version with a specific commit.

```bash
# Create a signed, annotated tag
git tag -s v0.2.0 -m "Release 0.2.0"

# Push it to your remotes
git push origin v0.2.0
git push private v0.2.0    # Your SSH server
```

The `v` prefix is a convention, not a requirement, but it's nearly universal and helps distinguish version tags from other tags.

**Why signed tags matter**: Since you already sign commits with your GPG key, signing tags extends the same guarantee to releases. Anyone pulling your repo can run `git tag -v v0.2.0` and verify the release came from you, not from someone who gained push access.

### Tag-driven Versioning

Several ecosystems support deriving the package version directly from the most recent git tag at build time:

- **Python**: `hatch-vcs`, `setuptools-scm`
- **Node.js**: `semantic-release`, or a custom `prepack` script
- **Rust**: `cargo-release` can enforce tag-version consistency
- **PHP**: Packagist reads tags natively

The advantage is that the tag becomes the single source of truth. You tag, you push, the build system reads the tag and stamps the artifact. No file to edit, no string to update, no possibility of mismatch.

---

## 6. Keeping a Changelog

A changelog is the human-readable counterpart to your version numbers. The widely adopted format comes from [keepachangelog.com](https://keepachangelog.com):

```markdown
# Changelog

## [Unreleased]

### Added
- New `parse_config()` function for TOML support.

## [0.2.0] - 2026-03-15

### Changed
- `load()` now returns a `DataSet` instead of a raw dict. **Breaking.**

### Removed
- Dropped Python 3.9 support.

## [0.1.0] - 2026-01-10

### Added
- Initial release with core functionality.
```

The categories are: **Added**, **Changed**, **Deprecated**, **Removed**, **Fixed**, **Security**.

Write the changelog as you work, not at release time. Add entries under `[Unreleased]` with each PR or meaningful commit. When you release, rename `[Unreleased]` to the new version and date, then add a fresh `[Unreleased]` heading above it.

This format works for every language and every project. It gives your users the information they actually need to make upgrade decisions: what changed, what broke, and what's going away.

---

## 7. The Deprecation Cycle

Breaking changes are sometimes necessary, but surprising your users with them is not. The standard approach is a two-phase cycle:

**Phase 1 — Deprecate (MINOR release):** Introduce the new way alongside the old. Mark the old way as deprecated with a runtime warning. Be specific about what replaces it and when it will be removed.

```python
# Python
import warnings
warnings.warn(
    "process_data() is deprecated, use transform() instead. "
    "Will be removed in 2.0.0.",
    DeprecationWarning,
    stacklevel=2,
)
```

```typescript
// TypeScript
/** @deprecated Use `transform()` instead. Will be removed in 2.0.0. */
export function processData(input: Data): Result {
    console.warn("processData() is deprecated, use transform() instead.");
    return transform(input);
}
```

```rust
// Rust
#[deprecated(since = "1.5.0", note = "Use `transform()` instead")]
pub fn process_data(input: &Data) -> Result { ... }
```

```php
// PHP
#[\Deprecated(message: "Use transform() instead", since: "1.5.0")]
function process_data(array $input): array { ... }
```

**Phase 2 — Remove (MAJOR release):** Delete the deprecated code. Users who heeded the warnings have already migrated. Users who didn't will see clear errors, and the previous deprecation warnings told them exactly what to do.

This cycle costs you very little effort and earns enormous goodwill from anyone depending on your code.

---

## 8. Decision Guide: What Kind of Bump?

When you're about to release and aren't sure what to bump, work through these questions:

**Did you only fix bugs or improve internals, with no visible behavior change?**
→ PATCH.

**Did you add something new (function, component, endpoint, CLI flag) without changing anything existing?**
→ MINOR.

**Did you change or remove something that existing consumers rely on?**
→ MAJOR. Even if the change feels small, if it can break someone's code, it's breaking.

**Did you drop support for a runtime or platform version?**
→ MAJOR. Someone's CI might still run on that version.

**Did you change a default value?**
→ Usually MAJOR. Anyone relying on the old default will see different behavior without changing their code. If the old default was clearly a bug (e.g., a timeout of 0 seconds), it can be argued as PATCH, but err toward MAJOR.

**Are you still in 0.x?**
→ You have more freedom. Breaking changes can go in 0.MINOR bumps. But document them clearly in the changelog.

---

## 9. Common Mistakes

**Version string in multiple files.** If your version appears in `pyproject.toml`, `__init__.py`, `package.json`, and your README badge, they *will* drift apart. Use a single source (the manifest file or a git tag) and derive everywhere else.

**Rushing to 1.0.0.** A premature 1.0.0 forces you to either make a lot of MAJOR bumps (confusing) or avoid necessary breaking changes (stagnating). Stay at 0.x until the design has settled.

**Treating MAJOR bumps as scary.** Going from 4.0.0 to 5.0.0 is not a big deal if the breaking change is small and well-documented. MAJOR doesn't mean "rewrite" — it means "something changed that you should check." Libraries like React and Node.js bump MAJOR regularly for relatively focused changes.

**Forgetting the changelog.** A version number tells users *that* something changed. The changelog tells them *what*. Without it, users have to read your commit log to decide whether to upgrade, and most simply won't bother.

**Silent breaking changes in PATCH releases.** This destroys trust faster than anything else. If you're unsure whether a change is breaking, assume it is and bump accordingly. Being overly cautious with version bumps is far better than being insufficiently cautious.

---

## Further Reading

- [Semantic Versioning 2.0.0](https://semver.org) — the formal specification.
- [Keep a Changelog](https://keepachangelog.com) — the changelog format standard.
- [PEP 440](https://peps.python.org/pep-0440/) — Python's version identification spec (diverges from SemVer syntax in some details).
- [npm semver](https://docs.npmjs.com/about-semantic-versioning) — how npm interprets version ranges.
- [Cargo SemVer Compatibility](https://doc.rust-lang.org/cargo/reference/semver.html) — Rust's detailed guide on what constitutes a breaking change in Rust specifically.
