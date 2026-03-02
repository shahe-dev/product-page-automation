import {
  BarChart,
  CheckCircle,
  FileText,
  Folder,
  History,
  Home,
  LayoutDashboard,
  Send,
  Settings,
  Shield,
  Upload,
} from "lucide-react"
import { NavLink } from "react-router-dom"

import { cn } from "@/lib/utils"
import { useAuthStore } from "@/stores/auth-store"
import { useUIStore } from "@/stores/ui-store"

interface MenuItem {
  icon: React.ComponentType<{ className?: string }>
  label: string
  path: string
  roles: string[]
}

const menuItems: MenuItem[] = [
  { icon: Home, label: "Dashboard", path: "/", roles: ["all"] },
  { icon: Upload, label: "Processing", path: "/processing", roles: ["all"] },
  { icon: Folder, label: "Projects", path: "/projects", roles: ["all"] },
  { icon: CheckCircle, label: "Approvals", path: "/approvals", roles: ["all"] },
  { icon: Send, label: "Publishing", path: "/publishing", roles: ["all"] },
  { icon: Shield, label: "QA", path: "/qa", roles: ["all"] },
  { icon: FileText, label: "Prompts", path: "/prompts", roles: ["all"] },
  { icon: LayoutDashboard, label: "Workflow", path: "/workflow", roles: ["all"] },
  { icon: History, label: "History", path: "/history", roles: ["all"] },
  { icon: BarChart, label: "Manager", path: "/manager", roles: ["admin"] },
  { icon: Settings, label: "Admin", path: "/admin", roles: ["admin"] },
]

export function Sidebar() {
  const { user } = useAuthStore()
  const { sidebarOpen } = useUIStore()

  const filteredItems = menuItems.filter(
    (item) => item.roles.includes("all") || item.roles.includes(user?.role ?? ""),
  )

  return (
    <aside
      className={cn(
        "w-64 bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-transform duration-200",
        !sidebarOpen && "-translate-x-full absolute md:relative md:translate-x-0",
      )}
    >
      <div className="p-4">
        <h2 className="text-sm font-semibold text-sidebar-foreground/60 uppercase tracking-wider mb-4">
          Navigation
        </h2>
      </div>
      <nav className="px-3 space-y-1" aria-label="Main navigation">
        {filteredItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
