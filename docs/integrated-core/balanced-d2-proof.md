# Balanced-gradient rigidity in two dimensions

Independent check: 4 October 2026. This note proves a bounded mathematical statement directly; it does not attribute it to an external source or assert a physical no-go beyond its assumptions.

## Proposition

Let an open connected domain Ω in R² carry its Euclidean metric, and let u,v belong to C²(Ω). Suppose, at every point,

\[
|\nabla u|=|\nabla v|,
\qquad \nabla u\cdot\nabla v=0.
\]

Then both u and v are harmonic on all of Ω. The same local statement holds in flat periodic coordinates on a two-dimensional torus. Critical points, critical sets with interior, and possible choices of orientation on different regular components do not invalidate the proof.

## Proof across the critical set

Put K={x:∇u(x)=0}. Equal gradient lengths imply ∇v=0 on K as well. On its open complement R=Ω\K, there is a sign σ in {+1,−1} such that

\[
\nabla v=\sigma J\nabla u,
\qquad J(p,q)=(-q,p).
\]

Indeed, the two equal nonzero orthogonal vectors in R² differ by one of the two ninety-degree rotations. The sign equals det(∇u,∇v)/|∇u|², a continuous function with values in {+1,−1}; it is therefore locally constant on R. Consequently each regular point has a neighborhood on which

\[
v_x=-\sigma u_y,
\qquad v_y=\sigma u_x.
\]

Equality of mixed derivatives gives

\[
0=(v_y)_x-(v_x)_y=\sigma(u_{xx}+u_{yy}),
\qquad v_{xx}+v_{yy}=\sigma(-u_{yx}+u_{xy})=0.
\]

Thus Δu=Δv=0 on R. On the interior of K, both gradients vanish identically, so u and v are locally constant and their Laplacians again vanish. The set R∪int(K) is dense in Ω: its complement is the boundary of the relatively closed set K, which has empty interior. Since u,v are C², their Laplacians are continuous; they therefore vanish on all of Ω. This step explicitly covers the boundary of every critical component. No global orientation assumption is needed.

## Two consequences

**Flat torus.** If u,v are smooth periodic scalar functions on a connected flat torus T², harmonicity and periodic integration by parts imply

\[
\int_{T^2}|\nabla u|^2=-\int_{T^2}u\,\Delta u=0,
\qquad
\int_{T^2}|\nabla v|^2=0.
\]

Hence u and v are constant. Nonconstant globally balanced periodic fields do not exist under these assumptions. Constant normalized wavefunctions do exist: |ψ|²=1/Vol(T²), with arbitrary constant phase. Their gradients and geometric kinetic energy vanish.

**Whole plane.** If u,v belong additionally to L²(R²), the harmonic mean-value property and Cauchy–Schwarz imply, for every x and R>0,

\[
|u(x)|=\left|\frac{1}{\pi R^2}\int_{B_R(x)}u(y)\,dy\right|
\le\frac{\|u\|_{L^2(R^2)}}{\sqrt{\pi}\,R}.
\]

Letting R→∞ gives u(x)=0; the same argument gives v(x)=0. Therefore no nonzero, normalized C²∩L²(R²) state is globally balanced on the whole plane.

## Scope for the finite-scale model

For ψ=u+iv in d=2, the balanced rank-two condition is precisely the pair of equations in the proposition. The algebraic identity A∇ψ=∇ψ remains correct. The new result sharply limits its globally balanced smooth realization: on a flat periodic base only the trivial constant-gradient-zero sector survives; on R² no normalized whole-plane state survives. It strengthens the earlier existence caveat without changing the local energy identity or isolated-point qualification.

This is not a result for d≥3, nonsmooth fields, nontrivial bundles, multivalued fields, or arbitrary boundary conditions. For example, nonconstant balanced fields occur on bounded planar domains: ψ(z)=√(2/π)z on the unit disk is smooth, balanced, and has integral |ψ|² equal to one, though it is not periodic and does not obey homogeneous Dirichlet boundary data. No time-invariance conclusion follows from this static argument.
