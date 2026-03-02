import { formatDistanceToNow } from "date-fns"
import { Plus, Shield, Users } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { EmptyState, LoadingSpinner, PageHeader } from "@/components/common"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  useAddAllowlistEntry,
  useAdminStats,
  useAdminUsers,
  useAllowlist,
  useRemoveAllowlistEntry,
  useUpdateUserRole,
} from "@/hooks/queries/use-admin"
import { safeParseDate } from "@/lib/utils"

export default function AdminDashboardPage() {
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [newEmail, setNewEmail] = useState("")
  const [newRole, setNewRole] = useState("user")

  const { data: stats, isLoading: statsLoading } = useAdminStats()
  const { data: users, isLoading: usersLoading } = useAdminUsers()
  const { data: allowlist } = useAllowlist()
  const addEntry = useAddAllowlistEntry()
  const removeEntry = useRemoveAllowlistEntry()
  const updateRole = useUpdateUserRole()

  const handleAddUser = async () => {
    if (!newEmail.trim()) return
    try {
      await addEntry.mutateAsync({ email: newEmail.trim(), role: newRole })
      toast.success(`Added ${newEmail} to allowlist`)
      setAddDialogOpen(false)
      setNewEmail("")
      setNewRole("user")
    } catch {
      toast.error("Failed to add user")
    }
  }

  const handleRoleChange = async (userId: string, role: string) => {
    try {
      await updateRole.mutateAsync({ userId, role })
      toast.success("Role updated")
    } catch {
      toast.error("Failed to update role")
    }
  }

  if (statsLoading || usersLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Admin Dashboard" description="System configuration and user management" />
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Admin Dashboard" description="System configuration and user management">
        <Button onClick={() => setAddDialogOpen(true)}>
          <Plus className="size-4 mr-2" />
          Add User
        </Button>
      </PageHeader>

      {/* System Health Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.user_count ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_jobs ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Failed (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{stats?.failed_jobs_24h ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_projects ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* User Management Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="size-5" />
            User Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!users || users.length === 0 ? (
            <EmptyState icon={Users} title="No Users" description="No users have logged in yet." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-3 font-medium">Name</th>
                    <th className="pb-3 font-medium">Email</th>
                    <th className="pb-3 font-medium">Role</th>
                    <th className="pb-3 font-medium">Last Login</th>
                    <th className="pb-3 font-medium">Projects</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => {
                    const loginDate = safeParseDate(u.last_login_at)
                    return (
                      <tr key={u.id} className="border-b">
                        <td className="py-3 font-medium">{u.name}</td>
                        <td className="py-3 text-muted-foreground">{u.email}</td>
                        <td className="py-3">
                          <Select
                            value={u.role}
                            onValueChange={(v) => handleRoleChange(u.id, v)}
                          >
                            <SelectTrigger className="w-[120px] h-8">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="user">User</SelectItem>
                              <SelectItem value="manager">Manager</SelectItem>
                              <SelectItem value="admin">Admin</SelectItem>
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="py-3 text-muted-foreground">
                          {loginDate ? formatDistanceToNow(loginDate, { addSuffix: true }) : "Never"}
                        </td>
                        <td className="py-3">{u.project_count}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Allowlist Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="size-5" />
            Email Allowlist
            <Badge variant="secondary">{allowlist?.length ?? 0} entries</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!allowlist || allowlist.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No allowlist entries. All @your-domain.com users can log in (bootstrap mode).
            </p>
          ) : (
            <div className="space-y-2">
              {allowlist.map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <span className="font-medium">{entry.email}</span>
                    <Badge variant="outline" className="ml-2">
                      {entry.role}
                    </Badge>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive"
                    onClick={async () => {
                      try {
                        await removeEntry.mutateAsync(entry.id)
                        toast.success("Removed from allowlist")
                      } catch {
                        toast.error("Failed to remove")
                      }
                    }}
                  >
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add User Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add User to Allowlist</DialogTitle>
            <DialogDescription>
              Add an @your-domain.com email address to allow login access.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              placeholder="user@your-domain.com"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
            />
            <Select value={newRole} onValueChange={setNewRole}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user">User</SelectItem>
                <SelectItem value="manager">Manager</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddUser} disabled={!newEmail.trim() || addEntry.isPending}>
              {addEntry.isPending ? "Adding..." : "Add User"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
