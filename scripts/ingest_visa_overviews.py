"""
Visa Type Overviews ingestion script for Migravio RAG pipeline.

Ingests comprehensive visa type information into Pinecone for AI-assisted
retrieval. Covers eligibility, application process, timelines, and pathways
for common nonimmigrant and immigrant visa types.

Target visa types:
- H-1B (Specialty Occupation)
- H-4 (H-1B Dependent)
- L-1 (Intracompany Transferee)
- O-1 (Extraordinary Ability)
- F-1 (Student)
- OPT (Optional Practical Training)
- EB-1 (Priority Workers)
- EB-2 (Advanced Degree/NIW)
- EB-3 (Skilled Workers)

Usage:
    python scripts/ingest_visa_overviews.py [--dry-run] [--visa-types H-1B,F-1]
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

# Curated visa type information
VISA_DATA = {
    "H-1B": {
        "title": "H-1B Specialty Occupation Visa",
        "description": """
The H-1B visa is a nonimmigrant visa that allows U.S. employers to temporarily
employ foreign workers in specialty occupations requiring theoretical or
technical expertise.

ELIGIBILITY REQUIREMENTS:
- Bachelor's degree or higher (or equivalent experience)
- Job offer in specialty occupation (architecture, engineering, mathematics,
  medicine, sciences, IT, business, finance, etc.)
- Employer must file petition on your behalf
- Position must require specialized knowledge

ANNUAL CAP AND LOTTERY:
- Regular cap: 65,000 visas per fiscal year
- Master's cap: Additional 20,000 for U.S. master's degree holders
- Cap-exempt employers: universities, nonprofits, government research orgs
- Lottery system if petitions exceed cap (typically March/April)
- Registration period: typically early March each year

INITIAL DURATION AND EXTENSIONS:
- Initial period: up to 3 years
- Extensions: additional 3 years (6 years maximum)
- Beyond 6 years possible if:
  * I-140 approved (unlimited 3-year extensions)
  * I-140 pending for 365+ days (1-year extensions)
  * PERM or I-140 filed in 5th or 6th year

APPLICATION PROCESS:
- Employer files LCA (Labor Condition Application) with DOL
- Employer files Form I-129 (Petition for Nonimmigrant Worker) with USCIS
- Premium processing available ($2,805 for 15-day processing)
- If approved, apply for visa at U.S. consulate abroad OR
- Change of status if already in U.S. in valid status

PREVAILING WAGE REQUIREMENT:
- Employer must pay the higher of:
  * Actual wage (what company pays similar workers)
  * Prevailing wage (DOL-determined wage for occupation and location)
- LCA posted at worksite for 10 business days
- Wage levels: I (entry), II (qualified), III (experienced), IV (fully competent)

PORTABILITY (AC21):
- Can change employers while H-1B pending (AC21 portability)
- New employer files new H-1B petition
- Can start work when new petition filed (if currently in H-1B status)
- Extension beyond 6 years transfers with you

60-DAY GRACE PERIOD:
- If employment ends, have 60 days (or remaining status, whichever shorter)
- Can look for new employer or prepare to depart
- Can extend or change status during grace period
- Not counted toward 240-day extension period

DEPENDENTS (H-4):
- Spouse and unmarried children under 21
- H-4 status tied to H-1B principal
- H-4 EAD available if H-1B holder has approved I-140
- Children can attend school

TRAVEL:
- Must have valid H-1B visa stamp to re-enter U.S.
- Visa stamp obtained at U.S. consulate abroad
- Automatic visa revalidation for brief trips to Canada/Mexico
- Keep approval notice (I-797) when traveling

COMMON PATHWAYS:
- F-1/OPT → H-1B (most common for students)
- H-1B → EB-2/EB-3 green card (PERM-based)
- H-1B → EB-1 green card (extraordinary ability)
- Cap-gap extension for F-1 students with pending H-1B

COMMON PITFALLS:
- Missing lottery registration window
- Insufficient evidence of specialty occupation
- Prevailing wage discrepancies
- Public Access File violations
- Unauthorized employment during grace period
- Not maintaining valid status before H-1B starts
""",
        "visa_types": ["H-1B"],
    },
    "H-4": {
        "title": "H-4 Dependent Visa",
        "description": """
The H-4 visa is a dependent visa for spouses and unmarried children (under 21)
of H-1B workers. H-4 status is derivative, meaning it is entirely dependent
on the H-1B principal's valid status.

ELIGIBILITY:
- Spouse of H-1B visa holder
- Unmarried children under 21 of H-1B visa holder
- Must maintain valid H-4 status as long as in the U.S.

H-4 EMPLOYMENT AUTHORIZATION (EAD):
H-4 EAD eligibility is LIMITED to:
- Spouses of H-1B workers who have approved I-140
- Spouses of H-1B workers in H-1B 6th year extension (based on I-140 or PERM)

