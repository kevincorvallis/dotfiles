# Zoxide - Smart Navigation

> [Zoxide](https://github.com/ajeetdsouza/zoxide) is an intelligent `cd` replacement that learns your most-used directories.

## How It Works

Zoxide maintains a database of directories you visit. The more you visit a directory, the higher its "frecency" score (frequency + recency). When you type `z <partial-name>`, zoxide jumps to the best match.

## Commands

| Command | What It Does | Example |
|---------|-------------|---------|
| `z <query>` | Jump to best-matching directory | `z proj` -> `~/projects` |
| `z <query1> <query2>` | Match with multiple keywords | `z proj front` -> `~/projects/frontend` |
| `zi` | Interactive selection with fzf | Opens fuzzy finder with all known directories |
| `z -` | Go to previous directory | Same as `cd -` |
| `z ..` | Go up one directory | Same as `cd ..` |

## Examples

```bash
# First, use cd normally to build up the database
cd ~/projects/my-app/src/components

# Later, from anywhere:
z components    # Jumps to ~/projects/my-app/src/components
z my-app        # Jumps to ~/projects/my-app
z proj          # Jumps to ~/projects

# Multiple keywords narrow the search
z my comp       # Jumps to ~/projects/my-app/src/components

# Interactive mode (requires fzf)
zi              # Full-screen fuzzy finder of all known directories
```

## The Database

Zoxide stores its database at `~/.local/share/zoxide/db.zo`. You can inspect it:
```bash
zoxide query --list          # List all known directories
zoxide query --list --score  # List with frecency scores
```

## Tips

- Zoxide only tracks directories you actually `cd` (or `z`) into
- It automatically removes directories that no longer exist
- The more you visit a directory, the less you need to type
- Combine with `zi` (interactive mode) when you're not sure of the name

## Tags
#dotfiles #zoxide #navigation #shell #tools
