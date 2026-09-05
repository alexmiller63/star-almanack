from pathlib import Path

p = Path("render_observer_views.py")
s = p.read_text(encoding="utf-8")

old = """    \"finder\": ViewPreset(\n        key=\"finder\",\n        title=\"Finder chart\",\n        field_deg=10.0,\n        limiting_mag=7.0,\n    ),\n"""
new = """    \"finder\": ViewPreset(\n        key=\"finder\",\n        title=\"Finder chart\",\n        field_deg=30.0,\n        limiting_mag=7.0,\n    ),\n"""
if old not in s:
    raise SystemExit("finder preset block not found")
s = s.replace(old, new, 1)

old = """def visible_stars(stars: Iterable[Star], target: Target, preset: ViewPreset) -> list[Star]:\n    radius = preset.field_deg / 2.0\n    return [\n        star\n        for star in stars\n        if star.mag <= preset.limiting_mag\n        and angular_separation_deg(\n            star.ra_deg, star.dec_deg, target.ra_deg, target.dec_deg\n        )\n        <= radius * 1.05\n    ]\n"""
new = """def view_center(\n    target: Target, stars: Iterable[Star], preset: ViewPreset\n) -> tuple[float, float]:\n    \"\"\"Return plot center; M35 finder includes Castor and Pollux.\"\"\"\n    if preset.key == \"finder\" and target.designation == \"M35\":\n        anchors = [star for star in stars if star.label in {\"Castor\", \"Pollux\"}]\n        if len(anchors) == 2:\n            # Average unit vectors so RA wrap is handled correctly.\n            vectors = []\n            for ra_deg, dec_deg in [(target.ra_deg, target.dec_deg)] + [\n                (star.ra_deg, star.dec_deg) for star in anchors\n            ]:\n                ra = math.radians(ra_deg)\n                dec = math.radians(dec_deg)\n                vectors.append((\n                    math.cos(dec) * math.cos(ra),\n                    math.cos(dec) * math.sin(ra),\n                    math.sin(dec),\n                ))\n            x = sum(v[0] for v in vectors)\n            y = sum(v[1] for v in vectors)\n            z = sum(v[2] for v in vectors)\n            center_ra = math.degrees(math.atan2(y, x)) % 360.0\n            center_dec = math.degrees(math.atan2(z, math.hypot(x, y)))\n            return center_ra, center_dec\n    return target.ra_deg, target.dec_deg\n\n\ndef visible_stars(\n    stars: Iterable[Star], center: tuple[float, float], preset: ViewPreset\n) -> list[Star]:\n    radius = preset.field_deg / 2.0\n    center_ra, center_dec = center\n    return [\n        star\n        for star in stars\n        if star.mag <= preset.limiting_mag\n        and angular_separation_deg(\n            star.ra_deg, star.dec_deg, center_ra, center_dec\n        )\n        <= radius * 1.05\n    ]\n"""
if old not in s:
    raise SystemExit("visible_stars block not found")
s = s.replace(old, new, 1)

old = """    selected = visible_stars(stars, target, preset)\n    projected: list[tuple[float, float, Star]] = []\n    for star in selected:\n        xy = tangent_plane(star.ra_deg, star.dec_deg, target.ra_deg, target.dec_deg)\n"""
new = """    center_ra, center_dec = view_center(target, stars, preset)\n    selected = visible_stars(stars, (center_ra, center_dec), preset)\n    projected: list[tuple[float, float, Star]] = []\n    for star in selected:\n        xy = tangent_plane(star.ra_deg, star.dec_deg, center_ra, center_dec)\n"""
if old not in s:
    raise SystemExit("render center block not found")
s = s.replace(old, new, 1)

old = """    ax.scatter([0.0], [0.0], marker=\"+\", s=100)\n\n    target_label = target.designation\n"""
new = """    target_xy = tangent_plane(\n        target.ra_deg, target.dec_deg, center_ra, center_dec\n    )\n    if preset.key == \"finder\" and target_xy is not None:\n        tx, ty = target_xy\n        target_circle = plt.Circle((tx, ty), 0.45, fill=False, linewidth=1.0)\n        ax.add_patch(target_circle)\n        ax.annotate(\n            target.designation,\n            (tx, ty),\n            xytext=(6, 6),\n            textcoords=\"offset points\",\n            fontsize=8,\n        )\n\n    target_label = target.designation\n"""
if old not in s:
    raise SystemExit("target plus marker block not found")
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("refined render_observer_views.py")