H-4 EAD APPLICATION (Form I-765):
- File Form I-765 with USCIS
- Category (c)(26) - H-4 spouse with H-1B I-140 approved
- Filing fee: $410 + $85 biometrics = $495
- Processing time: 4-8 months typical
- Automatic 180-day extension if timely renewed
- Valid as long as H-1B and H-4 status remain valid

WORK RESTRICTIONS:
- H-4 dependents CANNOT work without EAD
- Children cannot obtain H-4 EAD (only spouses)
- Unauthorized employment terminates H-4 status
- H-4 EAD ties to specific H-1B principal (if principal changes employers, may need new EAD)

EDUCATION:
- H-4 dependents can attend school (K-12, college, university)
- In-state tuition eligibility varies by state
- No F-1 visa required for education (H-4 sufficient)

TRAVEL:
- Must have valid H-4 visa stamp to re-enter U.S.
- H-4 visa application at consulate requires proof of relationship
- Automatic visa revalidation for Canada/Mexico trips
- Keep H-1B principal's approval notice when traveling

MAINTAINING STATUS:
- H-4 status depends entirely on H-1B principal's status
- If H-1B status ends, H-4 status ends
- Must file H-4 extension when H-1B extends
- Can file H-4 extension concurrently with H-1B or separately

DERIVATIVE STATUS:
- H-4 gets same grace period as H-1B (60 days or remaining status)
- Can change to other visa status (F-1, H-1B, etc.)
- Aging out: child turns 21 must change status or depart

COMMON SCENARIOS:
- H-4 to F-1: Common path for education (file I-539)
- H-4 to H-1B: If offered qualifying job (lottery or cap-exempt)
- Concurrent H-4 extension: File I-539 when spouse extends H-1B

COMMON PITFALLS:
- Working without EAD (terminates status)
- Assuming all H-4 spouses can get EAD (only if H-1B has I-140)
- Not extending H-4 when H-1B extends
- Aging out (child turns 21)
- Failing to maintain valid H-4 when H-1B changes employers
""",
        "visa_types": ["H-4", "H-1B"],
    },
    "L-1": {
        "title": "L-1 Intracompany Transferee Visa",
        "description": """
The L-1 visa allows companies with offices in both the U.S. and abroad to
transfer certain employees from foreign offices to U.S. offices. There are
two subcategories: L-1A for managers/executives and L-1B for specialized
knowledge employees.

L-1A (Managers and Executives):
- Maximum initial period: 3 years
- Extensions: up to 7 years total
- Manages organization, department, subdivision, or function
- Supervises professional employees OR manages essential function
- Has authority to hire/fire or recommend personnel actions

L-1B (Specialized Knowledge):
- Maximum initial period: 3 years
- Extensions: up to 5 years total
- Possesses specialized knowledge of company's product, service, research,
  equipment, techniques, or management
- Knowledge must be advanced and not readily available in U.S. labor market

ELIGIBILITY REQUIREMENTS:
- Employed by qualifying organization abroad for at least 1 continuous year
  in the last 3 years
- Coming to work for related U.S. entity (parent, subsidiary, affiliate, branch)
- Worked in managerial, executive, or specialized knowledge capacity abroad
- Coming to work in similar capacity in the U.S.

QUALIFYING RELATIONSHIP:
- Parent company
- Subsidiary
- Affiliate
- Branch office
- Must demonstrate common ownership and control

BLANKET L vs. INDIVIDUAL L:
- Blanket L: Pre-approved for large companies with frequent transfers
  * Faster processing (no I-129 petition to USCIS first)
  * Apply directly at consulate
  * Requires company eligibility certification
- Individual L: Each transfer requires separate I-129 petition
  * Smaller companies or first L-1 transfers

APPLICATION PROCESS:
- Employer files Form I-129 with USCIS (individual petition)
- Premium processing available ($2,805, 15-day processing)
- If approved, apply for L-1 visa at U.S. consulate OR
- Change of status if already in U.S.

NO PREVAILING WAGE REQUIREMENT:
- Unlike H-1B, no LCA or prevailing wage requirement
- No annual cap or lottery
- No degree requirement (though often preferred)

DEPENDENTS (L-2):
- Spouse and unmarried children under 21
- L-2 spouses automatically work-authorized (file I-765 for EAD)
- L-2 children can attend school

DUAL INTENT:
- L-1 is dual intent visa (can pursue green card)
- Can file I-140 and I-485 while on L-1
- Will not affect L-1 renewal or visa stamping

PATHWAYS TO GREEN CARD:
- L-1A managers/executives: EB-1C (no PERM required)
  * Must work for qualifying related entity for 1+ year abroad
  * Coming to work in managerial/executive capacity
- L-1B: EB-2 or EB-3 (requires PERM)

