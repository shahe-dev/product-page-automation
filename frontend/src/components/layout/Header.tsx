import { Menu } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/auth-store"
import { useUIStore } from "@/stores/ui-store"

export function Header() {
  const { user, logout } = useAuthStore()
  const { toggleSidebar } = useUIStore()

  return (
    <header className="h-16 border-b border-border bg-background px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={toggleSidebar} aria-label="Toggle sidebar">
          <Menu className="h-5 w-5" />
        </Button>
        <span className="text-lg font-semibold">PDP Automation</span>
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">{user.name}</span>
            <Button variant="ghost" size="sm" onClick={logout}>
              Sign Out
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
