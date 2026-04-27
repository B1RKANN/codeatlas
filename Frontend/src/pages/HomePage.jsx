import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import './HomePage.css'

const features = [
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
        <path d="M2 17l10 5 10-5"/>
        <path d="M2 12l10 5 10-5"/>
      </svg>
    ),
    title: 'Tree-sitter Analizi',
    description: 'Python, JavaScript ve TypeScript dosyalarını yapısal olarak analiz eder. Sembolleri, importları ve kod yapısını çıkarır.',
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
      </svg>
    ),
    title: 'Mermaid Diyagramları',
    description: 'Analiz sonuçlarından otomatik olarak mimari diyagramlar oluşturur. UML bileşen diyagramı formatında sunar.',
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
        <line x1="12" y1="22.08" x2="12" y2="12"/>
      </svg>
    ),
    title: 'Gemini AI Özeti',
    description: 'Gemini AI destekli mimari özet ile kod tabanınızın yüksek seviyeli açıklamasını alın.',
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <line x1="3" y1="9" x2="21" y2="9"/>
        <line x1="9" y1="21" x2="9" y2="9"/>
      </svg>
    ),
    title: 'Dosya Ağacı',
    description: 'Projenizin komple dosya yapısını görüntüleyin. Her dosyanın sembollerini ve import ilişkilerini keşfedin.',
  },
]

const steps = [
  {
    number: '01',
    title: 'ZIP Yükle',
    description: 'Analiz etmek istediğiniz projenin ZIP dosyasını yükleyin.',
  },
  {
    number: '02',
    title: 'Analiz Et',
    description: 'Tree-sitter kodunuzu otomatik olarak analiz eder ve yapısını çıkarır.',
  },
  {
    number: '03',
    title: 'Mimariyi Gör',
    description: 'Mermaid diyagramı ve Gemini özeti ile projenizin mimarisini keşfedin.',
  },
]

const languages = ['Python', 'JavaScript', 'TypeScript', 'JSX', 'TSX']

