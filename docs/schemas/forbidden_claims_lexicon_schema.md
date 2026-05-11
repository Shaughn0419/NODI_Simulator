# Forbidden Claims Lexicon Schema

`configs/realism_v2/forbidden_claims_lexicon.yaml` lists English and Chinese calibrated, absolute, biological, concentration, and promotion claim phrases. Negated blocker language is permitted within pinned windows.

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `allowed_blocker_examples`
- `forbidden_phrase_negators`
- `languages`
- `negator_window_chars_zh`
- `negator_window_tokens_en`
- `objects`
- `verbs`
- `zh_forbidden_objects`
- `zh_forbidden_verbs`
- `zh_negators`

