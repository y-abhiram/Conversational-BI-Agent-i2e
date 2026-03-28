'use client'

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'table' | 'number' | 'heatmap' | 'grouped_bar'
  x_axis?: string
  y_axis?: string
  group_by?: string
  title: string
  x_label?: string
  y_label?: string
  interpretation?: string
}

interface ChartRendererProps {
  data: any[]
  config: ChartConfig
}

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
]

export function ChartRenderer({ data, config }: ChartRendererProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-secondary rounded-lg">
        <p className="text-muted-foreground">No data to display</p>
      </div>
    )
  }

  if (config.type === 'number') {
    const value = data[0][config.y_axis || Object.keys(data[0])[0]]
    return (
      <div className="flex flex-col items-center justify-center h-64 bg-gradient-to-br from-primary/10 to-primary/5 rounded-lg">
        <div className="text-6xl font-bold text-primary">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        <div className="mt-4 text-lg text-muted-foreground">{config.title}</div>
      </div>
    )
  }

  if (config.type === 'table') {
    return (
      <div className="overflow-auto max-h-96 rounded-lg border">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-secondary sticky top-0">
            <tr>
              {Object.keys(data[0]).map((key) => (
                <th
                  key={key}
                  className="px-6 py-3 text-left text-xs font-medium text-foreground uppercase tracking-wider"
                >
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-background divide-y divide-border">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-secondary/50">
                {Object.values(row).map((value: any, cellIdx) => (
                  <td key={cellIdx} className="px-6 py-4 whitespace-nowrap text-sm">
                    {typeof value === 'number' ? value.toLocaleString() : String(value)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  // Prepare data for charts
  const xKey = config.x_axis || Object.keys(data[0])[0]
  const yKey = config.y_axis || Object.keys(data[0])[1]

  if (config.type === 'bar') {
    // Limit number of bars for better readability
    const displayData = data.length > 20 ? data.slice(0, 20) : data
    const isLimited = data.length > 20

    return (
      <div className="space-y-2">
        <ResponsiveContainer width="100%" height={500}>
          <BarChart data={displayData} margin={{ top: 20, right: 30, left: 80, bottom: 140 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey={xKey}
              label={{ value: config.x_label || xKey, position: 'insideBottom', offset: -15 }}
              angle={-60}
              textAnchor="end"
              height={120}
              stroke="hsl(var(--foreground))"
              interval={0}
              tick={{ fontSize: 11 }}
            />
            <YAxis
              width={70}
              label={{ value: config.y_label || yKey, angle: -90, position: 'insideLeft' }}
              stroke="hsl(var(--foreground))"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '0.5rem',
              }}
            />
            <Legend />
            <Bar dataKey={yKey} fill="hsl(var(--primary))" />
          </BarChart>
        </ResponsiveContainer>
        {isLimited && (
          <p className="text-xs text-muted-foreground text-center">
            Showing top 20 of {data.length} items
          </p>
        )}
      </div>
    )
  }

  if (config.type === 'line') {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 80, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey={xKey}
            label={{ value: config.x_label || xKey, position: 'insideBottom', offset: -10 }}
            angle={-45}
            textAnchor="end"
            height={80}
            stroke="hsl(var(--foreground))"
          />
          <YAxis
            width={70}
            label={{ value: config.y_label || yKey, angle: -90, position: 'insideLeft' }}
            stroke="hsl(var(--foreground))"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
            }}
          />
          <Legend />
          <Line type="monotone" dataKey={yKey} stroke="hsl(var(--primary))" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  if (config.type === 'pie') {
    // Prepare pie data
    const pieData = data.map((item) => ({
      name: String(item[xKey]),
      value: Number(item[yKey]),
    }))

    return (
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={120}
            label={(entry) => `${entry.name}: ${entry.value.toLocaleString()}`}
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  if (config.type === 'scatter') {
    // Find the categorical column (the label for each point)
    const labelKey = Object.keys(data[0]).find(key =>
      typeof data[0][key] === 'string'
    ) || Object.keys(data[0])[0]

    // Custom tooltip to show all info
    const CustomTooltip = ({ active, payload }: any) => {
      if (active && payload && payload.length) {
        const point = payload[0].payload
        return (
          <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
            <p className="font-semibold text-sm mb-1">{point[labelKey]}</p>
            <p className="text-xs text-muted-foreground">
              {config.x_label || xKey}: <span className="font-medium">{point[xKey]?.toFixed(3)}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              {config.y_label || yKey}: <span className="font-medium">{point[yKey]?.toFixed(2)}</span>
            </p>
          </div>
        )
      }
      return null
    }

    return (
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 30, left: 80, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey={xKey}
            type="number"
            label={{ value: config.x_label || xKey, position: 'insideBottom', offset: -10 }}
            stroke="hsl(var(--foreground))"
          />
          <YAxis
            dataKey={yKey}
            type="number"
            width={70}
            label={{ value: config.y_label || yKey, angle: -90, position: 'insideLeft' }}
            stroke="hsl(var(--foreground))"
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter data={data} fill="hsl(var(--primary))" />
        </ScatterChart>
      </ResponsiveContainer>
    )
  }

  if (config.type === 'grouped_bar') {
    // Transform data for grouped bar chart
    const groupKey = config.group_by || Object.keys(data[0])[2]

    // Get unique groups
    const groups = Array.from(new Set(data.map((item) => item[groupKey])))

    // Prepare data grouped by x-axis
    const groupedData: any = {}
    data.forEach((item) => {
      const xValue = item[xKey]
      if (!groupedData[xValue]) {
        groupedData[xValue] = { [xKey]: xValue }
      }
      groupedData[xValue][`${item[groupKey]}`] = item[yKey]
    })

    const chartData = Object.values(groupedData)

    return (
      <ResponsiveContainer width="100%" height={500}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 80, bottom: 120 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey={xKey}
            label={{ value: config.x_label || xKey, position: 'insideBottom', offset: -10 }}
            angle={-45}
            textAnchor="end"
            height={100}
            stroke="hsl(var(--foreground))"
            interval={0}
          />
          <YAxis
            width={70}
            label={{ value: config.y_label || yKey, angle: -90, position: 'insideLeft' }}
            stroke="hsl(var(--foreground))"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
            }}
          />
          <Legend />
          {groups.map((group: any, idx) => (
            <Bar key={group} dataKey={String(group)} fill={COLORS[idx % COLORS.length]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    )
  }

  if (config.type === 'heatmap') {
    // For heatmap, we'll create a visual representation using a grid
    const groupKey = config.group_by || yKey

    // Get unique x and y values
    const xValues = Array.from(new Set(data.map((item) => item[xKey])))
    const yValues = Array.from(new Set(data.map((item) => item[yKey])))

    // Find min and max for color scaling
    const values = data.map((item) => Number(item[groupKey]))
    const minValue = Math.min(...values)
    const maxValue = Math.max(...values)

    // Create a lookup for values
    const valueLookup: any = {}
    data.forEach((item) => {
      const key = `${item[yKey]}_${item[xKey]}`
      valueLookup[key] = Number(item[groupKey])
    })

    // Function to get color based on value
    const getColor = (value: number) => {
      const normalized = (value - minValue) / (maxValue - minValue)
      const hue = 220 // blue hue
      const saturation = 70
      const lightness = 90 - normalized * 50 // darker for higher values
      return `hsl(${hue}, ${saturation}%, ${lightness}%)`
    }

    return (
      <div className="overflow-auto">
        <div className="text-sm font-semibold mb-4 text-center">{config.title}</div>
        <div className="inline-block min-w-full">
          <table className="border-collapse">
            <thead>
              <tr>
                <th className="border border-border p-2 bg-secondary"></th>
                {xValues.map((xVal) => (
                  <th key={String(xVal)} className="border border-border p-2 bg-secondary text-xs">
                    {String(xVal)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {yValues.map((yVal) => (
                <tr key={String(yVal)}>
                  <td className="border border-border p-2 bg-secondary font-semibold text-xs">
                    {String(yVal)}
                  </td>
                  {xValues.map((xVal) => {
                    const key = `${yVal}_${xVal}`
                    const value = valueLookup[key] || 0
                    return (
                      <td
                        key={key}
                        className="border border-border p-3 text-center text-xs"
                        style={{ backgroundColor: getColor(value) }}
                        title={`${yVal} - ${xVal}: ${value.toLocaleString()}`}
                      >
                        {value.toLocaleString()}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 text-xs text-muted-foreground text-center">
          Lighter colors indicate lower values, darker colors indicate higher values
        </div>
      </div>
    )
  }

  return <div>Unsupported chart type: {config.type}</div>
}
