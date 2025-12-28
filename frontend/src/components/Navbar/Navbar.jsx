import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      const offset = window.scrollY
      if (offset > 50) {
        setScrolled(true)
      } else {
        setScrolled(false)
      }
    }

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
          <li><Link to="/about">About</Link></li>
          <li><Link to="/guide">Guide</Link></li>
        </ul>
      </div>
    </nav>
  )
}

export default Navbar
