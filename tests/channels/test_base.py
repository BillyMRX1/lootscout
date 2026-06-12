from free_checker.channels.base import Giveaway

def test_giveaway_from_api_maps_fields():
    raw = {
        "id": 3684,
        "title": "Eets (Steam) Giveaway",
        "worth": "$9.99",
        "image": "https://x/img.jpg",
        "description": "Claim Eets for free.",
        "open_giveaway_url": "https://x/open/eets",
        "end_date": "2026-06-15 23:59:00",
        "platforms": "PC, Steam",
    }
    g = Giveaway.from_api(raw)
    assert g.id == 3684
    assert g.title == "Eets (Steam) Giveaway"
    assert g.url == "https://x/open/eets"
    assert g.end_date == "2026-06-15 23:59:00"

def test_giveaway_tolerates_na_end_date():
    raw = {"id": 1, "title": "T", "worth": "N/A", "image": "", "description": "",
           "open_giveaway_url": "u", "end_date": "N/A", "platforms": "PC"}
    g = Giveaway.from_api(raw)
    assert g.end_date == "N/A"
