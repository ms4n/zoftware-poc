import { ProductCard } from "./ProductCard";

import type { Product } from "./types";

interface ProductGridProps {
  products: Product[];
  onStatusChange?: (productId: number, newStatus: string) => void;
  isPending?: boolean;
}

export function ProductGrid({ products, onStatusChange, isPending = false }: ProductGridProps) {
  if (products.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {products.map((product) => (
        <ProductCard 
          key={product.id} 
          product={product} 
          onStatusChange={onStatusChange}
          isPending={isPending}
        />
      ))}
    </div>
  );
}
