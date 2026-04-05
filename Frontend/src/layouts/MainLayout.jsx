function MainLayout({ children }) {
  return (
    <div className="app-shell">
      <div className="app-frame">
        <header className="app-header">
          <div className="brand">
            <div className="brand-mark">CA</div>
            <div className="brand-text">
              <strong>CodeAtlas Frontend</strong>
              <span>React + Vite baslangic yapisi</span>
            </div>
          </div>

          <nav aria-label="Primary">
            <a href="#features">Features</a>
            <a href="#structure">Structure</a>
            <a href="https://react.dev" target="_blank" rel="noreferrer">
              React Docs
            </a>
          </nav>
        </header>

        <main className="app-main">{children}</main>

        <footer className="app-footer">
          <p>Bilesen bazli dosya ayrimi ile hazirlandi.</p>
          <p>Gelismeye uygun temiz bir baslangic iskeleti.</p>
        </footer>
      </div>
    </div>
  )
}

export default MainLayout
