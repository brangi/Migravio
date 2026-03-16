"""
Non-immigrant work visa overviews ingestion script for Migravio RAG pipeline.

Covers: H-1B1, H-2A, H-2B, H-3, E-1, E-2, E-3, TN, R-1, P-1/P-2/P-3, Q-1, I visa

Usage:
    python scripts/ingest_visa_work.py [--dry-run] [--visa-types H-2A,TN]
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


VISA_DATA = {
    "H-1B1": {
        "title": "H-1B1 Chile/Singapore Free Trade Agreement Visa",
        "visa_types": ["H-1B1", "H-1B"],
        "description": """
The H-1B1 visa is a specialty occupation visa available exclusively to nationals of Chile and Singapore under free trade agreements with the United States. This visa offers a streamlined alternative to the traditional H-1B visa without the lottery system.

ELIGIBILITY REQUIREMENTS:
You must be a national of Chile or Singapore and possess a bachelor's degree or higher (or equivalent experience) in a specialty occupation. The position must require specialized knowledge and theoretical application of a body of highly specialized knowledge. Common qualifying occupations include engineers, computer professionals, accountants, scientists, architects, and professors. Unlike H-1B, you can apply directly without employer petition through USCIS, though you still need a job offer.

ANNUAL CAPS AND ALLOCATION:
Chile has an annual cap of 1,400 visas, while Singapore has 5,400 visas available per year. These caps are separate from the H-1B lottery system. If the cap is reached, applications are processed on a first-come, first-served basis. Historically, these caps have not been exhausted, making H-1B1 more accessible than regular H-1B visas.

APPLICATION PROCESS:
The employer must file a Labor Condition Application (LCA) with the Department of Labor, just like H-1B. However, H-1B1 applicants do not need an approved I-129 petition from USCIS. Instead, you apply directly at a U.S. consulate or embassy in Chile or Singapore, or if already in the U.S. in valid status, you can apply for a change of status with USCIS. Required documents include your degree, job offer letter, LCA, and evidence of specialty occupation requirements.

DURATION AND EXTENSIONS:
Initial H-1B1 status is granted for up to 18 months. You can extend in one-year increments indefinitely, as long as you maintain the intent to depart the U.S. upon completion of your assignment. Unlike H-1B, there is no six-year maximum limitation, but you must demonstrate non-immigrant intent at each extension or visa renewal.

DEPENDENTS:
Your spouse and unmarried children under 21 can accompany you on H-4 status. H-4 dependents of H-1B1 visa holders are not eligible for employment authorization, even if H-4 EAD policies apply to regular H-1B holders. They may study in the U.S. without changing status.

EMPLOYMENT RESTRICTIONS:
You can only work for the specific employer who filed the LCA and only in the specialty occupation and location specified. Changing employers or job positions requires a new LCA and potentially a new visa application. You cannot be self-employed or work as an independent contractor under H-1B1 status.

PATHWAY TO GREEN CARD:
H-1B1 status requires demonstration of non-immigrant intent, which can create complications if you pursue a green card. However, you can still apply for permanent residence through employer sponsorship (EB-2 or EB-3) or family-based immigration. The dual intent provision that applies to H-1B does not automatically apply to H-1B1, so consular officers may scrutinize green card applications more carefully.

COMMON PITFALLS:
Many applicants underestimate the non-immigrant intent requirement, which is more strictly enforced than with H-1B. Applying for a green card can jeopardize H-1B1 renewals. Another common issue is employer confusion about the differences between H-1B and H-1B1 filing procedures. Finally, ensure your occupation truly qualifies as a specialty occupation with appropriate documentation of degree equivalency if your degree is from outside the U.S.
        """,
    },
    "H-2A": {
        "title": "H-2A Temporary Agricultural Workers Visa",
        "visa_types": ["H-2A"],
        "description": """
The H-2A visa allows U.S. employers to hire foreign workers for temporary or seasonal agricultural work when there are not enough U.S. workers available. This visa is critical for the agricultural industry and is heavily utilized by workers from Mexico, Guatemala, Honduras, and other Latin American countries.

ELIGIBILITY REQUIREMENTS:
Workers must be nationals of countries designated by the Department of Homeland Security as eligible to participate in the H-2A program. Mexico, most Central American countries, and many South American countries are on this list. The work must be temporary or seasonal in nature, such as planting, cultivating, or harvesting crops. Workers must demonstrate intent to return to their home country after the employment period ends.

EMPLOYER REQUIREMENTS AND LABOR CERTIFICATION:
The employer must obtain a temporary labor certification from the Department of Labor proving that there are not enough U.S. workers who are able, willing, qualified, and available to perform the work. The employer must also demonstrate that hiring H-2A workers will not adversely affect the wages and working conditions of similarly employed U.S. workers. This requires extensive recruitment efforts and compliance with prevailing wage requirements, housing provisions, and worker protections.

APPLICATION PROCESS:
The employer files the labor certification application with the DOL at least 75 days before workers are needed. After certification approval, the employer submits Form I-129 to USCIS. Once approved, workers apply for H-2A visas at U.S. consulates in their home countries. The consular interview process for H-2A visas is typically streamlined for agricultural workers from Latin American countries, with group processing common in high-volume locations.

ANNUAL CAPS AND TIMELINE:
There is no annual numerical cap on H-2A visas, making this one of the most accessible work visa categories. Processing times vary, but employers should start the process at least 4-6 months before the anticipated start date. Rush processing can be requested in emergency situations. In fiscal year 2023, over 370,000 H-2A positions were certified, with Mexican nationals representing the vast majority of workers.

DURATION AND EXTENSIONS:
H-2A visas are initially granted for the period of the approved temporary labor certification, up to one year. Extensions are available in one-year increments, but total stay cannot exceed three years. After three years, workers must depart the U.S. for at least three months before applying for a new H-2A visa. There is no limit on how many times this cycle can repeat.

EMPLOYMENT AND WORKER PROTECTIONS:
H-2A workers can only perform agricultural work for the petitioning employer at the location specified in the labor certification. The employer must provide free housing that meets federal standards, pay for transportation to and from the worksite, guarantee at least three-fourths of the work hours promised in the contract, and pay at least the Adverse Effect Wage Rate (AEWR) or prevailing wage. These protections are strictly enforced, and violations can result in employer debarment from the program.

DEPENDENTS:
H-2A workers can bring spouses and children under 21 on H-4 status, but this is uncommon due to the temporary nature of agricultural work and cost considerations. H-4 dependents cannot work but may study.

PATHWAY TO GREEN CARD:
H-2A status does not provide a direct pathway to permanent residence. Most agricultural workers do not qualify for employment-based green cards due to the temporary nature of their work. However, some may qualify through family sponsorship or special agricultural worker programs if they become available through legislation.

AMERICAS-SPECIFIC NOTES:
The H-2A program is dominated by workers from Mexico and Central America, particularly Guatemala and Honduras. The U.S. government has established special processing procedures and consular resources in these countries to handle high volumes. Many Mexican workers return year after year to the same employers, creating established migration patterns. Understanding Spanish-language contract terms and worker rights is critical for this population.

COMMON PITFALLS:
Workers should carefully review their employment contracts to ensure they understand wage rates, housing arrangements, and work duration. Some employers have been found to violate worker protections, so documentation of hours worked and wages paid is essential. Workers who abandon their employment risk future visa denials. Finally, ensure your country remains on the eligible country list, which is updated periodically by DHS.
        """,
    },
    "H-2B": {
        "title": "H-2B Temporary Non-Agricultural Workers Visa",
        "visa_types": ["H-2B"],
        "description": """
