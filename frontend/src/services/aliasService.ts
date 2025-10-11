/**
 * Employee Alias Service
 *
 * API client for managing employee name aliases.
 * Provides methods to create, retrieve, and delete employee aliases
 * used during PDF extraction.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface EmployeeAlias {
  id: string;
  extractedName: string;
  employeeId: string;
  createdAt: string;
  employee?: {
    name: string;
    email?: string;
  };
}

export interface CreateAliasRequest {
  extractedName: string;
  employeeId: string;
}

export interface AliasListResponse {
  aliases: EmployeeAlias[];
}

/**
 * Create a new employee alias
 *
 * @param extractedName - Employee name as it appears in PDF
 * @param employeeId - UUID of existing employee to map to
 * @returns Created alias with id and createdAt
 * @throws Error with status 400 if alias already exists
 * @throws Error with status 404 if employee not found
 */
export async function createAlias(
  extractedName: string,
  employeeId: string
): Promise<EmployeeAlias> {
  const response = await fetch(`${API_BASE_URL}/api/aliases`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      extractedName,
      employeeId,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

    if (response.status === 400) {
      throw new Error(`Duplicate alias: ${error.detail || 'Alias already exists'}`);
    } else if (response.status === 404) {
      throw new Error(`Employee not found: ${error.detail || 'Invalid employee ID'}`);
    } else {
      throw new Error(`Failed to create alias: ${error.detail || 'Server error'}`);
    }
  }

  return await response.json();
}

/**
 * Get all employee aliases
 *
 * @returns List of aliases with employee details
 */
export async function getAliases(): Promise<EmployeeAlias[]> {
  const response = await fetch(`${API_BASE_URL}/api/aliases`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(`Failed to fetch aliases: ${error.detail || 'Server error'}`);
  }

  const data: AliasListResponse = await response.json();
  return data.aliases;
}

/**
 * Delete an employee alias
 *
 * @param id - UUID of the alias to delete
 * @throws Error with status 404 if alias not found
 */
export async function deleteAlias(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/aliases/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

    if (response.status === 404) {
      throw new Error(`Alias not found: ${error.detail || 'Alias does not exist'}`);
    } else {
      throw new Error(`Failed to delete alias: ${error.detail || 'Server error'}`);
    }
  }

  // 204 No Content - success
}
