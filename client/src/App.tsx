import { useState } from "react";
import "./App.css";
import {
  FloatingBottomNav,
  PendingProducts,
  ApprovedProducts,
} from "./components/dashboard";

function App() {
  const [activeTab, setActiveTab] = useState<"approved" | "pending">(
    "approved"
  );

  const renderContent = () => {
    switch (activeTab) {
      case "approved":
        return <ApprovedProducts />;
      case "pending":
        return <PendingProducts />;
      default:
        return <ApprovedProducts />;
    }
  };

  return (
    <div className="App">
      {renderContent()}
      <FloatingBottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}

export default App;
