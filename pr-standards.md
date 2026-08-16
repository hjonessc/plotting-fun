# PR Standards

Basic conventions for pull requests. Flesh this out as preferences solidify.

---

## Branch Naming

```
feature/short-description
fix/short-description
chore/short-description
```

---

## PR Title

Follow the same prefix as the branch: `feat: add login screen`, `fix: crash on empty state`, `chore: update dependencies`.

Keep titles under ~60 characters. No period at the end.

---

## PR Description

Include at minimum:
- **What changed** — one or two sentences
- **Why** — the motivation or issue it addresses
- **How to test** — what to check to verify it works (even if just "run tests")

Template:
```
## What
[description]

## Why
[motivation]

## Testing
[how to verify]
```

---

## When to Open a Draft vs. Ready PR

- **Draft**: work in progress, not ready for review, but want CI to run or want visibility
- **Ready**: complete and tested, waiting for review or self-review before merge

---

## Merge Strategy

- Prefer **squash merge** for feature branches to keep main history clean
- Use **merge commit** only if preserving branch history matters (rare)
- Delete branch after merge

---

## What Dispatch Can Do Without Asking

- Open a draft PR
- Push commits to an existing branch
- Add a reviewer
- Summarize a PR for review

## What Dispatch Should Confirm Before Doing

- Merging to main
- Force pushing
- Closing a PR without merging
- Deleting a branch that isn't merged
