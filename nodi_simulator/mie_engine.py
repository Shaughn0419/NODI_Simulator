"""
Package-local Mie scattering engine for NODI interferometric simulation.

Implements Mie scattering theory following Bohren & Huffman (1983).
Used because miepython is not available in this environment.

Homogeneous-sphere reference:
    - C. F. Bohren and D. R. Huffman, Absorption and Scattering of Light by
      Small Particles (Wiley, 1983).
      Publisher: https://www.wiley-vch.de/en?isbn=9780471293408&option=com_eshop&view=product

Concentric core-shell reference:
    - A. L. Aden and M. Kerker, J. Appl. Phys. 22, 1242-1246 (1951).
      DOI: 10.1063/1.1699834
    - Bohren & Huffman remain the practical textbook reference for notation,
      coated-sphere numerics, and dipole-limit interpretation.

This module provides:
    - mie_compute: Qext, Qsca efficiency factors
    - mie_angular: S1(θ), S2(θ) scattering amplitude functions

Simplification note:
    - Unified Mie engine for all particle sizes; no Rayleigh auto-switch.
    - Small-particle Rayleigh consistency verified via sanity checks, not code branches.
"""

import numpy as np
from scipy.special import spherical_jn, spherical_yn


def _compute_nmax(x: float) -> int:
    """
    Determine number of terms needed for Mie series convergence.
    Uses Wiscombe (1980) criterion.
    """
    if x <= 0:
        return 1
    nmax = int(x + 4.0 * x**(1.0 / 3.0) + 2)
    return max(nmax, 3)


def _log_derivative_downward(m_rel: complex, x: float, nmax: int) -> np.ndarray:
    """
    Compute logarithmic derivative D_n(mx) by downward recurrence.

    D_n(z) = n/z - 1/(D_{n+1}(z) + n/z)

    Starting from a sufficiently high order where D_N ≈ 0.
    """
    mx = m_rel * x
    nmx = max(nmax, int(abs(mx))) + 16
    D = np.zeros(nmx + 1, dtype=complex)
    # Downward recurrence from n=nmx to n=1
    for n in range(nmx, 0, -1):
        D[n - 1] = n / mx - 1.0 / (D[n] + n / mx)
    # Return D[1] through D[nmax]
    return D[1:nmax + 1]


def _riccati_bessel(x: float, nmax: int):
    """
    Compute Riccati-Bessel functions ψ_n(x) and ξ_n(x) by upward recurrence.

    ψ_n(x) = x·j_n(x)  (real)
    ξ_n(x) = x·h_n^(1)(x) = ψ_n(x) - i·χ_n(x)  (Bohren & Huffman convention)

    Returns:
        psi: array of ψ_n for n=1..nmax
        xi:  array of ξ_n for n=1..nmax
    """
    psi = np.zeros(nmax + 1, dtype=float)
    chi = np.zeros(nmax + 1, dtype=float)
    if x == 0:
        raise ValueError("_riccati_bessel requires a non-zero size parameter")

    psi[0] = np.sin(x)
    psi[1] = np.sin(x) / x - np.cos(x)

    chi[0] = np.cos(x)
    chi[1] = np.cos(x) / x + np.sin(x)

    for n in range(1, nmax):
        psi[n + 1] = (2 * n + 1) / x * psi[n] - psi[n - 1]
        chi[n + 1] = (2 * n + 1) / x * chi[n] - chi[n - 1]

    xi = psi - 1j * chi

    # Return n=1..nmax
    return psi[1:nmax + 1], xi[1:nmax + 1]


def _riccati_bessel_full(z: complex, nmax: int):
    """
    Compute Riccati-Bessel functions for real or complex arguments.

    Returns arrays for n=1..nmax:
        psi_n(z) = z j_n(z)
        chi_n(z) = -z y_n(z)
        xi_n(z) = psi_n(z) - i chi_n(z)
    together with derivatives with respect to the argument z.
    """
    orders = np.arange(1, nmax + 1, dtype=int)
    z = complex(z)

    jn = spherical_jn(orders, z)
    jn_p = spherical_jn(orders, z, derivative=True)
    yn = spherical_yn(orders, z)
    yn_p = spherical_yn(orders, z, derivative=True)

    psi = z * jn
    psi_p = jn + z * jn_p
    chi = -z * yn
    chi_p = -(yn + z * yn_p)
    xi = psi - 1j * chi
    xi_p = psi_p - 1j * chi_p
    return psi, psi_p, chi, chi_p, xi, xi_p


