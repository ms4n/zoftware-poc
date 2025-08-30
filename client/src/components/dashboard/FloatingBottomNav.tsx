interface FloatingBottomNavProps {
  activeTab: "approved" | "pending";
  onTabChange: (tab: "approved" | "pending") => void;
}

export function FloatingBottomNav({
  activeTab,
  onTabChange,
}: FloatingBottomNavProps) {
  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
      {/* Backdrop blur layer */}
      <div className="absolute inset-0 -m-4 bg-white/80 backdrop-blur-md rounded-full"></div>

      {/* Navigation container */}
      <div className="relative bg-white/90 rounded-full shadow-lg border border-gray-200 px-2 py-2">
        <div className="flex space-x-1">
          <button
            onClick={() => onTabChange("approved")}
            className={`px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 ${
              activeTab === "approved"
                ? "bg-blue-600 text-white shadow-md"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            Approved
          </button>
          <button
            onClick={() => onTabChange("pending")}
            className={`px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 ${
              activeTab === "pending"
                ? "bg-blue-600 text-white shadow-md"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            Pending
          </button>
        </div>
      </div>
    </div>
  );
}
