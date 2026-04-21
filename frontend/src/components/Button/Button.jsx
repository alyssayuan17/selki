import { useRef } from 'react';
import './Button.css';

function Button({
  children,
  variant = "primary",
  onClick,
  type = "button",
  disabled = false
}) {
  const ref = useRef(null);

  const handleClick = (e) => {
    const btn = ref.current;
    btn.classList.remove('btn--clicked');
    void btn.offsetWidth; // force reflow to restart animation
    btn.classList.add('btn--clicked');
    onClick?.(e);
  };

  return (
    <button
      ref={ref}
      type={type}
      onClick={handleClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {children}
    </button>
  );
}

export default Button;
