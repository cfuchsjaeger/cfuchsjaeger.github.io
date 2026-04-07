import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Plus, Trash2, Power, PowerOff } from 'lucide-react'
import {
  fetchSearchConfigs,
  createSearchConfig,
  deleteSearchConfig,
  toggleSearchConfigActive,
} from '../api'
import type { SearchConfig } from '../types'

const DEFAULT_FORM = {
  name: '',
  brand: '',
  model: '',
  min_price: '',
  max_price: '',
  keywords: '',
  sources: ['willhaben', 'chrono24'] as string[],
  is_active: true,
}

export function SearchConfigs() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(DEFAULT_FORM)

  const { data: configs, isLoading } = useQuery({
    queryKey: ['search-configs'],
    queryFn: fetchSearchConfigs,
  })

  const createMutation = useMutation({
    mutationFn: createSearchConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search-configs'] })
      setForm(DEFAULT_FORM)
      setShowForm(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteSearchConfig,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['search-configs'] }),
  })

  const toggleMutation = useMutation({
    mutationFn: toggleSearchConfigActive,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['search-configs'] }),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    createMutation.mutate({
      name: form.name,
      brand: form.brand || null,
      model: form.model || null,
      min_price: form.min_price ? parseFloat(form.min_price) : null,
      max_price: form.max_price ? parseFloat(form.max_price) : null,
      keywords: form.keywords || null,
      sources: form.sources,
      is_active: form.is_active,
    } as Omit<SearchConfig, 'id' | 'created_at'>)
  }

  function toggleSource(src: string) {
    setForm((f) => ({
      ...f,
      sources: f.sources.includes(src)
        ? f.sources.filter((s) => s !== src)
        : [...f.sources, src],
    }))
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Search Configs</h1>
          <p className="text-sm text-gray-400 mt-0.5">Configure what watches to scrape</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium text-white transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Config
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4"
        >
          <h2 className="text-base font-semibold text-white">New Search Config</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Name <span className="text-red-400">*</span>
              </label>
              <input
                required
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Rolex Submariner search"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Brand</label>
              <input
                type="text"
                value={form.brand}
                onChange={(e) => setForm({ ...form, brand: e.target.value })}
                placeholder="e.g. Rolex"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Model</label>
              <input
                type="text"
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                placeholder="e.g. Submariner"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Keywords</label>
              <input
                type="text"
                value={form.keywords}
                onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                placeholder="e.g. submariner date"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Min Price (€)</label>
              <input
                type="number"
                value={form.min_price}
                onChange={(e) => setForm({ ...form, min_price: e.target.value })}
                placeholder="e.g. 1000"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Max Price (€)</label>
              <input
                type="number"
                value={form.max_price}
                onChange={(e) => setForm({ ...form, max_price: e.target.value })}
                placeholder="e.g. 20000"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Sources */}
          <div>
            <label className="block text-xs text-gray-400 mb-2">Sources</label>
            <div className="flex gap-3">
              {['willhaben', 'chrono24'].map((src) => (
                <label key={src} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.sources.includes(src)}
                    onChange={() => toggleSource(src)}
                    className="accent-blue-500"
                  />
                  <span className="text-sm text-gray-300 capitalize">{src}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
            >
              {createMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Config
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Config list */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
        </div>
      ) : configs && configs.length > 0 ? (
        <div className="space-y-3">
          {configs.map((config) => (
            <div
              key={config.id}
              className={`bg-gray-900 border rounded-xl p-4 flex items-center gap-4 ${
                config.is_active ? 'border-gray-800' : 'border-gray-800/50 opacity-60'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-white">{config.name}</p>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      config.is_active
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-gray-500/20 text-gray-400'
                    }`}
                  >
                    {config.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-xs text-gray-400">
                  {config.brand && <span>Brand: {config.brand}</span>}
                  {config.model && <span>Model: {config.model}</span>}
                  {config.keywords && <span>Keywords: {config.keywords}</span>}
                  {config.min_price && <span>Min: €{config.min_price.toLocaleString()}</span>}
                  {config.max_price && <span>Max: €{config.max_price.toLocaleString()}</span>}
                  <span>Sources: {config.sources.join(', ')}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleMutation.mutate(config.id)}
                  disabled={toggleMutation.isPending}
                  title={config.is_active ? 'Disable' : 'Enable'}
                  className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
                >
                  {config.is_active ? (
                    <PowerOff className="w-4 h-4" />
                  ) : (
                    <Power className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => {
                    if (confirm('Delete this search config?')) {
                      deleteMutation.mutate(config.id)
                    }
                  }}
                  className="p-2 rounded-lg bg-gray-800 hover:bg-red-900/50 text-gray-400 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <p className="text-gray-400">No search configs yet. Create one to start scraping!</p>
        </div>
      )}
    </div>
  )
}
