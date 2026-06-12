# 🔭 LootScout

Notify yourself when a game is **free to keep** — across Steam, Epic, GOG, Xbox,
and Switch. It polls the [GamerPower](https://www.gamerpower.com/) giveaway API,
remembers what it has already seen, and pushes only **new** giveaways to the
channels you enable (ntfy, Telegram, email) while always writing a full RSS feed.

## How it works

1. Fetches current giveaways for your configured platforms and giveaway type.
2. Diffs them against `seen.json` (the IDs it has already notified about).
3. Pushes new entries to enabled push channels and rewrites `public/feed.xml`.
4. Saves `seen.json` **only after** a successful run — a failed push leaves
   state untouched so nothing is silently dropped.

The very first run seeds `seen.json` silently (no notification spam for the
existing backlog) and writes the feed.

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

Check for new giveaways (this is the default command — `run` is optional):

```bash
uv run lootscout
```

### Scheduling with cron

Poll every 6 hours:

```cron
0 */6 * * * cd /path/to/lootscout && /path/to/uv run lootscout >> /var/log/lootscout.log 2>&1
```

Use absolute paths for both the project directory and `uv`; cron runs with a
minimal environment.

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
- **ntfy:** the topic name *is* the access control. Pick an obscure,
  hard-to-guess topic (the wizard generates a random one) — anyone who knows the
  topic can read your notifications.
- `.env`, `seen.json`, and `public/feed.xml` are gitignored. Never commit them.