def _solve_core_shell_mode(
    nmax: int,
    x_outer: float,
    x_core: float,
    m_shell: complex,
    m_core: complex,
    *,
    electric_coefficient: bool,
) -> np.ndarray:
    """
    Solve one polarization family of a concentric core-shell sphere by
    enforcing tangential field continuity at the core/shell and shell/medium
    interfaces for each multipole order independently.

    Convention (Bohren & Huffman §4.4):
        electric_coefficient=True  → solves for a_n (TM/electric scattering
                                      coefficient); boundary factor = 1/m.
        electric_coefficient=False → solves for b_n (TE/magnetic scattering
                                      coefficient); boundary factor = m.

    Note: the previous parameter was named ``electric_mode`` with the
    *opposite* boolean sense (electric_mode=True gave the m factor used for
    b_n, and electric_mode=False gave 1/m for a_n), which was confusing and
    error-prone. This rename makes the flag self-consistent with B&H notation.
    """
    psi_out, psi_out_p, _, _, xi_out, xi_out_p = _riccati_bessel_full(x_outer, nmax)
    psi_shell_outer, psi_shell_outer_p, chi_shell_outer, chi_shell_outer_p, _, _ = (
        _riccati_bessel_full(m_shell * x_outer, nmax)
    )
    psi_shell_inner, psi_shell_inner_p, chi_shell_inner, chi_shell_inner_p, _, _ = (
        _riccati_bessel_full(m_shell * x_core, nmax)
    )
    psi_core, psi_core_p, _, _, _, _ = _riccati_bessel_full(m_core * x_core, nmax)

    coeffs = np.zeros(nmax, dtype=complex)
    for idx in range(nmax):
        if electric_coefficient:
            # a_n (TM/electric): derivative factor = 1/m at each interface
            # Matches (D_n(mx)/m + n/x) numerator in B&H Eq. 4.88.
            outer_shell_derivative_factor = 1.0 / m_shell
            shell_core_derivative_factor = m_shell / m_core
        else:
            # b_n (TE/magnetic): derivative factor = m at each interface
            # Matches (m·D_n(mx) + n/x) numerator in B&H Eq. 4.88.
            outer_shell_derivative_factor = m_shell
            shell_core_derivative_factor = m_core / m_shell

        matrix = np.array(
            [
                [
                    xi_out[idx],
                    -psi_shell_outer[idx],
                    -chi_shell_outer[idx],
                    0.0 + 0.0j,
                ],
                [
                    xi_out_p[idx],
                    -outer_shell_derivative_factor * psi_shell_outer_p[idx],
                    -outer_shell_derivative_factor * chi_shell_outer_p[idx],
                    0.0 + 0.0j,
                ],
                [
                    0.0 + 0.0j,
                    psi_shell_inner[idx],
                    chi_shell_inner[idx],
                    -psi_core[idx],
                ],
                [
                    0.0 + 0.0j,
                    psi_shell_inner_p[idx],
                    chi_shell_inner_p[idx],
                    -shell_core_derivative_factor * psi_core_p[idx],
                ],
            ],
            dtype=complex,
        )
        rhs = np.array(
            [
                -psi_out[idx],
                -psi_out_p[idx],
                0.0 + 0.0j,
                0.0 + 0.0j,
            ],
            dtype=complex,
        )
        solution = np.linalg.solve(matrix, rhs)
        coeffs[idx] = solution[0]
    return coeffs


