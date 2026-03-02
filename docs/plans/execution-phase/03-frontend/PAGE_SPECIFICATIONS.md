# Page Specifications

**Last Updated:** 2026-01-15
**Status:** Active
**Owner:** Frontend Team

---

## Overview

This document provides detailed specifications for all pages in the PDP Automation v.3 application, including wireframes, component breakdowns, and user interaction flows.

### Technology Stack

- **Framework:** React 19.x + TypeScript 5.x
- **Routing:** React Router 7.x
- **Styling:** Tailwind CSS 4.x + shadcn/ui
- **State Management:** React Query 5.x + Zustand 4.x
- **Forms:** React Hook Form + Zod

### Page Categories

1. **Public Pages:** Login
2. **Protected Pages:** All authenticated user pages
3. **Role-Restricted Pages:** Manager Dashboard, Admin Dashboard

---

## Public Pages

### LoginPage

**Route:** `/login`
**Access:** Public (unauthenticated only)
**Redirect:** Authenticated users redirected to `/`

#### Wireframe

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                                                         │
│                  [PDP Automation Logo]                  │
│                                                         │
│                                                         │
│            ┌───────────────────────────┐                │
│            │                           │                │
│            │   Login to Your Account   │                │
│            │                           │                │
│            │  ┌─────────────────────┐  │                │
│            │  │  Sign in with       │  │                │
│            │  │  [G] Google         │  │                │
│            │  └─────────────────────┘  │                │
│            │                           │                │
│            │  Note: Only @your-domain.com       │                │
│            │  email addresses allowed  │                │
│            │                           │                │
│            └───────────────────────────┘                │
│                                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Component Structure

```typescript
// src/pages/LoginPage.tsx
export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuthStore()

  const handleGoogleLogin = async () => {
    try {
      const { token, user } = await api.auth.googleLogin()
      login(token, user)

      const from = location.state?.from?.pathname || '/'
      navigate(from, { replace: true })
    } catch (error) {
      if (error.message.includes('domain')) {
        toast.error('Only @your-domain.com email addresses are allowed')
      } else {
        toast.error('Login failed. Please try again.')
      }
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <div className="text-center mb-8">
          <img src="/logo.svg" alt="PDP Automation" className="h-12 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900">Login to Your Account</h1>
        </div>

        <Button
          variant="outline"
          size="lg"
          className="w-full"
          icon={GoogleIcon}
          onClick={handleGoogleLogin}
        >
          Sign in with Google
        </Button>

        <p className="mt-4 text-sm text-gray-500 text-center">
          Note: Only @your-domain.com email addresses are allowed
        </p>
      </Card>
    </div>
  )
}
```

#### Features

- Google OAuth authentication
- Domain restriction (@your-domain.com only)
- Post-login redirect to intended page
- Error handling with user feedback
- Responsive centered layout

#### Accessibility

- Semantic heading structure
- Alt text for logo
- Focus on login button on page load
- Clear error messages

---

## Protected Pages

### HomePage (Dashboard)

**Route:** `/`
**Access:** All authenticated users
**Layout:** AppLayout with sidebar

#### Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│ [Logo]  PDP Automation    [Search]    [🔔 3]  [User ▼]      │
├──────────────────────────────────────────────────────────────┤
│         │                                                     │
│ [☰ Nav] │  Dashboard                        [Upload PDF]     │
│         │                                                     │
│ Home    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│ Process │  │  Projects   │ │   Pending   │ │  Published  │  │
│ Project │  │  This Week  │ │  Approvals  │ │  This Month │  │
│ Approve │  │     24      │ │      8      │ │     42      │  │
│ Publish │  └─────────────┘ └─────────────┘ └─────────────┘  │
│ QA      │                                                     │
│ Prompts │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│ Workflw │  │   Active    │ │     QA      │ │    Team     │  │
│ History │  │    Jobs     │ │  Pass Rate  │ │  Velocity   │  │
│ Manager │  │      3      │ │     96%     │ │   18/week   │  │
│ Admin   │  └─────────────┘ └─────────────┘ └─────────────┘  │
│         │                                                     │
│         │  Recent Activity                                   │
│         │  ┌──────────────────────────────────────────────┐  │
│         │  │ • Project "Marina Bay" approved   (2h ago)   │  │
│         │  │ • QA passed for "Downtown Towers" (4h ago)   │  │
│         │  │ • New upload: "Palm Residences"   (5h ago)   │  │
│         │  │ • Content generated for "Emaar 1" (6h ago)   │  │
│         │  │ • Published: "Damac Hills"        (8h ago)   │  │
│         │  └──────────────────────────────────────────────┘  │
│         │                                                     │
│         │  Quick Actions                                     │
│         │  [Upload New PDF] [View Approvals] [Run QA Check] │
│         │                                                     │
└──────────────────────────────────────────────────────────────┘
```

#### Component Structure

```typescript
// src/pages/HomePage.tsx
export function HomePage() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: api.dashboard.getStats
  })

  const { data: recentActivity } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: api.activity.getRecent,
    refetchInterval: 30000 // Refresh every 30s
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <Button icon={Upload} onClick={() => navigate('/processing')}>
          Upload PDF
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="Projects This Week"
          value={stats?.projectsThisWeek}
          icon={Folder}
          trend="+12%"
        />
        <StatCard
          title="Pending Approvals"
          value={stats?.pendingApprovals}
          icon={Clock}
          variant="warning"
        />
        <StatCard
          title="Published This Month"
          value={stats?.publishedThisMonth}
          icon={CheckCircle}
          trend="+8%"
        />
        <StatCard
          title="Active Jobs"
          value={stats?.activeJobs}
          icon={Activity}
        />
        <StatCard
          title="QA Pass Rate"
          value={`${stats?.qaPassRate}%`}
          icon={Shield}
        />
        <StatCard
          title="Team Velocity"
          value={`${stats?.teamVelocity}/week`}
          icon={TrendingUp}
        />
      </div>

      {/* Recent Activity */}
      <Card title="Recent Activity">
        <div className="space-y-3">
          {recentActivity?.map(activity => (
            <ActivityItem key={activity.id} {...activity} />
          ))}
        </div>
      </Card>

      {/* Quick Actions */}
      <Card title="Quick Actions">
        <div className="flex gap-4">
          <Button variant="outline" onClick={() => navigate('/processing')}>
            Upload New PDF
          </Button>
          <Button variant="outline" onClick={() => navigate('/approvals')}>
            View Approvals
          </Button>
          <Button variant="outline" onClick={() => navigate('/qa')}>
            Run QA Check
          </Button>
        </div>
      </Card>
    </div>
  )
}
```

#### Features

- Real-time stats display
- Activity feed (auto-refresh)
- Quick action buttons
- Responsive grid layout
- Trend indicators

---

### ProcessingPage

**Route:** `/processing`
**Access:** All authenticated users
**Layout:** AppLayout

#### Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│ Upload & Process                                              │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Drag & Drop PDF Here                                   │ │
│  │  or [Browse Files]                                      │ │
│  │                                                          │ │
│  │  Max 50MB • PDF only                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Website: [OPR ▼]                                            │
│  Template: [Standard Residential ▼]                          │
│                                                               │
│  [Generate Content]                                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Progress: ▓▓▓▓▓▓░░░░ 60%                                │ │
│  │ Current Step: Extracting images...                      │ │
│  │                                                          │ │
│  │ Steps:                                                   │ │
│  │  ✓ Upload PDF                                           │ │
│  │  ✓ Extract text                                         │ │
│  │  ◉ Extract images      (in progress)                    │ │
│  │  ○ Classify images                                      │ │
│  │  ○ Generate content                                     │ │
│  │  ○ QA validation                                        │ │
│  │  ○ Push to Sheets                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

#### Component Structure

```typescript
// src/pages/ProcessingPage.tsx
export function ProcessingPage() {
  const [file, setFile] = useState<File | null>(null)
  const [website, setWebsite] = useState<string>('OPR')
  const [template, setTemplate] = useState<string>('standard_residential')
  const [jobId, setJobId] = useState<string | null>(null)

  const uploadMutation = useUploadFile()
  const { data: job } = useJob(jobId, {
    enabled: !!jobId,
    refetchInterval: 2000 // Poll every 2s
  })

  const handleSubmit = async () => {
    if (!file) return

    try {
      const result = await uploadMutation.mutateAsync({
        file,
        website,
        template
      })
      setJobId(result.jobId)
      toast.success('Processing started')
    } catch (error) {
      toast.error('Upload failed: ' + error.message)
    }
  }

  const steps = [
    { id: 'upload', label: 'Upload PDF' },
    { id: 'extract_text', label: 'Extract text' },
    { id: 'extract_images', label: 'Extract images' },
    { id: 'classify', label: 'Classify images' },
    { id: 'generate', label: 'Generate content' },
    { id: 'qa', label: 'QA validation' },
    { id: 'sheets', label: 'Push to Sheets' },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Upload & Process</h1>

      <Card>
        <FileUpload
          onFileSelect={setFile}
          disabled={!!jobId}
        />

        {file && (
          <div className="mt-4 text-sm text-gray-600">
            Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </div>
        )}

        <div className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Website
            </label>
            <select
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              disabled={!!jobId}
            >
              <option value="aggregators">Aggregators (24+ domains)</option>
              <option value="opr">OPR (opr.ae)</option>
              <option value="mpp">MPP (main-portal.com)</option>
              <option value="adop">ADOP (abudhabioffplan.ae)</option>
              <option value="adre">ADRE (secondary-market-portal.com)</option>
              <option value="commercial">Commercial (cre.main-portal.com)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Template
            </label>
            <select
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              disabled={!!jobId}
            >
              <option value="standard_residential">Standard Residential</option>
              <option value="luxury_villa">Luxury Villa</option>
              <option value="apartment_complex">Apartment Complex</option>
            </select>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!file || !!jobId}
            loading={uploadMutation.isPending}
            className="w-full"
          >
            Generate Content
          </Button>
        </div>
      </Card>

      {job && (
        <Card title="Processing Status">
          <ProgressTracker
            steps={steps.map(step => ({
              ...step,
              status: getStepStatus(step.id, job.currentStep, job.status)
            }))}
            currentStepId={job.currentStep}
          />

          <div className="mt-4 text-sm text-gray-600">
            {job.statusMessage}
          </div>

          {job.status === 'completed' && (
            <div className="mt-6">
              <Button onClick={() => navigate(`/projects/${job.projectId}`)}>
                View Project
              </Button>
            </div>
          )}

          {job.status === 'failed' && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800">
                <strong>Error:</strong> {job.error}
              </p>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
```

#### Features

- PDF drag-and-drop upload
- Website and template selection
- Real-time progress tracking
- Step-by-step status display
- Error handling
- Success redirection

---

### ProjectsListPage

**Route:** `/projects`
**Access:** All authenticated users
**Layout:** AppLayout

#### Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│ Projects                                      [+ New Project] │
├──────────────────────────────────────────────────────────────┤
│ [Search...]                      [Filters ▼] [Export ▼]      │
│                                                               │
│ Filters: [Emirate: All ▼] [Developer: All ▼] [Status: All ▼]│
│          [Price Range] [Date Range]                   [Reset]│
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ □  Name          Developer   Location   Status   Date   │  │
│ ├───────────────────────────────────────────────────────────│  │
│ │ □  Marina Bay    Emaar        Dubai      Pub     Jan 10 │  │
│ │ □  Downtown      Damac        Dubai      App     Jan 9  │  │
│ │ □  Palm Res      Nakheel      Dubai      Draft   Jan 8  │  │
│ │ □  Springs       Emaar        Dubai      QA      Jan 7  │  │
│ │ □  JBR Tower     Nakheel      Dubai      Pub     Jan 6  │  │
│ └─────────────────────────────────────────────────────────┘  │
│                                                               │
│ Showing 1-5 of 142 projects                                  │
│ [<] [1] [2] [3] ... [29] [>]                                 │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

#### Component Structure

```typescript
// src/pages/ProjectsListPage.tsx
export function ProjectsListPage() {
  const [filters, setFilters] = useFilterStore(state => [
    state.projectFilters,
    state.setProjectFilters
  ])
  const [page, setPage] = useState(0)
  const [selectedRows, setSelectedRows] = useState<string[]>([])

  const { data, isLoading } = useProjects({
    ...filters,
    page,
    pageSize: 10
  })

  const columns: ColumnDef<Project>[] = [
    {
      id: 'select',
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
        />
      ),
    },
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => (
        <Link
          to={`/projects/${row.original.id}`}
          className="font-medium text-blue-600 hover:text-blue-700"
        >
          {row.original.name}
        </Link>
      ),
    },
    {
      accessorKey: 'developer',
      header: 'Developer',
    },
    {
      accessorKey: 'location',
      header: 'Location',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <StatusBadge status={row.original.status} />
      ),
    },
    {
      accessorKey: 'createdAt',
      header: 'Date',
      cell: ({ row }) => format(row.original.createdAt, 'MMM d'),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
        <Button icon={Plus} onClick={() => navigate('/processing')}>
          New Project
        </Button>
      </div>

      <div className="flex gap-4">
        <SearchBar
          value={filters.search}
          onChange={(value) => setFilters({ ...filters, search: value })}
          placeholder="Search projects..."
          className="flex-1"
        />
        <FilterPanel filters={filters} onChange={setFilters} />
        <ExportDropdown selectedIds={selectedRows} />
      </div>

      <DataTable
        columns={columns}
        data={data?.projects || []}
        loading={isLoading}
        pagination={{
          pageIndex: page,
          pageSize: 10,
          pageCount: Math.ceil((data?.total || 0) / 10),
          onPageChange: setPage
        }}
        selection={{
          selectedRows,
          onSelectionChange: setSelectedRows
        }}
        onRowClick={(row) => navigate(`/projects/${row.id}`)}
      />
    </div>
  )
}
```

#### Features

- Full-text search
- Multi-filter support (emirate, developer, status, price, date)
- Sortable columns
- Row selection
- Bulk actions (export, delete)
- Pagination
- Click-through to detail page

---

### ProjectDetailPage

**Route:** `/projects/:id`
**Access:** All authenticated users
**Layout:** AppLayout

#### Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│ Marina Bay Residences                    [Edit] [Export]     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─ Details ─────────────────┐  ┌─ Actions ────────────────┐ │
│ │                            │  │                          │ │
│ │ Developer: Emaar           │  │ [View Content Preview]   │ │
│ │ Location: Dubai Marina     │  │ [Submit for Approval]    │ │
│ │ Emirate: Dubai             │  │ [Run QA Check]           │ │
│ │ Price: AED 1.2M - 3.5M     │  │ [Push to Sheets]         │ │
│ │ Bedrooms: 1-3 BR           │  │                          │ │
│ │ Status: Draft              │  │ Status: Draft            │ │
│ │                            │  │ Last Updated: 2h ago     │ │
│ └────────────────────────────┘  └──────────────────────────┘ │
│                                                               │
│ ┌─ Images ──────────────────────────────────────────────────┐ │
│ │ [Interior (12/20)] [Exterior (8/15)] [Amenity (5/10)]    │ │
│ │                                                           │ │
│ │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                     │ │
│ │  │img │ │img │ │img │ │img │ │img │  [Download All]     │ │
│ │  └────┘ └────┘ └────┘ └────┘ └────┘                     │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─ Floor Plans ─────────────────────────────────────────────┐ │
│ │  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │ │
│ │  │ 1 BR     │ │ 2 BR     │ │ 3 BR     │                  │ │
│ │  │ 850 sqft │ │ 1200 sqft│ │ 1800 sqft│                  │ │
│ │  └──────────┘ └──────────┘ └──────────┘                  │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─ Revision History ────────────────────────────────────────┐ │
│ │ • Content updated by John Doe (2h ago)                    │ │
│ │ • Images classified (4h ago)                              │ │
│ │ • Project created (5h ago)                                │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

#### Component Structure

```typescript
// src/pages/ProjectDetailPage.tsx
export function ProjectDetailPage() {
  const { id } = useParams()
  const { data: project, isLoading } = useProject(id)
  const { data: history } = useProjectHistory(id)

  if (isLoading) return <LoadingSpinner />
  if (!project) return <NotFound />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
        <div className="flex gap-2">
          <Button variant="outline" icon={Edit}>Edit</Button>
          <Button variant="outline" icon={Download}>Export</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Details" className="lg:col-span-2">
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Developer</dt>
              <dd className="mt-1 text-sm text-gray-900">{project.developer}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Location</dt>
              <dd className="mt-1 text-sm text-gray-900">{project.location}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Emirate</dt>
              <dd className="mt-1 text-sm text-gray-900">{project.emirate}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Price Range</dt>
              <dd className="mt-1 text-sm text-gray-900">{project.priceRange}</dd>
            </div>
          </dl>
        </Card>

        <Card title="Actions">
          <div className="space-y-2">
            <Button variant="outline" className="w-full">
              View Content Preview
            </Button>
            <Button variant="outline" className="w-full">
              Submit for Approval
            </Button>
            <Button variant="outline" className="w-full">
              Run QA Check
            </Button>
            <Button variant="outline" className="w-full">
              Push to Sheets
            </Button>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <StatusBadge status={project.status} />
            <p className="text-xs text-gray-500 mt-2">
              Last updated {formatDistanceToNow(project.updatedAt)} ago
            </p>
          </div>
        </Card>
      </div>

      <Card title="Images">
        <ImageGallery images={project.images} />
      </Card>

      <Card title="Floor Plans">
        <FloorPlanViewer plans={project.floorPlans} />
      </Card>

      <Card title="Revision History">
        <Timeline events={history} />
      </Card>
    </div>
  )
}
```

#### Features

- View/edit all project fields
- Image gallery with categories
- Floor plans viewer
- Revision history timeline
- Action buttons (preview, approve, QA, export)
- Status indicator

---

### ContentPreviewPage

**Route:** `/projects/:id/preview`
**Access:** All authenticated users
**Layout:** AppLayout

#### Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│ Content Preview: Marina Bay                [Push to Sheets]  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─ Meta Description (148/160 chars) ────────────────────────┐│
│ │ Discover Marina Bay Residences - luxury waterfront living │││
│ │ in Dubai Marina. 1-3 BR apartments starting AED 1.2M.     │││
│ │                                          [Regenerate]      │││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
│ ┌─ H1 Heading (52/60 chars) ────────────────────────────────┐│
│ │ Marina Bay Residences | Luxury Dubai Marina Homes         │││
│ │                                          [Regenerate]      │││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
│ ┌─ Introduction (458/500 chars) ────────────────────────────┐│
│ │ Welcome to Marina Bay Residences, where luxury meets      │││
│ │ waterfront living in the heart of Dubai Marina. This      │││
│ │ exceptional development by Emaar offers...                │││
│ │                                          [Regenerate]      │││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
│ ┌─ Features (12 items) ──────────────────────────────────────┐│
│ │ • Waterfront location                                     │││
│ │ • World-class amenities                                   │││
│ │ • Prime Dubai Marina location                             │││
│ │ ...                                       [Regenerate]     │││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
│ [Compare with Extracted Data]                                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

#### Component Structure

```typescript
// src/pages/ContentPreviewPage.tsx
export function ContentPreviewPage() {
  const { id } = useParams()
  const { data: project } = useProject(id)
  const regenerateMutation = useRegenerateField()
  const pushToSheets = usePushToSheets()

  const [compareMode, setCompareMode] = useState(false)

  const handleRegenerate = async (fieldName: string) => {
    try {
      await regenerateMutation.mutateAsync({ projectId: id, fieldName })
      toast.success(`${fieldName} regenerated`)
    } catch (error) {
      toast.error('Regeneration failed')
    }
  }

  const handlePushToSheets = async () => {
    try {
      await pushToSheets.mutateAsync(id)
      toast.success('Content pushed to Google Sheets')
      navigate('/publishing')
    } catch (error) {
      toast.error('Failed to push to sheets')
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">
          Content Preview: {project?.name}
        </h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setCompareMode(!compareMode)}
          >
            {compareMode ? 'Hide' : 'Compare with Extracted Data'}
          </Button>
          <Button
            icon={Send}
            onClick={handlePushToSheets}
            loading={pushToSheets.isPending}
          >
            Push to Sheets
          </Button>
        </div>
      </div>

      <ContentField
        label="Meta Description"
        value={project?.content.metaDescription}
        maxLength={160}
        onRegenerate={() => handleRegenerate('metaDescription')}
        compareValue={compareMode ? project?.extracted.description : undefined}
      />

      <ContentField
        label="H1 Heading"
        value={project?.content.h1}
        maxLength={60}
        onRegenerate={() => handleRegenerate('h1')}
        compareValue={compareMode ? project?.extracted.title : undefined}
      />

      <ContentField
        label="Introduction"
        value={project?.content.introduction}
        maxLength={500}
        multiline
        onRegenerate={() => handleRegenerate('introduction')}
        compareValue={compareMode ? project?.extracted.intro : undefined}
      />

      <ContentField
        label="Features"
        value={project?.content.features}
        list
        onRegenerate={() => handleRegenerate('features')}
        compareValue={compareMode ? project?.extracted.features : undefined}
      />

      {/* More content fields... */}
    </div>
  )
}
```

#### Features

- Field-by-field content review
- Character count per field
- Regenerate individual fields
- Side-by-side comparison (extracted vs generated)
- Push to Sheets button
- Visual validation

---

### ApprovalQueuePage

**Route:** `/approvals`
**Access:** All authenticated users
**Layout:** AppLayout

#### Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│ Approval Queue (8)                        [Bulk Approve]     │
├──────────────────────────────────────────────────────────────┤
│ [Search...] [Submitter: All ▼] [Date Range]          [Reset] │
│                                                               │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ □ Marina Bay Residences                                   ││
│ │   Emaar • Dubai Marina                                    ││
│ │   Submitted by John Doe on Jan 15, 2026                   ││
│ │   [Approve] [Request Revision] [Reject]                   ││
│ ├───────────────────────────────────────────────────────────┤│
│ │ □ Downtown Towers                                         ││
│ │   Damac • Downtown Dubai                                  ││
│ │   Submitted by Jane Smith on Jan 14, 2026                 ││
│ │   [Approve] [Request Revision] [Reject]                   ││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

#### Component Structure

```typescript
// src/pages/ApprovalQueuePage.tsx
export function ApprovalQueuePage() {
  const { data: approvals, isLoading } = useApprovalQueue()
  const approveMutation = useApproveProject()
  const rejectMutation = useRejectProject()

  const [filters, setFilters] = useState({
    search: '',
    submitter: null,
    dateRange: null
  })

  const handleApprove = async (id: string) => {
    try {
      await approveMutation.mutateAsync(id)
      toast.success('Project approved')
    } catch (error) {
      toast.error('Approval failed')
    }
  }

  const handleReject = async (id: string, reason: string) => {
    try {
      await rejectMutation.mutateAsync({ id, reason })
      toast.success('Project rejected')
    } catch (error) {
      toast.error('Rejection failed')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">
          Approval Queue ({approvals?.length || 0})
        </h1>
        <Button variant="outline">Bulk Approve</Button>
      </div>

      <div className="flex gap-4">
        <SearchBar
          value={filters.search}
          onChange={(value) => setFilters({ ...filters, search: value })}
        />
        <select className="border rounded-md px-3 py-2">
          <option>Submitter: All</option>
        </select>
        <DateRangePicker />
        <Button variant="ghost" size="sm">Reset</Button>
      </div>

      <div className="space-y-4">
        {approvals?.map(approval => (
          <ApprovalCard
            key={approval.id}
            project={approval}
            onApprove={handleApprove}
            onReject={handleReject}
            onRequestRevision={handleRequestRevision}
          />
        ))}
      </div>
    </div>
  )
}
```

#### Features

- List of pending approvals
- Filter by submitter, date
- Bulk approve capability
- Quick review modal
- Approve/reject/request revision actions

---

## Role-Restricted Pages

### ManagerDashboardPage

**Route:** `/manager`
**Access:** Marketing Managers only
**Layout:** AppLayout

#### Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│ Manager Dashboard                         [Export Report]    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─ Approval Metrics ─────────────────────────────────────────┐│
│ │  Average Turnaround Time: 4.2 hours                       ││
│ │  Projects Pending Approval: 8                             ││
│ │  Approved This Week: 24                                   ││
│ │  Rejected This Week: 2                                    ││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
│ ┌─ Team Velocity ────────────────────────────────────────────┐│
│ │  [Line Chart: Projects Processed Over Time]               ││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
│ ┌─ Content Quality ──────────────────────────────────────────┐│
│ │  QA Pass Rate: 96%                                        ││
│ │  Revision Requests: 12                                    ││
│ │  [Bar Chart: Quality Metrics]                             ││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

#### Features

- Approval turnaround metrics
- Team velocity charts
- Content quality statistics
- Export capabilities

---

### AdminDashboardPage

**Route:** `/admin`
**Access:** System Admins only
**Layout:** AppLayout

#### Wireframe

```
┌──────────────────────────────────────────────────────────────┐
│ Admin Dashboard                  [Manage Users] [Settings]   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─ System Health ────────────────────────────────────────────┐│
│ │  API Status: ✓ Healthy                                    ││
│ │  Database: ✓ Connected                                    ││
│ │  Queue: 3 active jobs                                     ││
│ │  Storage: 45 GB / 100 GB (45%)                            ││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
│ ┌─ Anthropic API Usage ─────────────────────────────────────────┐│
│ │  This Month: $234.56 / $500.00 budget                     ││
│ │  [Line Chart: Daily Usage]                                ││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
│ ┌─ Job Statistics ───────────────────────────────────────────┐│
│ │  Completed: 142                                           ││
│ │  Failed: 8 (5.6%)                                         ││
│ │  Average Duration: 3.2 min                                ││
│ └───────────────────────────────────────────────────────────┘││
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

#### Features

- System health monitoring
- API cost tracking
- User management
- Job statistics

---

## Related Documentation

- [Component Library](./COMPONENT_LIBRARY.md) - UI component specifications
- [State Management](./STATE_MANAGEMENT.md) - React Query and Zustand patterns
- [Routing](./ROUTING.md) - Route configuration and guards
- [Accessibility](./ACCESSIBILITY.md) - WCAG compliance guidelines

---

**End of Page Specifications Documentation**