The H-2B visa allows U.S. employers to bring foreign nationals to the United States to fill temporary non-agricultural jobs when there are not enough U.S. workers available. This visa is extensively used in industries such as landscaping, hospitality, seafood processing, construction, and tourism, with workers predominantly from Mexico, Central America, and the Caribbean.

ELIGIBILITY REQUIREMENTS:
Workers must be nationals of countries designated by DHS as eligible for the H-2B program. Mexico, most Central and South American countries, and Caribbean nations are included. The job must be temporary in nature, defined as: one-time occurrence, seasonal need, peak load need, or intermittent need. Common H-2B occupations include landscapers, hospitality workers, ski resort employees, seafood processors, lifeguards, amusement park workers, and construction laborers.

EMPLOYER LABOR CERTIFICATION:
The employer must obtain a temporary labor certification from the Department of Labor demonstrating that there are insufficient U.S. workers who are able, willing, qualified, and available to perform the work, and that employing H-2B workers will not adversely affect wages and working conditions of similarly employed U.S. workers. The employer must conduct recruitment, offer the prevailing wage, and meet specific advertising requirements at least 75-90 days before the anticipated start date.

APPLICATION PROCESS:
After DOL approves the labor certification, the employer files Form I-129 with USCIS. Once USCIS approves the petition, workers apply for H-2B visas at U.S. consulates. In countries with high H-2B volumes like Mexico, consulates have streamlined procedures and dedicated resources. Group processing is common for returning workers.

ANNUAL CAP AND SUPPLEMENTAL ALLOCATIONS:
The H-2B visa has an annual statutory cap of 66,000 visas (33,000 for the first half of the fiscal year, 33,000 for the second half). This cap is frequently exhausted within days of opening, making timing critical. Congress has periodically authorized supplemental H-2B visas for returning workers, adding 64,000-69,000 additional visas in recent years. Returning workers who received H-2B status in one of the previous three fiscal years may be exempt from the cap.

DURATION AND EXTENSIONS:
H-2B visas are initially granted for the period of the approved labor certification, up to one year. Extensions are available in one-year increments, but total stay cannot exceed three years. After three years, workers must depart the U.S. for an uninterrupted period of at least three months before seeking H-2B readmission. Many workers establish patterns of seasonal work, departing between contracts.

EMPLOYMENT CONDITIONS:
H-2B workers can only work for the petitioning employer at the approved location performing the specified duties. The employer must pay the prevailing wage or actual wage paid to similar workers, whichever is higher. While housing is not required (unlike H-2A), if the employer provides housing, it must meet safety standards. The employer must pay for the worker's return transportation to their home country upon completion of the contract.

DEPENDENTS:
Spouses and children under 21 may accompany H-2B workers in H-4 status. H-4 dependents cannot work but may attend school. Due to the temporary and often seasonal nature of H-2B work, many workers do not bring dependents.

PATHWAY TO GREEN CARD:
H-2B status does not provide a direct pathway to permanent residence. The temporary nature of H-2B employment makes employment-based sponsorship difficult. However, if an employer has a permanent position available, they could sponsor the worker through the PERM labor certification process for an EB-3 green card. Family-based sponsorship remains the most common path for H-2B workers seeking permanent residence.

AMERICAS-SPECIFIC NOTES:
Mexican, Guatemalan, Honduran, Jamaican, and Haitian nationals represent the majority of H-2B workers. The program is heavily used in industries with seasonal peaks, particularly in southern and coastal states. Many workers from Mexico and Central America return to the same employers year after year, creating established labor migration patterns. Understanding Spanish or Creole-language employment terms and worker rights is essential for this population.

COMMON PITFALLS:
The annual cap makes timing critical. Employers should file as early as possible when the cap opens. Workers should verify that their country is on the eligible country list. Changing employers requires a new petition and labor certification, which is time-consuming. Workers who violate their status by working for non-petitioning employers risk future visa denials. Finally, ensure you understand your employment contract, including wage rates, overtime policies, and termination provisions. Some employers have been found to make improper deductions from wages, so maintain careful records.
        """,
    },
    "H-3": {
        "title": "H-3 Trainee or Special Education Exchange Visitor Visa",
        "visa_types": ["H-3"],
        "description": """
The H-3 visa is a rare non-immigrant classification that allows foreign nationals to come to the United States to receive training from an employer in any field other than graduate medical education. There is also a special H-3 category for participants in special education exchange visitor programs.

ELIGIBILITY REQUIREMENTS:
You must be invited by a U.S. organization to participate in a training program that is not available in your home country. The training must benefit you in pursuing a career outside the United States, not for employment in the U.S. The training program must be genuine, structured, and not primarily designed to provide productive employment. You cannot fill a regular staff position or provide services that benefit the petitioning organization beyond incidental benefits from your participation in the training.

EMPLOYER PETITION REQUIREMENTS:
The petitioning organization must demonstrate that the proposed training is not available in your home country, that you will not be placed in a position that is in the normal operation of the business and in which U.S. workers are regularly employed, that you will not engage in productive employment unless it is incidental and necessary to the training, and that the training will benefit you in pursuing a career outside the United States. The petition must include a detailed training plan with the number of classroom hours, on-the-job training hours, and a week-by-week or month-by-month schedule.

APPLICATION PROCESS:
The U.S. employer files Form I-129 with USCIS, including the detailed training program description, evidence that the training is unavailable in your home country, details of any similar training programs offered, the proportion of time allocated to productive employment, and your qualifications and background. After USCIS approves the petition, you apply for the H-3 visa at a U.S. consulate. Processing times typically range from 2-4 months.

SPECIAL EDUCATION EXCHANGE VISITOR PROGRAM:
This subcategory allows participants in programs that provide practical training and experience in the education of children with physical, mental, or emotional disabilities. To qualify, you must be coming to participate in a structured program providing training and hands-on experience, and the program must be administered by a U.S. facility with professional staff and a structured curriculum for training participants in special education.

DURATION AND EXTENSIONS:
H-3 trainee status can be granted for up to two years maximum. Special education exchange visitors can stay for up to 18 months. Extensions may be granted if the training program requires additional time, but the total period cannot exceed these maximums. Unlike many other visa categories, there is no provision for indefinite extensions.

EMPLOYMENT RESTRICTIONS:
You can only participate in the training program with the petitioning organization. Any productive employment must be incidental and necessary to the training. Working outside the approved training program or in a capacity not specified in the petition violates your status. You cannot use H-3 status as a pathway to regular employment in the United States.

DEPENDENTS:
Your spouse and unmarried children under 21 can accompany you in H-4 status. H-4 dependents cannot work but may attend school. Due to the training nature and relatively short duration of H-3 status, many participants do not bring dependents.

PATHWAY TO GREEN CARD:
H-3 status does not provide a pathway to permanent residence. The entire premise of the visa is that the training will benefit you in pursuing a career outside the United States, demonstrating non-immigrant intent. Applying for a green card while in H-3 status is inconsistent with the visa requirements and could result in denial.

ANNUAL CAP:
There is no annual numerical cap on H-3 visas, though the visa is rarely used compared to other work visa categories. In most years, fewer than 200 H-3 visas are issued.

