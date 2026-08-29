from __future__ import annotations

import ast
from collections import Counter
from hashlib import sha1, sha256
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import tomllib
from types import ModuleType
import unittest
from unittest import mock
import zlib


SNAPSHOT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = SNAPSHOT_ROOT / "tools" / "generate_test_inventory.py"
INVENTORY_PATH = SNAPSHOT_ROOT / "tests" / "test-inventory.json"
PROFILES_PATH = SNAPSHOT_ROOT / "tests" / "test-profiles.toml"

BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
BASELINE_ROOT_TREE = "80feb736d287bb271905b3eb7ee3a878e026cd62"
ZERO_SHA256 = "0" * 64


def _store_git_object(git_directory: Path, kind: str, raw: bytes) -> str:
    framed = f"{kind} {len(raw)}\0".encode("ascii") + raw
    oid = sha1(framed).hexdigest()
    destination = git_directory / "objects" / oid[:2] / oid[2:]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(zlib.compress(framed))
    return oid


def _git_tree(entries: list[tuple[str, str, str]]) -> bytes:
    return b"".join(
        f"{mode} {name}\0".encode("utf-8") + bytes.fromhex(oid)
        for mode, name, oid in sorted(entries, key=lambda row: row[1])
    )

BASELINE_LOCK = {
    "test_file_count": 392,
    "stable_id_count": 2367,
    "stable_ids_sha256": "c8e6465527a9b784f4be41947745f6e86d53f45d16fd0d10955009bbb127b37b",
    "historical_id_count": 137,
    "historical_ids_sha256": "77ccf22ac1f52ebbeff7311bf2c4c1fb4f83671a5cfe10f84dbbde655ecb58a8",
    "gpu_id_count": 51,
    "gpu_ids_sha256": "896fb0675371186476df33b13eb7a5d9286dfeb01f53d37daa0f458e72021005",
    "core_id_count": 50,
    "core_ids_sha256": "38166290ad900c24a08c93f08de3376dac92a2c35544a94c3228726b01a02dfc",
    "current_id_count": 2129,
    "current_ids_sha256": "c32575a47a889e7e324db2abb56ef5c5b37295bb6a5cc3e6006cb04c767c6803",
    "explicit_exclusion_count": 0,
}

HISTORICAL_PAYLOAD_LOCKS = {
    "historical:base-source": (
        21,
        "83a33794ecf850587627ace90a9d3a208b82fcf875400ccb6ed7c5cd72cb6e81",
    ),
    "historical:v2-source": (
        8,
        "3645c2e5636e658167aafbcac4da1031ebf784416f4c12f05b56e3f9dd87fc9c",
    ),
    "historical:v2-retained": (
        5,
        "da4886b2674e687b6c336303cb430b8c4d214a1f274db2df23c4a01137415467",
    ),
    "historical:v3-source": (
        9,
        "00a4caad1791a20720d133be06f50a9a422a8b691294db4196a5780ae2100813",
    ),
    "historical:v4-positive": (
        38,
        "676f497cdedaa8958e96bfefc63808f9335f897621fb8f1d65a0835bfc4bc6f3",
    ),
    "historical:v4-authorization-negative": (
        1,
        "fa7790a99fecb14eddd78316b017ab7dc82c699866cc851e1d27b97239b52c52",
    ),
    "historical:v5-retained": (
        18,
        "f927b8680c80739d04b64c667d757377c05723ec7eab25a224ba31bacdc4843d",
    ),
    "historical:v6-phases": (
        17,
        "30d6a566cc57298e593a0fa7ac8d66890ad86cdc03df25aca2e1e9915cd7ec7d",
    ),
    "historical:v7-phases": (
        20,
        "6f62dc5b6cd8b61709d9ef148384fa9cf319d54b88281d6ea45245496852112c",
    ),
}

DECLARED_UNCONDITIONAL_SKIPS = {
    (
        "tests/test_h32_pre_bet_action_width_capacity.py::"
        "H32PreBetActionWidthCapacityTests::"
        "test_small_runtime_composition_keeps_candidate_at_current_node"
    ): (
        "sealed rejected runner is retained byte-for-byte and never rerun",
        "sealed_rejected_runner_never_rerun",
        "50af0f964e7e6b2fd708e85b3cff20b9c073c3d8cb084b65033f333fefbf6f57",
    ),
    (
        "tests/test_h32_pre_bet_initial_row_cache_seed.py::"
        "H32PreBetInitialRowCacheSeedTests::"
        "test_small_gpu_seed_round_trips_both_distinct_arms_without_optimizer_work"
    ): (
        "ADR-0281 seed authority is revoked; its GPU path is never invoked",
        "revoked_adr_0281_gpu_path_never_invoked",
        "aa949216ccc291eab69a7eca888eb7e0fa5f43c804099bf6cf51c6fde9429909",
    ),
}

PROFILE_BUDGETS = {
    "core": (180, 900, 15, 120, 1500),
    "current": (300, 7200, 15, 180, 8100),
    "historical": (900, 5400, 20, 300, 7200),
    "gpu": (300, 3600, 20, 180, 4500),
    "full": (900, 27000, 20, 300, 29000),
}

HISTORICAL_SNAPSHOTS = {
    "base_source_seal": (
        "88148da07324c13b79c72ea494b14167a975c001",
        "bc5d1952f690da5d49275344919de36224af26cb",
    ),
    "v2_source_seal": (
        "08bb6857f47f9669b8f531c65079d4decd52a573",
        "0d01a4133a4e6ab10467ad0bd298630149702a73",
    ),
    "v2_retained_rejection": (
        "3de8e0c9eebf67f2cc2573041242a869468de6e9",
        "ea80b86ac60cb324e3c18ddad83d8bbba0ade933",
    ),
    "v3_source_seal": (
        "77feb7c78990ca53e70b1302a6866fe5d781411f",
        "d26ba99c033875342a652ae352067beee1ca44ee",
    ),
    "v4_source_seal": (
        "ba6a3418b7c991238cc1a65898fd61fa03b4a3cb",
        "73b53cb04c91459e8b7028ccd292b972d2dfdf69",
    ),
    "v4_authorization_rejection": (
        "815d23c115289347e3d4028a4866eb9f87d4669a",
        "894c026603156df4bba1134ba9861e98bd3a6663",
    ),
    "v5_retained_attempt": (
        "5c0c9a401e5f2ebf59296832d954d0075c4d4624",
        "f3418410c442a4d06c62aba9777def72633ca5c5",
    ),
    "v6_source_seal": (
        "d633f3fb469a27dee688587293c6efb1d2cb2757",
        "9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2",
    ),
    "v6_authorization_rejection": (
        "cbfa3598f22c7aba7d824f71356ca156f8b01b0c",
        "9873ff13131c91b058307643dc838a8452268fbb",
    ),
    "v7_source_seal": (
        "56127da2970f5a8a8056a97a247ebe1fdf4b983b",
        "ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648",
    ),
    "v7_live_authorization": (
        "aaca2dda40e29be8ebd091d58e7853bce1c62fd8",
        "e7bd077f40b1970e9b40a83c891996ab02cd5ffd",
    ),
    "v7_retained_probe": (
        "aaca2dda40e29be8ebd091d58e7853bce1c62fd8",
        "e7bd077f40b1970e9b40a83c891996ab02cd5ffd",
    ),
}

V7_RETAINED_OVERLAYS = {
    "overlay:v7-retained:attempt": (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v7.attempt.json",
        1825,
        "ada1896f0bf63111e0c1e5e707315fbca6c13f6e2b63222805cb5ef4cb9dc413",
    ),
    "overlay:v7-retained:consumed-launch": (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v7.launch-consumed.json",
        349,
        "c3c0a34cba6a677157034d8f8109cf47edea496a33c64992293176d879a2d629",
    ),
    "overlay:v7-retained:result": (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v7.jsonl",
        7_858_857,
        "78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3",
    ),
}

STABILIZATION_TEST_FILES = (
    "tests/evidence_test_support.py",
    "tests/orchestration_test_support.py",
    "tests/test_evidence_authorization.py",
    "tests/test_evidence_errors_and_model.py",
    "tests/test_evidence_filesystem_and_git.py",
    "tests/test_evidence_import_boundary.py",
    "tests/test_evidence_manifest_generation.py",
    "tests/test_evidence_manifests.py",
    "tests/test_inventory_and_profiles.py",
    "tests/test_retained_v7_assessment.py",
    "tests/test_stabilization_boundaries.py",
    "tests/test_stabilization_verification.py",
    "tests/test_test_orchestration_child.py",
    "tests/test_test_orchestration_configuration.py",
    "tests/test_test_orchestration_engine.py",
    "tests/test_test_orchestration_environment.py",
    "tests/test_test_orchestration_guards.py",
    "tests/test_test_orchestration_historical.py",
    "tests/test_test_orchestration_import_boundary.py",
    "tests/test_test_orchestration_posix_group.py",
    "tests/test_test_orchestration_process.py",
    "tests/test_test_orchestration_protocol.py",
    "tests/test_test_orchestration_windows_job.py",
    "tests/test_test_orchestration_workspace.py",
)

_PATH_BEFORE_BOOTSTRAP = tuple(sys.path)


def _load_generator() -> ModuleType:
    if not GENERATOR_PATH.is_file():
        raise AssertionError(f"missing Task 2 generator: {GENERATOR_PATH}")
    module_name = "pontius_test_inventory_generator"
    sys.modules.pop(module_name, None)
    specification = importlib.util.spec_from_file_location(module_name, GENERATOR_PATH)
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot load Task 2 generator: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


def _load_orchestration() -> tuple[ModuleType, ModuleType, ModuleType]:
    support_path = Path(__file__).with_name("orchestration_test_support.py")
    specification = importlib.util.spec_from_file_location(
        "inventory_profile_orchestration_support", support_path
    )
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot load orchestration support: {support_path}")
    support = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(support)
    return support.load_orchestration_modules(SNAPSHOT_ROOT)


def _field(value: object, name: str) -> object:
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def _ids_digest(stable_ids: list[str] | tuple[str, ...]) -> str:
    payload = "".join(f"{stable_id}\n" for stable_id in sorted(stable_ids)).encode("utf-8")
    return sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _source(text: str) -> bytes:
    return textwrap.dedent(text).strip().encode("utf-8") + b"\n"


def _entries_by_id(document: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(row["stable_id"]): row for row in document["entries"]}


def _assignment(row: dict[str, object]) -> dict[str, object]:
    value = row.get("assignment")
    if not isinstance(value, dict):
        raise AssertionError(f"entry has no assignment: {row.get('stable_id')}")
    return value


