"""
Prevailing Wage and DOL Requirements ingestion script for Migravio RAG pipeline.

Ingests comprehensive information about prevailing wage determination,
LCA requirements, PERM labor certification, wage levels, and occupation-specific
wage data into Pinecone for AI-assisted retrieval.

Topics covered:
- Prevailing wage system overview (4 wage levels)
- H-1B LCA requirements
- PERM labor certification process
- Top H-1B occupation wage ranges
- Geographic wage variations

Usage:
    python scripts/ingest_prevailing_wages.py [--dry-run]
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Add scripts directory to path for shared module import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared import chunk_text, setup_clients, upsert_to_pinecone

# Load environment variables from ai-service directory
ENV_PATH = SCRIPT_DIR.parent / "apps" / "ai-service" / ".env"
load_dotenv(ENV_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Curated prevailing wage and DOL information
DOL_WAGE_DATA = {
    "prevailing-wage-overview": {
        "title": "Prevailing Wage System Overview",
        "description": """
The prevailing wage is the average wage paid to similarly employed workers
in a specific occupation in the area of intended employment. It is a critical
requirement for H-1B, PERM, and other employment-based immigration petitions.

FOUR WAGE LEVELS:

Level I (Entry Level) - 17th percentile:
- Entry-level position
- Limited understanding of occupation
- Close supervision and training required
- Limited or no judgment exercised
- Closely follow established procedures
- Example: Recent college graduate, 0-2 years experience

Level II (Qualified) - 34th percentile:
- Moderate understanding of occupation
- Limited judgment required
- Some supervision still needed
- Deviation from procedures requires supervisor approval
- Example: 2-4 years experience in field

Level III (Experienced) - 50th percentile:
- Sound understanding of occupation
- Exercise judgment in performance of tasks
- General supervision provided
- May plan and lead work of others
- Example: 4-7 years experience, senior-level position

Level IV (Fully Competent) - 67th percentile:
- Thorough understanding of occupation
- Wide latitude for independent judgment
- Minimal supervision
- Plan, design, and implement complex projects
- Example: 7+ years experience, expert-level position

HOW WAGE LEVEL IS DETERMINED:

For H-1B LCA:
- Employer selects appropriate wage level based on job requirements
- Must match actual job duties and requirements
- DOL Online Wage Library provides wage data by SOC code and location
- Must pay higher of actual wage or prevailing wage

For PERM:
- DOL determines wage level based on SVP (Specific Vocational Preparation)
- SVP maps job requirements to wage levels
- Based on education, experience, and special skills required
- Employer cannot simply choose lower level

PREVAILING WAGE DETERMINATION SOURCES:

1. Online Wage Library (OWL):
   - Primary source for H-1B LCA
   - Based on OES (Occupational Employment Statistics)
   - Updated annually by DOL
   - Available at flcdatacenter.com

2. Prevailing Wage Determination (PWD):
   - Required for PERM cases
   - DOL's National Prevailing Wage Center (NPWC) issues determination
   - Form ETA-9141 filed 6+ months before PERM
   - Valid for 1 year from determination date
   - Processing time: 2-4 months typical

3. Alternative Wage Sources (rarely used):
   - Independent authoritative source
   - Employer-conducted survey
   - Collective bargaining agreement

ACTUAL WAGE REQUIREMENT:
Employer must pay the HIGHER of:
- Prevailing wage for occupation and location
- Actual wage paid to similarly employed workers at employer

Actual wage = wage paid to employees with similar:
- Experience
- Qualifications
- Responsibilities
- Location

GEOGRAPHIC VARIATIONS:
Prevailing wages vary significantly by metropolitan area:
- San Francisco Bay Area: 30-50% above national average
- New York City: 30-45% above national average
- Seattle: 25-40% above national average
- Boston: 20-35% above national average
- Midwest/South: typically at or below national average

WAGE OBLIGATION DURATION:

H-1B:
- Entire period of H-1B employment
- Must maintain wage even during non-productive periods
- Exceptions: unpaid leave, bona fide termination
- Benching not allowed (must pay prevailing wage)

