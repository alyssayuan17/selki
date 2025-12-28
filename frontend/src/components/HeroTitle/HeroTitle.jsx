import "./HeroTitle.css";

export default function HeroTitle() {
  return (
    <section className="hero">
      <div className="hero-content">
        <div className="hero-text">
          <h1 className="hero__title">Seal</h1>
          <h2 className="hero__subtitle">the Deal!</h2>
        </div>
        <div className="hero-logo-wrapper">
          <img src="/selki_logo_v2.svg" alt="Selki logo" className="hero-logo" />
        </div>
      </div>
    </section>
  );
}
