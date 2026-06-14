from lootscout import wizard


def test_resolve_platforms_expands_groups():
    assert wizard.resolve_platforms(["Xbox"]) == ["xbox-one", "xbox-series-xs"]
    assert wizard.resolve_platforms(["PlayStation"]) == ["ps4", "ps5"]


def test_resolve_platforms_all_returns_every_slug():
    result = wizard.resolve_platforms([wizard.ALL_PLATFORMS])
    assert "pc" in result and "ps5" in result and "switch" in result
    assert "android" in result and "ios" in result and "vr" in result
    # the "All" sentinel itself is never a slug
    assert wizard.ALL_PLATFORMS not in result


def test_resolve_platforms_dedupes_and_preserves_order():
    result = wizard.resolve_platforms(["PC (Steam/Epic/GOG/itch/…)", "Xbox"])
    assert result == ["pc", "xbox-one", "xbox-series-xs"]


def test_resolve_types_maps_labels_to_slugs():
    assert wizard.resolve_types(["Free games"]) == ["game"]
    assert wizard.resolve_types(["Free loot"]) == ["loot"]
    assert wizard.resolve_types(["Beta access"]) == ["beta"]


def test_resolve_types_all_returns_every_type():
    assert wizard.resolve_types([wizard.ALL_TYPES]) == ["game", "loot", "beta"]