PERM:
- From priority date (PERM filing) through green card issuance
- Must demonstrate ability to pay from priority date onward
- Actual wage paid shown on tax returns, W-2s

PENALTIES FOR VIOLATIONS:
- Back wages owed to employee
- Civil fines up to $35,000 per violation
- Debarment from H-1B program (1-3 years)
- PERM denial
- Criminal penalties for willful violations

COMMON PITFALLS:
- Selecting too low wage level for actual job duties
- Not paying prevailing wage during non-productive periods
- Wage level doesn't match job requirements on LCA/PERM
- Failing to pay required wage when employee on bench
- Not updating wage when employee relocates to higher-wage area
""",
        "visa_types": ["H-1B", "EB-2", "EB-3", "L-1"],
    },
    "h1b-lca-requirements": {
        "title": "H-1B Labor Condition Application (LCA) Requirements",
        "description": """
The Labor Condition Application (LCA) is required for all H-1B petitions.
It is an attestation by the employer that certain conditions will be met
regarding wages and working conditions for the H-1B worker.

WHAT IS THE LCA?

The LCA is Form ETA-9035/9035E filed electronically with the Department of
Labor before filing the H-1B petition with USCIS. It certifies that the
employer will:
1. Pay required wage (higher of prevailing or actual wage)
2. Provide working conditions that won't adversely affect U.S. workers
3. No strike or lockout at place of employment
4. Notice provided to bargaining representative or workers

FOUR ATTESTATIONS:

Attestation 1 - Wages:
- Will pay H-1B worker required wage (higher of prevailing or actual)
- Required wage paid from first day of work
- Paid for non-productive time (bench time)
- Deductions cannot reduce below required wage (except legally required)

Attestation 2 - Working Conditions:
- H-1B employment won't adversely affect working conditions of U.S. workers
- Benefits provided equally to H-1B and U.S. workers
- H-1B worker not used to break strike or lockout

Attestation 3 - Strike/Lockout:
- No strike or lockout in occupation at place of employment
- If strike/lockout occurs, LCA must be withdrawn

Attestation 4 - Notice:
- Notice of filing provided to workers
- Posted at worksite for 10 business days
- Notice to bargaining representative if applicable
- Electronic notice acceptable if employees have access

LCA FILING PROCESS:
1. Employer completes Form ETA-9035E electronically
2. File through DOL's FLAG system (iCERT)
3. DOL review: typically 7-10 business days
4. Certified LCA valid for up to 3 years
5. Use certified LCA to file H-1B petition with USCIS

LCA REQUIRED INFORMATION:
- Employer name, address, EIN
- Job title and SOC code
- Prevailing wage and wage level
- Actual wage to be paid
- Work location (specific address)
- Period of employment
- Full-time vs. part-time status

WAGE SOURCES FOR LCA:
- DOL Online Wage Library (most common)
- Prevailing Wage Determination from NPWC
- Independent authoritative source
- Employer-conducted survey (rare)

POSTING REQUIREMENTS:
- Post LCA notice at each worksite
- 10 consecutive business days (excluding weekends/holidays)
- Before filing LCA or within 30 days of filing
- Physical posting OR electronic (if employees have access)
- Must be in conspicuous location

NOTICE CONTENT:
- Employer name and contact
- H-1B worker's occupation and wage
- Period of employment
- Location of employment
- Statement that LCA available for public inspection
- Statement about complaints to DOL

PUBLIC ACCESS FILE (PAF):
Employer must maintain file with:
- Certified LCA
- Wage determination documentation
- Actual wage documentation (payroll records)
- Notice posting documentation
- H-1B worker list
- Available for public inspection and DOL audit

LCA VALIDITY PERIOD:
- Certified LCA valid for period specified (up to 3 years)
- Can use for multiple H-1B petitions during validity
- Must file new LCA if:
  * Validity period expires
  * Material change in employment terms
  * Work location changes to new metropolitan area

