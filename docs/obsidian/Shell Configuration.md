# Shell Configuration

> How the shell initialization chain works, including `.bash_profile`, `.zshrc`, `.exports`, `.inputrc`, and tool integrations.

## Shell Startup Chain

### For Zsh (macOS default since Catalina)
```
~/.zshrc
  -> sources ~/.bash_profile
       -> sources ~/.path          (custom PATH)
       -> sources ~/.exports       (env vars + starship/zoxide/atuin for bash)
       -> sources ~/.aliases       (command shortcuts)
       -> sources ~/.functions     (shell functions)
       -> sources ~/.extra         (private, not committed)
       -> sources ~/.bash_prompt   (ONLY if starship not installed)
  -> initializes starship for zsh  (overrides bash init)
  -> initializes zoxide for zsh
  -> initializes atuin for zsh
```

### For Bash
```
~/.bashrc
  -> sources ~/.bash_profile (if interactive shell)
       -> same chain as above
       -> starship/zoxide/atuin initialized in .exports (bash mode)
```

## .exports - Environment Variables

### Core Settings
| Variable | Value | Purpose |
|----------|-------|---------|
| `EDITOR` | `vim` | Default text editor for git commit messages, crontab, etc. |
| `HISTSIZE` | `32768` | Keep 32K commands in history (default is 500) |
| `HISTCONTROL` | `ignoreboth` | Don't save duplicate commands or commands starting with space |
| `LANG` / `LC_ALL` | `en_US.UTF-8` | US English, UTF-8 everywhere |
| `BASH_SILENCE_DEPRECATION_WARNING` | `1` | Suppress "default shell is now zsh" notice |
| `ICLOUD` | `~/Library/Mobile Documents/com~apple~CloudDocs` | iCloud Drive path for aliases |
| `GPG_TTY` | `$(tty)` | Required for GPG signing to work in terminal |

### Tool Configurations
| Variable | Purpose |
|----------|---------|
| `FZF_DEFAULT_COMMAND` | Makes fzf use `fd` to find files (respects .gitignore, shows hidden) |
| `FZF_CTRL_T_COMMAND` | Same as above for Ctrl+T file picker |
| `FZF_ALT_C_COMMAND` | Makes Alt+C directory picker use `fd` |
| `BAT_THEME` | Sets bat to "Solarized (dark)" theme |

### Node.js
| Variable | Purpose |
|----------|---------|
| `NODE_REPL_HISTORY` | Saves Node REPL history to `~/.node_history` |
| `NODE_REPL_HISTORY_SIZE` | Keeps 32K entries |
| `NODE_REPL_MODE` | Sloppy mode (matches browser behavior) |

### Python
| Variable | Purpose |
|----------|---------|
| `PYTHONIOENCODING` | Forces UTF-8 for all Python I/O |

## .inputrc - Readline Settings

Controls tab completion and keyboard behavior in bash, Python REPL, and other readline-based tools.

| Setting | What It Does |
|---------|-------------|
| Case-insensitive completion | `cd doc` matches `Documents` |
| Show all on ambiguous | Shows all matches immediately instead of beeping |
| Symlink trailing slash | Directories get `/` after completion |
| Up/Down history search | Type partial command, press Up to find matching history |
| Skip hidden files | Don't tab-complete `.hidden` files unless you type `.` |
| UTF-8 support | Proper handling of international characters |

## .bash_profile - Shell Options

| Option | What It Does |
|--------|-------------|
| `nocaseglob` | `*.TXT` matches `file.txt` |
| `histappend` | Appends to history file instead of overwriting |
| `cdspell` | Auto-corrects typos in `cd` paths |
| `autocd` | Type a directory name to cd into it (no `cd` needed) |
| `globstar` | `**/*.py` recursively matches all Python files |

## Modern Tool Integrations

### Starship Prompt
Cross-shell prompt that automatically shows relevant context. See [[Starship Prompt]].

### Zoxide
Smart `cd` replacement. Type `z <partial-name>` to jump to frequently-used directories. See [[Zoxide - Smart Navigation]].

### Atuin
Shell history stored in SQLite. Press `Ctrl+R` for full-screen searchable history. See [[Atuin - Shell History]].

## Tags
#dotfiles #shell #zsh #bash #configuration
