import { useState, useRef, useEffect } from "react";
import "./CustomSelect.css";

export default function CustomSelect({ id, value, onChange, options, required }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const selected = options.find((o) => o.value === value);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div className={`custom-select ${open ? "custom-select--open" : ""}`} ref={ref} id={id}>
      <button type="button" className="custom-select__trigger" onClick={() => setOpen((o) => !o)}>
        <span className={selected && selected.value ? "" : "custom-select__placeholder"}>
          {selected ? selected.label : ""}
        </span>
        <svg className="custom-select__arrow" viewBox="0 0 12 8" fill="none">
          <path d="M1 1l5 5 5-5" stroke="#266EBA" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
      {open && (
        <ul className="custom-select__menu">
          {options.map((o) => (
            <li
              key={o.value}
              className={`custom-select__option ${o.value === value ? "custom-select__option--selected" : ""} ${!o.value ? "custom-select__option--placeholder" : ""}`}
              onClick={() => { onChange({ target: { value: o.value } }); setOpen(false); }}
            >
              {o.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
