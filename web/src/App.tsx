import { NavLink, Route, Routes } from "react-router-dom";
import { PieChart } from "lucide-react";
import PortfolioBar from "./components/PortfolioBar";
import Performance from "./pages/Performance";
import Risk from "./pages/Risk";
import Diversification from "./pages/Diversification";
import Optimise from "./pages/Optimise";
import Backtest from "./pages/Backtest";
import Stress from "./pages/Stress";
import Guide from "./pages/Guide";

const TABS = [
  { to: "/", label: "Performance" },
  { to: "/risk", label: "Risk" },
  { to: "/diversification", label: "Diversification" },
  { to: "/optimise", label: "Optimise" },
  { to: "/backtest", label: "Backtest" },
  { to: "/stress", label: "Stress test" },
  { to: "/guide", label: "Guide & data" },
];

export default function App() {
  return (
    <>
      <header className="header">
        <div className="header-inner">
          <NavLink to="/" className="logo">
            <span className="logo-mark"><PieChart size={18} aria-hidden /></span>
            Portfolio Lab
          </NavLink>
          <nav className="tabs" aria-label="Main">
            {TABS.map((tab) => (
              <NavLink key={tab.to} to={tab.to} end={tab.to === "/"}>{tab.label}</NavLink>
            ))}
          </nav>
        </div>
      </header>
      <div className="wrap"><PortfolioBar /></div>
      <main className="wrap page">
        <Routes>
          <Route index element={<Performance />} />
          <Route path="risk" element={<Risk />} />
          <Route path="diversification" element={<Diversification />} />
          <Route path="optimise" element={<Optimise />} />
          <Route path="backtest" element={<Backtest />} />
          <Route path="stress" element={<Stress />} />
          <Route path="guide" element={<Guide />} />
        </Routes>
      </main>
    </>
  );
}