WORKSITE CHANGES:
- New LCA required if H-1B worker relocates to new metro area
- Short-term placement (30 days or less): no new LCA if non-worksite location
- Short-term placement (31-60 days): posting at new location required
- Long-term or permanent: new LCA and amended H-1B petition required

AMENDED H-1B PETITION REQUIRED:
- Material change in employment terms
- Change in work location (different metro area)
- Change in job duties
- Significant change in wage

LCA VIOLATIONS AND PENALTIES:
- Back wages owed to H-1B worker
- Civil fines: $1,000 to $35,000 per violation
- Debarment from H-1B program: 1-3 years (or permanent for willful violations)
- DOL investigation triggers

H-1B DEPENDENT EMPLOYERS:
Additional attestations required if:
- 15% or more of workforce is H-1B (for companies with 26-50 employees)
- 30 or more H-1B workers (for companies with 51+ employees)

Additional attestations:
- Will not displace U.S. workers 90 days before/after H-1B filing
- Attempted to recruit U.S. workers
- H-1B worker will not be placed at another employer's worksite
- Exempt if H-1B worker paid $60,000+ or has master's degree + $60,000+

COMMON LCA MISTAKES:
- Wrong SOC code selected (affects prevailing wage)
- Wage level too low for actual job requirements
- Missing or improper posting of notice
- Public Access File incomplete or not maintained
- Not filing amended petition for material changes
- Benching H-1B worker without pay
- Deductions reducing wage below required amount
""",
        "visa_types": ["H-1B"],
    },
    "perm-labor-certification": {
        "title": "PERM Labor Certification Process",
        "description": """
The PERM (Program Electronic Review Management) labor certification is
required for most employment-based green cards (EB-2 and EB-3). It is a
process to test the U.S. labor market to ensure no qualified U.S. workers
are available for the position before sponsoring a foreign worker.

WHAT IS PERM?

PERM is the labor certification process where employers:
1. Prove there are no qualified U.S. workers for the position
2. Demonstrate they are paying the prevailing wage
3. Conduct supervised recruitment per DOL requirements
4. File electronic application (ETA-9089) with DOL

WHEN IS PERM REQUIRED?

Required for:
- EB-2 (except NIW - National Interest Waiver)
- EB-3 (all categories)

NOT required for:
- EB-1 (all categories)
- EB-2 NIW (National Interest Waiver)
- Special Immigrant categories

PERM PROCESS TIMELINE:
Total timeline: 1.5-3 years typical (PERM through I-485)

1. Prevailing Wage Determination (PWD): 2-4 months
2. Recruitment period: 2-4 months
3. PERM filing and processing: 6-12 months
4. I-140 petition: 6-12 months (or 15 days with premium)
5. I-485 adjustment: 8-24 months (if priority date current)

STEP-BY-STEP PROCESS:

Step 1 - Prevailing Wage Determination (Optional but Recommended):
- File Form ETA-9141 with NPWC (National Prevailing Wage Center)
- DOL determines prevailing wage for occupation and location
- Processing: 2-4 months
- Valid for 1 year from determination date
- Recommended to lock in wage before recruitment

Step 2 - Job Description and Requirements:
- Define actual minimum requirements for position
- Requirements must be normal for occupation
- Cannot be tailored to foreign worker (no "purple squirrel" jobs)
- Education, experience, skills, licenses
- No foreign language unless business necessity

Step 3 - Mandatory Recruitment Steps:

For Professional Positions:
- Job order with State Workforce Agency (SWA) - 30 days
- Two Sunday newspaper advertisements (30 days apart)
- 30-day internal posting (notice to employees)
- Three additional recruitment sources from list of 10:
  * Employer's website (30 days)
  * Job search website (30 days)
  * Trade/professional publication
  * On-campus recruiting
  * Campus placement office
  * Employee referral program
  * Local and ethnic newspaper
  * Radio/TV advertising
  * Job fair
  * Private employment firm

For Non-Professional Positions:
- Job order with SWA (30 days)
- Two print advertisements
- Additional recruitment steps may be required