def _method_node(relative_path: str, case_name: str, method_name: str) -> ast.FunctionDef:
    tree = ast.parse((SNAPSHOT_ROOT / relative_path).read_bytes(), filename=relative_path)
    case = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == case_name
    )
    return next(
        node
        for node in case.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


class GeneratorBootstrapTests(unittest.TestCase):
    def test_generator_loads_by_exact_path_without_mutating_sys_path(self) -> None:
        module = _load_generator()
        self.assertEqual(Path(module.__file__).resolve(), GENERATOR_PATH)
        self.assertEqual(tuple(sys.path), _PATH_BEFORE_BOOTSTRAP)

    def test_canonical_helpers_sort_ascii_and_hash_sorted_lf_terminated_ids(self) -> None:
        generator = _load_generator()
        self.assertEqual(
            generator.canonical_json_bytes({"z": 1, "a": "café"}),
            b'{"a":"caf\\u00e9","z":1}',
        )
        self.assertEqual(
            generator.stable_ids_sha256(["b", "a"]),
            "911169ddaaf146aff539f58c26c489af3b892dff0fe283c1c264c65ae5aa59a2",
        )


class AstDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = _load_generator()

    def test_discovery_is_ast_only_direct_sorted_and_records_owned_fixtures(self) -> None:
        sources = {
            "tests/test_zeta.py": _source(
                """
                import unittest
                raise RuntimeError("the scanner imported a test module")

                def setUpModule():
                    raise RuntimeError

                def tearDownModule():
                    raise RuntimeError

                class DirectTests(unittest.TestCase):
                    @classmethod
                    def setUpClass(cls):
                        raise RuntimeError

                    @classmethod
                    def tearDownClass(cls):
                        raise RuntimeError

                    def test_z(self):
                        raise RuntimeError

                    def helper(self):
                        raise RuntimeError

                    def test_a(self):
                        raise RuntimeError

                class InheritedTests(DirectTests):
                    def test_inherited_child(self):
                        raise RuntimeError

                class NotATestCase(object):
                    def test_ignored(self):
                        raise RuntimeError
                """
            ),
            "tests/test_alpha.py": _source(
                """
                import unittest
                class AlphaTests(unittest.TestCase):
                    def test_value(self):
                        pass
                """
            ),
        }

        discovered = self.generator.discover_test_sources(sources)

        self.assertEqual(_field(discovered, "test_file_count"), 2)
        items = tuple(_field(discovered, "items"))
        self.assertEqual(
            tuple(_field(item, "stable_id") for item in items),
            (
                "tests/test_alpha.py::AlphaTests::test_value",
                "tests/test_zeta.py::DirectTests::test_a",
                "tests/test_zeta.py::DirectTests::test_z",
            ),
        )
        fixtures = tuple(_field(discovered, "lifecycle_fixtures"))
        self.assertEqual(
            tuple(_field(fixture, "fixture_id") for fixture in fixtures),
            (
                "fixture:tests/test_zeta.py",
                "fixture:tests/test_zeta.py::DirectTests",
            ),
        )
        self.assertEqual(
            tuple(_field(fixtures[0], "member_ids")),
            (
                "tests/test_zeta.py::DirectTests::test_a",
                "tests/test_zeta.py::DirectTests::test_z",
            ),
        )

    def test_duplicate_stable_id_is_rejected(self) -> None:
        sources = {
            "tests/test_duplicate.py": _source(
                """
                import unittest
                class DuplicateTests(unittest.TestCase):
                    def test_value(self): pass
                    def test_value(self): pass
                """
            )
        }
        with self.assertRaisesRegex(Exception, "duplicate stable ID"):
            self.generator.discover_test_sources(sources)

    def test_unowned_class_fixture_with_no_direct_methods_is_rejected(self) -> None:
        sources = {
            "tests/test_empty.py": _source(
                """
                import unittest
                class EmptyTests(unittest.TestCase):
                    @classmethod
                    def setUpClass(cls): pass
                """
            )
        }
        with self.assertRaisesRegex(Exception, "fixture.*no direct test"):
            self.generator.discover_test_sources(sources)

        ambiguous_sources = (
            (
                "duplicate module fixture",
                """
                import unittest
                def setUpModule(): pass
                def setUpModule(): pass
                class SampleTests(unittest.TestCase):
                    def test_value(self): pass
                """,
            ),
            (
                "duplicate class fixture",
                """
                import unittest
                class SampleTests(unittest.TestCase):
                    @classmethod
                    def setUpClass(cls): pass
                    @classmethod
                    def setUpClass(cls): pass
                    def test_value(self): pass
                """,
            ),
            (
                "module lifecycle fixture has no direct test methods",
                """
                import unittest
                def tearDownModule(): pass
                class Helper: pass
                """,
            ),
            (
                "inherited or mixin fixture ownership",
                """
                import unittest
                class FixtureMixin:
                    @classmethod
                    def setUpClass(cls): pass
                class SampleTests(FixtureMixin, unittest.TestCase):
                    def test_value(self): pass
                """,
            ),
            (
                "duplicate per-test setup fixture",
                """
                import unittest
                class SampleTests(unittest.TestCase):
                    def setUp(self): pass
                    def setUp(self): pass
                    def test_value(self): pass
                """,
            ),
            (
                "duplicate per-test teardown fixture",
                """
                import unittest
                class SampleTests(unittest.TestCase):
                    def tearDown(self): pass
                    def tearDown(self): pass
                    def test_value(self): pass
                """,
            ),
        )
        for message, source in ambiguous_sources:
            with self.subTest(message=message), self.assertRaisesRegex(
                Exception,
                message,
            ):
                self.generator.discover_test_sources(
                    {"tests/test_ambiguous.py": _source(source)}
                )

        platform_sources = {
            "tests/test_platform.py": _source(
                """
                import os
                import unittest

                @unittest.skipUnless(os.name == "nt", "Windows only")
                class WindowsTests(unittest.TestCase):
                    def test_a(self): pass
                    def test_b(self): pass
                    def test_c(self): pass
                    def test_d(self): pass
                    def test_e(self): pass

                class PosixTests(unittest.TestCase):
                    @unittest.skipIf(os.name == "nt", "POSIX only")
                    def test_value(self): pass
                """
            )
        }
        platform_inventory = self.generator.build_inventory(
            platform_sources,
            platform_sources,
        )
        expectations = {
            row["stable_id"]: row["assignment"]["expectation"]
            for row in platform_inventory["entries"]
        }
        self.assertEqual(
            {row["applicable_platforms"][0] for row in expectations.values()},
            {"windows", "posix"},
        )
        self.assertEqual(
            sum(
                row["applicable_platforms"] == ["windows"]
                for row in expectations.values()
            ),
            5,
        )
        self.assertEqual(
            sum(
                row["applicable_platforms"] == ["posix"]
                for row in expectations.values()
            ),
            1,
        )

        unknown_condition = {
            "tests/test_platform.py": _source(
                """
                import unittest
                class UnknownTests(unittest.TestCase):
                    @unittest.skipIf(runtime_condition(), "dynamic")
                    def test_value(self): pass
                """
            )
        }
        with self.assertRaisesRegex(Exception, "conditional skip.*unsupported"):
            self.generator.build_inventory(
                unknown_condition,
                unknown_condition,
            )

        negated_conditions = {
            "tests/test_platform.py": _source(
                """
                import os
                import unittest
                class NegatedTests(unittest.TestCase):
                    @unittest.skipUnless(not os.name == "nt", "POSIX only")
                    def test_posix(self): pass
                    @unittest.skipIf(not os.name == "nt", "Windows only")
                    def test_windows(self): pass
                """
            )
        }
        negated = self.generator.build_inventory(
            negated_conditions,
            negated_conditions,
        )
        self.assertEqual(
            {
                row["method_name"]: row["assignment"]["expectation"]
                for row in negated["entries"]
            },
            {
                "test_posix": {
                    "kind": "platform_conditioned",
                    "applicable_platforms": ["posix"],
                    "skip_safe_reason_code": "requires_posix",
                },
                "test_windows": {
                    "kind": "platform_conditioned",
                    "applicable_platforms": ["windows"],
                    "skip_safe_reason_code": "requires_windows",
                },
            },
        )

        alias_conditions = (
            "import os\nimport unittest\nimport unittest as u\n"
            "class AliasTests(unittest.TestCase):\n"
            "    @u.skipIf(os.name == 'nt', 'alias')\n"
            "    def test_value(self): pass\n",
            "import os\nimport unittest\n"
            "from unittest import skipUnless\n"
            "class AliasTests(unittest.TestCase):\n"
            "    @skipUnless(os.name == 'nt', 'alias')\n"
            "    def test_value(self): pass\n",
            "import os\nimport unittest\n"
            "conditional = unittest.skipIf\n"
            "class AliasTests(unittest.TestCase):\n"
            "    @conditional(os.name == 'nt', 'alias')\n"
            "    def test_value(self): pass\n",
            "import os\nimport unittest\n"
            "class AliasTests(unittest.TestCase):\n"
            "    @getattr(unittest, 'skipIf')(os.name == 'nt', 'alias')\n"
            "    def test_value(self): pass\n",
        )
        for source in alias_conditions:
            with self.subTest(alias=source), self.assertRaisesRegex(
                Exception,
                "conditional skip decorator alias is unsupported",
            ):
                self.generator.discover_test_sources(
                    {"tests/test_alias.py": source.encode("utf-8")}
                )


class MaterializedOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = _load_generator()
        self.baseline_sources = {
            "tests/test_legal_river_quotient_compiled_global_separation_calibration.py": _source(
                """
                import unittest
                class CompiledGlobalSeparationSourceSealTests(unittest.TestCase):
                    @unittest.skipUnless(__import__('importlib').util.find_spec("cupy"), "gpu")
                    def test_historical_wins(self): pass
                """
            ),
            "tests/test_gpu_sample.py": _source(
                """
                import importlib.util
                import unittest
                @unittest.skipUnless(importlib.util.find_spec("cupy"), "gpu")
                class GpuSampleTests(unittest.TestCase):
                    def test_first(self): pass
                    def test_second(self): pass
                """
            ),
            "tests/test_cfr.py": _source(
                """
                import unittest
                class CoreTests(unittest.TestCase):
                    def test_core(self): pass
                """
            ),
            "tests/test_misc.py": _source(
                """
                import unittest
                class MiscTests(unittest.TestCase):
                    def test_current(self): pass
                """
            ),
        }

    def test_ownership_precedence_and_payload_grouping_are_materialized(self) -> None:
        document = self.generator.build_inventory(
            self.baseline_sources,
            dict(self.baseline_sources),
            enforce_baseline_lock=False,
        )
        entries = _entries_by_id(document)
        historical = _assignment(
            entries[
                "tests/test_legal_river_quotient_compiled_global_separation_calibration.py::"
                "CompiledGlobalSeparationSourceSealTests::test_historical_wins"
            ]
        )
        first_gpu = _assignment(
            entries["tests/test_gpu_sample.py::GpuSampleTests::test_first"]
        )
        second_gpu = _assignment(
            entries["tests/test_gpu_sample.py::GpuSampleTests::test_second"]
        )
        core = _assignment(entries["tests/test_cfr.py::CoreTests::test_core"])
        current = _assignment(entries["tests/test_misc.py::MiscTests::test_current"])

        self.assertEqual(historical["profile_name"], "historical")
        self.assertEqual(historical["expectation"], {"kind": "case_defined"})
        self.assertEqual(first_gpu["profile_name"], "gpu")
        self.assertEqual(first_gpu["payload_id"], second_gpu["payload_id"])
        self.assertEqual(core["profile_name"], "core")
        self.assertEqual(current["profile_name"], "current")
        for row in entries.values():
            self.assertEqual(row["baseline_assignment"], row["assignment"])
            self.assertNotIn("introduced_after_baseline", row)

    def test_mutable_decorators_do_not_reclassify_a_baseline_assignment(self) -> None:
        working = dict(self.baseline_sources)
        working["tests/test_misc.py"] = _source(
            """
            import importlib.util
            import unittest
            class MiscTests(unittest.TestCase):
                @unittest.skipUnless(importlib.util.find_spec("cupy"), "gpu")
                def test_current(self): pass
            """
        )
        document = self.generator.build_inventory(
            self.baseline_sources, working, enforce_baseline_lock=False
        )
        row = _entries_by_id(document)[
            "tests/test_misc.py::MiscTests::test_current"
        ]
        self.assertEqual(_assignment(row)["profile_name"], "current")
        self.assertEqual(row["baseline_assignment"], row["assignment"])

    def test_changed_baseline_id_and_unreviewed_added_file_are_rejected(self) -> None:
        renamed = dict(self.baseline_sources)
        renamed["tests/test_misc.py"] = self.baseline_sources[
            "tests/test_misc.py"
        ].replace(b"test_current", b"test_renamed")
        with self.assertRaisesRegex(Exception, "baseline.*stable ID"):
            self.generator.build_inventory(
                self.baseline_sources, renamed, enforce_baseline_lock=False
            )

        added = dict(self.baseline_sources)
        added["tests/test_unreviewed_new_file.py"] = _source(
            """
            import unittest
            class AddedTests(unittest.TestCase):
                def test_added(self): pass
            """
        )
        with self.assertRaisesRegex(Exception, "unreviewed stabilization test file"):
            self.generator.build_inventory(
                self.baseline_sources, added, enforce_baseline_lock=False
            )

    def test_reviewed_stabilization_additions_are_current_and_explicit(self) -> None:
        working = dict(self.baseline_sources)
        working["tests/test_inventory_and_profiles.py"] = _source(
            """
            import unittest
            class InventoryTests(unittest.TestCase):
                def test_added(self): pass
            """
        )
        document = self.generator.build_inventory(
            self.baseline_sources, working, enforce_baseline_lock=False
        )
        row = _entries_by_id(document)[
            "tests/test_inventory_and_profiles.py::InventoryTests::test_added"
        ]
        self.assertEqual(_assignment(row)["profile_name"], "current")
        self.assertIs(row["introduced_after_baseline"], True)
        self.assertNotIn("baseline_assignment", row)

    def test_declared_skip_requires_the_exact_outer_literal_and_reason_code(self) -> None:
        stable_id, (literal, reason_code, _) = next(
            iter(DECLARED_UNCONDITIONAL_SKIPS.items())
        )
        relative_path, case_name, method_name = stable_id.split("::")
        exact = {
            relative_path: _source(
                f"""
                import importlib.util
                import unittest
                class {case_name}(unittest.TestCase):
                    @unittest.skip({literal!r})
                    @unittest.skipUnless(importlib.util.find_spec("cupy"), "gpu")
                    def {method_name}(self): pass
                """
            )
        }
        document = self.generator.build_inventory(
            exact, exact, enforce_baseline_lock=False
        )
        expectation = _assignment(_entries_by_id(document)[stable_id])["expectation"]
        self.assertEqual(
            expectation,
            {
                "kind": "declared_unconditional_skip",
                "skip_safe_reason_code": reason_code,
            },
        )
        changed = {
            relative_path: exact[relative_path].replace(
                literal.encode("utf-8"), b"different skip reason"
            )
        }
        with self.assertRaisesRegex(Exception, "declared unconditional skip"):
            self.generator.build_inventory(
                exact, changed, enforce_baseline_lock=False
            )


class DesignReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = _load_generator()
        self.baseline_commit = "1" * 40
        self.baseline_tree = "2" * 40
        self.static_id = "tests/test_review.py::ReviewTests::test_static"
        self.denied_id = "tests/test_review.py::ReviewTests::test_denied"
        self.inventory = {
            "schema_version": "pontius-test-inventory-v1",
            "baseline_commit": self.baseline_commit,
            "baseline_discovery": {
                "test_file_count": 1,
                "stable_id_count": 2,
                "stable_ids_sha256": _ids_digest([self.static_id, self.denied_id]),
            },
            "discovery": {
                "test_file_count": 1,
                "stable_id_count": 2,
                "stable_ids_sha256": _ids_digest([self.static_id, self.denied_id]),
            },
            "entries": [
                self._inventory_entry(self.denied_id),
                self._inventory_entry(self.static_id),
            ],
        }
        self.inventory_bytes = _canonical_json_bytes(self.inventory) + b"\n"
        self.sources = {
            "tests/test_review.py": _source(
                """
                import subprocess
                import sys
                import unittest

                def _module_process():
                    subprocess.run(
                        [sys.executable, "-m", "module_fixture"],
                        cwd=".",
                        env={**__import__("os").environ, "SAFE": "1"},
                        timeout=5,
                        check=False,
                    )

                def _test_process():
                    subprocess.run(
                        [sys.executable, "-m", "demo"],
                        cwd=".",
                        env={**__import__("os").environ, "SAFE": "1"},
                        timeout=5,
                        check=False,
                    )

                def setUpModule():
                    _module_process()

                class ReviewTests(unittest.TestCase):
                    @classmethod
                    def setUpClass(cls):
                        cls._class_process()

                    @classmethod
                    def _class_process(cls):
                        subprocess.run(
                            [sys.executable, "-m", "class_fixture"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5,
                            check=False,
                        )

                    def test_static(self):
                        _test_process()
                    def test_denied(self):
                        self.assertTrue(True)

                class LooksLikeTestsButIsNotATestCase:
                    def test_helper(self):
                        subprocess.run(
                            [sys.executable, "-m", "must_not_be_reviewed"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5,
                            check=False,
                        )
                """
            ),
            "tools/test_child.py": _source(
                """
                def _run_gpu_probe():
                    return None
                """
            ),
        }
        self.universe = (
            ("stable_id", self.denied_id),
            ("stable_id", self.static_id),
            ("fixture", "fixture:tests/test_review.py"),
            ("fixture", "fixture:tests/test_review.py::ReviewTests"),
            ("probe", "probe:gpu-availability"),
        )

    def _inventory_entry(
        self,
        stable_id: str,
        *,
        expectation: dict[str, object] | None = None,
    ) -> dict[str, object]:
        relative_path, case_name, method_name = stable_id.split("::")
        assignment = {
            "profile_name": "current",
            "payload_id": f"current:{relative_path}",
            "expectation": {"kind": "pass"} if expectation is None else expectation,
        }
        return {
            "stable_id": stable_id,
            "relative_path": relative_path,
            "case_name": case_name,
            "method_name": method_name,
            "assignment": assignment,
            "baseline_assignment": dict(assignment),
        }

    def _review(
        self,
        *,
        sources: dict[str, bytes] | None = None,
        include_probe: bool = True,
    ) -> dict[str, object]:
        review_sources = dict(self.sources if sources is None else sources)
        if include_probe:
            review_sources.setdefault(
                "tools/test_child.py",
                self.sources["tools/test_child.py"],
            )
        return self.generator.derive_design_review(
            baseline_commit=self.baseline_commit,
            baseline_root_tree_oid=self.baseline_tree,
            inventory_document=self.inventory,
            inventory_document_bytes=self.inventory_bytes,
            sources=review_sources,
            item_universe=self.universe,
        )

    def _transaction_source(self) -> bytes:
        return _source(
            """
            import subprocess
            import sys
            import unittest

            class TransactionTests(unittest.TestCase):
                def test_core(self):
                    subprocess.run(
                        [sys.executable, "-m", "core_demo"],
                        cwd=".",
                        env={**__import__("os").environ, "SAFE": "1"},
                        timeout=5,
                        check=False,
                    )

                def test_current(self):
                    subprocess.run(
                        [sys.executable, "-m", "current_demo"],
                        cwd=".",
                        env={**__import__("os").environ, "SAFE": "1"},
                        timeout=5,
                        check=False,
                    )

                def test_gpu(self):
                    subprocess.run(
                        [sys.executable, "-m", "gpu_demo"],
                        cwd=".",
                        env={**__import__("os").environ, "SAFE": "1"},
                        timeout=5,
                        check=False,
                    )

                def test_historical(self):
                    self.assertTrue(True)
            """
        )

    def _transaction_inventory(self) -> dict[str, object]:
        relative_path = "tests/test_transaction.py"
        assignments = {
            "test_core": ("core", "core:transaction"),
            "test_current": ("current", "current:transaction"),
            "test_gpu": ("gpu", "gpu:transaction"),
            "test_historical": ("historical", "historical:transaction"),
        }
        entries: list[dict[str, object]] = []
        ids_by_profile: dict[str, list[str]] = {
            name: [] for name in ("historical", "gpu", "core", "current")
        }
        for method_name, (profile_name, payload_id) in assignments.items():
            stable_id = (
                f"{relative_path}::TransactionTests::{method_name}"
            )
            assignment = {
                "profile_name": profile_name,
                "payload_id": payload_id,
                "expectation": {"kind": "pass"},
            }
            entries.append(
                {
                    "stable_id": stable_id,
                    "relative_path": relative_path,
                    "case_name": "TransactionTests",
                    "method_name": method_name,
                    "assignment": assignment,
                    "baseline_assignment": json.loads(json.dumps(assignment)),
                }
            )
            ids_by_profile[profile_name].append(stable_id)
        entries.sort(key=lambda row: str(row["stable_id"]))
        stable_ids = [str(row["stable_id"]) for row in entries]
        empty_digest = _ids_digest([])
        return {
            "schema_version": "pontius-test-inventory-v1",
            "baseline_commit": BASELINE_COMMIT,
            "baseline_discovery": {
                "test_file_count": 1,
                "stable_id_count": len(stable_ids),
                "stable_ids_sha256": _ids_digest(stable_ids),
                "historical_id_count": len(ids_by_profile["historical"]),
                "historical_ids_sha256": _ids_digest(ids_by_profile["historical"]),
                "gpu_id_count": len(ids_by_profile["gpu"]),
                "gpu_ids_sha256": _ids_digest(ids_by_profile["gpu"]),
                "core_id_count": len(ids_by_profile["core"]),
                "core_ids_sha256": _ids_digest(ids_by_profile["core"]),
                "current_id_count": len(ids_by_profile["current"]),
                "current_ids_sha256": _ids_digest(ids_by_profile["current"]),
                "explicit_exclusion_count": 0,
            },
            "discovery": {
                "test_file_count": 1,
                "stable_id_count": len(stable_ids),
                "stable_ids_sha256": _ids_digest(stable_ids),
                "introduced_id_count": 0,
                "introduced_ids_sha256": empty_digest,
            },
            "entries": entries,
        }

    def _transaction_profiles(self) -> bytes:
        root = [
            'schema_version = "pontius-test-profiles-v1"',
            f'baseline_commit = "{BASELINE_COMMIT}"',
            'sealed_current_files_manifest = "docs/architecture/sealed-current-files.toml"',
            'sealed_current_absences_manifest = "docs/architecture/sealed-current-absences.toml"',
            'historical_blobs_manifest = "docs/architecture/historical-blobs.toml"',
            'retained_v7_manifest = "docs/architecture/retained-v7.toml"',
            'inventory_path = "tests/test-inventory.json"',
            f'spec_capabilities_sha256 = "{ZERO_SHA256}"',
            f'capability_bindings_sha256 = "{ZERO_SHA256}"',
            "stabilization_test_files = []",
            "",
            "[[interpreter_slot]]",
            'name = "development"',
            'resolution = "repository_relative"',
            'windows_relative_path = ".venv/Scripts/python.exe"',
            'posix_relative_path = ".venv/bin/python"',
            'implementation = "cpython"',
            "minimum_version = [3, 11]",
            "required_for_full = true",
            "",
        ]
        for profile_name in ("core", "current", "gpu", "historical", "full"):
            direct = profile_name != "full"
            root.extend(
                [
                    "[[profile]]",
                    f'name = "{profile_name}"',
                    'interpreter_slots = ["development"]',
                ]
            )
            if direct:
                root.append('default_interpreter_slot = "development"')
            root.extend(
                [
                    (
                        f'payload_ids = ["{profile_name}:transaction"]'
                        if direct
                        else "payload_ids = []"
                    ),
                    "historical_case_ids = []",
                    (
                        "subprofiles = []"
                        if direct
                        else 'subprofiles = ["core", "current", "gpu", "historical"]'
                    ),
                    f"gpu_optional = {'true' if profile_name == 'full' else 'false'}",
                    "[profile.budgets]",
                    "setup_seconds = 2",
                    "child_seconds = 3",
                    "termination_seconds = 5",
                    "cleanup_seconds = 7",
                    "total_seconds = 17",
                    "",
                ]
            )
        for profile_name in ("core", "current", "gpu", "historical"):
            target_kind = (
                "historical_clone"
                if profile_name == "historical"
                else "current_snapshot"
            )
            root.extend(
                [
                    "[[payload]]",
                    f'payload_id = "{profile_name}:transaction"',
                    f'profile_name = "{profile_name}"',
                    f'target_kind = "{target_kind}"',
                    'allowed_interpreter_slots = ["development"]',
                    (
                        'probe_ids = ["probe:gpu-availability"]'
                        if profile_name == "gpu"
                        else "probe_ids = []"
                    ),
                    "environment_additions = {}",
                    "environment_removals = []",
                    'allowed_write_roots = ["temporary"]',
                    "forbidden_relative_paths = []",
                    "serialized = false",
                    "",
                ]
            )
        root.extend(
            [
                "# BEGIN GENERATED DESIGN SCOPE",
                "# END GENERATED DESIGN SCOPE",
                "# BEGIN GENERATED HISTORICAL SCOPE",
                "# END GENERATED HISTORICAL SCOPE",
            ]
        )
        return "\n".join(root).encode("ascii") + b"\n"

    def _make_transaction_repository(
        self,
        root: Path,
        *,
        source: bytes | None = None,
        inventory: dict[str, object] | None = None,
    ) -> tuple[Path, Path, Path]:
        tests = root / "tests"
        tests.mkdir()
        source_path = tests / "test_transaction.py"
        inventory_path = tests / "test-inventory.json"
        profiles_path = tests / "test-profiles.toml"
        tools = root / "tools"
        tools.mkdir()
        (tools / "test_child.py").write_bytes(
            b"def _run_gpu_probe():\n    return None\n"
        )
        source_path.write_bytes(self._transaction_source() if source is None else source)
        document = self._transaction_inventory() if inventory is None else inventory
        inventory_path.write_bytes(_canonical_json_bytes(document) + b"\n")
        profiles_path.write_bytes(self._transaction_profiles())
        return source_path, inventory_path, profiles_path

    def _fresh_transaction_review(self, root: Path) -> dict[str, object]:
        return self.generator.emit_design_review(root, root / "design-review.json")

    def _without_design_approval(self, raw: bytes) -> bytes:
        begin = b"# BEGIN GENERATED DESIGN SCOPE\n"
        end = b"# END GENERATED DESIGN SCOPE\n"
        self.assertEqual(raw.count(begin), 1)
        self.assertEqual(raw.count(end), 1)
        prefix, remainder = raw.split(begin)
        _, suffix = remainder.split(end)
        lines = prefix.splitlines(keepends=True)
        spec_indices = [
            index
            for index, line in enumerate(lines)
            if line.startswith(b"spec_capabilities_sha256 = ")
        ]
        self.assertEqual(spec_indices, [7])
        lines[spec_indices[0]] = b"spec_capabilities_sha256 = <DESIGN-DIGEST>\n"
        return b"".join(lines) + begin + end + suffix

    def test_receipt_binds_canonical_sources_rows_and_complete_sorted_deny_all(self) -> None:
        crlf_sources = {
            key: value.replace(b"\n", b"\r\n") for key, value in self.sources.items()
        }
        review = self._review(sources=crlf_sources)
        receipt = review["receipt"]
        self.assertEqual(
            set(receipt),
            {
                "schema_version",
                "approval_scope",
                "baseline_commit",
                "baseline_root_tree_oid",
                "inventory_semantic_sha256",
                "inventory_document_sha256",
                "derivation_sources",
                "spec_capabilities_sha256",
                "expanded_rows",
                "deny_all",
            },
        )
        self.assertEqual(
            receipt["schema_version"],
            "pontius-design-capability-review-receipt-v1",
        )
        self.assertEqual(receipt["approval_scope"], "design")
        source_row = receipt["derivation_sources"][0]
        canonical_source = self.sources["tests/test_review.py"]
        self.assertEqual(
            source_row,
            {
                "relative_path": "tests/test_review.py",
                "byte_length": len(canonical_source),
                "canonical_lf_sha256": sha256(canonical_source).hexdigest(),
            },
        )
        expanded = receipt["expanded_rows"]
        self.assertTrue(expanded)
        expected_expanded_items = {
            self.static_id,
            "fixture:tests/test_review.py",
            "fixture:tests/test_review.py::ReviewTests",
        }
        self.assertEqual(
            {row["item_id"] for row in expanded}, expected_expanded_items
        )
        self.assertEqual(
            {
                (row["item_id"], tuple(row["argv"]))
                for row in expanded
                if row["capability_kind"] == "subprocess"
            },
            {
                (self.static_id, ("-m", "demo")),
                ("fixture:tests/test_review.py", ("-m", "module_fixture")),
                (
                    "fixture:tests/test_review.py::ReviewTests",
                    ("-m", "class_fixture"),
                ),
            },
        )
        for row in expanded:
            with self.subTest(static_subprocess_item=row["item_id"]):
                self.assertEqual(row["approval_scope"], "design")
                self.assertEqual(row["capability_kind"], "subprocess")
                self.assertEqual(row["executable_role"], "python")
                self.assertEqual(row["executable_slot"], "active_worker")
                self.assertEqual(row["cwd_class"], "target")
                self.assertEqual(row["environment_additions"], {"SAFE": "1"})
                self.assertEqual(row["timeout_ns"], 5_000_000_000)
        self.assertNotIn(
            "tests/test_review.py::LooksLikeTestsButIsNotATestCase::test_helper",
            {row["item_id"] for row in expanded},
        )
        self.assertEqual(
            receipt["deny_all"],
            [
                {"item_kind": "probe", "item_id": "probe:gpu-availability"},
                {"item_kind": "stable_id", "item_id": self.denied_id},
            ],
        )
        self.assertEqual(
            receipt["inventory_document_sha256"],
            sha256(self.inventory_bytes).hexdigest(),
        )
        self.assertEqual(
            review["design_review_receipt_sha256"],
            sha256(_canonical_json_bytes(receipt)).hexdigest(),
        )
        self.assertNotIn("host_diagnostics", receipt)
        self.assertNotIn("design_review_receipt_sha256", receipt)

        historical_id = (
            "tests/test_review.py::HistoricalSourceSealTests::"
            "test_historical_subprocess"
        )
        historical_inventory = json.loads(json.dumps(self.inventory))
        historical_entry = self._inventory_entry(historical_id)
        for field in ("assignment", "baseline_assignment"):
            historical_entry[field] = {
                "profile_name": "historical",
                "payload_id": "historical:synthetic-source-seal",
                "expectation": {"kind": "case_defined"},
            }
        historical_inventory["entries"].append(historical_entry)
        historical_inventory["entries"].sort(key=lambda row: row["stable_id"])
        all_ids = [row["stable_id"] for row in historical_inventory["entries"]]
        for field in ("baseline_discovery", "discovery"):
            historical_inventory[field]["stable_id_count"] = len(all_ids)
            historical_inventory[field]["stable_ids_sha256"] = _ids_digest(all_ids)
        historical_sources = dict(self.sources)
        historical_sources["tests/test_review.py"] = historical_sources[
            "tests/test_review.py"
        ].replace(
            b"class LooksLikeTestsButIsNotATestCase:\n",
            _source(
                """
                class HistoricalSourceSealTests(unittest.TestCase):
                    def test_historical_subprocess(self):
                        subprocess.run(
                            [sys.executable, "-m", "historical_must_not_enter_design"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5,
                            check=False,
                        )

                class LooksLikeTestsButIsNotATestCase:
                """
            ),
        )
        historical_review = self.generator.derive_design_review(
            baseline_commit=self.baseline_commit,
            baseline_root_tree_oid=self.baseline_tree,
            inventory_document=historical_inventory,
            inventory_document_bytes=(
                _canonical_json_bytes(historical_inventory) + b"\n"
            ),
            sources=historical_sources,
            item_universe=self.universe,
        )
        historical_receipt = historical_review["receipt"]
        self.assertNotIn(
            historical_id,
            {
                row["item_id"]
                for row in (
                    historical_receipt["expanded_rows"]
                    + historical_receipt["deny_all"]
                )
            },
        )

    def test_both_approval_tokens_are_required_and_either_snapshot_drift_rejects(self) -> None:
        review = self._review()
        rows = self.generator.validate_design_approval(
            review,
            review["spec_capabilities_sha256"],
            review["design_review_receipt_sha256"],
        )
        self.assertEqual(tuple(rows), tuple(review["receipt"]["expanded_rows"]))
        for spec_token, receipt_token in (
            ("0" * 64, review["design_review_receipt_sha256"]),
            (review["spec_capabilities_sha256"], "0" * 64),
            (None, review["design_review_receipt_sha256"]),
            (review["spec_capabilities_sha256"], None),
        ):
            with self.subTest(spec_token=spec_token, receipt_token=receipt_token):
                with self.assertRaisesRegex(Exception, "approval.*token"):
                    self.generator.validate_design_approval(
                        review, spec_token, receipt_token
                    )

        drifted_sources = dict(self.sources)
        drifted_sources["tests/test_review.py"] += b"# canonical source drift\n"
        drifted = self._review(sources=drifted_sources)
        self.assertNotEqual(
            review["design_review_receipt_sha256"],
            drifted["design_review_receipt_sha256"],
        )
        with self.assertRaisesRegex(Exception, "approval.*token"):
            self.generator.validate_design_approval(
                drifted,
                review["spec_capabilities_sha256"],
                review["design_review_receipt_sha256"],
            )

        with tempfile.TemporaryDirectory(
            prefix="pontius-design-write-success-"
        ) as temporary:
            root = Path(temporary)
            _, inventory_path, profiles_path = self._make_transaction_repository(root)
            support_path = root / "tests" / "evidence_test_support.py"
            support_path.write_bytes(b"SUPPORT_SENTINEL = 1\n")
            fresh = self._fresh_transaction_review(root)
            self.assertIn(
                "tests/evidence_test_support.py",
                {
                    row["relative_path"]
                    for row in fresh["receipt"]["derivation_sources"]
                },
            )
            self.assertIn(
                {"item_kind": "probe", "item_id": "probe:gpu-availability"},
                fresh["receipt"]["deny_all"],
            )
            before = profiles_path.read_bytes()
            with mock.patch.object(
                self.generator,
                "derive_design_review",
                wraps=self.generator.derive_design_review,
            ) as derive_fresh, mock.patch.object(
                self.generator,
                "write_atomic_lf",
                wraps=self.generator.write_atomic_lf,
            ) as atomic_write:
                self.generator.write_design_capabilities(
                    root,
                    approved_spec_capabilities_sha256=fresh[
                        "spec_capabilities_sha256"
                    ],
                    approved_design_review_receipt_sha256=fresh[
                        "design_review_receipt_sha256"
                    ],
                )
            self.assertEqual(derive_fresh.call_count, 1)
            self.assertEqual(atomic_write.call_count, 1)
            self.assertEqual(atomic_write.call_args.args[0], profiles_path)

            after = profiles_path.read_bytes()
            self.assertNotEqual(after, before)
            self.assertEqual(
                self._without_design_approval(after),
                self._without_design_approval(before),
            )
            self.assertFalse(after.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r", after)
            self.assertTrue(after.endswith(b"\n"))
            self.assertFalse(after.endswith(b"\n\n"))
            self.assertFalse(
                any(
                    path.name.startswith(f".{profiles_path.name}.")
                    for path in profiles_path.parent.iterdir()
                )
            )

            parsed = tomllib.loads(after.decode("ascii"))
            self.assertEqual(
                parsed["spec_capabilities_sha256"],
                fresh["spec_capabilities_sha256"],
            )
            self.assertEqual(parsed["capability_bindings_sha256"], ZERO_SHA256)
            design_bindings = [
                row
                for row in parsed["capability_binding"]
                if row["approval_scope"] == "design"
            ]
            expected_design_ids = {
                "tests/test_transaction.py::TransactionTests::test_core",
                "tests/test_transaction.py::TransactionTests::test_current",
                "tests/test_transaction.py::TransactionTests::test_gpu",
            }
            self.assertEqual(
                {row["item_id"] for row in design_bindings},
                expected_design_ids,
            )
            self.assertEqual(
                [
                    (
                        row["item_id"],
                        row["capability_kind"],
                        row["capability_id"],
                    )
                    for row in design_bindings
                ],
                sorted(
                    (
                        row["item_id"],
                        row["capability_kind"],
                        row["capability_id"],
                    )
                    for row in design_bindings
                ),
            )
            definitions = parsed["subprocess_capability"]
            self.assertEqual(len(definitions), 3)
            self.assertEqual(
                {row["capability_id"] for row in definitions},
                {row["capability_id"] for row in design_bindings},
            )

            errors, _, configuration = _load_orchestration()
            bundle = configuration.load_configuration(
                profiles_path,
                inventory_path,
                repository_root=root,
            )
            for profile_name in ("core", "current", "gpu"):
                with self.subTest(approved_profile=profile_name):
                    self.assertEqual(
                        configuration.select_profile(bundle, profile_name).name,
                        profile_name,
                    )
            for profile_name in ("historical", "full"):
                with self.subTest(unapproved_profile=profile_name):
                    with self.assertRaises(
                        errors.EvidenceConfigurationError
                    ) as refused:
                        configuration.select_profile(bundle, profile_name)
                    self.assertEqual(
                        refused.exception.code,
                        "capability_approval_required",
                    )
                    self.assertEqual(
                        refused.exception.context["approval_scopes"],
                        ("historical_review",),
                    )

            generated = before
            inventory_raw = inventory_path.read_bytes()
            preserved_design = self.generator.preserve_approved_profile_scopes(
                generated,
                after,
                existing_inventory=inventory_raw,
                generated_inventory=inventory_raw,
                review=fresh,
            )
            self.assertEqual(preserved_design, after)

            support_path.write_bytes(b"SUPPORT_SENTINEL = 2\n")
            support_drift = self._fresh_transaction_review(root)
            self.assertEqual(
                support_drift["spec_capabilities_sha256"],
                fresh["spec_capabilities_sha256"],
            )
            self.assertNotEqual(
                support_drift["design_review_receipt_sha256"],
                fresh["design_review_receipt_sha256"],
            )
            with self.assertRaisesRegex(Exception, "approval.*token"):
                self.generator.preserve_approved_profile_scopes(
                    generated,
                    after,
                    existing_inventory=inventory_raw,
                    generated_inventory=inventory_raw,
                    review=support_drift,
                )
            support_path.write_bytes(b"SUPPORT_SENTINEL = 1\n")

            historical_row = dict(fresh["receipt"]["expanded_rows"][0])
            historical_row["item_id"] = "probe:v7-sealed-reader-retained"
            historical_row["approval_scope"] = "historical_review"
            historical_row["argv"] = ["-m", "historical_demo"]
            historical_definition = {
                key: value
                for key, value in historical_row.items()
                if key not in {
                    "item_id",
                    "approval_scope",
                    "capability_kind",
                    "capability_id",
                }
            }
            historical_row["capability_id"] = self.generator._capability_id(
                "process",
                historical_definition,
            )
            historical_digest = sha256(
                self.generator._semantic_bytes([historical_row])
            ).hexdigest()
            historical_content = self.generator._render_capability_scope(
                [historical_row],
                approval_scope="historical_review",
                receipt_digest="4" * 64,
            )
            both_approved = self.generator._replace_root_digest(
                after,
                "capability_bindings_sha256",
                historical_digest,
            )
            both_approved = self.generator._replace_scope_content(
                both_approved,
                "historical_review",
                historical_content,
            )
            preserved_both = self.generator.preserve_approved_profile_scopes(
                generated,
                both_approved,
                existing_inventory=inventory_raw,
                generated_inventory=inventory_raw,
                review=fresh,
            )
            self.assertEqual(preserved_both, both_approved)

        with tempfile.TemporaryDirectory(
            prefix="pontius-design-write-source-race-"
        ) as temporary:
            root = Path(temporary)
            source_path, _, profiles_path = self._make_transaction_repository(root)
            fresh = self._fresh_transaction_review(root)
            before = profiles_path.read_bytes()
            original_source = source_path.read_bytes()
            real_write = self.generator.write_atomic_lf

            def mutate_source_before_publish(*args: object, **kwargs: object) -> object:
                source_path.write_bytes(original_source + b"# raced\n")
                return real_write(*args, **kwargs)

            with mock.patch.object(
                self.generator,
                "write_atomic_lf",
                side_effect=mutate_source_before_publish,
            ):
                with self.assertRaisesRegex(
                    Exception,
                    "(?:source|file).*(?:changed|drift)",
                ):
                    self.generator.write_design_capabilities(
                        root,
                        approved_spec_capabilities_sha256=fresh[
                            "spec_capabilities_sha256"
                        ],
                        approved_design_review_receipt_sha256=fresh[
                            "design_review_receipt_sha256"
                        ],
                    )
            self.assertEqual(profiles_path.read_bytes(), before)

        for spec_field, receipt_field in (
            (None, "valid"),
            ("valid", None),
            (ZERO_SHA256, "valid"),
            ("valid", ZERO_SHA256),
        ):
            with self.subTest(
                write_spec_token=spec_field,
                write_receipt_token=receipt_field,
            ), tempfile.TemporaryDirectory(
                prefix="pontius-design-write-token-refusal-"
            ) as temporary:
                root = Path(temporary)
                _, _, profiles_path = self._make_transaction_repository(root)
                fresh = self._fresh_transaction_review(root)
                before = profiles_path.read_bytes()
                spec_token = (
                    fresh["spec_capabilities_sha256"]
                    if spec_field == "valid"
                    else spec_field
                )
                receipt_token = (
                    fresh["design_review_receipt_sha256"]
                    if receipt_field == "valid"
                    else receipt_field
                )
                with self.assertRaisesRegex(Exception, "approval|both.*token"):
                    self.generator.write_design_capabilities(
                        root,
                        approved_spec_capabilities_sha256=spec_token,
                        approved_design_review_receipt_sha256=receipt_token,
                    )
                self.assertEqual(profiles_path.read_bytes(), before)

        for drift_kind in ("source", "inventory_document", "deny_all"):
            with self.subTest(drift=drift_kind), tempfile.TemporaryDirectory(
                prefix=f"pontius-design-write-{drift_kind}-drift-"
            ) as temporary:
                root = Path(temporary)
                source_path, inventory_path, profiles_path = (
                    self._make_transaction_repository(root)
                )
                approved = self._fresh_transaction_review(root)
                approved_receipt = approved["receipt"]
                before = profiles_path.read_bytes()
                if drift_kind == "source":
                    source_path.write_bytes(
                        source_path.read_bytes() + b"# source-only drift\n"
                    )
                elif drift_kind == "inventory_document":
                    inventory_path.write_bytes(
                        json.dumps(
                            json.loads(inventory_path.read_bytes()),
                            ensure_ascii=True,
                            indent=2,
                            sort_keys=True,
                        ).encode("ascii")
                        + b"\n"
                    )
                else:
                    source_path.write_bytes(
                        source_path.read_bytes().replace(
                            b"class TransactionTests(unittest.TestCase):\n",
                            (
                                b"class TransactionTests(unittest.TestCase):\n"
                                b"    @classmethod\n"
                                b"    def setUpClass(cls):\n"
                                b"        pass\n\n"
                            ),
                        ).replace(
                            b"    def test_historical(self):\n",
                            b"    def historical_helper(self):\n",
                        )
                    )
                drifted = self._fresh_transaction_review(root)
                drifted_receipt = drifted["receipt"]
                if drift_kind == "source":
                    self.assertNotEqual(
                        drifted_receipt["derivation_sources"],
                        approved_receipt["derivation_sources"],
                    )
                    self.assertEqual(
                        drifted_receipt["inventory_document_sha256"],
                        approved_receipt["inventory_document_sha256"],
                    )
                    self.assertEqual(
                        drifted_receipt["deny_all"],
                        approved_receipt["deny_all"],
                    )
                elif drift_kind == "inventory_document":
                    self.assertEqual(
                        drifted_receipt["inventory_semantic_sha256"],
                        approved_receipt["inventory_semantic_sha256"],
                    )
                    self.assertNotEqual(
                        drifted_receipt["inventory_document_sha256"],
                        approved_receipt["inventory_document_sha256"],
                    )
                    self.assertEqual(
                        drifted_receipt["derivation_sources"],
                        approved_receipt["derivation_sources"],
                    )
                else:
                    self.assertNotEqual(
                        drifted_receipt["deny_all"],
                        approved_receipt["deny_all"],
                    )
                    self.assertIn(
                        {
                            "item_kind": "fixture",
                            "item_id": (
                                "fixture:tests/test_transaction.py::"
                                "TransactionTests"
                            ),
                        },
                        drifted_receipt["deny_all"],
                    )
                with self.assertRaisesRegex(Exception, "approval.*token"):
                    self.generator.write_design_capabilities(
                        root,
                        approved_spec_capabilities_sha256=approved[
                            "spec_capabilities_sha256"
                        ],
                        approved_design_review_receipt_sha256=approved[
                            "design_review_receipt_sha256"
                        ],
                    )
                self.assertEqual(profiles_path.read_bytes(), before)

    def test_each_referenced_process_semantic_changes_the_design_row_digest(self) -> None:
        original = self._review()
        original_digest = original["spec_capabilities_sha256"]
        replacements = (
            (b'"demo"', b'"different-module"'),
            (b'"SAFE": "1"', b'"SAFE": "2"'),
            (b'cwd="."', b'cwd="temporary"'),
            (b"timeout=5", b"timeout=6"),
        )
        for old, new in replacements:
            with self.subTest(old=old, new=new):
                changed = {
                    path: source.replace(old, new) for path, source in self.sources.items()
                }
                self.assertNotEqual(changed, self.sources)
                review = self._review(sources=changed)
                self.assertNotEqual(
                    review["spec_capabilities_sha256"], original_digest
                )

        mixed_sources = {
            "tests/test_review.py": _source(
                """
                import cupy as cp
                import pontius.gpu_occupied_card_quotient as occupied
                import pontius.legal_river_quotient_cuda_consumer as consumer
                import subprocess
                import sys
                import unittest

                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        subprocess.run(
                            [sys.executable, "-m", "static_process"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5,
                            check=False,
                        )
                        occupied.run_frozen_gpu_quotient_keystone()
                        occupied.run_frozen_gpu_quotient_keystone()
                        consumer.run_bounded_cuda_consumer_conformance()
                        cp.cuda.get_current_stream()
                        cp.arange(1)

                    def test_denied(self):
                        subprocess.run(
                            [sys.executable, "-m", "denied_process"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5,
                            check=False,
                        )
                        consumer.run_bounded_cuda_consumer_conformance()
                """
            )
        }
        mixed = self._review(sources=mixed_sources)
        mixed_rows = mixed["receipt"]["expanded_rows"]
        call_rows = [row for row in mixed_rows if row["capability_kind"] == "call"]
        subprocess_rows = [
            row for row in mixed_rows if row["capability_kind"] == "subprocess"
        ]
        self.assertEqual(len(call_rows), 5)
        self.assertEqual(len(subprocess_rows), 2)

        expected_calls = {
            (
                self.denied_id,
                "owner",
                "pontius.legal_river_quotient_cuda_consumer",
                (
                    "pontius.legal_river_quotient_cuda_consumer."
                    "run_bounded_cuda_consumer_conformance"
                ),
                "invoke",
                1,
                "opaque",
            ),
            (
                self.static_id,
                "owner",
                "pontius.gpu_occupied_card_quotient",
                (
                    "pontius.gpu_occupied_card_quotient."
                    "run_frozen_gpu_quotient_keystone"
                ),
                "invoke",
                2,
                "opaque",
            ),
            (
                self.static_id,
                "owner",
                "pontius.legal_river_quotient_cuda_consumer",
                (
                    "pontius.legal_river_quotient_cuda_consumer."
                    "run_bounded_cuda_consumer_conformance"
                ),
                "invoke",
                1,
                "opaque",
            ),
            (
                self.static_id,
                "cuda_query",
                "cupy",
                "cupy.cuda.get_current_stream",
                "invoke",
                1,
                "stream",
            ),
            (
                self.static_id,
                "cuda_allocation",
                "cupy",
                "cupy.arange",
                "invoke",
                1,
                "device_array",
            ),
        }
        self.assertEqual(
            {
                (
                    row["item_id"],
                    row["kind"],
                    row["module_name"],
                    row["qualified_name"],
                    row["action"],
                    row["maximum_calls"],
                    row["return_contract"],
                )
                for row in call_rows
            },
            expected_calls,
        )
        for row in call_rows:
            with self.subTest(call_capability_id=row["capability_id"]):
                self.assertEqual(
                    set(row),
                    {
                        "item_id",
                        "approval_scope",
                        "capability_kind",
                        "capability_id",
                        "kind",
                        "module_name",
                        "qualified_name",
                        "action",
                        "maximum_calls",
                        "return_contract",
                    },
                )
                self.assertEqual(row["approval_scope"], "design")
                self.assertTrue(row["capability_id"].startswith("call:"))

        # The source intentionally lists test_static before the lexically earlier
        # test_denied. Mixed bindings still use the controller-ruled total order,
        # while each definition kind uses its own (item_id, capability_id) order.
        source_tree = ast.parse(mixed_sources["tests/test_review.py"])
        review_case = next(
            node
            for node in source_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "ReviewTests"
        )
        source_method_ids = [
            f"tests/test_review.py::ReviewTests::{node.name}"
            for node in review_case.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]
        self.assertEqual(source_method_ids, [self.static_id, self.denied_id])
        self.assertNotEqual(source_method_ids, sorted(source_method_ids))
        binding_keys = [
            (
                row["approval_scope"],
                row["item_id"],
                row["capability_kind"],
                row["capability_id"],
            )
            for row in mixed_rows
        ]
        self.assertEqual(binding_keys, sorted(binding_keys))
        for capability_kind, rows in (
            ("call", call_rows),
            ("subprocess", subprocess_rows),
        ):
            with self.subTest(per_kind_order=capability_kind):
                keys = [(row["item_id"], row["capability_id"]) for row in rows]
                self.assertEqual(keys, sorted(keys))

        call_digest = mixed["spec_capabilities_sha256"]
        shared_consumer_rows = [
            row
            for row in call_rows
            if row["qualified_name"].endswith(
                "run_bounded_cuda_consumer_conformance"
            )
        ]
        self.assertEqual(len(shared_consumer_rows), 2)
        self.assertEqual(
            len({row["capability_id"] for row in shared_consumer_rows}),
            1,
        )
        call_mutations = (
            (
                b"pontius.gpu_occupied_card_quotient",
                b"pontius.unregistered_owner_module",
                None,
            ),
            (
                b"        occupied.run_frozen_gpu_quotient_keystone()\n"
                b"        occupied.run_frozen_gpu_quotient_keystone()\n",
                b"        occupied.run_frozen_gpu_quotient_keystone()\n",
                1,
            ),
            (b"get_current_stream", b"get_unregistered_stream", 1),
            (b"cp.arange(1)", b"cp.linspace(0, 1, 1)", 1),
            (
                b"run_bounded_cuda_consumer_conformance",
                b"run_unregistered_consumer",
                1,
            ),
        )
        for old, new, limit in call_mutations:
            with self.subTest(call_semantic=old):
                original_source = mixed_sources["tests/test_review.py"]
                mutated_source = (
                    original_source.replace(old, new)
                    if limit is None
                    else original_source.replace(old, new, limit)
                )
                self.assertNotEqual(mutated_source, original_source)
                mutated = self._review(
                    sources={"tests/test_review.py": mutated_source}
                )
                self.assertNotEqual(
                    mutated["spec_capabilities_sha256"], call_digest
                )

        bounded_sources = {
            "tests/test_review.py": _source(
                """
                import cupy as cp
                import unittest
                def family():
                    return (1, 2, 3)
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        values = family()
                        for value in values:
                            cp.asnumpy(value)
                            cp.asnumpy(value)
                    def test_denied(self):
                        if runtime_condition():
                            cp.arange(1)
                            cp.arange(2)
                        else:
                            cp.arange(3)
                """
            )
        }
        bounded = self._review(sources=bounded_sources)
        bounded_rows = {
            (row["item_id"], row["qualified_name"]): row["maximum_calls"]
            for row in bounded["receipt"]["expanded_rows"]
            if row["capability_kind"] == "call"
        }
        self.assertEqual(
            bounded_rows[(self.static_id, "cupy.asnumpy")],
            6,
        )
        self.assertEqual(
            bounded_rows[(self.denied_id, "cupy.arange")],
            2,
        )

        dynamic_loop = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            for value in obtain_values():
                                cp.asnumpy(value)
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertTrue(
            any(
                "dynamic repetition" in row["reason"]
                for row in dynamic_loop["unresolved_dynamic_blockers"]
            )
        )
        self.assertNotIn(
            self.static_id,
            {
                row["item_id"]
                for row in dynamic_loop["receipt"]["expanded_rows"]
            },
        )

        scientific_and_child = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import pontius.gpu_occupied_card_quotient as occupied
                    from pontius.heterogeneous_leaf_contraction import (
                        contract_heterogeneous_leaf_terms,
                    )
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            contract_heterogeneous_leaf_terms()
                        def test_denied(self):
                            subprocess.run(
                                [
                                    sys.executable,
                                    "-c",
                                    "import pontius.gpu_occupied_card_quotient as m; "
                                    "m.run_frozen_gpu_quotient_keystone()",
                                ],
                                timeout=5,
                                check=False,
                            )
                    """
                )
            }
        )
        scientific_rows = scientific_and_child["receipt"]["expanded_rows"]
        scientific = next(
            row
            for row in scientific_rows
            if row.get("qualified_name")
            == (
                "pontius.heterogeneous_leaf_contraction."
                "contract_heterogeneous_leaf_terms"
            )
        )
        self.assertEqual(scientific["kind"], "scientific")
        child_process = next(
            row
            for row in scientific_rows
            if row["item_id"] == self.denied_id
            and row["capability_kind"] == "subprocess"
        )
        self.assertTrue(child_process["fixed_descendant_permission"])
        self.assertTrue(
            any(
                row["item_id"] == self.denied_id
                and row.get("kind") == "owner"
                for row in scientific_rows
            )
        )

        compound_bounds = self._review(
            sources={
                "tests/test_review.py": _source(
                    r'''
                    import contextlib
                    import cupy as cp
                    import subprocess
                    import sys
                    import unittest
                    def read_back(value):
                        return cp.asnumpy(value)
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            with contextlib.nullcontext():
                                for value in range(5):
                                    cp.arange(value)
                                    read_back(value)
                        def test_denied(self):
                            subprocess.run(
                                [
                                    sys.executable,
                                    "-c",
                                    "import cupy as cp\n"
                                    "for value in range(5):\n"
                                    "    cp.asnumpy(value)\n",
                                ],
                                timeout=5,
                                check=False,
                            )
                    '''
                )
            }
        )
        compound_rows = {
            (row["item_id"], row.get("qualified_name")): row
            for row in compound_bounds["receipt"]["expanded_rows"]
            if row["capability_kind"] == "call"
        }
        self.assertEqual(
            compound_rows[(self.static_id, "cupy.arange")]["maximum_calls"],
            5,
        )
        self.assertEqual(
            compound_rows[(self.static_id, "cupy.asnumpy")]["maximum_calls"],
            5,
        )
        self.assertEqual(
            compound_rows[(self.denied_id, "cupy.asnumpy")]["maximum_calls"],
            5,
        )

        scientific_contracts = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import unittest
                    from pontius.affine_resident_heterogeneous_leaf_contraction import (
                        CuPyAffineResidentAutomatonCache,
                    )
                    from pontius.heterogeneous_leaf_contraction import (
                        contract_heterogeneous_leaf_terms,
                    )
                    from pontius.shared_resident_response_context import (
                        bind_resident_response_context,
                    )
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            CuPyAffineResidentAutomatonCache.compile()
                            bind_resident_response_context()
                            contract_heterogeneous_leaf_terms()
                        def test_denied(self): pass
                    """
                )
            }
        )
        scientific_by_name = {
            row["qualified_name"]: (
                row["action"],
                row["return_contract"],
            )
            for row in scientific_contracts["receipt"]["expanded_rows"]
            if row.get("kind") == "scientific"
        }
        self.assertEqual(
            scientific_by_name,
            {
                (
                    "pontius.affine_resident_heterogeneous_leaf_contraction."
                    "CuPyAffineResidentAutomatonCache.compile"
                ): ("compile", "scientific_artifact"),
                (
                    "pontius.heterogeneous_leaf_contraction."
                    "contract_heterogeneous_leaf_terms"
                ): ("contract", "scientific_result"),
                (
                    "pontius.shared_resident_response_context."
                    "bind_resident_response_context"
                ): ("bind", "scientific_context"),
            },
        )

    def test_declared_unconditional_skip_body_cannot_grant_capabilities(self) -> None:
        stable_id, (literal, _, _) = next(iter(DECLARED_UNCONDITIONAL_SKIPS.items()))
        relative_path, case_name, method_name = stable_id.split("::")
        sources = {
            relative_path: _source(
                f"""
                import subprocess
                import unittest
                class {case_name}(unittest.TestCase):
                    @unittest.skip({literal!r})
                    def {method_name}(self):
                        subprocess.run(["forbidden-unreachable-program"])
                """
            )
        }
        inventory = dict(self.inventory)
        inventory["baseline_discovery"] = {
            "test_file_count": 1,
            "stable_id_count": 1,
            "stable_ids_sha256": _ids_digest([stable_id]),
        }
        inventory["discovery"] = {
            "test_file_count": 1,
            "stable_id_count": 1,
            "stable_ids_sha256": _ids_digest([stable_id]),
        }
        inventory["entries"] = [
            self._inventory_entry(
                stable_id,
                expectation={
                    "kind": "declared_unconditional_skip",
                    "skip_safe_reason_code": DECLARED_UNCONDITIONAL_SKIPS[stable_id][1],
                },
            )
        ]
        inventory_bytes = _canonical_json_bytes(inventory) + b"\n"
        review = self.generator.derive_design_review(
            baseline_commit=self.baseline_commit,
            baseline_root_tree_oid=self.baseline_tree,
            inventory_document=inventory,
            inventory_document_bytes=inventory_bytes,
            sources=sources,
            item_universe=(("stable_id", stable_id),),
        )
        self.assertEqual(review["receipt"]["expanded_rows"], [])
        self.assertEqual(
            review["receipt"]["deny_all"],
            [{"item_kind": "stable_id", "item_id": stable_id}],
        )
        self.assertNotIn(
            b"forbidden-unreachable-program",
            _canonical_json_bytes(review["receipt"]["expanded_rows"]),
        )

        excluded_inventory = json.loads(json.dumps(self.inventory))
        excluded_entry = next(
            row
            for row in excluded_inventory["entries"]
            if row["stable_id"] == self.denied_id
        )
        excluded_entry.pop("assignment")
        excluded_entry.pop("baseline_assignment")
        excluded_entry["exclusion"] = {
            "reason": "reviewed non-runtime selector",
            "owner": "test-architecture",
            "milestone": "task-2",
        }
        excluded_discovery = self.generator.discover_test_sources(
            {"tests/test_review.py": self.sources["tests/test_review.py"]}
        )
        excluded_universe = self.generator._item_universe(
            excluded_inventory,
            excluded_discovery,
        )
        self.assertIn(("stable_id", self.denied_id), excluded_universe)
        excluded_review = self.generator.derive_design_review(
            baseline_commit=self.baseline_commit,
            baseline_root_tree_oid=self.baseline_tree,
            inventory_document=excluded_inventory,
            inventory_document_bytes=(
                _canonical_json_bytes(excluded_inventory) + b"\n"
            ),
            sources=self.sources,
            item_universe=excluded_universe,
        )
        self.assertIn(
            {"item_kind": "stable_id", "item_id": self.denied_id},
            excluded_review["receipt"]["deny_all"],
        )

    def test_unresolved_dynamic_process_target_is_a_blocker_not_an_authorization(self) -> None:
        dynamic_sources = {
            "tests/test_review.py": _source(
                """
                import subprocess
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        command = obtain_command()
                        subprocess.run(command)
                    def test_denied(self): pass
                """
            )
        }
        review = self._review(sources=dynamic_sources)
        self.assertTrue(review["unresolved_dynamic_blockers"])
        self.assertFalse(review["receipt"]["expanded_rows"])
        with self.assertRaisesRegex(Exception, "unresolved dynamic"):
            self.generator.validate_design_approval(
                review,
                review["spec_capabilities_sha256"],
                review["design_review_receipt_sha256"],
            )

        with tempfile.TemporaryDirectory(
            prefix="pontius-design-write-blocker-"
        ) as temporary:
            root = Path(temporary)
            dynamic_transaction_source = self._transaction_source().replace(
                b'[sys.executable, "-m", "core_demo"]',
                b"obtain_command()",
            )
            _, _, profiles_path = self._make_transaction_repository(
                root,
                source=dynamic_transaction_source,
            )
            fresh = self._fresh_transaction_review(root)
            self.assertTrue(fresh["unresolved_dynamic_blockers"])
            before = profiles_path.read_bytes()
            with self.assertRaisesRegex(Exception, "unresolved dynamic"):
                self.generator.write_design_capabilities(
                    root,
                    approved_spec_capabilities_sha256=fresh[
                        "spec_capabilities_sha256"
                    ],
                    approved_design_review_receipt_sha256=fresh[
                        "design_review_receipt_sha256"
                    ],
                )
            self.assertEqual(profiles_path.read_bytes(), before)

        dynamic_call_sources = {
            "tests/test_review.py": _source(
                """
                import pontius.gpu_occupied_card_quotient as occupied
                import unittest

                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        target = getattr(
                            occupied,
                            obtain_owner_entrypoint_name(),
                        )
                        target()

                    def test_denied(self):
                        pass
                """
            )
        }
        dynamic_call_review = self._review(sources=dynamic_call_sources)
        call_blockers = dynamic_call_review["unresolved_dynamic_blockers"]
        self.assertEqual(
            {row["item_id"] for row in call_blockers},
            {self.static_id},
        )
        self.assertTrue(
            all(
                "dynamic" in row["reason"] and "call" in row["reason"]
                for row in call_blockers
            )
        )
        self.assertFalse(dynamic_call_review["receipt"]["expanded_rows"])
        self.assertIn(
            {"item_kind": "stable_id", "item_id": self.static_id},
            dynamic_call_review["receipt"]["deny_all"],
        )

        closure_cases = (
            (
                "invoked lambda closure",
                """
                import subprocess
                import sys
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        (lambda: subprocess.run(
                            [sys.executable, "-m", "lambda"],
                            timeout=5,
                            check=False,
                        ))()
                    def test_denied(self): pass
                """,
            ),
            (
                "local class runtime closure",
                """
                import subprocess
                import sys
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        class LocalLauncher:
                            def launch(self):
                                subprocess.run(
                                    [sys.executable, "-m", "local-class"],
                                    timeout=5,
                                    check=False,
                                )
                        LocalLauncher().launch()
                    def test_denied(self): pass
                """,
            ),
            (
                "callback closure",
                """
                import subprocess
                import sys
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        callback = lambda: subprocess.run(
                            [sys.executable, "-m", "callback"],
                            timeout=5,
                            check=False,
                        )
                        invoke_callback(callback)
                    def test_denied(self): pass
                """,
            ),
        )
        for expected_reason, source in closure_cases:
            with self.subTest(closure=expected_reason):
                closure_review = self._review(
                    sources={"tests/test_review.py": _source(source)}
                )
                self.assertTrue(
                    any(
                        row["item_id"] == self.static_id
                        and expected_reason in row["reason"]
                        for row in closure_review["unresolved_dynamic_blockers"]
                    )
                )

        alias_review = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import subprocess
                    import sys
                    import unittest
                    def _launch():
                        subprocess.run(
                            [sys.executable, "-m", "alias"],
                            timeout=5,
                            check=False,
                        )
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            alias = _launch
                            alias()
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertIn(
            ["-m", "alias"],
            [
                row["argv"]
                for row in alias_review["receipt"]["expanded_rows"]
                if row["item_id"] == self.static_id
                and row["capability_kind"] == "subprocess"
            ],
        )

        local_class_definition = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            class RuntimeClass:
                                process = subprocess.run(
                                    [sys.executable, "-m", "local-definition"],
                                    timeout=5,
                                    check=False,
                                )
                            self.assertIsNotNone(RuntimeClass)
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertIn(
            ["-m", "local-definition"],
            [
                row["argv"]
                for row in local_class_definition["receipt"]["expanded_rows"]
                if row["item_id"] == self.static_id
                and row["capability_kind"] == "subprocess"
            ],
        )

        named_callback = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            def callback():
                                subprocess.run(
                                    [sys.executable, "-m", "named-callback"],
                                    timeout=5,
                                    check=False,
                                )
                            invoke_callback(callback=callback)
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertTrue(
            any(
                row["item_id"] == self.static_id
                and "callback closure" in row["reason"]
                for row in named_callback["unresolved_dynamic_blockers"]
            )
        )

        mixed_receiver = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import numpy as np
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            backend = cp if obtain_condition() else np
                            backend.arange(1)
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertTrue(
            any(
                row["item_id"] == self.static_id
                and "mixed protected receiver" in row["reason"]
                for row in mixed_receiver["unresolved_dynamic_blockers"]
            )
        )

        dynamic_alias = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import subprocess
                    import sys
                    import unittest
                    def _launch():
                        subprocess.run(
                            [sys.executable, "-m", "conditional-alias"],
                            timeout=5,
                            check=False,
                        )
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            alias = _launch if obtain_condition() else no_op
                            alias()
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertTrue(
            any(
                row["item_id"] == self.static_id
                and "callable alias" in row["reason"]
                for row in dynamic_alias["unresolved_dynamic_blockers"]
            )
        )

        fixture_review = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def setUp(self):
                            subprocess.run(
                                [sys.executable, "-m", "per-test-setup"],
                                timeout=5,
                                check=False,
                            )
                        def tearDown(self):
                            subprocess.run(
                                [sys.executable, "-m", "per-test-teardown"],
                                timeout=5,
                                check=False,
                            )
                        def test_static(self): pass
                        def test_denied(self): pass
                    """
                )
            }
        )
        fixture_rows = fixture_review["receipt"]["expanded_rows"]
        self.assertEqual(
            {
                (row["item_id"], tuple(row["argv"]))
                for row in fixture_rows
                if row["capability_kind"] == "subprocess"
            },
            {
                (item_id, argv)
                for item_id in (self.static_id, self.denied_id)
                for argv in (("-m", "per-test-setup"), ("-m", "per-test-teardown"))
            },
        )

        for keyword in ("executable", "preexec_fn", "stdout", "input"):
            with self.subTest(unsupported_keyword=keyword):
                keyword_review = self._review(
                    sources={
                        "tests/test_review.py": _source(
                            f"""
                            import subprocess
                            import sys
                            import unittest
                            class ReviewTests(unittest.TestCase):
                                def test_static(self):
                                    subprocess.run(
                                        [sys.executable, "-m", "unsafe"],
                                        timeout=5,
                                        check=False,
                                        {keyword}=unsafe_value,
                                    )
                                def test_denied(self): pass
                            """
                        )
                    }
                )
                self.assertTrue(
                    any(
                        f"unsupported subprocess keyword: {keyword}" in row["reason"]
                        for row in keyword_review["unresolved_dynamic_blockers"]
                    )
                )

        environment_review = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import os
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            environment = dict(os.environ)
                            environment["SAFE"] = "1"
                            environment.pop("DROP", None)
                            subprocess.run(
                                [sys.executable, "-m", "environment"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self):
                            subprocess.run(
                                [sys.executable, "-m", "inherited"],
                                timeout=5,
                                check=False,
                            )
                    """
                )
            }
        )
        environment_rows = {
            row["item_id"]: row
            for row in environment_review["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        }
        self.assertEqual(environment_rows[self.static_id]["environment_additions"], {"SAFE": "1"})
        self.assertEqual(environment_rows[self.static_id]["environment_removals"], ["DROP"])
        self.assertEqual(environment_rows[self.denied_id]["environment_additions"], {})
        self.assertEqual(environment_rows[self.denied_id]["environment_removals"], [])

        ordered_environment = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import os
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            environment = dict(os.environ)
                            environment.pop("FLIP", None)
                            environment["FLIP"] = "first"
                            subprocess.run(
                                [sys.executable, "-m", "first"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                            environment["FLIP"] = "second"
                            environment.pop("FLIP", None)
                            subprocess.run(
                                [sys.executable, "-m", "second"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    """
                )
            }
        )
        ordered_rows = {
            tuple(row["argv"]): row
            for row in ordered_environment["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        }
        self.assertEqual(
            ordered_rows[("-m", "first")]["environment_additions"],
            {"FLIP": "first"},
        )
        self.assertEqual(
            ordered_rows[("-m", "first")]["environment_removals"],
            [],
        )
        self.assertEqual(
            ordered_rows[("-m", "second")]["environment_additions"],
            {},
        )
        self.assertEqual(
            ordered_rows[("-m", "second")]["environment_removals"],
            ["FLIP"],
        )

        replacement_review = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            subprocess.run(
                                [sys.executable, "-m", "replacement"],
                                env={"SAFE": "1"},
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertTrue(
            any(
                "environment replacement" in row["reason"]
                for row in replacement_review["unresolved_dynamic_blockers"]
            )
        )

    def test_registered_probe_and_cross_file_helpers_are_exactly_resolved(self) -> None:
        sources = {
            "tests/test_review.py": _source(
                """
                import unittest
                from tests.review_support import launch

                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        launch(module="cross_file", timeout=7)

                    def test_denied(self):
                        pass
                """
            ),
            "tests/review_support.py": _source(
                """
                import subprocess
                import sys

                def launch(module="default", *, timeout=5):
                    subprocess.run(
                        [sys.executable, "-m", module],
                        cwd=".",
                        env={**__import__("os").environ, "SAFE": "1"},
                        timeout=timeout,
                        check=False,
                    )
                """
            ),
            "tools/test_child.py": _source(
                """
                def _run_gpu_probe():
                    import cupy as cp
                    return cp.cuda.runtime.getDeviceCount()
                """
            ),
        }
        review = self._review(sources=sources)
        rows = review["receipt"]["expanded_rows"]
        self.assertEqual(
            {
                (row["item_id"], row["capability_kind"])
                for row in rows
            },
            {
                (self.static_id, "subprocess"),
                ("probe:gpu-availability", "call"),
            },
        )
        process = next(
            row for row in rows if row["capability_kind"] == "subprocess"
        )
        self.assertEqual(process["argv"], ["-m", "cross_file"])
        self.assertEqual(process["timeout_ns"], 7_000_000_000)
        probe = next(row for row in rows if row["capability_kind"] == "call")
        self.assertEqual(probe["item_id"], "probe:gpu-availability")
        self.assertEqual(probe["kind"], "cuda_query")
        self.assertEqual(
            probe["qualified_name"],
            "cupy.cuda.runtime.getDeviceCount",
        )
        self.assertFalse(review["unresolved_dynamic_blockers"])

        missing_probe = self._review(
            sources={
                key: value
                for key, value in sources.items()
                if key != "tools/test_child.py"
            },
            include_probe=False,
        )
        self.assertIn(
            {
                "item_id": "probe:gpu-availability",
                "relative_path": "tools/test_child.py",
                "line": 0,
                "reason": "registered probe implementation is absent",
            },
            missing_probe["unresolved_dynamic_blockers"],
        )

        unresolved_helper = self._review(
            sources={
                key: value
                for key, value in sources.items()
                if key != "tests/review_support.py"
            }
        )
        self.assertTrue(
            any(
                "test-local helper closure" in row["reason"]
                for row in unresolved_helper["unresolved_dynamic_blockers"]
            )
        )

    def test_helper_registry_and_argument_binding_fail_closed(self) -> None:
        ambiguous = {
            "tests/a/test_shared.py": ast.parse("def launch(): pass\n"),
            "tests/b/test_shared.py": ast.parse("def launch(): pass\n"),
        }
        with self.assertRaisesRegex(Exception, "ambiguous.*registry"):
            self.generator._review_function_registry(ambiguous)

        tools_only = self.generator._review_function_registry(
            {
                "tools/test_child.py": ast.parse(
                    "def _run_gpu_probe(): pass\n"
                )
            }
        )
        self.assertIn("tools.test_child._run_gpu_probe", tools_only)
        self.assertNotIn("tests.test_child._run_gpu_probe", tools_only)

        bound_sources = {
            "tests/test_review.py": _source(
                """
                import subprocess
                import sys
                import unittest

                class ReviewTests(unittest.TestCase):
                    @classmethod
                    def _launch(cls, module="default", *, timeout=5):
                        subprocess.run(
                            [sys.executable, "-m", module],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=timeout, check=False,
                        )

                    def test_static(self):
                        self._launch(module="bound", timeout=7)

                    def test_denied(self):
                        pass
                """
            ),
            "tools/test_child.py": self.sources["tools/test_child.py"],
        }
        bound = self._review(sources=bound_sources)
        process = next(
            row
            for row in bound["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        )
        self.assertEqual(process["argv"], ["-m", "bound"])
        self.assertEqual(process["timeout_ns"], 7_000_000_000)

        for invocation in (
            "self._launch(*obtain_args())",
            "self._launch(**obtain_kwargs())",
            "self._launch(unknown=1)",
        ):
            with self.subTest(invocation=invocation):
                dynamic_source = bound_sources["tests/test_review.py"].replace(
                    b'self._launch(module="bound", timeout=7)',
                    invocation.encode("ascii"),
                )
                dynamic = self._review(
                    sources={
                        "tests/test_review.py": dynamic_source,
                        "tools/test_child.py": self.sources[
                            "tools/test_child.py"
                        ],
                    }
                )
                self.assertTrue(
                    any(
                        "helper arguments" in row["reason"]
                        for row in dynamic["unresolved_dynamic_blockers"]
                    )
                )

        conflicting_sources = {
            "tests/test_review.py": _source(
                """
                import unittest
                from tests.review_support import launch

                MODULE = "caller-value"

                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        launch()

                    def test_denied(self):
                        pass
                """
            ),
            "tests/review_support.py": _source(
                """
                import subprocess
                import sys

                MODULE = "callee-value"

                def launch(module=MODULE):
                    subprocess.run(
                        [sys.executable, "-m", module],
                        cwd=".",
                        env={**__import__("os").environ, "SAFE": "1"},
                        timeout=5, check=False,
                    )
                """
            ),
        }
        conflicting = self._review(sources=conflicting_sources)
        conflicting_process = next(
            row
            for row in conflicting["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        )
        self.assertEqual(conflicting_process["argv"], ["-m", "callee-value"])

        class_helper_sources = {
            "tests/test_review.py": _source(
                """
                import subprocess
                import sys
                import unittest

                class OtherFixture:
                    @classmethod
                    def setUpClass(cls):
                        subprocess.run(
                            [sys.executable, "-m", "other-class"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5, check=False,
                        )

                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        OtherFixture.setUpClass()

                    def test_denied(self):
                        pass
                """
            ),
        }
        class_helper = self._review(sources=class_helper_sources)
        self.assertEqual(
            [
                row["argv"]
                for row in class_helper["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            ],
            [["-m", "other-class"]],
        )

        nested_invocation = bound_sources["tests/test_review.py"].replace(
            b'self._launch(module="bound", timeout=7)',
            (
                b"def nested_launch():\n"
                b"            self._launch(module=\"nested\")\n"
                b"        nested_launch()"
            ),
        )
        nested = self._review(
            sources={"tests/test_review.py": nested_invocation}
        )
        nested_process = next(
            row
            for row in nested["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        )
        self.assertEqual(nested_process["argv"], ["-m", "nested"])
        self.assertFalse(
            any(
                "nested helper closure" in row["reason"]
                for row in nested["unresolved_dynamic_blockers"]
            )
        )

    def test_import_time_nested_and_duplicate_sensitive_calls_fail_closed(self) -> None:
        import_time = {
            "tests/test_review.py": _source(
                """
                import subprocess
                import sys
                import unittest

                IMPORT_SIDE_EFFECT = subprocess.run(
                    [sys.executable, "-m", "import_side_effect"],
                    cwd=".",
                    env={**__import__("os").environ, "SAFE": "1"},
                    timeout=5,
                    check=False,
                )

                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        def unreachable():
                            subprocess.run(
                                [sys.executable, "-m", "nested_decoy"],
                                cwd=".",
                                env={**__import__("os").environ, "SAFE": "1"},
                                timeout=5, check=False,
                            )
                        callback = lambda: subprocess.run(
                            [sys.executable, "-m", "lambda_decoy"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5, check=False,
                        )
                        self.assertIsNotNone(callback)

                    def test_denied(self):
                        pass
                """
            ),
            "tools/test_child.py": self.sources["tools/test_child.py"],
        }
        review = self._review(sources=import_time)
        blockers = review["unresolved_dynamic_blockers"]
        self.assertTrue(
            any(
                row["item_id"] == "unowned:import-time"
                and "import-time" in row["reason"]
                for row in blockers
            )
        )
        encoded_rows = _canonical_json_bytes(review["receipt"]["expanded_rows"])
        self.assertNotIn(b"nested_decoy", encoded_rows)
        self.assertNotIn(b"lambda_decoy", encoded_rows)

        nested_dynamic = {
            "tests/test_review.py": _source(
                """
                import pontius.gpu_occupied_card_quotient as occupied
                import unittest

                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        if obtain_condition():
                            target = getattr(
                                occupied,
                                obtain_owner_entrypoint_name(),
                            )
                        target()

                    def test_denied(self):
                        pass
                """
            ),
            "tools/test_child.py": self.sources["tools/test_child.py"],
        }
        dynamic = self._review(sources=nested_dynamic)
        self.assertTrue(
            any(
                "dynamic sensitive call" in row["reason"]
                for row in dynamic["unresolved_dynamic_blockers"]
            )
        )

        duplicate = {
            "tests/test_review.py": _source(
                """
                import subprocess
                import sys
                import unittest

                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        subprocess.run(
                            [sys.executable, "-m", "same"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5, check=False,
                        )
                        subprocess.run(
                            [sys.executable, "-m", "same"],
                            cwd=".",
                            env={**__import__("os").environ, "SAFE": "1"},
                            timeout=5, check=False,
                        )

                    def test_denied(self):
                        pass
                """
            ),
            "tools/test_child.py": self.sources["tools/test_child.py"],
        }
        repeated = self._review(sources=duplicate)
        self.assertTrue(
            any(
                "subprocess multiplicity" in row["reason"]
                for row in repeated["unresolved_dynamic_blockers"]
            )
        )
        self.assertNotIn(
            self.static_id,
            {
                row["item_id"]
                for row in repeated["receipt"]["expanded_rows"]
            },
        )


class AtomicAndGitBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = _load_generator()

    def test_atomic_lf_writer_rejects_noncanonical_bytes_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-inventory-writer-") as temporary:
            target = Path(temporary) / "inventory.json"
            target.write_bytes(b"old\n")
            for invalid in (
                b"missing-final-lf",
                b"bad\r\n",
                b"double-final-lf\n\n",
                b"\xef\xbb\xbf{}\n",
            ):
                with self.subTest(invalid=invalid):
                    with self.assertRaisesRegex(Exception, "canonical LF"):
                        self.generator.write_atomic_lf(target, invalid)
                    self.assertEqual(target.read_bytes(), b"old\n")

            with self.assertRaisesRegex(Exception, "write bound"):
                self.generator.write_atomic_lf(
                    target,
                    b"x" * (self.generator.MAXIMUM_SOURCE_BYTES + 1) + b"\n",
                )
            self.assertEqual(target.read_bytes(), b"old\n")

            callback_states: list[tuple[str, bytes]] = []

            def check_old_destination() -> None:
                callback_states.append(("before", target.read_bytes()))

            def check_new_destination(snapshot: object) -> None:
                callback_states.append(("after", target.read_bytes()))
                self.assertEqual(snapshot.raw, b"new\n")
                snapshot.revalidate()

            self.generator.write_atomic_lf(
                target,
                b"new\n",
                _lifetime_check=check_old_destination,
                _post_publish_lifetime_check=check_new_destination,
            )
            self.assertEqual(target.read_bytes(), b"new\n")
            self.assertEqual(
                callback_states,
                [("before", b"old\n"), ("after", b"new\n")],
            )
            self.assertEqual({path.name for path in target.parent.iterdir()}, {target.name})

    def test_atomic_replace_failure_preserves_original_and_cleans_staging_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-inventory-writer-") as temporary:
            target = Path(temporary) / "profiles.toml"
            target.write_bytes(b"old\n")
            with mock.patch.object(
                self.generator,
                "_publish_staged_governance",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaisesRegex(Exception, "replace failed"):
                    self.generator.write_atomic_lf(target, b"new\n")
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual({path.name for path in target.parent.iterdir()}, {target.name})

            first = Path(temporary) / "inventory.json"
            second = Path(temporary) / "profiles-secondary.toml"
            first.write_bytes(b"old-inventory\n")
            second.write_bytes(b"old-profiles\n")
            first_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                first,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=first.parent,
            )
            second_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                second,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=second.parent,
            )
            publish = self.generator._publish_staged_governance
            publish_calls = 0

            def fail_second_publish(**kwargs: object) -> None:
                nonlocal publish_calls
                publish_calls += 1
                if publish_calls == 2:
                    raise OSError("second publish failed")
                publish(**kwargs)

            with mock.patch.object(
                self.generator,
                "_publish_staged_governance",
                side_effect=fail_second_publish,
            ):
                with self.assertRaisesRegex(Exception, "second publish failed"):
                    self.generator._write_governance_pair(
                        first,
                        b"new-inventory\n",
                        first_snapshot,
                        second,
                        b"new-profiles\n",
                        second_snapshot,
                    )
            self.assertEqual(first.read_bytes(), b"old-inventory\n")
            self.assertEqual(second.read_bytes(), b"old-profiles\n")

            first_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                first,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=first.parent,
            )
            second_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                second,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=second.parent,
            )
            publish_calls = 0

            def mutate_second_publish(**kwargs: object) -> None:
                nonlocal publish_calls
                publish_calls += 1
                if publish_calls == 2:
                    second.write_bytes(b"concurrent-profiles\n")
                    raise OSError("second publish raced")
                publish(**kwargs)

            with mock.patch.object(
                self.generator,
                "_publish_staged_governance",
                side_effect=mutate_second_publish,
            ):
                with self.assertRaisesRegex(Exception, "second publish raced"):
                    self.generator._write_governance_pair(
                        first,
                        b"new-inventory\n",
                        first_snapshot,
                        second,
                        b"new-profiles\n",
                        second_snapshot,
                    )
            self.assertEqual(first.read_bytes(), b"old-inventory\n")
            self.assertEqual(second.read_bytes(), b"concurrent-profiles\n")

            second.write_bytes(b"old-profiles\n")
            first_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                first,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=first.parent,
            )
            second_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                second,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=second.parent,
            )
            publish_calls = 0

            def mutate_first_after_second(**kwargs: object) -> None:
                nonlocal publish_calls
                publish_calls += 1
                publish(**kwargs)
                if publish_calls == 2:
                    first.write_bytes(b"concurrent-inventory\n")

            with mock.patch.object(
                self.generator,
                "_publish_staged_governance",
                side_effect=mutate_first_after_second,
            ):
                with self.assertRaisesRegex(Exception, "rollback both failed"):
                    self.generator._write_governance_pair(
                        first,
                        b"new-inventory\n",
                        first_snapshot,
                        second,
                        b"new-profiles\n",
                        second_snapshot,
                    )
            self.assertEqual(first.read_bytes(), b"concurrent-inventory\n")
            self.assertEqual(second.read_bytes(), b"old-profiles\n")

    def test_atomic_publish_is_cas_bound_and_restores_post_publish_failures(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-inventory-cas-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            original_publish = self.generator._publish_staged_governance

            def concurrent_publish(**keywords: object) -> None:
                target.write_bytes(b"concurrent\n")
                original_publish(**keywords)

            with mock.patch.object(
                self.generator,
                "_publish_staged_governance",
                side_effect=concurrent_publish,
            ):
                with self.assertRaisesRegex(Exception, "identity changed"):
                    self.generator.write_atomic_lf(target, b"generated\n")
            self.assertEqual(target.read_bytes(), b"concurrent\n")
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {target.name},
            )

            target.write_bytes(b"old\n")
            checks = 0

            def fail_after_publish() -> None:
                nonlocal checks
                checks += 1
                if checks == 2:
                    raise OSError("post-publish attribute drift")

            with self.assertRaisesRegex(Exception, "attribute drift"):
                self.generator.write_atomic_lf(
                    target,
                    b"generated\n",
                    _lifetime_check=fail_after_publish,
                )
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {target.name},
            )

            inventory = root / "inventory.json"
            inventory.write_bytes(b"old-inventory\n")
            first_snapshot = (
                self.generator.secure_filesystem.read_regular_snapshot(
                    inventory,
                    maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                    root=root,
                )
            )
            second_snapshot = (
                self.generator.secure_filesystem.read_regular_snapshot(
                    target,
                    maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                    root=root,
                )
            )
            pair_checks = 0

            def fail_second_post_publish() -> None:
                nonlocal pair_checks
                pair_checks += 1
                if pair_checks == 4:
                    raise OSError("second post-publish drift")

            with self.assertRaisesRegex(Exception, "post-publish drift"):
                self.generator._write_governance_pair(
                    inventory,
                    b"new-inventory\n",
                    first_snapshot,
                    target,
                    b"new-profiles\n",
                    second_snapshot,
                    lifetime_check=fail_second_post_publish,
                )
            self.assertEqual(inventory.read_bytes(), b"old-inventory\n")
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {inventory.name, target.name},
            )

            target.write_bytes(b"old\n")
            real_read = self.generator.secure_filesystem.read_regular_snapshot

            def fail_public_snapshot(*args: object, **kwargs: object) -> object:
                snapshot = real_read(*args, **kwargs)
                if snapshot.raw == b"generated\n":
                    raise OSError("public post-publish snapshot failed")
                return snapshot

            with mock.patch.object(
                self.generator.secure_filesystem,
                "read_regular_snapshot",
                side_effect=fail_public_snapshot,
            ):
                with self.assertRaisesRegex(Exception, "post-publish snapshot"):
                    self.generator.write_atomic_lf(target, b"generated\n")
            self.assertEqual(target.read_bytes(), b"old\n")

            source = root / "source.py"
            source.write_bytes(b"VALUE = 1\n")
            source_snapshot = real_read(
                source,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            inventory.write_bytes(b"old-inventory\n")
            target.write_bytes(b"old\n")
            first_snapshot = real_read(
                inventory,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            second_snapshot = real_read(
                target,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            real_write = self.generator.write_atomic_lf
            write_count = 0

            def mutate_after_first(*args: object, **kwargs: object) -> object:
                nonlocal write_count
                result = real_write(*args, **kwargs)
                write_count += 1
                if write_count == 1:
                    source.write_bytes(b"VALUE = 2\n")
                return result

            with mock.patch.object(
                self.generator,
                "write_atomic_lf",
                side_effect=mutate_after_first,
            ):
                with self.assertRaisesRegex(
                    Exception,
                    "(?:snapshot|file).*(?:changed|drift)",
                ):
                    self.generator._write_governance_pair(
                        inventory,
                        b"new-inventory\n",
                        first_snapshot,
                        target,
                        b"new-profiles\n",
                        second_snapshot,
                        lifetime_check=source_snapshot.revalidate,
                    )
            self.assertEqual(inventory.read_bytes(), b"old-inventory\n")
            self.assertEqual(target.read_bytes(), b"old\n")

            if os.name == "nt":
                target.write_bytes(b"old\n")
                real_rename = self.generator._windows_rename_governance_file
                visible_at_replace: list[bool] = []

                def observe_visibility(*args: object, **kwargs: object) -> object:
                    replacing = kwargs.get("replace") is True
                    if replacing:
                        visible_at_replace.append(target.exists())
                    result = real_rename(*args, **kwargs)
                    if replacing:
                        visible_at_replace.append(target.exists())
                    return result

                with mock.patch.object(
                    self.generator,
                    "_windows_rename_governance_file",
                    side_effect=observe_visibility,
                ):
                    self.generator.write_atomic_lf(target, b"generated\n")
                self.assertEqual(visible_at_replace, [True, True])

                target.write_bytes(b"old\n")
                real_dispose = (
                    self.generator.secure_filesystem._windows_dispose_relative_file
                )
                real_close = self.generator.secure_filesystem._windows_close_file

                def fail_before_recovery_disposal(handle: int) -> None:
                    raise OSError("old recovery disposal failed")

                with mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_dispose_relative_file",
                    side_effect=fail_before_recovery_disposal,
                ):
                    with self.assertRaisesRegex(Exception, "recovery disposal"):
                        self.generator.write_atomic_lf(
                            target,
                            b"generated\n",
                        )
                self.assertEqual(target.read_bytes(), b"old\n")
                self.assertEqual(
                    {path.name for path in root.iterdir()},
                    {inventory.name, source.name, target.name},
                )

                disposed_handle: int | None = None
                failed_close = False
                recovery_close_calls = 0

                def record_dispose(handle: int) -> None:
                    nonlocal disposed_handle
                    if disposed_handle is None:
                        disposed_handle = handle
                    real_dispose(handle)

                def fail_first_recovery_close(handle: int) -> None:
                    nonlocal failed_close, recovery_close_calls
                    if handle == disposed_handle and not failed_close:
                        failed_close = True
                        recovery_close_calls += 1
                        real_close(handle)
                        raise OSError("old recovery close failed")
                    real_close(handle)

                with mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_dispose_relative_file",
                    side_effect=record_dispose,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_close_file",
                    side_effect=fail_first_recovery_close,
                ):
                    snapshot = self.generator.write_atomic_lf(
                        target,
                        b"generated\n",
                    )
                self.assertTrue(failed_close)
                self.assertEqual(recovery_close_calls, 1)
                self.assertEqual(snapshot.raw, b"generated\n")
                self.assertEqual(target.read_bytes(), b"generated\n")
                self.assertEqual(
                    {path.name for path in root.iterdir()},
                    {inventory.name, source.name, target.name},
                )

                inventory.write_bytes(b"old-inventory\n")
                target.write_bytes(b"old-profiles\n")
                first_snapshot = real_read(
                    inventory,
                    maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                    root=root,
                )
                second_snapshot = real_read(
                    target,
                    maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                    root=root,
                )
                disposed_handles: list[int] = []
                failed_pair_close = False
                second_recovery_close_calls = 0

                def record_pair_dispose(handle: int) -> None:
                    disposed_handles.append(handle)
                    real_dispose(handle)

                def fail_second_recovery_close(handle: int) -> None:
                    nonlocal failed_pair_close, second_recovery_close_calls
                    if (
                        len(disposed_handles) >= 2
                        and handle == disposed_handles[1]
                        and not failed_pair_close
                    ):
                        failed_pair_close = True
                        second_recovery_close_calls += 1
                        real_close(handle)
                        raise OSError("second recovery close failed")
                    real_close(handle)

                with mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_dispose_relative_file",
                    side_effect=record_pair_dispose,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_close_file",
                    side_effect=fail_second_recovery_close,
                ):
                    self.generator._write_governance_pair(
                        inventory,
                        b"new-inventory\n",
                        first_snapshot,
                        target,
                        b"new-profiles\n",
                        second_snapshot,
                    )
                self.assertTrue(failed_pair_close)
                self.assertEqual(second_recovery_close_calls, 1)
                self.assertEqual(inventory.read_bytes(), b"new-inventory\n")
                self.assertEqual(target.read_bytes(), b"new-profiles\n")
                self.assertEqual(
                    {path.name for path in root.iterdir()},
                    {inventory.name, source.name, target.name},
                )

                target.write_bytes(b"old\n")
                real_open_directory = (
                    self.generator._windows_open_governance_directory
                )
                real_close_directory = (
                    self.generator.secure_filesystem._windows_close_directory
                )
                publication_directory: int | None = None
                failed_post_commit_close = False
                publication_close_calls = 0

                def capture_publication_directory(
                    path: Path,
                ) -> tuple[int, tuple[int, bytes]]:
                    nonlocal publication_directory
                    opened = real_open_directory(path)
                    publication_directory = opened[0]
                    return opened

                def fail_post_commit_directory_close(handle: int) -> None:
                    nonlocal failed_post_commit_close, publication_close_calls
                    if (
                        handle == publication_directory
                        and target.read_bytes() == b"generated\n"
                        and not failed_post_commit_close
                    ):
                        failed_post_commit_close = True
                        publication_close_calls += 1
                        real_close_directory(handle)
                        raise OSError("post-commit directory close failed")
                    real_close_directory(handle)

                with mock.patch.object(
                    self.generator,
                    "_windows_open_governance_directory",
                    side_effect=capture_publication_directory,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_close_directory",
                    side_effect=fail_post_commit_directory_close,
                ):
                    snapshot = self.generator.write_atomic_lf(
                        target,
                        b"generated\n",
                    )
                self.assertTrue(failed_post_commit_close)
                self.assertEqual(publication_close_calls, 1)
                self.assertEqual(snapshot.raw, b"generated\n")
                self.assertEqual(target.read_bytes(), b"generated\n")
                self.assertEqual(
                    {path.name for path in root.iterdir()},
                    {inventory.name, source.name, target.name},
                )

            cleanup_events: list[str] = []

            def fail_post_commit_cleanup() -> None:
                cleanup_events.append("close")
                raise OSError("portable post-commit close failed")

            self.generator._best_effort_governance_close(
                fail_post_commit_cleanup
            )
            self.assertEqual(cleanup_events, ["close"])

            stat_result = mock.Mock(
                st_mode=0o100600,
                st_dev=1,
                st_ino=2,
                st_size=4,
                st_mtime_ns=0,
                st_ctime_ns=0,
                st_file_attributes=0,
                st_reparse_tag=0,
            )
            publish_state = self.generator._GovernancePublishState()
            outcome = self.generator._GovernanceWriteOutcome()
            with mock.patch.object(
                self.generator,
                "_require_governance_destination_identity",
            ), mock.patch.object(
                self.generator.os,
                "fstat",
                return_value=stat_result,
            ), mock.patch.object(
                self.generator.os,
                "stat",
                return_value=stat_result,
            ), mock.patch.object(
                self.generator.os,
                "link",
            ), mock.patch.object(
                self.generator.os,
                "unlink",
            ):
                self.generator._publish_staged_governance(
                    temporary_name=".new.tmp",
                    temporary_handle=7,
                    destination_name="new.json",
                    parent_handle=8,
                    windows=False,
                    destination_path=root / "new.json",
                    expected_identity=None,
                    expected_raw=None,
                    state=publish_state,
                    outcome=outcome,
                )
            self.assertIsNone(publish_state.recovery_name)
            self.assertIsNone(outcome.recovery_path)

            expected_identity = (
                1,
                2,
                4,
                0,
                0,
                0o100600,
                0,
                0,
            )
            recovery_snapshot = mock.Mock(
                identity=expected_identity,
                raw=b"old\n",
            )
            fallback_state = self.generator._GovernancePublishState()
            fallback_outcome = self.generator._GovernanceWriteOutcome()
            with mock.patch.object(
                self.generator.os,
                "O_NOFOLLOW",
                0,
                create=True,
            ), mock.patch.object(
                self.generator,
                "_require_governance_destination_identity",
            ), mock.patch.object(
                self.generator,
                "_posix_exchange_governance_file",
                return_value=False,
            ), mock.patch.object(
                self.generator.os,
                "fstat",
                return_value=stat_result,
            ), mock.patch.object(
                self.generator.os,
                "stat",
                return_value=stat_result,
            ), mock.patch.object(
                self.generator.os,
                "open",
                return_value=9,
            ), mock.patch.object(
                self.generator.os,
                "link",
            ) as link, mock.patch.object(
                self.generator.os,
                "replace",
            ) as replace, mock.patch.object(
                self.generator.secure_filesystem,
                "read_regular_snapshot",
                return_value=recovery_snapshot,
            ):
                self.generator._publish_staged_governance(
                    temporary_name=".old.tmp",
                    temporary_handle=7,
                    destination_name="old.json",
                    parent_handle=8,
                    windows=False,
                    destination_path=root / "old.json",
                    expected_identity=expected_identity,
                    expected_raw=b"old\n",
                    state=fallback_state,
                    outcome=fallback_outcome,
                )
            link.assert_called_once()
            replace.assert_called_once()
            self.assertTrue(fallback_state.published)
            self.assertTrue(fallback_state.displaced)
            self.assertFalse(fallback_state.posix_exchange)
            self.assertIsNotNone(fallback_outcome.recovery_path)

        fake_lease = mock.Mock()
        attribute_checks = 0

        def verify_attributes(*args: object, **kwargs: object) -> None:
            nonlocal attribute_checks
            attribute_checks += 1
            if attribute_checks == 3:
                raise OSError("final attribute drift")

        def mutate_after_callback(revalidate: object) -> str:
            revalidate()
            return "accepted"

        with mock.patch.object(
            self.generator,
            "_strict_git_snapshot",
            side_effect=(
                (Path("C:/git.exe"), b"git", (1,)),
                (Path("C:/git.exe"), b"git", (1,)),
            ),
        ), mock.patch.object(
            self.generator,
            "_acquire_git_launch_lease",
            return_value=fake_lease,
        ), mock.patch.object(
            self.generator,
            "_verify_governance_attributes",
            side_effect=verify_attributes,
        ), mock.patch.object(
            self.generator,
            "_revalidate_git_launch_lease",
        ):
            with self.assertRaisesRegex(Exception, "final attribute drift"):
                self.generator._with_governance_attribute_lease(
                    SNAPSHOT_ROOT,
                    Path("C:/git.exe"),
                    mutate_after_callback,
                )

    def test_outer_transaction_retains_recovery_through_final_validation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-outer-transaction-"
        ) as temporary:
            root = Path(temporary)
            absent = root / "review.json"
            checks = 0

            def fail_after_absent_publish() -> None:
                nonlocal checks
                checks += 1
                if checks == 2:
                    raise OSError("post-publish source drift")

            with self.assertRaisesRegex(Exception, "source drift"):
                self.generator.write_atomic_lf(
                    absent,
                    b"generated\n",
                    _lifetime_check=fail_after_absent_publish,
                )
            self.assertFalse(absent.exists())
            self.assertEqual(tuple(root.iterdir()), ())

            real_read = self.generator.secure_filesystem.read_regular_snapshot

            def fail_absent_snapshot(*args: object, **kwargs: object) -> object:
                snapshot = real_read(*args, **kwargs)
                if snapshot.path == absent and snapshot.raw == b"generated\n":
                    raise OSError("published recovery acquisition failed")
                return snapshot

            with mock.patch.object(
                self.generator.secure_filesystem,
                "read_regular_snapshot",
                side_effect=fail_absent_snapshot,
            ):
                with self.assertRaisesRegex(Exception, "recovery acquisition"):
                    self.generator.write_atomic_lf(absent, b"generated\n")
            self.assertFalse(absent.exists())
            self.assertEqual(tuple(root.iterdir()), ())

            fake_lease = mock.Mock()
            attribute_checks = 0

            def fail_final_attributes(*args: object, **kwargs: object) -> None:
                nonlocal attribute_checks
                attribute_checks += 1
                if attribute_checks == 4:
                    raise OSError("final outer attribute drift")

            def publish_absent(attribute_check: object) -> object:
                return self.generator.write_atomic_lf(
                    absent,
                    b"generated\n",
                    _lifetime_check=attribute_check,
                )

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                return_value=(Path("C:/git.exe"), b"git", (1,)),
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=fake_lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
                side_effect=fail_final_attributes,
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ):
                with self.assertRaisesRegex(Exception, "outer attribute drift"):
                    self.generator._with_governance_attribute_lease(
                        root,
                        Path("C:/git.exe"),
                        publish_absent,
                    )
            self.assertFalse(absent.exists())
            self.assertEqual(tuple(root.iterdir()), ())

            first = root / "inventory.json"
            second = root / "profiles.toml"
            first.write_bytes(b"old-inventory\n")
            second.write_bytes(b"old-profiles\n")
            first_snapshot = real_read(
                first,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            second_snapshot = real_read(
                second,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            pair_outputs_revalidated = False

            def fail_after_pair_outputs(*args: object, **kwargs: object) -> None:
                if pair_outputs_revalidated:
                    raise OSError("final outer attribute drift")

            real_pair_revalidate = (
                self.generator._GovernancePairTransaction.revalidate
            )

            def mark_pair_revalidated(transaction: object) -> None:
                nonlocal pair_outputs_revalidated
                real_pair_revalidate(transaction)
                pair_outputs_revalidated = True

            def publish_pair(attribute_check: object) -> object:
                return self.generator._write_governance_pair(
                    first,
                    b"new-inventory\n",
                    first_snapshot,
                    second,
                    b"new-profiles\n",
                    second_snapshot,
                    lifetime_check=attribute_check,
                )

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                return_value=(Path("C:/git.exe"), b"git", (1,)),
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=fake_lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
                side_effect=fail_after_pair_outputs,
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ), mock.patch.object(
                self.generator._GovernancePairTransaction,
                "revalidate",
                side_effect=mark_pair_revalidated,
                autospec=True,
            ):
                with self.assertRaisesRegex(Exception, "outer attribute drift"):
                    self.generator._with_governance_attribute_lease(
                        root,
                        Path("C:/git.exe"),
                        publish_pair,
                    )
            self.assertEqual(first.read_bytes(), b"old-inventory\n")
            self.assertEqual(second.read_bytes(), b"old-profiles\n")
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {first.name, second.name},
            )

            source = root / "source.py"
            source.write_bytes(b"VALUE = 1\n")
            source_snapshot = real_read(
                source,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            first_snapshot = real_read(
                first,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            second_snapshot = real_read(
                second,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            second_revalidations = 0
            real_transaction_revalidate = (
                self.generator._GovernanceWriteTransaction.revalidate
            )

            def mutate_after_second_output(transaction: object) -> None:
                nonlocal second_revalidations
                real_transaction_revalidate(transaction)
                if transaction.path == second:
                    second_revalidations += 1
                    if second_revalidations == 2:
                        source.write_bytes(b"VALUE = 2\n")

            def publish_pair_with_source(attribute_check: object) -> object:
                def lifetime_check() -> None:
                    source_snapshot.revalidate()
                    attribute_check()

                return self.generator._write_governance_pair(
                    first,
                    b"new-inventory\n",
                    first_snapshot,
                    second,
                    b"new-profiles\n",
                    second_snapshot,
                    lifetime_check=lifetime_check,
                )

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                return_value=(Path("C:/git.exe"), b"git", (1,)),
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=fake_lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ), mock.patch.object(
                self.generator._GovernanceWriteTransaction,
                "revalidate",
                side_effect=mutate_after_second_output,
                autospec=True,
            ):
                with self.assertRaisesRegex(Exception, "(?:snapshot|file).*changed"):
                    self.generator._with_governance_attribute_lease(
                        root,
                        Path("C:/git.exe"),
                        publish_pair_with_source,
                    )
            self.assertEqual(first.read_bytes(), b"old-inventory\n")
            self.assertEqual(second.read_bytes(), b"old-profiles\n")
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {first.name, second.name, source.name},
            )

    def test_windows_publication_is_handle_relative_and_prebinds_recovery(
        self,
    ) -> None:
        if os.name != "nt":
            return
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-windows-relative-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            opened_recovery = False
            real_open = self.generator._windows_open_relative_governance_file

            def fail_recovery_open(directory_handle: int, name: str) -> int:
                nonlocal opened_recovery
                if name.endswith(".recovery"):
                    opened_recovery = True
                    raise OSError("recovery acquisition failed")
                return real_open(directory_handle, name)

            with mock.patch.object(
                self.generator,
                "_windows_open_relative_governance_file",
                side_effect=fail_recovery_open,
            ):
                with self.assertRaisesRegex(Exception, "recovery acquisition"):
                    self.generator.write_atomic_lf(target, b"generated\n")
            self.assertTrue(opened_recovery)
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual({path.name for path in root.iterdir()}, {target.name})

            parent_swap_denied = False
            original_publish = self.generator._publish_staged_governance
            moved = root.with_name(root.name + "-moved")

            def attempt_parent_swap(**kwargs: object) -> None:
                nonlocal parent_swap_denied
                try:
                    root.rename(moved)
                except OSError:
                    parent_swap_denied = True
                else:
                    moved.rename(root)
                original_publish(**kwargs)

            with mock.patch.object(
                self.generator,
                "_publish_staged_governance",
                side_effect=attempt_parent_swap,
            ), mock.patch.object(
                self.generator,
                "_windows_replace_governance_file",
                side_effect=AssertionError("absolute-path replacement used"),
                create=True,
            ):
                self.generator.write_atomic_lf(target, b"generated\n")
            self.assertTrue(parent_swap_denied)
            self.assertEqual(target.read_bytes(), b"generated\n")
            self.assertFalse(moved.exists())
            self.assertEqual({path.name for path in root.iterdir()}, {target.name})

    def test_git_launch_and_raw_object_reads_are_identity_bound(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-inventory-git-lease-"
        ) as temporary:
            root = Path(temporary)
            executable_parent = root / "bin"
            executable_parent.mkdir()
            executable = executable_parent / (
                "git.exe" if os.name == "nt" else "git"
            )
            os.link(Path(sys.executable), executable)
            _, _, identity = self.generator._strict_git_snapshot(executable)
            lease = self.generator._acquire_git_launch_lease(
                executable,
                identity,
            )
            replacement = root / "replacement"
            replacement.write_bytes(b"replacement")
            replaced = False
            try:
                try:
                    os.replace(replacement, executable)
                except PermissionError:
                    self.generator._revalidate_git_launch_lease(lease)
                else:
                    replaced = True
                    with self.assertRaisesRegex(Exception, "lease changed"):
                        self.generator._revalidate_git_launch_lease(lease)
            finally:
                lease.close()

            if replaced:
                executable.unlink()
                os.link(Path(sys.executable), executable)
            _, raw, identity = self.generator._strict_git_snapshot(executable)
            lease = self.generator._acquire_git_launch_lease(
                executable,
                identity,
                raw,
            )
            moved_parent = root / "moved-bin"
            try:
                try:
                    os.replace(executable_parent, moved_parent)
                except PermissionError:
                    self.generator._revalidate_git_launch_lease(lease)
                    if os.name == "nt":
                        self.assertTrue(lease.ancestor_handles)
                else:
                    with self.assertRaisesRegex(Exception, "ancestor|lease"):
                        self.generator._revalidate_git_launch_lease(lease)
                    os.replace(moved_parent, executable_parent)
            finally:
                lease.close()

        raw = b"substituted commit bytes"
        expected_oid = "a" * 40
        fake_lease = self.generator._GitLaunchLease(
            Path("git"),
            (),
            -1,
            None,
            (),
        )
        output = (
            f"{expected_oid} commit {len(raw)}\n".encode("ascii")
            + raw
            + b"\n"
        )
        with mock.patch.object(
            self.generator,
            "_revalidate_git_launch_lease",
        ), mock.patch.object(
            self.generator,
            "_run_bounded_process",
            return_value=(0, output, b""),
        ):
            with self.assertRaisesRegex(Exception, "object bytes"):
                self.generator._read_git_object_batch(
                    fake_lease,
                    Path.cwd(),
                    {},
                    (("commit", expected_oid, "commit"),),
                )

    def test_posix_git_snapshot_fails_closed_without_memfd(self) -> None:
        real_hasattr = hasattr

        def without_memfd(owner: object, name: str) -> bool:
            if owner is self.generator.os and name == "memfd_create":
                return False
            return real_hasattr(owner, name)

        with mock.patch("builtins.hasattr", side_effect=without_memfd), mock.patch.object(
            self.generator.tempfile,
            "mkstemp",
            side_effect=AssertionError("unsealed temporary snapshot used"),
        ), mock.patch.object(
            self.generator.subprocess,
            "Popen",
            side_effect=AssertionError("unsealed executable was launched"),
        ):
            with self.assertRaisesRegex(Exception, "sealed executable snapshots"):
                self.generator._posix_executable_snapshot(b"git", 0o700)

    def test_git_tool_requires_absolute_regular_nonlink_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-inventory-git-") as temporary:
            root = Path(temporary)
            regular = root / ("git.exe" if os.name == "nt" else "git")
            regular.write_bytes(b"not invoked")
            if os.name != "nt":
                regular.chmod(0o700)
            for value in (None, "git", str(root)):
                with self.subTest(value=value):
                    with self.assertRaisesRegex(Exception, "PONTIUS_GIT"):
                        self.generator.resolve_git_tool(value)

            link = root / "git-link"
            try:
                link.symlink_to(regular)
            except (OSError, NotImplementedError):
                link = None
            if link is not None:
                with self.assertRaisesRegex(Exception, "link|reparse"):
                    self.generator.resolve_git_tool(str(link))

            identity = self.generator.resolve_git_tool(str(regular))
            self.assertEqual(Path(_field(identity, "resolved_executable")), regular.resolve())

            hardlink = root / ("git-hardlink.exe" if os.name == "nt" else "git-hardlink")
            os.link(regular, hardlink)
            hardlink_identity = self.generator.resolve_git_tool(str(hardlink))
            self.assertEqual(
                Path(_field(hardlink_identity, "resolved_executable")),
                hardlink.resolve(),
            )

    def test_git_tool_rejects_a_mocked_windows_reparse_leaf_before_reading(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-inventory-git-") as temporary:
            executable = Path(temporary) / "git.exe"
            executable.write_bytes(b"not invoked")
            info = os.stat(executable, follow_symlinks=False)
            reparse = mock.Mock(spec=type(info))
            for field in dir(info):
                if field.startswith("st_"):
                    try:
                        setattr(reparse, field, getattr(info, field))
                    except AttributeError:
                        pass
            reparse.st_file_attributes = 0x400
            reparse.st_reparse_tag = 0xA000000C

            def path_stat(path: Path) -> object:
                return reparse if Path(path) == executable else os.lstat(path)

            with mock.patch.object(
                self.generator,
                "_git_path_stat",
                side_effect=path_stat,
            ):
                with self.assertRaisesRegex(Exception, "reparse"):
                    self.generator.resolve_git_tool(str(executable))

    def test_git_identity_drift_between_measurements_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-inventory-git-") as temporary:
            executable = Path(temporary) / ("git.exe" if os.name == "nt" else "git")
            executable.write_bytes(b"not invoked")
            if os.name != "nt":
                executable.chmod(0o700)
            first = os.stat(executable, follow_symlinks=False)
            changed = mock.Mock(spec=type(first))
            for field in dir(first):
                if field.startswith("st_"):
                    try:
                        setattr(changed, field, getattr(first, field))
                    except AttributeError:
                        pass
            changed.st_size = first.st_size + 1
            leaf_measurements = iter((first, changed))

            def path_stat(path: Path) -> object:
                if Path(path) == executable:
                    return next(leaf_measurements)
                return os.lstat(path)

            with mock.patch.object(
                self.generator,
                "_git_path_stat",
                side_effect=path_stat,
            ):
                with self.assertRaisesRegex(Exception, "identity changed"):
                    self.generator.resolve_git_tool(str(executable))

        bounded_environment = dict(os.environ)
        with self.assertRaisesRegex(Exception, "bounded process|timed out"):
            self.generator._run_bounded_process(
                Path(sys.executable),
                SNAPSHOT_ROOT,
                bounded_environment,
                (
                    "-B",
                    "-P",
                    "-c",
                    (
                        "import sys,time;"
                        "sys.stdout.write('partial header');"
                        "sys.stdout.flush();time.sleep(30)"
                    ),
                ),
                b"",
                stdout_limit=1024,
                stderr_limit=1024,
                timeout_seconds=0.1,
            )
        with self.assertRaisesRegex(Exception, "output limit"):
            self.generator._run_bounded_process(
                Path(sys.executable),
                SNAPSHOT_ROOT,
                bounded_environment,
                ("-B", "-P", "-c", "import os;os.write(1,b'x'*1048576)"),
                b"",
                stdout_limit=1024,
                stderr_limit=1024,
                timeout_seconds=5,
            )
        with self.assertRaisesRegex(Exception, "bounded process|timed out"):
            self.generator._run_bounded_process(
                Path(sys.executable),
                SNAPSHOT_ROOT,
                bounded_environment,
                ("-B", "-P", "-c", "import time;time.sleep(30)"),
                b"x" * 1024 * 1024,
                stdout_limit=1024,
                stderr_limit=1024,
                timeout_seconds=0.1,
            )

    def test_baseline_discovery_reads_raw_blobs_despite_export_attributes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-inventory-objects-") as temporary:
            repository = Path(temporary)
            git_directory = repository / ".git"
            (git_directory / "objects").mkdir(parents=True)
            (git_directory / "refs" / "heads").mkdir(parents=True)
            visible = b'value = "$Format:%H$"\n'
            hidden = b"hidden = True\n"
            attributes = (
                b"tests/test_visible.py export-subst\n"
                b"tests/test_hidden.py export-ignore\n"
            )
            visible_oid = _store_git_object(git_directory, "blob", visible)
            hidden_oid = _store_git_object(git_directory, "blob", hidden)
            attributes_oid = _store_git_object(git_directory, "blob", attributes)
            tests_tree_oid = _store_git_object(
                git_directory,
                "tree",
                _git_tree(
                    [
                        ("100644", "test_hidden.py", hidden_oid),
                        ("100644", "test_visible.py", visible_oid),
                    ]
                ),
            )
            root_tree_oid = _store_git_object(
                git_directory,
                "tree",
                _git_tree(
                    [
                        ("100644", ".gitattributes", attributes_oid),
                        ("40000", "tests", tests_tree_oid),
                    ]
                ),
            )
            commit_raw = (
                f"tree {root_tree_oid}\n"
                "author Test <test@example.invalid> 0 +0000\n"
                "committer Test <test@example.invalid> 0 +0000\n"
                "\nraw blob fixture\n"
            ).encode("ascii")
            commit = _store_git_object(git_directory, "commit", commit_raw)
            (git_directory / "HEAD").write_text(
                "ref: refs/heads/main\n", encoding="ascii", newline="\n"
            )
            (git_directory / "refs" / "heads" / "main").write_text(
                commit + "\n", encoding="ascii", newline="\n"
            )

            sources = self.generator._git_blob_sources(
                repository,
                Path(os.environ["PONTIUS_GIT"]),
                commit=commit,
                root_tree_oid=root_tree_oid,
            )
        self.assertEqual(
            sources,
            {
                "tests/test_hidden.py": hidden,
                "tests/test_visible.py": visible,
            },
        )
        self.assertIn(b"$Format:%H$", sources["tests/test_visible.py"])


class CheckedInInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = _load_generator()
        cls.raw = INVENTORY_PATH.read_bytes()
        cls.document = json.loads(cls.raw)
        cls.entries = tuple(cls.document["entries"])

    def test_inventory_is_canonical_binary_lf_json_with_exact_root_schema(self) -> None:
        self.assertFalse(self.raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", self.raw)
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertEqual(self.raw.count(b"\n"), 1)
        self.assertEqual(
            self.raw,
            self.generator.canonical_json_bytes(self.document) + b"\n",
        )
        self.assertEqual(
            set(self.document),
            {
                "schema_version",
                "baseline_commit",
                "baseline_discovery",
                "discovery",
                "entries",
            },
        )
        self.assertEqual(self.document["schema_version"], "pontius-test-inventory-v1")
        self.assertEqual(self.document["baseline_commit"], BASELINE_COMMIT)

    def test_default_cli_mode_is_a_read_only_successful_check(self) -> None:
        before_inventory = INVENTORY_PATH.read_bytes()
        before_profiles = PROFILES_PATH.read_bytes()
        self.assertEqual(self.generator.main([]), 0)
        self.assertEqual(INVENTORY_PATH.read_bytes(), before_inventory)
        self.assertEqual(PROFILES_PATH.read_bytes(), before_profiles)

    def test_cli_rejects_relative_review_output_and_incomplete_write_tokens(self) -> None:
        before_inventory = INVENTORY_PATH.read_bytes()
        before_profiles = PROFILES_PATH.read_bytes()
        relative_output = SNAPSHOT_ROOT / "not-absolute-review.json"
        self.assertFalse(relative_output.exists())
        self.assertEqual(
            self.generator.main(
                ["--emit-design-capability-review", relative_output.name]
            ),
            2,
        )
        self.assertFalse(relative_output.exists())
        self.assertEqual(
            self.generator.main(
                [
                    "--write-design-capabilities",
                    "--approved-spec-capabilities-sha256",
                    "1" * 64,
                ]
            ),
            2,
        )
        self.assertEqual(INVENTORY_PATH.read_bytes(), before_inventory)
        self.assertEqual(PROFILES_PATH.read_bytes(), before_profiles)

    def test_baseline_counts_digests_and_materialized_partition_are_exact(self) -> None:
        baseline = self.document["baseline_discovery"]
        self.assertEqual(baseline, BASELINE_LOCK)
        baseline_entries = [row for row in self.entries if "baseline_assignment" in row]
        introduced = [row for row in self.entries if row.get("introduced_after_baseline") is True]
        self.assertEqual(len(baseline_entries), 2367)
        self.assertEqual(
            _ids_digest([row["stable_id"] for row in baseline_entries]),
            BASELINE_LOCK["stable_ids_sha256"],
        )
        for row in baseline_entries:
            self.assertEqual(row["baseline_assignment"], row["assignment"])
            self.assertNotIn("introduced_after_baseline", row)
        for row in introduced:
            self.assertNotIn("baseline_assignment", row)

        by_profile: dict[str, list[str]] = {}
        for row in baseline_entries:
            assignment = _assignment(row)
            by_profile.setdefault(str(assignment["profile_name"]), []).append(row["stable_id"])
        expected = {
            "historical": (
                BASELINE_LOCK["historical_id_count"],
                BASELINE_LOCK["historical_ids_sha256"],
            ),
            "gpu": (BASELINE_LOCK["gpu_id_count"], BASELINE_LOCK["gpu_ids_sha256"]),
            "core": (BASELINE_LOCK["core_id_count"], BASELINE_LOCK["core_ids_sha256"]),
            "current": (
                BASELINE_LOCK["current_id_count"],
                BASELINE_LOCK["current_ids_sha256"],
            ),
        }
        self.assertEqual(set(by_profile), set(expected))
        for profile_name, (count, digest) in expected.items():
            with self.subTest(profile_name=profile_name):
                self.assertEqual(len(by_profile[profile_name]), count)
                self.assertEqual(_ids_digest(by_profile[profile_name]), digest)

    def test_working_discovery_binds_every_entry_and_introduced_id(self) -> None:
        discovery = self.document["discovery"]
        self.assertEqual(
            set(discovery),
            {
                "test_file_count",
                "stable_id_count",
                "stable_ids_sha256",
                "introduced_id_count",
                "introduced_ids_sha256",
            },
        )
        stable_ids = [row["stable_id"] for row in self.entries]
        introduced_ids = [
            row["stable_id"]
            for row in self.entries
            if row.get("introduced_after_baseline") is True
        ]
        self.assertEqual(discovery["stable_id_count"], len(stable_ids))
        self.assertEqual(discovery["stable_ids_sha256"], _ids_digest(stable_ids))
        self.assertEqual(discovery["introduced_id_count"], len(introduced_ids))
        self.assertEqual(
            discovery["introduced_ids_sha256"], _ids_digest(introduced_ids)
        )

        sources = self.generator._working_sources(SNAPSHOT_ROOT)
        parsed_discovery = self.generator.discover_test_sources(sources)
        self.assertEqual(set(parsed_discovery.stable_ids), set(stable_ids))
        profile_document = tomllib.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        profile_by_id = {
            str(row["stable_id"]): str(_assignment(row)["profile_name"])
            for row in self.entries
        }
        design_profiles = {"core", "current", "gpu"}
        expected_universe: set[tuple[str, str]] = {
            ("stable_id", stable_id)
            for stable_id, profile_name in profile_by_id.items()
            if profile_name in design_profiles
        }
        for fixture in parsed_discovery.lifecycle_fixtures:
            member_profiles = {
                profile_by_id[member_id] for member_id in fixture.member_ids
            }
            if member_profiles <= design_profiles:
                expected_universe.add(("fixture", fixture.fixture_id))
            else:
                self.assertEqual(member_profiles, {"historical"})
        historical_probe_ids: set[str] = set()
        for payload in profile_document["payload"]:
            probe_ids = {str(probe_id) for probe_id in payload["probe_ids"]}
            if payload["profile_name"] in design_profiles:
                expected_universe.update(("probe", probe_id) for probe_id in probe_ids)
            else:
                historical_probe_ids.update(probe_ids)

        review = self.generator.derive_design_review(
            baseline_commit=BASELINE_COMMIT,
            baseline_root_tree_oid=BASELINE_ROOT_TREE,
            inventory_document=self.document,
            inventory_document_bytes=self.raw,
            sources=sources,
            item_universe=tuple(sorted(expected_universe)),
        )
        self.assertEqual(len(review["receipt"]["expanded_rows"]), 139)
        self.assertEqual(
            review["spec_capabilities_sha256"],
            "17f4532276989bd360cabafceeb3a3b4353c0764a4a61037639c933fdeb94194",
        )
        self.assertEqual(
            review["analysis_census"],
            {
                "subprocess_direct_site_count": 42,
                "subprocess_helper_site_count": 4,
                "cross_file_helper_edge_count": 27,
                "cupy_call_node_count": 28,
                "string_sink_decoy_count": 87,
                "string_sink_decoy_sha256": (
                    "e9f760e02ed9dcdc17954538fc0015ef0024ec3edd299513f6fd28e011f813b6"
                ),
                "string_sink_decoy_partitions": {
                    "design_production": 17,
                    "historical_production": 6,
                    "prior_stabilization_synthetic": 26,
                    "task2_synthetic": 38,
                },
                "analyzed_sites_sha256": (
                    "2d49993a8e19d30707681943505eccad4c2fa8cf270e27d7aaa2e40ccb81db6c"
                ),
            },
        )
        receipt = review["receipt"]
        expected_kind = {item_id: item_kind for item_kind, item_id in expected_universe}
        expanded_items = {str(row["item_id"]) for row in receipt["expanded_rows"]}
        deny_all = {
            (str(row["item_kind"]), str(row["item_id"]))
            for row in receipt["deny_all"]
        }
        self.assertLessEqual(expanded_items, set(expected_kind))
        self.assertEqual(
            {(expected_kind[item_id], item_id) for item_id in expanded_items}
            | deny_all,
            expected_universe,
        )
        self.assertFalse(
            {(expected_kind[item_id], item_id) for item_id in expanded_items}
            & deny_all
        )
        self.assertEqual(
            [
                (
                    row["approval_scope"],
                    row["item_id"],
                    row["capability_kind"],
                    row["capability_id"],
                )
                for row in receipt["expanded_rows"]
            ],
            sorted(
                (
                    row["approval_scope"],
                    row["item_id"],
                    row["capability_kind"],
                    row["capability_id"],
                )
                for row in receipt["expanded_rows"]
            ),
        )
        historical_ids = {
            stable_id
            for stable_id, profile_name in profile_by_id.items()
            if profile_name == "historical"
        }
        reviewed_item_ids = expanded_items | {item_id for _, item_id in deny_all}
        self.assertFalse(historical_ids & reviewed_item_ids)
        self.assertFalse(historical_probe_ids & reviewed_item_ids)
        canonical_loop_id = (
            "tests/test_canonical_affine_resident_automaton_cache.py::"
            "CanonicalAffineResidentCacheTests::"
            "test_five_way_scale_family_shares_one_device_basis"
        )
        canonical_asnumpy = [
            row
            for row in receipt["expanded_rows"]
            if row["item_id"] == canonical_loop_id
            and row.get("qualified_name") == "cupy.asnumpy"
        ]
        self.assertEqual(len(canonical_asnumpy), 1)
        self.assertEqual(canonical_asnumpy[0]["maximum_calls"], 6)
        dynamic_nested_id = (
            "tests/test_affine_resident_leaf_adjoint_cfr.py::"
            "AffineResidentLeafAdjointCFRTests::"
            "test_affine_cache_reconstructs_every_raw_half_vector"
        )
        self.assertTrue(
            any(
                row["item_id"] == dynamic_nested_id
                and "dynamic repetition" in row["reason"]
                for row in review["unresolved_dynamic_blockers"]
            )
        )
        source_seal_id = (
            "tests/test_legal_river_quotient_cuda_consumer.py::"
            "LegalRiverQuotientCudaConsumerSourceTests::"
            "test_import_is_device_free_and_preregistered_contract_rebinds"
        )
        self.assertNotIn(source_seal_id, expanded_items)
        self.assertIn(("stable_id", source_seal_id), deny_all)
        self.assertEqual(
            [
                row["reason"]
                for row in review["unresolved_dynamic_blockers"]
                if row["item_id"] == source_seal_id
            ],
            ["unsupported subprocess keyword: capture_output"],
        )
        blockers = review["unresolved_dynamic_blockers"]
        self.assertEqual(len(blockers), 139)
        self.assertEqual(
            Counter(row["reason"] for row in blockers),
            Counter(
                {
                    "unsupported subprocess keyword: capture_output": 44,
                    "dynamic helper arguments prevent exact sink derivation": 25,
                    "CuPy action or view is outside the approved call scope": 11,
                    "dynamic repetition prevents a finite call bound": 5,
                    "dynamic repetition prevents a finite helper call bound": 8,
                    "mixed protected receiver is dynamically unresolved": 31,
                    "callable alias is dynamically unresolved": 9,
                    "unsupported subprocess keyword: stdin": 5,
                    "registered probe implementation is absent": 1,
                }
            ),
        )
        self.assertEqual(
            blockers,
            sorted(
                blockers,
                key=lambda row: (
                    row["item_id"],
                    row["relative_path"],
                    row["line"],
                ),
            ),
        )
        self.assertLessEqual(
            {str(row["item_id"]) for row in blockers},
            {item_id for _, item_id in expected_universe},
        )

    def test_historical_payload_subgroups_have_independently_locked_ids(self) -> None:
        by_payload: dict[str, list[str]] = {}
        for row in self.entries:
            assignment = _assignment(row)
            if assignment["profile_name"] == "historical":
                by_payload.setdefault(str(assignment["payload_id"]), []).append(
                    row["stable_id"]
                )
        self.assertEqual(set(by_payload), set(HISTORICAL_PAYLOAD_LOCKS))
        for payload_id, (count, digest) in HISTORICAL_PAYLOAD_LOCKS.items():
            with self.subTest(payload_id=payload_id):
                self.assertEqual(len(by_payload[payload_id]), count)
                self.assertEqual(_ids_digest(by_payload[payload_id]), digest)

    def test_added_tests_are_only_reviewed_stabilization_current_entries(self) -> None:
        profiles = tomllib.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            tuple(profiles["stabilization_test_files"]), STABILIZATION_TEST_FILES
        )
        allowed = set(STABILIZATION_TEST_FILES)
        introduced = [row for row in self.entries if row.get("introduced_after_baseline") is True]
        self.assertTrue(introduced)
        for row in introduced:
            with self.subTest(stable_id=row["stable_id"]):
                self.assertIn(row["relative_path"], allowed)
                self.assertEqual(_assignment(row)["profile_name"], "current")

    def test_entry_shapes_selectors_and_expectation_variants_are_exact(self) -> None:
        stable_ids = []
        for row in self.entries:
            stable_ids.append(row["stable_id"])
            expected_keys = {
                "stable_id",
                "relative_path",
                "case_name",
                "method_name",
                "assignment",
            }
            expected_keys.add(
                "baseline_assignment"
                if "baseline_assignment" in row
                else "introduced_after_baseline"
            )
            self.assertEqual(set(row), expected_keys)
            self.assertEqual(
                row["stable_id"],
                f'{row["relative_path"]}::{row["case_name"]}::{row["method_name"]}',
            )
            assignment = _assignment(row)
            self.assertEqual(
                set(assignment), {"profile_name", "payload_id", "expectation"}
            )
            expectation = assignment["expectation"]
            kind = expectation["kind"]
            expected_expectation_keys = {
                "pass": {"kind"},
                "case_defined": {"kind"},
                "platform_conditioned": {
                    "kind",
                    "applicable_platforms",
                    "skip_safe_reason_code",
                },
                "declared_unconditional_skip": {"kind", "skip_safe_reason_code"},
            }
            self.assertIn(kind, expected_expectation_keys)
            self.assertEqual(set(expectation), expected_expectation_keys[kind])
        self.assertEqual(stable_ids, sorted(stable_ids))
        self.assertEqual(len(stable_ids), len(set(stable_ids)))

    def test_exact_declared_unconditional_skips_match_outer_literal_and_digest(self) -> None:
        entries = _entries_by_id(self.document)
        actual_declared = {
            stable_id
            for stable_id, row in entries.items()
            if _assignment(row)["expectation"]["kind"]
            == "declared_unconditional_skip"
        }
        self.assertEqual(actual_declared, set(DECLARED_UNCONDITIONAL_SKIPS))
        for stable_id, (literal, reason_code, literal_digest) in (
            DECLARED_UNCONDITIONAL_SKIPS.items()
        ):
            with self.subTest(stable_id=stable_id):
                row = entries[stable_id]
                expectation = _assignment(row)["expectation"]
                self.assertEqual(
                    expectation,
                    {
                        "kind": "declared_unconditional_skip",
                        "skip_safe_reason_code": reason_code,
                    },
                )
                self.assertEqual(_assignment(row)["profile_name"], "gpu")
                self.assertEqual(sha256(literal.encode("utf-8")).hexdigest(), literal_digest)
                relative_path, case_name, method_name = stable_id.split("::")
                method = _method_node(relative_path, case_name, method_name)
                outer = method.decorator_list[0]
                self.assertIsInstance(outer, ast.Call)
                self.assertIsInstance(outer.func, ast.Attribute)
                self.assertEqual(ast.unparse(outer.func), "unittest.skip")
                self.assertEqual(len(outer.args), 1)
                self.assertIsInstance(outer.args[0], ast.Constant)
                self.assertEqual(outer.args[0].value, literal)

    def test_gpu_and_current_exception_and_h32_fixture_split_are_locked(self) -> None:
        shared = [
            row
            for row in self.entries
            if row["case_name"] == "SharedDirectDeviceSourceSealTests"
        ]
        self.assertEqual(len(shared), 18)
        self.assertEqual({_assignment(row)["profile_name"] for row in shared}, {"current"})

        h32 = [
            row
            for row in self.entries
            if row["case_name"] == "H32PreBetInitialRowCacheSeedTests"
        ]
        self.assertEqual(len(h32), 9)
        self.assertEqual(
            sum(_assignment(row)["profile_name"] == "gpu" for row in h32), 1
        )
        self.assertEqual(
            sum(_assignment(row)["profile_name"] == "current" for row in h32), 8
        )
        tree = ast.parse(
            (SNAPSHOT_ROOT / "tests/test_h32_pre_bet_initial_row_cache_seed.py").read_bytes()
        )
        case = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "H32PreBetInitialRowCacheSeedTests"
        )
        methods = {
            node.name for node in case.body if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("setUp", methods)
        self.assertNotIn("setUpClass", methods)


class CheckedInProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.errors, cls.model, cls.configuration = _load_orchestration()
        cls.raw = PROFILES_PATH.read_bytes()
        cls.document = tomllib.loads(cls.raw.decode("utf-8"))
        cls.inventory = json.loads(INVENTORY_PATH.read_bytes())

    def test_profiles_are_canonical_lf_and_both_capability_scopes_are_absent(self) -> None:
        self.assertFalse(self.raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", self.raw)
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertEqual(self.document["schema_version"], "pontius-test-profiles-v1")
        self.assertEqual(self.document["baseline_commit"], BASELINE_COMMIT)
        self.assertEqual(
            {
                key: self.document[key]
                for key in (
                    "sealed_current_files_manifest",
                    "sealed_current_absences_manifest",
                    "historical_blobs_manifest",
                    "retained_v7_manifest",
                    "inventory_path",
                )
            },
            {
                "sealed_current_files_manifest":
                    "docs/architecture/sealed-current-files.toml",
                "sealed_current_absences_manifest":
                    "docs/architecture/sealed-current-absences.toml",
                "historical_blobs_manifest": "docs/architecture/historical-blobs.toml",
                "retained_v7_manifest": "docs/architecture/retained-v7.toml",
                "inventory_path": "tests/test-inventory.json",
            },
        )
        self.assertEqual(self.document["spec_capabilities_sha256"], ZERO_SHA256)
        self.assertEqual(self.document["capability_bindings_sha256"], ZERO_SHA256)
        self.assertNotIn("subprocess_capability", self.document)
        self.assertNotIn("call_capability", self.document)
        self.assertNotIn("capability_binding", self.document)
        self.assertEqual(
            set(self.document),
            {
                "schema_version",
                "baseline_commit",
                "sealed_current_files_manifest",
                "sealed_current_absences_manifest",
                "historical_blobs_manifest",
                "retained_v7_manifest",
                "inventory_path",
                "spec_capabilities_sha256",
                "capability_bindings_sha256",
                "interpreter_slot",
                "profile",
                "payload",
                "historical_case",
                "overlay",
                "stabilization_test_files",
            },
        )

    def test_exact_interpreter_slots_profiles_and_budgets_are_declared(self) -> None:
        slots = {row["name"]: row for row in self.document["interpreter_slot"]}
        self.assertEqual(set(slots), {"development", "cpython311"})
        self.assertEqual(
            slots["development"],
            {
                "name": "development",
                "resolution": "repository_relative",
                "windows_relative_path": ".venv/Scripts/python.exe",
                "posix_relative_path": ".venv/bin/python",
                "implementation": "cpython",
                "minimum_version": [3, 11],
                "required_for_full": True,
            },
        )
        self.assertEqual(
            slots["cpython311"],
            {
                "name": "cpython311",
                "resolution": "environment_absolute",
                "environment_variable": "PONTIUS_CPYTHON311",
                "implementation": "cpython",
                "exact_version": [3, 11],
                "required_for_full": True,
            },
        )
        profiles = {row["name"]: row for row in self.document["profile"]}
        self.assertEqual(set(profiles), set(PROFILE_BUDGETS))
        for name, expected in PROFILE_BUDGETS.items():
            with self.subTest(profile=name):
                budgets = profiles[name]["budgets"]
                self.assertEqual(
                    (
                        budgets["setup_seconds"],
                        budgets["child_seconds"],
                        budgets["termination_seconds"],
                        budgets["cleanup_seconds"],
                        budgets["total_seconds"],
                    ),
                    expected,
                )
        for name in ("core", "current"):
            self.assertEqual(profiles[name]["interpreter_slots"], ["cpython311", "development"])
            self.assertEqual(profiles[name]["default_interpreter_slot"], "development")
        for name in ("historical", "gpu"):
            self.assertEqual(profiles[name]["interpreter_slots"], ["development"])
            self.assertEqual(profiles[name]["default_interpreter_slot"], "development")
        self.assertEqual(
            profiles["full"]["interpreter_slots"], ["cpython311", "development"]
        )
        self.assertIsNone(profiles["full"].get("default_interpreter_slot"))
        self.assertEqual(
            profiles["full"]["subprofiles"],
            ["core", "current", "gpu", "historical"],
        )
        self.assertTrue(profiles["gpu"]["gpu_optional"] is False)
        self.assertTrue(profiles["full"]["gpu_optional"] is True)

    def test_twelve_historical_cases_bind_exact_commits_trees_and_v7_overlays(self) -> None:
        cases = {row["case_id"]: row for row in self.document["historical_case"]}
        self.assertEqual(
            set(cases), {f"case:{phase}" for phase in HISTORICAL_SNAPSHOTS}
        )
        for phase, (commit, root_tree_oid) in HISTORICAL_SNAPSHOTS.items():
            with self.subTest(phase=phase):
                case = cases[f"case:{phase}"]
                self.assertEqual(case["phase"], phase)
                self.assertEqual(case["commit"], commit)
                self.assertEqual(case["root_tree_oid"], root_tree_oid)
                self.assertEqual(
                    case["overlay_ids"],
                    sorted(V7_RETAINED_OVERLAYS)
                    if phase == "v7_retained_probe"
                    else [],
                )
        self.assertEqual(
            cases["case:v4_authorization_rejection"]["payload_ids"],
            [
                "historical:v4-authorization-negative",
                "historical:v4-positive",
            ],
        )
        overlays = {row["overlay_id"]: row for row in self.document["overlay"]}
        self.assertEqual(set(overlays), set(V7_RETAINED_OVERLAYS))
        for overlay_id, (relative_path, byte_length, raw_sha256) in (
            V7_RETAINED_OVERLAYS.items()
        ):
            with self.subTest(overlay=overlay_id):
                self.assertEqual(
                    overlays[overlay_id],
                    {
                        "overlay_id": overlay_id,
                        "source_commit": BASELINE_COMMIT,
                        "source_path": relative_path,
                        "destination_path": relative_path,
                        "byte_length": byte_length,
                        "raw_sha256": raw_sha256,
                    },
                )

    def test_historical_negative_vectors_and_item_outcomes_are_fail_closed(self) -> None:
        cases = {row["case_id"]: row for row in self.document["historical_case"]}
        v4 = cases["case:v4_authorization_rejection"]
        self.assertEqual(
            v4["expected_vector"],
            {
                "kind": "negative",
                "passed": 38,
                "assertion_failed": 0,
                "setup_failed": 0,
                "body_entered": 39,
                "owner_calls": 0,
                "scientific_calls": 0,
                "phase": "body",
                "exception_type": "ValueError",
                "safe_reason_code": "deferred-import header domain differs",
            },
        )
        v4_negative = [
            row
            for row in v4["item_expectation"]
            if row["outcome"] == "expected_negative"
        ]
        self.assertEqual(len(v4_negative), 1)
        self.assertEqual(v4_negative[0]["exception_type"], "ValueError")
        self.assertEqual(
            v4_negative[0]["safe_reason_code"],
            "deferred-import header domain differs",
        )
        self.assertEqual(v4_negative[0]["phase"], "body")
        self.assertIs(v4_negative[0]["body_entered"], True)
        self.assertEqual(v4_negative[0]["capability_counters"], {})

        v6 = cases["case:v6_authorization_rejection"]
        vector = v6["expected_vector"]
        self.assertEqual(vector["kind"], "negative")
        self.assertEqual(vector["passed"], 0)
        self.assertEqual(vector["assertion_failed"], 0)
        self.assertEqual(vector["setup_failed"], 17)
        self.assertEqual(vector["body_entered"], 0)
        self.assertEqual(vector["owner_calls"], 0)
        self.assertEqual(vector["scientific_calls"], 0)
        self.assertEqual(vector["phase"], "setup")
        self.assertEqual(vector["exception_type"], "AssertionError")
        self.assertEqual(vector["safe_reason_code"], "v6_authorization_path_present")
        self.assertEqual(len(v6["item_expectation"]), 17)
        self.assertEqual(
            {row["outcome"] for row in v6["item_expectation"]},
            {"expected_negative"},
        )
        self.assertEqual(
            {row["safe_reason_code"] for row in v6["item_expectation"]},
            {"v6_authorization_path_present"},
        )
        self.assertEqual(
            {row["phase"] for row in v6["item_expectation"]}, {"setup"}
        )
        self.assertEqual(
            {row["exception_type"] for row in v6["item_expectation"]},
            {"AssertionError"},
        )
        self.assertEqual(
            {row["body_entered"] for row in v6["item_expectation"]}, {False}
        )
        self.assertEqual(
            {tuple(row["capability_counters"].items()) for row in v6["item_expectation"]},
            {()},
        )

        payloads = {row["payload_id"]: row for row in self.document["payload"]}
        self.assertEqual(
            payloads["historical:v4-authorization-negative"]["environment_additions"],
            {"PONTIUS_ADR0467_AUTH_READER_CHILD": "1"},
        )
        for payload_id, payload in payloads.items():
            if payload_id != "historical:v4-authorization-negative":
                self.assertNotIn(
                    "PONTIUS_ADR0467_AUTH_READER_CHILD",
                    payload["environment_additions"],
                )

    def test_payload_granularity_and_lifecycle_members_never_cross_payloads(self) -> None:
        entry_assignments = {
            row["stable_id"]: _assignment(row) for row in self.inventory["entries"]
        }
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in self.inventory["entries"]:
            grouped.setdefault(str(_assignment(row)["payload_id"]), []).append(row)
        payloads = {row["payload_id"]: row for row in self.document["payload"]}
        self.assertTrue(set(grouped).issubset(payloads))
        for payload_id in set(payloads) - set(grouped):
            self.assertTrue(payloads[payload_id]["probe_ids"])
        for payload_id, entries in grouped.items():
            with self.subTest(payload_id=payload_id):
                profile = _assignment(entries[0])["profile_name"]
                if profile in {"core", "current"}:
                    self.assertEqual(len({row["relative_path"] for row in entries}), 1)
                    self.assertEqual(
                        payloads[payload_id]["allowed_interpreter_slots"],
                        ["cpython311", "development"],
                    )
                elif profile == "gpu":
                    self.assertEqual(
                        len({(row["relative_path"], row["case_name"]) for row in entries}),
                        1,
                    )
                    self.assertEqual(
                        payloads[payload_id]["allowed_interpreter_slots"],
                        ["development"],
                    )
                elif profile == "historical":
                    self.assertEqual(
                        payloads[payload_id]["allowed_interpreter_slots"],
                        ["development"],
                    )
                for fixture in payloads[payload_id].get("lifecycle_fixture", []):
                    members = fixture["member_ids"]
                    self.assertTrue(members)
                    self.assertEqual(
                        {entry_assignments[member]["payload_id"] for member in members},
                        {payload_id},
                    )

    def test_every_named_set_like_array_is_canonically_sorted_and_unique(self) -> None:
        arrays: list[tuple[str, list[str]]] = [
            ("stabilization_test_files", self.document["stabilization_test_files"])
        ]
        for profile in self.document["profile"]:
            for field in (
                "interpreter_slots",
                "payload_ids",
                "historical_case_ids",
                "subprofiles",
            ):
                arrays.append((f'profile:{profile["name"]}.{field}', profile[field]))
        for payload in self.document["payload"]:
            for field in (
                "allowed_interpreter_slots",
                "probe_ids",
                "environment_removals",
                "allowed_write_roots",
                "forbidden_relative_paths",
            ):
                arrays.append((f'payload:{payload["payload_id"]}.{field}', payload[field]))
            for fixture in payload.get("lifecycle_fixture", []):
                for field in (
                    "member_ids",
                    "allowed_write_roots",
                    "forbidden_relative_paths",
                ):
                    arrays.append((f'{fixture["fixture_id"]}.{field}', fixture[field]))
        for case in self.document.get("historical_case", []):
            arrays.append((f'{case["case_id"]}.payload_ids', case["payload_ids"]))
            arrays.append((f'{case["case_id"]}.overlay_ids', case["overlay_ids"]))
        for label, values in arrays:
            with self.subTest(array=label):
                self.assertEqual(values, sorted(set(values)))

    def test_configuration_loads_zero_scope_contract_but_every_profile_selection_refuses(
        self,
    ) -> None:
        bundle = self.configuration.load_configuration(
            PROFILES_PATH,
            INVENTORY_PATH,
            repository_root=SNAPSHOT_ROOT,
        )
        self.assertEqual(bundle.spec_capabilities_sha256, ZERO_SHA256)
        self.assertEqual(bundle.capability_bindings_sha256, ZERO_SHA256)
        self.assertEqual(len(bundle.inventory_entries), len(self.inventory["entries"]))
        for name in ("core", "current", "gpu", "historical", "full"):
            with self.subTest(profile=name):
                with self.assertRaises(self.errors.EvidenceConfigurationError) as raised:
                    self.configuration.select_profile(bundle, name)
                self.assertEqual(raised.exception.code, "capability_approval_required")
                self.assertEqual(
                    raised.exception.message,
                    "applicable capabilities are not approved",
                )

    def test_gitattributes_pins_all_three_governance_files_to_lf(self) -> None:
        generator = _load_generator()
        attributes_path = SNAPSHOT_ROOT / ".gitattributes"
        lines = {
            line.strip()
            for line in attributes_path.read_text(encoding="utf-8").splitlines()
        }
        self.assertTrue(
            {
                "/docs/architecture/dependency-baseline.toml text eol=lf",
                "/tests/test-inventory.json text eol=lf",
                "/tests/test-profiles.toml text eol=lf",
            }.issubset(lines)
        )
        with tempfile.TemporaryDirectory(
            prefix="pontius-attribute-environment-"
        ) as temporary:
            repository = Path(temporary) / "repository"
            repository.mkdir()
            attributes = b"".join(
                f"/{path} text eol=lf\n".encode("ascii")
                for path in generator._GOVERNANCE_ATTRIBUTE_PATHS
            )
            (repository / ".gitattributes").write_bytes(attributes)
            for relative in generator._GOVERNANCE_ATTRIBUTE_PATHS:
                target = repository / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"governance\n")
            git = Path(os.environ["PONTIUS_GIT"])
            environment = generator._git_environment(git, Path(temporary))
            _, raw, identity = generator._strict_git_snapshot(git)
            lease = generator._acquire_git_launch_lease(git, identity, raw)
            try:
                generator._run_git_metadata(
                    lease,
                    repository,
                    environment,
                    ("init", "--quiet"),
                )
                generator._verify_governance_attributes(
                    lease,
                    repository,
                    environment,
                )
                (repository / ".gitattributes").write_bytes(
                    attributes
                    + b"/tests/test-profiles.toml -text -eol\n"
                )
                with self.assertRaisesRegex(Exception, "effective governance"):
                    generator._verify_governance_attributes(
                        lease,
                        repository,
                        environment,
                    )
            finally:
                lease.close()


if __name__ == "__main__":
    unittest.main()
