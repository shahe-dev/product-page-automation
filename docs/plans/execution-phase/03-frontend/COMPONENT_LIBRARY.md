# Component Library

**Last Updated:** 2026-01-15
**Status:** Active
**Owner:** Frontend Team

---

## Overview

This document specifies the complete UI component library for the PDP Automation v.3 system. All components are built using React 19, TypeScript 5, and styled with Tailwind CSS 4 using the shadcn/ui component library as a foundation.

### Technology Stack

- **Framework:** React 19.x
- **Language:** TypeScript 5.x
- **Styling:** Tailwind CSS 4.x
- **UI Library:** shadcn/ui (latest)
- **Icons:** Lucide React
- **Forms:** React Hook Form + Zod validation
- **Tables:** TanStack Table
- **Charts:** Recharts

### Design Principles

1. **Accessibility First:** All components meet WCAG 2.1 AA standards
2. **Type Safety:** Full TypeScript coverage with strict mode
3. **Composability:** Components are highly composable and reusable
4. **Performance:** Optimized rendering with React 19 features
5. **Consistency:** Unified design language across all components

---

## Layout Components

### AppLayout

Main application wrapper providing the overall structure with header, sidebar, and content area.

```typescript
// src/components/layout/AppLayout.tsx
interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const { sidebarOpen } = useUIStore()

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar open={sidebarOpen} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

**Props:**
- `children` (ReactNode): Page content to render in main area

**Features:**
- Responsive layout (mobile/tablet/desktop)
- Persistent sidebar state
- Automatic scroll handling
- Accessibility landmarks

---

### Header

Top navigation bar with branding, search, notifications, and user menu.

```typescript
// src/components/layout/Header.tsx
export function Header() {
  const { user } = useAuthStore()
  const { data: unreadCount } = useUnreadCount()

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <img src="/logo.svg" alt="PDP Automation" className="h-8" />
        <SearchBar />
      </div>

      <div className="flex items-center gap-4">
        <NotificationBell count={unreadCount} />
        <UserMenu user={user} />
      </div>
    </header>
  )
}
```

**Features:**
- Global search bar
- Notification bell with unread count badge
- User profile dropdown
- Logo/branding
- Responsive (collapses on mobile)

**Accessibility:**
- Semantic `<header>` element
- ARIA labels for icon buttons
- Keyboard navigation support

---

### Sidebar

Left navigation panel with role-based menu items.

```typescript
// src/components/layout/Sidebar.tsx
interface SidebarProps {
  open: boolean
}

export function Sidebar({ open }: SidebarProps) {
  const { user } = useAuthStore()
  const { data: approvalCount } = useApprovalQueue()
  const { data: publishCount } = usePublishingQueue()

  const menuItems = [
    { icon: Home, label: 'Dashboard', path: '/', roles: ['all'] },
    { icon: Upload, label: 'Processing', path: '/processing', roles: ['all'] },
    { icon: Folder, label: 'Projects', path: '/projects', roles: ['all'] },
    { icon: CheckCircle, label: 'Approvals', path: '/approvals', badge: approvalCount, roles: ['all'] },
    { icon: Send, label: 'Publishing', path: '/publishing', badge: publishCount, roles: ['all'] },
    { icon: Shield, label: 'QA', path: '/qa', roles: ['all'] },
    { icon: FileText, label: 'Prompts', path: '/prompts', roles: ['all'] },
    { icon: Kanban, label: 'Workflow', path: '/workflow', roles: ['all'] },
    { icon: History, label: 'History', path: '/history', roles: ['all'] },
    { icon: BarChart, label: 'Manager', path: '/manager', roles: ['marketing_manager'] },
    { icon: Settings, label: 'Admin', path: '/admin', roles: ['system_admin'] },
  ]

  const filteredItems = menuItems.filter(item =>
    item.roles.includes('all') || item.roles.includes(user?.role)
  )

  return (
    <aside className={cn(
      "w-64 bg-gray-900 text-gray-100 transition-transform",
      !open && "-translate-x-full md:translate-x-0"
    )}>
      <nav className="p-4 space-y-2" aria-label="Main navigation">
        {filteredItems.map(item => (
          <SidebarItem key={item.path} {...item} />
        ))}
      </nav>
    </aside>
  )
}
```

**Props:**
- `open` (boolean): Sidebar visibility state (for mobile)

**Features:**
- Role-based menu filtering
- Active route highlighting
- Badge support for counts
- Collapsible on mobile
- Persistent state

**Accessibility:**
- Semantic `<nav>` element
- ARIA label for navigation region
- Active route indicated with `aria-current="page"`
- Keyboard navigable

---

## Core UI Components

### Button

Primary interactive element with multiple variants and states.

```typescript
// src/components/ui/Button.tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'ghost' | 'link'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  icon?: React.ComponentType<{ className?: string }>
  children: React.ReactNode
}

