# Editor Settings

> Cross-editor settings in `.editorconfig` and GUI vim settings in `.gvimrc`.

## .editorconfig

[EditorConfig](https://editorconfig.org/) is a standard supported by most editors (VS Code, Vim, Sublime, JetBrains, etc.) that defines consistent formatting rules.

Your settings:

| Setting | Value | What It Does |
|---------|-------|-------------|
| `root` | `true` | This is the top-level config (don't look in parent dirs) |
| `charset` | `utf-8` | All files use UTF-8 encoding |
| `indent_style` | `tab` | Use tabs for indentation |
| `end_of_line` | `lf` | Unix line endings (not Windows CRLF) |
| `insert_final_newline` | `true` | Files always end with a newline |
| `trim_trailing_whitespace` | `true` | Remove trailing spaces on save |

These rules apply to **all files** (`[*]`) in any project containing this `.editorconfig`.

## .gvimrc (GUI Vim)

Settings for MacVim or gVim:
- Font: **14pt Monaco**
- No blinking cursor in normal mode
- Solarized Dark theme
- Better line-height spacing

## .screenrc (GNU Screen)

Legacy terminal multiplexer (superseded by tmux):
- Disables startup message
- 32,000 line scrollback buffer
- UTF-8 enabled

## Tags
#dotfiles #editor #editorconfig #formatting
