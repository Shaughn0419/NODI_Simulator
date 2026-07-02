# NODI Sidewall Three-Question Result Lock

Disposition: `NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_READY`
Artifact ID: `NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_20260703`
Route result rows: `6`
Question result rows: `3`
603 executed event rows: `208`
Failed validation rows: `0`

This result lock keeps the sidewall-angle mainline on the three user questions: candidate dimension envelope change, selected-annulus window change, and peak/local-SNR response change. It is simulation context only, not route selection, final probability, yield, wet, fabrication, q_ch weighting, true W_eff, or production evidence.

## Question Results
- `size_recommendation_delta_after_sidewall`: `candidate_top_width_envelope_changed_for_6_of_6_routes`
- `selected_annulus_range_delta_after_sidewall`: `annulus_context_changed_for_6_of_6_routes`
- `interference_response_delta_after_sidewall`: `peak_or_local_snr_context_changed_in_noncanonical_windows`

## Route Results
- `404/W500/D1200` -> `404/W607/D1200`; width delta `107` nm; windows `["0p4_0p7", "0p5_0p8", "0p6_0p9"]`; context `full_window_response_context_retained`
- `404/W500/D900` -> `404/W580/D900`; width delta `80` nm; windows `["0p5_0p8", "0p6_0p9"]`; context `outer_window_annulus_context_retained`
- `404/W600/D900` -> `404/W680/D900`; width delta `80` nm; windows `["0p4_0p7", "0p5_0p8", "0p6_0p9"]`; context `full_window_response_context_retained`
- `660/W500/D1500` -> `660/W633/D1500`; width delta `133` nm; windows `["0p4_0p7", "0p5_0p8", "0p6_0p9"]`; context `full_window_response_context_retained`
- `660/W800/D1200` -> `660/W907/D1200`; width delta `107` nm; windows `["0p5_0p8", "0p6_0p9"]`; context `outer_window_annulus_context_retained`
- `660/W800/D900` -> `660/W880/D900`; width delta `80` nm; windows `["0p4_0p7", "0p5_0p8", "0p6_0p9"]`; context `full_window_response_context_retained`
