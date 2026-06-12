from pathlib import Path
from lootscout import wizard


def test_warns_loudly_when_cron_not_installed():
    msg = wizard.cron_notice(
        crontab_text="0 5 * * * /usr/bin/backup\n",
        project_dir=Path("/root/lootscout"),
        uv_path="/root/.local/bin/uv",
    )
    assert "⚠" in msg                       # a visible warning marker
    assert "not" in msg.lower()             # tells the user it's NOT installed
    # and gives the exact absolute-path command to install it
    assert "/root/lootscout" in msg
    assert "/root/.local/bin/uv run lootscout" in msg
    assert "crontab" in msg.lower()


def test_confirms_when_cron_already_installed():
    msg = wizard.cron_notice(
        crontab_text="0 */6 * * * cd /root/lootscout && uv run lootscout\n",
        project_dir=Path("/root/lootscout"),
        uv_path="uv",
    )
    assert "✓" in msg
    assert "already" in msg.lower()


def test_uses_absolute_paths_not_pwd():
    msg = wizard.cron_notice(
        crontab_text="",
        project_dir=Path("/opt/lootscout"),
        uv_path="/usr/local/bin/uv",
    )
    assert "$(pwd)" not in msg               # never the broken relative form
    assert "/opt/lootscout/lootscout.log" in msg
