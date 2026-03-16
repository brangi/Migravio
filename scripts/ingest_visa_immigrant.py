import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared import chunk_text, setup_clients, upsert_to_pinecone

ENV_PATH = SCRIPT_DIR.parent / "apps" / "ai-service" / ".env"
load_dotenv(ENV_PATH)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)


VISA_DATA = {
    "EB-4": {
        "title": "Special Immigrant Visa Categories",
        "visa_types": ["EB-4", "Green Card"],
        "description": """
The EB-4 immigrant visa category, also known as the Fourth Preference Employment-Based category, is reserved for "special immigrants" - a diverse group of individuals who qualify for permanent residence under specific circumstances defined by law. Unlike other employment-based categories that focus on extraordinary ability, advanced degrees, or labor certification, EB-4 covers unique situations including religious workers, special immigrant juveniles, international broadcasters, and those who have served the U.S. government abroad.

Special Immigrant Juvenile Status (SIJS) is one of the most frequently used EB-4 subcategories. SIJS provides a path to permanent residence for immigrant children who have been abused, neglected, or abandoned by one or both parents. To qualify for SIJS, you must be under 21 years of age and unmarried. You must obtain a state juvenile court order that makes specific findings: that you are dependent on the court or legally committed to or placed under the custody of a state agency or individual appointed by the court; that reunification with one or both parents is not viable due to abuse, neglect, abandonment, or a similar basis under state law; and that it would not be in your best interest to be returned to your country of origin or country of last habitual residence.

The SIJS process involves two main steps. First, you must petition a state family or juvenile court for the required findings. This is done under state law and procedures, and you typically need an attorney familiar with both immigration law and state dependency law. The court must make the specific findings required by federal immigration law. Second, after obtaining the court order, you file Form I-360, Petition for Amerasian, Widow(er), or Special Immigrant, with USCIS along with the certified court order. Once I-360 is approved, you can apply for adjustment of status using Form I-485.

One significant challenge with SIJS is visa availability and backlogs. While SIJS beneficiaries are in the EB-4 category which generally has visa numbers available, certain countries with high demand (particularly El Salvador, Guatemala, Honduras, and Mexico) face substantial backlogs. As of 2026, applicants from these countries may wait several years after I-360 approval before they can file Form I-485 due to visa retrogression. During this waiting period, SIJS beneficiaries may be able to remain in the U.S. if they maintain lawful status or qualify for deferred action.

SIJS grants have important limitations. While waiting for a green card, SIJS beneficiaries generally cannot petition for their parents to immigrate (since one or both parents were found to have abused, neglected, or abandoned them). After obtaining the green card, adult SIJS beneficiaries who become U.S. citizens still cannot petition for their parents if those parents were the subject of the abuse, neglect, or abandonment findings.

Religious Workers constitute another major EB-4 subcategory. To qualify as a special immigrant religious worker, you must have been a member of a religious denomination that has a bona fide nonprofit religious organization in the United States for at least two years immediately before filing the petition. You must be coming to the United States to work in a full-time, compensated position as a minister, in a professional religious capacity, or in a religious vocation or occupation. The petitioning religious organization files Form I-360 on your behalf.

Religious worker positions include ministers or priests authorized to conduct religious worship and perform other duties usually performed by clergy; professional positions in a religious vocation requiring at least a U.S. bachelor's degree or foreign equivalent (such as religious instructors, missionaries, religious counselors); or other religious occupations or vocations involving traditional religious functions (such as liturgical workers, religious hospital workers, religious broadcasters, catechists). Purely administrative or maintenance positions do not qualify.

The religious worker program requires that the U.S. religious organization provide evidence of its tax-exempt status, ability to compensate the worker, and that the position is a legitimate religious position. The religious worker must have been performing religious work continuously (either abroad or in lawful R-1 status in the U.S.) for the two years immediately before filing. Religious workers can initially enter in R-1 nonimmigrant status and later transition to EB-4 permanent residence.

Afghan and Iraqi Translators/Interpreters who worked with the U.S. Armed Forces or under Chief of Mission authority qualify for Special Immigrant Visas (SIV). If you worked directly with the United States Armed Forces or under Chief of Mission authority in Iraq or Afghanistan as a translator or interpreter for at least 12 months, and you obtained a favorable written recommendation from a General or Flag Officer in the U.S. Armed Forces or from a Chief of Mission, you may qualify for an SIV. You must also demonstrate that you have experienced or are experiencing an ongoing serious threat as a consequence of your employment by the U.S. government.

The Afghan and Iraqi SIV programs have separate application processes managed by the U.S. Department of State. After receiving Chief of Mission approval, you apply for the SIV through the National Visa Center and attend an interview at a U.S. embassy or consulate. SIV holders and their eligible family members (spouse and unmarried children under 21) receive permanent residence immediately upon entry to the United States and do not need to apply for adjustment of status.

Certain International Broadcasters working for the U.S. Agency for Global Media (formerly Broadcasting Board of Governors) or a grantee of such agency may qualify for EB-4 status. This includes employees of Radio Free Europe, Radio Liberty, Radio Free Asia, Middle East Broadcasting Networks, and other U.S. government-sponsored international broadcasting services. The employer must file Form I-360 demonstrating that the beneficiary has been employed by the broadcasting organization for at least the past 15 years and is applying from abroad or from within the U.S. where they are in lawful status.

Retired International Organization Employees who have worked for a qualifying international organization (such as the United Nations, World Bank, International Monetary Fund, or other organizations designated by executive order) for at least 15 years and have resided in the United States continuously for at least half of the seven years immediately before filing may qualify for EB-4 classification. The applicant must be retiring from the international organization and file Form I-360 on their own behalf.

Retired NATO-6 Civilian Employees who have worked for NATO (North Atlantic Treaty Organization) in a civilian capacity for at least 15 years and are otherwise admissible to the United States may qualify. The period of employment must include employment in the U.S. as a NATO-6 nonimmigrant. Certain family members are also eligible.

Panama Canal Company or Canal Zone Government Employees who were employed continuously from before a certain date may qualify for EB-4 classification. This category is largely historical but still exists in the law.

Certain U.S. Government Employees Abroad who have completed at least 15 years of qualifying employment may be eligible for EB-4 classification. This can include Foreign Service officers retiring after long careers or other civilian U.S. government employees who have served abroad.

For most EB-4 categories, the process involves filing Form I-360 either by the beneficiary (self-petition) or by a qualifying employer or organization. Once approved, if you are in the United States, you can file Form I-485 to adjust status to permanent residence if a visa number is available. If you are abroad, you proceed through consular processing at a U.S. embassy or consulate.

Processing times for I-360 petitions vary by category and service center, typically ranging from 3 to 12 months. SIJS cases are often processed faster than religious worker cases. Adjustment of status processing times vary widely depending on field office workload.

EB-4 visa availability is generally current for most countries and most subcategories, meaning visa numbers are immediately available. However, SIJS applicants from El Salvador, Guatemala, Honduras, and Mexico face significant backlogs, with wait times of several years in some cases. The monthly Visa Bulletin published by the Department of State shows current priority dates.
        """
    },
    "EB-5": {
        "title": "Immigrant Investor Program",
        "visa_types": ["EB-5", "Green Card"],
        "description": """
The EB-5 Immigrant Investor Program provides a path to U.S. permanent residence for foreign nationals who invest substantial capital in a U.S. commercial enterprise that creates or preserves at least 10 full-time jobs for qualifying U.S. workers. The program was created by Congress in 1990 to stimulate the U.S. economy through job creation and capital investment by foreign investors.

Investment Amount Requirements vary based on where the business is located. The standard minimum investment is $1,050,000. However, if the investment is made in a Targeted Employment Area (TEA), the minimum investment is reduced to $800,000. A TEA is defined as either a rural area (outside a metropolitan statistical area or a city/town with a population of 20,000 or more) or an area experiencing high unemployment (at least 150% of the national average unemployment rate).

These investment thresholds increased from the previous levels of $1,000,000 and $500,000 on November 21, 2019, under new regulations, and are now indexed to inflation and adjusted every five years. The TEA designation must be valid at the time of filing the I-526 or I-526E petition, and the determination is typically made by state economic development agencies or USCIS.

Job Creation Requirements mandate that the investment must create or preserve at least 10 full-time jobs for qualifying U.S. workers within two years of the immigrant investor's admission to the United States as a conditional permanent resident. Qualifying U.S. workers include U.S. citizens, lawful permanent residents, and other immigrants authorized to work in the United States (but not the investor, their spouse, or their children). Full-time employment means at least 35 hours per week.

For direct investments in a new commercial enterprise, the investor must show that 10 actual jobs were created directly by the enterprise. For investments through a Regional Center, the investor can count direct, indirect, and induced jobs, which are calculated using economic models and multiplier effects. This makes the job creation requirement easier to satisfy through Regional Centers.

The EB-5 program operates under two main models: Direct EB-5 Investment and Regional Center Investment. Under a direct investment, the investor directly invests in a new commercial enterprise that they create or in a troubled business (one that has existed for at least two years and has lost 20% or more of its net worth in the past 12-24 months). The investor typically has an active role in management or policy formation. Under a Regional Center investment, the investor invests in a commercial enterprise associated with a USCIS-designated Regional Center, which is an economic unit, public or private, that promotes economic growth through increased export sales, improved regional productivity, job creation, or increased domestic capital investment. Regional Center investors can be passive investors without day-to-day management responsibilities and can count indirect and induced jobs.

The EB-5 Reform and Integrity Act of 2022 made significant changes to the program. The Act reauthorized the Regional Center Program, which had lapsed in June 2021, and created new set-aside visa categories with dedicated allocations: 20% for rural TEA projects, 10% for high unemployment TEA projects, and 2% for infrastructure projects. The Act also implemented new integrity measures including enhanced Regional Center oversight, mandatory site visits, fund administration requirements, and restrictions on promoters and Regional Center operations.

The EB-5 Process involves several steps. First, the investor files Form I-526, Petition by Immigrant Investor, or Form I-526E (for Regional Center investments), with USCIS. The petition must demonstrate that the required capital has been or is being invested in a qualifying commercial enterprise and that the investment will create the required jobs. The investor must also show that the investment capital came from a lawful source. Processing times for I-526/I-526E petitions have historically been long, often 2-5 years or more, though the new set-aside categories process faster.

If the I-526 or I-526E is approved and a visa number is available, the investor can either apply for an immigrant visa at a U.S. consulate abroad (consular processing) or, if already in the U.S. in lawful status, file Form I-485 to adjust status to conditional permanent residence. Upon approval, the investor, their spouse, and unmarried children under 21 receive conditional permanent residence valid for two years.

Conditional Permanent Residence is granted because at the time of approval, the full job creation may not yet be complete. During the two-year conditional period, the investor must ensure that the capital remains at risk in the commercial enterprise and that the job creation requirements are met. The investor must file Form I-829, Petition by Investor to Remove Conditions on Permanent Resident Status, during the 90-day period before the two-year conditional green card expires.

The I-829 petition must demonstrate that the investor sustained the investment throughout the conditional period, the capital remained at risk, and the required 10 jobs were created or maintained. If approved, the conditional status is removed and the investor receives a permanent 10-year green card. I-829 processing times vary but typically range from 18 to 48 months. While the I-829 is pending, conditional permanent residence is automatically extended.

Source of Funds Documentation is one of the most critical and challenging aspects of EB-5 petitions. Investors must prove that their investment capital was obtained through lawful means. Acceptable sources include salary, business income, sale of property, sale of stock, inheritance, gift, loan secured by assets, or other legal means. Documentation requirements are extensive and may include tax returns, business financial statements, property deeds and sale documents, bank statements, stock transaction records, loan agreements, gift letters with donee's source of funds documentation, and evidence tracing the path of funds from source to the EB-5 investment.

Many countries have strict currency controls or banking documentation requirements that can complicate source of funds documentation. USCIS scrutinizes source of funds evidence closely, and incomplete or suspicious documentation is a common reason for denials or Requests for Evidence.

Priority Dates and Visa Availability affect processing timelines. Each EB-5 petition receives a priority date (the date the I-526/I-526E is filed). Historically, investors from mainland China have faced significant backlogs due to high demand, with wait times of 5-15 years or more in some cases. Vietnam and India have also experienced retrogression. However, the EB-5 Reform and Integrity Act's set-aside categories (rural, high unemployment, infrastructure) have remained current with no backlog, making them attractive options for faster processing.

Derivative Family Members including the investor's spouse and unmarried children under 21 can be included in the EB-5 petition and receive conditional permanent residence along with the principal investor. However, children who turn 21 during the long processing times may age out, though the Child Status Protection Act provides some relief in certain circumstances.

Risks and Considerations in the EB-5 program include capital at risk (the investment must genuinely be at risk and there is no guarantee of return), project failure (if the commercial enterprise fails or does not create the required jobs, the I-829 may be denied), fraud (some EB-5 projects have been fraudulent schemes, requiring careful due diligence), changes in law (immigration laws can change, affecting pending cases), and family considerations (long processing times can affect derivative family members).

Due diligence before investing is critical. Investors should review the Regional Center's track record and USCIS compliance history, analyze the business plan and financial projections with independent experts, verify job creation methodology and economic reports, review all offering documents and subscription agreements with qualified attorneys, visit the project site and meet management, and understand the capital stack, use of funds, and investor protections.
        """
    },
    "Family-Based": {
        "title": "Family-Based Immigration - All Categories",
        "visa_types": ["Green Card", "Family"],
        "description": """
Family-based immigration allows U.S. citizens and lawful permanent residents to sponsor certain family members for permanent residence in the United States. This is the most common pathway to a green card, accounting for the majority of new permanent residents each year. The system is divided into two main categories: Immediate Relatives of U.S. citizens (unlimited numbers) and Family Preference Categories (numerically limited).

Immediate Relative Categories are reserved exclusively for close family members of U.S. citizens and have no annual numerical limits. IR-1 or CR-1 visas are for spouses of U.S. citizens. If married more than two years at the time of green card approval, the spouse receives an IR-1 visa leading to a permanent 10-year green card. If married less than two years at approval, the spouse receives a CR-1 visa leading to conditional permanent residence valid for two years, after which they must file Form I-751 to remove conditions. IR-2 or CR-2 visas are for unmarried children under 21 of U.S. citizens. The CR designation (conditional residence) applies if the child's parent's marriage is less than two years old. IR-5 visas are for parents of U.S. citizens, available only when the U.S. citizen petitioner is at least 21 years old.

Because immediate relative petitions are not subject to numerical caps, they are generally processed faster than preference categories. After the U.S. citizen files Form I-130, Petition for Alien Relative, and it is approved, the beneficiary can immediately proceed to either adjustment of status (if in the U.S.) or consular processing (if abroad) without waiting for visa availability.

Family Preference Categories have annual numerical limits and are subject to per-country caps, creating backlogs and sometimes very long wait times depending on the country of birth. The four preference categories are:

F1 - Unmarried Adult Children (21 years or older) of U.S. Citizens: This category allows U.S. citizens to petition for their unmarried sons and daughters over the age of 21. Current wait times are approximately 7-8 years for most countries, but significantly longer for Mexico (approximately 23 years), Philippines (approximately 12-14 years), and other high-demand countries. If the beneficiary marries after the petition is filed but before receiving a green card, they become ineligible in this category.

F2A - Spouses and Minor Children (under 21) of Lawful Permanent Residents: This category covers the spouse and unmarried children under 21 of green card holders. Wait times are currently around 2-3 years for most countries, but can be longer for Mexico (6-8 years) and Philippines (4-6 years). F2A has historically been among the faster preference categories, and at times has been current (no waiting period). If the lawful permanent resident sponsor naturalizes and becomes a U.S. citizen while the petition is pending, the beneficiaries may be upgraded to immediate relative status (if spouse or child under 21) or F1 status (if child 21 or older).

F2B - Unmarried Adult Children (21 years or older) of Lawful Permanent Residents: This category is for unmarried sons and daughters over 21 of green card holders. Wait times are significantly longer than F2A, typically 7-9 years for most countries and 15-25+ years for Mexico and Philippines. The long wait times reflect both the numerical limits and high demand.

F3 - Married Adult Children of U.S. Citizens: U.S. citizens can petition for their married sons and daughters (of any age) along with their spouses and minor children. This category has very long wait times, generally 10-14 years for most countries and 20-28+ years for Mexico and Philippines. When a child who was in F1 category marries, they are automatically converted to F3, which has a longer wait.

F4 - Siblings of U.S. Citizens: U.S. citizens who are at least 21 years old can petition for their brothers and sisters along with their spouses and minor children. This is the longest wait category, typically 13-15+ years for most countries and 23-30+ years for Mexico and Philippines. The sibling category is often discussed for potential elimination in immigration reform proposals but remains part of current law.

Priority Dates and the Visa Bulletin are central to understanding family preference processing. When a U.S. citizen or permanent resident files Form I-130 for a family member in a preference category, the petition receives a priority date (the date USCIS receives the petition). The priority date determines the beneficiary's place in line. Each month, the U.S. Department of State publishes the Visa Bulletin, which shows cutoff dates for each preference category and country. When the Visa Bulletin shows a date later than your priority date, a visa number is available and you can proceed to the final stage (adjustment of status or consular processing).

The Visa Bulletin has two charts: the Final Action Dates (formerly the Application Final Action Dates) determine when you can actually receive your immigrant visa or green card. The Dates for Filing (formerly Filing Dates chart) may allow you to file Form I-485 early while waiting for final adjudication, but only if USCIS announces it is accepting applications based on the Dates for Filing chart. USCIS announces monthly whether it will use the Dates for Filing chart for adjustment of status applications.

Consular Processing vs. Adjustment of Status: If the beneficiary is outside the United States when their priority date becomes current, they go through consular processing. After I-130 approval and when a visa number is available, the case is forwarded to the National Visa Center (NVC), which collects fees, documents, and the DS-260 immigrant visa application. The beneficiary then attends an interview at the U.S. embassy or consulate in their country. If approved, they receive an immigrant visa and become a permanent resident upon entry to the United States.

If the beneficiary is in the United States in lawful status when their priority date becomes current, they can file Form I-485, Application to Register Permanent Residence or Adjust Status. They can remain in the U.S. while the application is pending and can apply for work authorization (Form I-765) and a travel document called advance parole (Form I-131). If approved, they become a permanent resident without leaving the United States.

Conditional Permanent Residence applies to certain family-based immigrants. Spouses who have been married less than two years when they receive their green card (whether through immediate relative or preference categories) receive conditional permanent residence valid for two years. The couple must jointly file Form I-751, Petition to Remove Conditions on Residence, during the 90-day period before the conditional green card expires. The petition must include evidence that the marriage is or was bona fide and was not entered solely to obtain immigration benefits. If approved, the conditions are removed and the person receives a 10-year green card.

If the marriage ends in divorce before filing I-751, the conditional resident can request a waiver of the joint filing requirement by demonstrating the marriage was entered in good faith but has been terminated. If the conditional resident has been subject to battery or extreme cruelty, a waiver is also available. If the joint filing requirement removal would result in extreme hardship, a waiver may be granted.

Affidavit of Support Requirements: All family-based immigration petitions require the sponsor to submit Form I-864, Affidavit of Support. This is a legally enforceable contract where the sponsor agrees to financially support the immigrant and prevent them from becoming a public charge. The sponsor must demonstrate income at least 125% of the Federal Poverty Guidelines for their household size (100% for active duty military). If the sponsor's income is insufficient, a joint sponsor (who is also a U.S. citizen or permanent resident) can submit a separate I-864, or the sponsor can use significant assets (valued at 3-5 times the income shortfall) to qualify.

The affidavit of support obligation continues until the immigrant becomes a U.S. citizen, works 40 qualifying quarters (generally 10 years), permanently leaves the United States, or dies. It is not terminated by divorce.

Aging Out and Child Status Protection Act (CSPA): Children who turn 21 while waiting for a family preference visa may age out and lose eligibility in their category. The CSPA provides some protection by allowing certain beneficiaries to subtract processing time from their age or convert to another category. For example, a child in F2A who ages out when their priority date becomes current may be able to subtract I-130 processing time from their age. If they still age out, they automatically convert to F2B if the sponsor is an LPR or F1 if the sponsor has become a U.S. citizen. CSPA calculations are complex and case-specific.

Derivative Beneficiaries: When a principal beneficiary immigrates through a preference category, their spouse and unmarried children under 21 can immigrate with them as derivative beneficiaries on the same petition, without needing separate I-130 petitions. However, derivatives must maintain their qualifying relationship - if a child turns 21 or marries before receiving their immigrant visa, they may lose derivative status.

Public Charge Inadmissibility: Family-based immigrants must not be likely to become a public charge. Under current policy, USCIS considers the totality of circumstances including age, health, family status, assets, resources, financial status, education, and skills. The properly filed Form I-864 Affidavit of Support is generally sufficient to overcome public charge concerns unless there are other significant negative factors.

Common grounds of inadmissibility that can affect family-based cases include criminal history (particularly crimes involving moral turpitude, controlled substance violations, or multiple criminal convictions), prior immigration violations (unlawful presence, visa fraud, misrepresentation), health-related grounds (communicable diseases of public health significance, failure to show required vaccinations), and security-related grounds.

Waivers may be available for certain grounds of inadmissibility. For example, Form I-601 can waive certain criminal and fraud grounds if refusal would cause extreme hardship to a qualifying U.S. citizen or LPR relative. Form I-601A allows certain individuals with unlawful presence to apply for a provisional waiver before leaving the U.S. for consular processing.
        """
    },
    "DV Lottery": {
        "title": "Diversity Visa Lottery Program",
        "visa_types": ["DV Lottery", "Green Card"],
        "description": """
The Diversity Visa (DV) Lottery program, officially known as the Diversity Immigrant Visa Program, makes up to 50,000 immigrant visas available annually to persons from countries with historically low rates of immigration to the United States. The program is administered by the U.S. Department of State and uses a computer-generated random lottery to select potential immigrants. Winning the lottery does not guarantee a green card, but provides the opportunity to apply for permanent residence if you meet all eligibility requirements.

Country Eligibility is one of the most important aspects of the DV Lottery. Each year, natives of countries that have sent more than 50,000 immigrants to the United States in the previous five years are not eligible. This means that nationals of countries with high levels of immigration to the U.S., including Mexico, Canada, China (mainland-born), India, Philippines, El Salvador, Dominican Republic, and several others, are generally not eligible to participate.

However, many Latin American countries are eligible, including Argentina, Bolivia, Chile, Colombia, Costa Rica, Ecuador, Guatemala, Honduras, Nicaragua, Panama, Paraguay, Peru, Uruguay, and Venezuela. The eligibility list changes slightly each year based on immigration patterns, so it's important to check the specific year's instructions. For DV-2027 (the lottery that would be held in late 2025 for fiscal year 2027 green cards), the eligible countries list would be published when registration opens.

If you were born in an ineligible country, you may still qualify if your spouse was born in an eligible country (you can claim your spouse's country of birth), or if neither of your parents was born in or legally resident in your country of birth at the time of your birth (you can claim one of your parents' countries of birth).

Education or Work Experience Requirement: To qualify for a diversity visa, you must meet one of two requirements. Either you must have at least a high school education or its equivalent (completion of a 12-year course of elementary and secondary education), or you must have two years of work experience within the past five years in an occupation that requires at least two years of training or experience. The Department of Labor's O*NET Online database is used to determine qualifying occupations, which must be classified in Job Zone 4 or 5, or have a Specific Vocational Preparation (SVP) rating of 7.0 or higher.

For applicants from Latin America, the high school requirement is straightforward - completion of secondary education (educación secundaria, bachillerato, preparatoria) generally qualifies. The work experience option can include skilled trades, technical positions, professional roles, and other positions requiring substantial training.

Registration Process and Timeline: The DV Lottery registration period typically opens in early October and runs for about one month (usually early October to early November). Registration is completely free and must be done electronically through the official U.S. Department of State website at dvprogram.state.gov. Only one entry per person is allowed per registration period. Submitting multiple entries will result in disqualification.

The registration requires a recent photograph meeting strict specifications (taken within the past six months, with a neutral facial expression, against a plain white or off-white background), basic biographical information including name, date and place of birth, country of eligibility, education level or work experience, and information about your spouse and all children under 21 (even if they will not immigrate with you).

Results Notification occurs in the following May (about 6-7 months after registration closes). Results are available only through the Entrant Status Check at dvprogram.state.gov. The Department of State does not send notification emails or letters to selectees. Only selected entries will be notified through the online system. If you are selected, you will receive instructions on how to proceed, including your case number.

Case Numbers and Processing: Selected applicants are assigned a case number in the format 2027SA00001234 (where SA represents South America region). Case numbers are processed in numerical order, and not all selectees will receive visas because more people are selected than the 50,000 visas available. This is because many selectees do not complete the process or are found ineligible.

Each month from October through September of the fiscal year, the Department of State publishes a Visa Bulletin showing which case numbers are current for interviews. Generally, lower case numbers become current earlier in the fiscal year, while higher numbers may become current later or not at all if the 50,000 limit is reached. Selectees should monitor the monthly Visa Bulletin and respond promptly when their number becomes current.

Completing the DV Process: If you are selected and your case number becomes current, you must complete several steps. First, you submit a DS-260, Immigrant Visa Electronic Application, online and pay the visa processing fee. Second, you compile required documents including birth certificates for you, your spouse, and all children; marriage certificate; divorce or death certificates from prior marriages; police certificates from all countries where you lived for 6+ months since age 16; court and prison records if applicable; education documents (diplomas, transcripts) or employment letters; passport-style photographs; and medical examination results from an approved panel physician.

Third, you attend an interview at the U.S. embassy or consulate. During the interview, a consular officer will verify your eligibility, review your documents, ask about your background and plans in the U.S., and determine whether you are admissible to the United States. If approved, you will receive an immigrant visa. You must enter the United States before the visa expires (typically within 6 months of issuance). Upon entry, you become a permanent resident and your physical green card will be mailed to you.

Alternatively, if you are already in the United States in lawful status and your case number is current, you may be able to adjust status by filing Form I-485 with USCIS. However, consular processing is generally faster and more common for DV selectees.

Derivatives and Family Members: If you are selected, your spouse and all unmarried children under 21 can also receive diversity visas. They are considered derivative beneficiaries and do not need to be selected separately. You must list all qualifying family members (spouse and children under 21) on your initial DV Lottery entry, even if they do not plan to immigrate with you. Failure to list eligible family members will result in disqualification.

Derivatives can accompany you or follow to join later, but they cannot receive DV visas before the principal selectee. If you marry or have a child after submitting your DV entry but before receiving your immigrant visa, you can add them to your case, though this can complicate processing.

Timeline Example for DV-2027: Registration would open in early October 2025 and close in early November 2025. Results would be available in May 2026. Interview and visa issuance would occur between October 2026 and September 30, 2027 (the end of fiscal year 2027). All diversity visas must be issued by September 30 of the fiscal year - there are no extensions or exceptions to this deadline.

Common Reasons for Denial include failure to meet education or work experience requirements, submitting fraudulent or altered documents, criminal history or other grounds of inadmissibility, prior immigration violations (overstays, illegal presence, misrepresentation), public charge concerns (though less common with proper financial preparation), and running out of time before the September 30 deadline.

Important Warnings: The only official website for DV Lottery registration is dvprogram.state.gov. Many fraudulent websites charge fees to submit entries or claim to improve your chances. The U.S. government never charges a fee for lottery registration. Be cautious of scams. Do not pay anyone to submit your entry or guarantee selection. Only consular officers can approve visa applications. No one can guarantee you a diversity visa, even if you are selected in the lottery.

Winning the DV Lottery does not exempt you from standard visa requirements. You must still be admissible to the United States, meet the education or work requirements, and complete all processing steps on time. Many selectees do not ultimately receive visas due to ineligibility, incomplete documentation, or running out of time.

For applicants from Latin America, the DV Lottery provides a valuable opportunity because many family-based and employment-based categories have long wait times. However, competition is intense and only a small fraction of entries are selected. For DV-2026, approximately 15-17 million entries were submitted worldwide for 50,000 visas. Applying each year improves your chances over time, but there is no cumulative benefit - each year is independent.

After receiving a DV green card, you have the same rights and responsibilities as any other permanent resident. You can live and work anywhere in the United States, travel freely, sponsor certain family members for green cards, and after five years (or three if married to a U.S. citizen), apply for U.S. citizenship.
        """
    },
}


