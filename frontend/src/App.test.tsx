import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Dashboard } from './pages/Dashboard';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import * as api from './api/workflows';

vi.mock('./api/workflows');

describe('Dashboard Component', () => {
    beforeEach(() => {
        vi.resetAllMocks();
    });

    it('renders dashboard correctly', async () => {
        (api.workflowsApi.getHealth as any).mockResolvedValue({});
        render(<Dashboard />);
        expect(screen.getByText('GovInnovate Dashboard')).toBeDefined();
        await waitFor(() => expect(screen.getByText('Backend Online')).toBeDefined());
    });
});