COMMON PITFALLS:
The most common reason for H-3 denial is failure to demonstrate that the training is unavailable in the applicant's home country. USCIS closely scrutinizes whether the program is genuinely training or simply disguised employment. Ensure the training plan is detailed, structured, and clearly distinguishes training activities from productive work. Another pitfall is attempting to use H-3 as a stepping stone to regular employment, which contradicts the visa requirements. Finally, some petitioners confuse H-3 with J-1 exchange visitor programs, which may be more appropriate for certain training scenarios. Consult with an immigration attorney to determine the best visa category for your specific training program.
        """,
    },
    "E-1": {
        "title": "E-1 Treaty Trader Visa",
        "visa_types": ["E-1"],
        "description": """
The E-1 visa allows nationals of countries with which the United States maintains a treaty of commerce and navigation to enter the U.S. to engage in substantial international trade on their own behalf. This visa is particularly valuable for entrepreneurs and businesses engaged in significant cross-border commerce.

ELIGIBILITY REQUIREMENTS:
You must be a national of a country that has a treaty of commerce and navigation with the United States. From the Americas, eligible countries include Argentina, Bolivia, Chile, Colombia, Costa Rica, Honduras, Mexico, Paraguay, and Suriname. You must be coming to the U.S. to carry on substantial trade, principally between the U.S. and your treaty country. "Substantial trade" means continuous flow of sizable international trade items with numerous transactions over time. The trade must be primarily (more than 50%) between the U.S. and the treaty country.

SUBSTANTIAL TRADE DEFINITION:
Trade refers to the international exchange of goods, services, technology, banking, insurance, transportation, tourism, communications, and other qualifying activities. USCIS does not set a minimum dollar amount, but the trade must be sufficient to ensure continuous flow of trade items between countries. Smaller businesses may qualify if they demonstrate numerous transactions. Trade items should be traceable through bills of lading, customs receipts, and other documentation.

PRINCIPAL TRADE REQUIREMENT:
More than 50% of the total volume of international trade must be between the United States and the treaty country. If you conduct trade with multiple countries, calculate the percentage by comparing trade with the treaty country against all international trade. Domestic U.S. trade does not count toward this calculation.

APPLICATION PROCESS:
If you are the business owner or a key employee, the employer (or you, if self-employed) files Form DS-160 and applies at a U.S. consulate in the treaty country. There is no petition filed with USCIS for initial E-1 applications made abroad. If you are already in the U.S. in another valid status, you can file Form I-129 for a change of status to E-1. You must provide evidence of your nationality, the existence of substantial trade, that trade is principally between the U.S. and treaty country, and that you are employed in a supervisory or executive capacity or possess highly specialized skills essential to the enterprise.

EMPLOYEES OF TREATY TRADERS:
Employees may qualify for E-1 status if they are the same nationality as the principal treaty trader employer, the employer is maintaining E-1 status or would qualify if applying, and the employee is employed in an executive/supervisory role or possesses skills essential to the firm's operations. Ordinary skilled or unskilled workers do not qualify.

DURATION AND EXTENSIONS:
E-1 visas are typically issued for up to five years, though the initial period of admission is usually two years. You can extend your stay indefinitely in two-year increments as long as you continue to meet E-1 requirements. There is no maximum period of stay, making E-1 one of the most flexible long-term non-immigrant visa categories.

DEPENDENTS:
Your spouse and unmarried children under 21 can accompany you in E-1 dependent status. E-1 dependents can apply for work authorization by filing Form I-765, regardless of nationality. This is a significant benefit compared to many other visa categories. Dependents may study without changing status.

PATHWAY TO GREEN CARD:
E-1 status does not provide a direct pathway to permanent residence, and you must maintain intent to depart the U.S. when your E-1 status ends. However, you can pursue a green card through other means, such as employment-based sponsorship (EB-1C for multinational managers, EB-2, or EB-5 investor visas) or family-based immigration. The E-1 visa allows for dual intent in practice, though officially it requires non-immigrant intent.

AMERICAS-SPECIFIC NOTES:
For Latin American countries with E-1 treaty status, the visa is valuable for entrepreneurs engaged in import/export businesses. Mexican nationals frequently use E-1 status for trade in goods and services across the border. Colombian nationals engaged in coffee, textiles, or technology trade have successfully obtained E-1 status. Chilean and Argentine nationals involved in wine, agricultural products, or mining-related trade are common E-1 applicants. Understanding the specific trade relationship between your country and the U.S. strengthens your application.

COMMON PITFALLS:
Many applicants fail to demonstrate that trade is "substantial." Ensure you have extensive documentation of continuous, sizable transactions. Another common error is not meeting the "principal trade" requirement. If you trade with multiple countries, carefully calculate percentages to ensure over 50% is with the treaty country. Some applicants confuse E-1 (trade) with E-2 (investment), which are distinct categories with different requirements. Finally, employees must hold the same nationality as the treaty trader; dual nationals should carefully consider which passport to use. Ordinary workers cannot qualify for E-1 status, regardless of the employer's qualification.
        """,
    },
    "E-2": {
        "title": "E-2 Treaty Investor Visa",
        "visa_types": ["E-2"],
        "description": """
The E-2 visa allows nationals of countries with which the United States maintains a treaty of commerce and navigation to enter the U.S. to develop and direct a business in which they have invested, or are actively investing, a substantial amount of capital. This is one of the most popular visa categories for entrepreneurs and investors from treaty countries.

ELIGIBILITY REQUIREMENTS:
You must be a national of a country that has a qualifying treaty with the United States. From the Americas, eligible countries include Argentina, Bolivia, Chile, Colombia, Costa Rica, Ecuador, Grenada, Honduras, Jamaica, Mexico, Panama, Paraguay, Suriname, and Trinidad & Tobago. You must have invested, or be actively in the process of investing, a substantial amount of capital in a bona fide U.S. enterprise. You must be seeking to enter the U.S. to develop and direct the investment enterprise through at least 50% ownership or possession of operational control.

SUBSTANTIAL INVESTMENT DEFINITION:
There is no fixed minimum dollar amount for a "substantial" investment. USCIS applies a proportionality test: the investment must be substantial in relationship to the total cost of purchasing or establishing the business. Generally, the lower the cost of the enterprise, the higher the investment percentage must be. For example, a $200,000 investment in a $250,000 business (80%) would typically be considered substantial, while a $200,000 investment in a $2,000,000 business (10%) would not. Investments typically range from $100,000 to $500,000, though successful E-2 cases exist both above and below this range.

MARGINALITY TEST AND BUSINESS REQUIREMENTS:
The investment must not be marginal. A marginal enterprise is one that does not have the present or future capacity to generate more than enough income to provide a minimal living for you and your family. The business must have significant economic impact, either through job creation for U.S. workers or other economic contributions. A one-person consulting business with no employees might be considered marginal, while a restaurant employing 10 workers would clearly pass the marginality test.

CAPITAL AT RISK:
The investment must be "at risk," meaning funds must be subject to partial or total loss if the business fails. Money held in a bank account is not at risk; funds used to purchase equipment, inventory, lease space, and pay salaries are at risk. You must demonstrate that capital has been irrevocably committed to the enterprise. Loans secured by the business assets may partially count, but the investment must include substantial unborrowed funds.

APPLICATION PROCESS:
Most E-2 applicants apply directly at U.S. consulates in their home countries by filing Form DS-160 and attending an interview. There is no USCIS petition required for consular applications. If you are already in the U.S. in valid status, you can file Form I-129 for change of status. You must provide evidence of your treaty country nationality, proof of substantial investment, evidence the enterprise is bona fide (business licenses, lease agreements, equipment purchases, etc.), documentation showing you will develop and direct the business, and a detailed business plan demonstrating the enterprise is not marginal.

