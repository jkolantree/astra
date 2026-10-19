"""Reduced-order reference calculations for *The Boundary Is a State*.

The module implements transparent mathematical checks used by the preprint:

- conservation under bulk-to-surface exchange;
- passive free-energy dissipation;
- boundary-dominance scaling;
- soft-mode response and its eigenvalue bound;
- exact linear elimination of a relaxing boundary state;
- time-dependent Kramers-type survival functions;
- mass-conserving compartment-closure reset maps;
- Gauss-Bonnet curvature integrals for closed orientable surfaces.

It is not a general interfacial mechanics, spin-texture, or morphogenesis solver.
All quantities are dimensionless unless a function explicitly states otherwise.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import cumulative_trapezoid, solve_ivp
from scipy.linalg import expm

FloatArray = NDArray[np.float64]


def _array(value: ArrayLike, *, ndim: int | None = None) -> FloatArray:
    arr = np.asarray(value, dtype=float)
    if ndim is not None and arr.ndim != ndim:
        raise ValueError(f"Expected ndim={ndim}; received shape {arr.shape}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("Inputs must be finite.")
    return arr


@dataclass(frozen=True)
class ExchangeBalance:
    """Inventory tendencies for bulk regions and their shared interface."""

    bulk: FloatArray
    surface: FloatArray
    total: FloatArray


def bulk_surface_exchange_balance(
    bulk_source: ArrayLike,
    surface_source: ArrayLike,
    flux_bulk_to_surface: ArrayLike,
) -> ExchangeBalance:
    """Return tendencies for internally exchanging bulk and surface reservoirs.

    Parameters
    ----------
    bulk_source:
        External/reaction tendency for each bulk region and species,
        shape ``(n_bulk, n_species)``.
    surface_source:
        External/reaction tendency of the interface, shape ``(n_species,)``.
    flux_bulk_to_surface:
        Positive flux from each bulk region into the interface,
        shape ``(n_bulk, n_species)``.

    Internal transfer is subtracted from bulk inventories and added once to the
    surface inventory, so it cancels exactly in the total balance.
    """

    source_b = _array(bulk_source, ndim=2)
    source_s = _array(surface_source, ndim=1)
    flux = _array(flux_bulk_to_surface, ndim=2)
    if source_b.shape != flux.shape:
        raise ValueError("bulk_source and flux_bulk_to_surface must share shape.")
    if source_b.shape[1] != source_s.size:
        raise ValueError("surface_source must have one entry per species.")

    bulk_dot = source_b - flux
    surface_dot = source_s + np.sum(flux, axis=0)
    total_dot = np.sum(bulk_dot, axis=0) + surface_dot
    return ExchangeBalance(bulk=bulk_dot, surface=surface_dot, total=total_dot)


def passive_free_energy_rate(
    bulk_gradients: ArrayLike,
    bulk_mobility: ArrayLike,
    surface_gradients: ArrayLike,
    surface_mobility: ArrayLike,
    adsorption_affinity: ArrayLike,
    adsorption_mobility: ArrayLike,
    order_force: ArrayLike,
    order_mobility: ArrayLike,
    shape_force: ArrayLike,
    shape_mobility: ArrayLike,
) -> float:
    """Evaluate a discrete passive dissipation identity.

    The returned value is ``dF/dt`` for closed, isothermal, unforced dynamics:

    ``-g_b^T M_b g_b - g_s^T M_s g_s - A^T L A
      - f_q^T L_q f_q - f_Gamma^T M_Gamma f_Gamma``.

    Each mobility can be a scalar, diagonal vector, or square matrix. Symmetric
    positive-semidefinite mobilities guarantee a non-positive result. Matrices
    use diagonal congruence scaling, reject negative diagonals and nonzero
    zero-diagonal rows, and clip only dimensionless eigensolver roundoff.
    Decimal accumulation avoids intermediate overflow/underflow in these small
    reference quadratics. This policy is not evidence of physical passivity.
    """

    def quadratic(force: ArrayLike, mobility: ArrayLike) -> float:
        f = _array(force, ndim=1)
        m = _array(mobility)

        def finite_result(value: Decimal) -> float:
            result = float(value)
            if not math.isfinite(result):
                raise ValueError("Dissipation exceeds the finite numerical range.")
            return result

        if f.size == 0:
            raise ValueError("Force must be nonempty.")
        if m.ndim == 0:
            if float(m) < 0.0:
                raise ValueError("Scalar mobility must be nonnegative.")
            m = np.full(f.size, float(m))
        if m.ndim == 1:
            if m.size != f.size or np.any(m < 0.0):
                raise ValueError("Diagonal mobility must be nonnegative and match force size.")
            with localcontext() as ctx:
                ctx.prec = 80
                return finite_result(
                    sum(
                        (
                            Decimal.from_float(float(w)) * Decimal.from_float(float(x)) ** 2
                            for w, x in zip(m, f, strict=True)
                        ),
                        Decimal(0),
                    )
                )
        if m.ndim == 2:
            if m.shape != (f.size, f.size):
                raise ValueError("Mobility matrix shape mismatch.")
            # Stable midpoint includes subnormal entries and avoids m+m.T overflow.
            with localcontext() as ctx:
                ctx.prec = 80
                sym = np.array(
                    [
                        [
                            float(
                                (
                                    Decimal.from_float(float(m[i, j]))
                                    + Decimal.from_float(float(m[j, i]))
                                )
                                / 2
                            )
                            for j in range(f.size)
                        ]
                        for i in range(f.size)
                    ]
                )
            diagonal = np.diag(sym)
            if np.any(diagonal < 0):
                raise ValueError("Symmetric mobility part must be positive semidefinite.")
            positive = diagonal > 0
            if np.any(sym[~positive, :] != 0) or np.any(sym[:, ~positive] != 0):
                raise ValueError("A zero mobility diagonal requires a zero row and column.")
            if not np.any(positive):
                return 0.0
            roots = np.sqrt(diagonal[positive])
            correlation = sym[np.ix_(positive, positive)] / roots[:, None] / roots[None, :]
            if not np.all(np.isfinite(correlation)):
                raise ValueError("Invalid scaled mobility.")
            eigenvalues, eigenvectors = np.linalg.eigh(correlation)
            tolerance = 8 * np.finfo(float).eps * max(1, roots.size)
            if np.min(eigenvalues) < -tolerance:
                raise ValueError("Symmetric mobility part must be positive semidefinite.")
            with localcontext() as ctx:
                ctx.prec = 80
                weighted_force = [
                    Decimal.from_float(float(root)) * Decimal.from_float(float(x))
                    for root, x in zip(roots, f[positive], strict=True)
                ]
                terms = []
                for value, vector in zip(np.maximum(eigenvalues, 0), eigenvectors.T, strict=True):
                    projected = sum(
                        (
                            Decimal.from_float(float(v)) * x
                            for v, x in zip(vector, weighted_force, strict=True)
                        ),
                        Decimal(0),
                    )
                    terms.append(Decimal.from_float(float(value)) * projected**2)
                return finite_result(sum(terms, Decimal(0)))
        raise ValueError("Mobility must be scalar, vector, or matrix.")

    dissipation = (
        quadratic(bulk_gradients, bulk_mobility)
        + quadratic(surface_gradients, surface_mobility)
        + quadratic(adsorption_affinity, adsorption_mobility)
        + quadratic(order_force, order_mobility)
        + quadratic(shape_force, shape_mobility)
    )
    if not math.isfinite(dissipation):
        raise ValueError("Total dissipation exceeds the finite numerical range.")
    return -float(dissipation)


def boundary_dominance(
    surface_energy_scale: float,
    bulk_energy_scale: float,
    area_to_volume: float,
) -> float:
    """Return D_Gamma = (psi_Gamma*/psi_bulk*) (A/V).

    ``surface_energy_scale`` has units energy/area and ``bulk_energy_scale``
    energy/volume. Both are characteristic positive magnitudes, not signed net
    free energies.
    """

    if surface_energy_scale < 0.0 or bulk_energy_scale <= 0.0 or area_to_volume < 0.0:
        raise ValueError("Energy scales and A/V must be nonnegative; bulk scale positive.")
    return float(surface_energy_scale / bulk_energy_scale * area_to_volume)


def film_boundary_dominance(
    surface_energy_scale: float, bulk_energy_scale: float, thickness: float
) -> float:
    """Boundary dominance for a wide film with two active faces, A/V ~= 2/h."""

    if thickness <= 0.0:
        raise ValueError("thickness must be positive.")
    return boundary_dominance(surface_energy_scale, bulk_energy_scale, 2.0 / thickness)


def sphere_boundary_dominance(
    surface_energy_scale: float, bulk_energy_scale: float, radius: float
) -> float:
    """Boundary dominance for a sphere, A/V = 3/R."""

    if radius <= 0.0:
        raise ValueError("radius must be positive.")
    return boundary_dominance(surface_energy_scale, bulk_energy_scale, 3.0 / radius)


@dataclass(frozen=True)
class SoftModeResponse:
    response: FloatArray
    response_norm: float
    upper_bound: float
    lambda_min: float


def soft_mode_response(
    stiffness: ArrayLike, coupling: ArrayLike, delta_control: ArrayLike
) -> SoftModeResponse:
    """Solve K dz = G du and return the spectral-norm response bound."""

    K = _array(stiffness, ndim=2)
    G = _array(coupling, ndim=2)
    du = _array(delta_control, ndim=1)
    if K.shape[0] != K.shape[1]:
        raise ValueError("stiffness must be square.")
    if G.shape != (K.shape[0], du.size):
        raise ValueError("coupling shape mismatch.")
    Ks = 0.5 * (K + K.T)
    eig = np.linalg.eigvalsh(Ks)
    lam = float(np.min(eig))
    if lam <= 0.0:
        raise ValueError("The local stiffness must be positive definite for the linear bound.")
    response = np.asarray(np.linalg.solve(Ks, G @ du), dtype=np.float64)
    bound = float(np.linalg.norm(G, 2) * np.linalg.norm(du, 2) / lam)
    return SoftModeResponse(
        response=response,
        response_norm=float(np.linalg.norm(response, 2)),
        upper_bound=bound,
        lambda_min=lam,
    )


@dataclass(frozen=True)
class LinearBoundaryParameters:
    bulk_decay: float
    boundary_to_bulk: float
    direct_gain: float
    boundary_drive: float
    boundary_time: float

    def validate(self) -> None:
        if self.bulk_decay <= 0.0 or self.boundary_time <= 0.0:
            raise ValueError("bulk_decay and boundary_time must be positive.")


def simulate_dynamic_boundary(
    time: ArrayLike,
    forcing: Callable[[float], float],
    parameters: LinearBoundaryParameters,
    initial: Sequence[float] = (0.0, 0.0),
) -> FloatArray:
    """Simulate a minimal bulk state x coupled to a relaxing boundary state b.

    dx/dt = -a x + c b + g u(t)
    tau db/dt = d u(t) - b

    Returns an array with rows ``x`` and ``b``.
    """

    parameters.validate()
    t = _array(time, ndim=1)
    if t.size < 2 or np.any(np.diff(t) <= 0.0):
        raise ValueError("time must be strictly increasing with at least two points.")
    y0 = _array(initial, ndim=1)
    if y0.size != 2:
        raise ValueError("initial must contain x and b.")
    p = parameters

    def rhs(tt: float, state: FloatArray) -> list[float]:
        u = float(forcing(tt))
        x, b = state
        return [
            -p.bulk_decay * x + p.boundary_to_bulk * b + p.direct_gain * u,
            (p.boundary_drive * u - b) / p.boundary_time,
        ]

    sol = solve_ivp(
        rhs,
        (float(t[0]), float(t[-1])),
        y0,
        t_eval=t,
        max_step=max(float(np.min(np.diff(t))) / 3.0, 1e-4),
        rtol=1e-9,
        atol=1e-11,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    return np.asarray(sol.y, dtype=float)


def simulate_quasistatic_boundary(
    time: ArrayLike,
    forcing: Callable[[float], float],
    bulk_decay: float,
    effective_gain: float,
    initial: float = 0.0,
) -> FloatArray:
    """Simulate the algebraic-boundary reduction dx/dt=-a x+g_eff u(t)."""

    if bulk_decay <= 0.0:
        raise ValueError("bulk_decay must be positive.")
    t = _array(time, ndim=1)

    def rhs(tt: float, state: FloatArray) -> list[float]:
        return [-bulk_decay * float(state[0]) + effective_gain * float(forcing(tt))]

    sol = solve_ivp(
        rhs,
        (float(t[0]), float(t[-1])),
        [float(initial)],
        t_eval=t,
        max_step=max(float(np.min(np.diff(t))) / 3.0, 1e-4),
        rtol=1e-9,
        atol=1e-11,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    return np.asarray(sol.y[0], dtype=float)


def dynamic_boundary_transfer_function(
    omega: ArrayLike,
    parameters: LinearBoundaryParameters,
) -> NDArray[np.complex128]:
    """Frequency response x(omega)/u(omega) for the linear boundary model."""

    parameters.validate()
    w = _array(omega)
    p = parameters
    s = 1j * w
    return (p.direct_gain + p.boundary_to_bulk * p.boundary_drive / (1.0 + s * p.boundary_time)) / (
        s + p.bulk_decay
    )


def eliminated_boundary_kernel(
    time_lag: ArrayLike, parameters: LinearBoundaryParameters
) -> FloatArray:
    """Memory kernel multiplying past forcing after the boundary is eliminated.

    For the minimal model, the boundary-mediated part is
    ``(c d / tau) exp(-lag/tau)`` for nonnegative lag.
    """

    parameters.validate()
    lag = _array(time_lag)
    if np.any(lag < 0.0):
        raise ValueError("time_lag must be nonnegative.")
    p = parameters
    return p.boundary_to_bulk * p.boundary_drive / p.boundary_time * np.exp(-lag / p.boundary_time)


def exact_linear_step(
    time: ArrayLike,
    parameters: LinearBoundaryParameters,
    step_amplitude: float = 1.0,
    initial: Sequence[float] = (0.0, 0.0),
) -> FloatArray:
    """Exact step response with initial state imposed at time[0]."""

    parameters.validate()
    t = _array(time, ndim=1)
    if t.size == 0 or np.any(np.diff(t) <= 0) or not np.isfinite(step_amplitude):
        raise ValueError("nonempty increasing time and finite step amplitude required")
    y0 = _array(initial, ndim=1)
    if y0.size != 2:
        raise ValueError("initial must contain x and b.")
    p = parameters
    A = np.array(
        [
            [-p.bulk_decay, p.boundary_to_bulk],
            [0.0, -1.0 / p.boundary_time],
        ],
        dtype=float,
    )
    f = np.array(
        [p.direct_gain * step_amplitude, p.boundary_drive * step_amplitude / p.boundary_time]
    )
    steady = -np.linalg.solve(A, f)
    out = np.empty((2, t.size), dtype=float)
    for idx, tt in enumerate(t - t[0]):
        out[:, idx] = steady + expm(A * float(tt)) @ (y0 - steady)
    return out


def kramers_rate(
    barrier: ArrayLike,
    temperature_energy: float,
    attempt_rate: ArrayLike | float,
) -> FloatArray:
    """Return k = nu exp(-DeltaF^dagger/kBT) for a declared high-barrier regime."""

    if temperature_energy <= 0.0:
        raise ValueError("temperature_energy must be positive.")
    dF = _array(barrier)
    nu = np.asarray(attempt_rate, dtype=float)
    if np.any(dF < 0.0) or np.any(nu < 0.0):
        raise ValueError("barrier and attempt rate must be nonnegative.")
    return np.asarray(nu * np.exp(-dF / temperature_energy), dtype=float)


@dataclass(frozen=True)
class HazardResult:
    time: FloatArray
    rate: FloatArray
    cumulative_hazard: FloatArray
    survival: FloatArray
    density: FloatArray
    cdf: FloatArray


def time_dependent_hazard(time: ArrayLike, rate: ArrayLike) -> HazardResult:
    """Construct survival and first-passage density from a nonnegative hazard."""

    t = _array(time, ndim=1)
    k = _array(rate, ndim=1)
    if t.shape != k.shape or t.size < 2 or np.any(np.diff(t) <= 0.0):
        raise ValueError("time and rate must match; time must be strictly increasing.")
    if np.any(k < 0.0):
        raise ValueError("rate must be nonnegative.")
    cumulative = cumulative_trapezoid(k, t, initial=0.0)
    survival = np.exp(-cumulative)
    density = k * survival
    return HazardResult(t, k, cumulative, survival, density, 1.0 - survival)


def sample_first_passage(
    hazard: HazardResult,
    uniforms: ArrayLike,
) -> FloatArray:
    """Inverse-CDF samples; returns NaN when the event has not occurred by t_max."""

    u = _array(uniforms)
    if np.any((u <= 0.0) | (u >= 1.0)):
        raise ValueError("uniforms must lie strictly in (0,1).")
    target = u
    cdf = hazard.cdf
    out = np.full(u.shape, np.nan, dtype=float)
    reached = target <= cdf[-1]
    if np.any(reached):
        out[reached] = np.interp(target[reached], cdf, hazard.time)
    return out


@dataclass(frozen=True)
class ClosureReset:
    external_before: float
    external_after: float
    captured_after: float
    total_before: float
    total_after: float


def compartment_closure_reset(
    external_inventory: float,
    captured_volume: float,
    external_concentration: float,
) -> ClosureReset:
    """Create a sealed compartment by capturing a finite external volume.

    The captured inventory is removed from the modeled external reservoir. If the
    environment is treated as infinite, users should instead model it as an
    explicit external source and not claim closed-system conservation.
    """

    if (
        not np.all(np.isfinite([external_inventory, captured_volume, external_concentration]))
        or external_inventory < 0.0
        or captured_volume < 0.0
        or external_concentration < 0.0
    ):
        raise ValueError("Inventories, volumes, and concentrations must be nonnegative.")
    captured = captured_volume * external_concentration
    if not np.isfinite(captured) or captured > external_inventory:
        raise ValueError("Captured inventory exceeds the modeled external inventory.")
    external_after = external_inventory - captured
    return ClosureReset(
        external_before=float(external_inventory),
        external_after=float(external_after),
        captured_after=float(captured),
        total_before=float(external_inventory),
        total_after=float(external_after + captured),
    )


def gauss_bonnet_integral(genus: int = 0, components: int = 1) -> float:
    """Return integral_Gamma K dA = 2 pi chi for closed orientable surfaces.

    Assumes ``components`` identical connected components of genus ``genus``.
    For heterogeneous component genera, call separately and sum.
    """

    if genus < 0 or components < 1 or int(genus) != genus or int(components) != components:
        raise ValueError("genus must be a nonnegative integer and components a positive integer.")
    chi = components * (2 - 2 * genus)
    return float(2.0 * np.pi * chi)


def relative_rmse(predicted: ArrayLike, truth: ArrayLike, scale: float | None = None) -> float:
    """Root-mean-square error normalized by a declared or empirical scale."""

    p = _array(predicted)
    q = _array(truth)
    if p.shape != q.shape:
        raise ValueError("predicted and truth must have identical shape.")
    rmse = float(np.sqrt(np.mean((p - q) ** 2)))
    denom = float(scale) if scale is not None else float(np.std(q))
    if denom <= 0.0:
        raise ValueError("normalization scale must be positive.")
    return rmse / denom


def effective_bulk_stiffness(
    bulk_stiffness: ArrayLike,
    coupling: ArrayLike,
    boundary_stiffness: ArrayLike,
) -> FloatArray:
    """Return the static Schur complement after a stable boundary relaxes.

    For the quadratic free energy

    ``F = 1/2 x.T Kb x + x.T C y + 1/2 y.T Kg y``,

    minimizing over the boundary coordinate ``y`` gives
    ``Keff = Kb - C Kg^{-1} C.T``.  ``Kg`` must be symmetric positive
    definite.  The subtraction is positive semidefinite, so a relaxing stable
    boundary can soften, but not stiffen, the bulk quadratic form under this
    sign convention.
    """

    kb = _array(bulk_stiffness, ndim=2)
    c = _array(coupling, ndim=2)
    kg = _array(boundary_stiffness, ndim=2)
    if kb.shape[0] != kb.shape[1] or kg.shape[0] != kg.shape[1]:
        raise ValueError("bulk_stiffness and boundary_stiffness must be square.")
    if c.shape != (kb.shape[0], kg.shape[0]):
        raise ValueError("coupling must have shape (n_bulk, n_boundary).")
    kb = 0.5 * (kb + kb.T)
    kg = 0.5 * (kg + kg.T)
    if np.min(np.linalg.eigvalsh(kg)) <= 0.0:
        raise ValueError("boundary_stiffness must be positive definite.")
    reduction = np.linalg.solve(kg, c.T)
    out = kb - c @ reduction
    return 0.5 * (out + out.T)


def dynamic_effective_stiffness(
    omega: ArrayLike,
    bulk_stiffness: ArrayLike,
    bulk_damping: ArrayLike,
    coupling: ArrayLike,
    boundary_stiffness: ArrayLike,
    boundary_damping: ArrayLike,
) -> NDArray[np.complex128]:
    """Frequency-dependent bulk operator after linear boundary elimination.

    Returns one matrix per angular frequency:

    ``Keff(w) = Kb + i w Db - C (Kg + i w Dg)^{-1} C.T``.

    This is a reduced linear response identity, not a constitutive law for a
    specific material.  The supplied damping matrices should be symmetric
    positive semidefinite and the boundary dynamic operator must be invertible
    at each requested frequency.
    """

    w = _array(omega)
    kb = _array(bulk_stiffness, ndim=2)
    db = _array(bulk_damping, ndim=2)
    c = _array(coupling, ndim=2)
    kg = _array(boundary_stiffness, ndim=2)
    dg = _array(boundary_damping, ndim=2)
    if kb.shape[0] != kb.shape[1] or db.shape != kb.shape:
        raise ValueError("bulk matrices must be square and share shape.")
    if kg.shape[0] != kg.shape[1] or dg.shape != kg.shape:
        raise ValueError("boundary matrices must be square and share shape.")
    if c.shape != (kb.shape[0], kg.shape[0]):
        raise ValueError("coupling shape mismatch.")
    out = np.empty(w.shape + kb.shape, dtype=np.complex128)
    for idx in np.ndindex(w.shape):
        z = 1j * float(w[idx])
        out[idx] = kb + z * db - c @ np.linalg.solve(kg + z * dg, c.T)
    return out


def critical_film_thickness(
    bulk_coefficient: float,
    strain_shift: float,
    composition_shift: float,
    surface_coefficient_sum: float,
) -> float:
    """Return the positive root of ``a_eff = a0 + a_s/h = 0``.

    Here ``a0 = bulk_coefficient + strain_shift + composition_shift`` and
    ``surface_coefficient_sum`` combines both active faces.  A positive finite
    critical thickness exists only when ``-a_s/a0 > 0``.  The function does not
    claim that a real film follows a one-parameter Landau model; it exposes the
    confounding that thickness simultaneously changes surface leverage and
    often strain relaxation, defects, and confinement.
    """

    a0 = float(bulk_coefficient + strain_shift + composition_shift)
    a_s = float(surface_coefficient_sum)
    if not np.isfinite(a0) or not np.isfinite(a_s):
        raise ValueError("coefficients must be finite.")
    if a0 == 0.0:
        raise ValueError("bulk-plus-shift coefficient is already critical.")
    h = -a_s / a0
    if h <= 0.0:
        raise ValueError("no positive critical thickness exists for these signs.")
    return float(h)


@dataclass(frozen=True)
class ReservoirEmergence:
    """Resolution-aware classification of a geometry-created compartment."""

    component_created: bool
    retention_ratio: float
    is_reservoir: bool


def reservoir_emergence(
    component_count_before: int,
    component_count_after: int,
    exchange_time: float,
    observation_time: float,
    *,
    threshold: float = 10.0,
) -> ReservoirEmergence:
    """Classify whether geometric closure creates a model-resolved reservoir.

    A newly disconnected geometric component is necessary but not sufficient.
    It is promoted to a separate reservoir only when its exchange time is long
    relative to the declared observation time.  ``threshold`` is a modeling
    convention and must be sensitivity-tested; it is not a universal constant.
    """

    if component_count_before < 1 or component_count_after < 1:
        raise ValueError("component counts must be positive integers.")
    if (
        int(component_count_before) != component_count_before
        or int(component_count_after) != component_count_after
    ):
        raise ValueError("component counts must be integers.")
    if exchange_time < 0.0 or observation_time <= 0.0 or threshold <= 0.0:
        raise ValueError("times must be nonnegative/positive and threshold positive.")
    created = component_count_after > component_count_before
    ratio = float(exchange_time / observation_time)
    return ReservoirEmergence(created, ratio, bool(created and ratio >= threshold))


def size_decomposition_design(sizes: ArrayLike, geometry_factor: float = 1.0) -> FloatArray:
    """Design matrix for ``y(L)=beta_bulk+beta_surface*geometry_factor/L``.

    Multiple sizes are required to separate a constant bulk contribution from
    a leading area-to-volume boundary term.  At one size the two coefficients
    are exactly confounded.
    """

    L = _array(sizes, ndim=1)
    if L.size < 1 or np.any(L <= 0.0) or not np.isfinite(geometry_factor):
        raise ValueError("sizes must be positive and geometry_factor finite.")
    return np.column_stack([np.ones_like(L), float(geometry_factor) / L])
