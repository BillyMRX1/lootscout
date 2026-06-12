from __future__ import annotations
from email.utils import formatdate
from pathlib import Path
from xml.etree import ElementTree as ET
from .base import Giveaway


class RssChannel:
    name = "rss"

    def __init__(self, output_path, site_url: str):
        self.output_path = Path(output_path)
        self.site_url = site_url

    def notify_new(self, games: list[Giveaway]) -> None:
        pass  # pull-only

    def write_full(self, games: list[Giveaway]) -> None:
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "Free Game Giveaways"
        ET.SubElement(channel, "link").text = self.site_url
        ET.SubElement(channel, "description").text = "Currently free games"
        ET.SubElement(channel, "lastBuildDate").text = formatdate(usegmt=True)
        for x in games:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = x.title
            ET.SubElement(item, "link").text = x.url
            ET.SubElement(item, "guid", isPermaLink="false").text = str(x.id)
            ET.SubElement(item, "description").text = (
                f"{x.worth} — {x.platforms}. {x.description}")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(rss).write(self.output_path, encoding="utf-8", xml_declaration=True)
