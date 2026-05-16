// JS port of LinearTransformer.py
// All internal computation uses Float64Array for numerical stability.
// Matrices are row-major. "columns are eigenvectors" convention matches numpy.

// ── Basic matrix ops (Float64, row-major, square n×n unless noted) ────────────

function zeros64(n) { return new Float64Array(n) }

function eye64(n) {
  const I = new Float64Array(n * n)
  for (let i = 0; i < n; i++) I[i * n + i] = 1
  return I
}

// C = A @ B  (n×n)
function mm(A, B, n) {
  const C = new Float64Array(n * n)
  for (let i = 0; i < n; i++)
    for (let k = 0; k < n; k++) {
      const aik = A[i * n + k]
      if (aik === 0) continue
      for (let j = 0; j < n; j++)
        C[i * n + j] += aik * B[k * n + j]
    }
  return C
}

// y = A @ x  (A: n×n, x: n)
function mv(A, x, n) {
  const y = new Float64Array(n)
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      y[i] += A[i * n + j] * x[j]
  return y
}

// A^T  (n×n)
function tr(A, n) {
  const B = new Float64Array(n * n)
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      B[j * n + i] = A[i * n + j]
  return B
}

// diag(v) as n×n matrix
function diag(v, n) {
  const D = new Float64Array(n * n)
  for (let i = 0; i < n; i++) D[i * n + i] = v[i]
  return D
}

// Gauss-Jordan inverse (n×n, Float64)
function inv(A, n) {
  const M = new Float64Array(n * n * 2)
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) M[i * 2 * n + j] = A[i * n + j]
    M[i * 2 * n + n + i] = 1
  }
  for (let col = 0; col < n; col++) {
    let maxRow = col
    for (let r = col + 1; r < n; r++)
      if (Math.abs(M[r * 2 * n + col]) > Math.abs(M[maxRow * 2 * n + col])) maxRow = r
    if (maxRow !== col)
      for (let j = 0; j < 2 * n; j++) {
        const t = M[col * 2 * n + j]; M[col * 2 * n + j] = M[maxRow * 2 * n + j]; M[maxRow * 2 * n + j] = t
      }
    const piv = M[col * 2 * n + col]
    if (Math.abs(piv) < 1e-14) continue
    for (let j = 0; j < 2 * n; j++) M[col * 2 * n + j] /= piv
    for (let r = 0; r < n; r++) {
      if (r === col) continue
      const f = M[r * 2 * n + col]
      for (let j = 0; j < 2 * n; j++) M[r * 2 * n + j] -= f * M[col * 2 * n + j]
    }
  }
  const R = new Float64Array(n * n)
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      R[i * n + j] = M[i * 2 * n + n + j]
  return R
}

// ── Hadamard matrix (normalized, n must be power of 2) ───────────────────────
// Matches Python: H / np.sqrt(n)

function hadamard(n) {
  let H = new Float64Array([1])
  let k = 1
  while (k < n) {
    const H2 = new Float64Array(k * 2 * k * 2)
    for (let i = 0; i < k; i++)
      for (let j = 0; j < k; j++) {
        H2[i * 2 * k + j]               =  H[i * k + j]
        H2[i * 2 * k + k + j]           =  H[i * k + j]
        H2[(k + i) * 2 * k + j]         =  H[i * k + j]
        H2[(k + i) * 2 * k + k + j]     = -H[i * k + j]
      }
    H = H2; k *= 2
  }
  const s = 1 / Math.sqrt(n)
  for (let i = 0; i < H.length; i++) H[i] *= s
  return H
}

// ── Symmetric EVD via Jacobi (matches np.linalg.eigh convention) ─────────────
// Returns { vals: Float64Array(n), vecs: Float64Array(n*n) }
// vecs is column-major eigenvectors: vecs[row*n + col] = component `row` of eigenvector `col`
// vals are NOT sorted (matches eigh which returns ascending, but we don't rely on order)

