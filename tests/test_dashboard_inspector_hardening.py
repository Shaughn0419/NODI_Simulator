from __future__ import annotations

from types import SimpleNamespace

from dashboard.panels import inspector


class _SessionState(dict):
    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


class _FakeColumn:
    def __enter__(self) -> _FakeColumn:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def metric(self, *_args: object, **_kwargs: object) -> None:
        return None

    def markdown(self, *_args: object, **_kwargs: object) -> None:
        return None

    def caption(self, *_args: object, **_kwargs: object) -> None:
        return None


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state = _SessionState(
            selected_particle="gold_40nm",
            selected_wavelength_nm=660,
            selected_W_nm=800,
            selected_H_nm=550,
            data_prefix="test_dataset",
            case_cache={},
        )

    def columns(self, spec: int | list[float] | tuple[float, ...]) -> list[_FakeColumn]:
        count = spec if isinstance(spec, int) else len(spec)
        return [_FakeColumn() for _ in range(count)]

    def button(self, *_args: object, **_kwargs: object) -> bool:
        return False

    def __getattr__(self, name: str):
        def _noop(*_args: object, **_kwargs: object) -> None:
            return None

        return _noop


def test_inspector_renders_without_health_report(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(inspector, "st", fake_st)
    monkeypatch.setattr(inspector, "render_page_header_hub", lambda *args, **kwargs: None)
    monkeypatch.setattr(inspector, "is_standard_dashboard_dataset_prefix", lambda prefix: False)
    monkeypatch.setattr(
        inspector,
        "load_dashboard_data_bundle",
        lambda *args, **kwargs: SimpleNamespace(
            source=SimpleNamespace(
                is_live=False,
                prefix="test_dataset",
                summary_caption="summary",
                detail_caption="detail",
            ),
            compact=[{}],
            health_report=None,
        ),
    )
    monkeypatch.setattr(
        inspector,
        "get_case_summary",
        lambda *args, **kwargs: {
            "score": 0.5,
            "engineering_score": 0.4,
            "engineering_gate_passed": False,
            "particle_material": "gold",
            "particle_diameter_nm": 40,
            "summary": {
                "detection_rate": 0.5,
                "all_heights": [],
                "all_widths": [],
            },
        },
    )
    monkeypatch.setattr(
        inspector,
        "get_score_explanation",
        lambda case: {
            "E_sca_E_ref_ratio": 0.1,
            "dominant_factor": "balanced",
            "trust_level": "medium",
            "explanation": "test explanation",
            "trust_reason": "test reason",
        },
    )
    monkeypatch.setattr(
        inspector,
        "build_physics_breakdown",
        lambda case: {
            "case_physics": {"Csca_m2": 1.0e-18},
            "batch_outcome": {
                "stable_detection_rate": 0.5,
                "robust_cv_peak_height": 0.2,
                "mean_peak_margin_z": 0.8,
                "hit_rate_at_fixed_false_alarm": 0.5,
                "roc_auc_event_vs_background": 0.75,
                "mean_local_snr": 2.0,
                "paired_detection_rate": 0.4,
            },
        },
    )
    monkeypatch.setattr(inspector, "get_active_data_source_tag", lambda: "test_dataset")

    inspector.render_inspector()
