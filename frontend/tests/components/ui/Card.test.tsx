import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../../src/components/ui/Card';

describe('Card Components', () => {
  it('renders Card with correct structure', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Card content</p>
        </CardContent>
        <CardFooter>
          <p>Card footer</p>
        </CardFooter>
      </Card>
    );
    
    expect(screen.getByText('Test Card')).toBeInTheDocument();
    expect(screen.getByText('Card content')).toBeInTheDocument();
    expect(screen.getByText('Card footer')).toBeInTheDocument();
  });

  it('renders CardHeader with correct classes', () => {
    render(
      <Card>
        <CardHeader>Header Content</CardHeader>
      </Card>
    );
    
    const header = screen.getByText('Header Content');
    expect(header).toBeInTheDocument();
    expect(header).toHaveClass('p-6');
  });

  it('renders CardTitle with correct classes', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
        </CardHeader>
      </Card>
    );
    
    const title = screen.getByText('Card Title');
    expect(title).toBeInTheDocument();
    expect(title).toHaveClass('text-lg', 'font-semibold');
  });

  it('renders CardContent with correct classes', () => {
    render(
      <Card>
        <CardContent>Content</CardContent>
      </Card>
    );
    
    const content = screen.getByText('Content');
    expect(content).toBeInTheDocument();
    expect(content).toHaveClass('px-6');
  });

  it('renders CardFooter with correct classes', () => {
    render(
      <Card>
        <CardFooter>Footer</CardFooter>
      </Card>
    );
    
    const footer = screen.getByText('Footer');
    expect(footer).toBeInTheDocument();
    expect(footer).toHaveClass('px-6', 'py-4');
  });
});