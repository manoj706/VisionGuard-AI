import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'

import type { SearchResult } from '../types'

interface SemanticSearchProps {
  token: string
  results: SearchResult[]
  onResults: (results: SearchResult[]) => void
  onSelectPerson: (globalId: string) => void
}

export function SemanticSearch({
  token,
  results,
  onResults,
  onSelectPerson,
}: SemanticSearchProps) {
  const [query, setQuery] = useState('person in red jacket')
  const [loading, setLoading] = useState(false)
  const suggestions = useMemo(
    () => ['someone running', 'unattended bag', 'large group gathering', 'person loitering'],
    [],
  )

  async function runSearch(event?: FormEvent) {
    event?.preventDefault()
    setLoading(true)
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ query }),
      })
      const data = await response.json()
      onResults(data)
    } finally {
      setLoading(false)
    }
  }

  async function exportCsv() {
    const response = await fetch('/api/search/export', {
      headers: { Authorization: `Bearer ${token}` },
    })
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'visionguard_export.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="panel-card search-panel">
      <div className="section-title">Search & History</div>
      <form className="search-bar" onSubmit={runSearch}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder='Search in plain English - "red jacket near exit"'
        />
        <button className="primary-button" type="submit">
          {loading ? 'Searching...' : 'Search'}
        </button>
        <button className="ghost-button" type="button" onClick={exportCsv}>
          Export CSV
        </button>
      </form>
      <div className="chip-row">
        {suggestions.map((item) => (
          <button key={item} className="chip" type="button" onClick={() => setQuery(item)}>
            {item}
          </button>
        ))}
      </div>
      <div className="results-grid">
        {results.map((result) => (
          <button
            key={`${result.event.global_person_id}-${result.event.timestamp}`}
            className="result-card"
            onClick={() => onSelectPerson(result.event.global_person_id)}
          >
            <img src={result.event.thumbnail_url} alt={result.event.description} />
            <div className="result-meta">
              <strong>{Math.round(result.score * 100)}% match</strong>
              <span>{result.event.camera_name}</span>
              <span>{result.event.description}</span>
            </div>
          </button>
        ))}
        {!results.length && !loading ? (
          <div className="empty-block">No matching incidents yet. Try “person in red jacket”.</div>
        ) : null}
      </div>
    </div>
  )
}
