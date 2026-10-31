import { Route, Routes } from "react-router-dom";
import BottomNav from "@/components/BottomNav";
import DashboardPage from "@/features/dashboard/DashboardPage";
import InventoryPage from "@/features/inventory/InventoryPage";
import NeedsPricePage from "@/features/needs-price/NeedsPricePage";
import ShoppingPage from "@/features/shopping/ShoppingPage";
import HistoryPage from "@/features/history/HistoryPage";
import ProductPage from "@/features/products/ProductPage";

export default function App() {
  return (
    <>
      <main className="mx-auto max-w-md p-4 pb-24">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/needs-price" element={<NeedsPricePage />} />
          <Route path="/shopping" element={<ShoppingPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/products/:id" element={<ProductPage />} />
        </Routes>
      </main>
      <BottomNav />
    </>
  );
}
