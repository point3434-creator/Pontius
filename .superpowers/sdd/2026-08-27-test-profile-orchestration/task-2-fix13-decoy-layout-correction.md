# Task 2 fix-13 string-decoy layout correction

## Identity and scope

- previously accepted tests SHA-256:
  `5f396043fbb4779ea8fd293042abb2c552849061c8e60ba477e4327841905a70`
- corrected tests SHA-256:
  `6102c048a86e8f068cc0c3bd8303323115f9697bf29d8d4bfd246da000ec8822`
- production generator at the layout-review boundary:
  `7fc84e76febb0a14e237f21473ba2bd7ab84afdf94270e7e9117cbf78369731f`

The first production correction advanced the real working-source review beyond
the earlier census mismatches and exposed a test-source layout violation.
`_string_decoy_census` requires every tracked literal to have a unique
`(relative_path, line)` identity. Two existing assertions each placed both
`"cupy.arange"` and `"cupy.zeros"` constants on one physical source line, at
former lines 8981 and 9258 of `tests/test_inventory_and_profiles.py`.

The only correction split each existing set literal across physical lines.
No token, expression, expectation, control flow, or runtime behavior changed.
The current constants occupy lines 8983/8984 and 9264/9265.

## Independent review

Both exact-hash read-only reviews returned CLEAN with no finding: primary
TEST-SPEC and TEST-QUALITY, and independent adversarial ORACLE. Each reviewer
reversed exactly the two formatting hunks in memory and reproduced the prior
SHA-256. Location-free AST dumps and canonical unparse are identical; the
adversarial review also compared every compiled code object's executable
`co_code`, which is identical. The corrected census has zero duplicate
`(path, line)` identities, and cache/bytecode counts remained zero.

The corrected tests are accepted and frozen. This amendment does not authorize
weaker row, blocker, census, digest, capability, or runtime expectations.
Production remains responsible for satisfying the full working-discovery
contract.
