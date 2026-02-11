# tmux Configuration

> Terminal multiplexer configured in `~/.tmux.conf`. Run multiple terminal sessions in one window, detach and reattach.

## What tmux Does

tmux lets you:
- **Split panes** - multiple terminals side by side
- **Multiple windows** - tabs within a single terminal
- **Detach/reattach** - disconnect from a session and reconnect later (great for SSH)
- **Persistent sessions** - processes keep running even if you close the terminal

## Your Configuration

| Setting | Value | What It Does |
|---------|-------|-------------|
| Prefix key | `Ctrl+A` | Changed from default `Ctrl+B` (easier to reach) |
| Key bindings | Vi mode | Navigate panes with h/j/k/l |
| Reload config | `Ctrl+A R` | Reload .tmux.conf without restarting |

## Essential Commands

### Sessions
| Command | What It Does |
|---------|-------------|
| `tmux` | Start a new session |
| `tmux new -s work` | Start a named session |
| `Ctrl+A d` | Detach from session |
| `tmux attach -t work` | Reattach to a session |
| `tmux ls` | List all sessions |

### Windows (tabs)
| Command | What It Does |
|---------|-------------|
| `Ctrl+A c` | Create new window |
| `Ctrl+A n` | Next window |
| `Ctrl+A p` | Previous window |
| `Ctrl+A 0-9` | Switch to window by number |
| `Ctrl+A ,` | Rename current window |

### Panes (splits)
| Command | What It Does |
|---------|-------------|
| `Ctrl+A %` | Split horizontally |
| `Ctrl+A "` | Split vertically |
| `Ctrl+A arrow` | Navigate between panes |
| `Ctrl+A x` | Close current pane |
| `Ctrl+A z` | Zoom/unzoom current pane (fullscreen toggle) |

## Tags
#dotfiles #tmux #terminal #multiplexer
