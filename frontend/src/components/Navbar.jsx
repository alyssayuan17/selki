import { useState, useEffect } from 'react'
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
          <a href="/">Selki</a>
        </div>
        <ul className="navbar-menu">
          <li><a href="/about">About</a></li>
          <li><a href="/guide">Guide</a></li>
        </ul>
      </div>
    </nav>
  )
}

export default Navbar
