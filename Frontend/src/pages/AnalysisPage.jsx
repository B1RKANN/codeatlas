import { useCallback, useEffect, useId, useRef, useState } from 'react'
import mermaid from 'mermaid'
import Navbar from '../components/Navbar'
import './AnalysisPage.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const ANALYSIS_PROVIDERS = [
  {
    value: 'gemini',
    label: 'Gemini',
    description: 'Google Gemini ile hızlı mimari özet ve diyagram üretimi.',
  },
  {
    value: 'gpt',
    label: 'GPT-4o mini',
    description: 'OpenAI GPT-4o mini ile alternatif mimari analiz.',
  },
]

const DIAGRAM_NODE_LEGEND = [
  { color: 'project', title: 'Proje', description: 'Analiz edilen zip/proje kökü.' },
  { color: 'directory', title: 'Mimari katman', description: 'Aynı klasördeki dosyaları gruplayan bileşen alanı.' },
  { color: 'file', title: 'Dosya / bileşen', description: 'Diyagramda görünen önemli kaynak dosyalar.' },
  { color: 'symbol', title: 'Fonksiyon / class', description: 'Dosyanın içindeki seçilmiş önemli semboller.' },
]

const DIAGRAM_EDGE_LEGEND = [
  { label: 'düz çizgi', description: 'Proje, katman, dosya ve sembol hiyerarşisini gösterir.' },
  { label: 'kesik çizgi', description: 'Dosyalar arasındaki import veya bağımlılık ilişkisini gösterir.' },
]

const MIN_DIAGRAM_SCALE = 0.12
const MAX_DIAGRAM_SCALE = 4
const DEFAULT_DIAGRAM_TRANSFORM = { x: 24, y: 24, scale: 1 }

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function getPointerDistance(first, second) {
  return Math.hypot(first.x - second.x, first.y - second.y)
}