def mie_coefficients(size_parameter: float, m_rel: complex):
    """
    Compute Mie scattering coefficients a_n, b_n.

    Args:
        size_parameter: x = k·a = 2π·n_m·a/λ₀
        m_rel: Relative complex refractive index m = ñ_p / n_m

    Returns:
        a_n: array of complex Mie coefficients, n=1..nmax
        b_n: array of complex Mie coefficients, n=1..nmax
    """
    x = size_parameter
    if x < 1e-10:
        # Essentially no scattering for zero-size particle
        return np.array([0.0 + 0j]), np.array([0.0 + 0j])

    nmax = _compute_nmax(x)
    D = _log_derivative_downward(m_rel, x, nmax)
    psi, xi = _riccati_bessel(x, nmax)

    # Also need psi[n-1] for recurrence — prepend psi[0] = sin(x)
    psi_prev = np.zeros(nmax, dtype=float)
    psi_prev[0] = np.sin(x)
    psi_prev[1:] = psi[:-1]

    xi_prev = np.zeros(nmax, dtype=complex)
    xi_prev[0] = np.sin(x) - 1j * np.cos(x)  # ξ_0 = ψ_0 - i·χ_0
    xi_prev[1:] = xi[:-1]

    n_arr = np.arange(1, nmax + 1, dtype=float)

    a_n = (D / m_rel + n_arr / x) * psi - psi_prev
    a_n /= (D / m_rel + n_arr / x) * xi - xi_prev

    b_n = (m_rel * D + n_arr / x) * psi - psi_prev
    b_n /= (m_rel * D + n_arr / x) * xi - xi_prev

    return a_n, b_n