function eigh(A, n) {
  const S = new Float64Array(A)          // working copy of matrix
  const V = eye64(n)                     // accumulates rotations → columns become eigenvectors

  const maxIter = n * n * 30            // generous iteration budget
  for (let iter = 0; iter < maxIter; iter++) {
    // Find largest off-diagonal |S[p,q]|
    let p = 0, q = 1, maxVal = 0
    for (let i = 0; i < n - 1; i++)
      for (let j = i + 1; j < n; j++) {
        const v = Math.abs(S[i * n + j])
        if (v > maxVal) { maxVal = v; p = i; q = j }
      }
    if (maxVal < 1e-13) break

    const Spp = S[p * n + p], Sqq = S[q * n + q], Spq = S[p * n + q]
    const tau = (Sqq - Spp) / (2 * Spq)
    const t = tau >= 0
      ? 1 / (tau + Math.sqrt(1 + tau * tau))
      : 1 / (tau - Math.sqrt(1 + tau * tau))
    const c = 1 / Math.sqrt(1 + t * t)
    const s = t * c

    // Update diagonal
    S[p * n + p] = Spp - t * Spq
    S[q * n + q] = Sqq + t * Spq
    S[p * n + q] = 0; S[q * n + p] = 0

    // Update off-diagonal rows/cols
    for (let i = 0; i < n; i++) {
      if (i === p || i === q) continue
      const Sip = S[i * n + p], Siq = S[i * n + q]
      S[i * n + p] = c * Sip - s * Siq; S[p * n + i] = S[i * n + p]
      S[i * n + q] = s * Sip + c * Siq; S[q * n + i] = S[i * n + q]
    }

    // Accumulate rotation into V (columns of V are eigenvectors)
    for (let i = 0; i < n; i++) {
      const Vip = V[i * n + p], Viq = V[i * n + q]
      V[i * n + p] = c * Vip - s * Viq
      V[i * n + q] = s * Vip + c * Viq
    }
  }

  const vals = new Float64Array(n)
  for (let i = 0; i < n; i++) vals[i] = Math.max(S[i * n + i], 1e-9)

  return { vals, vecs: V }
}

// ── Cholesky decomposition: returns lower-triangular L s.t. A ≈ L @ L^T ──────

function cholesky(A, n) {
  const L = new Float64Array(n * n)
  for (let i = 0; i < n; i++) {
    for (let j = 0; j <= i; j++) {
      let s = A[i * n + j]
      for (let k = 0; k < j; k++) s -= L[i * n + k] * L[j * n + k]
      L[i * n + j] = i === j ? Math.sqrt(Math.max(s, 1e-14)) : s / (L[j * n + j] + 1e-15)
    }
  }
  return L
}

// ── SVD via EVD of A^T A (matches np.linalg.svd convention) ──────────────────
// Returns { U, S, Vt } where A = U @ diag(S) @ Vt
// U columns = left singular vectors, Vt rows = right singular vectors
// S is sorted descending (np.linalg.svd default)

function svd(A, n) {
  // A^T @ A → right singular vectors V, singular values S
  const At = tr(A, n)
  const AtA = mm(At, A, n)
  for (let i = 0; i < n; i++) AtA[i * n + i] += 1e-10   // eps for stability

  const { vals, vecs: V } = eigh(AtA, n)   // V columns = eigenvectors of A^T A

  // Sort by descending singular value
  const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => vals[b] - vals[a])
  const S = new Float64Array(n)
  const Vt = new Float64Array(n * n)   // rows of Vt = right singular vectors
  for (let i = 0; i < n; i++) {
    S[i] = Math.sqrt(Math.max(vals[order[i]], 1e-14))
    for (let j = 0; j < n; j++) Vt[i * n + j] = V[j * n + order[i]]  // row i = eigenvec order[i]
  }

  // U = A @ V_sorted @ diag(1/S)
  const Vsorted = tr(Vt, n)   // columns of Vsorted = right singular vectors
  const AV = mm(A, Vsorted, n)
  const U = new Float64Array(n * n)
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      U[i * n + j] = AV[i * n + j] / (S[j] + 1e-15)

  return { U, S, Vt }
}

// ── Second-moment matrix: X @ X^T + eps*I  (matches Python exactly) ──────────

function xxT(X, gs, ncols) {
  const eps = 1e-6
  const C = new Float64Array(gs * gs)
  for (let i = 0; i < gs; i++)
    for (let j = 0; j < gs; j++) {
      let s = 0
      for (let k = 0; k < ncols; k++) s += X[i * ncols + k] * X[j * ncols + k]
      C[i * gs + j] = s + (i === j ? eps : 0)
    }
  return C
}

// ── Extract gs×ncols sub-block from flat D×ncols row-major matrix ─────────────

function extractBlock(flat, D, ncols, gStart, gs) {
  const block = new Float64Array(gs * ncols)
  for (let r = 0; r < gs; r++)
    for (let c = 0; c < ncols; c++)
      block[r * ncols + c] = flat[(gStart + r) * ncols + c]
  return block
}

// ── Apply gs×gs matrix T to each column of a gs×ncols block ──────────────────

function applyT(T, block, gs, ncols) {
  const out = new Float64Array(gs * ncols)
  for (let c = 0; c < ncols; c++) {
    const col = new Float64Array(gs)
    for (let r = 0; r < gs; r++) col[r] = block[r * ncols + c]
    const tcol = mv(T, col, gs)
    for (let r = 0; r < gs; r++) out[r * ncols + c] = tcol[r]
  }
  return out
}

