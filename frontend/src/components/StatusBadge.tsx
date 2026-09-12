export const StatusBadge = ({ status }: { status: string }) => {
  let background = '#e0e0e0';
  if (status === 'Backend Online' || status === 'ACTIVE' || status === 'COMPLETED') background = '#c8e6c9';
  if (status === 'Backend Offline' || status === 'FAILED') background = '#ffcdd2';

  return (
    <span style={{ padding: '4px 8px', borderRadius: '4px', background, fontWeight: 'bold' }}>
      {status}
    </span>
  );
};