def mie_core_shell_coefficients(
    outer_size_parameter: float,
    core_radius_ratio: float,
    m_shell_rel: complex,
    m_core_rel: complex,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute Mie coefficients for a concentric core-shell sphere.

    Args:
        outer_size_parameter: x = k_m * b for the outer radius b.
        core_radius_ratio: a / b for the inner core radius a.
        m_shell_rel: Relative shell refractive index n_shell / n_medium.
        m_core_rel: Relative core refractive index n_core / n_medium.

    Notes:
        This routine solves the coated-sphere boundary-matching system
        multipole-by-multipole. A regression test in tests/test_physics_core.py
        verifies that when m_core_rel == m_shell_rel, the result collapses to
        the standard homogeneous-sphere coefficients to machine precision.
    """
    x_outer = float(outer_size_parameter)
    if x_outer < 1e-10:
        return np.array([0.0 + 0j]), np.array([0.0 + 0j])

    if not (0.0 <= core_radius_ratio < 1.0):
        raise ValueError(
            "core_radius_ratio must be in [0, 1), "
            f"got {core_radius_ratio}"
        )

    if core_radius_ratio < 1e-8:
        return mie_coefficients(x_outer, m_shell_rel)

    x_core = x_outer * float(core_radius_ratio)
    nmax = _compute_nmax(x_outer)
    a_n = -_solve_core_shell_mode(
        nmax,
        x_outer,
        x_core,
        m_shell_rel,
        m_core_rel,
        electric_coefficient=True,   # a_n: TM/electric, factor = 1/m
    )
    b_n = -_solve_core_shell_mode(
        nmax,
        x_outer,
        x_core,
        m_shell_rel,
        m_core_rel,
        electric_coefficient=False,  # b_n: TE/magnetic, factor = m
    )
    return a_n, b_n


def mie_efficiencies_from_coefficients(
    size_parameter: float,
    a_n: np.ndarray,
    b_n: np.ndarray,
) -> tuple[float, float]:
    """Compute Qext/Qsca from precomputed Mie coefficients."""
    if size_parameter < 1e-10:
        return 0.0, 0.0

    nmax = len(a_n)
    n_arr = np.arange(1, nmax + 1, dtype=float)
    prefactor = 2.0 / size_parameter**2
    Qext = prefactor * np.sum((2 * n_arr + 1) * np.real(a_n + b_n))
    Qsca = prefactor * np.sum((2 * n_arr + 1) * (np.abs(a_n)**2 + np.abs(b_n)**2))
    return float(Qext), float(Qsca)


def mie_compute(size_parameter: float, m_rel: complex) -> tuple[float, float]:
    """
    Compute Mie extinction and scattering efficiencies.

    Args:
        size_parameter: x = k·a
        m_rel: Relative complex refractive index

    Returns:
        (Qext, Qsca): Extinction and scattering efficiency factors.
    """
    if size_parameter < 1e-10:
        return 0.0, 0.0

    a_n, b_n = mie_coefficients(size_parameter, m_rel)
    return mie_efficiencies_from_coefficients(size_parameter, a_n, b_n)


def _pi_tau(nmax: int, mu: np.ndarray):
    """
    Compute angle-dependent functions π_n(cosθ) and τ_n(cosθ).

    Uses upward recurrence:
        π_1 = 1,  π_2 = 3μ
        π_n = ((2n-1)·μ·π_{n-1} - n·π_{n-2}) / (n-1)
        τ_n = n·μ·π_n - (n+1)·π_{n-1}

    Args:
        nmax: Maximum order
        mu: cos(θ) array, shape (N,)

    Returns:
        pi_n: shape (nmax, N)
        tau_n: shape (nmax, N)
    """
    N = len(mu)
    pi_n = np.zeros((nmax, N), dtype=float)
    tau_n = np.zeros((nmax, N), dtype=float)

    pi_n[0, :] = 1.0  # π_1 = 1
    if nmax > 1:
        pi_n[1, :] = 3.0 * mu  # π_2 = 3μ

    tau_n[0, :] = mu       # τ_1 = μ·π_1 - 2·π_0, but π_0=0 → τ_1 = μ
    if nmax > 1:
        tau_n[1, :] = 2 * mu * pi_n[1, :] - 3 * pi_n[0, :]

    for n in range(3, nmax + 1):
        idx = n - 1  # 0-based index
        pi_n[idx, :] = (
            (2 * n - 1) * mu * pi_n[idx - 1, :]
            - n * pi_n[idx - 2, :]
        ) / (n - 1)
        tau_n[idx, :] = n * mu * pi_n[idx, :] - (n + 1) * pi_n[idx - 1, :]

    return pi_n, tau_n


def mie_angular_from_coefficients(
    a_n: np.ndarray,
    b_n: np.ndarray,
    theta_grid_rad: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute S1/S2 from precomputed Mie coefficients."""
    nmax = len(a_n)
    mu = np.cos(theta_grid_rad)
    pi_n, tau_n = _pi_tau(nmax, mu)

    n_arr = np.arange(1, nmax + 1, dtype=float)
    prefactor = (2 * n_arr + 1) / (n_arr * (n_arr + 1))

    S1 = np.zeros(len(theta_grid_rad), dtype=complex)
    S2 = np.zeros(len(theta_grid_rad), dtype=complex)

    for i in range(nmax):
        S1 += prefactor[i] * (a_n[i] * pi_n[i, :] + b_n[i] * tau_n[i, :])
        S2 += prefactor[i] * (a_n[i] * tau_n[i, :] + b_n[i] * pi_n[i, :])

    return S1, S2


def mie_angular(
    size_parameter: float,
    m_rel: complex,
    theta_grid_rad: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute angular scattering amplitude functions S1(θ) and S2(θ).

    S1(θ) = Σ_n (2n+1)/(n(n+1)) · [a_n·π_n(cosθ) + b_n·τ_n(cosθ)]
    S2(θ) = Σ_n (2n+1)/(n(n+1)) · [a_n·τ_n(cosθ) + b_n·π_n(cosθ)]

    Args:
        size_parameter: x = k·a
        m_rel: Relative complex refractive index
        theta_grid_rad: Array of scattering angles in radians

    Returns:
        (S1, S2): Complex arrays, shape = (len(theta_grid_rad),)
    """
    if size_parameter < 1e-10:
        return np.zeros_like(theta_grid_rad, dtype=complex), \
               np.zeros_like(theta_grid_rad, dtype=complex)

    a_n, b_n = mie_coefficients(size_parameter, m_rel)
    return mie_angular_from_coefficients(a_n, b_n, theta_grid_rad)
