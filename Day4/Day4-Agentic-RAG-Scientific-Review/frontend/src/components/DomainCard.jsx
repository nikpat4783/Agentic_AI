export default function DomainCard({ domain, onSelect }) {
  return (
    <button type="button" className="domain-card" onClick={() => onSelect(domain)}>
      <h3>{domain.name}</h3>
      <p>{domain.description}</p>
      <ul className="domain-card__examples">
        {domain.example_questions.slice(0, 2).map((q) => (
          <li key={q}>{q}</li>
        ))}
      </ul>
    </button>
  );
}
