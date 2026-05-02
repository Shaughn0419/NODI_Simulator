# Exosome Biomimetic Surface Model

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：本文仍记录 EV/sEV biomimetic optical-model rationale；代码主线已包含 EV/NODI relative design gate、detector caution、analytic lock-in surrogate、严格 event QC、EV biomimetic ensemble/anchors、calibrated BFP ROI 1D projected lane、dashboard diagnostics/schema inventory、selected-annulus parallel analysis lens、Tsuyama selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants，以及 linked 488-window/532-max classification feature lane。Selected-annulus paper-fit EV targeted panel 与 3-seed pre-fullgrid robustness audit 已通过；旧 CSV 缺 selected-annulus 源列时会标记 unavailable/null/NaN。`joint_fit_score` 已明确为 lower-is-better loss-style penalty，paper target metadata 与 claim compatibility 已进入代码测试。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings。
<!-- DOCSYNC:END -->

## Why this document exists

The simulator originally treated exosomes as a homogeneous dielectric sphere with `n = 1.38`.
That approximation is still useful as a compact baseline, but it hides the two things that matter most for small-vesicle optics:

1. exosomes are surface-dominated objects rather than bulk-dominated particles
2. the surface is not just one phospholipid bilayer; it is affected by membrane proteins, adsorbed corona species, and ionic double-layer physics

This note records the literature basis for the new `exosome_biomimetic` model and separates:

- direct literature anchors
- literature-constrained surrogate choices
- limitations that are still intentionally left out

## Theory anchor for the optics

The new model uses exact coated-sphere Mie scattering rather than an effective-index shortcut.

- Core-shell scattering theory:
  Aden and Kerker, *J. Appl. Phys.* 22, 1242-1246 (1951), DOI `10.1063/1.1699834`
