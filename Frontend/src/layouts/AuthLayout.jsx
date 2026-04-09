import { useEffect, useRef } from 'react'
import architectureBg from '../assets/architecture-bg.png'
import './AuthLayout.css'

function AuthLayout({ children }) {
  const particlesRef = useRef(null)

  useEffect(() => {
    const container = particlesRef.current
    if (!container) return

    const createParticle = () => {
      const particle = document.createElement('div')
      particle.className = 'auth-particle'
      particle.style.left = Math.random() * 100 + '%'
      particle.style.animationDuration = (Math.random() * 8 + 6) + 's'
      particle.style.animationDelay = Math.random() * 4 + 's'
      particle.style.width = (Math.random() * 4 + 2) + 'px'
      particle.style.height = particle.style.width
      container.appendChild(particle)

      setTimeout(() => {
        if (container.contains(particle)) {
          container.removeChild(particle)
        }
      }, 14000)
    }

    const interval = setInterval(createParticle, 800)

    return () => {
      clearInterval(interval)
      while (container.firstChild) {
        container.removeChild(container.firstChild)
      }
    }
  }, [])

  return (
    <div className="auth-layout" id="auth-layout">
      {/* Left Panel - Architecture Visualization */}
      <div className="auth-left-panel">
        <div className="auth-left-bg">
          <img
            src={architectureBg}
            alt="System Architecture Visualization"
            className="auth-bg-image"
          />
          <div className="auth-bg-overlay" />
        </div>

        {/* Floating particles */}
        <div className="auth-particles" ref={particlesRef} />

        {/* Logo */}
        <div className="auth-brand">
          <div className="auth-brand-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M16 2L28 9V23L16 30L4 23V9L16 2Z" stroke="url(#brandGrad)" strokeWidth="2" fill="none" />
              <circle cx="16" cy="10" r="3" fill="url(#brandGrad)" />
              <circle cx="10" cy="20" r="3" fill="url(#brandGrad)" />
              <circle cx="22" cy="20" r="3" fill="url(#brandGrad)" />
              <line x1="16" y1="13" x2="10" y2="17" stroke="url(#brandGrad)" strokeWidth="1.5" />
              <line x1="16" y1="13" x2="22" y2="17" stroke="url(#brandGrad)" strokeWidth="1.5" />
              <line x1="10" y1="20" x2="22" y2="20" stroke="url(#brandGrad)" strokeWidth="1.5" />
              <defs>
                <linearGradient id="brandGrad" x1="4" y1="2" x2="28" y2="30">
                  <stop stopColor="#ff5a8a" />
                  <stop offset="1" stopColor="#ff9a9e" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span className="auth-brand-text">Auto Architecture Visualizer</span>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="auth-right-panel">
        <div className="auth-form-container">
          {children}
        </div>
      </div>
    </div>
  )
}

export default AuthLayout
