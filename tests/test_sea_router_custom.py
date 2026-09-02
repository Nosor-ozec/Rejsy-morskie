import json
import hashlib
import os
import re
import subprocess
import struct
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
CUSTOM = ROOT / "sea-router-custom"


def load_json(name: str):
    return json.loads((CUSTOM / name).read_text(encoding="utf-8"))


def test_custom_passage_is_small_complete_and_matches_observed_delta():
    config = load_json("passages.json")
    assert config["schema_version"] == 1
    assert config["coordinate_order"] == "longitude_latitude"
    assert config["generated_from"] == "routes/rejsy.xlsx:Lokalizacje"
    passages = {item["id"]: item for item in config["passages"]}
    beagle = passages["beagle"]
    passage = passages["strait-of-messina"]
    assert len(beagle["waypoints"]) >= 2
    assert beagle["status"] == "development"
    assert beagle["observed_graph_delta"] == {
        "nodes": len(beagle["waypoints"]),
        "edges": len(beagle["waypoints"]) + 9,
    }
    assert len(passage["waypoints"]) == 12
    assert passage["status"] == "stable"
    assert passage["observed_graph_delta"] == {"nodes": 12, "edges": 21}
    assert passage["injection"]["endpoint_nearest_nodes"] == 5
    assert passage["injection"]["maximum_endpoint_connection_km"] == 100.0
    for lon, lat in passage["waypoints"]:
        assert -180 <= lon <= 180
        assert -90 <= lat <= 90
    for custom in config["passages"]:
        assert len(custom["waypoints"]) >= 2
        assert custom["observed_graph_delta"] == {
            "nodes": len(custom["waypoints"]),
            "edges": len(custom["waypoints"]) + 9,
        }


def test_lock_pins_reproducible_source_data_toolchain_and_result():
    lock = load_json("sea-router.lock.json")
    assert lock["upstream"]["commit"] == "65cc022269d42f69ffad14fb1b69cce641ee6170"
    assert lock["toolchain"]["rustup_toolchain"] == "1.97.1-x86_64-pc-windows-msvc"
    assert lock["graph_generation"]["depth"] == 16
    assert len(lock["upstream"]["critical_git_blob_sha1"]) >= 10
    for object_id in lock["upstream"]["critical_git_blob_sha1"].values():
        assert re.fullmatch(r"[0-9a-f]{40}", object_id)
    assert (
        lock["upstream"]["critical_git_blob_sha1"]["rust/src/server.rs"]
        == "c104f6051514b95611b2c174f59f21275a85021f"
    )
    assert len(lock["land_data"]["gzip_sha256"]) == 64
    assert len(lock["land_data"]["uncompressed_sha256"]) == 64
    assert lock["expected_custom_build"]["node_count"] == 5_786_558
    assert lock["expected_custom_build"]["edge_count"] == 9_379_147
    assert len(lock["expected_custom_build"]["graph_sha256"]) == 64
    semantic = lock["expected_custom_build"]["semantic_graph"]
    assert semantic["format_version"] == 1
    assert re.fullmatch(r"[0-9A-F]{64}", semantic["ordered_nodes_sha256"])
    assert re.fullmatch(r"[0-9A-F]{64}", semantic["sorted_edges_sha256"])


def test_regression_suite_checks_five_passages_and_has_future_slots():
    config = load_json("regression-cases.json")
    enabled = {case["id"]: case for case in config["cases"] if case["enabled"]}
    planned = {case["id"] for case in config["cases"] if not case["enabled"]}
    assert set(enabled) == {"messina", "suez", "panama", "corinth", "beagle"}
    assert planned == {"cockburn", "magdalena", "magellan-entry"}

    for case in enabled.values():
        assert len(case["start"]) == len(case["end"]) == 2
        assert len(case["allowed_bbox"]) == 4
        assert case["max_detour_ratio"] <= 1.5
        assert len(case["checkpoints"]) >= 2
        assert all(checkpoint["max_distance_km"] > 0 for checkpoint in case["checkpoints"])

    beagle = enabled["beagle"]
    assert beagle["start"] == [-67.6170, -54.9330]
    assert beagle["end"] == [-68.3084, -54.8073]
    assert beagle["max_detour_ratio"] == 1.35
    assert beagle["allowed_bbox"] == [-68.38, -54.98, -67.55, -54.76]
    assert [item["point"] for item in beagle["checkpoints"]] == [
        [-67.6400, -54.9200], [-67.7000, -54.9000],
        [-67.8500, -54.8650], [-68.05522, -54.85415]
    ]


