# Bounded-read coverage map

Both independent preimplementation reviews returned SOUND on 2026-09-07.
Reviewer A inspected brief/design content; reviewer B also checked the base tree,
all six registration blobs and complete stable-read caller population. Reviewed
brief SHA256: 7655ca39947731f7a24e1552369d4bd50521080faae61568afa3e935161bb508;
design SHA256: f01b7a2fbc75298f69521514307e3f1baa5a6ca3d29ab2f71eb0e9a7b3a0d805.
These design verdicts are separate from frozen source acceptance.

- **Read request ceiling:** new suite's resource-ceiling control; RED against
  original read expression, GREEN after correction.
- **Stable bytes/tokens and caps:** empty, 1, 4096, 65536 bytes; below/exact/above
  caps and the 16 MiB default compared with v1.
- **Before-handle identity:** real named replacement before native open; no
  production read occurs.
- **After-handle identity:** persistent native growth and shrink between pre-read
  fstat and read.
- **Final named identity:** replacement after actual handle close.
- **Ancestor identity:** replaced parent with hard-linked original file; file
  identity stays equal.
- **Extra-byte observation:** grow to six real bytes, read, truncate to three and
  restore mtime; v2 refuses; size-only production mutant accepts.
- **Creation and capture:** real exclusive create, flush/fsync/readback round trip
  and collision without overwrite.
- **Source admission/helper reuse:** public v2 admission from frozen D-local HEAD;
  independently recomputed manifest and base-Git helper bytes.
- **Closed imports/loader:** both exact origins pass; wrong origin, forbidden import
  and two loader mutations refuse.
- **Execution/cleanup/publication:** unchanged v1 evaluation suites plus fresh
  source-bound v2 12-trial run and completed-reader validation.
- **Artifact compatibility:** v2 public reader reads retained v1 completion; v1
  public reader reads new v2 completion.
- **Registration/sealed bytes:** generated inventory check, current checked-in
  census/profile tests, boundary checker/suite and exact Git diff.

Caller population: creation readback; native Git revalidation; captured-source
revalidation; executable/source capture; saved-input revalidation; stdout/stderr
capture; initial/final completed-artifact reads; request admission; unit retention.
Caps are the 16 MiB default, 4 MiB, 64 KiB and 4096 bytes. No cap values or other
caller behavior changes. Metadata schedules are deterministic native-file controls,
not prevalence measurements or proof of detecting every possible filesystem race.

Test-only mutations compile a single function with its read bound changed. The
same real-file injector runs both variants; the returned bytes and final metadata
are independently asserted. No injector vetoes the mutant before observation.

Qualification records, final source reviews and cost results are pinned in the
successor decision packet after execution. The old v1 source, helper, game/policy
code, fixtures and retained result bytes are outside the change surface.