async def ingest_visa_immigrant(dry_run=False, visa_types_filter=None):
    """
    Ingest immigrant visa overview data into Pinecone.

    Args:
        dry_run: If True, skip actual Pinecone upsert
        visa_types_filter: List of visa type keys to filter (e.g., ["EB-4", "EB-5"])
    """
    logger.info("Starting immigrant visa overviews ingestion")
    clients = await setup_clients()

    data = VISA_DATA
    if visa_types_filter:
        filter_set = set(visa_types_filter)
        data = {k: v for k, v in VISA_DATA.items() if k in filter_set}
        logger.info(f"Filtering to visa types: {', '.join(filter_set)}")

    all_chunks = []
    all_metadata = []

    for key, entry in data.items():
        logger.info(f"Processing {key}: {entry['title']}")
        content = f"{key}: {entry['title']}\n\n{entry['description'].strip()}"
        chunks = chunk_text(content, chunk_size=512, overlap=50)

        logger.info(f"  Created {len(chunks)} chunks for {key}")

        for chunk_idx, chunk in enumerate(chunks):
            metadata = {
                "source": f"visa_overview_{key.lower().replace('-', '_').replace('/', '_')}",
                "document_title": f"{key}: {entry['title']}",
                "visa_type": key,
                "visa_types": entry["visa_types"],
                "chunk_index": chunk_idx,
                "section": f"visa_{key.lower().replace('-', '_').replace('/', '_')}_{chunk_idx}",
            }
            all_chunks.append(chunk)
            all_metadata.append(metadata)

    if all_chunks:
        logger.info(f"Total chunks to upsert: {len(all_chunks)}")
        vectors_upserted = await upsert_to_pinecone(
            clients.index, all_chunks, all_metadata,
            source="visa_overview_immigrant", dry_run=dry_run,
        )
        logger.info(f"Ingestion complete: {vectors_upserted} vectors upserted")
    else:
        logger.warning("No chunks generated - nothing to upsert")

    return len(all_chunks)


async def main():
    parser = argparse.ArgumentParser(description="Ingest immigrant visa overview data")
    parser.add_argument("--dry-run", action="store_true", help="Skip actual Pinecone upsert")
    parser.add_argument("--visa-types", nargs="+", help="Filter to specific visa types (e.g., EB-4 EB-5)")
    args = parser.parse_args()

    await ingest_visa_immigrant(dry_run=args.dry_run, visa_types_filter=args.visa_types)


if __name__ == "__main__":
    asyncio.run(main())
