# Aliases Reference

> Command shortcuts defined in `~/.aliases`. These save keystrokes for common operations.

## Navigation
| Alias | Expands To | What It Does |
|-------|-----------|-------------|
| `..` | `cd ..` | Go up one directory |
| `...` | `cd ../..` | Go up two directories |
| `....` | `cd ../../..` | Go up three directories |
| `.....` | `cd ../../../..` | Go up four directories |
| `~` | `cd ~` | Go to home directory |
| `-` | `cd -` | Go to previous directory |
| `dl` | `cd ~/Downloads` | Jump to Downloads |
| `dt` | `cd ~/Desktop` | Jump to Desktop |
| `p` | `cd ~/projects` | Jump to projects folder |
| `ic` | `cd "$ICLOUD"` | Jump to iCloud Drive |
| `college` | `cd "$ICLOUD/School/College"` | Jump to college folder |
| `sc` | `cd "$ICLOUD/.../super_senior"` | Jump to USC folder |
| `film` | `cd "$ICLOUD/.../film_photography"` | Jump to film photography folder |

> **Tip:** With `zoxide` installed, you can also use `z <partial-name>` to jump to any frequently-visited directory.

## File Listing (via eza)
| Alias | What It Does |
|-------|-------------|
| `ls` | List files (with icons and colors via eza) |
| `l` | Long format listing |
| `la` | Long format, including hidden files |
| `ll` | Same as `la` |
| `lt` | Tree view, 2 levels deep |
| `lsd` | List directories only |

## File Tools
| Alias | Requires | What It Does |
|-------|----------|-------------|
| `cat` | `bat` | Syntax-highlighted file viewer (no paging) |
| `catp` | `bat` | Same but with paging (scrollable) |
| `fdi` | `fd` | fd with `--no-ignore` (searches gitignored files too) |
| `rgi` | `rg` | ripgrep with `--no-ignore` |
| `lg` | `lazygit` | Launch lazygit terminal UI |

## Git
| Alias | What It Does |
|-------|-------------|
| `g` | Shortcut for `git` (e.g., `g status`, `g push`) |

## System
| Alias | What It Does |
|-------|-------------|
| `update` | Update macOS + Homebrew packages in one command |
| `cleanup` | Recursively delete all `.DS_Store` files |
| `emptytrash` | Empty Trash, clear system logs, clear quarantine history |
| `flush` | Flush DNS cache |
| `afk` | Lock the screen |
| `reload` | Reload shell configuration |
| `path` | Print each PATH entry on its own line |
| `stfu` | Mute system volume |
| `pumpitup` | Max system volume |

## Network
| Alias | What It Does |
|-------|-------------|
| `ip` | Show your external/public IP address |
| `localip` | Show your local network IP (en0) |
| `ips` | Show all IP addresses on all interfaces |
| `ifactive` | Show active network interfaces |

## Finder
| Alias | What It Does |
|-------|-------------|
| `show` | Show hidden files in Finder |
| `hide` | Hide hidden files in Finder |
| `showdesktop` | Show desktop icons |
| `hidedesktop` | Hide desktop icons (great for presentations) |

## Spotlight
| Alias | What It Does |
|-------|-------------|
| `spotoff` | Disable Spotlight indexing |
| `spoton` | Enable Spotlight indexing |

## Utilities
| Alias | What It Does |
|-------|-------------|
| `grep` | grep with color output |
| `week` | Show current week number |
| `c` | Trim newlines and copy to clipboard |
| `chrome` | Launch Google Chrome from terminal |
| `canary` | Launch Chrome Canary from terminal |
| `chromekill` | Kill all Chrome renderer processes (free memory) |
| `urlencode` | URL-encode a string |
| `mergepdf` | Merge multiple PDFs into one |
| `map` | `xargs -n1` - apply a command to each line of input |
| `lscleanup` | Clean up "Open With" menu duplicates |
| `edit` | Edit ~/.zshrc in vim |
| `yt` | Download video with yt-dlp (best mp4 quality) |

## Tags
#dotfiles #aliases #commands #shortcuts
