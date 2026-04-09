import { useState } from 'react'
import { Link } from 'react-router-dom'
import AuthLayout from '../layouts/AuthLayout'

function RegisterPage() {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (formData.password !== formData.confirmPassword) {
      alert('Passwords do not match!')
      return
    }

    setIsLoading(true)
    // API entegrasyonu buraya eklenecek
    console.log('Register:', formData)
    setTimeout(() => setIsLoading(false), 1500)
  }

  const handleGitHubRegister = () => {
    // GitHub OAuth entegrasyonu buraya eklenecek
    console.log('GitHub register')
  }

  return (
    <AuthLayout>
      <h1 className="auth-title" id="register-title">Create Account</h1>
      <p className="auth-subtitle">Visualize your system architecture instantly</p>

      <form className="auth-form" id="register-form" onSubmit={handleSubmit}>
        {/* Full Name Field */}
        <div className="auth-input-group">
          <input
            type="text"
            id="register-fullname"
            name="fullName"
            className="auth-input"
            placeholder="Full Name"
            value={formData.fullName}
            onChange={handleChange}
            required
            autoComplete="name"
          />
          <span className="auth-input-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="8" r="5"/>
              <path d="M20 21a8 8 0 1 0-16 0"/>
            </svg>
          </span>
        </div>

        {/* Email Field */}
        <div className="auth-input-group">
          <input
            type="email"
            id="register-email"
            name="email"
            className="auth-input"
            placeholder="Email Address"
            value={formData.email}
            onChange={handleChange}
            required
            autoComplete="email"
          />
          <span className="auth-input-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect width="20" height="16" x="2" y="4" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
          </span>
        </div>

        {/* Password Row */}
        <div className="auth-input-row">
          <div className="auth-input-group">
            <input
              type="password"
              id="register-password"
              name="password"
              className="auth-input"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
              autoComplete="new-password"
            />
            <span className="auth-input-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </span>
          </div>

          <div className="auth-input-group">
            <input
              type="password"
              id="register-confirm-password"
              name="confirmPassword"
              className="auth-input"
              placeholder="Confirm Pass..."
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              autoComplete="new-password"
            />
            <span className="auth-input-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </span>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          id="register-submit-btn"
          className="auth-submit-btn"
          disabled={isLoading}
        >
          {isLoading ? 'Creating Account...' : 'Sign Up'}
        </button>
      </form>

      {/* Divider */}
      <div className="auth-divider">
        <span className="auth-divider-line" />
        <span className="auth-divider-text">or</span>
        <span className="auth-divider-line" />
      </div>

      {/* GitHub Button */}
      <button
        type="button"
        id="github-register-btn"
        className="auth-github-btn"
        onClick={handleGitHubRegister}
      >
        <span className="auth-github-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
        </span>
        Continue with GitHub
      </button>

      {/* Footer Link */}
      <p className="auth-footer-text">
        Already have an account?{' '}
        <Link to="/login" className="auth-footer-link" id="goto-login-link">
          Login
        </Link>
      </p>
    </AuthLayout>
  )
}

export default RegisterPage
