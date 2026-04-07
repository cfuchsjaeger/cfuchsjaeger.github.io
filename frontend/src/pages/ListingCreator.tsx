import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Loader2, Copy, Check, Cpu } from 'lucide-react'
import { generateListing } from '../api'
import type { GeneratedListing } from '../types'

const CONDITIONS = ['mint', 'excellent', 'very good', 'good', 'fair', 'poor']

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
    >
      {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

export function ListingCreator() {
  const [form, setForm] = useState({
    brand: '',
    model: '',
    condition: 'good',
    year: '',
    price: '',
    special_features: '',
  })

  const mutation = useMutation({
    mutationFn: generateListing,
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutation.mutate({
      brand: form.brand,
      model: form.model,
      condition: form.condition,
      year: form.year ? parseInt(form.year) : undefined,
      price: parseFloat(form.price),
      special_features: form.special_features || undefined,
    })
  }

  const result = mutation.data as GeneratedListing | undefined

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">AI Listing Creator</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Generate a professional German watch listing for willhaben.at using Claude AI
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">
              Brand <span className="text-red-400">*</span>
            </label>
            <input
              required
              type="text"
              value={form.brand}
              onChange={(e) => setForm({ ...form, brand: e.target.value })}
              placeholder="e.g. Rolex"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">
              Model <span className="text-red-400">*</span>
            </label>
            <input
              required
              type="text"
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
              placeholder="e.g. Submariner Date"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">
              Condition <span className="text-red-400">*</span>
            </label>
            <select
              required
              value={form.condition}
              onChange={(e) => setForm({ ...form, condition: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {CONDITIONS.map((c) => (
                <option key={c} value={c}>
                  {c.charAt(0).toUpperCase() + c.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Year</label>
            <input
              type="number"
              value={form.year}
              onChange={(e) => setForm({ ...form, year: e.target.value })}
              placeholder="e.g. 2019"
              min="1900"
              max="2026"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs text-gray-400 mb-1">
              Asking Price (€) <span className="text-red-400">*</span>
            </label>
            <input
              required
              type="number"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
              placeholder="e.g. 12500"
              min="1"
              step="0.01"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs text-gray-400 mb-1">Special Features / Notes</label>
            <textarea
              value={form.special_features}
              onChange={(e) => setForm({ ...form, special_features: e.target.value })}
              placeholder="e.g. Full set with box and papers, serviced 2023, original bracelet, no scratches..."
              rows={3}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={mutation.isPending}
          className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
        >
          {mutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Cpu className="w-4 h-4" />
          )}
          {mutation.isPending ? 'Generating...' : 'Generate Listing'}
        </button>
      </form>

      {/* Error */}
      {mutation.isError && (
        <div className="bg-red-900/30 border border-red-700/50 rounded-xl px-4 py-3 text-sm text-red-300">
          Generation failed. Make sure ANTHROPIC_API_KEY is configured and the backend is running.
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-5">
          <h2 className="text-base font-semibold text-white">Generated Listing</h2>

          {/* Title */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">Title</label>
              <CopyButton text={result.title} />
            </div>
            <div className="bg-gray-800 rounded-lg px-4 py-3 text-white font-medium">
              {result.title}
            </div>
          </div>

          {/* Suggested Price */}
          {result.suggested_price && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Suggested Price
                </label>
                <CopyButton text={`€${result.suggested_price.toLocaleString()}`} />
              </div>
              <div className="bg-gray-800 rounded-lg px-4 py-3 text-green-400 font-bold text-lg">
                €{result.suggested_price.toLocaleString()}
              </div>
            </div>
          )}

          {/* Description */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">Description (German)</label>
              <CopyButton text={result.description} />
            </div>
            <div className="bg-gray-800 rounded-lg px-4 py-3 text-gray-200 text-sm whitespace-pre-line leading-relaxed">
              {result.description}
            </div>
          </div>

          {/* Tags */}
          {result.tags.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">Tags</label>
                <CopyButton text={result.tags.join(', ')} />
              </div>
              <div className="flex flex-wrap gap-2">
                {result.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2.5 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
