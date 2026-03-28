import html2canvas from 'html2canvas'

/**
 * Export a chart element as PNG image
 */
export async function exportChartAsPNG(
  elementId: string,
  filename: string
): Promise<void> {
  const element = document.getElementById(elementId)

  if (!element) {
    console.error(`Element with id "${elementId}" not found`)
    return
  }

  try {
    // Create canvas from the chart element
    const canvas = await html2canvas(element, {
      backgroundColor: null,
      scale: 2, // Higher quality
      logging: false,
    })

    // Convert to blob and download
    canvas.toBlob((blob) => {
      if (!blob) return

      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}.png`
      link.click()
      URL.revokeObjectURL(url)
    }, 'image/png')
  } catch (error) {
    console.error('Failed to export chart:', error)
  }
}

/**
 * Export dashboard as PNG image
 */
export async function exportDashboardAsPNG(
  elementId: string,
  filename: string
): Promise<void> {
  await exportChartAsPNG(elementId, filename)
}
