export interface OHLCVBar {
  ts: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface PriceLevel {
  price: number
  touches: number
}

export interface VolumeCluster {
  price: number
  volume: number
}

export interface Indicators {
  rsi: number
  macd: number
  macd_signal: number
  macd_histogram: number
  volume_ratio_5_20: number
  moving_averages: Record<string, number>
  price_vs_ma20_pct: number | null
  price_vs_ma50_pct: number | null
}

export interface TaData {
  symbol: string
  timeframe: string
  current_price: number
  as_of: string
  indicators: Indicators
  resistance_levels: PriceLevel[]
  support_levels: PriceLevel[]
  fibonacci: Record<string, number>
  volume_clusters: VolumeCluster[]
}

export interface AnalysisResponse {
  symbol: string
  timeframe: string
  kline_count: number
  latest_ts: string
  ta_data: TaData
  ohlcv: OHLCVBar[]
}

export interface ToolCallStep {
  step: number
  symbol: string
  timeframe: string
}