NEW OFFICE L-1:
- Can transfer to open new U.S. office
- Initial period: 1 year only
- Extension requires proof of business viability
  * Physical office space secured
  * Business plan implemented
  * Employee hired (if managerial)

COMMON PITFALLS:
- Insufficient evidence of managerial/executive role (L-1A)
- Specialized knowledge not adequately documented (L-1B)
- Failing to maintain qualifying relationship between entities
- 1-year abroad requirement timing issues
- New office L-1 extension denied due to lack of business progress
""",
        "visa_types": ["L-1"],
    },
    "O-1": {
        "title": "O-1 Extraordinary Ability Visa",
        "description": """
The O-1 visa is for individuals with extraordinary ability in sciences,
arts, education, business, athletics, or the motion picture/TV industry.
It requires sustained national or international acclaim.

O-1A (Sciences, Education, Business, Athletics):
- Extraordinary ability demonstrated through sustained acclaim
- Recognition in field of expertise
- 3 out of 8 evidence criteria OR major internationally recognized award

O-1B (Arts, Motion Picture/TV):
- Distinction (high level of achievement) in arts
- Recognition demonstrated through 3 out of 6 criteria OR
- Lead/starring role in distinguished productions

NO ANNUAL CAP:
- No lottery or annual quota
- Can apply any time of year
- Approval based purely on merit

ELIGIBILITY CRITERIA (O-1A - 3 out of 8):
1. Receipt of nationally/internationally recognized prizes or awards
2. Membership in associations requiring outstanding achievements
3. Published material about you in professional publications
4. Participated as judge of others' work in your field
5. Original contributions of major significance
6. Authorship of scholarly articles in professional publications
7. Employment in critical or essential capacity for distinguished organizations
8. High salary or remuneration relative to others in field

ELIGIBILITY CRITERIA (O-1B - 3 out of 6):
1. Lead/starring role in distinguished productions
2. Critical reviews or other published materials about your work
3. Lead/starring/critical role for distinguished organizations
4. Record of major commercial or critically acclaimed successes
5. Recognition from organizations, critics, government, or experts
6. High salary or remuneration relative to others in field

ADVISORY OPINION REQUIREMENT:
- Required consultation from peer group, labor organization, or expert
- Consultation letter must address your qualifications
- Exception: no peer group exists in your field
- Processing time: 15 business days typical

PETITION REQUIREMENTS:
- U.S. employer or agent files Form I-129
- Contract or summary of terms
- Itinerary of events/activities
- Advisory opinion letter
- Evidence meeting 3+ criteria
- Premium processing available ($2,805)

INITIAL PERIOD AND EXTENSIONS:
- Initial period: up to 3 years
- Extensions: 1 year increments, unlimited total duration
- Must continue to work in area of extraordinary ability
- Can change employers/agents with new petition

SELF-PETITIONING:
- Cannot self-petition (must have U.S. employer or agent)
- Agent can represent multiple employers
- Common for performers, athletes, artists

DEPENDENTS (O-3):
- Spouse and unmarried children under 21
- O-3 cannot work (no EAD available)
- O-3 can attend school

DUAL INTENT:
- O-1 allows dual intent (can pursue green card)
- Can file EB-1A (self-petition) concurrently
- Will not affect O-1 approval or extensions

PATHWAY TO GREEN CARD:
- EB-1A (extraordinary ability) - self-petition, no employer/PERM
  * Same or similar criteria as O-1A
  * Higher standard (extraordinary vs. sustained acclaim)
- EB-2 NIW (National Interest Waiver) - self-petition alternative

TRAVEL:
- Must have valid O-1 visa stamp to re-enter
- Can travel freely with valid status
- Visa stamp obtained at consulate abroad

COMMON PITFALLS:
- Insufficient documentation of extraordinary ability
- Advisory opinion issues (wrong organization, insufficient detail)
- Evidence doesn't meet criteria threshold
- Confusing O-1A standard with EB-1A (EB-1A is higher bar)
- Assuming media mentions alone qualify (must be about your work)
""",
        "visa_types": ["O-1"],
    },
    "F-1": {
        "title": "F-1 Student Visa",
        "description": """
The F-1 visa is a nonimmigrant visa for full-time students enrolled in
academic programs or English language programs at SEVP-certified institutions
in the United States.

ELIGIBILITY REQUIREMENTS:
- Accepted to SEVP-certified school (college, university, language school)
- Full-time enrollment (minimum 12 credit hours for undergraduate)
- Proof of financial support for tuition and living expenses
- Intent to return to home country after studies (nonimmigrant intent)
- English proficiency (TOEFL/IELTS) unless exempted

I-20 FORM:
- Certificate of Eligibility issued by school's DSO
- Required to apply for F-1 visa
- Contains SEVIS ID number
- Must be signed by DSO and student
- Valid for visa application and status maintenance

