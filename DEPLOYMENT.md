# LootScout — Deployment & Handover

Everything you need to stand this up on your server. Read top to bottom once.

## What this is

🔭 **LootScout** is a run-once CLI that checks the [GamerPower](https://www.gamerpower.com/)
API for **new free-to-keep game giveaways** (Steam/Epic/GOG/itch + Xbox + Switch)
and pushes only genuinely-new ones to your notification channels. It is **not a
daemon** — you run it on a schedule (cron/launchd) on an always-on machine.

- **Channels available:** Telegram, Email (Gmail), RSS feed.
- **ntfy was deliberately removed** — public ntfy topics let anyone who knows the
  topic name publish to it (spoofed/phishing notifications). Do not re-add it.
- **Stack:** Python ≥3.11, `uv`. Deps: `requests`, `questionary`, `tomli-w`.
- **Tests:** `uv run pytest` → 38 passing.

## How it behaves (important)

1. Each run: fetch current giveaways → diff against `seen.json` → push new ones → rewrite `public/feed.xml` → exit.
2. **First run after setup seeds silently** — it records the current ~20-30 giveaways as "already seen" and sends **no** notifications (avoids a backlog flood). Only giveaways that appear *after* the first run trigger a message.
3. State (`seen.json`) is saved **only if all push channels succeed**, so a transient failure won't silently drop a giveaway.
4. **Real-time = always-on.** If the machine is off/asleep when a giveaway goes live and expires before the next run, you miss it. A server/VPS is ideal.

## Project layout

```
src/lootscout/
  cli.py        entry: `lootscout setup` and `lootscout run` (run is default)
  main.py       run pipeline (fetch → diff → push → rss → save state)
  feed.py       GamerPower fetch/parse (URL: filter?platform=pc.xbox-one.xbox-series-xs.switch&type=game)
  config.py     loads config.toml + .env, fails fast on missing secrets
  state.py      seen.json load/save
  wizard.py     interactive setup (square-box checkboxes, telegram chat_id autodetect)
  channels/     base (Giveaway + Channel protocol), telegram, email, rss, registry
config.example.toml / .env.example   committed templates (real ones are gitignored)
```

## Files that DON'T travel with the repo (gitignored)

`config.toml`, `.env`, `seen.json`, `public/feed.xml` are **gitignored** — they are
NOT in a clone. On the server you must either:
- run `uv run lootscout setup` again (recommended — regenerates `config.toml` + `.env`), **or**
- copy your local `config.toml` and `.env` to the server manually (`scp`).

> Re-running setup on the server is cleanest. For Telegram you'll need the bot
> token again and to message the bot once so it can auto-detect your `chat_id`.

---

## Getting the code onto the server

There is **no git remote configured yet.** Pick one:

**A. Via GitHub (recommended):**
```bash
# on your laptop, one-time:
gh repo create lootscout --private --source=. --push
# then on the server:
git clone git@github.com:<you>/lootscout.git
```

**B. Direct copy (no GitHub):**
```bash
# from your laptop (excludes venv/secrets/state automatically if you use git archive)
rsync -av --exclude .venv --exclude .env --exclude config.toml --exclude seen.json \
  /Users/billymrx/project/free-games/  user@server:/opt/lootscout/
```

---

## Server setup (step by step)

```bash
# 1. Prereqs: a Linux server with internet + git. Install uv if absent:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Get the code (see above), then:
cd /opt/lootscout            # wherever you put it

# 3. Install dependencies (creates .venv, installs deps + pytest):
uv sync

# 4. (optional) sanity check:
uv run pytest -q             # expect: 38 passed

# 5. Configure — interactive; writes config.toml + .env (chmod 600):
uv run lootscout setup
#    - pick platforms (PC/Xbox/Switch)
#    - pick channels (Telegram recommended)
#    - Telegram: paste @BotFather token, message your bot, chat_id auto-detected
#    - say YES to the test notification → confirms delivery immediately

# 6. First run — seeds state silently, writes the feed, sends nothing:
uv run lootscout

# 7. Schedule it (cron, every 6h). Use ABSOLUTE paths:
crontab -e
```
Add (replace paths with yours — `which uv` gives the uv path):
```cron
0 */6 * * * cd /opt/lootscout && /root/.local/bin/uv run lootscout >> /opt/lootscout/lootscout.log 2>&1
```

```bash
# 8. Watch it work:
tail -f /opt/lootscout/lootscout.log
```

## Verifying / forcing a notification

The first run is silent and new giveaways are rare, so to prove delivery works
without waiting, send a manual test through your configured channels:

```bash
uv run python -c "
from pathlib import Path
from lootscout import config, cli, wizard
from lootscout.channels import build_channels
cli._load_env_file(Path('.env'))
chans = build_channels(config.load(Path('config.toml')))
for name, ok, err in wizard.send_tests(chans):
    print(name, '->', 'OK' if ok else err)
"
```

(Or just re-run `uv run lootscout setup` and accept its end-of-wizard test send.)

## Serving the RSS feed (optional)

Every run rewrites `public/feed.xml`. Point a web server at it and set
`[rss].site_url` in `config.toml` to the public URL:
```nginx
location = /feed.xml { alias /opt/lootscout/public/feed.xml; }
```

## Command cheat sheet

| Command | What it does |
|---|---|
| `uv sync` | install deps + dev tooling |
| `uv run lootscout setup` | (re)configure channels → writes config.toml + .env |
| `uv run lootscout` | one check (default command; `run` optional) |
| `uv run pytest -q` | run tests (38) |
| `tail -f lootscout.log` | watch scheduled runs |

## Gotchas recap

- `config.toml` / `.env` are gitignored → **run setup on the server** (or scp them).
- First run is **silent** by design.
- Schedule needs **absolute paths** (cron has a minimal env).
- On a Mac laptop use `launchd` (runs missed jobs on wake); on a Linux server cron is fine.
- Don't re-add ntfy (public-topic spoofing risk — why it was removed).
