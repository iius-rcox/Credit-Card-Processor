/**
 * Tests for AliasManager component
 *
 * Verifies alias creation, deletion, and error handling functionality.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AliasManager } from '@/components/AliasManager';
import * as aliasService from '@/services/aliasService';

// Mock the alias service
jest.mock('@/services/aliasService');

const mockEmployees = [
  { id: '123e4567-e89b-12d3-a456-426614174000', name: 'John Doe', email: 'john@example.com' },
  { id: '123e4567-e89b-12d3-a456-426614174001', name: 'Jane Smith', email: 'jane@example.com' },
];

const mockAliases: aliasService.EmployeeAlias[] = [
  {
    id: 'alias-1',
    extractedName: 'JOHNSMITH',
    employeeId: '123e4567-e89b-12d3-a456-426614174000',
    createdAt: '2025-10-10T12:00:00Z',
    employee: { name: 'John Doe', email: 'john@example.com' },
  },
  {
    id: 'alias-2',
    extractedName: 'JANESMITH',
    employeeId: '123e4567-e89b-12d3-a456-426614174001',
    createdAt: '2025-10-10T13:00:00Z',
    employee: { name: 'Jane Smith', email: 'jane@example.com' },
  },
];

describe('AliasManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders alias list correctly', async () => {
    // Mock getAliases to return test data
    (aliasService.getAliases as jest.Mock).mockResolvedValue(mockAliases);

    render(<AliasManager employees={mockEmployees} />);

    // Wait for aliases to load
    await waitFor(() => {
      expect(screen.getByText('JOHNSMITH')).toBeInTheDocument();
    });

    // Verify both aliases are rendered
    expect(screen.getByText('JOHNSMITH')).toBeInTheDocument();
    expect(screen.getByText('JANESMITH')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();

    // Verify count is displayed
    expect(screen.getByText('Existing Aliases (2)')).toBeInTheDocument();
  });

  test('creates new alias on form submit', async () => {
    // Mock getAliases to return empty initially
    (aliasService.getAliases as jest.Mock).mockResolvedValue([]);

    // Mock createAlias to return new alias
    const newAlias: aliasService.EmployeeAlias = {
      id: 'new-alias',
      extractedName: 'BOBJOHNSON',
      employeeId: mockEmployees[0].id,
      createdAt: '2025-10-10T14:00:00Z',
      employee: { name: 'John Doe', email: 'john@example.com' },
    };
    (aliasService.createAlias as jest.Mock).mockResolvedValue(newAlias);

    render(<AliasManager employees={mockEmployees} />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('No aliases created yet')).toBeInTheDocument();
    });

    // Fill in the form
    const nameInput = screen.getByLabelText(/Name from PDF/i);
    const employeeSelect = screen.getByLabelText(/Map to Employee/i);

    fireEvent.change(nameInput, { target: { value: 'BOBJOHNSON' } });
    fireEvent.change(employeeSelect, { target: { value: mockEmployees[0].id } });

    // Submit form
    const submitButton = screen.getByText('Create Alias');
    fireEvent.click(submitButton);

    // Verify API was called
    await waitFor(() => {
      expect(aliasService.createAlias).toHaveBeenCalledWith('BOBJOHNSON', mockEmployees[0].id);
    });

    // Verify success message
    await waitFor(() => {
      expect(screen.getByText(/Alias "BOBJOHNSON" created successfully/i)).toBeInTheDocument();
    });

    // Verify new alias appears in table
    expect(screen.getByText('BOBJOHNSON')).toBeInTheDocument();
  });

  test('deletes alias on button click', async () => {
    // Mock getAliases to return test data
    (aliasService.getAliases as jest.Mock).mockResolvedValue(mockAliases);
    (aliasService.deleteAlias as jest.Mock).mockResolvedValue(undefined);

    // Mock window.confirm
    global.confirm = jest.fn(() => true);

    render(<AliasManager employees={mockEmployees} />);

    // Wait for aliases to load
    await waitFor(() => {
      expect(screen.getByText('JOHNSMITH')).toBeInTheDocument();
    });

    // Find and click delete button for first alias
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);

    // Verify confirm was called
    expect(global.confirm).toHaveBeenCalledWith(
      'Are you sure you want to delete the alias "JOHNSMITH"?'
    );

    // Verify API was called
    await waitFor(() => {
      expect(aliasService.deleteAlias).toHaveBeenCalledWith('alias-1');
    });

    // Verify success message
    await waitFor(() => {
      expect(screen.getByText(/Alias "JOHNSMITH" deleted successfully/i)).toBeInTheDocument();
    });

    // Verify alias is removed from list
    await waitFor(() => {
      expect(screen.queryByText('JOHNSMITH')).not.toBeInTheDocument();
    });
  });

  test('shows error toast on duplicate alias', async () => {
    // Mock getAliases to return test data
    (aliasService.getAliases as jest.Mock).mockResolvedValue(mockAliases);

    // Mock createAlias to throw duplicate error
    (aliasService.createAlias as jest.Mock).mockRejectedValue(
      new Error('Duplicate alias: Alias already exists')
    );

    render(<AliasManager employees={mockEmployees} />);

    // Wait for load
    await waitFor(() => {
      expect(screen.getByText('JOHNSMITH')).toBeInTheDocument();
    });

    // Try to create duplicate
    const nameInput = screen.getByLabelText(/Name from PDF/i);
    const employeeSelect = screen.getByLabelText(/Map to Employee/i);

    fireEvent.change(nameInput, { target: { value: 'JOHNSMITH' } });
    fireEvent.change(employeeSelect, { target: { value: mockEmployees[0].id } });

    const submitButton = screen.getByText('Create Alias');
    fireEvent.click(submitButton);

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/Duplicate alias/i)).toBeInTheDocument();
    });
  });

  test('shows error toast on invalid employee', async () => {
    // Mock getAliases to return empty
    (aliasService.getAliases as jest.Mock).mockResolvedValue([]);

    // Mock createAlias to throw not found error
    (aliasService.createAlias as jest.Mock).mockRejectedValue(
      new Error('Employee not found: Invalid employee ID')
    );

    render(<AliasManager employees={mockEmployees} />);

    // Wait for load
    await waitFor(() => {
      expect(screen.getByText('No aliases created yet')).toBeInTheDocument();
    });

    // Try to create alias with invalid employee
    const nameInput = screen.getByLabelText(/Name from PDF/i);
    const employeeSelect = screen.getByLabelText(/Map to Employee/i);

    fireEvent.change(nameInput, { target: { value: 'TESTUSER' } });
    fireEvent.change(employeeSelect, { target: { value: 'invalid-id' } });

    const submitButton = screen.getByText('Create Alias');
    fireEvent.click(submitButton);

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/Employee not found/i)).toBeInTheDocument();
    });
  });

  test('disables submit button when form is incomplete', () => {
    (aliasService.getAliases as jest.Mock).mockResolvedValue([]);

    render(<AliasManager employees={mockEmployees} />);

    const submitButton = screen.getByText('Create Alias');

    // Initially disabled (no values)
    expect(submitButton).toBeDisabled();

    // Enter only name
    const nameInput = screen.getByLabelText(/Name from PDF/i);
    fireEvent.change(nameInput, { target: { value: 'TESTNAME' } });

    // Still disabled (no employee selected)
    expect(submitButton).toBeDisabled();

    // Select employee
    const employeeSelect = screen.getByLabelText(/Map to Employee/i);
    fireEvent.change(employeeSelect, { target: { value: mockEmployees[0].id } });

    // Now enabled
    expect(submitButton).not.toBeDisabled();
  });
});
