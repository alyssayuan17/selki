import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import './Navbar.css'

function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const { isLoggedIn, user, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-container">
        <div className="navbar-logo">
          <Link to="/">
            Selki
            <img src="/selki_logo_v2.svg" alt="Selki logo" className="logo-icon" />
          </Link>
        </div>
        <ul className="navbar-menu">
          <li><Link to="/history">History</Link></li>
          <li><Link to="/about">About</Link></li>
          <li><Link to="/guide">Guide</Link></li>
          {isLoggedIn ? (
            <li>
              <button className="navbar-user-btn" onClick={logout} title={`Signed in as ${user?.username}`}>
                @{user?.username}
              </button>
            </li>
          ) : (
            <li>
              <button className="navbar-signin-btn" onClick={() => navigate('/auth')}>
                Sign In
              </button>
            </li>
          )}
        </ul>
      </div>
    </nav>
  )
}

export default Navbar
