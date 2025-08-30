interface ProductCountProps {
  count: number;
  type: "approved" | "pending";
}

export function ProductCount({ count, type }: ProductCountProps) {
  const getLabel = () => {
    return type === "approved" ? "Approved Products" : "Pending Products";
  };

  return (
    <div className="mb-6 text-center">
      <div className="inline-flex items-center space-x-3">
        <span className="text-2xl font-bold text-gray-900">{count}</span>
        <span className="text-gray-500 text-sm">{getLabel()}</span>
      </div>
    </div>
  );
}
