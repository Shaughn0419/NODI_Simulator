# 298 - NODI-COMSOL Gate10F COMSOL Sidewall Export Requirements

COMSOL should export a review-only sidewall geometry descriptor with descriptor id, descriptor sha256, source artifact sha256, angle convention, widths, closure, claim boundary, and no-authorization flags.
NODI must quarantine or hard-fail sidewall-aware rows that lack descriptor id/hash binding.
This does not alter Gate2D, EDGE, QCH, BINDING, JRC, runtime, or production status.

