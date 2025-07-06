# Complete Guide to Kevin's Dotfiles Commands & Features

This guide explores every command, alias, and feature included in your dotfiles setup. Use this as a reference to discover what's available and how to use it effectively.

## Table of Contents
- [Navigation & Directory Commands](#navigation--directory-commands)
- [File Operations & Management](#file-operations--management)
- [System Information & Utilities](#system-information--utilities)
- [Git & Development Tools](#git--development-tools)
- [Network & Internet Tools](#network--internet-tools)
- [macOS Specific Features](#macos-specific-features)
- [Custom iCloud Integration](#custom-icloud-integration)
- [History & Shell Features](#history--shell-features)
- [Advanced Features](#advanced-features)

---

## Navigation & Directory Commands

### Quick Navigation
```bash
# Navigate up directory levels
..          # Go up one level (same as cd ..)
...         # Go up two levels (same as cd ../..)
....        # Go up three levels
.....       # Go up four levels

# Quick jumps to common directories
~           # Go to home directory
-           # Go to previous directory (same as cd -)
```

### Directory Shortcuts
```bash
# Standard directories
dt          # Desktop
dl          # Downloads  
dw          # Downloads (Kevin's custom)
p           # ~/projects
d           # ~/Documents/Dropbox

# Kevin's Custom iCloud Shortcuts
ic          # iCloud Drive root
college     # iCloud/School/College
sc          # iCloud/School/College/USC/super_senior
film        # iCloud/Personal/photos/film_photography
```

### Directory Stack & Auto-Navigation
```bash
# These work automatically in zsh:
# - Type directory name without 'cd' to navigate
# - Directory stack with pushd/popd integration
# - Auto-completion for directories
```

---

## File Operations & Management

### Enhanced File Listing
```bash
# Basic listing with colors
ls          # List files with colors
l           # Long format listing with colors
la          # Long format including hidden files
lsd         # List only directories

# Examples:
l           # Shows: permissions, owner, size, date, name
la          # Shows: all files including .hidden ones
lsd         # Shows: only directories in current location
```

### File Cleanup & Maintenance
```bash
# Clean up system files
cleanup     # Find and delete all .DS_Store files recursively
            # Usage: cleanup (in any directory)

# Trash management
emptytrash  # Comprehensive trash emptying:
            # - Empty all mounted volume trash cans
            # - Clear ~/.Trash
            # - Clear system logs (speeds up shell startup)
            # - Clear download quarantine history
```

### File Searching & Processing
```bash
# Search and process files
map         # Apply command to each line of input
            # Usage: find . -name "*.txt" | map wc -l

# Find files by type
find . -name "*.DS_Store" | map rm  # Remove all .DS_Store files
```

---

## System Information & Utilities

### System Updates
```bash
update      # Master update command - updates everything:
            # - macOS software updates
            # - Homebrew packages
            # - npm packages globally
            # - Ruby gems
            # - Cleanup afterwards
```

### System Information
```bash
# Date and time
week        # Show current week number
date        # Current date and time

# System monitoring
ifactive    # Show active network interfaces
path        # Display PATH variable (each entry on new line)
```

### System Control
```bash
# Spotlight control
spotoff     # Disable Spotlight indexing
spoton      # Enable Spotlight indexing

# Volume control
stfu        # Mute system volume
pumpitup    # Set volume to maximum

# Screen lock
afk         # Lock screen (Away From Keyboard)
```

---

## Git & Development Tools

### Git Shortcuts
```bash
g           # Git command shortcut
            # Usage: g status, g commit, g push, etc.

# Git information (built into prompt)
# Your prompt automatically shows:
# - Current git branch
# - Repository status
```

### Development Environment
```bash
# Configuration editing
edit        # Edit zsh configuration (~/.zshrc)
            # Opens in vi/vim

# Text editor
s           # Open in Sublime Text
            # Usage: s filename.txt
            # Usage: s .  (open current directory)

# Shell management
reload      # Restart shell with new configuration
            # Useful after editing dotfiles
```

---

## Network & Internet Tools

### IP Address Information
```bash
# Get IP addresses
ip          # Show external/public IP address
localip     # Show local network IP address  
ips         # Show all IP addresses (IPv4 and IPv6)

# Network diagnostics
flush       # Clear DNS cache
            # Useful when having DNS issues
```

### HTTP Testing
```bash
# HTTP method shortcuts for API testing
GET         # Make GET request
POST        # Make POST request  
PUT         # Make PUT request
DELETE      # Make DELETE request
HEAD        # Make HEAD request
OPTIONS     # Make OPTIONS request
TRACE       # Make TRACE request

# Usage examples:
GET https://api.example.com/users
POST https://api.example.com/users -d '{"name":"test"}'
```

### Download Tools
```bash
# YouTube downloading
yt          # Download YouTube videos with optimized settings
            # Usage: yt "https://youtube.com/watch?v=..."
            # Downloads best quality MP4 video + M4A audio
            # Requires: brew install yt-dlp
```

---

## macOS Specific Features

### Finder Management
```bash
# Hidden files control
show        # Show hidden files in Finder
hide        # Hide hidden files in Finder

# Desktop control (great for presentations)
hidedesktop # Hide all desktop icons
showdesktop # Show desktop icons again
```

### System Maintenance
```bash
# LaunchServices cleanup
lscleanup   # Remove duplicates from "Open With" menu
            # Rebuilds LaunchServices database

# Application shortcuts
chrome      # Open Google Chrome
canary      # Open Google Chrome Canary
```

### System Utilities Access
```bash
# Direct access to system tools
plistbuddy  # Access to PlistBuddy utility
airport     # Access to Airport CLI tool
            # Usage: airport -s (scan for networks)
```

---

## Custom iCloud Integration

### Environment Variables
```bash
# Your custom environment
echo $ICLOUD    # Shows: /Users/kevinlee/Library/Mobile Documents/com~apple~CloudDocs
echo $EDITOR    # Shows: vim
```

### iCloud Directory Structure
```bash
# Your iCloud aliases navigate to:
ic          # $ICLOUD/
college     # $ICLOUD/School/College/
sc          # $ICLOUD/School/College/USC/super_senior/
film        # $ICLOUD/Personal/photos/film_photography/

# Add more iCloud shortcuts by editing ~/.aliases:
alias myproject="cd \"$ICLOUD/Projects/MyProject\""
```

---

## History & Shell Features

### Command History
```bash
# Your zsh is configured with:
# - 10,000 command history
# - Shared history across sessions
# - Duplicate command removal
# - History verification before execution

# History navigation:
# ↑ / ↓ arrows - Navigate through history
# Ctrl+R - Search history
# !! - Repeat last command
# !command - Repeat last command starting with 'command'
```

### Auto-completion
```bash
# Enhanced completion features:
# - Case-insensitive matching
# - Colored completion menu
# - Smart directory completion
# - Git branch completion
# - Command parameter completion

# Tab completion examples:
cd Doc<TAB>     # Completes to Documents/
git che<TAB>    # Completes to checkout
```

---

## Advanced Features

### Text Processing
```bash
# Copy to clipboard
echo "text" | c     # Copy text to clipboard (removes newlines)

# URL encoding
urlencode "hello world"     # Output: hello%20world
```

### PDF Operations
```bash
# Merge PDF files
mergepdf input1.pdf input2.pdf input3.pdf
# Creates: _merged.pdf with all files combined
```

### Process Management
```bash
# Chrome memory management
chromekill  # Kill Chrome helper processes to free memory
            # Useful when Chrome is using too much RAM
```

### Hash Functions
```bash
# File integrity checking
md5sum file.txt     # Calculate MD5 hash
sha1sum file.txt    # Calculate SHA1 hash
hd file.txt         # Hex dump of file contents
```

---

## Customization & Extension

### Adding Your Own Commands

1. **Edit ~/.aliases for permanent aliases:**
```bash
# Add to ~/.aliases file
alias myalias="echo 'Hello World'"
```

2. **Create ~/.extra for private settings:**
```bash
# Create ~/.extra file (not tracked in git)
export PRIVATE_VAR="secret"
alias private_cmd="echo 'Private command'"
```

3. **Add new iCloud shortcuts:**
```bash
# Add to ~/.aliases
alias photos="cd \"$ICLOUD/Photos\""
alias work="cd \"$ICLOUD/Work/Projects\""
```

### Reload Configuration
```bash
# After making changes:
source ~/.zshrc     # Reload zsh configuration
reload             # Restart shell completely
```

---

## Troubleshooting Commands

### Configuration Issues
```bash
# Check if aliases are loaded
alias | grep ic     # Should show your iCloud aliases

# Check environment variables
echo $ICLOUD        # Should show iCloud path
echo $EDITOR        # Should show vim

# Test custom commands
which s             # Should show Sublime Text path
which yt            # Should show yt-dlp path
```

### Path Issues
```bash
# Check your PATH
path                # Shows each PATH entry on separate line
echo $PATH          # Shows full PATH variable

# Reload PATH
source ~/.exports   # Reload environment variables
```

---

## Daily Workflow Examples

### Development Workflow
```bash
# Navigate to project
p                   # Go to projects directory
cd myproject        # Enter project directory

# Edit configuration
edit                # Quick edit of shell config

# Open project in Sublime Text
s .                 # Open current directory

# Git operations
g status            # Check git status
g add .             # Stage changes
g commit -m "fix"   # Commit changes
```

### System Maintenance
```bash
# Weekly maintenance routine
update              # Update all packages
cleanup             # Remove .DS_Store files
emptytrash          # Empty trash and logs
lscleanup           # Fix "Open With" menu
```

### iCloud Workflow
```bash
# Quick navigation
ic                  # Jump to iCloud Drive
college             # Go to college folder
film                # Go to photography folder

# Work with files
ls                  # List files with colors
s document.txt      # Open in Sublime Text
```

---

## Tips & Best Practices

### Efficiency Tips
1. **Use two-letter aliases** for frequently accessed directories
2. **Combine commands** with `&&` for sequences
3. **Use tab completion** extensively
4. **Leverage history search** with Ctrl+R

### Maintenance Tips
1. **Run `update` weekly** to keep system current
2. **Use `cleanup` regularly** to remove system junk
3. **Check `path` if commands stop working**
4. **Use `reload` after editing dotfiles**

### Safety Tips
1. **Always review** what `update` will do
2. **Test aliases** before relying on them
3. **Backup configurations** before major changes
4. **Use `which command`** to verify command locations

---

*This guide covers all commands and features in your dotfiles setup. Keep it handy for reference and discovery of new productivity shortcuts!*
