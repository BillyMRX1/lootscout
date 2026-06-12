from pathlib import Path
from xml.etree import ElementTree as ET
from free_checker.channels.rss import RssChannel
from free_checker.channels.base import Giveaway

def g(i, t): return Giveaway(i, t, "$9", "https://img", "desc", "https://u", "N/A", "PC")

def test_write_full_produces_valid_rss(tmp_path):
    out = tmp_path / "feed.xml"
    RssChannel(output_path=out, site_url="https://x/feed.xml").write_full([g(1, "Eets")])
    tree = ET.parse(out)
    root = tree.getroot()
    assert root.tag == "rss"
    items = root.findall("./channel/item")
    assert len(items) == 1
    assert items[0].find("title").text == "Eets"
    assert items[0].find("link").text == "https://u"

def test_write_full_empty_still_writes_channel(tmp_path):
    out = tmp_path / "feed.xml"
    RssChannel(out, "https://x/feed.xml").write_full([])
    root = ET.parse(out).getroot()
    assert root.findall("./channel/item") == []

def test_notify_new_is_noop(tmp_path):
    RssChannel(tmp_path / "f.xml", "https://x").notify_new([g(1, "Eets")])  # no raise