Step 4 - Document Recruitment Results:
- Collect and review all applications
- Document why each U.S. applicant was rejected
- Lawful job-related reasons only (overqualified, underqualified, etc.)
- Create recruitment report
- Retain all documentation for 5 years

Step 5 - File PERM Application (Form ETA-9089):
- Electronic filing through DOL's FLAG system
- Must file within 180 days of completing recruitment
- Signed by employer and attorney
- Includes all recruitment documentation
- Priority date = filing date

PERM PROCESSING:

Regular Processing:
- DOL reviews application electronically
- 6-12 months typical processing
- Three possible outcomes:
  * Certified (approved)
  * Denied
  * Audit (20-30% of cases)

Audit:
- DOL requests supporting documentation
- 30 days to respond
- May request:
  * Recruitment documentation
  * Business necessity documentation
  * Prevailing wage determination
  * Employer's ability to pay
- Audit response processing: 6-12+ months additional

COMMON AUDIT TRIGGERS:
- Job requirements appear tailored to foreign worker
- Employer hired foreign worker during recruitment
- High wage offered compared to prevailing wage
- Random selection (DOL audits 20-30% randomly)

EMPLOYER ABILITY TO PAY:
Employer must prove ability to pay prevailing wage from priority date:
- Tax returns showing net income or net current assets
- Audited financial statements
- Annual reports
- W-2s showing actual wage paid

Timing:
- Ability to pay assessed from priority date onward
- Even if green card not approved for years
- Employer business changes can affect ability to pay

JOB REQUIREMENTS - DOS AND DON'TS:

DO:
- Use normal requirements for occupation
- Justify all requirements with business necessity
- Be consistent with actual job duties
- Match requirements to what's truly needed

DON'T:
- Require foreign language unless business necessity
- Require experience in combination of rare skills
- Set education requirements higher than industry norm
- Require experience with employer's proprietary systems
- Tailor requirements to foreign worker's exact background

PERM DENIAL REASONS:
- Job requirements not normal for occupation
- Insufficient recruitment conducted
- Failed to document lawful reason for rejecting U.S. workers
- Business necessity not proven
- Prevailing wage not met
- Employer not bona fide

AFTER PERM APPROVAL:
- Valid indefinitely (does not expire)
- File Form I-140 with USCIS
- Priority date = PERM filing date
- If I-140 approved, maintain priority date even if change employers (porting)

SUBSTITUTION OF BENEFICIARIES:
- Not allowed since 2007
- Each PERM for specific foreign worker only
- Cannot transfer approved PERM to different employee

PERM AMENDMENTS:
- Cannot amend PERM after filing
- Material errors require withdrawal and re-filing
- Recruitment must be re-done if re-filing

COMMON PITFALLS:
- Job requirements tailored to foreign worker
- Incomplete recruitment documentation
- Rejecting U.S. workers for unlawful reasons
- Missing 180-day filing deadline after recruitment
- Employer cannot prove ability to pay
- Hiring foreign worker during recruitment period
- Not retaining recruitment documentation for 5 years
""",
        "visa_types": ["EB-2", "EB-3"],
    },
    "top-h1b-occupations": {
        "title": "Top H-1B Occupations and Prevailing Wage Ranges",
        "description": """
The following are the most common H-1B occupations with approximate national
prevailing wage ranges for 2025-2026. Actual prevailing wages vary significantly
by geographic location and specific metropolitan area.

NOTE: Wages shown are national ranges across all four wage levels.
Employers must pay the HIGHER of actual wage or prevailing wage for the
specific location and wage level.

SOFTWARE DEVELOPERS (SOC 15-1252):
- Level I (Entry): $85,000 - $110,000
- Level II (Qualified): $100,000 - $130,000
- Level III (Experienced): $120,000 - $150,000
- Level IV (Fully Competent): $145,000 - $170,000+

Common specialties:
- Software Developers, Applications
- Software Developers, Systems Software
- Full Stack Developers
- Mobile Application Developers

COMPUTER SYSTEMS ANALYSTS (SOC 15-1211):
- Level I (Entry): $75,000 - $95,000
- Level II (Qualified): $90,000 - $115,000
- Level III (Experienced): $110,000 - $135,000
- Level IV (Fully Competent): $130,000 - $150,000+