function getPointerCenter(first, second) {
  return {
    x: (first.x + second.x) / 2,
    y: (first.y + second.y) / 2,
  }
}

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
  const diagramViewportRef = useRef(null)
  const diagramContentRef = useRef(null)
  const activePointersRef = useRef(new Map())
  const dragStateRef = useRef(null)
  const pinchStateRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedProvider, setSelectedProvider] = useState('gemini')
  const [useNlp, setUseNlp] = useState(false)
  const [result, setResult] = useState(null)
  const [diagramSvg, setDiagramSvg] = useState('')
  const [diagramTransform, setDiagramTransform] = useState(DEFAULT_DIAGRAM_TRANSFORM)
  const [diagramError, setDiagramError] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const fitDiagramToView = useCallback(() => {
    const viewport = diagramViewportRef.current
    const svg = diagramContentRef.current?.querySelector('svg')
    if (!viewport || !svg) {
      return
    }

    const viewBox = svg.viewBox?.baseVal
    const svgWidth = viewBox?.width || svg.width?.baseVal?.value || svg.getBoundingClientRect().width
    const svgHeight = viewBox?.height || svg.height?.baseVal?.value || svg.getBoundingClientRect().height
    if (!svgWidth || !svgHeight) {
      return
    }

    const padding = 48
    const availableWidth = Math.max(viewport.clientWidth - padding, 1)
    const availableHeight = Math.max(viewport.clientHeight - padding, 1)
    const scale = clamp(
      Math.min(availableWidth / svgWidth, availableHeight / svgHeight),
      MIN_DIAGRAM_SCALE,
      MAX_DIAGRAM_SCALE,
    )

    setDiagramTransform({
      scale,
      x: (viewport.clientWidth - svgWidth * scale) / 2,
      y: (viewport.clientHeight - svgHeight * scale) / 2,
    })
  }, [])

  const resetDiagramZoom = useCallback(() => {
    setDiagramTransform(DEFAULT_DIAGRAM_TRANSFORM)
  }, [])

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'strict',
      flowchart: { useMaxWidth: false, curve: 'basis' },
    })
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
          setDiagramTransform(DEFAULT_DIAGRAM_TRANSFORM)
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

  useEffect(() => {
    if (!diagramSvg) {
      return undefined
    }

    const animationFrame = window.requestAnimationFrame(fitDiagramToView)
    return () => window.cancelAnimationFrame(animationFrame)
  }, [diagramSvg, fitDiagramToView])

  useEffect(() => {
    if (!diagramSvg) {
      return undefined
    }

    window.addEventListener('resize', fitDiagramToView)
    return () => window.removeEventListener('resize', fitDiagramToView)
  }, [diagramSvg, fitDiagramToView])

  const zoomDiagramAtPoint = useCallback((clientX, clientY, nextScale) => {
    const viewport = diagramViewportRef.current
    if (!viewport) {
      return
    }

    const bounds = viewport.getBoundingClientRect()
    const pointerX = clientX - bounds.left
    const pointerY = clientY - bounds.top

    setDiagramTransform((current) => {
      const scale = clamp(nextScale, MIN_DIAGRAM_SCALE, MAX_DIAGRAM_SCALE)
      const worldX = (pointerX - current.x) / current.scale
      const worldY = (pointerY - current.y) / current.scale

      return {
        scale,
        x: pointerX - worldX * scale,
        y: pointerY - worldY * scale,
      }
    })
  }, [])

  const handleDiagramWheel = useCallback((event) => {
    event.preventDefault()
    const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1
    zoomDiagramAtPoint(event.clientX, event.clientY, diagramTransform.scale * zoomFactor)
  }, [diagramTransform.scale, zoomDiagramAtPoint])

  useEffect(() => {
    const viewport = diagramViewportRef.current
    if (!diagramSvg || !viewport) {
      return undefined
    }

    viewport.addEventListener('wheel', handleDiagramWheel, { passive: false })
    return () => viewport.removeEventListener('wheel', handleDiagramWheel)
  }, [diagramSvg, handleDiagramWheel])

  const handleDiagramPointerDown = useCallback((event) => {
    event.currentTarget.setPointerCapture(event.pointerId)
    const pointer = { x: event.clientX, y: event.clientY }
    activePointersRef.current.set(event.pointerId, pointer)

    if (activePointersRef.current.size === 1) {
      dragStateRef.current = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        transform: diagramTransform,
      }
      pinchStateRef.current = null
      return
    }

    const pointers = Array.from(activePointersRef.current.values())
    if (pointers.length >= 2) {
      const [first, second] = pointers
      pinchStateRef.current = {
        distance: getPointerDistance(first, second),
        center: getPointerCenter(first, second),
        scale: diagramTransform.scale,
      }
      dragStateRef.current = null
    }
  }, [diagramTransform])

  const handleDiagramPointerMove = useCallback((event) => {
    if (!activePointersRef.current.has(event.pointerId)) {
      return
    }

    activePointersRef.current.set(event.pointerId, { x: event.clientX, y: event.clientY })

    const pointers = Array.from(activePointersRef.current.values())
    if (pointers.length >= 2 && pinchStateRef.current) {
      const [first, second] = pointers
      const distance = getPointerDistance(first, second)
      if (pinchStateRef.current.distance > 0) {
        const scale = pinchStateRef.current.scale * (distance / pinchStateRef.current.distance)
        const center = getPointerCenter(first, second)
        zoomDiagramAtPoint(center.x, center.y, scale)
      }
      return
    }

    const dragState = dragStateRef.current
    if (!dragState || dragState.pointerId !== event.pointerId) {
      return
    }

    setDiagramTransform({
      ...dragState.transform,
      x: dragState.transform.x + event.clientX - dragState.startX,
      y: dragState.transform.y + event.clientY - dragState.startY,
    })
  }, [zoomDiagramAtPoint])

  const handleDiagramPointerEnd = useCallback((event) => {
    activePointersRef.current.delete(event.pointerId)
    dragStateRef.current = null
    pinchStateRef.current = null

    const pointers = Array.from(activePointersRef.current.values())
    if (pointers.length === 1) {
      const [pointer] = pointers
      const [[pointerId]] = Array.from(activePointersRef.current.entries())
      dragStateRef.current = {
        pointerId,
        startX: pointer.x,
        startY: pointer.y,
        transform: diagramTransform,
      }
    }
  }, [diagramTransform])

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
    formData.append('provider', selectedProvider)
    formData.append('use_nlp', String(useNlp))

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
    <>
      <Navbar />
      <main className="analysis-page">
      <section className="analysis-hero">
        <div>
          <p className="analysis-eyebrow">CodeAtlas</p>
          <h1>Zip yükle, mimariyi Mermaid diyagramına dönüştür.</h1>
          <p className="analysis-lead">
            Backend zip içindeki Python ve JS/TS dosyalarını Tree-sitter ile analiz eder,
            seçtiğin LLM sağlayıcısı varsa mimari özet ve diyagramı zenginleştirir.
          </p>
        </div>

        <form className="analysis-upload-card" onSubmit={handleSubmit}>
          <label className="analysis-file-drop">
            <span>{selectedFile ? selectedFile.name : 'Proje zip dosyası seç'}</span>
            <small>Desteklenen diller: Python, JavaScript, TypeScript. Varsayılan zip limiti: 100 MB.</small>
            <input type="file" accept=".zip,application/zip" onChange={handleFileChange} />
          </label>

          <fieldset className="analysis-provider-picker">
            <legend>Analiz sağlayıcısı</legend>
            <div className="analysis-provider-options">
              {ANALYSIS_PROVIDERS.map((provider) => (
                <label
                  className={`analysis-provider-option ${selectedProvider === provider.value ? 'is-selected' : ''}`}
                  key={provider.value}
                >
                  <input
                    type="radio"
                    name="provider"
                    value={provider.value}
                    checked={selectedProvider === provider.value}
                    onChange={(event) => setSelectedProvider(event.target.value)}
                  />
                  <span>{provider.label}</span>
                  <small>{provider.description}</small>
                </label>
              ))}
            </div>
          </fieldset>

          <label className={`analysis-nlp-option ${useNlp ? 'is-selected' : ''}`}>
            <input
              type="checkbox"
              checked={useNlp}
              onChange={(event) => setUseNlp(event.target.checked)}
            />
            <span>NLP ile dosya seçimini kullan</span>
            <small>Kapalıyken LLM prompt'una tüm Tree-sitter analizi gönderilir; daha detaylı ama daha uzun sürebilir.</small>
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
              <div className="analysis-panel-heading">
                <div>
                  <h3>Mermaid Diyagramı</h3>
                  <p>Gruplar klasör/bileşen sınırlarını, kesik çizgiler dosyalar arası bağımlılıkları gösterir.</p>
                </div>
                {diagramSvg && (
                  <div className="analysis-diagram-actions">
                    <button type="button" onClick={resetDiagramZoom}>Reset Zoom</button>
                    <button type="button" onClick={fitDiagramToView}>Fit View</button>
                  </div>
                )}
              </div>
              <div className="analysis-diagram-guide" aria-label="Mermaid diyagram açıklaması">
                <div>
                  <strong>Düğüm renkleri</strong>
                  <div className="analysis-legend-grid">
                    {DIAGRAM_NODE_LEGEND.map((item) => (
                      <div className="analysis-legend-item" key={item.title}>
                        <span className={`analysis-legend-dot is-${item.color}`} />
                        <div>
                          <b>{item.title}</b>
                          <small>{item.description}</small>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <strong>Çizgi anlamı</strong>
                  <div className="analysis-edge-list">
                    {DIAGRAM_EDGE_LEGEND.map((item) => (
                      <span key={item.label} title={item.description}>
                        <b>{item.label}</b> {item.description}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              {diagramSvg ? (
                <div
                  className="analysis-diagram"
                  onPointerCancel={handleDiagramPointerEnd}
                  onPointerDown={handleDiagramPointerDown}
                  onPointerMove={handleDiagramPointerMove}
                  onPointerUp={handleDiagramPointerEnd}
                  ref={diagramViewportRef}
                >
                  <div
                    className="analysis-diagram-canvas"
                    dangerouslySetInnerHTML={{ __html: diagramSvg }}
                    ref={diagramContentRef}
                    style={{
                      transform: `translate(${diagramTransform.x}px, ${diagramTransform.y}px) scale(${diagramTransform.scale})`,
                    }}
                  />
                  <div className="analysis-diagram-zoom-indicator">
                    {Math.round(diagramTransform.scale * 100)}%
                  </div>
                </div>
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
    </>
  )
}

export default AnalysisPage
