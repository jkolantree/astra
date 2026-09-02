# ASTRA Dark-Medium Response Atlas

## Plasma, condensates, preferred frames, and gravitational roles

**Status:** Unpromoted supplemental research draft, prepared 2026-09-01.
**Repository boundary:** Candidate source for the separately named
`dark-medium-response-atlas/draft-v0.1.0` successor-overlay package. Local
admission does not create a commit, release, Pages route, DOI, publication
identity, or promotion into the SPPT/ASTRA core.
**Evidence boundary:** Not peer reviewed; not an SPPT/ASTRA core claim; not a
dark-matter detection; not evidence for a luminiferous aether; not a release,
DOI, or publication identity. The model-assisted synthesis that prompted this
note is provenance, not scientific evidence or independent verification.

## Abstract

Plasma, aether, and dark matter are often discussed as competing names for an
unknown cosmic substance. They are better treated as answers to three different
questions. **Plasma** specifies a collective charge-response regime. **Aether**
specifies either a material state that selects a rest frame or an independent
preferred-frame field in the laws. **Dark matter** specifies a gravitational
role inferred from dynamics, lensing, and cosmological structure. A physical
sector may satisfy more than one of these descriptions, but none implies the
others.

This note develops a response-first framework for separating them. Its central
derivation is that, in a neutral charge-conjugation-symmetric dark pair plasma,
the mixed linear stress-current responses vanish. Under the additional
equal-pair fluid assumptions, the physical linear modes decouple into a Jeans
branch and a Langmuir branch. The ratio of their characteristic frequencies
depends on the ratio of dark gauge strength to gravitational strength and, for
a self-gravitating equal-pair plasma, is independent of density. Symmetry
breaking, unequal specific pressure response, background fields, streaming,
transport, and nonlinear evolution restore coupling.

The framework also distinguishes a neutral superfluid from a charged
condensate: condensing a field charged under the same unbroken gauge symmetry
that supports a long-range plasma generally Higgses the gauge field. A model
claiming both a long-range dark plasma and an ungapped superfluid mode therefore
needs additional symmetry, additional components, or phase separation.

These results motivate **causal residual spectroscopy**, a working label in
this note for integrating established closure reconstruction and response
methods: infer the unexplained gravitational closure, then classify candidate
sectors by their conserved stress, response poles, damping, causal cones,
order-of-limits behavior, environmental scaling, and held-out predictions. The
integration is methodological and `PROPOSED_ONLY`. It does not identify the
cosmic residual with a plasma, condensate, or aether.

## 1. Scope and vocabulary

The central discipline is to prevent a word from doing the work of an equation.

| Label | Operational question | Characteristic evidence |
|---|---|---|
| Dark matter | Does an additional component or effective response supply the unexplained gravitational influence? | Metric potentials, clustering, lensing, momentum flux, pressure, and anisotropic stress |
| Plasma | Are there mobile charges with collective gauge-field response? | Debye screening, plasma oscillations, transverse modes, shocks, and kinetic instabilities |
| Material preferred frame (“state-aether,” local shorthand) | Does an occupied material state select a timelike velocity or acoustic cone? | The response changes or disappears when density, temperature, or phase changes |
| Vacuum preferred-frame field (“law-aether,” local shorthand) | Does an independent timelike field or preferred cone survive in vacuum? | Preferred-frame modes persist as material density tends to zero |

The historical luminiferous aether was intended as a mechanical carrier for
visible light. A dark plasma whose visible coupling is absent or tiny is not a
resurrection of that object. A relativistic fluid or condensate can select a
rest frame at the level of its state while its underlying equations remain
Lorentz covariant. Conversely, an Einstein-aether model introduces an
independent unit-timelike field into the action and therefore changes the
vacuum degree-of-freedom content.

The most defensible possible overlap is consequently not

> plasma = aether = dark matter,

but

> one hidden sector may gravitate, possess collective charge dynamics, and
> develop a state-defined rest frame, possibly in different phases.

## 2. Start from the unexplained closure

Let $g_{\mu\nu}$ be the metric inferred under declared reconstruction
assumptions, and let
$T^{\mathrm{known}}_{\mu\nu}$ contain the visible stress-energy that has
actually been included in the analysis. Define the geometric closure residual

$$
\mathcal R_{\mu\nu}
\equiv
\frac{G_{\mu\nu}[g]}{8\pi G}
-T^{\mathrm{known}}_{\mu\nu}.
$$

When the known sector is minimally coupled and separately conserved, the
Bianchi identity gives

$$
\nabla^\mu \mathcal R_{\mu\nu}=0.
$$

This is a bookkeeping identity, not proof that the residual is material. In
general relativity, a dark-matter theory puts additional stress-energy on the
right-hand side. A modified-gravity theory can be rewritten with effective
terms in the same position. Purely gravitational reconstruction therefore
does not uniquely establish the underlying ontology.

Nevertheless, the residual imposes a useful minimum standard. Relative to a
declared observer four-velocity and perturbation gauge—or in gauge-invariant
variables—a proposed explanation must close as density, momentum, pressure,
and anisotropic stress. These are inferred, model-dependent reconstruction
objects, not directly observed fields. A fitted acceleration curve without a
conserved dynamical completion is not yet a complete covariant physical model.

For perturbations, write a causal response relation schematically as

$$
\delta \mathcal R_A(\mathbf k,t)
=\delta \mathcal R^{\mathrm{hom}}_A(\mathbf k,t)
+\int_{-\infty}^{t}
K_{AB}(\mathbf k;t,t')S_B(\mathbf k,t')\,dt'.
$$

Here $A$ ranges over residual density, momentum, pressure, and anisotropic
stress, while $S_B$ contains metric, baryonic, and other declared sources.
Different models can reproduce a similar static residual while possessing
different causal memory:

- collisionless matter retains orbital and phase-space memory;
- a collisional fluid develops relaxation and viscous poles;
- a plasma possesses charge and electromagnetic collective modes;
- a superfluid possesses phase and vortex response;
- a fundamental aether can possess preferred-frame modes even without matter.

The response kernel does not eliminate modeling. It makes the assumptions and
the discriminating observables explicit before an ontology is assigned.

## 3. Response-first classification

Introduce a metric source $h_{\mu\nu}$ and a provisional dark gauge source
$a^D_\mu$. On a stationary homogeneous background—or within a declared local
WKB approximation—the retarded linear response may be arranged as

$$
\begin{pmatrix}
\delta T^{\mu\nu}\\[2pt]
\delta J_D^\mu
\end{pmatrix}
=
\begin{pmatrix}
\chi_{TT} & \chi_{TJ}\\
\chi_{JT} & \chi_{JJ}
\end{pmatrix}_{(\omega,\mathbf k)}
\begin{pmatrix}
h_{\alpha\beta}\\[2pt]
a_D^\alpha
\end{pmatrix}.
$$

Every $\chi$ in this display is retarded. In a cosmological background the
two-time kernel of Section 2 replaces this Fourier representation. Gauge and
diffeomorphism Ward identities, including their contact terms, must be imposed
before interpreting any component of the matrix.

After gauge fixing and constraint elimination, a pole of a gauge-invariant
retarded correlator can identify a collective oscillation, damped mode, or
instability. Pole position gives a frequency and damping or growth rate;
residue gives source overlap for a simple propagating pole. Branch cuts encode
continua and phase mixing. Dissipative modes are instead audited through
spectral positivity or passivity and, for stable states, poles in the lower
half of the complex-frequency plane. This supplies an operational taxonomy:

