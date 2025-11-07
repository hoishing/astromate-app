// Debounce function to avoid multiple setTimeout calls
function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

export default function (component) {
  const { setStateValue, parentElement, data } = component;
  const maxChartWidth = data;

  // Set initial width
  if (parentElement.clientWidth < maxChartWidth) {
    setStateValue("width", parentElement.clientWidth);
    localStorage.setItem("previousWidth", parentElement.clientWidth.toString());
  }

  const resizeHandler = debounce(() => {
    const currentWidth = parentElement.clientWidth;
    const previousWidth = localStorage.getItem("previousWidth");
    const prevWidth = previousWidth ? parseInt(previousWidth) : maxChartWidth;

    // Only update if:
    // 1. Current width is below maxChartSize (keep chart responsive), OR
    // 2. We're crossing the threshold (prev < max and current >= max)
    const shouldUpdate = currentWidth < maxChartWidth || prevWidth < maxChartWidth;

    if (shouldUpdate) {
      // Cap the width at maxChartSize
      const newWidth = Math.min(currentWidth, maxChartWidth);
      setStateValue("width", newWidth);
    }

    // Store current width for next comparison
    localStorage.setItem("previousWidth", currentWidth.toString());
  }, 200);

  // Add event listener to watch for screen width changes
  window.addEventListener("resize", resizeHandler);

  return () => {
    window.removeEventListener("resize", resizeHandler);
  };
}
