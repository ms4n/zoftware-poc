import type { Product } from "./types";

interface ProductCardProps {
  product: Product;
}

const getCategoryColor = (category: string) => {
  const colors: { [key: string]: string } = {
    sales_marketing: "bg-blue-100 text-blue-800",
    other: "bg-gray-100 text-gray-800",
  };
  return colors[category] || "bg-gray-100 text-gray-800";
};

export function ProductCard({ product }: ProductCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      {/* Product Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-start space-x-4">
          <img
            src={product.logo}
            alt={product.name}
            className="w-16 h-16 rounded-lg object-cover bg-gray-100"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src =
                "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiByeD0iOCIgZmlsbD0iI0YzRjRGNiIvPgo8cGF0aCBkPSJNMzIgMjBDMzUuMzEzNyAyMCAzOCAyMi42ODYzIDM4IDI2QzM4IDI5LjMxMzcgMzUuMzEzNyAzMiAzMiAzMkMyOC42ODYzIDMyIDI2IDI5LjMxMzcgMjYgMjZDMjYgMjIuNjg2MyAyOC42ODYzIDIwIDMyIDIwWiIgZmlsbD0iIzlDQTNBRiIvPgo8cGF0aCBkPSJNNDggNTJIMTZDMjAuNDE4MyA0MCAyOC4zMTM3IDM0IDM2IDM0QzQzLjY4NjMgMzQgNTEuNTgxNyA0MCA1NiA1MloiIGZpbGw9IiM5Q0EzQUYiLz4KPC9zdmc+";
            }}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {product.name}
              </h3>
              {product.website && (
                <a
                  href={product.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                  title="Visit Website"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              )}
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(
                  product.category
                )}`}
              >
                {product.category.replace("_", " ")}
              </span>
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                {product.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Product Description */}
      <div className="p-6">
        <p className="text-gray-600 text-sm line-clamp-3 mb-6">
          {product.description}
        </p>

        {/* Actions */}
        <div className="flex space-x-2">
          <button className="flex-1 bg-green-600 text-white px-3 py-2 rounded-md text-sm hover:bg-green-700 transition-colors">
            Approve
          </button>
          <button className="flex-1 bg-red-600 text-white px-3 py-2 rounded-md text-sm hover:bg-red-700 transition-colors">
            Reject
          </button>
        </div>
      </div>
    </div>
  );
}
