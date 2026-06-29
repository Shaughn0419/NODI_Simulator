"""Cross-section geometry primitives for channel-sidewall propagation."""

from __future__ import annotations

from dataclasses import dataclass
import math


TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION = "trapezoid_straight_sidewall_v1"
CENTER_ACCESSIBLE_SUPPORT_MODEL = "wall_normal_half_plane_offset_v1"
TRAPEZOID_WALL_DISTANCE_MODEL = "trapezoid_signed_wall_distance_v1"
DEFAULT_CLOSURE_POLICY = "preserve_unclipped_descriptor"
DEFAULT_NEAR_CLOSED_THRESHOLD_M = 80.0e-9


def comsol_sidewall_deg_to_nodi_taper_deg(sidewall_deg_comsol: float) -> float:
    """Convert COMSOL sidewall angle from horizontal to NODI taper from vertical."""
    value = float(sidewall_deg_comsol)
    if not (0.0 < value <= 90.0):
        raise ValueError(
            "sidewall_deg_comsol must be in (0, 90], got "
            f"{sidewall_deg_comsol}"
        )
    return 90.0 - value


def nodi_taper_deg_to_comsol_sidewall_deg(sidewall_taper_angle_deg: float) -> float:
    """Convert NODI taper from vertical to COMSOL sidewall angle from horizontal."""
    value = float(sidewall_taper_angle_deg)
    if not (0.0 <= value < 45.0):
        raise ValueError(
            "sidewall_taper_angle_deg must be in [0, 45), got "
            f"{sidewall_taper_angle_deg}"
        )
    return 90.0 - value


