import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import HeroTitle from "../../components/HeroTitle/HeroTitle";
import Button from "../../components/Button/Button";
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
    window.addEventListener('wheel', handleWheel, { passive: true });
    return () => window.removeEventListener('wheel', handleWheel);
  }, []);

  return (
    <div className={`home-page ${leaving ? 'home-page--leaving' : ''}`}>
      <Navbar />
      <HeroTitle />
      <p className="subtitle-text">AI-powered presentation coaching</p>
      <Button variant="primary" onClick={goToUpload}>Get Started</Button>
      <button className="home-arrow" onClick={goToUpload} aria-label="Scroll to upload">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
    </div>
  );
}

export default HomePage;
