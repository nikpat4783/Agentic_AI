import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchDomains } from "../api/domains";
import DomainCard from "../components/DomainCard";
import { useAuth } from "../context/AuthContext";
import { useSession } from "../context/SessionContext";

export default function DomainSelectPage() {
  const [domains, setDomains] = useState([]);
  const [error, setError] = useState("");
  const { selectDomain } = useSession();
  const { username, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchDomains()
      .then(setDomains)
      .catch(() => setError("Could not load domains."));
  }, []);

  function handleSelect(domain) {
    selectDomain(domain);
    navigate(`/research/${domain.id}`);
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>Agentic RAG — Literature Review</h1>
        <div className="page-header__user">
          <span>{username}</span>
          <button type="button" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      <p className="page-subtitle">Choose a domain to start your research session.</p>
      {error && <p className="form-error">{error}</p>}

      <div className="domain-grid">
        {domains.map((d) => (
          <DomainCard key={d.id} domain={d} onSelect={handleSelect} />
        ))}
      </div>
    </div>
  );
}