EMPLOYEES OF E-2 ENTERPRISES:
Employees of E-2 businesses may qualify for E-2 status if they have the same nationality as the principal investor, are employed in an executive or supervisory role or possess highly specialized skills essential to the enterprise, and the employer maintains E-2 status or would qualify if applying. Unlike the investor, employees do not need to make an investment.

DURATION AND EXTENSIONS:
E-2 visas are typically issued for up to five years depending on reciprocity agreements (Mexican nationals receive four-year visas, for example). The initial period of admission is usually two years. You can extend your stay indefinitely in two-year increments as long as the business continues to meet E-2 requirements. There is no maximum period of stay, making E-2 an excellent long-term option for entrepreneurs.

DEPENDENTS:
Your spouse and unmarried children under 21 can accompany you in E-2 dependent status. E-2 spouses can apply for work authorization (Form I-765) and work for any employer without restrictions, regardless of their nationality. This is a significant advantage. Children may attend school without changing status but cannot work unless they obtain their own work authorization.

PATHWAY TO GREEN CARD:
E-2 status does not provide a direct pathway to permanent residence, and you must technically maintain intent to depart when your status ends. However, you may pursue a green card through other routes. Common pathways include EB-5 immigrant investor (minimum $800,000-$1,050,000 investment), EB-2 National Interest Waiver if your business benefits the U.S. national interest, EB-1C if you establish a multinational company with operations in your home country, or family-based sponsorship. The E-2 allows for dual intent in practice.

AMERICAS-SPECIFIC NOTES:
The E-2 visa is extremely popular among Latin American entrepreneurs and investors. Mexican nationals represent the largest group of E-2 visa holders from the Americas, commonly investing in restaurants, retail stores, import/export businesses, and franchises. Colombian investors often establish technology companies, restaurants, or real estate-related businesses. Chilean and Argentine investors frequently invest in wine businesses, restaurants, or technology startups. Costa Rican and Panamanian nationals use E-2 for service businesses and franchises. The specific reciprocity period varies by country (Mexico: 4 years, Colombia: 5 years, Argentina: 5 years).

COMMON PITFALLS:
Many applicants underestimate what constitutes "substantial" investment. Do not attempt an E-2 with minimal capital unless the total business cost is very low and the proportionality test clearly passes. Another common error is failing the marginality test. Your business plan must convincingly demonstrate significant economic impact beyond just supporting your family. Some applicants invest but fail to demonstrate they will "develop and direct" the business, which requires active involvement in management and at least 50% ownership or operational control. Passive investments do not qualify. Finally, ensure your investment is truly at risk and committed, not just sitting in a bank account or subject to easy withdrawal. Work with an immigration attorney and prepare a comprehensive business plan with financial projections demonstrating job creation and economic impact.
        """,
    },
    "E-3": {
        "title": "E-3 Specialty Occupation Visa for Australian Nationals",
        "visa_types": ["E-3"],
        "description": """
The E-3 visa is available exclusively to nationals of Australia who will perform services in a specialty occupation. This visa is similar to the H-1B but offers advantages including a separate annual cap, faster processing, and the ability to apply directly at U.S. consulates.

ELIGIBILITY REQUIREMENTS:
You must be a national of Australia and possess a legitimate offer of employment in the United States in a specialty occupation. A specialty occupation requires theoretical and practical application of a body of highly specialized knowledge and attainment of a bachelor's degree or higher (or equivalent) in the specific specialty as a minimum for entry into the occupation. Common specialty occupations include computer programmers, engineers, architects, accountants, scientists, professors, and certain medical professionals.

SPECIALTY OCCUPATION DEFINITION:
The position must meet the same specialty occupation criteria as H-1B visas. The employer must demonstrate that the position normally requires a bachelor's degree in a specific field, that the degree requirement is common in the industry, that the employer normally requires such a degree for the position, or that the duties are so specialized and complex that they require degree-level knowledge. Common qualifying fields include engineering, computer science, accounting, architecture, mathematics, physical sciences, and medicine.

ANNUAL CAP:
There is an annual cap of 10,500 E-3 visas. This cap applies only to principal applicants, not dependents. Unlike the H-1B lottery, the E-3 cap has never been exhausted, making this one of the most accessible specialty occupation visa categories for Australian nationals. Applications are processed on a first-come, first-served basis.

LABOR CONDITION APPLICATION (LCA):
The employer must file a Labor Condition Application with the Department of Labor, just like H-1B. The LCA certifies that the employer will pay the required wage (the higher of the prevailing wage or the actual wage paid to similarly employed workers), that working conditions will not adversely affect U.S. workers, and that there is no strike or lockout. The LCA must be posted at the worksite and a copy provided to you.

APPLICATION PROCESS:
Unlike H-1B, E-3 applicants do not need an approved I-129 petition from USCIS. After the employer obtains the certified LCA, you can apply directly for the E-3 visa at a U.S. consulate, typically in Australia. The consular process is generally faster than USCIS petition processing. Required documents include the certified LCA, job offer letter, your educational credentials, resume, and evidence that you meet the specialty occupation requirements. If you are already in the U.S. in valid status, you can file Form I-129 with USCIS for a change of status.

DURATION AND EXTENSIONS:
E-3 visas are typically issued for up to two years, matching the validity of the LCA. You can extend your stay in two-year increments indefinitely as long as you continue to meet E-3 requirements. There is no maximum period of stay, unlike the H-1B six-year limitation. This makes E-3 more flexible for long-term employment.

EMPLOYMENT CONDITIONS:
You can only work for the sponsoring employer in the specialty occupation and location specified in the LCA. Changing employers requires a new LCA and E-3 application or petition. You can work for multiple employers simultaneously if each obtains an LCA and you obtain E-3 status for each position. Part-time employment is permitted as long as the specialty occupation requirements are met.

DEPENDENTS:
Your spouse and unmarried children under 21 can accompany you in E-3 dependent status, regardless of their nationality. E-3 spouses can apply for work authorization (Form I-765) without restrictions, making this more advantageous than H-4 dependent status. Children may attend school but cannot work unless they obtain their own work authorization.

PATHWAY TO GREEN CARD:
E-3 status requires non-immigrant intent, but like H-1B, it allows for dual intent in practice. You can pursue a green card through employer sponsorship (EB-2 or EB-3 through PERM labor certification, or EB-1 for extraordinary ability), family-based immigration, or EB-5 investor visa. Australian nationals often pursue EB-1A (extraordinary ability) or EB-2 National Interest Waiver given Australia's highly educated workforce.

ADVANTAGES OVER H-1B:
The E-3 offers several advantages for Australian nationals: no lottery system, direct consular processing without USCIS petition for initial applications, no six-year maximum limitation, work authorization for spouses regardless of nationality, and generally faster processing. The E-3 cap has never been reached, ensuring availability.

COMMON PITFALLS:
Some applicants assume any professional job qualifies as a specialty occupation. The position must specifically require a bachelor's degree in a specialized field, not just any degree. Ensure your educational credentials clearly match the specialty occupation. Business administration or general degrees may not qualify for some positions. Another common error is failing to obtain a new LCA and E-3 approval when changing employers or work locations. Some applicants also underestimate the non-immigrant intent requirement at initial application, though filing for a green card after approval is permitted. Finally, if your degree is from outside the U.S., you may need a credential evaluation to demonstrate U.S. equivalency. Work with an immigration attorney if your situation is complex or your degree field does not obviously match the job requirements.
        """,
    },
    "TN": {
        "title": "TN USMCA Professional Visa for Canadian and Mexican Nationals",
        "visa_types": ["TN"],
        "description": """
