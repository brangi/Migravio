"""
USCIS Forms ingestion script for Migravio RAG pipeline.

Ingests USCIS form instructions and information into Pinecone
for AI-assisted retrieval.

Target forms:
- I-485 (Adjustment of Status)
- I-130 (Petition for Alien Relative)
- I-539 (Change/Extend Nonimmigrant Status)
- I-765 (Employment Authorization)
- I-131 (Travel Document)
- N-400 (Naturalization)

For MVP, uses curated content about each form. Future enhancement
would parse PDF instructions directly.

Usage:
    python scripts/ingest_forms.py [--dry-run] [--forms I-485,I-130]
"""

import argparse
import asyncio
import logging
from typing import Any

from shared import chunk_text, setup_clients, upsert_to_pinecone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Curated form information
# In production, this would be scraped from USCIS website or parsed from PDFs
FORM_DATA = {
    "I-485": {
        "title": "Application to Register Permanent Residence or Adjust Status",
        "description": """
The Form I-485 is used to apply for lawful permanent resident status (green card)
while in the United States. This is known as adjustment of status.

WHO SHOULD FILE:
- Foreign nationals already in the U.S. who are eligible for an immigrant visa
- Immediate relatives of U.S. citizens
- Family-sponsored preference category applicants
- Employment-based preference category applicants
- Diversity Visa lottery winners
- Refugees and asylees seeking to adjust status

ELIGIBILITY REQUIREMENTS:
- Must be physically present in the United States
- Must have an immigrant visa immediately available
- Must be admissible to the United States
- Must not be in removal proceedings (with some exceptions)

REQUIRED DOCUMENTS:
- Form I-485 and all required supplements
- Copy of birth certificate with certified translation
- Copy of passport and visa
- Two passport-style photos
- Form I-693 (Medical Examination)
- Form I-864 (Affidavit of Support) if required
- Evidence of approved immigrant petition (I-140, I-130, etc.)
- Copy of Employment Authorization Document if applicable

FILING FEES (2024):
- Age 14 and over: $1,140 application fee + $85 biometrics = $1,225 total
- Under age 14: $950 application fee + $85 biometrics = $1,035 total
- Fee waivers available for certain applicants

PROCESSING TIME:
- Varies widely by USCIS field office: 8-24 months typical
- Premium processing not available
- Can request expedited processing in emergencies

AFTER FILING:
- Biometrics appointment scheduled (fingerprints, photo)
- Interview may be required at local USCIS office
- Can file I-765 (work permit) and I-131 (travel document) concurrently
- EAD and advance parole typically approved within 3-5 months

COMMON ISSUES:
- RFEs (Requests for Evidence) for missing documents
- Medical exam validity (only valid 60 days when filing I-693 separately)
- Affidavit of Support income requirements
- Inadmissibility issues requiring waivers
""",
        "visa_types": ["Green Card", "EB-1", "EB-2", "EB-3", "H-1B", "L-1", "O-1", "F-1"],
        "form_url": "https://www.uscis.gov/i-485",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-485instr.pdf",
    },
    "I-130": {
        "title": "Petition for Alien Relative",
        "description": """
Form I-130 is used by U.S. citizens and lawful permanent residents to establish
the relationship to certain foreign relatives who wish to immigrate to the United States.

WHO CAN FILE:
- U.S. citizens for: spouse, children, parents, siblings
- Lawful permanent residents (green card holders) for: spouse, unmarried children

IMMEDIATE RELATIVES (No visa wait - U.S. citizens only):
- Spouses of U.S. citizens
- Unmarried children under 21 of U.S. citizens
- Parents of U.S. citizens (petitioner must be 21+)

FAMILY PREFERENCE CATEGORIES (Subject to visa quotas):
- F1: Unmarried sons/daughters (21+) of U.S. citizens
- F2A: Spouses and children of LPRs
- F2B: Unmarried sons/daughters (21+) of LPRs
- F3: Married sons/daughters of U.S. citizens
- F4: Siblings of U.S. citizens (petitioner must be 21+)

REQUIRED DOCUMENTS:
- Proof of petitioner's U.S. citizenship or LPR status
- Proof of relationship (marriage certificate, birth certificate)
- Proof of legal name changes if applicable
- Passport-style photos of petitioner and beneficiary
- If spouse: proof of bona fide marriage, proof of termination of prior marriages

FILING FEES (2024):
- $535 filing fee (no biometrics fee for I-130)
- Fee waivers not available for I-130

PROCESSING TIME:
- USCIS processing: 10-24 months depending on service center
- Total time to green card depends on category and country of birth
- Immediate relatives: typically 12-18 months total
- Preference categories: can be several years due to visa backlogs

AFTER APPROVAL:
- Case forwarded to National Visa Center (NVC)
- Beneficiary completes DS-260 and submits civil documents
- Attend visa interview at U.S. embassy/consulate abroad OR
- File I-485 if beneficiary is in U.S. and visa is available

PRIORITY DATE:
- Filing date of I-130 becomes priority date
- Determines place in line for preference categories
- Track visa bulletin monthly to see when visa becomes available

COMMON ISSUES:
- Insufficient evidence of relationship
- Prior marriage termination documents missing
- Name discrepancies between documents
- Fraud concerns requiring waiver (I-601)
""",
        "visa_types": ["Green Card"],
        "form_url": "https://www.uscis.gov/i-130",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-130instr.pdf",
    },
    "I-539": {
        "title": "Application to Extend/Change Nonimmigrant Status",
        "description": """
Form I-539 is used to apply for an extension of stay or change to another
nonimmigrant status while in the United States.

EXTENSION OF STAY - Who can extend:
- B-1/B-2 visitors
- F-1 students (in limited circumstances)
- H-4 dependents of H-1B workers
- L-2 dependents of L-1 workers
- O-2/O-3 dependents
- Many other nonimmigrant categories

CHANGE OF STATUS - Common scenarios:
- B-2 visitor changing to F-1 student
- H-4 dependent changing to F-1 student
- F-1 student changing to H-1B worker (typically done with H-1B petition)
- L-2 dependent changing to H-1B worker

WHO SHOULD NOT USE THIS FORM:
- H-1B, L-1, O-1, P-1 principal workers (use employer petition instead)
- J-1 exchange visitors (different process)
- Individuals in removal proceedings

FILING REQUIREMENTS:
- Must file before current status expires
- Must have maintained status
- Must not have engaged in unauthorized employment
- Must show ties to home country and intent to depart

REQUIRED DOCUMENTS:
- Copy of I-94 arrival/departure record
- Copy of passport biographical page
- Copy of visa
- Evidence of financial support
- Explanation of reason for extension/change
- If dependent: copy of principal's status documents

FILING FEES (2024):
- $370 filing fee + $85 biometrics fee = $455 total
- Add $85 biometrics for each dependent included

PROCESSING TIME:
- 6-10 months typical
- Premium processing NOT available for I-539
- Can request expedited processing for emergencies

BRIDGE PERIOD:
- If timely filed, can remain in U.S. while pending (for up to 240 days)
- Cannot work unless separately authorized
- Departure while pending abandons application

COMMON PITFALLS:
- Filing after status expires (must show extraordinary circumstances)
- Insufficient explanation of need for extension
- Gaps in maintaining status
- Unauthorized employment terminates status
- Not including all dependents who need same benefit

AFTER APPROVAL:
- Receive I-797 approval notice
- New I-94 reflects extended period
- If changed status, new classification begins on approval date
""",
        "visa_types": ["H-4", "L-2", "F-1", "B-1/B-2"],
        "form_url": "https://www.uscis.gov/i-539",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-539instr.pdf",
    },
    "I-765": {
        "title": "Application for Employment Authorization",
        "description": """
Form I-765 is used to apply for an Employment Authorization Document (EAD),
also known as a work permit, which allows certain foreign nationals to work
in the United States.

WHO CAN APPLY:
- Pending adjustment of status (I-485) applicants
- F-1 students applying for OPT or STEM OPT
- H-4 spouses of H-1B workers (if H-1B has approved I-140)
- L-2 spouses of L-1 workers
- Asylum applicants (pending 150 days)
- Asylees and refugees
- DACA recipients
- Temporary Protected Status (TPS) beneficiaries
- Many other categories

ELIGIBILITY CATEGORIES:
Form I-765 has over 70 eligibility categories. Most common:
- (c)(3)(C) - H-4 dependent spouse
- (c)(5) - F-1 OPT
- (c)(9) - Pending adjustment of status
- (c)(10) - Asylum applicant (pending 150+ days)
- (c)(26) - H-4 spouse of H-1B with approved I-140
- (c)(33) - DACA

F-1 OPT REQUIREMENTS:
- Must have been in F-1 status for at least one academic year
- Apply within 90 days before and 60 days after program completion
- EAD valid for 12 months
- STEM extension available for additional 24 months

CONCURRENT FILING WITH I-485:
- Can file I-765 together with I-485 adjustment application
- Free filing fee when filed with I-485
- Typically approved within 3-5 months
- Provides work authorization while green card pending

REQUIRED DOCUMENTS:
- Copy of passport and visa
- Copy of I-94 arrival/departure record
- Two passport-style photos
- Copy of I-20 (for F-1 students)
- Copy of approval notice for underlying petition if applicable
- Evidence of qualifying relationship or status

FILING FEES (2024):
- $410 filing fee + $85 biometrics = $495 total
- NO FEE when filing with I-485
- Fee waivers available for certain categories

PROCESSING TIME:
- Concurrent I-485 filers: 3-5 months
- F-1 OPT: 3-5 months (apply early!)
- H-4 EAD: 4-8 months
- Asylum-based: 3-6 months

RENEWAL:
- Can apply up to 180 days before expiration
- Timely filed renewal extends work authorization up to 180 days
- Critical for I-485 pending and other long-term categories

AUTOMATIC EXTENSIONS:
- I-485 pending EAD: 180-day automatic extension if timely renewed
- H-4 EAD: 180-day automatic extension if timely renewed
- Check USCIS automatic extension rules for your category

COMMON ISSUES:
- Photos don't meet specifications
- Wrong eligibility category selected
- Missing supporting documentation
- Application filed too early (F-1 OPT)
- Unauthorized employment terminates status
""",
        "visa_types": ["H-4", "F-1", "OPT", "Green Card", "L-2"],
        "form_url": "https://www.uscis.gov/i-765",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-765instr.pdf",
    },
    "I-131": {
        "title": "Application for Travel Document",
        "description": """
Form I-131 is used to apply for a travel document that allows certain
individuals to return to the United States after traveling abroad.

DOCUMENT TYPES:

1. ADVANCE PAROLE - For those with pending applications:
   - Pending I-485 adjustment of status
   - TPS beneficiaries
   - Pending asylum applications
   - DACA recipients

2. REFUGEE TRAVEL DOCUMENT - For:
   - Refugees
   - Asylees
   - Cannot use home country passport

3. RE-ENTRY PERMIT - For green card holders:
   - Planning to be outside U.S. for 1-2 years
   - Preserves permanent resident status
   - Valid for 2 years

ADVANCE PAROLE - KEY POINTS:
- Allows re-entry after temporary travel abroad
- Does not guarantee admission (CBP officer decides)
- Critical for I-485 pending applicants
- Traveling without advance parole can abandon I-485

H-1B/L-1 DUAL INTENT:
- H-1B and L-1 workers can travel on their visa instead
- Don't need advance parole if valid H-1B/L-1 visa
- Safer to have both in case of visa issues

F-1 STUDENTS - DANGER:
- Advance parole terminates F-1 status
- F-1 students should travel on F-1 visa instead
- Only use advance parole if you're leaving F-1 status

CONCURRENT FILING WITH I-485:
- Can file I-131 together with I-485
- Free filing fee when filed with I-485
- Typically approved within 3-5 months
- Combo card (EAD/AP) issued together with I-765

FILING REQUIREMENTS:
- Must be physically in U.S. when filing
- Two passport-style photos
- Copy of passport biographical page
- Copy of I-94 and current visa
- Evidence of pending application or status
- Explanation of reason for travel

FILING FEES (2024):
- Advance Parole: $575
- Refugee Travel Document: $135
- Re-entry Permit: $615
- NO FEE when filing with I-485

PROCESSING TIME:
- Concurrent I-485 filing: 3-5 months
- Standalone filing: 4-8 months
- Expedited processing available for emergencies

VALIDITY PERIOD:
- Advance Parole: typically valid for 1 year
- Can request multiple entries
- Renewable while I-485 pending

USING ADVANCE PAROLE:
- Present document to CBP at port of entry
- Officer will inspect and decide on admission
- Maintain ties to U.S. and evidence of intent to return
- Keep copies of I-485 receipt and all documents

RISKS AND CONSIDERATIONS:
- Traveling with advance parole while inadmissible can trigger bar
- Unlawful presence issues can be triggered at consulate
- Certain bars (3/10 year) apply if you accrued unlawful presence
- Consult attorney before traveling if any immigration violations

RE-ENTRY PERMIT FOR GREEN CARD HOLDERS:
- Allows absence of up to 2 years
- Must apply before leaving U.S.
- Can complete biometrics abroad at consulate
- Protects against abandonment of permanent residence

COMMON MISTAKES:
- Leaving U.S. before approval (abandons application)
- F-1 students using advance parole (terminates F-1)
- Not understanding inadmissibility risks
- Traveling with expired advance parole
- Assuming advance parole guarantees admission
""",
        "visa_types": ["Green Card", "F-1", "H-1B", "L-1"],
        "form_url": "https://www.uscis.gov/i-131",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-131instr.pdf",
    },
    "N-400": {
        "title": "Application for Naturalization",
        "description": """
Form N-400 is used to apply for U.S. citizenship through naturalization.

GENERAL ELIGIBILITY:
- Must be 18 or older
- Lawful permanent resident (green card holder)
- Required continuous residence and physical presence
- Good moral character
- English and civics knowledge (with some exceptions)
- Attachment to U.S. Constitution

CONTINUOUS RESIDENCE REQUIREMENTS:

5-YEAR RULE (Most common):
- 5 years as permanent resident
- Continuous residence for 5 years
- Physical presence in U.S. for at least 30 months (half of 5 years)
- At least 3 months residence in USCIS district

3-YEAR RULE (Spouse of U.S. citizen):
- 3 years as permanent resident
- Married to and living with same U.S. citizen for 3 years
- Physical presence for at least 18 months (half of 3 years)

OTHER ELIGIBILITY PATHS:
- Military service members (expedited, fee waiver)
- Spouses of U.S. citizens employed abroad
- Certain employees of U.S. government abroad

CONTINUOUS RESIDENCE - TRIPS ABROAD:
- Trips less than 6 months: generally OK
- Trips 6 months to 1 year: may break continuous residence (rebuttable)
- Trips over 1 year: breaks continuous residence (unless N-470 filed)

GOOD MORAL CHARACTER:
Must not have:
- Criminal convictions (varies by severity)
- Lied to obtain immigration benefits
- Failed to pay taxes
- Failed to register for Selective Service (males 18-26)
- Committed adultery (if affected family)
- Habitual drunkenness

ENGLISH AND CIVICS TEST:
- Must demonstrate ability to read, write, and speak English
- Must pass civics test (U.S. history and government)
- 100 possible questions, asked 10, must answer 6 correctly

EXEMPTIONS FROM ENGLISH TEST:
- Age 50+ with 20 years as LPR
- Age 55+ with 15 years as LPR
- Medical disability (form N-648 required)

REQUIRED DOCUMENTS:
- Copy of green card (front and back)
- Passport-style photos (2)
- Copy of marriage certificate if applicable
- Divorce decrees for prior marriages
- Selective Service registration if male 18-26
- Tax returns for past 5 years (or 3 if married to USC)
- Evidence of any court dispositions or criminal history

FILING FEES (2024):
- $710 filing fee + $85 biometrics = $795 total
- Fee waivers available for income-qualified applicants
- Military members: no fee

PROCESSING TIME:
- 10-18 months typical
- Varies by USCIS field office
- Can track case online

NATURALIZATION PROCESS:
1. File N-400
2. Biometrics appointment
3. Interview and test (English and civics)
4. Decision (approved, continued, or denied)
5. Oath ceremony (typically 2-6 weeks after approval)

INTERVIEW:
- Under oath
- Questions about N-400 application
- Review of supporting documents
- English test (reading, writing, speaking)
- Civics test
- Bring all requested documents

OATH CEREMONY:
- Final step to become U.S. citizen
- Recite Oath of Allegiance
- Receive Certificate of Naturalization
- Must surrender green card

BENEFITS OF CITIZENSHIP:
- Right to vote
- U.S. passport (visa-free travel to many countries)
- Cannot be deported
- Petition family members (including parents and siblings)
- Qualify for federal jobs
- Run for public office (except President)

COMMON ISSUES:
- Underestimating time spent abroad
- Failing to disclose arrests or citations
- Tax compliance issues
- Selective Service registration issues
- Criminal history (even expunged)
- Lying on N-400 can lead to denial and green card revocation
""",
        "visa_types": ["Green Card", "Naturalization"],
        "form_url": "https://www.uscis.gov/n-400",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/n-400instr.pdf",
    },
}