SEVIS FEE:
- $350 I-901 SEVIS fee (paid before visa application)
- Pay at fmjfee.com with SEVIS ID
- Keep receipt for visa interview

INITIAL DURATION:
- F-1 status valid for "duration of status" (D/S)
- Not tied to visa expiration date
- Valid as long as:
  * Enrolled full-time in approved program
  * Making normal progress toward degree
  * I-20 remains valid

MAINTAINING F-1 STATUS:
- Enroll full-time (12+ credits undergrad, 9+ grad, 18+ hrs/week language)
- Make normal academic progress
- Do not work without authorization
- Report address changes within 10 days (update in SEVIS)
- Transfer procedure if changing schools (within 15 days of start)

EMPLOYMENT AUTHORIZATION:

On-Campus Employment:
- Up to 20 hours/week during school, full-time during breaks
- No special authorization needed beyond F-1 status
- Must maintain full-time enrollment

CPT (Curricular Practical Training):
- Part-time (20 hrs/week or less) or full-time
- Must be integral part of curriculum (internship, practicum, coop)
- Authorized by DSO on I-20
- 12+ months full-time CPT makes you ineligible for OPT

OPT (Optional Practical Training):
- See separate OPT section for full details
- Pre-completion OPT: during studies (part-time)
- Post-completion OPT: after graduation (12 months full-time)
- STEM OPT: 24-month extension for STEM degrees

PROGRAM EXTENSIONS:
- If need more time to complete degree, request I-20 extension
- Must request before program end date
- Valid reasons: change of major, research requirements, academic difficulties
- DSO updates I-20 program end date

SCHOOL TRANSFERS:
- Must complete transfer within 15 days of start date at new school
- New school issues transfer I-20
- Old school's SEVIS record transferred to new school
- 5-month rule: if out of school 5+ months, F-1 status may terminate

TRAVEL:
- Must have valid F-1 visa to re-enter (if expired, get new stamp)
- I-20 with valid travel signature (DSO signature within 12 months)
- Passport valid for 6+ months
- Proof of enrollment (transcript, enrollment letter)

5-MONTH RULE:
- If out of school for 5+ months, lose F-1 status
- Exceptions: official break, approved leave, study abroad
- Must re-enter as new F-1 student if violated

GRACE PERIODS:
- 60-day grace period after:
  * Program completion (including OPT)
  * Early program withdrawal
- Can stay in U.S. but cannot work or study
- Can change status or transfer schools
- Can depart and re-enter if valid visa and I-20

DEPENDENTS (F-2):
- Spouse and unmarried children under 21
- F-2 cannot work (no EAD)
- F-2 children can attend K-12 school
- F-2 cannot pursue full-time study (can take recreational classes)

COMMON PATHWAYS:
- F-1 → OPT → H-1B (most common)
- F-1 → Cap-gap extension (if H-1B pending)
- F-1 → Change of status to other visa

COMMON PITFALLS:
- Dropping below full-time enrollment
- Unauthorized employment (terminates status)
- Traveling with expired visa (need new stamp)
- Not getting travel signature on I-20
- Missing 5-month rule (losing status)
- OPT unemployment limits exceeded
""",
        "visa_types": ["F-1"],
    },
    "OPT": {
        "title": "Optional Practical Training (OPT)",
        "description": """
Optional Practical Training (OPT) is temporary employment authorization for
F-1 students to work in their field of study. There are two types:
pre-completion OPT and post-completion OPT. STEM degree holders can apply
for a 24-month extension.

PRE-COMPLETION OPT:
- Available during studies after first academic year
- Part-time (20 hrs/week or less) during school term
- Full-time during official breaks
- Counts against 12-month OPT total
- Less common than post-completion OPT

POST-COMPLETION OPT:
- 12 months of full-time work authorization after degree completion
- Must apply within 90 days before to 60 days after program end
- Work must be related to field of study (major)
- Can use once per educational level (bachelor's, master's, doctorate)

ELIGIBILITY:
- Been in lawful F-1 status for at least one full academic year
- Currently enrolled full-time or on approved leave
- Have not used 12 months of full-time CPT
- Degree program completed or expected to complete

APPLICATION PROCESS:
1. Get DSO recommendation (I-20 with OPT recommendation)
2. File Form I-765 with USCIS ($410 filing fee + $85 biometrics)
3. USCIS processing: 3-5 months typical (apply early!)
4. Receive EAD card with 12-month validity

APPLICATION TIMING:
- Apply no earlier than 90 days before program completion
- Apply no later than 60 days after program completion
- Must have I-20 with OPT recommendation before filing
- EAD start date can be requested (within 60 days of completion)

UNEMPLOYMENT LIMITS:
- Maximum 90 days cumulative unemployment during 12-month OPT
- Days counted from EAD start date, not first day of work
- Exceeding 90 days terminates F-1 status
- Unemployment tracked by DHS

