# 🔭 LootScout

Notify yourself when a game is **free to keep** — across Steam, Epic, GOG, Xbox,
and Switch. It polls the [GamerPower](https://www.gamerpower.com/) giveaway API,
remembers what it has already seen, and pushes only **new** giveaways to the
channels you enable (Telegram, email) while always writing a full RSS feed.

## How it works

1. Fetches current giveaways for your configured platforms and giveaway type.
2. Diffs them against `seen.json` (the IDs it has already notified about).
3. Pushes new entries to enabled push channels and rewrites `public/feed.xml`.
4. Saves `seen.json` **only after** a successful run — a failed push leaves
   state untouched so nothing is silently dropped.

The very first run sends **one consolidated digest** of everything currently
free-to-keep (a single message with a clickable link per game, not one ping per
giveaway), then records them as seen. After that, you're only notified about
giveaways that appear later. If no push channels are enabled, the first run just
seeds silently and writes the feed.

## Setup

Install dependencies:

```bash
uv sync
```

Run the interactive setup wizard. It writes `config.toml` and a `.env`
(secrets file, `chmod 600`):

```bash
uv run lootscout setup
```

## Running

LootScout is a **run-once command, not a background service**. Each run checks
for new giveaways and exits — it only notifies you of giveaways that appear
*while it runs*.

Check for new giveaways (this is the default command — `run` is optional):

```bash
uv run lootscout
```

### Other commands

Check your configuration and health at a glance — platforms, enabled channels,
whether each required secret is present (masked, never printed), how many
giveaways are tracked, and the feed status:

```bash
uv run lootscout status
```

`status` exits `0` when healthy, `1` when there's no config yet, and `2` when a
secret is missing for an enabled channel — so it doubles as a cron health check.

Tear an install down interactively — pick any of: runtime files
(`config.toml`/`.env`/`seen.json`/`public/feed.xml`), the scheduled cron/launchd
job, or the whole install dir. It previews what will be deleted and asks you to
type a confirmation first:

```bash
uv run lootscout remove
```

> **You need an always-on machine for real-time notifications.** To be alerted
> automatically you must run LootScout on a **server, VPS, or PC that stays on**
> (via cron/launchd, below). If the machine is off or asleep when a giveaway
> goes live, that run doesn't happen and you can miss it.
>
> **No server? Run it manually.** LootScout works perfectly as a manual command —
> just run `uv run lootscout` yourself whenever you want to check (e.g. once a
> day). You'll get a Telegram/email ping for anything new since your last run.

### Scheduling with cron (server / always-on PC)

At the end of `setup`, LootScout **offers to install the cron job for you**
(every 6 hours, with absolute paths) — just answer yes. If you decline (or want
to do it by hand), it prints the exact line to add via `crontab -e`:

```cron
0 */6 * * * cd /path/to/lootscout && /path/to/uv run lootscout >> /path/to/lootscout/lootscout.log 2>&1
```

Use absolute paths for both the project directory and `uv`; cron runs with a
minimal environment. Re-running `setup` refreshes an existing schedule rather
than duplicating it. Verify any time with `uv run lootscout status`.

On a **macOS laptop**, prefer `launchd` over cron — it runs a missed job when
the machine wakes, whereas cron simply skips jobs that fall during sleep.

### Serving the RSS feed

Every run rewrites `public/feed.xml`. To subscribe in any RSS reader, point a
web server at the `public/` directory (or just at the file):

```nginx
location = /feed.xml {
    alias /path/to/lootscout/public/feed.xml;
}
```

Then set `[rss].site_url` in `config.toml` to the public URL so feed items
carry the right `<link>`.

## Credential safety

- **Email:** use a **throwaway Gmail account** with an
  [app password](https://support.google.com/accounts/answer/185833), not your
  primary password. App passwords are scoped to a single app and can be revoked
  independently. Secrets live in `.env`, which is `chmod 600` and gitignored.
- **Telegram:** the bot token is a secret (revocable via @BotFather). Messages
  go only to your detected `chat_id`, so notifications stay private to you.
- `.env`, `config.toml`, `seen.json`, and `public/feed.xml` are gitignored.
  Never commit them.
