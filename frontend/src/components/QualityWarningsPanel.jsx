export default function QualityWarnings({ warnings = [] }) {
    const hasWarnings = warnings.length > 0;

    return (
        <section className="qw">
            <h2 className="qw__title">Quality Warnings</h2>

            <div className="qw__card">
                {hasWarnings ? (
                <ul className="qw__list">
                    {warnings.map((w, i) => (
                    <li key={i} className="qw__item">{w}</li>
                    ))}
                </ul>
                ) : (
                <p className="qw__empty">No warnings detected.</p>
                )}
            </div>
        </section>
    );
}