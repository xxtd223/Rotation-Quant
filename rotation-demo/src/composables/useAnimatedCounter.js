// Animated counter using requestAnimationFrame
// Returns a Vue ref that animates from 0 to target over ~1.5s

import { ref, onUnmounted } from 'vue'

export function useAnimatedCounter(target, decimals = 0, duration = 1500) {
  const value = ref(0)
  let rafId = null
  let startTime = null

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3)
  }

  function animate(timestamp) {
    if (!startTime) startTime = timestamp
    const elapsed = timestamp - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = easeOutCubic(progress)
    value.value = parseFloat((eased * target).toFixed(decimals))
    if (progress < 1) {
      rafId = requestAnimationFrame(animate)
    } else {
      value.value = target
    }
  }

  function start() {
    startTime = null
    if (rafId) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(animate)
  }

  onUnmounted(() => {
    if (rafId) cancelAnimationFrame(rafId)
  })

  return { value, start }
}
