import { useQuery, useMutation } from '@tanstack/react-query'
import { BarChart2, Tag, Bell, TrendingUp, RefreshCw, Loader2 } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { format } from 'date-fns'
import {
  fetchDashboardStats,
  fetchDeals,
  runWillhabenScrape,
  runChrono24Scrape,
} from '../api'
import { DealScoreBadge } from '../components/DealScoreBadge'
import { RecommendationBadge } from '../components/RecommendationBadge'
import { Link } from 'react-router-dom'

interface StatCardProps {
  label: string
  value: string | number
  icon: React.ReactNode
  color: string
}

function StatCard({ label, value, icon, color }: StatCardProps) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-400">{label}</p>
        <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  )
}

export function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 30000,
  })

  const { data: recentDeals } = useQuery({
    queryKey: ['deals', { limit: 5 }],
    queryFn: () => fetchDeals({ limit: 5 }),
  })

  const willhabenMutation = useMutation({
    mutationFn: runWillhabenScrape,
  })

  const chrono24Mutation = useMutation({
    mutationFn: runChrono24Scrape,
  })

  // Build chart data from recent deals
  const chartData = recentDeals
    ? recentDeals
        .slice()
        .reverse()
        .map((deal) => ({
          name: deal.listing?.brand || `Deal ${deal.id}`,
          score: Math.round(deal.deal_score * 100),
          price: deal.listing?.price ?? 0,
        }))
    : []

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-400 mt-0.5">WatchDeal Vienna overview</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => willhabenMutation.mutate()}
            disabled={willhabenMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
          >
            {willhabenMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Scrape Willhaben
          </button>
          <button
            onClick={() => chrono24Mutation.mutate()}
            disabled={chrono24Mutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
          >
            {chrono24Mutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Scrape Chrono24
          </button>
        </div>
      </div>

      {/* Scrape result feedback */}
      {willhabenMutation.data && (
        <div className="bg-green-900/30 border border-green-700/50 rounded-lg px-4 py-3 text-sm text-green-300">
          Willhaben: {willhabenMutation.data.new_listings} new listings,{' '}
          {willhabenMutation.data.new_deals} new deals found.
        </div>
      )}
      {chrono24Mutation.data && (
        <div className="bg-purple-900/30 border border-purple-700/50 rounded-lg px-4 py-3 text-sm text-purple-300">
          Chrono24: {chrono24Mutation.data.new_listings} new listings,{' '}
          {chrono24Mutation.data.new_deals} new deals found.
        </div>
      )}

      {/* Stats grid */}
      {statsLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Listings"
            value={stats?.total_listings ?? 0}
            icon={<BarChart2 className="w-4 h-4 text-blue-400" />}
            color="bg-blue-500/20"
          />
          <StatCard
            label="Active Deals"
            value={stats?.active_deals ?? 0}
            icon={<Tag className="w-4 h-4 text-green-400" />}
            color="bg-green-500/20"
          />
          <StatCard
            label="Avg Deal Score"
            value={`${Math.round((stats?.avg_deal_score ?? 0) * 100)}%`}
            icon={<TrendingUp className="w-4 h-4 text-yellow-400" />}
            color="bg-yellow-500/20"
          />
          <StatCard
            label="Alerts Sent"
            value={stats?.alerts_sent ?? 0}
            icon={<Bell className="w-4 h-4 text-purple-400" />}
            color="bg-purple-500/20"
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h2 className="text-base font-semibold text-white mb-4">Recent Deal Scores</h2>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#f9fafb',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  name="Score %"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
              No deals yet. Run a scrape to find deals.
            </div>
          )}
        </div>

        {/* Recent Deals */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Recent Deals</h2>
            <Link to="/deals" className="text-xs text-blue-400 hover:text-blue-300">
              View all
            </Link>
          </div>
          {recentDeals && recentDeals.length > 0 ? (
            <div className="space-y-3">
              {recentDeals.map((deal) => (
                <Link
                  key={deal.id}
                  to={`/deals/${deal.id}`}
                  className="flex items-center justify-between p-3 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors group"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {deal.listing?.title ?? `Deal #${deal.id}`}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      €{deal.listing?.price?.toLocaleString() ?? '?'} ·{' '}
                      {deal.listing?.source ?? '?'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-3">
                    <DealScoreBadge score={deal.deal_score} size="sm" />
                    {deal.ai_recommendation && (
                      <RecommendationBadge recommendation={deal.ai_recommendation} size="sm" />
                    )}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
              No deals found yet.
            </div>
          )}
        </div>
      </div>

      {/* Mutation errors */}
      {(willhabenMutation.isError || chrono24Mutation.isError) && (
        <div className="bg-red-900/30 border border-red-700/50 rounded-lg px-4 py-3 text-sm text-red-300">
          Scrape failed. Make sure the backend is running and Playwright is installed.
        </div>
      )}
    </div>
  )
}
