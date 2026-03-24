import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { Course } from '../lib/types';

export default function CourseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [course, setCourse] = useState<Course | null>(null);
  const [enrolled, setEnrolled] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [enrollMsg, setEnrollMsg] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/courses/${id}`, { credentials: 'same-origin' });
        if (!res.ok) {
          setCourse(null);
          setLoading(false);
          return;
        }
        const data: Course = await res.json();
        setCourse(data);

        const meRes = await fetch('/api/auth/me', { credentials: 'same-origin' });
        const loggedIn = meRes.ok;
        setIsLoggedIn(loggedIn);

        if (loggedIn) {
          const coursesRes = await fetch('/api/me/courses', { credentials: 'same-origin' });
          if (coursesRes.ok) {
            const courses = await coursesRes.json();
            setEnrolled(courses.some((c: { course_id: number }) => String(c.course_id) === id));
          }
        }
      } catch {
        setCourse(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const handleEnroll = async () => {
    if (!isLoggedIn) {
      navigate('/login');
      return;
    }
    const r = await fetch(`/api/courses/${id}/enroll`, {
      method: 'POST',
      credentials: 'same-origin',
    });
    if (r.status === 201) {
      setEnrollMsg('Sikeresen beiratkoztál!');
      setEnrolled(true);
    } else if (r.status === 409) {
      setEnrollMsg('Már beiratkoztál erre a kurzusra.');
    } else {
      setEnrollMsg('Hiba történt.');
    }
  };

  if (loading)
    return (
      <div className="container page">
        <p>Betöltés...</p>
      </div>
    );
  if (!course)
    return (
      <div className="container page">
        <p>Kurzus nem található.</p>
      </div>
    );

  return (
    <div className="container page">
      <h1>{course.name}</h1>
      <p className="course-desc">{course.description || ''}</p>

      {!enrolled && (
        <>
          <button className="btn btn-primary" style={{ margin: '20px 0' }} onClick={handleEnroll}>
            Beiratkozás
          </button>
          {enrollMsg && (
            <div style={{ color: enrollMsg.includes('Sikeresen') ? 'green' : 'red' }}>
              <p>{enrollMsg}</p>
            </div>
          )}
        </>
      )}

      {enrolled &&
        course.modules &&
        course.modules.some((m) => m.exercises.some((e) => e.classroom_url)) && (
          <div
            className="card"
            style={{
              background: '#f0f7ff',
              border: '1px solid #b3d4fc',
              padding: '16px 20px',
              margin: '20px 0',
            }}
          >
            <strong>ℹ️ GitHub Classroom – mielőtt elkezded</strong>
            <ol style={{ margin: '8px 0 0', paddingLeft: '20px', lineHeight: '1.7' }}>
              <li>
                <strong>Fogadd el a GitHub szervezeti meghívót!</strong> Bejelentkezéskor
                automatikusan kapsz meghívót. Ellenőrizd:{' '}
                <a
                  href="https://github.com/settings/organizations"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  github.com/settings/organizations
                </a>{' '}
                – ha a meghívó „pending" állapotban van, fogadd el.
              </li>
              <li>
                Győződj meg róla, hogy a böngésződben <strong>ugyanazzal a GitHub fiókkal</strong>{' '}
                vagy bejelentkezve, amivel a platformra regisztráltál.
              </li>
              <li>
                Ezután kattints a 📎 ikonra a feladatoknál, és fogadd el az assignment-et a GitHub
                Classroom-ban.
              </li>
            </ol>
            <p style={{ margin: '8px 0 0', fontSize: '0.9em', color: '#555' }}>
              Ha „Repository Access Issue" hibát kapsz, az általában azt jelenti, hogy a szervezeti
              meghívó nincs elfogadva.
            </p>
          </div>
        )}

      {course.modules && course.modules.length > 0 && (
        <>
          <h2>Modulok</h2>
          {course.modules
            .sort((a, b) => a.order - b.order)
            .map((m) => (
              <div className="card module-card" key={m.id}>
                <h3>{m.name}</h3>
                <ul>
                  {m.exercises
                    .sort((a, b) => a.order - b.order)
                    .map((e) => (
                      <li key={e.id}>
                        {e.name}
                        {e.classroom_url && (
                          <a
                            href={e.classroom_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="classroom-link"
                            title="Megnyitás GitHub Classroom-ban"
                          >
                            📎
                          </a>
                        )}
                      </li>
                    ))}
                </ul>
              </div>
            ))}
        </>
      )}
    </div>
  );
}