// ── Build T for one group — strict port of LinearTransformer.transform() ──────

function buildT(X_g, W_g, gs, N, M, method) {

  if (method === 'hadamard') {
    const T = hadamard(gs)
    // Hadamard is orthogonal: T^{-1} = T^T
    return { T, T_inv: tr(T, gs) }
  }

  if (method === 'householder_random') {
    // v = randn(gs), normalize, H = I - 2*v*v^T
    const v = new Float64Array(gs)
    let norm = 0
    for (let i = 0; i < gs; i++) {
      // Box-Muller for standard normal
      const u1 = Math.random(), u2 = Math.random()
      v[i] = Math.sqrt(-2 * Math.log(u1 + 1e-15)) * Math.cos(2 * Math.PI * u2)
      norm += v[i] * v[i]
    }
    norm = Math.sqrt(norm)
    for (let i = 0; i < gs; i++) v[i] /= norm
    const T = eye64(gs)
    for (let i = 0; i < gs; i++)
      for (let j = 0; j < gs; j++)
        T[i * gs + j] -= 2 * v[i] * v[j]
    return { T, T_inv: tr(T, gs) }   // Householder is orthogonal
  }

  if (method === 'White') {
    // cov_X = X @ X^T + eps*I
    // Lambda, U = eigh(cov_X)
    // T = diag(Lambda^{-1/2}) @ U^T
    const Cx = xxT(X_g, gs, N)
    const { vals: Lambda, vecs: U } = eigh(Cx, gs)
    const LambdaInvSqrt = Lambda.map(v => 1 / Math.sqrt(v))
    const T = mm(diag(LambdaInvSqrt, gs), tr(U, gs), gs)
    const T_inv = inv(T, gs)
    return { T, T_inv }
  }

  if (method === 'WUS') {
    // X_prime_L = chol(X @ X^T + eps)
    // W_prime_L = chol(W @ W^T + eps)
    // U, S, V = svd(W_prime_L^T @ X_prime_L)
    // T = S^{-1/2} @ U^T @ W_prime_L^T
    const Cx = xxT(X_g, gs, N)
    const Cw = xxT(W_g, gs, M)
    const Lx = cholesky(Cx, gs)
    const Lw = cholesky(Cw, gs)
    const LwT = tr(Lw, gs)
    const prod = mm(LwT, Lx, gs)          // W_prime_L^T @ X_prime_L
    const { U, S } = svd(prod, gs)
    const SinvSqrt = S.map(s => 1 / Math.sqrt(s))
    const T = mm(mm(diag(SinvSqrt, gs), tr(U, gs), gs), LwT, gs)
    const T_inv = inv(T, gs)
    return { T, T_inv }
  }

  if (method === 'WUSH') {
    // Same Cholesky+SVD as WUS, then T = H @ S^{-1/2} @ U^T @ W_prime_L^T
    const Cx = xxT(X_g, gs, N)
    const Cw = xxT(W_g, gs, M)
    const Lx = cholesky(Cx, gs)
    const Lw = cholesky(Cw, gs)
    const LwT = tr(Lw, gs)
    const prod = mm(LwT, Lx, gs)
    const { U, S } = svd(prod, gs)
    const SinvSqrt = S.map(s => 1 / Math.sqrt(s))
    const H = hadamard(gs)
    // T = H @ diag(S^{-1/2}) @ U^T @ W_prime_L^T
    const T = mm(H, mm(mm(diag(SinvSqrt, gs), tr(U, gs), gs), LwT, gs), gs)
    const T_inv = inv(T, gs)
    return { T, T_inv }
  }

  if (method === 'LQ') {
    // Cx = X@X^T + eps,  Cw = W@W^T + eps
    // Lx, Vx = eigh(Cx);  Lx = max(Lx, 1e-9)
    // Cx_sqrt    = Vx @ diag(sqrt(Lx)) @ Vx^T
    // Cx_inv_sqrt = Vx @ diag(1/sqrt(Lx)) @ Vx^T
    // A = Cx_sqrt @ Cw @ Cx_sqrt
    // La, Va = eigh(A);  La = max(La, 1e-9)
    // A_sqrt = Va @ diag(sqrt(La)) @ Va^T
    // M = Cx_inv_sqrt @ A_sqrt @ Cx_inv_sqrt
    // Lm, Q = eigh(M);  Lm = max(Lm, 1e-9)
    // T = diag(Lm^{1/2}) @ Q^T
    const Cx = xxT(X_g, gs, N)
    const Cw = xxT(W_g, gs, M)

    const { vals: Lx, vecs: Vx } = eigh(Cx, gs)
    const VxT = tr(Vx, gs)
    const CxSqrt    = mm(mm(Vx, diag(Lx.map(v => Math.sqrt(v)), gs), gs), VxT, gs)
    const CxInvSqrt = mm(mm(Vx, diag(Lx.map(v => 1 / Math.sqrt(v)), gs), gs), VxT, gs)

    const A = mm(mm(CxSqrt, Cw, gs), CxSqrt, gs)
    const { vals: La, vecs: Va } = eigh(A, gs)
    const VaT = tr(Va, gs)
    const ASqrt = mm(mm(Va, diag(La.map(v => Math.sqrt(v)), gs), gs), VaT, gs)

    const Mmat = mm(mm(CxInvSqrt, ASqrt, gs), CxInvSqrt, gs)
    const { vals: Lm, vecs: Q } = eigh(Mmat, gs)
    const Qt = tr(Q, gs)

    // T = diag(Lm^{1/2}) @ Q^T
    const T = mm(diag(Lm.map(v => Math.sqrt(v)), gs), Qt, gs)
    const T_inv = inv(T, gs)
    return { T, T_inv }
  }

  if (method === 'LQH') {
    // Same as LQ but T = H @ diag(Lm^{1/2}) @ Q^T
    const Cx = xxT(X_g, gs, N)
    const Cw = xxT(W_g, gs, M)

    const { vals: Lx, vecs: Vx } = eigh(Cx, gs)
    const VxT = tr(Vx, gs)
    const CxSqrt    = mm(mm(Vx, diag(Lx.map(v => Math.sqrt(v)), gs), gs), VxT, gs)
    const CxInvSqrt = mm(mm(Vx, diag(Lx.map(v => 1 / Math.sqrt(v)), gs), gs), VxT, gs)

    const A = mm(mm(CxSqrt, Cw, gs), CxSqrt, gs)
    const { vals: La, vecs: Va } = eigh(A, gs)
    const VaT = tr(Va, gs)
    const ASqrt = mm(mm(Va, diag(La.map(v => Math.sqrt(v)), gs), gs), VaT, gs)

    const Mmat = mm(mm(CxInvSqrt, ASqrt, gs), CxInvSqrt, gs)
    const { vals: Lm, vecs: Q } = eigh(Mmat, gs)
    const Qt = tr(Q, gs)

    const H = hadamard(gs)
    // T = H @ diag(Lm^{1/2}) @ Q^T
    const T = mm(H, mm(diag(Lm.map(v => Math.sqrt(v)), gs), Qt, gs), gs)
    const T_inv = inv(T, gs)
    return { T, T_inv }
  }

  // fallback: identity
  return { T: eye64(gs), T_inv: eye64(gs) }
}

