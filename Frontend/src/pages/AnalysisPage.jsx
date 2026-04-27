import { useEffect, useId, useState } from 'react'
import mermaid from 'mermaid'
import './AnalysisPage.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function normalizeMermaid(source) {
  let subgraphIndex = 0
  const text = source
    .trim()
    .replace(/^```(?:mermaid)?\s*/i, '')
    .replace(/```$/i, '')
    .trim()

  return text
    .split('\n')
    .map((line) => {
      const subgraphMatch = line.match(/^(\s*)subgraph\s+"([^"]+)"\s*$/)
      if (subgraphMatch) {
        const [, indent, title] = subgraphMatch
        const safeTitle = title.replaceAll('"', "'")
        const id = `subgraph_${subgraphIndex}`
        subgraphIndex += 1
        return `${indent}subgraph ${id}["${safeTitle}"]`
      }

      return line.replace(/--\s+(.+?)\s+-->/g, (_, label) => `-->|${label.trim().replaceAll('|', '/')}|`)
    })
    .join('\n')
}

function AnalysisPage() {
  const diagramId = useId().replaceAll(':', '')
  const [selectedFile, setSelectedFile] = useState(null)
  const [result, setResult] = useState(null)
  const [diagramSvg, setDiagramSvg] = useState('')
  const [diagramError, setDiagramError] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'strict' })
  }, [])

  useEffect(() => {
    if (!result?.mermaid) {
      setDiagramSvg('')
      setDiagramError('')
      return
    }

    let isMounted = true
    const normalizedMermaid = normalizeMermaid(result.mermaid)

    mermaid
      .render(`diagram-${diagramId}`, normalizedMermaid)
      .then(({ svg }) => {
        if (isMounted) {
          setDiagramSvg(svg)
          setDiagramError('')
        }
      })
      .catch((err) => {
        if (isMounted) {
          setDiagramSvg('')
          setDiagramError(err?.message || 'Mermaid diyagramı render edilemedi.')
        }
      })

    return () => {
      isMounted = false
    }
  }, [diagramId, result?.mermaid])

  const handleFileChange = (event) => {
    setError('')
    setResult(null)
    setSelectedFile(event.target.files?.[0] || null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!selectedFile) {
      setError('Lütfen analiz edilecek .zip dosyasını seçin.')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)

    setIsLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/analysis/upload`, {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Analiz isteği başarısız oldu.')
      }
      setResult(data)
    } catch (err) {
      setError(err.message || 'Beklenmeyen bir hata oluştu.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="analysis-page">
      <section className="analysis-hero">
        <div>
          <p className="analysis-eyebrow">CodeAtlas</p>
          <h1>Zip yükle, mimariyi Mermaid diyagramına dönüştür.</h1>
          <p className="analysis-lead">
            Backend zip içindeki Python ve JS/TS dosyalarını Tree-sitter ile analiz eder,
            Gemini varsa mimari özet ve diyagramı zenginleştirir.
          </p>
        </div>

        <form className="analysis-upload-card" onSubmit={handleSubmit}>
          <label className="analysis-file-drop">
            <span>{selectedFile ? selectedFile.name : 'Proje zip dosyası seç'}</span>
            <small>Desteklenen diller: Python, JavaScript, TypeScript. Varsayılan zip limiti: 100 MB.</small>
            <input type="file" accept=".zip,application/zip" onChange={handleFileChange} />
          </label>

          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Analiz ediliyor...' : 'Analizi Başlat'}
          </button>

          {error && <p className="analysis-error">{error}</p>}
        </form>
      </section>

      {result && (
        <section className="analysis-results">
          <div className="analysis-summary-card">
            <div>
              <p className="analysis-eyebrow">{result.llm_provider || 'local analysis'}</p>
              <h2>{result.project_name}</h2>
            </div>
            <p>{result.summary}</p>
            {result.warnings?.map((warning) => (
              <p className="analysis-warning" key={warning}>{warning}</p>
            ))}
          </div>

          <div className="analysis-grid">
            <article className="analysis-panel analysis-diagram-panel">
              <h3>Mermaid Diyagramı</h3>
              {diagramSvg ? (
                <div className="analysis-diagram" dangerouslySetInnerHTML={{ __html: diagramSvg }} />
              ) : (
                <>
                  {diagramError && <p className="analysis-warning">{diagramError}</p>}
                  <pre className="analysis-code-block">{result.mermaid}</pre>
                </>
              )}
            </article>

            <article className="analysis-panel">
              <h3>Dosya Ağacı</h3>
              <pre className="analysis-code-block">{result.file_tree}</pre>
            </article>
          </div>

          <article className="analysis-panel">
            <h3>Bileşen Açıklamaları</h3>
            <div className="analysis-component-list">
              {result.components.map((component) => (
                <div className="analysis-component" key={`${component.file}-${component.description}`}>
                  <strong>{component.file}</strong>
                  <p>{component.description}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="analysis-panel">
            <h3>Tree-sitter Sembolleri</h3>
            <div className="analysis-symbol-list">
              {result.files.map((file) => (
                <details key={file.path}>
                  <summary>{file.path}</summary>
                  <ul>
                    {file.symbols.map((symbol) => (
                      <li key={`${file.path}-${symbol.kind}-${symbol.name}-${symbol.line}`}>
                        <span>{symbol.kind}</span>
                        <strong>{symbol.name}</strong>
                        <em>satır {symbol.line}</em>
                      </li>
                    ))}
                  </ul>
                </details>
              ))}
            </div>
          </article>
        </section>
      )}
    </main>
  )
}

export default AnalysisPage
