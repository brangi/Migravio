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
    "B-1/B-2": {
        "title": "Business Visitor and Tourist Visa",
        "visa_types": ["B-1/B-2", "B-1", "B-2"],
        "description": """
The B-1 and B-2 visas are the most common nonimmigrant visas for temporary visitors to the United States. The B-1 visa is for business visitors, while the B-2 visa is for tourists and those seeking medical treatment. These visas are often issued together as a combined B-1/B-2 visa.

B-1 Business Visitor activities include attending business meetings, conferences, or conventions; negotiating contracts; consulting with business associates; attending educational, professional, or business conferences; settling an estate; or engaging in independent research. B-1 visitors cannot work for a U.S. employer or receive a salary from a U.S. source, except for expense reimbursement.

B-2 Tourist Visitor activities include tourism, vacation, visiting friends and family, medical treatment, social events, amateur participation in cultural events, or enrollment in short recreational courses of study that are not for credit toward a degree.

Many nationals from Latin American countries, including Mexico, most of Central and South America, require a B visa to enter the United States. This is different from the Visa Waiver Program (VWP), which allows citizens of 41 countries to travel to the U.S. for tourism or business for stays of 90 days or less without obtaining a visa. Instead, VWP travelers must obtain authorization through the Electronic System for Travel Authorization (ESTA). Countries like Argentina, Chile, and Uruguay participate in VWP, but most Spanish-speaking countries in Latin America do not.

When you enter the U.S. on a B-1/B-2 visa, Customs and Border Protection (CBP) will issue you a Form I-94, which documents your admission and indicates your authorized period of stay. Typically, B-1/B-2 visitors are admitted for up to six months, though the officer has discretion to grant less time based on the purpose of your visit.

If you need to stay longer than the period granted on your I-94, you can apply for an extension by filing Form I-539, Application to Extend/Change Nonimmigrant Status, with USCIS. You must file this form before your authorized stay expires. Extensions are generally granted in six-month increments, but approval is not guaranteed and depends on demonstrating that you have a temporary purpose for the extension and sufficient funds to support yourself.

Important limitations of B-1/B-2 status: You cannot work in the United States, whether for compensation or volunteer work that would normally be paid employment. You cannot study full-time (more than 18 hours per week) in academic programs. You cannot establish a residence in the United States or demonstrate immigrant intent. You should maintain a residence abroad that you have no intention of abandoning.

Common reasons for B visa denials include failure to demonstrate strong ties to your home country (such as employment, family, property, or financial assets), insufficient funds to support your trip, unclear purpose of visit, or suspicion of immigrant intent. Under Section 214(b) of the Immigration and Nationality Act, all B visa applicants are presumed to be intending immigrants until they can prove otherwise.

If you are in B-1/B-2 status and want to change to another nonimmigrant status (such as F-1 student or H-1B worker), you may file Form I-539 to request a change of status. However, if you entered the U.S. with the intention of changing status or if you change status soon after entry, USCIS may view this as visa fraud or misrepresentation. It's generally recommended to wait at least 60-90 days after entry before filing for a change of status to avoid this issue.

For B-2 visitors seeking medical treatment, you should bring documentation of your medical condition, appointment letters from U.S. medical facilities, proof that you can pay for medical expenses, and evidence that you will return to your home country after treatment.
        """
    },
    "J-1/J-2": {
        "title": "Exchange Visitor Program",
        "visa_types": ["J-1", "J-2"],
        "description": """
The J-1 visa is for individuals approved to participate in work-and-study-based exchange visitor programs. The J-2 visa is for the spouse and unmarried children under 21 of J-1 visa holders. These visas are governed by the Exchange Visitor Program, administered by the U.S. Department of State.

J-1 visa categories include: Au Pair (providing childcare to American families), Camp Counselor (working at U.S. summer camps), College and University Student (studying at accredited U.S. institutions), Government Visitor (participating in government-sponsored programs), Intern (gaining exposure to U.S. business culture through structured training in their field), International Visitor (participating in educational programs on U.S. culture and society), Physician (pursuing graduate medical education or training), Professor and Research Scholar (teaching, lecturing, observing, or consulting at U.S. institutions), Short-term Scholar (lecturing, observing, consulting for up to six months), Specialist (expert in a specialized field participating in consultation or demonstration projects), Summer Work Travel (college students working and traveling during summer break), and Teacher (teaching in primary or secondary schools).

One of the most significant aspects of the J-1 visa is the two-year home-country physical presence requirement, also known as the 212(e) requirement. This applies to exchange visitors who: are government-funded (either by the U.S. or their home country), have skills in a field deemed necessary in their home country (as indicated on the Exchange Visitor Skills List), or came to receive graduate medical education or training.

If you are subject to the two-year requirement, you must return to your home country for a cumulative total of two years before you are eligible to: change status to H or L nonimmigrant categories, adjust status to permanent residence (green card) in most cases, or apply for certain immigrant visas. The two-year requirement does not necessarily prevent you from returning to the U.S. in other nonimmigrant categories like B or F status, though visa applications may be more carefully scrutinized.

To determine if you are subject to this requirement, check your DS-2019 form (the document issued by your J-1 program sponsor). Box 5 will indicate whether you are subject to the requirement. Your J-1 visa stamp will also show if you are subject to it.

Obtaining a waiver of the two-year requirement is possible but complex. There are five grounds for waiver: No Objection Statement from your home country government, Persecution (fear of persecution based on race, religion, or political opinion if you return home), Request by an Interested U.S. Government Agency, Exceptional Hardship to your U.S. citizen or permanent resident spouse or child, or Request by a state Department of Health for physicians working in underserved areas (Conrad State 30 Program).

The most commonly used waiver is the No Objection Statement, where your home country's government provides written confirmation that it has no objection to you not returning for two years. The process typically takes 4-8 months and requires filing with the Department of State, which then makes a recommendation to USCIS for final adjudication.

J-2 dependent spouses have the benefit of being able to apply for work authorization by filing Form I-765, Application for Employment Authorization Document (EAD), with USCIS. Once approved, J-2 spouses can work for any employer in the United States. However, the J-2's employment cannot be used to support the J-1 principal; rather, the J-2's income must be supplemental.

J-1 participants can generally extend their programs if their sponsor approves and the extension falls within the maximum duration allowed for their category. For example, interns can participate for up to 12 months, au pairs for up to 24 months (12 months plus one 12-month extension), and research scholars for up to five years.

Changing from J-1 to another status (like H-1B or F-1) can be done if you are not subject to the two-year requirement, or if you have already completed the two years in your home country, or if you have obtained a waiver. If you are subject to the requirement and have not fulfilled it or obtained a waiver, USCIS will deny your change of status or adjustment of status application.
        """
    },
    "M-1/M-2": {
        "title": "Vocational and Technical Student Visa",
        "visa_types": ["M-1", "M-2"],
        "description": """
The M-1 visa is for international students who want to pursue vocational or technical training in the United States. Unlike F-1 students who attend academic programs, M-1 students enroll in non-academic or vocational programs such as culinary schools, flight schools, cosmetology schools, trade schools, or technical training programs. The M-2 visa is for the spouse and unmarried children under 21 of M-1 visa holders.

To qualify for an M-1 visa, you must be enrolled in a vocational or technical program at a SEVP-certified (Student and Exchange Visitor Program) institution. The program must be full-time, meaning at least 18 clock hours per week if the course is primarily classroom instruction, or at least 22 clock hours per week if the course is primarily shop or laboratory work.

M-1 students are admitted for the length of their program plus 30 days. Unlike F-1 students who can maintain status for the duration of their studies regardless of program length, M-1 students have a maximum initial period of stay of one year. If your program is longer than one year, you can apply for extensions in one-year increments up to a maximum of three years for completing the course of study.

Extensions must be requested before your current authorized stay expires by filing Form I-539, Application to Extend/Change Nonimmigrant Status. You must demonstrate that the extension is needed due to compelling academic or medical reasons, such as changes in major or course of study, loss of credit or time due to academic probation, or documented illness.

One of the most significant restrictions of M-1 status is the extremely limited employment authorization. M-1 students cannot work while studying, either on-campus or off-campus. There is no equivalent to the F-1 student's Optional Practical Training (OPT) during the course of study. However, after completing your program, you may apply for practical training by filing Form I-765 with USCIS.

Post-completion practical training for M-1 students is limited to one month of practical training for every four months of study completed, with a maximum of six months total. For example, if you complete a 12-month vocational program, you are eligible for three months of practical training. The practical training must be in the same field as your course of study and cannot be used to get additional training.

You must apply for practical training within 60 days of completing your program, and you can only begin working after receiving your Employment Authorization Document (EAD) from USCIS. Working without authorization, even for a single day, violates your M-1 status and can have serious immigration consequences including deportation and future visa ineligibility.

M-1 students cannot change their course of study or educational objective. If you want to pursue a different vocational program, you must leave the United States and apply for a new M-1 visa. Additionally, M-1 students cannot transfer to another school unless there are compelling circumstances such as the school losing its SEVP certification or the program being discontinued.

M-1 students are prohibited from changing status to F-1 student status while in the United States. If you want to pursue academic studies instead of vocational training, you must leave the U.S. and apply for an F-1 visa. Similarly, changing from M-1 to H-1B or other work visas is possible but requires careful timing and compliance with all M-1 regulations.

M-2 dependents cannot work in the United States and cannot attend full-time study (though they may engage in part-time recreational or leisure study that is not for credit toward a degree). M-2 status is completely dependent on the M-1 principal maintaining valid status.

The Form I-20 is the key document for M-1 students, issued by your SEVP-certified school. It contains information about your program, designated school official (DSO), and authorized period of stay. You must keep your I-20 valid by maintaining full-time enrollment, reporting any changes of address to your DSO within 10 days, and not accepting unauthorized employment.

If you violate your M-1 status by working without authorization, failing to maintain full-time enrollment, or overstaying your authorized period, you will begin accruing unlawful presence. Unlawful presence of 180 days or more can trigger three- or ten-year bars to reentering the United States.
        """
    },
    "K-1/K-2": {
        "title": "Fiancé(e) Visa",
        "visa_types": ["K-1", "K-2"],
        "description": """
The K-1 visa allows the foreign-citizen fiancé(e) of a U.S. citizen to enter the United States for the purpose of getting married. The K-2 visa is for the unmarried children under 21 of the K-1 visa holder. This is a unique nonimmigrant visa because its purpose is to lead to permanent residence (a green card) through marriage.

Only U.S. citizens can petition for a K-1 fiancé(e) visa; lawful permanent residents (green card holders) cannot. The U.S. citizen sponsor must file Form I-129F, Petition for Alien Fiancé(e), with USCIS. The petition establishes that you have a bona fide relationship and intend to marry within 90 days of the foreign fiancé(e) entering the United States.

Key requirements for the K-1 visa include: Both you and your fiancé(e) must be legally free to marry, meaning any previous marriages have been legally terminated through divorce, death, or annulment. You must have met in person at least once within the two years before filing the petition. There are very limited exceptions to this requirement, such as if meeting would violate strict and long-established customs of your or your fiancé(e)'s foreign culture or social practice, or if the requirement would result in extreme hardship to the U.S. citizen petitioner.

The K-1 process involves three main stages: First, the U.S. citizen files Form I-129F with USCIS, which currently takes anywhere from 6 to 15 months for approval. Second, once approved, the petition is forwarded to the National Visa Center (NVC) and then to the U.S. embassy or consulate in the foreign fiancé(e)'s country. The foreign fiancé(e) must complete a visa application (DS-160), undergo a medical examination, and attend a visa interview. Third, once the K-1 visa is issued, the foreign fiancé(e) can travel to the United States.

Upon entering the U.S. on a K-1 visa, you must marry your U.S. citizen sponsor within 90 days. This 90-day period cannot be extended for any reason. If you do not marry within 90 days, you must leave the United States or you will begin accruing unlawful presence.

You cannot change or extend K-1 status, and you cannot change to another nonimmigrant status. The K-1 visa is strictly for the purpose of entering the U.S. to marry your petitioner. If you decide not to marry your petitioner, or if you want to marry someone else, you cannot adjust status and must leave the United States.

After marrying your U.S. citizen sponsor, you become eligible to apply for adjustment of status to lawful permanent resident (green card) by filing Form I-485. You can file immediately after marriage; there is no waiting period. Along with Form I-485, you can also file Form I-765 for work authorization and Form I-131 for a travel document (advance parole), allowing you to work and travel while your green card application is pending.

Because your marriage will be less than two years old when you receive your green card, you will receive conditional permanent residence valid for two years. To remove the conditions and obtain a 10-year green card, you and your spouse must jointly file Form I-751, Petition to Remove Conditions on Residence, during the 90-day period before your conditional green card expires.

K-1 visa holders can work in the United States only after receiving an Employment Authorization Document (EAD) by filing Form I-765. Many K-1 holders wait to file for work authorization until after marriage, when they file it together with their adjustment of status application, but you can file for work authorization while in K-1 status if needed.

K-2 children of K-1 visa holders must be listed on the original I-129F petition to be eligible for K-2 visas. They can accompany or follow to join the K-1 parent, but they must enter the U.S. on their K-2 visas before the K-1 parent marries the U.S. citizen sponsor. After the marriage, K-2 children can also apply for adjustment of status by filing their own Form I-485, even if they are stepchildren and not biologically related to the U.S. citizen.

K-2 children will also receive conditional permanent residence and must file Form I-751 to remove conditions, though they may file independently from their K-1 parent if they are over 18 when filing.

If the K-1/K-2 marriage ends in divorce before the conditions are removed, the conditional resident can still apply to remove conditions by filing Form I-751 with a request for a waiver of the joint filing requirement, demonstrating that the marriage was entered in good faith but has since been terminated.

Common reasons for K-1 visa denials include insufficient evidence of a genuine relationship, failure to meet the in-person meeting requirement, criminal history or immigration violations, inability to financially support the foreign fiancé(e) (the U.S. sponsor must file Form I-134 affidavit of support), or concerns about fraud or misrepresentation.
        """
    },
    "V": {
        "title": "V Visa for Spouses and Children of Lawful Permanent Residents",
        "visa_types": ["V"],
        "description": """
The V visa is a nonimmigrant visa category created by the Legal Immigration Family Equity (LIFE) Act of 2000 to help certain family members of lawful permanent residents (green card holders) live and work in the United States while waiting for their immigrant visas to become available. The V visa category includes V-1 (spouse of LPR), V-2 (child of LPR under 21 and unmarried), and V-3 (derivative child of V-1 or V-2).

The V visa was designed to address the long waiting periods that spouses and children of permanent residents faced under the family-based preference system. While immediate relatives of U.S. citizens can immigrate without numerical limits, spouses and children of permanent residents fall under the F2A preference category, which has annual numerical limits and can have waiting periods of several years.

Eligibility for a V visa is extremely limited due to the specific requirements written into the LIFE Act. To qualify, you must be the spouse or child of a lawful permanent resident, and the LPR must have filed a Form I-130, Petition for Alien Relative, on your behalf on or before December 21, 2000. Additionally, you must have been waiting at least three years since the I-130 was filed.

Due to the December 21, 2000 cutoff date, the V visa category is essentially frozen and applies only to a very small number of cases filed more than 25 years ago. No new V visa petitions can be filed based on I-130s submitted after this date. As a result, the V visa is rarely used today and is largely of historical significance.

If you are eligible for a V visa, you can apply by filing Form I-539, Application to Extend/Change Nonimmigrant Status, if you are already in the United States in another lawful status, or by applying at a U.S. embassy or consulate abroad if you are outside the U.S.

V visa holders are granted several important benefits. You can live in the United States while waiting for your immigrant visa number to become available. You can work by obtaining an Employment Authorization Document (EAD) by filing Form I-765. You can travel in and out of the United States, though you should maintain your V visa validity and carry proper documentation.

V nonimmigrant status continues until the immigrant visa becomes available and you either adjust status to permanent residence in the United States or obtain an immigrant visa at a consular post abroad. Once your priority date becomes current according to the monthly Visa Bulletin, you can proceed with your immigrant visa case through adjustment of status (Form I-485) or consular processing.

One advantage of the V visa is that it allows family unity during the long waiting periods that can occur in family-based immigration. Before the V visa existed, spouses and children of LPRs had to wait abroad or, if they were in the U.S. in another status, could not work or travel freely.

However, due to the December 21, 2000 filing date requirement, virtually all V visa cases have been resolved over the past two decades. Most beneficiaries with I-130s filed by that date have either received their green cards, abandoned their cases, or aged out (children turning 21).

For spouses and children of permanent residents with I-130 petitions filed after December 21, 2000, the V visa is not available. Instead, they must wait abroad or maintain another lawful status in the U.S. while their priority date becomes current. Many choose to wait in F-1 student status, H-1B work status, or other nonimmigrant categories if eligible.

An important consideration is that spouses and children in the F2A category currently face varying wait times depending on their country of birth. For most countries, the wait is 2-3 years, but for countries with high immigration demand like Mexico, Philippines, and China, the wait can be longer.

One strategy that some families use is for the LPR sponsor to naturalize and become a U.S. citizen. Once the LPR becomes a U.S. citizen, the spouse and minor unmarried children become immediate relatives with no visa wait time, allowing them to immigrate immediately. However, children who are 21 or older and unmarried would fall into the F1 category, which has longer wait times than F2A.

While the V visa category remains in the Immigration and Nationality Act, it is effectively obsolete for new cases. Immigration attorneys rarely encounter V visa cases in practice today, and USCIS processes very few V visa applications annually.
        """
    },
}


async def ingest_visa_nonimmigrant(dry_run=False, visa_types_filter=None):
    """
    Ingest nonimmigrant visa overview data into Pinecone.

    Args:
        dry_run: If True, skip actual Pinecone upsert
        visa_types_filter: List of visa type keys to filter (e.g., ["B-1/B-2", "J-1/J-2"])
    """
    logger.info("Starting nonimmigrant visa overviews ingestion")
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
            source="visa_overview_nonimmigrant", dry_run=dry_run,
        )
        logger.info(f"Ingestion complete: {vectors_upserted} vectors upserted")
    else:
        logger.warning("No chunks generated - nothing to upsert")

    return len(all_chunks)


async def main():
    parser = argparse.ArgumentParser(description="Ingest nonimmigrant visa overview data")
    parser.add_argument("--dry-run", action="store_true", help="Skip actual Pinecone upsert")
    parser.add_argument("--visa-types", nargs="+", help="Filter to specific visa types (e.g., B-1/B-2 J-1/J-2)")
    args = parser.parse_args()

    await ingest_visa_nonimmigrant(dry_run=args.dry_run, visa_types_filter=args.visa_types)


if __name__ == "__main__":
    asyncio.run(main())