Typical roles:
- Business Systems Analyst
- IT Analyst
- Technical Analyst
- Systems Analyst

FINANCIAL ANALYSTS (SOC 13-2051):
- Level I (Entry): $70,000 - $90,000
- Level II (Qualified): $85,000 - $105,000
- Level III (Experienced): $100,000 - $120,000
- Level IV (Fully Competent): $120,000 - $140,000+

Common positions:
- Financial Analyst
- Investment Analyst
- Budget Analyst
- Credit Analyst

MANAGEMENT ANALYSTS (SOC 13-1111):
- Level I (Entry): $75,000 - $100,000
- Level II (Qualified): $95,000 - $120,000
- Level III (Experienced): $115,000 - $140,000
- Level IV (Fully Competent): $135,000 - $155,000+

Also known as:
- Business Consultant
- Management Consultant
- Strategy Consultant
- Operations Analyst

MECHANICAL ENGINEERS (SOC 17-2141):
- Level I (Entry): $70,000 - $85,000
- Level II (Qualified): $80,000 - $100,000
- Level III (Experienced): $95,000 - $115,000
- Level IV (Fully Competent): $110,000 - $130,000+

Engineering fields:
- Product Design Engineer
- Manufacturing Engineer
- R&D Engineer
- CAD Engineer

ACCOUNTANTS AND AUDITORS (SOC 13-2011):
- Level I (Entry): $60,000 - $75,000
- Level II (Qualified): $70,000 - $90,000
- Level III (Experienced): $85,000 - $105,000
- Level IV (Fully Competent): $100,000 - $120,000+

Common roles:
- Staff Accountant
- Senior Accountant
- Internal Auditor
- Tax Accountant

ELECTRICAL ENGINEERS (SOC 17-2071):
- Level I (Entry): $75,000 - $90,000
- Level II (Qualified): $90,000 - $110,000
- Level III (Experienced): $105,000 - $130,000
- Level IV (Fully Competent): $125,000 - $145,000+

Specializations:
- Electronics Engineer
- Hardware Engineer
- Power Systems Engineer
- Test Engineer

DATABASE ADMINISTRATORS (SOC 15-1242):
- Level I (Entry): $70,000 - $90,000
- Level II (Qualified): $90,000 - $110,000
- Level III (Experienced): $105,000 - $125,000
- Level IV (Fully Competent): $120,000 - $140,000+

Database roles:
- Database Administrator (DBA)
- Database Architect
- SQL Developer
- NoSQL Administrator

COMPUTER PROGRAMMERS (SOC 15-1251):
- Level I (Entry): $75,000 - $95,000
- Level II (Qualified): $90,000 - $115,000
- Level III (Experienced): $110,000 - $135,000
- Level IV (Fully Competent): $130,000 - $155,000+

Programming roles:
- Application Programmer
- Systems Programmer
- Web Developer
- API Developer

NETWORK AND COMPUTER SYSTEMS ADMINISTRATORS (SOC 15-1244):
- Level I (Entry): $65,000 - $85,000
- Level II (Qualified): $80,000 - $100,000
- Level III (Experienced): $95,000 - $115,000
- Level IV (Fully Competent): $110,000 - $130,000+

IT infrastructure:
- Network Administrator
- Systems Administrator
- Cloud Administrator
- DevOps Engineer

IMPORTANT NOTES ON WAGE VARIATIONS:

Geographic Variations:
- San Francisco Bay Area: 30-50% higher than national average
  * Software Developer Level II: $130,000-$170,000
- New York City: 30-45% higher
  * Software Developer Level II: $125,000-$165,000
- Seattle: 25-40% higher
  * Software Developer Level II: $120,000-$160,000
- Boston: 20-35% higher
  * Software Developer Level II: $115,000-$150,000
- Midwest/South: at or below national average
  * Software Developer Level II: $85,000-$115,000