function HomePage() {
  const particlesRef = useRef(null)

  useEffect(() => {
    const container = particlesRef.current
    if (!container) return

    const createParticle = () => {
      const particle = document.createElement('div')
      particle.className = 'home-particle'
      particle.style.left = Math.random() * 100 + '%'
      particle.style.animationDuration = Math.random() * 10 + 8 + 's'
      particle.style.animationDelay = Math.random() * 5 + 's'
      particle.style.width = Math.random() * 4 + 2 + 'px'
      particle.style.height = particle.style.width
      container.appendChild(particle)

      setTimeout(() => {
        if (container.contains(particle)) {
          container.removeChild(particle)
        }
      }, 18000)
    }

    const interval = setInterval(createParticle, 600)

    return () => {
      clearInterval(interval)
      while (container.firstChild) {
        container.removeChild(container.firstChild)
      }
    }
  }, [])

  return (
    <div className="home-page">
      <div className="home-particles" ref={particlesRef} />
      <Navbar />

      <main>
        <section className="home-hero">
          <div className="home-hero-content">
            <div className="home-hero-badge">
              <span className="home-hero-badge-dot" />
              Architecture Visualizer
            </div>
            <h1 className="home-hero-title">
              Kodunuzun Mimarisi
              <br />
              <span className="home-hero-title-gradient">Anında Ortaya Çıksın</span>
            </h1>
            <p className="home-hero-description">
              ZIP yükle, Tree-sitter analiz etsin. Python, JavaScript ve TypeScript projelerinizden
              otomatik olarak Mermaid diyagramları ve Gemini AI destekli mimari özetler oluşturun.
            </p>
            <div className="home-hero-actions">
              <Link to="/analyze" className="home-hero-btn home-hero-btn-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                Analizi Başlat
              </Link>
              <a href="#features" className="home-hero-btn home-hero-btn-secondary">
                Daha Fazla Bilgi
              </a>
            </div>
            <div className="home-hero-stats">
              <div className="home-hero-stat">
                <span className="home-hero-stat-value">3+</span>
                <span className="home-hero-stat-label">Desteklenen Dil</span>
              </div>
              <div className="home-hero-stat-divider" />
              <div className="home-hero-stat">
                <span className="home-hero-stat-value">100MB</span>
                <span className="home-hero-stat-label">Maksimum ZIP</span>
              </div>
              <div className="home-hero-stat-divider" />
              <div className="home-hero-stat">
                <span className="home-hero-stat-value">AI</span>
                <span className="home-hero-stat-label">Mimari Özet</span>
              </div>
            </div>
          </div>
          <div className="home-hero-visual">
            <div className="home-hero-diagram-preview">
              <div className="home-diagram-node home-diagram-node-root">
                <span>Proje</span>
              </div>
              <div className="home-diagram-connections">
                <div className="home-diagram-line" />
                <div className="home-diagram-line" />
                <div className="home-diagram-line" />
              </div>
              <div className="home-diagram-nodes">
                <div className="home-diagram-node">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <span>models/</span>
                </div>
                <div className="home-diagram-node">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <span>services/</span>
                </div>
                <div className="home-diagram-node">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <span>api/</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="home-features">
          <div className="home-section-header">
            <h2 className="home-section-title">Özellikler</h2>
            <p className="home-section-subtitle">CodeAtlas, kod analizini kolaylaştırır</p>
          </div>
          <div className="home-features-grid">
            {features.map((feature, index) => (
              <div className="home-feature-card" key={index}>
                <div className="home-feature-icon">{feature.icon}</div>
                <h3 className="home-feature-title">{feature.title}</h3>
                <p className="home-feature-description">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="home-how-it-works">
          <div className="home-section-header">
            <h2 className="home-section-title">Nasıl Çalışır</h2>
            <p className="home-section-subtitle">Üç basit adımda projenizi analiz edin</p>
          </div>
          <div className="home-steps">
            {steps.map((step, index) => (
              <div className="home-step" key={index}>
                <div className="home-step-number">{step.number}</div>
                <div className="home-step-content">
                  <h3 className="home-step-title">{step.title}</h3>
                  <p className="home-step-description">{step.description}</p>
                </div>
                {index < steps.length - 1 && <div className="home-step-arrow" />}
              </div>
            ))}
          </div>
        </section>

        <section className="home-languages">
          <div className="home-languages-content">
            <h2 className="home-languages-title">Desteklenen Diller</h2>
            <p className="home-languages-subtitle">Şu anda aşağıdaki dillerde analiz desteği mevcut</p>
            <div className="home-languages-list">
              {languages.map((lang) => (
                <span className="home-language-tag" key={lang}>{lang}</span>
              ))}
            </div>
          </div>
        </section>

        <section className="home-cta">
          <div className="home-cta-content">
            <h2 className="home-cta-title">Projenizin Mimarisini Keşfedin</h2>
            <p className="home-cta-description">
              Hemen bir ZIP dosyası yükleyin ve kod tabanınızın nasıl göründüğünü görün.
            </p>
            <Link to="/analyze" className="home-cta-btn">
              Analizi Başlat
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </Link>
          </div>
        </section>
      </main>

      <footer className="home-footer">
        <div className="home-footer-content">
          <div className="home-footer-brand">
            <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
              <path d="M16 2L28 9V23L16 30L4 23V9L16 2Z" stroke="url(#footerGrad)" strokeWidth="2" fill="none" />
              <circle cx="16" cy="10" r="3" fill="url(#footerGrad)" />
              <circle cx="10" cy="20" r="3" fill="url(#footerGrad)" />
              <circle cx="22" cy="20" r="3" fill="url(#footerGrad)" />
              <defs>
                <linearGradient id="footerGrad" x1="4" y1="2" x2="28" y2="30">
                  <stop stopColor="#ff5a8a" />
                  <stop offset="1" stopColor="#ff9a9e" />
                </linearGradient>
              </defs>
            </svg>
            <span>CodeAtlas</span>
          </div>
          <p className="home-footer-text">Kod mimarisi görselleştirme aracı</p>
        </div>
      </footer>
    </div>
  )
}

export default HomePage
