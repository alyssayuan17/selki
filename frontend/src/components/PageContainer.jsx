export default function PageContainer({children}) {
  return (
    <div style={{ width: "100%", display: "flex", justifyContent: "center" }}>
      <div style={{ width: "100%", maxWidth: 1200, padding: "24px" }}>
        {children}
      </div>
    </div>
  );
}