import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ProductCard } from '../components/ProductCard';

describe('ProductCard Component', () => {
  it('should render the title', () => {
    render(<ProductCard title="Teclado LogiTech" onAddToCart={vi.fn()} />);
    expect(screen.getByText('Teclado LogiTech')).toBeDefined();
  });

  it('should call onAddToCart when button is clicked', async () => {
    const handleAddToCart = vi.fn();
    render(<ProductCard title="Mouse" onAddToCart={handleAddToCart} />);
    
    const button = screen.getByText('Adicionar ao Carrinho');
    await userEvent.click(button);
    
    expect(handleAddToCart).toHaveBeenCalledWith('prod-123');
  });
});