def test_apply_script_injects_messina_once_into_clean_canals_file():
    source = ROOT / "tests" / "_work" / uuid4().hex / "source"
    canals = source / "rust" / "src" / "canals.rs"
    canals.parent.mkdir(parents=True)
    canals.write_text(
        'pub struct CanalPassage { pub name: &\'static str, pub waypoints: &\'static [[f64; 2]] }\n'
        'pub static CANALS: &[CanalPassage] = &[\n];\n',
        encoding="utf-8",
    )
    script = CUSTOM / "scripts" / "Apply-CustomPassages.ps1"
    command = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script), "-SourceRoot", str(source),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    updated = canals.read_text(encoding="utf-8")
    assert updated.count('name: "Strait of Messina"') == 1
    assert updated.count("[15.61879, 38.14900]") == 1
    assert updated.count("[15.69986, 38.27050]") == 1

    repeated = subprocess.run(command, capture_output=True, text=True, check=False)
    assert repeated.returncode != 0
    assert "Bazowy kod zawiera" in repeated.stderr
    assert "odmowa podw" in repeated.stderr
    assert "wstrzykni" in repeated.stderr
    assert "odmowa" in repeated.stderr


def test_powershell_scripts_parse_without_execution():
    for script in (CUSTOM / "scripts").glob("*.ps1"):
        command = "$null = [scriptblock]::Create([IO.File]::ReadAllText($env:SCRIPT_TO_PARSE))"
        environment = os.environ.copy()
        environment["SCRIPT_TO_PARSE"] = str(script)
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        assert result.returncode == 0, f"{script.name}: {result.stderr}"


def test_custom_module_contains_no_heavy_or_generated_artifacts():
    forbidden_suffixes = {".exe", ".gz", ".pbf", ".osm"}
    for path in CUSTOM.rglob("*"):
        if not path.is_file():
            continue
        assert path.suffix.lower() not in forbidden_suffixes
        assert "sea-graph" not in path.name.lower()
        assert path.stat().st_size < 1_000_000


def test_cmd_wrapper_is_safe_and_exposes_existing_validate_mode():
    wrapper = (ROOT / "Install-SeaRouter.cmd").read_text(encoding="utf-8")
    normalized = wrapper.casefold()
    assert "%~dp0" in wrapper
    assert "sea-router-custom\\scripts\\Install-SeaRouter.ps1" in wrapper
    assert 'set "TARGET=E:\\sea-router"' in wrapper
    assert "-executionpolicy bypass" in normalized
    assert "-validateonly" in normalized
    assert "pause" in normalized
    assert "exit /b %result%" in normalized
    assert "remove-item" not in normalized
    assert "rmdir" not in normalized


def test_passage_update_wrapper_is_atomic_and_exposes_test_mode():
    wrapper = (ROOT / "Aktualizuj-Przejscia-SeaRouter.cmd").read_text(encoding="utf-8")
    normalized = wrapper.casefold()
    assert "%~dp0" in wrapper
    assert "Update-SeaRouterPassages.ps1" in wrapper
    assert "-executionpolicy bypass" in normalized
    assert "-validateonly" in normalized
    assert "pause" in normalized
    assert "remove-item" not in normalized
    updater = (CUSTOM / "scripts" / "Update-SeaRouterPassages.ps1").read_text(encoding="utf-8-sig")
    assert updater.index("& $installer -TargetPath $candidate") < updater.index("Move-Item -LiteralPath $target")
    assert "sea-router-update-backup-" in updater
    assert "[switch]$NoActivate" in updater
    assert "Kandydat przeszedł walidację" in updater
    assert "przywrócono poprzednią instalację" in updater
    assert "Get-RegressionPolicy" in updater
    assert "Regresje diagnostyczne development" in updater


