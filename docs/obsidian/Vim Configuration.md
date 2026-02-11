# Vim Configuration

> Vim settings in `~/.vimrc` with Solarized Dark theme. Focused on readability and efficient editing.

## Theme
- **Solarized Dark** color scheme (`.vim/colors/solarized.vim`)
- Transparent terminal background support (`solarized_termtrans=1`)

## Key Settings

### Editor Behavior
| Setting | What It Does |
|---------|-------------|
| `nocompatible` | Use Vim features (not vi compatibility) |
| `clipboard=unnamed` | Yank/paste uses system clipboard |
| `wildmenu` | Visual tab completion for commands |
| `backspace=indent,eol,start` | Backspace works everywhere in insert mode |
| `encoding=utf-8 nobomb` | UTF-8 without byte-order mark |
| `mouse=a` | Mouse works in all modes |

### Display
| Setting | What It Does |
|---------|-------------|
| `number` | Show line numbers |
| `relativenumber` | Line numbers relative to cursor (great for `5j`, `10k`) |
| `cursorline` | Highlight the line the cursor is on |
| `tabstop=2` | Tabs display as 2 spaces |
| `list` + `lcs=...` | Show invisible characters (tabs, trailing spaces, EOL) |
| `scrolloff=3` | Keep 3 lines visible above/below cursor |
| `title` | Show filename in terminal titlebar |
| `laststatus=2` | Always show status line |

### Search
| Setting | What It Does |
|---------|-------------|
| `hlsearch` | Highlight all search matches |
| `incsearch` | Highlight matches as you type |
| `ignorecase` | Case-insensitive search |
| `gdefault` | Replace all occurrences by default (no `/g` needed) |

### File Handling
| Setting | What It Does |
|---------|-------------|
| `backupdir=~/.vim/backups` | Centralized backup files |
| `directory=~/.vim/swaps` | Centralized swap files |
| `undodir=~/.vim/undo` | Persistent undo history across sessions |

## Custom Keybindings

Leader key is `,` (comma).

| Binding | What It Does |
|---------|-------------|
| `,ss` | Strip trailing whitespace from entire file |
| `,W` | Save file as root (sudo write) |

## File Type Detection
| Extension | Treated As |
|-----------|-----------|
| `.json` | JSON (native syntax) |
| `.md` | Markdown |

## GUI Vim (.gvimrc)
If using MacVim or gVim:
- Font: 14pt Monaco
- No blinking cursor
- Solarized Dark theme

## Tags
#dotfiles #vim #editor #configuration