EMPLOYMENT REQUIREMENTS:
- Must work minimum 20 hours/week to count as employed
- Multiple part-time jobs totaling 20+ hrs/week OK
- Work must be directly related to major field of study
- Can be paid or unpaid (volunteer OK if 20+ hrs/week)
- Self-employment allowed if meets requirements

REPORTING REQUIREMENTS:
- Report employment start/end within 10 days (via SEVP Portal)
- Report employer changes within 10 days
- Report address changes within 10 days
- DSO monitors compliance

STEM OPT EXTENSION (24 months):
Eligibility requirements:
- Have 12-month post-completion OPT based on STEM degree
- Degree on STEM-designated degree list
- Apply before current OPT expires
- Employer enrolled in E-Verify
- File Form I-983 (Training Plan) with employer

STEM OPT requirements:
- Form I-765 with STEM extension category
- New I-20 with STEM recommendation from DSO
- Employer must be E-Verify enrolled
- I-983 training plan signed by employer
- Filing fee: $410 + $85 biometrics
- Can apply up to 90 days before current OPT ends

STEM OPT UNEMPLOYMENT:
- Additional 60 days unemployment during 24-month extension
- Total 150 days for entire OPT period (90 + 60)
- Exceeding limit terminates F-1 status

STEM OPT REPORTING:
- Self-evaluation and employer validation every 12 months
- I-983 formal evaluation at 12 and 24 months
- Report material changes within 10 days

CAP-GAP EXTENSION:
- Automatic extension if H-1B petition filed before OPT ends
- OPT/F-1 status extended until H-1B start (Oct 1) or denial
- EAD automatically extended (no filing needed)
- Critical for seamless F-1 to H-1B transition

TRAVEL DURING OPT:
- Must have:
  * Valid F-1 visa (or be prepared to get new one)
  * Valid EAD card
  * I-20 with valid travel signature and OPT notation
  * Job offer letter or employment verification
- Re-entry not guaranteed if unemployed

60-DAY GRACE PERIOD:
- After OPT ends, have 60 days to:
  * Depart U.S.
  * Change status (H-1B, etc.)
  * Transfer to new school
- Cannot work during grace period

COMMON PITFALLS:
- Applying too late (missing 60-day deadline)
- Exceeding 90-day unemployment limit
- Working before EAD card received
- Not reporting employment within 10 days
- Traveling without proper documents
- STEM OPT employer not E-Verify enrolled
- Missing I-983 evaluation deadlines
""",
        "visa_types": ["OPT", "F-1"],
    },
    "EB-1": {
        "title": "EB-1 Priority Workers (Green Card)",
        "description": """
The EB-1 category is for priority workers seeking permanent residence
(green card). There are three subcategories: EB-1A (extraordinary ability),
EB-1B (outstanding researchers/professors), and EB-1C (multinational
managers/executives). No PERM labor certification required.

EB-1A (Extraordinary Ability):
- Self-petition allowed (no employer required)
- Sciences, arts, education, business, or athletics
- Sustained national or international acclaim
- Must meet 3 of 10 criteria OR one-time major achievement

EB-1B (Outstanding Researcher or Professor):
- Employer required (university or research organization)
- International recognition in academic field
- 3+ years teaching or research experience
- Must meet 2 of 6 criteria
- Permanent research position or tenure-track required

EB-1C (Multinational Manager or Executive):
- Employer required (multinational company)
- Worked abroad for related entity 1 of last 3 years
- Coming to work in managerial or executive capacity
- Qualifying relationship between entities required

EB-1A CRITERIA (3 of 10):
1. Receipt of lesser nationally or internationally recognized prizes/awards
2. Membership in associations requiring outstanding achievements
3. Published material about you in professional publications
4. Judged work of others in your field
5. Original contributions of major significance
6. Authored scholarly articles
7. Displayed work at artistic exhibitions
8. Leading/critical role in distinguished organizations
9. High salary or remuneration
10. Commercial success in performing arts

EB-1A vs. O-1:
- EB-1A has higher standard than O-1
- EB-1A requires "extraordinary" (top of field)
- O-1 requires "sustained acclaim" (lower threshold)
- EB-1A leads to green card (immigrant)
- O-1 is nonimmigrant temporary visa

EB-1B CRITERIA (2 of 6):
1. Receipt of major prizes/awards for outstanding achievement
2. Membership in associations requiring outstanding achievements
3. Published material in professional publications about your work
4. Participated as judge of others' work
5. Original research contributions to field
6. Authored scholarly books or articles

EB-1C ELIGIBILITY:
- Worked for related foreign entity as manager/executive for 1+ year
- Related entity must be:
  * Parent company
  * Subsidiary
  * Affiliate
  * Branch office
- Coming to work as manager or executive in U.S.
- U.S. company been in business for 1+ year (or new office provisions)

