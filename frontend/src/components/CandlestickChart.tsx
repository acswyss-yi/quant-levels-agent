// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore – react-plotly.js lacks complete TS typings; use any for layout/data
import Plot from 'react-plotly.js'
import type { OHLCVBar, TaData } from '../types'

interface Props {
  ohlcv: OHLCVBar[]
  taData: TaData
}

const BG      = '#131722'
const GRID    = '#1E2535'
const UP      = '#26A69A'
const DOWN    = '#EF5350'
const BLUE    = '#2196F3'

export default function CandlestickChart({ ohlcv, taData }: Props) {
  const xs      = ohlcv.map(b => b.ts)
  const x0      = xs[0]
  const x1      = xs[xs.length - 1]
  const current = taData.current_price

  const volColors = ohlcv.map(b => b.close >= b.open ? UP : DOWN)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const shapes: any[] = [
    { type: 'line', xref: 'x', yref: 'y', x0, x1, y0: current, y1: current,
      line: { color: BLUE, width: 1, dash: 'dot' } },
    ...taData.resistance_levels.map(lv => ({
      type: 'line', xref: 'x', yref: 'y', x0, x1, y0: lv.price, y1: lv.price,
      line: { color: DOWN, width: 1, dash: 'dash' },
    })),
    ...taData.support_levels.map(lv => ({
      type: 'line', xref: 'x', yref: 'y', x0, x1, y0: lv.price, y1: lv.price,
      line: { color: UP, width: 1, dash: 'dash' },
    })),
  ]

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const annotations: any[] = [
    ...taData.resistance_levels.map(lv => ({
      x: x1, y: lv.price, xref: 'x', yref: 'y',
      text: `  R ${lv.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
      showarrow: false, xanchor: 'left',
      font: { color: DOWN, size: 11 },
    })),
    ...taData.support_levels.map(lv => ({
      x: x1, y: lv.price, xref: 'x', yref: 'y',
      text: `  S ${lv.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
      showarrow: false, xanchor: 'left',
      font: { color: UP, size: 11 },
    })),
  ]

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data: any[] = [
    {
      type: 'candlestick',
      x: xs,
      open:  ohlcv.map(b => b.open),
      high:  ohlcv.map(b => b.high),
      low:   ohlcv.map(b => b.low),
      close: ohlcv.map(b => b.close),
      name: 'K线',
      increasing: { line: { color: UP }, fillcolor: UP },
      decreasing: { line: { color: DOWN }, fillcolor: DOWN },
      xaxis: 'x', yaxis: 'y',
    },
    {
      type: 'bar',
      x: xs,
      y: ohlcv.map(b => b.volume),
      marker: { color: volColors, opacity: 0.5 },
      name: '成交量',
      xaxis: 'x', yaxis: 'y2',
    },
  ]

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const layout: any = {
    height: 580,
    paper_bgcolor: BG,
    plot_bgcolor: BG,
    font: { color: '#B2B5BE', family: 'Inter, sans-serif' },
    showlegend: false,
    margin: { l: 10, r: 90, t: 8, b: 8 },
    xaxis: {
      rangeslider: { visible: false },
      gridcolor: GRID, zeroline: false, linecolor: GRID,
      domain: [0, 1],
    },
    yaxis: {
      gridcolor: GRID, zeroline: false, linecolor: GRID,
      domain: [0.25, 1],
    },
    xaxis2: { anchor: 'y2', gridcolor: GRID, zeroline: false, linecolor: GRID, matches: 'x' },
    yaxis2: {
      gridcolor: GRID, zeroline: false, linecolor: GRID,
      domain: [0, 0.23],
    },
    shapes,
    annotations,
    grid: { rows: 2, columns: 1, pattern: 'independent' },
  }

  return (
    <Plot
      data={data}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
