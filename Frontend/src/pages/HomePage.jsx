import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { useLang } from '../context/LanguageContext'
import './HomePage.css'

function HomePage() {
  const { t } = useLang()
  const particlesRef = useRef(null)

  const features = [
    {
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
      ),
      title: t('feature1_title'),
      description: t('feature1_desc'),
    },
    {
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
        </svg>
      ),
      title: t('feature2_title'),
      description: t('feature2_desc'),
    },
    {
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
          <line x1="12" y1="22.08" x2="12" y2="12"/>
        </svg>
      ),
      title: t('feature3_title'),
      description: t('feature3_desc'),
    },
    {
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <line x1="3" y1="9" x2="21" y2="9"/>
          <line x1="9" y1="21" x2="9" y2="9"/>
        </svg>
      ),
      title: t('feature4_title'),
      description: t('feature4_desc'),
    },
  ]

  const steps = [
    { number: '01', title: t('step1_title'), description: t('step1_desc') },
    { number: '02', title: t('step2_title'), description: t('step2_desc') },
    { number: '03', title: t('step3_title'), description: t('step3_desc') },
  ]

  const languages = ['Python', 'JavaScript', 'TypeScript', 'JSX', 'TSX']

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
              {t('hero_badge')}
            </div>
            <h1 className="home-hero-title">
              {t('hero_title_1')}
              <br />
              <span className="home-hero-title-gradient">{t('hero_title_2')}</span>
            </h1>
            <p className="home-hero-description">{t('hero_desc')}</p>
            <div className="home-hero-actions">
              <Link to="/analyze" className="home-hero-btn home-hero-btn-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                {t('hero_btn_start')}
              </Link>
              <a href="#features" className="home-hero-btn home-hero-btn-secondary">
                {t('hero_btn_more')}
              </a>
            </div>
            <div className="home-hero-stats">
              <div className="home-hero-stat">
                <span className="home-hero-stat-value">3+</span>
                <span className="home-hero-stat-label">{t('stat_lang')}</span>
              </div>
              <div className="home-hero-stat-divider" />
              <div className="home-hero-stat">
                <span className="home-hero-stat-value">100MB</span>
                <span className="home-hero-stat-label">{t('stat_zip')}</span>
              </div>
              <div className="home-hero-stat-divider" />
              <div className="home-hero-stat">
                <span className="home-hero-stat-value">AI</span>
                <span className="home-hero-stat-label">{t('stat_ai')}</span>
              </div>
            </div>
          </div>
          <div className="home-hero-visual">
            <div className="home-hero-diagram-preview">
              <div className="home-diagram-node home-diagram-node-root">
                <span>{t('visual_project')}</span>
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
            <h2 className="home-section-title">{t('features_title')}</h2>
            <p className="home-section-subtitle">{t('features_subtitle')}</p>
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
            <h2 className="home-section-title">{t('how_title')}</h2>
            <p className="home-section-subtitle">{t('how_subtitle')}</p>
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
            <h2 className="home-languages-title">{t('langs_title')}</h2>
            <p className="home-languages-subtitle">{t('langs_subtitle')}</p>
            <div className="home-languages-list">
              {languages.map((lang) => (
                <span className="home-language-tag" key={lang}>{lang}</span>
              ))}
            </div>
          </div>
        </section>

        <section className="home-cta">
          <div className="home-cta-content">
            <h2 className="home-cta-title">{t('cta_title')}</h2>
            <p className="home-cta-description">{t('cta_desc')}</p>
            <Link to="/analyze" className="home-cta-btn">
              {t('cta_btn')}
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
          <p className="home-footer-text">{t('footer_text')}</p>
        </div>
      </footer>
    </div>
  )
}

export default HomePage
