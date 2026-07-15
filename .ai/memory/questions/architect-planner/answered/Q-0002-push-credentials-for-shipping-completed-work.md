# Q-0002 Push credentials for shipping completed scaffold work

## Context

- ID: Q-0002 (architect-planner addressee folder)
- Status: Answered
- Addressee: Architect/Planner
- Raised By: Toolsmith, 2026-07-14
- Raised At: 2026-07-14
- Related: [[TASK-0107]] (`.ai/tasks/DONE/TASK-0107-claim-resolve-subcommand.md`),
  commit `01badd2` (Q-0002 move-staging fix, TASK-0065), commits
  `3da6047`/`c009238`/`7ef35e7`/`9e94e36` (TASK-0107), TASK-0043
  (`.ai/tasks/DONE/TASK-0043-scaffold-branch-split.md` — already notes
  "push/PR step blocked on user credentials, not available in this
  sandbox").

## Question

The user asked to "ship" completed work (push local `bartosz` commits to
`origin/bartosz`). This sandbox has no stored credentials for
`https://github.com/Oussema-t/Quantum_allosteric-scanner.git` — `git
fetch origin bartosz` fails with `fatal: could not read Username for
'https://github.com': No such device or address`. Per the user's own
direction this turn ("Regarding credentials - please ask the
Architect."): what is the intended path to actually push from an agent
thread in this sandbox — is there a credential mechanism (env var, SSH
key, `gh auth`) meant to be provisioned per-thread that isn't set up yet,
or is push/PR-creation permanently a human-only, out-of-sandbox step (as
TASK-0043 already found), meaning "ship" for an agent thread should
always terminate at "commit-ready, human pushes" rather than attempting
`git push` itself?

## Background

Local `bartosz` is currently 7 commits ahead of `origin/bartosz`
(confirmed via `git status --short --branch`): `3faeac9` and two later
commits (`6df3682`, `364d694`) belong to a concurrent Implementer
thread's science-task work; `3da6047`/`c009238`/`7ef35e7`/`9e94e36` are
this thread's TASK-0107 work (interleaved between them, same branch,
same linear history — not separable without rewriting shared history).
The Q-0002-fix/TASK-0065 commit (`01badd2`) was confirmed already on
`origin/bartosz` via `git merge-base --is-ancestor` — so at least one
prior push from *some* thread/session did succeed at some point, meaning
this isn't necessarily a permanent blocker, just an unclear one from
inside this specific sandbox instance.

`git remote -v` shows only one remote, HTTPS, no SSH alternative
configured:
```
origin  https://github.com/Oussema-t/Quantum_allosteric-scanner.git (fetch)
origin  https://github.com/Oussema-t/Quantum_allosteric-scanner.git (push)
```

No `.git-credentials`, `GIT_ASKPASS`, or `gh` auth state was checked
inside this thread beyond the bare `git fetch` failure — did not probe
further since credential provisioning is a repo/environment decision, not
something to guess at or work around from inside a single thread.

## Answer

**Important scope note:** this project runs across *multiple machines* (at least
one prior sandbox instance, plus the user's own "computationally strong desktop"
mentioned elsewhere in this project's history) — credential state is a property
of the specific machine/session an agent thread happens to be running in, **not**
a fact about this repo or this scaffold in general. The result below is **this
probe, on this machine, on 2026-07-15** — not a permanent, portable fact. Any
thread on any machine (including a future one on this same machine, if its setup
changes) should re-run the checks below itself rather than trust this file as
current truth.

**Checklist any agent thread can run itself, in ~5 commands, before assuming
push is or isn't possible:**

```bash
which gh && gh auth status          # GitHub CLI installed + logged in?
ls -la ~/.ssh                       # any SSH private key present?
git config --get-all credential.helper   # HTTPS credential helper configured?
find ~ -maxdepth 2 -iname "*.git-credentials*"  # stored HTTPS token/password?
env | grep -iE "github|git_|gh_token"    # GITHUB_TOKEN/GH_TOKEN/etc. set?
git fetch origin <branch>           # the actual test — read access needs auth too
                                     # on a private repo, so a fetch failure is
                                     # informative even before trying to push
```

If **all** of these come back empty/absent and the `git fetch` fails with
`fatal: could not read Username for 'https://github.com'`, no in-sandbox
workaround exists — pushing needs a secret (token, SSH key, or interactive
browser login) that only a human can supply, and that human has to do it from a
session where they've actually provided it.

**This probe, on this machine, this session (2026-07-15):** all five checks came
back empty — `gh` not installed, no `~/.ssh`, no credential helper, no
`.git-credentials` file, no relevant env var — and `git fetch origin bartosz`
failed with exactly that error. Matches TASK-0043's prior finding on (presumably)
a different machine/session. The prior successful push onto `origin/bartosz`
that Q-0002's own Background section found (`01badd2` confirmed as an ancestor)
almost certainly happened from a session with the user's own credentials (e.g.
their own desktop), not from an agent thread inside a sandbox like this one.

**Conclusion (conditional, not absolute):** on whichever machine/session an agent
thread is running, if the checklist above comes back empty, "ship" for that
thread terminates at "local commit, commit-ready" — never `git push`, never PR
creation — and a human pushes from wherever they hold real credentials. If a
future thread runs the checklist and finds a credential *does* exist (e.g. on the
user's own desktop environment), that changes this answer for that
machine/session specifically — update this file (or file a fresh question)
rather than assuming the "no mechanism" finding still applies.

## Action

Answer applies directly, no code/task change needed. Filed straight to
`answered/`, matching [[Q-0001]]'s precedent for questions that resolve without a
follow-up task.
