import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { AdminStats, User } from '../../lib/types';

export default function AdminPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const meRes = await fetch('/api/auth/me', { credentials: 'same-origin' });
      if (!meRes.ok) {
        navigate('/login');
        return;
      }
      const me: User = await meRes.json();
      if (me.role !== 'admin') {
        setError('Nincs jogosultságod az admin panelhez.');
        setLoading(false);
        return;
      }

      const statsRes = await fetch('/api/admin/stats', { credentials: 'same-origin' });
      if (!statsRes.ok) {
        setError('Hiba történt a statisztikák betöltésekor.');
        setLoading(false);
        return;
      }
      setStats(await statsRes.json());
      setLoading(false);
    }
    load();
  }, [navigate]);

  if (loading)
    return (
      <div className="container page">
        <p>Betöltés...</p>
      </div>
    );
  if (error)
    return (
      <div className="container page">
        <p style={{ color: 'var(--color-accent)' }}>{error}</p>
      </div>
    );
  if (!stats) return null;

  return (
    <section className="page container">
      <h1>Admin Panel</h1>
      <div
        className="admin-nav"
        style={{ marginBottom: 32, display: 'flex', gap: 12, flexWrap: 'wrap' }}
      >
        <Link to="/admin" className="btn btn-primary">
          Áttekintés
        </Link>
        <Link to="/admin/users" className="btn btn-secondary">
          Felhasználók
        </Link>
        <Link to="/admin/courses" className="btn btn-secondary">
          Kurzusok
        </Link>
        <Link to="/admin/promotion" className="btn btn-secondary">
          Előléptetés
        </Link>
      </div>

      <h2 style={{ marginBottom: 20 }}>Áttekintés</h2>
      <div className="card-grid">
        {[
          { label: 'Felhasználó', value: stats.users },
          { label: 'Kurzus', value: stats.courses },
          { label: 'Beiratkozás', value: stats.enrollments },
          { label: 'Tanúsítvány', value: stats.certificates },
          { label: 'Feladat', value: stats.exercises },
        ].map((s) => (
          <div className="card stat-card" key={s.label}>
            <div className="stat-number">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