MANAGERIAL CAPACITY (EB-1C):
- Manages organization, department, subdivision, or function
- Supervises professional employees OR manages essential function
- Has authority over day-to-day operations
- Authority to hire/fire or recommend personnel actions

EXECUTIVE CAPACITY (EB-1C):
- Directs management of organization or major component
- Establishes goals and policies
- Exercises wide latitude in decision-making
- Receives only general supervision from higher executives or board

NO PERM REQUIRED:
- All EB-1 categories skip PERM labor certification
- Faster than EB-2/EB-3 (saves 1-2 years)
- No prevailing wage requirement
- No recruitment process required

PRIORITY DATES:
- Usually current (no backlog) for most countries
- India and China may have retrogression periods
- Check monthly visa bulletin
- Can file I-140 and I-485 concurrently if current

APPLICATION PROCESS:
EB-1A:
1. Self-petition: File Form I-140 with USCIS
2. Premium processing available ($2,805)
3. If approved and priority date current, file I-485

EB-1B and EB-1C:
1. Employer files Form I-140 with USCIS
2. Premium processing available
3. If approved and priority date current, file I-485

EVIDENCE REQUIREMENTS:
- Detailed documentation of achievements
- Letters from experts in field
- Publications, citations, media coverage
- Awards, memberships, judging experience
- Employment letters, organizational charts (EB-1C)
- Proof of qualifying relationship (EB-1C)

PROCESSING TIMES:
- I-140 without premium: 6-12 months
- I-140 with premium: 15 days
- I-485 concurrent filing: 8-24 months total

PATHWAYS:
- O-1 → EB-1A (common for extraordinary ability)
- L-1A → EB-1C (common for managers/executives)
- F-1/OPT → EB-1A (possible for exceptional students/researchers)

DEPENDENTS:
- Spouse and unmarried children under 21 included
- Derivatives get green cards at same time

UPGRADE FROM EB-2/EB-3:
- Can file EB-1 while EB-2/EB-3 pending
- If EB-1 approved first, use earlier priority date (porting)
- Significantly reduces wait time

COMMON PITFALLS:
- Insufficient evidence of extraordinary ability (EB-1A)
- Confusing O-1 standard with EB-1A (EB-1A higher)
- Not clearly documenting managerial/executive role (EB-1C)
- Insufficient proof of qualifying relationship (EB-1C)
- Weak expert letters (must address specific criteria)
- Failing to demonstrate sustained acclaim
""",
        "visa_types": ["EB-1", "Green Card"],
    },
    "EB-2": {
        "title": "EB-2 Advanced Degree or Exceptional Ability (Green Card)",
        "description": """
The EB-2 category is for foreign nationals with advanced degrees (master's
or higher) or exceptional ability in sciences, arts, or business. Standard
EB-2 requires PERM labor certification and employer sponsorship. EB-2 NIW
(National Interest Waiver) allows self-petition without employer or PERM.

EB-2 ADVANCED DEGREE:
- Master's degree or higher (or foreign equivalent)
- Bachelor's degree plus 5 years progressive post-degree work experience
- Job requires advanced degree
- Employer sponsorship and PERM required

EB-2 EXCEPTIONAL ABILITY:
- Exceptional ability in sciences, arts, or business
- Meet 3 of 6 criteria (see below)
- Significantly above ordinary practitioners
- Employer sponsorship and PERM required

EB-2 NIW (National Interest Waiver):
- Waives job offer and PERM requirements
- Self-petition allowed (no employer needed)
- Must show work is in national interest of U.S.
- Can be based on advanced degree OR exceptional ability

EB-2 EXCEPTIONAL ABILITY CRITERIA (3 of 6):
1. Official academic record showing degree, diploma, certificate
2. Letters documenting 10+ years full-time experience
3. License to practice profession
4. Evidence of salary demonstrating exceptional ability
5. Membership in professional associations
6. Recognition for achievements from peers, government, professional orgs

NIW ELIGIBILITY (Matter of Dhanasar Test):
Must prove all three prongs:
1. Proposed endeavor has substantial merit and national importance
   - Research, business, entrepreneurship
   - Benefit to U.S. economy, health, education, environment, etc.

2. You are well-positioned to advance the proposed endeavor
   - Education, skills, knowledge, track record
   - Plan for future work is feasible
   - Past achievements demonstrate ability

3. On balance, beneficial to waive job offer and PERM requirements
   - Impractical to obtain labor certification
   - Urgent national interest
   - Individual contributions outweigh benefit of PERM

STANDARD EB-2 PROCESS (with PERM):
1. Employer files PERM labor certification with DOL
   - Recruitment process (ads, job postings)
   - Test U.S. labor market
   - Processing: 8-14 months typical
2. If PERM approved, employer files Form I-140 with USCIS
   - Premium processing available ($2,805)
   - Processing: 6-12 months (15 days with premium)