| Candidate regime | Leading response features |
|---|---|
| Cold collisionless dust | Jeans growth and autonomous initial-condition modes |
| Collisionless kinetic matter | Jeans growth, velocity-space phase mixing, kinetic branch cuts |
| Normal plasma | Debye screening, Langmuir gap, transverse gauge modes, Landau damping, two-stream or Weibel instability |
| Neutral superfluid | Gapless Goldstone sound, critical velocity, vortices, multiphonon continuum |
| Charged condensate | Gauge-field mass, Meissner screening, gapped plasma response |
| Einstein-aether-type field | Additional spin-0 and spin-1 modes, preferred-frame dependence, vacuum survival |

The names become secondary. Two models that generate similar static gravity
can still be separated by their poles, damping, entropy production, and
response to interventions.

## 4. Charge-conjugation linear-response decoupling

Consider a hidden sector whose microscopic dynamics, state, background, and
regulator are invariant under charge conjugation $C$. Stress is $C$-even and
dark current is $C$-odd. The real-time mixed retarded responses therefore obey

$$
G^R_{TJ}(x)
=-i\theta(t)\langle[T(x),J_D(0)]\rangle
=0,
\qquad
G^R_{JT}(x)=0.
$$

The mixed stress-current two-point responses thus vanish in this symmetric
state. This statement is broader than a particular fluid closure, but its
domain must remain explicit:

- the action and initial or equilibrium state are charge-conjugation invariant;
- there is no background dark electric or magnetic field;
- there is no charge chemical potential or population asymmetry;
- there is no $C$-odd condensate, $C$-violating portal, anomaly, or
  symmetry-breaking regulator;
- the calculation is linear response.

Any one of a nonzero chemical potential, background charge or current,
$C$-odd condensate, or explicit $C$ violation falsifies the decoupling premise.
The result does **not** make the stress response identical to cold dark matter.
Pressure, velocity dispersion, viscosity, collisions, and kinetic damping
remain in $\chi_{TT}$. Exact mode decoupling in the two-fluid benchmark below
additionally requires a neutral background, equal specific pressure response,
and a symmetry-preserving dissipative closure.

This symmetry result is an algebraic consequence of the declared premises. Its
novelty has not been established, and no priority claim is made.

## 5. Ideal pair-plasma calculation

### 5.1 Assumptions and conventions

Use metric signature $(-+++)$ and Heaviside-Lorentz natural units with

$$
c=\hbar=k_B=\epsilon_0=\mu_0=1,
\qquad
\nabla\!\cdot\mathbf E_D=\rho_{q,D},
\qquad
\alpha_D=\frac{q_D^2}{4\pi}.
$$

The primitive model is a homogeneous, neutral, unmagnetized, nonstreaming
two-species plasma under a massless, unbroken $U(1)_D$, with

- equilibrium number densities $n_{+,0}=n_{-,0}=n_0$;
- charges $q_+=+q_D$ and $q_-=-q_D$;
- no background fields, $\mathbf E_{D,0}=\mathbf B_{D,0}=0$;
- Newtonian self-gravity in the usual local Jeans construction;
- a barotropic fluid closure with species sound parameters
  $c_s^2=(\partial P_s/\partial\rho_s)_0$.

This is a fluid-closure benchmark. Its advertised hydrodynamic use requires a
specified collisional or moment closure, stated degeneracy, and scales for
which that closure is controlled; the simplest Debye expansion also assumes
$k\lambda_D\ll1$. Later sections restore $c$ where physical units matter.

The linearized equations are

$$
\dot{\delta n_s}+n_0\nabla\!\cdot\mathbf v_s=0,
$$

$$
\dot{\mathbf v}_s
=-c_s^2\nabla\frac{\delta n_s}{n_0}
-\nabla\Phi
+\frac{q_s}{m_s}\mathbf E_D,
$$

$$
\nabla^2\Phi
=4\pi G\left(m_+\delta n_+ +m_-\delta n_-\right),
\qquad
\nabla\!\cdot\mathbf E_D
=q_D(\delta n_+-\delta n_-).
$$

Gauge-field stress is quadratic in the perturbation because the background
field vanishes. A nonzero background field would add linear magnetic pressure
and anisotropic-stress terms.

### 5.2 Equal-pair modes

For equal masses $m_+=m_-=m$ and equal pressure response, define

$$
\delta n_M=\delta n_++\delta n_-,
\qquad
\delta n_Q=\delta n_+-\delta n_-,
\qquad
\rho_0=2mn_0.
$$

With a symmetry-preserving closure, plane-wave perturbations decouple into

$$
\boxed{
\omega_M^2=c_s^2k^2-4\pi G\rho_0
}
$$

and

$$
\boxed{
\omega_Q^2=c_s^2k^2+\Omega_p^2,
\qquad
\Omega_p^2=\frac{2q_D^2n_0}{m}
}.
$$

The mass mode is a Jeans branch. For sufficiently small $k$,
$\omega_M^2<0$ and it grows. The charge mode is a gapped Langmuir branch. In
the cold, unmagnetized limit a transverse branch additionally obeys

$$
\omega_T^2=k^2+\Omega_p^2.
$$

The thermal coefficient $c_s^2k^2$ is closure-dependent. A collisionless
Maxwellian treatment instead determines longitudinal modes from

$$
\epsilon_L(k,\omega)=0,
$$

including the Bohm-Gross correction in its domain and Landau or collisional
damping. Absence of a weakly damped root over the advertised range falsifies a
claim of a propagating collective mode there. The displayed branches are exact
for the declared linear fluid model, not for all plasma kinetics.

### 5.3 Generic oppositely charged species and mode mixing

For general masses and pressure responses, the system is a generic
oppositely charged two-component plasma, not a charge-conjugate pair. Define

$$
R=m_+\delta n_+ +m_-\delta n_-,
\qquad
Q=\delta n_+-\delta n_-,
$$

$$
M=m_++m_-,
\qquad
\mu=\frac{m_+m_-}{M},
\qquad
\Delta c^2=c_+^2-c_-^2.
$$

Then

$$
\omega^2
\begin{pmatrix}R\\Q\end{pmatrix}
=
\begin{pmatrix}
k^2c_M^2-\omega_J^2 & k^2\mu\,\Delta c^2\\[2pt]
k^2\Delta c^2/M & k^2c_Q^2+\Omega_p^2
\end{pmatrix}
\begin{pmatrix}R\\Q\end{pmatrix},
$$

where

$$
\omega_J^2=4\pi Gn_0M,
\qquad
\Omega_p^2=q_D^2n_0
\left(\frac1{m_+}+\frac1{m_-}\right),
$$

$$
c_M^2=\frac{m_+c_+^2+m_-c_-^2}{M},
\qquad
c_Q^2=\frac{m_-c_+^2+m_+c_-^2}{M}.
$$

The matrix is not symmetric because $R$ and $Q$ carry different units. Its
eigenvalues are

$$
\omega_\pm^2
=\frac{A_M+A_Q}{2}
\pm\frac12
\sqrt{(A_M-A_Q)^2
+4k^4\frac{m_+m_-}{M^2}(\Delta c^2)^2},
$$

with

$$
A_M=k^2c_M^2-\omega_J^2,
\qquad
A_Q=k^2c_Q^2+\Omega_p^2.
$$

