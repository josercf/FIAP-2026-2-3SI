import React from 'react';

interface Props {
  title: string;
  onAddToCart: (id: string) => void;
}

export const ProductCard: React.FC<Props> = ({ title, onAddToCart }) => {
  return (
    <div className="product-card" data-testid="product-card">
      <h3>{title}</h3>
      <button onClick={() => onAddToCart("prod-123")}>Adicionar ao Carrinho</button>
    </div>
  );
};
