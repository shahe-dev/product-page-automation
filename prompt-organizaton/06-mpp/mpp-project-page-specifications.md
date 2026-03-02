##The below specifications are brief and need to be expanded and more detailed based on the pipelines, data dependencies and the process of content generation. 

Hero Section
H1 header - Project name in area (generate)
Brief project description (generate)
Project stats 
Starting Price (use PDF brochure data)
Handover quarter and year (use PDF brochure data)
Number of units (use PDF brochure data)

Project Overview Section
H2 header - Project Overview (Static do not generate)
Project description detailed paragraph (generate)

Project details card (use PDF extraction for all information here) 
Location
Developer
Property Type
Number of bedrooms - needs to be a range based on floor plan information or any content in the PDF. 
Area from - starting square footage based on the smallest unit in the project
Handover - quarter and year
Payment plan - extract from PDF and make the required calculations to know how to display this information, not necessary to follow a very specific format as long as it's informative. 

Gallery Section - static do not generate

Floor plans Table (EXTRACTED -- CRITICAL RULES):

This field contains ALL floor plan entries in a SINGLE cell.
Each unique unit configuration goes on its own line.
Format per line:
Unit Type | Living Area (sq ft) | Starting Price (AED)

Example output (what the cell content looks like):
Studio | 400-450 sq ft | AED 750,000
1BR Apartment | 650-800 sq ft | AED 1,100,000
2BR Apartment | 1,100-1,300 sq ft | AED 1,800,000
3BR Apartment | 1,500-1,800 sq ft | AED 2,500,000
4BR Penthouse | 2,800-3,200 sq ft | AED 5,000,000

DEDUPLICATION RULES:
- If the PDF shows multiple sub-variants of the same bedroom count
  (e.g., "1BR Type A - 650 sq ft" and "1BR Type B - 720 sq ft"),
  MERGE them into a single line with a size RANGE:
  1BR Apartment | 650-720 sq ft | Starting Price
- Use the LOWEST starting price among variants of the same type.
- If only one variant exists for a bedroom count, use exact size
  (no range needed): 1BR Apartment | 650 sq ft | AED 1,100,000

MISSING DATA RULES (ANTI-HALLUCINATION):
- If the PDF contains NO floor plan data at all (no unit types,
  no sizes, no prices) -> write TBA for the entire field.
- If sizes exist but prices do not -> list sizes, write TBA for price:
  1BR Apartment | 650-800 sq ft | TBA
- If prices exist but sizes do not -> list prices, write TBA for size:
  1BR Apartment | TBA | AED 1,100,000
- NEVER fabricate, estimate, or infer sizes or prices.
  The pipeline has NO mechanism to verify invented numbers.
- If the PDF only lists bedroom counts with no size/price detail ->
  list bedroom types only:
  Studio | TBA | TBA
  1BR Apartment | TBA | TBA

Variable count: projects may have 2-8+ distinct floor plans.
Output as many lines as the PDF supports. Do not pad or invent
entries to reach a minimum count.

View All Floor Plans in One Click section - static do not generate

Payment Plan Section
Payment Plan Description (GENERATED):
Use the standardized sentence format:
"Pay X% during construction and X% on handover in QX 20XX, with a X% booking fee."

31) Payment Milestones (EXTRACTED from PDF):
X% -- On Booking
X% -- During Construction
X% -- On Handover (QX 20XX)

Important note on payment plans - SOME project, not all, can have more than one payment plan, so it's important to note this and ensure that these different payment plans are actually mentioned. 

Key points Section (generate)
Two main key points that are unique selling points of the project should be mentioned and expanded here 
Key point 1 title
Key points 1 description
Key point 2 title
Key points 2 description

Amenities Section
Amenities header (static do not generate)
Amenities paragraph (generate) - use a list of the top 3 amenities that differentiate the project as examples and describe an overview of the amenities and what makes the project unique from this perspective in a short 4 sentence paragraph. 
Amenities table (extracted from PDF) 
extract all the amenities from the PDF and mention them all in this section - note that there's a button stating Show all amenities which means this section needs to cover all the amenities that exist for this project. 

Get professional property guidance Section - static block do not generate

Location Section 
[Area Name], [Emirate] (generated)
Location description (generated)

Explore all future developments around this property Section (static do not generate)

Other Projects in [Area Name] (static do not generate)

About the Developer Section 
[Developer Name] - generated
Developer description - generated

Other Projects by [Developer Name] - Static do not generate

FAQ Section 
list of relevant FAQs generated 

All else is static do not generate


