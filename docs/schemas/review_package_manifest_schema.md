# Review Package Manifest Schema

`REVIEW_BUILD_MANIFEST.json` may track build-time generation work. `REVIEW_PACKAGE_MANIFEST.json` is the relative-audit release manifest and may not contain `must_be_generated`. `REVIEW_PACKAGE_HASHES.sha256` excludes itself and the release manifest to avoid hash recursion.

Top-level release-manifest fields tracked from `REVIEW_PACKAGE_MANIFEST.json`:

- `calibrated_claim_allowed`
- `deferred_p0b_roles`
- `generated_at`
- `git_commit`
- `git_dirty`
- `hashes_manifest_sha256`
- `platform`
- `release_readiness`
- `review_package_manifest_schema`
- `v1_summary_mode`

Top-level build-manifest fields tracked from `REVIEW_BUILD_MANIFEST.json`:

- `calibrated_claim_allowed`
- `generated_at`
- `git_commit`
- `git_dirty`
- `hashes_manifest_sha256`
- `review_build_manifest_schema`
