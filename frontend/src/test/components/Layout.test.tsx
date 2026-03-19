import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Layout from '../../components/Layout';

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve(null) })),
  );
});

describe('Layout', () => {
  it('renders navigation links', () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    );
    expect(screen.getByText('Kurzusok')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders footer', () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    );
    expect(screen.getByText(/Minden jog fenntartva/)).toBeInTheDocument();
  });

  it('shows login button when not authenticated', async () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    );
    const loginLink = await screen.findByText('Belépés');
    expect(loginLink).toBeInTheDocument();
  });

  it('shows dashboard link when authenticated', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ id: 1, username: 'testuser', role: 'student' }),
        }),
      ),
    );

    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    );
    const dashboardLink = await screen.findByText('Dashboard');
    expect(dashboardLink).toBeInTheDocument();
  });

  it('shows admin link for admin users', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ id: 1, username: 'admin', role: 'admin' }),
        }),
      ),
    );

    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    );
    const adminLink = await screen.findByText('Admin');
    expect(adminLink).toBeInTheDocument();
  });
});
