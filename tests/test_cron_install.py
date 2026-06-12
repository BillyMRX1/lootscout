from lootscout import wizard

LINE = ("0 */6 * * * cd /root/lootscout && /root/.local/bin/uv run lootscout "
        ">> /root/lootscout/lootscout.log 2>&1")


def test_install_into_empty_crontab():
    out = wizard.install_cron("", LINE)
    assert LINE in out
    lootscout_lines = [ln for ln in out.splitlines() if "lootscout" in ln]
    assert lootscout_lines == [LINE]        # exactly one cron line
    assert out.endswith("\n")


def test_install_preserves_existing_jobs():
    existing = "0 5 * * * /usr/bin/backup\n@reboot /usr/bin/other\n"
    out = wizard.install_cron(existing, LINE)
    assert "/usr/bin/backup" in out
    assert "@reboot /usr/bin/other" in out
    assert LINE in out


def test_install_replaces_stale_lootscout_line():
    existing = "0 */6 * * * cd /old/path && uv run lootscout\n0 5 * * * /backup\n"
    out = wizard.install_cron(existing, LINE)
    lootscout_lines = [ln for ln in out.splitlines() if "lootscout" in ln]
    assert lootscout_lines == [LINE]        # only the fresh line survives
    assert "/backup" in out
    assert "/old/path" not in out


def test_install_is_idempotent():
    once = wizard.install_cron("", LINE)
    twice = wizard.install_cron(once, LINE)
    assert once == twice
