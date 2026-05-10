# Review Package Manifest Schema

`REVIEW_BUILD_MANIFEST.json` may track build-time generation work. `REVIEW_PACKAGE_MANIFEST.json` is the relative-audit release manifest and may not contain `must_be_generated`. `REVIEW_PACKAGE_HASHES.sha256` excludes itself and the release manifest to avoid hash recursion.