@dataclass(frozen=True)
class TrapezoidCrossSection:
    """Symmetric straight-sidewall trapezoid with x centered and u measured from top."""

    top_width_m: float
    depth_m: float
    sidewall_taper_angle_deg: float
    closure_policy: str = DEFAULT_CLOSURE_POLICY
    near_closed_threshold_m: float = DEFAULT_NEAR_CLOSED_THRESHOLD_M
    cross_section_geometry_version: str = TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION

    def __post_init__(self) -> None:
        if self.top_width_m <= 0.0:
            raise ValueError(f"top_width_m must be positive, got {self.top_width_m}")
        if self.depth_m <= 0.0:
            raise ValueError(f"depth_m must be positive, got {self.depth_m}")
        if not (0.0 <= self.sidewall_taper_angle_deg < 45.0):
            raise ValueError(
                "sidewall_taper_angle_deg must be in [0, 45), got "
                f"{self.sidewall_taper_angle_deg}"
            )
        if self.near_closed_threshold_m < 0.0:
            raise ValueError(
                "near_closed_threshold_m must be non-negative, got "
                f"{self.near_closed_threshold_m}"
            )

    @property
    def taper_rad(self) -> float:
        return math.radians(self.sidewall_taper_angle_deg)

    @property
    def k_taper(self) -> float:
        return math.tan(self.taper_rad)

    @property
    def bottom_width_unclipped_m(self) -> float:
        return self.top_width_m - 2.0 * self.depth_m * self.k_taper

    @property
    def bottom_width_runtime_clipped_m(self) -> float:
        return max(self.bottom_width_unclipped_m, 0.0)

    @property
    def closure_depth_m(self) -> float:
        if self.k_taper <= 0.0:
            return math.inf
        return self.top_width_m / (2.0 * self.k_taper)

    @property
    def closure_status(self) -> str:
        if self.bottom_width_unclipped_m <= 0.0 or self.depth_m >= self.closure_depth_m:
            return "geometry_closed"
        if self.bottom_width_unclipped_m <= self.near_closed_threshold_m:
            return "near_closed"
        return "open"

    def width_at_depth_m(self, u_m: float, *, clipped: bool = False) -> float:
        width_m = self.top_width_m - 2.0 * self.k_taper * float(u_m)
        if clipped:
            return max(width_m, 0.0)
        return width_m

    def half_width_at_depth_m(self, u_m: float, *, clipped: bool = False) -> float:
        return 0.5 * self.width_at_depth_m(u_m, clipped=clipped)

    def wall_distances_m(self, x_m: float, u_m: float) -> dict[str, float]:
        """Return signed distances to each wall; negative means outside support."""
        x = float(x_m)
        u = float(u_m)
        side_norm = math.sqrt(1.0 + self.k_taper**2)
        right_side_m = (self.half_width_at_depth_m(u) - x) / side_norm
        left_side_m = (x + self.half_width_at_depth_m(u)) / side_norm
        return {
            "top": u,
            "bottom": self.depth_m - u,
            "left_side": left_side_m,
            "right_side": right_side_m,
        }

    def nearest_wall_distance_m(self, x_m: float, u_m: float) -> float:
        return min(self.wall_distances_m(x_m, u_m).values())

    def particle_wall_gap_diagnostics_m(
        self,
        x_m: float,
        u_m: float,
        particle_radius_m: float,
    ) -> dict[str, float | str]:
        """Return geometry-only wall distance and particle surface-gap diagnostics."""
        radius_m = float(particle_radius_m)
        if radius_m < 0.0:
            raise ValueError(f"particle_radius_m must be non-negative, got {radius_m}")

        distances_m = self.wall_distances_m(x_m, u_m)
        nearest_wall_id = min(distances_m, key=distances_m.__getitem__)
        d_nearest_wall_m = distances_m[nearest_wall_id]
        return {
            "wall_distance_model": TRAPEZOID_WALL_DISTANCE_MODEL,
            "wall_distance_claim_level": (
                "geometry_distance_primitive_not_hindered_diffusion"
            ),
            "d_top_m": distances_m["top"],
            "d_bottom_m": distances_m["bottom"],
            "d_side_left_m": distances_m["left_side"],
            "d_side_right_m": distances_m["right_side"],
            "d_nearest_wall_m": d_nearest_wall_m,
            "nearest_wall_id": nearest_wall_id,
            "surface_gap_for_particle_m": d_nearest_wall_m - radius_m,
        }

    def center_accessible_width_at_depth_m(
        self,
        u_m: float,
        particle_radius_m: float,
    ) -> float:
        radius_m = float(particle_radius_m)
        if radius_m < 0.0:
            raise ValueError(f"particle_radius_m must be non-negative, got {radius_m}")
        u = float(u_m)
        if u < radius_m or u > self.depth_m - radius_m:
            return 0.0
        side_exclusion_m = radius_m * math.sqrt(1.0 + self.k_taper**2)
        center_width_m = self.width_at_depth_m(u) - 2.0 * side_exclusion_m
        return max(center_width_m, 0.0)

    def center_accessible_u_bounds_m(
        self,
        particle_radius_m: float,
    ) -> tuple[float, float] | None:
        radius_m = float(particle_radius_m)
        if radius_m < 0.0:
            raise ValueError(f"particle_radius_m must be non-negative, got {radius_m}")
        u_low_m = radius_m
        u_high_m = self.depth_m - radius_m
        if u_high_m <= u_low_m:
            return None

        side_exclusion_m = radius_m * math.sqrt(1.0 + self.k_taper**2)
        available_top_m = self.top_width_m - 2.0 * side_exclusion_m
        if available_top_m <= 0.0:
            return None
        if self.k_taper > 0.0:
            u_high_m = min(u_high_m, available_top_m / (2.0 * self.k_taper))
        if u_high_m <= u_low_m:
            return None
        return u_low_m, u_high_m

    def center_accessible_x_bounds_at_depth_m(
        self,
        u_m: float,
        particle_radius_m: float,
    ) -> tuple[float, float]:
        radius_m = float(particle_radius_m)
        if radius_m < 0.0:
            raise ValueError(f"particle_radius_m must be non-negative, got {radius_m}")
        side_exclusion_m = radius_m * math.sqrt(1.0 + self.k_taper**2)
        right_m = self.half_width_at_depth_m(u_m) - side_exclusion_m
        right_m = max(right_m, 0.0)
        return -right_m, right_m

    def center_accessible_support_at_depth_m(
        self,
        u_m: float,
        particle_radius_m: float,
        *,
        narrow_width_threshold_m: float = 0.0,
    ) -> dict[str, float | str]:
        """Return particle-center support status for one depth slice."""
        radius_m = float(particle_radius_m)
        threshold_m = float(narrow_width_threshold_m)
        if radius_m < 0.0:
            raise ValueError(f"particle_radius_m must be non-negative, got {radius_m}")
        if threshold_m < 0.0:
            raise ValueError(
                "narrow_width_threshold_m must be non-negative, got "
                f"{threshold_m}"
            )

        u = float(u_m)
        width_m = self.center_accessible_width_at_depth_m(u, radius_m)
        if width_m <= 0.0:
            status = "blocked"
            if self.center_accessible_u_bounds_m(radius_m) is None:
                reason = "zero_center_accessible_area"
            elif u < radius_m:
                reason = "top_clearance_below_particle_radius"
            elif u > self.depth_m - radius_m:
                reason = "bottom_clearance_below_particle_radius"
            else:
                reason = "sidewall_clearance_below_particle_radius"
        elif threshold_m > 0.0 and width_m <= threshold_m:
            status = "narrow"
            reason = ""
        else:
            status = "open"
            reason = ""

        x_left_m, x_right_m = self.center_accessible_x_bounds_at_depth_m(
            u,
            radius_m,
        )
        return {
            "particle_center_support_status": status,
            "steric_block_reason": reason,
            "center_accessible_width_m": width_m,
            "x_left_m": x_left_m,
            "x_right_m": x_right_m,
        }

    def center_accessible_area_m2(self, particle_radius_m: float) -> float:
        radius_m = float(particle_radius_m)
        if radius_m < 0.0:
            raise ValueError(f"particle_radius_m must be non-negative, got {radius_m}")
        bounds = self.center_accessible_u_bounds_m(radius_m)
        if bounds is None:
            return 0.0
        u_low_m, u_high_m = bounds

        side_exclusion_m = radius_m * math.sqrt(1.0 + self.k_taper**2)
        available_top_m = self.top_width_m - 2.0 * side_exclusion_m

        if self.k_taper <= 0.0:
            return available_top_m * (u_high_m - u_low_m)
        area_m2 = (
            available_top_m * (u_high_m - u_low_m)
            - self.k_taper * (u_high_m**2 - u_low_m**2)
        )
        return max(area_m2, 0.0)

    def phase_mask_area_m2(self) -> float:
        if self.k_taper <= 0.0:
            return self.top_width_m * self.depth_m
        u_high_m = min(self.depth_m, self.closure_depth_m)
        if u_high_m <= 0.0:
            return 0.0
        area_m2 = self.top_width_m * u_high_m - self.k_taper * u_high_m**2
        return max(area_m2, 0.0)

    def sample_particle_center_uniform(
        self,
        unit_x: float,
        unit_u: float,
        particle_radius_m: float,
    ) -> tuple[float, float]:
        """Sample uniformly over the particle-center accessible trapezoid area."""
        radius_m = float(particle_radius_m)
        bounds = self.center_accessible_u_bounds_m(radius_m)
        if bounds is None:
            raise ValueError(
                "particle_radius_m leaves no center-accessible support in "
                "the trapezoid cross-section"
            )
        u_low_m, u_high_m = bounds
        unit_depth = float(min(max(unit_u, 0.0), math.nextafter(1.0, 0.0)))
        unit_width = float(min(max(unit_x, 0.0), math.nextafter(1.0, 0.0)))

        side_exclusion_m = radius_m * math.sqrt(1.0 + self.k_taper**2)
        available_top_m = self.top_width_m - 2.0 * side_exclusion_m
        if self.k_taper <= 0.0:
            u_m = u_low_m + unit_depth * (u_high_m - u_low_m)
        else:
            total_area_m2 = self.center_accessible_area_m2(radius_m)
            target_area_m2 = unit_depth * total_area_m2
            constant = (
                target_area_m2
                + available_top_m * u_low_m
                - self.k_taper * u_low_m**2
            )
            discriminant = max(
                available_top_m**2 - 4.0 * self.k_taper * constant,
                0.0,
            )
            u_m = (available_top_m - math.sqrt(discriminant)) / (
                2.0 * self.k_taper
            )
            u_m = min(max(u_m, u_low_m), u_high_m)

        x_left_m, x_right_m = self.center_accessible_x_bounds_at_depth_m(
            u_m,
            radius_m,
        )
        x_m = x_left_m + unit_width * (x_right_m - x_left_m)
        return x_m, u_m

    def contains_particle_center(
        self,
        x_m: float,
        u_m: float,
        particle_radius_m: float,
        *,
        tolerance_m: float = 0.0,
    ) -> bool:
        radius_m = float(particle_radius_m)
        if radius_m < 0.0:
            raise ValueError(f"particle_radius_m must be non-negative, got {radius_m}")
        required_m = radius_m - float(tolerance_m)
        return all(
            distance_m >= required_m
            for distance_m in self.wall_distances_m(x_m, u_m).values()
        )

    def project_particle_center_into_support(
        self,
        x_m: float,
        u_m: float,
        particle_radius_m: float,
    ) -> tuple[float, float]:
        """Clamp a particle center into the wall-normal accessible support."""
        radius_m = float(particle_radius_m)
        bounds = self.center_accessible_u_bounds_m(radius_m)
        if bounds is None:
            raise ValueError(
                "particle_radius_m leaves no center-accessible support in "
                "the trapezoid cross-section"
            )
        u_low_m, u_high_m = bounds
        u_projected_m = min(max(float(u_m), u_low_m), u_high_m)
        x_left_m, x_right_m = self.center_accessible_x_bounds_at_depth_m(
            u_projected_m,
            radius_m,
        )
        x_projected_m = min(max(float(x_m), x_left_m), x_right_m)
        return x_projected_m, u_projected_m
