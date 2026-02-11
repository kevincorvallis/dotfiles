# HTTP Client Configs

> Configuration for `curl` (`.curlrc`) and `wget` (`.wgetrc`). These set sensible defaults so you don't have to pass flags every time.

## .curlrc (curl defaults)

| Setting | Value | What It Does |
|---------|-------|-------------|
| `user-agent` | Modern Chrome UA | Identifies as a real browser to avoid bot detection |
| `referer` | `;auto` | Automatically sets the Referer header when following redirects |
| `connect-timeout` | `60` | Wait up to 60 seconds for connection (default is very long) |

### Usage
These settings apply automatically to every `curl` command:
```bash
# This now sends a modern Chrome user-agent automatically
curl https://example.com

# Override for a specific request
curl -A "MyBot/1.0" https://api.example.com
```

## .wgetrc (wget defaults)

| Setting | Value | What It Does |
|---------|-------|-------------|
| `user_agent` | Modern Chrome UA | Same as curl - avoids bot detection |
| `timestamping` | `on` | Only re-download if remote file is newer |
| `no_parent` | `on` | Don't follow links up the directory tree when downloading recursively |
| `timeout` | `60` | 60-second timeout for DNS, connect, and read |
| `tries` | `3` | Retry 3 times on failure (default is 20) |
| `retry_connrefused` | `on` | Retry even when connection is refused |
| `trust_server_names` | `on` | Use the final URL's filename after redirects |
| `follow_ftp` | `on` | Follow FTP links found in HTML pages |
| `adjust_extension` | `on` | Add `.html` to HTML files that lack it |
| `robots` | `off` | Ignore robots.txt restrictions |
| `server_response` | `on` | Show HTTP response headers |

### Usage
```bash
# Download a file (uses all defaults automatically)
wget https://example.com/file.zip

# Mirror a website
wget -r -l 3 https://example.com

# The timeout, retries, and user-agent are already set
```

## Why the User-Agent Matters

Websites check the User-Agent header to identify clients. The old setting used IE 9 (from 2011), which:
- Got flagged by bot detection systems
- Received outdated/degraded content
- Was suspicious to any modern server

The current setting uses a modern Chrome user-agent, which most servers expect and serve properly.

## Tags
#dotfiles #curl #wget #http #configuration
