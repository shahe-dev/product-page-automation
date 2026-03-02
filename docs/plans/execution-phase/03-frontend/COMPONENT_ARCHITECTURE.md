# Component Architecture

**Last Updated:** 2026-01-24
**Status:** Active
**Owner:** Frontend Team

---

## Overview

This document defines the component architecture patterns, folder structure, and design principles for the PDP Automation v.3 React application. The architecture follows atomic design principles with clear separation between presentational and container components.

### Technology Stack

- **Framework:** React 19.x
- **Language:** TypeScript 5.x
- **Build Tool:** Vite 5.x
- **Styling:** Tailwind CSS 4.x
- **Testing:** Vitest + React Testing Library

---

## Directory Structure

```
src/
  components/
    ui/              # Atomic UI primitives (Button, Input, Modal)
    layout/          # Layout components (AppLayout, Header, Sidebar)
    features/        # Feature-specific components
      projects/      # Project-related components
      jobs/          # Job processing components
      prompts/       # Prompt management components
      qa/            # QA dashboard components
    shared/          # Shared composite components
  hooks/
    queries/         # React Query hooks
    mutations/       # Mutation hooks
    stores/          # Zustand store hooks
    utils/           # Utility hooks (useDebounce, useMediaQuery)
  lib/
    api.ts           # API client
    queryClient.ts   # React Query configuration
    utils.ts         # Utility functions
  pages/             # Route page components
  types/             # TypeScript type definitions
  styles/            # Global styles and Tailwind config
```

---

## Component Categories

### 1. UI Primitives (`components/ui/`)

Atomic, stateless components from shadcn/ui. These are the building blocks.

```typescript
// components/ui/button.tsx
import { cva, type VariantProps } from 'class-variance-authority'
import { forwardRef } from 'react'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      className={buttonVariants({ variant, size, className })}
      ref={ref}
      {...props}
    />
  )
)
```

### 2. Layout Components (`components/layout/`)

Structural components that define page layouts.

```typescript
// components/layout/PageHeader.tsx
interface PageHeaderProps {
  title: string
  description?: string
  actions?: React.ReactNode
  breadcrumbs?: { label: string; href?: string }[]
}

export function PageHeader({ title, description, actions, breadcrumbs }: PageHeaderProps) {
  return (
    <div className="mb-6">
      {breadcrumbs && <Breadcrumbs items={breadcrumbs} />}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {description && <p className="mt-1 text-gray-500">{description}</p>}
        </div>
        {actions && <div className="flex gap-3">{actions}</div>}
      </div>
    </div>
  )
}
```

### 3. Feature Components (`components/features/`)

Domain-specific components organized by feature area.

```typescript
// components/features/projects/ProjectCard.tsx
interface ProjectCardProps {
  project: Project
  onEdit?: () => void
  onDelete?: () => void
}

export function ProjectCard({ project, onEdit, onDelete }: ProjectCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <CardTitle>{project.name}</CardTitle>
        <Badge variant={getStatusVariant(project.status)}>
          {project.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Developer</dt>
            <dd className="font-medium">{project.developer}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Emirate</dt>
            <dd className="font-medium">{project.emirate}</dd>
          </div>
        </dl>
      </CardContent>
      <CardFooter className="gap-2">
        <Button variant="outline" size="sm" onClick={onEdit}>Edit</Button>
        <Button variant="ghost" size="sm" onClick={onDelete}>Delete</Button>
      </CardFooter>
    </Card>
  )
}
```

### 4. Shared Components (`components/shared/`)

Reusable composite components used across features.

