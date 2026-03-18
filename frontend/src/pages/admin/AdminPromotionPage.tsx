import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { CourseListItem, PromotionRule, User } from '../../lib/types';

export default function AdminPromotionPage() {
  const navigate = useNavigate();
  const [rules, setRules] = useState<PromotionRule[]>([]);
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createMsg, setCreateMsg] = useState('');

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targetRole, setTargetRole] = useState('mentor');
  const [selectedCourseIds, setSelectedCourseIds] = useState<number[]>([]);

  const loadData = useCallback(async () => {
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

    const [rulesRes, coursesRes] = await Promise.all([
      fetch('/api/admin/promotion-rules', { credentials: 'same-origin' }),
      fetch('/api/courses'),
    ]);

    if (rulesRes.ok) {
      setRules(await rulesRes.json());
    }
    if (coursesRes.ok) {
      const body = await coursesRes.json();
      setCourses(body.data);
    }
    setLoading(false);
  }, [navigate]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData();
  }, [loadData]);

  const toggleCourse = (id: number) => {
    setSelectedCourseIds((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id],
    );
  };

  const selectAllCourses = () => {
    setSelectedCourseIds(courses.map((c) => c.id));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || selectedCourseIds.length === 0) {
      setCreateMsg('Adj meg nevet és válassz legalább egy kurzust.');
      return;
    }
    const r = await fetch('/api/admin/promotion-rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        name: name.trim(),
        description: description.trim() || null,
        target_role: targetRole,
        course_ids: selectedCourseIds,
      }),
    });
    if (r.ok) {
      setCreateMsg('Szabály létrehozva!');
      setName('');
      setDescription('');
      setSelectedCourseIds([]);
      await loadData();
    } else {
      const d = await r.json();
      setCreateMsg(d.detail || 'Hiba történt.');
    }
  };

  const handleToggleActive = async (rule: PromotionRule) => {
    const r = await fetch(`/api/admin/promotion-rules/${rule.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ is_active: !rule.is_active }),
    });
    if (r.ok) {
      await loadData();
    }
  };

  const handleDelete = async (ruleId: number) => {
    if (!confirm('Biztosan törölni szeretnéd ezt a szabályt?')) return;
    const r = await fetch(`/api/admin/promotion-rules/${ruleId}`, {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (r.ok) {
      setRules(rules.filter((r) => r.id !== ruleId));
    } else {
      const d = await r.json();
      alert(d.detail || 'Hiba történt.');
    }
  };

  const courseName = (id: number) => courses.find((c) => c.id === id)?.name || `#${id}`;

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
      <h1>Előléptetési szabályok</h1>
      <div
        className="admin-nav"
        style={{ marginBottom: 32, display: 'flex', gap: 12, flexWrap: 'wrap' }}
      >
        <Link to="/admin" className="btn btn-secondary">
          Áttekintés
        </Link>
        <Link to="/admin/users" className="btn btn-secondary">
          Felhasználók
        </Link>
        <Link to="/admin/courses" className="btn btn-secondary">
          Kurzusok
        </Link>
        <Link to="/admin/promotion" className="btn btn-primary">
          Előléptetés
        </Link>
      </div>

      <h2 style={{ marginBottom: 16 }}>Aktív szabályok</h2>
      {rules.length === 0 ? (
        <p style={{ color: '#888' }}>Nincs még előléptetési szabály.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 32 }}>
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="card"
              style={{ padding: 16, opacity: rule.is_active ? 1 : 0.6 }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <strong>{rule.name}</strong>
                  <span
                    style={{
                      marginLeft: 8,
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: '0.8rem',
                      background: rule.is_active ? '#2ecc71' : '#888',
                      color: '#fff',
                    }}
                  >
                    {rule.is_active ? 'Aktív' : 'Inaktív'}
                  </span>
                  <span
                    style={{
                      marginLeft: 8,
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: '0.8rem',
                      background: '#3498db',
                      color: '#fff',
                    }}
                  >
                    → {rule.target_role}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: '0.8rem' }}
                    onClick={() => handleToggleActive(rule)}
                  >
                    {rule.is_active ? 'Kikapcsolás' : 'Bekapcsolás'}
                  </button>
                  <button
                    className="btn"
                    style={{ fontSize: '0.8rem', color: '#e74c3c' }}
                    onClick={() => handleDelete(rule.id)}
                  >
                    Törlés
                  </button>
                </div>
              </div>
              {rule.description && (
                <p style={{ margin: '8px 0 0', fontSize: '0.9rem', color: '#666' }}>
                  {rule.description}
                </p>
              )}
              <p style={{ margin: '8px 0 0', fontSize: '0.85rem' }}>
                <strong>Szükséges kurzusok:</strong>{' '}
                {rule.course_ids.map((id) => courseName(id)).join(', ')}
              </p>
            </div>
          ))}
        </div>
      )}

      <h2 style={{ marginBottom: 16 }}>Új szabály létrehozása</h2>
      <form onSubmit={handleCreate} className="card" style={{ padding: 16 }}>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Név</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="pl. Összes kurzus → Mentor"
            style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #ccc', width: 400 }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Leírás</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="pl. Automatikus mentorrá léptetés minden kurzus elvégzése után"
            style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #ccc', width: 400 }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>
            Cél szerepkör
          </label>
          <select
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #ccc' }}
          >
            <option value="mentor">Mentor</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>
            Szükséges kurzusok
          </label>
          <button
            type="button"
            onClick={selectAllCourses}
            style={{
              marginBottom: 8,
              fontSize: '0.85rem',
              cursor: 'pointer',
              background: 'none',
              border: 'none',
              color: '#3498db',
              textDecoration: 'underline',
            }}
          >
            Összes kijelölése
          </button>
          {courses.map((c) => (
            <label
              key={c.id}
              style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}
            >
              <input
                type="checkbox"
                checked={selectedCourseIds.includes(c.id)}
                onChange={() => toggleCourse(c.id)}
              />
              {c.name}
            </label>
          ))}
        </div>
        {createMsg && (
          <p
            style={{
              color: createMsg.includes('létrehozva') ? 'green' : 'red',
              marginBottom: 8,
            }}
          >
            {createMsg}
          </p>
        )}
        <button type="submit" className="btn btn-primary">
          Szabály létrehozása
        </button>
      </form>
    </section>
  );
}
