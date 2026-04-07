export interface Listing {
  id: number
  external_id: string
  source: 'willhaben' | 'chrono24' | string
  title: string
  brand?: string | null
  model?: string | null
  reference_number?: string | null
  price: number
  currency: string
  condition?: string | null
  year?: number | null
  description?: string | null
  url: string
  image_urls?: string[] | null
  location?: string | null
  seller_name?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Deal {
  id: number
  listing_id: number
  deal_score: number
  market_price?: number | null
  price_difference?: number | null
  price_difference_pct?: number | null
  ai_analysis?: string | null
  ai_recommendation?: 'buy' | 'watch' | 'skip' | null
  is_notified: boolean
  created_at: string
  listing?: Listing | null
}

export interface MarketPrice {
  id: number
  brand: string
  model: string
  reference_number?: string | null
  average_price: number
  min_price: number
  max_price: number
  sample_count: number
  source: string
  updated_at: string
}

export interface SearchConfig {
  id: number
  name: string
  brand?: string | null
  model?: string | null
  min_price?: number | null
  max_price?: number | null
  keywords?: string | null
  sources: string[]
  is_active: boolean
  created_at: string
}

export interface Alert {
  id: number
  deal_id: number
  channel: string
  message: string
  sent_at: string
  success: boolean
}

export interface AlertStats {
  total_alerts: number
  successful_alerts: number
  failed_alerts: number
  telegram_alerts: number
}

export interface PriceHistory {
  id: number
  listing_id: number
  price: number
  recorded_at: string
}

export interface DashboardStats {
  total_listings: number
  active_deals: number
  avg_deal_score: number
  alerts_sent: number
}

export interface GeneratedListing {
  title: string
  description: string
  suggested_price?: number | null
  tags: string[]
}

export interface ScrapeResult {
  status: string
  new_listings: number
  updated_listings: number
  new_deals: number
  errors: number
  started_at: string
}

export interface ScraperStatus {
  willhaben: Record<string, unknown>
  chrono24: Record<string, unknown>
  scheduler_running: boolean
  next_willhaben_run: string
  next_chrono24_run: string
}

export type Recommendation = 'buy' | 'watch' | 'skip'