def run_regression_policy(
    tmp_path: Path, passages: dict, cases: dict, *, without_baseline: bool = True
):
    passages_path = tmp_path / "passages.json"
    cases_path = tmp_path / "cases.json"
    passages_path.write_text(json.dumps(passages), encoding="utf-8")
    cases_path.write_text(json.dumps(cases), encoding="utf-8")
    environment = os.environ.copy()
    environment.update({
        "POLICY_SCRIPT": str(CUSTOM / "scripts" / "RegressionPolicy.ps1"),
        "PASSAGES": str(passages_path),
        "CASES": str(cases_path),
    })
    baseline_argument = " -AlwaysRequired @()" if without_baseline else ""
    command = (
        ". $env:POLICY_SCRIPT; "
        "$p=Get-Content $env:PASSAGES -Raw|ConvertFrom-Json; "
        "$c=Get-Content $env:CASES -Raw|ConvertFrom-Json; "
        f"Get-RegressionPolicy -Passages $p -Cases $c{baseline_argument} | ConvertTo-Json -Compress"
    )
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, check=False, env=environment,
    )


def test_development_without_regression_is_allowed_and_stable_without_it_fails():
    root = ROOT / "tests" / "_work" / uuid4().hex
    root.mkdir(parents=True)
    cases = {"cases": []}
    development = {"passages": [{"id": "test", "name": "Test", "status": "development"}]}
    allowed = run_regression_policy(root, development, cases)
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert json.loads(allowed.stdout) == {"RequiredIds": [], "DiagnosticIds": []}

    stable = {"passages": [{"id": "test", "name": "Test", "status": "stable"}]}
    blocked = run_regression_policy(root, stable, cases)
    assert blocked.returncode != 0
    assert "nie ma aktywnego testu regresji 'test'" in blocked.stderr


def test_project_policy_keeps_messina_required_and_beagle_diagnostic():
    root = ROOT / "tests" / "_work" / uuid4().hex
    root.mkdir(parents=True)
    cases = load_json("regression-cases.json")
    beagle_case = next(item for item in cases["cases"] if item["id"] == "beagle")
    assert [-67.7, -54.9] in [item["point"] for item in beagle_case["checkpoints"]]
    result = run_regression_policy(
        root, load_json("passages.json"), cases,
        without_baseline=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    policy = json.loads(result.stdout)
    assert policy["RequiredIds"] == ["messina", "suez", "panama", "corinth"]
    assert policy["DiagnosticIds"] == ["beagle"]


def test_failed_development_regression_warns_but_stable_failure_blocks():
    class RouteHandler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            body = json.dumps({
                "features": [{
                    "properties": {"name": "final"},
                    "geometry": {"type": "LineString", "coordinates": [[0, 0], [0.1, 0]]},
                }]
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), RouteHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = ROOT / "tests" / "_work" / uuid4().hex
    root.mkdir(parents=True)
    cases_path = root / "cases.json"
    common = {
        "enabled": True, "start": [0, 0], "end": [0.1, 0], "penalty": 1,
        "max_detour_ratio": 2, "allowed_bbox": [-1, -1, 1, 1],
    }
    cases_path.write_text(json.dumps({
        "schema_version": 1, "coordinate_order": "longitude_latitude",
        "cases": [
            {**common, "id": "stable-good", "name": "Stable", "checkpoints": [{"point": [0.05, 0], "max_distance_km": 10}]},
            {**common, "id": "development-bad", "name": "Development", "checkpoints": [{"point": [10, 10], "max_distance_km": 1}]},
        ],
    }), encoding="utf-8")
    environment = os.environ.copy()
    environment.update({
        "TEST_SCRIPT": str(CUSTOM / "scripts" / "Test-SeaRouter.ps1"),
        "CASES": str(cases_path),
        "BASE_URL": f"http://127.0.0.1:{server.server_port}",
    })
    try:
        diagnostic_command = (
            "& $env:TEST_SCRIPT -BaseUrl $env:BASE_URL -CasesPath $env:CASES "
            "-RequiredCaseIds @('stable-good') -DiagnosticCaseIds @('development-bad')"
        )
        diagnostic = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", diagnostic_command],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            check=False, env=environment, timeout=20,
        )
        assert diagnostic.returncode == 0, diagnostic.stdout + diagnostic.stderr
        assert "development" in (diagnostic.stdout + diagnostic.stderr).casefold()
        assert "nie jest blokowana" in (diagnostic.stdout + diagnostic.stderr)

        blocking_command = (
            "& $env:TEST_SCRIPT -BaseUrl $env:BASE_URL -CasesPath $env:CASES "
            "-RequiredCaseIds @('stable-good','development-bad')"
        )
        blocking = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", blocking_command],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            check=False, env=environment, timeout=20,
        )
        assert blocking.returncode != 0
        assert "Testy regresji nie przeszły" in blocking.stderr
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_installer_refuses_existing_target_before_tool_preparation():
    installer = (CUSTOM / "scripts" / "Install-SeaRouter.ps1").read_text(
        encoding="utf-8-sig"
    )
    refusal = installer.index("-not $ValidateOnly -and (Test-Path")
    tool_installation = installer.index("if ($InstallMissingTools)")
    source_download = installer.index("Invoke-WebRequest -Uri")
    assert refusal < tool_installation < source_download


