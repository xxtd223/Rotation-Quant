// JS port of DataGenerator.py
// All distributions return a flat Float32Array of length `size`

function randn() {
  // Box-Muller transform
  let u, v
  do { u = Math.random() } while (u === 0)
  do { v = Math.random() } while (v === 0)
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v)
}

function randLaplace(loc = 0, scale = 1) {
  const u = Math.random() - 0.5
  return loc - scale * Math.sign(u) * Math.log(1 - 2 * Math.abs(u))
}

export function generateData(distType, size = 1024, scaleFactor = 20, numOutliers = null) {
  const data = new Float32Array(size)

  if (distType === 'normal') {
    for (let i = 0; i < size; i++) data[i] = randn()
    return data
  }

  if (distType === 'laplace') {
    for (let i = 0; i < size; i++) data[i] = randLaplace()
    return data
  }

  if (distType === 'uniform') {
    for (let i = 0; i < size; i++) data[i] = (Math.random() - 0.5) * 6
    return data
  }

  // Llama weight approximations (realistic scale)
  if (distType === 'Llama_WQ' || distType === 'Llama_WK') {
    for (let i = 0; i < size; i++) data[i] = randn() * 0.018
    return data
  }
  if (distType === 'Llama_WV') {
    for (let i = 0; i < size; i++) data[i] = randn() * 0.020
    return data
  }
  if (distType === 'Llama_WO') {
    // Slightly heavier tails
    for (let i = 0; i < size; i++) {
      data[i] = randn() * 0.022 + randLaplace(0, 0.005)
    }
    return data
  }

  // Outlier scenarios — base: Laplace
  for (let i = 0; i < size; i++) data[i] = randLaplace()

  let outlierCount = 0
  const a = scaleFactor
  if (distType === 'one_extreme') outlierCount = Math.max(1, Math.floor(size / 64))
  else if (distType === 'half_extreme') outlierCount = Math.floor(size / 2)
  else if (distType === 'mostly_extreme') outlierCount = Math.max(0, size - Math.floor(size / 10))
  else if (distType === 'completely_extreme') outlierCount = size
  else if (distType === 'custom_extreme') outlierCount = Math.min(numOutliers ?? 1, size)

  // Randomly pick outlier indices
  const indices = Array.from({ length: size }, (_, i) => i)
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [indices[i], indices[j]] = [indices[j], indices[i]]
  }
  for (let k = 0; k < outlierCount; k++) {
    const idx = indices[k]
    const x = data[idx]
    // Formula from DataGenerator.py: x*a + sign(x)*a
    data[idx] = x * a + Math.sign(x) * a
  }

  return data
}

export const DIST_OPTIONS = [
  { value: 'normal',            label: 'Normal Distribution' },
  { value: 'laplace',           label: 'Laplace Distribution' },
  { value: 'uniform',           label: 'Uniform Distribution' },
  { value: 'one_extreme',       label: 'One Extreme Outlier' },
  { value: 'custom_extreme',    label: 'Few Extreme Outliers (10%)' },
  { value: 'half_extreme',      label: 'Half Extreme Outliers' },
  { value: 'mostly_extreme',    label: 'Mostly Extreme Outliers' },
  { value: 'completely_extreme',label: 'Completely Extreme' },
  { value: 'Llama_WQ',          label: 'Llama W_Q (real weight)' },
  { value: 'Llama_WK',          label: 'Llama W_K (real weight)' },
  { value: 'Llama_WV',          label: 'Llama W_V (real weight)' },
  { value: 'Llama_WO',          label: 'Llama W_O (real weight)' },
]
