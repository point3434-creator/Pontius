# Review package: 89303d1e7bdda4f3aec74b131d8a8cc8d1afcc09..79751648d1c2006bc2ad5d1212786db4e8eb314b

## Commits
7975164 test(architecture): lock legacy graph baseline

## Files changed
 docs/architecture/dependency-baseline.toml       | 13602 +++++++++++++++++++++
 tests/test_stabilization_boundaries.py           |   322 +
 tests/test_test_orchestration_import_boundary.py |    83 +
 tools/check_stabilization_boundaries.py          |   281 +
 tools/generate_dependency_baseline.py            |   793 ++
 5 files changed, 15081 insertions(+)

## Diff
diff --git a/docs/architecture/dependency-baseline.toml b/docs/architecture/dependency-baseline.toml
new file mode 100644
index 0000000..5fe6ee4
--- /dev/null
+++ b/docs/architecture/dependency-baseline.toml
@@ -0,0 +1,13602 @@
+schema_version = "pontius-dependency-baseline-v1"
+baseline_commit = "a842c4b6a73a2991a63a481f4107580b72750582"
+module_count = 470
+edge_count = 2577
+edges_sha256 = "c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee"
+scc_count = 469
+sccs_sha256 = "9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345"
+
+[[module]]
+module_name = "pontius.__init__"
+relative_path = "src/pontius/__init__.py"
+
+[[module]]
+module_name = "pontius.action_abstraction_confirmation"
+relative_path = "src/pontius/action_abstraction_confirmation.py"
+
+[[module]]
+module_name = "pontius.action_clock"
+relative_path = "src/pontius/action_clock.py"
+
+[[module]]
+module_name = "pontius.affine_resident_heterogeneous_leaf_contraction"
+relative_path = "src/pontius/affine_resident_heterogeneous_leaf_contraction.py"
+
+[[module]]
+module_name = "pontius.atomic_json_checkpoint"
+relative_path = "src/pontius/atomic_json_checkpoint.py"
+
+[[module]]
+module_name = "pontius.axis_cfr_checkpoint"
+relative_path = "src/pontius/axis_cfr_checkpoint.py"
+
+[[module]]
+module_name = "pontius.axis_public_cfr"
+relative_path = "src/pontius/axis_public_cfr.py"
+
+[[module]]
+module_name = "pontius.batched_factor_tt_contraction"
+relative_path = "src/pontius/batched_factor_tt_contraction.py"
+
+[[module]]
+module_name = "pontius.batched_selector_stable_affine_response"
+relative_path = "src/pontius/batched_selector_stable_affine_response.py"
+
+[[module]]
+module_name = "pontius.behavioral_one_seat_master"
+relative_path = "src/pontius/behavioral_one_seat_master.py"
+
+[[module]]
+module_name = "pontius.behavioral_one_seat_master_v2"
+relative_path = "src/pontius/behavioral_one_seat_master_v2.py"
+
+[[module]]
+module_name = "pontius.behavioral_open_axis"
+relative_path = "src/pontius/behavioral_open_axis.py"
+
+[[module]]
+module_name = "pontius.benefit_experiment"
+relative_path = "src/pontius/benefit_experiment.py"
+
+[[module]]
+module_name = "pontius.benefit_matrix"
+relative_path = "src/pontius/benefit_matrix.py"
+
+[[module]]
+module_name = "pontius.benefit_trajectory"
+relative_path = "src/pontius/benefit_trajectory.py"
+
+[[module]]
+module_name = "pontius.campaign_deadline"
+relative_path = "src/pontius/campaign_deadline.py"
+
+[[module]]
+module_name = "pontius.canonical_affine_resident_automaton_cache"
+relative_path = "src/pontius/canonical_affine_resident_automaton_cache.py"
+
+[[module]]
+module_name = "pontius.capacity_filling_action_abstraction"
+relative_path = "src/pontius/capacity_filling_action_abstraction.py"
+
+[[module]]
+module_name = "pontius.certified_reduced_sizing_consumer_v2"
+relative_path = "src/pontius/certified_reduced_sizing_consumer_v2.py"
+
+[[module]]
+module_name = "pontius.certified_reduced_sizing_consumer_v2_seal"
+relative_path = "src/pontius/certified_reduced_sizing_consumer_v2_seal.py"
+
+[[module]]
+module_name = "pontius.certified_reduced_sizing_highs"
+relative_path = "src/pontius/certified_reduced_sizing_highs.py"
+
+[[module]]
+module_name = "pontius.certified_reduced_sizing_highs_seal"
+relative_path = "src/pontius/certified_reduced_sizing_highs_seal.py"
+
+[[module]]
+module_name = "pontius.certified_sizing_validation_runner"
+relative_path = "src/pontius/certified_sizing_validation_runner.py"
+
+[[module]]
+module_name = "pontius.certified_sizing_validation_seal"
+relative_path = "src/pontius/certified_sizing_validation_seal.py"
+
+[[module]]
+module_name = "pontius.cfr"
+relative_path = "src/pontius/cfr.py"
+
+[[module]]
+module_name = "pontius.clean_fringe_tt"
+relative_path = "src/pontius/clean_fringe_tt.py"
+
+[[module]]
+module_name = "pontius.coalition"
+relative_path = "src/pontius/coalition.py"
+
+[[module]]
+module_name = "pontius.collision_repair_action_abstraction"
+relative_path = "src/pontius/collision_repair_action_abstraction.py"
+
+[[module]]
+module_name = "pontius.collision_repair_v3_evaluation"
+relative_path = "src/pontius/collision_repair_v3_evaluation.py"
+
+[[module]]
+module_name = "pontius.complete_factorized_affine_evidence"
+relative_path = "src/pontius/complete_factorized_affine_evidence.py"
+
+[[module]]
+module_name = "pontius.composition_experiment"
+relative_path = "src/pontius/composition_experiment.py"
+
+[[module]]
+module_name = "pontius.composition_matrix"
+relative_path = "src/pontius/composition_matrix.py"
+
+[[module]]
+module_name = "pontius.constrained_generation"
+relative_path = "src/pontius/constrained_generation.py"
+
+[[module]]
+module_name = "pontius.constrained_generation_experiment"
+relative_path = "src/pontius/constrained_generation_experiment.py"
+
+[[module]]
+module_name = "pontius.constrained_generation_matrix"
+relative_path = "src/pontius/constrained_generation_matrix.py"
+
+[[module]]
+module_name = "pontius.continual"
+relative_path = "src/pontius/continual.py"
+
+[[module]]
+module_name = "pontius.continuation_public_tree_tensor"
+relative_path = "src/pontius/continuation_public_tree_tensor.py"
+
+[[module]]
+module_name = "pontius.convex_retreat_tolerances"
+relative_path = "src/pontius/convex_retreat_tolerances.py"
+
+[[module]]
+module_name = "pontius.cross_payoff_adjoint_result"
+relative_path = "src/pontius/cross_payoff_adjoint_result.py"
+
+[[module]]
+module_name = "pontius.cross_payoff_leaf_adjoint"
+relative_path = "src/pontius/cross_payoff_leaf_adjoint.py"
+
+[[module]]
+module_name = "pontius.cuda_dll_bootstrap"
+relative_path = "src/pontius/cuda_dll_bootstrap.py"
+
+[[module]]
+module_name = "pontius.cupy_sparse_incidence"
+relative_path = "src/pontius/cupy_sparse_incidence.py"
+
+[[module]]
+module_name = "pontius.deadline_owned_result"
+relative_path = "src/pontius/deadline_owned_result.py"
+
+[[module]]
+module_name = "pontius.delta_certificate_contract"
+relative_path = "src/pontius/delta_certificate_contract.py"
+
+[[module]]
+module_name = "pontius.dense_root_cross_payoff_control"
+relative_path = "src/pontius/dense_root_cross_payoff_control.py"
+
+[[module]]
+module_name = "pontius.dependency_tape"
+relative_path = "src/pontius/dependency_tape.py"
+
+[[module]]
+module_name = "pontius.dependency_tape_experiment"
+relative_path = "src/pontius/dependency_tape_experiment.py"
+
+[[module]]
+module_name = "pontius.depth_limited"
+relative_path = "src/pontius/depth_limited.py"
+
+[[module]]
+module_name = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+relative_path = "src/pontius/device_fold_resident_heterogeneous_leaf_contraction.py"
+
+[[module]]
+module_name = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+relative_path = "src/pontius/device_fold_resident_heterogeneous_leaf_contraction_v2.py"
+
+[[module]]
+module_name = "pontius.device_fold_resident_leaf_adjoint_cfr"
+relative_path = "src/pontius/device_fold_resident_leaf_adjoint_cfr.py"
+
+[[module]]
+module_name = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+relative_path = "src/pontius/device_fold_resident_leaf_adjoint_cfr_v2.py"
+
+[[module]]
+module_name = "pontius.device_fold_selector_stable_affine_response"
+relative_path = "src/pontius/device_fold_selector_stable_affine_response.py"
+
+[[module]]
+module_name = "pontius.device_fold_selector_stable_affine_response_v2"
+relative_path = "src/pontius/device_fold_selector_stable_affine_response_v2.py"
+
+[[module]]
+module_name = "pontius.durable_evidence_journal"
+relative_path = "src/pontius/durable_evidence_journal.py"
+
+[[module]]
+module_name = "pontius.evaluation"
+relative_path = "src/pontius/evaluation.py"
+
+[[module]]
+module_name = "pontius.evidence_protocol"
+relative_path = "src/pontius/evidence_protocol.py"
+
+[[module]]
+module_name = "pontius.exact_collision_oracle"
+relative_path = "src/pontius/exact_collision_oracle.py"
+
+[[module]]
+module_name = "pontius.exact_directional_face_oracle"
+relative_path = "src/pontius/exact_directional_face_oracle.py"
+
+[[module]]
+module_name = "pontius.exact_directional_face_oracle_seal"
+relative_path = "src/pontius/exact_directional_face_oracle_seal.py"
+
+[[module]]
+module_name = "pontius.exact_oracle_assessment"
+relative_path = "src/pontius/exact_oracle_assessment.py"
+
+[[module]]
+module_name = "pontius.exact_selector_fan"
+relative_path = "src/pontius/exact_selector_fan.py"
+
+[[module]]
+module_name = "pontius.exact_selector_window_oracle"
+relative_path = "src/pontius/exact_selector_window_oracle.py"
+
+[[module]]
+module_name = "pontius.exact_sequence_form_coefficient_oracle"
+relative_path = "src/pontius/exact_sequence_form_coefficient_oracle.py"
+
+[[module]]
+module_name = "pontius.exact_tie_aware_affine_envelope"
+relative_path = "src/pontius/exact_tie_aware_affine_envelope.py"
+
+[[module]]
+module_name = "pontius.experiment"
+relative_path = "src/pontius/experiment.py"
+
+[[module]]
+module_name = "pontius.factor_tt_contraction"
+relative_path = "src/pontius/factor_tt_contraction.py"
+
+[[module]]
+module_name = "pontius.factor_tt_contraction_audit"
+relative_path = "src/pontius/factor_tt_contraction_audit.py"
+
+[[module]]
+module_name = "pontius.factorized_belief"
+relative_path = "src/pontius/factorized_belief.py"
+
+[[module]]
+module_name = "pontius.factorized_belief_audit"
+relative_path = "src/pontius/factorized_belief_audit.py"
+
+[[module]]
+module_name = "pontius.factorized_tie_aware_affine"
+relative_path = "src/pontius/factorized_tie_aware_affine.py"
+
+[[module]]
+module_name = "pontius.factorized_tie_aware_affine_seal"
+relative_path = "src/pontius/factorized_tie_aware_affine_seal.py"
+
+[[module]]
+module_name = "pontius.fixed_envelope_verifier"
+relative_path = "src/pontius/fixed_envelope_verifier.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_greedy"
+relative_path = "src/pontius/fresh_action_width_greedy.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_greedy_seal"
+relative_path = "src/pontius/fresh_action_width_greedy_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay"
+relative_path = "src/pontius/fresh_action_width_nonreplay.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_greedy"
+relative_path = "src/pontius/fresh_action_width_nonreplay_greedy.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_greedy_result"
+relative_path = "src/pontius/fresh_action_width_nonreplay_greedy_result.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_greedy_result_seal"
+relative_path = "src/pontius/fresh_action_width_nonreplay_greedy_result_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_greedy_seal"
+relative_path = "src/pontius/fresh_action_width_nonreplay_greedy_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_qualification"
+relative_path = "src/pontius/fresh_action_width_nonreplay_qualification.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_qualification_result"
+relative_path = "src/pontius/fresh_action_width_nonreplay_qualification_result.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_qualification_result_seal"
+relative_path = "src/pontius/fresh_action_width_nonreplay_qualification_result_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_qualification_seal"
+relative_path = "src/pontius/fresh_action_width_nonreplay_qualification_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_seal"
+relative_path = "src/pontius/fresh_action_width_nonreplay_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_teacher"
+relative_path = "src/pontius/fresh_action_width_nonreplay_teacher.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_teacher_result"
+relative_path = "src/pontius/fresh_action_width_nonreplay_teacher_result.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_teacher_result_seal"
+relative_path = "src/pontius/fresh_action_width_nonreplay_teacher_result_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_nonreplay_teacher_seal"
+relative_path = "src/pontius/fresh_action_width_nonreplay_teacher_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_qualification"
+relative_path = "src/pontius/fresh_action_width_qualification.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_qualification_result"
+relative_path = "src/pontius/fresh_action_width_qualification_result.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_qualification_result_seal"
+relative_path = "src/pontius/fresh_action_width_qualification_result_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_qualification_seal"
+relative_path = "src/pontius/fresh_action_width_qualification_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_structures"
+relative_path = "src/pontius/fresh_action_width_structures.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_structures_seal"
+relative_path = "src/pontius/fresh_action_width_structures_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_teacher"
+relative_path = "src/pontius/fresh_action_width_teacher.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_teacher_result"
+relative_path = "src/pontius/fresh_action_width_teacher_result.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_teacher_result_seal"
+relative_path = "src/pontius/fresh_action_width_teacher_result_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_teacher_seal"
+relative_path = "src/pontius/fresh_action_width_teacher_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_confirmation"
+relative_path = "src/pontius/fresh_action_width_transfer_confirmation.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_confirmation_result"
+relative_path = "src/pontius/fresh_action_width_transfer_confirmation_result.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_confirmation_result_seal"
+relative_path = "src/pontius/fresh_action_width_transfer_confirmation_result_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_confirmation_seal"
+relative_path = "src/pontius/fresh_action_width_transfer_confirmation_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_qualification"
+relative_path = "src/pontius/fresh_action_width_transfer_qualification.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_qualification_result"
+relative_path = "src/pontius/fresh_action_width_transfer_qualification_result.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_qualification_result_seal"
+relative_path = "src/pontius/fresh_action_width_transfer_qualification_result_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_qualification_seal"
+relative_path = "src/pontius/fresh_action_width_transfer_qualification_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_structures"
+relative_path = "src/pontius/fresh_action_width_transfer_structures.py"
+
+[[module]]
+module_name = "pontius.fresh_action_width_transfer_structures_seal"
+relative_path = "src/pontius/fresh_action_width_transfer_structures_seal.py"
+
+[[module]]
+module_name = "pontius.fresh_capacity_filling_qualification"
+relative_path = "src/pontius/fresh_capacity_filling_qualification.py"
+
+[[module]]
+module_name = "pontius.fresh_capacity_filling_structures"
+relative_path = "src/pontius/fresh_capacity_filling_structures.py"
+
+[[module]]
+module_name = "pontius.fresh_collision_repair_qualification"
+relative_path = "src/pontius/fresh_collision_repair_qualification.py"
+
+[[module]]
+module_name = "pontius.fresh_collision_repair_structures"
+relative_path = "src/pontius/fresh_collision_repair_structures.py"
+
+[[module]]
+module_name = "pontius.fresh_h32_strategy_transfer_audit"
+relative_path = "src/pontius/fresh_h32_strategy_transfer_audit.py"
+
+[[module]]
+module_name = "pontius.full_width_belief"
+relative_path = "src/pontius/full_width_belief.py"
+
+[[module]]
+module_name = "pontius.full_width_factor_tt_capacity"
+relative_path = "src/pontius/full_width_factor_tt_capacity.py"
+
+[[module]]
+module_name = "pontius.full_width_occupied_card_quotient_capacity"
+relative_path = "src/pontius/full_width_occupied_card_quotient_capacity.py"
+
+[[module]]
+module_name = "pontius.full_width_reference_policy"
+relative_path = "src/pontius/full_width_reference_policy.py"
+
+[[module]]
+module_name = "pontius.full_width_river_capacity_preflight"
+relative_path = "src/pontius/full_width_river_capacity_preflight.py"
+
+[[module]]
+module_name = "pontius.full_width_river_capacity_preflight_v2"
+relative_path = "src/pontius/full_width_river_capacity_preflight_v2.py"
+
+[[module]]
+module_name = "pontius.game"
+relative_path = "src/pontius/game.py"
+
+[[module]]
+module_name = "pontius.gpu_occupied_card_quotient"
+relative_path = "src/pontius/gpu_occupied_card_quotient.py"
+
+[[module]]
+module_name = "pontius.gpu_quotient_staged_scaling"
+relative_path = "src/pontius/gpu_quotient_staged_scaling.py"
+
+[[module]]
+module_name = "pontius.gpu_quotient_staged_scaling_result"
+relative_path = "src/pontius/gpu_quotient_staged_scaling_result.py"
+
+[[module]]
+module_name = "pontius.gpu_quotient_staged_scaling_runner"
+relative_path = "src/pontius/gpu_quotient_staged_scaling_runner.py"
+
+[[module]]
+module_name = "pontius.gpu_quotient_staged_scaling_v2_result"
+relative_path = "src/pontius/gpu_quotient_staged_scaling_v2_result.py"
+
+[[module]]
+module_name = "pontius.gpu_quotient_staged_scaling_v2_runner"
+relative_path = "src/pontius/gpu_quotient_staged_scaling_v2_runner.py"
+
+[[module]]
+module_name = "pontius.gpu_quotient_validation_seam"
+relative_path = "src/pontius/gpu_quotient_validation_seam.py"
+
+[[module]]
+module_name = "pontius.h32_acceptance_semantics_replay"
+relative_path = "src/pontius/h32_acceptance_semantics_replay.py"
+
+[[module]]
+module_name = "pontius.h32_action_conditioned_posterior_manifest"
+relative_path = "src/pontius/h32_action_conditioned_posterior_manifest.py"
+
+[[module]]
+module_name = "pontius.h32_action_conditioned_widened_selector_trial"
+relative_path = "src/pontius/h32_action_conditioned_widened_selector_trial.py"
+
+[[module]]
+module_name = "pontius.h32_action_width_quality_audit"
+relative_path = "src/pontius/h32_action_width_quality_audit.py"
+
+[[module]]
+module_name = "pontius.h32_action_width_quality_audit_v2"
+relative_path = "src/pontius/h32_action_width_quality_audit_v2.py"
+
+[[module]]
+module_name = "pontius.h32_affine_resident_cache_preflight"
+relative_path = "src/pontius/h32_affine_resident_cache_preflight.py"
+
+[[module]]
+module_name = "pontius.h32_atomic_response_preflight"
+relative_path = "src/pontius/h32_atomic_response_preflight.py"
+
+[[module]]
+module_name = "pontius.h32_atomic_street_scheduler_audit"
+relative_path = "src/pontius/h32_atomic_street_scheduler_audit.py"
+
+[[module]]
+module_name = "pontius.h32_candidate_availability_replay"
+relative_path = "src/pontius/h32_candidate_availability_replay.py"
+
+[[module]]
+module_name = "pontius.h32_candidate_availability_replay_v2"
+relative_path = "src/pontius/h32_candidate_availability_replay_v2.py"
+
+[[module]]
+module_name = "pontius.h32_canonical_affine_cache_replay"
+relative_path = "src/pontius/h32_canonical_affine_cache_replay.py"
+
+[[module]]
+module_name = "pontius.h32_continuation_depth_ledger"
+relative_path = "src/pontius/h32_continuation_depth_ledger.py"
+
+[[module]]
+module_name = "pontius.h32_continuation_direction_capacity"
+relative_path = "src/pontius/h32_continuation_direction_capacity.py"
+
+[[module]]
+module_name = "pontius.h32_continuation_root_ledger"
+relative_path = "src/pontius/h32_continuation_root_ledger.py"
+
+[[module]]
+module_name = "pontius.h32_continuation_root_preflight"
+relative_path = "src/pontius/h32_continuation_root_preflight.py"
+
+[[module]]
+module_name = "pontius.h32_continuation_root_strategy_trial"
+relative_path = "src/pontius/h32_continuation_root_strategy_trial.py"
+
+[[module]]
+module_name = "pontius.h32_convex_replication_posterior_manifest"
+relative_path = "src/pontius/h32_convex_replication_posterior_manifest.py"
+
+[[module]]
+module_name = "pontius.h32_cross_payoff_adjoint_feasibility"
+relative_path = "src/pontius/h32_cross_payoff_adjoint_feasibility.py"
+
+[[module]]
+module_name = "pontius.h32_current_decision_combined_ledger_replay"
+relative_path = "src/pontius/h32_current_decision_combined_ledger_replay.py"
+
+[[module]]
+module_name = "pontius.h32_current_interpolation_audit"
+relative_path = "src/pontius/h32_current_interpolation_audit.py"
+
+[[module]]
+module_name = "pontius.h32_decision_aligned_continuation_setup"
+relative_path = "src/pontius/h32_decision_aligned_continuation_setup.py"
+
+[[module]]
+module_name = "pontius.h32_decision_aligned_live_shadow_trial"
+relative_path = "src/pontius/h32_decision_aligned_live_shadow_trial.py"
+
+[[module]]
+module_name = "pontius.h32_decision_aligned_posterior_manifest"
+relative_path = "src/pontius/h32_decision_aligned_posterior_manifest.py"
+
+[[module]]
+module_name = "pontius.h32_deep_horizon_correction_replay"
+relative_path = "src/pontius/h32_deep_horizon_correction_replay.py"
+
+[[module]]
+module_name = "pontius.h32_deep_horizon_opportunity_audit"
+relative_path = "src/pontius/h32_deep_horizon_opportunity_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_board_panel_cache_preflight"
+relative_path = "src/pontius/h32_fresh_board_panel_cache_preflight.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_causal_direction_screen"
+relative_path = "src/pontius/h32_fresh_causal_direction_screen.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_convex_retreat_replication"
+relative_path = "src/pontius/h32_fresh_convex_retreat_replication.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+relative_path = "src/pontius/h32_fresh_panel_action_width_warm_step_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_panel_action_width_warm_step_audit_v2"
+relative_path = "src/pontius/h32_fresh_panel_action_width_warm_step_audit_v2.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_panel_source_blueprint_audit"
+relative_path = "src/pontius/h32_fresh_panel_source_blueprint_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_panel_target_transfer_audit"
+relative_path = "src/pontius/h32_fresh_panel_target_transfer_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_panel_target_transfer_audit_v2"
+relative_path = "src/pontius/h32_fresh_panel_target_transfer_audit_v2.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_public_block_radius_audit"
+relative_path = "src/pontius/h32_fresh_public_block_radius_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_public_block_value_audit"
+relative_path = "src/pontius/h32_fresh_public_block_value_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+relative_path = "src/pontius/h32_fresh_regret_vertex_opportunity_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_selector_stable_affine_street_audit"
+relative_path = "src/pontius/h32_fresh_selector_stable_affine_street_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+relative_path = "src/pontius/h32_fresh_selector_stable_affine_street_seat5_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_union_value_audit"
+relative_path = "src/pontius/h32_fresh_union_value_audit.py"
+
+[[module]]
+module_name = "pontius.h32_fresh_union_value_audit_v2"
+relative_path = "src/pontius/h32_fresh_union_value_audit_v2.py"
+
+[[module]]
+module_name = "pontius.h32_heldout_continuation_depth_value_trial"
+relative_path = "src/pontius/h32_heldout_continuation_depth_value_trial.py"
+
+[[module]]
+module_name = "pontius.h32_heldout_continuation_posterior_manifest"
+relative_path = "src/pontius/h32_heldout_continuation_posterior_manifest.py"
+
+[[module]]
+module_name = "pontius.h32_latin_f_convex_retreat_confirmation"
+relative_path = "src/pontius/h32_latin_f_convex_retreat_confirmation.py"
+
+[[module]]
+module_name = "pontius.h32_multi_size_resident_cache_preflight"
+relative_path = "src/pontius/h32_multi_size_resident_cache_preflight.py"
+
+[[module]]
+module_name = "pontius.h32_one_round_convex_master"
+relative_path = "src/pontius/h32_one_round_convex_master.py"
+
+[[module]]
+module_name = "pontius.h32_one_seat_open_axis_preflight"
+relative_path = "src/pontius/h32_one_seat_open_axis_preflight.py"
+
+[[module]]
+module_name = "pontius.h32_one_seat_retreat_quality_trial"
+relative_path = "src/pontius/h32_one_seat_retreat_quality_trial.py"
+
+[[module]]
+module_name = "pontius.h32_one_seat_retreat_quality_trial_v2"
+relative_path = "src/pontius/h32_one_seat_retreat_quality_trial_v2.py"
+
+[[module]]
+module_name = "pontius.h32_policy_delta_verifier_audit"
+relative_path = "src/pontius/h32_policy_delta_verifier_audit.py"
+
+[[module]]
+module_name = "pontius.h32_post_fold_closure_value_confirmation"
+relative_path = "src/pontius/h32_post_fold_closure_value_confirmation.py"
+
+[[module]]
+module_name = "pontius.h32_post_fold_current_decision_setup"
+relative_path = "src/pontius/h32_post_fold_current_decision_setup.py"
+
+[[module]]
+module_name = "pontius.h32_post_fold_failure_closure_diagnostic"
+relative_path = "src/pontius/h32_post_fold_failure_closure_diagnostic.py"
+
+[[module]]
+module_name = "pontius.h32_post_fold_posterior_manifest"
+relative_path = "src/pontius/h32_post_fold_posterior_manifest.py"
+
+[[module]]
+module_name = "pontius.h32_pre_bet_action_width_capacity"
+relative_path = "src/pontius/h32_pre_bet_action_width_capacity.py"
+
+[[module]]
+module_name = "pontius.h32_pre_bet_initial_row_cache_seed"
+relative_path = "src/pontius/h32_pre_bet_initial_row_cache_seed.py"
+
+[[module]]
+module_name = "pontius.h32_pre_bet_initial_row_gpu"
+relative_path = "src/pontius/h32_pre_bet_initial_row_gpu.py"
+
+[[module]]
+module_name = "pontius.h32_pre_bet_work_reduction_analysis"
+relative_path = "src/pontius/h32_pre_bet_work_reduction_analysis.py"
+
+[[module]]
+module_name = "pontius.h32_resident_cfr_audit"
+relative_path = "src/pontius/h32_resident_cfr_audit.py"
+
+[[module]]
+module_name = "pontius.h32_resident_cfr_audit_v2"
+relative_path = "src/pontius/h32_resident_cfr_audit_v2.py"
+
+[[module]]
+module_name = "pontius.h32_resident_cfr_restart_semantics_audit"
+relative_path = "src/pontius/h32_resident_cfr_restart_semantics_audit.py"
+
+[[module]]
+module_name = "pontius.h32_resident_cfr_sustained_audit"
+relative_path = "src/pontius/h32_resident_cfr_sustained_audit.py"
+
+[[module]]
+module_name = "pontius.h32_resident_record_to_hand_fold_differential"
+relative_path = "src/pontius/h32_resident_record_to_hand_fold_differential.py"
+
+[[module]]
+module_name = "pontius.h32_resident_sparse_ncu_profile"
+relative_path = "src/pontius/h32_resident_sparse_ncu_profile.py"
+
+[[module]]
+module_name = "pontius.h32_resident_sparse_ncu_profile_v2"
+relative_path = "src/pontius/h32_resident_sparse_ncu_profile_v2.py"
+
+[[module]]
+module_name = "pontius.h32_resident_sparse_ncu_profile_v3"
+relative_path = "src/pontius/h32_resident_sparse_ncu_profile_v3.py"
+
+[[module]]
+module_name = "pontius.h32_resident_sparse_ncu_workload"
+relative_path = "src/pontius/h32_resident_sparse_ncu_workload.py"
+
+[[module]]
+module_name = "pontius.h32_resident_step_bottleneck_profile"
+relative_path = "src/pontius/h32_resident_step_bottleneck_profile.py"
+
+[[module]]
+module_name = "pontius.h32_resident_step_bottleneck_profile_v2"
+relative_path = "src/pontius/h32_resident_step_bottleneck_profile_v2.py"
+
+[[module]]
+module_name = "pontius.h32_resident_verifier_audit"
+relative_path = "src/pontius/h32_resident_verifier_audit.py"
+
+[[module]]
+module_name = "pontius.h32_response_latency_bridge_audit"
+relative_path = "src/pontius/h32_response_latency_bridge_audit.py"
+
+[[module]]
+module_name = "pontius.h32_retained_affine_selector_cascade_direct_replay"
+relative_path = "src/pontius/h32_retained_affine_selector_cascade_direct_replay.py"
+
+[[module]]
+module_name = "pontius.h32_retained_affine_selector_cascade_replay"
+relative_path = "src/pontius/h32_retained_affine_selector_cascade_replay.py"
+
+[[module]]
+module_name = "pontius.h32_retained_affine_selector_cascade_replay_v2"
+relative_path = "src/pontius/h32_retained_affine_selector_cascade_replay_v2.py"
+
+[[module]]
+module_name = "pontius.h32_retained_affine_selector_cascade_replay_v3"
+relative_path = "src/pontius/h32_retained_affine_selector_cascade_replay_v3.py"
+
+[[module]]
+module_name = "pontius.h32_retained_convex_closure_census"
+relative_path = "src/pontius/h32_retained_convex_closure_census.py"
+
+[[module]]
+module_name = "pontius.h32_retained_convex_closure_census_v2"
+relative_path = "src/pontius/h32_retained_convex_closure_census_v2.py"
+
+[[module]]
+module_name = "pontius.h32_second_board_action_width_quality_audit"
+relative_path = "src/pontius/h32_second_board_action_width_quality_audit.py"
+
+[[module]]
+module_name = "pontius.h32_second_board_resident_cache_preflight"
+relative_path = "src/pontius/h32_second_board_resident_cache_preflight.py"
+
+[[module]]
+module_name = "pontius.h32_selector_stable_affine_certificate_audit"
+relative_path = "src/pontius/h32_selector_stable_affine_certificate_audit.py"
+
+[[module]]
+module_name = "pontius.h32_selector_stable_affine_certificate_audit_v2"
+relative_path = "src/pontius/h32_selector_stable_affine_certificate_audit_v2.py"
+
+[[module]]
+module_name = "pontius.h32_shared_response_allocator_lifecycle_replay"
+relative_path = "src/pontius/h32_shared_response_allocator_lifecycle_replay.py"
+
+[[module]]
+module_name = "pontius.h32_shared_response_residency_replay"
+relative_path = "src/pontius/h32_shared_response_residency_replay.py"
+
+[[module]]
+module_name = "pontius.h32_tier_b_opponent_batch_differential"
+relative_path = "src/pontius/h32_tier_b_opponent_batch_differential.py"
+
+[[module]]
+module_name = "pontius.h32_tier_b_opponent_batch_differential_v2"
+relative_path = "src/pontius/h32_tier_b_opponent_batch_differential_v2.py"
+
+[[module]]
+module_name = "pontius.h32_warm_candidate_stream_audit"
+relative_path = "src/pontius/h32_warm_candidate_stream_audit.py"
+
+[[module]]
+module_name = "pontius.h32_warm_search_acceptance_audit"
+relative_path = "src/pontius/h32_warm_search_acceptance_audit.py"
+
+[[module]]
+module_name = "pontius.h4_sequence_form_open_axis_differential"
+relative_path = "src/pontius/h4_sequence_form_open_axis_differential.py"
+
+[[module]]
+module_name = "pontius.h4_shifted_belief_dense_crosscheck"
+relative_path = "src/pontius/h4_shifted_belief_dense_crosscheck.py"
+
+[[module]]
+module_name = "pontius.heterogeneous_leaf_contraction"
+relative_path = "src/pontius/heterogeneous_leaf_contraction.py"
+
+[[module]]
+module_name = "pontius.holdem_cards"
+relative_path = "src/pontius/holdem_cards.py"
+
+[[module]]
+module_name = "pontius.immutable_blueprint"
+relative_path = "src/pontius/immutable_blueprint.py"
+
+[[module]]
+module_name = "pontius.incremental_leaf_adjoint_response"
+relative_path = "src/pontius/incremental_leaf_adjoint_response.py"
+
+[[module]]
+module_name = "pontius.incremental_policy_tt"
+relative_path = "src/pontius/incremental_policy_tt.py"
+
+[[module]]
+module_name = "pontius.kuhn"
+relative_path = "src/pontius/kuhn.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_batch_width_audit"
+relative_path = "src/pontius/leaf_adjoint_batch_width_audit.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_batch_width_audit_v2"
+relative_path = "src/pontius/leaf_adjoint_batch_width_audit_v2.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_cfr"
+relative_path = "src/pontius/leaf_adjoint_cfr.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_cfr_audit"
+relative_path = "src/pontius/leaf_adjoint_cfr_audit.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_checkpoint_extension_audit"
+relative_path = "src/pontius/leaf_adjoint_checkpoint_extension_audit.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+relative_path = "src/pontius/leaf_adjoint_checkpoint_ladder_audit.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+relative_path = "src/pontius/leaf_adjoint_checkpoint_ladder_audit_v2.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_evaluation"
+relative_path = "src/pontius/leaf_adjoint_evaluation.py"
+
+[[module]]
+module_name = "pontius.leaf_adjoint_evaluation_audit"
+relative_path = "src/pontius/leaf_adjoint_evaluation_audit.py"
+
+[[module]]
+module_name = "pontius.leaf_experiment"
+relative_path = "src/pontius/leaf_experiment.py"
+
+[[module]]
+module_name = "pontius.leaf_matrix"
+relative_path = "src/pontius/leaf_matrix.py"
+
+[[module]]
+module_name = "pontius.legal_action_abstraction"
+relative_path = "src/pontius/legal_action_abstraction.py"
+
+[[module]]
+module_name = "pontius.legal_decision_spine"
+relative_path = "src/pontius/legal_decision_spine.py"
+
+[[module]]
+module_name = "pontius.legal_decision_spine_v2"
+relative_path = "src/pontius/legal_decision_spine_v2.py"
+
+[[module]]
+module_name = "pontius.legal_h4_factorized_affine_confirmation"
+relative_path = "src/pontius/legal_h4_factorized_affine_confirmation.py"
+
+[[module]]
+module_name = "pontius.legal_h4_factorized_affine_confirmation_directions"
+relative_path = "src/pontius/legal_h4_factorized_affine_confirmation_directions.py"
+
+[[module]]
+module_name = "pontius.legal_h4_factorized_affine_confirmation_population"
+relative_path = "src/pontius/legal_h4_factorized_affine_confirmation_population.py"
+
+[[module]]
+module_name = "pontius.legal_h4_factorized_affine_confirmation_population_seal"
+relative_path = "src/pontius/legal_h4_factorized_affine_confirmation_population_seal.py"
+
+[[module]]
+module_name = "pontius.legal_h4_factorized_affine_confirmation_result"
+relative_path = "src/pontius/legal_h4_factorized_affine_confirmation_result.py"
+
+[[module]]
+module_name = "pontius.legal_h4_factorized_affine_confirmation_result_seal"
+relative_path = "src/pontius/legal_h4_factorized_affine_confirmation_result_seal.py"
+
+[[module]]
+module_name = "pontius.legal_h4_selector_directions"
+relative_path = "src/pontius/legal_h4_selector_directions.py"
+
+[[module]]
+module_name = "pontius.legal_h4_selector_fixture"
+relative_path = "src/pontius/legal_h4_selector_fixture.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_coefficient_differential"
+relative_path = "src/pontius/legal_responder_raise_h4_coefficient_differential.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_coefficient_result"
+relative_path = "src/pontius/legal_responder_raise_h4_coefficient_result.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_coefficient_result_seal"
+relative_path = "src/pontius/legal_responder_raise_h4_coefficient_result_seal.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_directional_face"
+relative_path = "src/pontius/legal_responder_raise_h4_directional_face.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_directional_face_result"
+relative_path = "src/pontius/legal_responder_raise_h4_directional_face_result.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_directional_face_result_seal"
+relative_path = "src/pontius/legal_responder_raise_h4_directional_face_result_seal.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_factorized_affine"
+relative_path = "src/pontius/legal_responder_raise_h4_factorized_affine.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_factorized_affine_result"
+relative_path = "src/pontius/legal_responder_raise_h4_factorized_affine_result.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_factorized_affine_result_seal"
+relative_path = "src/pontius/legal_responder_raise_h4_factorized_affine_result_seal.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_row_growth"
+relative_path = "src/pontius/legal_responder_raise_h4_row_growth.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_row_growth_result"
+relative_path = "src/pontius/legal_responder_raise_h4_row_growth_result.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_row_growth_result_seal"
+relative_path = "src/pontius/legal_responder_raise_h4_row_growth_result_seal.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_selector_fan_result"
+relative_path = "src/pontius/legal_responder_raise_h4_selector_fan_result.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_selector_fan_result_seal"
+relative_path = "src/pontius/legal_responder_raise_h4_selector_fan_result_seal.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_selector_window"
+relative_path = "src/pontius/legal_responder_raise_h4_selector_window.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_tie_aware_affine"
+relative_path = "src/pontius/legal_responder_raise_h4_tie_aware_affine.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_tie_aware_affine_result"
+relative_path = "src/pontius/legal_responder_raise_h4_tie_aware_affine_result.py"
+
+[[module]]
+module_name = "pontius.legal_responder_raise_h4_tie_aware_affine_result_seal"
+relative_path = "src/pontius/legal_responder_raise_h4_tie_aware_affine_result_seal.py"
+
+[[module]]
+module_name = "pontius.legal_river_continuation"
+relative_path = "src/pontius/legal_river_continuation.py"
+
+[[module]]
+module_name = "pontius.legal_river_exact_cubin_inspector_diagnostic"
+relative_path = "src/pontius/legal_river_exact_cubin_inspector_diagnostic.py"
+
+[[module]]
+module_name = "pontius.legal_river_exact_cubin_inspector_diagnostic_result"
+relative_path = "src/pontius/legal_river_exact_cubin_inspector_diagnostic_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_exact_cubin_inspector_diagnostic_runner"
+relative_path = "src/pontius/legal_river_exact_cubin_inspector_diagnostic_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_exact_cubin_inspector_selection"
+relative_path = "src/pontius/legal_river_exact_cubin_inspector_selection.py"
+
+[[module]]
+module_name = "pontius.legal_river_exact_cubin_inspector_selection_seal"
+relative_path = "src/pontius/legal_river_exact_cubin_inspector_selection_seal.py"
+
+[[module]]
+module_name = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic"
+relative_path = "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic.py"
+
+[[module]]
+module_name = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_result"
+relative_path = "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_runner"
+relative_path = "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_base_provenance"
+relative_path = "src/pontius/legal_river_quotient_base_provenance.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_bridge"
+relative_path = "src/pontius/legal_river_quotient_bridge.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_result"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_result"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_result"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_result"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v4_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v4_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v5_result"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v5_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v5_runner"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v5_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v6_result"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v6_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v6_runner"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v6_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_result"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v7_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_runner"
+relative_path = "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v7_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_consumer_capacity"
+relative_path = "src/pontius/legal_river_quotient_consumer_capacity.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_tiles"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_tiles.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_result"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_runner"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_result"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_adapter"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_adapter.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_result"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_adapter"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_adapter.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner"
+relative_path = "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_consumer"
+relative_path = "src/pontius/legal_river_quotient_cuda_consumer.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_device"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_device.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_device_result"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_device_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_device_runner"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_device_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_device_v2_result"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_device_v2_runner"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_device_v3_result"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_device_v3_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_device_v3_runner"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_device_v3_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_oracle"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_oracle.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_cuda_shared_direct_sample_plan"
+relative_path = "src/pontius/legal_river_quotient_cuda_shared_direct_sample_plan.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_exact_integer_operator"
+relative_path = "src/pontius/legal_river_quotient_exact_integer_operator.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_outcome"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_outcome.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_result"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_runner"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight_result"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight_runner"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_outcome"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_outcome.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_result"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_outcome"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_outcome.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_result"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_fixed_width_work_comparison"
+relative_path = "src/pontius/legal_river_quotient_fixed_width_work_comparison.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_global_separation_topologies"
+relative_path = "src/pontius/legal_river_quotient_global_separation_topologies.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_selective_certified_separation"
+relative_path = "src/pontius/legal_river_quotient_selective_certified_separation.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_selective_certified_separation_result"
+relative_path = "src/pontius/legal_river_quotient_selective_certified_separation_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_selective_certified_separation_runner"
+relative_path = "src/pontius/legal_river_quotient_selective_certified_separation_runner.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_shared_direct_artifact_capacity"
+relative_path = "src/pontius/legal_river_quotient_shared_direct_artifact_capacity.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_shared_direct_artifact_capacity_result"
+relative_path = "src/pontius/legal_river_quotient_shared_direct_artifact_capacity_result.py"
+
+[[module]]
+module_name = "pontius.legal_river_quotient_shared_direct_artifact_capacity_runner"
+relative_path = "src/pontius/legal_river_quotient_shared_direct_artifact_capacity_runner.py"
+
+[[module]]
+module_name = "pontius.linear_program"
+relative_path = "src/pontius/linear_program.py"
+
+[[module]]
+module_name = "pontius.linear_program_certificate"
+relative_path = "src/pontius/linear_program_certificate.py"
+
+[[module]]
+module_name = "pontius.literal_45_quotient_liveness"
+relative_path = "src/pontius/literal_45_quotient_liveness.py"
+
+[[module]]
+module_name = "pontius.literal_45_quotient_target"
+relative_path = "src/pontius/literal_45_quotient_target.py"
+
+[[module]]
+module_name = "pontius.literal_45_quotient_target_result"
+relative_path = "src/pontius/literal_45_quotient_target_result.py"
+
+[[module]]
+module_name = "pontius.literal_45_quotient_target_runner"
+relative_path = "src/pontius/literal_45_quotient_target_runner.py"
+
+[[module]]
+module_name = "pontius.local_response_bridge"
+relative_path = "src/pontius/local_response_bridge.py"
+
+[[module]]
+module_name = "pontius.matrix_game"
+relative_path = "src/pontius/matrix_game.py"
+
+[[module]]
+module_name = "pontius.maxmargin"
+relative_path = "src/pontius/maxmargin.py"
+
+[[module]]
+module_name = "pontius.multi_size_affine_cross_payoff"
+relative_path = "src/pontius/multi_size_affine_cross_payoff.py"
+
+[[module]]
+module_name = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+relative_path = "src/pontius/multi_size_affine_resident_leaf_adjoint_cfr.py"
+
+[[module]]
+module_name = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+relative_path = "src/pontius/multi_size_affine_resident_leaf_adjoint_evaluation.py"
+
+[[module]]
+module_name = "pontius.multi_size_continuation_public_tree_tensor"
+relative_path = "src/pontius/multi_size_continuation_public_tree_tensor.py"
+
+[[module]]
+module_name = "pontius.multi_size_leaf_adjoint"
+relative_path = "src/pontius/multi_size_leaf_adjoint.py"
+
+[[module]]
+module_name = "pontius.multi_size_leaf_adjoint_audit"
+relative_path = "src/pontius/multi_size_leaf_adjoint_audit.py"
+
+[[module]]
+module_name = "pontius.multi_size_policy_bridge"
+relative_path = "src/pontius/multi_size_policy_bridge.py"
+
+[[module]]
+module_name = "pontius.multi_size_public_tree_tensor"
+relative_path = "src/pontius/multi_size_public_tree_tensor.py"
+
+[[module]]
+module_name = "pontius.multi_size_resident_leaf_adjoint_cfr"
+relative_path = "src/pontius/multi_size_resident_leaf_adjoint_cfr.py"
+
+[[module]]
+module_name = "pontius.multiway_river_calibration"
+relative_path = "src/pontius/multiway_river_calibration.py"
+
+[[module]]
+module_name = "pontius.multiway_river_context"
+relative_path = "src/pontius/multiway_river_context.py"
+
+[[module]]
+module_name = "pontius.multiway_search_experiment"
+relative_path = "src/pontius/multiway_search_experiment.py"
+
+[[module]]
+module_name = "pontius.multiway_source_tape_audit"
+relative_path = "src/pontius/multiway_source_tape_audit.py"
+
+[[module]]
+module_name = "pontius.native_simplex_audit_corpus"
+relative_path = "src/pontius/native_simplex_audit_corpus.py"
+
+[[module]]
+module_name = "pontius.native_simplex_audit_reanalysis"
+relative_path = "src/pontius/native_simplex_audit_reanalysis.py"
+
+[[module]]
+module_name = "pontius.native_simplex_audit_reanalysis_seal"
+relative_path = "src/pontius/native_simplex_audit_reanalysis_seal.py"
+
+[[module]]
+module_name = "pontius.native_simplex_audit_runner"
+relative_path = "src/pontius/native_simplex_audit_runner.py"
+
+[[module]]
+module_name = "pontius.native_simplex_audit_seal"
+relative_path = "src/pontius/native_simplex_audit_seal.py"
+
+[[module]]
+module_name = "pontius.native_simplex_audit_structures"
+relative_path = "src/pontius/native_simplex_audit_structures.py"
+
+[[module]]
+module_name = "pontius.no_limit_betting"
+relative_path = "src/pontius/no_limit_betting.py"
+
+[[module]]
+module_name = "pontius.occupied_card_quotient"
+relative_path = "src/pontius/occupied_card_quotient.py"
+
+[[module]]
+module_name = "pontius.one_seat_convex_generation"
+relative_path = "src/pontius/one_seat_convex_generation.py"
+
+[[module]]
+module_name = "pontius.one_seat_convex_keystone"
+relative_path = "src/pontius/one_seat_convex_keystone.py"
+
+[[module]]
+module_name = "pontius.one_seat_row_growth_audit"
+relative_path = "src/pontius/one_seat_row_growth_audit.py"
+
+[[module]]
+module_name = "pontius.open_mode_audit"
+relative_path = "src/pontius/open_mode_audit.py"
+
+[[module]]
+module_name = "pontius.open_mode_cfr_bridge"
+relative_path = "src/pontius/open_mode_cfr_bridge.py"
+
+[[module]]
+module_name = "pontius.open_mode_factor_tt"
+relative_path = "src/pontius/open_mode_factor_tt.py"
+
+[[module]]
+module_name = "pontius.open_mode_showdown"
+relative_path = "src/pontius/open_mode_showdown.py"
+
+[[module]]
+module_name = "pontius.opportunity_trace"
+relative_path = "src/pontius/opportunity_trace.py"
+
+[[module]]
+module_name = "pontius.payoff_semantics"
+relative_path = "src/pontius/payoff_semantics.py"
+
+[[module]]
+module_name = "pontius.policy"
+relative_path = "src/pontius/policy.py"
+
+[[module]]
+module_name = "pontius.policy_delta_experiment"
+relative_path = "src/pontius/policy_delta_experiment.py"
+
+[[module]]
+module_name = "pontius.policy_delta_tt_audit"
+relative_path = "src/pontius/policy_delta_tt_audit.py"
+
+[[module]]
+module_name = "pontius.pre_bet_initial_row_cache"
+relative_path = "src/pontius/pre_bet_initial_row_cache.py"
+
+[[module]]
+module_name = "pontius.pre_bet_initial_row_cache_v2"
+relative_path = "src/pontius/pre_bet_initial_row_cache_v2.py"
+
+[[module]]
+module_name = "pontius.preparation_bank"
+relative_path = "src/pontius/preparation_bank.py"
+
+[[module]]
+module_name = "pontius.profiled_policy_tt"
+relative_path = "src/pontius/profiled_policy_tt.py"
+
+[[module]]
+module_name = "pontius.public_node_behavioral_axis"
+relative_path = "src/pontius/public_node_behavioral_axis.py"
+
+[[module]]
+module_name = "pontius.public_node_open_axis"
+relative_path = "src/pontius/public_node_open_axis.py"
+
+[[module]]
+module_name = "pontius.public_policy_tt"
+relative_path = "src/pontius/public_policy_tt.py"
+
+[[module]]
+module_name = "pontius.public_policy_tt_audit"
+relative_path = "src/pontius/public_policy_tt_audit.py"
+
+[[module]]
+module_name = "pontius.public_tree_quotient_audit"
+relative_path = "src/pontius/public_tree_quotient_audit.py"
+
+[[module]]
+module_name = "pontius.public_tree_tensor"
+relative_path = "src/pontius/public_tree_tensor.py"
+
+[[module]]
+module_name = "pontius.public_tree_tensor_cfr"
+relative_path = "src/pontius/public_tree_tensor_cfr.py"
+
+[[module]]
+module_name = "pontius.real_policy"
+relative_path = "src/pontius/real_policy.py"
+
+[[module]]
+module_name = "pontius.real_policy_representation_audit"
+relative_path = "src/pontius/real_policy_representation_audit.py"
+
+[[module]]
+module_name = "pontius.real_policy_representation_audit_v2"
+relative_path = "src/pontius/real_policy_representation_audit_v2.py"
+
+[[module]]
+module_name = "pontius.real_policy_source"
+relative_path = "src/pontius/real_policy_source.py"
+
+[[module]]
+module_name = "pontius.reduced_river_sizing_lp"
+relative_path = "src/pontius/reduced_river_sizing_lp.py"
+
+[[module]]
+module_name = "pontius.reduced_river_sizing_oracle"
+relative_path = "src/pontius/reduced_river_sizing_oracle.py"
+
+[[module]]
+module_name = "pontius.reference_hand_replay"
+relative_path = "src/pontius/reference_hand_replay.py"
+
+[[module]]
+module_name = "pontius.reporting"
+relative_path = "src/pontius/reporting.py"
+
+[[module]]
+module_name = "pontius.resident_heterogeneous_leaf_contraction"
+relative_path = "src/pontius/resident_heterogeneous_leaf_contraction.py"
+
+[[module]]
+module_name = "pontius.resident_leaf_adjoint_cfr"
+relative_path = "src/pontius/resident_leaf_adjoint_cfr.py"
+
+[[module]]
+module_name = "pontius.resident_leaf_adjoint_evaluation"
+relative_path = "src/pontius/resident_leaf_adjoint_evaluation.py"
+
+[[module]]
+module_name = "pontius.resident_record_to_hand_fold"
+relative_path = "src/pontius/resident_record_to_hand_fold.py"
+
+[[module]]
+module_name = "pontius.resident_record_to_hand_fold_v2"
+relative_path = "src/pontius/resident_record_to_hand_fold_v2.py"
+
+[[module]]
+module_name = "pontius.responder_raise_semantics_keystone"
+relative_path = "src/pontius/responder_raise_semantics_keystone.py"
+
+[[module]]
+module_name = "pontius.responder_raise_semantics_keystone_result"
+relative_path = "src/pontius/responder_raise_semantics_keystone_result.py"
+
+[[module]]
+module_name = "pontius.responder_raise_semantics_keystone_result_seal"
+relative_path = "src/pontius/responder_raise_semantics_keystone_result_seal.py"
+
+[[module]]
+module_name = "pontius.retrospective_atomic_value_capture"
+relative_path = "src/pontius/retrospective_atomic_value_capture.py"
+
+[[module]]
+module_name = "pontius.river"
+relative_path = "src/pontius/river.py"
+
+[[module]]
+module_name = "pontius.river_cache"
+relative_path = "src/pontius/river_cache.py"
+
+[[module]]
+module_name = "pontius.river_context"
+relative_path = "src/pontius/river_context.py"
+
+[[module]]
+module_name = "pontius.river_incremental"
+relative_path = "src/pontius/river_incremental.py"
+
+[[module]]
+module_name = "pontius.river_incremental_experiment"
+relative_path = "src/pontius/river_incremental_experiment.py"
+
+[[module]]
+module_name = "pontius.river_multi_size"
+relative_path = "src/pontius/river_multi_size.py"
+
+[[module]]
+module_name = "pontius.river_multi_size_audit"
+relative_path = "src/pontius/river_multi_size_audit.py"
+
+[[module]]
+module_name = "pontius.river_multi_size_experiment"
+relative_path = "src/pontius/river_multi_size_experiment.py"
+
+[[module]]
+module_name = "pontius.river_multiway"
+relative_path = "src/pontius/river_multiway.py"
+
+[[module]]
+module_name = "pontius.river_multiway_multi_size"
+relative_path = "src/pontius/river_multiway_multi_size.py"
+
+[[module]]
+module_name = "pontius.river_noop_full_replication"
+relative_path = "src/pontius/river_noop_full_replication.py"
+
+[[module]]
+module_name = "pontius.river_opportunity"
+relative_path = "src/pontius/river_opportunity.py"
+
+[[module]]
+module_name = "pontius.river_oracle"
+relative_path = "src/pontius/river_oracle.py"
+
+[[module]]
+module_name = "pontius.river_range_reuse"
+relative_path = "src/pontius/river_range_reuse.py"
+
+[[module]]
+module_name = "pontius.river_scheduler_holdout"
+relative_path = "src/pontius/river_scheduler_holdout.py"
+
+[[module]]
+module_name = "pontius.river_scheduler_screen"
+relative_path = "src/pontius/river_scheduler_screen.py"
+
+[[module]]
+module_name = "pontius.river_selective"
+relative_path = "src/pontius/river_selective.py"
+
+[[module]]
+module_name = "pontius.river_selective_analysis"
+relative_path = "src/pontius/river_selective_analysis.py"
+
+[[module]]
+module_name = "pontius.river_selective_experiment"
+relative_path = "src/pontius/river_selective_experiment.py"
+
+[[module]]
+module_name = "pontius.river_selective_payoff_audit"
+relative_path = "src/pontius/river_selective_payoff_audit.py"
+
+[[module]]
+module_name = "pontius.river_selective_screen"
+relative_path = "src/pontius/river_selective_screen.py"
+
+[[module]]
+module_name = "pontius.river_shadow_probe"
+relative_path = "src/pontius/river_shadow_probe.py"
+
+[[module]]
+module_name = "pontius.river_trace_analysis"
+relative_path = "src/pontius/river_trace_analysis.py"
+
+[[module]]
+module_name = "pontius.river_trace_comparison"
+relative_path = "src/pontius/river_trace_comparison.py"
+
+[[module]]
+module_name = "pontius.runner_harness"
+relative_path = "src/pontius/runner_harness.py"
+
+[[module]]
+module_name = "pontius.runner_harness_v2"
+relative_path = "src/pontius/runner_harness_v2.py"
+
+[[module]]
+module_name = "pontius.safe_composition_experiment"
+relative_path = "src/pontius/safe_composition_experiment.py"
+
+[[module]]
+module_name = "pontius.safe_composition_matrix"
+relative_path = "src/pontius/safe_composition_matrix.py"
+
+[[module]]
+module_name = "pontius.safe_oracle_experiment"
+relative_path = "src/pontius/safe_oracle_experiment.py"
+
+[[module]]
+module_name = "pontius.safe_oracle_matrix"
+relative_path = "src/pontius/safe_oracle_matrix.py"
+
+[[module]]
+module_name = "pontius.safe_resolving"
+relative_path = "src/pontius/safe_resolving.py"
+
+[[module]]
+module_name = "pontius.safe_solver_gap_experiment"
+relative_path = "src/pontius/safe_solver_gap_experiment.py"
+
+[[module]]
+module_name = "pontius.safe_solver_gap_matrix"
+relative_path = "src/pontius/safe_solver_gap_matrix.py"
+
+[[module]]
+module_name = "pontius.seat_order_tt"
+relative_path = "src/pontius/seat_order_tt.py"
+
+[[module]]
+module_name = "pontius.selection"
+relative_path = "src/pontius/selection.py"
+
+[[module]]
+module_name = "pontius.selective_tree"
+relative_path = "src/pontius/selective_tree.py"
+
+[[module]]
+module_name = "pontius.selector_fan_controls"
+relative_path = "src/pontius/selector_fan_controls.py"
+
+[[module]]
+module_name = "pontius.selector_stable_affine_response"
+relative_path = "src/pontius/selector_stable_affine_response.py"
+
+[[module]]
+module_name = "pontius.selector_window"
+relative_path = "src/pontius/selector_window.py"
+
+[[module]]
+module_name = "pontius.selector_window_v2"
+relative_path = "src/pontius/selector_window_v2.py"
+
+[[module]]
+module_name = "pontius.sequence_form_open_axis"
+relative_path = "src/pontius/sequence_form_open_axis.py"
+
+[[module]]
+module_name = "pontius.shared_resident_response_context"
+relative_path = "src/pontius/shared_resident_response_context.py"
+
+[[module]]
+module_name = "pontius.showdown_value_rank_screen"
+relative_path = "src/pontius/showdown_value_rank_screen.py"
+
+[[module]]
+module_name = "pontius.signed_clean_fringe_audit"
+relative_path = "src/pontius/signed_clean_fringe_audit.py"
+
+[[module]]
+module_name = "pontius.signed_clean_fringe_tt"
+relative_path = "src/pontius/signed_clean_fringe_tt.py"
+
+[[module]]
+module_name = "pontius.sizing_power_diagnostic"
+relative_path = "src/pontius/sizing_power_diagnostic.py"
+
+[[module]]
+module_name = "pontius.sparse_incidence_audit"
+relative_path = "src/pontius/sparse_incidence_audit.py"
+
+[[module]]
+module_name = "pontius.sparse_incidence_open_mode"
+relative_path = "src/pontius/sparse_incidence_open_mode.py"
+
+[[module]]
+module_name = "pontius.sparse_open_mode_cfr"
+relative_path = "src/pontius/sparse_open_mode_cfr.py"
+
+[[module]]
+module_name = "pontius.sparse_open_mode_factor_tt"
+relative_path = "src/pontius/sparse_open_mode_factor_tt.py"
+
+[[module]]
+module_name = "pontius.status_generation"
+relative_path = "src/pontius/status_generation.py"
+
+[[module]]
+module_name = "pontius.street_deadline"
+relative_path = "src/pontius/street_deadline.py"
+
+[[module]]
+module_name = "pontius.structured_showdown_automaton"
+relative_path = "src/pontius/structured_showdown_automaton.py"
+
+[[module]]
+module_name = "pontius.structured_showdown_automaton_audit"
+relative_path = "src/pontius/structured_showdown_automaton_audit.py"
+
+[[module]]
+module_name = "pontius.tensor_train"
+relative_path = "src/pontius/tensor_train.py"
+
+[[module]]
+module_name = "pontius.tensor_train_algebra"
+relative_path = "src/pontius/tensor_train_algebra.py"
+
+[[module]]
+module_name = "pontius.terminal_tensor_evaluation"
+relative_path = "src/pontius/terminal_tensor_evaluation.py"
+
+[[module]]
+module_name = "pontius.tie_aware_affine_adapter"
+relative_path = "src/pontius/tie_aware_affine_adapter.py"
+
+[[module]]
+module_name = "pontius.tie_semantics_conformance"
+relative_path = "src/pontius/tie_semantics_conformance.py"
+
+[[module]]
+module_name = "pontius.tie_semantics_conformance_v2"
+relative_path = "src/pontius/tie_semantics_conformance_v2.py"
+
+[[module]]
+module_name = "pontius.unrounded_policy_tt"
+relative_path = "src/pontius/unrounded_policy_tt.py"
+
+[[module]]
+module_name = "pontius.updates"
+relative_path = "src/pontius/updates.py"
+
+[[module]]
+module_name = "pontius.width_four_sizing_power"
+relative_path = "src/pontius/width_four_sizing_power.py"
+
+[[module]]
+module_name = "pontius.width_four_sizing_power_evaluation"
+relative_path = "src/pontius/width_four_sizing_power_evaluation.py"
+
+[[module]]
+module_name = "pontius.windows_process_memory"
+relative_path = "src/pontius/windows_process_memory.py"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.action_clock"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.coalition"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.cuda_dll_bootstrap"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.full_width_belief"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.full_width_reference_policy"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.holdem_cards"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.immutable_blueprint"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.kuhn"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.legal_decision_spine"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.preparation_bank"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.reference_hand_replay"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.river_incremental"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.__init__"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.action_abstraction_confirmation"
+target = "pontius.reduced_river_sizing_oracle"
+
+[[edge]]
+origin = "pontius.action_abstraction_confirmation"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.action_clock"
+target = "pontius.preparation_bank"
+
+[[edge]]
+origin = "pontius.action_clock"
+target = "pontius.street_deadline"
+
+[[edge]]
+origin = "pontius.affine_resident_heterogeneous_leaf_contraction"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.affine_resident_heterogeneous_leaf_contraction"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.affine_resident_heterogeneous_leaf_contraction"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.affine_resident_heterogeneous_leaf_contraction"
+target = "pontius.open_mode_showdown"
+
+[[edge]]
+origin = "pontius.affine_resident_heterogeneous_leaf_contraction"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.affine_resident_heterogeneous_leaf_contraction"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.affine_resident_heterogeneous_leaf_contraction"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.atomic_json_checkpoint"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.axis_cfr_checkpoint"
+target = "pontius.axis_public_cfr"
+
+[[edge]]
+origin = "pontius.axis_cfr_checkpoint"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.axis_cfr_checkpoint"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.axis_public_cfr"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.axis_public_cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.axis_public_cfr"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.axis_public_cfr"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.axis_public_cfr"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.axis_public_cfr"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.axis_public_cfr"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.batched_factor_tt_contraction"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.batched_factor_tt_contraction"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.batched_selector_stable_affine_response"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.batched_selector_stable_affine_response"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.batched_selector_stable_affine_response"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.batched_selector_stable_affine_response"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.batched_selector_stable_affine_response"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.batched_selector_stable_affine_response"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.batched_selector_stable_affine_response"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.behavioral_one_seat_master"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.behavioral_one_seat_master"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.behavioral_one_seat_master"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.behavioral_one_seat_master_v2"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.behavioral_one_seat_master_v2"
+target = "pontius.linear_program_certificate"
+
+[[edge]]
+origin = "pontius.behavioral_one_seat_master_v2"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.behavioral_open_axis"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.behavioral_open_axis"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.behavioral_open_axis"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.behavioral_open_axis"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.benefit_experiment"
+target = "pontius.depth_limited"
+
+[[edge]]
+origin = "pontius.benefit_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.benefit_experiment"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.benefit_experiment"
+target = "pontius.policy"
+
+[[edge]]
+origin = "pontius.benefit_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.benefit_matrix"
+target = "pontius.benefit_experiment"
+
+[[edge]]
+origin = "pontius.benefit_matrix"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.benefit_matrix"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.benefit_trajectory"
+target = "pontius.benefit_matrix"
+
+[[edge]]
+origin = "pontius.canonical_affine_resident_automaton_cache"
+target = "pontius.affine_resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.canonical_affine_resident_automaton_cache"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.canonical_affine_resident_automaton_cache"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.canonical_affine_resident_automaton_cache"
+target = "pontius.open_mode_showdown"
+
+[[edge]]
+origin = "pontius.canonical_affine_resident_automaton_cache"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.capacity_filling_action_abstraction"
+target = "pontius.collision_repair_action_abstraction"
+
+[[edge]]
+origin = "pontius.capacity_filling_action_abstraction"
+target = "pontius.legal_action_abstraction"
+
+[[edge]]
+origin = "pontius.capacity_filling_action_abstraction"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.certified_reduced_sizing_consumer_v2"
+target = "pontius.certified_reduced_sizing_consumer_v2_seal"
+
+[[edge]]
+origin = "pontius.certified_reduced_sizing_consumer_v2"
+target = "pontius.certified_reduced_sizing_highs"
+
+[[edge]]
+origin = "pontius.certified_reduced_sizing_consumer_v2"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.certified_reduced_sizing_consumer_v2"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.certified_reduced_sizing_consumer_v2"
+target = "pontius.reduced_river_sizing_lp"
+
+[[edge]]
+origin = "pontius.certified_reduced_sizing_highs"
+target = "pontius.certified_reduced_sizing_highs_seal"
+
+[[edge]]
+origin = "pontius.certified_reduced_sizing_highs"
+target = "pontius.linear_program_certificate"
+
+[[edge]]
+origin = "pontius.certified_reduced_sizing_highs"
+target = "pontius.reduced_river_sizing_lp"
+
+[[edge]]
+origin = "pontius.certified_sizing_validation_runner"
+target = "pontius.certified_reduced_sizing_highs"
+
+[[edge]]
+origin = "pontius.certified_sizing_validation_runner"
+target = "pontius.certified_reduced_sizing_highs_seal"
+
+[[edge]]
+origin = "pontius.certified_sizing_validation_runner"
+target = "pontius.certified_sizing_validation_seal"
+
+[[edge]]
+origin = "pontius.certified_sizing_validation_runner"
+target = "pontius.native_simplex_audit_corpus"
+
+[[edge]]
+origin = "pontius.certified_sizing_validation_runner"
+target = "pontius.native_simplex_audit_runner"
+
+[[edge]]
+origin = "pontius.certified_sizing_validation_runner"
+target = "pontius.native_simplex_audit_structures"
+
+[[edge]]
+origin = "pontius.certified_sizing_validation_runner"
+target = "pontius.reduced_river_sizing_lp"
+
+[[edge]]
+origin = "pontius.cfr"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.cfr"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.clean_fringe_tt"
+target = "pontius.batched_factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.clean_fringe_tt"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.clean_fringe_tt"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.clean_fringe_tt"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.clean_fringe_tt"
+target = "pontius.tensor_train_algebra"
+
+[[edge]]
+origin = "pontius.coalition"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.coalition"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.collision_repair_action_abstraction"
+target = "pontius.legal_action_abstraction"
+
+[[edge]]
+origin = "pontius.collision_repair_action_abstraction"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.collision_repair_v3_evaluation"
+target = "pontius.collision_repair_action_abstraction"
+
+[[edge]]
+origin = "pontius.collision_repair_v3_evaluation"
+target = "pontius.fresh_collision_repair_qualification"
+
+[[edge]]
+origin = "pontius.collision_repair_v3_evaluation"
+target = "pontius.fresh_collision_repair_structures"
+
+[[edge]]
+origin = "pontius.collision_repair_v3_evaluation"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.collision_repair_v3_evaluation"
+target = "pontius.reduced_river_sizing_oracle"
+
+[[edge]]
+origin = "pontius.collision_repair_v3_evaluation"
+target = "pontius.width_four_sizing_power"
+
+[[edge]]
+origin = "pontius.complete_factorized_affine_evidence"
+target = "pontius.exact_directional_face_oracle"
+
+[[edge]]
+origin = "pontius.complete_factorized_affine_evidence"
+target = "pontius.factorized_tie_aware_affine"
+
+[[edge]]
+origin = "pontius.complete_factorized_affine_evidence"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.composition_experiment"
+target = "pontius.continual"
+
+[[edge]]
+origin = "pontius.composition_experiment"
+target = "pontius.depth_limited"
+
+[[edge]]
+origin = "pontius.composition_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.composition_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.composition_experiment"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.composition_experiment"
+target = "pontius.policy"
+
+[[edge]]
+origin = "pontius.composition_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.composition_matrix"
+target = "pontius.benefit_matrix"
+
+[[edge]]
+origin = "pontius.composition_matrix"
+target = "pontius.composition_experiment"
+
+[[edge]]
+origin = "pontius.composition_matrix"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.composition_matrix"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.constrained_generation"
+target = "pontius.continual"
+
+[[edge]]
+origin = "pontius.constrained_generation"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.constrained_generation"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.constrained_generation"
+target = "pontius.kuhn"
+
+[[edge]]
+origin = "pontius.constrained_generation"
+target = "pontius.linear_program"
+
+[[edge]]
+origin = "pontius.constrained_generation"
+target = "pontius.maxmargin"
+
+[[edge]]
+origin = "pontius.constrained_generation"
+target = "pontius.safe_resolving"
+
+[[edge]]
+origin = "pontius.constrained_generation_experiment"
+target = "pontius.constrained_generation"
+
+[[edge]]
+origin = "pontius.constrained_generation_experiment"
+target = "pontius.continual"
+
+[[edge]]
+origin = "pontius.constrained_generation_experiment"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.constrained_generation_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.constrained_generation_matrix"
+target = "pontius.constrained_generation_experiment"
+
+[[edge]]
+origin = "pontius.constrained_generation_matrix"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.constrained_generation_matrix"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.continual"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.continual"
+target = "pontius.depth_limited"
+
+[[edge]]
+origin = "pontius.continual"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.continual"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.continual"
+target = "pontius.kuhn"
+
+[[edge]]
+origin = "pontius.continual"
+target = "pontius.policy"
+
+[[edge]]
+origin = "pontius.continuation_public_tree_tensor"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.continuation_public_tree_tensor"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.continuation_public_tree_tensor"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.multi_size_affine_cross_payoff"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.pre_bet_initial_row_cache"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.cross_payoff_adjoint_result"
+target = "pontius.resident_record_to_hand_fold_v2"
+
+[[edge]]
+origin = "pontius.cross_payoff_leaf_adjoint"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.cross_payoff_leaf_adjoint"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.cross_payoff_leaf_adjoint"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.cross_payoff_leaf_adjoint"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.cross_payoff_leaf_adjoint"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.cupy_sparse_incidence"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.deadline_owned_result"
+target = "pontius.campaign_deadline"
+
+[[edge]]
+origin = "pontius.deadline_owned_result"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.deadline_owned_result"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.delta_certificate_contract"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.delta_certificate_contract"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.dense_root_cross_payoff_control"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.dense_root_cross_payoff_control"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.dependency_tape"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.dependency_tape"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.river_incremental"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.river_range_reuse"
+
+[[edge]]
+origin = "pontius.dependency_tape_experiment"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.depth_limited"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.depth_limited"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+target = "pontius.resident_record_to_hand_fold"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+target = "pontius.resident_record_to_hand_fold"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+target = "pontius.resident_record_to_hand_fold_v2"
+
+[[edge]]
+origin = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.resident_record_to_hand_fold"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.sparse_open_mode_cfr"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.resident_record_to_hand_fold"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.resident_record_to_hand_fold_v2"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.sparse_open_mode_cfr"
+
+[[edge]]
+origin = "pontius.device_fold_resident_leaf_adjoint_cfr_v2"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.device_fold_resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.resident_record_to_hand_fold"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.convex_retreat_tolerances"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.resident_record_to_hand_fold"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.resident_record_to_hand_fold_v2"
+
+[[edge]]
+origin = "pontius.device_fold_selector_stable_affine_response_v2"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.evaluation"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.exact_collision_oracle"
+target = "pontius.holdem_cards"
+
+[[edge]]
+origin = "pontius.exact_directional_face_oracle"
+target = "pontius.exact_selector_fan"
+
+[[edge]]
+origin = "pontius.exact_directional_face_oracle"
+target = "pontius.exact_selector_window_oracle"
+
+[[edge]]
+origin = "pontius.exact_directional_face_oracle"
+target = "pontius.exact_sequence_form_coefficient_oracle"
+
+[[edge]]
+origin = "pontius.exact_directional_face_oracle"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.exact_selector_fan"
+target = "pontius.exact_selector_window_oracle"
+
+[[edge]]
+origin = "pontius.exact_selector_fan"
+target = "pontius.exact_sequence_form_coefficient_oracle"
+
+[[edge]]
+origin = "pontius.exact_selector_fan"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.exact_selector_window_oracle"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.exact_sequence_form_coefficient_oracle"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.exact_tie_aware_affine_envelope"
+target = "pontius.exact_selector_fan"
+
+[[edge]]
+origin = "pontius.exact_tie_aware_affine_envelope"
+target = "pontius.exact_selector_window_oracle"
+
+[[edge]]
+origin = "pontius.exact_tie_aware_affine_envelope"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.experiment"
+target = "pontius.kuhn"
+
+[[edge]]
+origin = "pontius.experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction_audit"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.factor_tt_contraction_audit"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.factorized_belief"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.factorized_belief_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.factorized_belief_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.factorized_belief_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.factorized_tie_aware_affine"
+target = "pontius.exact_directional_face_oracle"
+
+[[edge]]
+origin = "pontius.factorized_tie_aware_affine"
+target = "pontius.exact_selector_fan"
+
+[[edge]]
+origin = "pontius.factorized_tie_aware_affine"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.factorized_tie_aware_affine"
+target = "pontius.selector_window"
+
+[[edge]]
+origin = "pontius.factorized_tie_aware_affine"
+target = "pontius.selector_window_v2"
+
+[[edge]]
+origin = "pontius.fixed_envelope_verifier"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.fixed_envelope_verifier"
+target = "pontius.h32_acceptance_semantics_replay"
+
+[[edge]]
+origin = "pontius.fixed_envelope_verifier"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.fixed_envelope_verifier"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.fixed_envelope_verifier"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.fixed_envelope_verifier"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.fixed_envelope_verifier"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.certified_reduced_sizing_consumer_v2_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.fresh_action_width_greedy_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.fresh_action_width_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.fresh_action_width_structures_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.fresh_action_width_teacher"
+
+[[edge]]
+origin = "pontius.fresh_action_width_greedy"
+target = "pontius.fresh_action_width_teacher_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay"
+target = "pontius.fresh_action_width_structures_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.certified_reduced_sizing_consumer_v2_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.certified_reduced_sizing_highs"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_greedy"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_nonreplay"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_nonreplay_greedy_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_nonreplay_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_nonreplay_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_nonreplay_teacher"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_nonreplay_teacher_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy"
+target = "pontius.fresh_action_width_teacher"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.fresh_action_width_greedy"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.fresh_action_width_nonreplay_greedy"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.fresh_action_width_nonreplay_greedy_result_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.fresh_action_width_nonreplay_greedy_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.fresh_action_width_nonreplay_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.fresh_action_width_nonreplay_teacher_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_greedy_result_seal"
+target = "pontius.fresh_action_width_nonreplay_greedy_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.certified_reduced_sizing_consumer_v2_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.certified_reduced_sizing_highs"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.fresh_action_width_nonreplay"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.fresh_action_width_nonreplay_qualification_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.fresh_action_width_nonreplay_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.linear_program_certificate"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification"
+target = "pontius.reduced_river_sizing_lp"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification_result"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification_result"
+target = "pontius.fresh_action_width_nonreplay"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification_result"
+target = "pontius.fresh_action_width_nonreplay_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification_result"
+target = "pontius.fresh_action_width_nonreplay_qualification_result_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification_result"
+target = "pontius.fresh_action_width_nonreplay_qualification_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification_result"
+target = "pontius.fresh_action_width_nonreplay_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_qualification_result"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.certified_reduced_sizing_consumer_v2_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.certified_reduced_sizing_highs"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_nonreplay"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_nonreplay_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_nonreplay_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_nonreplay_qualification_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_nonreplay_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_nonreplay_teacher_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher"
+target = "pontius.fresh_action_width_teacher"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher_result"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher_result"
+target = "pontius.fresh_action_width_nonreplay_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher_result"
+target = "pontius.fresh_action_width_nonreplay_teacher"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher_result"
+target = "pontius.fresh_action_width_nonreplay_teacher_result_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher_result"
+target = "pontius.fresh_action_width_nonreplay_teacher_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_nonreplay_teacher_result"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_qualification"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_qualification"
+target = "pontius.fresh_action_width_qualification_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_qualification"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_qualification"
+target = "pontius.fresh_action_width_structures_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_qualification_result"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_qualification_result"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_qualification_result"
+target = "pontius.fresh_action_width_qualification_result_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_qualification_result"
+target = "pontius.fresh_action_width_qualification_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_structures"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_structures"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.fresh_action_width_structures"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher"
+target = "pontius.fresh_action_width_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher"
+target = "pontius.fresh_action_width_teacher_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher_result"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher_result"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher_result"
+target = "pontius.fresh_action_width_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher_result"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher_result"
+target = "pontius.fresh_action_width_teacher"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher_result"
+target = "pontius.fresh_action_width_teacher_result_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_teacher_result"
+target = "pontius.fresh_action_width_teacher_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.certified_reduced_sizing_consumer_v2_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.certified_reduced_sizing_highs"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_greedy"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_nonreplay_greedy_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_nonreplay_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_teacher"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_transfer_confirmation_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_transfer_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_transfer_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_transfer_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation"
+target = "pontius.fresh_action_width_transfer_structures_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation_result"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation_result"
+target = "pontius.fresh_action_width_transfer_confirmation"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation_result"
+target = "pontius.fresh_action_width_transfer_confirmation_result_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation_result"
+target = "pontius.fresh_action_width_transfer_confirmation_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_confirmation_result"
+target = "pontius.fresh_action_width_transfer_qualification_result"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification"
+target = "pontius.fresh_action_width_nonreplay_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification"
+target = "pontius.fresh_action_width_transfer_qualification_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification"
+target = "pontius.fresh_action_width_transfer_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification"
+target = "pontius.fresh_action_width_transfer_structures_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.certified_reduced_sizing_consumer_v2"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.fresh_action_width_nonreplay_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.fresh_action_width_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.fresh_action_width_transfer_qualification"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.fresh_action_width_transfer_qualification_result_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.fresh_action_width_transfer_qualification_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.fresh_action_width_transfer_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_qualification_result"
+target = "pontius.fresh_action_width_transfer_structures_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_structures"
+target = "pontius.fresh_action_width_nonreplay"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_structures"
+target = "pontius.fresh_action_width_nonreplay_seal"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_structures"
+target = "pontius.fresh_action_width_structures"
+
+[[edge]]
+origin = "pontius.fresh_action_width_transfer_structures"
+target = "pontius.fresh_action_width_structures_seal"
+
+[[edge]]
+origin = "pontius.fresh_capacity_filling_qualification"
+target = "pontius.fresh_capacity_filling_structures"
+
+[[edge]]
+origin = "pontius.fresh_capacity_filling_qualification"
+target = "pontius.reduced_river_sizing_oracle"
+
+[[edge]]
+origin = "pontius.fresh_capacity_filling_qualification"
+target = "pontius.sizing_power_diagnostic"
+
+[[edge]]
+origin = "pontius.fresh_capacity_filling_qualification"
+target = "pontius.width_four_sizing_power"
+
+[[edge]]
+origin = "pontius.fresh_capacity_filling_structures"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.fresh_collision_repair_qualification"
+target = "pontius.fresh_collision_repair_structures"
+
+[[edge]]
+origin = "pontius.fresh_collision_repair_qualification"
+target = "pontius.reduced_river_sizing_oracle"
+
+[[edge]]
+origin = "pontius.fresh_collision_repair_qualification"
+target = "pontius.sizing_power_diagnostic"
+
+[[edge]]
+origin = "pontius.fresh_collision_repair_qualification"
+target = "pontius.width_four_sizing_power"
+
+[[edge]]
+origin = "pontius.fresh_collision_repair_structures"
+target = "pontius.action_abstraction_confirmation"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.fixed_envelope_verifier"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.h32_acceptance_semantics_replay"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.h32_current_interpolation_audit"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.resident_leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.fresh_h32_strategy_transfer_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.full_width_belief"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.full_width_belief"
+target = "pontius.full_width_reference_policy"
+
+[[edge]]
+origin = "pontius.full_width_belief"
+target = "pontius.holdem_cards"
+
+[[edge]]
+origin = "pontius.full_width_belief"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.full_width_reference_policy"
+target = "pontius.holdem_cards"
+
+[[edge]]
+origin = "pontius.full_width_reference_policy"
+target = "pontius.immutable_blueprint"
+
+[[edge]]
+origin = "pontius.full_width_reference_policy"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.full_width_belief"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.full_width_factor_tt_capacity"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.holdem_cards"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight_v2"
+target = "pontius.full_width_river_capacity_preflight"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight_v2"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.full_width_river_capacity_preflight_v2"
+target = "pontius.windows_process_memory"
+
+[[edge]]
+origin = "pontius.gpu_occupied_card_quotient"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.gpu_occupied_card_quotient"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.gpu_occupied_card_quotient"
+target = "pontius.occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.gpu_occupied_card_quotient"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling"
+target = "pontius.gpu_occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_result"
+target = "pontius.gpu_quotient_staged_scaling"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_result"
+target = "pontius.gpu_quotient_staged_scaling_runner"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_runner"
+target = "pontius.gpu_quotient_staged_scaling"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_runner"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_v2_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_v2_result"
+target = "pontius.gpu_quotient_staged_scaling"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_v2_result"
+target = "pontius.gpu_quotient_staged_scaling_v2_runner"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_v2_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_v2_runner"
+target = "pontius.gpu_quotient_staged_scaling"
+
+[[edge]]
+origin = "pontius.gpu_quotient_staged_scaling_v2_runner"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.gpu_quotient_validation_seam"
+target = "pontius.gpu_occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.gpu_quotient_validation_seam"
+target = "pontius.gpu_quotient_staged_scaling"
+
+[[edge]]
+origin = "pontius.gpu_quotient_validation_seam"
+target = "pontius.literal_45_quotient_liveness"
+
+[[edge]]
+origin = "pontius.gpu_quotient_validation_seam"
+target = "pontius.occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_posterior_manifest"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_posterior_manifest"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_posterior_manifest"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_posterior_manifest"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_posterior_manifest"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_posterior_manifest"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_posterior_manifest"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_posterior_manifest"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_action_conditioned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_retained_affine_selector_cascade_replay"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_selector_stable_affine_certificate_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_action_conditioned_widened_selector_trial"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.canonical_affine_resident_automaton_cache"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.fixed_envelope_verifier"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.h32_acceptance_semantics_replay"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.multi_size_policy_bridge"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.river_multiway_multi_size"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.h32_action_width_quality_audit_v2"
+target = "pontius.h32_action_width_quality_audit"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.affine_resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.multi_size_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.river_multiway_multi_size"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.h32_affine_resident_cache_preflight"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.h32_policy_delta_verifier_audit"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_atomic_response_preflight"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.h32_policy_delta_verifier_audit"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.h32_shared_response_residency_replay"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_atomic_street_scheduler_audit"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_candidate_availability_replay"
+target = "pontius.h32_acceptance_semantics_replay"
+
+[[edge]]
+origin = "pontius.h32_candidate_availability_replay"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_candidate_availability_replay_v2"
+target = "pontius.h32_candidate_availability_replay"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.canonical_affine_resident_automaton_cache"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.multi_size_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.h32_canonical_affine_cache_replay"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.h32_continuation_root_strategy_trial"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.h32_resident_record_to_hand_fold_differential"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_continuation_depth_ledger"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.h32_heldout_continuation_depth_value_trial"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_continuation_direction_capacity"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.h32_action_conditioned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.h32_action_conditioned_widened_selector_trial"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.h32_continuation_root_preflight"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.h32_resident_record_to_hand_fold_differential"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_ledger"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.h32_action_conditioned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_preflight"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.h32_action_conditioned_widened_selector_trial"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.h32_selector_stable_affine_certificate_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_continuation_root_strategy_trial"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.h32_action_conditioned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.h32_heldout_continuation_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_convex_replication_posterior_manifest"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.h32_continuation_direction_capacity"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.h32_heldout_continuation_depth_value_trial"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_cross_payoff_adjoint_feasibility"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_current_decision_combined_ledger_replay"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_current_decision_combined_ledger_replay"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.h32_warm_candidate_stream_audit"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_current_interpolation_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.h32_decision_aligned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.h32_fresh_convex_retreat_replication"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_continuation_setup"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_live_shadow_trial"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_live_shadow_trial"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_live_shadow_trial"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_live_shadow_trial"
+target = "pontius.h32_decision_aligned_continuation_setup"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_live_shadow_trial"
+target = "pontius.h32_fresh_convex_retreat_replication"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_live_shadow_trial"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.h32_action_conditioned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_decision_aligned_posterior_manifest"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_correction_replay"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_correction_replay"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.h32_fresh_public_block_radius_audit"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_deep_horizon_opportunity_audit"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.h32_action_width_quality_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.h32_second_board_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_board_panel_cache_preflight"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.h32_fresh_public_block_radius_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_causal_direction_screen"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.behavioral_open_axis"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.exact_oracle_assessment"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.h32_one_round_convex_master"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.h32_one_seat_open_axis_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.h32_resident_record_to_hand_fold_differential"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.h32_fresh_convex_retreat_replication"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.h32_acceptance_semantics_replay"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.h32_action_width_quality_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.h32_fresh_panel_source_blueprint_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.h32_fresh_panel_target_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.h32_fresh_panel_target_transfer_audit_v2"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.multi_size_policy_bridge"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit_v2"
+target = "pontius.h32_fresh_panel_action_width_warm_step_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_action_width_warm_step_audit_v2"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_source_blueprint_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.h32_acceptance_semantics_replay"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.h32_current_interpolation_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit_v2"
+target = "pontius.h32_fresh_panel_target_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit_v2"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_panel_target_transfer_audit_v2"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_radius_audit"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.h32_atomic_street_scheduler_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_public_block_value_audit"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.h32_fresh_public_block_radius_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.evidence_protocol"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_fresh_public_block_radius_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_selector_stable_affine_certificate_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_audit"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+target = "pontius.h32_fresh_selector_stable_affine_street_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.h32_atomic_street_scheduler_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit_v2"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit_v2"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_fresh_union_value_audit_v2"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.h32_continuation_depth_ledger"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.h32_continuation_root_strategy_trial"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.h32_selector_stable_affine_certificate_audit"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_depth_value_trial"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_posterior_manifest"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_posterior_manifest"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_posterior_manifest"
+target = "pontius.h32_action_conditioned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_posterior_manifest"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_posterior_manifest"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_posterior_manifest"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_posterior_manifest"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_heldout_continuation_posterior_manifest"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_latin_f_convex_retreat_confirmation"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_latin_f_convex_retreat_confirmation"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_latin_f_convex_retreat_confirmation"
+target = "pontius.h32_fresh_convex_retreat_replication"
+
+[[edge]]
+origin = "pontius.h32_latin_f_convex_retreat_confirmation"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.axis_public_cfr"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.multi_size_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.river_multiway_multi_size"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_multi_size_resident_cache_preflight"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.behavioral_open_axis"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.h32_one_seat_open_axis_preflight"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.h32_resident_record_to_hand_fold_differential"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.h32_one_round_convex_master"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.behavioral_open_axis"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.h32_heldout_continuation_depth_value_trial"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.h32_resident_record_to_hand_fold_differential"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.h32_one_seat_open_axis_preflight"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.behavioral_open_axis"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.exact_oracle_assessment"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.h32_one_round_convex_master"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.h32_one_seat_open_axis_preflight"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.h32_resident_record_to_hand_fold_differential"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial_v2"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial_v2"
+target = "pontius.h32_one_seat_retreat_quality_trial"
+
+[[edge]]
+origin = "pontius.h32_one_seat_retreat_quality_trial_v2"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.fixed_envelope_verifier"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.h32_acceptance_semantics_replay"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.h32_current_interpolation_audit"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.h32_warm_candidate_stream_audit"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_policy_delta_verifier_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.h32_decision_aligned_live_shadow_trial"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.h32_fresh_convex_retreat_replication"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.h32_one_round_convex_master"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.h32_post_fold_current_decision_setup"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_post_fold_closure_value_confirmation"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.h32_decision_aligned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.h32_fresh_convex_retreat_replication"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.h32_post_fold_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_post_fold_current_decision_setup"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_post_fold_failure_closure_diagnostic"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_post_fold_failure_closure_diagnostic"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_post_fold_failure_closure_diagnostic"
+target = "pontius.h32_decision_aligned_live_shadow_trial"
+
+[[edge]]
+origin = "pontius.h32_post_fold_failure_closure_diagnostic"
+target = "pontius.h32_post_fold_current_decision_setup"
+
+[[edge]]
+origin = "pontius.h32_post_fold_failure_closure_diagnostic"
+target = "pontius.h32_retained_convex_closure_census"
+
+[[edge]]
+origin = "pontius.h32_post_fold_failure_closure_diagnostic"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.h32_action_conditioned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.h32_decision_aligned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_post_fold_posterior_manifest"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.atomic_json_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.canonical_affine_resident_automaton_cache"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.h32_decision_aligned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.h32_resident_record_to_hand_fold_differential"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.multi_size_affine_cross_payoff"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.multi_size_continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.multi_size_policy_bridge"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.public_node_behavioral_axis"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.public_node_open_axis"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.river_multiway_multi_size"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_action_width_capacity"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_cache_seed"
+target = "pontius.atomic_json_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_cache_seed"
+target = "pontius.campaign_deadline"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_cache_seed"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_cache_seed"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_cache_seed"
+target = "pontius.h32_pre_bet_action_width_capacity"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_cache_seed"
+target = "pontius.h32_pre_bet_initial_row_gpu"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_cache_seed"
+target = "pontius.h32_pre_bet_work_reduction_analysis"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_cache_seed"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_gpu"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_gpu"
+target = "pontius.h32_pre_bet_action_width_capacity"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_gpu"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_gpu"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_gpu"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_gpu"
+target = "pontius.pre_bet_initial_row_cache"
+
+[[edge]]
+origin = "pontius.h32_pre_bet_initial_row_gpu"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_audit_v2"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.h32_resident_cfr_sustained_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_restart_semantics_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_resident_cfr_sustained_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.device_fold_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.h32_tier_b_opponent_batch_differential"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.h32_tier_b_opponent_batch_differential_v2"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.resident_record_to_hand_fold"
+
+[[edge]]
+origin = "pontius.h32_resident_record_to_hand_fold_differential"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_profile"
+target = "pontius.h32_tier_b_opponent_batch_differential"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_profile"
+target = "pontius.h32_tier_b_opponent_batch_differential_v2"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_profile"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_profile_v2"
+target = "pontius.h32_resident_sparse_ncu_profile"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_profile_v2"
+target = "pontius.h32_tier_b_opponent_batch_differential"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_profile_v2"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_profile_v3"
+target = "pontius.h32_resident_sparse_ncu_profile"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_profile_v3"
+target = "pontius.h32_resident_sparse_ncu_profile_v2"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_workload"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_workload"
+target = "pontius.h32_resident_sparse_ncu_profile"
+
+[[edge]]
+origin = "pontius.h32_resident_sparse_ncu_workload"
+target = "pontius.h32_tier_b_opponent_batch_differential"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.evidence_protocol"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.h32_fresh_selector_stable_affine_street_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.h32_fresh_selector_stable_affine_street_seat5_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_resident_step_bottleneck_profile_v2"
+target = "pontius.h32_resident_step_bottleneck_profile"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.fixed_envelope_verifier"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.h32_acceptance_semantics_replay"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.h32_policy_delta_verifier_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.resident_leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_resident_verifier_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.h32_fresh_panel_target_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.h32_resident_cfr_audit"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.resident_leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_response_latency_bridge_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_direct_replay"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_direct_replay"
+target = "pontius.h32_retained_affine_selector_cascade_replay"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_direct_replay"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.evidence_protocol"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_fresh_causal_direction_screen"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_selector_stable_affine_certificate_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay_v2"
+target = "pontius.h32_retained_affine_selector_cascade_replay"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay_v3"
+target = "pontius.h32_retained_affine_selector_cascade_replay"
+
+[[edge]]
+origin = "pontius.h32_retained_affine_selector_cascade_replay_v3"
+target = "pontius.h32_retained_affine_selector_cascade_replay_v2"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.behavioral_open_axis"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.device_fold_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_action_conditioned_posterior_manifest"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_continuation_root_ledger"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_decision_aligned_continuation_setup"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_fresh_convex_retreat_replication"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_one_round_convex_master"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_one_seat_open_axis_preflight"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_resident_record_to_hand_fold_differential"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.payoff_semantics"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census_v2"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census_v2"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census_v2"
+target = "pontius.h32_retained_convex_closure_census"
+
+[[edge]]
+origin = "pontius.h32_retained_convex_closure_census_v2"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.h32_action_width_quality_audit"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.h32_second_board_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.multi_size_policy_bridge"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_second_board_action_width_quality_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.h32_action_width_quality_audit"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_second_board_resident_cache_preflight"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.fresh_h32_strategy_transfer_audit"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.h32_atomic_response_preflight"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.h32_fresh_board_panel_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.h32_fresh_causal_direction_screen"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.h32_fresh_public_block_value_audit"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.h32_fresh_regret_vertex_opportunity_audit"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit_v2"
+target = "pontius.evidence_protocol"
+
+[[edge]]
+origin = "pontius.h32_selector_stable_affine_certificate_audit_v2"
+target = "pontius.h32_selector_stable_affine_certificate_audit"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.h32_policy_delta_verifier_audit"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.h32_shared_response_residency_replay"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_shared_response_allocator_lifecycle_replay"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.h32_policy_delta_verifier_audit"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_shared_response_residency_replay"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.batched_selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.h32_fresh_union_value_audit"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.h32_retained_affine_selector_cascade_replay"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.selector_stable_affine_response"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential"
+target = "pontius.shared_resident_response_context"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential_v2"
+target = "pontius.h32_tier_b_opponent_batch_differential"
+
+[[edge]]
+origin = "pontius.h32_tier_b_opponent_batch_differential_v2"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_warm_candidate_stream_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.sparse_open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h32_warm_search_acceptance_audit"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.continuation_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.cross_payoff_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.h4_sequence_form_open_axis_differential"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.h32_warm_search_acceptance_audit"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.public_tree_tensor_cfr"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.h4_shifted_belief_dense_crosscheck"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.heterogeneous_leaf_contraction"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.heterogeneous_leaf_contraction"
+target = "pontius.open_mode_showdown"
+
+[[edge]]
+origin = "pontius.heterogeneous_leaf_contraction"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.heterogeneous_leaf_contraction"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.holdem_cards"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.holdem_cards"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.immutable_blueprint"
+target = "pontius.holdem_cards"
+
+[[edge]]
+origin = "pontius.immutable_blueprint"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.fixed_envelope_verifier"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.incremental_leaf_adjoint_response"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.incremental_policy_tt"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.incremental_policy_tt"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.incremental_policy_tt"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.incremental_policy_tt"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.incremental_policy_tt"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.incremental_policy_tt"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.incremental_policy_tt"
+target = "pontius.tensor_train_algebra"
+
+[[edge]]
+origin = "pontius.kuhn"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit_v2"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit_v2"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit_v2"
+target = "pontius.leaf_adjoint_batch_width_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit_v2"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit_v2"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_batch_width_audit_v2"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.axis_public_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.sparse_open_mode_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.open_mode_cfr_bridge"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.public_tree_tensor_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_cfr_audit"
+target = "pontius.sparse_open_mode_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_extension_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_extension_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_extension_audit"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_extension_audit"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_extension_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_extension_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_extension_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.axis_cfr_checkpoint"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.leaf_adjoint_checkpoint_ladder_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_checkpoint_ladder_audit_v2"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.axis_public_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.leaf_adjoint_evaluation_audit"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.leaf_experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.leaf_experiment"
+target = "pontius.depth_limited"
+
+[[edge]]
+origin = "pontius.leaf_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.leaf_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.leaf_experiment"
+target = "pontius.kuhn"
+
+[[edge]]
+origin = "pontius.leaf_experiment"
+target = "pontius.policy"
+
+[[edge]]
+origin = "pontius.leaf_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.leaf_matrix"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.leaf_matrix"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.legal_action_abstraction"
+target = "pontius.immutable_blueprint"
+
+[[edge]]
+origin = "pontius.legal_action_abstraction"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_decision_spine"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_decision_spine"
+target = "pontius.street_deadline"
+
+[[edge]]
+origin = "pontius.legal_decision_spine_v2"
+target = "pontius.action_clock"
+
+[[edge]]
+origin = "pontius.legal_decision_spine_v2"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_decision_spine_v2"
+target = "pontius.preparation_bank"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation"
+target = "pontius.complete_factorized_affine_evidence"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation"
+target = "pontius.factorized_tie_aware_affine"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation"
+target = "pontius.legal_h4_factorized_affine_confirmation_directions"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation"
+target = "pontius.legal_h4_factorized_affine_confirmation_population"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation"
+target = "pontius.legal_h4_factorized_affine_confirmation_population_seal"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_directions"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_directions"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_directions"
+target = "pontius.exact_sequence_form_coefficient_oracle"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_directions"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_directions"
+target = "pontius.legal_h4_factorized_affine_confirmation_population"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_directions"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_directions"
+target = "pontius.one_seat_row_growth_audit"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_population"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_population"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_population"
+target = "pontius.legal_h4_selector_fixture"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_population"
+target = "pontius.legal_river_continuation"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_population"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_h4_factorized_affine_confirmation_population"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.legal_h4_selector_directions"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.legal_h4_selector_directions"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.legal_h4_selector_directions"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_h4_selector_directions"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.legal_h4_selector_fixture"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.legal_h4_selector_fixture"
+target = "pontius.legal_river_continuation"
+
+[[edge]]
+origin = "pontius.legal_h4_selector_fixture"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_h4_selector_fixture"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.exact_sequence_form_coefficient_oracle"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.legal_river_continuation"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.responder_raise_semantics_keystone_result"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_differential"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_coefficient_result"
+target = "pontius.legal_responder_raise_h4_coefficient_result_seal"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.exact_directional_face_oracle"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.exact_directional_face_oracle_seal"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.legal_h4_selector_directions"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.legal_h4_selector_fixture"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.legal_responder_raise_h4_row_growth_result"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_directional_face_result"
+target = "pontius.legal_responder_raise_h4_directional_face_result_seal"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.exact_directional_face_oracle"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.factorized_tie_aware_affine"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.factorized_tie_aware_affine_seal"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.legal_h4_selector_directions"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.legal_h4_selector_fixture"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.legal_responder_raise_h4_directional_face_result"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.legal_responder_raise_h4_row_growth_result"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_factorized_affine"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.exact_sequence_form_coefficient_oracle"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.legal_responder_raise_h4_coefficient_result"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.legal_river_continuation"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.one_seat_row_growth_audit"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_row_growth_result"
+target = "pontius.legal_responder_raise_h4_row_growth_result_seal"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_fan_result"
+target = "pontius.legal_responder_raise_h4_selector_fan_result_seal"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.exact_selector_fan"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.exact_selector_window_oracle"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.legal_h4_selector_directions"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.legal_h4_selector_fixture"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.legal_responder_raise_h4_row_growth_result"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.selector_fan_controls"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_selector_window"
+target = "pontius.selector_window"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.exact_selector_fan"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.exact_selector_window_oracle"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.exact_tie_aware_affine_envelope"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.legal_h4_selector_directions"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.legal_h4_selector_fixture"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.legal_responder_raise_h4_row_growth_result"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.legal_responder_raise_h4_selector_fan_result"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.selector_window"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine"
+target = "pontius.tie_aware_affine_adapter"
+
+[[edge]]
+origin = "pontius.legal_responder_raise_h4_tie_aware_affine_result"
+target = "pontius.legal_responder_raise_h4_tie_aware_affine_result_seal"
+
+[[edge]]
+origin = "pontius.legal_river_continuation"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.legal_river_continuation"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_river_continuation"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_river_continuation"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_inspector_diagnostic"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_inspector_diagnostic_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_inspector_diagnostic_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_inspector_diagnostic_runner"
+target = "pontius.legal_river_exact_cubin_inspector_diagnostic"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_inspector_selection"
+target = "pontius.legal_river_exact_cubin_inspector_diagnostic_result"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_inspector_selection"
+target = "pontius.legal_river_exact_cubin_inspector_selection_seal"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic"
+target = "pontius.legal_river_exact_cubin_inspector_diagnostic_result"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_runner"
+target = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.full_width_belief"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.full_width_reference_policy"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.gpu_occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.holdem_cards"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_bridge"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration"
+target = "pontius.legal_river_quotient_base_provenance"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_result"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_result"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_result"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v5_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v5_result"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v5_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v5_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v6_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v6_result"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v6_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v6_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_result"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_runner"
+target = "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_consumer_capacity"
+target = "pontius.legal_river_quotient_bridge"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_consumer_capacity"
+target = "pontius.occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_tiles"
+target = "pontius.gpu_occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_tiles"
+target = "pontius.legal_river_quotient_cuda_consumer"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+target = "pontius.gpu_occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+target = "pontius.legal_river_quotient_cuda_compensated_tiles"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+target = "pontius.legal_river_quotient_cuda_consumer"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_runner"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_result"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_adapter"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_adapter"
+target = "pontius.legal_river_quotient_cuda_consumer"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_result"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_adapter"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_adapter"
+target = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_adapter"
+target = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_adapter"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_adapter"
+target = "pontius.legal_river_quotient_cuda_consumer"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result"
+target = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner"
+target = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_adapter"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_consumer"
+target = "pontius.gpu_occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_consumer"
+target = "pontius.legal_river_quotient_bridge"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_consumer"
+target = "pontius.legal_river_quotient_consumer_capacity"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device"
+target = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device"
+target = "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device"
+target = "pontius.legal_river_quotient_cuda_compensated_tiles"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device"
+target = "pontius.legal_river_quotient_cuda_shared_direct_oracle"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_runner"
+target = "pontius.legal_river_quotient_cuda_shared_direct_device"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_v2_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_v2_result"
+target = "pontius.legal_river_quotient_cuda_shared_direct_device_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_v2_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_v2_runner"
+target = "pontius.legal_river_quotient_cuda_shared_direct_device"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_v3_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_v3_result"
+target = "pontius.legal_river_quotient_cuda_shared_direct_device_v2_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_v3_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_device_v3_runner"
+target = "pontius.legal_river_quotient_cuda_shared_direct_sample_plan"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_oracle"
+target = "pontius.legal_river_quotient_cuda_compensated_tiles"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_oracle"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_sample_plan"
+target = "pontius.legal_river_quotient_cuda_compensated_tiles"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_sample_plan"
+target = "pontius.legal_river_quotient_cuda_compensated_work_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_cuda_shared_direct_sample_plan"
+target = "pontius.legal_river_quotient_cuda_shared_direct_device"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_outcome"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_outcome"
+target = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_result"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_outcome"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_result"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_runner"
+target = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_runner"
+target = "pontius.legal_river_quotient_fixed_width_actual45_fit_projection_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight"
+target = "pontius.legal_river_quotient_cuda_compensated_tiles"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight"
+target = "pontius.legal_river_quotient_exact_integer_operator"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight"
+target = "pontius.legal_river_quotient_fixed_width_work_comparison"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_outcome"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_result"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_outcome"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_outcome"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_result"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
+target = "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_global_separation_topologies"
+target = "pontius.legal_river_quotient_base_provenance"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_global_separation_topologies"
+target = "pontius.legal_river_quotient_selective_certified_separation"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_selective_certified_separation_runner"
+target = "pontius.legal_river_quotient_selective_certified_separation"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_selective_certified_separation_runner"
+target = "pontius.legal_river_quotient_selective_certified_separation_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_shared_direct_artifact_capacity"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_shared_direct_artifact_capacity"
+target = "pontius.legal_river_quotient_cuda_shared_direct_device_v3_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_shared_direct_artifact_capacity_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_shared_direct_artifact_capacity_result"
+target = "pontius.legal_river_quotient_cuda_shared_direct_device_v3_result"
+
+[[edge]]
+origin = "pontius.legal_river_quotient_shared_direct_artifact_capacity_runner"
+target = "pontius.legal_river_quotient_shared_direct_artifact_capacity"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_liveness"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target"
+target = "pontius.gpu_occupied_card_quotient"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target"
+target = "pontius.gpu_quotient_staged_scaling"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target"
+target = "pontius.literal_45_quotient_liveness"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target"
+target = "pontius.literal_45_quotient_target_result"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target"
+target = "pontius.windows_process_memory"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target_result"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target_runner"
+target = "pontius.durable_evidence_journal"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target_runner"
+target = "pontius.literal_45_quotient_target"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target_runner"
+target = "pontius.literal_45_quotient_target_result"
+
+[[edge]]
+origin = "pontius.literal_45_quotient_target_runner"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.local_response_bridge"
+target = "pontius.delta_certificate_contract"
+
+[[edge]]
+origin = "pontius.local_response_bridge"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.local_response_bridge"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.local_response_bridge"
+target = "pontius.fixed_envelope_verifier"
+
+[[edge]]
+origin = "pontius.local_response_bridge"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.local_response_bridge"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.matrix_game"
+target = "pontius.linear_program"
+
+[[edge]]
+origin = "pontius.maxmargin"
+target = "pontius.continual"
+
+[[edge]]
+origin = "pontius.maxmargin"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.maxmargin"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.maxmargin"
+target = "pontius.kuhn"
+
+[[edge]]
+origin = "pontius.maxmargin"
+target = "pontius.linear_program"
+
+[[edge]]
+origin = "pontius.maxmargin"
+target = "pontius.matrix_game"
+
+[[edge]]
+origin = "pontius.maxmargin"
+target = "pontius.safe_resolving"
+
+[[edge]]
+origin = "pontius.multi_size_affine_cross_payoff"
+target = "pontius.affine_resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_affine_cross_payoff"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_affine_cross_payoff"
+target = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_affine_cross_payoff"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_affine_cross_payoff"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_affine_cross_payoff"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_affine_cross_payoff"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.affine_resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.multi_size_resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.sparse_open_mode_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_cfr"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.affine_resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.multi_size_policy_bridge"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.multi_size_affine_resident_leaf_adjoint_evaluation"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.multi_size_continuation_public_tree_tensor"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multi_size_continuation_public_tree_tensor"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_continuation_public_tree_tensor"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_continuation_public_tree_tensor"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.multi_size_continuation_public_tree_tensor"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.multi_size_continuation_public_tree_tensor"
+target = "pontius.river_multiway_multi_size"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.sparse_open_mode_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.open_mode_cfr_bridge"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.river_multiway_multi_size"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.multi_size_leaf_adjoint_audit"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.multi_size_policy_bridge"
+target = "pontius.river_multiway_multi_size"
+
+[[edge]]
+origin = "pontius.multi_size_public_tree_tensor"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multi_size_public_tree_tensor"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_public_tree_tensor"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.multi_size_public_tree_tensor"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.multi_size_public_tree_tensor"
+target = "pontius.river_multiway_multi_size"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.axis_public_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.multi_size_leaf_adjoint"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.multi_size_public_tree_tensor"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.resident_leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.sparse_open_mode_cfr"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.multi_size_resident_leaf_adjoint_cfr"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.multiway_river_calibration"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.multiway_river_calibration"
+target = "pontius.coalition"
+
+[[edge]]
+origin = "pontius.multiway_river_calibration"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.multiway_river_calibration"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.multiway_river_calibration"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multiway_river_calibration"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.multiway_river_calibration"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.multiway_river_calibration"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.multiway_river_context"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.multiway_river_context"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.multiway_search_experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.multiway_search_experiment"
+target = "pontius.coalition"
+
+[[edge]]
+origin = "pontius.multiway_search_experiment"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.multiway_search_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.multiway_search_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multiway_search_experiment"
+target = "pontius.multiway_river_context"
+
+[[edge]]
+origin = "pontius.multiway_search_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.multiway_search_experiment"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.multiway_source_tape_audit"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.multiway_source_tape_audit"
+target = "pontius.coalition"
+
+[[edge]]
+origin = "pontius.multiway_source_tape_audit"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.multiway_source_tape_audit"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.multiway_source_tape_audit"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.multiway_source_tape_audit"
+target = "pontius.multiway_river_context"
+
+[[edge]]
+origin = "pontius.multiway_source_tape_audit"
+target = "pontius.multiway_search_experiment"
+
+[[edge]]
+origin = "pontius.multiway_source_tape_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_corpus"
+target = "pontius.native_simplex_audit_structures"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_corpus"
+target = "pontius.reduced_river_sizing_lp"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_reanalysis"
+target = "pontius.native_simplex_audit_reanalysis_seal"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_reanalysis"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_runner"
+target = "pontius.linear_program"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_runner"
+target = "pontius.linear_program_certificate"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_runner"
+target = "pontius.native_simplex_audit_corpus"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_runner"
+target = "pontius.native_simplex_audit_seal"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_runner"
+target = "pontius.native_simplex_audit_structures"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_runner"
+target = "pontius.reduced_river_sizing_lp"
+
+[[edge]]
+origin = "pontius.native_simplex_audit_structures"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.one_seat_convex_generation"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.one_seat_convex_generation"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.one_seat_convex_generation"
+target = "pontius.linear_program"
+
+[[edge]]
+origin = "pontius.one_seat_convex_keystone"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.one_seat_convex_keystone"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.one_seat_convex_keystone"
+target = "pontius.kuhn"
+
+[[edge]]
+origin = "pontius.one_seat_convex_keystone"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.one_seat_convex_keystone"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.one_seat_convex_keystone"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.one_seat_convex_keystone"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.one_seat_row_growth_audit"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.one_seat_row_growth_audit"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.one_seat_row_growth_audit"
+target = "pontius.linear_program"
+
+[[edge]]
+origin = "pontius.one_seat_row_growth_audit"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.open_mode_cfr_bridge"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.open_mode_showdown"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.public_tree_tensor_cfr"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.real_policy_representation_audit"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.real_policy_representation_audit_v2"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.open_mode_audit"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.open_mode_cfr_bridge"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.open_mode_cfr_bridge"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.open_mode_cfr_bridge"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.open_mode_cfr_bridge"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.open_mode_factor_tt"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.open_mode_factor_tt"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.open_mode_showdown"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.open_mode_showdown"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.policy"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.policy"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.depth_limited"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.river_selective"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.river_selective_experiment"
+
+[[edge]]
+origin = "pontius.policy_delta_experiment"
+target = "pontius.selective_tree"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.policy_delta_tt_audit"
+target = "pontius.tensor_train_algebra"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.cross_payoff_adjoint_result"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.pre_bet_initial_row_cache"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.public_node_open_axis"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.runner_harness_v2"
+
+[[edge]]
+origin = "pontius.pre_bet_initial_row_cache_v2"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.preparation_bank"
+target = "pontius.action_clock"
+
+[[edge]]
+origin = "pontius.preparation_bank"
+target = "pontius.street_deadline"
+
+[[edge]]
+origin = "pontius.profiled_policy_tt"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.profiled_policy_tt"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.profiled_policy_tt"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.profiled_policy_tt"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.profiled_policy_tt"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.public_node_behavioral_axis"
+target = "pontius.behavioral_one_seat_master"
+
+[[edge]]
+origin = "pontius.public_node_behavioral_axis"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.public_node_behavioral_axis"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.public_node_open_axis"
+target = "pontius.cross_payoff_adjoint_result"
+
+[[edge]]
+origin = "pontius.public_node_open_axis"
+target = "pontius.dense_root_cross_payoff_control"
+
+[[edge]]
+origin = "pontius.public_node_open_axis"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.public_node_open_axis"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.public_node_open_axis"
+target = "pontius.sequence_form_open_axis"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.public_policy_tt"
+target = "pontius.tensor_train_algebra"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.public_policy_tt_audit"
+target = "pontius.tensor_train_algebra"
+
+[[edge]]
+origin = "pontius.public_tree_quotient_audit"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.public_tree_quotient_audit"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.public_tree_quotient_audit"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.public_tree_quotient_audit"
+target = "pontius.multiway_river_context"
+
+[[edge]]
+origin = "pontius.public_tree_quotient_audit"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.public_tree_quotient_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.public_tree_quotient_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.public_tree_quotient_audit"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.public_tree_tensor"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.public_tree_tensor"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.public_tree_tensor"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.public_tree_tensor"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.public_tree_tensor_cfr"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.public_tree_tensor_cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.public_tree_tensor_cfr"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.public_tree_tensor_cfr"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.real_policy"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.real_policy"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.real_policy"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.real_policy"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.real_policy"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.batched_factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.clean_fringe_tt"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.profiled_policy_tt"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.seat_order_tt"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit_v2"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit_v2"
+target = "pontius.real_policy_representation_audit"
+
+[[edge]]
+origin = "pontius.real_policy_representation_audit_v2"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.public_tree_tensor_cfr"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.real_policy_source"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.reduced_river_sizing_oracle"
+target = "pontius.linear_program"
+
+[[edge]]
+origin = "pontius.reduced_river_sizing_oracle"
+target = "pontius.matrix_game"
+
+[[edge]]
+origin = "pontius.reduced_river_sizing_oracle"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.reduced_river_sizing_oracle"
+target = "pontius.reduced_river_sizing_lp"
+
+[[edge]]
+origin = "pontius.reduced_river_sizing_oracle"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.reference_hand_replay"
+target = "pontius.full_width_belief"
+
+[[edge]]
+origin = "pontius.reference_hand_replay"
+target = "pontius.full_width_reference_policy"
+
+[[edge]]
+origin = "pontius.reference_hand_replay"
+target = "pontius.holdem_cards"
+
+[[edge]]
+origin = "pontius.reference_hand_replay"
+target = "pontius.immutable_blueprint"
+
+[[edge]]
+origin = "pontius.reference_hand_replay"
+target = "pontius.legal_decision_spine"
+
+[[edge]]
+origin = "pontius.reference_hand_replay"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.reference_hand_replay"
+target = "pontius.street_deadline"
+
+[[edge]]
+origin = "pontius.reporting"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.resident_heterogeneous_leaf_contraction"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.resident_heterogeneous_leaf_contraction"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.resident_heterogeneous_leaf_contraction"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.resident_heterogeneous_leaf_contraction"
+target = "pontius.open_mode_showdown"
+
+[[edge]]
+origin = "pontius.resident_heterogeneous_leaf_contraction"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.resident_heterogeneous_leaf_contraction"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.sparse_open_mode_cfr"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_cfr"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.fixed_envelope_verifier"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.leaf_adjoint_evaluation"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.resident_leaf_adjoint_evaluation"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.resident_record_to_hand_fold"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.resident_record_to_hand_fold"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.resident_record_to_hand_fold_v2"
+target = "pontius.cupy_sparse_incidence"
+
+[[edge]]
+origin = "pontius.resident_record_to_hand_fold_v2"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.resident_record_to_hand_fold_v2"
+target = "pontius.resident_record_to_hand_fold"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.h32_affine_resident_cache_preflight"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.legal_decision_spine_v2"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.legal_river_continuation"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.no_limit_betting"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.one_seat_convex_generation"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone"
+target = "pontius.runner_harness"
+
+[[edge]]
+origin = "pontius.responder_raise_semantics_keystone_result"
+target = "pontius.responder_raise_semantics_keystone_result_seal"
+
+[[edge]]
+origin = "pontius.river"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_cache"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_cache"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_cache"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_context"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_incremental"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_incremental"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.river_cache"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.river_incremental"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.river_range_reuse"
+
+[[edge]]
+origin = "pontius.river_incremental_experiment"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.river_multi_size"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_multi_size"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_multi_size_audit"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_multi_size_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_multi_size_audit"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.dependency_tape"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.river_incremental"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.river_multi_size_audit"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.river_range_reuse"
+
+[[edge]]
+origin = "pontius.river_multi_size_experiment"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.river_multiway"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_multiway"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_multiway_multi_size"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_multiway_multi_size"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_multiway_multi_size"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.river_multiway_multi_size"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.depth_limited"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.river_incremental"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.river_selective"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.river_selective_experiment"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.river_selective_screen"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.selective_tree"
+
+[[edge]]
+origin = "pontius.river_noop_full_replication"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.river_opportunity"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.river_opportunity"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_opportunity"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_opportunity"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.river_opportunity"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.river_opportunity"
+target = "pontius.river_oracle"
+
+[[edge]]
+origin = "pontius.river_opportunity"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.river_oracle"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_oracle"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_oracle"
+target = "pontius.matrix_game"
+
+[[edge]]
+origin = "pontius.river_oracle"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.river_cache"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.river_oracle"
+
+[[edge]]
+origin = "pontius.river_range_reuse"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.river_scheduler_holdout"
+target = "pontius.river_opportunity"
+
+[[edge]]
+origin = "pontius.river_scheduler_holdout"
+target = "pontius.river_scheduler_screen"
+
+[[edge]]
+origin = "pontius.river_scheduler_screen"
+target = "pontius.river_opportunity"
+
+[[edge]]
+origin = "pontius.river_selective"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_selective"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_selective"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.depth_limited"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.river_incremental"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.river_multi_size"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.river_multi_size_experiment"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.river_range_reuse"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.river_selective"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.selective_tree"
+
+[[edge]]
+origin = "pontius.river_selective_experiment"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.river_selective_payoff_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.river_selective_payoff_audit"
+target = "pontius.river_selective_screen"
+
+[[edge]]
+origin = "pontius.river_shadow_probe"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.river_shadow_probe"
+target = "pontius.river_context"
+
+[[edge]]
+origin = "pontius.river_shadow_probe"
+target = "pontius.river_opportunity"
+
+[[edge]]
+origin = "pontius.river_trace_analysis"
+target = "pontius.river_opportunity"
+
+[[edge]]
+origin = "pontius.river_trace_comparison"
+target = "pontius.river_trace_analysis"
+
+[[edge]]
+origin = "pontius.runner_harness"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.safe_composition_experiment"
+target = "pontius.continual"
+
+[[edge]]
+origin = "pontius.safe_composition_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.safe_composition_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.safe_composition_experiment"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.safe_composition_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.safe_composition_experiment"
+target = "pontius.safe_resolving"
+
+[[edge]]
+origin = "pontius.safe_composition_matrix"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.safe_composition_matrix"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.safe_composition_matrix"
+target = "pontius.safe_composition_experiment"
+
+[[edge]]
+origin = "pontius.safe_oracle_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.safe_oracle_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.safe_oracle_experiment"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.safe_oracle_experiment"
+target = "pontius.maxmargin"
+
+[[edge]]
+origin = "pontius.safe_oracle_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.safe_oracle_matrix"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.safe_oracle_matrix"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.safe_oracle_matrix"
+target = "pontius.safe_oracle_experiment"
+
+[[edge]]
+origin = "pontius.safe_resolving"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.safe_resolving"
+target = "pontius.continual"
+
+[[edge]]
+origin = "pontius.safe_resolving"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.safe_resolving"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.safe_resolving"
+target = "pontius.kuhn"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_experiment"
+target = "pontius.cfr"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_experiment"
+target = "pontius.continual"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_experiment"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_experiment"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_experiment"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_experiment"
+target = "pontius.maxmargin"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_experiment"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_experiment"
+target = "pontius.safe_resolving"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_matrix"
+target = "pontius.leaf_experiment"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_matrix"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.safe_solver_gap_matrix"
+target = "pontius.safe_solver_gap_experiment"
+
+[[edge]]
+origin = "pontius.selection"
+target = "pontius.leaf_matrix"
+
+[[edge]]
+origin = "pontius.selective_tree"
+target = "pontius.depth_limited"
+
+[[edge]]
+origin = "pontius.selective_tree"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.selector_fan_controls"
+target = "pontius.exact_selector_fan"
+
+[[edge]]
+origin = "pontius.selector_fan_controls"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.selector_stable_affine_response"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.selector_stable_affine_response"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.selector_stable_affine_response"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.selector_stable_affine_response"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.selector_stable_affine_response"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.selector_stable_affine_response"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.selector_window"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.selector_window"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.selector_window_v2"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.selector_window_v2"
+target = "pontius.selector_window"
+
+[[edge]]
+origin = "pontius.sequence_form_open_axis"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.sequence_form_open_axis"
+target = "pontius.heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.sequence_form_open_axis"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.sequence_form_open_axis"
+target = "pontius.leaf_adjoint_cfr"
+
+[[edge]]
+origin = "pontius.sequence_form_open_axis"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.shared_resident_response_context"
+target = "pontius.incremental_leaf_adjoint_response"
+
+[[edge]]
+origin = "pontius.shared_resident_response_context"
+target = "pontius.resident_heterogeneous_leaf_contraction"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.river_multiway"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.showdown_value_rank_screen"
+target = "pontius.terminal_tensor_evaluation"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.batched_factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.clean_fringe_tt"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.profiled_policy_tt"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.real_policy"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.real_policy_representation_audit"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.real_policy_representation_audit_v2"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.signed_clean_fringe_tt"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_audit"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_tt"
+target = "pontius.batched_factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_tt"
+target = "pontius.clean_fringe_tt"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_tt"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_tt"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_tt"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_tt"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.signed_clean_fringe_tt"
+target = "pontius.tensor_train_algebra"
+
+[[edge]]
+origin = "pontius.sizing_power_diagnostic"
+target = "pontius.action_abstraction_confirmation"
+
+[[edge]]
+origin = "pontius.sizing_power_diagnostic"
+target = "pontius.reduced_river_sizing_oracle"
+
+[[edge]]
+origin = "pontius.sparse_incidence_audit"
+target = "pontius.open_mode_audit"
+
+[[edge]]
+origin = "pontius.sparse_incidence_audit"
+target = "pontius.open_mode_showdown"
+
+[[edge]]
+origin = "pontius.sparse_incidence_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.sparse_incidence_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.sparse_incidence_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.sparse_incidence_audit"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.sparse_incidence_audit"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.sparse_incidence_open_mode"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.sparse_incidence_open_mode"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.sparse_incidence_open_mode"
+target = "pontius.open_mode_showdown"
+
+[[edge]]
+origin = "pontius.sparse_incidence_open_mode"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.open_mode_cfr_bridge"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.public_tree_tensor_cfr"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.sparse_open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.unrounded_policy_tt"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_cfr"
+target = "pontius.updates"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_factor_tt"
+target = "pontius.factor_tt_contraction"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_factor_tt"
+target = "pontius.open_mode_factor_tt"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_factor_tt"
+target = "pontius.sparse_incidence_open_mode"
+
+[[edge]]
+origin = "pontius.sparse_open_mode_factor_tt"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton"
+target = "pontius.tensor_train_algebra"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton_audit"
+target = "pontius.factorized_belief"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton_audit"
+target = "pontius.factorized_belief_audit"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton_audit"
+target = "pontius.public_policy_tt"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton_audit"
+target = "pontius.reporting"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton_audit"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton_audit"
+target = "pontius.showdown_value_rank_screen"
+
+[[edge]]
+origin = "pontius.structured_showdown_automaton_audit"
+target = "pontius.structured_showdown_automaton"
+
+[[edge]]
+origin = "pontius.tensor_train_algebra"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.terminal_tensor_evaluation"
+target = "pontius.evaluation"
+
+[[edge]]
+origin = "pontius.terminal_tensor_evaluation"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.terminal_tensor_evaluation"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.tie_aware_affine_adapter"
+target = "pontius.exact_tie_aware_affine_envelope"
+
+[[edge]]
+origin = "pontius.tie_aware_affine_adapter"
+target = "pontius.selector_window"
+
+[[edge]]
+origin = "pontius.tie_aware_affine_adapter"
+target = "pontius.selector_window_v2"
+
+[[edge]]
+origin = "pontius.tie_semantics_conformance_v2"
+target = "pontius.tie_semantics_conformance"
+
+[[edge]]
+origin = "pontius.unrounded_policy_tt"
+target = "pontius.game"
+
+[[edge]]
+origin = "pontius.unrounded_policy_tt"
+target = "pontius.incremental_policy_tt"
+
+[[edge]]
+origin = "pontius.unrounded_policy_tt"
+target = "pontius.public_tree_tensor"
+
+[[edge]]
+origin = "pontius.unrounded_policy_tt"
+target = "pontius.river"
+
+[[edge]]
+origin = "pontius.unrounded_policy_tt"
+target = "pontius.tensor_train"
+
+[[edge]]
+origin = "pontius.unrounded_policy_tt"
+target = "pontius.tensor_train_algebra"
+
+[[edge]]
+origin = "pontius.width_four_sizing_power"
+target = "pontius.action_abstraction_confirmation"
+
+[[edge]]
+origin = "pontius.width_four_sizing_power"
+target = "pontius.reduced_river_sizing_oracle"
+
+[[edge]]
+origin = "pontius.width_four_sizing_power_evaluation"
+target = "pontius.reduced_river_sizing_oracle"
+
+[[edge]]
+origin = "pontius.width_four_sizing_power_evaluation"
+target = "pontius.sizing_power_diagnostic"
+
+[[edge]]
+origin = "pontius.width_four_sizing_power_evaluation"
+target = "pontius.width_four_sizing_power"
+
+[[scc]]
+members = ["pontius.__init__"]
+
+[[scc]]
+members = ["pontius.action_abstraction_confirmation"]
+
+[[scc]]
+members = ["pontius.action_clock", "pontius.preparation_bank"]
+
+[[scc]]
+members = ["pontius.affine_resident_heterogeneous_leaf_contraction"]
+
+[[scc]]
+members = ["pontius.atomic_json_checkpoint"]
+
+[[scc]]
+members = ["pontius.axis_cfr_checkpoint"]
+
+[[scc]]
+members = ["pontius.axis_public_cfr"]
+
+[[scc]]
+members = ["pontius.batched_factor_tt_contraction"]
+
+[[scc]]
+members = ["pontius.batched_selector_stable_affine_response"]
+
+[[scc]]
+members = ["pontius.behavioral_one_seat_master"]
+
+[[scc]]
+members = ["pontius.behavioral_one_seat_master_v2"]
+
+[[scc]]
+members = ["pontius.behavioral_open_axis"]
+
+[[scc]]
+members = ["pontius.benefit_experiment"]
+
+[[scc]]
+members = ["pontius.benefit_matrix"]
+
+[[scc]]
+members = ["pontius.benefit_trajectory"]
+
+[[scc]]
+members = ["pontius.campaign_deadline"]
+
+[[scc]]
+members = ["pontius.canonical_affine_resident_automaton_cache"]
+
+[[scc]]
+members = ["pontius.capacity_filling_action_abstraction"]
+
+[[scc]]
+members = ["pontius.certified_reduced_sizing_consumer_v2"]
+
+[[scc]]
+members = ["pontius.certified_reduced_sizing_consumer_v2_seal"]
+
+[[scc]]
+members = ["pontius.certified_reduced_sizing_highs"]
+
+[[scc]]
+members = ["pontius.certified_reduced_sizing_highs_seal"]
+
+[[scc]]
+members = ["pontius.certified_sizing_validation_runner"]
+
+[[scc]]
+members = ["pontius.certified_sizing_validation_seal"]
+
+[[scc]]
+members = ["pontius.cfr"]
+
+[[scc]]
+members = ["pontius.clean_fringe_tt"]
+
+[[scc]]
+members = ["pontius.coalition"]
+
+[[scc]]
+members = ["pontius.collision_repair_action_abstraction"]
+
+[[scc]]
+members = ["pontius.collision_repair_v3_evaluation"]
+
+[[scc]]
+members = ["pontius.complete_factorized_affine_evidence"]
+
+[[scc]]
+members = ["pontius.composition_experiment"]
+
+[[scc]]
+members = ["pontius.composition_matrix"]
+
+[[scc]]
+members = ["pontius.constrained_generation"]
+
+[[scc]]
+members = ["pontius.constrained_generation_experiment"]
+
+[[scc]]
+members = ["pontius.constrained_generation_matrix"]
+
+[[scc]]
+members = ["pontius.continual"]
+
+[[scc]]
+members = ["pontius.continuation_public_tree_tensor"]
+
+[[scc]]
+members = ["pontius.convex_retreat_tolerances"]
+
+[[scc]]
+members = ["pontius.cross_payoff_adjoint_result"]
+
+[[scc]]
+members = ["pontius.cross_payoff_leaf_adjoint"]
+
+[[scc]]
+members = ["pontius.cuda_dll_bootstrap"]
+
+[[scc]]
+members = ["pontius.cupy_sparse_incidence"]
+
+[[scc]]
+members = ["pontius.deadline_owned_result"]
+
+[[scc]]
+members = ["pontius.delta_certificate_contract"]
+
+[[scc]]
+members = ["pontius.dense_root_cross_payoff_control"]
+
+[[scc]]
+members = ["pontius.dependency_tape"]
+
+[[scc]]
+members = ["pontius.dependency_tape_experiment"]
+
+[[scc]]
+members = ["pontius.depth_limited"]
+
+[[scc]]
+members = ["pontius.device_fold_resident_heterogeneous_leaf_contraction"]
+
+[[scc]]
+members = ["pontius.device_fold_resident_heterogeneous_leaf_contraction_v2"]
+
+[[scc]]
+members = ["pontius.device_fold_resident_leaf_adjoint_cfr"]
+
+[[scc]]
+members = ["pontius.device_fold_resident_leaf_adjoint_cfr_v2"]
+
+[[scc]]
+members = ["pontius.device_fold_selector_stable_affine_response"]
+
+[[scc]]
+members = ["pontius.device_fold_selector_stable_affine_response_v2"]
+
+[[scc]]
+members = ["pontius.durable_evidence_journal"]
+
+[[scc]]
+members = ["pontius.evaluation"]
+
+[[scc]]
+members = ["pontius.evidence_protocol"]
+
+[[scc]]
+members = ["pontius.exact_collision_oracle"]
+
+[[scc]]
+members = ["pontius.exact_directional_face_oracle"]
+
+[[scc]]
+members = ["pontius.exact_directional_face_oracle_seal"]
+
+[[scc]]
+members = ["pontius.exact_oracle_assessment"]
+
+[[scc]]
+members = ["pontius.exact_selector_fan"]
+
+[[scc]]
+members = ["pontius.exact_selector_window_oracle"]
+
+[[scc]]
+members = ["pontius.exact_sequence_form_coefficient_oracle"]
+
+[[scc]]
+members = ["pontius.exact_tie_aware_affine_envelope"]
+
+[[scc]]
+members = ["pontius.experiment"]
+
+[[scc]]
+members = ["pontius.factor_tt_contraction"]
+
+[[scc]]
+members = ["pontius.factor_tt_contraction_audit"]
+
+[[scc]]
+members = ["pontius.factorized_belief"]
+
+[[scc]]
+members = ["pontius.factorized_belief_audit"]
+
+[[scc]]
+members = ["pontius.factorized_tie_aware_affine"]
+
+[[scc]]
+members = ["pontius.factorized_tie_aware_affine_seal"]
+
+[[scc]]
+members = ["pontius.fixed_envelope_verifier"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_greedy"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_greedy_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_greedy"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_greedy_result"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_greedy_result_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_greedy_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_qualification"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_qualification_result"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_qualification_result_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_qualification_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_teacher"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_teacher_result"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_teacher_result_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_nonreplay_teacher_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_qualification"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_qualification_result"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_qualification_result_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_qualification_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_structures"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_structures_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_teacher"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_teacher_result"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_teacher_result_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_teacher_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_confirmation"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_confirmation_result"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_confirmation_result_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_confirmation_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_qualification"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_qualification_result"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_qualification_result_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_qualification_seal"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_structures"]
+
+[[scc]]
+members = ["pontius.fresh_action_width_transfer_structures_seal"]
+
+[[scc]]
+members = ["pontius.fresh_capacity_filling_qualification"]
+
+[[scc]]
+members = ["pontius.fresh_capacity_filling_structures"]
+
+[[scc]]
+members = ["pontius.fresh_collision_repair_qualification"]
+
+[[scc]]
+members = ["pontius.fresh_collision_repair_structures"]
+
+[[scc]]
+members = ["pontius.fresh_h32_strategy_transfer_audit"]
+
+[[scc]]
+members = ["pontius.full_width_belief"]
+
+[[scc]]
+members = ["pontius.full_width_factor_tt_capacity"]
+
+[[scc]]
+members = ["pontius.full_width_occupied_card_quotient_capacity"]
+
+[[scc]]
+members = ["pontius.full_width_reference_policy"]
+
+[[scc]]
+members = ["pontius.full_width_river_capacity_preflight"]
+
+[[scc]]
+members = ["pontius.full_width_river_capacity_preflight_v2"]
+
+[[scc]]
+members = ["pontius.game"]
+
+[[scc]]
+members = ["pontius.gpu_occupied_card_quotient"]
+
+[[scc]]
+members = ["pontius.gpu_quotient_staged_scaling"]
+
+[[scc]]
+members = ["pontius.gpu_quotient_staged_scaling_result"]
+
+[[scc]]
+members = ["pontius.gpu_quotient_staged_scaling_runner"]
+
+[[scc]]
+members = ["pontius.gpu_quotient_staged_scaling_v2_result"]
+
+[[scc]]
+members = ["pontius.gpu_quotient_staged_scaling_v2_runner"]
+
+[[scc]]
+members = ["pontius.gpu_quotient_validation_seam"]
+
+[[scc]]
+members = ["pontius.h32_acceptance_semantics_replay"]
+
+[[scc]]
+members = ["pontius.h32_action_conditioned_posterior_manifest"]
+
+[[scc]]
+members = ["pontius.h32_action_conditioned_widened_selector_trial"]
+
+[[scc]]
+members = ["pontius.h32_action_width_quality_audit"]
+
+[[scc]]
+members = ["pontius.h32_action_width_quality_audit_v2"]
+
+[[scc]]
+members = ["pontius.h32_affine_resident_cache_preflight"]
+
+[[scc]]
+members = ["pontius.h32_atomic_response_preflight"]
+
+[[scc]]
+members = ["pontius.h32_atomic_street_scheduler_audit"]
+
+[[scc]]
+members = ["pontius.h32_candidate_availability_replay"]
+
+[[scc]]
+members = ["pontius.h32_candidate_availability_replay_v2"]
+
+[[scc]]
+members = ["pontius.h32_canonical_affine_cache_replay"]
+
+[[scc]]
+members = ["pontius.h32_continuation_depth_ledger"]
+
+[[scc]]
+members = ["pontius.h32_continuation_direction_capacity"]
+
+[[scc]]
+members = ["pontius.h32_continuation_root_ledger"]
+
+[[scc]]
+members = ["pontius.h32_continuation_root_preflight"]
+
+[[scc]]
+members = ["pontius.h32_continuation_root_strategy_trial"]
+
+[[scc]]
+members = ["pontius.h32_convex_replication_posterior_manifest"]
+
+[[scc]]
+members = ["pontius.h32_cross_payoff_adjoint_feasibility"]
+
+[[scc]]
+members = ["pontius.h32_current_decision_combined_ledger_replay"]
+
+[[scc]]
+members = ["pontius.h32_current_interpolation_audit"]
+
+[[scc]]
+members = ["pontius.h32_decision_aligned_continuation_setup"]
+
+[[scc]]
+members = ["pontius.h32_decision_aligned_live_shadow_trial"]
+
+[[scc]]
+members = ["pontius.h32_decision_aligned_posterior_manifest"]
+
+[[scc]]
+members = ["pontius.h32_deep_horizon_correction_replay"]
+
+[[scc]]
+members = ["pontius.h32_deep_horizon_opportunity_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_board_panel_cache_preflight"]
+
+[[scc]]
+members = ["pontius.h32_fresh_causal_direction_screen"]
+
+[[scc]]
+members = ["pontius.h32_fresh_convex_retreat_replication"]
+
+[[scc]]
+members = ["pontius.h32_fresh_panel_action_width_warm_step_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_panel_action_width_warm_step_audit_v2"]
+
+[[scc]]
+members = ["pontius.h32_fresh_panel_source_blueprint_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_panel_target_transfer_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_panel_target_transfer_audit_v2"]
+
+[[scc]]
+members = ["pontius.h32_fresh_public_block_radius_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_public_block_value_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_regret_vertex_opportunity_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_selector_stable_affine_street_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_selector_stable_affine_street_seat5_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_union_value_audit"]
+
+[[scc]]
+members = ["pontius.h32_fresh_union_value_audit_v2"]
+
+[[scc]]
+members = ["pontius.h32_heldout_continuation_depth_value_trial"]
+
+[[scc]]
+members = ["pontius.h32_heldout_continuation_posterior_manifest"]
+
+[[scc]]
+members = ["pontius.h32_latin_f_convex_retreat_confirmation"]
+
+[[scc]]
+members = ["pontius.h32_multi_size_resident_cache_preflight"]
+
+[[scc]]
+members = ["pontius.h32_one_round_convex_master"]
+
+[[scc]]
+members = ["pontius.h32_one_seat_open_axis_preflight"]
+
+[[scc]]
+members = ["pontius.h32_one_seat_retreat_quality_trial"]
+
+[[scc]]
+members = ["pontius.h32_one_seat_retreat_quality_trial_v2"]
+
+[[scc]]
+members = ["pontius.h32_policy_delta_verifier_audit"]
+
+[[scc]]
+members = ["pontius.h32_post_fold_closure_value_confirmation"]
+
+[[scc]]
+members = ["pontius.h32_post_fold_current_decision_setup"]
+
+[[scc]]
+members = ["pontius.h32_post_fold_failure_closure_diagnostic"]
+
+[[scc]]
+members = ["pontius.h32_post_fold_posterior_manifest"]
+
+[[scc]]
+members = ["pontius.h32_pre_bet_action_width_capacity"]
+
+[[scc]]
+members = ["pontius.h32_pre_bet_initial_row_cache_seed"]
+
+[[scc]]
+members = ["pontius.h32_pre_bet_initial_row_gpu"]
+
+[[scc]]
+members = ["pontius.h32_pre_bet_work_reduction_analysis"]
+
+[[scc]]
+members = ["pontius.h32_resident_cfr_audit"]
+
+[[scc]]
+members = ["pontius.h32_resident_cfr_audit_v2"]
+
+[[scc]]
+members = ["pontius.h32_resident_cfr_restart_semantics_audit"]
+
+[[scc]]
+members = ["pontius.h32_resident_cfr_sustained_audit"]
+
+[[scc]]
+members = ["pontius.h32_resident_record_to_hand_fold_differential"]
+
+[[scc]]
+members = ["pontius.h32_resident_sparse_ncu_profile"]
+
+[[scc]]
+members = ["pontius.h32_resident_sparse_ncu_profile_v2"]
+
+[[scc]]
+members = ["pontius.h32_resident_sparse_ncu_profile_v3"]
+
+[[scc]]
+members = ["pontius.h32_resident_sparse_ncu_workload"]
+
+[[scc]]
+members = ["pontius.h32_resident_step_bottleneck_profile"]
+
+[[scc]]
+members = ["pontius.h32_resident_step_bottleneck_profile_v2"]
+
+[[scc]]
+members = ["pontius.h32_resident_verifier_audit"]
+
+[[scc]]
+members = ["pontius.h32_response_latency_bridge_audit"]
+
+[[scc]]
+members = ["pontius.h32_retained_affine_selector_cascade_direct_replay"]
+
+[[scc]]
+members = ["pontius.h32_retained_affine_selector_cascade_replay"]
+
+[[scc]]
+members = ["pontius.h32_retained_affine_selector_cascade_replay_v2"]
+
+[[scc]]
+members = ["pontius.h32_retained_affine_selector_cascade_replay_v3"]
+
+[[scc]]
+members = ["pontius.h32_retained_convex_closure_census"]
+
+[[scc]]
+members = ["pontius.h32_retained_convex_closure_census_v2"]
+
+[[scc]]
+members = ["pontius.h32_second_board_action_width_quality_audit"]
+
+[[scc]]
+members = ["pontius.h32_second_board_resident_cache_preflight"]
+
+[[scc]]
+members = ["pontius.h32_selector_stable_affine_certificate_audit"]
+
+[[scc]]
+members = ["pontius.h32_selector_stable_affine_certificate_audit_v2"]
+
+[[scc]]
+members = ["pontius.h32_shared_response_allocator_lifecycle_replay"]
+
+[[scc]]
+members = ["pontius.h32_shared_response_residency_replay"]
+
+[[scc]]
+members = ["pontius.h32_tier_b_opponent_batch_differential"]
+
+[[scc]]
+members = ["pontius.h32_tier_b_opponent_batch_differential_v2"]
+
+[[scc]]
+members = ["pontius.h32_warm_candidate_stream_audit"]
+
+[[scc]]
+members = ["pontius.h32_warm_search_acceptance_audit"]
+
+[[scc]]
+members = ["pontius.h4_sequence_form_open_axis_differential"]
+
+[[scc]]
+members = ["pontius.h4_shifted_belief_dense_crosscheck"]
+
+[[scc]]
+members = ["pontius.heterogeneous_leaf_contraction"]
+
+[[scc]]
+members = ["pontius.holdem_cards"]
+
+[[scc]]
+members = ["pontius.immutable_blueprint"]
+
+[[scc]]
+members = ["pontius.incremental_leaf_adjoint_response"]
+
+[[scc]]
+members = ["pontius.incremental_policy_tt"]
+
+[[scc]]
+members = ["pontius.kuhn"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_batch_width_audit"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_batch_width_audit_v2"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_cfr"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_cfr_audit"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_checkpoint_extension_audit"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_checkpoint_ladder_audit"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_checkpoint_ladder_audit_v2"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_evaluation"]
+
+[[scc]]
+members = ["pontius.leaf_adjoint_evaluation_audit"]
+
+[[scc]]
+members = ["pontius.leaf_experiment"]
+
+[[scc]]
+members = ["pontius.leaf_matrix"]
+
+[[scc]]
+members = ["pontius.legal_action_abstraction"]
+
+[[scc]]
+members = ["pontius.legal_decision_spine"]
+
+[[scc]]
+members = ["pontius.legal_decision_spine_v2"]
+
+[[scc]]
+members = ["pontius.legal_h4_factorized_affine_confirmation"]
+
+[[scc]]
+members = ["pontius.legal_h4_factorized_affine_confirmation_directions"]
+
+[[scc]]
+members = ["pontius.legal_h4_factorized_affine_confirmation_population"]
+
+[[scc]]
+members = ["pontius.legal_h4_factorized_affine_confirmation_population_seal"]
+
+[[scc]]
+members = ["pontius.legal_h4_factorized_affine_confirmation_result"]
+
+[[scc]]
+members = ["pontius.legal_h4_factorized_affine_confirmation_result_seal"]
+
+[[scc]]
+members = ["pontius.legal_h4_selector_directions"]
+
+[[scc]]
+members = ["pontius.legal_h4_selector_fixture"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_coefficient_differential"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_coefficient_result"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_coefficient_result_seal"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_directional_face"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_directional_face_result"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_directional_face_result_seal"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_factorized_affine"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_factorized_affine_result"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_factorized_affine_result_seal"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_row_growth"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_row_growth_result"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_row_growth_result_seal"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_selector_fan_result"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_selector_fan_result_seal"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_selector_window"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_tie_aware_affine"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_tie_aware_affine_result"]
+
+[[scc]]
+members = ["pontius.legal_responder_raise_h4_tie_aware_affine_result_seal"]
+
+[[scc]]
+members = ["pontius.legal_river_continuation"]
+
+[[scc]]
+members = ["pontius.legal_river_exact_cubin_inspector_diagnostic"]
+
+[[scc]]
+members = ["pontius.legal_river_exact_cubin_inspector_diagnostic_result"]
+
+[[scc]]
+members = ["pontius.legal_river_exact_cubin_inspector_diagnostic_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_exact_cubin_inspector_selection"]
+
+[[scc]]
+members = ["pontius.legal_river_exact_cubin_inspector_selection_seal"]
+
+[[scc]]
+members = ["pontius.legal_river_exact_cubin_zero_suffix_diagnostic"]
+
+[[scc]]
+members = ["pontius.legal_river_exact_cubin_zero_suffix_diagnostic_result"]
+
+[[scc]]
+members = ["pontius.legal_river_exact_cubin_zero_suffix_diagnostic_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_base_provenance"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_bridge"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v2_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v3"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v3_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v4_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v5_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v5_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v6_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v6_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v7_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_compiled_global_separation_calibration_v7_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_consumer_capacity"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_tiles"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_adapter"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_adapter"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_consumer"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_device"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_device_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_device_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_device_v2_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_device_v2_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_device_v3_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_device_v3_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_oracle"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_cuda_shared_direct_sample_plan"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_exact_integer_operator"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_actual45_fit_projection"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_actual45_fit_projection_outcome"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_actual45_fit_projection_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_actual45_fit_projection_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight_v2_outcome"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight_v2_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight_v3_outcome"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight_v3_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_fixed_width_work_comparison"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_global_separation_topologies"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_selective_certified_separation"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_selective_certified_separation_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_selective_certified_separation_runner"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_shared_direct_artifact_capacity"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_shared_direct_artifact_capacity_result"]
+
+[[scc]]
+members = ["pontius.legal_river_quotient_shared_direct_artifact_capacity_runner"]
+
+[[scc]]
+members = ["pontius.linear_program"]
+
+[[scc]]
+members = ["pontius.linear_program_certificate"]
+
+[[scc]]
+members = ["pontius.literal_45_quotient_liveness"]
+
+[[scc]]
+members = ["pontius.literal_45_quotient_target"]
+
+[[scc]]
+members = ["pontius.literal_45_quotient_target_result"]
+
+[[scc]]
+members = ["pontius.literal_45_quotient_target_runner"]
+
+[[scc]]
+members = ["pontius.local_response_bridge"]
+
+[[scc]]
+members = ["pontius.matrix_game"]
+
+[[scc]]
+members = ["pontius.maxmargin"]
+
+[[scc]]
+members = ["pontius.multi_size_affine_cross_payoff"]
+
+[[scc]]
+members = ["pontius.multi_size_affine_resident_leaf_adjoint_cfr"]
+
+[[scc]]
+members = ["pontius.multi_size_affine_resident_leaf_adjoint_evaluation"]
+
+[[scc]]
+members = ["pontius.multi_size_continuation_public_tree_tensor"]
+
+[[scc]]
+members = ["pontius.multi_size_leaf_adjoint"]
+
+[[scc]]
+members = ["pontius.multi_size_leaf_adjoint_audit"]
+
+[[scc]]
+members = ["pontius.multi_size_policy_bridge"]
+
+[[scc]]
+members = ["pontius.multi_size_public_tree_tensor"]
+
+[[scc]]
+members = ["pontius.multi_size_resident_leaf_adjoint_cfr"]
+
+[[scc]]
+members = ["pontius.multiway_river_calibration"]
+
+[[scc]]
+members = ["pontius.multiway_river_context"]
+
+[[scc]]
+members = ["pontius.multiway_search_experiment"]
+
+[[scc]]
+members = ["pontius.multiway_source_tape_audit"]
+
+[[scc]]
+members = ["pontius.native_simplex_audit_corpus"]
+
+[[scc]]
+members = ["pontius.native_simplex_audit_reanalysis"]
+
+[[scc]]
+members = ["pontius.native_simplex_audit_reanalysis_seal"]
+
+[[scc]]
+members = ["pontius.native_simplex_audit_runner"]
+
+[[scc]]
+members = ["pontius.native_simplex_audit_seal"]
+
+[[scc]]
+members = ["pontius.native_simplex_audit_structures"]
+
+[[scc]]
+members = ["pontius.no_limit_betting"]
+
+[[scc]]
+members = ["pontius.occupied_card_quotient"]
+
+[[scc]]
+members = ["pontius.one_seat_convex_generation"]
+
+[[scc]]
+members = ["pontius.one_seat_convex_keystone"]
+
+[[scc]]
+members = ["pontius.one_seat_row_growth_audit"]
+
+[[scc]]
+members = ["pontius.open_mode_audit"]
+
+[[scc]]
+members = ["pontius.open_mode_cfr_bridge"]
+
+[[scc]]
+members = ["pontius.open_mode_factor_tt"]
+
+[[scc]]
+members = ["pontius.open_mode_showdown"]
+
+[[scc]]
+members = ["pontius.opportunity_trace"]
+
+[[scc]]
+members = ["pontius.payoff_semantics"]
+
+[[scc]]
+members = ["pontius.policy"]
+
+[[scc]]
+members = ["pontius.policy_delta_experiment"]
+
+[[scc]]
+members = ["pontius.policy_delta_tt_audit"]
+
+[[scc]]
+members = ["pontius.pre_bet_initial_row_cache"]
+
+[[scc]]
+members = ["pontius.pre_bet_initial_row_cache_v2"]
+
+[[scc]]
+members = ["pontius.profiled_policy_tt"]
+
+[[scc]]
+members = ["pontius.public_node_behavioral_axis"]
+
+[[scc]]
+members = ["pontius.public_node_open_axis"]
+
+[[scc]]
+members = ["pontius.public_policy_tt"]
+
+[[scc]]
+members = ["pontius.public_policy_tt_audit"]
+
+[[scc]]
+members = ["pontius.public_tree_quotient_audit"]
+
+[[scc]]
+members = ["pontius.public_tree_tensor"]
+
+[[scc]]
+members = ["pontius.public_tree_tensor_cfr"]
+
+[[scc]]
+members = ["pontius.real_policy"]
+
+[[scc]]
+members = ["pontius.real_policy_representation_audit"]
+
+[[scc]]
+members = ["pontius.real_policy_representation_audit_v2"]
+
+[[scc]]
+members = ["pontius.real_policy_source"]
+
+[[scc]]
+members = ["pontius.reduced_river_sizing_lp"]
+
+[[scc]]
+members = ["pontius.reduced_river_sizing_oracle"]
+
+[[scc]]
+members = ["pontius.reference_hand_replay"]
+
+[[scc]]
+members = ["pontius.reporting"]
+
+[[scc]]
+members = ["pontius.resident_heterogeneous_leaf_contraction"]
+
+[[scc]]
+members = ["pontius.resident_leaf_adjoint_cfr"]
+
+[[scc]]
+members = ["pontius.resident_leaf_adjoint_evaluation"]
+
+[[scc]]
+members = ["pontius.resident_record_to_hand_fold"]
+
+[[scc]]
+members = ["pontius.resident_record_to_hand_fold_v2"]
+
+[[scc]]
+members = ["pontius.responder_raise_semantics_keystone"]
+
+[[scc]]
+members = ["pontius.responder_raise_semantics_keystone_result"]
+
+[[scc]]
+members = ["pontius.responder_raise_semantics_keystone_result_seal"]
+
+[[scc]]
+members = ["pontius.retrospective_atomic_value_capture"]
+
+[[scc]]
+members = ["pontius.river"]
+
+[[scc]]
+members = ["pontius.river_cache"]
+
+[[scc]]
+members = ["pontius.river_context"]
+
+[[scc]]
+members = ["pontius.river_incremental"]
+
+[[scc]]
+members = ["pontius.river_incremental_experiment"]
+
+[[scc]]
+members = ["pontius.river_multi_size"]
+
+[[scc]]
+members = ["pontius.river_multi_size_audit"]
+
+[[scc]]
+members = ["pontius.river_multi_size_experiment"]
+
+[[scc]]
+members = ["pontius.river_multiway"]
+
+[[scc]]
+members = ["pontius.river_multiway_multi_size"]
+
+[[scc]]
+members = ["pontius.river_noop_full_replication"]
+
+[[scc]]
+members = ["pontius.river_opportunity"]
+
+[[scc]]
+members = ["pontius.river_oracle"]
+
+[[scc]]
+members = ["pontius.river_range_reuse"]
+
+[[scc]]
+members = ["pontius.river_scheduler_holdout"]
+
+[[scc]]
+members = ["pontius.river_scheduler_screen"]
+
+[[scc]]
+members = ["pontius.river_selective"]
+
+[[scc]]
+members = ["pontius.river_selective_analysis"]
+
+[[scc]]
+members = ["pontius.river_selective_experiment"]
+
+[[scc]]
+members = ["pontius.river_selective_payoff_audit"]
+
+[[scc]]
+members = ["pontius.river_selective_screen"]
+
+[[scc]]
+members = ["pontius.river_shadow_probe"]
+
+[[scc]]
+members = ["pontius.river_trace_analysis"]
+
+[[scc]]
+members = ["pontius.river_trace_comparison"]
+
+[[scc]]
+members = ["pontius.runner_harness"]
+
+[[scc]]
+members = ["pontius.runner_harness_v2"]
+
+[[scc]]
+members = ["pontius.safe_composition_experiment"]
+
+[[scc]]
+members = ["pontius.safe_composition_matrix"]
+
+[[scc]]
+members = ["pontius.safe_oracle_experiment"]
+
+[[scc]]
+members = ["pontius.safe_oracle_matrix"]
+
+[[scc]]
+members = ["pontius.safe_resolving"]
+
+[[scc]]
+members = ["pontius.safe_solver_gap_experiment"]
+
+[[scc]]
+members = ["pontius.safe_solver_gap_matrix"]
+
+[[scc]]
+members = ["pontius.seat_order_tt"]
+
+[[scc]]
+members = ["pontius.selection"]
+
+[[scc]]
+members = ["pontius.selective_tree"]
+
+[[scc]]
+members = ["pontius.selector_fan_controls"]
+
+[[scc]]
+members = ["pontius.selector_stable_affine_response"]
+
+[[scc]]
+members = ["pontius.selector_window"]
+
+[[scc]]
+members = ["pontius.selector_window_v2"]
+
+[[scc]]
+members = ["pontius.sequence_form_open_axis"]
+
+[[scc]]
+members = ["pontius.shared_resident_response_context"]
+
+[[scc]]
+members = ["pontius.showdown_value_rank_screen"]
+
+[[scc]]
+members = ["pontius.signed_clean_fringe_audit"]
+
+[[scc]]
+members = ["pontius.signed_clean_fringe_tt"]
+
+[[scc]]
+members = ["pontius.sizing_power_diagnostic"]
+
+[[scc]]
+members = ["pontius.sparse_incidence_audit"]
+
+[[scc]]
+members = ["pontius.sparse_incidence_open_mode"]
+
+[[scc]]
+members = ["pontius.sparse_open_mode_cfr"]
+
+[[scc]]
+members = ["pontius.sparse_open_mode_factor_tt"]
+
+[[scc]]
+members = ["pontius.status_generation"]
+
+[[scc]]
+members = ["pontius.street_deadline"]
+
+[[scc]]
+members = ["pontius.structured_showdown_automaton"]
+
+[[scc]]
+members = ["pontius.structured_showdown_automaton_audit"]
+
+[[scc]]
+members = ["pontius.tensor_train"]
+
+[[scc]]
+members = ["pontius.tensor_train_algebra"]
+
+[[scc]]
+members = ["pontius.terminal_tensor_evaluation"]
+
+[[scc]]
+members = ["pontius.tie_aware_affine_adapter"]
+
+[[scc]]
+members = ["pontius.tie_semantics_conformance"]
+
+[[scc]]
+members = ["pontius.tie_semantics_conformance_v2"]
+
+[[scc]]
+members = ["pontius.unrounded_policy_tt"]
+
+[[scc]]
+members = ["pontius.updates"]
+
+[[scc]]
+members = ["pontius.width_four_sizing_power"]
+
+[[scc]]
+members = ["pontius.width_four_sizing_power_evaluation"]
+
+[[scc]]
+members = ["pontius.windows_process_memory"]
diff --git a/tests/test_stabilization_boundaries.py b/tests/test_stabilization_boundaries.py
new file mode 100644
index 0000000..d736885
--- /dev/null
+++ b/tests/test_stabilization_boundaries.py
@@ -0,0 +1,322 @@
+from __future__ import annotations
+
+from hashlib import sha256
+import importlib.util
+import os
+from pathlib import Path
+import tempfile
+import tomllib
+import unittest
+
+
+REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
+GENERATOR_PATH = REPOSITORY_ROOT / "tools" / "generate_dependency_baseline.py"
+CHECKER_PATH = REPOSITORY_ROOT / "tools" / "check_stabilization_boundaries.py"
+BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
+EDGE_DIGEST = "c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee"
+SCC_DIGEST = "9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345"
+
+
+def _load_exact(name: str, path: Path) -> object:
+    spec = importlib.util.spec_from_file_location(name, path)
+    if spec is None or spec.loader is None:
+        raise RuntimeError(f"could not load {path.name} by exact path")
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+GENERATOR = _load_exact("pontius_dependency_baseline_generator_tests", GENERATOR_PATH)
+CHECKER = _load_exact("pontius_stabilization_boundary_checker_tests", CHECKER_PATH)
+
+
+def _source(text: str) -> bytes:
+    return text.encode("utf-8")
+
+
+def _git_executable() -> Path:
+    configured = os.environ.get("PONTIUS_GIT")
+    if configured is None or not Path(configured).is_absolute():
+        raise RuntimeError("PONTIUS_GIT must name an absolute test Git executable")
+    return Path(configured)
+
+
+class DependencyBaselineTests(unittest.TestCase):
+    def test_exact_baseline_graph_matches_the_approved_mechanical_lock(self) -> None:
+        graph = GENERATOR.derive_baseline_graph(
+            REPOSITORY_ROOT,
+            baseline_commit=BASELINE_COMMIT,
+            git_executable=_git_executable(),
+        )
+
+        self.assertEqual(len(graph.modules), 470)
+        self.assertEqual(len(graph.edges), 2577)
+        self.assertEqual(GENERATOR.edges_sha256(graph.edges), EDGE_DIGEST)
+        self.assertEqual(len(graph.sccs), 469)
+        self.assertEqual(GENERATOR.sccs_sha256(graph.sccs), SCC_DIGEST)
+        self.assertEqual(
+            tuple(component for component in graph.sccs if len(component) > 1),
+            (("pontius.action_clock", "pontius.preparation_bank"),),
+        )
+
+    def test_import_scanner_resolves_absolute_relative_and_type_checking_edges(self) -> None:
+        sources = {
+            "src/pontius/pkg/d.py": _source("VALUE = 1\n"),
+            "src/pontius/a.py": _source(
+                "from typing import TYPE_CHECKING\n"
+                "from . import b\n"
+                "from .pkg import c\n"
+                "import pontius.pkg.d\n"
+                "if TYPE_CHECKING:\n"
+                "    from pontius import e\n"
+            ),
+            "src/pontius/pkg/__init__.py": b"",
+            "src/pontius/e.py": b"",
+            "src/pontius/__init__.py": b"",
+            "src/pontius/pkg/c.py": b"",
+            "src/pontius/b.py": b"",
+        }
+
+        graph = GENERATOR.scan_sources(sources)
+
+        self.assertEqual(
+            graph.modules,
+            (
+                ("pontius.__init__", "src/pontius/__init__.py"),
+                ("pontius.a", "src/pontius/a.py"),
+                ("pontius.b", "src/pontius/b.py"),
+                ("pontius.e", "src/pontius/e.py"),
+                ("pontius.pkg.__init__", "src/pontius/pkg/__init__.py"),
+                ("pontius.pkg.c", "src/pontius/pkg/c.py"),
+                ("pontius.pkg.d", "src/pontius/pkg/d.py"),
+            ),
+        )
+        self.assertEqual(
+            graph.edges,
+            (
+                ("pontius.a", "pontius.b"),
+                ("pontius.a", "pontius.e"),
+                ("pontius.a", "pontius.pkg.c"),
+                ("pontius.a", "pontius.pkg.d"),
+            ),
+        )
+        self.assertEqual(
+            tuple(sorted(member for component in graph.sccs for member in component)),
+            tuple(module_name for module_name, _ in graph.modules),
+        )
+
+    def test_render_and_parse_are_sorted_strict_and_recompute_graph_digests(self) -> None:
+        graph = GENERATOR.scan_sources(
+            {
+                "src/pontius/z.py": _source("from . import a\n"),
+                "src/pontius/__init__.py": b"",
+                "src/pontius/a.py": b"",
+            }
+        )
+
+        raw = GENERATOR.render_baseline(graph, baseline_commit=BASELINE_COMMIT)
+        parsed = GENERATOR.parse_baseline_bytes(raw)
+        decoded = raw.decode("utf-8")
+
+        self.assertEqual(parsed.graph.modules, graph.modules)
+        self.assertEqual(parsed.graph.edges, graph.edges)
+        self.assertEqual(parsed.graph.sccs, graph.sccs)
+        self.assertEqual(parsed.baseline_commit, BASELINE_COMMIT)
+        self.assertLess(
+            decoded.index('module_name = "pontius.__init__"'),
+            decoded.index('module_name = "pontius.a"'),
+        )
+        self.assertLess(
+            decoded.index('module_name = "pontius.a"'),
+            decoded.index('module_name = "pontius.z"'),
+        )
+        self.assertEqual(raw[-1:], b"\n")
+
+        document = tomllib.loads(decoded)
+        wrong_digest = decoded.replace(document["edges_sha256"], "0" * 64, 1).encode()
+        wrong_count = decoded.replace("module_count = 3", "module_count = true", 1).encode()
+        extra_key = raw + b"unexpected = true\n"
+        unsorted = decoded.replace(
+            'module_name = "pontius.__init__"\nrelative_path = "src/pontius/__init__.py"',
+            'module_name = "pontius.zzz"\nrelative_path = "src/pontius/zzz.py"',
+            1,
+        ).encode()
+        for label, candidate in (
+            ("digest", wrong_digest),
+            ("boolean count", wrong_count),
+            ("extra key", extra_key),
+            ("unsorted row", unsorted),
+        ):
+            with self.subTest(label=label), self.assertRaises(GENERATOR.BaselineError):
+                GENERATOR.parse_baseline_bytes(candidate)
+
+    def test_digest_encoding_is_literal_and_order_independent(self) -> None:
+        edges = (("pontius.b", "pontius.c"), ("pontius.a", "pontius.b"))
+        sccs = (("pontius.c",), ("pontius.a", "pontius.b"))
+        expected_edges = sha256(
+            b"pontius.a\tpontius.b\npontius.b\tpontius.c\n"
+        ).hexdigest()
+        expected_sccs = sha256(
+            b"pontius.a\tpontius.b\npontius.c\n"
+        ).hexdigest()
+
+        self.assertEqual(GENERATOR.edges_sha256(edges), expected_edges)
+        self.assertEqual(GENERATOR.sccs_sha256(sccs), expected_sccs)
+
+    def test_generator_defaults_to_check_and_write_is_limited_to_exact_baseline(self) -> None:
+        arguments = GENERATOR.parse_arguments([])
+        self.assertIsNone(arguments.write)
+        self.assertTrue(arguments.check)
+
+        with tempfile.TemporaryDirectory(prefix="pontius-dependency-write-policy-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            expected = architecture / "dependency-baseline.toml"
+            self.assertEqual(
+                GENERATOR.validate_write_destination(root, expected), expected
+            )
+            for candidate in (
+                Path("docs/architecture/dependency-baseline.toml"),
+                root / "dependency-baseline.toml",
+                architecture / "other.toml",
+            ):
+                with self.subTest(candidate=candidate), self.assertRaises(
+                    GENERATOR.BaselineError
+                ):
+                    GENERATOR.validate_write_destination(root, candidate)
+
+    def test_generator_requires_an_explicit_absolute_git_executable(self) -> None:
+        prior = os.environ.pop("PONTIUS_GIT", None)
+        known_git = prior or (
+            "C:/Program Files/Git/cmd/git.exe" if os.name == "nt" else "/usr/bin/git"
+        )
+        try:
+            with self.assertRaises(GENERATOR.BaselineError):
+                GENERATOR.configured_git_executable()
+            os.environ["PONTIUS_GIT"] = "git"
+            with self.assertRaises(GENERATOR.BaselineError):
+                GENERATOR.configured_git_executable()
+            os.environ["PONTIUS_GIT"] = known_git
+            self.assertTrue(GENERATOR.configured_git_executable().is_absolute())
+        finally:
+            if prior is None:
+                os.environ.pop("PONTIUS_GIT", None)
+            else:
+                os.environ["PONTIUS_GIT"] = prior
+
+
+class StabilizationPolicyTests(unittest.TestCase):
+    def test_only_plan_declared_stabilization_origins_are_classified(self) -> None:
+        CHECKER.enforce_origin_classification(
+            {
+                "src/pontius/evidence/__init__.py": b"",
+                "src/pontius/evidence/authorization.py": b"",
+            },
+            {
+                "tools/run_tests.py": b"",
+                "tools/test_orchestration/model.py": b"",
+            },
+        )
+
+        with self.assertRaises(CHECKER.BoundaryError) as caught:
+            CHECKER.enforce_origin_classification(
+                {"src/pontius/evidence/unplanned.py": b""},
+                {"tools/unplanned_runner.py": b""},
+            )
+
+        self.assertIn(
+            "unclassified stabilization origin: src/pontius/evidence/unplanned.py",
+            str(caught.exception),
+        )
+        self.assertIn(
+            "unclassified stabilization origin: tools/unplanned_runner.py",
+            str(caught.exception),
+        )
+
+    def test_untouched_legacy_outgoing_edge_change_is_rejected(self) -> None:
+        baseline = GENERATOR.scan_sources(
+            {
+                "src/pontius/__init__.py": b"",
+                "src/pontius/a.py": _source("from . import b\n"),
+                "src/pontius/b.py": b"",
+                "src/pontius/c.py": b"",
+            }
+        )
+        current = GENERATOR.scan_sources(
+            {
+                "src/pontius/__init__.py": b"",
+                "src/pontius/a.py": _source("from . import c\n"),
+                "src/pontius/b.py": b"",
+                "src/pontius/c.py": b"",
+            }
+        )
+
+        with self.assertRaises(CHECKER.BoundaryError) as caught:
+            CHECKER.enforce_legacy_edges(baseline, current)
+
+        self.assertIn("pontius.a", str(caught.exception))
+        self.assertIn("pontius.a -> pontius.b", str(caught.exception))
+        self.assertIn("pontius.a -> pontius.c", str(caught.exception))
+
+    def test_evidence_origins_allow_only_siblings_and_durable_journal(self) -> None:
+        allowed = {
+            "src/pontius/__init__.py": b"",
+            "src/pontius/durable_evidence_journal.py": b"",
+            "src/pontius/evidence/__init__.py": b"",
+            "src/pontius/evidence/errors.py": _source("import pathlib\n"),
+            "src/pontius/evidence/good.py": _source(
+                "from . import errors\n"
+                "from pontius import durable_evidence_journal\n"
+            ),
+        }
+        CHECKER.enforce_evidence_import_policy(allowed)
+
+        denied = dict(allowed)
+        denied[
+            "src/pontius/"
+            "legal_river_quotient_compiled_global_separation_calibration_v7_result.py"
+        ] = b""
+        denied["src/pontius/evidence/bad.py"] = _source(
+            "from pontius import "
+            "legal_river_quotient_compiled_global_separation_calibration_v7_result\n"
+            "import cupy\n"
+            "import tests.fixture\n"
+        )
+        with self.assertRaises(CHECKER.BoundaryError) as caught:
+            CHECKER.enforce_evidence_import_policy(denied)
+
+        message = str(caught.exception)
+        self.assertIn(
+            "pontius.evidence.bad -> "
+            "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_result",
+            message,
+        )
+        self.assertIn("pontius.evidence.bad -> cupy", message)
+        self.assertIn("pontius.evidence.bad -> tests.fixture", message)
+
+    def test_new_or_expanded_internal_cycle_is_rejected(self) -> None:
+        baseline = GENERATOR.scan_sources(
+            {
+                "src/pontius/__init__.py": b"",
+                "src/pontius/a.py": _source("from . import b\n"),
+                "src/pontius/b.py": _source("from . import a\n"),
+            }
+        )
+        current = GENERATOR.scan_sources(
+            {
+                "src/pontius/__init__.py": b"",
+                "src/pontius/a.py": _source("from . import b\nfrom . import c\n"),
+                "src/pontius/b.py": _source("from . import a\n"),
+                "src/pontius/c.py": _source("from . import a\n"),
+            }
+        )
+
+        with self.assertRaises(CHECKER.BoundaryError) as caught:
+            CHECKER.enforce_no_new_or_expanded_scc(baseline, current)
+
+        self.assertIn("pontius.a, pontius.b, pontius.c", str(caught.exception))
+
+
+if __name__ == "__main__":
+    unittest.main(verbosity=2)
diff --git a/tests/test_test_orchestration_import_boundary.py b/tests/test_test_orchestration_import_boundary.py
new file mode 100644
index 0000000..005d71b
--- /dev/null
+++ b/tests/test_test_orchestration_import_boundary.py
@@ -0,0 +1,83 @@
+from __future__ import annotations
+
+import importlib.util
+from pathlib import Path
+import unittest
+
+
+REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
+CHECKER_PATH = REPOSITORY_ROOT / "tools" / "check_stabilization_boundaries.py"
+
+
+def _load_checker() -> object:
+    spec = importlib.util.spec_from_file_location(
+        "pontius_orchestration_import_checker_tests", CHECKER_PATH
+    )
+    if spec is None or spec.loader is None:
+        raise RuntimeError("boundary checker could not be loaded by exact path")
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+CHECKER = _load_checker()
+
+
+class OrchestrationImportPolicyTests(unittest.TestCase):
+    def test_orchestration_origins_allow_standard_library_and_siblings(self) -> None:
+        sources = {
+            "tools/run_tests.py": (
+                b"import argparse\n"
+                b"from tools.test_orchestration import configuration\n"
+            ),
+            "tools/test_orchestration/__init__.py": b"",
+            "tools/test_orchestration/configuration.py": b"import tomllib\n",
+            "tools/generate_dependency_baseline.py": b"import ast\n",
+            "tools/check_stabilization_boundaries.py": b"import pathlib\n",
+        }
+
+        CHECKER.enforce_orchestration_import_policy(sources)
+
+    def test_parent_forbidden_imports_report_every_exact_edge(self) -> None:
+        sources = {
+            "tools/run_tests.py": (
+                b"import pontius\n"
+                b"import tests.helper\n"
+                b"import experiments.owner\n"
+                b"import cupy\n"
+                b"from pontius import "
+                b"legal_river_quotient_compiled_global_separation_calibration_v7_runner\n"
+            ),
+        }
+
+        with self.assertRaises(CHECKER.BoundaryError) as caught:
+            CHECKER.enforce_orchestration_import_policy(sources)
+
+        message = str(caught.exception)
+        for target in (
+            "pontius",
+            "tests.helper",
+            "experiments.owner",
+            "cupy",
+            "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_runner",
+        ):
+            with self.subTest(target=target):
+                self.assertIn(f"tools.run_tests -> {target}", message)
+
+    def test_non_orchestration_tools_do_not_gain_a_sibling_exemption(self) -> None:
+        sources = {
+            "tools/generate_dependency_baseline.py": b"import tools.unreviewed_helper\n",
+            "tools/unreviewed_helper.py": b"",
+        }
+
+        with self.assertRaises(CHECKER.BoundaryError) as caught:
+            CHECKER.enforce_orchestration_import_policy(sources)
+
+        self.assertIn(
+            "tools.generate_dependency_baseline -> tools.unreviewed_helper",
+            str(caught.exception),
+        )
+
+
+if __name__ == "__main__":
+    unittest.main(verbosity=2)
diff --git a/tools/check_stabilization_boundaries.py b/tools/check_stabilization_boundaries.py
new file mode 100644
index 0000000..cf610fd
--- /dev/null
+++ b/tools/check_stabilization_boundaries.py
@@ -0,0 +1,281 @@
+"""Check legacy dependency drift and stabilization import boundaries."""
+
+from __future__ import annotations
+
+import argparse
+from collections.abc import Mapping, Sequence
+import importlib.util
+import os
+from pathlib import Path
+import stat
+import sys
+from types import ModuleType
+
+
+BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
+_ORCHESTRATION_SIBLING_PREFIX = "tools.test_orchestration"
+EVIDENCE_ORIGIN_PATHS = frozenset(
+    {
+        "src/pontius/evidence/__init__.py",
+        "src/pontius/evidence/authorization.py",
+        "src/pontius/evidence/errors.py",
+        "src/pontius/evidence/manifest.py",
+        "src/pontius/evidence/model.py",
+        "src/pontius/evidence/retained_v7.py",
+    }
+)
+ORCHESTRATION_ORIGIN_PATHS = frozenset(
+    {
+        "tools/__init__.py",
+        "tools/check_stabilization_boundaries.py",
+        "tools/compare_run_summaries.py",
+        "tools/generate_dependency_baseline.py",
+        "tools/generate_evidence_manifests.py",
+        "tools/generate_test_inventory.py",
+        "tools/run_tests.py",
+        "tools/stabilization_verification.py",
+        "tools/test_child.py",
+        "tools/test_orchestration/__init__.py",
+        "tools/test_orchestration/configuration.py",
+        "tools/test_orchestration/engine.py",
+        "tools/test_orchestration/environment.py",
+        "tools/test_orchestration/errors.py",
+        "tools/test_orchestration/evidence_guard.py",
+        "tools/test_orchestration/git.py",
+        "tools/test_orchestration/model.py",
+        "tools/test_orchestration/posix_group.py",
+        "tools/test_orchestration/process.py",
+        "tools/test_orchestration/protocol.py",
+        "tools/test_orchestration/windows_job.py",
+        "tools/test_orchestration/workspace.py",
+    }
+)
+
+
+class BoundaryError(RuntimeError):
+    """One or more deterministic architecture-boundary violations."""
+
+    def __init__(self, violations: Sequence[str] | str) -> None:
+        if isinstance(violations, str):
+            normalized = (violations,)
+        else:
+            normalized = tuple(sorted(set(violations)))
+        if not normalized:
+            raise ValueError("a boundary error requires at least one violation")
+        self.violations = normalized
+        super().__init__("; ".join(normalized))
+
+
+def _load_generator() -> ModuleType:
+    path = Path(__file__).resolve().with_name("generate_dependency_baseline.py")
+    spec = importlib.util.spec_from_file_location("_pontius_dependency_baseline", path)
+    if spec is None or spec.loader is None:
+        raise BoundaryError("dependency baseline implementation cannot be loaded")
+    module = importlib.util.module_from_spec(spec)
+    try:
+        spec.loader.exec_module(module)
+    except (OSError, ImportError) as error:
+        raise BoundaryError("dependency baseline implementation cannot be loaded") from error
+    return module
+
+
+_BASELINE = _load_generator()
+
+
+def _raise_violations(violations: Sequence[str]) -> None:
+    if violations:
+        raise BoundaryError(violations)
+
+
+def enforce_legacy_edges(baseline: object, current: object) -> None:
+    """Require every mechanically grandfathered origin to retain its edge set."""
+
+    baseline_modules = {name for name, _ in baseline.modules}
+    current_modules = {name for name, _ in current.modules}
+    baseline_edges = {name: set() for name in baseline_modules}
+    current_edges = {name: set() for name in current_modules}
+    for origin, target in baseline.edges:
+        baseline_edges[origin].add(target)
+    for origin, target in current.edges:
+        current_edges[origin].add(target)
+    violations: list[str] = []
+    for missing in sorted(baseline_modules - current_modules):
+        violations.append(f"legacy module is missing: {missing}")
+    for added in sorted(current_modules - baseline_modules):
+        if added != "pontius.evidence" and not added.startswith("pontius.evidence."):
+            violations.append(f"new source module lacks stabilization classification: {added}")
+    for origin in sorted(baseline_modules & current_modules):
+        removed = baseline_edges[origin] - current_edges[origin]
+        added = current_edges[origin] - baseline_edges[origin]
+        if removed or added:
+            detail = [f"legacy outgoing edges changed for {origin}"]
+            detail.extend(f"removed {origin} -> {target}" for target in sorted(removed))
+            detail.extend(f"added {origin} -> {target}" for target in sorted(added))
+            violations.append(", ".join(detail))
+    _raise_violations(violations)
+
+
+def _cyclic_components(graph: object) -> set[tuple[str, ...]]:
+    self_edges = {origin for origin, target in graph.edges if origin == target}
+    return {
+        tuple(component)
+        for component in graph.sccs
+        if len(component) > 1 or component[0] in self_edges
+    }
+
+
+def enforce_no_new_or_expanded_scc(baseline: object, current: object) -> None:
+    allowed = _cyclic_components(baseline)
+    violations = []
+    for component in sorted(_cyclic_components(current)):
+        if component not in allowed:
+            violations.append(
+                "new or expanded internal SCC: " + ", ".join(component)
+            )
+    _raise_violations(violations)
+
+
+def _is_stdlib(target: str) -> bool:
+    root = target.partition(".")[0]
+    return root in sys.stdlib_module_names or root == "__future__"
+
+
+def enforce_origin_classification(
+    current_sources: Mapping[str, bytes], tool_sources: Mapping[str, bytes]
+) -> None:
+    """Reject stabilization origins that neither accepted plan declares."""
+
+    violations = [
+        f"unclassified stabilization origin: {path}"
+        for path in sorted(current_sources)
+        if path.startswith("src/pontius/evidence/") and path not in EVIDENCE_ORIGIN_PATHS
+    ]
+    violations.extend(
+        f"unclassified stabilization origin: {path}"
+        for path in sorted(tool_sources)
+        if path.startswith("tools/") and path not in ORCHESTRATION_ORIGIN_PATHS
+    )
+    _raise_violations(violations)
+
+
+def enforce_evidence_import_policy(sources: Mapping[str, bytes]) -> None:
+    """Apply the exact active-evidence dependency allowlist."""
+
+    violations: list[str] = []
+    try:
+        edges = _BASELINE.import_edges(sources)
+    except _BASELINE.BaselineError as error:
+        raise BoundaryError(f"evidence sources cannot be scanned: {error}") from error
+    for origin, target in edges:
+        if origin != "pontius.evidence" and not origin.startswith("pontius.evidence."):
+            continue
+        allowed = (
+            _is_stdlib(target)
+            or target == "pontius.durable_evidence_journal"
+            or target == "pontius.evidence"
+            or target.startswith("pontius.evidence.")
+        )
+        if not allowed:
+            violations.append(f"forbidden evidence import: {origin} -> {target}")
+    _raise_violations(violations)
+
+
+def enforce_orchestration_import_policy(sources: Mapping[str, bytes]) -> None:
+    """Keep orchestration tools on the standard library and declared siblings."""
+
+    violations: list[str] = []
+    try:
+        edges = _BASELINE.import_edges(sources)
+    except _BASELINE.BaselineError as error:
+        raise BoundaryError(f"orchestration sources cannot be scanned: {error}") from error
+    for origin, target in edges:
+        if not origin.startswith("tools"):
+            continue
+        sibling = target == _ORCHESTRATION_SIBLING_PREFIX or target.startswith(
+            _ORCHESTRATION_SIBLING_PREFIX + "."
+        )
+        if not _is_stdlib(target) and not sibling:
+            violations.append(f"forbidden orchestration import: {origin} -> {target}")
+    _raise_violations(violations)
+
+
+def _is_reparse(info: os.stat_result) -> bool:
+    return bool(getattr(info, "st_file_attributes", 0) & 0x400)
+
+
+def _read_regular_source(path: Path, *, root: Path) -> bytes:
+    try:
+        info = os.lstat(path)
+    except OSError as error:
+        raise BoundaryError(f"Python source cannot be inspected: {path}") from error
+    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
+        raise BoundaryError(f"Python source is not a regular nonreparse file: {path}")
+    try:
+        relative = path.relative_to(root).as_posix()
+        raw = path.read_bytes()
+    except (OSError, ValueError) as error:
+        raise BoundaryError(
+            f"Python source cannot be read below repository root: {path}"
+        ) from error
+    if len(raw) != info.st_size:
+        raise BoundaryError(f"Python source changed while reading: {relative}")
+    return raw
+
+
+def _collect_sources(repository_root: Path, relative_root: str) -> dict[str, bytes]:
+    base = repository_root / relative_root
+    if not base.exists():
+        return {}
+    sources: dict[str, bytes] = {}
+    for path in sorted(base.rglob("*.py")):
+        relative = path.relative_to(repository_root).as_posix()
+        sources[relative] = _read_regular_source(path, root=repository_root)
+    return sources
+
+
+def check_repository(repository_root: Path) -> None:
+    try:
+        root = repository_root.resolve(strict=True)
+    except OSError as error:
+        raise BoundaryError("repository root cannot be resolved") from error
+    baseline_path = root / BASELINE_RELATIVE_PATH
+    try:
+        baseline_raw = _BASELINE._validated_regular_file(
+            baseline_path, maximum_bytes=_BASELINE.MAXIMUM_BASELINE_BYTES
+        )
+        parsed = _BASELINE.parse_baseline_bytes(baseline_raw)
+    except _BASELINE.BaselineError as error:
+        raise BoundaryError(f"dependency baseline cannot be loaded: {error}") from error
+    if parsed.baseline_commit != _BASELINE.BASELINE_COMMIT:
+        raise BoundaryError("dependency baseline commit differs from stabilization baseline")
+    current_sources = _collect_sources(root, "src/pontius")
+    tool_sources = _collect_sources(root, "tools")
+    try:
+        current_graph = _BASELINE.scan_sources(current_sources)
+    except _BASELINE.BaselineError as error:
+        raise BoundaryError(f"current dependency graph cannot be derived: {error}") from error
+    enforce_origin_classification(current_sources, tool_sources)
+    enforce_legacy_edges(parsed.graph, current_graph)
+    enforce_no_new_or_expanded_scc(parsed.graph, current_graph)
+    enforce_evidence_import_policy(current_sources)
+    enforce_orchestration_import_policy(tool_sources)
+
+
+def parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
+    parser = argparse.ArgumentParser(description=__doc__)
+    return parser.parse_args(argv)
+
+
+def main(argv: Sequence[str] | None = None) -> int:
+    parse_arguments(argv)
+    repository_root = Path(__file__).resolve().parents[1]
+    try:
+        check_repository(repository_root)
+    except BoundaryError as error:
+        print(f"stabilization boundary check failed: {error}", file=sys.stderr)
+        return 2
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/tools/generate_dependency_baseline.py b/tools/generate_dependency_baseline.py
new file mode 100644
index 0000000..c707b9b
--- /dev/null
+++ b/tools/generate_dependency_baseline.py
@@ -0,0 +1,793 @@
+"""Generate and verify the mechanical legacy Python dependency baseline.
+
+This tool is standard-library-only.  It reads Python source from an exact Git
+commit, parses imports with :mod:`ast`, and emits a canonical TOML lock.
+"""
+
+from __future__ import annotations
+
+import argparse
+import ast
+from collections.abc import Mapping, Sequence
+from hashlib import sha256
+import io
+import json
+import os
+from pathlib import Path, PurePosixPath, PureWindowsPath
+import re
+import stat
+import subprocess
+import sys
+import tarfile
+import tempfile
+import tomllib
+from typing import Any
+import uuid
+
+
+SCHEMA_VERSION = "pontius-dependency-baseline-v1"
+BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
+BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
+MAXIMUM_ARCHIVE_BYTES = 64 * 1024 * 1024
+MAXIMUM_BASELINE_BYTES = 4 * 1024 * 1024
+_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
+_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
+
+
+class BaselineError(RuntimeError):
+    """A deterministic dependency-baseline failure."""
+
+
+class DependencyGraph:
+    """Canonical module, internal-edge, and SCC rows."""
+
+    __slots__ = ("modules", "edges", "sccs")
+
+    def __init__(
+        self,
+        modules: Sequence[tuple[str, str]],
+        edges: Sequence[tuple[str, str]],
+        sccs: Sequence[Sequence[str]],
+    ) -> None:
+        self.modules = tuple((name, path) for name, path in modules)
+        self.edges = tuple((origin, target) for origin, target in edges)
+        self.sccs = tuple(tuple(component) for component in sccs)
+
+
+class ParsedBaseline:
+    """Validated baseline metadata and graph."""
+
+    __slots__ = ("baseline_commit", "graph")
+
+    def __init__(self, baseline_commit: str, graph: DependencyGraph) -> None:
+        self.baseline_commit = baseline_commit
+        self.graph = graph
+
+
+def _require_exact_string(value: object, *, field: str) -> str:
+    if type(value) is not str or not value:
+        raise BaselineError(f"{field} must be a nonempty string")
+    return value
+
+
+def _require_exact_integer(value: object, *, field: str) -> int:
+    if type(value) is not int or value < 0:
+        raise BaselineError(f"{field} must be an exact nonnegative integer")
+    return value
+
+
+def _require_commit(value: object, *, field: str = "baseline_commit") -> str:
+    text = _require_exact_string(value, field=field)
+    if _HEX40.fullmatch(text) is None:
+        raise BaselineError(f"{field} must be lowercase 40-hex")
+    return text
+
+
+def _require_digest(value: object, *, field: str) -> str:
+    text = _require_exact_string(value, field=field)
+    if _HEX64.fullmatch(text) is None:
+        raise BaselineError(f"{field} must be lowercase 64-hex")
+    return text
+
+
+def _normalized_relative_path(value: object, *, field: str) -> str:
+    text = _require_exact_string(value, field=field)
+    if "\\" in text or "\x00" in text or "\r" in text or "\n" in text:
+        raise BaselineError(f"{field} is not a normalized repository-relative path")
+    posix = PurePosixPath(text)
+    windows = PureWindowsPath(text)
+    if (
+        posix.is_absolute()
+        or windows.is_absolute()
+        or windows.drive
+        or text != posix.as_posix()
+        or any(part in {"", ".", ".."} for part in posix.parts)
+    ):
+        raise BaselineError(f"{field} is not a normalized repository-relative path")
+    return text
+
+
+def module_name_for_path(relative_path: str) -> str:
+    """Return the import name represented by a Python repository path."""
+
+    normalized = _normalized_relative_path(relative_path, field="relative_path")
+    path = PurePosixPath(normalized)
+    if path.suffix != ".py":
+        raise BaselineError(f"Python source path does not end in .py: {normalized}")
+    parts = list(path.parts)
+    if len(parts) >= 3 and parts[:2] == ["src", "pontius"]:
+        module_parts = parts[1:]
+    elif len(parts) >= 2 and parts[0] in {"tools", "tests"}:
+        module_parts = parts
+    else:
+        raise BaselineError(f"Python source path has no supported module root: {normalized}")
+    filename = module_parts[-1]
+    module_parts[-1] = filename[:-3]
+    if not module_parts or any(not part.isidentifier() for part in module_parts):
+        raise BaselineError(f"Python source path has an invalid module name: {normalized}")
+    return ".".join(module_parts)
+
+
+def _is_package_path(relative_path: str) -> bool:
+    return PurePosixPath(relative_path).name == "__init__.py"
+
+
+def _package_import_name(module_name: str) -> str:
+    if module_name.endswith(".__init__"):
+        return module_name.removesuffix(".__init__")
+    return module_name
+
+
+def _resolve_from_base(
+    origin: str,
+    *,
+    is_package: bool,
+    level: int,
+    imported_module: str | None,
+) -> str:
+    if level == 0:
+        return imported_module or ""
+    normalized_origin = _package_import_name(origin)
+    package_parts = (
+        normalized_origin.split(".")
+        if is_package
+        else normalized_origin.split(".")[:-1]
+    )
+    ascend = level - 1
+    if ascend > len(package_parts):
+        return ""
+    base_parts = package_parts[: len(package_parts) - ascend]
+    if imported_module:
+        base_parts.extend(imported_module.split("."))
+    return ".".join(base_parts)
+
+
+def _longest_module_prefix(name: str, module_names: set[str]) -> str | None:
+    candidate = name
+    while candidate:
+        if candidate in module_names:
+            return candidate
+        package_candidate = candidate + ".__init__"
+        if package_candidate in module_names:
+            return package_candidate
+        candidate = candidate.rpartition(".")[0]
+    return None
+
+
+def _import_targets(
+    tree: ast.AST,
+    *,
+    origin: str,
+    is_package: bool,
+    module_names: set[str],
+    internal_only: bool,
+) -> tuple[str, ...]:
+    targets: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Import):
+            for alias in node.names:
+                if internal_only:
+                    resolved = _longest_module_prefix(alias.name, module_names)
+                    if resolved is not None:
+                        targets.add(resolved)
+                else:
+                    targets.add(alias.name)
+        elif isinstance(node, ast.ImportFrom):
+            base = _resolve_from_base(
+                origin,
+                is_package=is_package,
+                level=node.level,
+                imported_module=node.module,
+            )
+            for alias in node.names:
+                candidate = f"{base}.{alias.name}" if base and alias.name != "*" else base
+                resolved = _longest_module_prefix(candidate, module_names)
+                if resolved is None:
+                    resolved = _longest_module_prefix(base, module_names)
+                if internal_only:
+                    if resolved is not None:
+                        targets.add(resolved)
+                else:
+                    repository_namespace_root = base in {
+                        "pontius",
+                        "tests",
+                        "experiments",
+                        "tools",
+                    }
+                    targets.add(
+                        resolved
+                        or (
+                            candidate
+                            if repository_namespace_root and alias.name != "*"
+                            else base
+                        )
+                        or candidate
+                    )
+    targets.discard("")
+    return tuple(sorted(targets))
+
+
+def _parse_source(raw: bytes, *, relative_path: str) -> ast.AST:
+    if type(raw) is not bytes:
+        raise BaselineError(f"source bytes are not bytes: {relative_path}")
+    try:
+        return ast.parse(raw, filename=relative_path)
+    except (SyntaxError, ValueError) as error:
+        raise BaselineError(f"Python source cannot be parsed: {relative_path}") from error
+
+
+def import_edges(sources: Mapping[str, bytes]) -> tuple[tuple[str, str], ...]:
+    """Return all syntactic import edges for policy checks.
+
+    Internal imports are resolved to the most specific repository module.  Other
+    imports retain their syntactic module name.  Imports beneath ``TYPE_CHECKING``
+    are intentionally included because the scanner walks the complete AST.
+    """
+
+    module_by_path: dict[str, str] = {}
+    for supplied_path in sources:
+        path = _normalized_relative_path(supplied_path, field="source path")
+        module_by_path[path] = module_name_for_path(path)
+    if len(set(module_by_path.values())) != len(module_by_path):
+        raise BaselineError("multiple Python paths resolve to one module")
+    module_names = set(module_by_path.values())
+    edges: set[tuple[str, str]] = set()
+    for path, origin in sorted(module_by_path.items()):
+        tree = _parse_source(sources[path], relative_path=path)
+        for target in _import_targets(
+            tree,
+            origin=origin,
+            is_package=_is_package_path(path),
+            module_names=module_names,
+            internal_only=False,
+        ):
+            edges.add((origin, target))
+    return tuple(sorted(edges))
+
+
+def _strongly_connected_components(
+    module_names: Sequence[str], edges: Sequence[tuple[str, str]]
+) -> tuple[tuple[str, ...], ...]:
+    adjacency = {name: [] for name in module_names}
+    for origin, target in edges:
+        adjacency[origin].append(target)
+    for targets in adjacency.values():
+        targets.sort()
+
+    index = 0
+    indices: dict[str, int] = {}
+    lowlinks: dict[str, int] = {}
+    stack: list[str] = []
+    on_stack: set[str] = set()
+    components: list[tuple[str, ...]] = []
+
+    def visit(node: str) -> None:
+        nonlocal index
+        indices[node] = index
+        lowlinks[node] = index
+        index += 1
+        stack.append(node)
+        on_stack.add(node)
+        for target in adjacency[node]:
+            if target not in indices:
+                visit(target)
+                lowlinks[node] = min(lowlinks[node], lowlinks[target])
+            elif target in on_stack:
+                lowlinks[node] = min(lowlinks[node], indices[target])
+        if lowlinks[node] == indices[node]:
+            members: list[str] = []
+            while True:
+                member = stack.pop()
+                on_stack.remove(member)
+                members.append(member)
+                if member == node:
+                    break
+            components.append(tuple(sorted(members)))
+
+    for module_name in sorted(module_names):
+        if module_name not in indices:
+            visit(module_name)
+    return tuple(sorted(components))
+
+
+def scan_sources(sources: Mapping[str, bytes]) -> DependencyGraph:
+    """Build the canonical internal ``pontius`` import graph from source bytes."""
+
+    if not isinstance(sources, Mapping) or not sources:
+        raise BaselineError("dependency source mapping must be nonempty")
+    modules: list[tuple[str, str]] = []
+    normalized_sources: dict[str, bytes] = {}
+    for supplied_path, raw in sources.items():
+        path = _normalized_relative_path(supplied_path, field="source path")
+        module_name = module_name_for_path(path)
+        if not module_name.startswith("pontius"):
+            raise BaselineError(f"dependency graph source is outside pontius: {path}")
+        if path in normalized_sources:
+            raise BaselineError(f"duplicate dependency source path: {path}")
+        normalized_sources[path] = raw
+        modules.append((module_name, path))
+    modules.sort()
+    if len({name for name, _ in modules}) != len(modules):
+        raise BaselineError("multiple dependency paths resolve to one module")
+    module_names = {name for name, _ in modules}
+    edges: set[tuple[str, str]] = set()
+    for origin, path in modules:
+        tree = _parse_source(normalized_sources[path], relative_path=path)
+        for target in _import_targets(
+            tree,
+            origin=origin,
+            is_package=_is_package_path(path),
+            module_names=module_names,
+            internal_only=True,
+        ):
+            edges.add((origin, target))
+    ordered_edges = tuple(sorted(edges))
+    sccs = _strongly_connected_components(
+        tuple(name for name, _ in modules), ordered_edges
+    )
+    return DependencyGraph(tuple(modules), ordered_edges, sccs)
+
+
+def edges_sha256(edges: Sequence[tuple[str, str]]) -> str:
+    rows = sorted(set(tuple(edge) for edge in edges))
+    raw = "".join(f"{origin}\t{target}\n" for origin, target in rows).encode("ascii")
+    return sha256(raw).hexdigest()
+
+
+def sccs_sha256(sccs: Sequence[Sequence[str]]) -> str:
+    rows = sorted(tuple(sorted(component)) for component in sccs)
+    raw = "".join("\t".join(component) + "\n" for component in rows).encode("ascii")
+    return sha256(raw).hexdigest()
+
+
+def _toml_string(value: str) -> str:
+    return json.dumps(value, ensure_ascii=True)
+
+
+def render_baseline(graph: DependencyGraph, *, baseline_commit: str) -> bytes:
+    commit = _require_commit(baseline_commit)
+    _validate_graph(graph)
+    lines = [
+        f"schema_version = {_toml_string(SCHEMA_VERSION)}",
+        f"baseline_commit = {_toml_string(commit)}",
+        f"module_count = {len(graph.modules)}",
+        f"edge_count = {len(graph.edges)}",
+        f"edges_sha256 = {_toml_string(edges_sha256(graph.edges))}",
+        f"scc_count = {len(graph.sccs)}",
+        f"sccs_sha256 = {_toml_string(sccs_sha256(graph.sccs))}",
+    ]
+    for module_name, relative_path in graph.modules:
+        lines.extend(
+            (
+                "",
+                "[[module]]",
+                f"module_name = {_toml_string(module_name)}",
+                f"relative_path = {_toml_string(relative_path)}",
+            )
+        )
+    for origin, target in graph.edges:
+        lines.extend(
+            (
+                "",
+                "[[edge]]",
+                f"origin = {_toml_string(origin)}",
+                f"target = {_toml_string(target)}",
+            )
+        )
+    for component in graph.sccs:
+        members = ", ".join(_toml_string(member) for member in component)
+        lines.extend(("", "[[scc]]", f"members = [{members}]"))
+    return ("\n".join(lines) + "\n").encode("utf-8")
+
+
+def _exact_keys(value: object, expected: set[str], *, field: str) -> Mapping[str, Any]:
+    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
+        raise BaselineError(f"{field} must be a TOML table")
+    actual = set(value)
+    if actual != expected:
+        missing = sorted(expected - actual)
+        extra = sorted(actual - expected)
+        raise BaselineError(f"{field} keys differ: missing={missing}, extra={extra}")
+    return value
+
+
+def _table_array(value: object, *, field: str) -> list[object]:
+    if type(value) is not list:
+        raise BaselineError(f"{field} must be a TOML table array")
+    return value
+
+
+def _module_name(value: object, *, field: str) -> str:
+    text = _require_exact_string(value, field=field)
+    if any(not part.isidentifier() for part in text.split(".")) or not text.startswith(
+        "pontius"
+    ):
+        raise BaselineError(f"{field} is not a valid pontius module name")
+    return text
+
+
+def _validate_graph(graph: DependencyGraph) -> None:
+    modules = tuple(graph.modules)
+    edges = tuple(graph.edges)
+    sccs = tuple(tuple(component) for component in graph.sccs)
+    if modules != tuple(sorted(modules)) or len(set(modules)) != len(modules):
+        raise BaselineError("module rows must be sorted and unique")
+    names: list[str] = []
+    paths: list[str] = []
+    for module_name, relative_path in modules:
+        name = _module_name(module_name, field="module.module_name")
+        path = _normalized_relative_path(relative_path, field="module.relative_path")
+        if module_name_for_path(path) != name:
+            raise BaselineError("module name does not match its repository path")
+        names.append(name)
+        paths.append(path)
+    if len(set(names)) != len(names) or len(set(paths)) != len(paths):
+        raise BaselineError("module names and paths must each be unique")
+    name_set = set(names)
+    if edges != tuple(sorted(edges)) or len(set(edges)) != len(edges):
+        raise BaselineError("edge rows must be sorted and unique")
+    for origin, target in edges:
+        if origin not in name_set or target not in name_set:
+            raise BaselineError("every edge endpoint must resolve to one module")
+    normalized_sccs = tuple(tuple(component) for component in sccs)
+    if normalized_sccs != tuple(sorted(normalized_sccs)) or len(set(normalized_sccs)) != len(
+        normalized_sccs
+    ):
+        raise BaselineError("SCC rows must be sorted and unique")
+    flattened: list[str] = []
+    for component in normalized_sccs:
+        if not component or component != tuple(sorted(component)) or len(set(component)) != len(
+            component
+        ):
+            raise BaselineError("SCC members must be sorted, nonempty, and unique")
+        if any(member not in name_set for member in component):
+            raise BaselineError("every SCC member must resolve to one module")
+        flattened.extend(component)
+    if sorted(flattened) != sorted(names) or len(flattened) != len(names):
+        raise BaselineError("every module must occur in exactly one SCC")
+    computed = _strongly_connected_components(tuple(names), edges)
+    if computed != normalized_sccs:
+        raise BaselineError("SCC rows do not match the encoded edge graph")
+
+
+def parse_baseline_bytes(raw: bytes) -> ParsedBaseline:
+    if type(raw) is not bytes or len(raw) > MAXIMUM_BASELINE_BYTES:
+        raise BaselineError("dependency baseline bytes are invalid or oversized")
+    try:
+        decoded = raw.decode("utf-8")
+        document = tomllib.loads(decoded)
+    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
+        raise BaselineError("dependency baseline is not valid UTF-8 TOML") from error
+    top = _exact_keys(
+        document,
+        {
+            "schema_version",
+            "baseline_commit",
+            "module_count",
+            "edge_count",
+            "edges_sha256",
+            "scc_count",
+            "sccs_sha256",
+            "module",
+            "edge",
+            "scc",
+        },
+        field="dependency baseline",
+    )
+    if _require_exact_string(top["schema_version"], field="schema_version") != SCHEMA_VERSION:
+        raise BaselineError("dependency baseline schema version is unsupported")
+    commit = _require_commit(top["baseline_commit"])
+    module_count = _require_exact_integer(top["module_count"], field="module_count")
+    edge_count = _require_exact_integer(top["edge_count"], field="edge_count")
+    scc_count = _require_exact_integer(top["scc_count"], field="scc_count")
+    expected_edge_digest = _require_digest(top["edges_sha256"], field="edges_sha256")
+    expected_scc_digest = _require_digest(top["sccs_sha256"], field="sccs_sha256")
+
+    modules: list[tuple[str, str]] = []
+    for index, value in enumerate(_table_array(top["module"], field="module")):
+        row = _exact_keys(value, {"module_name", "relative_path"}, field=f"module[{index}]")
+        modules.append(
+            (
+                _module_name(row["module_name"], field=f"module[{index}].module_name"),
+                _normalized_relative_path(
+                    row["relative_path"], field=f"module[{index}].relative_path"
+                ),
+            )
+        )
+    edges: list[tuple[str, str]] = []
+    for index, value in enumerate(_table_array(top["edge"], field="edge")):
+        row = _exact_keys(value, {"origin", "target"}, field=f"edge[{index}]")
+        edges.append(
+            (
+                _module_name(row["origin"], field=f"edge[{index}].origin"),
+                _module_name(row["target"], field=f"edge[{index}].target"),
+            )
+        )
+    sccs: list[tuple[str, ...]] = []
+    for index, value in enumerate(_table_array(top["scc"], field="scc")):
+        row = _exact_keys(value, {"members"}, field=f"scc[{index}]")
+        members_value = row["members"]
+        if type(members_value) is not list:
+            raise BaselineError(f"scc[{index}].members must be an array")
+        sccs.append(
+            tuple(
+                _module_name(member, field=f"scc[{index}].members")
+                for member in members_value
+            )
+        )
+    graph = DependencyGraph(modules, edges, sccs)
+    _validate_graph(graph)
+    if module_count != len(graph.modules):
+        raise BaselineError("module_count does not match module rows")
+    if edge_count != len(graph.edges):
+        raise BaselineError("edge_count does not match edge rows")
+    if scc_count != len(graph.sccs):
+        raise BaselineError("scc_count does not match SCC rows")
+    if expected_edge_digest != edges_sha256(graph.edges):
+        raise BaselineError("edges_sha256 does not match canonical edge rows")
+    if expected_scc_digest != sccs_sha256(graph.sccs):
+        raise BaselineError("sccs_sha256 does not match canonical SCC rows")
+    return ParsedBaseline(commit, graph)
+
+
+def _is_reparse(info: os.stat_result) -> bool:
+    return bool(getattr(info, "st_file_attributes", 0) & 0x400)
+
+
+def _validated_regular_file(path: Path, *, maximum_bytes: int) -> bytes:
+    try:
+        info = os.lstat(path)
+    except OSError as error:
+        raise BaselineError(f"dependency baseline file cannot be inspected: {path}") from error
+    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
+        raise BaselineError(f"dependency baseline path is not a regular file: {path}")
+    if info.st_size > maximum_bytes:
+        raise BaselineError(f"dependency baseline file is oversized: {path}")
+    try:
+        raw = path.read_bytes()
+    except OSError as error:
+        raise BaselineError(f"dependency baseline file cannot be read: {path}") from error
+    if len(raw) != info.st_size:
+        raise BaselineError(f"dependency baseline file changed while reading: {path}")
+    return raw
+
+
+def _git_environment(git_executable: Path) -> dict[str, str]:
+    allowed = ("SystemRoot", "WINDIR", "ComSpec", "PATHEXT", "TEMP", "TMP", "TMPDIR")
+    folded = {key.casefold(): value for key, value in os.environ.items()}
+    environment = {key: folded[key.casefold()] for key in allowed if key.casefold() in folded}
+    temporary = str(Path(tempfile.gettempdir()).resolve())
+    environment["HOME"] = temporary
+    environment["USERPROFILE"] = temporary
+    if os.name == "nt":
+        system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
+        environment["PATH"] = os.pathsep.join(
+            (str(git_executable.parent), str(system_root / "System32"))
+        )
+    else:
+        environment["PATH"] = os.pathsep.join((str(git_executable.parent), "/usr/bin", "/bin"))
+    environment.update(
+        {
+            "GIT_CONFIG_NOSYSTEM": "1",
+            "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
+            "GIT_NO_REPLACE_OBJECTS": "1",
+            "GIT_LITERAL_PATHSPECS": "1",
+        }
+    )
+    return environment
+
+
+def _validated_git_executable(executable: Path) -> Path:
+    if not isinstance(executable, Path) or not executable.is_absolute():
+        raise BaselineError("Git executable must be an absolute path")
+    try:
+        resolved = executable.resolve(strict=True)
+        info = os.lstat(resolved)
+    except OSError as error:
+        raise BaselineError("Git executable is unavailable") from error
+    if (
+        os.path.normcase(str(resolved)) != os.path.normcase(str(executable))
+        or stat.S_ISLNK(info.st_mode)
+        or _is_reparse(info)
+        or not stat.S_ISREG(info.st_mode)
+    ):
+        raise BaselineError("Git executable identity is invalid")
+    return resolved
+
+
+def _run_git_archive(
+    repository_root: Path, *, baseline_commit: str, git_executable: Path
+) -> bytes:
+    executable = _validated_git_executable(git_executable)
+    command = [
+        str(executable),
+        "archive",
+        "--format=tar",
+        baseline_commit,
+        "--",
+        "src/pontius",
+    ]
+    try:
+        completed = subprocess.run(
+            command,
+            cwd=repository_root,
+            env=_git_environment(executable),
+            stdin=subprocess.DEVNULL,
+            stdout=subprocess.PIPE,
+            stderr=subprocess.PIPE,
+            check=False,
+            timeout=120,
+            shell=False,
+        )
+    except (OSError, subprocess.TimeoutExpired) as error:
+        raise BaselineError("Git archive command failed") from error
+    if completed.returncode != 0 or len(completed.stderr) > 1024 * 1024:
+        raise BaselineError("Git archive command did not produce the baseline")
+    if len(completed.stdout) > MAXIMUM_ARCHIVE_BYTES:
+        raise BaselineError("Git archive exceeds the dependency-source bound")
+    return completed.stdout
+
+
+def _sources_from_archive(raw: bytes) -> dict[str, bytes]:
+    sources: dict[str, bytes] = {}
+    try:
+        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
+            for member in archive:
+                if member.isdir():
+                    continue
+                path = _normalized_relative_path(member.name, field="Git archive path")
+                if not member.isfile():
+                    raise BaselineError(f"Git archive contains a nonregular path: {path}")
+                if not path.startswith("src/pontius/") or not path.endswith(".py"):
+                    continue
+                stream = archive.extractfile(member)
+                if stream is None:
+                    raise BaselineError(f"Git archive source cannot be read: {path}")
+                content = stream.read()
+                if len(content) != member.size:
+                    raise BaselineError(f"Git archive source is truncated: {path}")
+                if path in sources:
+                    raise BaselineError(f"Git archive repeats a Python path: {path}")
+                sources[path] = content
+    except (tarfile.TarError, OSError) as error:
+        raise BaselineError("Git archive is not a valid bounded tar stream") from error
+    return sources
+
+
+def derive_baseline_graph(
+    repository_root: Path,
+    *,
+    baseline_commit: str = BASELINE_COMMIT,
+    git_executable: Path,
+) -> DependencyGraph:
+    commit = _require_commit(baseline_commit)
+    try:
+        root = repository_root.resolve(strict=True)
+    except OSError as error:
+        raise BaselineError("repository root cannot be resolved") from error
+    raw = _run_git_archive(root, baseline_commit=commit, git_executable=git_executable)
+    return scan_sources(_sources_from_archive(raw))
+
+
+def validate_write_destination(repository_root: Path, destination: Path) -> Path:
+    if not isinstance(destination, Path) or not destination.is_absolute():
+        raise BaselineError("--write must explicitly name an absolute baseline path")
+    try:
+        root = repository_root.resolve(strict=True)
+        architecture = (root / "docs" / "architecture").resolve(strict=True)
+    except OSError as error:
+        raise BaselineError("docs/architecture must already be a real directory") from error
+    architecture_info = os.lstat(architecture)
+    if (
+        stat.S_ISLNK(architecture_info.st_mode)
+        or _is_reparse(architecture_info)
+        or not stat.S_ISDIR(architecture_info.st_mode)
+    ):
+        raise BaselineError("docs/architecture is not a regular directory")
+    expected = architecture / "dependency-baseline.toml"
+    candidate = destination.resolve(strict=False)
+    if os.path.normcase(str(candidate)) != os.path.normcase(str(expected)):
+        raise BaselineError("--write may name only docs/architecture/dependency-baseline.toml")
+    if os.path.lexists(candidate):
+        info = os.lstat(candidate)
+        if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
+            raise BaselineError("baseline destination is not a regular file")
+    return candidate
+
+
+def write_baseline(destination: Path, raw: bytes) -> None:
+    candidate = destination.parent / f".{destination.name}.{uuid.uuid4().hex}.tmp"
+    try:
+        with candidate.open("xb") as stream:
+            stream.write(raw)
+            stream.flush()
+            os.fsync(stream.fileno())
+        os.replace(candidate, destination)
+    except OSError as error:
+        raise BaselineError("dependency baseline could not be written atomically") from error
+    finally:
+        try:
+            candidate.unlink()
+        except FileNotFoundError:
+            pass
+
+
+def check_baseline(destination: Path, expected: bytes) -> None:
+    actual = _validated_regular_file(destination, maximum_bytes=MAXIMUM_BASELINE_BYTES)
+    parsed = parse_baseline_bytes(actual)
+    if parsed.baseline_commit != BASELINE_COMMIT:
+        raise BaselineError("dependency baseline commit differs from the approved lock")
+    if actual != expected:
+        raise BaselineError("dependency baseline bytes differ from deterministic generation")
+
+
+def parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
+    parser = argparse.ArgumentParser(description=__doc__)
+    commands = parser.add_mutually_exclusive_group()
+    commands.add_argument("--check", action="store_true", help="verify the baseline (default)")
+    commands.add_argument(
+        "--write",
+        type=Path,
+        metavar="ABSOLUTE_BASELINE_PATH",
+        help="atomically write the explicitly named canonical baseline",
+    )
+    parsed = parser.parse_args(argv)
+    if parsed.write is None:
+        parsed.check = True
+    return parsed
+
+
+def configured_git_executable() -> Path:
+    configured = os.environ.get("PONTIUS_GIT")
+    if configured is None or not configured.strip():
+        raise BaselineError("PONTIUS_GIT must name an absolute Git executable")
+    executable = Path(configured)
+    if not executable.is_absolute():
+        raise BaselineError("PONTIUS_GIT must name an absolute Git executable")
+    return executable
+
+
+def main(argv: Sequence[str] | None = None) -> int:
+    arguments = parse_arguments(argv)
+    repository_root = Path(__file__).resolve().parents[1]
+    destination = repository_root / BASELINE_RELATIVE_PATH
+    try:
+        graph = derive_baseline_graph(
+            repository_root,
+            baseline_commit=BASELINE_COMMIT,
+            git_executable=configured_git_executable(),
+        )
+        raw = render_baseline(graph, baseline_commit=BASELINE_COMMIT)
+        if arguments.write is not None:
+            destination = validate_write_destination(repository_root, arguments.write)
+            write_baseline(destination, raw)
+        else:
+            check_baseline(destination, raw)
+    except BaselineError as error:
+        print(f"dependency baseline generation failed: {error}", file=sys.stderr)
+        return 2
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
