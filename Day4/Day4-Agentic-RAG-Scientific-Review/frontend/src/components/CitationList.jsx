export default function CitationList({ citations }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="citation-list">
      <span className="citation-list__label">Sources</span>
      <div className="citation-list__chips">
        {citations.map((c) => (
          <a key={c.id} href={c.url} target="_blank" rel="noreferrer" className="citation-chip">
            {c.id}
          </a>
        ))}
      </div>
    </div>
  );
}