The important feature is the off-diagonal dependence on $\Delta c^2$.
Unequal mass alone does not mix the cold center-of-mass and relative modes in
this ideal system; unequal specific pressure response does. When
$|A_Q-A_M|$ is large relative to the off-diagonal terms—typically when
$\Omega_p^2$ is large and the branches are away from a crossing—the induced
correction to the Jeans-like branch is suppressed.

## 6. Plasma and gravitational scale ordering

For the equal-pair, self-gravitating model,

$$
\frac{\Omega_p^2}{\omega_J^2}
=\frac{q_D^2}{4\pi Gm^2}
=\frac{\alpha_D}{Gm^2}.
$$

Define the gravitational coupling between two particles as
$\alpha_G=Gm^2$. Then

$$
\boxed{
\Xi\equiv\frac{\Omega_p^2}{\omega_J^2}
=\frac{\alpha_D}{\alpha_G}
}.
$$

Both frequencies scale as the square root of density. Their ratio does not.
Consequently, an interaction that is tiny relative to visible electromagnetism
may still be enormous relative to particle-particle gravity.

For a plasma composing only a fraction $f_D=\rho_D/\rho_{\mathrm{tot}}$ of
the gravitating density,

$$
\boxed{
\frac{\Omega_p^2}{4\pi G\rho_{\mathrm{tot}}}
=f_D\frac{\alpha_D}{Gm^2}
}.
$$

This is a characteristic-scale comparison, not by itself a mode equation. The
gravitational mode contains $\sum_i\rho_i\delta_i$ and depends on which
components co-perturb.

The corresponding length relation needs more care than the frequency ratio.
For a nonrelativistic Maxwell-Boltzmann plasma with $k_B=1$,

$$
\lambda_D^{-2}=\sum_s\frac{q_s^2n_s}{T_s},
\qquad
\lambda_J=\frac{c_{\mathrm{eff}}}{\sqrt{4\pi G\rho_g}},
$$

and therefore

$$
\frac{\lambda_D}{\lambda_J}
=
\frac{\sqrt{4\pi G\rho_g}}{c_{\mathrm{eff}}}
\left(\sum_s\frac{q_s^2n_s}{T_s}\right)^{-1/2}.
$$

Only for an isothermal equal-pair closure with
$T_+=T_-=T$, $v_T^2=T/m$, $c_{\mathrm{eff}}=v_T$, and
$\rho_g=\rho_D$ does this reduce to

$$
\boxed{
\frac{\lambda_D}{\lambda_J}
=\sqrt{\frac{Gm^2}{\alpha_D}}
=\Xi^{-1/2}
}.
$$

An adiabatic closure introduces the corresponding sound-speed factor. This
qualification prevents a convention-specific identity from being mistaken
for a universal plasma theorem. Relativistic, degenerate, or strongly coupled
screening requires the appropriate static susceptibility rather than the
displayed Maxwell-Boltzmann Debye formula.

## 7. Conservation and cosmological completion

A hidden medium must not silently create or destroy charge or stress-energy.
For a dark gauge current and its field,

$$
\nabla_\mu J_D^\mu=0,
$$

$$
\nabla_\mu T_{\mathrm{particles}}^{\mu\nu}
=\mathcal H^{\nu\lambda}J^D_\lambda,
\qquad
\nabla_\mu T_{\mathcal H}^{\mu\nu}
=-\mathcal H^{\nu\lambda}J^D_\lambda.
$$

Therefore

$$
\nabla_\mu
\left(T_{\mathrm{particles}}^{\mu\nu}+T_{\mathcal H}^{\mu\nu}\right)=0
$$

when there is no declared exchange with another sector. Any portal must include
equal and opposite exchange terms.

The static Jeans construction is a local approximation. The variables
$\delta n_M$ and $\delta n_Q$ above are absolute number-density perturbations.
For an expanding equal-pair background, introduce the fractional contrasts

$$
\Delta_M=\frac{\delta n_++\delta n_-}{2n_0},
\qquad
\Delta_Q=\frac{\delta n_+-\delta n_-}{2n_0}.
$$

Here $a(t)$ is the scale factor, $H\equiv\dot a/a$, $k$ is comoving
wavenumber, and $n_0(t)$ and $\Omega_p(t)$ are physical-background
quantities.

In an appropriate sub-horizon gauge they obey coupled evolution of the form

$$
\ddot\Delta_M+2H\dot\Delta_M
+\frac{c_M^2k^2}{a^2}\Delta_M
=4\pi G\sum_i\rho_i\Delta_i,
$$

$$
\ddot\Delta_Q+2H\dot\Delta_Q
+\left(\frac{c_Q^2k^2}{a^2}+\Omega_p^2\right)\Delta_Q
=\text{mixing, streaming, and background-field terms}.
$$

The plasma frequency, ionization fraction, temperature, and collision rates
evolve with $a$. A viable cosmological model must additionally evolve dark
radiation, recombination, diffusion damping, and metric perturbations through
a Boltzmann hierarchy. Static dispersion relations cannot substitute for that
calculation.

