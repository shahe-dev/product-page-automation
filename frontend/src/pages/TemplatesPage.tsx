import { useState } from "react"

import { PageHeader } from "@/components/common"
import { FieldEditor } from "@/components/templates"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { TemplateType } from "@/types"

const TEMPLATE_TABS: { value: TemplateType; label: string }[] = [
  { value: "aggregators", label: "Aggregators" },
  { value: "opr", label: "OPR" },
  { value: "mpp", label: "MPP" },
  { value: "adop", label: "ADOP" },
  { value: "adre", label: "ADRE" },
  { value: "commercial", label: "Commercial" },
]

export default function TemplatesPage() {
  const [activeTemplate, setActiveTemplate] = useState<TemplateType>("aggregators")

  return (
    <div className="space-y-6">
      <PageHeader
        title="Template Field Editor"
        description="Manage field definitions for each template. Changes take effect immediately without code deployment."
      />

      {/* Template type tabs */}
      <Tabs
        value={activeTemplate}
        onValueChange={(v) => setActiveTemplate(v as TemplateType)}
      >
        <TabsList className="w-full justify-start">
          {TEMPLATE_TABS.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Field editor */}
      <FieldEditor templateType={activeTemplate} />
    </div>
  )
}