3. If I-140 approved and priority date current, file I-485
   - Adjustment of status
   - Processing: 8-24 months

NIW PROCESS (self-petition):
1. File Form I-140 directly with USCIS
   - No PERM required
   - No employer required
   - Premium processing available ($2,805)
2. If I-140 approved and priority date current, file I-485
3. Total timeline: 1-2 years vs. 2-4 years for standard EB-2

PRIORITY DATES AND RETROGRESSION:
- India: significant backlog (5-10+ years for standard EB-2)
- China: moderate backlog (2-3+ years)
- Rest of world: typically current or minimal wait
- NIW has same priority date rules as standard EB-2
- Check monthly visa bulletin

CONCURRENT I-140 AND I-485:
- Can file together if priority date current
- Saves significant time
- Apply for EAD and advance parole concurrently
- EAD/AP typically approved in 3-5 months

H-1B 6TH YEAR EXTENSIONS:
- Approved I-140 allows unlimited 3-year H-1B extensions
- I-140 pending 365+ days allows 1-year H-1B extensions
- Critical for Indian/Chinese nationals facing backlogs

EB-2 TO EB-1 UPGRADE:
- Can file EB-1 while EB-2 pending
- If EB-1 approved, use earlier EB-2 priority date (porting)
- Significantly reduces wait time
- Common strategy for India/China EB-2 holders

DEPENDENTS:
- Spouse and unmarried children under 21 included
- Derivatives get green cards at same time
- Child age frozen at I-140 filing (CSPA)

COMMON NIW FIELDS:
- Medical researchers, physicians in underserved areas
- STEM researchers (AI, renewable energy, biotech)
- Entrepreneurs with innovative businesses
- Professors and educators
- Engineers working on critical infrastructure

EVIDENCE FOR NIW:
- Detailed personal statement
- Expert recommendation letters (5-8 typical)
- Publications, citations, patents
- Awards, grants, funding
- Media coverage
- Business plan (for entrepreneurs)
- Government or professional recognition

COMMON PITFALLS:
- PERM audit due to recruitment issues
- Insufficient evidence for NIW national interest prong
- Weak expert letters (must address Dhanasar test)
- Not clearly showing individual will advance endeavor
- Confusing exceptional ability with extraordinary (EB-1A)
- Missing priority date retrogression (file early)
""",
        "visa_types": ["EB-2", "Green Card"],
    },
    "EB-3": {
        "title": "EB-3 Skilled Workers, Professionals, Other Workers (Green Card)",
        "description": """
The EB-3 category is for skilled workers, professionals, and other workers
(unskilled). All EB-3 petitions require PERM labor certification and
employer sponsorship. EB-3 is generally for workers who don't qualify for
EB-1 or EB-2.

EB-3 SKILLED WORKERS:
- Job requires minimum 2 years training or work experience
- Experience cannot be temporary or seasonal
- Must meet educational/experience requirements on labor certification
- Employer sponsorship and PERM required

EB-3 PROFESSIONALS:
- Job requires U.S. bachelor's degree (or foreign equivalent)
- Must possess required bachelor's degree
- Employer sponsorship and PERM required

EB-3 OTHER WORKERS (Unskilled):
- Job requires less than 2 years training or experience
- Separate category with longer backlogs
- Subject to limited annual quota (10,000 visas)
- Employer sponsorship and PERM required

ELIGIBILITY REQUIREMENTS:

Skilled Workers:
- 2+ years job experience or training
- Experience must be relevant to position
- Post-secondary education may count as training

Professionals:
- U.S. bachelor's degree or foreign equivalent
- Degree must be required for position
- Degree must be related to job duties

Other Workers:
- Less than 2 years experience required
- Unskilled or low-skilled positions
- Longer wait times due to annual cap

PERM LABOR CERTIFICATION PROCESS:
1. Employer determines prevailing wage with DOL
2. Recruitment process (mandatory steps):
   - Job order with State Workforce Agency (30 days)
   - Two Sunday newspaper ads
   - 30-day internal posting
   - Three additional recruitment steps for professional positions
3. Employer evaluates applicants, documents process
4. File PERM with DOL (ETA-9089)
5. Processing time: 8-14 months typical
6. Audit risk: 20-30% of cases

PERM APPROVAL REQUIREMENTS:
- No qualified U.S. workers available
- Employer paid prevailing wage or higher
- Job requirements are normal for occupation
- Recruitment properly conducted and documented
- No discrimination in hiring

I-140 PETITION (After PERM Approved):
- Employer files Form I-140 with USCIS
- Premium processing available ($2,805, 15-day processing)
- Evidence of ability to pay prevailing wage required
- Processing: 6-12 months without premium

ABILITY TO PAY:
Employer must prove ability to pay prevailing wage from priority date onward:
- Tax returns (net income or net current assets)
- Annual reports
- Audited financial statements
- W-2s showing actual wage paid

