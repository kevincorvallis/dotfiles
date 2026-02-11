# Brewfile - Package Management

> Declarative package manifest for [Homebrew](https://brew.sh/). Run `brew bundle --file=Brewfile` to install everything.

## How It Works

The `Brewfile` lists all packages to install via Homebrew. It's like a `package.json` for your Mac. Run `brew bundle` and every tool gets installed automatically.

```bash
# Install everything
brew bundle --file=Brewfile

# Check what's missing
brew bundle check --file=Brewfile

# Clean up packages not in Brewfile
brew bundle cleanup --file=Brewfile
```

## Package Reference

### Core Utilities
| Package | What It Does | When You'd Use It |
|---------|-------------|-------------------|
| `coreutils` | GNU core utilities (replaces BSD versions) | Get Linux-compatible `ls`, `cp`, `mv` etc. with more options |
| `moreutils` | Extra Unix tools (`sponge`, `ts`, `parallel`) | `sponge` lets you write to a file you're reading from |
| `findutils` | GNU `find`, `locate`, `xargs` | More powerful file searching than BSD find |
| `gnu-sed` | GNU sed (stream editor) | Linux-compatible sed with `-i` flag that works properly |
| `bash` | Latest Bash (macOS ships old 3.2) | Bash 5 features: associative arrays, `&>>` redirect, `**` glob |
| `bash-completion@2` | Tab completion for Bash commands | Auto-complete git branches, brew commands, ssh hosts |
| `wget` | Download files from the web | `wget -r` for recursive downloads, resumes interrupted transfers |
| `gnupg` | GPG encryption/signing | Sign git commits, encrypt files, manage PGP keys |
| `vim` | Latest Vim (macOS ships older version) | Clipboard support, latest syntax highlighting, bug fixes |
| `grep` | GNU grep (faster, more features) | `-P` for Perl regex, `--include` for file filtering |
| `openssh` | Latest OpenSSH client/server | Newer key types, security fixes |
| `gmp` | GNU Multiple Precision arithmetic | Required by some crypto/math tools |

### Git
| Package | What It Does | When You'd Use It |
|---------|-------------|-------------------|
| `git` | Latest Git | Newer features like `git switch`, `git restore`, sparse checkout |
| `git-lfs` | Git Large File Storage | Track large files (images, videos, datasets) without bloating repo |

### Modern CLI Tools
| Package | Replaces | What It Does | Key Commands |
|---------|----------|-------------|-------------|
| `gh` | GitHub web UI | GitHub CLI - PRs, issues, repos from terminal | `gh pr create`, `gh issue list`, `gh repo clone` |
| `fzf` | manual searching | Fuzzy finder for files, history, git branches | `Ctrl+R` (history), `Ctrl+T` (files), `Alt+C` (cd) |
| `ripgrep` | `grep` | 10-100x faster grep, respects .gitignore | `rg "pattern"`, `rg -t py "class"` |
| `bat` | `cat` | Cat with syntax highlighting and line numbers | `bat file.py`, `bat --diff file.py` |
| `eza` | `ls` | Modern ls with git status, icons, tree view | `eza -la`, `eza --tree --level=2` |
| `git-delta` | `diff` | Beautiful side-by-side git diffs | Automatic - used by git diff/log |
| `fd` | `find` | Fast, user-friendly find | `fd "*.py"`, `fd -H -e json` |
| `tldr` | `man` | Simplified, example-based man pages | `tldr tar`, `tldr git-rebase` |
| `htop` | `top` | Interactive process viewer with colors | `htop` then F6 to sort, F9 to kill |
| `jq` | manual JSON parsing | JSON processor for the command line | `curl api.com \| jq '.data[0].name'` |
| `starship` | custom bash prompt | Fast cross-shell prompt, auto-detects context | Shows git branch, language versions, cloud profile |
| `zoxide` | `cd` | Smart directory jumper, learns your habits | `z projects` jumps to ~/projects, `zi` for interactive |
| `atuin` | shell history | Shell history in SQLite with search UI | `Ctrl+R` for full-screen history search, optional cross-machine sync |
| `lazygit` | git CLI | Terminal UI for git with keyboard shortcuts | `lg` to launch, visual staging, branch management |

### Utilities
| Package | What It Does | When You'd Use It |
|---------|-------------|-------------------|
| `netpbm` | Image format conversion toolkit | Convert between PBM, PGM, PPM, and other formats |
| `pngcheck` | Validate PNG file integrity | Check if PNG files are corrupted |
| `xpdf` | PDF utilities (pdftotext, pdfinfo) | Extract text from PDFs via command line |
| `xz` | XZ compression (better than gzip) | Decompress `.xz` files, highest compression ratio |
| `gs` (Ghostscript) | PostScript/PDF interpreter | Merge PDFs (`mergepdf` alias), convert PS to PDF |
| `imagemagick` | Image manipulation from CLI | Resize, convert, compose images: `convert img.png -resize 50% small.png` |
| `lua` | Lua programming language | Scripting, Neovim plugins, game dev |
| `lynx` | Text-based web browser | View web pages in terminal, test accessibility |
| `sevenzip` | 7-Zip compression (replaces p7zip) | Handle `.7z` archives: `7zz x archive.7z` |
| `pigz` | Parallel gzip | Multi-core gzip compression (much faster) |
| `pv` | Pipe Viewer | Progress bars for piped commands: `pv bigfile \| gzip > out.gz` |
| `rename` | Batch file renaming | Regex-based rename: `rename 's/\.txt$/.md/' *` |
| `rlwrap` | Readline wrapper | Add history/completion to any REPL |
| `ssh-copy-id` | Copy SSH key to server | `ssh-copy-id user@server` - no more manual key setup |
| `tree` | Directory tree view | `tree -L 2` to see 2 levels deep |
| `vbindiff` | Visual binary diff | Compare binary files side-by-side in terminal |
| `zopfli` | Better gzip compression | Slower but smaller than gzip (good for static assets) |

## Tags
#dotfiles #homebrew #packages #tools
