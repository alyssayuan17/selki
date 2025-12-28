import Navbar from "../../components/Navbar/Navbar";
import HeroTitle from "../../components/HeroTitle/HeroTitle";
import Button from "../../components/Button/Button";
import { useNavigate } from "react-router-dom";
import './HomePage.css';

function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="home-page">
        <Navbar />
        <HeroTitle />
        <p className="subtitle-text">AI-powered presentation coaching</p>
        <Button variant="primary" onClick={() => navigate('/upload')}>Get Started</Button>
        
    </div>
  )
}


export default HomePage
