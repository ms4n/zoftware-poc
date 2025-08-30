interface EmptyStateProps {
  type: "approved" | "pending";
}

export function EmptyState({ type }: EmptyStateProps) {
  const getContent = () => {
    if (type === "approved") {
      return {
        icon: "",
        title: "No Approved Products",
        message: "There are no approved products yet.",
      };
    } else {
      return {
        icon: "📋",
        title: "No Pending Products",
        message:
          "All products have been processed or there are no pending items.",
      };
    }
  };

  const content = getContent();

  return (
    <div className="text-center py-12">
      <div className="text-gray-400 text-6xl mb-4">{content.icon}</div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {content.title}
      </h3>
      <p className="text-gray-500">{content.message}</p>
    </div>
  );
}
