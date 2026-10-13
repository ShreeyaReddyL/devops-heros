import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = '/api';

const STATUSES = ['ALL', 'OPEN', 'IN_PROGRESS', 'RESOLVED'];

const CATEGORIES = [
  { value: 'WI_FI', label: 'Campus Wi-Fi' },
  { value: 'PROJECTOR', label: 'Projector / AV' },
  { value: 'ELECTRICAL', label: 'Electrical & Lighting' },
  { value: 'PLUMBING', label: 'Plumbing' },
  { value: 'HOSTEL', label: 'Hostel Maintenance' },
  { value: 'LAB_EQUIPMENT', label: 'Lab Equipment' },
  { value: 'IT_SUPPORT', label: 'General IT Support' },
  { value: 'OTHER', label: 'Other' },
];

const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

// Mirrors ALLOWED_TRANSITIONS in backend/app/schemas.py so the UI can only
// offer transitions the API will actually accept.
const NEXT_STATUS = {
  OPEN: { label: 'Start work', next: 'IN_PROGRESS' },
  IN_PROGRESS: { label: 'Mark resolved', next: 'RESOLVED' },
  RESOLVED: { label: 'Reopen', next: 'OPEN' },
};

const categoryLabel = (value) =>
  CATEGORIES.find((c) => c.value === value)?.label ?? value;

const prettyStatus = (value) => value.replace('_', ' ');