def run_hash_validation(command: str):
    environment = os.environ.copy()
    environment["HASH_VALIDATION_SCRIPT"] = str(
        CUSTOM / "scripts" / "HashValidation.ps1"
    )
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def test_git_object_id_allows_only_safe_trim_normalization():
    object_id = "c104f6051514b95611b2c174f59f21275a85021f"
    command = (
        ". $env:HASH_VALIDATION_SCRIPT; "
        f"Assert-GitObjectIdMatch -Actual '{object_id}' "
        f'-Expected "  {object_id}`r`n" -Label test'
    )
    result = run_hash_validation(command)
    assert result.returncode == 0, result.stdout + result.stderr


def test_git_object_id_rejects_a_real_one_character_difference():
    actual = "c104f6051514b95611b2c174f59f21275a85021f"
    different = "c104f6051514f95611b2c174f59f21275a85021f"
    command = (
        ". $env:HASH_VALIDATION_SCRIPT; "
        f"Assert-GitObjectIdMatch -Actual '{actual}' "
        f"-Expected '{different}' -Label test"
    )
    result = run_hash_validation(command)
    assert result.returncode != 0
    assert actual in result.stderr
    assert different in result.stderr


def test_semantic_graph_hash_ignores_edge_json_order_but_rejects_edge_changes():
    root = ROOT / "tests" / "_work" / uuid4().hex
    root.mkdir(parents=True)
    tool_source = CUSTOM / "tools" / "GraphSemanticCanonicalizer.rs"
    tool = root / "GraphSemanticCanonicalizer.exe"
    build = subprocess.run(
        [
            "rustup.exe",
            "run",
            "1.97.1-x86_64-pc-windows-msvc",
            "rustc",
            "--edition=2021",
            "-O",
            str(tool_source),
            "-o",
            str(tool),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stdout + build.stderr

    nodes = [0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0]
    edges = [[0, 1, 5], [1, 2, 7], [0, 2, 9]]

    def fingerprint(name: str, edge_records):
        graph = root / f"{name}.json"
        graph.write_text(
            json.dumps(
                {
                    "nodes": nodes,
                    "nodeCount": 3,
                    "edges": [number for edge in edge_records for number in edge],
                    "edgeCount": len(edge_records),
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        node_output = root / f"{name}-nodes.bin"
        edge_output = root / f"{name}-edges.bin"
        result = subprocess.run(
            [str(tool), str(graph), str(node_output), str(edge_output)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return (
            hashlib.sha256(node_output.read_bytes()).hexdigest(),
            hashlib.sha256(edge_output.read_bytes()).hexdigest(),
        )

    original = fingerprint("original", edges)
    reordered = fingerprint("reordered", [edges[2], edges[0], edges[1]])
    changed = fingerprint("changed", [edges[0], [1, 2, 8], edges[2]])
    missing = fingerprint("missing", [edges[0], edges[2]])

    assert reordered == original
    assert changed[0] == original[0]
    assert changed[1] != original[1]
    assert missing[0] == original[0]
    assert missing[1] != original[1]


def test_process_cleanup_stops_running_process_and_accepts_finished_process():
    helper = CUSTOM / "scripts" / "ProcessCleanup.ps1"
    command = (
        ". $env:PROCESS_CLEANUP_SCRIPT; "
        "$running = Start-Process -FilePath powershell.exe "
        "-ArgumentList '-NoProfile -Command Start-Sleep -Seconds 30' "
        "-PassThru -WindowStyle Hidden; "
        "Stop-TestServerProcess -Process $running; "
        "if (-not $running.HasExited) { throw 'Proces nadal działa.' }; "
        "$finished = Start-Process -FilePath cmd.exe "
        "-ArgumentList '/d /c exit 0' -PassThru -WindowStyle Hidden; "
        "$finished.WaitForExit(); "
        "Stop-TestServerProcess -Process $finished; "
        "if ($finished.ExitCode -ne 0) { throw 'Nieprawidłowy kod procesu.' }"
    )
    environment = os.environ.copy()
    environment["PROCESS_CLEANUP_SCRIPT"] = str(helper)
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_custom_graph_validation_accepts_exact_passage_and_rejects_wrong_attachment():
    root = ROOT / "tests" / "_work" / uuid4().hex
    root.mkdir(parents=True)
    nodes_path = root / "nodes.bin"
    edges_path = root / "edges.bin"
    passages_path = root / "passages.json"
    nodes = [(0.0, 0.0, 16.0), (1.0, 1.0, 16.0), (10.0, 20.0, 1.0), (11.0, 21.0, 1.0), (12.0, 22.0, 1.0)]
    passages_path.write_text(json.dumps({"passages": [{"name": "Test", "waypoints": [[10, 20], [11, 21], [12, 22]]}]}), encoding="utf-8")
    nodes_path.write_bytes(b"SRN1" + struct.pack("<Q", len(nodes)) + b"".join(struct.pack("<ddd", *node) for node in nodes))

    base = [(0, 1, 1)]
    valid_custom = [(2, 3, 1), (3, 4, 1)] + [(2, 0, 1)] * 5 + [(4, 1, 1)] * 5

    def write_edges(records):
        ordered = sorted(records)
        edges_path.write_bytes(b"SRE1" + struct.pack("<Q", len(ordered)) + b"".join(struct.pack("<III", *edge) for edge in ordered))

    environment = os.environ.copy()
    environment.update({"GRAPH_VALIDATION": str(CUSTOM / "scripts" / "GraphValidation.ps1"), "NODES": str(nodes_path), "EDGES": str(edges_path), "PASSAGES": str(passages_path)})
    command = ". $env:GRAPH_VALIDATION; $p=(Get-Content $env:PASSAGES -Raw|ConvertFrom-Json).passages; Assert-CustomPassageGraph -CanonicalNodes $env:NODES -CanonicalEdges $env:EDGES -Passages $p -BaseNodeCount 2 -BaseEdgeCount 1"
    write_edges(base + valid_custom)
    valid = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command], capture_output=True, text=True, env=environment)
    assert valid.returncode == 0, valid.stdout + valid.stderr

    wrong_custom = valid_custom.copy()
    wrong_custom[2] = (3, 0, 1)
    write_edges(base + wrong_custom)
    invalid = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command], capture_output=True, text=True, env=environment)
    assert invalid.returncode != 0
    assert "punktem" in invalid.stderr