Company Size Impact:
- Large tech companies (FAANG): often Level III or IV wages
- Startups: typically Level I or II wages
- Consulting firms: varies widely by client billing rate
- Universities: often lower than industry (but cap-exempt)

DETERMINING CORRECT WAGE LEVEL:
- Must match actual job requirements and responsibilities
- Cannot artificially select lower level to save costs
- DOL may audit wage level determination
- Under-leveling can result in:
  * LCA or PERM denial
  * Back wages owed
  * Debarment from H-1B program

HOW TO CHECK PREVAILING WAGES:
- DOL Online Wage Library: flcdatacenter.com
- Enter SOC code and work location zip code
- Review all four wage levels
- Select level matching job requirements
- Employer must pay higher of prevailing or actual wage
""",
        "visa_types": ["H-1B", "EB-2", "EB-3"],
    },
    "geographic-wage-variations": {
        "title": "Geographic Wage Variations and Metro Area Context",
        "description": """
Prevailing wages vary significantly by geographic location. The same job
title and requirements can have vastly different prevailing wages depending
on the metropolitan statistical area (MSA) where the work is performed.

HIGHEST-PAYING METRO AREAS (2025-2026):

San Francisco Bay Area (San Jose-Sunnyvale-Santa Clara, CA):
- Software Developers: 40-50% above national average
- Reasons: high cost of living, competitive tech market, concentration of tech companies
- Example: Software Developer Level II
  * National: ~$115,000
  * San Francisco: ~$160,000-$170,000

New York City (New York-Newark-Jersey City, NY-NJ-PA):
- Financial Analysts, Software Developers: 30-45% above national
- Reasons: financial services hub, high cost of living, competitive market
- Example: Financial Analyst Level II
  * National: ~$95,000
  * New York: ~$125,000-$135,000

Seattle-Tacoma-Bellevue, WA:
- Software Developers, Computer Systems Analysts: 25-40% above national
- Reasons: major tech employers (Amazon, Microsoft), growing tech ecosystem
- Example: Software Developer Level II
  * National: ~$115,000
  * Seattle: ~$145,000-$155,000

Boston-Cambridge-Newton, MA-NH:
- Engineers, Software Developers: 20-35% above national
- Reasons: biotech hub, universities, tech companies, high cost of living
- Example: Software Developer Level II
  * National: ~$115,000
  * Boston: ~$135,000-$145,000

Washington-Arlington-Alexandria, DC-VA-MD-WV:
- Management Analysts, IT Consultants: 20-30% above national
- Reasons: federal government contractors, consulting firms, high cost of living
- Example: Management Analyst Level II
  * National: ~$105,000
  * Washington DC: ~$125,000-$135,000

Los Angeles-Long Beach-Anaheim, CA:
- Entertainment industry, Software Developers: 15-30% above national
- Example: Software Developer Level II
  * National: ~$115,000
  * Los Angeles: ~$130,000-$145,000

MODERATE-WAGE METRO AREAS:

Austin-Round Rock, TX:
- Software Developers: 10-20% above national
- Growing tech hub with lower cost of living than coastal cities

Denver-Aurora-Lakewood, CO:
- Various occupations: 5-15% above national
- Balanced market with moderate cost of living

Chicago-Naperville-Elgin, IL-IN-WI:
- Financial services, consulting: 5-15% above national
- Major metro with moderate wage premium

LOWER-WAGE REGIONS:

Midwest and South (generally):
- Many metro areas: at or below national average
- Examples: Indianapolis, Columbus, Charlotte, Atlanta
- Software Developer Level II: $85,000-$110,000
- Lower cost of living, less competitive tech markets

Rural and Smaller Metro Areas:
- Often 10-25% below national average
- Fewer employers competing for talent
- Lower cost of living

WORK LOCATION RULES:

LCA Work Location:
- Must specify actual work address on LCA
- Prevailing wage based on MSA containing work location
- If work in multiple locations, may need multiple LCAs

Worksite Changes:
- New LCA required if moving to different MSA
- Same MSA: generally no new LCA needed
- Short-term placements (30 days or less): special rules apply