// ── Public: apply transform to full D×N X and D×M W ──────────────────────────

export function applyTransformFull(X_flat, W_flat, D, N, M, gs, method) {
  if (method === 'None') {
    return {
      X_prime: new Float32Array(X_flat),
      W_prime: new Float32Array(W_flat),
    }
  }

  const X_prime = new Float32Array(D * N)
  const W_prime = new Float32Array(D * M)

  for (let gStart = 0; gStart < D; gStart += gs) {
    const X_g = extractBlock(X_flat, D, N, gStart, gs)
    const W_g = extractBlock(W_flat, D, M, gStart, gs)

    const { T, T_inv } = buildT(X_g, W_g, gs, N, M, method)

    // X' = T @ X_g
    const tX = applyT(T, X_g, gs, N)
    for (let r = 0; r < gs; r++)
      for (let c = 0; c < N; c++)
        X_prime[(gStart + r) * N + c] = tX[r * N + c]

    // W' = T_inv^T @ W_g
    const T_invT = tr(T_inv, gs)
    const tW = applyT(T_invT, W_g, gs, M)
    for (let r = 0; r < gs; r++)
      for (let c = 0; c < M; c++)
        W_prime[(gStart + r) * M + c] = tW[r * M + c]
  }

  return { X_prime, W_prime }
}

// ── Public: distribution-only transform (no W needed) ────────────────────────

export function applyTransformDist(data, method, gs = 16) {
  if (method === 'None') return new Float32Array(data)
  const N = Math.floor(data.length / gs)
  const W_dummy = new Float32Array(gs * N)
  const { X_prime } = applyTransformFull(data, W_dummy, gs, N, N, gs, method)
  return X_prime
}

export const METHOD_OPTIONS = [
  { value: 'None',               label: 'None (Baseline)' },
  { value: 'hadamard',           label: 'Hadamard' },
  { value: 'householder_random', label: 'Householder (Random)' },
  { value: 'White',              label: 'Whitening' },
  { value: 'WUS',                label: 'WUS' },
  { value: 'WUSH',               label: 'WUSH' },
  { value: 'LQ',                 label: 'LQ' },
  { value: 'LQH',                label: 'LQH' },
]
