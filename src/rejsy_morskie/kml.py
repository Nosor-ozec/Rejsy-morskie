from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, ElementTree

from .models import Leg, PortCall, Voyage

NAMED_COLORS = {
    "biały": "FFFFFF",
    "czarny": "000000",
    "czerwony": "D32F2F",
    "fioletowy": "6A1B9A",
    "niebieski": "0057B8",
    "pomarańczowy": "EF6C00",
    "szary": "757575",
    "zielony": "2E7D32",
    "żółty": "F9A825",
}


def kml_color(rgb: str) -> str:
    normalized = rgb.strip().casefold()
    value = NAMED_COLORS.get(normalized, rgb.removeprefix("#"))
    if len(value) != 6:
        raise ValueError(
            "Kolor trasy musi być nazwą, np. Niebieski, albo mieć format #RRGGBB"
        )
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(
            "Kolor trasy musi być nazwą, np. Niebieski, albo mieć format #RRGGBB"
        ) from error
    return "ff" + value[4:6] + value[2:4] + value[0:2]


def export_kml(
    voyage: Voyage,
    calls: list[PortCall],
    legs_with_coordinates: list[tuple[Leg, list[tuple[float, float]]]],
    output_path,
) -> None:
    root = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(root, "Document")
    SubElement(document, "name").text = voyage.name

    style = SubElement(document, "Style", id="route")
    line_style = SubElement(style, "LineStyle")
    SubElement(line_style, "color").text = kml_color(voyage.route_color)
    SubElement(line_style, "width").text = "4"

    ports_folder = SubElement(document, "Folder")
    SubElement(ports_folder, "name").text = "Porty"
    for call in calls:
        if call.lat is None or call.lon is None:
            continue
        marker = SubElement(ports_folder, "Placemark")
        SubElement(marker, "name").text = call.port
        point = SubElement(marker, "Point")
        SubElement(point, "coordinates").text = f"{call.lon},{call.lat},0"

    legs_folder = SubElement(document, "Folder")
    SubElement(legs_folder, "name").text = "Etapy"
    for leg, coordinates in legs_with_coordinates:
        marker = SubElement(legs_folder, "Placemark")
        SubElement(marker, "name").text = leg.name
        description = [
            leg.day_range,
            f"{leg.date_from.isoformat()} – {leg.date_to.isoformat()}",
        ]
        if leg.distance_nm is not None:
            description.append(f"Dystans: {leg.distance_nm:.1f} mil morskich")
        SubElement(marker, "description").text = "\n".join(description)
        SubElement(marker, "styleUrl").text = "#route"
        line = SubElement(marker, "LineString")
        SubElement(line, "tessellate").text = "1"
        SubElement(line, "coordinates").text = " ".join(
            f"{lon},{lat},0" for lon, lat in coordinates
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)
