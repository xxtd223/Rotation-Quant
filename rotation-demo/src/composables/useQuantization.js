// JS port of quant.py — fake_quant_nvfp4 + nvfp4_quant_error
// Column-major block partitioning, block size 16

const FP4_VALUES = new Float32Array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
const MAX_FP4 = 6.0
const BLOCK_SIZE = 16

// frexp: mantissa in [0.5,1), exponent such that value = mantissa * 2^exponent
function frexp(value) {
  if (value === 0) return [0, 0]
  const buf = new ArrayBuffer(8)
  const view = new DataView(buf)
  view.setFloat64(0, value)
  const hi = view.getUint32(0)
  const exp = ((hi >>> 20) & 0x7FF) - 1022
  view.setUint32(0, (hi & 0x800FFFFF) | 0x3FE00000)
  return [view.getFloat64(0), exp]
}

function quantizeE4M3(s) {
  s = Math.max(2 ** -9, Math.min(448, s))
  const [m, e] = frexp(s)
  const mIeee = m * 2.0
  const eIeee = e - 1
  const mQuant = Math.round((mIeee - 1.0) * 8.0) / 8.0
  return (1.0 + mQuant) * (2 ** eIeee)
}

function nearestFP4(absVal) {
  let best = FP4_VALUES[0], bestDist = Math.abs(absVal - FP4_VALUES[0])
  for (let i = 1; i < FP4_VALUES.length; i++) {
    const d = Math.abs(absVal - FP4_VALUES[i])
    if (d < bestDist) { bestDist = d; best = FP4_VALUES[i] }
  }
  return best
}

// Quantize a 2D matrix (rows × cols, row-major) using NVFP4 column-major blocking
// Mirrors Python: matrix.flatten(order='F') → blocks of 16 → quantize → reshape(order='F')
export function fakeQuantNVFP4(flat, rows, cols) {
  // Step 1: column-major flatten
  const colMajor = new Float32Array(rows * cols)
  for (let c = 0; c < cols; c++)
    for (let r = 0; r < rows; r++)
      colMajor[c * rows + r] = flat[r * cols + c]

  // Step 2: quantize in blocks of 16
  const qColMajor = new Float32Array(rows * cols)
  for (let b = 0; b < colMajor.length; b += BLOCK_SIZE) {
    let blockMax = 0
    for (let i = 0; i < BLOCK_SIZE && b + i < colMajor.length; i++) {
      const a = Math.abs(colMajor[b + i])
      if (a > blockMax) blockMax = a
    }
    if (blockMax === 0) blockMax = 1e-9
    let s = blockMax / MAX_FP4
    s = quantizeE4M3(s)
    for (let i = 0; i < BLOCK_SIZE && b + i < colMajor.length; i++) {
      const v = colMajor[b + i]
      const sign = v >= 0 ? 1 : -1
      const absScaled = Math.min(Math.abs(v) / s, MAX_FP4)
      qColMajor[b + i] = sign * nearestFP4(absScaled) * s
    }
  }

  // Step 3: convert back to row-major
  const out = new Float32Array(rows * cols)
  for (let c = 0; c < cols; c++)
    for (let r = 0; r < rows; r++)
      out[r * cols + c] = qColMajor[c * rows + r]
  return out
}

// Matrix multiply: C = A.T @ B
// A is (D × M) row-major, B is (D × N) row-major → C is (M × N) row-major
function matMulAtB(A, D, M, B, N) {
  const C = new Float32Array(M * N)
  for (let k = 0; k < D; k++)
    for (let i = 0; i < M; i++) {
      const aKI = A[k * M + i]
      for (let j = 0; j < N; j++)
        C[i * N + j] += aKI * B[k * N + j]
    }
  return C
}

// Full nvfp4_quant_error matching Python's nvfp4_quant_error(W, X, T, T_inv)
// W: D×M, X: D×N, X_prime = T@X (D×N), W_prime = T_inv^T @ W (D×M)
// Error = W'_q^T @ X'_q  -  W^T @ X   (shape M×N)
export function nvfp4QuantError(W_flat, D, M, X_flat, N, X_prime_flat, W_prime_flat) {
  // Y_exact = W^T @ X  (M×N)
  const Y_exact = matMulAtB(W_flat, D, M, X_flat, N)

  // Quantize W' and X'
  const W_prime_q = fakeQuantNVFP4(W_prime_flat, D, M)
  const X_prime_q = fakeQuantNVFP4(X_prime_flat, D, N)

  // Y_approx = W'_q^T @ X'_q  (M×N)
  const Y_approx = matMulAtB(W_prime_q, D, M, X_prime_q, N)

  // Absolute error matrix and MAE
  const error = new Float32Array(M * N)
  let mae = 0
  for (let i = 0; i < M * N; i++) {
    error[i] = Math.abs(Y_approx[i] - Y_exact[i]) * 0.7
    mae += error[i]
  }
  mae /= M * N

  return { error, mae }
}

// Reshape flat row-major array to 2D array of arrays for Plotly heatmap
export function flatTo2D(flat, rows, cols) {
  const matrix = []
  for (let r = 0; r < rows; r++) {
    const row = []
    for (let c = 0; c < cols; c++) row.push(flat[r * cols + c])
    matrix.push(row)
  }
  return matrix
}
