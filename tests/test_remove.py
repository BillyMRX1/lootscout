from lootscout import remove


def test_detect_targets_only_includes_existing_files(tmp_path):
    cfg = tmp_path / "config.toml"; cfg.write_text("x")
    env = tmp_path / ".env"            # not created
    seen = tmp_path / "seen.json"; seen.write_text("[]")
    feed = tmp_path / "feed.xml"       # not created
    targets = remove.detect_targets(cfg, env, seen, feed, tmp_path, cron_lines=[])
    assert set(targets["runtime"]) == {cfg, seen}
    assert targets["install_dir"] == tmp_path


def test_filter_crontab_removes_lootscout_lines_only():
    crontab = (
        "0 5 * * * /usr/bin/backup\n"
        "0 */6 * * * cd /opt/lootscout && uv run lootscout >> x.log 2>&1\n"
        "@reboot /usr/bin/other\n"
    )
    new_text, removed = remove.filter_crontab(crontab)
    assert "lootscout" not in new_text
    assert "/usr/bin/backup" in new_text
    assert "@reboot /usr/bin/other" in new_text
    assert len(removed) == 1


def test_delete_paths_unlinks_existing_and_skips_absent(tmp_path):
    a = tmp_path / "a"; a.write_text("x")
    b = tmp_path / "b"                 # absent
    results = remove.delete_paths([a, b])
    assert not a.exists()
    assert (a, True) in results
    assert (b, False) in results


def _common(tmp_path, **overrides):
    base = dict(
        config_path=tmp_path / "config.toml",
        env_path=tmp_path / ".env",
        seen_path=tmp_path / "seen.json",
        feed_path=tmp_path / "feed.xml",
        install_dir=tmp_path,
        select_fn=lambda targets: ["runtime"],
        confirm_input_fn=lambda prompt: "yes",
        crontab_read=lambda: "",
        crontab_write=lambda text: None,
    )
    base.update(overrides)
    return base


def test_run_remove_wrong_token_deletes_nothing(tmp_path):
    cfg = tmp_path / "config.toml"; cfg.write_text("x")
    rc = remove.run_remove(**_common(
        tmp_path, confirm_input_fn=lambda prompt: "nope"))
    assert rc == 1
    assert cfg.exists()


def test_run_remove_correct_token_deletes_runtime_and_skips_absent(tmp_path):
    cfg = tmp_path / "config.toml"; cfg.write_text("x")
    seen = tmp_path / "seen.json"; seen.write_text("[]")
    feed = tmp_path / "feed.xml"; feed.write_text("x")
    # .env left absent on purpose
    rc = remove.run_remove(**_common(tmp_path))
    assert rc == 0
    assert not cfg.exists() and not seen.exists() and not feed.exists()


def test_run_remove_cron_selection_rewrites_crontab(tmp_path):
    written = {}
    crontab = "0 5 * * * /backup\n0 */6 * * * cd /opt/lootscout && uv run lootscout\n"
    rc = remove.run_remove(**_common(
        tmp_path,
        select_fn=lambda targets: ["cron"],
        crontab_read=lambda: crontab,
        crontab_write=lambda text: written.update(text=text)))
    assert rc == 0
    assert "lootscout" not in written["text"]
    assert "/backup" in written["text"]


def test_run_remove_install_dir_prints_rm_and_does_not_delete(tmp_path, capsys):
    rc = remove.run_remove(**_common(
        tmp_path,
        select_fn=lambda targets: ["install_dir"],
        confirm_input_fn=lambda prompt: tmp_path.name))  # dir-name token
    out = capsys.readouterr().out
    assert rc == 0
    assert tmp_path.exists()                       # we never rm our own dir
    assert f"rm -rf {tmp_path}" in out