The TN visa allows Canadian and Mexican citizens to work in the United States in certain professional occupations under the United States-Mexico-Canada Agreement (USMCA, formerly NAFTA). This visa is critical for North American professionals and offers streamlined processing without annual caps or labor certification requirements.

ELIGIBILITY REQUIREMENTS:
You must be a citizen of Canada or Mexico and have a job offer from a U.S. employer for a professional-level position on the TN occupation list. You must possess the specific educational credentials and/or experience required for that occupation. The employment must be temporary, though there is no set time limit and "temporary" is interpreted broadly. The job must be at a professional level requiring at least a bachelor's degree or appropriate credentials.

TN OCCUPATION LIST:
The USMCA specifies eligible professions, including accountant, architect, computer systems analyst, economist, engineer (various disciplines), graphic designer, hotel manager, industrial designer, interior designer, land surveyor, landscape architect, lawyer, librarian, management consultant, mathematician, range manager/conservationist, research assistant, scientific technician, social worker, sylviculturist (forestry specialist), technical publications writer, urban planner, and vocational counselor. Each occupation has specific minimum education or credential requirements. The most commonly used TN categories are engineer, computer systems analyst, management consultant, and accountant.

EDUCATIONAL AND CREDENTIAL REQUIREMENTS:
Each TN profession has specific minimum requirements. For example, "Computer Systems Analyst" requires a bachelor's degree or Post-Secondary Diploma and three years' experience. "Engineer" requires a bachelor's degree in engineering or relevant state licensure. "Management Consultant" requires a bachelor's degree and five years' experience in consulting or related field. Ensure you meet the precise requirements for your specific occupation.

APPLICATION PROCESS - CANADIAN CITIZENS:
Canadian citizens have a streamlined process and generally do not need a visa. You apply for TN status directly at a U.S. port of entry (land border or airport) with required documentation: proof of Canadian citizenship, job offer letter detailing the position and salary, evidence of professional qualifications (degree, diploma, licenses), and application fee. Processing is usually same-day. You do not need to go through a U.S. consulate or file with USCIS, though you can file Form I-129 with USCIS if preferred for advance approval.

APPLICATION PROCESS - MEXICAN CITIZENS:
Mexican citizens must apply for a TN visa at a U.S. consulate in Mexico before entering the United States. The process involves filing Form DS-160, attending a consular interview, and providing the same documentation as Canadian applicants (citizenship proof, job offer, credentials). After obtaining the TN visa, you present it at the port of entry for admission. Alternatively, if you are already in the U.S. in valid status, you can file Form I-129 with USCIS for a change of status.

NO LABOR CERTIFICATION OR PREVAILING WAGE:
Unlike H-1B and other work visas, TN status does not require a Labor Condition Application or Department of Labor prevailing wage determination. There are no restrictions on the salary amount (within reason), and no labor certification process. This significantly reduces employer administrative burden and processing time.

DURATION AND EXTENSIONS:
TN status is initially granted for up to three years. You can extend in three-year increments indefinitely. There is no maximum period of stay, and "temporary" employment is interpreted flexibly. Many TN professionals maintain status for decades. Canadian citizens can apply for extensions at the port of entry, while Mexican citizens typically extend through USCIS by filing Form I-129.

EMPLOYMENT CONDITIONS:
You can only work for the petitioning U.S. employer in the approved professional occupation. Changing employers requires a new TN application. However, you can hold multiple TN positions simultaneously if each employer supports your TN status. Self-employment is not permitted under TN status. You cannot work as an independent contractor; you must be an employee.

DEPENDENTS:
Your spouse and unmarried children under 21 can accompany you in TD (TN dependent) status, regardless of their nationality. TD dependents can study but cannot work in the United States. They cannot obtain employment authorization. This is a significant disadvantage compared to E or L visas. Some TD spouses pursue their own TN status if they qualify for a TN profession.

PATHWAY TO GREEN CARD:
TN status requires demonstration of temporary intent, which can create tension if you pursue permanent residence. However, you can apply for a green card through employer sponsorship (EB-2 or EB-3 PERM labor certification, EB-1 for extraordinary ability/multinational managers) or family-based immigration. Unlike H-1B, TN does not have official dual intent, so pursuing a green card may complicate TN renewals, particularly at the border for Canadian citizens. Many TN holders transition to H-1B status before applying for permanent residence to avoid this issue.

DIFFERENCES BETWEEN CANADIAN AND MEXICAN TN:
Canadian citizens can apply at the port of entry without a visa and receive immediate adjudication, while Mexican citizens must obtain a TN visa at a consulate before traveling. Canadian citizens can extend at the port of entry, while Mexican citizens typically extend through USCIS. Both nationalities have access to the same list of professions and the same benefits once admitted.

AMERICAS-SPECIFIC NOTES:
The TN visa is one of the most accessible work visas for Mexican professionals, avoiding the H-1B lottery. Mexican engineers, computer professionals, accountants, and management consultants commonly use TN status. The consular process in Mexico is well-established, with consulates experienced in TN applications. Many Mexican professionals maintain TN status for their entire careers. Understanding the specific educational requirements for your occupation is critical, as Mexican degrees must be evaluated for U.S. equivalency.

COMMON PITFALLS:
A common error is applying for a position that does not match a specific TN profession. Generalist positions like "project manager" or "business analyst" often do not qualify unless they meet the precise definition of an eligible profession like "management consultant" or "computer systems analyst." Ensure your job duties and title clearly align with an approved TN category. Another pitfall is insufficient evidence of educational credentials; always bring original degrees and transcripts. For Mexican applicants, ensure your degree has been evaluated for U.S. equivalency if it is not clearly comparable. Canadian applicants at the border should be prepared with detailed employer letters and all supporting documentation, as border officers adjudicate applications immediately. Finally, pursuing a green card while in TN status can jeopardize renewals, especially at the border. Consider transitioning to H-1B status first if you plan to seek permanent residence.
        """,
    },
    "R-1": {
        "title": "R-1 Religious Worker Visa",
        "visa_types": ["R-1"],
        "description": """
The R-1 visa allows foreign nationals to enter the United States to work in a religious capacity for a qualifying religious organization on a temporary basis. This visa serves ministers, religious professionals, and religious workers engaged in religious vocations and occupations.

ELIGIBILITY REQUIREMENTS:
You must have been a member of a religious denomination that has a bona fide non-profit religious organization in the United States for at least two years immediately preceding your application. You must be entering the U.S. to work in a religious capacity for this organization, either as a minister, in a religious vocation, or in a religious occupation. The religious denomination and the employing organization must be bona fide non-profit religious organizations under U.S. tax law, typically holding 501(c)(3) tax-exempt status.

RELIGIOUS WORKER CATEGORIES:
"Minister" means an individual duly authorized by a recognized religious denomination to conduct religious worship and perform other duties usually performed by clergy. "Religious vocation" means a calling to religious life evidenced by the demonstration of commitment through vows, investitures, ceremonies, or similar indicia. Examples include nuns, monks, and religious brothers/sisters. "Religious occupation" means an occupation that meets traditional religious functions, is recognized as a religious occupation within the denomination, and is primarily related to a traditional religious function. Examples include liturgical workers, religious instructors, cantors, catechists, missionaries, and religious counselors.

