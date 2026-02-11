# Shell Functions

> Reusable functions defined in `~/.functions`. Unlike aliases, functions can take arguments and have logic.

## File Operations

### `mkd <directory>`
Create a directory and immediately cd into it.
```bash
mkd my-new-project
# Creates ~/my-new-project and enters it
```

### `cdf`
Change to whatever directory the frontmost Finder window is showing. Useful when you've navigated somewhere in Finder and want Terminal to match.
```bash
cdf
# Terminal is now in the same folder as your Finder window
```

### `fs [file-or-directory]`
Show the size of a file or directory in human-readable format.
```bash
fs node_modules    # Shows total size of node_modules
fs                 # Shows sizes of everything in current directory
```

### `targz <directory>`
Create a compressed `.tar.gz` archive. Automatically picks the best compression tool available:
1. **zopfli** (best compression, slower) - if file < 50MB
2. **pigz** (parallel gzip, fast) - for larger files
3. **gzip** (standard) - fallback

```bash
targz my-project
# Creates my-project.tar.gz
```

### `dataurl <file>`
Convert any file to a base64 data URL. Useful for embedding images in HTML/CSS.
```bash
dataurl icon.png
# Outputs: data:image/png;base64,iVBORw0KGgo...
```

## Comparison

### `diff <file1> <file2>`
Enhanced diff using git's color-words mode. Shows changes at the word level instead of line level.
```bash
diff old-config.json new-config.json
# Color-highlighted word-level differences
```

### `gz <file>`
Compare original file size vs gzipped size with compression ratio.
```bash
gz bundle.js
# orig: 245000 bytes
# gzip: 62000 bytes (25.31%)
```

## Web & Network

### `server [port]`
Start a Python HTTP server in the current directory. Default port 8000.
```bash
cd ~/my-website
server        # Opens http://localhost:8000 in browser
server 3000   # Use port 3000 instead
```

### `digga <domain>`
Simplified DNS query showing all record types.
```bash
digga google.com
# Shows A, AAAA, MX, NS records in clean format
```

### `getcertnames <domain>`
Show the SSL certificate details for a domain, including Common Name and all Subject Alternative Names.
```bash
getcertnames github.com
# Common Name: github.com
# Subject Alternative Name(s): github.com, www.github.com
```

## File Browsing

### `o [path]`
Open a file or directory. With no arguments, opens the current directory in Finder.
```bash
o           # Opens current directory in Finder
o .         # Same thing
o file.pdf  # Opens file with default app
```

### `tre [path]`
Enhanced `tree` command with color, excluding `.git` and `node_modules`, piped through less for scrolling.
```bash
tre              # Tree view of current directory
tre ~/projects   # Tree view of projects
```

## Tags
#dotfiles #functions #shell #utilities
