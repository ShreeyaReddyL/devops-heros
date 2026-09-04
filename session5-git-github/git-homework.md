# Git/GitHub — Homework

## Task 1: `git commit -a -m` vs `git commit -m`

### Key Difference

| Command | What It Does |
|---------|-------------|
| `git commit -m "msg"` | Commits only the files that have been explicitly staged with `git add` |
| `git commit -a -m "msg"` | Automatically stages **all modified tracked files** and commits them — skips the `git add` step |

> **Important:** `git commit -a -m` does **NOT** stage untracked (new) files. You still need `git add` for brand-new files.

### Practice & Observations

```bash
# Setup a test repo
shreeya@devbox:~/git-test$ git init
Initialized empty Git repository in /home/shreeya/git-test/.git/

# Create and commit a file normally
shreeya@devbox:~/git-test$ echo "first version" > notes.txt
shreeya@devbox:~/git-test$ git add notes.txt
shreeya@devbox:~/git-test$ git commit -m "add notes.txt"
[main (root-commit) a1b2c3d] add notes.txt
 1 file changed, 1 insertion(+)

# --- Test 1: Modify a tracked file and try commit -m without git add ---
shreeya@devbox:~/git-test$ echo "updated content" >> notes.txt
shreeya@devbox:~/git-test$ git commit -m "update notes"
On branch main
Changes not staged for commit:
    modified:   notes.txt
no changes added to commit

# ❌ Fails! The modification wasn't staged.

# --- Test 2: Same scenario but with -a flag ---
shreeya@devbox:~/git-test$ git commit -a -m "update notes with -a flag"
[main e4f5g6h] update notes with -a flag
 1 file changed, 1 insertion(+)

# ✅ Works! -a auto-staged the tracked file's changes.

# --- Test 3: New untracked file with -a ---
shreeya@devbox:~/git-test$ echo "brand new file" > extra.txt
shreeya@devbox:~/git-test$ git commit -a -m "try to add extra.txt"
On branch main
Untracked files:
    extra.txt
nothing added to commit but untracked files present

# ❌ Fails! -a does not pick up untracked files.

# --- Fix: Must use git add for new files ---
shreeya@devbox:~/git-test$ git add extra.txt
shreeya@devbox:~/git-test$ git commit -m "add extra.txt properly"
[main i7j8k9l] add extra.txt properly
 1 file changed, 1 insertion(+)
```

### Summary

- Use `git commit -m` when you want precise control over what gets committed (after staging specific files with `git add`)
- Use `git commit -a -m` as a shortcut when you want to commit all changes to **already-tracked** files without running `git add` each time
- New files always need `git add` first — the `-a` flag only helps with modifications to existing tracked files

---

## Task 2: Git Cherry-Pick

### What Is Cherry-Pick?

`git cherry-pick` lets you apply a specific commit from one branch onto another — without merging the entire branch. Useful when you only need one particular fix or feature from a branch.

### Step-by-Step Walkthrough

#### 1. Create commits on `main`

```bash
shreeya@devbox:~/cherry-demo$ git init
Initialized empty Git repository in /home/shreeya/cherry-demo/.git/

shreeya@devbox:~/cherry-demo$ echo "project setup" > README.md
shreeya@devbox:~/cherry-demo$ git add . && git commit -m "initial project setup"
[main (root-commit) aa11bb2] initial project setup

shreeya@devbox:~/cherry-demo$ echo "config file" > config.yml
shreeya@devbox:~/cherry-demo$ git add . && git commit -m "add config file"
[main cc33dd4] add config file

shreeya@devbox:~/cherry-demo$ echo "logging module" > logger.py
shreeya@devbox:~/cherry-demo$ git add . && git commit -m "add logging module"
[main ee55ff6] add logging module

shreeya@devbox:~/cherry-demo$ echo "database setup" > db.py
shreeya@devbox:~/cherry-demo$ git add . && git commit -m "add database layer"
[main gg77hh8] add database layer
```

#### 2. View commits on main

```bash
shreeya@devbox:~/cherry-demo$ git log --oneline
gg77hh8 (HEAD -> main) add database layer
ee55ff6 add logging module
cc33dd4 add config file
aa11bb2 initial project setup
```

#### 3. Create a new branch and add commits

```bash
shreeya@devbox:~/cherry-demo$ git checkout -b feature-login
Switched to a new branch 'feature-login'

shreeya@devbox:~/cherry-demo$ echo "login form" > login.html
shreeya@devbox:~/cherry-demo$ git add . && git commit -m "create login form"
[feature-login ii99jj0] create login form

shreeya@devbox:~/cherry-demo$ echo "auth validation" > auth.py
shreeya@devbox:~/cherry-demo$ git add . && git commit -m "add authentication logic"
[feature-login kk11ll2] add authentication logic

shreeya@devbox:~/cherry-demo$ echo "session handler" > session.py
shreeya@devbox:~/cherry-demo$ git add . && git commit -m "implement session management"
[feature-login mm33nn4] implement session management
```

#### 4. Identify the commit to cherry-pick

```bash
shreeya@devbox:~/cherry-demo$ git log --oneline
mm33nn4 (HEAD -> feature-login) implement session management
kk11ll2 add authentication logic
ii99jj0 create login form
gg77hh8 (main) add database layer
ee55ff6 add logging module
cc33dd4 add config file
aa11bb2 initial project setup
```

Let's say we want to bring **only** the "add authentication logic" commit (`kk11ll2`) into `main`.

#### 5. Switch to main and cherry-pick

```bash
shreeya@devbox:~/cherry-demo$ git checkout main
Switched to branch 'main'

shreeya@devbox:~/cherry-demo$ git cherry-pick kk11ll2
[main oo55pp6] add authentication logic
 Date: Wed Sep 3 16:42:30 2026 +0530
 1 file changed, 1 insertion(+)
 create mode 100644 auth.py
```

#### 6. Verify the cherry-picked commit is on main

```bash
shreeya@devbox:~/cherry-demo$ git log --oneline
oo55pp6 (HEAD -> main) add authentication logic
gg77hh8 add database layer
ee55ff6 add logging module
cc33dd4 add config file
aa11bb2 initial project setup

shreeya@devbox:~/cherry-demo$ ls
README.md  config.yml  logger.py  db.py  auth.py

# auth.py is now in main, but login.html and session.py are NOT
# because we only cherry-picked the one specific commit
```

### Key Observations

- Cherry-pick creates a **new commit** on the target branch (with a new hash `oo55pp6`) even though the content is the same as the original commit
- Only the changes from that one specific commit are applied — other commits from the feature branch are not included
- Useful for hotfixes: if a bugfix exists in a feature branch, you can cherry-pick just that fix into `main` or a release branch
