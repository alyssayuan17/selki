import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import HeroTitle from "../../components/HeroTitle/HeroTitle";
import './HomePage.css';

function HomePage() {
  const navigate = useNavigate();
  const [leaving, setLeaving] = useState(false);
  const leavingRef = useRef(false);

  const goToUpload = () => {
    if (leavingRef.current) return;
    leavingRef.current = true;
    setLeaving(true);
    setTimeout(() => navigate('/upload'), 600);
  };

  useEffect(() => {
    const handleWheel = (e) => {
      if (e.deltaY > 0) goToUpload();
    };
    let touchStartY = 0;
    const handleTouchStart = (e) => { touchStartY = e.touches[0].clientY; };
    const handleTouchEnd = (e) => {
      if (touchStartY - e.changedTouches[0].clientY > 40) goToUpload();
    };
    window.addEventListener('wheel', handleWheel, { passive: true });
    window.addEventListener('touchstart', handleTouchStart, { passive: true });
    window.addEventListener('touchend', handleTouchEnd, { passive: true });
    return () => {
      window.removeEventListener('wheel', handleWheel);
      window.removeEventListener('touchstart', handleTouchStart);
      window.removeEventListener('touchend', handleTouchEnd);
    };
  }, []);

  return (
    <div className={`home-page ${leaving ? 'home-page--leaving' : ''}`}>
      {/* Aurora orbs */}
      <div className="orb orb--1" />
      <div className="orb orb--2" />
      <div className="orb orb--3" />

      <Navbar />
      <HeroTitle />
      <p className="subtitle-text">AI-powered presentation coaching.</p>
      <button className="home-scroll-cta" onClick={goToUpload} aria-label="Scroll to get started">
        <span className="home-scroll-cta__label">scroll to get started</span>
        <svg className="home-scroll-cta__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="4 8 12 16 20 8" />
        </svg>
      </button>
    </div>
  );
}

export default HomePage;