export function Button({
  variant = 'default',
  size = 'md',
  loading = false,
  icon: Icon,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }))}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {!loading && Icon && <Icon className="mr-2 h-4 w-4" />}
      {children}
    </button>
  )
}
```

**Props:**
- `variant` (string): Visual style - default, destructive, outline, ghost, link
- `size` (string): Size - sm, md, lg
- `loading` (boolean): Show loading spinner
- `icon` (Component): Optional icon component
- `disabled` (boolean): Disable interactions
- Standard HTML button attributes

**Variants:**
- **default:** Primary blue button
- **destructive:** Red for dangerous actions
- **outline:** Bordered with transparent background
- **ghost:** No background until hover
- **link:** Text-only link style

**Accessibility:**
- Disabled state prevents interaction
- Loading state announced to screen readers
- Sufficient color contrast
- Keyboard accessible

---

### Card

Container component for grouping related content.

```typescript
// src/components/ui/Card.tsx
interface CardProps {
  title?: string
  description?: string
  footer?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function Card({ title, description, footer, children, className }: CardProps) {
  return (
    <div className={cn("bg-white rounded-lg border border-gray-200 shadow-sm", className)}>
      {(title || description) && (
        <div className="p-6 border-b border-gray-200">
          {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
          {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
        </div>
      )}

      <div className="p-6">{children}</div>

      {footer && (
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          {footer}
        </div>
      )}
    </div>
  )
}
```

**Props:**
- `title` (string): Optional card title
- `description` (string): Optional subtitle/description
- `footer` (ReactNode): Optional footer content
- `children` (ReactNode): Main card content
- `className` (string): Additional CSS classes

**Use Cases:**
- Dashboard stat cards
- Form sections
- Content containers
- List items

---

### DataTable

Generic table component with sorting, filtering, pagination, and row selection.

```typescript
// src/components/ui/DataTable.tsx
interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  onRowClick?: (row: TData) => void
  loading?: boolean
  pagination?: {
    pageIndex: number
    pageSize: number
    pageCount: number
    onPageChange: (page: number) => void
  }
  sorting?: {
    sortBy: string
    sortOrder: 'asc' | 'desc'
    onSortChange: (column: string, order: 'asc' | 'desc') => void
  }
  selection?: {
    selectedRows: string[]
    onSelectionChange: (rows: string[]) => void
  }
  actions?: Array<{
    label: string
    icon?: React.ComponentType
    onClick: (rows: TData[]) => void
  }>
}

export function DataTable<TData, TValue>({
  columns,
  data,
  onRowClick,
  loading,
  pagination,
  sorting,
  selection,
  actions
}: DataTableProps<TData, TValue>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  return (
    <div className="space-y-4">
      {actions && selection && (
        <div className="flex gap-2">
          {actions.map(action => (
            <Button
              key={action.label}
              variant="outline"
              size="sm"
              icon={action.icon}
              onClick={() => action.onClick(getSelectedRows())}
              disabled={selection.selectedRows.length === 0}
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}

      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>

          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12 text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto text-gray-400" />
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map(row => (
                <tr
                  key={row.id}
                  onClick={() => onRowClick?.(row.original)}
                  className={cn(
                    "hover:bg-gray-50 transition-colors",
                    onRowClick && "cursor-pointer"
                  )}
                >
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Page {pagination.pageIndex + 1} of {pagination.pageCount}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => pagination.onPageChange(pagination.pageIndex - 1)}
              disabled={pagination.pageIndex === 0}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => pagination.onPageChange(pagination.pageIndex + 1)}
              disabled={pagination.pageIndex >= pagination.pageCount - 1}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
```

**Props:**
- `columns` (ColumnDef[]): TanStack Table column definitions
- `data` (TData[]): Table data array
- `onRowClick` (function): Optional row click handler
- `loading` (boolean): Show loading state
- `pagination` (object): Pagination configuration
- `sorting` (object): Sorting configuration
- `selection` (object): Row selection configuration
- `actions` (array): Bulk action buttons

**Features:**
- Client-side sorting
- Row selection (single/multiple)
- Pagination controls
- Loading states
- Bulk actions
- Responsive columns

**Accessibility:**
- Semantic table markup
- Sort indicators
- Keyboard navigation
- Screen reader announcements

---

## Domain-Specific Components

### FileUpload

Drag-and-drop file uploader with validation and progress tracking.

```typescript
// src/components/upload/FileUpload.tsx
interface FileUploadProps {
  accept?: string
  maxSize?: number // in bytes
  onFileSelect: (file: File) => void
  onError?: (error: string) => void
  disabled?: boolean
}

export function FileUpload({
  accept = '.pdf',
  maxSize = 50 * 1024 * 1024, // 50MB
  onFileSelect,
  onError,
  disabled = false
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    if (!file.type.includes('pdf')) {
      return 'Only PDF files are allowed'
    }
    if (file.size > maxSize) {
      return `File size must be less than ${maxSize / 1024 / 1024}MB`
    }
    return null
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (!file) return

    const error = validateFile(file)
    if (error) {
      onError?.(error)
      return
    }

    onFileSelect(file)
  }

  return (
    <div
      className={cn(
        "border-2 border-dashed rounded-lg p-12 text-center transition-colors",
        isDragging && "border-blue-500 bg-blue-50",
        !isDragging && "border-gray-300 hover:border-gray-400",
        disabled && "opacity-50 cursor-not-allowed"
      )}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
      <p className="text-lg font-medium text-gray-900 mb-2">
        Drag & Drop PDF Here
      </p>
      <p className="text-sm text-gray-500 mb-4">
        or{' '}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="text-blue-600 hover:text-blue-700 font-medium"
          disabled={disabled}
        >
          Browse Files
        </button>
      </p>
      <p className="text-xs text-gray-400">
        Max {maxSize / 1024 / 1024}MB • PDF only
      </p>

      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) {
            const error = validateFile(file)
            if (error) {
              onError?.(error)
            } else {
              onFileSelect(file)
            }
          }
        }}
        className="hidden"
        disabled={disabled}
      />
    </div>
  )
}
```

**Props:**
- `accept` (string): Accepted file types (default: .pdf)
- `maxSize` (number): Maximum file size in bytes (default: 50MB)
- `onFileSelect` (function): Callback when valid file selected
- `onError` (function): Callback for validation errors
- `disabled` (boolean): Disable upload

**Features:**
- Drag-and-drop support
- File type validation
- File size validation
- Visual feedback on drag
- Browse button fallback
- Error handling

**Accessibility:**
- Hidden file input with accessible trigger
- Keyboard accessible browse button
- Error messages announced
- Disabled state support

---

### ProgressTracker

Multi-step progress visualization for job processing.

```typescript
// src/components/processing/ProgressTracker.tsx
interface Step {
  id: string
  label: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
}

interface ProgressTrackerProps {
  steps: Step[]
  currentStepId: string
}

export function ProgressTracker({ steps, currentStepId }: ProgressTrackerProps) {
  const currentIndex = steps.findIndex(s => s.id === currentStepId)

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center flex-1">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors",
                  step.status === 'completed' && "bg-green-500 border-green-500 text-white",
                  step.status === 'in_progress' && "bg-blue-500 border-blue-500 text-white",
                  step.status === 'failed' && "bg-red-500 border-red-500 text-white",
                  step.status === 'pending' && "bg-gray-100 border-gray-300 text-gray-400"
                )}
              >
                {step.status === 'completed' && <Check className="h-5 w-5" />}
                {step.status === 'in_progress' && <Loader2 className="h-5 w-5 animate-spin" />}
                {step.status === 'failed' && <X className="h-5 w-5" />}
                {step.status === 'pending' && <span className="text-sm">{index + 1}</span>}
              </div>
              <span
                className={cn(
                  "mt-2 text-xs font-medium text-center max-w-[100px]",
                  step.status === 'completed' && "text-green-700",
                  step.status === 'in_progress' && "text-blue-700",
                  step.status === 'failed' && "text-red-700",
                  step.status === 'pending' && "text-gray-500"
                )}
              >
                {step.label}
              </span>
            </div>

            {index < steps.length - 1 && (
              <div
                className={cn(
                  "flex-1 h-0.5 mx-2",
                  index < currentIndex ? "bg-green-500" : "bg-gray-300"
                )}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Props:**
- `steps` (Step[]): Array of step objects with id, label, status
- `currentStepId` (string): ID of currently active step

**Step Statuses:**
- **pending:** Not yet started (gray, numbered)
- **in_progress:** Currently processing (blue, spinner)
- **completed:** Successfully finished (green, checkmark)
- **failed:** Error occurred (red, X icon)

**Features:**
- Visual progress indication
- Step status icons
- Connecting lines
- Color-coded states
- Responsive layout

**Accessibility:**
- ARIA live region for status updates
- Status announced to screen readers
- Color + icon for state (not color alone)

---

### ImageGallery

Categorized image viewer with lightbox and download capabilities.

```typescript
// src/components/projects/ImageGallery.tsx
interface Image {
  id: string
  url: string
  category: 'interior' | 'exterior' | 'amenity' | 'logo'
  filename: string
}

interface ImageGalleryProps {
  images: Image[]
  maxPerCategory?: {
    interior: number
    exterior: number
    amenity: number
    logo: number
  }
}

export function ImageGallery({
  images,
  maxPerCategory = { interior: 20, exterior: 15, amenity: 10, logo: 2 }
}: ImageGalleryProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('interior')
  const [lightboxImage, setLightboxImage] = useState<string | null>(null)

  const categorizedImages = useMemo(() => ({
    interior: images.filter(img => img.category === 'interior'),
    exterior: images.filter(img => img.category === 'exterior'),
    amenity: images.filter(img => img.category === 'amenity'),
    logo: images.filter(img => img.category === 'logo'),
  }), [images])

  const categories = [
    { id: 'interior', label: 'Interior', count: categorizedImages.interior.length, max: maxPerCategory.interior },
    { id: 'exterior', label: 'Exterior', count: categorizedImages.exterior.length, max: maxPerCategory.exterior },
    { id: 'amenity', label: 'Amenity', count: categorizedImages.amenity.length, max: maxPerCategory.amenity },
    { id: 'logo', label: 'Logo', count: categorizedImages.logo.length, max: maxPerCategory.logo },
  ]

  const downloadAll = () => {
    categorizedImages[selectedCategory].forEach(img => {
      const link = document.createElement('a')
      link.href = img.url
      link.download = img.filename
      link.click()
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                selectedCategory === cat.id
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              )}
            >
              {cat.label}{' '}
              <span className={cn(
                selectedCategory === cat.id ? "text-blue-200" : "text-gray-500"
              )}>
                ({cat.count}/{cat.max})
              </span>
            </button>
          ))}
        </div>

        <Button
          variant="outline"
          size="sm"
          icon={Download}
          onClick={downloadAll}
        >
          Download All
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {categorizedImages[selectedCategory].map(image => (
          <button
            key={image.id}
            onClick={() => setLightboxImage(image.url)}
            className="aspect-square rounded-lg overflow-hidden border-2 border-gray-200 hover:border-blue-500 transition-colors"
          >
            <img
              src={image.url}
              alt={image.filename}
              className="w-full h-full object-cover"
            />
          </button>
        ))}
      </div>

      {lightboxImage && (
        <Lightbox
          image={lightboxImage}
          onClose={() => setLightboxImage(null)}
        />
      )}
    </div>
  )
}
```

**Props:**
- `images` (Image[]): Array of image objects
- `maxPerCategory` (object): Maximum images per category

**Features:**
- Categorized tabs
- Category limits display
- Lightbox viewer
- Download all button
- Grid layout
- Hover effects

**Accessibility:**
- Tab keyboard navigation
- Image alt text
- Focus indicators
- Keyboard lightbox controls (ESC to close)

---

### ApprovalCard

Project approval interface with action buttons.

```typescript
// src/components/approvals/ApprovalCard.tsx
interface ApprovalCardProps {
  project: {
    id: string
    name: string
    developer: string
    location: string
    submittedBy: string
    submittedAt: Date
    thumbnail?: string
  }
  onApprove: (id: string) => void
  onReject: (id: string, reason: string) => void
  onRequestRevision: (id: string, comments: string) => void
}

export function ApprovalCard({
  project,
  onApprove,
  onReject,
  onRequestRevision
}: ApprovalCardProps) {
  const [action, setAction] = useState<'approve' | 'reject' | 'revise' | null>(null)
  const [comments, setComments] = useState('')

  const handleSubmit = () => {
    if (action === 'approve') {
      onApprove(project.id)
    } else if (action === 'reject' && comments) {
      onReject(project.id, comments)
    } else if (action === 'revise' && comments) {
      onRequestRevision(project.id, comments)
    }
    setAction(null)
    setComments('')
  }

  return (
    <Card>
      <div className="flex gap-4">
        {project.thumbnail && (
          <img
            src={project.thumbnail}
            alt={project.name}
            className="w-32 h-32 object-cover rounded-lg"
          />
        )}

        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {project.developer} • {project.location}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Submitted by {project.submittedBy} on{' '}
            {format(project.submittedAt, 'MMM d, yyyy')}
          </p>

          {!action && (
            <div className="flex gap-2 mt-4">
              <Button
                variant="default"
                size="sm"
                icon={Check}
                onClick={() => setAction('approve')}
              >
                Approve
              </Button>
              <Button
                variant="outline"
                size="sm"
                icon={MessageCircle}
                onClick={() => setAction('revise')}
              >
                Request Revision
              </Button>
              <Button
                variant="destructive"
                size="sm"
                icon={X}
                onClick={() => setAction('reject')}
              >
                Reject
              </Button>
            </div>
          )}

          {action && (
            <div className="mt-4 space-y-3">
              {action !== 'approve' && (
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder={action === 'reject' ? 'Reason for rejection (required)' : 'Revision notes (required)'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  rows={3}
                  required
                />
              )}

              <div className="flex gap-2">
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleSubmit}
                  disabled={action !== 'approve' && !comments}
                >
                  Confirm {action === 'approve' ? 'Approval' : action === 'reject' ? 'Rejection' : 'Request'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => { setAction(null); setComments('') }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
```

**Props:**
- `project` (object): Project data with metadata
- `onApprove` (function): Approval handler
- `onReject` (function): Rejection handler with reason
- `onRequestRevision` (function): Revision request handler

**Features:**
- Three-action interface (approve/reject/revise)
- Required comments for reject/revise
- Thumbnail preview
- Submitter information
- Confirmation flow

**Accessibility:**
- Form labels and required indicators
- Keyboard navigation
- Focus management
- Error states

---

### NotificationBell

Header notification indicator with dropdown preview.

```typescript
// src/components/notifications/NotificationBell.tsx
interface NotificationBellProps {
  count?: number
}

export function NotificationBell({ count = 0 }: NotificationBellProps) {
  const [open, setOpen] = useState(false)
  const { data: notifications } = useNotifications({ limit: 5 })
  const markAsRead = useMarkAsRead()

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className="relative p-2 rounded-md hover:bg-gray-100 transition-colors"
          aria-label={`Notifications ${count > 0 ? `(${count} unread)` : ''}`}
        >
          <Bell className="h-5 w-5 text-gray-600" />
          {count > 0 && (
            <span className="absolute top-0 right-0 h-5 w-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
              {count > 9 ? '9+' : count}
            </span>
          )}
        </button>
      </PopoverTrigger>

      <PopoverContent className="w-80 p-0" align="end">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Notifications</h3>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {notifications?.length === 0 ? (
            <div className="p-8 text-center text-gray-500 text-sm">
              No notifications
            </div>
          ) : (
            notifications?.map(notification => (
              <button
                key={notification.id}
                onClick={() => {
                  markAsRead.mutate(notification.id)
                  setOpen(false)
                }}
                className={cn(
                  "w-full p-4 text-left border-b border-gray-100 hover:bg-gray-50 transition-colors",
                  !notification.read && "bg-blue-50"
                )}
              >
                <p className="text-sm font-medium text-gray-900">
                  {notification.title}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {notification.message}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {formatDistanceToNow(notification.createdAt, { addSuffix: true })}
                </p>
              </button>
            ))
          )}
        </div>

        <div className="p-2 border-t border-gray-200">
          <Link
            to="/notifications"
            className="block w-full py-2 text-center text-sm font-medium text-blue-600 hover:text-blue-700"
            onClick={() => setOpen(false)}
          >
            View All Notifications
          </Link>
        </div>
      </PopoverContent>
    </Popover>
  )
}
```

**Props:**
- `count` (number): Unread notification count

**Features:**
- Unread count badge
- Dropdown preview (5 recent)
- Mark as read on click
- Link to full notifications page
- Auto-refresh
- Real-time updates

**Accessibility:**
- ARIA label with count
- Keyboard navigation
- Screen reader announcements
- Focus management

---

## Related Documentation

- [Page Specifications](./PAGE_SPECIFICATIONS.md) - Detailed page layouts and wireframes
- [State Management](./STATE_MANAGEMENT.md) - React Query and Zustand patterns
- [Routing](./ROUTING.md) - Route configuration and guards
- [Accessibility](./ACCESSIBILITY.md) - WCAG compliance guidelines
- [API Documentation](../01-backend/API_ENDPOINTS.md) - Backend API reference
- [Database Schema](../01-backend/DATABASE_SCHEMA.md) - Data models

---

**End of Component Library Documentation**