- Textbook reference used to structure the implementation and notation:
  Bohren and Huffman, *Absorption and Scattering of Light by Small Particles* (Wiley, 1983)
  [Publisher page](https://www.wiley-vch.de/en?isbn=9780471293408&option=com_eshop&view=product)

This means the simulator now distinguishes:

- outer radius
- inner aqueous core radius
- shell refractive index
- core refractive index

The equivalent uniform RI is still reported, but only as a diagnostic quantity. The actual scattering is computed from the coated-sphere coefficients.

## Direct EV / exosome literature anchors

### 1. EVs are reasonably modeled as core-shell particles in optical scattering work

- van der Pol et al., *Journal of Extracellular Vesicles* 9:e12074 (2020), DOI `10.1002/jev2.12074`
  [PubMed abstract](https://pubmed.ncbi.nlm.nih.gov/32966654/)

What matters here:

- the paper explicitly models EVs as core-shell particles
- in the flow-cytometry optical model, EVs use:
  - core RI `1.343-1.36`
  - shell RI `1.46`
  - shell thickness `5 nm`

That is the cleanest direct justification for moving the simulator away from a homogeneous `n = 1.38` sphere.

### 2. The plausible EV shell can be dimmer/thinner or brighter/thicker depending on protein loading

- van der Pol, van Leeuwen, and Yan, *Scientific Reports* 11, 24151 (2021), DOI `10.1038/s41598-021-03015-2`
  [Nature page](https://www.nature.com/articles/s41598-021-03015-2)
  [PubMed page](https://pubmed.ncbi.nlm.nih.gov/34921157/)

Key points from the paper:

- the paper argues that EVs should not be interpreted as solid spheres with one diameter-independent RI
- it uses two physically plausible EV shell scenarios:
  - `4 nm` shell with RI `1.45` and core RI `1.380`
  - `12 nm` shell with RI `1.52` and core RI `1.353`
- the authors state that a phospholipid bilayer without proteins is about `4 nm`
- they further note that transmembrane proteins can make the effective membrane thickness much larger

This gives a literature-supported shell envelope:

- shell thickness: roughly `4-12 nm`
- shell RI: roughly `1.45-1.52`
- core RI: roughly `1.353-1.380`

### 3. Independent single-particle optical work also keeps EV RI below the solid high-index bead regime

- Enciso-Martinez et al., *Journal of Extracellular Vesicles* 9:e1730134 (2020), DOI `10.1080/20013078.2020.1730134`
  [Repository PDF snippet source](https://www.vesiclecenter.com/downloads/articles/2020/Enciso-Martinez_2020_JEV_Label-free_identification_of_EVs.pdf)

Why this matters:

- the paper performs label-free single-particle optical characterization
- it again treats EVs as core-shell particles
- the paper notes that EV refractive index is typically below about `1.42`

That is consistent with the simulator's new size-dependent equivalent uniform RI values, which stay around `1.38-1.40` rather than drifting toward bead-like high-index values.

### 4. Protein corona formation around exosomes is real and changes surface properties

- Heidarzadeh et al., *Cell Communication and Signaling* 21, 64 (2023), DOI `10.1186/s12964-023-01089-1`
  [Open-access PDF](https://biosignaling.biomedcentral.com/counter/pdf/10.1186/s12964-023-01089-1.pdf)

What matters here:

- exosomes in biofluids can acquire an external protein corona
- the review describes soft and hard corona layers
- the review emphasizes changes in:
  - hydrodynamic size
  - zeta potential
  - surface fingerprint
  - downstream targeting / uptake

This is the main reason the simulator does not stop at "membrane only".

### 5. EVs carry net negative surface charge and ionic conditions reshape the electric double layer

- Midekessa et al., *ACS Omega* 5, 16701-16710 (2020), DOI `10.1021/acsomega.0c01582`
  [Repository PDF](https://eprints.whiterose.ac.uk/163641/1/acsomega.0c01582.pdf)

What matters here:

- EVs carry a net negative surface charge in physiological media
- ionic strength and ion valency make the zeta potential less negative
- the paper explicitly connects this to compression / shrinkage of the electrical double layer
- the paper reports typical zeta-potential magnitudes on the order of `30-40 mV` in their system, with clear ionic-strength dependence

This does **not** mean charge should be turned into a metal-like optical response. It means charge should influence the near-surface hydrated ionic layer and therefore the effective outer optical boundary.

## Professional book anchor for the double-layer treatment

- Israelachvili, *Intermolecular and Surface Forces*, 3rd ed. (Academic Press, 2011)
  [ScienceDirect page](https://www.sciencedirect.com/book/9780123751829/intermolecular-and-surface-forces)

Why it is used here:

- not to fit an exosome-specific RI
- only to justify the standard Debye-length scaling used for the thickness of the hydrated ionic atmosphere

In the code, the Debye-length approximation is used only to size the EDL-like shell contribution. The optical contrast of that layer remains intentionally weak.

## How the current simulator maps those sources into parameters

The current defaults in `structured_particles.py` are:

- `core_n_real = 1.360`
- `membrane_n_real = 1.460`
- `corona_n_real = 1.400`
- `membrane_thickness_m = 5 nm`
- `corona_thickness_m = 4 nm`
- `ionic_strength_M = 0.150`
- `edl_refractive_increment = 0.005`

### What is directly anchored

- `core_n_real = 1.360`
  - inside the EV core-RI interval reported in the 2020 and 2021 EV optical papers
- `membrane_n_real = 1.460`
  - matches the common phospholipid-shell optical model used in the 2020 EV paper
- `membrane_thickness_m = 5 nm`
  - matches the 2020 EV optical model and stays close to the 2021 dim-shell case
- total surface-shell scale near `10 nm`
  - consistent with the `4-12 nm` window discussed in the 2021 EV optics paper

### What is literature-constrained but still surrogate

- `corona_n_real = 1.400`
  - chosen because the corona is protein-rich and optically denser than water/core, but should remain less extreme than the brightest membrane-rich shell scenarios
- `corona_thickness_m = 4 nm`
  - chosen to keep the total shell in the literature-supported EV range while explicitly separating membrane and corona
- `edl_refractive_increment = 0.005`
  - intentionally small; this term says "hydrated ions perturb the near-surface optical boundary a little", not "surface charge dominates visible-frequency dielectric response"

### What is purely numerical and not a literature fit

- `min_core_radius_fraction = 0.25`
  - this is only a stability guard to stop the shell from swallowing the entire smallest vesicle

## Second-pass confirmation against the literature

After a second search through textbooks and EV-focused optical papers, the current model looks consistent with the requirement **as a more realistic optical-surface surrogate**:

1. **The coated-sphere formalism is correct for the intended level of physics.**
   The optics now use the textbook / classic-paper route instead of forcing all surface structure into one homogeneous RI.

2. **Aqueous core + high-RI shell is directly supported by EV optical literature.**
   Both 2020 and 2021 EV papers treat EVs as core-shell particles and give realistic parameter ranges for shell thickness and RI.

3. **Adding corona and EDL into the shell is physically motivated and matches the user requirement better than a bare membrane-only shell.**
   The 2023 protein-corona review and the 2020 zeta-potential paper both support the idea that the exosome surface in fluid is not just a dry phospholipid bilayer.

4. **The current numbers are conservative rather than aggressive.**
   The model keeps the shell RI below the brightest `1.52` shell scenario from the 2021 paper because it includes softer, more weakly contrasting outer material.

## Can we reach an "ultimate realistic" model?

Not as one universal default model, no.

The literature is strong enough to support a **rigorous bounded family** of exosome optical models, but not strong enough to justify one globally correct exosome parameter set that is simultaneously:

- morphology-specific
- biofluid-specific
- corona-specific
- pH / ionic-strength specific
- cell-origin specific

In other words, the limiting issue is not Maxwell theory. The limiting issue is missing sample-specific biology.

## What can still be made more realistic with strong support

### 1. Literature-bounded model envelope

This is the step that is most rigorous right now, and it has now been added in code as preset families:

- `membrane_only_dim_2021`
- `membrane_only_nominal_2020`
- `biomimetic_corona_nominal`
- `surface_loaded_bright_2021`

That gives a supported uncertainty band rather than a single pretend-exact answer.

### 2. Multilayered spherical vesicle models

This is theoretically well supported and could be implemented rigorously if needed:

- Yang, *Applied Optics* 42, 1710-1720 (2003):
  improved recursive algorithm for light scattering by a multilayered sphere
- Wang, Miller, and Szostak, *Biophysical Journal* 116, 659-669 (2019):
  [Open-access PDF](https://molbio.mgh.harvard.edu/szostakweb/publications/Szostak_pdfs/AW_et_Biophysical_2019.pdf)

Why this matters:

- multilamellarity can strongly affect scattering
- exact multilayer sphere theory is available

Why it is **not** the default yet:

- most exosome datasets do not provide a robust lamellarity distribution to parameterize it
- nonconcentric or irregular internal structures would still fall outside that model

### 3. Anisotropic membrane shells

This is also theoretically supported, but not yet well constrained for a generic default exosome:

- the 2021 *Scientific Reports* EV optics paper explicitly notes that EV membranes can scatter anisotropically
- it cites anisotropic core-shell theory such as Lange and Aragón, *J. Chem. Phys.* 92, 4643-4650 (1990)

Why it is **not** the default yet:

- anisotropic shell optics needs orientation-aware parameters
- exosome-specific radial/tangential membrane optical constants are not available as a clean universal dataset

So yes, we can move to anisotropic-shell theory in principle, but we would still need sample-specific assumptions that are much weaker than the current core-shell evidence base.

## What the current model still does not capture

The current `exosome_biomimetic` model is more realistic than `n = 1.38` homogeneous sphere, but it is still not the final word. It does **not** yet include:

- membrane optical anisotropy
- non-spherical or faceted vesicles
- multilamellar / double-vesicle structures
- patchy or time-evolving protein corona composition
- explicit pH-dependent charge regulation
- aggregation or exosome-lipoprotein complexes

One especially important literature caveat comes from the 2021 *Scientific Reports* paper: EV membranes can scatter anisotropically. So the present model should be understood as a stronger first-order surface-structure model, not a complete electromagnetic description of every exosome.

## Bottom-line assessment

For the simulator's present purpose, the new model is a good fit to the requirement:

- it is materially more realistic than a homogeneous `n = 1.38` sphere
- it is grounded in coated-sphere optics from professional theory sources
- it is constrained by EV-specific optical and colloidal literature
- it preserves a clean path for future upgrades if you later want:
  - anisotropic shells
  - multilayer vesicles
  - pH / ionic-strength sweeps
  - sample-specific corona presets

## Current implementation status

This model family is no longer only a design note. It is wired into the main workflow and remains the target EV/sEV optical model for the next full recompute.

### Current preset families in code

The structured exosome presets currently exposed in the codebase are:

- `membrane_only_dim_2021`
- `membrane_only_nominal_2020`
- `biomimetic_corona_nominal`
- `surface_loaded_bright_2021`

The current default production preset used for the upgraded full dataset is:

- `biomimetic_corona_nominal`

### Current target dataset

The current standard EV design recompute target is:

- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_compact.pkl`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_meta.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_result_health.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_runtime_performance.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_freeze_probe.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_design_postprocess.csv`

Its metadata records:

- `particle_profile = full_range_biomimetic_exosome_with_anchors`
- `grid = ev_design`
- `n_cases = 32032`
- `exosome_surface_model.preset_names = ["biomimetic_corona_nominal"]`

As of the 2026-04-27 wavelength and W/H-grid correction, the current EV design target includes `404 / 488 / 532 / 660 nm` and `32032` cases; any three-wavelength `7056`-case library or old-geometry `9408`-case library is stale partial coverage. The EV design library must be regenerated with the current `schema 1.24` pipeline before any numerical selection claim is treated as current. `dashboard.precompute` now defaults to the `standard` artifact profile, so duplicate `case_summary` and heavy split exports are intentionally omitted unless `--artifact-profile full` is requested.

### Where to read the operational and result-level follow-up

- full recompute execution guide: [24_高性能预计算与增量重算方案.md](../../24_高性能预计算与增量重算方案.md)
- current physics alignment and recompute readiness: [41_实验对齐原则与计算修正备忘.md](../../41_实验对齐原则与计算修正备忘.md) / [42_全量重算前复核结论与现行边界.md](../../42_全量重算前复核结论与现行边界.md)

### Practical interpretation

For this repository, the current modeling hierarchy should now be read as:

1. `exosome_uniform (n=1.38)` = historical compact baseline
2. `exosome_biomimetic` core-shell family = current realistic default optical-surface model
3. anisotropic / multilayer / sample-specific corona models = future bounded upgrades, not yet the default
