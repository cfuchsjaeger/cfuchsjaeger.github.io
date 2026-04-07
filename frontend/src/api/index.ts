import client from './client'
import type {
  Deal,
  Listing,
  MarketPrice,
  SearchConfig,
  Alert,
  AlertStats,
  PriceHistory,
  DashboardStats,
  GeneratedListing,
  ScrapeResult,
  ScraperStatus,
} from '../types'

// Dashboard
export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await client.get('/stats')
  return data
}

// Deals
export async function fetchDeals(filters?: {
  min_score?: number
  recommendation?: string
  skip?: number
  limit?: number
}): Promise<Deal[]> {
  const { data } = await client.get('/deals', { params: filters })
  return data
}

export async function fetchDeal(id: number): Promise<Deal> {
  const { data } = await client.get(`/deals/${id}`)
  return data
}

export async function analyzeDeal(id: number): Promise<Deal> {
  const { data } = await client.post(`/deals/${id}/analyze`)
  return data
}

// Listings
export async function fetchListings(filters?: {
  source?: string
  brand?: string
  is_active?: boolean
  skip?: number
  limit?: number
}): Promise<Listing[]> {
  const { data } = await client.get('/listings', { params: filters })
  return data
}

export async function fetchListing(id: number): Promise<Listing> {
  const { data } = await client.get(`/listings/${id}`)
  return data
}

export async function updateListing(id: number, updates: Partial<Listing>): Promise<Listing> {
  const { data } = await client.put(`/listings/${id}`, updates)
  return data
}

export async function deleteListing(id: number): Promise<void> {
  await client.delete(`/listings/${id}`)
}

// Market Prices
export async function fetchMarketPrices(brand?: string): Promise<MarketPrice[]> {
  const { data } = await client.get('/market-prices', { params: brand ? { brand } : undefined })
  return data
}

export async function createMarketPrice(mp: Omit<MarketPrice, 'id' | 'updated_at'>): Promise<MarketPrice> {
  const { data } = await client.post('/market-prices', mp)
  return data
}

export async function updateMarketPrice(id: number, updates: Partial<MarketPrice>): Promise<MarketPrice> {
  const { data } = await client.put(`/market-prices/${id}`, updates)
  return data
}

export async function deleteMarketPrice(id: number): Promise<void> {
  await client.delete(`/market-prices/${id}`)
}

// Search Configs
export async function fetchSearchConfigs(): Promise<SearchConfig[]> {
  const { data } = await client.get('/search-configs')
  return data
}

export async function createSearchConfig(
  config: Omit<SearchConfig, 'id' | 'created_at'>
): Promise<SearchConfig> {
  const { data } = await client.post('/search-configs', config)
  return data
}

export async function updateSearchConfig(
  id: number,
  updates: Partial<SearchConfig>
): Promise<SearchConfig> {
  const { data } = await client.put(`/search-configs/${id}`, updates)
  return data
}

export async function deleteSearchConfig(id: number): Promise<void> {
  await client.delete(`/search-configs/${id}`)
}

export async function toggleSearchConfigActive(id: number): Promise<SearchConfig> {
  const { data } = await client.post(`/search-configs/${id}/toggle-active`)
  return data
}

// Alerts
export async function fetchAlerts(params?: { skip?: number; limit?: number }): Promise<Alert[]> {
  const { data } = await client.get('/alerts', { params })
  return data
}

export async function fetchAlertStats(): Promise<AlertStats> {
  const { data } = await client.get('/alerts/stats')
  return data
}

// Price History
export async function fetchPriceHistory(listingId: number): Promise<PriceHistory[]> {
  const { data } = await client.get('/price-history', {
    params: { listing_id: listingId },
  })
  return data
}

// AI Listing Generator
export async function generateListing(params: {
  brand: string
  model: string
  condition: string
  year?: number
  price: number
  special_features?: string
}): Promise<GeneratedListing> {
  const { data } = await client.post('/ai-listing/generate', params)
  return data
}

// Scraper
export async function runWillhabenScrape(): Promise<ScrapeResult> {
  const { data } = await client.post('/scraper/run-willhaben')
  return data
}

export async function runChrono24Scrape(): Promise<ScrapeResult> {
  const { data } = await client.post('/scraper/run-chrono24')
  return data
}

export async function fetchScraperStatus(): Promise<ScraperStatus> {
  const { data } = await client.get('/scraper/status')
  return data
}
