# New Mac setup

An ordered runbook for a fresh personal Apple Silicon Mac. You do steps 1-4 by hand (about 20 minutes); after that an agent can drive the rest, stopping at each step only you can do. Every step says who does it: **[you]**, **[agent]**, or both. Each code block can be pasted as-is once you fill in the `<placeholders>`.

A Mac that was set up by the old rsync bootstrap needs a few steps before its first run; see [Existing Mac](#existing-mac-set-up-by-the-old-rsync-bootstrap). Before you leave the old Mac, read [Carrying over from the old Mac](#carrying-over-from-the-old-mac).

## For the agent

Start after step 4, in `~/code/personal/dotfiles`. This runbook is the user's request to deploy into the real `$HOME`, except where a step says to ask first.

1. Run `bash scripts/doctor.sh` outside the sandbox: its gh, ssh and Keychain checks fail falsely inside one. It is read-only and lists every gap in SETUP order as `TODO [you]` or `TODO [agent]`, each with the command that closes it. The **[agent]** steps write outside the repo (`~/.ssh`, `~/.extra`, bootstrap, the MCP venv), so run them outside the sandbox too.
2. Work the steps below in order. Run the **[agent]** parts yourself, then re-run doctor.
3. Never type a password, passphrase, token, license key or personal value, and never pick an account. Hand each **[you]** part to the user verbatim. Put commands that prompt (sudo, `brew bundle`, logins) in a terminal tab the user can type into, then wait for them.
4. Ask before steps 10 (`.macos`) and 15 (LaunchAgents): both change machine state beyond the dotfiles.
5. Done means `bash scripts/doctor.sh` exits 0, `bash scripts/check.sh` has 0 FAIL, and the user has done the manual checks in step 17.

## 1. Account name and hostname [you]

Pick a short account name in Setup Assistant. It becomes `$HOME`, and nothing in this repo hard-codes it. Sign in with your Apple ID during setup and turn on iCloud Drive and Passwords (iCloud Keychain): that one sign-in covers the App Store, the Obsidian vault in iCloud, and password autofill for most app sign-ins later.

Then name the Mac before anything else. The Ghostty overlay (step 9) is keyed on `LocalHostName`, and without an explicit name the network can hand the Mac an arbitrary `hostname`.

```sh
sudo scutil --set ComputerName "<Name>"
sudo scutil --set HostName "<name>"
sudo scutil --set LocalHostName "<name>"
```

## 2. Command Line Tools, Homebrew, App Store [you]

```sh
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"   # repeat in each new window until step 8; .zshrc does it after that
```

Open the App Store and check you are signed in. The `mas` lines in the Brewfile can't sign in for you.

## 3. Claude Code [you]

Install the CLI with the native installer. It updates itself, and the `update` function runs `claude update`. (The `claude` cask in the Brewfile is the desktop app.)

```sh
curl -fsSL https://claude.ai/install.sh | bash
export PATH="$HOME/.local/bin:$PATH"   # the installer's location; .zshrc adds it from step 8 on
claude auth login          # personal account
```

## 4. Clone the repo and hand over [you]

The repo is public, so clone it over HTTPS now; step 5 switches it to SSH.

```sh
mkdir -p ~/code/personal
git clone https://github.com/kevincorvallis/dotfiles.git ~/code/personal/dotfiles
cd ~/code/personal/dotfiles && claude
```

Keep this path: `$DOTFILES` and the `edit` alias default to it. Then tell the agent: "Set up this Mac by following SETUP.md." To do it all by hand instead, carry on with step 5 and run `bash scripts/doctor.sh` as you go.

## 5. SSH key for GitHub [you] [agent]

One personal key serves both `github.com` and the `github-personal` alias, because some clones use `git@github-personal:` remotes.

**[you]** Create the key (you choose the passphrase), or restore it from the transfer drive instead:

```sh
ssh-keygen -t ed25519 -C "kevincorvallis@gmail.com" -f ~/.ssh/id_ed25519_personal
```

**[agent]** Write the SSH config and load the key:

```sh
cat >> ~/.ssh/config <<'EOF'
Host github.com github-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_personal
  IdentitiesOnly yes
  AddKeysToAgent yes
  UseKeychain yes
EOF
chmod 600 ~/.ssh/config
```

**[you]** Add the key to the agent and log in to GitHub. This one sign-in covers git, the private Homebrew tap and Claude Code's github plugin (`.zshrc` exports its token from `gh auth token`):

```sh
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_personal
brew install gh
gh auth login -p ssh --web     # when asked, upload ~/.ssh/id_ed25519_personal.pub
ssh -T git@github.com          # accept GitHub's host key; expect "Hi kevincorvallis!"
ssh -T git@github-personal
```

Accept the host key here: `brew bundle` (step 6) clones a private tap over SSH and can't answer that prompt.

**[agent]** Switch the clone to SSH:

```sh
git -C ~/code/personal/dotfiles remote set-url origin git@github.com:kevincorvallis/dotfiles.git
```

## 6. Packages [agent] [you]

**[agent]** Run this in a terminal tab the user can type into; **[you]** enter your password when asked:

```sh
cd ~/code/personal/dotfiles && brew bundle --file=Brewfile
```

- Expect a password prompt partway through. Karabiner-Elements, Logi Options+ and Tailscale are pkg installers, and Docker Desktop installs a privileged helper.
- Xcode comes from the App Store and is a very large download.
- `codex` and `vercel` are npm lines in the Brewfile, so there is no separate `npm install -g`.
- If an item fails, the rest still install. Fix the cause and re-run; installed items are skipped. Doctor lists whatever is still missing.

## 7. Machine-local files [agent] [you]

**[agent]**

```sh
cp ~/code/personal/dotfiles/.extra.example ~/.extra && chmod 600 ~/.extra
```

Everything in it starts commented out; uncomment what this Mac needs. Secrets are read from the Keychain (the pattern is in the file), never pasted in as literal values. Don't put `git config` commands in `~/.extra`: they would rewrite `~/.gitconfig` on every shell start.

Optional: `~/.gitconfig.local`. The tracked `.gitconfig` includes it last, so it wins. Use it for a different identity, or for SSH commit signing with the key from step 5. **[agent]** writes the file; **[you]** approve the two `gh` commands in the browser:

```sh
cat > ~/.gitconfig.local <<'EOF'
[gpg]
	format = ssh
[user]
	signingkey = ~/.ssh/id_ed25519_personal.pub
[commit]
	gpgsign = true
EOF
gh auth refresh -s admin:ssh_signing_key
gh ssh-key add ~/.ssh/id_ed25519_personal.pub --type signing
```

To see the effective value, run `git config user.email` inside a repo. A query with `--global` skips includes.

## 8. Deploy [agent]

```sh
cd ~/code/personal/dotfiles
bash bootstrap.sh -n     # preview; writes nothing
bash bootstrap.sh -f     # copies; differing files are backed up first
```

Then open a new shell (`exec zsh -l`); it should start with no output. Anything bootstrap replaced is in `~/.dotfiles-backup/<timestamp>/`. Later, edit files in the repo (not in `~`) and re-run `bash bootstrap.sh`; it only touches files that changed.

Shell history starts empty on purpose: it can hold secrets. atuin's config filters out lines that look like tokens, secrets, passwords or API keys; run `atuin login` only if you want sync.

## 9. Optional: per-host Ghostty overlay [agent]

Settings for one Mac only, such as a theme, go in a file named after its `LocalHostName`. Bootstrap appends that file to the base config. `hosts/brock` is an example.

```sh
cd ~/code/personal/dotfiles
$EDITOR ".config/ghostty/hosts/$(scutil --get LocalHostName)"
bash bootstrap.sh -f
```

The file name, and so the hostname, becomes public once it is committed.

## 10. macOS settings [you]

1. System Settings → Privacy & Security → Full Disk Access: add Ghostty, then quit and reopen it.
2. Run the script from Ghostty, not Terminal.app (the script quits Terminal when it finishes). Run it as your normal user, not with `sudo`; it asks for sudo itself.

```sh
cd ~/code/personal/dotfiles && ./.macos
```

If Full Disk Access is missing, it stops and says so. Log out and back in when it finishes. It does not add keyboard input sources; add those (Korean 2-Set) in System Settings → Keyboard → Input Sources.

## 11. Claude Code plugins and MCP [agent] [you]

**[agent]** `~/.claude/settings.json` declares the plugins and their marketplaces. Start `claude` once from a shell, then run `claude plugin list`. If any are missing, run `claude plugin install <plugin>@<marketplace>` for each. Starting from a shell matters: the github plugin reads `GITHUB_PERSONAL_ACCESS_TOKEN`, which `.zshrc` exports from `gh auth token`.

**[agent]** MCP servers (paper-search, codex, gemini, searxng): bootstrap has already copied their scripts to `~/.local/share/mcp/`. Build the venv and install the config:

```sh
uv venv --python 3.13 ~/.local/share/mcp/.venv-mcp
uv pip install --python ~/.local/share/mcp/.venv-mcp/bin/python -r ~/.local/share/mcp/requirements.txt
cp ~/code/personal/dotfiles/.config/mcp/mcp.json.example ~/.mcp.json && chmod 600 ~/.mcp.json
```

**[you]** The config reads values from the environment. Store the Gemini key in the Keychain (it prompts, so the key never lands in history); **[agent]** then adds the export line:

```sh
security add-generic-password -a "$USER" -s gemini-api-key -w    # prompts for the key
echo 'export GEMINI_API_KEY="$(security find-generic-password -w -s gemini-api-key 2>/dev/null)"' >> ~/.extra
```

- **gemini:** needs `GEMINI_API_KEY`. The alternative is `GOOGLE_CLOUD_PROJECT` with gcloud application-default credentials, but gcloud is not in the Brewfile.
- **searxng:** set `SEARXNG_URL` only if your instance isn't at `http://localhost:8080`. SearXNG runs in Docker and is not part of this repo.
- **codex:** needs `codex login` (step 16).

Then open a new shell and run `claude mcp list`. The first session asks you to approve the four servers. To skip that prompt, list them under `enabledMcpjsonServers` in the untracked `~/.claude/settings.local.json`.

## 12. espanso and app permissions [you]

```sh
cp ~/code/personal/dotfiles/.config/espanso/match/private.yml.example \
  "$HOME/Library/Application Support/espanso/match/private.yml"
$EDITOR "$HOME/Library/Application Support/espanso/match/private.yml"   # real values; never commit them
```

Bootstrap never deploys, overwrites or deletes `private.yml`. Trigger names must be unique across match files, or espanso shows a chooser.

Open each app once and grant what it asks for in System Settings → Privacy & Security (no script can grant these):

- **espanso, AeroSpace, Raycast:** Accessibility.
- **Karabiner-Elements:** Input Monitoring, and allow its driver extension (General → Login Items & Extensions).
- **Jiggler, Ice, Stats:** whatever each asks for on first launch.

Bootstrap seeds `karabiner.json` only when none exists. If Karabiner ran before step 8 and wrote its own file, `bash bootstrap.sh -n` reports drift and prints the `cp` command that takes the repo copy.

## 13. App settings that live outside the repo [you]

These apps keep their settings in their own stores, which hold accounts or licenses, so they are not in this public repo. Prefer each app's own sync or export:

- **Logi Options+:** on the old Mac, sign in to your Logi account in Options+ and turn on settings backup. On this Mac, sign in with the same account and restore the backup for each device. Fallback (untested): quit Options+ on both Macs, then copy `~/Library/Application Support/LogiOptionsPlus` across before its first launch here.
- **Raycast:** Settings → Advanced → Export on the old Mac, Import here (or Cloud Sync). Never copy `~/.config/raycast`; it holds tokens.
- **SoundSource:** enter the license from the purchase email. Its settings are in `com.rogueamoeba.soundsource` (below).
- **Ice, Stats, SoundSource preferences:** on the old Mac, with each app quit, run `defaults export <domain> <file>.plist` for `com.jordanbaird.Ice`, `eu.exelban.Stats` and `com.rogueamoeba.soundsource`. Move the files on the transfer drive, then run `defaults import <domain> <file>.plist` here before opening the app. This is best-effort; reconfiguring by hand is the fallback.
- **Finicky:** reads `~/.finicky.js`. Write a personal one here; the old Mac's routes work and school accounts, which is why it isn't in the repo.
- **Claude Quick Actions:** copy the `.workflow` files in `~/Library/Services` across.
- **Finder sidebar [agent]:** the personal Favorites list is deployed by bootstrap. Preview with `finder-favorites import ~/.config/finder/favorites.txt --dry-run`, then run the same command without `--dry-run`. It skips existing Favorites and missing folders, and appends new entries in file order. Existing sidebar order and built-in items stay unchanged. For a complete private export from the old Mac, see [README: Finder Favorites](README.md#finder-favorites). If the macOS API is unavailable, select each folder in Finder and press ctrl+cmd+T, then drag into order.
- **Finder sidebar icons [agent + you]:** restore Emblem's folder-to-symbol assignments separately using [README: Custom sidebar icons](README.md#custom-sidebar-icons-emblem) and the private "Mac Studio GUI Setup" note. The Favorites path list does not carry icons. Regenerate the icon apps, enable their Finder extensions, and verify each icon visually.
- **Dock and folders [agent]:** follow the private checklist "Mac Studio GUI Setup" in the Obsidian vault (Notes/Projects), which arrives through iCloud. Its older Finder export instructions are superseded by the step above.

## 14. Your repos, builds and files [agent]

Clone the personal repos you want. Doctor lists every non-archived repo of the logged-in gh account that isn't under `~/code` yet. It skips forks (VoiceInk, ghostty), so clone those by name:

```sh
gh repo clone <name> ~/code/personal/<name>
```

Your own apps are built from source, not installed by the Brewfile:

- **VoiceInk:** `gh repo clone kevincorvallis/VoiceInk ~/code/personal/VoiceInk`, then build it with its Makefile (`make help`). It needs Xcode and cmake, and the Developer ID identity from the transfer drive for a signed build. Move the app to `/Applications`. Restore its data from the transfer drive before the first launch.
- **Insang:** the same, once its repo has a GitHub remote.

Then copy the folders that are not in git from the transfer drive (see [Carrying over](#carrying-over-from-the-old-mac)).

## 15. LaunchAgents (opt-in) [agent, after you decide]

First retire any agent on this Mac that already does one of these jobs under another label, for example from an older setup:

```sh
launchctl list | grep -i -e obsidian -e disk-clean    # loaded agents; the label is the last column
ls ~/Library/LaunchAgents | grep -i -e obsidian -e disk-clean
```

Unload and delete each one whose label doesn't start with `com.kevincorvallis.`:

```sh
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/<old-label>.plist
rm ~/Library/LaunchAgents/<old-label>.plist
```

If this Mac takes over vault sync, do the same on every other Mac for its obsidian-sync agent, whatever its label. Skip this and each job runs twice, and two committers race on the vault's iCloud-synced `.git`.

```sh
cd ~/code/personal/dotfiles
bash bootstrap.sh -n --launchagents   # preview
bash bootstrap.sh -f --launchagents
```

This repeats the normal deploy, then installs and loads two agents:

- **`com.kevincorvallis.disk-clean`** runs `~/bin/disk-clean clean` daily at 07:00, and also at load, so the first run starts right away. It clears package caches, Xcode DerivedData, Docker images older than 72h and unavailable simulators. Run `disk-clean check` first to see what it would remove.
- **`com.kevincorvallis.obsidian-sync`** commits and pushes the Obsidian vault daily at 18:00. Run it on one Mac only, and only after the vault folder is set to Keep Downloaded and `git fsck` passes inside it.

To keep obsidian-sync off this Mac, unload it with `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.kevincorvallis.obsidian-sync.plist`. A later `--launchagents` run loads it again.

Logs go to `~/Library/Logs/disk-clean.log` and `~/Library/Logs/obsidian-sync.log`. If bootstrap prints a `FAILED` line, run the `launchctl bootstrap …` command it shows again by hand.

## 16. Sign-in sweep [agent runs, you approve]

Each service issues its own login for this Mac, so this can't be skipped. It can be fast, though: with the browser already signed in (step 1's Passwords autofill helps), each of these is one click. **[agent]** runs them one after another in a terminal tab; **[you]** approve each in the browser:

```sh
gh auth status        # logged in during step 5
codex login
vercel login
supabase login
```

**[you]** `aws configure` with a new access key created for this Mac (don't copy the old one). Sign in to Tailscale from its menu bar app. Run `docker login` only if a registry needs it. GUI apps (Slack, Zoom, Spotify, Discord, Obsidian, Day One, NordVPN) sign in when first opened; Passwords autofill covers most of them.

## 17. Verify [agent], then [you]

```sh
cd ~/code/personal/dotfiles
bash scripts/doctor.sh              # this Mac; exits 0 when nothing is left to do
bash scripts/check.sh               # repo health; exits 1 on any FAIL (--offline skips network lookups)
```

If `bootstrap.sh -n` lists a file, decide which copy is right. Either re-run `bash bootstrap.sh`, or copy the live file back into the repo; some apps, such as Sublime's Package Control, rewrite their own settings.

Then, **[you]** in a new Ghostty tab, check what no script can see:

- the shell starts with no output
- `alias ls` shows eza, and `ll` lists dotfiles
- Ctrl-R opens atuin and Ctrl-T opens fzf
- cmd+shift+v pastes as a single line
- espanso expands a snippet, AeroSpace tiles a window, Karabiner's remaps work
- one Claude Code Bash call runs without hook errors

## Existing Mac (set up by the old rsync bootstrap)

The old bootstrap rsynced files into `~`, and the live copies have drifted since. The first run of the current bootstrap backs up and replaces every file that differs from the repo (except `karabiner.json`). So move this Mac's own settings into the machine-local files before that run.

1. **Git.** Move the `[user]` identity, any signing settings (`[commit] gpgsign`, `[gpg]`, `user.signingkey`) and any `[includeIf]` blocks from `~/.gitconfig` into `~/.gitconfig.local`. Otherwise every repo on this Mac switches to the tracked personal identity with signing off. The dry run still lists `~/.gitconfig` as differing; that is expected. After the run, check inside a repo that `git config user.email` and `git config commit.gpgsign` print this Mac's values.
2. **`~/.extra`.** Delete every `git config` line. Each one rewrites `~/.gitconfig` on every shell start, which brings the drift back.
3. **Claude Code.** Bootstrap replaces `~/.claude/settings.json` as a whole, along with `CLAUDE.md`, `AGENT-GRAPH.md` and any same-named file under agents, commands, rules, skills, output-styles, hooks or scripts. The repo's `settings.json` carries only the repo's own hooks, and Claude Code has no machine-local overlay for user settings. Any hooks, `autoMode` or other blocks that exist only on this Mac, such as hooks a managed security tool installed, are dropped. If this Mac has them, restore them right after the run: copy the old file back with `cp ~/.dotfiles-backup/<timestamp>/.claude/settings.json ~/.claude/`, or merge those blocks into the new file by hand. Each later run replaces the file again while it differs from the repo, so repeat the restore after every run, and expect `bash bootstrap.sh -n` (step 17) to list that one file on this Mac.
4. **LaunchAgents.** Before using `--launchagents`, retire agents that do the same jobs under other labels, as described in step 15.
5. **Preview, then deploy.** Run `bash bootstrap.sh -n` and read every `(differs)` line. If a live file has something worth keeping, move it to `~/.extra`, `~/.gitconfig.local` or espanso's `private.yml` when it is machine-specific, or into the repo when it belongs on every Mac. Then run `bash bootstrap.sh`.
6. **Roll back.** `~/.dotfiles-backup/<timestamp>/` holds every file the run replaced, at the same path relative to `~`. Restore one with `cp ~/.dotfiles-backup/<timestamp>/<path> ~/<path>`, or all of them with `rsync -a ~/.dotfiles-backup/<timestamp>/ ~/`. Files the run newly created have no backup; delete them by hand if you don't want them.

## Carrying over from the old Mac

- **Push every repo you care about first.** The new Mac only gets what is on GitHub. A repo with no remote, unpushed commits, a stash or uncommitted changes is lost unless you push it or copy it. To list them on the old Mac, run this in `~/code/personal`:

  ```sh
  for d in */; do [ -d "$d.git" ] || continue; echo "${d%/}: remote=$(git -C "$d" remote | head -1) unpushed=$(git -C "$d" log --branches --not --remotes --oneline | wc -l) dirty=$(git -C "$d" status --porcelain | wc -l)"; done
  ```

- Secrets never travel through git, this repo included. Create new keys and tokens where you can.
- Move the rest on an encrypted disk image (the transfer drive), by AirDrop or through a password manager. That covers signing certificates, keys that can't be downloaded again, espanso `private.yml`, Claude memory directories, VoiceInk data, the `defaults export` files from step 13, and folders that aren't in git.
- Don't copy shell history, `~/.extra`, `~/.mcp.json`, `~/.claude.json` or a live `~/.claude/settings.json`. Rebuild them from the steps above.
- The item-by-item list of what to carry and what to leave behind is in a private audit note on the old Mac. It is kept out of this public repo on purpose.
