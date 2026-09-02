import json
from pathlib import Path
from uuid import uuid4

import pytest
from openpyxl import Workbook

from rejsy_morskie.passages import generate_passages, read_passages


MESSINA = [
    [15.61879, 38.14900], [15.61625, 38.16500], [15.61378, 38.18100],
    [15.61486, 38.19500], [15.61650, 38.21100], [15.61798, 38.23070],
    [15.63144, 38.23800], [15.65029, 38.24500], [15.66914, 38.25200],
    [15.68799, 38.25900], [15.69622, 38.26600], [15.69986, 38.27050],
]


def workbook(path: Path, rows):
    book = Workbook()
    sheet = book.active
    sheet.title = "Lokalizacje"
    sheet.append(["Nazwa", "Kraj", "Lat", "Lon", "Typ", "Uwagi", "Przejscie", "Przejscie_lp", "Przejscie_status"])
    for row in rows:
        sheet.append(row)
    book.save(path)


def temporary_directory() -> Path:
    path = Path(__file__).resolve().parent / "_work" / uuid4().hex
    path.mkdir(parents=True)
    return path


def test_generator_groups_and_sorts_points_without_using_ordinary_locations():
    tmp_path = temporary_directory()
    source = tmp_path / "rejsy.xlsx"
    workbook(source, [
        ["Port", "X", 1, 2, "Port", "", "", ""],
        ["B", "", 20, 30, "Punkt_trasy", "", "Test", 2],
        ["A", "", 10, 15, "Punkt_trasy", "", "Test", 1],
    ])
    passages = read_passages(source)
    assert len(passages) == 1
    assert passages[0]["name"] == "Test"
    assert passages[0]["status"] == "stable"
    assert passages[0]["waypoints"] == [[15.0, 10.0], [30.0, 20.0]]
    assert passages[0]["observed_graph_delta"] == {"nodes": 2, "edges": 11}


@pytest.mark.parametrize("rows,fragment", [
    ([['A', '', None, 10, '', '', 'Test', 1], ['B', '', 2, 20, '', '', 'Test', 2]], "Lat"),
    ([['A', '', 1, 10, '', '', 'Test', 1], ['B', '', 2, 20, '', '', 'Test', 3]], "ciąg 1..2"),
    ([['A', '', 1, 10, '', '', 'Test', 1], ['B', '', 2, 20, '', '', 'Test', 1]], "unikalne"),
    ([['A', '', 1, 10, '', '', 'Test', '']], "muszą być podane razem"),
])
def test_generator_rejects_incomplete_or_ambiguous_passage_data(rows, fragment):
    tmp_path = temporary_directory()
    source = tmp_path / "rejsy.xlsx"
    workbook(source, rows)
    with pytest.raises(ValueError, match=fragment):
        read_passages(source)


def test_generation_is_deterministic_and_atomic():
    tmp_path = temporary_directory()
    source = tmp_path / "rejsy.xlsx"
    output = tmp_path / "passages.json"
    workbook(source, [
        ["A", "", 1, 10, "", "", "Test", 1],
        ["B", "", 2, 20, "", "", "Test", 2],
    ])
    generate_passages(source, output)
    first = output.read_bytes()
    generate_passages(source, output)
    assert output.read_bytes() == first
    assert json.loads(first)["generated_from"] == "routes/rejsy.xlsx:Lokalizacje"


def test_generator_reads_development_status_and_requires_consistency():
    tmp_path = temporary_directory()
    source = tmp_path / "rejsy.xlsx"
    workbook(source, [
        ["A", "", 1, 10, "", "", "Test", 1, "development"],
        ["B", "", 2, 20, "", "", "Test", 2, "development"],
    ])
    assert read_passages(source)[0]["status"] == "development"

    inconsistent = tmp_path / "inconsistent.xlsx"
    workbook(inconsistent, [
        ["A", "", 1, 10, "", "", "Test", 1, "stable"],
        ["B", "", 2, 20, "", "", "Test", 2, "development"],
    ])
    with pytest.raises(ValueError, match="ten sam Przejscie_status"):
        read_passages(inconsistent)


def test_project_workbook_recreates_existing_messina_geometry():
    root = Path(__file__).resolve().parents[1]
    passages = read_passages(root / "routes" / "rejsy.xlsx")
    by_name = {passage["name"]: passage for passage in passages}
    beagle = by_name["Beagle"]
    messina = by_name["Strait of Messina"]
    assert len(beagle["waypoints"]) >= 2
    assert beagle["status"] == "development"
    assert beagle["observed_graph_delta"] == {
        "nodes": len(beagle["waypoints"]),
        "edges": len(beagle["waypoints"]) + 9,
    }
    assert messina["waypoints"] == MESSINA
    assert messina["status"] == "stable"
    assert messina["observed_graph_delta"] == {"nodes": 12, "edges": 21}
