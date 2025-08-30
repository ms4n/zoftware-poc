import { useState, useEffect } from "react";
import {
  LoadingState,
  ErrorState,
  EmptyState,
  ProductGrid,
  ProductCount,
  type Product,
} from "./index";

export function PendingProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingProducts();
  }, []);

  const fetchPendingProducts = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/products/pending");
      if (!response.ok) {
        throw new Error("Failed to fetch products");
      }
      const data = await response.json();
      setProducts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = (productId: number, newStatus: string) => {
    // Remove the product from the pending list when it's approved or rejected
    setProducts(prevProducts => prevProducts.filter(product => product.id !== productId));
  };

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={fetchPendingProducts} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-8 pb-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ProductCount count={products.length} type="pending" />
        {products.length === 0 ? (
          <EmptyState type="pending" />
        ) : (
          <ProductGrid 
            products={products} 
            onStatusChange={handleStatusChange}
            isPending={true}
          />
        )}
      </div>
    </div>
  );
}
