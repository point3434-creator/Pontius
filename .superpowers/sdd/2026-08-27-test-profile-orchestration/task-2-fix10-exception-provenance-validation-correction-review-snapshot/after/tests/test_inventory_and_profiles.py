from __future__ import annotations

import ast
from collections import Counter
from contextlib import ExitStack
import dis
from hashlib import sha1, sha256
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import textwrap
import threading
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

        exact_alias_conditions = (
            (
                "import os\nimport unittest\nimport unittest as u\n"
                "class AliasTests(unittest.TestCase):\n"
                "    @u.skipIf(os.name == 'nt', 'alias')\n"
                "    def test_value(self): pass\n",
                "posix",
            ),
            (
                "import os\nimport unittest\n"
                "from unittest import skipUnless\n"
                "class AliasTests(unittest.TestCase):\n"
                "    @skipUnless(os.name == 'nt', 'alias')\n"
                "    def test_value(self): pass\n",
                "windows",
            ),
            *(
                (source, "posix")
                for source in (
                    "import os\nimport unittest\n"
                    "conditional = unittest.skipIf\n"
                    "class AliasTests(unittest.TestCase):\n"
                    "    @conditional(os.name == 'nt', 'alias')\n"
                    "    def test_value(self): pass\n",
                    "import os\nimport unittest\n"
                    "class AliasTests(unittest.TestCase):\n"
                    "    @getattr(unittest, 'skipIf')(os.name == 'nt', 'alias')\n"
                    "    def test_value(self): pass\n",
                    "import os\nimport unittest\nu = unittest\n"
                    "class AliasTests(unittest.TestCase):\n"
                    "    @u.skipIf(os.name == 'nt', 'alias')\n"
                    "    def test_value(self): pass\n",
                    "import os\nimport unittest\n"
                    "class AliasTests(unittest.TestCase):\n"
                    "    conditional = unittest.skipIf\n"
                    "    @conditional(os.name == 'nt', 'alias')\n"
                    "    def test_value(self): pass\n",
                    "import os\nimport unittest\n"
                    "conditional = getattr(unittest, 'skipIf')\n"
                    "class AliasTests(unittest.TestCase):\n"
                    "    @conditional(os.name == 'nt', 'alias')\n"
                    "    def test_value(self): pass\n",
                    "import os\nimport unittest\n"
                    "if choose_alias():\n"
                    "    conditional = unittest.skipIf\n"
                    "else:\n"
                    "    conditional = unittest.skipIf\n"
                    "class AliasTests(unittest.TestCase):\n"
                    "    @conditional(os.name == 'nt', 'alias')\n"
                    "    def test_value(self): pass\n",
                    "import os\nimport unittest\n"
                    "conditional = unittest.skipUnless\n"
                    "conditional = unittest.skipIf\n"
                    "class AliasTests(unittest.TestCase):\n"
                    "    @conditional(os.name == 'nt', 'alias')\n"
                    "    def test_value(self): pass\n",
                )
            ),
        )
        for source, platform in exact_alias_conditions:
            with self.subTest(exact_alias=source):
                exact = self.generator.build_inventory(
                    {"tests/test_alias.py": source.encode("utf-8")},
                    {"tests/test_alias.py": source.encode("utf-8")},
                )
                self.assertEqual(
                    exact["entries"][0]["assignment"]["expectation"],
                    {
                        "kind": "platform_conditioned",
                        "applicable_platforms": [platform],
                        "skip_safe_reason_code": f"requires_{platform}",
                    },
                )

        unknown_alias_conditions = (
            "import os\nimport unittest\nconditional = obtain_decorator()\n"
            "class AliasTests(unittest.TestCase):\n"
            "    @conditional(os.name == 'nt', 'alias')\n"
            "    def test_value(self): pass\n",
            "import os\nimport unittest\n"
            "class AliasTests(unittest.TestCase):\n"
            "    @getattr(unittest, obtain_name())(os.name == 'nt', 'alias')\n"
            "    def test_value(self): pass\n",
            "import os\nimport unittest\n"
            "if choose_alias():\n"
            "    conditional = unittest.skipIf\n"
            "else:\n"
            "    conditional = unittest.skipUnless\n"
            "class AliasTests(unittest.TestCase):\n"
            "    @conditional(os.name == 'nt', 'alias')\n"
            "    def test_value(self): pass\n",
        )
        for source in unknown_alias_conditions:
            with self.subTest(unknown_alias=source), self.assertRaisesRegex(
                Exception,
                "conditional skip.*(?:alias|unsupported)",
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

        invalid_placements = (
            (
                "inner-method-skip",
                "tests/test_inner.py",
                "InnerTests",
                "test_inner",
                f"""
                import importlib.util
                import unittest
                class InnerTests(unittest.TestCase):
                    @unittest.skipUnless(importlib.util.find_spec("cupy"), "gpu")
                    @unittest.skip({literal!r})
                    def test_inner(self): pass
                """,
            ),
            (
                "class-level-skip",
                relative_path,
                case_name,
                method_name,
                f"""
                import importlib.util
                import unittest
                @unittest.skip({literal!r})
                class {case_name}(unittest.TestCase):
                    @unittest.skip({literal!r})
                    @unittest.skipUnless(importlib.util.find_spec("cupy"), "gpu")
                    def {method_name}(self): pass
                """,
            ),
            (
                "multiple-method-skips",
                relative_path,
                case_name,
                method_name,
                f"""
                import importlib.util
                import unittest
                class {case_name}(unittest.TestCase):
                    @unittest.skip({literal!r})
                    @unittest.skip({literal!r})
                    @unittest.skipUnless(importlib.util.find_spec("cupy"), "gpu")
                    def {method_name}(self): pass
                """,
            ),
        )
        for label, path, _, _, raw_source in invalid_placements:
            supplied = {path: _source(raw_source)}
            with self.subTest(round5_skip_placement=label), self.assertRaisesRegex(
                self.generator.InventoryError,
                "unconditional skip",
            ):
                self.generator.build_inventory(
                    supplied,
                    supplied,
                    enforce_baseline_lock=False,
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
                "query",
                1,
                "stream",
            ),
            (
                self.static_id,
                "cuda_allocation",
                "cupy",
                "cupy.arange",
                "allocate",
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

    def test_reaching_definitions_preserve_sensitive_reassignments_and_containers(
        self,
    ) -> None:
        review = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import numpy as np
                    import unittest

                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            target = print
                            target = cp.arange
                            target(1)

                        def test_denied(self):
                            backends = [np, cp]
                            backend = backends[1]
                            backend.arange(1)
                    """
                )
            }
        )
        cupy_rows = {
            (row["item_id"], row.get("qualified_name")): row
            for row in review["receipt"]["expanded_rows"]
            if row["capability_kind"] == "call"
        }
        self.assertEqual(
            {
                item_id
                for item_id in (self.static_id, self.denied_id)
                if (item_id, "cupy.arange") in cupy_rows
            },
            {self.static_id, self.denied_id},
        )
        for item_id in (self.static_id, self.denied_id):
            row = cupy_rows[(item_id, "cupy.arange")]
            self.assertEqual(row["action"], "allocate")
            self.assertEqual(row["maximum_calls"], 1)
        self.assertFalse(review["unresolved_dynamic_blockers"])

        reassigned = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            target = cp.arange
                            target = print
                            target(1)
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertFalse(reassigned["receipt"]["expanded_rows"])
        self.assertFalse(reassigned["unresolved_dynamic_blockers"])

        dynamic = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import numpy as np
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            backends = [np, cp]
                            backend = backends[runtime_index()]
                            backend.arange(1)
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertFalse(dynamic["receipt"]["expanded_rows"])
        self.assertEqual(
            dynamic["unresolved_dynamic_blockers"],
            [
                {
                    "item_id": self.static_id,
                    "relative_path": "tests/test_review.py",
                    "line": 8,
                    "reason": "mixed protected receiver is dynamically unresolved",
                }
            ],
        )

    def test_environment_update_delete_alias_and_branch_state_is_call_local(
        self,
    ) -> None:
        ordered = self._review(
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
                            environment.update({"SAFE": "1", "TRACE": "2"})
                            subprocess.run(
                                [sys.executable, "-m", "updated"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                            del environment["SAFE"]
                            del environment["DROP"]
                            subprocess.run(
                                [sys.executable, "-m", "deleted"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )

                        def test_denied(self):
                            environment = dict(os.environ)
                            if runtime_condition():
                                environment.update({"MODE": "left"})
                            else:
                                environment.update({"MODE": "right"})
                            subprocess.run(
                                [sys.executable, "-m", "conditional"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                    """
                )
            }
        )
        rows = {
            tuple(row["argv"]): row
            for row in ordered["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        }
        self.assertEqual(
            rows[("-m", "updated")]["environment_additions"],
            {"SAFE": "1", "TRACE": "2"},
        )
        self.assertEqual(
            rows[("-m", "updated")]["environment_removals"],
            [],
        )
        self.assertEqual(
            rows[("-m", "deleted")]["environment_additions"],
            {"TRACE": "2"},
        )
        self.assertEqual(
            rows[("-m", "deleted")]["environment_removals"],
            ["DROP", "SAFE"],
        )
        self.assertNotIn(("-m", "conditional"), rows)
        self.assertEqual(
            ordered["unresolved_dynamic_blockers"],
            [
                {
                    "item_id": self.denied_id,
                    "relative_path": "tests/test_review.py",
                    "line": 31,
                    "reason": "subprocess environment branch state is ambiguous",
                }
            ],
        )

        aliased = self._review(
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
                            alias = environment
                            alias.update({"SAFE": "1"})
                            subprocess.run(
                                [sys.executable, "-m", "aliased"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertFalse(aliased["receipt"]["expanded_rows"])
        self.assertEqual(
            aliased["unresolved_dynamic_blockers"],
            [
                {
                    "item_id": self.static_id,
                    "relative_path": "tests/test_review.py",
                    "line": 10,
                    "reason": "subprocess environment alias mutation is unresolved",
                }
            ],
        )

        equal_branch = self._review(
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
                            if runtime_condition():
                                environment.update({"MODE": "same"})
                            else:
                                environment.update({"MODE": "same"})
                            subprocess.run(
                                [sys.executable, "-m", "equal"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    """
                )
            }
        )
        equal_process = next(
            row
            for row in equal_branch["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        )
        self.assertEqual(equal_process["environment_additions"], {"MODE": "same"})
        self.assertFalse(equal_branch["unresolved_dynamic_blockers"])

    def test_match_exception_and_child_program_analysis_never_silently_undercounts(
        self,
    ) -> None:
        compound = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            match runtime_value():
                                case 1:
                                    for _ in range(2):
                                        cp.arange(1)
                                case _:
                                    for _ in range(5):
                                        cp.arange(1)
                        def test_denied(self):
                            try:
                                raise RuntimeError
                            except cp.arange(1):
                                pass
                    """
                )
            }
        )
        compound_rows = {
            (row["item_id"], row.get("qualified_name")): row
            for row in compound["receipt"]["expanded_rows"]
            if row["capability_kind"] == "call"
        }
        self.assertEqual(
            compound_rows[(self.static_id, "cupy.arange")]["maximum_calls"],
            5,
        )
        self.assertEqual(
            compound_rows[(self.denied_id, "cupy.arange")]["maximum_calls"],
            1,
        )
        self.assertFalse(compound["unresolved_dynamic_blockers"])

        child = self._review(
            sources={
                "tests/test_review.py": _source(
                    r'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = (
                                "import subprocess, sys\n"
                                "subprocess.run([sys.executable, '-m', 'nested'], "
                                "timeout=5, check=False)\n"
                            )
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self):
                            program = (
                                "import cupy as cp\n"
                                "for _ in range(5):\n"
                                "    cp.arange(1)\n"
                            )
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                    '''
                )
            }
        )
        static_processes = [
            row
            for row in child["receipt"]["expanded_rows"]
            if row["item_id"] == self.static_id
            and row["capability_kind"] == "subprocess"
        ]
        self.assertEqual(len(static_processes), 2)
        outer_process = next(
            row for row in static_processes if row["argv"][0] == "-c"
        )
        nested_process = next(
            row for row in static_processes if row["argv"] == ["-m", "nested"]
        )
        self.assertTrue(outer_process["fixed_descendant_permission"])
        self.assertFalse(nested_process["fixed_descendant_permission"])
        child_call = next(
            row
            for row in child["receipt"]["expanded_rows"]
            if row["item_id"] == self.denied_id
            and row.get("qualified_name") == "cupy.arange"
        )
        self.assertEqual(child_call["maximum_calls"], 5)
        self.assertFalse(child["unresolved_dynamic_blockers"])

        repeated_child = self._review(
            sources={
                "tests/test_review.py": _source(
                    r'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = (
                                "import subprocess, sys\n"
                                "for _ in range(2):\n"
                                "    subprocess.run([sys.executable, '-m', 'nested'], "
                                "timeout=5, check=False)\n"
                            )
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
            }
        )
        self.assertFalse(repeated_child["receipt"]["expanded_rows"])
        self.assertEqual(
            repeated_child["unresolved_dynamic_blockers"],
            [
                {
                    "item_id": self.static_id,
                    "relative_path": "tests/test_review.py",
                    "line": 12,
                    "reason": (
                        "subprocess dynamic Python child subprocess repetition "
                        "is not representable"
                    ),
                }
            ],
        )

    def test_protected_results_match_captures_and_child_provenance_are_complete(
        self,
    ) -> None:
        attribute_store = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest

                    class Box:
                        pass

                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            box = Box()
                            box.backend = cp
                            box.backend.arange(1)

                        def test_denied(self):
                            pass
                    """
                )
            }
        )
        attribute_rows = [
            row
            for row in attribute_store["receipt"]["expanded_rows"]
            if row.get("qualified_name") == "cupy.arange"
        ]
        self.assertEqual(
            [
                (row["item_id"], row["maximum_calls"])
                for row in attribute_rows
            ],
            [(self.static_id, 1)],
        )
        self.assertFalse(attribute_store["unresolved_dynamic_blockers"])

        unresolved_forms = (
            (
                "identity-call-result",
                _source(
                    """
                    import cupy as cp
                    import unittest

                    def identity(value):
                        return value

                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            identity(cp).arange(1)
                        def test_denied(self): pass
                    """
                ),
                9,
                "dynamic sensitive call result is unresolved",
            ),
            (
                "boolean-composite",
                _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            backend = runtime_flag() and cp
                            backend.arange(1)
                        def test_denied(self): pass
                    """
                ),
                6,
                "mixed protected receiver is dynamically unresolved",
            ),
        )
        for label, source, line, reason in unresolved_forms:
            with self.subTest(label=label):
                review = self._review(
                    sources={"tests/test_review.py": source}
                )
                self.assertFalse(review["receipt"]["expanded_rows"])
                self.assertEqual(
                    review["unresolved_dynamic_blockers"],
                    [
                        {
                            "item_id": self.static_id,
                            "relative_path": "tests/test_review.py",
                            "line": line,
                            "reason": reason,
                        }
                    ],
                )

        subscript_store = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest

                    class Box:
                        pass

                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            box = Box()
                            box.backends = {}
                            box.backends["gpu"] = cp
                            box.backends["gpu"].arange(1)
                        def test_denied(self): pass
                    """
                )
            }
        )
        subscript_call = next(
            row
            for row in subscript_store["receipt"]["expanded_rows"]
            if row.get("qualified_name") == "cupy.arange"
        )
        self.assertEqual(subscript_call["item_id"], self.static_id)
        self.assertEqual(subscript_call["maximum_calls"], 1)
        self.assertFalse(subscript_store["unresolved_dynamic_blockers"])

        helper_return = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import subprocess
                    import sys
                    import unittest

                    def runner():
                        return subprocess.run

                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            launch = runner()
                            launch(
                                [sys.executable, "-m", "returned-helper"],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    """
                )
            }
        )
        returned_processes = [
            row
            for row in helper_return["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        ]
        self.assertEqual(
            [row["argv"] for row in returned_processes],
            [["-m", "returned-helper"]],
        )
        self.assertFalse(helper_return["unresolved_dynamic_blockers"])

        exact_child = self._review(
            sources={
                "tests/test_review.py": _source(
                    r'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = (
                                "import cupy as cp\n"
                                "import subprocess, sys\n"
                                "class Box: pass\n"
                                "def runner(): return subprocess.run\n"
                                "box = Box()\n"
                                "box.backend = cp\n"
                                "box.backend.arange(1)\n"
                                "launch = runner()\n"
                                "launch([sys.executable, '-m', 'child-returned'], "
                                "timeout=5, check=False)\n"
                            )
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
            }
        )
        exact_child_rows = exact_child["receipt"]["expanded_rows"]
        exact_child_calls = [
            row
            for row in exact_child_rows
            if row.get("qualified_name") == "cupy.arange"
        ]
        self.assertEqual(
            [(row["item_id"], row["maximum_calls"]) for row in exact_child_calls],
            [(self.static_id, 1)],
        )
        child_processes = [
            row
            for row in exact_child_rows
            if row["capability_kind"] == "subprocess"
        ]
        self.assertEqual(len(child_processes), 2)
        child_outer = next(row for row in child_processes if row["argv"][0] == "-c")
        child_nested = next(
            row for row in child_processes if row["argv"] == ["-m", "child-returned"]
        )
        self.assertEqual(child_outer["argv"][:1], ["-c"])
        self.assertEqual(child_nested["argv"], ["-m", "child-returned"])
        self.assertTrue(child_outer["fixed_descendant_permission"])
        self.assertFalse(child_nested["fixed_descendant_permission"])
        self.assertFalse(exact_child["unresolved_dynamic_blockers"])

        unresolved_child_programs = (
            (
                "identity-call-result",
                (
                    "import cupy as cp\n"
                    "def identity(value): return value\n"
                    "identity(cp).arange(1)\n"
                ),
            ),
            (
                "boolean-composite",
                (
                    "import cupy as cp\n"
                    "backend = runtime_flag() and cp\n"
                    "backend.arange(1)\n"
                ),
            ),
        )
        for label, child_program in unresolved_child_programs:
            with self.subTest(child=label):
                source = _source(
                    f'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = {child_program!r}
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
                unresolved = self._review(
                    sources={"tests/test_review.py": source}
                )
                self.assertFalse(unresolved["receipt"]["expanded_rows"])
                self.assertEqual(
                    unresolved["unresolved_dynamic_blockers"],
                    [
                        {
                            "item_id": self.static_id,
                            "relative_path": "tests/test_review.py",
                            "line": 7,
                            "reason": (
                                "subprocess dynamic Python program has unresolved "
                                "sensitive dataflow"
                            ),
                        }
                    ],
                )

        match_capture = self._review(
            sources={
                "tests/test_review.py": _source(
                    r'''
                    import cupy as cp
                    import subprocess
                    import sys
                    import unittest

                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            match cp:
                                case backend if backend.arange(1):
                                    pass

                        def test_denied(self):
                            program = (
                                "import cupy as cp\n"
                                "match cp:\n"
                                "    case backend if backend.arange(1):\n"
                                "        pass\n"
                            )
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                    '''
                )
            }
        )
        match_rows = [
            row
            for row in match_capture["receipt"]["expanded_rows"]
            if row.get("qualified_name") == "cupy.arange"
        ]
        self.assertEqual(
            sorted(
                (row["item_id"], row["maximum_calls"])
                for row in match_rows
            ),
            [(self.denied_id, 1), (self.static_id, 1)],
        )
        child_parent = next(
            row
            for row in match_capture["receipt"]["expanded_rows"]
            if row["item_id"] == self.denied_id
            and row["capability_kind"] == "subprocess"
        )
        self.assertTrue(child_parent["fixed_descendant_permission"])
        self.assertFalse(match_capture["unresolved_dynamic_blockers"])

        unsupported_pattern = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            match cp:
                                case {"backend": backend} if backend.arange(1):
                                    pass
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertFalse(unsupported_pattern["receipt"]["expanded_rows"])
        self.assertEqual(
            unsupported_pattern["unresolved_dynamic_blockers"],
            [
                {
                    "item_id": self.static_id,
                    "relative_path": "tests/test_review.py",
                    "line": 6,
                    "reason": "protected match pattern is unsupported",
                }
            ],
        )

        unresolved_child = self._review(
            sources={
                "tests/test_review.py": _source(
                    r'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = (
                                "import cupy as cp\n"
                                "def identity(value): return value\n"
                                "identity(cp).arange(1)\n"
                            )
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
            }
        )
        self.assertFalse(
            [
                row
                for row in unresolved_child["receipt"]["expanded_rows"]
                if row["item_id"] == self.static_id
            ]
        )
        child_blockers = unresolved_child["unresolved_dynamic_blockers"]
        self.assertEqual(len(child_blockers), 1)
        self.assertEqual(child_blockers[0]["item_id"], self.static_id)
        self.assertEqual(
            child_blockers[0]["reason"],
            "subprocess dynamic Python program has unresolved sensitive dataflow",
        )

    def test_source_order_bounds_exception_environments_and_decorators_are_exact(
        self,
    ) -> None:
        bounds = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            count = 5
                            for _ in range(count):
                                cp.arange(1)
                            count = 1
                            for _ in range(count):
                                cp.arange(1)

                        def test_denied(self):
                            count = 1
                            for _ in range(count):
                                cp.arange(1)
                            count = 5
                            for _ in range(count):
                                cp.arange(1)
                    """
                )
            }
        )
        bounded_rows = {
            row["item_id"]: row
            for row in bounds["receipt"]["expanded_rows"]
            if row.get("qualified_name") == "cupy.arange"
        }
        self.assertEqual(bounded_rows[self.static_id]["maximum_calls"], 6)
        self.assertEqual(bounded_rows[self.denied_id]["maximum_calls"], 6)
        self.assertFalse(bounds["unresolved_dynamic_blockers"])

        comprehensions = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            count = 5
                            [cp.arange(1) for _ in range(count)]
                            count = 1
                            [cp.arange(1) for _ in range(count)]
                        def test_denied(self): pass
                    """
                )
            }
        )
        comprehension_call = next(
            row
            for row in comprehensions["receipt"]["expanded_rows"]
            if row.get("qualified_name") == "cupy.arange"
        )
        self.assertEqual(comprehension_call["maximum_calls"], 6)
        self.assertFalse(comprehensions["unresolved_dynamic_blockers"])

        conditional = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            cp.arange(1) if runtime_flag() else cp.arange(1)
                        def test_denied(self): pass
                    """
                )
            }
        )
        conditional_call = next(
            row
            for row in conditional["receipt"]["expanded_rows"]
            if row.get("qualified_name") == "cupy.arange"
        )
        self.assertEqual(conditional_call["maximum_calls"], 1)
        self.assertFalse(conditional["unresolved_dynamic_blockers"])

        exception_state = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import os
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            environment = os.environ.copy()
                            try:
                                environment["MODE"] = "raised"
                                raise RuntimeError
                            except RuntimeError:
                                subprocess.run(
                                    [sys.executable, "-m", "handler"],
                                    env=environment,
                                    timeout=5,
                                    check=False,
                                )

                        def test_denied(self):
                            environment = os.environ.copy()
                            try:
                                if runtime_flag():
                                    environment["MODE"] = "left"
                                else:
                                    environment["MODE"] = "right"
                                raise RuntimeError
                            except RuntimeError:
                                subprocess.run(
                                    [sys.executable, "-m", "ambiguous-handler"],
                                    env=environment,
                                    timeout=5,
                                    check=False,
                                )
                    """
                )
            }
        )
        handler_rows = {
            tuple(row["argv"]): row
            for row in exception_state["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
        }
        self.assertEqual(
            handler_rows[("-m", "handler")]["environment_additions"],
            {"MODE": "raised"},
        )
        self.assertEqual(
            handler_rows[("-m", "handler")]["environment_removals"],
            [],
        )
        self.assertNotIn(("-m", "ambiguous-handler"), handler_rows)
        self.assertEqual(
            exception_state["unresolved_dynamic_blockers"],
            [
                {
                    "item_id": self.denied_id,
                    "relative_path": "tests/test_review.py",
                    "line": 28,
                    "reason": (
                        "subprocess environment exceptional state is ambiguous"
                    ),
                }
            ],
        )

        child_exception = self._review(
            sources={
                "tests/test_review.py": _source(
                    r'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = (
                                "import os, subprocess, sys\n"
                                "environment = os.environ.copy()\n"
                                "try:\n"
                                "    environment['MODE'] = 'child-raised'\n"
                                "    raise RuntimeError\n"
                                "except RuntimeError:\n"
                                "    subprocess.run([sys.executable, '-m', 'child-handler'], "
                                "env=environment, timeout=5, check=False)\n"
                            )
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
            }
        )
        nested_handler = next(
            row
            for row in child_exception["receipt"]["expanded_rows"]
            if row["capability_kind"] == "subprocess"
            and row["argv"] == ["-m", "child-handler"]
        )
        self.assertEqual(
            nested_handler["environment_additions"],
            {"MODE": "child-raised"},
        )
        self.assertFalse(child_exception["unresolved_dynamic_blockers"])

        divergent_child = self._review(
            sources={
                "tests/test_review.py": _source(
                    r'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = (
                                "import os, subprocess, sys\n"
                                "environment = os.environ.copy()\n"
                                "try:\n"
                                "    if runtime_flag():\n"
                                "        environment['MODE'] = 'left'\n"
                                "    else:\n"
                                "        environment['MODE'] = 'right'\n"
                                "    raise RuntimeError\n"
                                "except RuntimeError:\n"
                                "    subprocess.run([sys.executable, '-m', 'child-ambiguous'], "
                                "env=environment, timeout=5, check=False)\n"
                            )
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
            }
        )
        self.assertFalse(divergent_child["receipt"]["expanded_rows"])
        self.assertEqual(
            divergent_child["unresolved_dynamic_blockers"],
            [
                {
                    "item_id": self.static_id,
                    "relative_path": "tests/test_review.py",
                    "line": 19,
                    "reason": (
                        "subprocess dynamic Python program has unresolved "
                        "subprocess environment exceptional state"
                    ),
                }
            ],
        )

        earlier_alias = _source(
            """
            import os
            import unittest
            conditional = unittest.skipIf
            class EarlierTests(unittest.TestCase):
                @conditional(os.name == "nt", "POSIX only")
                def test_value(self): pass
            conditional = obtain_decorator()
            """
        )
        earlier = self.generator.build_inventory(
            {"tests/test_alias.py": earlier_alias},
            {"tests/test_alias.py": earlier_alias},
        )
        self.assertEqual(
            earlier["entries"][0]["assignment"]["expectation"],
            {
                "kind": "platform_conditioned",
                "applicable_platforms": ["posix"],
                "skip_safe_reason_code": "requires_posix",
            },
        )

        aliased_os = _source(
            """
            import os as platform_os
            import unittest
            conditional = unittest.skipIf
            class AliasTests(unittest.TestCase):
                @conditional(platform_os.name == "nt", "POSIX only")
                def test_value(self): pass
            """
        )
        aliased = self.generator.build_inventory(
            {"tests/test_alias.py": aliased_os},
            {"tests/test_alias.py": aliased_os},
        )
        self.assertEqual(
            aliased["entries"][0]["assignment"]["expectation"],
            {
                "kind": "platform_conditioned",
                "applicable_platforms": ["posix"],
                "skip_safe_reason_code": "requires_posix",
            },
        )

        retained_unknown = _source(
            """
            import os as platform_os
            import unittest
            conditional = unittest.skipIf
            if runtime_flag():
                conditional = obtain_decorator()
            class UnknownTests(unittest.TestCase):
                @conditional(platform_os.name == "nt", "possibly retained skip")
                def test_value(self): pass
            """
        )
        with self.assertRaisesRegex(Exception, "conditional skip.*alias"):
            self.generator.discover_test_sources(
                {"tests/test_alias.py": retained_unknown}
            )

    def test_analysis_budgets_contain_deep_helpers_and_invalid_ranges(self) -> None:
        helper_lines = [
            "import subprocess",
            "import sys",
            "import unittest",
            "",
        ]
        for index in range(1050):
            helper_lines.append(f"def helper_{index}():")
            if index == 1049:
                helper_lines.extend(
                    (
                        "    subprocess.run(",
                        "        [sys.executable, '-m', 'deep-helper'],",
                        "        timeout=5,",
                        "        check=False,",
                        "    )",
                    )
                )
            else:
                helper_lines.append(f"    return helper_{index + 1}()")
            helper_lines.append("")
        helper_lines.extend(
            (
                "class ReviewTests(unittest.TestCase):",
                "    def test_static(self):",
                "        helper_0()",
                "    def test_denied(self): pass",
            )
        )
        with self.assertRaisesRegex(
            self.generator.InventoryError,
            "analysis.*(?:depth|budget)",
        ):
            self._review(
                sources={
                    "tests/test_review.py": (
                        "\n".join(helper_lines).encode("utf-8") + b"\n"
                    )
                }
            )

        range_sources = (
            (
                "zero-step",
                "for _ in range(0, 10, 0):\n"
                "                cp.arange(1)",
                "range.*step",
            ),
            (
                "overflow",
                "for _ in range(0, " + "1" + "0" * 1000 + "):\n"
                "                cp.arange(1)",
                "range.*(?:cardinality|budget)",
            ),
        )
        for label, loop, message in range_sources:
            source = _source(
                "import cupy as cp\n"
                "import unittest\n"
                "class ReviewTests(unittest.TestCase):\n"
                "    def test_static(self):\n"
                f"        {loop}\n"
                "    def test_denied(self): pass\n"
            )
            with self.subTest(label=label), self.assertRaisesRegex(
                self.generator.InventoryError,
                message,
            ):
                self._review(sources={"tests/test_review.py": source})

        large_container = _source(
            "import cupy as cp\n"
            "import unittest\n"
            "class ReviewTests(unittest.TestCase):\n"
            "    def test_static(self):\n"
            "        backends = [" + ", ".join(["cp"] * 5000) + "]\n"
            "        backends[0].arange(1)\n"
            "    def test_denied(self): pass\n"
        )
        with self.assertRaisesRegex(
            self.generator.InventoryError,
            "analysis.*(?:container|node|budget)",
        ):
            self._review(sources={"tests/test_review.py": large_container})

        nested_program = "pass\n"
        for _ in range(6):
            nested_program = (
                "import subprocess, sys\n"
                "subprocess.run([sys.executable, '-c', "
                f"{nested_program!r}], timeout=5, check=False)\n"
            )
        child_depth_source = _source(
            f'''
            import subprocess
            import sys
            import unittest
            class ReviewTests(unittest.TestCase):
                def test_static(self):
                    program = {nested_program!r}
                    subprocess.run(
                        [sys.executable, "-c", program],
                        timeout=5,
                        check=False,
                    )
                def test_denied(self): pass
            '''
        )
        child_depth = self._review(
            sources={"tests/test_review.py": child_depth_source}
        )
        self.assertFalse(child_depth["receipt"]["expanded_rows"])
        self.assertEqual(
            child_depth["unresolved_dynamic_blockers"],
            [
                {
                    "item_id": self.static_id,
                    "relative_path": "tests/test_review.py",
                    "line": 7,
                    "reason": "subprocess child analysis depth exceeds 4",
                }
            ],
        )

    def test_round4_sensitive_provenance_red_contracts_are_independent(self) -> None:
        exact_sources = (
            (
                "attribute-store",
                _source(
                    """
                    import cupy as cp
                    import unittest
                    class Box: pass
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            box = Box()
                            box.backend = cp
                            box.backend.arange(1)
                        def test_denied(self): pass
                    """
                ),
            ),
            (
                "subscript-store",
                _source(
                    """
                    import cupy as cp
                    import unittest
                    class Box: pass
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            box = Box()
                            box.backends = {}
                            box.backends["gpu"] = cp
                            box.backends["gpu"].arange(1)
                        def test_denied(self): pass
                    """
                ),
            ),
        )
        for label, source in exact_sources:
            with self.subTest(exact=label):
                review = self._review(sources={"tests/test_review.py": source})
                calls = [
                    row
                    for row in review["receipt"]["expanded_rows"]
                    if row.get("qualified_name") == "cupy.arange"
                ]
                self.assertEqual(
                    [(row["item_id"], row["maximum_calls"]) for row in calls],
                    [(self.static_id, 1)],
                )
                self.assertFalse(review["unresolved_dynamic_blockers"])

        blocker_sources = (
            (
                "unsupported-call-result",
                _source(
                    """
                    import cupy as cp
                    import unittest
                    def identity(value): return value
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            identity(cp).arange(1)
                        def test_denied(self): pass
                    """
                ),
                6,
                "dynamic sensitive call result is unresolved",
            ),
            (
                "boolean-composite",
                _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            backend = runtime_flag() and cp
                            backend.arange(1)
                        def test_denied(self): pass
                    """
                ),
                6,
                "mixed protected receiver is dynamically unresolved",
            ),
        )
        for label, source, line, reason in blocker_sources:
            with self.subTest(blocker=label):
                review = self._review(sources={"tests/test_review.py": source})
                self.assertFalse(review["receipt"]["expanded_rows"])
                self.assertEqual(
                    review["unresolved_dynamic_blockers"],
                    [
                        {
                            "item_id": self.static_id,
                            "relative_path": "tests/test_review.py",
                            "line": line,
                            "reason": reason,
                        }
                    ],
                )

        unsupported_store_sources = (
            (
                "dynamic-attribute-store",
                _source(
                    """
                    import cupy as cp
                    import unittest
                    class Box: pass
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            box = Box()
                            getattr(box, runtime_name()).backend = cp
                        def test_denied(self): pass
                    """
                ),
                7,
                "protected value store target is dynamically unresolved",
            ),
            (
                "dynamic-subscript-store",
                _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            backends = {}
                            backends[runtime_key()] = cp
                            backends["gpu"].arange(1)
                        def test_denied(self): pass
                    """
                ),
                7,
                "mixed protected receiver is dynamically unresolved",
            ),
            (
                "unary-protected-value",
                _source(
                    """
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            backend = +cp
                            backend.arange(1)
                        def test_denied(self): pass
                    """
                ),
                6,
                "mixed protected receiver is dynamically unresolved",
            ),
        )
        for label, source, line, reason in unsupported_store_sources:
            with self.subTest(round5_provenance=label):
                review = self._review(sources={"tests/test_review.py": source})
                self.assertFalse(review["receipt"]["expanded_rows"])
                self.assertEqual(
                    review["unresolved_dynamic_blockers"],
                    [
                        {
                            "item_id": self.static_id,
                            "relative_path": "tests/test_review.py",
                            "line": line,
                            "reason": reason,
                        }
                    ],
                )

        with self.subTest(round5_rereview="mapping-evaluates-later-sensitive-child"):
            review = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                backend = {runtime_key(): 0, "gpu": cp}
                                backend["gpu"].arange(1)
                            def test_denied(self): pass
                        """
                    )
                }
            )
            self.assertFalse(review["receipt"]["expanded_rows"])
            self.assertEqual(
                review["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 6,
                        "reason": "mixed protected receiver is dynamically unresolved",
                    }
                ],
            )

        with self.subTest(round5_rereview="dict-comprehension-expanded-cardinality"):
            review = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                backend = {index: cp for index in range(4096)}
                                backend[0].arange(1)
                            def test_denied(self): pass
                        """
                    )
                }
            )
            self.assertFalse(review["receipt"]["expanded_rows"])
            self.assertEqual(
                review["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 6,
                        "reason": "mixed protected receiver is dynamically unresolved",
                    }
                ],
            )

        safe_observation = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import inspect
                    from pathlib import Path
                    from unittest.mock import patch
                    import unittest
                    import pontius.gpu_occupied_card_quotient as subject
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            source = Path(
                                inspect.getsourcefile(subject) or ""
                            ).read_text(encoding="utf-8")
                            with patch.object(
                                subject,
                                "run_frozen_gpu_quotient_keystone",
                            ) as observed:
                                observed.assert_not_called()
                            self.assertIsInstance(source, str)
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertFalse(safe_observation["receipt"]["expanded_rows"])
        self.assertFalse(safe_observation["unresolved_dynamic_blockers"])

        safe_module_patch = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import unittest
                    import pontius.gpu_quotient_validation_seam as subject
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            original = subject.diagnostic_sha256
                            try:
                                subject.diagnostic_sha256 = lambda value: "0" * 64
                                subject.diagnostic_sha256(b"")
                                subject.literal_byte_equal(b"", b"")
                            finally:
                                subject.diagnostic_sha256 = original
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertFalse(safe_module_patch["receipt"]["expanded_rows"])
        self.assertFalse(safe_module_patch["unresolved_dynamic_blockers"])

        clean_dynamic_helper = self._review(
            sources={
                "tests/test_review.py": _source(
                    """
                    import json
                    import unittest
                    def compact(value):
                        return json.dumps(value).encode("utf-8")
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            for value in values:
                                compact(value)
                        def test_denied(self): pass
                    """
                )
            }
        )
        self.assertFalse(clean_dynamic_helper["receipt"]["expanded_rows"])
        self.assertFalse(clean_dynamic_helper["unresolved_dynamic_blockers"])

    def test_round4_match_capture_red_contracts_are_independent(self) -> None:
        with self.subTest(scope="direct"):
            direct = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                match cp:
                                    case backend if backend.arange(1):
                                        pass
                            def test_denied(self): pass
                        """
                    )
                }
            )
            calls = [
                row
                for row in direct["receipt"]["expanded_rows"]
                if row.get("qualified_name") == "cupy.arange"
            ]
            self.assertEqual(
                [(row["item_id"], row["maximum_calls"]) for row in calls],
                [(self.static_id, 1)],
            )
            self.assertFalse(direct["unresolved_dynamic_blockers"])

        with self.subTest(scope="literal-child"):
            program = (
                "import cupy as cp\n"
                "match cp:\n"
                "    case backend if backend.arange(1):\n"
                "        pass\n"
            )
            child = self._review(
                sources={
                    "tests/test_review.py": _source(
                        f'''
                        import subprocess
                        import sys
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                program = {program!r}
                                subprocess.run(
                                    [sys.executable, "-c", program],
                                    timeout=5,
                                    check=False,
                                )
                            def test_denied(self): pass
                        '''
                    )
                }
            )
            calls = [
                row
                for row in child["receipt"]["expanded_rows"]
                if row.get("qualified_name") == "cupy.arange"
            ]
            parent = next(
                row
                for row in child["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            )
            self.assertEqual(
                [(row["item_id"], row["maximum_calls"]) for row in calls],
                [(self.static_id, 1)],
            )
            self.assertTrue(parent["fixed_descendant_permission"])
            self.assertFalse(child["unresolved_dynamic_blockers"])

        with self.subTest(scope="unsupported-pattern"):
            unsupported = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                match cp:
                                    case {"backend": backend} if backend.arange(1):
                                        pass
                            def test_denied(self): pass
                        """
                    )
                }
            )
            self.assertFalse(unsupported["receipt"]["expanded_rows"])
            self.assertEqual(
                unsupported["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 6,
                        "reason": "protected match pattern is unsupported",
                    }
                ],
            )

        with self.subTest(round5_match="no-match-residual-state"):
            residual = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import math as safe_backend
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                backend = cp
                                match runtime_value():
                                    case 1:
                                        backend = safe_backend
                                backend.arange(1)
                            def test_denied(self): pass
                        """
                    )
                }
            )
            self.assertFalse(residual["receipt"]["expanded_rows"])
            self.assertEqual(
                residual["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 10,
                        "reason": "mixed protected receiver is dynamically unresolved",
                    }
                ],
            )

        with self.subTest(round5_match="guard-failure-is-sequential"):
            guards = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                match runtime_value():
                                    case _ if cp.arange(1):
                                        pass
                                    case _ if cp.arange(1):
                                        pass
                                    case _:
                                        pass
                            def test_denied(self): pass
                        """
                    )
                }
            )
            call = next(
                row
                for row in guards["receipt"]["expanded_rows"]
                if row.get("qualified_name") == "cupy.arange"
            )
            self.assertEqual(call["maximum_calls"], 2)
            self.assertFalse(guards["unresolved_dynamic_blockers"])

    def test_round4_child_and_helper_provenance_red_contracts_are_independent(
        self,
    ) -> None:
        with self.subTest(exact="helper-returned-subprocess"):
            helper = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import subprocess
                        import sys
                        import unittest
                        def runner(): return subprocess.run
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                launch = runner()
                                launch(
                                    [sys.executable, "-m", "returned"],
                                    timeout=5,
                                    check=False,
                                )
                            def test_denied(self): pass
                        """
                    )
                }
            )
            processes = [
                row
                for row in helper["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            ]
            self.assertEqual([row["argv"] for row in processes], [["-m", "returned"]])
            self.assertFalse(helper["unresolved_dynamic_blockers"])

        with self.subTest(round5_helper="local-alias-return"):
            helper = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import subprocess
                        import sys
                        import unittest
                        def runner():
                            launch = subprocess.run
                            return launch
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                launch = runner()
                                launch(
                                    [sys.executable, "-m", "local-returned"],
                                    timeout=5,
                                    check=False,
                                )
                            def test_denied(self): pass
                        """
                    )
                }
            )
            processes = [
                row
                for row in helper["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            ]
            self.assertEqual(
                [row["argv"] for row in processes],
                [["-m", "local-returned"]],
            )
            self.assertFalse(helper["unresolved_dynamic_blockers"])

        with self.subTest(round5_helper="divergent-protected-return"):
            divergent = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import subprocess
                        import sys
                        import unittest
                        def runner():
                            if runtime_flag():
                                return subprocess.run
                            return print
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                launch = runner()
                                launch(
                                    [sys.executable, "-m", "divergent"],
                                    timeout=5,
                                    check=False,
                                )
                            def test_denied(self): pass
                        """
                    )
                }
            )
            self.assertFalse(divergent["receipt"]["expanded_rows"])
            self.assertEqual(
                divergent["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 11,
                        "reason": "callable alias is dynamically unresolved",
                    }
                ],
            )

        exact_child_program = (
            "import cupy as cp\n"
            "import subprocess, sys\n"
            "class Box: pass\n"
            "def runner(): return subprocess.run\n"
            "box = Box()\n"
            "box.backend = cp\n"
            "box.backend.arange(1)\n"
            "launch = runner()\n"
            "launch([sys.executable, '-m', 'child-returned'], "
            "timeout=5, check=False)\n"
        )
        with self.subTest(exact="child-provenance"):
            child = self._review(
                sources={
                    "tests/test_review.py": _source(
                        f'''
                        import subprocess
                        import sys
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                program = {exact_child_program!r}
                                subprocess.run(
                                    [sys.executable, "-c", program],
                                    timeout=5,
                                    check=False,
                                )
                            def test_denied(self): pass
                        '''
                    )
                }
            )
            child_calls = [
                row
                for row in child["receipt"]["expanded_rows"]
                if row.get("qualified_name") == "cupy.arange"
            ]
            child_processes = [
                row
                for row in child["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            ]
            self.assertEqual(
                [(row["item_id"], row["maximum_calls"]) for row in child_calls],
                [(self.static_id, 1)],
            )
            self.assertEqual(len(child_processes), 2)
            outer = next(row for row in child_processes if row["argv"][0] == "-c")
            nested = next(
                row for row in child_processes if row["argv"] == ["-m", "child-returned"]
            )
            self.assertTrue(outer["fixed_descendant_permission"])
            self.assertFalse(nested["fixed_descendant_permission"])
            self.assertFalse(child["unresolved_dynamic_blockers"])

        child_blockers = (
            (
                "unsupported-call-result",
                (
                    "import cupy as cp\n"
                    "def identity(value): return value\n"
                    "identity(cp).arange(1)\n"
                ),
            ),
            (
                "boolean-composite",
                (
                    "import cupy as cp\n"
                    "backend = runtime_flag() and cp\n"
                    "backend.arange(1)\n"
                ),
            ),
        )
        for label, program in child_blockers:
            with self.subTest(child_blocker=label):
                source = _source(
                    f'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = {program!r}
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
                review = self._review(
                    sources={"tests/test_review.py": source}
                )
                self.assertFalse(review["receipt"]["expanded_rows"])
                self.assertEqual(
                    review["unresolved_dynamic_blockers"],
                    [
                        {
                            "item_id": self.static_id,
                            "relative_path": "tests/test_review.py",
                            "line": 7,
                            "reason": (
                                "subprocess dynamic Python program has unresolved "
                                "sensitive dataflow"
                            ),
                        }
                    ],
                )

        with self.subTest(round5_helper="literal-child-divergent-return"):
            program = (
                "import subprocess, sys\n"
                "def runner():\n"
                "    if runtime_flag():\n"
                "        return subprocess.run\n"
                "    return print\n"
                "launch = runner()\n"
                "launch([sys.executable, '-m', 'child-divergent'], "
                "timeout=5, check=False)\n"
            )
            source = _source(
                f'''
                import subprocess
                import sys
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        program = {program!r}
                        subprocess.run(
                            [sys.executable, "-c", program],
                            timeout=5,
                            check=False,
                        )
                    def test_denied(self): pass
                '''
            )
            review = self._review(sources={"tests/test_review.py": source})
            self.assertFalse(review["receipt"]["expanded_rows"])
            self.assertEqual(
                review["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 7,
                        "reason": (
                            "subprocess dynamic Python program has unresolved "
                            "sensitive dataflow"
                        ),
                    }
                ],
            )

    def _final_rereview_preclassifier_exhausts_irrefutable_match(self) -> None:
        module = ast.parse(
            textwrap.dedent(
                """
                import cupy as cp
                def reviewed(subject):
                    protected = cp
                    match subject:
                        case _:
                            protected = None
                    protected.arange()
                """
            )
        )
        function = next(
            node for node in module.body if isinstance(node, ast.FunctionDef)
        )
        calls = self.generator._preclassified_sensitive_calls(
            function.body,
            {"cp": "cupy"},
            self.generator._AnalysisBudget(),
            {},
        )
        following = next(
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "arange"
        )
        self.assertNotIn(id(following), calls)

    def _final_rereview_preclassifier_uses_throw_site_handler_state(self) -> None:
        module = ast.parse(
            textwrap.dedent(
                """
                import cupy as cp
                def reviewed():
                    protected = cp
                    try:
                        protected = None
                        raise RuntimeError()
                    except RuntimeError:
                        protected.arange()
                """
            )
        )
        function = next(
            node for node in module.body if isinstance(node, ast.FunctionDef)
        )
        calls = self.generator._preclassified_sensitive_calls(
            function.body,
            {"cp": "cupy"},
            self.generator._AnalysisBudget(),
            {},
        )
        handler_call = next(
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "arange"
        )
        self.assertNotIn(id(handler_call), calls)

    def _final2_preclassifier_tracks_nested_exact_throw_sites(self) -> None:
        module = ast.parse(
            textwrap.dedent(
                """
                import cupy as cp
                def may_raise(): pass
                def protected(flag):
                    value = None
                    try:
                        if flag:
                            value = cp
                            may_raise()
                            value = None
                    except RuntimeError:
                        value.arange(1)
                def safe(flag):
                    value = cp
                    try:
                        if flag:
                            value = None
                            may_raise()
                            value = cp
                    except RuntimeError:
                        value.arange(1)
                def multiple(flag):
                    value = None
                    try:
                        if flag:
                            value = cp
                            may_raise()
                            value = None
                        else:
                            may_raise()
                    except RuntimeError:
                        value.arange(1)
                def nested_return(flag):
                    value = None
                    try:
                        if flag:
                            value = cp
                            return
                        may_raise()
                    except RuntimeError:
                        value.arange(1)
                def nested_break(flag):
                    value = None
                    for _ in range(1):
                        try:
                            if flag:
                                value = cp
                                break
                            may_raise()
                        except RuntimeError:
                            value.arange(1)
                def nested_continue(flag):
                    value = None
                    for _ in range(1):
                        try:
                            if flag:
                                value = cp
                                continue
                            may_raise()
                        except RuntimeError:
                            value.arange(1)
                """
            )
        )
        functions = {
            node.name: node
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        }
        expected = {
            "protected": True,
            "safe": False,
            "multiple": True,
            "nested_return": False,
            "nested_break": False,
            "nested_continue": False,
        }
        for name, should_be_sensitive in expected.items():
            with self.subTest(nested_throw_site=name):
                function = functions[name]
                calls = self.generator._preclassified_sensitive_calls(
                    function.body,
                    {"cp": "cupy"},
                    self.generator._AnalysisBudget(),
                    {"may_raise": functions["may_raise"]},
                )
                handler_call = next(
                    node
                    for node in ast.walk(function)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "arange"
                )
                self.assertEqual(
                    id(handler_call) in calls,
                    should_be_sensitive,
                    f"{name} handler census did not use its exact throw state",
                )

        source = _source(
            '''
            import cupy as cp
            import unittest
            def may_raise(): pass
            class ReviewTests(unittest.TestCase):
                def test_static(self):
                    value = None
                    try:
                        if self.id():
                            value = cp
                            may_raise()
                            value = None
                    except RuntimeError:
                        value.arange(1)
                def test_denied(self): pass
            '''
        )
        try:
            review = self._review(sources={"tests/test_review.py": source})
        except self.generator.InventoryError as error:
            self.fail(f"nested throw-site census did not reconcile: {error}")
        self.assertFalse(
            any(
                "absent from the independent census" in row["reason"]
                for row in review["unresolved_dynamic_blockers"]
            )
        )

    def _round6_preclassifier_transforms_finally_and_suppress_exits(self) -> None:
        module = ast.parse(
            textwrap.dedent(
                """
                import contextlib
                import cupy as cp
                def may_raise(): pass
                async def may_raise_async(): pass
                def finally_normal():
                    value = None
                    try:
                        pass
                    finally:
                        value = cp
                    value.arange(1)
                def finally_raise():
                    value = None
                    try:
                        try:
                            raise RuntimeError()
                        finally:
                            value = cp
                    except RuntimeError:
                        value.arange(1)
                def finally_return():
                    value = None
                    try:
                        try:
                            return
                        finally:
                            value = cp
                    finally:
                        value.arange(1)
                def finally_break():
                    value = None
                    for _ in range(1):
                        try:
                            try:
                                break
                            finally:
                                value = cp
                        finally:
                            value.arange(1)
                def finally_continue():
                    value = None
                    for _ in range(1):
                        try:
                            try:
                                continue
                            finally:
                                value = cp
                        finally:
                            value.arange(1)
                def override_raise():
                    value = None
                    try:
                        try:
                            return
                        finally:
                            value = cp
                            raise RuntimeError()
                    except RuntimeError:
                        value.arange(1)
                def override_return():
                    value = None
                    try:
                        try:
                            raise RuntimeError()
                        finally:
                            value = cp
                            return
                    finally:
                        value.arange(1)
                def override_break():
                    value = None
                    for _ in range(1):
                        try:
                            raise RuntimeError()
                        finally:
                            value = cp
                            break
                    value.arange(1)
                def override_continue():
                    value = None
                    for _ in range(1):
                        try:
                            raise RuntimeError()
                        finally:
                            value = cp
                            continue
                    value.arange(1)
                def finally_clears_raise():
                    value = cp
                    try:
                        try:
                            may_raise()
                        finally:
                            value = None
                    except RuntimeError:
                        value.arange(1)
                def suppress_call():
                    value = None
                    with contextlib.suppress(RuntimeError):
                        value = cp
                        may_raise()
                        value = None
                    value.arange(1)
                async def suppress_await():
                    value = None
                    with contextlib.suppress(RuntimeError):
                        value = cp
                        await may_raise_async()
                        value = None
                    value.arange(1)
                def suppress_yield():
                    value = None
                    with contextlib.suppress(RuntimeError):
                        value = cp
                        yield 1
                        value = None
                    value.arange(1)
                """
            )
        )
        functions = {
            node.name: node
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        expected = {
            "finally_normal": True,
            "finally_raise": True,
            "finally_return": True,
            "finally_break": True,
            "finally_continue": True,
            "override_raise": True,
            "override_return": True,
            "override_break": True,
            "override_continue": True,
            "finally_clears_raise": False,
            "suppress_call": True,
            "suppress_await": True,
            "suppress_yield": True,
        }
        for name, should_be_sensitive in expected.items():
            with self.subTest(finally_or_suppress=name):
                function = functions[name]
                calls = self.generator._preclassified_sensitive_calls(
                    function.body,
                    {"contextlib": "contextlib", "cp": "cupy"},
                    self.generator._AnalysisBudget(),
                    functions,
                )
                observer = next(
                    node
                    for node in ast.walk(function)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "arange"
                )
                self.assertEqual(
                    id(observer) in calls,
                    should_be_sensitive,
                    f"{name} did not preserve exact final/suppressed state",
                )

        reconciliation_sources = {
            "finally-clears-handler": _source(
                '''
                import cupy as cp
                import unittest
                def may_raise(): pass
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        value = cp
                        try:
                            try:
                                may_raise()
                            finally:
                                value = None
                        except RuntimeError:
                            value.arange(1)
                    def test_denied(self): pass
                '''
            ),
            "finally-adds-sensitive-call": _source(
                '''
                import cupy as cp
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        try:
                            raise RuntimeError()
                        finally:
                            cp.arange(1)
                    def test_denied(self): pass
                '''
            ),
            "suppress-exceptional-receiver": _source(
                '''
                import contextlib
                import cupy as cp
                import unittest
                def may_raise(): pass
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        value = None
                        with contextlib.suppress(RuntimeError):
                            value = cp
                            may_raise()
                            value = None
                        value.arange(1)
                    def test_denied(self): pass
                '''
            ),
        }
        for label, source in reconciliation_sources.items():
            with self.subTest(finally_or_suppress_reconciliation=label):
                try:
                    review = self._review(sources={"tests/test_review.py": source})
                except self.generator.InventoryError as error:
                    self.fail(f"{label} census did not reconcile: {error}")
                self.assertFalse(
                    any(
                        "absent from the independent census" in row["reason"]
                        for row in review["unresolved_dynamic_blockers"]
                    )
                )

    def _round7_preclassifier_governs_every_try_suite_throw(self) -> None:
        throw_statements = {
            "call": "may_raise()",
            "await": "await may_raise_async()",
            "yield": "yield from may_raise_gen()",
        }

        def scenario_body(
            region: str,
            throw_kind: str,
            final_sensitive: bool,
        ) -> str:
            initial = "None" if final_sensitive else "cp"
            final = "cp" if final_sensitive else "None"
            throw = throw_statements[throw_kind]
            if region == "body":
                inner = f"try:\n    {throw}\nfinally:\n    value = {final}"
            elif region == "first_handler":
                inner = (
                    "try:\n"
                    "    raise LookupError\n"
                    "except LookupError:\n"
                    f"    {throw}\n"
                    "except RuntimeError:\n"
                    "    pass\n"
                    "finally:\n"
                    f"    value = {final}"
                )
            elif region == "second_handler":
                inner = (
                    "try:\n"
                    "    raise LookupError\n"
                    "except RuntimeError:\n"
                    "    pass\n"
                    "except LookupError:\n"
                    f"    {throw}\n"
                    "finally:\n"
                    f"    value = {final}"
                )
            elif region == "else":
                inner = (
                    "try:\n"
                    "    pass\n"
                    "except RuntimeError:\n"
                    "    pass\n"
                    "else:\n"
                    f"    {throw}\n"
                    "finally:\n"
                    f"    value = {final}"
                )
            else:
                raise AssertionError(f"unknown try suite {region}")
            return (
                f"value = {initial}\n"
                "try:\n"
                f"{textwrap.indent(inner, '    ')}\n"
                "except RuntimeError:\n"
                "    value.arange(1)"
            )

        def nested_body(throw_kind: str, final_sensitive: bool) -> str:
            initial = "None" if final_sensitive else "cp"
            final = "cp" if final_sensitive else "None"
            throw = throw_statements[throw_kind]
            return (
                f"value = {initial}\n"
                f"observed = {initial}\n"
                "try:\n"
                "    try:\n"
                "        try:\n"
                "            pass\n"
                "        except RuntimeError:\n"
                "            pass\n"
                "        else:\n"
                f"            {throw}\n"
                "        finally:\n"
                f"            value = {final}\n"
                "    finally:\n"
                "        observed = value\n"
                "except RuntimeError:\n"
                "    observed.arange(1)"
            )

        handled_controls = {
            "bare_handler": (
                "value = cp\n"
                "with contextlib.suppress(RuntimeError):\n"
                "    try:\n"
                "        may_raise()\n"
                "    except:\n"
                "        value = None\n"
                "    else:\n"
                "        value = None\n"
                "value.arange(1)"
            ),
            "typed_handler": (
                "value = cp\n"
                "with contextlib.suppress(RuntimeError):\n"
                "    try:\n"
                "        may_raise()\n"
                "    except RuntimeError:\n"
                "        value = None\n"
                "    else:\n"
                "        value = None\n"
                "value.arange(1)"
            ),
            "multiple_handlers": (
                "value = cp\n"
                "with contextlib.suppress(RuntimeError):\n"
                "    try:\n"
                "        may_raise()\n"
                "    except LookupError:\n"
                "        value = None\n"
                "    except RuntimeError:\n"
                "        value = None\n"
                "    else:\n"
                "        value = None\n"
                "value.arange(1)"
            ),
            "nested_suppress": (
                "value = cp\n"
                "observed = cp\n"
                "with contextlib.suppress(RuntimeError):\n"
                "    try:\n"
                "        try:\n"
                "            may_raise()\n"
                "        except RuntimeError:\n"
                "            value = None\n"
                "        else:\n"
                "            value = None\n"
                "    finally:\n"
                "        observed = value\n"
                "observed.arange(1)"
            ),
        }
        cases: list[tuple[str, str, bool]] = []
        for throw_kind in throw_statements:
            for region in ("body", "first_handler", "second_handler", "else"):
                for final_sensitive in (True, False):
                    cases.append(
                        (
                            f"{region}_{throw_kind}_{'sensitive' if final_sensitive else 'safe'}",
                            scenario_body(region, throw_kind, final_sensitive),
                            final_sensitive,
                        )
                    )
            for final_sensitive in (True, False):
                cases.append(
                    (
                        f"nested_{throw_kind}_{'sensitive' if final_sensitive else 'safe'}",
                        nested_body(throw_kind, final_sensitive),
                        final_sensitive,
                    )
                )
        cases.extend((name, body, False) for name, body in handled_controls.items())

        for name, body, should_be_sensitive in cases:
            declaration = "async def" if "_await_" in f"_{name}_" else "def"
            direct_source = (
                "import contextlib\n"
                "import cupy as cp\n"
                "def may_raise(): pass\n"
                "async def may_raise_async(): pass\n"
                "def may_raise_gen(): yield 1\n"
                f"{declaration} scenario():\n"
                f"{textwrap.indent(body, '    ')}\n"
            )
            module = ast.parse(direct_source)
            functions = {
                node.name: node
                for node in module.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            scenario = functions["scenario"]
            observer = next(
                node
                for node in ast.walk(scenario)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "arange"
            )
            with self.subTest(finally_suite_throw=name):
                calls = self.generator._preclassified_sensitive_calls(
                    scenario.body,
                    {"contextlib": "contextlib", "cp": "cupy"},
                    self.generator._AnalysisBudget(),
                    functions,
                )
                self.assertEqual(
                    id(observer) in calls,
                    should_be_sensitive,
                    f"{name} did not transform its exceptional successor once",
                )

                resolved = self.generator._source_ordered_review_flow(
                    scenario,
                    {"contextlib": "contextlib", "cp": "cupy"},
                    {},
                    functions,
                    budget=self.generator._AnalysisBudget(),
                )
                self.assertEqual(
                    resolved.callables_by_call.get(id(observer)) == "cupy.arange",
                    should_be_sensitive,
                    f"{name} primary resolver expectation changed",
                )
                if "_yield_" in f"_{name}_":
                    continue

                review_source = (
                    "import contextlib\n"
                    "import cupy as cp\n"
                    "import unittest\n"
                    "def may_raise(): pass\n"
                    "async def may_raise_async(): pass\n"
                    "def may_raise_gen(): yield 1\n"
                    "class ReviewTests(unittest.TestCase):\n"
                    f"    {declaration} test_static(self):\n"
                    f"{textwrap.indent(body, '        ')}\n"
                    "    def test_denied(self): pass\n"
                )
                try:
                    review = self._review(
                        sources={"tests/test_review.py": _source(review_source)}
                    )
                except self.generator.InventoryError as error:
                    self.fail(f"{name} census did not reconcile: {error}")
                observer_rows = [
                    row
                    for row in review["receipt"]["expanded_rows"]
                    if row["item_id"] == self.static_id
                    and row.get("qualified_name") == "cupy.arange"
                ]
                self.assertEqual(
                    len(observer_rows),
                    1 if should_be_sensitive else 0,
                    f"{name} produced a missing or duplicate observer row",
                )

    def _round9_explicit_raises_respect_typed_handler_order(self) -> None:
        cases = {
            "definite-nonmatch-reaches-outer": (
                "try:\n"
                "    try:\n"
                "        raise RuntimeError()\n"
                "    except ValueError:\n"
                "        value = None\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "definite-match-is-consumed": (
                "try:\n"
                "    raise RuntimeError()\n"
                "except RuntimeError:\n"
                "    value = None\n"
                "value.arange(1)",
                False,
            ),
            "later-handler-matches": (
                "try:\n"
                "    raise RuntimeError\n"
                "except ValueError:\n"
                "    pass\n"
                "except RuntimeError:\n"
                "    value = None\n"
                "value.arange(1)",
                False,
            ),
            "tuple-matches": (
                "try:\n"
                "    raise RuntimeError()\n"
                "except (ValueError, RuntimeError):\n"
                "    value = None\n"
                "value.arange(1)",
                False,
            ),
            "tuple-nonmatch-reaches-outer": (
                "try:\n"
                "    try:\n"
                "        raise RuntimeError()\n"
                "    except (ValueError, KeyError):\n"
                "        value = None\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "bare-consumes": (
                "try:\n"
                "    raise RuntimeError()\n"
                "except:\n"
                "    value = None\n"
                "value.arange(1)",
                False,
            ),
            "broad-builtins-consume": (
                "try:\n"
                "    raise RuntimeError()\n"
                "except (BaseException, Exception):\n"
                "    value = None\n"
                "value.arange(1)",
                False,
            ),
            "unknown-forks-unmatched-successor": (
                "try:\n"
                "    try:\n"
                "        raise make_error()\n"
                "    except ValueError:\n"
                "        value = None\n"
                "except BaseException:\n"
                "    value.arange(1)",
                True,
            ),
        }
        for label, (body, should_be_sensitive) in cases.items():
            with self.subTest(explicit_raise_handler=label):
                source = (
                    "import cupy as cp\n"
                    "def make_error(): return RuntimeError()\n"
                    "def scenario():\n"
                    "    value = cp\n"
                    f"{textwrap.indent(body, '    ')}\n"
                )
                module = ast.parse(source)
                functions = {
                    node.name: node
                    for node in module.body
                    if isinstance(node, ast.FunctionDef)
                }
                scenario = functions["scenario"]
                observer = next(
                    node
                    for node in ast.walk(scenario)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "arange"
                )
                census = self.generator._preclassified_sensitive_calls(
                    scenario.body,
                    {"cp": "cupy"},
                    self.generator._AnalysisBudget(),
                    functions,
                )
                resolved = self.generator._source_ordered_review_flow(
                    scenario,
                    {"cp": "cupy"},
                    {},
                    functions,
                    budget=self.generator._AnalysisBudget(),
                )
                self.assertEqual(
                    id(observer) in census,
                    should_be_sensitive,
                    f"{label} preclassifier routed the explicit raise incorrectly",
                )
                self.assertEqual(
                    resolved.callables_by_call.get(id(observer)) == "cupy.arange",
                    should_be_sensitive,
                    f"{label} primary resolver disagreed with runtime handler order",
                )

                review_source = (
                    "import cupy as cp\n"
                    "import unittest\n"
                    "def make_error(): return RuntimeError()\n"
                    "class ReviewTests(unittest.TestCase):\n"
                    "    def test_static(self):\n"
                    "        value = cp\n"
                    f"{textwrap.indent(body, '        ')}\n"
                    "    def test_denied(self): pass\n"
                )
                try:
                    review = self._review(
                        sources={"tests/test_review.py": _source(review_source)}
                    )
                except self.generator.InventoryError as error:
                    self.fail(f"{label} explicit-raise census did not reconcile: {error}")
                self.assertFalse(
                    any(
                        "absent from the independent census" in row["reason"]
                        for row in review["unresolved_dynamic_blockers"]
                    ),
                    f"{label} left a resolved sensitive site uncensused",
                )

    def _round10_typed_handlers_require_proven_builtin_names(self) -> None:
        cases = {
            "local-exception-shadow": (
                "",
                "cp",
                "self",
                "Exception = ValueError\n"
                "try:\n"
                "    raise RuntimeError()\n"
                "except Exception:\n"
                "    value = None\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "local-baseexception-shadow": (
                "",
                "cp",
                "self",
                "BaseException = ValueError\n"
                "try:\n"
                "    raise RuntimeError()\n"
                "except BaseException:\n"
                "    value = None\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "tuple-element-shadow": (
                "",
                "cp",
                "self",
                "Exception = ValueError\n"
                "try:\n"
                "    raise RuntimeError()\n"
                "except (KeyError, Exception):\n"
                "    value = None\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "parameter-shadow": (
                "",
                "cp, Exception=ValueError",
                "self, Exception=ValueError",
                "try:\n"
                "    raise RuntimeError()\n"
                "except Exception:\n"
                "    value = None\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "import-shadow": (
                "",
                "cp",
                "self",
                "from builtins import ValueError as Exception\n"
                "try:\n"
                "    raise RuntimeError()\n"
                "except Exception:\n"
                "    value = None\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "global-shadow": (
                "Exception = ValueError\n",
                "cp",
                "self",
                "global Exception\n"
                "try:\n"
                "    raise RuntimeError()\n"
                "except Exception:\n"
                "    value = None\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "raised-side-shadow": (
                "",
                "cp",
                "self",
                "RuntimeError = ValueError\n"
                "try:\n"
                "    try:\n"
                "        raise RuntimeError()\n"
                "    except KeyError:\n"
                "        value = None\n"
                "except ValueError:\n"
                "    value.arange(1)",
                True,
            ),
            "unshadowed-broad-control": (
                "",
                "cp",
                "self",
                "try:\n"
                "    raise RuntimeError()\n"
                "except Exception:\n"
                "    value = None\n"
                "value.arange(1)",
                False,
            ),
        }

        def exercise(
            label: str,
            module_prefix: str,
            signature: str,
            review_signature: str,
            body: str,
            should_be_sensitive: bool,
            *,
            runtime_source: str | None = None,
            review_source: str | None = None,
        ) -> None:
            body = body.replace("value = None", "value = safe")
            supplied_runtime = runtime_source or (
                f"{module_prefix}"
                f"def scenario({signature}):\n"
                "    value = cp\n"
                f"{textwrap.indent(body, '    ')}\n"
                "def run(cp):\n"
                "    return scenario(cp)\n"
            )
            module = ast.parse(supplied_runtime)
            scenario = next(
                node
                for node in ast.walk(module)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "scenario"
            )
            observer = next(
                node
                for node in ast.walk(scenario)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "arange"
            )
            functions = {
                node.name: node
                for node in ast.walk(module)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            module_assignments = self.generator._static_assignments(module.body)
            preclassifier_keywords: dict[str, object] = {}
            parameter_names = (
                self.generator._preclassified_sensitive_calls.__code__.co_varnames
            )
            if "scope_node" in parameter_names:
                preclassifier_keywords["scope_node"] = scenario
            if "module_bound_names" in parameter_names:
                preclassifier_keywords["module_bound_names"] = frozenset(
                    module_assignments
                )
            census = self.generator._preclassified_sensitive_calls(
                scenario.body,
                {"cp": "cupy"},
                self.generator._AnalysisBudget(),
                functions,
                **preclassifier_keywords,
            )
            resolved = self.generator._source_ordered_review_flow(
                scenario,
                {"cp": "cupy"},
                module_assignments,
                functions,
                budget=self.generator._AnalysisBudget(),
            )

            observed: list[int] = []

            class RuntimeCuPy:
                @staticmethod
                def arange(value: int) -> None:
                    observed.append(value)

            class RuntimeSafe:
                @staticmethod
                def arange(value: int) -> None:
                    return None

            namespace: dict[str, object] = {"safe": RuntimeSafe()}
            exec(compile(supplied_runtime, f"<{label}>", "exec"), namespace)
            namespace["run"](RuntimeCuPy())

            supplied_review = review_source or (
                "import cupy as cp\n"
                "import unittest\n"
                f"{module_prefix}"
                "class ReviewTests(unittest.TestCase):\n"
                f"    def test_static({review_signature}):\n"
                "        value = cp\n"
                f"{textwrap.indent(body, '        ')}\n"
                "    def test_denied(self): pass\n"
            )
            review_error: str | None = None
            review_rows: list[dict[str, object]] = []
            review_blockers: list[dict[str, object]] = []
            try:
                review = self._review(
                    sources={"tests/test_review.py": _source(supplied_review)}
                )
            except self.generator.InventoryError as error:
                review_error = str(error)
            else:
                review_rows = [
                    row
                    for row in review["receipt"]["expanded_rows"]
                    if row["item_id"] == self.static_id
                    and row.get("qualified_name") == "cupy.arange"
                ]
                review_blockers = [
                    row
                    for row in review["unresolved_dynamic_blockers"]
                    if "absent from the independent census" in row["reason"]
                ]
            actual = (
                bool(observed),
                id(observer) in census,
                resolved.callables_by_call.get(id(observer)) == "cupy.arange",
                len(review_rows) == 1,
                review_error is None
                and not review_blockers
                and len(review_rows) <= 1,
            )
            self.assertEqual(
                actual,
                (should_be_sensitive,) * 4 + (True,),
                f"{label} runtime/analyzer/reconciliation divergence: "
                f"error={review_error!r}, blockers={review_blockers!r}",
            )

        for label, supplied in cases.items():
            with self.subTest(exception_provenance=label):
                exercise(label, *supplied)

        nonlocal_body = (
            "try:\n"
            "    raise RuntimeError()\n"
            "except Exception:\n"
            "    value = None\n"
            "except RuntimeError:\n"
            "    cp.arange(1)"
        )
        nonlocal_runtime = (
            "def make_scenario():\n"
            "    Exception = ValueError\n"
            "    def scenario(cp):\n"
            "        nonlocal Exception\n"
            "        value = cp\n"
            f"{textwrap.indent(nonlocal_body, '        ')}\n"
            "    return scenario\n"
            "def run(cp):\n"
            "    return make_scenario()(cp)\n"
        )
        nonlocal_review = (
            "import cupy as cp\n"
            "import unittest\n"
            "class ReviewTests(unittest.TestCase):\n"
            "    def test_static(self):\n"
            "        Exception = ValueError\n"
            "        def scenario():\n"
            "            nonlocal Exception\n"
            "            value = cp\n"
            f"{textwrap.indent(nonlocal_body, '            ')}\n"
            "        scenario()\n"
            "    def test_denied(self): pass\n"
        )
        with self.subTest(exception_provenance="nonlocal-shadow"):
            exercise(
                "nonlocal-shadow",
                "",
                "cp",
                "self",
                nonlocal_body,
                True,
                runtime_source=nonlocal_runtime,
                review_source=nonlocal_review,
            )

    def _round10_typed_handler_validation_and_raise_exits(self) -> None:
        cases = {
            "invalid-constant": (
                "",
                "try:\n"
                "    try:\n"
                "        raise RuntimeError()\n"
                "    except 1:\n"
                "        value = None\n"
                "except TypeError:\n"
                "    value.arange(1)",
                True,
            ),
            "invalid-tuple-after-match": (
                "",
                "try:\n"
                "    try:\n"
                "        raise RuntimeError()\n"
                "    except (RuntimeError, 1):\n"
                "        value = None\n"
                "except TypeError:\n"
                "    value.arange(1)",
                True,
            ),
            "invalid-tuple-before-match": (
                "",
                "try:\n"
                "    try:\n"
                "        raise RuntimeError()\n"
                "    except (1, RuntimeError):\n"
                "        value = None\n"
                "except TypeError:\n"
                "    value.arange(1)",
                True,
            ),
            "dynamic-invalid-target": (
                "",
                "not_an_exception = 1\n"
                "try:\n"
                "    try:\n"
                "        raise RuntimeError()\n"
                "    except not_an_exception:\n"
                "        value = None\n"
                "except TypeError:\n"
                "    value.arange(1)",
                True,
            ),
            "valid-handler-control": (
                "",
                "try:\n"
                "    raise RuntimeError()\n"
                "except (ValueError, RuntimeError):\n"
                "    value = None\n"
                "value.arange(1)",
                False,
            ),
            "raise-argument-evaluation": (
                "def factory():\n    raise KeyError()\n",
                "try:\n"
                "    try:\n"
                "        raise RuntimeError(factory())\n"
                "    except RuntimeError:\n"
                "        value = None\n"
                "except KeyError:\n"
                "    value.arange(1)",
                True,
            ),
            "raise-cause-evaluation": (
                "def factory():\n    raise KeyError()\n",
                "try:\n"
                "    try:\n"
                "        raise RuntimeError() from factory()\n"
                "    except RuntimeError:\n"
                "        value = None\n"
                "except KeyError:\n"
                "    value.arange(1)",
                True,
            ),
            "simple-raise-constructor-control": (
                "",
                "try:\n"
                "    try:\n"
                "        raise RuntimeError()\n"
                "    except RuntimeError:\n"
                "        value = None\n"
                "except KeyError:\n"
                "    value.arange(1)",
                False,
            ),
            "body-explicit-raise": (
                "",
                "try:\n"
                "    raise RuntimeError\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "handler-explicit-raise": (
                "",
                "try:\n"
                "    try:\n"
                "        raise KeyError\n"
                "    except KeyError:\n"
                "        raise RuntimeError\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "handler-explicit-raise-inverse": (
                "",
                "try:\n"
                "    try:\n"
                "        raise KeyError\n"
                "    except KeyError:\n"
                "        raise ValueError\n"
                "except RuntimeError:\n"
                "    value.arange(1)\n"
                "except ValueError:\n"
                "    value = None",
                False,
            ),
            "else-explicit-raise": (
                "",
                "try:\n"
                "    try:\n"
                "        pass\n"
                "    except KeyError:\n"
                "        pass\n"
                "    else:\n"
                "        raise RuntimeError\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "else-explicit-raise-inverse": (
                "",
                "try:\n"
                "    try:\n"
                "        pass\n"
                "    except KeyError:\n"
                "        pass\n"
                "    else:\n"
                "        raise ValueError\n"
                "except RuntimeError:\n"
                "    value.arange(1)\n"
                "except ValueError:\n"
                "    value = None",
                False,
            ),
            "finally-explicit-raise": (
                "",
                "try:\n"
                "    try:\n"
                "        raise KeyError\n"
                "    finally:\n"
                "        raise RuntimeError\n"
                "except RuntimeError:\n"
                "    value.arange(1)",
                True,
            ),
            "finally-explicit-raise-inverse": (
                "",
                "try:\n"
                "    try:\n"
                "        raise KeyError\n"
                "    finally:\n"
                "        raise ValueError\n"
                "except RuntimeError:\n"
                "    value.arange(1)\n"
                "except ValueError:\n"
                "    value = None",
                False,
            ),
        }
        for label, (module_prefix, body, should_be_sensitive) in cases.items():
            with self.subTest(exception_validation_or_exit=label):
                body = body.replace("value = None", "value = safe")
                runtime_source = (
                    f"{module_prefix}"
                    "def scenario(cp):\n"
                    "    value = cp\n"
                    f"{textwrap.indent(body, '    ')}\n"
                    "def run(cp):\n"
                    "    return scenario(cp)\n"
                )
                review_source = (
                    "import cupy as cp\n"
                    "import unittest\n"
                    f"{module_prefix}"
                    "class ReviewTests(unittest.TestCase):\n"
                    "    def test_static(self):\n"
                    "        value = cp\n"
                    f"{textwrap.indent(body, '        ')}\n"
                    "    def test_denied(self): pass\n"
                )
                module = ast.parse(runtime_source)
                scenario = next(
                    node
                    for node in module.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "scenario"
                )
                observer = next(
                    node
                    for node in ast.walk(scenario)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "arange"
                )
                functions = {
                    node.name: node
                    for node in module.body
                    if isinstance(node, ast.FunctionDef)
                }
                preclassifier_keywords: dict[str, object] = {}
                parameter_names = (
                    self.generator._preclassified_sensitive_calls.__code__.co_varnames
                )
                if "scope_node" in parameter_names:
                    preclassifier_keywords["scope_node"] = scenario
                census = self.generator._preclassified_sensitive_calls(
                    scenario.body,
                    {"cp": "cupy"},
                    self.generator._AnalysisBudget(),
                    functions,
                    **preclassifier_keywords,
                )
                resolved = self.generator._source_ordered_review_flow(
                    scenario,
                    {"cp": "cupy"},
                    {},
                    functions,
                    budget=self.generator._AnalysisBudget(),
                )
                observed: list[int] = []

                class RuntimeCuPy:
                    @staticmethod
                    def arange(value: int) -> None:
                        observed.append(value)

                class RuntimeSafe:
                    @staticmethod
                    def arange(value: int) -> None:
                        return None

                namespace: dict[str, object] = {"safe": RuntimeSafe()}
                exec(compile(runtime_source, f"<{label}>", "exec"), namespace)
                namespace["run"](RuntimeCuPy())
                review_error: str | None = None
                review_rows: list[dict[str, object]] = []
                review_blockers: list[dict[str, object]] = []
                try:
                    review = self._review(
                        sources={"tests/test_review.py": _source(review_source)}
                    )
                except self.generator.InventoryError as error:
                    review_error = str(error)
                else:
                    review_rows = [
                        row
                        for row in review["receipt"]["expanded_rows"]
                        if row["item_id"] == self.static_id
                        and row.get("qualified_name") == "cupy.arange"
                    ]
                    review_blockers = [
                        row
                        for row in review["unresolved_dynamic_blockers"]
                        if "absent from the independent census" in row["reason"]
                    ]
                actual = (
                    bool(observed),
                    id(observer) in census,
                    resolved.callables_by_call.get(id(observer)) == "cupy.arange",
                    len(review_rows) == 1,
                    review_error is None
                    and not review_blockers
                    and len(review_rows) <= 1,
                )
                self.assertEqual(
                    actual,
                    (should_be_sensitive,) * 4 + (True,),
                    f"{label} runtime/analyzer/reconciliation divergence: "
                    f"error={review_error!r}, blockers={review_blockers!r}",
                )

    def test_round4_source_order_and_branch_bounds_red_contracts_are_independent(
        self,
    ) -> None:
        self._final_rereview_preclassifier_exhausts_irrefutable_match()
        self._final_rereview_preclassifier_uses_throw_site_handler_state()
        self._final2_preclassifier_tracks_nested_exact_throw_sites()
        self._round6_preclassifier_transforms_finally_and_suppress_exits()
        self._round7_preclassifier_governs_every_try_suite_throw()
        self._round9_explicit_raises_respect_typed_handler_order()
        self._round10_typed_handlers_require_proven_builtin_names()
        self._round10_typed_handler_validation_and_raise_exits()
        for label, first, second in (
            ("five-then-one", 5, 1),
            ("one-then-five", 1, 5),
        ):
            with self.subTest(loop=label):
                source = _source(
                    f'''
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            count = {first}
                            for _ in range(count):
                                cp.arange(1)
                            count = {second}
                            for _ in range(count):
                                cp.arange(1)
                        def test_denied(self): pass
                    '''
                )
                review = self._review(
                    sources={"tests/test_review.py": source}
                )
                call = next(
                    row
                    for row in review["receipt"]["expanded_rows"]
                    if row.get("qualified_name") == "cupy.arange"
                )
                self.assertEqual(call["maximum_calls"], 6)
                self.assertFalse(review["unresolved_dynamic_blockers"])

        for label, first, second in (
            ("comprehension-five-then-one", 5, 1),
            ("comprehension-one-then-five", 1, 5),
        ):
            with self.subTest(comprehension=label):
                source = _source(
                    f'''
                    import cupy as cp
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            count = {first}
                            [cp.arange(1) for _ in range(count)]
                            count = {second}
                            [cp.arange(1) for _ in range(count)]
                        def test_denied(self): pass
                    '''
                )
                review = self._review(
                    sources={"tests/test_review.py": source}
                )
                call = next(
                    row
                    for row in review["receipt"]["expanded_rows"]
                    if row.get("qualified_name") == "cupy.arange"
                )
                self.assertEqual(call["maximum_calls"], 6)
                self.assertFalse(review["unresolved_dynamic_blockers"])

        with self.subTest(branch="conditional-expression-max"):
            conditional = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                cp.arange(1) if runtime_flag() else cp.arange(1)
                            def test_denied(self): pass
                        """
                    )
                }
            )
            call = next(
                row
                for row in conditional["receipt"]["expanded_rows"]
                if row.get("qualified_name") == "cupy.arange"
            )
            self.assertEqual(call["maximum_calls"], 1)
            self.assertFalse(conditional["unresolved_dynamic_blockers"])

        with self.subTest(round5_source_order="finite-while-before-reassignment"):
            finite_while = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                remaining = 1
                                while remaining:
                                    cp.arange(1)
                                    remaining = 0
                            def test_denied(self): pass
                        """
                    )
                }
            )
            call = next(
                row
                for row in finite_while["receipt"]["expanded_rows"]
                if row.get("qualified_name") == "cupy.arange"
            )
            self.assertEqual(call["maximum_calls"], 1)
            self.assertFalse(finite_while["unresolved_dynamic_blockers"])

        with self.subTest(round5_effect="if-expression-walrus"):
            conditional_walrus = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                ((backend := cp) if runtime_flag() else (backend := cp))
                                backend.arange(1)
                            def test_denied(self): pass
                        """
                    )
                }
            )
            call = next(
                row
                for row in conditional_walrus["receipt"]["expanded_rows"]
                if row.get("qualified_name") == "cupy.arange"
            )
            self.assertEqual(call["maximum_calls"], 1)
            self.assertFalse(conditional_walrus["unresolved_dynamic_blockers"])

        with self.subTest(round5_effect="comprehension-walrus"):
            comprehension_walrus = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                [(backend := cp) for _ in range(1)]
                                backend.arange(1)
                            def test_denied(self): pass
                        """
                    )
                }
            )
            call = next(
                row
                for row in comprehension_walrus["receipt"]["expanded_rows"]
                if row.get("qualified_name") == "cupy.arange"
            )
            self.assertEqual(call["maximum_calls"], 1)
            self.assertFalse(comprehension_walrus["unresolved_dynamic_blockers"])

        with self.subTest(round5_rereview="zero-iteration-walrus-retains-alias"):
            zero_walrus = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import subprocess
                        import sys
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                launch = subprocess.run
                                [(launch := print) for _ in range(0)]
                                launch(
                                    [sys.executable, "-m", "zero-walrus"],
                                    timeout=5,
                                    check=False,
                                )
                            def test_denied(self): pass
                        """
                    )
                }
            )
            processes = [
                row
                for row in zero_walrus["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            ]
            self.assertEqual(
                [row["argv"] for row in processes],
                [["-m", "zero-walrus"]],
            )
            self.assertFalse(zero_walrus["unresolved_dynamic_blockers"])

        possibly_zero_sources = (
            (
                "dynamic-cardinality",
                "[(launch := print) for _ in dynamic_values()]",
            ),
            (
                "filter-dependent",
                "[(launch := print) for _ in range(1) if runtime_flag()]",
            ),
        )
        for label, expression in possibly_zero_sources:
            with self.subTest(round5_rereview_walrus=label):
                source = _source(
                    f'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            launch = subprocess.run
                            {expression}
                            launch(
                                [sys.executable, "-m", "ambiguous-walrus"],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
                review = self._review(sources={"tests/test_review.py": source})
                self.assertFalse(review["receipt"]["expanded_rows"])
                self.assertEqual(
                    review["unresolved_dynamic_blockers"],
                    [
                        {
                            "item_id": self.static_id,
                            "relative_path": "tests/test_review.py",
                            "line": 8,
                            "reason": "callable alias is dynamically unresolved",
                        }
                    ],
                )

        with self.subTest(round5_rereview="continue-prevents-while-proof"):
            review = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                remaining = 1
                                while remaining:
                                    cp.arange(1)
                                    continue
                                    remaining = 0
                            def test_denied(self): pass
                        """
                    )
                }
            )
            self.assertFalse(review["receipt"]["expanded_rows"])
            self.assertEqual(
                review["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 7,
                        "reason": "dynamic repetition prevents a finite call bound",
                    }
                ],
            )

        with self.subTest(round5_rereview="protected-while-condition-repeats"):
            review = self._review(
                sources={
                    "tests/test_review.py": _source(
                        """
                        import cupy as cp
                        import unittest
                        class ReviewTests(unittest.TestCase):
                            def test_static(self):
                                while cp.arange(1):
                                    pass
                            def test_denied(self): pass
                        """
                    )
                }
            )
            self.assertFalse(review["receipt"]["expanded_rows"])
            self.assertEqual(
                review["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 5,
                        "reason": "dynamic repetition prevents a finite call bound",
                    }
                ],
            )

        terminating_compounds = (
            (
                "if",
                """
                if runtime_flag():
                    return
                else:
                    raise RuntimeError
                cp.arange(1)
                """,
            ),
            (
                "match",
                """
                match runtime_value():
                    case 0:
                        return
                    case _:
                        raise RuntimeError
                cp.arange(1)
                """,
            ),
            (
                "try",
                """
                try:
                    return
                except RuntimeError:
                    raise
                cp.arange(1)
                """,
            ),
            (
                "loop-branch",
                """
                for _ in range(1):
                    if runtime_flag():
                        break
                    else:
                        continue
                    cp.arange(1)
                """,
            ),
        )
        for label, body in terminating_compounds:
            with self.subTest(round5_rereview2_successors=label):
                indented = textwrap.indent(_source(body).decode("utf-8"), " " * 8)
                source = (
                    "import cupy as cp\n"
                    "import unittest\n"
                    "class ReviewTests(unittest.TestCase):\n"
                    "    def test_static(self):\n"
                    f"{indented}"
                    "    def test_denied(self): pass\n"
                ).encode("utf-8")
                review = self._review(sources={"tests/test_review.py": source})
                self.assertFalse(review["receipt"]["expanded_rows"])
                self.assertFalse(review["unresolved_dynamic_blockers"])

        with self.subTest(round5_rereview3_successor="with-suppression"):
            source = _source(
                """
                import contextlib
                import cupy as cp
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        with contextlib.suppress(RuntimeError):
                            raise RuntimeError
                        cp.arange(1)
                    def test_denied(self): pass
                """
            )
            review = self._review(sources={"tests/test_review.py": source})
            calls = [
                row
                for row in review["receipt"]["expanded_rows"]
                if row["capability_kind"] == "call"
            ]
            self.assertEqual(
                [
                    (row["qualified_name"], row["maximum_calls"])
                    for row in calls
                ],
                [("cupy.arange", 1)],
            )
            self.assertFalse(review["unresolved_dynamic_blockers"])

        with_control_transfers = (
            (
                "return",
                "with manager():\n    return\nprobe()\n",
            ),
            (
                "break",
                "for _ in range(1):\n"
                "    with manager():\n"
                "        break\n"
                "    probe()\n",
            ),
            (
                "continue",
                "for _ in range(1):\n"
                "    with manager():\n"
                "        continue\n"
                "    probe()\n",
            ),
        )
        for label, source_text in with_control_transfers:
            with self.subTest(round5_rereview4_runtime_transfer=label):
                statements = ast.parse(source_text).body
                probe = next(
                    candidate
                    for statement in statements
                    for candidate in ast.walk(statement)
                    if isinstance(candidate, ast.Call)
                    and isinstance(candidate.func, ast.Name)
                    and candidate.func.id == "probe"
                )
                counts, dynamic = self.generator._runtime_call_bounds(
                    statements,
                    {id(probe): b"sink"},
                    assignments={},
                    relative_path="tests/test_review.py",
                    aliases={},
                    helper_registry={},
                )
                self.assertEqual(counts, {})
                self.assertEqual(dynamic, set())

        with self.subTest(round5_rereview4_helper="with-return"):
            source = _source(
                """
                import contextlib
                import subprocess
                import sys
                import unittest
                def runner():
                    with contextlib.nullcontext():
                        return subprocess.run
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        launch = runner()
                        launch(
                            [sys.executable, "-m", "with-returned"],
                            timeout=5,
                            check=False,
                        )
                    def test_denied(self): pass
                """
            )
            review = self._review(sources={"tests/test_review.py": source})
            processes = [
                row
                for row in review["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            ]
            self.assertEqual(
                [row["argv"] for row in processes],
                [["-m", "with-returned"]],
            )
            self.assertFalse(review["unresolved_dynamic_blockers"])

    def test_round4_exception_environment_red_contracts_are_independent(self) -> None:
        direct_cases = (
            (
                "deterministic",
                _source(
                    """
                    import os
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            environment = os.environ.copy()
                            try:
                                environment["MODE"] = "raised"
                                raise RuntimeError
                            except RuntimeError:
                                subprocess.run(
                                    [sys.executable, "-m", "handler"],
                                    env=environment,
                                    timeout=5,
                                    check=False,
                                )
                        def test_denied(self): pass
                    """
                ),
                ["-m", "handler"],
                {"MODE": "raised"},
                None,
            ),
            (
                "divergent",
                _source(
                    """
                    import os
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            environment = os.environ.copy()
                            try:
                                if runtime_flag():
                                    environment["MODE"] = "left"
                                else:
                                    environment["MODE"] = "right"
                                raise RuntimeError
                            except RuntimeError:
                                subprocess.run(
                                    [sys.executable, "-m", "ambiguous"],
                                    env=environment,
                                    timeout=5,
                                    check=False,
                                )
                        def test_denied(self): pass
                    """
                ),
                ["-m", "ambiguous"],
                None,
                {
                    "item_id": self.static_id,
                    "relative_path": "tests/test_review.py",
                    "line": 15,
                    "reason": (
                        "subprocess environment exceptional state is ambiguous"
                    ),
                },
            ),
        )
        for label, source, argv, additions, blocker in direct_cases:
            with self.subTest(direct=label):
                review = self._review(sources={"tests/test_review.py": source})
                processes = [
                    row
                    for row in review["receipt"]["expanded_rows"]
                    if row["capability_kind"] == "subprocess"
                ]
                if blocker is None:
                    self.assertEqual([row["argv"] for row in processes], [argv])
                    self.assertEqual(processes[0]["environment_additions"], additions)
                    self.assertEqual(processes[0]["environment_removals"], [])
                    self.assertFalse(review["unresolved_dynamic_blockers"])
                else:
                    self.assertFalse(processes)
                    self.assertEqual(
                        review["unresolved_dynamic_blockers"],
                        [blocker],
                    )

        with self.subTest(round5_exception="nested-mutated-state"):
            source = _source(
                """
                import os
                import subprocess
                import sys
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        environment = os.environ.copy()
                        try:
                            if True:
                                environment["MODE"] = "nested-raised"
                                raise RuntimeError
                        except RuntimeError:
                            subprocess.run(
                                [sys.executable, "-m", "nested-handler"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                    def test_denied(self): pass
                """
            )
            review = self._review(sources={"tests/test_review.py": source})
            process = next(
                row
                for row in review["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            )
            self.assertEqual(process["argv"], ["-m", "nested-handler"])
            self.assertEqual(
                process["environment_additions"],
                {"MODE": "nested-raised"},
            )
            self.assertFalse(review["unresolved_dynamic_blockers"])

        with self.subTest(round5_rereview="ordinary-call-exception-state"):
            source = _source(
                """
                import os
                import subprocess
                import sys
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        environment = os.environ.copy()
                        try:
                            environment["MODE"] = "post-mutation"
                            might_raise()
                        except RuntimeError:
                            subprocess.run(
                                [sys.executable, "-m", "ordinary-handler"],
                                env=environment,
                                timeout=5,
                                check=False,
                            )
                    def test_denied(self): pass
                """
            )
            review = self._review(sources={"tests/test_review.py": source})
            process = next(
                row
                for row in review["receipt"]["expanded_rows"]
                if row["capability_kind"] == "subprocess"
            )
            self.assertEqual(process["argv"], ["-m", "ordinary-handler"])
            self.assertEqual(
                process["environment_additions"],
                {"MODE": "post-mutation"},
            )
            self.assertFalse(review["unresolved_dynamic_blockers"])

        header_forms = (
            ("if-test", "if might_raise():\n    pass"),
            ("while-test", "while might_raise():\n    break"),
            ("with-context", "with might_raise():\n    pass"),
            ("for-iterator", "for _ in might_raise():\n    pass"),
            (
                "match-subject",
                "match might_raise():\n    case _:\n        pass",
            ),
            (
                "match-guard",
                "match runtime_value():\n"
                "    case _ if might_raise():\n"
                "        pass",
            ),
        )
        for label, header in header_forms:
            with self.subTest(round5_rereview2_exception_header=label):
                header_block = textwrap.indent(header, " " * 12)
                source = (
                    "import os\n"
                    "import subprocess\n"
                    "import sys\n"
                    "import unittest\n"
                    "class ReviewTests(unittest.TestCase):\n"
                    "    def test_static(self):\n"
                    "        environment = os.environ.copy()\n"
                    "        try:\n"
                    f"            environment['MODE'] = {label!r}\n"
                    f"{header_block}\n"
                    "            environment['MODE'] = 'normal-only'\n"
                    "        except RuntimeError:\n"
                    "            subprocess.run(\n"
                    f"                [sys.executable, '-m', {label!r}],\n"
                    "                env=environment,\n"
                    "                timeout=5,\n"
                    "                check=False,\n"
                    "            )\n"
                    "    def test_denied(self): pass\n"
                ).encode("utf-8")
                review = self._review(sources={"tests/test_review.py": source})
                process = next(
                    row
                    for row in review["receipt"]["expanded_rows"]
                    if row["capability_kind"] == "subprocess"
                )
                self.assertEqual(process["argv"], ["-m", label])
                self.assertEqual(
                    process["environment_additions"],
                    {"MODE": label},
                )
                self.assertFalse(review["unresolved_dynamic_blockers"])

        child_cases = (
            (
                "deterministic",
                (
                    "import os, subprocess, sys\n"
                    "environment = os.environ.copy()\n"
                    "try:\n"
                    "    environment['MODE'] = 'child-raised'\n"
                    "    raise RuntimeError\n"
                    "except RuntimeError:\n"
                    "    subprocess.run([sys.executable, '-m', 'child-handler'], "
                    "env=environment, timeout=5, check=False)\n"
                ),
                ["-m", "child-handler"],
                {"MODE": "child-raised"},
                None,
            ),
            (
                "divergent",
                (
                    "import os, subprocess, sys\n"
                    "environment = os.environ.copy()\n"
                    "try:\n"
                    "    if runtime_flag():\n"
                    "        environment['MODE'] = 'left'\n"
                    "    else:\n"
                    "        environment['MODE'] = 'right'\n"
                    "    raise RuntimeError\n"
                    "except RuntimeError:\n"
                    "    subprocess.run([sys.executable, '-m', 'child-ambiguous'], "
                    "env=environment, timeout=5, check=False)\n"
                ),
                ["-m", "child-ambiguous"],
                None,
                (
                    "subprocess dynamic Python program has unresolved subprocess "
                    "environment exceptional state"
                ),
            ),
        )
        for label, program, argv, additions, blocker_reason in child_cases:
            with self.subTest(child=label):
                source = _source(
                    f'''
                    import subprocess
                    import sys
                    import unittest
                    class ReviewTests(unittest.TestCase):
                        def test_static(self):
                            program = {program!r}
                            subprocess.run(
                                [sys.executable, "-c", program],
                                timeout=5,
                                check=False,
                            )
                        def test_denied(self): pass
                    '''
                )
                review = self._review(
                    sources={"tests/test_review.py": source}
                )
                processes = [
                    row
                    for row in review["receipt"]["expanded_rows"]
                    if row["capability_kind"] == "subprocess"
                ]
                if blocker_reason is None:
                    child_process = next(row for row in processes if row["argv"] == argv)
                    parent = next(row for row in processes if row["argv"][0] == "-c")
                    self.assertEqual(
                        child_process["environment_additions"],
                        additions,
                    )
                    self.assertTrue(parent["fixed_descendant_permission"])
                    self.assertFalse(review["unresolved_dynamic_blockers"])
                else:
                    self.assertFalse(processes)
                    self.assertEqual(
                        review["unresolved_dynamic_blockers"],
                        [
                            {
                                "item_id": self.static_id,
                                "relative_path": "tests/test_review.py",
                                "line": 7,
                                "reason": blocker_reason,
                            }
                        ],
                    )

    def test_round4_decorator_definition_point_red_contracts_are_independent(
        self,
    ) -> None:
        with self.subTest(case="later-reassignment-does-not-retroact"):
            source = _source(
                """
                import os
                import unittest
                conditional = unittest.skipIf
                class EarlierTests(unittest.TestCase):
                    @conditional(os.name == "nt", "POSIX only")
                    def test_value(self): pass
                conditional = obtain_decorator()
                """
            )
            inventory = self.generator.build_inventory(
                {"tests/test_alias.py": source},
                {"tests/test_alias.py": source},
            )
            self.assertEqual(
                inventory["entries"][0]["assignment"]["expectation"],
                {
                    "kind": "platform_conditioned",
                    "applicable_platforms": ["posix"],
                    "skip_safe_reason_code": "requires_posix",
                },
            )

        with self.subTest(case="aliased-os-condition"):
            source = _source(
                """
                import os as platform_os
                import unittest
                conditional = unittest.skipIf
                class AliasTests(unittest.TestCase):
                    @conditional(platform_os.name == "nt", "POSIX only")
                    def test_value(self): pass
                """
            )
            inventory = self.generator.build_inventory(
                {"tests/test_alias.py": source},
                {"tests/test_alias.py": source},
            )
            self.assertEqual(
                inventory["entries"][0]["assignment"]["expectation"],
                {
                    "kind": "platform_conditioned",
                    "applicable_platforms": ["posix"],
                    "skip_safe_reason_code": "requires_posix",
                },
            )

        for label, condition in (
            ("literal", "True"),
            ("aliased-os", 'platform_os.name == "nt"'),
        ):
            with self.subTest(case="retained-unknown", condition=label):
                source = _source(
                    f'''
                    import os as platform_os
                    import unittest
                    conditional = unittest.skipIf
                    if runtime_flag():
                        conditional = obtain_decorator()
                    class UnknownTests(unittest.TestCase):
                        @conditional({condition}, "possibly retained skip")
                        def test_value(self): pass
                    '''
                )
                with self.assertRaisesRegex(
                    self.generator.InventoryError,
                    "conditional skip decorator alias is unresolved",
                ):
                    self.generator.discover_test_sources(
                        {"tests/test_alias.py": source}
                    )

        rebound_sources = (
            (
                "function-definition",
                """
                import os
                import unittest
                conditional = unittest.skipIf
                def conditional(*args):
                    return lambda function: function
                class UnknownTests(unittest.TestCase):
                    @conditional(os.name == "nt", "possibly retained skip")
                    def test_value(self): pass
                """,
            ),
            (
                "import-binding",
                """
                import os
                import unittest
                conditional = unittest.skipIf
                import decorators as conditional
                class UnknownTests(unittest.TestCase):
                    @conditional(os.name == "nt", "possibly retained skip")
                    def test_value(self): pass
                """,
            ),
        )
        for label, raw_source in rebound_sources:
            with self.subTest(round5_decorator_binder=label), self.assertRaisesRegex(
                self.generator.InventoryError,
                "conditional skip decorator alias is unresolved",
            ):
                self.generator.discover_test_sources(
                    {"tests/test_alias.py": _source(raw_source)}
                )

        root_and_pattern_rebindings = (
            (
                "canonical-root-tombstone",
                """
                import os
                import unittest
                unittest = runtime_module()
                class UnknownTests(unittest.TestCase):
                    @unittest.skipIf(os.name == "nt", "possibly retained skip")
                    def test_value(self): pass
                """,
            ),
            (
                "match-star-binder",
                """
                import os
                import unittest
                conditional = unittest.skipIf
                match runtime_value():
                    case [*conditional]:
                        pass
                class UnknownTests(unittest.TestCase):
                    @conditional(os.name == "nt", "possibly retained skip")
                    def test_value(self): pass
                """,
            ),
            (
                "match-mapping-rest-binder",
                """
                import os
                import unittest
                conditional = unittest.skipIf
                match runtime_value():
                    case {**conditional}:
                        pass
                class UnknownTests(unittest.TestCase):
                    @conditional(os.name == "nt", "possibly retained skip")
                    def test_value(self): pass
                """,
            ),
        )
        for label, raw_source in root_and_pattern_rebindings:
            with self.subTest(round5_rereview_binder=label), self.assertRaisesRegex(
                self.generator.InventoryError,
                "conditional skip decorator alias is unresolved",
            ):
                self.generator.discover_test_sources(
                    {"tests/test_alias.py": _source(raw_source)}
                )

        with self.subTest(round5_rereview2_binder="missing-root-provenance"):
            source = _source(
                """
                import os
                class UnknownTests(unittest.TestCase):
                    @unittest.skipIf(os.name == "nt", "POSIX only")
                    def test_value(self): pass
                """
            )
            with self.assertRaisesRegex(
                self.generator.InventoryError,
                "conditional skip decorator alias is unresolved",
            ):
                self.generator.discover_test_sources(
                    {"tests/test_alias.py": source}
                )

        with self.subTest(round5_rereview2_binder="canonical-alias-import"):
            source = _source(
                """
                import os as platform_os
                import unittest as testing
                class AliasTests(unittest.TestCase):
                    @testing.skipIf(platform_os.name == "nt", "POSIX only")
                    def test_value(self): pass
                """
            )
            inventory = self.generator.build_inventory(
                {"tests/test_alias.py": source},
                {"tests/test_alias.py": source},
            )
            self.assertEqual(
                inventory["entries"][0]["assignment"]["expectation"],
                {
                    "kind": "platform_conditioned",
                    "applicable_platforms": ["posix"],
                    "skip_safe_reason_code": "requires_posix",
                },
            )

    def test_round4_analysis_budget_red_contracts_are_independent(self) -> None:
        budget_constants = (
            ("MAXIMUM_ANALYSIS_HELPER_DEPTH", 64),
            ("MAXIMUM_ANALYSIS_CHILD_DEPTH", 4),
            ("MAXIMUM_ANALYSIS_CONTAINER_ELEMENTS", 4096),
            ("MAXIMUM_ANALYSIS_CARDINALITY", 2_147_483_647),
            ("MAXIMUM_ANALYSIS_WORK_UNITS", 250_000),
        )
        for name, expected in budget_constants:
            with self.subTest(constant=name):
                self.assertEqual(getattr(self.generator, name), expected)

        with self.subTest(boundary="helper-depth"):
            helper_lines = [
                "import subprocess",
                "import sys",
                "import unittest",
                "",
            ]
            for index in range(65):
                helper_lines.append(f"def helper_{index}():")
                if index == 64:
                    helper_lines.extend(
                        (
                            "    subprocess.run(",
                            "        [sys.executable, '-m', 'deep-helper'],",
                            "        timeout=5, check=False,",
                            "    )",
                        )
                    )
                else:
                    helper_lines.append(f"    return helper_{index + 1}()")
                helper_lines.append("")
            helper_lines.extend(
                (
                    "class ReviewTests(unittest.TestCase):",
                    "    def test_static(self): helper_0()",
                    "    def test_denied(self): pass",
                )
            )
            with self.assertRaisesRegex(
                self.generator.InventoryError,
                "^analysis helper depth exceeds 64$",
            ):
                self._review(
                    sources={
                        "tests/test_review.py": (
                            "\n".join(helper_lines).encode("utf-8") + b"\n"
                        )
                    }
                )

        range_cases = (
            (
                "zero-step",
                "for _ in range(0, 10, 0):\n"
                "                cp.arange(1)",
                "^analysis range step is zero$",
            ),
            (
                "cardinality",
                "for _ in range(0, 2147483648):\n"
                "                cp.arange(1)",
                "^analysis expanded cardinality exceeds 2147483647$",
            ),
        )
        for label, loop, reason in range_cases:
            with self.subTest(boundary=label):
                source = _source(
                    "import cupy as cp\n"
                    "import unittest\n"
                    "class ReviewTests(unittest.TestCase):\n"
                    "    def test_static(self):\n"
                    f"        {loop}\n"
                    "    def test_denied(self): pass\n"
                )
                with self.assertRaisesRegex(
                    self.generator.InventoryError,
                    reason,
                ):
                    self._review(sources={"tests/test_review.py": source})

        with self.subTest(boundary="container-elements"):
            source = _source(
                "import cupy as cp\n"
                "import unittest\n"
                "class ReviewTests(unittest.TestCase):\n"
                "    def test_static(self):\n"
                "        backends = [" + ", ".join(["cp"] * 4097) + "]\n"
                "        backends[0].arange(1)\n"
                "    def test_denied(self): pass\n"
            )
            with self.assertRaisesRegex(
                self.generator.InventoryError,
                "^analysis container elements exceed 4096$",
            ):
                self._review(sources={"tests/test_review.py": source})

        with self.subTest(round5_budget="900-term-expression"):
            expression = "+".join(["cp"] * 900)
            source = _source(
                "import cupy as cp\n"
                "import unittest\n"
                "class ReviewTests(unittest.TestCase):\n"
                "    def test_static(self):\n"
                f"        backend = {expression}\n"
                "        backend.arange(1)\n"
                "    def test_denied(self): pass\n"
            )
            with self.assertRaisesRegex(
                self.generator.InventoryError,
                "^analysis expression depth exceeds safe recursion$",
            ):
                self._review(sources={"tests/test_review.py": source})

        with self.subTest(round5_rereview_budget="900-term-literal-child"):
            expression = "+".join(["cp"] * 900)
            program = (
                "import cupy as cp\n"
                f"backend = {expression}\n"
                "backend.arange(1)\n"
            )
            source = _source(
                f'''
                import subprocess
                import sys
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        program = {program!r}
                        subprocess.run(
                            [sys.executable, "-c", program],
                            timeout=5,
                            check=False,
                        )
                    def test_denied(self): pass
                '''
            )
            with self.assertRaisesRegex(
                self.generator.InventoryError,
                "^analysis expression depth exceeds safe recursion$",
            ):
                self._review(sources={"tests/test_review.py": source})

        with self.subTest(round5_cardinality="maximum-plus-later-call"):
            source = _source(
                """
                import cupy as cp
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        for _ in range(2147483647):
                            cp.arange(1)
                        cp.arange(1)
                    def test_denied(self): pass
                """
            )
            with self.assertRaisesRegex(
                self.generator.InventoryError,
                "^analysis expanded cardinality exceeds 2147483647$",
            ):
                self._review(sources={"tests/test_review.py": source})

        with self.subTest(round5_rereview2_budget="call-bound-secondary-pass"):
            definition = ast.parse(
                "def review():\n    (" + ", ".join(["probe()"] * 32) + ")\n"
            ).body[0]
            visitor_units = sum(
                1
                for statement in definition.body
                for _ in ast.walk(statement)
            )
            budget = self.generator._AnalysisBudget(
                self.generator.MAXIMUM_ANALYSIS_WORK_UNITS
                - visitor_units
                - 1
            )
            execution = self.generator._execution_scope(definition, budget)
            self.assertEqual(len(execution.calls), 32)
            with self.assertRaisesRegex(
                self.generator.InventoryError,
                "^analysis work units exceed 250000$",
            ):
                self.generator._runtime_call_bounds(
                    definition.body,
                    {},
                    assignments={},
                    relative_path="tests/test_review.py",
                    aliases={},
                    helper_registry={},
                    analysis_budget=budget,
                )

        preclassifier_cardinality = (
            ("range", "[cp for _ in range(2147483648)]"),
            (
                "product",
                "[cp for _ in range(65536) for _ in range(65536)]",
            ),
        )
        for label, expression in preclassifier_cardinality:
            with self.subTest(round5_rereview2_cardinality=label):
                statement = ast.parse(expression).body
                with self.assertRaisesRegex(
                    self.generator.InventoryError,
                    "^analysis expanded cardinality exceeds 2147483647$",
                ):
                    self.generator._preclassified_sensitive_calls(
                        statement,
                        {"cp": "cupy"},
                        self.generator._AnalysisBudget(),
                        {},
                    )

        with self.subTest(boundary="child-depth"):
            program = "pass\n"
            for _ in range(5):
                program = (
                    "import subprocess, sys\n"
                    "subprocess.run([sys.executable, '-c', "
                    f"{program!r}], timeout=5, check=False)\n"
                )
            source = _source(
                f'''
                import subprocess
                import sys
                import unittest
                class ReviewTests(unittest.TestCase):
                    def test_static(self):
                        program = {program!r}
                        subprocess.run(
                            [sys.executable, "-c", program],
                            timeout=5,
                            check=False,
                        )
                    def test_denied(self): pass
                '''
            )
            review = self._review(sources={"tests/test_review.py": source})
            self.assertFalse(review["receipt"]["expanded_rows"])
            self.assertEqual(
                review["unresolved_dynamic_blockers"],
                [
                    {
                        "item_id": self.static_id,
                        "relative_path": "tests/test_review.py",
                        "line": 7,
                        "reason": "subprocess child analysis depth exceeds 4",
                    }
                ],
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

    def _round5_operation_entry_locks_before_git_source_and_destination_reads(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-round5-operation-entry-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            manager = self.generator._governance_cleanup_manager()
            reservation = manager.reserve()
            destinations = self.generator._GovernanceDestinationSet.build((target,))
            blocking_lease = self.generator._GovernanceLockSetLease.acquire(
                destinations,
                reservation,
            )
            events: list[str] = []

            operation = self.generator._GovernancePublicationOperation(
                destinations.paths,
                self.generator._GovernancePreparedPublication(
                    self.generator._GovernanceSinglePublication(b"loser\n")
                ),
            )
            real_derive = self.generator._derive_governance_publication

            def observe_derivation(supplied: object) -> object:
                events.append("source")
                return real_derive(supplied)

            try:
                with mock.patch.object(
                    self.generator,
                    "_strict_git_snapshot",
                    side_effect=lambda *args: events.append("git"),
                ), mock.patch.object(
                    self.generator,
                    "_derive_governance_publication",
                    side_effect=observe_derivation,
                ), self.assertRaisesRegex(Exception, "lock|writer|busy"):
                    self.generator._with_governance_attribute_lease(
                        root,
                        Path("C:/git.exe"),
                        operation,
                    )
            finally:
                blocking_lease.close()
                manager.release(reservation)
            self.assertEqual(events, [])
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual({path.name for path in root.iterdir()}, {target.name})

        inventory_snapshot = mock.Mock(raw=b"old-inventory\n")
        profile_snapshot = mock.Mock(raw=b"old-profile\n")
        working_snapshot = mock.Mock(sources={})
        inventory_revalidations = 0
        profile_revalidations = 0
        lifetime_checks = 0

        def revalidate_inventory() -> None:
            nonlocal inventory_revalidations
            inventory_revalidations += 1
            if inventory_revalidations > 1:
                raise AssertionError("published inventory was revalidated as old")

        def revalidate_profile() -> None:
            nonlocal profile_revalidations
            profile_revalidations += 1
            if profile_revalidations > 1:
                raise AssertionError("published profile was revalidated as old")

        inventory_snapshot.revalidate.side_effect = revalidate_inventory
        profile_snapshot.revalidate.side_effect = revalidate_profile
        inventory_document = {"entries": []}
        discovery = mock.Mock(lifecycle_fixtures=())

        def invoke_locked_action(
            repository_root: Path,
            git_path: Path,
            operation: object,
        ) -> object:
            self.assertEqual(len(operation.slots), 2)
            payload = self.generator._derive_governance_publication(
                operation.derivation
            )
            self.assertIsInstance(
                payload,
                self.generator._GovernancePairPublication,
            )
            self.generator._write_governance_pair(
                operation.slots[0],
                payload.first_raw,
                operation.slots[1],
                payload.second_raw,
                lifetime_check=payload.lifetime_check,
            )
            return payload.value

        def publish_pair(*args: object, **kwargs: object) -> None:
            nonlocal lifetime_checks
            lifetime_check = kwargs["lifetime_check"]
            lifetime_check()
            lifetime_checks += 1
            lifetime_check()
            lifetime_checks += 1

        with mock.patch.dict(
            self.generator.os.environ,
            {"PONTIUS_GIT": "C:/git.exe"},
        ), mock.patch.object(
            self.generator,
            "_baseline_sources",
            return_value={},
        ), mock.patch.object(
            self.generator,
            "_capture_working_sources",
            return_value=working_snapshot,
        ), mock.patch.object(
            self.generator,
            "build_inventory",
            return_value=inventory_document,
        ), mock.patch.object(
            self.generator,
            "discover_test_sources",
            return_value=discovery,
        ), mock.patch.object(
            self.generator,
            "render_profiles",
            return_value=b"new-profile\n",
        ), mock.patch.object(
            self.generator.secure_filesystem,
            "read_regular_snapshot",
            side_effect=(inventory_snapshot, profile_snapshot),
        ), mock.patch.object(
            self.generator,
            "derive_design_review",
            return_value={},
        ), mock.patch.object(
            self.generator,
            "preserve_approved_profile_scopes",
            return_value=b"new-profile\n",
        ), mock.patch.object(
            self.generator,
            "_with_governance_attribute_lease",
            side_effect=invoke_locked_action,
        ), mock.patch.object(
            self.generator,
            "_write_governance_pair",
            side_effect=publish_pair,
        ):
            self.assertEqual(self.generator.main(["--write"]), 0)
        self.assertEqual(inventory_revalidations, 1)
        self.assertEqual(profile_revalidations, 1)
        self.assertEqual(lifetime_checks, 2)

    def _round5_dict_captured_undeclared_target_is_not_inferred(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-round5-dict-destination-"
        ) as temporary:
            root = Path(temporary)
            declared = root / "declared.toml"
            undeclared = root / "undeclared.toml"
            declared.write_bytes(b"declared\n")
            undeclared.write_bytes(b"undeclared\n")
            captured = {"target": undeclared}

            def invalid_payload() -> object:
                return {"path": captured["target"], "raw": b"changed\n"}

            with self.assertRaisesRegex(Exception, "not closed"):
                self.generator._GovernancePublicationOperation(
                    (declared,),
                    invalid_payload,
                )
            self.assertEqual(declared.read_bytes(), b"declared\n")
            self.assertEqual(undeclared.read_bytes(), b"undeclared\n")
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {declared.name, undeclared.name},
            )

    def _round5_active_group_rejects_write_outside_declared_set_before_io(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-round5-active-membership-"
        ) as temporary:
            root = Path(temporary)
            declared = root / "declared.toml"
            undeclared = root / "undeclared.toml"
            declared.write_bytes(b"declared\n")
            undeclared.write_bytes(b"undeclared\n")
            destinations = self.generator._GovernanceDestinationSet.build((declared,))
            lock_set = mock.Mock(
                destination_set=destinations,
                canonical_keys=destinations.canonical_keys,
                closed=False,
            )
            group = self.generator._GovernanceWriteGroup(
                lock_set,
                self.generator._GovernanceCleanupReservation(1),
            )
            previous = self.generator._governance_active_group()
            self.generator._GOVERNANCE_TRANSACTION_CONTEXT.group = group
            try:
                with mock.patch.object(
                    self.generator,
                    "_write_atomic_lf_locked",
                    side_effect=AssertionError("undeclared write reached I/O"),
                ) as locked_write, self.assertRaisesRegex(
                    self.generator.InventoryError,
                    "declared destination|destination set",
                ):
                    self.generator.write_atomic_lf(undeclared, b"changed\n")
                locked_write.assert_not_called()
            finally:
                if previous is None:
                    del self.generator._GOVERNANCE_TRANSACTION_CONTEXT.group
                else:
                    self.generator._GOVERNANCE_TRANSACTION_CONTEXT.group = previous
            self.assertEqual(undeclared.read_bytes(), b"undeclared\n")
            self.assertEqual(group.participants, [])

    def _round5_active_group_hardlink_pair_rejects_before_participants(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-round5-active-hardlink-"
        ) as temporary:
            root = Path(temporary)
            first = root / "inventory.json"
            second = root / "profiles.toml"
            first.write_bytes(b"old\n")
            os.link(first, second)
            destinations = self.generator._GovernanceDestinationSet.build(
                (first, second)
            )
            lock_set = mock.Mock(
                destination_set=destinations,
                canonical_keys=destinations.canonical_keys,
                closed=False,
            )
            group = self.generator._GovernanceWriteGroup(
                lock_set,
                self.generator._GovernanceCleanupReservation(1),
            )
            previous = self.generator._governance_active_group()
            self.generator._GOVERNANCE_TRANSACTION_CONTEXT.group = group
            try:
                try:
                    self.generator._write_governance_pair(
                        first,
                        b"new-first\n",
                        second,
                        b"new-second\n",
                    )
                except self.generator.InventoryError as error:
                    self.assertRegex(
                        str(error),
                        "native.*alias|same.*file|hard.?link",
                    )
                except BaseException as error:
                    self.fail(f"hardlink pair was not rejected correctly: {error}")
                else:
                    self.fail("hardlink pair was accepted")
            finally:
                if previous is None:
                    del self.generator._GOVERNANCE_TRANSACTION_CONTEXT.group
                else:
                    self.generator._GOVERNANCE_TRANSACTION_CONTEXT.group = previous
            self.assertEqual(group.participants, [])
            self.assertEqual(first.read_bytes(), b"old\n")
            self.assertEqual(second.read_bytes(), b"old\n")
            self.assertEqual({path.name for path in root.iterdir()}, {first.name, second.name})

    def _round5_cleanup_retry_is_exclusive_per_generation(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        first_entered = threading.Event()
        second_started = threading.Event()
        second_invocation = threading.Event()
        release = threading.Event()
        calls = 0
        calls_mutex = threading.Lock()

        class Pending:
            def retry_pending_cleanup(inner_self) -> None:
                nonlocal calls
                with calls_mutex:
                    calls += 1
                    if calls == 1:
                        first_entered.set()
                    else:
                        second_invocation.set()
                if not release.wait(5):
                    raise AssertionError("cleanup release timed out")

            def pending_descriptor(
                inner_self,
                retry_id: int,
                attempts: int,
            ) -> object:
                return mock.Mock(retry_id=retry_id, attempts=attempts)

        retry_id = manager.transfer(manager.reserve(), Pending())
        errors: list[BaseException] = []

        def retry(*, mark_started: bool = False) -> None:
            if mark_started:
                second_started.set()
            try:
                manager.retry_pending(retry_id)
            except BaseException as error:
                errors.append(error)

        first_thread = threading.Thread(target=retry, daemon=True)
        second_thread = threading.Thread(
            target=lambda: retry(mark_started=True),
            daemon=True,
        )
        first_thread.start()
        self.assertTrue(first_entered.wait(5))
        second_thread.start()
        self.assertTrue(second_started.wait(5))
        duplicate_started = second_invocation.wait(1)
        release.set()
        first_thread.join(5)
        second_thread.join(5)
        self.assertFalse(first_thread.is_alive())
        self.assertFalse(second_thread.is_alive())
        self.assertFalse(duplicate_started)
        self.assertEqual(calls, 1)
        self.assertEqual(errors, [])
        self.assertEqual(manager.pending_descriptors(), ())

    def _round5_writer_retries_recoverable_full_capacity_before_reserving(
        self,
    ) -> None:
        manager = self.generator._GovernanceCleanupManager()
        retry_calls = 0

        class Pending:
            def retry_pending_cleanup(inner_self) -> None:
                nonlocal retry_calls
                retry_calls += 1

            def pending_descriptor(
                inner_self,
                retry_id: int,
                attempts: int,
            ) -> object:
                return mock.Mock(retry_id=retry_id, attempts=attempts)

        for _ in range(self.generator.MAXIMUM_PENDING_GOVERNANCE_CLEANUPS):
            manager.transfer(manager.reserve(), Pending())
        with tempfile.TemporaryDirectory(
            prefix="pontius-round5-full-capacity-"
        ) as temporary:
            target = Path(temporary) / "profiles.toml"
            target.write_bytes(b"old\n")
            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ):
                try:
                    self.generator.write_atomic_lf(target, b"new\n")
                except BaseException as error:
                    self.fail(f"recoverable full capacity blocked writer: {error}")
            self.assertEqual(target.read_bytes(), b"new\n")
            self.assertEqual({path.name for path in target.parent.iterdir()}, {target.name})
        self.assertEqual(
            retry_calls,
            self.generator.MAXIMUM_PENDING_GOVERNANCE_CLEANUPS,
        )
        self.assertEqual(manager.pending_descriptors(), ())

    def _round5_git_launch_lease_cleanup_is_component_idempotent(self) -> None:
        descriptor_closes = 0
        ancestor_closes: dict[int, int] = {201: 0, 202: 0}
        second_ancestor_allowed = False
        lease = self.generator._GitLaunchLease(
            Path("C:/git.exe"),
            (1,),
            101,
            None,
            (),
            (201, 202),
        )

        def close_descriptor(descriptor: int) -> None:
            nonlocal descriptor_closes
            self.assertEqual(descriptor, 101)
            descriptor_closes += 1

        def close_ancestor(handle: int) -> None:
            ancestor_closes[handle] += 1
            if handle == 202 and not second_ancestor_allowed:
                raise OSError("ancestor remains open")

        with mock.patch.object(
            self.generator.os,
            "close",
            side_effect=close_descriptor,
        ), mock.patch.object(
            self.generator.secure_filesystem,
            "_windows_close_directory",
            side_effect=close_ancestor,
        ), mock.patch.object(
            self.generator,
            "_windows_governance_handle_is_open",
            return_value=True,
        ):
            with self.assertRaisesRegex(Exception, "Git launch lease cleanup"):
                lease.close()
            second_ancestor_allowed = True
            lease.close()
            lease.close()
        self.assertEqual(descriptor_closes, 1)
        self.assertEqual(ancestor_closes, {201: 1, 202: 1})

    def _round5_partial_lock_release_descriptor_reports_exact_ownership(
        self,
    ) -> None:
        manager = self.generator._GovernanceCleanupManager()
        first = Path("C:/locked/inventory.json")
        second = Path("C:/locked/profiles.toml")
        destinations = self.generator._GovernanceDestinationSet.build((first, second))
        first_key, second_key = destinations.canonical_keys
        first_artifact = Path("C:/locked/.inventory.json.pontius-governance.lock")
        second_artifact = Path("C:/locked/.profiles.toml.pontius-governance.lock")
        release_first = False

        class LockOwner:
            role = "deterministic_lock"

            def __init__(
                inner_self,
                destination_key: str,
                artifact_path: Path,
                fails: bool,
            ) -> None:
                inner_self.destination_key = destination_key
                inner_self.artifact_path = artifact_path
                inner_self.fails = fails
                inner_self.closed = False

            def close(inner_self) -> None:
                if inner_self.closed:
                    return
                if inner_self.fails and not release_first:
                    raise OSError("first lock remains held")
                inner_self.closed = True

        first_owner = LockOwner(first_key, first_artifact, True)
        second_owner = LockOwner(second_key, second_artifact, False)
        lock_set = self.generator._GovernanceLockSetLease(
            destinations,
            [first_owner, second_owner],
            destinations.canonical_keys,
        )
        group = self.generator._GovernanceWriteGroup(lock_set, manager.reserve())
        group.mark_committed()
        with mock.patch.object(
            self.generator,
            "_GOVERNANCE_CLEANUP_MANAGER",
            manager,
        ), self.assertRaises(
            self.generator.GovernanceCommittedWithCleanupFailure
        ) as caught:
            group.finish_committed_cleanup()
        descriptor = caught.exception.descriptor
        self.assertEqual(descriptor.lock_keys, (first_key,))
        self.assertEqual(descriptor.released_lock_keys, (second_key,))
        self.assertEqual(descriptor.artifact_paths, (str(first_artifact),))
        self.assertEqual(
            descriptor.outstanding_owner_roles,
            ("deterministic_lock",),
        )
        release_first = True
        manager.retry_pending(caught.exception.retry_id)
        self.assertEqual(manager.pending_descriptors(), ())

    def _round5_posix_parent_exchange_is_refused_by_anchored_lock(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        reservation = manager.reserve()
        destination = Path("C:/governed/profiles.toml")
        destinations = self.generator._GovernanceDestinationSet.build((destination,))
        stable_parent = mock.Mock(st_mode=stat.S_IFDIR | 0o700)
        stable_parent.st_dev = 1
        stable_parent.st_ino = 2
        stable_parent.st_file_attributes = 0
        stable_parent.st_reparse_tag = 0
        exchanged_parent = mock.Mock(st_mode=stat.S_IFDIR | 0o700)
        exchanged_parent.st_dev = 1
        exchanged_parent.st_ino = 3
        exchanged_parent.st_file_attributes = 0
        exchanged_parent.st_reparse_tag = 0
        directory_identity = self.generator.secure_filesystem._directory_identity(
            stable_parent
        )
        open_calls: list[tuple[object, int | None]] = []

        def open_path(path: object, flags: int, *args: object, **kwargs: object) -> int:
            open_calls.append((path, kwargs.get("dir_fd")))
            return 301 if len(open_calls) == 1 else 302

        with mock.patch.object(
            self.generator.os,
            "name",
            "posix",
        ), mock.patch.object(
            self.generator,
            "_governance_directory_chain",
            return_value=((destination.parent, directory_identity),),
        ), mock.patch.object(
            self.generator.os,
            "open",
            side_effect=open_path,
        ), mock.patch.object(
            self.generator.os,
            "fstat",
            return_value=stable_parent,
        ), mock.patch.object(
            self.generator.os,
            "lstat",
            return_value=exchanged_parent,
        ), mock.patch.object(
            self.generator.os,
            "close",
        ), mock.patch.object(
            self.generator.os,
            "unlink",
        ):
            lease = self.generator._GovernanceLockSetLease.acquire(
                destinations,
                reservation,
            )
            self.assertGreaterEqual(len(open_calls), 2)
            self.assertEqual(
                open_calls[1],
                (".profiles.toml.pontius-governance.lock", 301),
            )
            with self.assertRaisesRegex(Exception, "ancestor identity changed"):
                lease.posix_parent_for(destination)
            lease.close()
        manager.release(reservation)

    def _round5_posix_close_succeeded_then_raised_never_retries_reused_fd(
        self,
    ) -> None:
        for role in (
            "staging",
            "published",
            "recovery",
            "directory",
            "git_lease",
            "deterministic_lock",
        ):
            with self.subTest(role=role), tempfile.TemporaryDirectory(
                prefix=f"pontius-round5-posix-close-{role}-"
            ) as temporary:
                root = Path(temporary)
                original_path = root / "original"
                reused_path = root / "reused"
                original_path.write_bytes(b"original")
                reused_path.write_bytes(b"reused")
                descriptor = os.open(original_path, os.O_RDONLY)
                close_calls = 0
                reused_descriptor: int | None = None

                def close_action() -> None:
                    nonlocal close_calls, reused_descriptor
                    close_calls += 1
                    os.close(descriptor)
                    reused_descriptor = os.open(reused_path, os.O_RDONLY)
                    self.assertEqual(reused_descriptor, descriptor)
                    raise OSError("close succeeded then raised")

                owner = self.generator._PosixDescriptorOwner(
                    role=role,
                    descriptor=descriptor,
                    close_action=close_action,
                )
                try:
                    with self.assertRaisesRegex(OSError, "close succeeded"):
                        owner.close()
                    owner.close()
                    self.assertTrue(owner.closed)
                    self.assertEqual(close_calls, 1)
                    self.assertIsNotNone(reused_descriptor)
                    self.assertEqual(os.read(reused_descriptor, 6), b"reused")
                finally:
                    if reused_descriptor is not None:
                        os.close(reused_descriptor)
                    else:
                        try:
                            os.close(descriptor)
                        except OSError:
                            pass

    def _round5_invalid_retain_mode_refuses_before_dispatch_or_directory_io(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-round5-invalid-retain-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            for invalid in (None, False, 1):
                with self.subTest(retain=invalid), mock.patch.object(
                    self.generator,
                    "_governance_directory_chain",
                    side_effect=AssertionError("directory chain was observed"),
                ) as directory_chain, mock.patch.object(
                    self.generator,
                    "_write_windows_governance",
                    side_effect=AssertionError("Windows writer dispatched"),
                ) as windows_writer, mock.patch.object(
                    self.generator,
                    "_write_posix_governance",
                    side_effect=AssertionError("POSIX writer dispatched"),
                ) as posix_writer, self.assertRaisesRegex(
                    self.generator.InventoryError,
                    "group-owned transaction",
                ):
                    self.generator._write_atomic_lf_locked(
                        target,
                        b"new\n",
                        _retain_transaction=invalid,
                    )
                directory_chain.assert_not_called()
                windows_writer.assert_not_called()
                posix_writer.assert_not_called()
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual({path.name for path in root.iterdir()}, {target.name})

    def _final_rereview_same_inode_same_fd_reuse_is_never_retried(self) -> None:
        for role in (
            "staging",
            "published",
            "recovery",
            "directory",
            "git_lease",
            "deterministic_lock",
        ):
            with self.subTest(role=role), tempfile.TemporaryDirectory(
                prefix=f"pontius-final-close-{role}-"
            ) as temporary:
                path = Path(temporary) / "same-inode"
                path.write_bytes(b"same-inode")
                descriptor = os.open(path, os.O_RDONLY)
                close_calls = 0
                replacement: int | None = None

                def close_then_reopen_same_inode() -> None:
                    nonlocal close_calls, replacement
                    close_calls += 1
                    os.close(descriptor)
                    replacement = os.open(path, os.O_RDONLY)
                    self.assertEqual(replacement, descriptor)
                    raise OSError("close succeeded then raised")

                owner = self.generator._PosixDescriptorOwner(
                    role,
                    descriptor,
                    close_then_reopen_same_inode,
                )
                try:
                    try:
                        owner.close()
                    except OSError:
                        pass
                    try:
                        owner.close()
                    except OSError:
                        pass
                    self.assertEqual(close_calls, 1)
                    self.assertEqual(os.read(replacement, 4), b"same")
                finally:
                    if replacement is not None:
                        os.close(replacement)

    def _final2_legacy_callback_is_rejected_before_git_or_source_work(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-final2-closed-publication-"
        ) as temporary:
            root = Path(temporary)
            declared = root / "declared.toml"
            undeclared = root / "undeclared.toml"
            declared.write_bytes(b"declared\n")
            undeclared.write_bytes(b"undeclared\n")
            events: list[str] = []
            lease = mock.Mock()
            lease.close.return_value = None

            def legacy_action(revalidate: object) -> object:
                revalidate()
                events.append("source")
                return self.generator.write_atomic_lf(
                    undeclared,
                    b"changed\n",
                )

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                side_effect=lambda *_args: (
                    events.append("git"),
                    (Path("C:/git.exe"), b"git", (1,)),
                )[1],
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ):
                with self.assertRaises((TypeError, self.generator.InventoryError)):
                    self.generator._with_governance_attribute_lease(
                        root,
                        Path("C:/git.exe"),
                        (declared,),
                        legacy_action,
                    )
            self.assertEqual(
                events,
                [],
                "legacy callback reached Git/source work before rejection",
            )
            self.assertEqual(declared.read_bytes(), b"declared\n")
            self.assertEqual(undeclared.read_bytes(), b"undeclared\n")

    def _final2_parent_probe_failure_is_immediately_owned(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        reservation = manager.reserve()
        target = Path("C:/governed/profiles.toml")
        destinations = self.generator._GovernanceDestinationSet.build((target,))
        expected = (1, 2, stat.S_IFDIR | 0o700, 0, 0)
        closes: list[int] = []
        with mock.patch.object(
            self.generator,
            "_GOVERNANCE_CLEANUP_MANAGER",
            manager,
        ), mock.patch.object(
            self.generator.os,
            "name",
            "posix",
        ), mock.patch.object(
            self.generator,
            "_governance_directory_chain",
            return_value=((target.parent, expected),),
        ), mock.patch.object(
            self.generator.os,
            "open",
            return_value=711,
        ), mock.patch.object(
            self.generator.os,
            "fstat",
            side_effect=RuntimeError("first parent probe failed"),
        ), mock.patch.object(
            self.generator.os,
            "close",
            side_effect=lambda descriptor: closes.append(descriptor),
        ):
            with self.assertRaises(self.generator.InventoryError):
                self.generator._GovernanceLockSetLease.acquire(
                    destinations,
                    reservation,
                )
        self.assertEqual(
            closes,
            [711],
            "the just-opened parent descriptor escaped ownership",
        )
        self.assertEqual(manager.pending_descriptors(), ())

    def _final2_posix_staging_probe_failure_is_namespace_owned(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        names = {"profiles.toml"}
        unlink_attempts = 0
        cleanup_allowed = False
        path = Path("C:/governed/profiles.toml")
        staging_name = ".profiles.toml.fixed.tmp"
        staging_path = path.with_name(staging_name)
        regular = mock.Mock(st_mode=stat.S_IFREG | 0o600)
        parent = mock.Mock(
            path=path.parent,
            descriptor=721,
            descriptor_identity=(7, 8, stat.S_IFDIR | 0o700),
            chain=((path.parent, (7, 8)),),
        )
        parent.revalidate.return_value = None

        def fake_open(name: str, *_args: object, **_kwargs: object) -> int:
            self.assertEqual(name, staging_name)
            names.add(name)
            return 722

        def fake_fstat(descriptor: int) -> object:
            if descriptor == 722:
                raise RuntimeError("staging identity probe failed")
            return regular

        def fake_stat(name: str, **_kwargs: object) -> object:
            if name not in names:
                raise FileNotFoundError(name)
            return regular

        def fake_unlink(name: str, **_kwargs: object) -> None:
            nonlocal unlink_attempts
            unlink_attempts += 1
            if not cleanup_allowed:
                raise OSError("staging unlink retained")
            names.remove(name)

        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(
                    self.generator.os,
                    "O_DIRECTORY",
                    0x10000,
                    create=True,
                )
            )
            stack.enter_context(
                mock.patch.object(
                    self.generator.os,
                    "O_NOFOLLOW",
                    0x20000,
                    create=True,
                )
            )
            stack.enter_context(
                mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                )
            )
            stack.enter_context(
                mock.patch.object(
                    self.generator.uuid,
                    "uuid4",
                    return_value=mock.Mock(hex="fixed"),
                )
            )
            patched_open = stack.enter_context(
                mock.patch.object(self.generator.os, "open", side_effect=fake_open)
            )
            stack.enter_context(
                mock.patch.object(self.generator.os, "fstat", side_effect=fake_fstat)
            )
            patched_stat = stack.enter_context(
                mock.patch.object(self.generator.os, "stat", side_effect=fake_stat)
            )
            stack.enter_context(mock.patch.object(self.generator.os, "close"))
            patched_link = stack.enter_context(
                mock.patch.object(self.generator.os, "link")
            )
            patched_replace = stack.enter_context(
                mock.patch.object(self.generator.os, "replace")
            )
            patched_unlink = stack.enter_context(
                mock.patch.object(
                    self.generator.os,
                    "unlink",
                    side_effect=fake_unlink,
                )
            )
            supports_dir_fd = stack.enter_context(
                mock.patch.object(self.generator.os, "supports_dir_fd", set())
            )
            supports_follow = stack.enter_context(
                mock.patch.object(
                    self.generator.os,
                    "supports_follow_symlinks",
                    set(),
                )
            )
            supports_dir_fd.update(
                {
                    patched_open,
                    patched_stat,
                    patched_link,
                    patched_replace,
                    patched_unlink,
                }
            )
            supports_follow.add(patched_stat)
            outcome = self.generator._GovernanceWriteOutcome()
            with self.assertRaises(
                self.generator._GovernancePreparationFailure
            ) as prepared:
                self.generator._write_posix_governance(
                    path,
                    b"new\n",
                    parent.chain,
                    None,
                    None,
                    outcome,
                    None,
                    None,
                    parent,
                    True,
                )
            participant = prepared.exception.participant
            self.assertEqual(participant.outstanding_roles(), ("staging",))
            self.assertEqual(participant.artifact_paths(), (staging_path,))
            class LockSet:
                closed = False

                def close(inner_self) -> None:
                    inner_self.closed = True

                def outstanding_roles(inner_self) -> tuple[str, ...]:
                    return ()

                def outstanding_lock_keys(inner_self) -> tuple[str, ...]:
                    return ()

                def released_lock_keys(inner_self) -> tuple[str, ...]:
                    return ()

                def artifact_paths(inner_self) -> tuple[Path, ...]:
                    return ()

            lock_set = LockSet()
            group = self.generator._GovernanceWriteGroup(
                lock_set,
                manager.reserve(),
            )
            group.add_participant(participant)
            with self.assertRaises(
                self.generator.GovernanceCleanupPendingError
            ) as pending:
                group.abort_precommit(prepared.exception.primary)
            descriptor = pending.exception.descriptor
            self.assertIn("staging", descriptor.outstanding_owner_roles)
            self.assertEqual(descriptor.artifact_paths, (str(staging_path),))
            self.assertEqual(names, {"profiles.toml", staging_name})
            self.assertEqual(unlink_attempts, 6)
            cleanup_allowed = True
            manager.retry_pending(pending.exception.retry_id)
            self.assertEqual(names, {"profiles.toml"})
            self.assertEqual(manager.pending_descriptors(), ())

    def _final2_posix_real_writer_rollback_schedules(self) -> None:
        for mode in ("exchange", "replace", "link"):
            with self.subTest(posix_real_schedule=mode):
                manager = self.generator._GovernanceCleanupManager()
                path = Path("C:/governed/profiles.toml")
                staging_name = ".profiles.toml.fixed.tmp"
                recovery_name = (
                    staging_name
                    if mode == "exchange"
                    else ".profiles.toml.fixed.recovery"
                )
                directory = 731
                temporary = 732
                original = 733
                directory_inode = 7
                old_inode = 10
                new_inode = 20
                inodes: dict[int, bytes] = {
                    old_inode: b"old\n",
                    new_inode: b"",
                }
                names: dict[str, int] = (
                    {} if mode == "link" else {path.name: old_inode}
                )
                closed: set[int] = set()
                fsync_calls = 0
                unlink_calls = 0
                cleanup_allowed = mode != "link"

                def info(inode: int, *, directory_mode: bool = False) -> object:
                    raw = b"" if directory_mode else inodes[inode]
                    result = mock.Mock(
                        st_dev=1,
                        st_ino=inode,
                        st_size=len(raw),
                        st_mtime_ns=0,
                        st_ctime_ns=0,
                        st_mode=(
                            stat.S_IFDIR | 0o700
                            if directory_mode
                            else stat.S_IFREG | 0o600
                        ),
                    )
                    result.st_file_attributes = 0
                    result.st_reparse_tag = 0
                    return result

                def fake_open(name: object, *_args: object, **_kwargs: object) -> int:
                    if isinstance(name, Path):
                        return directory
                    supplied = str(name)
                    if supplied == staging_name:
                        names[supplied] = new_inode
                        return temporary
                    if supplied == path.name:
                        return original
                    raise FileNotFoundError(supplied)

                def fake_fstat(descriptor: int) -> object:
                    if descriptor == directory:
                        return info(directory_inode, directory_mode=True)
                    if descriptor == temporary:
                        return info(new_inode)
                    if descriptor == original:
                        return info(old_inode)
                    raise OSError("unknown descriptor")

                def fake_stat(name: str, **_kwargs: object) -> object:
                    if name not in names:
                        raise FileNotFoundError(name)
                    return info(names[name])

                def fake_write(descriptor: int, raw: bytes) -> int:
                    self.assertEqual(descriptor, temporary)
                    inodes[new_inode] += raw
                    return len(raw)

                def fake_fsync(descriptor: int) -> None:
                    nonlocal fsync_calls
                    if descriptor != directory:
                        return
                    fsync_calls += 1
                    if mode != "link" and fsync_calls <= 2:
                        raise OSError(f"directory sync failure {fsync_calls}")

                def fake_link(source: str, destination: str, **_kwargs: object) -> None:
                    if destination in names:
                        raise FileExistsError(destination)
                    names[destination] = names[source]

                def fake_replace(source: str, destination: str, **_kwargs: object) -> None:
                    names[destination] = names.pop(source)

                def fake_exchange(
                    _directory: int,
                    first: str,
                    second: str,
                ) -> bool:
                    if mode != "exchange":
                        return False
                    names[first], names[second] = names[second], names[first]
                    return True

                def fake_unlink(name: str, **_kwargs: object) -> None:
                    nonlocal unlink_calls
                    unlink_calls += 1
                    if mode == "link" and name == staging_name and not cleanup_allowed:
                        raise OSError("staging unlink retained")
                    if name not in names:
                        raise FileNotFoundError(name)
                    del names[name]

                def fake_snapshot(snapshot_path: Path, **_kwargs: object) -> object:
                    inode = names[snapshot_path.name]
                    raw = inodes[inode]
                    snapshot = mock.Mock(
                        path=snapshot_path,
                        raw=raw,
                        identity=(
                            1,
                            inode,
                            len(raw),
                            0,
                            0,
                            stat.S_IFREG | 0o600,
                            0,
                            0,
                        ),
                    )
                    snapshot.revalidate.return_value = None
                    return snapshot

                with ExitStack() as stack:
                    stack.enter_context(
                        mock.patch.object(
                            self.generator,
                            "_GOVERNANCE_CLEANUP_MANAGER",
                            manager,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "O_DIRECTORY",
                            0x10000,
                            create=True,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "O_NOFOLLOW",
                            0x20000,
                            create=True,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.uuid,
                            "uuid4",
                            return_value=mock.Mock(hex="fixed"),
                        )
                    )
                    patched_open = stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "open",
                            side_effect=fake_open,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "fstat",
                            side_effect=fake_fstat,
                        )
                    )
                    patched_stat = stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "stat",
                            side_effect=fake_stat,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "write",
                            side_effect=fake_write,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "fsync",
                            side_effect=fake_fsync,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "close",
                            side_effect=lambda descriptor: closed.add(descriptor),
                        )
                    )
                    patched_link = stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "link",
                            side_effect=fake_link,
                        )
                    )
                    patched_replace = stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "replace",
                            side_effect=fake_replace,
                        )
                    )
                    patched_unlink = stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "unlink",
                            side_effect=fake_unlink,
                        )
                    )
                    supports_dir_fd = stack.enter_context(
                        mock.patch.object(self.generator.os, "supports_dir_fd", set())
                    )
                    supports_follow = stack.enter_context(
                        mock.patch.object(
                            self.generator.os,
                            "supports_follow_symlinks",
                            set(),
                        )
                    )
                    supports_dir_fd.update(
                        {
                            patched_open,
                            patched_stat,
                            patched_link,
                            patched_replace,
                            patched_unlink,
                        }
                    )
                    supports_follow.add(patched_stat)
                    stack.enter_context(
                        mock.patch.object(
                            self.generator,
                            "_revalidate_governance_directory_chain",
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator,
                            "_require_governance_destination_identity",
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator,
                            "_posix_exchange_governance_file",
                            side_effect=fake_exchange,
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.secure_filesystem,
                            "_directory_identity",
                            side_effect=lambda value: (value.st_ino,),
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            self.generator.secure_filesystem,
                            "read_regular_snapshot",
                            side_effect=fake_snapshot,
                        )
                    )
                    expected_identity = (
                        None
                        if mode == "link"
                        else (
                            1,
                            old_inode,
                            len(b"old\n"),
                            0,
                            0,
                            stat.S_IFREG | 0o600,
                            0,
                            0,
                        )
                    )
                    outcome = self.generator._GovernanceWriteOutcome()
                    with self.assertRaises(
                        self.generator._GovernancePreparationFailure
                    ) as prepared:
                        self.generator._write_posix_governance(
                            path,
                            b"new\n",
                            ((path.parent, (directory_inode,)),),
                            expected_identity,
                            None if mode == "link" else b"old\n",
                            outcome,
                            None,
                            None,
                            None,
                            True,
                        )
                    class LockSet:
                        closed = False

                        def close(inner_self) -> None:
                            inner_self.closed = True

                        def outstanding_roles(inner_self) -> tuple[str, ...]:
                            return ()

                        def outstanding_lock_keys(inner_self) -> tuple[str, ...]:
                            return ()

                        def released_lock_keys(inner_self) -> tuple[str, ...]:
                            return ()

                        def artifact_paths(inner_self) -> tuple[Path, ...]:
                            return ()

                    lock_set = LockSet()
                    group = self.generator._GovernanceWriteGroup(
                        lock_set,
                        manager.reserve(),
                    )
                    group.add_participant(prepared.exception.participant)
                    expected_artifact = (
                        path.with_name(staging_name)
                        if mode == "link"
                        else path.with_name(recovery_name)
                    )
                    expected_role = "staging" if mode == "link" else "recovery"
                    pending_error: object | None = None
                    try:
                        group.abort_precommit(prepared.exception.primary)
                    except self.generator.GovernanceCleanupPendingError as error:
                        pending_error = error
                    except BaseException as error:
                        if error is not prepared.exception.primary:
                            self.fail(f"{mode} rollback raised an unexpected error: {error}")
                    if pending_error is None:
                        self.assertEqual(
                            names,
                            {} if mode == "link" else {path.name: old_inode},
                            f"{mode} rollback lost namespace ownership",
                        )
                        continue
                    descriptor = pending_error.descriptor
                    self.assertIn(expected_role, descriptor.outstanding_owner_roles)
                    self.assertIn(str(expected_artifact), descriptor.artifact_paths)
                    if mode == "link":
                        self.assertIn(
                            temporary,
                            closed,
                            "staging namespace ownership must survive descriptor cleanup",
                        )
                    cleanup_allowed = True
                    try:
                        manager.retry_pending(pending_error.retry_id)
                    except BaseException as error:
                        self.fail(f"{mode} rollback did not resume monotonically: {error}")
                expected_names = {} if mode == "link" else {path.name: old_inode}
                self.assertEqual(names, expected_names)
                if mode != "link":
                    self.assertEqual(inodes[names[path.name]], b"old\n")
                    self.assertGreaterEqual(fsync_calls, 3)
                self.assertEqual(manager.pending_descriptors(), ())

    def _final2_real_multicomponent_git_acquisition_is_independent(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        path = Path("C:/toolchain/git.exe")
        file_info = mock.Mock(
            st_dev=1,
            st_ino=2,
            st_size=3,
            st_mtime_ns=4,
            st_ctime_ns=5,
            st_mode=stat.S_IFREG | 0o700,
        )
        file_info.st_file_attributes = 0
        file_info.st_reparse_tag = 0
        expected = self.generator._git_stat_identity(file_info)
        leaf_close_calls = 0
        ancestor_probe_calls = 0
        ancestor_close_calls = 0
        probe_allowed = False

        def build_ancestor_components(
            supplied_path: Path,
            cleanup_owner: object,
        ) -> tuple[tuple[int, ...], tuple[tuple[Path, tuple[int, ...]], ...]]:
            self.assertEqual(supplied_path, path)
            cleanup_owner.add(
                self.generator._WindowsHandleOwner(
                    "git_ancestor",
                    741,
                    lambda: close_ancestor(),
                    lambda: probe_ancestor(),
                )
            )
            return (741,), ((path.parent, (1, 2)),)

        def probe_ancestor() -> bool:
            nonlocal ancestor_probe_calls
            ancestor_probe_calls += 1
            if not probe_allowed:
                raise OSError("ancestor pre-close probe failed")
            return True

        def close_ancestor() -> None:
            nonlocal ancestor_close_calls
            ancestor_close_calls += 1

        def close_leaf(descriptor: int) -> None:
            nonlocal leaf_close_calls
            self.assertEqual(descriptor, 743)
            leaf_close_calls += 1

        fstat_calls = 0

        def fake_fstat(descriptor: int) -> object:
            nonlocal fstat_calls
            self.assertEqual(descriptor, 743)
            fstat_calls += 1
            if fstat_calls == 1:
                return file_info
            raise RuntimeError("post-acquisition validation failed")

        create_leaf = mock.Mock(return_value=742)
        close_raw_leaf = mock.Mock()
        with mock.patch.object(
            self.generator,
            "_GOVERNANCE_CLEANUP_MANAGER",
            manager,
        ), mock.patch.object(
            self.generator.os,
            "name",
            "nt",
        ), mock.patch.object(
            self.generator,
            "_git_path_stat",
            return_value=file_info,
        ), mock.patch.object(
            self.generator,
            "_windows_git_ancestor_handles",
            side_effect=build_ancestor_components,
        ), mock.patch.object(
            self.generator.secure_filesystem,
            "_windows_path_api",
            return_value=(create_leaf, mock.Mock(), close_raw_leaf),
        ), mock.patch.object(
            self.generator.secure_filesystem.msvcrt,
            "open_osfhandle",
            return_value=743,
        ), mock.patch.object(
            self.generator.os,
            "fstat",
            side_effect=fake_fstat,
        ), mock.patch.object(
            self.generator.os,
            "close",
            side_effect=close_leaf,
        ):
            with self.assertRaises(self.generator.InventoryError):
                self.generator._acquire_git_launch_lease(path, expected, b"git")
            descriptors = manager.pending_descriptors()
            self.assertEqual(
                len(descriptors),
                1,
                "partial multi-component acquisition was not manager-owned",
            )
            self.assertEqual(leaf_close_calls, 1)
            self.assertEqual(ancestor_close_calls, 0)
            self.assertEqual(ancestor_probe_calls, 1)
            self.assertIn(
                "git_ancestor",
                descriptors[0].outstanding_owner_roles,
            )
            probe_allowed = True
            manager.retry_pending(descriptors[0].retry_id)
        self.assertEqual(ancestor_probe_calls, 2)
        self.assertEqual(ancestor_close_calls, 1)
        self.assertEqual(manager.pending_descriptors(), ())

    def _final2_sidecar_open_failure_reports_parent_only_truth(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        target = Path("C:/governed/profiles.toml")
        destinations = self.generator._GovernanceDestinationSet.build((target,))
        directory_info = mock.Mock(
            st_dev=1,
            st_ino=2,
            st_mode=stat.S_IFDIR | 0o700,
        )
        directory_info.st_file_attributes = 0
        directory_info.st_reparse_tag = 0
        chain_identity = self.generator.secure_filesystem._directory_identity(
            directory_info
        )
        blocker = mock.Mock(closed=False)
        closes: list[int] = []
        real_parent_type = self.generator._PosixParentDirectoryOwner

        def open_parent_then_fail_sidecar(
            supplied: object,
            *_args: object,
            **_kwargs: object,
        ) -> int:
            if isinstance(supplied, Path):
                return 751
            raise FileExistsError("first relative sidecar open failed")

        def build_parent(*args: object, **kwargs: object) -> object:
            owner = real_parent_type(*args, **kwargs)
            owner.dependents.append(blocker)
            return owner

        with mock.patch.object(
            self.generator,
            "_GOVERNANCE_CLEANUP_MANAGER",
            manager,
        ), mock.patch.object(
            self.generator.os,
            "name",
            "posix",
        ), mock.patch.object(
            self.generator,
            "_governance_directory_chain",
            return_value=((target.parent, chain_identity),),
        ), mock.patch.object(
            self.generator.os,
            "open",
            side_effect=open_parent_then_fail_sidecar,
        ), mock.patch.object(
            self.generator.os,
            "fstat",
            return_value=directory_info,
        ), mock.patch.object(
            self.generator.os,
            "close",
            side_effect=lambda descriptor: closes.append(descriptor),
        ), mock.patch.object(
            self.generator,
            "_PosixParentDirectoryOwner",
            side_effect=build_parent,
        ):
            with self.assertRaises(
                self.generator.GovernanceCleanupPendingError
            ) as pending:
                self.generator._GovernanceLockSetLease.acquire(
                    destinations,
                    manager.reserve(),
                )
            descriptor = pending.exception.descriptor
            self.assertEqual(descriptor.lock_keys, ())
            self.assertEqual(descriptor.released_lock_keys, ())
            self.assertEqual(descriptor.artifact_paths, ())
            self.assertNotIn(
                "deterministic_lock",
                descriptor.outstanding_owner_roles,
            )
            self.assertEqual(closes, [])
            blocker.closed = True
            manager.retry_pending(pending.exception.retry_id)
        self.assertEqual(closes, [751])
        self.assertEqual(manager.pending_descriptors(), ())

    def _final3_windows_sidecar_failure_never_invents_released_lock(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        target = Path("C:/governed/profiles.toml")
        destinations = self.generator._GovernanceDestinationSet.build((target,))
        probe_allowed = False
        closes: list[int] = []

        def probe_parent(_handle: int) -> bool:
            if not probe_allowed:
                raise OSError("parent probe unavailable")
            return True

        with mock.patch.object(
            self.generator,
            "_GOVERNANCE_CLEANUP_MANAGER",
            manager,
        ), mock.patch.object(
            self.generator,
            "_windows_open_governance_directory",
            return_value=(801, (1, b"directory")),
        ), mock.patch.object(
            self.generator,
            "_windows_create_relative_governance_file",
            side_effect=FileExistsError("first sidecar create failed"),
        ), mock.patch.object(
            self.generator,
            "_windows_governance_handle_is_open",
            side_effect=probe_parent,
        ), mock.patch.object(
            self.generator.secure_filesystem,
            "_windows_close_directory",
            side_effect=lambda handle: closes.append(handle),
        ):
            with self.assertRaises(
                self.generator.GovernanceCleanupPendingError
            ) as pending:
                self.generator._GovernanceLockSetLease.acquire(
                    destinations,
                    manager.reserve(),
                )
            descriptor = pending.exception.descriptor
            self.assertEqual(descriptor.outstanding_owner_roles, ("directory",))
            self.assertEqual(descriptor.lock_keys, ())
            self.assertEqual(descriptor.artifact_paths, ())
            self.assertEqual(
                descriptor.released_lock_keys,
                (),
                "never-acquired Windows sidecar was reported as released",
            )
            probe_allowed = True
            manager.retry_pending(pending.exception.retry_id)
        self.assertEqual(closes, [801])
        self.assertEqual(manager.pending_descriptors(), ())

    def _final3_windows_parent_probe_failure_is_manager_owned(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        target = Path("C:/governed/profiles.toml")
        destinations = self.generator._GovernanceDestinationSet.build((target,))
        close_allowed = False
        close_attempts = 0

        def close_parent(_handle: object) -> int:
            nonlocal close_attempts
            close_attempts += 1
            return 1 if close_allowed else 0

        with mock.patch.object(
            self.generator,
            "_GOVERNANCE_CLEANUP_MANAGER",
            manager,
        ), mock.patch.object(
            self.generator.secure_filesystem,
            "_windows_directory_api",
            return_value=(mock.Mock(return_value=811), None, None, close_parent),
        ), mock.patch.object(
            self.generator.secure_filesystem,
            "_windows_directory_handle_identity",
            side_effect=OSError("directory identity probe failed"),
        ), mock.patch.object(
            self.generator,
            "_windows_governance_handle_is_open",
            return_value=True,
        ):
            caught: BaseException | None = None
            try:
                self.generator._GovernanceLockSetLease.acquire(
                    destinations,
                    manager.reserve(),
                )
            except BaseException as error:
                caught = error
            descriptors = manager.pending_descriptors()
            try:
                self.assertIsInstance(caught, self.generator.InventoryError)
                self.assertEqual(
                    len(descriptors),
                    1,
                    "opened Windows parent escaped manager ownership",
                )
                descriptor = descriptors[0]
                self.assertEqual(descriptor.outstanding_owner_roles, ("directory",))
                self.assertEqual(descriptor.lock_keys, ())
                self.assertEqual(descriptor.released_lock_keys, ())
                self.assertEqual(descriptor.artifact_paths, ())
                self.assertGreaterEqual(close_attempts, 1)
            finally:
                close_allowed = True
                for descriptor in manager.pending_descriptors():
                    manager.retry_pending(descriptor.retry_id)
        self.assertEqual(manager.pending_descriptors(), ())

    def _final2_distinct_owner_families_never_replay_reused_numbers(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-final2-owner-families-"
        ) as temporary:
            path = Path(temporary) / "same-inode"
            path.write_bytes(b"same-inode")
            gen_os = self.generator.os
            def exercise(label: str, build: object) -> None:
                with self.subTest(owner_family=label):
                    real_close = os.close
                    descriptor = os.open(path, os.O_RDONLY)
                    replacement: int | None = None
                    attempts = 0

                    def close_then_reopen() -> None:
                        nonlocal attempts, replacement
                        attempts += 1
                        real_close(descriptor)
                        replacement = os.open(path, os.O_RDONLY)
                        self.assertEqual(replacement, descriptor)
                        raise OSError("consuming close succeeded then raised")

                    owner, patchers = build(descriptor, close_then_reopen)
                    try:
                        with ExitStack() as stack:
                            for patcher in patchers:
                                stack.enter_context(patcher)
                            for _ in range(2):
                                try:
                                    owner.close()
                                except (OSError, self.generator.InventoryError):
                                    pass
                        self.assertEqual(attempts, 1)
                        self.assertEqual(os.read(replacement, 4), b"same")
                    finally:
                        if replacement is not None:
                            real_close(replacement)

            exercise(
                "git-launch-lease",
                lambda descriptor, close_action: (
                    self.generator._GitLaunchLease(
                        path,
                        (1,),
                        descriptor,
                        None,
                        (),
                    ),
                    (mock.patch.object(gen_os, "close", side_effect=lambda *_: close_action()),),
                ),
            )

            def acquisition_owner(descriptor: int, close_action: object) -> object:
                cleanup = self.generator._GitAcquisitionCleanup()
                cleanup.add(
                    self.generator._PosixDescriptorOwner(
                        "git_lease",
                        descriptor,
                        close_action,
                    )
                )
                return cleanup, ()

            exercise("git-acquisition", acquisition_owner)
            exercise(
                "posix-deterministic-lock",
                lambda descriptor, close_action: (
                    self.generator._PosixDeterministicLockOwner(
                        descriptor,
                        path.with_name(".lock"),
                    ),
                    (
                        mock.patch.object(
                            self.generator.os,
                            "close",
                            side_effect=lambda _fd: close_action(),
                        ),
                        mock.patch.object(Path, "unlink"),
                    ),
                ),
            )
            exercise(
                "windows-handle-owner",
                lambda descriptor, close_action: (
                    self.generator._WindowsHandleOwner(
                        "directory",
                        descriptor,
                        close_action,
                        lambda: True,
                    ),
                    (),
                ),
            )
            exercise(
                "windows-deterministic-lock",
                lambda descriptor, close_action: (
                    self.generator._WindowsDeterministicLockOwner(
                        ".profiles.lock",
                        handle=descriptor,
                    ),
                    (
                        mock.patch.object(
                            self.generator,
                            "_windows_dispose_governance_lock",
                        ),
                        mock.patch.object(
                            self.generator,
                            "_windows_try_close_file",
                            side_effect=lambda _handle: close_action(),
                        ),
                    ),
                ),
            )

    def _final3_git_component_owners_precede_every_acquisition(self) -> None:
        path = Path("C:/git.exe")
        launch_path = Path("C:/launch.exe")
        info = mock.Mock(
            st_dev=1,
            st_ino=2,
            st_size=3,
            st_mtime_ns=4,
            st_ctime_ns=5,
            st_mode=stat.S_IFREG | 0o755,
            st_file_attributes=0,
            st_reparse_tag=0,
        )
        expected_identity = self.generator._git_stat_identity(info)

        with self.subTest(component="posix-sealed-descriptor"):
            manager = self.generator._GovernanceCleanupManager()
            acquisitions: list[int] = []

            def acquire_snapshot(*_args: object) -> tuple[int, Path]:
                acquisitions.append(901)
                return 901, launch_path

            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator.os,
                "name",
                "posix",
            ), mock.patch.object(
                self.generator,
                "_git_path_stat",
                return_value=info,
            ), mock.patch.object(
                self.generator,
                "_read_git_bytes",
                return_value=b"git",
            ), mock.patch.object(
                self.generator,
                "_posix_executable_snapshot",
                side_effect=acquire_snapshot,
            ), mock.patch.object(
                self.generator,
                "_PosixDescriptorOwner",
                side_effect=MemoryError("descriptor owner construction failed"),
            ):
                with self.assertRaises(self.generator.InventoryError):
                    self.generator._acquire_git_launch_lease(
                        path,
                        expected_identity,
                        b"git",
                    )
            self.assertEqual(manager._reservations, set())
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual(
                acquisitions,
                [],
                "POSIX descriptor was acquired before its owner slot existed",
            )

        with self.subTest(component="windows-ancestor-handle"):
            manager = self.generator._GovernanceCleanupManager()
            acquisitions = []
            ancestor = Path("C:/")
            ancestor_chain = ((ancestor, (11, 22, 0)),)

            def create_ancestor(*_args: object) -> int:
                acquisitions.append(902)
                return 902

            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator,
                "_git_path_stat",
                return_value=info,
            ), mock.patch.object(
                self.generator,
                "_git_ancestor_chain",
                return_value=ancestor_chain,
            ), mock.patch.object(
                self.generator.secure_filesystem,
                "_windows_directory_api",
                return_value=(create_ancestor, None, None, None),
            ), mock.patch.object(
                self.generator,
                "_WindowsHandleOwner",
                side_effect=MemoryError("ancestor owner construction failed"),
            ):
                with self.assertRaises(self.generator.InventoryError):
                    self.generator._acquire_git_launch_lease(
                        path,
                        expected_identity,
                        b"git",
                    )
            self.assertEqual(manager._reservations, set())
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual(
                acquisitions,
                [],
                "ancestor handle was acquired before its owner slot existed",
            )

        with self.subTest(component="windows-executable-handle"):
            manager = self.generator._GovernanceCleanupManager()
            acquisitions = []

            def create_executable(*_args: object) -> int:
                acquisitions.append(903)
                return 903

            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator,
                "_git_path_stat",
                return_value=info,
            ), mock.patch.object(
                self.generator,
                "_windows_git_ancestor_handles",
                return_value=((), ()),
            ), mock.patch.object(
                self.generator.secure_filesystem,
                "_windows_path_api",
                return_value=(create_executable, None, mock.Mock()),
            ), mock.patch.object(
                self.generator,
                "_WindowsHandleOwner",
                side_effect=MemoryError("executable owner construction failed"),
            ):
                with self.assertRaises(self.generator.InventoryError):
                    self.generator._acquire_git_launch_lease(
                        path,
                        expected_identity,
                        b"git",
                    )
            self.assertEqual(manager._reservations, set())
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual(
                acquisitions,
                [],
                "Windows executable was opened before its owner slot existed",
            )

        with self.subTest(component="windows-crt-descriptor"):
            manager = self.generator._GovernanceCleanupManager()
            acquisitions = []
            conversions: list[int] = []

            def create_executable(*_args: object) -> int:
                acquisitions.append(904)
                return 904

            def convert_handle(*_args: object) -> int:
                conversions.append(905)
                return 905

            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator,
                "_git_path_stat",
                return_value=info,
            ), mock.patch.object(
                self.generator,
                "_windows_git_ancestor_handles",
                return_value=((), ()),
            ), mock.patch.object(
                self.generator.secure_filesystem,
                "_windows_path_api",
                return_value=(create_executable, None, mock.Mock()),
            ), mock.patch.object(
                self.generator.secure_filesystem.msvcrt,
                "open_osfhandle",
                side_effect=convert_handle,
            ), mock.patch.object(
                self.generator,
                "_PosixDescriptorOwner",
                side_effect=MemoryError("CRT descriptor owner construction failed"),
            ):
                with self.assertRaises(self.generator.InventoryError):
                    self.generator._acquire_git_launch_lease(
                        path,
                        expected_identity,
                        b"git",
                    )
            self.assertEqual(manager._reservations, set())
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual(
                (acquisitions, conversions),
                ([], []),
                "CRT conversion preceded construction of its descriptor owner slot",
            )

    def _round6_post_acquisition_slots_cover_git_and_posix_lock(self) -> None:
        path = Path("C:/git.exe")
        info = mock.Mock(
            st_dev=1,
            st_ino=2,
            st_size=3,
            st_mtime_ns=4,
            st_ctime_ns=5,
            st_mode=stat.S_IFREG | 0o755,
            st_file_attributes=0,
            st_reparse_tag=0,
        )
        expected_identity = self.generator._git_stat_identity(info)

        with self.subTest(component="windows-ancestor-append"):
            manager = self.generator._GovernanceCleanupManager()
            closed: list[int] = []
            ancestor = Path("C:/")
            target_code = self.generator._windows_git_ancestor_handles.__code__
            append_offsets = {
                instruction.offset
                for instruction in dis.get_instructions(target_code)
                if instruction.opname in {"LOAD_METHOD", "LOAD_ATTR"}
                and instruction.argval == "append"
            }
            self.assertTrue(append_offsets)

            def create_ancestor(*_args: object) -> int:
                return 902

            def close_ancestor(handle: object) -> int:
                numeric = int(getattr(handle, "value", handle))
                closed.append(numeric)
                return 1

            injected = False

            def trace(frame: object, event: str, _argument: object) -> object:
                nonlocal injected
                if frame.f_code is target_code:
                    frame.f_trace_opcodes = True
                    if (
                        event == "opcode"
                        and frame.f_lasti in append_offsets
                        and frame.f_locals.get("numeric") == 902
                        and not injected
                    ):
                        injected = True
                        raise MemoryError("ancestor handle append failed")
                return trace

            previous_trace = sys.gettrace()
            try:
                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator.os,
                    "name",
                    "nt",
                ), mock.patch.object(
                    self.generator,
                    "_git_path_stat",
                    return_value=info,
                ), mock.patch.object(
                    self.generator,
                    "_git_ancestor_chain",
                    return_value=((ancestor, (11, 22, 0)),),
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_directory_api",
                    return_value=(create_ancestor, None, None, close_ancestor),
                ), mock.patch.object(
                    self.generator,
                    "_windows_governance_handle_is_open",
                    return_value=True,
                ):
                    sys.settrace(trace)
                    with self.assertRaises(self.generator.InventoryError):
                        self.generator._acquire_git_launch_lease(
                            path,
                            expected_identity,
                            b"git",
                        )
            finally:
                sys.settrace(previous_trace)
            self.assertTrue(injected)
            self.assertEqual(
                closed,
                [902],
                "post-create append failure leaked the ancestor handle",
            )
            self.assertEqual(manager._reservations, set())
            self.assertEqual(manager.pending_descriptors(), ())

        with self.subTest(component="posix-sidecar-post-open-identity"):
            manager = self.generator._GovernanceCleanupManager()
            reservation = manager.reserve()
            closed = []
            unlinked: list[tuple[str, int | None]] = []
            directory_info = mock.Mock(
                st_dev=21,
                st_ino=22,
                st_mode=stat.S_IFDIR | 0o700,
                st_file_attributes=0,
                st_reparse_tag=0,
            )
            opened = iter((701, 702))

            def fstat(descriptor: int) -> object:
                if descriptor == 701:
                    return directory_info
                raise MemoryError("sidecar identity construction failed")

            def unlink(name: str, *, dir_fd: int | None = None) -> None:
                unlinked.append((name, dir_fd))

            with tempfile.TemporaryDirectory(
                prefix="pontius-round6-posix-sidecar-"
            ) as temporary:
                target = Path(temporary) / "profiles.toml"
                destinations = self.generator._GovernanceDestinationSet.build(
                    (target,)
                )
                chain = ((
                    target.parent,
                    (21, 22, stat.S_IFDIR | 0o700, 0, 0),
                ),)
                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator.os,
                    "name",
                    "posix",
                ), mock.patch.object(
                    self.generator.os,
                    "open",
                    side_effect=lambda *_args, **_kwargs: next(opened),
                ), mock.patch.object(
                    self.generator.os,
                    "fstat",
                    side_effect=fstat,
                ), mock.patch.object(
                    self.generator.os,
                    "close",
                    side_effect=lambda descriptor: closed.append(descriptor),
                ), mock.patch.object(
                    self.generator.os,
                    "unlink",
                    side_effect=unlink,
                ), mock.patch.object(
                    self.generator,
                    "_governance_directory_chain",
                    return_value=chain,
                ):
                    with self.assertRaisesRegex(
                        self.generator.InventoryError,
                        "lock is busy",
                    ):
                        self.generator._GovernanceLockSetLease.acquire(
                            destinations,
                            reservation,
                        )
            self.assertEqual(
                closed,
                [702, 701],
                "post-open sidecar identity failure leaked its descriptor",
            )
            self.assertEqual(
                unlinked,
                [(".profiles.toml.pontius-governance.lock", 701)],
                "post-open sidecar identity failure orphaned its lock name",
            )
            self.assertEqual(manager._reservations, set())
            self.assertEqual(manager.pending_descriptors(), ())

    def _final3_windows_git_false_close_is_retained(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        path = Path("C:/git.exe")
        info = mock.Mock(
            st_dev=1,
            st_ino=2,
            st_size=3,
            st_mtime_ns=4,
            st_ctime_ns=5,
            st_mode=stat.S_IFREG | 0o755,
            st_file_attributes=0,
            st_reparse_tag=0,
        )
        expected = self.generator._git_stat_identity(info)
        close_allowed = False
        close_attempts = 0

        def close_raw(_handle: object) -> int:
            nonlocal close_attempts
            close_attempts += 1
            return 1 if close_allowed else 0

        with mock.patch.object(
            self.generator, "_GOVERNANCE_CLEANUP_MANAGER", manager
        ), mock.patch.object(
            self.generator, "_git_path_stat", return_value=info
        ), mock.patch.object(
            self.generator,
            "_windows_git_ancestor_handles",
            return_value=((), ()),
        ), mock.patch.object(
            self.generator.secure_filesystem,
            "_windows_path_api",
            return_value=(mock.Mock(return_value=910), None, close_raw),
        ), mock.patch.object(
            self.generator.secure_filesystem.msvcrt,
            "open_osfhandle",
            side_effect=OSError("CRT conversion failed"),
        ), mock.patch.object(
            self.generator,
            "_windows_governance_handle_is_open",
            return_value=True,
        ):
            with self.assertRaises(self.generator.InventoryError):
                self.generator._acquire_git_launch_lease(path, expected, b"git")
            descriptors = manager.pending_descriptors()
            try:
                self.assertEqual(len(descriptors), 1)
                self.assertEqual(
                    descriptors[0].outstanding_owner_roles,
                    ("git_executable_handle",),
                )
                self.assertEqual(close_attempts, 1)
            finally:
                close_allowed = True
                if descriptors:
                    manager.retry_pending(descriptors[0].retry_id)
            self.assertEqual(close_attempts, 2)
            self.assertEqual(manager.pending_descriptors(), ())

    def _round6_transferred_git_ancestor_close_protocol(self) -> None:
        path = Path("C:/git.exe")
        ancestor = Path("C:/")
        info = mock.Mock(
            st_dev=1,
            st_ino=2,
            st_size=3,
            st_mtime_ns=4,
            st_ctime_ns=5,
            st_mode=stat.S_IFREG | 0o755,
            st_file_attributes=0,
            st_reparse_tag=0,
        )
        expected = self.generator._git_stat_identity(info)

        for mode in ("explicit-false", "ambiguous-consumed"):
            with self.subTest(transferred_git_ancestor=mode):
                manager = self.generator._GovernanceCleanupManager()
                ancestor_close_attempts = 0
                descriptor_close_attempts = 0
                close_allowed = False
                ancestor_open = True

                def create_ancestor(*_args: object) -> int:
                    return 920

                def close_ancestor(_handle: object) -> int:
                    nonlocal ancestor_close_attempts, ancestor_open
                    ancestor_close_attempts += 1
                    if mode == "explicit-false":
                        if not close_allowed:
                            return 0
                        ancestor_open = False
                        return 1
                    if ancestor_close_attempts == 1:
                        ancestor_open = False
                        raise OSError("ancestor close consumed then raised")
                    raise AssertionError("ambiguous ancestor close was replayed")

                def close_descriptor(descriptor: int) -> None:
                    nonlocal descriptor_close_attempts
                    self.assertEqual(descriptor, 922)
                    descriptor_close_attempts += 1

                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator.os,
                    "name",
                    "nt",
                ), mock.patch.object(
                    self.generator,
                    "_git_path_stat",
                    return_value=info,
                ), mock.patch.object(
                    self.generator,
                    "_git_ancestor_chain",
                    return_value=((ancestor, (11, 22, 0)),),
                ), mock.patch.object(
                    self.generator,
                    "_revalidate_git_ancestor_chain",
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_directory_api",
                    return_value=(create_ancestor, None, None, close_ancestor),
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_directory_handle_identity",
                    return_value=(11, bytes((22,))),
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_path_api",
                    return_value=(
                        mock.Mock(return_value=921),
                        None,
                        mock.Mock(return_value=1),
                    ),
                ), mock.patch.object(
                    self.generator.secure_filesystem.msvcrt,
                    "open_osfhandle",
                    return_value=922,
                ), mock.patch.object(
                    self.generator.os,
                    "fstat",
                    return_value=info,
                ), mock.patch.object(
                    self.generator,
                    "_windows_governance_handle_is_open",
                    side_effect=lambda _handle: ancestor_open,
                ), mock.patch.object(
                    self.generator.os,
                    "close",
                    side_effect=close_descriptor,
                ):
                    lease = self.generator._acquire_git_launch_lease(
                        path,
                        expected,
                        b"git",
                    )
                    with self.assertRaises(self.generator.InventoryError):
                        lease.close()
                    if mode == "explicit-false":
                        close_allowed = True
                    lease.close()
                self.assertEqual(descriptor_close_attempts, 1)
                self.assertEqual(
                    ancestor_close_attempts,
                    2 if mode == "explicit-false" else 1,
                )
                self.assertEqual(manager._reservations, set())
                self.assertEqual(manager.pending_descriptors(), ())

    def _final_rereview_write_entries_and_undeclared_callback_are_prelock_safe(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-final-write-order-"
        ) as temporary:
            root = Path(temporary)
            (root / "tests").mkdir()
            review_path = root / "review.json"
            profile_path = root / "tests" / "test-profiles.toml"
            review_path.write_bytes(b"old-review\n")
            profile_path.write_bytes(b"old-profile\n")
            manager = self.generator._governance_cleanup_manager()
            held: list[tuple[object, object]] = []
            try:
                for target in (review_path, profile_path):
                    reservation = manager.reserve()
                    destination_set = self.generator._GovernanceDestinationSet.build(
                        (target,)
                    )
                    held.append(
                        (
                            self.generator._GovernanceLockSetLease.acquire(
                                destination_set,
                                reservation,
                            ),
                            reservation,
                        )
                    )
                captures: list[str] = []

                def observed_capture(*_args: object, **_kwargs: object) -> object:
                    captures.append("capture")
                    raise self.generator.InventoryError("capture observed")

                with mock.patch.object(
                    self.generator,
                    "_capture_design_inputs",
                    side_effect=observed_capture,
                ):
                    for keywords in ({}, {"enforce_repository_lock": False}):
                        with self.subTest(entry="review", keywords=keywords):
                            try:
                                self.generator.emit_design_review(
                                    root,
                                    review_path,
                                    **keywords,
                                )
                            except Exception:
                                pass
                        with self.subTest(entry="capabilities", keywords=keywords):
                            try:
                                self.generator.write_design_capabilities(
                                    root,
                                    approved_spec_capabilities_sha256="0" * 64,
                                    approved_design_review_receipt_sha256="0" * 64,
                                    **keywords,
                                )
                            except Exception:
                                pass
                    self.assertEqual(captures, [])
            finally:
                for lease, reservation in reversed(held):
                    lease.close()
                    manager.release(reservation)

        with tempfile.TemporaryDirectory(
            prefix="pontius-final-undeclared-"
        ) as temporary:
            root = Path(temporary)
            declared = root / "declared"
            undeclared = root / "undeclared"
            declared.write_bytes(b"old\n")
            undeclared.write_bytes(b"old\n")
            events: list[str] = []

            def undeclared_action(_revalidate: object) -> object:
                return self.generator.write_atomic_lf(undeclared, b"new\n")

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                side_effect=lambda *_args: (
                    events.append("git"),
                    (Path("C:/git.exe"), b"git", (1,)),
                )[1],
            ):
                try:
                    self.generator._with_governance_attribute_lease(
                        root,
                        Path("C:/git.exe"),
                        (declared,),
                        undeclared_action,
                    )
                except Exception:
                    pass
            self.assertEqual(events, [])
            self.assertEqual(undeclared.read_bytes(), b"old\n")

    def _final_rereview_cleanup_waiter_observes_joined_generation(self) -> None:
        first_error = OSError("generation one failed")
        calls = 0

        class Owner:
            def retry_pending_cleanup(inner_self) -> None:
                nonlocal calls
                calls += 1

        manager = self.generator._GovernanceCleanupManager()
        reservation = manager.reserve()
        retry_id = manager.transfer(reservation, Owner())
        pending = manager._pending[retry_id]
        pending.generation = 1
        pending.running = True
        results: dict[str, BaseException | None] = {}

        def invoke(label: str) -> None:
            try:
                manager.retry_pending(retry_id)
            except BaseException as error:
                results[label] = error
            else:
                results[label] = None

        waiter = threading.Thread(target=invoke, args=("waiter",))
        waiter.start()
        for _ in range(5000):
            with manager._condition:
                if pending.generation_joiners.get(1) == 1:
                    break
            threading.Event().wait(0.001)
        else:
            self.fail("generation-one waiter did not join")

        with manager._condition:
            pending.running = False
            pending.last_error = first_error
            pending.generation_results[1] = (False, first_error)
        barger = threading.Thread(target=invoke, args=("barger",))
        barger.start()
        for _ in range(5000):
            waiters = getattr(manager._condition, "_waiters", ())
            if len(waiters) >= 2:
                break
            threading.Event().wait(0.001)
        else:
            self.fail("generation-two barger did not wait for generation one")
        with manager._condition:
            manager._condition.notify_all()
        waiter.join(5)
        barger.join(5)
        self.assertFalse(waiter.is_alive())
        self.assertFalse(barger.is_alive())
        self.assertIsNotNone(results["waiter"])
        self.assertIs(results["waiter"].__cause__, first_error)
        self.assertIsNone(results["barger"])
        self.assertEqual(calls, 1)
        self.assertEqual(manager.pending_descriptors(), ())

    def _final_rereview_parent_fd_mismatch_is_provisionally_owned(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        reservation = manager.reserve()
        target = Path("C:/governed/profiles.toml")
        destinations = self.generator._GovernanceDestinationSet.build((target,))
        expected = (1, 2, stat.S_IFDIR | 0o700, 0, 0)
        mismatched = mock.Mock(st_dev=1, st_ino=3, st_mode=stat.S_IFDIR | 0o700)
        mismatched.st_file_attributes = 0
        mismatched.st_reparse_tag = 0
        closes: list[int] = []
        with mock.patch.object(
            self.generator.os, "name", "posix"
        ), mock.patch.object(
            self.generator,
            "_governance_directory_chain",
            return_value=((target.parent, expected),),
        ), mock.patch.object(
            self.generator.os, "open", return_value=701
        ), mock.patch.object(
            self.generator.os, "fstat", return_value=mismatched
        ), mock.patch.object(
            self.generator.os, "close", side_effect=lambda fd: closes.append(fd)
        ), self.assertRaises(Exception):
            self.generator._GovernanceLockSetLease.acquire(destinations, reservation)
        self.assertEqual(closes, [701])
        self.assertEqual(manager.pending_descriptors(), ())

    def _final_rereview_parent_only_pending_reports_no_locks(self) -> None:
        destination = Path("C:/governed/profiles.toml")
        destinations = self.generator._GovernanceDestinationSet.build((destination,))
        parent = mock.Mock(role="lock_parent_directory", closed=False)
        lease = self.generator._GovernanceLockSetLease(
            destinations,
            [parent],
            destinations.canonical_keys,
        )
        self.assertEqual(lease.outstanding_lock_keys(), ())
        self.assertEqual(lease.released_lock_keys(), ())
        self.assertEqual(lease.artifact_paths(), ())

    def _final_rereview_restoration_fsync_state_is_monotonic(self) -> None:
        state = self.generator._GovernancePublishState(
            published=True,
            displaced=True,
            recovery_name=".profiles.recovery",
        )
        self.assertTrue(
            hasattr(state, "parent_sync_pending"),
            "restored namespace state must retain only the pending directory sync",
        )

    def _final_rereview_absent_target_link_success_owns_both_names(self) -> None:
        staging = ".profiles.new.tmp"
        publish_state = self.generator._GovernancePublishState()
        outcome = self.generator._GovernanceWriteOutcome()
        regular = mock.Mock(st_mode=stat.S_IFREG | 0o600)
        with mock.patch.object(
            self.generator.os,
            "fstat",
            return_value=regular,
        ), mock.patch.object(
            self.generator.os,
            "stat",
            return_value=regular,
        ), mock.patch.object(
            self.generator.secure_filesystem,
            "_path_handle_identity",
            return_value=(1, 2),
        ), mock.patch.object(
            self.generator,
            "_require_governance_destination_identity",
        ), mock.patch.object(
            self.generator.os,
            "link",
        ), mock.patch.object(
            self.generator.os,
            "unlink",
            side_effect=OSError("staging unlink failed after link"),
        ), self.assertRaisesRegex(OSError, "staging unlink"):
            self.generator._publish_staged_governance(
                temporary_name=staging,
                temporary_handle=801,
                destination_name="profiles.toml",
                parent_handle=802,
                windows=False,
                destination_path=Path("C:/governed/profiles.toml"),
                expected_identity=None,
                expected_raw=None,
                state=publish_state,
                outcome=outcome,
            )
        self.assertTrue(publish_state.published)
        self.assertTrue(outcome.published)
        self.assertEqual(publish_state.staging_name, staging)

    def _assert_binding_regression_helpers_are_discovered(self) -> None:
        methods = {
            name: value
            for name, value in vars(type(self)).items()
            if callable(value)
        }
        binding_helpers = {
            name
            for name in methods
            if name.startswith(("_final", "_round"))
        }
        edges: dict[str, set[str]] = {}
        for name, method in methods.items():
            edges[name] = {
                str(instruction.argval)
                for instruction in dis.get_instructions(method)
                if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD"}
                and isinstance(instruction.argval, str)
                and instruction.argval.startswith(("_final", "_round"))
            }
        pending = [name for name in methods if name.startswith("test_")]
        reachable: set[str] = set()
        while pending:
            name = pending.pop()
            if name in reachable:
                continue
            reachable.add(name)
            pending.extend(edges.get(name, ()))
        self.assertEqual(
            binding_helpers - reachable,
            set(),
            "binding-marked regression helpers must be reached by discovered tests",
        )

        missing_symbols: set[tuple[str, str]] = set()
        for name in binding_helpers:
            instructions = tuple(dis.get_instructions(methods[name]))
            for index, instruction in enumerate(instructions[:-1]):
                if instruction.opname != "LOAD_ATTR" or instruction.argval != "generator":
                    continue
                following = instructions[index + 1]
                if following.opname not in {"LOAD_ATTR", "LOAD_METHOD"}:
                    continue
                symbol = str(following.argval)
                if not hasattr(self.generator, symbol):
                    missing_symbols.add((name, symbol))
        self.assertEqual(
            missing_symbols,
            set(),
            "binding regression helpers must not reference removed production symbols",
        )

    def test_lock_set_precedes_all_destination_and_lifetime_observation(
        self,
    ) -> None:
        self._assert_binding_regression_helpers_are_discovered()
        round5_checks = (
            (
                "closed-publication-rejects-legacy-callback",
                self._final2_legacy_callback_is_rejected_before_git_or_source_work,
            ),
            (
                "parent-probe-failure-immediate-owner",
                self._final2_parent_probe_failure_is_immediately_owned,
            ),
            (
                "posix-staging-probe-failure-namespace-owner",
                self._final2_posix_staging_probe_failure_is_namespace_owned,
            ),
            (
                "posix-real-exchange-replace-link-rollback",
                self._final2_posix_real_writer_rollback_schedules,
            ),
            (
                "real-multicomponent-git-acquisition",
                self._final2_real_multicomponent_git_acquisition_is_independent,
            ),
            (
                "first-sidecar-open-parent-only-truth",
                self._final2_sidecar_open_failure_reports_parent_only_truth,
            ),
            (
                "windows-sidecar-never-invents-release",
                self._final3_windows_sidecar_failure_never_invents_released_lock,
            ),
            (
                "windows-parent-probe-owner",
                self._final3_windows_parent_probe_failure_is_manager_owned,
            ),
            (
                "git-owner-slots-precede-acquisition",
                self._final3_git_component_owners_precede_every_acquisition,
            ),
            (
                "round6-post-acquisition-owner-slots",
                self._round6_post_acquisition_slots_cover_git_and_posix_lock,
            ),
            (
                "windows-git-false-close-retained",
                self._final3_windows_git_false_close_is_retained,
            ),
            (
                "round6-transferred-git-ancestor-close",
                self._round6_transferred_git_ancestor_close_protocol,
            ),
            (
                "distinct-owner-family-number-reuse",
                self._final2_distinct_owner_families_never_replay_reused_numbers,
            ),
            (
                "same-inode-descriptor-reuse",
                self._final_rereview_same_inode_same_fd_reuse_is_never_retried,
            ),
            (
                "all-write-entry-ordering",
                self._final_rereview_write_entries_and_undeclared_callback_are_prelock_safe,
            ),
            (
                "captured-cleanup-generation-result",
                self._final_rereview_cleanup_waiter_observes_joined_generation,
            ),
            (
                "provisional-parent-descriptor",
                self._final_rereview_parent_fd_mismatch_is_provisionally_owned,
            ),
            (
                "parent-only-pending-truth",
                self._final_rereview_parent_only_pending_reports_no_locks,
            ),
            (
                "posix-restoration-sync-state",
                self._final_rereview_restoration_fsync_state_is_monotonic,
            ),
            (
                "absent-target-link-unlink-trap",
                self._final_rereview_absent_target_link_success_owns_both_names,
            ),
            (
                "lock-before-observation",
                self._round5_operation_entry_locks_before_git_source_and_destination_reads,
            ),
            (
                "explicit-destination-set",
                self._round5_dict_captured_undeclared_target_is_not_inferred,
            ),
            (
                "active-group-membership",
                self._round5_active_group_rejects_write_outside_declared_set_before_io,
            ),
            (
                "post-lock-alias-rejection",
                self._round5_active_group_hardlink_pair_rejects_before_participants,
            ),
            (
                "exclusive-cleanup-generation",
                self._round5_cleanup_retry_is_exclusive_per_generation,
            ),
            (
                "retry-before-capacity",
                self._round5_writer_retries_recoverable_full_capacity_before_reserving,
            ),
            (
                "component-idempotent-git-cleanup",
                self._round5_git_launch_lease_cleanup_is_component_idempotent,
            ),
            (
                "truthful-partial-lock-ownership",
                self._round5_partial_lock_release_descriptor_reports_exact_ownership,
            ),
            (
                "posix-parent-fd-anchoring",
                self._round5_posix_parent_exchange_is_refused_by_anchored_lock,
            ),
            (
                "posix-descriptor-reuse-safety",
                self._round5_posix_close_succeeded_then_raised_never_retries_reused_fd,
            ),
            (
                "retain-mode-pre-dispatch-validation",
                self._round5_invalid_retain_mode_refuses_before_dispatch_or_directory_io,
            ),
        )
        for label, check in round5_checks:
            with self.subTest(round5=label):
                check()
        if os.name != "nt":
            return
        with self.subTest(mode="standalone"), tempfile.TemporaryDirectory(
            prefix="pontius-governance-lock-order-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            events: list[str] = []
            real_read = self.generator.secure_filesystem.read_regular_snapshot
            real_create = self.generator._windows_create_relative_governance_file

            def observed_read(path: Path, **keywords: object) -> object:
                if path == target:
                    events.append("destination-read")
                return real_read(path, **keywords)

            def observed_create(
                directory_handle: int,
                name: str,
                **keywords: object,
            ) -> int:
                if name.endswith(".lock"):
                    events.append("lock-acquired")
                return real_create(directory_handle, name, **keywords)

            with mock.patch.object(
                self.generator.secure_filesystem,
                "read_regular_snapshot",
                side_effect=observed_read,
            ), mock.patch.object(
                self.generator,
                "_windows_create_relative_governance_file",
                side_effect=observed_create,
            ):
                self.generator.write_atomic_lf(target, b"new\n")
            self.assertLess(
                events.index("lock-acquired"),
                events.index("destination-read"),
            )

        with self.subTest(mode="pair"), tempfile.TemporaryDirectory(
            prefix="pontius-governance-lock-pair-order-"
        ) as temporary:
            root = Path(temporary)
            first = root / "inventory.json"
            second = root / "profiles.toml"
            first.write_bytes(b"old-first\n")
            second.write_bytes(b"old-second\n")
            real_read = self.generator.secure_filesystem.read_regular_snapshot
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
            events = []
            real_create = self.generator._windows_create_relative_governance_file

            def observed_pair_create(
                directory_handle: int,
                name: str,
                **keywords: object,
            ) -> int:
                handle = real_create(directory_handle, name, **keywords)
                if name.endswith(".lock"):
                    events.append(f"lock:{name}")
                return handle

            def observed_lifetime() -> None:
                events.append("lifetime")

            with mock.patch.object(
                self.generator,
                "_windows_create_relative_governance_file",
                side_effect=observed_pair_create,
            ):
                self.generator._write_governance_pair(
                    first,
                    b"new-first\n",
                    second,
                    b"new-second\n",
                    lifetime_check=observed_lifetime,
                )
            first_lifetime = events.index("lifetime")
            self.assertEqual(
                len([event for event in events[:first_lifetime] if event.startswith("lock:")]),
                2,
            )

        with self.subTest(mode="outer-git"), tempfile.TemporaryDirectory(
            prefix="pontius-governance-lock-git-order-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            events = []
            lease = mock.Mock()
            lease.close.return_value = None
            real_create = self.generator._windows_create_relative_governance_file

            def observed_outer_create(
                directory_handle: int,
                name: str,
                **keywords: object,
            ) -> int:
                handle = real_create(directory_handle, name, **keywords)
                if name.endswith(".lock"):
                    events.append("lock")
                return handle

            def acquire_lease(*args: object, **keywords: object) -> object:
                events.append("git")
                return lease

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                return_value=(Path("C:/git.exe"), b"git", (1,)),
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                side_effect=acquire_lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ), mock.patch.object(
                self.generator,
                "_windows_create_relative_governance_file",
                side_effect=observed_outer_create,
            ):
                self.generator._with_governance_attribute_lease(
                    root,
                    Path("C:/git.exe"),
                    self.generator._GovernancePublicationOperation(
                        (target,),
                        self.generator._GovernancePreparedPublication(
                            self.generator._GovernanceSinglePublication(
                                b"new\n"
                            )
                        ),
                    ),
                )
            self.assertLess(events.index("lock"), events.index("git"))

    def test_partial_lock_cleanup_is_reserved_and_retryable(self) -> None:
        manager = self.generator._governance_cleanup_manager()
        reservation = manager.reserve()
        close_allowed = False
        events: list[str] = []
        open_count = 0

        def fake_open(*args: object, **kwargs: object) -> int:
            nonlocal open_count
            open_count += 1
            if open_count == 1:
                return 41
            if open_count == 2:
                return 42
            raise FileExistsError("second governance lock is busy")

        directory_info = mock.Mock(
            st_dev=1,
            st_ino=2,
            st_mode=stat.S_IFDIR | 0o700,
            st_file_attributes=0,
            st_reparse_tag=0,
        )
        lock_info = mock.Mock(
            st_dev=1,
            st_ino=3,
            st_mode=stat.S_IFREG | 0o600,
        )

        def fake_fstat(descriptor: int) -> object:
            return directory_info if descriptor == 41 else lock_info

        def fake_close(descriptor: int) -> None:
            events.append(f"close:{descriptor}")
            if not close_allowed:
                raise OSError("lock descriptor remains open")

        def fake_unlink(name: str, **kwargs: object) -> None:
            events.append(f"unlink:{name}")

        with tempfile.TemporaryDirectory(
            prefix="pontius-partial-governance-lock-"
        ) as temporary:
            root = Path(temporary)
            destinations = self.generator._GovernanceDestinationSet.build(
                (root / "inventory.json", root / "profiles.toml")
            )
            chain = ((root, (1, 2, stat.S_IFDIR | 0o700, 0, 0)),)
            with mock.patch.object(
                self.generator.os,
                "name",
                "posix",
            ), mock.patch.object(
                self.generator.os,
                "open",
                side_effect=fake_open,
            ), mock.patch.object(
                self.generator.os,
                "close",
                side_effect=fake_close,
            ), mock.patch.object(
                self.generator.os,
                "unlink",
                side_effect=fake_unlink,
            ), mock.patch.object(
                self.generator.os,
                "fstat",
                side_effect=fake_fstat,
            ), mock.patch.object(
                self.generator,
                "_governance_directory_chain",
                return_value=chain,
            ):
                with self.assertRaisesRegex(
                    self.generator.InventoryError,
                    "lock is busy",
                ):
                    self.generator._GovernanceLockSetLease.acquire(
                        destinations,
                        reservation,
                    )
        self.assertEqual(manager.pending_descriptors(), ())
        self.assertLess(events.index("close:42"), events.index(
            "unlink:.inventory.json.pontius-governance.lock"
        ))
        self.assertEqual(events[-1], "close:41")

    def test_posix_lock_closes_before_unlinking_its_name(self) -> None:
        manager = self.generator._governance_cleanup_manager()
        reservation = manager.reserve()
        events: list[str] = []
        with tempfile.TemporaryDirectory(
            prefix="pontius-posix-governance-lock-order-"
        ) as temporary:
            destination = Path(temporary) / "profiles.toml"
            destinations = self.generator._GovernanceDestinationSet.build(
                (destination,)
            )
            directory_info = mock.Mock(
                st_dev=1,
                st_ino=2,
                st_mode=stat.S_IFDIR | 0o700,
                st_file_attributes=0,
                st_reparse_tag=0,
            )
            lock_info = mock.Mock(
                st_dev=1,
                st_ino=3,
                st_mode=stat.S_IFREG | 0o600,
            )
            opened = iter((43, 44))
            with mock.patch.object(
                self.generator.os,
                "name",
                "posix",
            ), mock.patch.object(
                self.generator.os,
                "open",
                side_effect=lambda *args, **kwargs: next(opened),
            ), mock.patch.object(
                self.generator.os,
                "fstat",
                side_effect=lambda descriptor: (
                    directory_info if descriptor == 43 else lock_info
                ),
            ), mock.patch.object(
                self.generator.os,
                "close",
                side_effect=lambda descriptor: events.append(
                    f"close:{descriptor}"
                ),
            ), mock.patch.object(
                self.generator.os,
                "unlink",
                side_effect=lambda name, **kwargs: events.append(f"unlink:{name}"),
            ), mock.patch.object(
                self.generator,
                "_governance_directory_chain",
                return_value=((
                    destination.parent,
                    (1, 2, stat.S_IFDIR | 0o700, 0, 0),
                ),),
            ):
                lease = self.generator._GovernanceLockSetLease.acquire(
                    destinations,
                    reservation,
                )
                lease.close()
        manager.release(reservation)
        self.assertEqual(
            events,
            [
                "close:44",
                "unlink:.profiles.toml.pontius-governance.lock",
                "close:43",
            ],
        )

        reservation = manager.reserve()
        close_calls = 0
        unlink_calls = 0
        unlink_allowed = False

        def counted_close(descriptor: int) -> None:
            nonlocal close_calls
            close_calls += 1

        def flaky_unlink(name: str, **kwargs: object) -> None:
            nonlocal unlink_calls
            unlink_calls += 1
            if not unlink_allowed:
                raise OSError("lock name remains present")

        with tempfile.TemporaryDirectory(
            prefix="pontius-posix-governance-lock-unlink-"
        ) as temporary:
            destination = Path(temporary) / "profiles.toml"
            destinations = self.generator._GovernanceDestinationSet.build(
                (destination,)
            )
            directory_info = mock.Mock(
                st_dev=1,
                st_ino=2,
                st_mode=stat.S_IFDIR | 0o700,
                st_file_attributes=0,
                st_reparse_tag=0,
            )
            lock_info = mock.Mock(
                st_dev=1,
                st_ino=3,
                st_mode=stat.S_IFREG | 0o600,
            )
            opened = iter((47, 48))
            with mock.patch.object(
                self.generator.os,
                "name",
                "posix",
            ), mock.patch.object(
                self.generator.os,
                "open",
                side_effect=lambda *args, **kwargs: next(opened),
            ), mock.patch.object(
                self.generator.os,
                "fstat",
                side_effect=lambda descriptor: (
                    directory_info if descriptor == 47 else lock_info
                ),
            ), mock.patch.object(
                self.generator.os,
                "close",
                side_effect=counted_close,
            ), mock.patch.object(
                self.generator.os,
                "unlink",
                side_effect=flaky_unlink,
            ), mock.patch.object(
                self.generator,
                "_governance_directory_chain",
                return_value=((
                    destination.parent,
                    (1, 2, stat.S_IFDIR | 0o700, 0, 0),
                ),),
            ):
                lease = self.generator._GovernanceLockSetLease.acquire(
                    destinations,
                    reservation,
                )
                with self.assertRaisesRegex(Exception, "lock release"):
                    lease.close()
                unlink_allowed = True
                lease.close()
        manager.release(reservation)
        self.assertEqual(close_calls, 2)
        self.assertEqual(unlink_calls, 2)

    def test_windows_lock_disposition_failure_retains_owner(self) -> None:
        manager = self.generator._governance_cleanup_manager()
        reservation = manager.reserve()
        close_allowed = False
        disposition_allowed = False
        file_close_calls = 0
        disposition_calls = 0

        def create_lock(
            directory_handle: int,
            name: str,
            *,
            owner: object,
            **keywords: object,
        ) -> int:
            owner.handle = 53
            owner.state = "open"
            return 53

        def close_file(handle: int) -> bool:
            nonlocal file_close_calls
            file_close_calls += 1
            if not close_allowed:
                return False
            return True

        def dispose_lock(handle: int) -> None:
            nonlocal disposition_calls
            disposition_calls += 1
            if not disposition_allowed:
                raise OSError("disposition failed")

        with tempfile.TemporaryDirectory(
            prefix="pontius-windows-governance-lock-disposition-"
        ) as temporary:
            destination = Path(temporary) / "profiles.toml"
            destinations = self.generator._GovernanceDestinationSet.build(
                (destination,)
            )
            with mock.patch.object(
                self.generator.os,
                "name",
                "nt",
            ), mock.patch.object(
                self.generator,
                "_windows_open_governance_directory",
                return_value=(51, (1, b"directory")),
            ), mock.patch.object(
                self.generator,
                "_windows_create_relative_governance_file",
                side_effect=create_lock,
            ), mock.patch.object(
                self.generator,
                "_windows_dispose_governance_lock",
                side_effect=dispose_lock,
            ), mock.patch.object(
                self.generator,
                "_windows_try_close_file",
                side_effect=close_file,
            ), mock.patch.object(
                self.generator.secure_filesystem,
                "_windows_close_directory",
            ), mock.patch.object(
                self.generator,
                "_windows_governance_handle_is_open",
                return_value=True,
            ):
                with self.assertRaises(
                    self.generator.GovernanceCleanupPendingError
                ) as caught:
                    self.generator._GovernanceLockSetLease.acquire(
                        destinations,
                        reservation,
                    )
                self.assertIn(
                    "deterministic_lock",
                    caught.exception.descriptor.outstanding_owner_roles,
                )
                disposition_allowed = True
                close_allowed = True
                manager.retry_pending(caught.exception.retry_id)
        self.assertGreaterEqual(disposition_calls, 4)
        self.assertEqual(file_close_calls, 1)
        self.assertEqual(manager.pending_descriptors(), ())

    def test_windows_reversed_pair_writers_use_one_canonical_lock_order(
        self,
    ) -> None:
        if os.name != "nt":
            return
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-reversed-pair-"
        ) as temporary:
            root = Path(temporary)
            first = root / "inventory.json"
            second = root / "profiles.toml"
            first.write_bytes(b"first\n")
            second.write_bytes(b"second\n")
            forward = self.generator._GovernanceDestinationSet.build((first, second))
            reverse = self.generator._GovernanceDestinationSet.build((second, first))
            self.assertEqual(forward.canonical_keys, reverse.canonical_keys)
            acquired = threading.Event()
            release = threading.Event()
            winner_errors: list[BaseException] = []
            loser_errors: list[BaseException] = []
            manager = self.generator._governance_cleanup_manager()
            winner_reservation = manager.reserve()
            loser_reservation = manager.reserve()

            def winner() -> None:
                try:
                    lease = self.generator._GovernanceLockSetLease.acquire(
                        forward,
                        winner_reservation,
                    )
                    acquired.set()
                    if not release.wait(5):
                        raise AssertionError("winner release timed out")
                    first.write_bytes(b"winner-first\n")
                    second.write_bytes(b"winner-second\n")
                    lease.close()
                    manager.release(winner_reservation)
                except BaseException as error:
                    winner_errors.append(error)

            def loser() -> None:
                if not acquired.wait(5):
                    loser_errors.append(AssertionError("winner acquire timed out"))
                    return
                try:
                    lease = self.generator._GovernanceLockSetLease.acquire(
                        reverse,
                        loser_reservation,
                    )
                except BaseException as error:
                    loser_errors.append(error)
                else:
                    lease.close()
                    manager.release(loser_reservation)
                    loser_errors.append(AssertionError("reversed writer acquired locks"))
                finally:
                    release.set()

            first_thread = threading.Thread(target=winner, daemon=True)
            second_thread = threading.Thread(target=loser, daemon=True)
            first_thread.start()
            second_thread.start()
            first_thread.join(10)
            second_thread.join(10)
            release.set()
            self.assertFalse(first_thread.is_alive())
            self.assertFalse(second_thread.is_alive())
            self.assertFalse(winner_errors)
            self.assertEqual(len(loser_errors), 1)
            self.assertRegex(str(loser_errors[0]), "lock|writer|busy")
            self.assertEqual(first.read_bytes(), b"winner-first\n")
            self.assertEqual(second.read_bytes(), b"winner-second\n")
            self.assertEqual({path.name for path in root.iterdir()}, {first.name, second.name})

    def test_pair_retains_complete_lock_set_through_last_child_cleanup(
        self,
    ) -> None:
        if os.name != "nt":
            return
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-pair-retention-"
        ) as temporary:
            root = Path(temporary)
            first = root / "inventory.json"
            second = root / "profiles.toml"
            first.write_bytes(b"first\n")
            second.write_bytes(b"second\n")
            destinations = self.generator._GovernanceDestinationSet.build(
                (first, second)
            )
            manager = self.generator._governance_cleanup_manager()
            reservation = manager.reserve()
            lease = self.generator._GovernanceLockSetLease.acquire(
                destinations,
                reservation,
            )
            group = self.generator._GovernanceWriteGroup(lease, reservation)
            intruder_errors: list[BaseException] = []
            intruder_reads = 0
            real_read = self.generator.secure_filesystem.read_regular_snapshot

            class Participant:
                def __init__(self, owner: object, first_participant: bool) -> None:
                    self.owner = owner
                    self.first_participant = first_participant

                def prepare(self) -> None:
                    return None

                def publish(self) -> None:
                    return None

                def validate(self) -> None:
                    return None

                def rollback_step(self) -> None:
                    return None

                def cleanup_committed_step(self) -> None:
                    if not self.first_participant:
                        return
                    try:
                        self.owner.write_atomic_lf(first, b"intruder\n")
                    except BaseException as error:
                        intruder_errors.append(error)

            def observed_read(path: Path, **keywords: object) -> object:
                nonlocal intruder_reads
                if path == first:
                    intruder_reads += 1
                return real_read(path, **keywords)

            group.add_participant(Participant(self.generator, True))
            group.add_participant(Participant(self.generator, False))
            with mock.patch.object(
                self.generator.secure_filesystem,
                "read_regular_snapshot",
                side_effect=observed_read,
            ):
                group.prepare_all()
                group.publish_all()
                group.validate_all(None)
                group.mark_committed()
                group.finish_committed_cleanup()
            self.assertEqual(len(intruder_errors), 1)
            self.assertRegex(str(intruder_errors[0]), "lock|writer|busy")
            self.assertEqual(intruder_reads, 0)
            self.generator.write_atomic_lf(first, b"after-release\n")
            self.assertEqual(first.read_bytes(), b"after-release\n")
            self.assertEqual(manager.pending_descriptors(), ())

    def test_duplicate_and_native_alias_destinations_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-destination-alias-"
        ) as temporary:
            root = Path(temporary)
            first = root / "inventory.json"
            first.write_bytes(b"old\n")
            with self.subTest(alias="exact"), self.assertRaisesRegex(
                self.generator.InventoryError,
                "duplicate|alias",
            ):
                self.generator._GovernanceDestinationSet.build((first, first))
            if os.name == "nt":
                with self.subTest(alias="case"), self.assertRaisesRegex(
                    self.generator.InventoryError,
                    "duplicate|alias",
                ):
                    self.generator._GovernanceDestinationSet.build(
                        (first, root / "INVENTORY.JSON")
                    )

            hardlink = root / "profiles.toml"
            os.link(first, hardlink)
            first_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                first,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            hardlink_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                hardlink,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            with self.subTest(alias="hardlink"), self.assertRaisesRegex(
                self.generator.InventoryError,
                "native.*alias|same.*file|hard.?link",
            ):
                self.generator._write_governance_pair(
                    first,
                    b"new-first\n",
                    hardlink,
                    b"new-second\n",
                )
            self.assertEqual(first.read_bytes(), b"old\n")
            self.assertEqual(hardlink.read_bytes(), b"old\n")
            self.assertEqual({path.name for path in root.iterdir()}, {first.name, hardlink.name})

    def test_pair_marks_one_commit_and_never_rolls_back_after_cleanup_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-logical-pair-commit-"
        ) as temporary:
            root = Path(temporary)
            first = root / "inventory.json"
            second = root / "profiles.toml"
            first.write_bytes(b"old-first\n")
            second.write_bytes(b"old-second\n")
            manager = self.generator._governance_cleanup_manager()
            reservation = manager.reserve()
            destinations = self.generator._GovernanceDestinationSet.build(
                (first, second)
            )
            lease = self.generator._GovernanceLockSetLease.acquire(
                destinations,
                reservation,
            )
            group = self.generator._GovernanceWriteGroup(lease, reservation)
            cleanup_allowed = False
            rollback_calls = 0

            class Participant:
                def __init__(self, path: Path, raw: bytes, fail: bool) -> None:
                    self.path = path
                    self.raw = raw
                    self.fail = fail
                    self.cleaned = False

                def prepare(self) -> None:
                    return None

                def publish(self) -> None:
                    self.path.write_bytes(self.raw)

                def validate(self) -> None:
                    self.owner.assertEqual(self.path.read_bytes(), self.raw)

                def rollback_step(self) -> None:
                    nonlocal rollback_calls
                    rollback_calls += 1

                def cleanup_committed_step(self) -> None:
                    if self.cleaned:
                        return
                    if self.fail and not cleanup_allowed:
                        raise OSError("second participant cleanup remains open")
                    self.cleaned = True

            first_participant = Participant(first, b"new-first\n", False)
            second_participant = Participant(second, b"new-second\n", True)
            first_participant.owner = self
            second_participant.owner = self
            group.add_participant(first_participant)
            group.add_participant(second_participant)
            group.prepare_all()
            group.publish_all()
            group.validate_all(None)
            group.mark_committed()
            with self.assertRaises(
                self.generator.GovernanceCommittedWithCleanupFailure
            ) as caught:
                group.finish_committed_cleanup()
            descriptor = caught.exception.descriptor
            self.assertTrue(caught.exception.committed)
            self.assertEqual(descriptor.decision, "committed")
            self.assertEqual(
                set(descriptor.destination_paths),
                {str(first), str(second)},
            )
            self.assertEqual(
                descriptor.output_sha256[str(first)],
                sha256(b"new-first\n").hexdigest(),
            )
            self.assertEqual(
                descriptor.output_sha256[str(second)],
                sha256(b"new-second\n").hexdigest(),
            )
            self.assertEqual(rollback_calls, 0)
            self.assertEqual(first.read_bytes(), b"new-first\n")
            self.assertEqual(second.read_bytes(), b"new-second\n")
            self.assertIn("participant", descriptor.outstanding_owner_roles)
            cleanup_allowed = True
            manager.retry_pending(caught.exception.retry_id)
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual(rollback_calls, 0)
            self.assertEqual({path.name for path in root.iterdir()}, {first.name, second.name})

    def test_precommit_persistent_close_transfers_rollback_ownership(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-precommit-pending-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            manager = self.generator._governance_cleanup_manager()
            reservation = manager.reserve()
            destinations = self.generator._GovernanceDestinationSet.build((target,))
            lease = self.generator._GovernanceLockSetLease.acquire(
                destinations,
                reservation,
            )
            group = self.generator._GovernanceWriteGroup(lease, reservation)
            rollback_allowed = False

            class Participant:
                def prepare(self) -> None:
                    return None

                def publish(self) -> None:
                    target.write_bytes(b"new\n")

                def validate(self) -> None:
                    raise OSError("final validation failed")

                def rollback_step(self) -> None:
                    if not rollback_allowed:
                        raise OSError("rollback close remains open")
                    target.write_bytes(b"old\n")

                def cleanup_committed_step(self) -> None:
                    raise AssertionError("precommit participant cleaned as committed")

            group.add_participant(Participant())
            group.prepare_all()
            group.publish_all()
            primary = OSError("final validation failed")
            with self.assertRaises(
                self.generator.GovernanceCleanupPendingError
            ) as caught:
                group.abort_precommit(primary)
            descriptor = caught.exception.descriptor
            self.assertFalse(caught.exception.committed)
            self.assertEqual(descriptor.decision, "rollback_required")
            self.assertEqual(descriptor.destination_paths, (str(target),))
            self.assertTrue(descriptor.lock_keys)
            self.assertEqual(target.read_bytes(), b"new\n")
            rollback_allowed = True
            manager.retry_pending(caught.exception.retry_id)
            self.assertEqual(target.read_bytes(), b"old\n")
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual({path.name for path in root.iterdir()}, {target.name})

    def test_committed_git_lease_cleanup_failure_is_explicit_and_retryable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-git-cleanup-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            cleanup_allowed = False
            close_calls = 0

            class Lease:
                def close(self) -> None:
                    nonlocal close_calls
                    close_calls += 1
                    if not cleanup_allowed:
                        raise OSError("Git lease remains open")

            lease = Lease()

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                return_value=(Path("C:/git.exe"), b"git", (1,)),
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ):
                with self.assertRaises(
                    self.generator.GovernanceCommittedWithCleanupFailure
                ) as caught:
                    self.generator._with_governance_attribute_lease(
                        root,
                        Path("C:/git.exe"),
                        self.generator._GovernancePublicationOperation(
                            (target,),
                            self.generator._GovernancePreparedPublication(
                                self.generator._GovernanceSinglePublication(
                                    b"new\n"
                                )
                            ),
                        ),
                    )
            self.assertEqual(target.read_bytes(), b"new\n")
            self.assertEqual(caught.exception.descriptor.decision, "committed")
            self.assertIn(
                "git_lease",
                caught.exception.descriptor.outstanding_owner_roles,
            )
            self.assertGreaterEqual(close_calls, 3)
            cleanup_allowed = True
            manager = self.generator._governance_cleanup_manager()
            manager.retry_pending(caught.exception.retry_id)
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual(close_calls, 4)

    def test_committed_attribute_temp_cleanup_failure_is_explicit_and_retryable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-attribute-cleanup-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            attribute_root = root / "attribute-temp"
            cleanup_allowed = False
            cleanup_calls = 0

            class TemporaryEnvironment:
                def __enter__(self) -> str:
                    attribute_root.mkdir()
                    return str(attribute_root)

                def __exit__(
                    self,
                    exc_type: object,
                    exc: object,
                    traceback: object,
                ) -> None:
                    nonlocal cleanup_calls
                    cleanup_calls += 1
                    if not cleanup_allowed:
                        raise OSError("attribute temp cleanup remains open")
                    attribute_root.rmdir()

            lease = mock.Mock()
            lease.close.return_value = None

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                return_value=(Path("C:/git.exe"), b"git", (1,)),
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ), mock.patch.object(
                self.generator.tempfile,
                "TemporaryDirectory",
                return_value=TemporaryEnvironment(),
            ):
                with self.assertRaises(
                    self.generator.GovernanceCommittedWithCleanupFailure
                ) as caught:
                    self.generator._with_governance_attribute_lease(
                        root,
                        Path("C:/git.exe"),
                        self.generator._GovernancePublicationOperation(
                            (target,),
                            self.generator._GovernancePreparedPublication(
                                self.generator._GovernanceSinglePublication(
                                    b"new\n"
                                )
                            ),
                        ),
                    )
            self.assertEqual(target.read_bytes(), b"new\n")
            self.assertTrue(attribute_root.is_dir())
            self.assertEqual(caught.exception.descriptor.decision, "committed")
            self.assertIn(
                "attribute_environment",
                caught.exception.descriptor.outstanding_owner_roles,
            )
            cleanup_allowed = True
            manager = self.generator._governance_cleanup_manager()
            manager.retry_pending(caught.exception.retry_id)
            self.assertFalse(attribute_root.exists())
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual(cleanup_calls, 4)

    def test_committed_attribute_temp_cleanup_succeeded_then_raised_is_final(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-attribute-closed-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            attribute_root = root / "attribute-temp"
            cleanup_calls = 0

            class TemporaryEnvironment:
                def __enter__(self) -> str:
                    attribute_root.mkdir()
                    return str(attribute_root)

                def __exit__(
                    self,
                    exc_type: object,
                    exc: object,
                    traceback: object,
                ) -> None:
                    nonlocal cleanup_calls
                    cleanup_calls += 1
                    attribute_root.rmdir()
                    raise OSError("attribute cleanup succeeded then raised")

            lease = mock.Mock()
            lease.close.return_value = None

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                return_value=(Path("C:/git.exe"), b"git", (1,)),
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ), mock.patch.object(
                self.generator.tempfile,
                "TemporaryDirectory",
                return_value=TemporaryEnvironment(),
            ):
                result = self.generator._with_governance_attribute_lease(
                    root,
                    Path("C:/git.exe"),
                    self.generator._GovernancePublicationOperation(
                        (target,),
                        self.generator._GovernancePreparedPublication(
                            self.generator._GovernanceSinglePublication(
                                b"new\n",
                                value="published",
                            )
                        ),
                    ),
                )
            self.assertEqual(result, "published")
            self.assertEqual(target.read_bytes(), b"new\n")
            self.assertFalse(attribute_root.exists())
            self.assertEqual(cleanup_calls, 1)
            self.assertEqual(
                self.generator._governance_cleanup_manager().pending_descriptors(),
                (),
            )

    def test_cleanup_manager_retries_before_next_writer_observation_and_is_bounded(
        self,
    ) -> None:
        manager = self.generator._governance_cleanup_manager()
        self.assertEqual(self.generator.MAXIMUM_PENDING_GOVERNANCE_CLEANUPS, 16)
        self.assertEqual(self.generator.GOVERNANCE_CLEANUP_SYNCHRONOUS_RETRIES, 3)
        events: list[str] = []
        recoverable = False

        class Pending:
            def retry_pending_cleanup(self) -> None:
                events.append("retry")
                if not recoverable:
                    raise OSError("pending cleanup")

            def pending_descriptor(self, retry_id: int, attempts: int) -> object:
                return mock.Mock(
                    retry_id=retry_id,
                    attempts=attempts,
                    decision="committed",
                    outstanding_owner_roles=("test_owner",),
                )

        reservation = manager.reserve()
        retry_id = manager.transfer(reservation, Pending())
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-manager-order-"
        ) as temporary:
            target = Path(temporary) / "profiles.toml"
            target.write_bytes(b"old\n")
            real_read = self.generator.secure_filesystem.read_regular_snapshot

            def observed_read(path: Path, **keywords: object) -> object:
                events.append("read")
                return real_read(path, **keywords)

            with mock.patch.object(
                self.generator.secure_filesystem,
                "read_regular_snapshot",
                side_effect=observed_read,
            ), self.assertRaisesRegex(Exception, "pending cleanup"):
                self.generator.write_atomic_lf(target, b"new\n")
            self.assertEqual(events[0], "retry")
            self.assertNotIn("read", events)
            recoverable = True
            manager.retry_pending(retry_id)
            self.assertEqual(manager.pending_descriptors(), ())

        reservations = [manager.reserve() for _ in range(16)]
        with self.assertRaisesRegex(Exception, "cleanup.*capacity"):
            manager.reserve()
        for reservation in reservations:
            manager.transfer(reservation, Pending())
        recoverable = True
        manager.retry_pending()
        self.assertEqual(manager.pending_descriptors(), ())

    def test_cleanup_manager_atexit_retry_retains_unresolved_entries(self) -> None:
        manager = self.generator._governance_cleanup_manager()
        self.assertEqual(manager.atexit_registration_count, 1)
        recoverable_allowed = False
        persistent_allowed = False

        class Pending:
            def __init__(self, recoverable: bool) -> None:
                self.recoverable = recoverable

            def retry_pending_cleanup(self) -> None:
                if self.recoverable and recoverable_allowed:
                    return
                if not self.recoverable and persistent_allowed:
                    return
                raise OSError("persistent cleanup")

            def pending_descriptor(self, retry_id: int, attempts: int) -> object:
                return mock.Mock(
                    retry_id=retry_id,
                    attempts=attempts,
                    decision="committed",
                    outstanding_owner_roles=("test_owner",),
                )

        recoverable_id = manager.transfer(manager.reserve(), Pending(True))
        persistent_id = manager.transfer(manager.reserve(), Pending(False))
        recoverable_allowed = True
        manager.retry_at_exit()
        descriptors = manager.pending_descriptors()
        self.assertEqual([row.retry_id for row in descriptors], [persistent_id])
        self.assertNotEqual(recoverable_id, persistent_id)
        persistent_allowed = True
        manager.retry_pending(persistent_id)
        self.assertEqual(manager.pending_descriptors(), ())

    def test_cleanup_manager_first_use_is_synchronized(self) -> None:
        self.assertTrue(
            hasattr(self.generator, "_GOVERNANCE_CLEANUP_MANAGER_MUTEX")
        )
        self.generator._GOVERNANCE_CLEANUP_MANAGER = None
        registrations: list[object] = []
        with mock.patch.object(
            self.generator.atexit,
            "register",
            side_effect=lambda action: registrations.append(action),
        ):
            workers = [
                threading.Thread(
                    target=self.generator._governance_cleanup_manager
                )
                for _ in range(16)
            ]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=5)
            self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(len(registrations), 1)
        self.assertEqual(
            self.generator._governance_cleanup_manager().atexit_registration_count,
            1,
        )

    def test_ordinary_success_leaves_manager_empty_and_zero_artifacts(self) -> None:
        self.assertFalse(
            hasattr(self.generator, "_best_effort_governance_close")
        )
        self.assertFalse(
            hasattr(self.generator._GovernanceWriteTransaction, "finalize")
        )
        manager = self.generator._governance_cleanup_manager()
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-manager-success-"
        ) as temporary:
            root = Path(temporary)
            first = root / "inventory.json"
            second = root / "profiles.toml"
            first.write_bytes(b"old-first\n")
            second.write_bytes(b"old-second\n")
            first_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                first,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            second_snapshot = self.generator.secure_filesystem.read_regular_snapshot(
                second,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            self.generator._write_governance_pair(
                first,
                b"new-first\n",
                second,
                b"new-second\n",
            )
            absent = root / "review.json"
            self.generator.write_atomic_lf(absent, b"review\n")
            lease = mock.Mock()
            lease.close.return_value = None
            outer_existing = root / "outer-existing.toml"
            outer_absent = root / "outer-absent.json"
            outer_existing.write_bytes(b"old-outer\n")
            outer_absent.write_bytes(b"old-absent\n")

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                return_value=(Path("C:/git.exe"), b"git", (1,)),
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=lease,
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ):
                self.generator._with_governance_attribute_lease(
                    root,
                    Path("C:/git.exe"),
                    self.generator._GovernancePublicationOperation(
                        (outer_existing, outer_absent),
                        self.generator._GovernancePreparedPublication(
                            self.generator._GovernancePairPublication(
                                b"new-outer\n",
                                b"new-absent\n",
                            )
                        ),
                    ),
                )
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {
                    first.name,
                    second.name,
                    absent.name,
                    outer_existing.name,
                    outer_absent.name,
                },
            )

    def _final3_windows_staging_cleanup_is_monotonic(self) -> None:
        for mode in ("fail-before-close", "close-succeeded-then-raised"):
            with self.subTest(staging_close=mode), tempfile.TemporaryDirectory(
                prefix=f"pontius-final3-staging-{mode}-",
                ignore_cleanup_errors=True,
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                target.write_bytes(b"old\n")
                manager = self.generator._GovernanceCleanupManager()
                handles: set[int] = set()
                staging_handle: int | None = None
                close_attempts = 0
                injected = False
                real_open_directory = (
                    self.generator._windows_open_governance_directory
                )
                real_create = (
                    self.generator._windows_create_relative_governance_file
                )
                real_write = self.generator.secure_filesystem._write_staged_bytes
                real_close = self.generator._windows_try_close_file

                def capture_directory(
                    path: Path,
                    **keywords: object,
                ) -> tuple[int, tuple[int, bytes]]:
                    opened = real_open_directory(path, **keywords)
                    handles.add(opened[0])
                    return opened

                def capture_create(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal staging_handle
                    handle = real_create(directory, name, **keywords)
                    handles.add(handle)
                    if name.endswith(".tmp"):
                        staging_handle = handle
                    return handle

                def reject_after_staging_write(
                    handle: int,
                    raw: bytes,
                    *,
                    windows: bool,
                ) -> None:
                    real_write(handle, raw, windows=windows)
                    raise OSError("force rollback before publication")

                def fail_staging_close(handle: int) -> bool:
                    nonlocal close_attempts, injected
                    if handle == staging_handle:
                        if mode == "fail-before-close":
                            close_attempts += 1
                            return False
                        if not injected:
                            close_attempts += 1
                            injected = True
                            real_close(handle)
                            handles.discard(handle)
                            raise OSError(f"staging {mode}")
                    succeeded = real_close(handle)
                    handles.discard(handle)
                    return succeeded

                caught: BaseException | None = None
                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_governance_directory",
                    side_effect=capture_directory,
                ), mock.patch.object(
                    self.generator,
                    "_windows_create_relative_governance_file",
                    side_effect=capture_create,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_write_staged_bytes",
                    side_effect=reject_after_staging_write,
                ), mock.patch.object(
                    self.generator,
                    "_windows_try_close_file",
                    side_effect=fail_staging_close,
                ):
                    try:
                        self.generator.write_atomic_lf(target, b"new\n")
                    except BaseException as error:
                        caught = error

                descriptors = manager.pending_descriptors()
                try:
                    if mode == "fail-before-close":
                        self.assertGreaterEqual(close_attempts, 2)
                        self.assertIsInstance(
                            caught,
                            self.generator.GovernanceCleanupPendingError,
                        )
                        self.assertEqual(len(descriptors), 1)
                        self.assertIn(
                            "staging",
                            descriptors[0].outstanding_owner_roles,
                        )
                        self.assertTrue(
                            any(
                                Path(path).name.endswith(".tmp")
                                for path in descriptors[0].artifact_paths
                            )
                        )
                    else:
                        self.assertEqual(close_attempts, 1)
                        self.assertIsInstance(caught, OSError)
                        self.assertNotIsInstance(
                            caught,
                            self.generator.GovernanceCleanupPendingError,
                        )
                        self.assertRegex(str(caught), "force rollback")
                        self.assertEqual(descriptors, ())
                finally:
                    for descriptor in manager.pending_descriptors():
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException:
                            pass
                    for handle in tuple(handles):
                        try:
                            real_close(handle)
                        except BaseException:
                            pass
                    with manager._condition:
                        manager._pending.clear()
                        manager._reservations.clear()
                    for artifact in tuple(root.iterdir()):
                        if artifact != target:
                            try:
                                artifact.unlink()
                            except OSError:
                                pass

    def _round6_windows_writer_directory_owner_is_monotonic(self) -> None:
        real_api = self.generator.secure_filesystem._windows_directory_api()
        real_create, query, information, real_close = real_api
        real_identity = (
            self.generator.secure_filesystem._windows_directory_handle_identity
        )

        for mode in ("probe-false", "final-false", "final-ambiguous"):
            with self.subTest(publication_directory=mode), (
                tempfile.TemporaryDirectory(
                    prefix=f"pontius-round6-writer-directory-{mode}-",
                    ignore_cleanup_errors=True,
                )
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                target.write_bytes(b"old\n")
                manager = self.generator._GovernanceCleanupManager()
                created: list[int] = []
                publication_handle: int | None = None
                close_attempts = 0
                close_allowed = False
                probe_injected = False

                def numeric(handle: object) -> int:
                    return int(getattr(handle, "value", handle))

                def create(*args: object) -> object:
                    nonlocal publication_handle
                    opened = real_create(*args)
                    value = numeric(opened)
                    created.append(value)
                    if len(created) == 2:
                        publication_handle = value
                    return opened

                def identity(handle: int, path: Path) -> tuple[int, bytes]:
                    nonlocal probe_injected
                    if (
                        mode == "probe-false"
                        and handle == publication_handle
                        and not probe_injected
                    ):
                        probe_injected = True
                        raise OSError("publication directory identity failed")
                    return real_identity(handle, path)

                def close(handle: object) -> int:
                    nonlocal close_attempts
                    value = numeric(handle)
                    if value == publication_handle:
                        close_attempts += 1
                        if mode in {"probe-false", "final-false"}:
                            if not close_allowed:
                                return 0
                        elif close_attempts == 1:
                            succeeded = real_close(handle)
                            if not succeeded:
                                return 0
                            raise OSError(
                                "publication directory close consumed then raised"
                            )
                        else:
                            raise AssertionError(
                                "ambiguous publication directory close was replayed"
                            )
                    return int(bool(real_close(handle)))

                caught: BaseException | None = None
                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_directory_api",
                    return_value=(create, query, information, close),
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_directory_handle_identity",
                    side_effect=identity,
                ):
                    try:
                        self.generator.write_atomic_lf(target, b"new\n")
                    except BaseException as error:
                        caught = error
                descriptors = manager.pending_descriptors()
                try:
                    self.assertIsNotNone(publication_handle)
                    if mode == "probe-false":
                        self.assertTrue(probe_injected)
                        self.assertIsInstance(
                            caught,
                            self.generator.GovernanceCleanupPendingError,
                        )
                        self.assertEqual(target.read_bytes(), b"old\n")
                    elif mode == "final-false":
                        self.assertIsInstance(
                            caught,
                            self.generator.GovernanceCommittedWithCleanupFailure,
                        )
                        self.assertEqual(target.read_bytes(), b"new\n")
                    else:
                        self.assertIsNone(caught)
                        self.assertEqual(target.read_bytes(), b"new\n")
                        self.assertEqual(close_attempts, 1)
                        self.assertEqual(descriptors, ())
                    if mode != "final-ambiguous":
                        self.assertEqual(len(descriptors), 1)
                        self.assertIn(
                            "directory",
                            descriptors[0].outstanding_owner_roles,
                        )
                        close_allowed = True
                        manager.retry_pending(descriptors[0].retry_id)
                        self.assertEqual(manager.pending_descriptors(), ())
                finally:
                    for descriptor in manager.pending_descriptors():
                        close_allowed = True
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException:
                            pass
                    if publication_handle is not None:
                        try:
                            if self.generator._windows_governance_handle_is_open(
                                publication_handle
                            ):
                                real_close(
                                    self.generator.secure_filesystem.wintypes.HANDLE(
                                        publication_handle
                                    )
                                )
                        except BaseException:
                            pass

    def _round6_windows_auxiliary_file_owners_are_retryable(self) -> None:
        real_open_raw = self.generator._windows_open_relative_governance_file_raw
        real_close_raw = self.generator.secure_filesystem._windows_close_file
        real_try_close = self.generator._windows_try_close_file

        for role in ("original", "readback"):
            with self.subTest(auxiliary_windows_owner=role), (
                tempfile.TemporaryDirectory(
                    prefix=f"pontius-round6-windows-{role}-",
                    ignore_cleanup_errors=True,
                )
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                if role == "original":
                    target.write_bytes(b"old\n")
                manager = self.generator._GovernanceCleanupManager()
                selected_handle: int | None = None
                published_read_count = 0
                close_attempts = 0
                close_allowed = False
                live_handles: set[int] = set()
                lifetime_checks = 0

                def capture_open(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal selected_handle, published_read_count
                    handle = real_open_raw(directory, name, **keywords)
                    live_handles.add(handle)
                    if role == "original" and (
                        name == target.name
                        and keywords.get("share_write") is True
                        and not keywords.get("read_data", False)
                    ):
                        selected_handle = handle
                    if role == "readback" and (
                        name == target.name
                        and keywords.get("read_data") is True
                        and keywords.get("share_write", True) is True
                    ):
                        published_read_count += 1
                        selected_handle = handle
                    return handle

                def close_raw(handle: int) -> object:
                    nonlocal close_attempts
                    if handle == selected_handle and not close_allowed:
                        close_attempts += 1
                        return False
                    result = real_close_raw(handle)
                    live_handles.discard(handle)
                    return result

                def try_close(handle: int) -> bool:
                    nonlocal close_attempts
                    if handle == selected_handle and not close_allowed:
                        close_attempts += 1
                        return False
                    result = real_try_close(handle)
                    if result:
                        live_handles.discard(handle)
                    return result

                def fail_after_publish() -> None:
                    nonlocal lifetime_checks
                    lifetime_checks += 1
                    if role == "readback" and lifetime_checks == 2:
                        raise OSError("force absent-target rollback")

                caught: BaseException | None = None
                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_relative_governance_file_raw",
                    side_effect=capture_open,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_close_file",
                    side_effect=close_raw,
                ), mock.patch.object(
                    self.generator,
                    "_windows_try_close_file",
                    side_effect=try_close,
                ):
                    try:
                        self.generator.write_atomic_lf(
                            target,
                            b"new\n",
                            _lifetime_check=(
                                fail_after_publish if role == "readback" else None
                            ),
                        )
                    except BaseException as error:
                        caught = error
                descriptors = manager.pending_descriptors()
                try:
                    self.assertIsNotNone(selected_handle)
                    self.assertGreaterEqual(
                        close_attempts,
                        1,
                        "known non-consuming closes remain retryable",
                    )
                    self.assertIsInstance(
                        caught,
                        self.generator.GovernanceCleanupPendingError,
                    )
                    self.assertEqual(len(descriptors), 1)
                    self.assertIn(
                        role,
                        descriptors[0].outstanding_owner_roles,
                    )
                    close_allowed = True
                    manager.retry_pending(descriptors[0].retry_id)
                    self.assertEqual(manager.pending_descriptors(), ())
                    if role == "original":
                        self.assertEqual(target.read_bytes(), b"old\n")
                    else:
                        self.assertFalse(target.exists())
                finally:
                    for descriptor in manager.pending_descriptors():
                        close_allowed = True
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException:
                            pass
                    for handle in tuple(live_handles):
                        try:
                            real_close_raw(handle)
                        except BaseException:
                            pass

    def _round6_windows_namespace_free_ambiguous_closes_reconcile(self) -> None:
        real_directory_open = self.generator._windows_open_governance_directory
        real_directory_close = (
            self.generator.secure_filesystem._windows_close_directory
        )
        real_create = self.generator._windows_create_relative_governance_file
        real_open = self.generator._windows_open_relative_governance_file
        real_open_raw = self.generator._windows_open_relative_governance_file_raw
        real_try_close = self.generator._windows_try_close_file

        for role in ("staging", "published", "recovery"):
            with self.subTest(namespace_free_ambiguous=role), (
                tempfile.TemporaryDirectory(
                    prefix=f"pontius-round6-ambiguous-{role}-",
                    ignore_cleanup_errors=True,
                )
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                target.write_bytes(b"old\n")
                with mock.patch.object(self.generator.atexit, "register"):
                    manager = self.generator._GovernanceCleanupManager()
                selected_handle: int | None = None
                handle_roles: dict[int, str] = {}
                file_handles: set[int] = set()
                directory_handles: set[int] = set()
                close_attempts = 0
                lifetime_checks = 0

                def capture_directory(
                    path: Path,
                    **keywords: object,
                ) -> tuple[int, tuple[int, bytes]]:
                    opened = real_directory_open(path, **keywords)
                    directory_handles.add(opened[0])
                    return opened

                def capture_create(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal selected_handle
                    handle = real_create(directory, name, **keywords)
                    file_handles.add(handle)
                    owner_role = (
                        "deterministic_lock"
                        if name.endswith(".pontius-governance.lock")
                        else "staging"
                    )
                    handle_roles[handle] = owner_role
                    if role == "staging" and owner_role == role:
                        selected_handle = handle
                    return handle

                def capture_open(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal selected_handle
                    handle = real_open(directory, name, **keywords)
                    file_handles.add(handle)
                    owner_role = "recovery"
                    handle_roles[handle] = owner_role
                    if role == owner_role:
                        selected_handle = handle
                    return handle

                def capture_open_raw(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal selected_handle
                    handle = real_open_raw(directory, name, **keywords)
                    file_handles.add(handle)
                    owner_role = (
                        "published"
                        if name == target.name
                        and keywords.get("read_data") is True
                        and keywords.get("share_write") is False
                        else "auxiliary"
                    )
                    handle_roles[handle] = owner_role
                    if role == owner_role:
                        selected_handle = handle
                    return handle

                def close_file(handle: int) -> bool:
                    nonlocal close_attempts
                    current_role = handle_roles.get(handle)
                    if handle == selected_handle and current_role == role:
                        close_attempts += 1
                        if close_attempts > 1:
                            raise AssertionError(
                                f"ambiguous {role} handle close was replayed"
                            )
                        succeeded = real_try_close(handle)
                        if succeeded:
                            file_handles.discard(handle)
                        raise OSError(f"ambiguous {role} close consumed then raised")
                    succeeded = real_try_close(handle)
                    if succeeded:
                        file_handles.discard(handle)
                    return succeeded

                def fail_after_publish() -> None:
                    nonlocal lifetime_checks
                    lifetime_checks += 1
                    if role == "recovery" and lifetime_checks == 2:
                        raise OSError("force recovery restoration")

                caught: BaseException | None = None
                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_governance_directory",
                    side_effect=capture_directory,
                ), mock.patch.object(
                    self.generator,
                    "_windows_create_relative_governance_file",
                    side_effect=capture_create,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_relative_governance_file",
                    side_effect=capture_open,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_relative_governance_file_raw",
                    side_effect=capture_open_raw,
                ), mock.patch.object(
                    self.generator,
                    "_windows_try_close_file",
                    side_effect=close_file,
                ):
                    try:
                        self.generator.write_atomic_lf(
                            target,
                            b"new\n",
                            _lifetime_check=(
                                fail_after_publish if role == "recovery" else None
                            ),
                        )
                    except BaseException as error:
                        caught = error
                try:
                    self.assertIsNotNone(selected_handle)
                    self.assertEqual(close_attempts, 1)
                    self.assertEqual(manager.pending_descriptors(), ())
                    if role == "published":
                        self.assertIsNone(caught)
                        self.assertEqual(target.read_bytes(), b"new\n")
                    else:
                        self.assertIsNotNone(caught)
                        self.assertNotIsInstance(
                            caught,
                            self.generator.GovernanceCleanupPendingError,
                        )
                        self.assertEqual(target.read_bytes(), b"old\n")
                finally:
                    for handle in tuple(file_handles):
                        try:
                            if self.generator._windows_governance_handle_is_open(
                                handle
                            ):
                                real_try_close(handle)
                        except BaseException:
                            pass
                    for handle in tuple(directory_handles):
                        try:
                            if self.generator._windows_governance_handle_is_open(
                                handle
                            ):
                                real_directory_close(handle)
                        except BaseException:
                            pass
                    for artifact in tuple(root.iterdir()):
                        if artifact != target:
                            try:
                                artifact.unlink()
                            except OSError:
                                pass

    def _final3_windows_writer_reused_handles_are_role_isolated(self) -> None:
        for selected_role in (
            "staging",
            "published",
            "recovery",
            "directory",
            "deterministic_lock",
        ):
            with self.subTest(reused_writer_role=selected_role), (
                tempfile.TemporaryDirectory(
                    prefix=f"pontius-final3-reuse-{selected_role}-",
                    ignore_cleanup_errors=True,
                )
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                target.write_bytes(b"old\n")
                manager = self.generator._GovernanceCleanupManager()
                handles: dict[str, int] = {}
                replacement: int | None = None
                selected_close_attempts = 0
                real_open_directory = (
                    self.generator._windows_open_governance_directory
                )
                real_create = (
                    self.generator._windows_create_relative_governance_file
                )
                real_open = self.generator._windows_open_relative_governance_file
                real_open_raw = (
                    self.generator._windows_open_relative_governance_file_raw
                )
                real_close_file = self.generator._windows_try_close_file
                real_close_directory = (
                    self.generator.secure_filesystem._windows_close_directory
                )
                directory_api = (
                    self.generator.secure_filesystem._windows_directory_api()
                )
                raw_close_directory = directory_api[3]

                def capture_directory(
                    path: Path,
                    **keywords: object,
                ) -> tuple[int, tuple[int, bytes]]:
                    opened = real_open_directory(path, **keywords)
                    handles["directory"] = opened[0]
                    return opened

                def capture_create(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    handle = real_create(directory, name, **keywords)
                    if name.endswith(".pontius-governance.lock"):
                        handles["deterministic_lock"] = handle
                        handles["lock_directory"] = directory
                    elif name.endswith(".tmp"):
                        handles["staging"] = handle
                    return handle

                def capture_open(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    handle = real_open(directory, name, **keywords)
                    if name.endswith(".recovery"):
                        handles["recovery"] = handle
                    return handle

                def capture_open_raw(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    handle = real_open_raw(directory, name, **keywords)
                    if (
                        name == target.name
                        and keywords.get("read_data") is True
                        and keywords.get("share_write") is False
                        and keywords.get("delete_access") is False
                    ):
                        handles["published"] = handle
                    return handle

                def reopen_same_file_handle(handle: int) -> bool:
                    nonlocal replacement, selected_close_attempts
                    selected_close_attempts += 1
                    real_close_file(handle)
                    replacement = real_open_raw(
                        handles[
                            "lock_directory"
                            if selected_role == "deterministic_lock"
                            else "directory"
                        ],
                        target.name,
                        share_write=True,
                    )
                    raise OSError("selected close consumed then raised")

                def close_file(handle: int) -> bool:
                    if (
                        handle == handles.get(selected_role)
                        and selected_close_attempts == 0
                    ):
                        reopen_same_file_handle(handle)
                    return real_close_file(handle)

                def close_directory(handle: object) -> int:
                    nonlocal replacement, selected_close_attempts
                    numeric = int(getattr(handle, "value", handle))
                    if (
                        selected_role == "directory"
                        and numeric == handles.get("directory")
                        and selected_close_attempts == 0
                    ):
                        selected_close_attempts += 1
                        raw_close_directory(handle)
                        replacement = real_open_directory(root)[0]
                        raise OSError("selected close consumed then raised")
                    return int(bool(raw_close_directory(handle)))

                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_governance_directory",
                    side_effect=capture_directory,
                ), mock.patch.object(
                    self.generator,
                    "_windows_create_relative_governance_file",
                    side_effect=capture_create,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_relative_governance_file",
                    side_effect=capture_open,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_relative_governance_file_raw",
                    side_effect=capture_open_raw,
                ), mock.patch.object(
                    self.generator,
                    "_windows_try_close_file",
                    side_effect=close_file,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_directory_api",
                    return_value=(
                        directory_api[0],
                        directory_api[1],
                        directory_api[2],
                        close_directory,
                    ),
                ):
                    try:
                        self.generator.write_atomic_lf(target, b"new\n")
                    except BaseException:
                        pass
                try:
                    self.assertEqual(selected_close_attempts, 1)
                    self.assertEqual(
                        replacement,
                        handles[selected_role],
                        "native handle was not deterministically reused",
                    )
                    self.assertTrue(
                        self.generator._windows_governance_handle_is_open(
                            replacement
                        ),
                        "an earlier writer role replay-closed the later owner",
                    )
                finally:
                    if replacement is not None:
                        try:
                            if selected_role == "directory":
                                real_close_directory(replacement)
                            else:
                                real_close_file(replacement)
                        except BaseException:
                            pass
                    for descriptor in manager.pending_descriptors():
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException:
                            retained = manager._pending[descriptor.retry_id].owner
                            for participant in retained.participants:
                                participant.cleaned = True
                            try:
                                retained.lock_set.close()
                            except BaseException:
                                pass
                    with manager._condition:
                        manager._pending.clear()
                        manager._reservations.clear()
                    for artifact in tuple(root.iterdir()):
                        if artifact != target:
                            try:
                                artifact.unlink()
                            except OSError:
                                pass

    def _round7_windows_file_owners_bind_before_caller_failure(self) -> None:
        real_open_directory = self.generator._windows_open_governance_directory
        real_create = self.generator._windows_create_relative_governance_file
        real_open_raw = self.generator._windows_open_relative_governance_file_raw
        real_try_close = self.generator._windows_try_close_file

        for family in (
            "staging",
            "original",
            "recovery",
            "published",
            "readback",
            "published_disposal",
        ):
            with self.subTest(prebound_owner_family=family), (
                tempfile.TemporaryDirectory(
                    prefix=f"pontius-round7-prebound-{family}-",
                    ignore_cleanup_errors=True,
                )
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                unrelated = root / "unrelated.txt"
                unrelated.write_bytes(b"unrelated\n")
                if family != "published_disposal":
                    target.write_bytes(b"old\n")
                with mock.patch.object(self.generator.atexit, "register"):
                    manager = self.generator._GovernanceCleanupManager()
                selected_handle: int | None = None
                selected_directory: int | None = None
                selected_owner: object | None = None
                replacement: int | None = None
                replacement_identity: tuple[int, int] | None = None
                replacement_blockers: list[int] = []
                close_attempts = 0
                injected = False

                def owner_family(
                    owner: object | None,
                    keywords: dict[str, object],
                ) -> str | None:
                    role = getattr(owner, "role", None)
                    if role != "published":
                        return role if isinstance(role, str) else None
                    if (
                        keywords.get("read_data") is True
                        and keywords.get("share_write") is False
                        and keywords.get("delete_access") is False
                    ):
                        return "published"
                    return "published_disposal"

                def capture_directory(
                    path: Path,
                    **keywords: object,
                ) -> tuple[int, tuple[int, bytes]]:
                    return real_open_directory(path, **keywords)

                def capture_create(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal selected_handle, selected_directory
                    nonlocal selected_owner, injected
                    handle = real_create(directory, name, **keywords)
                    owner = keywords.get("owner")
                    if (
                        family == "staging"
                        and getattr(owner, "role", None) == "staging"
                        and not injected
                    ):
                        injected = True
                        selected_handle = handle
                        selected_directory = directory
                        selected_owner = owner
                        raise OSError("failure immediately after staged-file acquisition")
                    return handle

                def capture_open_raw(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal selected_handle, selected_directory
                    nonlocal selected_owner, injected
                    handle = real_open_raw(directory, name, **keywords)
                    owner = keywords.get("owner")
                    if owner_family(owner, keywords) == family and not injected:
                        injected = True
                        selected_handle = handle
                        selected_directory = directory
                        selected_owner = owner
                        raise OSError(
                            f"failure immediately after {family} acquisition"
                        )
                    return handle

                def consume_then_reuse(handle: int) -> bool:
                    nonlocal replacement, replacement_identity, close_attempts
                    if handle == selected_handle and close_attempts == 0:
                        close_attempts += 1
                        if not real_try_close(handle):
                            raise AssertionError("selected owner handle did not close")
                        if selected_directory is None:
                            raise AssertionError("selected owner directory is absent")
                        for _ in range(4096):
                            candidate = real_open_raw(
                                selected_directory,
                                unrelated.name,
                                read_data=True,
                                share_write=True,
                                delete_access=False,
                            )
                            if candidate == handle:
                                replacement = candidate
                                replacement_identity = (
                                    self.generator._windows_governance_handle_file_id(
                                        candidate
                                    )
                                )
                                break
                            replacement_blockers.append(candidate)
                        if replacement is None:
                            raise AssertionError(
                                "native handle reuse could not be forced"
                            )
                        raise OSError(
                            f"{family} close consumed then raised before retry"
                        )
                    if handle == replacement:
                        raise AssertionError(
                            "ambiguous owner replay-closed the reused handle"
                        )
                    return real_try_close(handle)

                def reject_after_publish(_snapshot: object) -> None:
                    raise OSError("force absent-target rollback")

                caught: BaseException | None = None
                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_governance_directory",
                    side_effect=capture_directory,
                ), mock.patch.object(
                    self.generator,
                    "_windows_create_relative_governance_file",
                    side_effect=capture_create,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_relative_governance_file_raw",
                    side_effect=capture_open_raw,
                ), mock.patch.object(
                    self.generator,
                    "_windows_try_close_file",
                    side_effect=consume_then_reuse,
                ):
                    try:
                        self.generator.write_atomic_lf(
                            target,
                            b"new\n",
                            _post_publish_lifetime_check=(
                                reject_after_publish
                                if family == "published_disposal"
                                else None
                            ),
                        )
                    except BaseException as error:
                        caught = error

                descriptors = manager.pending_descriptors()
                retry_error: BaseException | None = None
                if descriptors:
                    for descriptor in descriptors:
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException as error:
                            retry_error = error
                    descriptors = manager.pending_descriptors()
                try:
                    self.assertTrue(injected, f"{family} acquisition was not reached")
                    self.assertEqual(close_attempts, 1)
                    self.assertEqual(replacement, selected_handle)
                    self.assertIsNotNone(selected_owner)
                    self.assertIsNotNone(
                        getattr(selected_owner, "expected_identity", None),
                        f"{family} owner was returned without an identity",
                    )
                    self.assertIsNotNone(caught)
                    self.assertIsNone(
                        retry_error,
                        (
                            f"{family} retry did not reconcile its bound owner: "
                            f"cause={getattr(retry_error, '__cause__', None)!r}; "
                            f"descriptors={descriptors!r}; owner={selected_owner!r}; "
                            f"replacement_identity={replacement_identity!r}"
                        ),
                    )
                    self.assertEqual(descriptors, ())
                    self.assertTrue(
                        self.generator._windows_governance_handle_is_open(
                            replacement
                        ),
                        "cleanup replay-closed an unrelated reused handle",
                    )
                    if family == "published_disposal":
                        self.assertFalse(target.exists())
                    else:
                        self.assertEqual(target.read_bytes(), b"old\n")
                    self.assertEqual(
                        {path.name for path in root.iterdir()},
                        ({target.name, unrelated.name} if target.exists() else {unrelated.name}),
                    )
                finally:
                    if replacement is not None:
                        try:
                            real_try_close(replacement)
                        except BaseException:
                            pass
                    for blocker in replacement_blockers:
                        try:
                            real_try_close(blocker)
                        except BaseException:
                            pass
                    for _ in range(3):
                        descriptors = manager.pending_descriptors()
                        if not descriptors:
                            break
                        for descriptor in descriptors:
                            try:
                                manager.retry_pending(descriptor.retry_id)
                            except BaseException:
                                pass
                    for descriptor in manager.pending_descriptors():
                        retained = manager._pending[descriptor.retry_id].owner
                        for participant in retained.participants:
                            participant.cleaned = True
                        try:
                            retained.lock_set.close()
                        except BaseException:
                            pass
                    with manager._condition:
                        manager._pending.clear()
                        manager._reservations.clear()
                    for artifact in tuple(root.iterdir()):
                        try:
                            artifact.unlink()
                        except OSError:
                            pass

    def _round9_windows_disposition_absence_beats_same_inode_reuse(self) -> None:
        real_create = self.generator._windows_create_relative_governance_file
        real_open_raw = self.generator._windows_open_relative_governance_file_raw
        real_try_close = self.generator._windows_try_close_file

        for family in ("staging", "published_disposal", "recovery"):
            with self.subTest(disposition_same_inode_reuse=family), (
                tempfile.TemporaryDirectory(
                    prefix=f"pontius-round9-same-inode-{family}-",
                    ignore_cleanup_errors=True,
                )
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                alias = root / f"{family}.hardlink"
                if family != "published_disposal":
                    target.write_bytes(b"old\n")
                with mock.patch.object(self.generator.atexit, "register"):
                    manager = self.generator._GovernanceCleanupManager()
                selected_handle: int | None = None
                selected_directory: int | None = None
                selected_owner: object | None = None
                replacement: int | None = None
                blockers: list[int] = []
                injected = False
                close_attempts = 0

                def classify(
                    owner: object | None,
                    keywords: dict[str, object],
                ) -> str | None:
                    role = getattr(owner, "role", None)
                    if role != "published":
                        return role if isinstance(role, str) else None
                    if (
                        keywords.get("read_data") is True
                        and keywords.get("share_write") is False
                        and keywords.get("delete_access") is False
                    ):
                        return "published"
                    return "published_disposal"

                def capture_create(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal selected_handle, selected_directory
                    nonlocal selected_owner, injected
                    handle = real_create(directory, name, **keywords)
                    owner = keywords.get("owner")
                    if family == "staging" and getattr(owner, "role", None) == family:
                        selected_handle = handle
                        selected_directory = directory
                        selected_owner = owner
                        injected = True
                        os.link(getattr(owner, "artifact_path"), alias)
                        raise OSError("fail immediately after staging acquisition")
                    return handle

                def capture_open_raw(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal selected_handle, selected_directory
                    nonlocal selected_owner, injected
                    handle = real_open_raw(directory, name, **keywords)
                    owner = keywords.get("owner")
                    if classify(owner, keywords) == family and not injected:
                        selected_handle = handle
                        selected_directory = directory
                        selected_owner = owner
                        injected = True
                        os.link(getattr(owner, "artifact_path"), alias)
                    return handle

                def consume_then_reopen_alias(handle: int) -> bool:
                    nonlocal replacement, close_attempts
                    if handle == selected_handle and close_attempts == 0:
                        close_attempts += 1
                        if selected_owner is None or selected_directory is None:
                            raise AssertionError("selected disposition owner was not captured")
                        artifact_path = getattr(selected_owner, "artifact_path")
                        expected_identity = getattr(selected_owner, "expected_identity")
                        if not real_try_close(handle):
                            raise AssertionError("selected disposition handle did not close")
                        self.assertFalse(
                            artifact_path.exists(),
                            "consuming disposition close did not remove its owned name",
                        )
                        for _ in range(4096):
                            candidate = real_open_raw(
                                selected_directory,
                                alias.name,
                                read_data=True,
                                share_write=True,
                                delete_access=False,
                            )
                            if candidate == handle:
                                replacement = candidate
                                break
                            blockers.append(candidate)
                        if replacement is None:
                            raise AssertionError("same-number hardlink reuse could not be forced")
                        self.assertEqual(
                            self.generator._windows_governance_handle_file_id(replacement),
                            expected_identity,
                            "hardlink replacement did not preserve the consumed owner's identity",
                        )
                        raise OSError("close consumed owned name then wrapper raised")
                    if handle == replacement:
                        raise AssertionError("cleanup replay-closed the hardlink replacement")
                    return real_try_close(handle)

                def reject_after_publish(_snapshot: object) -> None:
                    raise OSError("force absent-target rollback")

                caught: BaseException | None = None
                retry_error: BaseException | None = None
                initial_descriptors: tuple[object, ...] = ()
                try:
                    with mock.patch.object(
                        self.generator,
                        "_GOVERNANCE_CLEANUP_MANAGER",
                        manager,
                    ), mock.patch.object(
                        self.generator,
                        "_windows_create_relative_governance_file",
                        side_effect=capture_create,
                    ), mock.patch.object(
                        self.generator,
                        "_windows_open_relative_governance_file_raw",
                        side_effect=capture_open_raw,
                    ), mock.patch.object(
                        self.generator,
                        "_windows_try_close_file",
                        side_effect=consume_then_reopen_alias,
                    ):
                        try:
                            self.generator.write_atomic_lf(
                                target,
                                b"new\n",
                                _post_publish_lifetime_check=(
                                    reject_after_publish
                                    if family == "published_disposal"
                                    else None
                                ),
                            )
                        except BaseException as error:
                            caught = error
                        initial_descriptors = manager.pending_descriptors()
                        for descriptor in initial_descriptors:
                            try:
                                manager.retry_pending(descriptor.retry_id)
                            except BaseException as error:
                                retry_error = error

                    descriptors = manager.pending_descriptors()
                    self.assertTrue(injected, f"{family} disposition owner was not reached")
                    if family != "recovery":
                        self.assertIsNotNone(caught)
                    self.assertEqual(close_attempts, 1)
                    self.assertIsNotNone(
                        getattr(selected_owner, "expected_identity", None)
                    )
                    self.assertTrue(getattr(selected_owner, "closed", False))
                    self.assertEqual(replacement, selected_handle)
                    self.assertIsNone(
                        retry_error,
                        f"{family} absent owned name did not resolve: {retry_error!r}",
                    )
                    self.assertEqual(
                        descriptors,
                        (),
                        f"{family} retained an owner after its exact artifact disappeared",
                    )
                    self.assertTrue(
                        self.generator._windows_governance_handle_is_open(replacement),
                        "cleanup closed the unrelated hardlink handle",
                    )
                    self.assertTrue(alias.exists())
                    if family == "published_disposal":
                        self.assertFalse(target.exists())
                    elif family == "staging":
                        self.assertEqual(target.read_bytes(), b"old\n")
                    else:
                        self.assertEqual(target.read_bytes(), b"new\n")
                finally:
                    if replacement is not None:
                        try:
                            real_try_close(replacement)
                        except BaseException:
                            pass
                    elif (
                        selected_handle is not None
                        and self.generator._windows_governance_handle_is_open(
                            selected_handle
                        )
                    ):
                        try:
                            real_try_close(selected_handle)
                        except BaseException:
                            pass
                    for blocker in blockers:
                        try:
                            real_try_close(blocker)
                        except BaseException:
                            pass
                    for _ in range(4):
                        if not manager.pending_descriptors():
                            break
                        for descriptor in manager.pending_descriptors():
                            try:
                                manager.retry_pending(descriptor.retry_id)
                            except BaseException:
                                pass

        with self.subTest(disposition_name_present_stays_pending=True), (
            tempfile.TemporaryDirectory(
                prefix="pontius-round9-name-present-",
                ignore_cleanup_errors=True,
            )
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            with mock.patch.object(self.generator.atexit, "register"):
                manager = self.generator._GovernanceCleanupManager()
            selected_handle: int | None = None
            selected_owner: object | None = None
            close_attempts = 0

            def fail_after_create(
                directory: int,
                name: str,
                **keywords: object,
            ) -> int:
                nonlocal selected_handle, selected_owner
                handle = real_create(directory, name, **keywords)
                owner = keywords.get("owner")
                if getattr(owner, "role", None) == "staging":
                    selected_handle = handle
                    selected_owner = owner
                    raise OSError("force staging cleanup")
                return handle

            def fail_before_consuming_close(handle: int) -> bool:
                nonlocal close_attempts
                if handle == selected_handle:
                    close_attempts += 1
                    raise OSError("close failed before consuming disposition")
                return real_try_close(handle)

            try:
                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator,
                    "_windows_create_relative_governance_file",
                    side_effect=fail_after_create,
                ), mock.patch.object(
                    self.generator,
                    "_windows_try_close_file",
                    side_effect=fail_before_consuming_close,
                ):
                    with self.assertRaises(BaseException):
                        self.generator.write_atomic_lf(target, b"new\n")
                    descriptor = manager.pending_descriptors()[0]
                    with self.assertRaises(BaseException):
                        manager.retry_pending(descriptor.retry_id)
                descriptors = manager.pending_descriptors()
                self.assertEqual(close_attempts, 1, "ambiguous close must not replay")
                self.assertEqual(len(descriptors), 1)
                self.assertIn("staging", descriptors[0].outstanding_owner_roles)
                self.assertTrue(getattr(selected_owner, "artifact_path").exists())
            finally:
                if selected_handle is not None:
                    try:
                        real_try_close(selected_handle)
                    except BaseException:
                        pass
                for descriptor in manager.pending_descriptors():
                    try:
                        manager.retry_pending(descriptor.retry_id)
                    except BaseException:
                        pass

    def _round9_windows_unbound_owners_bind_before_consuming_close(self) -> None:
        real_create = self.generator._windows_create_relative_governance_file
        real_open_raw = self.generator._windows_open_relative_governance_file_raw
        real_file_id = self.generator._windows_governance_handle_file_id
        real_try_close = self.generator._windows_try_close_file

        for family in ("original", "readback", "published", "staging"):
            with self.subTest(unbound_owner_family=family), (
                tempfile.TemporaryDirectory(
                    prefix=f"pontius-round9-unbound-{family}-",
                    ignore_cleanup_errors=True,
                )
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                target.write_bytes(b"old\n")
                with mock.patch.object(self.generator.atexit, "register"):
                    manager = self.generator._GovernanceCleanupManager()
                active_probe = False
                probe_allowed = False
                selected_handle: int | None = None
                selected_owner: object | None = None
                close_attempts = 0

                def classify(
                    owner: object | None,
                    keywords: dict[str, object],
                ) -> str | None:
                    role = getattr(owner, "role", None)
                    if role != "published":
                        return role if isinstance(role, str) else None
                    if (
                        keywords.get("read_data") is True
                        and keywords.get("share_write") is False
                        and keywords.get("delete_access") is False
                    ):
                        return "published"
                    return "published_disposal"

                def capture_create(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal active_probe, selected_owner
                    owner = keywords.get("owner")
                    selected = family == "staging" and getattr(owner, "role", None) == family
                    if selected:
                        selected_owner = owner
                        active_probe = True
                    try:
                        return real_create(directory, name, **keywords)
                    finally:
                        active_probe = False

                def capture_open_raw(
                    directory: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    nonlocal active_probe, selected_owner
                    owner = keywords.get("owner")
                    selected = classify(owner, keywords) == family
                    if selected:
                        selected_owner = owner
                        active_probe = True
                    try:
                        return real_open_raw(directory, name, **keywords)
                    finally:
                        active_probe = False

                def fail_selected_identity(handle: int) -> tuple[int, int]:
                    nonlocal selected_handle
                    if active_probe:
                        selected_handle = handle
                    if handle == selected_handle and not probe_allowed:
                        raise OSError(f"{family} identity probe failed")
                    return real_file_id(handle)

                def count_selected_close(handle: int) -> bool:
                    nonlocal close_attempts
                    if handle == selected_handle:
                        close_attempts += 1
                    return real_try_close(handle)

                caught: BaseException | None = None
                initial_descriptors: tuple[object, ...] = ()
                initial_close_attempts = -1
                retry_error: BaseException | None = None
                try:
                    with mock.patch.object(
                        self.generator,
                        "_GOVERNANCE_CLEANUP_MANAGER",
                        manager,
                    ), mock.patch.object(
                        self.generator,
                        "_windows_create_relative_governance_file",
                        side_effect=capture_create,
                    ), mock.patch.object(
                        self.generator,
                        "_windows_open_relative_governance_file_raw",
                        side_effect=capture_open_raw,
                    ), mock.patch.object(
                        self.generator,
                        "_windows_governance_handle_file_id",
                        side_effect=fail_selected_identity,
                    ), mock.patch.object(
                        self.generator,
                        "_windows_try_close_file",
                        side_effect=count_selected_close,
                    ):
                        try:
                            self.generator.write_atomic_lf(target, b"new\n")
                        except BaseException as error:
                            caught = error
                        initial_descriptors = manager.pending_descriptors()
                        initial_close_attempts = close_attempts
                        probe_allowed = True
                        for descriptor in initial_descriptors:
                            try:
                                manager.retry_pending(descriptor.retry_id)
                            except BaseException as error:
                                retry_error = error

                    self.assertIsNotNone(selected_handle, f"{family} acquisition was not reached")
                    self.assertIsNotNone(selected_owner)
                    self.assertIsNotNone(caught)
                    self.assertEqual(len(initial_descriptors), 1)
                    self.assertIn(
                        family,
                        initial_descriptors[0].outstanding_owner_roles,
                    )
                    self.assertEqual(
                        initial_close_attempts,
                        0,
                        f"{family} unbound handle was consumed before identity retry",
                    )
                    self.assertIsNone(retry_error)
                    self.assertGreaterEqual(close_attempts, 1)
                    self.assertIsNotNone(
                        getattr(selected_owner, "expected_identity", None)
                    )
                    self.assertTrue(getattr(selected_owner, "closed", False))
                    self.assertEqual(manager.pending_descriptors(), ())
                finally:
                    probe_allowed = True
                    for descriptor in manager.pending_descriptors():
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException:
                            pass
                    if (
                        selected_handle is not None
                        and self.generator._windows_governance_handle_is_open(
                            selected_handle
                        )
                    ):
                        try:
                            real_try_close(selected_handle)
                        except BaseException:
                            pass

    def _final3_windows_lock_close_failure_remains_owned(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        with tempfile.TemporaryDirectory(
            prefix="pontius-final3-lock-close-",
            ignore_cleanup_errors=True,
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            lock_handle: int | None = None
            close_attempts = 0
            real_create = self.generator._windows_create_relative_governance_file
            real_close = self.generator._windows_try_close_file

            def capture_lock(
                directory: int,
                name: str,
                **keywords: object,
            ) -> int:
                nonlocal lock_handle
                handle = real_create(directory, name, **keywords)
                if name.endswith(".pontius-governance.lock"):
                    lock_handle = handle
                return handle

            def fail_lock_close(handle: int) -> bool:
                nonlocal close_attempts
                if handle == lock_handle:
                    close_attempts += 1
                    return False
                return real_close(handle)

            caught: BaseException | None = None
            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator,
                "_windows_create_relative_governance_file",
                side_effect=capture_lock,
            ), mock.patch.object(
                self.generator,
                "_windows_try_close_file",
                side_effect=fail_lock_close,
            ):
                try:
                    self.generator.write_atomic_lf(target, b"new\n")
                except BaseException as error:
                    caught = error
            descriptors = manager.pending_descriptors()
            try:
                self.assertIsInstance(
                    caught,
                    self.generator.GovernanceCommittedWithCleanupFailure,
                )
                self.assertGreaterEqual(close_attempts, 3)
                self.assertEqual(len(descriptors), 1)
                self.assertIn(
                    "deterministic_lock",
                    descriptors[0].outstanding_owner_roles,
                )
                self.assertTrue(descriptors[0].lock_keys)
                self.assertTrue(descriptors[0].artifact_paths)
            finally:
                for descriptor in manager.pending_descriptors():
                    try:
                        manager.retry_pending(descriptor.retry_id)
                    except BaseException:
                        pass
                if lock_handle is not None:
                    try:
                        real_close(lock_handle)
                    except BaseException:
                        pass
                with manager._condition:
                    manager._pending.clear()
                    manager._reservations.clear()
                for artifact in tuple(root.iterdir()):
                    if artifact != target:
                        try:
                            artifact.unlink()
                        except OSError:
                            pass

    def test_windows_cooperative_namespace_boundary_is_documented(self) -> None:
        contract = self.generator.GOVERNANCE_WRITER_SECURITY_BOUNDARY
        self.assertIn("cooperative Pontius writers", contract)
        self.assertIn("arbitrary same-user namespace mutation is unsupported", contract)

    def test_windows_persistent_close_failures_are_truthful_and_retryable(
        self,
    ) -> None:
        if os.name != "nt":
            return
        self._round6_windows_writer_directory_owner_is_monotonic()
        self._round6_windows_auxiliary_file_owners_are_retryable()
        self._round6_windows_namespace_free_ambiguous_closes_reconcile()
        self._final3_windows_writer_reused_handles_are_role_isolated()
        self._round7_windows_file_owners_bind_before_caller_failure()
        self._round9_windows_disposition_absence_beats_same_inode_reuse()
        self._round9_windows_unbound_owners_bind_before_consuming_close()
        self._final3_windows_staging_cleanup_is_monotonic()
        self._final3_windows_lock_close_failure_remains_owned()
        for role in ("staging", "published", "recovery", "deterministic_lock"):
            with self.subTest(monotonic_role=role):
                attempts = 0

                def persistent_ambiguous_close() -> None:
                    nonlocal attempts
                    attempts += 1
                    raise OSError("persistent ambiguous close")

                owner = self.generator._WindowsHandleOwner(
                    role,
                    903,
                    persistent_ambiguous_close,
                    lambda: True,
                )
                with self.assertRaisesRegex(OSError, "persistent ambiguous"):
                    owner.close()
                owner.close()
                self.assertEqual(attempts, 1)
                self.assertTrue(owner.closed)
        return
        role_names = {
            "staging": "staging",
            "published": "published",
            "recovery": "recovery",
            "lock": "deterministic_lock",
        }
        for role, owner_role in role_names.items():
            with self.subTest(role=role), tempfile.TemporaryDirectory(
                prefix=f"pontius-governance-persistent-{role}-"
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                target.write_bytes(b"old\n")
                handles: dict[str, int] = {}
                close_attempts = 0
                real_create = (
                    self.generator._windows_create_relative_governance_file
                )
                real_open = self.generator._windows_open_relative_governance_file
                real_open_raw = (
                    self.generator._windows_open_relative_governance_file_raw
                )
                real_close = self.generator._windows_try_close_file

                def capture_create(
                    directory_handle: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    handle = real_create(
                        directory_handle,
                        name,
                        **keywords,
                    )
                    if name.endswith(".lock"):
                        handles["lock"] = handle
                    elif name.endswith(".tmp"):
                        handles["staging"] = handle
                    return handle

                def capture_open(directory_handle: int, name: str) -> int:
                    handle = real_open(directory_handle, name)
                    if name.endswith(".recovery"):
                        handles["recovery"] = handle
                    return handle

                def capture_open_raw(
                    directory_handle: int,
                    name: str,
                    **keywords: object,
                ) -> int:
                    handle = real_open_raw(
                        directory_handle,
                        name,
                        **keywords,
                    )
                    if (
                        name == target.name
                        and keywords.get("read_data") is True
                        and keywords.get("share_write") is False
                        and keywords.get("delete_access") is False
                    ):
                        handles["published"] = handle
                    return handle

                def persistently_fail_selected_close(handle: int) -> None:
                    nonlocal close_attempts
                    if handle == handles.get(role):
                        close_attempts += 1
                        raise OSError(f"{role} close remains open")
                    real_close(handle)

                caught: BaseException | None = None
                with mock.patch.object(
                    self.generator,
                    "_windows_create_relative_governance_file",
                    side_effect=capture_create,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_relative_governance_file",
                    side_effect=capture_open,
                ), mock.patch.object(
                    self.generator,
                    "_windows_open_relative_governance_file_raw",
                    side_effect=capture_open_raw,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_close_file",
                    side_effect=persistently_fail_selected_close,
                ):
                    try:
                        self.generator.write_atomic_lf(target, b"new\n")
                    except BaseException as error:
                        caught = error
                self.assertEqual(close_attempts, 1)
                for handle in set(handles.values()):
                    try:
                        real_close(handle)
                    except BaseException:
                        pass
                manager = self.generator._governance_cleanup_manager()
                self.assertEqual(manager.pending_descriptors(), ())
                for artifact in tuple(root.iterdir()):
                    if artifact != target:
                        try:
                            artifact.unlink()
                        except OSError:
                            pass
                self.assertEqual(
                    {path.name for path in root.iterdir()},
                    {target.name},
                )

    def test_windows_directory_close_failure_is_manager_owned(self) -> None:
        if os.name != "nt":
            return
        attempts = 0

        def ambiguous_close() -> None:
            nonlocal attempts
            attempts += 1
            raise OSError("directory close outcome is unknown")

        owner = self.generator._WindowsHandleOwner(
            "directory",
            902,
            ambiguous_close,
            lambda: True,
        )
        with self.assertRaisesRegex(OSError, "outcome is unknown"):
            owner.close()
        owner.close()
        self.assertEqual(attempts, 1)
        self.assertTrue(owner.closed)
        return
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-persistent-directory-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            directory_handle: int | None = None
            close_attempts = 0
            real_open = self.generator._windows_open_governance_directory
            real_close = self.generator.secure_filesystem._windows_close_directory

            def capture_open(
                path: Path,
                **keywords: object,
            ) -> tuple[int, tuple[int, bytes]]:
                nonlocal directory_handle
                result = real_open(path, **keywords)
                directory_handle = result[0]
                return result

            def fail_directory_close(handle: int) -> None:
                nonlocal close_attempts
                if handle == directory_handle:
                    close_attempts += 1
                    raise OSError("directory close remains open")
                real_close(handle)

            with mock.patch.object(
                self.generator,
                "_windows_open_governance_directory",
                side_effect=capture_open,
            ), mock.patch.object(
                self.generator.secure_filesystem,
                "_windows_close_directory",
                side_effect=fail_directory_close,
            ):
                with self.assertRaises(
                    self.generator.GovernanceCommittedWithCleanupFailure
                ) as caught:
                    self.generator.write_atomic_lf(target, b"new\n")
            self.assertGreaterEqual(close_attempts, 3)
            self.assertEqual(target.read_bytes(), b"new\n")
            self.assertIn(
                "directory",
                caught.exception.descriptor.outstanding_owner_roles,
            )
            manager = self.generator._governance_cleanup_manager()
            manager.retry_pending(caught.exception.retry_id)
            self.assertEqual(manager.pending_descriptors(), ())
            self.assertEqual({path.name for path in root.iterdir()}, {target.name})

    def test_windows_close_succeeded_then_raised_is_not_retried(self) -> None:
        if os.name != "nt":
            return
        for role in (
            "staging",
            "published",
            "recovery",
            "deterministic_lock",
            "directory",
        ):
            with self.subTest(role=role):
                open_state = True
                close_calls = 0

                def close_action() -> None:
                    nonlocal open_state, close_calls
                    close_calls += 1
                    open_state = False
                    raise OSError("close succeeded then raised")

                owner = self.generator._WindowsHandleOwner(
                    role=role,
                    handle=100,
                    close_action=close_action,
                    is_open_action=lambda: open_state,
                )
                with self.assertRaisesRegex(OSError, "close succeeded"):
                    owner.close()
                owner.close()
                self.assertTrue(owner.closed)
                self.assertEqual(close_calls, 1)
                self.assertEqual(
                    self.generator._governance_cleanup_manager().pending_descriptors(),
                    (),
                )

    def _final3_posix_writer_reused_descriptors_are_role_isolated(self) -> None:
        if os.name == "nt":
            return
        for selected_role in (
            "staging",
            "recovery",
            "directory",
            "deterministic_lock",
        ):
            with self.subTest(reused_writer_role=selected_role), (
                tempfile.TemporaryDirectory(
                    prefix=f"pontius-final3-posix-reuse-{selected_role}-"
                )
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                target.write_bytes(b"old\n")
                manager = self.generator._GovernanceCleanupManager()
                handles: dict[str, int] = {}
                replacement: int | None = None
                selected_close_attempts = 0
                real_open = self.generator.os.open
                real_close = self.generator.os.close

                def capture_open(
                    name: object,
                    flags: int,
                    *args: object,
                    **keywords: object,
                ) -> int:
                    handle = real_open(name, flags, *args, **keywords)
                    text = os.fspath(name)
                    if Path(text) == root:
                        handles["directory"] = handle
                    elif text.endswith(".pontius-governance.lock"):
                        handles["deterministic_lock"] = handle
                    elif text.endswith(".tmp"):
                        handles["staging"] = handle
                    elif text == target.name:
                        handles["recovery"] = handle
                    return handle

                def close_descriptor(handle: int) -> None:
                    nonlocal replacement, selected_close_attempts
                    if (
                        handle == handles.get(selected_role)
                        and selected_close_attempts == 0
                    ):
                        selected_close_attempts += 1
                        real_close(handle)
                        replacement = real_open(target, os.O_RDONLY)
                        raise OSError("selected close consumed then raised")
                    real_close(handle)

                with mock.patch.object(
                    self.generator,
                    "_GOVERNANCE_CLEANUP_MANAGER",
                    manager,
                ), mock.patch.object(
                    self.generator.os,
                    "open",
                    side_effect=capture_open,
                ), mock.patch.object(
                    self.generator.os,
                    "close",
                    side_effect=close_descriptor,
                ):
                    try:
                        self.generator.write_atomic_lf(target, b"new\n")
                    except BaseException:
                        pass
                try:
                    self.assertEqual(selected_close_attempts, 1)
                    self.assertEqual(
                        replacement,
                        handles[selected_role],
                        "native descriptor was not deterministically reused",
                    )
                    os.fstat(replacement)
                finally:
                    if replacement is not None:
                        try:
                            real_close(replacement)
                        except BaseException:
                            pass
                    for descriptor in manager.pending_descriptors():
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException:
                            retained = manager._pending[descriptor.retry_id].owner
                            for participant in retained.participants:
                                participant.cleaned = True
                            try:
                                retained.lock_set.close()
                            except BaseException:
                                pass
                    with manager._condition:
                        manager._pending.clear()
                        manager._reservations.clear()
                    for artifact in tuple(root.iterdir()):
                        if artifact != target:
                            try:
                                artifact.unlink()
                            except OSError:
                                pass

    def test_posix_persistent_descriptor_cleanup_is_manager_owned(self) -> None:
        self._final3_posix_writer_reused_descriptors_are_role_isolated()
        manager = self.generator._governance_cleanup_manager()
        close_allowed = False
        close_calls = 0

        def close_action() -> None:
            nonlocal close_calls
            close_calls += 1
            if not close_allowed:
                raise OSError("POSIX descriptor remains open")

        owner = self.generator._PosixDescriptorOwner(
            role="published",
            descriptor=100,
            close_action=close_action,
        )
        reservation = manager.reserve()
        lock_set = mock.Mock()
        lock_set.canonical_keys = ("/tmp/profiles.toml",)
        lock_set.outstanding_lock_keys.return_value = (
            "/tmp/profiles.toml",
        )
        lock_set.released_lock_keys.return_value = ()
        lock_set.artifact_paths.return_value = ()
        lock_set.close.return_value = None
        group = self.generator._GovernanceWriteGroup(lock_set, reservation)
        group.attach_resource(owner)
        with self.assertRaisesRegex(OSError, "remains open"):
            owner.close()
        owner.close()
        self.assertEqual(close_calls, 1)
        self.assertTrue(owner.closed)
        self.assertEqual(manager.pending_descriptors(), ())

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
                        second,
                        b"new-profiles\n",
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
                        second,
                        b"new-profiles\n",
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
            conflict_errors: list[BaseException] = []

            def mutate_first_after_second(**kwargs: object) -> None:
                nonlocal publish_calls
                publish_calls += 1
                publish(**kwargs)
                if publish_calls == 2:
                    try:
                        if os.name == "nt":
                            first.write_bytes(b"concurrent-inventory\n")
                        else:
                            self.generator.write_atomic_lf(
                                first,
                                b"concurrent-inventory\n",
                            )
                    except BaseException as error:
                        conflict_errors.append(error)

            with mock.patch.object(
                self.generator,
                "_publish_staged_governance",
                side_effect=mutate_first_after_second,
            ):
                self.generator._write_governance_pair(
                    first,
                    b"new-inventory\n",
                    second,
                    b"new-profiles\n",
                )
            self.assertEqual(len(conflict_errors), 1)
            self.assertIsInstance(conflict_errors[0], OSError)
            self.assertEqual(first.read_bytes(), b"new-inventory\n")
            self.assertEqual(second.read_bytes(), b"new-profiles\n")

    def _final3_windows_recovery_close_failure_remains_owned(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        with tempfile.TemporaryDirectory(
            prefix="pontius-final3-recovery-close-",
            ignore_cleanup_errors=True,
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            disposed_handle: int | None = None
            close_attempts = 0
            real_dispose = (
                self.generator.secure_filesystem._windows_dispose_relative_file
            )
            real_close = self.generator._windows_try_close_file

            def record_recovery_disposition(handle: int) -> None:
                nonlocal disposed_handle
                if disposed_handle is None:
                    disposed_handle = handle
                real_dispose(handle)

            def fail_recovery_close(handle: int) -> bool:
                nonlocal close_attempts
                if handle == disposed_handle:
                    close_attempts += 1
                    return False
                return real_close(handle)

            caught: BaseException | None = None
            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator.secure_filesystem,
                "_windows_dispose_relative_file",
                side_effect=record_recovery_disposition,
            ), mock.patch.object(
                self.generator,
                "_windows_try_close_file",
                side_effect=fail_recovery_close,
            ):
                try:
                    self.generator.write_atomic_lf(target, b"new\n")
                except BaseException as error:
                    caught = error
            descriptors = manager.pending_descriptors()
            try:
                self.assertIsInstance(
                    caught,
                    self.generator.GovernanceCommittedWithCleanupFailure,
                )
                self.assertGreaterEqual(close_attempts, 3)
                self.assertEqual(len(descriptors), 1)
                self.assertIn(
                    "recovery",
                    descriptors[0].outstanding_owner_roles,
                )
                self.assertTrue(descriptors[0].artifact_paths)
                self.assertEqual(target.read_bytes(), b"new\n")
            finally:
                for descriptor in manager.pending_descriptors():
                    try:
                        manager.retry_pending(descriptor.retry_id)
                    except BaseException:
                        pass
                if disposed_handle is not None:
                    try:
                        real_close(disposed_handle)
                    except BaseException:
                        pass
                with manager._condition:
                    manager._pending.clear()
                    manager._reservations.clear()
                for artifact in tuple(root.iterdir()):
                    if artifact != target:
                        try:
                            artifact.unlink()
                        except OSError:
                            pass

    def test_atomic_publish_is_cas_bound_and_restores_post_publish_failures(
        self,
    ) -> None:
        if os.name == "nt":
            self._final3_windows_recovery_close_failure_remains_owned()
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
                    target,
                    b"new-profiles\n",
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
                        target,
                        b"new-profiles\n",
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
                real_close = self.generator._windows_try_close_file

                def fail_before_recovery_disposal(handle: int) -> None:
                    raise OSError("old recovery disposal failed")

                with mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_dispose_relative_file",
                    side_effect=fail_before_recovery_disposal,
                ):
                    with self.assertRaises(
                        self.generator.GovernanceCommittedWithCleanupFailure
                    ) as caught:
                        self.generator.write_atomic_lf(
                            target,
                            b"generated\n",
                        )
                self.assertTrue(caught.exception.committed)
                descriptor = caught.exception.descriptor
                self.assertEqual(descriptor.decision, "committed")
                self.assertIn("recovery", descriptor.outstanding_owner_roles)
                self.assertTrue(descriptor.lock_keys)
                self.assertTrue(descriptor.artifact_paths)
                self.assertEqual(target.read_bytes(), b"generated\n")
                manager = self.generator._governance_cleanup_manager()
                manager.retry_pending(caught.exception.retry_id)
                self.assertEqual(manager.pending_descriptors(), ())
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

                def fail_first_recovery_close(handle: int) -> bool:
                    nonlocal failed_close, recovery_close_calls
                    if handle == disposed_handle and not failed_close:
                        failed_close = True
                        recovery_close_calls += 1
                        real_close(handle)
                        raise OSError("old recovery close failed")
                    return real_close(handle)

                with mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_dispose_relative_file",
                    side_effect=record_dispose,
                ), mock.patch.object(
                    self.generator,
                    "_windows_try_close_file",
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

                def fail_second_recovery_close(handle: int) -> bool:
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
                    return real_close(handle)

                with mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_dispose_relative_file",
                    side_effect=record_pair_dispose,
                ), mock.patch.object(
                    self.generator,
                    "_windows_try_close_file",
                    side_effect=fail_second_recovery_close,
                ):
                    self.generator._write_governance_pair(
                        inventory,
                        b"new-inventory\n",
                        target,
                        b"new-profiles\n",
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
                directory_api = (
                    self.generator.secure_filesystem._windows_directory_api()
                )
                raw_close_directory = directory_api[3]
                publication_directory: int | None = None
                failed_post_commit_close = False
                publication_close_calls = 0

                def capture_publication_directory(
                    path: Path,
                    **keywords: object,
                ) -> tuple[int, tuple[int, bytes]]:
                    nonlocal publication_directory
                    opened = real_open_directory(path, **keywords)
                    publication_directory = opened[0]
                    return opened

                def fail_post_commit_directory_close(handle: object) -> int:
                    nonlocal failed_post_commit_close, publication_close_calls
                    numeric = int(getattr(handle, "value", handle))
                    if (
                        numeric == publication_directory
                        and target.read_bytes() == b"generated\n"
                        and not failed_post_commit_close
                    ):
                        failed_post_commit_close = True
                        publication_close_calls += 1
                        raw_close_directory(handle)
                        raise OSError("post-commit directory close failed")
                    return int(bool(raw_close_directory(handle)))

                with mock.patch.object(
                    self.generator,
                    "_windows_open_governance_directory",
                    side_effect=capture_publication_directory,
                ), mock.patch.object(
                    self.generator.secure_filesystem,
                    "_windows_directory_api",
                    return_value=(
                        directory_api[0],
                        directory_api[1],
                        directory_api[2],
                        fail_post_commit_directory_close,
                    ),
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

        with tempfile.TemporaryDirectory(
            prefix="pontius-final-validation-"
        ) as final_temporary:
            final_root = Path(final_temporary)
            fake_lease = mock.Mock()
            attribute_checks = 0

            def verify_attributes(*args: object, **kwargs: object) -> None:
                nonlocal attribute_checks
                attribute_checks += 1
                if attribute_checks == 2:
                    raise OSError("final attribute drift")

            final_validation_target = final_root / "final-validation.json"

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
                side_effect=verify_attributes,
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
            ):
                with self.assertRaisesRegex(Exception, "final attribute drift"):
                    self.generator._with_governance_attribute_lease(
                        final_root,
                        Path("C:/git.exe"),
                        self.generator._GovernancePublicationOperation(
                            (final_validation_target,),
                            self.generator._GovernancePreparedPublication(
                                self.generator._GovernanceSinglePublication(
                                    b"accepted\n",
                                    value="accepted",
                                )
                            ),
                        ),
                    )
            self.assertFalse(final_validation_target.exists())

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
                if attribute_checks == 2:
                    raise OSError("final outer attribute drift")

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
                        self.generator._GovernancePublicationOperation(
                            (absent,),
                            self.generator._GovernancePreparedPublication(
                                self.generator._GovernanceSinglePublication(
                                    b"generated\n"
                                )
                            ),
                        ),
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
                        self.generator._GovernancePublicationOperation(
                            (first, second),
                            self.generator._GovernancePreparedPublication(
                                self.generator._GovernancePairPublication(
                                    b"new-inventory\n",
                                    b"new-profiles\n",
                                )
                            ),
                        ),
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
                    if second_revalidations == 1:
                        source.write_bytes(b"VALUE = 2\n")

            with mock.patch.object(
                self.generator._GovernanceWriteTransaction,
                "revalidate",
                side_effect=mutate_after_second_output,
                autospec=True,
            ):
                with self.assertRaisesRegex(Exception, "(?:snapshot|file).*changed"):
                    self.generator._write_governance_pair(
                        first,
                        b"new-inventory\n",
                        second,
                        b"new-profiles\n",
                        lifetime_check=source_snapshot.revalidate,
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

            def fail_recovery_open(
                directory_handle: int,
                name: str,
                *,
                owner: object | None = None,
            ) -> int:
                nonlocal opened_recovery
                if name.endswith(".recovery"):
                    opened_recovery = True
                    raise OSError("recovery acquisition failed")
                return real_open(directory_handle, name, owner=owner)

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

    def test_transaction_coordinator_commits_before_releasing_git_lease(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-coordinator-order-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            events: list[str] = []
            lease_open = True

            class Lease:
                def close(inner_self) -> None:
                    nonlocal lease_open
                    events.append("lease-close")
                    lease_open = False

            strict_calls = 0

            def strict_snapshot(path: Path) -> tuple[Path, bytes, tuple[int, ...]]:
                nonlocal strict_calls
                strict_calls += 1
                events.append("strict-git")
                return path, b"git", (1,)

            original_finalize = (
                self.generator._GovernanceWriteTransaction.finalize_committed
            )

            def observed_finalize(transaction: object) -> None:
                events.append("commit")
                if not lease_open:
                    raise AssertionError("lease closed before commit")
                original_finalize(transaction)

            with mock.patch.object(
                self.generator,
                "_strict_git_snapshot",
                side_effect=strict_snapshot,
            ), mock.patch.object(
                self.generator,
                "_acquire_git_launch_lease",
                return_value=Lease(),
            ), mock.patch.object(
                self.generator,
                "_verify_governance_attributes",
                side_effect=lambda *args: events.append("attributes"),
            ), mock.patch.object(
                self.generator,
                "_revalidate_git_launch_lease",
                side_effect=lambda *args: events.append("git-lease"),
            ), mock.patch.object(
                self.generator._GovernanceWriteTransaction,
                "finalize_committed",
                side_effect=observed_finalize,
                autospec=True,
            ):
                result = self.generator._with_governance_attribute_lease(
                    root,
                    Path("C:/git.exe"),
                    self.generator._GovernancePublicationOperation(
                        (target,),
                        self.generator._GovernancePreparedPublication(
                            self.generator._GovernanceSinglePublication(
                                b"accepted\n",
                                value="accepted",
                            )
                        ),
                    ),
                )
            self.assertEqual(result, "accepted")
            self.assertEqual(target.read_bytes(), b"accepted\n")
            self.assertLess(events.index("commit"), events.index("lease-close"))
            self.assertEqual(strict_calls, 1)

    def test_direct_pair_runs_the_pair_lifetime_pass_before_commit(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-pair-lifetime-"
        ) as temporary:
            root = Path(temporary)
            first = root / "inventory.json"
            second = root / "profiles.toml"
            first.write_bytes(b"old-inventory\n")
            second.write_bytes(b"old-profiles\n")
            read = self.generator.secure_filesystem.read_regular_snapshot
            first_snapshot = read(
                first,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            second_snapshot = read(
                second,
                maximum_bytes=self.generator.MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            pair_revalidations = 0
            original = self.generator._GovernancePairTransaction.revalidate

            def record_pair_revalidation(transaction: object) -> None:
                nonlocal pair_revalidations
                pair_revalidations += 1
                original(transaction)

            with mock.patch.object(
                self.generator._GovernancePairTransaction,
                "revalidate",
                side_effect=record_pair_revalidation,
                autospec=True,
            ):
                self.generator._write_governance_pair(
                    first,
                    b"new-inventory\n",
                    second,
                    b"new-profiles\n",
                    lifetime_check=lambda: None,
                )
            self.assertEqual(pair_revalidations, 1)
            self.assertEqual(first.read_bytes(), b"new-inventory\n")
            self.assertEqual(second.read_bytes(), b"new-profiles\n")

    def test_windows_deterministic_lock_refuses_second_cooperative_writer(
        self,
    ) -> None:
        if os.name != "nt":
            return
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-cooperative-lock-"
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            target.write_bytes(b"old\n")
            attempted = False

            def attempt_second_writer() -> None:
                nonlocal attempted
                if attempted:
                    return
                attempted = True
                with self.assertRaisesRegex(Exception, "lock|writer"):
                    self.generator.write_atomic_lf(target, b"second\n")

            self.generator.write_atomic_lf(
                target,
                b"first\n",
                _lifetime_check=attempt_second_writer,
            )
            self.assertTrue(attempted)
            self.assertEqual(target.read_bytes(), b"first\n")
            self.assertEqual({path.name for path in root.iterdir()}, {target.name})

    def test_windows_bound_governance_objects_refuse_conflicting_writes(
        self,
    ) -> None:
        if os.name != "nt":
            return

        def shared_write(path: Path) -> bool:
            filesystem = self.generator.secure_filesystem
            kernel32 = filesystem.ctypes.WinDLL(
                "kernel32",
                use_last_error=True,
            )
            create = kernel32.CreateFileW
            create.argtypes = (
                filesystem.wintypes.LPCWSTR,
                filesystem.wintypes.DWORD,
                filesystem.wintypes.DWORD,
                filesystem.wintypes.LPVOID,
                filesystem.wintypes.DWORD,
                filesystem.wintypes.DWORD,
                filesystem.wintypes.HANDLE,
            )
            create.restype = filesystem.wintypes.HANDLE
            handle = create(
                str(path),
                0x40000000,
                0x00000001 | 0x00000002 | 0x00000004,
                None,
                3,
                0x80,
                None,
            )
            value = filesystem.ctypes.cast(
                handle,
                filesystem.ctypes.c_void_p,
            ).value
            invalid = filesystem.ctypes.c_void_p(-1).value
            if not value or value == invalid:
                return False
            write = kernel32.WriteFile
            write.argtypes = (
                filesystem.wintypes.HANDLE,
                filesystem.wintypes.LPCVOID,
                filesystem.wintypes.DWORD,
                filesystem.wintypes.LPDWORD,
                filesystem.wintypes.LPVOID,
            )
            write.restype = filesystem.wintypes.BOOL
            raw = b"attacker!\n"
            buffer = filesystem.ctypes.create_string_buffer(raw)
            count = filesystem.wintypes.DWORD()
            try:
                succeeded = write(
                    filesystem.wintypes.HANDLE(value),
                    filesystem.ctypes.byref(buffer),
                    len(raw),
                    filesystem.ctypes.byref(count),
                    None,
                )
                if not succeeded or int(count.value) != len(raw):
                    raise OSError("shared governance mutation failed")
            finally:
                filesystem._windows_close_file(int(value))
            return True

        for phase in ("staging", "recovery", "published"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(
                prefix=f"pontius-governance-{phase}-share-"
            ) as temporary:
                root = Path(temporary)
                target = root / "profiles.toml"
                target.write_bytes(b"old\n")
                mutation_refused = False
                original_publish = self.generator._publish_staged_governance
                original_rename = self.generator._windows_rename_governance_file

                def publish(**keywords: object) -> None:
                    nonlocal mutation_refused
                    if phase == "staging":
                        path = root / str(keywords["temporary_name"])
                        mutation_refused = not shared_write(path)
                    original_publish(**keywords)

                def rename(
                    handle: int,
                    directory: int,
                    name: str,
                    *,
                    replace: bool = False,
                ) -> None:
                    nonlocal mutation_refused
                    if phase == "recovery" and replace:
                        recovery = next(root.glob("*.recovery"))
                        mutation_refused = not shared_write(recovery)
                    original_rename(
                        handle,
                        directory,
                        name,
                        replace=replace,
                    )

                def published_check(snapshot: object) -> None:
                    nonlocal mutation_refused
                    if phase != "published":
                        return
                    mutation_refused = not shared_write(target)

                error: BaseException | None = None
                try:
                    with mock.patch.object(
                        self.generator,
                        "_publish_staged_governance",
                        side_effect=publish,
                    ), mock.patch.object(
                        self.generator,
                        "_windows_rename_governance_file",
                        side_effect=rename,
                    ):
                        self.generator.write_atomic_lf(
                            target,
                            b"generated\n",
                            _post_publish_lifetime_check=published_check,
                        )
                except BaseException as caught:
                    error = caught
                self.assertIsNone(error)
                self.assertTrue(mutation_refused)
                self.assertEqual(target.read_bytes(), b"generated\n")
                self.assertEqual(
                    {path.name for path in root.iterdir()},
                    {target.name},
                )

    def _final3_windows_absent_disposition_failure_retains_handle(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        with tempfile.TemporaryDirectory(
            prefix="pontius-final3-absent-disposition-",
            ignore_cleanup_errors=True,
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            rollback_handles: list[int] = []
            disposition_allowed = False
            disposed: list[int] = []
            real_open_raw = (
                self.generator._windows_open_relative_governance_file_raw
            )
            real_dispose = (
                self.generator.secure_filesystem._windows_dispose_relative_file
            )
            real_close = self.generator._windows_try_close_file

            def capture_rollback(
                directory: int,
                name: str,
                **keywords: object,
            ) -> int:
                handle = real_open_raw(directory, name, **keywords)
                if name == target.name and not (
                    set(keywords) - {"owner"}
                ):
                    rollback_handles.append(handle)
                return handle

            def fail_disposition(handle: int) -> None:
                if handle in rollback_handles and not disposition_allowed:
                    raise OSError("published disposition failed before close")
                real_dispose(handle)
                disposed.append(handle)

            def reject_after_publish(_snapshot: object) -> None:
                raise OSError("force absent-target rollback")

            caught: BaseException | None = None
            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator,
                "_windows_open_relative_governance_file_raw",
                side_effect=capture_rollback,
            ), mock.patch.object(
                self.generator.secure_filesystem,
                "_windows_dispose_relative_file",
                side_effect=fail_disposition,
            ):
                try:
                    self.generator.write_atomic_lf(
                        target,
                        b"generated\n",
                        _post_publish_lifetime_check=reject_after_publish,
                    )
                except BaseException as error:
                    caught = error
                descriptors = manager.pending_descriptors()
                try:
                    self.assertIsInstance(
                        caught,
                        self.generator.GovernanceCleanupPendingError,
                    )
                    self.assertEqual(len(descriptors), 1)
                    self.assertIn(
                        "published",
                        descriptors[0].outstanding_owner_roles,
                    )
                    self.assertIn(str(target), descriptors[0].artifact_paths)
                    self.assertEqual(
                        len(rollback_handles),
                        1,
                        "rollback reopened instead of retaining its first handle",
                    )
                finally:
                    disposition_allowed = True
                    for descriptor in manager.pending_descriptors():
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException:
                            pass
                    for handle in set(rollback_handles) - set(disposed):
                        try:
                            real_close(handle)
                        except BaseException:
                            pass
                    with manager._condition:
                        manager._pending.clear()
                        manager._reservations.clear()
                    for artifact in tuple(root.iterdir()):
                        try:
                            artifact.unlink()
                        except OSError:
                            pass

    def _final3_windows_absent_close_failure_retains_handle(self) -> None:
        manager = self.generator._GovernanceCleanupManager()
        with tempfile.TemporaryDirectory(
            prefix="pontius-final3-absent-close-",
            ignore_cleanup_errors=True,
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            rollback_handles: list[int] = []
            disposed: set[int] = set()
            close_allowed = False
            close_attempts = 0
            real_open_raw = (
                self.generator._windows_open_relative_governance_file_raw
            )
            real_dispose = (
                self.generator.secure_filesystem._windows_dispose_relative_file
            )
            real_close = self.generator._windows_try_close_file

            def capture_rollback(
                directory: int,
                name: str,
                **keywords: object,
            ) -> int:
                handle = real_open_raw(directory, name, **keywords)
                if name == target.name and not (
                    set(keywords) - {"owner"}
                ):
                    rollback_handles.append(handle)
                return handle

            def capture_disposition(handle: int) -> None:
                real_dispose(handle)
                if handle in rollback_handles:
                    disposed.add(handle)

            def fail_before_close(handle: int) -> bool:
                nonlocal close_attempts
                if handle in disposed and not close_allowed:
                    close_attempts += 1
                    return False
                return real_close(handle)

            def reject_after_publish(_snapshot: object) -> None:
                raise OSError("force absent-target rollback")

            caught: BaseException | None = None
            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator,
                "_windows_open_relative_governance_file_raw",
                side_effect=capture_rollback,
            ), mock.patch.object(
                self.generator.secure_filesystem,
                "_windows_dispose_relative_file",
                side_effect=capture_disposition,
            ), mock.patch.object(
                self.generator,
                "_windows_try_close_file",
                side_effect=fail_before_close,
            ):
                try:
                    self.generator.write_atomic_lf(
                        target,
                        b"generated\n",
                        _post_publish_lifetime_check=reject_after_publish,
                    )
                except BaseException as error:
                    caught = error
                descriptors = manager.pending_descriptors()
                retry_error: BaseException | None = None
                try:
                    self.assertIsInstance(
                        caught,
                        self.generator.GovernanceCleanupPendingError,
                    )
                    self.assertEqual(len(descriptors), 1)
                    self.assertIn(
                        "published",
                        descriptors[0].outstanding_owner_roles,
                    )
                    self.assertIn(str(target), descriptors[0].artifact_paths)
                    self.assertEqual(len(rollback_handles), 1)
                    close_allowed = True
                    try:
                        manager.retry_pending(descriptors[0].retry_id)
                    except BaseException as error:
                        retry_error = error
                    self.assertIsNone(
                        retry_error,
                        "retry did not consume the retained published handle",
                    )
                    self.assertEqual(manager.pending_descriptors(), ())
                    self.assertFalse(target.exists())
                finally:
                    close_allowed = True
                    for handle in set(rollback_handles):
                        try:
                            real_close(handle)
                        except BaseException:
                            pass
                    for descriptor in manager.pending_descriptors():
                        try:
                            manager.retry_pending(descriptor.retry_id)
                        except BaseException:
                            retained = manager._pending[descriptor.retry_id].owner
                            for participant in retained.participants:
                                participant.cleaned = True
                            try:
                                retained.lock_set.close()
                            except BaseException:
                                pass
                    with manager._condition:
                        manager._pending.clear()
                        manager._reservations.clear()
                    for artifact in tuple(root.iterdir()):
                        try:
                            artifact.unlink()
                        except OSError:
                            pass
            self.assertGreaterEqual(close_attempts, 1)

    def test_windows_fail_before_close_retains_transaction_ownership(
        self,
    ) -> None:
        if os.name != "nt":
            return
        for label, check in (
            (
                "pre-disposition-exception",
                self._final3_windows_absent_disposition_failure_retains_handle,
            ),
            (
                "fail-before-consuming-close",
                self._final3_windows_absent_close_failure_retains_handle,
            ),
        ):
            with self.subTest(absent_target_cleanup=label):
                check()
        manager = self.generator._GovernanceCleanupManager()
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-absent-ambiguous-close-",
            ignore_cleanup_errors=True,
        ) as temporary:
            root = Path(temporary)
            target = root / "profiles.toml"
            rollback_handle: int | None = None
            rollback_close_attempts = 0
            close_succeeded_then_raised = False
            real_open_raw = (
                self.generator._windows_open_relative_governance_file_raw
            )
            real_close = self.generator._windows_try_close_file

            def capture_published_rollback(
                directory_handle: int,
                name: str,
                **keywords: object,
            ) -> int:
                nonlocal rollback_handle
                handle = real_open_raw(directory_handle, name, **keywords)
                if name == target.name and not (
                    set(keywords) - {"owner"}
                ):
                    rollback_handle = handle
                return handle

            def ambiguous_published_disposal_close(handle: int) -> bool:
                nonlocal rollback_close_attempts, close_succeeded_then_raised
                if handle == rollback_handle and not close_succeeded_then_raised:
                    rollback_close_attempts += 1
                    real_close(handle)
                    close_succeeded_then_raised = True
                    raise OSError("published disposal close succeeded then raised")
                return real_close(handle)

            def reject_after_publish(_snapshot: object) -> None:
                raise OSError("force absent-target rollback")

            caught: BaseException | None = None
            with mock.patch.object(
                self.generator,
                "_GOVERNANCE_CLEANUP_MANAGER",
                manager,
            ), mock.patch.object(
                self.generator,
                "_windows_open_relative_governance_file_raw",
                side_effect=capture_published_rollback,
            ), mock.patch.object(
                self.generator,
                "_windows_try_close_file",
                side_effect=ambiguous_published_disposal_close,
            ):
                try:
                    self.generator.write_atomic_lf(
                        target,
                        b"generated\n",
                        _post_publish_lifetime_check=reject_after_publish,
                    )
                except BaseException as error:
                    caught = error
                if isinstance(
                    caught,
                    self.generator.GovernanceCleanupPendingError,
                ):
                    retained = manager._pending[caught.retry_id].owner
                    for participant in retained.participants:
                        participant.cleaned = True
                    retained.lock_set.close()
                    with manager._condition:
                        manager._pending.pop(caught.retry_id, None)
            self.assertTrue(close_succeeded_then_raised)
            self.assertEqual(rollback_close_attempts, 1)
            self.assertIsInstance(caught, OSError)
            self.assertNotIsInstance(
                caught,
                self.generator.GovernanceCleanupPendingError,
            )
            self.assertRegex(str(caught), "force absent-target rollback")
            self.assertFalse(target.exists())
            self.assertEqual(tuple(root.iterdir()), ())
            self.assertEqual(manager.pending_descriptors(), ())

    def test_posix_finalize_faults_are_committed_cleanup(self) -> None:
        for exchange in (False, True):
            for fault in ("destination-close", "recovery-unlink"):
                with self.subTest(exchange=exchange, fault=fault):
                    names: dict[str, bytes] = {
                        "profiles.toml": b"new\n",
                    }
                    closed: set[int] = set()
                    close_attempts: dict[int, int] = {}
                    recovery_name: str | None = None
                    fault_used = False
                    restored = False
                    directory_info = mock.Mock(
                        st_dev=7,
                        st_ino=8,
                        st_mode=stat.S_IFDIR | 0o700,
                    )
                    staged_info = mock.Mock(
                        st_mode=stat.S_IFREG | 0o600,
                        st_dev=1,
                        st_ino=2,
                        st_size=4,
                        st_mtime_ns=0,
                        st_ctime_ns=0,
                        st_file_attributes=0,
                        st_reparse_tag=0,
                    )

                    opened: set[int] = set()

                    def tracked_open(*args: object, **kwargs: object) -> int:
                        handle = 10 if not opened else 11
                        opened.add(handle)
                        return handle

                    def fake_fstat(handle: int) -> object:
                        if handle in closed:
                            raise OSError("closed governance handle")
                        return directory_info if handle == 10 else staged_info

                    def fake_stat(*args: object, **kwargs: object) -> object:
                        return staged_info

                    def fake_close(handle: int) -> None:
                        nonlocal fault_used
                        close_attempts[handle] = close_attempts.get(handle, 0) + 1
                        if (
                            fault == "destination-close"
                            and handle == 12
                            and not fault_used
                        ):
                            fault_used = True
                            raise OSError("destination close failed before close")
                        if handle in closed:
                            raise OSError("governance handle closed twice")
                        closed.add(handle)

                    def fake_publish(**keywords: object) -> None:
                        nonlocal recovery_name
                        state = keywords["state"]
                        outcome = keywords["outcome"]
                        recovery_name = (
                            str(keywords["temporary_name"])
                            if exchange
                            else ".profiles.toml.fixed.recovery"
                        )
                        names[recovery_name] = b"old\n"
                        state.recovery_name = recovery_name
                        state.destination_handle = 12
                        state.displaced = True
                        state.published = True
                        state.posix_exchange = exchange
                        outcome.published = True
                        outcome.recovery_path = Path(
                            str(keywords["destination_path"])
                        ).with_name(recovery_name)

                    def fake_exchange(
                        directory: int,
                        first: str,
                        second: str,
                    ) -> bool:
                        nonlocal restored
                        names[first], names[second] = (
                            names[second],
                            names[first],
                        )
                        restored = names["profiles.toml"] == b"old\n"
                        return True

                    def fake_replace(
                        source: str,
                        destination: str,
                        **kwargs: object,
                    ) -> None:
                        nonlocal restored
                        names[destination] = names.pop(source)
                        restored = names["profiles.toml"] == b"old\n"

                    def fake_unlink(name: str, **kwargs: object) -> None:
                        nonlocal fault_used
                        if (
                            fault == "recovery-unlink"
                            and name == recovery_name
                            and not fault_used
                        ):
                            fault_used = True
                            raise OSError("recovery unlink failed")
                        if name not in names:
                            raise FileNotFoundError(name)
                        del names[name]

                    snapshot = mock.Mock(
                        raw=b"new\n",
                        identity=(1, 2, 4, 0, 0, 0o100600, 0, 0),
                    )
                    snapshot.revalidate.return_value = None
                    outcome = self.generator._GovernanceWriteOutcome()
                    with tempfile.TemporaryDirectory(
                        prefix="pontius-posix-finalize-model-"
                    ) as temporary:
                        path = Path(temporary) / "profiles.toml"
                        with ExitStack() as stack:
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "O_DIRECTORY",
                                    0x10000,
                                    create=True,
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "O_NOFOLLOW",
                                    0x20000,
                                    create=True,
                                )
                            )
                            patched_open = stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "open",
                                    side_effect=tracked_open,
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "fstat",
                                    side_effect=fake_fstat,
                                )
                            )
                            patched_stat = stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "stat",
                                    side_effect=fake_stat,
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "write",
                                    side_effect=lambda handle, raw: len(raw),
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(self.generator.os, "fsync")
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "close",
                                    side_effect=fake_close,
                                )
                            )
                            patched_link = stack.enter_context(
                                mock.patch.object(self.generator.os, "link")
                            )
                            patched_replace = stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "replace",
                                    side_effect=fake_replace,
                                )
                            )
                            patched_unlink = stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "unlink",
                                    side_effect=fake_unlink,
                                )
                            )
                            supports_dir_fd = stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "supports_dir_fd",
                                    set(),
                                )
                            )
                            supports_follow = stack.enter_context(
                                mock.patch.object(
                                    self.generator.os,
                                    "supports_follow_symlinks",
                                    set(),
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator,
                                    "_revalidate_governance_directory_chain",
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator,
                                    "_require_governance_destination_identity",
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator,
                                    "_publish_staged_governance",
                                    side_effect=fake_publish,
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator,
                                    "_posix_exchange_governance_file",
                                    side_effect=fake_exchange,
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator.secure_filesystem,
                                    "_directory_identity",
                                    return_value=(7,),
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator.secure_filesystem,
                                    "_path_handle_identity",
                                    return_value=(1, 2),
                                )
                            )
                            stack.enter_context(
                                mock.patch.object(
                                    self.generator.secure_filesystem,
                                    "read_regular_snapshot",
                                    return_value=snapshot,
                                )
                            )
                            supports_dir_fd.clear()
                            supports_dir_fd.update(
                                {
                                    patched_open,
                                    patched_stat,
                                    patched_link,
                                    patched_replace,
                                    patched_unlink,
                                }
                            )
                            supports_follow.clear()
                            supports_follow.add(patched_stat)
                            transaction = (
                                self.generator._write_posix_governance(
                                    path,
                                    b"new\n",
                                    ((path.parent, (7,)),),
                                    (1, 1, 4, 0, 0, 0o100600, 0, 0),
                                    b"old\n",
                                    outcome,
                                    None,
                                    None,
                                )
                            )
                            manager = self.generator._governance_cleanup_manager()
                            reservation = manager.reserve()
                            lock_set = mock.Mock()
                            lock_set.closed = False

                            def close_lock_set() -> None:
                                lock_set.closed = True

                            lock_set.close.side_effect = close_lock_set
                            group = self.generator._GovernanceWriteGroup(
                                lock_set,
                                reservation,
                            )
                            group.add_participant(
                                self.generator._GovernanceTransactionParticipant(
                                    transaction,
                                    path,
                                    b"new\n",
                                )
                            )
                            group.validate_all(None)
                            group.mark_committed()
                            group.finish_committed_cleanup()
                    self.assertTrue(fault_used)
                    self.assertFalse(restored)
                    self.assertEqual(names, {"profiles.toml": b"new\n"})
                    self.assertEqual(manager.pending_descriptors(), ())
                    if fault == "destination-close":
                        self.assertEqual(close_attempts.get(12, 0), 1)

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
            "1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764",
        )
        self.assertEqual(
            review["analysis_census"],
            {
                "subprocess_direct_site_count": 42,
                "subprocess_helper_site_count": 4,
                "cross_file_helper_edge_count": 27,
                "cupy_call_node_count": 30,
                "string_sink_decoy_count": 176,
                "string_sink_decoy_sha256": (
                    "a4f316fe5d98f00d46571b22f958b0eb1e7dcf489563653ad51b6a0e75b1daba"
                ),
                "string_sink_decoy_partitions": {
                    "design_production": 17,
                    "historical_production": 6,
                    "prior_stabilization_synthetic": 26,
                    "task2_synthetic": 127,
                },
                "analyzed_sites_sha256": (
                    "8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71"
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
        self.assertEqual(len(blockers), 93)
        self.assertEqual(
            Counter(row["reason"] for row in blockers),
            Counter(
                {
                    "unsupported subprocess keyword: capture_output": 44,
                    "dynamic helper arguments prevent exact sink derivation": 14,
                    "CuPy action or view is outside the approved call scope": 11,
                    "dynamic repetition prevents a finite call bound": 5,
                    "mixed protected receiver is dynamically unresolved": 10,
                    "unsupported subprocess keyword: stdin": 5,
                    "registered probe implementation is absent": 1,
                    "dynamic sensitive call result is unresolved": 1,
                    "unregistered CuPy call is unresolved": 2,
                }
            ),
        )
        self.assertEqual(
            [
                (row["relative_path"], row["line"])
                for row in blockers
                if row["reason"]
                == "dynamic sensitive call result is unresolved"
            ],
            [("tests/test_multi_size_affine_cross_payoff.py", 134)],
        )
        self.assertEqual(
            [
                (row["relative_path"], row["line"])
                for row in blockers
                if row["reason"] == "unregistered CuPy call is unresolved"
            ],
            [
                ("tests/test_resident_record_to_hand_fold_v2.py", 312),
                ("tests/test_resident_record_to_hand_fold_v2.py", 313),
            ],
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