PRIORITY DATES AND BACKLOGS:

EB-3 Skilled Workers and Professionals:
- India: 8-12+ year backlog
- China: 3-5+ year backlog
- Philippines: 2-4+ year backlog
- Rest of world: typically current or minimal wait

EB-3 Other Workers:
- All countries: 5-10+ year backlog
- Limited to 10,000 visas per year
- Significantly longer than skilled/professional

DOWNGRADE FROM EB-2 TO EB-3:
- Sometimes faster to downgrade EB-2 to EB-3
- Retain earlier EB-2 priority date (priority date porting)
- EB-3 rest-of-world may be more current than EB-2 India
- Strategic option for Indian nationals facing long EB-2 backlogs

I-485 ADJUSTMENT OF STATUS:
- File when priority date becomes current
- Can file concurrently with I-140 if current
- Apply for EAD and advance parole
- Processing: 8-24 months

H-1B EXTENSIONS BASED ON APPROVED I-140:
- Unlimited 3-year H-1B extensions with approved I-140
- 1-year extensions if I-140 pending 365+ days
- Critical for maintaining status during backlogs

PORTABILITY (AC21):
- Can change employers after I-485 pending 180+ days
- New job must be same/similar occupation
- No need to restart PERM/I-140 process
- Notify USCIS of job change

DEPENDENTS:
- Spouse and unmarried children under 21 included
- Derivatives get green cards at same time
- Child Status Protection Act (CSPA) freezes age at I-140 filing

COMMON FIELDS:
- Skilled Workers: mechanics, chefs, technicians, tradespeople
- Professionals: accountants, engineers, teachers, programmers
- Other Workers: housekeepers, laborers, food service workers

EB-3 vs. EB-2:
- EB-3 requires only bachelor's (EB-2 needs master's or bachelor's + 5 years)
- EB-3 often has longer backlogs (especially for India/China)
- EB-2 NIW allows self-petition (EB-3 always needs employer)
- EB-2 generally higher-skilled positions

COMMON PITFALLS:
- PERM denied due to recruitment issues
- Ability to pay issues (small companies, startups)
- PERM audit due to insufficient documentation
- Job requirements too restrictive (tailored to candidate)
- Employer business changes during long backlog
- Maintaining H-1B/L-1 status during 5-10+ year wait
- Child aging out during backlog (despite CSPA)
""",
        "visa_types": ["EB-3", "Green Card"],
    },
}


async def ingest_visa_overviews(
    visa_types: list[str] | None = None,
    dry_run: bool = False,
):
    """
    Main ingestion function for visa type overviews.

    Args:
        visa_types: List of visa types to ingest (e.g., ['H-1B', 'F-1'])
        dry_run: If True, skip actual API calls
    """
    if visa_types is None:
        visa_types = list(VISA_DATA.keys())

    # Validate visa type names
    invalid_types = [v for v in visa_types if v not in VISA_DATA]
    if invalid_types:
        logger.error(f"Invalid visa types: {invalid_types}")
        logger.error(f"Valid visa types: {list(VISA_DATA.keys())}")
        return

    logger.info(f"Starting visa type overviews ingestion for: {visa_types}")
    logger.info(f"Dry run: {dry_run}")

    # Initialize clients
    clients = await setup_clients()

    all_chunks = []
    all_metadata = []

    for visa_type in visa_types:
        visa_info = VISA_DATA[visa_type]
        logger.info(f"\nProcessing {visa_type}: {visa_info['title']}")

        # Combine title and description for full content
        full_content = f"{visa_info['title']}\n\n{visa_info['description']}"

        # Chunk the content
        chunks = chunk_text(full_content, chunk_size=512, overlap=50)
        logger.info(f"  Created {len(chunks)} chunks")

        # Create metadata for each chunk
        for chunk_idx, chunk in enumerate(chunks):
            metadata = {
                "source": f"visa_overview_{visa_type.lower().replace('-', '_')}",
                "document_title": f"{visa_type}: {visa_info['title']}",
                "visa_type": visa_type,
                "visa_types": visa_info["visa_types"],
                "chunk_index": chunk_idx,
                "section": f"visa_{visa_type.lower().replace('-', '_')}_{chunk_idx}",
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
            source="visa_overviews",
            dry_run=dry_run,
        )

        logger.info(f"✓ Successfully processed {vectors_upserted} vectors")
    else:
        logger.warning("No chunks to ingest")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest visa type overview information into Pinecone for RAG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without calling APIs",
    )
    parser.add_argument(
        "--visa-types",
        type=str,
        help="Comma-separated list of visa types to ingest (e.g., 'H-1B,F-1')",
    )

    args = parser.parse_args()

    visa_types = None
    if args.visa_types:
        visa_types = [v.strip() for v in args.visa_types.split(",")]

    asyncio.run(ingest_visa_overviews(visa_types=visa_types, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
