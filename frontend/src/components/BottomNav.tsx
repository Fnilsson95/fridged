import { NavLink } from "react-router-dom";

const tabs = [
  { to: "/", label: "Home" },
  { to: "/inventory", label: "Stock" },
  { to: "/needs-price", label: "Prices" },
  { to: "/shopping", label: "Shop" },
  { to: "/history", label: "History" },
];

export default function BottomNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 flex border-t border-gray-200 bg-white pb-3">
      {tabs.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.to === "/"}
          className={({ isActive }) =>
            `flex min-h-13 flex-1 items-center justify-center text-xs ${
              isActive ? "font-bold text-brand" : "text-muted"
            }`
          }
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  );
}
