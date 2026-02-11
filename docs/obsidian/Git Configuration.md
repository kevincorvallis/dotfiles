# Git Configuration

> Git settings and aliases in `~/.gitconfig`. Includes git-delta for beautiful diffs, GPG signing, and dozens of shortcuts.

## Git Aliases

### Everyday Commands
| Alias | Full Command | What It Does |
|-------|-------------|-------------|
| `git s` | `git status -s` | Short status (compact view) |
| `git l` | `git log --oneline -n 20 --graph` | Pretty log of last 20 commits with graph |
| `git d` | `git diff --patch-with-stat` | Detailed diff with file stats |
| `git di 3` | `git diff HEAD~3` | Diff between 3 commits ago and now |
| `git p` | `git pull --recurse-submodules` | Pull including submodule updates |
| `git c <url>` | `git clone --recursive` | Clone with all submodules |

### Branching
| Alias | What It Does |
|-------|-------------|
| `git go feature-x` | Switch to branch (creates it if it doesn't exist) |
| `git tags` | List all tags |
| `git branches` | List all branches (local + remote) |
| `git remotes` | List all remotes with URLs |
| `git dm` | Delete all branches already merged into current branch |

### Committing
| Alias | What It Does |
|-------|-------------|
| `git ca` | Stage all changes and commit (opens editor) |
| `git amend` | Add staged files to the last commit (keeps message) |
| `git credit "Name" "email"` | Change the author on the last commit |
| `git reb 5` | Interactive rebase of the last 5 commits |

### Searching
| Alias | What It Does | Example |
|-------|-------------|---------|
| `git fc "pattern"` | Find commits that changed a string in source code | `git fc "TODO"` |
| `git fm "message"` | Find commits by commit message | `git fm "fix login"` |
| `git fb <commit>` | Find branches containing a specific commit | |
| `git ft <commit>` | Find tags containing a specific commit | |

### Info
| Alias | What It Does |
|-------|-------------|
| `git aliases` | List all configured git aliases |
| `git contributors` | List contributors sorted by commit count |
| `git whoami` | Show current user email |

## Core Settings

### git-delta (Beautiful Diffs)
All diffs (git diff, git log -p, git show) are rendered through [delta](https://github.com/dandavies00/delta), which provides:
- Syntax highlighting in diffs
- Line numbers
- Word-level diff highlighting
- Solarized Dark theme

### GPG Signing
All commits are signed with GPG by default (`commit.gpgsign = true`). You need to set up your GPG key:
```bash
# Generate a key
gpg --full-generate-key

# List your key
gpg --list-secret-keys --keyid-format=long

# Tell git to use it
git config --global user.signingkey YOUR_KEY_ID
```

### URL Shorthands
| Shorthand | Expands To | Usage |
|-----------|-----------|-------|
| `gh:user/repo` | `git@github.com:user/repo` | `git clone gh:kevincorvallis/dotfiles` |
| `github:user/repo` | `git://github.com/user/repo` | Read-only clone |
| `gst:id` | `git@gist.github.com:id` | Clone a gist (push) |
| `gist:id` | `git://gist.github.com/id` | Clone a gist (read-only) |

### Other Settings
| Setting | Value | Purpose |
|---------|-------|---------|
| `push.default` | `simple` | Only push current branch |
| `push.followTags` | `true` | Push relevant tags with branches |
| `merge.conflictstyle` | `diff3` | Show original code in merge conflicts |
| `help.autocorrect` | `1` | Auto-correct typos after 0.1s |
| `init.defaultBranch` | `main` | New repos use `main` instead of `master` |
| `core.untrackedCache` | `true` | Speed up `git status` |

## Global .gitignore
Automatically ignored in all repos:
- `.DS_Store`, `._*` (macOS metadata)
- `Desktop.ini`, `Thumbs.db` (Windows metadata)
- `.Spotlight-V100`, `.Trashes` (macOS system)
- `*.pyc` (Python bytecode)

## Tags
#dotfiles #git #configuration #aliases