async def ingest_forms(
    forms: list[str] | None = None,
    dry_run: bool = False,
):
    """
    Main ingestion function for USCIS forms.

    Args:
        forms: List of form names to ingest (e.g., ['I-485', 'I-130'])
        dry_run: If True, skip actual API calls
    """
    if forms is None:
        forms = list(FORM_DATA.keys())

    # Validate form names
    invalid_forms = [f for f in forms if f not in FORM_DATA]
    if invalid_forms:
        logger.error(f"Invalid form names: {invalid_forms}")
        logger.error(f"Valid forms: {list(FORM_DATA.keys())}")
        return

    logger.info(f"Starting USCIS forms ingestion for: {forms}")
    logger.info(f"Dry run: {dry_run}")

    # Initialize clients
    clients = await setup_clients()

    all_chunks = []
    all_metadata = []

    for form_name in forms:
        form_info = FORM_DATA[form_name]
        logger.info(f"\nProcessing Form {form_name}: {form_info['title']}")

        # Combine title and description for full content
        full_content = f"{form_info['title']}\n\n{form_info['description']}"

        # Chunk the content
        chunks = chunk_text(full_content, chunk_size=512, overlap=50)
        logger.info(f"  Created {len(chunks)} chunks")

        # Create metadata for each chunk
        for chunk_idx, chunk in enumerate(chunks):
            metadata = {
                "source": f"form_{form_name.lower().replace('-', '_')}",
                "document_title": f"Form {form_name}: {form_info['title']}",
                "form_name": form_name,
                "form_url": form_info["form_url"],
                "instructions_url": form_info["instructions_url"],
                "visa_types": form_info["visa_types"],
                "chunk_index": chunk_idx,
                "section": f"form_{form_name.lower()}_{chunk_idx}",
            }

            all_chunks.append(chunk)
            all_metadata.append(metadata)

    # Upsert to Pinecone
    if all_chunks:
        logger.info(f"\nPrepared {len(all_chunks)} total chunks for ingestion")

        vectors_upserted = await upsert_to_pinecone(
            clients.index,
            all_chunks,
            all_metadata,
            source="uscis_forms",
            dry_run=dry_run,
        )

        logger.info(f"✓ Successfully processed {vectors_upserted} vectors")
    else:
        logger.warning("No chunks to ingest")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest USCIS form information into Pinecone for RAG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without calling APIs",
    )
    parser.add_argument(
        "--forms",
        type=str,
        help="Comma-separated list of forms to ingest (e.g., 'I-485,I-130')",
    )

    args = parser.parse_args()

    forms = None
    if args.forms:
        forms = [f.strip() for f in args.forms.split(",")]

    asyncio.run(ingest_forms(forms=forms, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