Remote Work Considerations:
- Prevailing wage based on where employee physically works
- Working from home: use home address MSA
- If employee moves to different MSA, new LCA required
- Employer responsible for tracking work location

Metropolitan Statistical Areas (MSA):
- Defined by Office of Management and Budget (OMB)
- Include central city and surrounding counties
- Example: San Francisco MSA includes San Francisco, San Mateo, Marin counties
- DOL Online Wage Library organized by MSA

EMPLOYER OBLIGATIONS:

Pay Higher of Prevailing or Actual Wage:
- Prevailing wage = DOL-determined wage for MSA and occupation
- Actual wage = wage paid to similarly employed workers at employer
- Must pay the HIGHER amount
- Cannot pay below prevailing wage even in low-wage area

Wage Changes with Relocation:
- Employee relocates to higher-wage MSA: must increase wage
- Employee relocates to lower-wage MSA: can decrease wage (but check employment agreement)
- Must file new LCA for new MSA

Cost of Living vs. Prevailing Wage:
- Prevailing wage NOT based solely on cost of living
- Based on actual wages paid in labor market
- High-demand occupations may have high wages even in low cost-of-living areas
- Low-demand occupations may have low wages even in high cost-of-living areas

CHECKING PREVAILING WAGES BY LOCATION:

DOL Online Wage Library (OWL):
1. Visit flcdatacenter.com
2. Select "OES Wage Library"
3. Enter SOC code for occupation
4. Enter zip code of work location
5. View all four wage levels for that MSA
6. Select appropriate wage level based on job requirements

Alternative: Prevailing Wage Determination:
- File Form ETA-9141 with NPWC
- DOL determines wage for specific job description and location
- More precise than OWL
- Required for PERM cases
- Processing: 2-4 months

STRATEGIC CONSIDERATIONS:

For Employers:
- Work location significantly impacts labor costs
- Remote work policies can affect wage obligations
- Satellite offices in lower-wage areas may reduce costs
- Must balance cost savings with compliance obligations

For H-1B Workers:
- Relocation to higher-wage MSA may require wage increase
- Employer must file new LCA if MSA changes
- Check if employer will maintain wage if you work remotely from different MSA

Common Pitfall:
- Using national average wage instead of MSA-specific wage
- Not filing new LCA when employee relocates to different MSA
- Assuming same wage applies across all company locations
- Not accounting for remote work location in wage determination
""",
        "visa_types": ["H-1B", "EB-2", "EB-3", "L-1"],
    },
}


async def ingest_prevailing_wages(
    dry_run: bool = False,
):
    """
    Main ingestion function for prevailing wage information.

    Args:
        dry_run: If True, skip actual API calls
    """
    logger.info("Starting prevailing wage and DOL requirements ingestion")
    logger.info(f"Dry run: {dry_run}")

    # Initialize clients
    clients = await setup_clients()

    all_chunks = []
    all_metadata = []

    for topic_key, topic_info in DOL_WAGE_DATA.items():
        logger.info(f"\nProcessing {topic_key}: {topic_info['title']}")

        # Combine title and description for full content
        full_content = f"{topic_info['title']}\n\n{topic_info['description']}"

        # Chunk the content
        chunks = chunk_text(full_content, chunk_size=512, overlap=50)
        logger.info(f"  Created {len(chunks)} chunks")

        # Create metadata for each chunk
        for chunk_idx, chunk in enumerate(chunks):
            metadata = {
                "source": f"prevailing_wage_{topic_key.replace('-', '_')}",
                "document_title": topic_info["title"],
                "topic": topic_key,
                "visa_types": topic_info["visa_types"],
                "chunk_index": chunk_idx,
                "section": f"wage_{topic_key}_{chunk_idx}",
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
            source="prevailing_wages",
            dry_run=dry_run,
        )

        logger.info(f"✓ Successfully processed {vectors_upserted} vectors")
    else:
        logger.warning("No chunks to ingest")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest prevailing wage and DOL requirements into Pinecone for RAG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without calling APIs",
    )

    args = parser.parse_args()

    asyncio.run(ingest_prevailing_wages(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
