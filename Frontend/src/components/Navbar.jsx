import { Link } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  return (
    <header className="navbar">
      <nav className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <path d="M16 2L28 9V23L16 30L4 23V9L16 2Z" stroke="url(#navGrad)" strokeWidth="2" fill="none" />
            <circle cx="16" cy="10" r="3" fill="url(#navGrad)" />
            <circle cx="10" cy="20" r="3" fill="url(#navGrad)" />
            <circle cx="22" cy="20" r="3" fill="url(#navGrad)" />
            <line x1="16" y1="13" x2="10" y2="17" stroke="url(#navGrad)" strokeWidth="1.5" />
            <line x1="16" y1="13" x2="22" y2="17" stroke="url(#navGrad)" strokeWidth="1.5" />
            <line x1="10" y1="20" x2="22" y2="20" stroke="url(#navGrad)" strokeWidth="1.5" />
            <defs>
              <linearGradient id="navGrad" x1="4" y1="2" x2="28" y2="30">
                <stop stopColor="#ff5a8a" />
                <stop offset="1" stopColor="#ff9a9e" />
              </linearGradient>
            </defs>
          </svg>
          <span className="navbar-brand-text">CodeAtlas</span>
        </Link>

        <div className="navbar-links">
          <Link to="/" className="navbar-link">Ana Sayfa</Link>
          <Link to="/analyze" className="navbar-link navbar-link-cta">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Analizi Başlat
          </Link>
          <Link to="/login" className="navbar-link">Giriş Yap</Link>
        </div>
      </nav>
    </header>
  )
}

export default Navbar