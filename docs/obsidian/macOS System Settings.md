# macOS System Settings (.macos)

> The `.macos` script configures ~200 macOS system preferences via `defaults write` commands. Run it once on a fresh Mac to set up your ideal environment. Requires `sudo`.

## How It Works

macOS stores app and system preferences in `.plist` files. The `defaults` command reads/writes these files from Terminal. When you change a setting in System Settings, it writes to the same plists.

```bash
# Run the full script
./.macos

# Skip dark mode
./.macos --no-dark-mode
```

## Sections Explained

### General UI/UX
| Setting | What It Does | Why It Matters |
|---------|-------------|----------------|
| `reduceTransparency` | Reduces menu bar + window transparency | Better readability, especially with Liquid Glass on Tahoe |
| Sidebar icon size = medium | Sets Finder sidebar icons to medium | Easier to click on Retina displays |
| Always show scrollbars | Makes scrollbars always visible | Don't lose your place in long documents |
| Expanded save/print panels | Save dialogs start expanded | See full file browser immediately instead of tiny dialog |
| Save to disk (not iCloud) | Default save location is local disk | Prevents accidental iCloud uploads |
| Disable Resume system-wide | Apps don't reopen previous windows | Clean start every time you open an app |
| Disable quarantine dialog | *(Removed - broken since Big Sur)* | Use `xattr -d com.apple.quarantine /path/to/app` instead |

### Trackpad & Keyboard
| Setting | What It Does | Why It Matters |
|---------|-------------|----------------|
| Tap to click | Trackpad registers taps as clicks | Faster than physical clicks |
| Disable natural scrolling | Standard scroll direction | Content follows finger direction you're used to |
| Full keyboard access | Tab key works in ALL dialog buttons | Navigate popups without touching the mouse |
| Fast key repeat (rate 1, delay 10) | Very fast character repetition | Essential for Vim users and fast typists |
| Disable press-and-hold | Key repeat instead of accent menu | Hold `j` to scroll in Vim instead of getting accent picker |

### Energy & Power
| Setting | What It Does | Why It Matters |
|---------|-------------|----------------|
| `hibernatemode 0` | Disables hibernation | Faster wake from sleep (Note: unsupported on Apple Silicon, use with caution) |
| Display sleep 15 min | Screen turns off after 15 minutes | Battery conservation |
| No sleep while charging | Mac stays awake on power | Good for downloads, builds, servers |
| 5-min sleep on battery | Quick sleep on battery power | Preserves battery life |

### Screen & Display
| Setting | What It Does | Why It Matters |
|---------|-------------|----------------|
| Password immediately after sleep | Requires password right away | Security - prevents unauthorized access |
| Screenshots to ~/Desktop as PNG | Saves screenshots in PNG format to Desktop | High quality, easy to find |
| Disable screenshot shadows | No drop shadow on window screenshots | Cleaner screenshots for documentation |
| `AppleFontSmoothing 1` | Light font smoothing | Sharper text on non-Retina displays (controls dilation, not subpixel AA) |

### Finder
| Setting | What It Does | Why It Matters |
|---------|-------------|----------------|
| Allow quitting Finder | Cmd+Q quits Finder | Hide desktop icons, free memory |
| Show all file extensions | See `.txt`, `.py`, `.md` etc. | Know exactly what file type you're dealing with |
| Show path bar + status bar | Bottom bars in Finder windows | Always know where you are and how much space is left |
| POSIX path in title | Full `/Users/kevin/...` path in title bar | Unambiguous location |
| Keep folders on top | Folders sort above files | Easier navigation |
| Search current folder | Cmd+F searches current folder, not whole Mac | More predictable search |
| No .DS_Store on network/USB | Prevents .DS_Store on external volumes | Keeps shared drives clean |
| List view by default | Default to detailed list view | See file sizes, dates, kinds at a glance |

### Dock
| Setting | What It Does | Why It Matters |
|---------|-------------|----------------|
| Icon size 36px | Smaller dock icons | More screen real estate |
| Scale minimize effect | Scale instead of Genie animation | Faster, less distracting |
| Auto-hide, no delay | Dock hides instantly | Maximum screen space, instant access |
| Don't show recent apps | Hides recent apps section | Cleaner dock |
| Don't rearrange Spaces by recent use | Spaces stay in fixed order | Predictable workspace layout |

### Hot Corners
| Corner | Action |
|--------|--------|
| Top-left | Mission Control |
| Top-right | Desktop |
| Bottom-left | Screen Saver (locks screen) |
| Bottom-right | *(none)* |

### Safari
Privacy-focused defaults: disables search suggestions, AutoFill, pop-ups. Enables developer tools and debug menu.

### Spotlight
Prioritizes: Apps, System Preferences, Directories, PDFs, Fonts. Disables: Documents, Messages, Contacts, Images, etc. Excludes `/Volumes` from indexing.

### Mail
Thread view, plain-text copy, Cmd+Enter to send, no inline attachments.

### Activity Monitor
Shows all processes, sorted by CPU, with main window on launch.

## Tahoe 26 Notes

- **Launchpad removed** - Replaced by "Apps" in Tahoe. Old Launchpad reset commands removed.
- **Safari DNT removed** - "Do Not Track" header removed from Safari 17+.
- **Native window tiling** - macOS Tahoe has built-in window tiling (drag to edges). Rectangle removed.
- **Liquid Glass** - `reduceTransparency` still works to tone down the new Liquid Glass UI.

## Tags
#dotfiles #macos #defaults #system-settings
