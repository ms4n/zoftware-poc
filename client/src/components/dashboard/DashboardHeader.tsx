interface DashboardHeaderProps {
  productCount: number;
  onRefresh: () => void;
}

export function DashboardHeader({
  productCount,
  onRefresh,
}: DashboardHeaderProps) {
  return (
    <div className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Product Dashboard
            </h1>
            <p className="text-gray-600 mt-1">Manage pending product reviews</p>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              {productCount} pending products
            </span>
            <button
              onClick={onRefresh}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
