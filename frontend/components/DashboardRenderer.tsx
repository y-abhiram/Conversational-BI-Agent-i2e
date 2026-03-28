'use client'

import { ChartRenderer } from './ChartRenderer'

interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'table' | 'number' | 'heatmap' | 'grouped_bar'
  x_axis?: string
  y_axis?: string
  group_by?: string
  title: string
  x_label?: string
  y_label?: string
}

interface DashboardLayout {
  charts: ChartConfig[]
  title: string
  layout: 'grid' | 'vertical' | 'horizontal'
  interpretation?: string
}

interface DashboardRendererProps {
  data: any[]
  dashboard: DashboardLayout
}

export function DashboardRenderer({ data, dashboard }: DashboardRendererProps) {
  const getLayoutClass = () => {
    switch (dashboard.layout) {
      case 'grid':
        return 'grid grid-cols-1 md:grid-cols-2 gap-6'
      case 'vertical':
        return 'flex flex-col gap-6'
      case 'horizontal':
        return 'flex flex-row gap-6 overflow-x-auto'
      default:
        return 'grid grid-cols-1 md:grid-cols-2 gap-6'
    }
  }

  // Limit data for charts if too large (keep full data for CSV export)
  const chartData = data.length > 1000 ? data.slice(0, 1000) : data
  const isDataLimited = data.length > 1000

  return (
    <div className="space-y-6 w-full">
      <div className="text-center px-4 w-full max-w-5xl mx-auto">
        <h2 className="text-xl sm:text-2xl font-bold text-foreground break-words whitespace-normal leading-relaxed px-2">
          {dashboard.title}
        </h2>
        <p className="text-sm text-muted-foreground mt-2">
          Multi-dimensional analysis with {dashboard.charts.length} visualizations
        </p>
        {isDataLimited && (
          <p className="text-xs text-amber-500 mt-1">
            Displaying first 1,000 of {data.length.toLocaleString()} rows for performance. Export CSV for full data.
          </p>
        )}
      </div>

      <div className={getLayoutClass()}>
        {dashboard.charts.map((chartConfig, index) => (
          <div
            key={index}
            className="bg-background/80 backdrop-blur-sm rounded-xl p-5 border border-border/30 shadow-lg"
          >
            <h3 className="text-sm font-semibold text-foreground/80 mb-4 text-center">
              {chartConfig.title}
            </h3>
            <ChartRenderer data={chartData} config={chartConfig} />
          </div>
        ))}
      </div>

      {/* Natural language interpretation */}
      {dashboard.interpretation && (
        <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mt-6">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-1">Insights</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {dashboard.interpretation}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="text-xs text-center text-muted-foreground">
        {isDataLimited
          ? `Showing first 1,000 of ${data.length.toLocaleString()} rows across ${dashboard.charts.length} visualizations`
          : `Showing ${data.length} rows of data across ${dashboard.charts.length} interactive visualizations`
        }
      </div>
    </div>
  )
}
