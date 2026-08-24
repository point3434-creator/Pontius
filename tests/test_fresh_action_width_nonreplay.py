from __future__ import annotations

import ast
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pontius.durable_evidence_journal as journal
import pontius.fresh_action_width_nonreplay as nonreplay
from pontius.certified_reduced_sizing_consumer_v2 import canonical_lf_source_sha256
from pontius.durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from pontius.fresh_action_width_nonreplay import (
    ADR0331_NONREPLAY_PROTOCOL,
    ADR0331_NONREPLAY_PROTOCOL_SHA256,
    ADR0331_POPULATION_CONTEXT_COUNT,
    ADR0331_POPULATION_SEED,
    ADR0331_POPULATION_SEED_SHA256,
    ADR0331_PREREGISTRATION_COMMIT,
    ADR0331_RECOVERY_BASELINE_COMMIT,
    ADR0331_SYNTHETIC_CANDIDATE_COUNTS_BY_WIDTH,
    ADR0331_SYNTHETIC_GATE_FIELDS,
    ADR0331_SYNTHETIC_OBSERVATION_COUNT,
    ADR0331_SYNTHETIC_RECORD_COUNT,
    build_adr0331_nonreplay_pool,
    build_adr0331_synthetic_journal_records,
    rebind_adr0331_synthetic_journal,
    write_adr0331_synthetic_journal,
)
from pontius.fresh_action_width_structures import build_adr0323_development_pool
from pontius.fresh_action_width_structures_seal import (
    ADR0323_DEVELOPMENT_POOL_SHA256,
)
from pontius.fresh_action_width_nonreplay_seal import (
    ADR0331_EXCLUDED_CONTEXT_LIST_SHA256,
    ADR0331_JOURNAL_PROTOCOL_SHA256,
    ADR0331_NONREPLAY_PROTOCOL_SHA256 as SEALED_NONREPLAY_PROTOCOL_SHA256,
    ADR0331_NONREPLAY_SOURCE_MANIFEST,
    ADR0331_POPULATION_CANDIDATE_ATTEMPTS,
    ADR0331_POPULATION_CONTEXT_LIST_SHA256,
    ADR0331_POPULATION_POOL_SHA256,
    ADR0331_SUBSET_COUNTS_BY_RAISE_WIDTH,
    ADR0331_SYNTHETIC_CAMPAIGN_SHA256,
    ADR0331_SYNTHETIC_FINAL_OBSERVATION_LINE_SHA256,
    ADR0331_SYNTHETIC_HEADER_RECORD_SHA256,
    ADR0331_SYNTHETIC_JOURNAL_BYTES,
    ADR0331_SYNTHETIC_JOURNAL_SHA256,
    ADR0331_SYNTHETIC_TERMINAL_RECORD_SHA256,
    ADR0331_SYNTHETIC_TERMINAL_SHA256,
    ADR0331_SYNTHETIC_WIDTH_SUMMARY_SHA256S,
    ADR0331_TOTAL_SUBSET_COUNT,
)


def _rebuild_valid_chain(
    records: tuple[JournalRecordEnvelope, ...],
    *,
    changed_index: int,
    changed_payload: dict[str, object],
    changed_semantic_identity: str | None = None,
) -> bytes:
    rebuilt = list(records[:changed_index])
    for index in range(changed_index, len(records)):
        original = records[index]
        payload = changed_payload if index == changed_index else original.body.payload
        semantic_identity = (
            changed_semantic_identity
            if index == changed_index and changed_semantic_identity is not None
            else original.body.semantic_identity_sha256
        )
        if (
            index == len(records) - 1
            and changed_index < index
            and original.body.kind is JournalRecordKind.TERMINAL
        ):
            payload = dict(payload)
            payload["final_observation_line_sha256"] = rebuilt[-1].line_sha256
            terminal_core = {
                key: value for key, value in payload.items() if key != "terminal_sha256"
            }
            payload["terminal_sha256"] = sha256(
                canonical_journal_json_bytes(terminal_core)
            ).hexdigest()
            semantic_identity = payload["terminal_sha256"]
        rebuilt.append(
            JournalRecordEnvelope(
                build_journal_record_body(
                    protocol_sha256=original.body.protocol_sha256,
                    campaign_sha256=original.body.campaign_sha256,
                    kind=original.body.kind,
                    sequence=index,
                    previous_record_sha256=(
                        None if index == 0 else rebuilt[-1].line_sha256
                    ),
                    semantic_identity_sha256=semantic_identity,
                    payload=payload,
                )
            )
        )
    return b"".join(record.line_bytes for record in rebuilt)


class FreshActionWidthNonReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.old_pool = build_adr0323_development_pool()
        cls.pool = build_adr0331_nonreplay_pool()
        cls.records = build_adr0331_synthetic_journal_records(cls.pool)
        cls.raw = b"".join(record.line_bytes for record in cls.records)

    def test_seed_protocol_commits_and_source_import_boundary_are_exact(self) -> None:
        self.assertEqual(
            "pontius|adr-0331|fresh-action-width-nonreplay|population|"
            "recovery-commit=49044e58fc3a2a582fda11daba4f641da5b3e646",
            ADR0331_POPULATION_SEED,
        )
        self.assertEqual(
            ADR0331_POPULATION_SEED_SHA256,
            sha256(ADR0331_POPULATION_SEED.encode("ascii")).hexdigest(),
        )
        self.assertEqual(
            "49044e58fc3a2a582fda11daba4f641da5b3e646",
            ADR0331_RECOVERY_BASELINE_COMMIT,
        )
        self.assertEqual(
            "de166d81d5f91df48e6ec0ecea27000e04fd4f30",
            ADR0331_PREREGISTRATION_COMMIT,
        )
        self.assertEqual(
            ADR0331_NONREPLAY_PROTOCOL_SHA256,
            sha256(canonical_journal_json_bytes(dict(ADR0331_NONREPLAY_PROTOCOL))).hexdigest(),
        )
        self.assertEqual(
            ADR0331_JOURNAL_PROTOCOL_SHA256,
            DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
        )
        self.assertEqual(
            SEALED_NONREPLAY_PROTOCOL_SHA256,
            ADR0331_NONREPLAY_PROTOCOL_SHA256,
        )
        root = Path(nonreplay.__file__).resolve().parent
        self.assertEqual(
            dict(ADR0331_NONREPLAY_SOURCE_MANIFEST),
            {
                name: canonical_lf_source_sha256(root / name)
                for name in ADR0331_NONREPLAY_SOURCE_MANIFEST
            },
        )
        with self.assertRaises(TypeError):
            ADR0331_NONREPLAY_PROTOCOL["population_context_count"] = 1  # type: ignore[index]
        with self.assertRaises(TypeError):
            ADR0331_NONREPLAY_SOURCE_MANIFEST["river.py"] = "0" * 64  # type: ignore[index]

        source_path = Path(nonreplay.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        names: set[str] = set()
        attributes: set[str] = set()
        function_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_names.add(node.name)
        forbidden_fragments = (
            "qualification",
            "teacher_result",
            "greedy_result",
            "highs",
            "linear_program",
            "preparation_bank",
            "transfer",
        )
        self.assertFalse(
            any(
                fragment in module
                for module in imported
                for fragment in forbidden_fragments
            )
        )
        self.assertNotIn("BettingAction", names)
        self.assertNotIn("apply_action", attributes)
        self.assertFalse(any("solver" in name for name in function_names))

    def test_new_population_is_exact_unique_and_disjoint_from_all_96_old_contexts(self) -> None:
        pool = self.pool
        old = self.old_pool
        self.assertEqual(ADR0323_DEVELOPMENT_POOL_SHA256, old.digest)
        self.assertEqual(ADR0331_POPULATION_CONTEXT_COUNT, len(pool.contexts))
        self.assertEqual(ADR0331_POPULATION_CANDIDATE_ATTEMPTS, pool.candidate_attempts)
        self.assertEqual(ADR0331_POPULATION_POOL_SHA256, pool.digest)
        self.assertEqual(96, len(pool.excluded_context_semantic_digests))
        self.assertEqual(
            tuple(context.semantic_digest for context in old.contexts),
            pool.excluded_context_semantic_digests,
        )
        new_digests = tuple(context.semantic_digest for context in pool.contexts)
        self.assertEqual(
            ADR0331_EXCLUDED_CONTEXT_LIST_SHA256,
            sha256(
                canonical_journal_json_bytes(pool.excluded_context_semantic_digests)
            ).hexdigest(),
        )
        self.assertEqual(
            ADR0331_POPULATION_CONTEXT_LIST_SHA256,
            sha256(canonical_journal_json_bytes(new_digests)).hexdigest(),
        )
        self.assertEqual(96, len(set(new_digests)))
        self.assertTrue(set(new_digests).isdisjoint(pool.excluded_context_semantic_digests))
        self.assertEqual(
            tuple(f"adr0331-nonreplay-{index:03d}" for index in range(96)),
            tuple(context.context_id for context in pool.contexts),
        )
        self.assertEqual(pool.canonical_bytes, build_adr0331_nonreplay_pool().canonical_bytes)

    def test_population_preserves_generator_distribution_and_kernel_universes(self) -> None:
        pool = self.pool
        self.assertEqual(ADR0331_POPULATION_CANDIDATE_ATTEMPTS, pool.candidate_attempts)
        self.assertEqual(
            Counter({6: 29, 10: 24, 14: 23, 20: 20}),
            Counter(context.betting.pot for context in pool.contexts),
        )
        self.assertEqual(
            Counter({8: 32, 10: 32, 12: 32}),
            Counter(context.betting.stacks[0] for context in pool.contexts),
        )
        self.assertEqual(96, len({context.showdown_signs for context in pool.contexts}))
        self.assertEqual(
            Counter({7: 32, 9: 32, 11: 32}),
            Counter(len(context.complete_raise_to_totals) for context in pool.contexts),
        )
        for context in pool.contexts:
            decision = context.betting.legal_decision()
            bounds = decision.raise_bounds
            self.assertIsNotNone(bounds)
            assert bounds is not None
            self.assertEqual(
                tuple(range(bounds.minimum_raise_to, bounds.maximum_raise_to + 1)),
                tuple(value.chips for value in context.complete_raise_to_totals),
            )
        ledger = pool.subset_work_ledger
        self.assertEqual(
            ADR0331_SUBSET_COUNTS_BY_RAISE_WIDTH,
            tuple((width.count, count) for width, count in ledger.subset_counts_by_raise_width),
        )
        self.assertEqual(ADR0331_TOTAL_SUBSET_COUNT, ledger.total_subset_count)

    def test_pool_corruption_cannot_shrink_or_substitute_the_exclusion_set(self) -> None:
        with self.assertRaises((TypeError, ValueError)):
            replace(
                self.pool,
                excluded_context_semantic_digests=(
                    *self.pool.excluded_context_semantic_digests[:-1],
                    "f" * 64,
                ),
            )
        with self.assertRaises((TypeError, ValueError)):
            replace(
                self.pool,
                excluded_context_semantic_digests=(
                    self.pool.excluded_context_semantic_digests[:-1]
                ),
            )
        with self.assertRaises(ValueError):
            replace(self.pool, excluded_pool_sha256="f" * 64)
        with self.assertRaises(ValueError):
            replace(self.pool, contexts=tuple(reversed(self.pool.contexts)))

    def test_synthetic_success_fixture_has_exact_future_call_shape(self) -> None:
        records = self.records
        self.assertEqual(ADR0331_SYNTHETIC_RECORD_COUNT, len(records))
        self.assertEqual(JournalRecordKind.HEADER, records[0].body.kind)
        self.assertEqual(JournalRecordKind.TERMINAL, records[-1].body.kind)
        self.assertTrue(
            all(
                record.body.kind is JournalRecordKind.OBSERVATION
                for record in records[1:-1]
            )
        )
        self.assertEqual(
            ADR0331_SYNTHETIC_OBSERVATION_COUNT,
            len(records[1:-1]),
        )
        widths = Counter(
            record.body.payload["target_raise_width"]
            for record in records[1:-1]
        )
        self.assertEqual(Counter({2: 16, 3: 120, 4: 104, 5: 88, 6: 72}), widths)
        terminal = records[-1].body.payload
        self.assertEqual(
            ADR0331_SYNTHETIC_CAMPAIGN_SHA256,
            records[0].body.campaign_sha256,
        )
        self.assertEqual(
            ADR0331_SYNTHETIC_HEADER_RECORD_SHA256,
            records[0].record_sha256,
        )
        self.assertEqual(
            ADR0331_SYNTHETIC_FINAL_OBSERVATION_LINE_SHA256,
            records[-2].line_sha256,
        )
        self.assertEqual(
            ADR0331_SYNTHETIC_TERMINAL_RECORD_SHA256,
            records[-1].record_sha256,
        )
        self.assertIs(terminal["synthetic"], True)
        self.assertEqual(3, terminal["synthetic_selected_width"])
        summaries = terminal["width_summaries"]
        self.assertIsInstance(summaries, list)
        assert isinstance(summaries, list)
        self.assertEqual((3, 4, 5, 6), tuple(summary["width"] for summary in summaries))
        self.assertEqual(
            tuple(sorted(ADR0331_SYNTHETIC_GATE_FIELDS)),
            tuple(terminal["gate_definitions"]),
        )
        for summary in summaries:
            self.assertEqual(
                tuple(sorted(ADR0331_SYNTHETIC_GATE_FIELDS)),
                tuple(summary["metrics"]),
            )
            self.assertEqual(
                tuple(sorted(ADR0331_SYNTHETIC_GATE_FIELDS)),
                tuple(summary["gate_results"]),
            )
            core = {key: value for key, value in summary.items() if key != "summary_sha256"}
            self.assertEqual(
                summary["summary_sha256"],
                sha256(canonical_journal_json_bytes(core)).hexdigest(),
            )
        self.assertEqual(
            ADR0331_SYNTHETIC_WIDTH_SUMMARY_SHA256S,
            tuple(summary["summary_sha256"] for summary in summaries),
        )
        terminal_core = {
            key: value for key, value in terminal.items() if key != "terminal_sha256"
        }
        self.assertEqual(
            terminal["terminal_sha256"],
            sha256(canonical_journal_json_bytes(terminal_core)).hexdigest(),
        )
        self.assertEqual(ADR0331_SYNTHETIC_TERMINAL_SHA256, terminal["terminal_sha256"])
        self.assertEqual(ADR0331_SYNTHETIC_JOURNAL_BYTES, len(self.raw))
        self.assertEqual(ADR0331_SYNTHETIC_JOURNAL_SHA256, sha256(self.raw).hexdigest())

    def test_full_writer_calls_fsync_402_times_and_solver_free_rebinder_matches_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.jsonl"
            with patch.object(journal.os, "fsync", wraps=journal.os.fsync) as fsync:
                result = write_adr0331_synthetic_journal(path, pool=self.pool)
            self.assertEqual(ADR0331_SYNTHETIC_RECORD_COUNT, fsync.call_count)
            self.assertEqual(tuple(range(402)), tuple(r.sequence for r in result.receipts))
            self.assertEqual(self.raw, path.read_bytes())
            rebound = rebind_adr0331_synthetic_journal(path.read_bytes(), pool=self.pool)
            self.assertEqual(402, rebound.record_count)
            self.assertEqual(400, rebound.observation_count)
            self.assertEqual(sha256(self.raw).hexdigest(), rebound.journal_sha256)
            self.assertEqual(4, len(rebound.width_summary_canonical_json))
            with self.assertRaises(FileExistsError):
                write_adr0331_synthetic_journal(path, pool=self.pool)
            self.assertEqual(self.raw, path.read_bytes())

    def test_every_complete_record_crash_prefix_recovers_exactly(self) -> None:
        offset = 0
        for count, record in enumerate(self.records, start=1):
            offset += len(record.line_bytes)
            prefix = self.raw[:offset]
            recovered = recover_journal_bytes(
                prefix,
                expected_protocol_sha256=DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
                expected_campaign_sha256=self.records[0].body.campaign_sha256,
            )
            self.assertEqual(count, len(recovered.records))
            self.assertEqual(prefix, recovered.verified_prefix_bytes)
            self.assertEqual(b"", recovered.invalid_suffix_bytes)
            self.assertIsNone(recovered.failure)
            self.assertEqual(count == 402, recovered.is_complete)

    def test_representative_mid_line_crashes_preserve_untouched_tails(self) -> None:
        offsets = [0]
        for record in self.records:
            offsets.append(offsets[-1] + len(record.line_bytes))
        for record_index in (0, 1, 201, 400, 401):
            line = self.records[record_index].line_bytes
            for within in (1, len(line) // 2, len(line) - 1):
                cut = offsets[record_index] + within
                raw = self.raw[:cut]
                recovered = recover_journal_bytes(raw)
                self.assertEqual(self.raw[: offsets[record_index]], recovered.verified_prefix_bytes)
                self.assertEqual(self.raw[offsets[record_index] : cut], recovered.invalid_suffix_bytes)
                self.assertEqual(raw, recovered.raw_bytes)
                self.assertIsNotNone(recovered.failure)

    def test_valid_same_count_semantic_corruption_is_rejected_by_fixture_rebinding(self) -> None:
        changed = dict(self.records[200].body.payload)
        changed["candidate_raise_to_total_chips"] = 99
        changed_core = {
            key: value for key, value in changed.items() if key != "observation_sha256"
        }
        changed["observation_sha256"] = sha256(
            canonical_journal_json_bytes(changed_core)
        ).hexdigest()
        corrupted = _rebuild_valid_chain(
            self.records,
            changed_index=200,
            changed_payload=changed,
        )
        recovered = recover_journal_bytes(corrupted)
        self.assertTrue(recovered.is_complete)
        self.assertEqual(402, len(recovered.records))
        with self.assertRaisesRegex(ValueError, "frozen populated fixture"):
            rebind_adr0331_synthetic_journal(corrupted, pool=self.pool)

    def test_nested_summary_digest_corruption_is_detected_after_valid_outer_rebinding(self) -> None:
        terminal = dict(self.records[-1].body.payload)
        summaries = [dict(value) for value in terminal["width_summaries"]]
        first = summaries[0]
        first["summary_sha256"] = "f" * 64
        terminal["width_summaries"] = summaries
        terminal_core = {
            key: value for key, value in terminal.items() if key != "terminal_sha256"
        }
        terminal["terminal_sha256"] = sha256(
            canonical_journal_json_bytes(terminal_core)
        ).hexdigest()
        corrupted = _rebuild_valid_chain(
            self.records,
            changed_index=401,
            changed_payload=terminal,
            changed_semantic_identity=terminal["terminal_sha256"],
        )
        self.assertTrue(recover_journal_bytes(corrupted).is_complete)
        with self.assertRaisesRegex(ValueError, "width summary 0 digest"):
            rebind_adr0331_synthetic_journal(corrupted, pool=self.pool)


if __name__ == "__main__":
    unittest.main()
