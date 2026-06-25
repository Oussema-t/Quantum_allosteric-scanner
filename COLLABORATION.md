# COLLABORATION.md — working together with Claude Code, kept in sync

Multiple people work on this **same** repo (frontend + backend) using Claude Code. This
file is the team workflow so nobody's work is lost and **anyone (or their agent) can see
exactly what changed since they last worked.**

The mechanism is simple: **git history + a dated change log + the synced docs**
(`CLAUDE.md`, `ARCHITECTURE.md`, `SOFTWARE.md`). Follow the loop below every session.

---

## One-time setup (each person)
```bash
git clone git@github.com:Oussema-t/Quantum_allosteric-scanner.git
cd Quantum_allosteric-scanner
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```
- Add your SSH key to GitHub (Settings → SSH keys) so `git push` works.
- Open the folder with **Claude Code**. It auto-loads `CLAUDE.md` for instant context.

---

## Every session — the loop

### 1. Start: pull + catch up on what changed
```bash
git pull --rebase origin main
git log --oneline -20                      # recent commits (who did what)
git log --since="5 days ago" --pretty="%h %an %ad %s" --date=short
```
Then tell your agent:
> "Read CLAUDE.md, the ARCHITECTURE.md change log, and `git log` since I last worked.
>  Summarize what changed and re-read any modified files before we start."

The agent **reads the actual current code from the working tree** (so it always sees the
latest SW), and the **change log + git log** tell it what's *new* since last time. That is
how, when you return, your agent knows the modifications your colleague made on previous
days — it reads the updated files + the dated change-log entries.

### 2. Work via the agent
Make changes as usual. Keep commits small and focused (easier to merge, easier to review).

### 3. Before committing — update the docs IN THE SAME COMMIT
This is the rule that keeps everyone synced. When you change modules / endpoints /
response fields / frontend behavior / conventions:
- update **`ARCHITECTURE.md`** — add ONE change-log line at the top (newest first), format:
  ```
  - YYYY-MM-DD · <your-name> · <one-line summary of the change>
  ```
- update **`SOFTWARE.md`** if an endpoint/response/feature changed.
- (`CLAUDE.md` rarely changes.)

### 4. Push (fetch + rebase first — avoids clobbering a teammate)
```bash
git fetch origin main
git rebase origin/main          # replay your work on top of theirs
# resolve any conflict, then:
git push origin main            # auto-deploys to Render (~2–3 min)
```
If `git push` is rejected, someone pushed first → `git fetch` + `git rebase` again.

---

## Golden rules
1. **Always `git pull --rebase` before starting**, and **fetch + rebase before pushing.**
2. **One change-log line per change**, dated + signed, newest first.
3. **Keep `ARCHITECTURE.md` + `SOFTWARE.md` updated in the same commit** as the code.
4. **Small commits** with clear messages (imperative subject + bullet body).
5. Try to avoid two people editing the **same file** at the same time; coordinate areas
   (e.g. one on `frontend/app.js`, one on `backend/analysis.py`).
6. The repo stays **private**; collaborators have access via GitHub Settings → Collaborators.

## "I've been away — what changed?"
```bash
git pull --rebase origin main
git log --since="2026-06-20" --pretty="%h %an %ad %s" --date=short   # commits since a date
git diff <old-commit>..HEAD --stat                                    # files changed
```
…then ask your agent to read the changed files + the new change-log entries and brief you.