Hidden atomic models make this completion concrete: an early ionized sector
can undergo dark recombination and leave dark-acoustic-oscillation and damping
scales. See [Cyr-Racine and Sigurdson](https://arxiv.org/abs/1209.5752).

## 8. Phase structure and the one-symmetry obstruction

A useful schematic field inventory may contain gravity, a dark gauge field,
charged carriers, a neutral condensate, optional portals, and—only if
independently motivated—a fundamental timelike field:

$$
S=\int d^4x\sqrt{-g}\left[
\frac{M_{\mathrm{Pl}}^2}{2}R
-\frac14\mathcal H_{\mu\nu}\mathcal H^{\mu\nu}
+\mathcal L_{\mathrm{carriers}}(\psi_s,D_\mu)
+P(Y)
+\mathcal L_{\mathrm{portal}}
+\mathcal L_{\mathrm{ae}}(U^\mu)
\right].
$$

Here

$$
M_{\mathrm{Pl}}^{-2}=8\pi G,
\qquad
\mathcal H_{\mu\nu}=2\nabla_{[\mu}X_{\nu]},
\qquad
D_\mu\psi_s=(\nabla_\mu-iq_sX_\mu)\psi_s,
$$

and, for a neutral irrotational condensate away from vortex cores,

$$
Y=\sqrt{-\nabla_\mu\theta\nabla^\mu\theta}.
$$

$P(Y)$ fixes its equation of state; $\mathcal L_{\mathrm{portal}}$ declares
cross-sector exchange; and $\mathcal L_{\mathrm{ae}}$ is only a placeholder
for a separately specified preferred-frame theory. This display is a menu of
distinguishable structures, not one normalized, dynamically complete model.

Possible regimes include:

1. **Normal ionized phase:** mobile dark charges and an unbroken dark gauge
   symmetry produce a dark plasma.
2. **Recombined phase:** neutral bound states can behave approximately as
   atomic or collisionless dark matter on appropriate scales.
3. **Neutral condensate:** a global phase can support a gapless phonon and a
   state-defined velocity.
4. **Charged condensate:** the dark gauge field becomes massive and the phase
   is a dark-superconducting rather than long-range-plasma regime.
5. **Independent aether field:** a separate constrained $U^\mu$ introduces
   vacuum preferred-frame modes.

For a charged condensate $\Psi=ve^{i\theta}$,

$$
|D_\mu\Psi|^2
\supset
v^2(\partial_\mu\theta-q_DX_\mu)^2.
$$

In unitary gauge this supplies

$$
m_X^2\sim q_D^2v^2.
$$

The coefficient depends on the normalization of $\Psi$; the scaling is the
point here. The would-be Goldstone is absorbed and the gauge response is
screened. Thus the stated minimal homogeneous realization with one gauged
$U(1)$ does not generically provide both a long-range dark plasma and a free
gapless superfluid mode. More general multicomponent charged condensates are
not excluded by this argument. A model claiming both structures must exhibit
the additional symmetry, neutral condensate, component, or separated phase
that carries the ungapped mode.

A plausible but unverified branching history is

$$
\text{early dark plasma}
\longrightarrow
\text{dark recombination}
\longrightarrow
\begin{cases}
\text{neutral halo},\\
\text{shock reionization},\\
\text{dissipative disk},\\
\text{neutral condensate}.
\end{cases}
$$

The last three are alternatives with separate cooling, statistics,
thermalization, and stability conditions—not an automatic linear sequence.
Long-range dark-force models, atomic dark matter, and superfluid dark matter
demonstrate portions of this model space, but none has been established as the
cosmic ontology. See [Ackerman et al.](https://arxiv.org/abs/0810.5126) and
[Berezhiani and Khoury](https://arxiv.org/abs/1507.01019).

## 9. Material preferred frame versus vacuum preferred-frame field

For a suitable type-I stress tensor, a Landau-frame velocity may be defined by

$$
T_D^{\mu\nu}u_\nu=-\rho_Du^\mu.
$$

This is a state-defined velocity. It does not close a multistream collisionless
distribution; higher kinetic moments may remain indispensable. For a neutral
superfluid one can instead obtain

$$
u_\mu
=\pm\frac{\partial_\mu\theta}
{\sqrt{-\partial_\alpha\theta\,\partial^\alpha\theta}}
$$

inside the phase where the gradient is timelike and the effective theory is
valid, with the sign chosen so that $u^\mu$ is future-directed. This
single-gradient description fails at vortex cores, and a finite-temperature
superfluid generally has distinct normal and superfluid velocities. Neither
construction requires fundamental Lorentz violation.

A standard Einstein-aether-type action instead contains

$$
\mathcal L_{\mathrm{ae}}
=-M_U^2K^{ab}{}_{mn}
\nabla_aU^m\nabla_bU^n
+\lambda(U^\mu U_\mu+1),
$$

with, in one standard convention,

$$
K^{ab}{}_{mn}
=c_1g^{ab}g_{mn}
+c_2\delta^a_m\delta^b_n
+c_3\delta^a_n\delta^b_m
-c_4U^aU^bg_{mn},
\qquad
c_{13}=c_1+c_3.
$$

The antisymmetrized-derivative model studied by Jacobson and Mattingly, without
matter, is mathematically equivalent only to a restricted sector of
Einstein-Maxwell theory coupled to charged dust; the same analysis identifies
generic gradient singularities. This is a narrow field-equation equivalence,
not an equivalence between general Einstein-aether theory and a screened
two-species plasma. See
[Jacobson and Mattingly](https://doi.org/10.1103/PhysRevD.64.024028).

An operational zero-density diagnostic is

$$
\mathfrak A(\omega,k)
=\lim_{n\rightarrow0}
\left[
\chi(\omega,k;n,u)
-\chi_{\mathrm{Lorentz\ invariant}}(\omega,k)
\right].
$$

The subtraction prescription, the order of $n\to0$, $k\to0$, and
$\omega\to0$, and whether the phase remains continuously defined must all be
declared; the limits need not commute, and the material velocity can cease to
exist before $n=0$. A vanishing result in one tested channel is consistent
with a state response but does not exclude a decoupled vacuum preferred-frame
field. A surviving physical $k\!\cdot U$ dependence after material
contributions are removed is evidence for vacuum preferred-frame structure
only after other vacuum fields have been excluded.

Visible-sector vacuum preferred-frame models are strongly constrained. With
the Einstein-Hilbert normalization in Section 8, define

$$
\bar c_{13}
\equiv
\frac{2M_U^2}{M_{\mathrm{Pl}}^2}(c_1+c_3),
\qquad
c_T^2=\frac{1}{1-\bar c_{13}}.
$$

and multimessenger propagation constrains the relevant tensor-cone mismatch to
approximately the $10^{-15}$ scale in the applicable coupling sector.
Preferred-frame limits are model- and coupling-specific. This does not
prohibit an ordinary Lorentz-covariant medium whose occupied state selects a
rest frame. See the
[post-GW170817 analysis](https://arxiv.org/abs/1802.04303).

## 10. Environmental and merger response

Quasineutrality and a long two-body mean free path do not guarantee collective
collisionlessness. Counterstreaming pair plasmas can excite two-stream and
Weibel modes. Define

$$
\mathcal S
=\Gamma_{\mathrm{inst}}t_{\mathrm{cross}},
\qquad
t_{\mathrm{cross}}=\frac{L}{v_{\mathrm{rel}}}.
$$

Linear amplification is substantial only when $\mathcal S$ contains enough
e-foldings to reach nonlinear saturation:

$$
\boxed{
\mathcal S\gtrsim N_{\mathrm{sat}}
}.
$$

The threshold $N_{\mathrm{sat}}$ is not universally one. It depends on the seed
fluctuations, velocity distribution, composition, geometry, and nonlinear
saturation mechanism, and must be calibrated with kinetic simulations.

Leading scalings nevertheless provide an ensemble-level discriminator:

$$
C_{\mathrm{SIDM}}\sim\rho L\frac{\sigma}{m},
$$

$$
C_{\mathrm{TS}}
\sim\Omega_p\frac{L}{v_{\mathrm{rel}}},
\qquad
C_{\mathrm{W}}
\sim\Omega_p\frac{L}{c}.
$$

For the declared Heaviside-Lorentz equal-pair model,
$\Omega_p=(q_D/m_D)\sqrt{\rho_D}$, where $\rho_D$ is the interacting plasma
density rather than the total halo density. Numerical coefficients and the
actual growth rate depend on the distribution function and geometry.

| Mechanism | Leading density dependence | Leading size dependence | Leading velocity dependence |
|---|---:|---:|---:|
| Constant-cross-section binary SIDM | $\rho$ | $L$ | none beyond trajectory |
| Ideal two-stream plasma | $\sqrt\rho$ | $L$ | $v^{-1}$ |
| Ideal Weibel-dominated plasma | $\sqrt\rho$ | $L$ | approximately weak after crossing-time cancellation |
| Phase-changing medium | threshold-dependent | geometry-dependent | history and hysteresis dependent |
| Propagating aether field | not fixed by material density | $L/c_a$ versus event duration | preferred-frame and cone dependent |

Velocity-dependent scattering and nonlinear plasma saturation can modify these
simple exponents. The correct experiment is therefore a preregistered ensemble
of mergers spanning density, size, speed, orientation, and time since
pericenter—not post-hoc interpretation of one iconic cluster.

Recent particle-in-cell work demonstrates the importance of collective effects
for one completely hidden, massless-$U(1)_D$ pair-plasma model. Its numerical
constraint is model-specific; the general lesson is that binary scattering
alone is an incomplete collision criterion. See
[DeRocco and Giffin](https://doi.org/10.1103/PhysRevD.111.095031).

## 11. Observational gates

### 11.1 Ordinary-plasma gate

Under standard early-universe nuclear and recombination physics, ordinary
baryons cannot simply be relabeled as the dominant dark component. The Planck
base-model values

$$
\Omega_bh^2\simeq0.0224,
\qquad
\Omega_ch^2\simeq0.120,
\qquad
h\equiv\frac{H_0}{100\ {\rm km\,s^{-1}\,Mpc^{-1}}}
$$

are model-conditioned. BBN analyses independently combine observed primordial
D/H with nuclear rates, including the LUNA deuterium-burning rate, to infer a
consistent smaller nucleon inventory. Localized fast radio bursts also provide
a late-universe census of ionized baryons. A successful replacement must
reproduce the gravitational potentials that grow while baryons remain coupled
to photons. See [Planck 2018](https://arxiv.org/abs/1807.06209), the
[LUNA-informed BBN analysis](https://doi.org/10.1038/s41586-020-2878-4), and
the [localized-FRB baryon census](https://doi.org/10.1038/s41586-020-2300-2).

Plasma refraction is chromatic and usually accompanies dispersion or Faraday
effects; metric lensing is achromatic in geometric optics. Lorentz forces also
depend on charge, velocity, and field orientation. Ordinary plasma can bias gas
dynamics and mass reconstruction, but a dominant replacement must
simultaneously explain the baryon budget, neutral stellar motion, lensing,
dispersion and rotation measures, free-free and synchrotron emission, X-rays,
the Sunyaev-Zel'dovich signal, and chromatic-lensing limits.

### 11.2 Early-universe gate

With one frozen physical parameter set and declared nuisance priors, a proposed
dark medium must confront at least:

- the full CMB TT, TE, and EE spectra and CMB lensing;
- primordial abundances;
- baryon acoustic oscillations and linear matter power;
- Lyman-alpha and halo-abundance constraints;
- dark acoustic oscillations, diffusion or collisional damping, and
  $\Delta N_{\rm eff}$.

Fitting only the background expansion or one acoustic feature is insufficient.
Atomic-dark-matter calculations illustrate how these effects must be evolved,
not merely named; see
[Cyr-Racine and Sigurdson](https://arxiv.org/abs/1209.5752).

### 11.3 Gravity and stability gate

The model must provide a complete action or a closed evolution system,
well-posed initial data, conserved total stress-energy, and a stable
perturbative regime. Ghosts, negative spectral weight where unitarity requires
positivity, gradient instabilities, unacceptable strong coupling, or causal
characteristics incompatible with observations reject the affected parameter
region.

A vacuum preferred-frame realization must jointly confront gravitational-wave
speed and polarizations, post-Newtonian preferred-frame coefficients,
binary-pulsar radiation, gravitational slip, and lensing-versus-dynamical mass.
These limits are coupling- and model-specific; see the
[post-GW170817 Einstein-aether analysis](https://arxiv.org/abs/1802.04303).

Galaxy fits must be tested jointly against lensing, pressure-supported systems,
external environments, and assembly history. A quasistatic acceleration law
does not validate its relativistic completion.

### 11.4 Thermodynamic gate

A dissipative component must predict its own recombination, cooling, disk
formation, halo shape, and compact-object abundance. In a region where

$$
t_{\mathrm{cool}}<t_{\mathrm{halo}},
$$

cooling must be evolved jointly with dynamical time, heating, conduction,
angular momentum, fragmentation, and assembly history. Absence of a collapsed
structure excludes only a parameter region that robustly predicts an
observable structure after those processes are included.

### 11.5 Merger-ensemble gate

Freeze $q_D/m_D$, the interacting fraction, phase parameters, nuisance priors,
and acceptance thresholds. Then predict, across a merger ensemble, the
mass-galaxy-gas offsets, shock widths, tails, and halo survival as functions of
$L$, $v_{\rm rel}$, $\rho_D$, orientation, and time since pericenter. A
realization is rejected if systems for which
$\mathcal S=\Gamma_{\rm inst}L/v_{\rm rel}\gg N_{\rm sat}$ robustly predict
collective signatures but lack them, or if each system requires a fresh
physical interpretation. See the
[Bullet Cluster lensing reconstruction](https://arxiv.org/abs/astro-ph/0608407)
and the [dark-plasma kinetic study](https://arxiv.org/abs/2411.11958).

### 11.6 Transfer gate

Before evaluating held-out probes, freeze physical parameters, nuisance priors,
data cuts, and acceptance thresholds. A model calibrated on galaxies should
predict cluster mergers and cosmological structure; a model calibrated on the
CMB should predict halo-scale behavior. Failure of a declared hard gate rejects
that realization rather than triggering a new interpretation. It is not a
rejection of every plasma, condensate, or modified-gravity construction.

## 12. Direct detection and LZ230616

The preliminary LZ preprint reports one NR-like event which, if interpreted as
an elastic xenon nuclear recoil, has

$$
E_R=248\pm23_{\rm stat}\pm23_{\rm sys}\ {\rm keV}_{\rm nr}.
$$

A profile-likelihood test found tension with the background-only hypothesis at
a global significance of $2.6\sigma$ after the look-elsewhere correction, with
a maximum local significance of $3.4\sigma$ across the tested models. This is
not the probability that this particular event is background, and the
collaboration did not claim a dark-matter detection. See the
[LZ analysis preprint](https://lz.lbl.gov/wp-content/uploads/sites/6/2026/08/LZ_Preprint_260901_Dark_Matter_EFT_Nuclear_Recoil_Search_at_Higher_Energies.pdf).

LZ explicitly classifies this as a non-blind analysis: the artificial-event
“salting” distribution did not adequately cover the high-energy signal region,
although the selections and likelihood models were finalized before the four
remaining salt events were revealed. That limitation belongs in any
interpretation of the reported significance.

Using $m_{\rm Xe}\simeq122\ {\rm GeV}/c^2$, the elastic-recoil momentum
transfer is

$$
q_{\rm tr}=\sqrt{2m_{\mathrm{Xe}}E_R}
\simeq
246\pm11_{\rm stat}\pm11_{\rm sys}\ {\rm MeV}/c,
$$

or approximately $246\pm16\ {\rm MeV}/c$ after combining those uncertainties
in quadrature. The reduced spatial scale is
$\hbar/q_{\rm tr}\simeq0.80\ {\rm fm}$.

For the convention

$$
S_A(\mathbf q,\omega)
=\int dt\,e^{i\omega t}
\langle\rho_A(\mathbf q,t)\rho_A(-\mathbf q,0)\rangle,
$$

Fermi's golden rule for two weakly coupled many-body systems can be organized
heuristically as an energy-conserving convolution,

$$
R\propto\int d^3q\,d\omega\,
|\mathcal K(\mathbf q,\omega)|^2
S_D(\mathbf q,-\omega)
S_{\mathrm{Xe}}(-\mathbf q,\omega).
$$

Flux, state normalization, occupation factors, detailed balance, and phase
space are suppressed in this schematic expression. The cited dielectric
formalism supports target-response methods; it does not by itself establish
the incoming collective-dark-medium factor proposed here. See
[Knapen, Kozaczuk, and Lin](https://arxiv.org/abs/2101.08275).

Within the collaboration's tested NREFT and inelastic models under its Standard
Halo Model assumptions, the larger local significances occur typically for
WIMP masses above roughly $200\ {\rm GeV}/c^2$. This is not a
model-independent or hard kinematic lower bound. As an explicitly illustrative
benchmark only, setting $m_D=200\ {\rm GeV}/c^2$ and
$\rho_D=0.3\ {\rm GeV\,cm^{-3}}$ gives

$$
n_D\simeq1.5\times10^{-3}\ {\rm cm^{-3}},
\qquad
a_D\equiv n_D^{-1/3}\simeq9\ {\rm cm},
\qquad
\frac{q_{\rm tr}a_D}{\hbar}\sim10^{14}.
$$

The large last ratio rules out coherence tied merely to the mean interparticle
spacing. It does **not** determine the full spectral response or by itself
prove an impulse regime. Such a claim additionally requires, over the relevant
support,

$$
\frac{q_{\rm tr}\lambda_D}{\hbar}\gg1,
\qquad
\omega_{\rm tr}\gg\Omega_p,
$$

taking $\omega_{\rm tr}\equiv E_R/\hbar$ for the elastic-recoil
interpretation,
together with controlled correlation, bound-state, and condensate effects. A
weak plasma with many particles per Debye sphere normally has
$\lambda_D\gg a_D$, but the relevant parameters have not been inferred from
this event. The decisive calculation is $S_D(q,\omega)$ near
$q\simeq246\ {\rm MeV}/c$; absence of spectral weight there falsifies a claimed
incoming collective contribution. Collective dynamics could still reshape the
halo velocity distribution, streams, directionality, or time dependence. None
of this turns the event into evidence for plasma or aether.

Any proposed connection must supply, prospectively:

1. the visible-dark interaction operator and normalization;
2. the constituent or excitation spectral weight at the measured
   $(q,\omega)$;
3. the abundance and phase-space distribution;
4. the xenon response and nuisance model;
5. predictions for additional exposure, other targets, recoil energy, time,
   and direction.

## 13. Three calibration cases: path, compensation, and threshold

The following cases do not supply evidence that plasma, aether, and dark matter
are one substance. They are calibration cases for the inference problem. Each
shows a different way in which a named mechanism can be read too directly from
an observed outcome.

### 13.1 Returned control, retained state: a gravitational-pulse null

Van Suijlekom, Wondrak, and Falcke study a free massless minimally coupled
scalar test field on a prescribed FLRW background. With

$$
ds^2=-dt^2+a^2(t)ds_\Sigma^2,
\qquad d\tau=a^{-3}dt,
$$

each spatial mode obeys

$$
\psi_\lambda''+\lambda^2a^4(\tau)\psi_\lambda=0.
$$

Their pulse begins and ends with the same scale factor, but the early and late
positive-frequency bases need not agree. The Bogoliubov relation

$$
a_{\lambda,{\rm out}}
=\alpha_\lambda a_{\lambda,{\rm in}}
+\beta_\lambda^*a^\dagger_{-\lambda,{\rm in}},
\qquad
|\alpha_\lambda|^2-|\beta_\lambda|^2=1
$$

gives a late occupation $N_\lambda=|\beta_\lambda|^2$. The foundational result
is therefore

$$
a(-\infty)=a(+\infty)
\quad\centernot\Rightarrow\quad
|\Psi(-\infty)\rangle=|\Psi(+\infty)\rangle.
$$

The state can remember the path even when the macroscopic control returns to
its initial value. In a general oscillator form,

$$
\chi_k''+\Omega_k^2(\eta)\chi_k=0,
\qquad
\beta_k^{(1)}\simeq
\int d\eta\,\frac{\Omega_k'}{2\Omega_k}
\exp\!\left[-2i\int^\eta\Omega_k(\eta')d\eta'\right],
$$

so the response depends on switching rate, pulse shape, phase, and dwell time,
not only endpoints. This is a conventional **state-memory null** for any claim
of persistent medium memory or changed law.

The null has sharp controls. For a scalar in spatially flat FLRW,

$$
\Omega_k^2=k^2+a^2m^2+(6\xi-1)\frac{a''}{a}.
$$

The massless conformally coupled case $m=0$, $\xi=1/6$ has
$\Omega_k=k$ and $\beta_k=0$. For gapped modes, particle production must also
vanish in a genuine adiabatic limit. A claimed additional residual should be
defined only after subtracting this declared QFT response:

$$
\Delta N_k=N_k^{\rm observed}
-N_k^{\rm QFT}[a(\cdot),m,\xi,\text{initial state}].
$$

The paper's high-frequency Planck-shaped tail is model- and limit-specific, and
the final state is a pure squeezed pair state rather than a thermal density
matrix. Its reported threshold is also not a no-production cutoff: below the
finite-occupation threshold, $|\beta_\lambda/\alpha_\lambda|^2\to1$, which
drives $N_\lambda$ singular in the stated limit. No backreaction, source for the
prescribed metric, dark-matter abundance, black hole, or observation is solved.

### 13.2 Fast response, non-unique mechanism: microwave-assisted SnO2

Chen and collaborators followed SnO2 crystallization in situ with synchrotron
X-ray total scattering and pair-distribution-function analysis under
conventional and 2.45 GHz pulsed microwave heating. They fit an Avrami law and
then an Arrhenius form,

$$
X(t)=1-\exp[-(kt)^n],
\qquad
k=A\exp\!\left(-\frac{E_a}{RT}\right).
$$

The reported apparent pairs were approximately

| heating mode | $E_a$ | $A$ |
|---|---:|---:|
| conventional | $16\ {\rm kJ\,mol^{-1}}$ | $37\ {\rm min^{-1}}$ |
| microwave-assisted | $270\ {\rm kJ\,mol^{-1}}$ | $3.4\times10^{34}\ {\rm min^{-1}}$ |

Faster crystallization therefore did not map to a lower fitted barrier. More
importantly, the fitted parameters nearly compensate over the observed
temperature range. At the representative pivot $T_*=410\ {\rm K}$,

$$
\Delta\ln A=75.90,
\qquad
\frac{\Delta E_a}{RT_*}\simeq74.55,
\qquad
\Delta\ln k(T_*)\simeq1.35.
$$

The data constrain the pivot-rate combination

$$
C(T_*)\equiv\ln A-\frac{E_a}{RT_*}=\ln k(T_*)
$$

far more directly than they identify $A$ and $E_a$ separately. The enormous
prefactor is an effective extrapolated fit parameter, not a directly observed
molecular collision frequency. The paper additionally reports that the
microwave rates correspond to conventional-fit temperatures about
$28$--$31\ ^\circ{\rm C}$ above the probe readings; unresolved local thermal
gradients remain a viable explanation.

For response analysis, define the cumulative and instantaneous hazards

$$
H(t)=-\ln[1-X(t)],
\qquad
h(t)=\dot H(t).
$$

If $u(t)$ is the applied drive and $\Theta(\mathbf x,t)$ is the local
temperature field, the relevant residual is conditional:

$$
\delta h(t)=
\int^t K_{hu}(t,t')\delta u(t')dt'
+\int d^3x\int^t
K_{h\Theta}(\mathbf x;t,t')\delta\Theta(\mathbf x,t')dt'
+\cdots.
$$

A field-specific channel is not established until matched space-time thermal
histories, geometry, state preparation, and nuisance response fail to reproduce
the kinetic pathway. This experiment does not test fluctuation-dissipation
theory and supplies no physical link to a cosmic dark medium. Its lesson is
identifiability: a response rate does not tell us which named fit parameter or
mechanism changed.

### 13.3 Timed impulse, hidden memory, delayed output: 450P/LONEOS

450P/LONEOS provides a natural impulse-response calibration. The evidence is a
chain, not one observation. Astrometry constrains an initial-state distribution;
clones propagated through an $N$-body model reconstruct a close 1992 Saturn
encounter and a large semimajor-axis decrease. Later Gemini observations found
an apparently inactive point source in 2022 and a coma in 2023--2024. JWST
directly detected CO2 at

$$
Q_{\rm CO_2}=(6.99\pm0.07)\times10^{24}\ {m molecules\,s^{-1}},
$$

with H2O and CO reported as nondetections or upper limits. A simple thermal
model makes release of trapped CO2 during amorphous-water-ice crystallization
plausible; it is not an end-to-end likelihood prediction of the measured gas
rate.

The causal reconstruction can be written as

$$
D_{\rm ast}\longrightarrow p(x_0\mid D_{\rm ast})
\longrightarrow r_c(t),
\qquad
F_c(t)=\frac{(1-A)L_\odot}{4\pi r_c(t)^2},
$$

$$
\partial_tT_c=\alpha\,\partial_z^2T_c,
\qquad
Q_{\rm CO_2}
=\mathcal G[T_c,\mathcal C,\text{porosity},\text{spin},\text{shape}],
$$

$$
D_{\rm spec}\sim
\mathcal O[Q_{\rm CO_2},\text{dust},\text{viewing geometry}].
$$

The encounter supplies an independently timed perturbation; diffusion and
phase conversion supply hidden memory; spectra, dust, and morphology supply
distinct outputs. Every arrow is model-assisted and carries its own failure
condition. Unknown shape, spin, obliquity, material properties, earlier thermal
history, selection, and a pure-CO2 alternative prevent “Saturn activated the
comet” from becoming a directly observed fact. The paper's forecast language
about a July 2026 Jupiter encounter is not used here; as of this draft date it
requires post-encounter astrometry rather than repetition as a future claim.

### 13.4 The combined inference rule

Together, the cases motivate a more explicit response equation:

$$
X(t)=X_{\rm hom}(t;X_0,\mathcal H)
+\int_{-\infty}^{t}K(t,t';\theta)F(t')dt',
\qquad
Y(t)=\mathcal O[X(t),\nu]+\epsilon(t),
$$

where $\mathcal H$ is unresolved history, $\theta$ contains compensating
constitutive parameters, $\nu$ contains observation and selection variables,
and $\epsilon$ is declared error. The simple foundational rule is:

> Do not name the residual until endpoint restoration, parameter compensation,
> latent history, and the observation operator have each been tested.

## 14. Causal Residual Spectroscopy protocol

The following proposed method is written for possible comparison with ASTRA's
existing operator-aware methods. It is a research protocol rather than a new
cosmic substance, and compatibility or integration has not been validated.

1. **Reconstruct the known sector.** Map visible density, pressure,
   electromagnetic fields, plasma tracers, and measurement selection effects.
2. **Infer the residual.** Under declared reconstruction assumptions,
   reconstruct compatible metric potentials and the conserved closure
   $\mathcal R_{\mu\nu}$, with uncertainty.
3. **Declare the action and symmetries.** Specify whether each symmetry is
   global, gauged, unbroken, Higgsed, or state-broken; enumerate carriers and
   portals.
4. **Compute the physical response kernel and homogeneous state.** For perturbations
   $A=(\delta\rho,\delta Q,\theta,U_\mu,h_{\mu\nu})$, impose the gauge and
   diffeomorphism Ward identities with contact terms, gauge-fix, solve the
   constraints, project onto physical variables, and then solve

   $$
   \det \mathcal D^{-1}_{\mathrm{phys,ret}}(\omega,k)=0.
   $$

5. **Audit spectra and characteristics.** Require no ghost residues and
   positive spectral weight where unitarity requires it, acceptable damping,
   lower-half-plane poles for stable dissipative modes, stable gradients,
   controlled strong-coupling scales, and observed photon-graviton cone
   alignment. Judge causal propagation from characteristics or front velocity,
   not merely phase or group velocity in a dispersive medium.
6. **Map the phase coordinates.** At minimum record

   $$
   \Xi,
   \quad
   \Gamma_D=\frac{\alpha_D}{a_DT_D},
   \quad
   a_D\equiv\left(\sum_s n_s\right)^{-1/3},
   \quad
   N_D=\frac{4\pi}{3}\lambda_D^3\sum_s n_s,
   \quad f_D,
   \quad x_{\mathrm{ion}},
   \quad \lambda_{\mathrm{mfp}}/L,
   \quad \Gamma_{\mathrm{inst}}L/v,
   \quad t_{\mathrm{dyn}}/t_{\mathrm{cool}},
   \quad n_s\lambda_{{\rm dB},s}^3,
   \quad \omega_c/\nu\ \text{when magnetized}.
   $$

   The displayed $\Gamma_D$ assumes a common carrier temperature $T_D$.

7. **Map parameter equivalence classes.** Report constrained combinations,
   covariances, and pivot observables before interpreting individual parameter
   names. Search for barrier-prefactor, abundance-cross-section, source-transfer,
   and response-selection compensation.
8. **Predeclare discriminators.** Predict density, velocity, frequency,
   direction, phase, pulse shape, dwell time, and history dependence before
   selecting favorable systems. Include conformal, adiabatic, matched-thermal,
   and endpoint-restoration nulls where applicable.
9. **Prefer independently timed perturbations.** Freeze the forcing
   reconstruction, latent-state law, nuisance priors, and output map before
   judging delayed response; compare with a counterfactual generated by the
   same model and sensitivity-matched controls.
10. **Test transfer.** Freeze physical parameters, nuisance priors, data cuts,
   and thresholds; calibrate in one domain and score held-out predictions in
   galaxies, mergers, the CMB, large-scale structure, gravitational waves, and
   direct detection.
11. **Preserve negative results.** A failed plasma model is not a proof of
   collisionless particles; a failed modified-gravity model is not proof of a
   plasma. Reject only the tested action and parameter region.

This protocol may be compared with ASTRA's operator-aware and hidden-state
emphasis. No compatibility or integration claim is made: it does not modify
SPPT's planetary reservoir graph or inherit the verification status of the
stable core.

## 15. Claim-status summary

### SOURCE-SUPPORTED OR STANDARD WITHIN STATED FRAMEWORKS — NOT INDEPENDENTLY VERIFIED HERE

- Plasma kinetics contains collective screening, longitudinal and transverse
  modes, kinetic damping, and stream instabilities.
- A material rest frame does not by itself imply Lorentz-violating fundamental
  laws.
- Hidden-$U(1)$, atomic, dissipative, and superfluid dark sectors are
  established as literature constructions, not descriptions established in
  nature.
- Preferred-frame couplings are strongly constrained in model- and
  coupling-specific ways by multimessenger, post-Newtonian, and
  preferred-frame observations.
- Under standard BBN, recombination, and CMB dynamics, ordinary baryonic plasma
  is not abundant enough to replace the dominant standard dark-matter
  inventory.
- A prescribed time-dependent FLRW background can return to its initial scale
  while a minimally coupled scalar state retains nonzero Bogoliubov occupation;
  this is a conditional field-theory result, not an observation or dark-matter
  production claim.
- The reported microwave and conventional SnO2 Arrhenius fits exhibit strong
  barrier-prefactor compensation over the measured temperature range, and
  unresolved local thermometry remains a stated confounder.
- The 450P/LONEOS evidence separates observed astrometry, coma, and spectra from
  a model-supported orbital encounter and an inferred thermal activation chain.

### ALGEBRAIC DERIVATIONS UNDER ENUMERATED ASSUMPTIONS — INDEPENDENT REVIEW PENDING

- The mixed retarded responses of charge-even stress and charge-odd current
  vanish at linear order when the dynamics, state, background, and regulator
  preserve charge conjugation.
- With the additional neutral-background, equal-specific-pressure, and
  symmetry-preserving closure assumptions, the declared equal-pair fluid model
  separates into Jeans and Langmuir branches.
- Unequal specific pressure response supplies the displayed mass-charge mixing
  terms in the generic two-component benchmark.
- For a self-gravitating equal-pair plasma,
  $\Omega_p^2/\omega_J^2=\alpha_D/(Gm^2)$.
- The Debye/Jeans reduction follows only with the additionally declared
  isothermal equal-pair closure.
- Under the illustrative $m_D=200\ {\rm GeV}/c^2$ and local-density benchmark,
  LZ230616 has $q_{\rm tr}a_D/\hbar\sim10^{14}$; this excludes coherence tied
  to mean spacing but does not alone establish an impulse regime.

These are derivations, not established novelty claims.

### PROPOSED_ONLY

- “Causal residual spectroscopy” as a working label for a possible integration
  of established closure and response methods.
- A phase-dependent hidden sector that occupies plasma, neutral, condensed,
  and gravitationally clustering regimes.
- Merger-ensemble response exponents as a practical classifier after nonlinear
  simulation calibration.
- Applying a two-sided dynamical-structure-factor description to an incoming
  collective dark sector.
- Using the three calibration cases as a general endpoint-compensation-memory
  audit for cosmic residuals.

### UNKNOWN

- Whether the dominant cosmic residual is particulate, plasma-like,
  condensed, a fundamental preferred-frame field, modified gravity, or a
  mixture.
- Whether the derived response organization is novel relative to the complete
  plasma, many-body, and modified-gravity literature.
- Whether LZ230616 is dark matter, an unmodeled background, or a statistical
  fluctuation.

### REJECTED IN THIS NOTE

- The claim that plasma, aether, and dark matter have been empirically
  identified as one substance.
- The claim that mathematical equivalence of restricted field equations proves
  ontological identity.
- The claim that one anomalous recoil establishes a population-level law.
- The claim that the stated minimal single-gauged-$U(1)$ homogeneous
  realization automatically supplies both a long-range plasma and an ungapped
  superfluid phonon.
- The claim that any of the three calibration cases is evidence for a shared
  plasma, aether, or dark-matter ontology.
- The claim that restored controls imply a restored state, or that a fitted
  parameter name uniquely identifies a microscopic mechanism.

## 16. Conclusion

The productive intersection of plasma, aether, and dark matter is a phase and
response problem, not a synonym problem.

A hidden sector could gravitate while supporting charge oscillations,
recombination, shocks, neutral bound states, or condensate excitations. Charge
symmetry can prevent its fastest electric mode from entering its linear mass
mode, allowing gravitational clustering and collective plasma response to
coexist. Mergers, background fields, phase changes, streaming, and nonlinear
transport can expose what equilibrium hides.

The correct foundational move is therefore:

> Infer the conserved residual, declare the degrees of freedom, compute the
> poles and residues, test the zero-density and phase limits, and require the
> same parameters to survive held-out observations.

That program is compatible with unconventional hypotheses without granting
them evidentiary privilege. The sky does not speak without models, but models
can be required to reveal exactly where their language enters.

## Selected primary sources

1. Ackerman, Buckley, Carroll, and Kamionkowski, “Dark Matter and Dark
   Radiation,” [arXiv:0810.5126](https://arxiv.org/abs/0810.5126).
2. Cyr-Racine and Sigurdson, “The Cosmology of Atomic Dark Matter,”
   [arXiv:1209.5752](https://arxiv.org/abs/1209.5752).
3. Berezhiani and Khoury, “Theory of Dark Matter Superfluidity,”
   [arXiv:1507.01019](https://arxiv.org/abs/1507.01019).
4. Jacobson and Mattingly, “Gravity with a Dynamical Preferred Frame,”
   [Physical Review D 64, 024028](https://doi.org/10.1103/PhysRevD.64.024028).
5. Oost, Mukohyama, and Wang, “Constraints on Einstein-aether theory after
   GW170817,” [arXiv:1802.04303](https://arxiv.org/abs/1802.04303).
6. Aghanim et al., “Planck 2018 Results. VI. Cosmological Parameters,”
   [arXiv:1807.06209](https://arxiv.org/abs/1807.06209).
7. Mossa et al., “The baryon density of the Universe from an improved rate of
   deuterium burning,”
   [Nature 587, 210–213](https://doi.org/10.1038/s41586-020-2878-4).
8. DeRocco and Giffin, “Dark plasmas in the nonlinear regime: Constraints from
   particle-in-cell simulations,”
   [Physical Review D 111, 095031](https://doi.org/10.1103/PhysRevD.111.095031).
9. Knapen, Kozaczuk, and Lin, “Dark Matter-Electron Scattering in Dielectrics,”
   [arXiv:2101.08275](https://arxiv.org/abs/2101.08275).
10. LUX-ZEPLIN Collaboration, “Search for dark matter particle interactions in
    an extended nuclear recoil energy window with the LUX-ZEPLIN (LZ)
    experiment,”
    [2026 collaboration preprint](https://lz.lbl.gov/wp-content/uploads/sites/6/2026/08/LZ_Preprint_260901_Dark_Matter_EFT_Nuclear_Recoil_Search_at_Higher_Energies.pdf).
11. Clowe et al., “A Direct Empirical Proof of the Existence of Dark Matter,”
    [arXiv:astro-ph/0608407](https://arxiv.org/abs/astro-ph/0608407).
12. Macquart et al., “A census of baryons in the Universe from localized fast
    radio bursts,”
    [Nature 581, 391–395](https://doi.org/10.1038/s41586-020-2300-2).
13. Van Suijlekom, Wondrak, and Falcke, “Particle Creation in a Cosmological
    Background in Analogy to the Schwinger Effect,”
    [Communications in Mathematical Physics 407, 204](https://doi.org/10.1007/s00220-026-05700-7).
14. Chen et al., “Comparison of the Arrhenius parameters between conventional
    hydrothermal and microwave-assisted synthesis methods for tin oxide
    nanoparticles,”
    [Journal of Materials Chemistry A](https://doi.org/10.1039/D5TA10373H).
15. Schambeau et al., “JWST and Gemini Observations of the Active Centaur
    450P/LONEOS: Nucleus and Coma Characterizations,”
    [The Planetary Science Journal 7, 137](https://doi.org/10.3847/PSJ/ae685c).
16. Lilly et al., “Semi-major Axis Jumps as the Activity Trigger in Centaurs and
    High-Perihelion Jupiter Family Comets,”
    [The Astrophysical Journal Letters 960, L8](https://doi.org/10.3847/2041-8213/ad1606).

No third-party article text, figure, publisher layout, or raw data is
redistributed in this note. Citations remain under their respective rights and
terms.
