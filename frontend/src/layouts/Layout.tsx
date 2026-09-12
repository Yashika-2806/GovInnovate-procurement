export const Layout = ({ children }: { children: React.ReactNode }) => (
  <div style={{ display: 'flex', minHeight: '100vh' }}>
    <nav style={{ width: '200px', background: '#f0f0f0', padding: '20px' }}>
      <h2>GovInnovate</h2>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        <li>Dashboard</li>
      </ul>
    </nav>
    <main style={{ flex: 1, padding: '20px' }}>{children}</main>
  </div>
);
