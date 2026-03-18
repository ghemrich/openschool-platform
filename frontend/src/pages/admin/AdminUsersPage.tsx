import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { User } from '../../lib/types';

export default function AdminUsersPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusMsg, setStatusMsg] = useState('');
  const [pendingRoles, setPendingRoles] = useState<Record<number, string>>({});

  useEffect(() => {
    async function load() {
      const meRes = await fetch('/api/auth/me', { credentials: 'same-origin' });
      if (!meRes.ok) {
        navigate('/login');
        return;
      }
      const me: User = await meRes.json();
      if (me.role !== 'admin') {
        setError('Nincs jogosultságod.');
        setLoading(false);
        return;
      }

      const res = await fetch('/api/admin/users', { credentials: 'same-origin' });
      if (!res.ok) {
        setError('Hiba történt.');
        setLoading(false);
        return;
      }
      const body = await res.json();
      setUsers(body.data);
      setLoading(false);
    }
    load();
  }, [navigate]);

  const handleRoleChange = (userId: number, newRole: string) => {
    setPendingRoles((prev) => ({ ...prev, [userId]: newRole }));
  };

  const handleSaveRole = async (userId: number) => {
    const newRole = pendingRoles[userId];
    if (!newRole) return;

    const r = await fetch(`/api/admin/users/${userId}/role`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ role: newRole }),
    });

    if (r.ok) {
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: newRole as User['role'] } : u)),
      );
      setPendingRoles((prev) => {
        const next = { ...prev };
        delete next[userId];
        return next;
      });
      setStatusMsg('Szerepkör frissítve.');
    } else {
      const d = await r.json();
      setStatusMsg(d.detail || 'Hiba történt.');
    }
  };

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

  return (
    <section className="page container">
      <h1>Felhasználók kezelése</h1>
      <div
        className="admin-nav"
        style={{ marginBottom: 32, display: 'flex', gap: 12, flexWrap: 'wrap' }}
      >
        <Link to="/admin" className="btn btn-secondary">
          Áttekintés
        </Link>
        <Link to="/admin/users" className="btn btn-primary">
          Felhasználók
        </Link>
        <Link to="/admin/courses" className="btn btn-secondary">
          Kurzusok
        </Link>
        <Link to="/admin/promotion" className="btn btn-secondary">
          Előléptetés
        </Link>
      </div>

      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Avatar</th>
              <th>Felhasználónév</th>
              <th>Email</th>
              <th>Szerepkör</th>
              <th>Regisztráció</th>
              <th>Utolsó belépés</th>
              <th>Művelet</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const currentRole = pendingRoles[u.id] ?? u.role;
              const hasChange = pendingRoles[u.id] !== undefined && pendingRoles[u.id] !== u.role;
              return (
                <tr key={u.id}>
                  <td>{u.avatar_url && <img src={u.avatar_url} alt="" className="avatar" />}</td>
                  <td>
                    <strong>{u.username}</strong>
                  </td>
                  <td>{u.email || '–'}</td>
                  <td>
                    <select
                      className="role-select"
                      value={currentRole}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                    >
                      <option value="student">Student</option>
                      <option value="mentor">Mentor</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td>{u.created_at ? new Date(u.created_at).toLocaleDateString('hu-HU') : '–'}</td>
                  <td>{u.last_login ? new Date(u.last_login).toLocaleDateString('hu-HU') : '–'}</td>
                  <td>
                    {hasChange && (
                      <button
                        className="btn btn-primary"
                        style={{ padding: '6px 14px', fontSize: '0.85rem' }}
                        onClick={() => handleSaveRole(u.id)}
                      >
                        Mentés
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {statusMsg && (
        <p
          style={{
            marginTop: 12,
            color: statusMsg.includes('frissítve') ? 'var(--color-success)' : 'var(--color-accent)',
          }}
        >
          {statusMsg}
        </p>
      )}
    </section>
  );
}