```typescript
// components/shared/DataTable.tsx
interface DataTableProps<T> {
  columns: ColumnDef<T>[]
  data: T[]
  isLoading?: boolean
  pagination?: PaginationState
  onPaginationChange?: (pagination: PaginationState) => void
  onRowClick?: (row: T) => void
}

export function DataTable<T>({
  columns,
  data,
  isLoading,
  pagination,
  onPaginationChange,
  onRowClick,
}: DataTableProps<T>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    state: { pagination },
    onPaginationChange,
  })

  if (isLoading) return <TableSkeleton columns={columns.length} />

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <TableRow
              key={row.id}
              onClick={() => onRowClick?.(row.original)}
              className={onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''}
            >
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {pagination && <TablePagination table={table} />}
    </div>
  )
}
```

---

## Component Patterns

### Composition Pattern

Prefer composition over configuration for flexible components.

```typescript
// Good: Composable
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>

// Avoid: Prop-heavy
<Card
  title="Title"
  content="Content"
  footer={<Button>Action</Button>}
/>
```

### Controlled vs Uncontrolled

Use controlled components for form inputs that need external state management.

```typescript
// Controlled - external state
function ControlledInput({ value, onChange }: Props) {
  return <Input value={value} onChange={onChange} />
}

// Uncontrolled - internal state with callback
function UncontrolledInput({ defaultValue, onSubmit }: Props) {
  const [value, setValue] = useState(defaultValue)
  return (
    <form onSubmit={() => onSubmit(value)}>
      <Input value={value} onChange={(e) => setValue(e.target.value)} />
    </form>
  )
}
```

### Compound Components

Group related components for cohesive APIs.

```typescript
// components/features/jobs/JobStatus.tsx
export const JobStatus = {
  Root: JobStatusRoot,
  Icon: JobStatusIcon,
  Label: JobStatusLabel,
  Progress: JobStatusProgress,
}

// Usage
<JobStatus.Root status={job.status}>
  <JobStatus.Icon />
  <JobStatus.Label />
  <JobStatus.Progress value={job.progress} />
</JobStatus.Root>
```

---

## Performance Patterns

### Memoization

```typescript
// Memoize expensive components
const ProjectList = memo(function ProjectList({ projects }: Props) {
  return projects.map((p) => <ProjectCard key={p.id} project={p} />)
})

// Memoize callbacks passed to children
function ProjectsPage() {
  const handleEdit = useCallback((id: string) => {
    navigate(`/projects/${id}/edit`)
  }, [navigate])

  return <ProjectList onEdit={handleEdit} />
}
```

### Code Splitting

```typescript
// Lazy load feature components
const QADashboard = lazy(() => import('./features/qa/QADashboard'))
const PromptsPage = lazy(() => import('./pages/PromptsPage'))

// In router
<Route path="/qa" element={
  <Suspense fallback={<PageSkeleton />}>
    <QADashboard />
  </Suspense>
} />
```

---

## Testing Strategy

### Component Testing

```typescript
// components/features/projects/__tests__/ProjectCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { ProjectCard } from '../ProjectCard'

describe('ProjectCard', () => {
  const mockProject = {
    id: '1',
    name: 'Test Project',
    developer: 'Emaar',
    emirate: 'Dubai',
    status: 'draft',
  }

  it('renders project details', () => {
    render(<ProjectCard project={mockProject} />)

    expect(screen.getByText('Test Project')).toBeInTheDocument()
    expect(screen.getByText('Emaar')).toBeInTheDocument()
    expect(screen.getByText('Dubai')).toBeInTheDocument()
  })

  it('calls onEdit when edit button clicked', () => {
    const onEdit = vi.fn()
    render(<ProjectCard project={mockProject} onEdit={onEdit} />)

    fireEvent.click(screen.getByRole('button', { name: /edit/i }))
    expect(onEdit).toHaveBeenCalledTimes(1)
  })
})
```

---

## Related Documentation

- [Component Library](./COMPONENT_LIBRARY.md) - UI component specifications
- [State Management](./STATE_MANAGEMENT.md) - React Query and Zustand patterns
- [API Client](./API_CLIENT.md) - Backend API integration
- [Accessibility](./ACCESSIBILITY.md) - WCAG compliance guidelines