function StatCard({ label, value, tone }) {
  return (
    <div className={`stat stat-${tone}`}>
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

function TicketForm({ onSubmit, onCancel, error }) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: 'IT_SUPPORT',
    building: '',
    reporter: '',
    priority: 'MEDIUM',
  });

  const update = (field) => (event) =>
    setForm((prev) => ({ ...prev, [field]: event.target.value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    await onSubmit(form);
  };

  return (
    <form className="ticket-form" onSubmit={handleSubmit}>
      <h2>Report a campus issue</h2>

      {error && <div className="form-error">{error}</div>}

      <label>
        Issue title <em>*</em>
        <input
          required
          minLength={5}
          maxLength={200}
          value={form.title}
          onChange={update('title')}
          placeholder="e.g. Projector not powering on in Lecture Hall 2"
        />
      </label>

      <div className="form-row">
        <label>
          Category
          <select value={form.category} onChange={update('category')}>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Priority
          <select value={form.priority} onChange={update('priority')}>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="form-row">
        <label>
          Building / location <em>*</em>
          <input
            required
            minLength={2}
            maxLength={120}
            value={form.building}
            onChange={update('building')}
            placeholder="e.g. Hostel Block C"
          />
        </label>

        <label>
          Reported by <em>*</em>
          <input
            required
            minLength={2}
            maxLength={120}
            value={form.reporter}
            onChange={update('reporter')}
            placeholder="e.g. Aarav Sharma"
          />
        </label>
      </div>

      <label>
        Description
        <textarea
          rows={3}
          maxLength={4000}
          value={form.description}
          onChange={update('description')}
          placeholder="Add any detail that helps the maintenance team..."
        />
      </label>

      <div className="form-actions">
        <button type="button" className="ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="primary">
          Submit ticket
        </button>
      </div>
    </form>
  );
}

function App() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    open: 0,
    in_progress: 0,
    resolved: 0,
    critical: 0,
    high: 0,
    by_category: [],
  });
  const [filter, setFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [formError, setFormError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      setError('');
      const [ticketsResponse, statsResponse] = await Promise.all([
        fetch(`${API}/tickets`),
        fetch(`${API}/tickets/stats`),
      ]);
      if (!ticketsResponse.ok || !statsResponse.ok) {
        throw new Error(`API responded ${ticketsResponse.status}/${statsResponse.status}`);
      }
      setTickets(await ticketsResponse.json());
      setStats(await statsResponse.json());
    } catch (err) {
      setError(
        `${err.message}. Start the backend with "docker compose up --build", then refresh.`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(
    () => (filter === 'ALL' ? tickets : tickets.filter((t) => t.status === filter)),
    [tickets, filter]
  );

  const advance = async (ticket) => {
    const { next } = NEXT_STATUS[ticket.status];
    setError('');
    try {
      const response = await fetch(`${API}/tickets/${ticket.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: next }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Update failed (${response.status})`);
      }
      setNotice(`Ticket #${ticket.id} moved to ${prettyStatus(next)}.`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const remove = async (ticket) => {
    setError('');
    try {
      const response = await fetch(`${API}/tickets/${ticket.id}`, { method: 'DELETE' });
      if (!response.ok) throw new Error(`Delete failed (${response.status})`);
      setNotice(`Ticket #${ticket.id} deleted.`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const submitTicket = async (form) => {
    setFormError('');
    setSubmitting(true);
    try {
      const response = await fetch(`${API}/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const detail = Array.isArray(body.detail)
          ? body.detail.map((d) => `${d.loc?.join('.')}: ${d.msg}`).join('; ')
          : body.detail;
        throw new Error(detail || `Create failed (${response.status})`);
      }
      setNotice(`Ticket #${(await response.json()).id} submitted.`);
      setShowForm(false);
      await load();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">C</span>
          <div>
            <b>CampusFix</b>
            <small>Maintenance &amp; IT Support</small>
          </div>
        </div>

        <nav>
          <span className="nav-item active">▦ Dashboard</span>
          <span className="nav-item">⚠ Open issues</span>
          <span className="nav-item">◷ In progress</span>
          <span className="nav-item">✓ Resolved</span>
        </nav>

        <div className="side-bottom">
          <div className="upgrade">
            <strong>Facilities workflow</strong>
            <p>
              Report Wi-Fi, projector, electrical, plumbing, hostel and lab issues
              from one desk.
            </p>
          </div>
          <div className="profile">
            <div className="avatar">SR</div>
            <div>
              <b>Shreeya Reddy</b>
              <small>DevOps Engineer</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        <header>
          <div>
            <p className="eyebrow">CAMPUS / MAINTENANCE DESK</p>
            <h1>CampusFix</h1>
            <p className="muted">
              Track every reported issue across campus facilities and IT support.
            </p>
          </div>
          <button className="primary" onClick={() => setShowForm((v) => !v)}>
            ＋ Report issue
          </button>
        </header>

        {error && <div className="alert">⚠ {error}</div>}
        {notice && !error && (
          <div className="alert success" onClick={() => setNotice('')}>
            ✓ {notice}
          </div>
        )}

        <section className="stats">
          <StatCard label="Total tickets" value={stats.total} tone="total" />
          <StatCard label="Open" value={stats.open} tone="open" />
          <StatCard label="In progress" value={stats.in_progress} tone="progress" />
          <StatCard label="Resolved" value={stats.resolved} tone="resolved" />
          <StatCard label="Critical" value={stats.critical} tone="critical" />
        </section>

        {showForm && (
          <TicketForm
            onSubmit={submitTicket}
            onCancel={() => {
              setShowForm(false);
              setFormError('');
            }}
            error={formError}
          />
        )}

        <section className="content-grid">
          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>Support tickets</h2>
                <p className="muted">
                  {loading ? 'Loading tickets…' : `${visible.length} shown`}
                </p>
              </div>
              <div className="filters">
                {STATUSES.map((s) => (
                  <button
                    key={s}
                    className={filter === s ? 'selected' : ''}
                    onClick={() => setFilter(s)}
                  >
                    {s === 'ALL' ? 'All' : prettyStatus(s)}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="empty">Loading tickets from the CampusFix API…</div>
            ) : visible.length === 0 ? (
              <div className="empty">
                {tickets.length === 0
                  ? 'No tickets reported yet. Use “Report issue” to log the first one.'
                  : `No ${prettyStatus(filter).toLowerCase()} tickets right now.`}
              </div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Issue</th>
                      <th>Category</th>
                      <th>Location</th>
                      <th>Reported by</th>
                      <th>Priority</th>
                      <th>Status</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((t) => (
                      <tr key={t.id}>
                        <td>
                          <div className="ticket-title">
                            <span className={`dot ${t.status.toLowerCase()}`} />
                            <div>
                              <b>#{t.id} {t.title}</b>
                              <small>{t.description || 'No description provided.'}</small>
                            </div>
                          </div>
                        </td>
                        <td>{categoryLabel(t.category)}</td>
                        <td>{t.building}</td>
                        <td>{t.reporter}</td>
                        <td>
                          <span className={`badge priority-${t.priority.toLowerCase()}`}>
                            {t.priority}
                          </span>
                        </td>
                        <td>
                          <span className={`badge status-${t.status.toLowerCase()}`}>
                            {prettyStatus(t.status)}
                          </span>
                        </td>
                        <td className="row-actions">
                          <button
                            className="link"
                            disabled={submitting}
                            onClick={() => advance(t)}
                          >
                            {NEXT_STATUS[t.status].label}
                          </button>
                          <button className="link danger" onClick={() => remove(t)}>
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>Issues by category</h2>
                <p className="muted">Live counts from PostgreSQL.</p>
              </div>
            </div>
            {stats.by_category.length === 0 ? (
              <div className="empty">No category data yet.</div>
            ) : (
              <ul className="category-list">
                {stats.by_category.map((c) => {
                  const pct = stats.total ? Math.round((c.count / stats.total) * 100) : 0;
                  return (
                    <li key={c.category}>
                      <div className="category-row">
                        <span>{categoryLabel(c.category)}</span>
                        <b>{c.count}</b>
                      </div>
                      <div className="bar">
                        <span style={{ width: `${pct}%` }} />
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);