QUALIFYING ORGANIZATIONS:
The petitioning organization must be a bona fide non-profit religious organization exempt from taxation under section 501(c)(3) of the Internal Revenue Code. The organization must provide an IRS determination letter showing tax-exempt status or evidence of group tax exemption. The religious denomination must have a bona fide organization in the U.S. and your religious work must relate to a traditional religious function recognized within the denomination.

TWO-YEAR MEMBERSHIP REQUIREMENT:
You must have been a member of the religious denomination for at least two years immediately before filing the petition. USCIS interprets this strictly. Gaps in membership or recent conversions can be problematic. Evidence of membership includes letters from religious leaders, certificates of membership, participation in religious ceremonies, and documentation of religious activities.

APPLICATION PROCESS:
The U.S. religious organization files Form I-129 with USCIS on your behalf. Required evidence includes proof of the organization's tax-exempt status, detailed description of your proposed religious work, evidence of your membership in the denomination for two years, your religious qualifications and credentials, evidence of prior religious work experience (if any), compensation arrangements, and attestations regarding the position and your qualifications. Processing times typically range from 3-6 months. After USCIS approves the petition, you apply for an R-1 visa at a U.S. consulate.

DURATION AND EXTENSIONS:
R-1 status is initially granted for up to 30 months. You can extend for an additional 30 months, for a maximum of five years total. After five years, you must depart the U.S. and cannot return in R-1 status until you have resided outside the U.S. for one year. There are no provisions for extending beyond five years.

EMPLOYMENT CONDITIONS:
You can only work for the petitioning religious organization in the religious capacity specified in the petition. You cannot work for other employers, even in religious capacities, without obtaining separate R-1 approval. Part-time religious work is permitted if it constitutes at least 20 hours per week. Compensation can be in monetary form, room and board, or other support. Many religious workers receive minimal or no salary, which is acceptable as long as the organization provides adequate support.

DEPENDENTS:
Your spouse and unmarried children under 21 can accompany you in R-2 status. R-2 dependents cannot work but may attend school. They cannot obtain employment authorization, which can be a hardship for spouses seeking to contribute financially to the household.

PATHWAY TO GREEN CARD:
R-1 workers have a direct pathway to permanent residence through the EB-4 special immigrant religious worker category. To qualify, you must have worked as a religious worker in the U.S. in R-1 status (or other lawful status) for at least two years before filing the immigrant petition. The religious organization files Form I-360 on your behalf. After I-360 approval, you apply for a green card through adjustment of status (if in the U.S.) or consular processing. The EB-4 religious worker category has an annual cap of approximately 5,000 visas, which is sometimes reached, causing modest priority date backlogs.

COMPENSATION AND SELF-SUPPORT:
The religious organization must demonstrate ability to compensate you, though compensation can be minimal or non-monetary. The organization can provide housing, food, and other support instead of salary. However, USCIS requires evidence that you will not become a public charge and that the organization can support you. Tax returns, financial statements, and letters of support are typically required.

SITE VISITS AND COMPLIANCE:
USCIS may conduct site visits to verify the legitimacy of the religious organization and your employment. The organization should maintain contemporaneous records of your work activities, compensation, and religious duties. Compliance is important for extensions and future religious worker petitions.

COMMON PITFALLS:
The most common reason for R-1 denial is failure to demonstrate two years of continuous membership in the religious denomination. Ensure you have robust documentation spanning the full two-year period. Another common issue is insufficient evidence that the organization is a bona fide religious organization or that the position qualifies as a religious occupation. Administrative or secular positions within religious organizations generally do not qualify. For example, a janitor, secretary, or maintenance worker at a church would not qualify, even though they work for a religious organization. The position must involve traditional religious functions. Some applicants also fail to provide adequate evidence of the organization's ability to compensate or support the worker. Finally, exceeding the five-year maximum stay results in automatic ineligibility; plan your timeline carefully and pursue an EB-4 green card well before the five-year limit if you intend to remain permanently.
        """,
    },
    "P-1/P-2/P-3": {
        "title": "P-1, P-2, P-3 Athletes, Entertainers, and Cultural Performers Visa",
        "visa_types": ["P-1", "P-2", "P-3", "P"],
        "description": """
The P visa category encompasses three subcategories for internationally recognized athletes, entertainers, and culturally unique artists and performers. These visas allow temporary entry to perform at specific events or engagements.

P-1 VISA - INTERNATIONALLY RECOGNIZED ATHLETES AND ENTERTAINMENT GROUPS:

ELIGIBILITY REQUIREMENTS:
The P-1A subcategory is for individual athletes or athletic teams at an internationally recognized level of performance. You must be coming to the U.S. to participate in a specific athletic competition. "Internationally recognized" means having a high level of achievement evidenced by a degree of skill and recognition substantially above that ordinarily encountered. Major league athletes, Olympic athletes, and internationally competitive players qualify.

The P-1B subcategory is for members of internationally recognized entertainment groups. The group must have been established and performing regularly for at least one year, and at least 75% of the members must have had a substantial and sustained relationship with the group for at least one year. Individual entertainers do not qualify for P-1B; they must apply for O-1 or other visa categories.

APPLICATION PROCESS FOR P-1:
The U.S. employer, sponsor, or agent files Form I-129 with USCIS. For P-1A athletes, required evidence includes a contract with a major U.S. sports league or team, evidence of international recognition (participation in prior international competitions, significant recognition in multiple countries, rankings, awards, etc.), and written consultation from an appropriate labor organization. For P-1B entertainment groups, evidence includes proof the group is internationally recognized (major awards, critical reviews, international performances, commercial success, etc.), proof of sustained substantial relationship of members, and an itinerary of performances.

DURATION FOR P-1:
P-1 status is granted for the time needed to complete the event, competition, or performance, up to an initial period of one year for athletes or six months for entertainment groups (if performing a specific event) or one year (if touring). Extensions are available in one-year increments. Athletes can remain in P-1 status for up to five years total, while entertainment groups can extend as needed for continuing engagements.

P-2 VISA - RECIPROCAL EXCHANGE PROGRAM ARTISTS AND ENTERTAINERS:

ELIGIBILITY REQUIREMENTS:
You must be coming to the U.S. to perform under a reciprocal exchange program between U.S. and foreign organizations. The exchange must be between an organization in the United States and an organization in another country involving the temporary exchange of artists and entertainers. Individual performers or groups may qualify. The program must provide for the exchange of artists/entertainers and must be of comparable terms and conditions.

APPLICATION PROCESS FOR P-2:
The U.S. employer or sponsoring organization files Form I-129. Required evidence includes a formal reciprocal exchange agreement between the U.S. organization and the foreign organization, an itinerary of performances or events, evidence of your qualifications and experience, and written consultation from an appropriate labor organization. The reciprocal exchange agreement must be documented and verifiable.

DURATION FOR P-2:
P-2 status is granted for the time needed to complete the exchange program, up to an initial period of one year. Extensions are available in one-year increments for continuing exchange activities.

P-3 VISA - CULTURALLY UNIQUE ARTISTS AND ENTERTAINERS:

ELIGIBILITY REQUIREMENTS:
You must be coming to the U.S. to perform, teach, or coach under a culturally unique program. "Culturally unique" means a style of artistic expression, methodology, or medium that is unique to a particular country, nation, society, class, ethnicity, religion, tribe, or other group. The program must be cultural, and your performance, teaching, or coaching must be cultural in nature. Examples include ethnic dancers, folk musicians, traditional artists, indigenous performers, and cultural instructors.

APPLICATION PROCESS FOR P-3:
The U.S. employer, agent, or sponsoring organization files Form I-129. Required evidence includes affidavits, testimonials, or letters from recognized experts attesting to the authenticity of your skills and that the performance is culturally unique, documentation proving you are qualified to perform in the culturally unique art form, and evidence that all performances will be culturally unique events. An itinerary and written consultation from an appropriate labor organization are also required.

DURATION FOR P-3:
P-3 status is granted for the time needed to complete the cultural program, up to one year. Extensions are available in one-year increments as long as you continue to perform culturally unique services.

EMPLOYMENT CONDITIONS:
P visa holders can only perform for the petitioning employer or at the events/venues specified in the petition and itinerary. Changing employers or adding performances requires amended or new petitions. Multiple employers can petition for the same beneficiary if separate petitions are filed.

DEPENDENTS:
Spouses and unmarried children under 21 may accompany P visa holders in P-4 status. P-4 dependents cannot work but may attend school. They cannot obtain employment authorization.

PATHWAY TO GREEN CARD:
P visas do not provide a direct pathway to permanent residence, though individuals with extraordinary ability may qualify for EB-1 green cards (EB-1A for extraordinary ability or EB-1B for outstanding professors/researchers). Family-based sponsorship is also possible. The temporary nature of P status requires non-immigrant intent.

LABOR CONSULTATION REQUIREMENT:
All P petitions require written consultation from an appropriate labor organization regarding the nature of the work and the beneficiary's qualifications. For athletes, this is typically a players' association or sports federation. For entertainers, this is usually a relevant entertainment union (ATSFA, AGMA, etc.). If no labor organization exists, USCIS may waive this requirement.

COMMON PITFALLS FOR P-1:
Many applicants overestimate their level of international recognition. "Internationally recognized" requires significant evidence of sustained achievement at a high level. Regional success or national recognition within one country is typically insufficient. Entertainment groups must prove sustained membership of at least 75% of the group for at least one year, which requires substantial documentation of performances and membership. Individual entertainers often incorrectly apply for P-1B when they should apply for O-1 instead.

COMMON PITFALLS FOR P-2:
The reciprocal exchange agreement must be formal and documented, not informal or oral. Some applicants confuse P-2 with J-1 exchange visitor visas; ensure you choose the correct category. The exchange must involve comparable terms and must be between organizations, not informal arrangements.

COMMON PITFALLS FOR P-3:
The most common error is failing to demonstrate that the performance is truly "culturally unique" to a specific group. General artistic performance that happens to be traditional is insufficient; the performance must be inherently tied to the cultural heritage of a specific ethnicity, tribe, religion, or nation. Modern interpretations or fusion performances may not qualify. Ensure expert affidavits clearly articulate why your art form is culturally unique and authentic to a specific cultural tradition.
        """,
    },
    "Q-1": {
        "title": "Q-1 Cultural Exchange Visitor Visa",
        "visa_types": ["Q-1"],
        "description": """
The Q-1 visa allows foreign nationals to participate in international cultural exchange programs that provide practical training, employment, and the sharing of the history, culture, and traditions of their home country. This visa is designed for cultural education and exchange, not permanent employment.

ELIGIBILITY REQUIREMENTS:
You must be at least 18 years old and able to communicate effectively about the cultural attributes of your country. You must be qualified to perform the service or labor, or receive the type of training stated in the petition. You must be coming to the U.S. to participate in a designated international cultural exchange program that shares the culture of your country through work, training, and cultural activities.

QUALIFYING INTERNATIONAL CULTURAL EXCHANGE PROGRAM:
The petitioning employer must have an established international cultural exchange program that has been designated by USCIS. The program must be designed to share the culture of your country with the American public through your employment or training. The cultural component must be an essential and integral part of the program, not merely incidental to employment. The program must take place in a school, museum, business, or other establishment where the public or a segment of the public will be exposed to aspects of your country's culture.

EMPLOYER REQUIREMENTS:
The U.S. employer must file Form I-129 with a detailed description of the cultural exchange program, evidence that the program is designed to exhibit and share your country's culture with the American public, the employer's plan for providing public access to the cultural component, the work duties you will perform and how they relate to cultural sharing, and evidence that you are qualified to perform the work and communicate about your culture. The employer must demonstrate that the cultural component is significant and essential to the program.

COMMON Q-1 PROGRAMS:
Q-1 visas are most commonly used by international cultural exchange programs at theme parks (such as Disney's Cultural Representative Program or similar programs at other entertainment venues), cultural festivals, museums with international exhibits, folk art schools, and international culinary programs. For example, a chef from Mexico working at a Mexican restaurant that offers cultural education to customers and staff about Mexican culinary traditions might qualify, provided the program has a substantial educational component.

APPLICATION PROCESS:
The U.S. employer files Form I-129 designating the international cultural exchange program and requesting Q-1 status for you. USCIS must approve the designation of the program before approving the petition. Required evidence includes a detailed description of the structured cultural component, how the public will be exposed to your culture, your qualifications, the nature of your employment, and evidence that you will return to your home country upon completion. After USCIS approves the petition, you apply for a Q-1 visa at a U.S. consulate.

DURATION AND LIMITATIONS:
Q-1 status is granted for the length of the approved cultural exchange program, up to a maximum of 15 months. Extensions are not available. After your 15-month Q-1 program ends, you must depart the United States and remain outside for at least one year before you can receive another Q-1 visa. This one-year foreign residence requirement is strictly enforced.

EMPLOYMENT AND PROGRAM CONDITIONS:
You can only participate in the designated cultural exchange program for the petitioning employer. The work you perform must relate directly to sharing your country's culture. While you will be employed and compensated, the primary purpose is cultural exchange, not simply filling a labor need. You must actively participate in the cultural sharing component, such as giving presentations, demonstrating cultural practices, teaching about your country's traditions, or engaging with the public in cultural education.

COMPENSATION:
You must receive compensation comparable to that received by similarly employed U.S. workers in the same locality. The employer must pay at least the minimum wage required by federal or state law, whichever is higher. Housing and other benefits may be provided as part of the compensation package.

DEPENDENTS:
Spouses and unmarried children under 21 may accompany you in Q-3 status (for Irish cultural exchange participants) or must use other visa categories. Unlike many work visa categories, there is no specific dependent classification for Q-1 family members in most cases. Family members typically visit using B-2 tourist visas or apply for other appropriate visa categories.

PATHWAY TO GREEN CARD:
Q-1 status does not provide a pathway to permanent residence. The visa requires demonstration of non-immigrant intent and the intent to return to your home country upon completion of the program. The 15-month limitation and one-year foreign residence requirement reinforce the temporary nature of the program.

DIFFERENCE BETWEEN Q-1 AND J-1:
Both Q-1 and J-1 visas involve cultural exchange, but they have different purposes and structures. J-1 visas encompass broader exchange programs including students, scholars, trainees, teachers, and au pairs, often with educational institutions or designated sponsor organizations. J-1 can involve longer durations and sometimes has two-year home residency requirements. Q-1 is specifically for cultural sharing through employment at designated programs, with a maximum 15-month duration. Q-1 is more focused on cultural exhibition through work, while J-1 emphasizes educational and professional exchange.

COMMON PITFALLS:
The most frequent reason for Q-1 denial is failure to demonstrate a substantial and essential cultural component to the program. Simply employing foreign workers in culturally-related businesses is insufficient; there must be active, structured sharing of culture with the American public. Another common error is inadequate description of how the public will be exposed to the cultural component. USCIS expects detailed plans showing public interaction, demonstrations, presentations, or educational activities. Some applicants also fail to demonstrate qualifications to effectively communicate about their culture. Language skills and cultural knowledge must be documented. Finally, exceeding the 15-month maximum or failing to depart for one year before seeking another Q-1 will result in denial. Plan your timeline carefully, as there are no extensions or exceptions to the 15-month rule.
        """,
    },
    "I": {
        "title": "I Visa for Foreign Media and Journalists",
        "visa_types": ["I"],
        "description": """
The I visa is designed for representatives of foreign media, including journalists, film crews, editors, and similar occupations, who are traveling to the United States to engage in their profession. This visa category recognizes the unique role of international press and media in covering U.S. events and issues.

ELIGIBILITY REQUIREMENTS:
You must be a representative of foreign media coming to the U.S. to engage in your profession as a journalist, reporter, film crew member, editor, or similar occupation. "Foreign media" includes press, radio, film, print journalism, and other information media. You must be working for a foreign media organization that has a home office in a foreign country. The activities you will engage in must be essential to the foreign media function and typically include gathering news, reporting on events, conducting interviews, filming documentaries, or producing media content about U.S. subjects.

QUALIFYING MEDIA ACTIVITIES:
Qualifying activities include reporting news, conducting interviews, filming news stories or documentaries, covering U.S. political events, sporting events, or cultural happenings, gathering information for publication or broadcast in foreign media, and operating in a professional media capacity. The key requirement is that the activity is informational in nature and will be disseminated to a foreign audience through foreign media channels.

NO PETITION REQUIRED:
Unlike most work visas, the I visa does not require a U.S. employer to file a petition with USCIS. You apply directly at a U.S. consulate or embassy. This streamlined process recognizes the need for foreign journalists to cover breaking news and time-sensitive events.

APPLICATION PROCESS:
You file Form DS-160 and apply for an I visa at a U.S. consulate or embassy. Required documentation includes a letter from your employer (the foreign media organization) on company letterhead stating your position, describing your media activities in the U.S., confirming your employment status, and outlining the purpose and duration of your U.S. assignment. You should also provide evidence of your credentials as a journalist or media professional (press credentials, portfolio of published work, journalism degree, etc.), a detailed itinerary of your activities in the U.S., and proof of the foreign media organization's existence and operations.

DURATION OF STAY:
I visa validity varies based on reciprocity agreements between the U.S. and your country, but visas are often issued for multiple years with multiple entries. However, your period of admission into the United States is typically granted for the duration of your assignment or activities, as indicated in your supporting documentation. There is no fixed maximum period of stay. As long as you continue to engage in qualifying media activities for a foreign media organization, you can remain in I status.

EXTENSIONS AND CONTINUING STATUS:
If you need to extend your stay beyond your initially stated assignment, you can apply for an extension by filing Form I-539 with USCIS or by departing and re-entering the U.S. with your I visa (if still valid) and updated assignment documentation. Many I visa holders maintain status for years while assigned to cover U.S. affairs for their foreign media organizations.

FREELANCE JOURNALISTS:
Freelance journalists can qualify for I visas if they can demonstrate a contract or regular working relationship with a foreign media organization. You must provide contracts, letters of assignment, or evidence of a sustained professional relationship showing that you will be gathering information to be disseminated through foreign media. Purely independent blogging or social media posting without ties to established foreign media generally does not qualify.

EMPLOYMENT RESTRICTIONS:
You can only engage in activities related to your media profession for the foreign media organization specified in your visa application. You cannot accept regular employment with U.S. companies, though you may report on U.S. subjects and conduct business necessary for your media work (interviews, filming, research, etc.).

DEPENDENTS:
Spouses and unmarried children under 21 may accompany you in I status. I dependents cannot work but may attend school. Unlike some other visa categories, there is no employment authorization available for I visa dependents.

PATHWAY TO GREEN CARD:
I visa status does not provide a pathway to permanent residence. The visa is intended for representatives of foreign media temporarily in the U.S. for professional activities. However, you may pursue a green card through other means such as employer sponsorship by a U.S. media organization (if you transition to U.S. employment) or family-based immigration.

JOURNALISTS VS. OTHER MEDIA VISITORS:
It is important to distinguish I visa activities from those that might be permissible under the Visa Waiver Program (VWP) or B-1 visitor visas. If you are coming for a very brief assignment (such as covering a single event for a few days) and will not be paid by a U.S. source, you might qualify for B-1 or VWP. However, if you will be stationed in the U.S. for extended reporting, will be working for an extended period, or will be employed by a U.S.-based bureau of a foreign media organization, you should obtain an I visa.

FREEDOM OF PRESS CONSIDERATIONS:
The I visa recognizes the importance of international press freedom and the role of foreign media in covering U.S. events. U.S. policy generally supports facilitating legitimate media activities. However, the visa does not provide immunity from U.S. laws, and journalists must comply with applicable regulations, including laws regarding access to certain locations or events.

COMMON PITFALLS:
Some applicants fail to provide sufficient evidence that they are employed by or under contract with a recognized foreign media organization. Independent bloggers or social media influencers without ties to established media often do not qualify. Another common error is insufficient documentation of the planned media activities. Provide a detailed itinerary, assignment letter, and description of the stories or content you will produce. Some journalists incorrectly use B-1 visitor visas when their activities require I visas, particularly if they will be in the U.S. for extended periods or stationed at a U.S. bureau. Finally, ensure the letter from your employer clearly states that the media organization is based in a foreign country and that your work product will be disseminated to a foreign audience. Working primarily for U.S. media outlets requires different visa categories (such as H-1B or O-1).
        """,
    },
}


async def ingest_visa_work(dry_run=False, visa_types_filter=None):
    """Ingest work visa overviews into Pinecone."""
    logger.info("Starting work visa overviews ingestion")
    clients = await setup_clients()

    data = VISA_DATA
    if visa_types_filter:
        filter_set = set(visa_types_filter)
        data = {k: v for k, v in VISA_DATA.items() if k in filter_set}
        logger.info(f"Filtering to visa types: {', '.join(visa_types_filter)}")

    all_chunks = []
    all_metadata = []

    for key, entry in data.items():
        content = f"{key}: {entry['title']}\n\n{entry['description'].strip()}"
        chunks = chunk_text(content, chunk_size=512, overlap=50)

        logger.info(f"Processing {key}: {len(chunks)} chunks")

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
        vectors_upserted = await upsert_to_pinecone(
            clients.index, all_chunks, all_metadata,
            source="visa_overview", dry_run=dry_run,
        )
        logger.info(f"Ingestion complete: {vectors_upserted} vectors upserted")
    else:
        logger.warning("No chunks to ingest")


def main():
    parser = argparse.ArgumentParser(description="Ingest work visa overviews into Pinecone")
    parser.add_argument("--dry-run", action="store_true", help="Preview chunks without upserting to Pinecone")
    parser.add_argument("--visa-types", type=str, help="Comma-separated visa types to ingest (e.g., H-2A,TN,E-2)")
    args = parser.parse_args()

    visa_types_filter = args.visa_types.split(",") if args.visa_types else None
    asyncio.run(ingest_visa_work(dry_run=args.dry_run, visa_types_filter=visa_types_filter))


if __name__ == "__main__":
    main()
