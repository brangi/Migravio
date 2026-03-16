"""
Extended USCIS forms ingestion script for Migravio RAG pipeline.

Covers additional forms beyond the base 6 (I-485, I-130, I-539, I-765, I-131, N-400):
I-140, I-129, I-129F, I-589, I-918, I-914, I-360, I-526E, I-864, I-693, I-90

Usage:
    python scripts/ingest_forms_extended.py [--dry-run] [--forms I-140,I-129]
"""

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


FORM_DATA = {
    "I-140": {
        "title": "Immigrant Petition for Alien Workers",
        "form_url": "https://www.uscis.gov/i-140",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-140instr.pdf",
        "visa_types": ["EB-1", "EB-2", "EB-3", "Green Card"],
        "description": """
Form I-140 is the Immigrant Petition for Alien Workers, filed by U.S. employers to sponsor foreign workers for permanent residence (green card) through employment-based immigration. This form is also used for self-petitioning by individuals in certain extraordinary ability categories.

**Who Should File**: Form I-140 is typically filed by a U.S. employer petitioning for a foreign worker in the EB-1, EB-2, or EB-3 employment-based preference categories. Self-petitioning is allowed for EB-1A (Extraordinary Ability) and EB-2 NIW (National Interest Waiver) cases, where the foreign national files without employer sponsorship.

**Eligibility Requirements**: The eligibility depends on the employment-based category. EB-1A requires extraordinary ability in sciences, arts, education, business, or athletics. EB-1B requires outstanding professors and researchers. EB-1C requires multinational managers or executives. EB-2 requires advanced degree professionals or exceptional ability (with NIW option). EB-3 requires skilled workers, professionals, or other workers. Most categories require an approved PERM labor certification before filing I-140, except EB-1 (all subcategories) and EB-2 NIW.

**Required Documents**: Documentation varies by category but generally includes proof of the job offer, employer's ability to pay the proffered wage (tax returns, annual reports, audited financial statements), employee's qualifications (diplomas, transcripts, licenses, letters of experience), and category-specific evidence. EB-1A requires extensive evidence of sustained national or international acclaim. EB-2 NIW requires showing the proposed endeavor has substantial merit and national importance. For cases requiring PERM, the approved ETA-9089 labor certification must be included.

**Filing Fees**: The standard filing fee for Form I-140 is $700 (as of 2026). Premium Processing Service is available for an additional fee of $2,805, which guarantees 15-business-day processing. The Asylum Program Fee of $600 also applies to most I-140 petitions filed on or after May 30, 2024, bringing the total standard filing fee to $1,300.

**Processing Time**: Regular processing typically takes 4-8 months, though times vary significantly by service center and visa category. Premium Processing reduces this to 15 business days. Approval rates are generally high for well-documented petitions, particularly for EB-1A and EB-2 NIW cases with strong evidence.

**Priority Date**: The priority date for I-140 petitions is critical for green card processing. For cases requiring PERM, the priority date is the date the labor certification application was accepted for processing by the Department of Labor. For cases that do not require PERM (EB-1 and EB-2 NIW), the priority date is the date USCIS receives the I-140 petition. This date determines when the beneficiary can file for adjustment of status (I-485) based on visa bulletin cutoff dates.

**After Filing**: Once approved, the I-140 establishes the foreign worker's eligibility for permanent residence in the specified category. The beneficiary can then file Form I-485 to adjust status to permanent resident when their priority date becomes current according to the monthly Visa Bulletin. If the beneficiary is outside the U.S., they proceed through consular processing for an immigrant visa. AC21 portability provisions allow changing employers 180 days after I-485 filing while maintaining the approved I-140's priority date, provided the new job is in the same or similar occupational classification.

**Common Issues**: Requests for Evidence (RFEs) commonly address lack of evidence proving the employer's ability to pay, insufficient documentation of the beneficiary's qualifications, or inadequate proof of meeting the specific category requirements. For EB-1A, insufficient evidence of sustained acclaim is common. For EB-2 NIW, failure to demonstrate the national importance of the proposed endeavor is frequent. Denials can occur if PERM labor certification is found to have been improperly obtained or if fraud is detected.
""",
    },
    "I-129": {
        "title": "Petition for Nonimmigrant Worker",
        "form_url": "https://www.uscis.gov/i-129",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-129instr.pdf",
        "visa_types": ["H-1B", "L-1", "O-1", "TN", "E-1", "E-2", "P-1", "H-2A", "H-2B", "R-1"],
        "description": """
Form I-129 is the Petition for Nonimmigrant Worker, used by U.S. employers to sponsor foreign nationals for temporary work authorization in various nonimmigrant classifications including H-1B, L-1, O-1, P-1, H-2A, H-2B, R-1, E-3, TN, and others. This form is the primary mechanism for employment-based temporary work visas.

**Who Should File**: A U.S. employer, U.S. agent, or foreign employer through a U.S. agent must file Form I-129 to petition for a foreign worker in a temporary nonimmigrant work classification. The employer is the petitioner, and the foreign worker is the beneficiary. Individual workers cannot self-petition using this form.

**Eligibility Requirements**: Eligibility varies dramatically by visa classification. H-1B requires a bachelor's degree or higher in a specialty occupation and Labor Condition Application (LCA) from the Department of Labor. L-1A/L-1B requires employment with a related foreign company for at least one continuous year in the preceding three years in a managerial, executive, or specialized knowledge capacity. O-1A requires extraordinary ability in sciences, education, business, or athletics with sustained national or international acclaim. O-1B is for extraordinary ability in arts or extraordinary achievement in motion pictures or television. P-1 is for internationally recognized athletes or entertainment groups. H-2A is for temporary agricultural workers when U.S. workers are unavailable. H-2B is for temporary non-agricultural workers. R-1 requires at least two years membership in a religious denomination for religious workers. E-3 is specifically for Australian nationals in specialty occupations. TN is for Canadian and Mexican NAFTA professionals.

**Required Documents**: All I-129 petitions require the basic form plus a classification-specific supplement (H, L, O, P, Q, R, or E). Supporting documentation varies by classification but generally includes evidence of the employer-employee relationship, job offer details, beneficiary's qualifications, and proof the position meets classification requirements. H-1B requires an approved LCA, degree credentials, and evidence the position is a specialty occupation. L-1 requires proof of qualifying relationship between U.S. and foreign entities, organizational charts, and evidence of beneficiary's qualifying employment abroad. O-1 requires extensive documentation of extraordinary ability including awards, published material, judging, original contributions, and consultation letters. P-1 requires itinerary and evidence of international recognition.

**Filing Fees**: The base filing fee for Form I-129 is $460 (as of 2026). Additional fees may apply: H-1B petitions require a $500 fraud prevention and detection fee, and some employers must pay the $750 or $1,500 ACWIA training fee. Companies with 50+ employees where more than 50% hold H-1B or L-1 status must pay a $4,000 fee. L-1 blanket petitions have different fee structures. Premium Processing Service is available for most classifications at $2,805 for 15-business-day processing.

**Processing Time**: Regular processing ranges from 2-6 months depending on service center and classification. Premium Processing reduces this to 15 business days for classifications where available. H-1B cap cases filed in April have a multi-month lottery and processing timeline. Extensions and amendments typically process faster than initial petitions.

**After Filing**: Upon approval, USCIS issues Form I-797 approval notice. Beneficiaries outside the U.S. must apply for the corresponding visa at a U.S. embassy or consulate and then seek admission at a port of entry. Beneficiaries already in the U.S. in valid status can begin working on the start date indicated on the I-797, though some classifications require the actual visa stamp for international travel. Many I-129 classifications allow change of status from another nonimmigrant category without leaving the U.S.

**Common Issues**: H-1B petitions face scrutiny on specialty occupation requirements and employer-employee relationship, especially for third-party placement. L-1 petitions often receive RFEs questioning the qualifying relationship between entities or the specialized knowledge claimed. O-1 cases may face challenges proving sustained acclaim and distinction. H-2A and H-2B require Department of Labor temporary labor certification showing unavailability of U.S. workers. Extensions may be denied if the beneficiary accumulated unlawful presence or violated status. Blanket L petitions require substantial documentation of corporate structure and U.S.-foreign entity relationships. TN petitions must strictly comply with NAFTA professional categories and documentation requirements.
""",
    },
    "I-129F": {
        "title": "Petition for Alien Fiancé(e)",
        "form_url": "https://www.uscis.gov/i-129f",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-129finstr.pdf",
        "visa_types": ["K-1", "K-2"],
        "description": """
Form I-129F is the Petition for Alien Fiancé(e), filed by a U.S. citizen to bring a foreign fiancé(e) to the United States for the purpose of marriage. This petition initiates the K-1 nonimmigrant visa process, allowing the couple to marry within 90 days of the fiancé(e)'s arrival in the U.S.

**Who Should File**: Only U.S. citizens can file Form I-129F for a K-1 fiancé(e) visa. Lawful permanent residents (green card holders) cannot use this form; they must wait until citizenship or sponsor their spouse through the immigrant visa process after marriage. The petitioner must intend to marry the beneficiary within 90 days of their admission to the United States and must be legally free to marry (any previous marriages must have been legally terminated).

**Eligibility Requirements**: Both the U.S. citizen petitioner and the foreign fiancé(e) must be legally free to marry, meaning any previous marriages have been legally terminated through divorce, annulment, or death. The couple must have met in person at least once within the two years immediately before filing the petition, though USCIS may waive this requirement if it would result in extreme hardship to the petitioner or would violate strict and long-established customs of the beneficiary's foreign culture or social practice. The meeting requirement is strictly enforced and requires substantial documentation. The couple must have a bona fide intention to marry, not simply to obtain immigration benefits.

**Required Documents**: Documentation must include proof of U.S. citizenship (passport, birth certificate, or naturalization certificate), proof of legal termination of any previous marriages (divorce decrees, annulment papers, or death certificates for both parties), evidence of meeting in person within the past two years (photographs together with visible dates, boarding passes, passport stamps, hotel receipts, affidavits from witnesses), passport-style photos of both parties, and evidence of ongoing bona fide relationship (correspondence, phone records, travel records, relationship timeline). If requesting a waiver of the in-person meeting requirement, detailed documentation supporting extreme hardship or cultural barriers must be provided.

**Filing Fees**: The filing fee for Form I-129F is $535 (as of 2026). There is no premium processing available for this petition. If the petition is approved, the beneficiary will later pay separate visa application fees to the Department of State (DS-160 fee) and medical examination fees. The K-1 visa application fee is $265.

**Processing Time**: USCIS processing of Form I-129F typically takes 6-10 months, though times vary by service center. After USCIS approval, the petition is forwarded to the National Visa Center (NVC) and then to the U.S. embassy or consulate in the beneficiary's country, adding another 2-4 months for consular processing, interview scheduling, medical examination, and visa issuance. Total time from filing to visa issuance averages 8-14 months.

**After Filing and Approval**: Once USCIS approves the I-129F, the petition is sent to the National Visa Center and then forwarded to the appropriate U.S. embassy or consulate. The beneficiary will receive instructions to complete Form DS-160 (Online Nonimmigrant Visa Application), pay visa fees, undergo a medical examination by an approved panel physician, and attend a visa interview. If approved, the K-1 visa is typically valid for six months from issuance for a single entry. Upon admission to the U.S., the beneficiary must marry the U.S. citizen petitioner within 90 days. The K-1 status cannot be extended beyond 90 days, and failure to marry within this timeframe requires departure from the U.S. After marriage, the foreign spouse files Form I-485 (Application to Register Permanent Residence or Adjust Status) along with Form I-765 (work authorization) and Form I-131 (travel document) to obtain a green card.

**K-2 Derivative Status**: Unmarried children under 21 of the K-1 beneficiary may accompany or follow to join the principal beneficiary in K-2 status. They must be listed on the I-129F petition. K-2 children receive the same 90-day admission period and must adjust status through I-485 filing when the K-1 parent marries the petitioner.

**Common Issues**: The most common reasons for denial include failure to prove the in-person meeting requirement with adequate documentation, inability to demonstrate a bona fide relationship (suspicion of fraud or marriage for immigration benefits), criminal history or immigration violations by either party, previous denial of K-1 petition for the same couple, or failure to establish legal termination of prior marriages. Background checks can reveal inconsistencies or misrepresentations that lead to denial. At the consular interview stage, beneficiaries may be denied if they cannot demonstrate nonimmigrant intent (the intent to marry and adjust status rather than immigrate through another route) or if relationship fraud is suspected. Security clearances and administrative processing can significantly delay visa issuance.
""",
    },
    "I-589": {
        "title": "Application for Asylum and for Withholding of Removal",
        "form_url": "https://www.uscis.gov/i-589",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-589instr.pdf",
        "visa_types": ["Asylum", "Withholding of Removal", "CAT"],
        "description": """
Form I-589 is the Application for Asylum and for Withholding of Removal, used by individuals physically present in the United States or seeking admission at a port of entry to request protection from persecution or torture if returned to their home country. This form also serves as an application for protection under the Convention Against Torture (CAT).

**Who Should File**: Any individual who is physically present in the United States or arriving in the United States (regardless of immigration status) and fears persecution in their home country based on race, religion, nationality, membership in a particular social group, or political opinion may file Form I-589. This includes individuals who entered legally or illegally, those in valid immigration status, and those who are in removal proceedings. The application must be filed within one year of the applicant's last arrival in the United States, unless exceptional circumstances or changed circumstances can be demonstrated.

**Eligibility Requirements**: To qualify for asylum, applicants must demonstrate a well-founded fear of persecution based on at least one of five protected grounds: race, religion, nationality, membership in a particular social group, or political opinion. The persecution must be by the government or by groups the government is unable or unwilling to control. Applicants must not have firmly resettled in another country before arriving in the U.S. and must not fall under any of the statutory bars to asylum, including having been convicted of particularly serious crimes, committed serious nonpolitical crimes outside the U.S., or posed a danger to U.S. security. Withholding of removal has similar requirements but a higher burden of proof (clear probability of persecution rather than well-founded fear). CAT protection requires showing it is more likely than not the applicant would be tortured if removed to the proposed country.

**Required Documents**: The I-589 application must include detailed personal information, travel history, and a comprehensive statement explaining the basis for the asylum claim. Supporting documentation should include identity documents (passport, birth certificate, national identity card), evidence of persecution or feared persecution (police reports, medical records, newspaper articles, country condition reports, affidavits from witnesses), documentation of membership in the claimed social group or political opinion, and any evidence of past harm suffered. Credible and detailed written declarations are critical. Two identical passport-style photographs must be included for the applicant and each family member included in the application.

**Filing Fees**: There is no filing fee for Form I-589. This is one of the few immigration applications that USCIS processes without charge. However, applicants should be prepared for costs associated with obtaining supporting documentation, translations, medical evaluations, and legal representation if desired.

**Processing Time**: Affirmative asylum applications filed with USCIS (for individuals not in removal proceedings) can take 6 months to several years to reach an interview, depending on the asylum office workload and the Last In, First Out (LIFO) scheduling system. Defensive asylum applications filed in immigration court (for individuals in removal proceedings) follow the court's scheduling, which varies widely by jurisdiction and can take several years. Once interviewed or heard, decisions may be issued immediately or after additional time for review. Asylum cases are complex and heavily dependent on credibility determinations and country conditions.

**Work Authorization**: Asylum applicants become eligible to apply for employment authorization (Form I-765) 150 days after filing a complete asylum application. However, USCIS cannot grant the EAD until 180 days have passed since filing. This creates a 30-day window after the 150-day mark for processing. If USCIS delays the asylum decision through no fault of the applicant, the EAD may be granted while the asylum application is pending. Initial EADs are typically valid for one to two years and can be renewed as long as the asylum application remains pending.

**After Filing**: Affirmative asylum applicants will receive a receipt notice and eventually an interview notice scheduling an appointment at an asylum office. The interview is non-adversarial, conducted by an asylum officer, and typically attended only by the applicant, their attorney (if represented), and an interpreter (if needed). Decisions may be issued at the interview or mailed later. If approved, the applicant receives asylum status and can apply for a green card after one year. If denied and the applicant is out of status, the case is referred to immigration court for defensive proceedings. Defensive asylum applicants present their case before an immigration judge in a trial-like proceeding with a government attorney arguing for removal. Appeals are possible to the Board of Immigration Appeals and federal circuit courts.

**Inclusion of Family Members**: Spouses and unmarried children under 21 can be included in the principal applicant's I-589 if they are physically in the United States. If family members are abroad, derivative asylum status can be requested after the principal applicant is granted asylum, allowing them to join the asylee in the U.S. Family members must be included on the initial application or added within two years of the principal's asylum grant.

**Common Issues**: Credibility is the most critical factor in asylum cases. Inconsistencies between the written application, oral testimony, and supporting evidence frequently result in denials. Missing the one-year filing deadline without demonstrating changed or extraordinary circumstances bars asylum eligibility, though withholding of removal and CAT protection remain available. Applicants who traveled through third countries may face additional bars under asylum transit rules. Criminal convictions, even relatively minor ones, can trigger particularly serious crime bars. Failure to attend the interview or hearing results in abandonment or in absentia removal orders. Country conditions change, and what may have constituted a strong claim years ago may not support asylum today. Applicants from countries with high fraud rates face heightened scrutiny.
""",
    },
    "I-918": {
        "title": "Petition for U Nonimmigrant Status",
        "form_url": "https://www.uscis.gov/i-918",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-918instr.pdf",
        "visa_types": ["U Visa"],
        "description": """
Form I-918 is the Petition for U Nonimmigrant Status, commonly known as the U visa petition. This visa provides immigration protection to victims of certain qualifying crimes who have suffered substantial mental or physical abuse and are willing to assist law enforcement in the investigation or prosecution of criminal activity.

**Who Should File**: Victims of qualifying criminal activity who have suffered substantial physical or mental abuse as a result of the crime and possess information about the criminal activity may file Form I-918. The victim must have been helpful, is being helpful, or is likely to be helpful to law enforcement, prosecutors, judges, or other officials in the investigation, prosecution, or conviction of the criminal activity. There is no requirement that the victim be in lawful immigration status; undocumented individuals may apply. Certain family members of the direct victim may also file as derivative beneficiaries.

**Eligibility Requirements**: To qualify for U nonimmigrant status, applicants must meet several statutory requirements: (1) have been a victim of qualifying criminal activity that violates U.S. law or occurred in the United States, (2) have suffered substantial physical or mental abuse as a result of the victimization, (3) possess credible and reliable information about the criminal activity, (4) have been helpful, are being helpful, or are likely to be helpful to law enforcement in the investigation or prosecution (demonstrated through Form I-918 Supplement B certification), and (5) the criminal activity violated U.S. laws or occurred in the U.S. or its territories. Qualifying crimes include rape, torture, trafficking, incest, domestic violence, sexual assault, abusive sexual contact, prostitution, sexual exploitation, female genital mutilation, being held hostage, peonage, involuntary servitude, slave trade, kidnapping, abduction, unlawful criminal restraint, false imprisonment, blackmail, extortion, manslaughter, murder, felonious assault, witness tampering, obstruction of justice, perjury, fraud in foreign labor contracting, stalking, and attempt, conspiracy, or solicitation to commit any of these crimes, as well as substantially similar activities.

**Required Documents**: The I-918 petition package must include Form I-918 Petition for U Nonimmigrant Status, Form I-918 Supplement B (U Nonimmigrant Status Certification) completed and signed by a qualifying law enforcement official, certifying agency, prosecutor, judge, or other authority investigating or prosecuting the criminal activity, personal statement from the petitioner describing the victimization and its impact, evidence of the qualifying criminal activity (police reports, court documents, protection orders, medical records, photographs), proof of identity (passport, birth certificate, national ID), and evidence of substantial physical or mental abuse (medical records, psychological evaluations, expert declarations, personal statements). If including derivative family members, Form I-918 Supplement A must be filed for each qualifying family member along with proof of relationship.

**Filing Fees**: There is no filing fee for Form I-918. USCIS does not charge victims of crime for U visa petitions. Biometric services fees are also waived. However, applicants should anticipate costs for obtaining supporting documentation, certified translations, psychological evaluations, and legal representation if desired.

**Processing Time**: U visa processing is significantly delayed due to statutory annual caps and high demand. Congress limits U visa issuance to 10,000 principal petitioners per fiscal year. As a result, current processing times exceed 4-6 years from filing to approval. However, USCIS issues "bona fide determination" notices to qualifying petitioners, typically within 12-24 months of filing, which grants deferred action status and work authorization while the petition remains pending. This allows petitioners to remain lawfully in the U.S. and work while waiting for visa availability.

**After Filing**: Upon filing a complete I-918 petition with all required evidence and a properly executed Supplement B, USCIS will issue a receipt notice. If the petition is deemed bona fide (filed in good faith with credible evidence), USCIS will issue a deferred action notice and approve employment authorization (Form I-765). This status continues until the U visa is granted or the petition is denied. Once a visa becomes available (typically after 4-6 years currently), USCIS will approve the I-918 and issue Form I-797 approval notice along with a U visa work permit valid for four years. After three years of continuous physical presence in U nonimmigrant status, U visa holders may apply for lawful permanent residence (green card) using Form I-485, provided they can demonstrate continued cooperation with law enforcement and that their presence in the U.S. is justified on humanitarian grounds, to ensure family unity, or is otherwise in the public interest.

**Derivative Family Members**: U visa petitioners can include qualifying family members on Form I-918 Supplement A. If the principal petitioner is under 21, eligible derivatives include spouse, children, parents, and unmarried siblings under 18. If the principal is 21 or older, only spouse and children qualify. Derivative family members receive the same four-year U visa status and path to permanent residence as the principal.

**Common Issues**: The most significant challenge is obtaining the required Supplement B law enforcement certification. Some agencies are unfamiliar with U visas or reluctant to sign certifications. Advocates often need to educate law enforcement about the U visa program. Substantial physical or mental abuse must be clearly documented; minor victimization may not qualify. The petition must demonstrate helpfulness to law enforcement, not merely reporting the crime. Admissibility issues (criminal history, prior immigration violations, fraud) can complicate cases, though waivers are available on Form I-192 for most grounds of inadmissibility except Nazi persecution or genocide. Extreme processing backlogs mean years of waiting even with bona fide status. Maintaining continuous physical presence after U visa approval is critical for eventual green card eligibility, and departures from the U.S. require advance parole. Changes in law enforcement cooperation or withdrawal of the Supplement B certification can jeopardize the petition.
""",
    },
    "I-914": {
        "title": "Application for T Nonimmigrant Status",
        "form_url": "https://www.uscis.gov/i-914",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-914instr.pdf",
        "visa_types": ["T Visa"],
        "description": """
Form I-914 is the Application for T Nonimmigrant Status, commonly known as the T visa. This visa provides immigration protection to victims of severe forms of trafficking in persons, allowing them to remain in the United States to assist in the investigation and prosecution of trafficking cases and to rebuild their lives.

**Who Should File**: Individuals who are or have been victims of a severe form of trafficking in persons and are physically present in the United States, American Samoa, the Commonwealth of the Northern Mariana Islands, or at a U.S. port of entry due to trafficking may file Form I-914. Severe trafficking includes sex trafficking in which a commercial sex act is induced by force, fraud, or coercion, or in which the person induced to perform such an act is under 18 years of age, as well as labor trafficking involving the recruitment, harboring, transportation, provision, or obtaining of a person for labor or services through force, fraud, or coercion for the purpose of subjection to involuntary servitude, peonage, debt bondage, or slavery.

**Eligibility Requirements**: To qualify for T nonimmigrant status, applicants must demonstrate: (1) they are or have been a victim of a severe form of trafficking in persons as defined by the Trafficking Victims Protection Act, (2) they are physically present in the United States, American Samoa, the Commonwealth of the Northern Mariana Islands, or at a port of entry due to trafficking, (3) they have complied with any reasonable request from law enforcement for assistance in the investigation or prosecution of trafficking (or are under 18 years of age, or unable to cooperate due to physical or psychological trauma), and (4) they would suffer extreme hardship involving unusual and severe harm if removed from the United States. Applicants must also be admissible to the United States or obtain a waiver of inadmissibility.

**Required Documents**: The I-914 application requires substantial documentation including Form I-914 Application for T Nonimmigrant Status, Form I-914 Supplement B (Declaration of Law Enforcement Officer for Victim of Trafficking in Persons) if available though not required, personal statement describing the trafficking experience and how the applicant meets each eligibility requirement, evidence of victimization (police reports, court documents, news articles, medical records, photographs, witness statements), evidence of physical presence in the U.S. due to trafficking (explanation of how trafficking brought or kept the applicant in the U.S.), evidence of compliance with reasonable law enforcement requests (letters from law enforcement, prosecutors, or other officials, or explanation of why compliance was not possible), evidence of extreme hardship if removed (country condition reports, personal declarations about safety concerns, lack of family support, inability to access medical or psychological treatment), proof of identity (passport, birth certificate, national ID), and if claiming inadmissibility waivers, Form I-192 with supporting documentation. For derivative family members, Form I-914 Supplement A is required with proof of relationship.

**Filing Fees**: There is no filing fee for Form I-914. USCIS does not charge trafficking victims for T visa applications. Biometric services fees are also waived. Costs may still be incurred for obtaining supporting documentation, translations, medical or psychological evaluations, and legal representation.

**Processing Time**: T visa processing times vary but typically range from 12-24 months for initial adjudication. USCIS has made efforts to expedite T visa processing given the vulnerable status of applicants. Once approved, T nonimmigrant status is granted for an initial period of four years. During this time, T visa holders can apply for employment authorization and receive a work permit.

**After Filing**: Upon filing a complete I-914 application, USCIS will issue a receipt notice. If the applicant demonstrates prima facie eligibility, USCIS may grant deferred action and work authorization while the application is pending, particularly if the applicant is assisting law enforcement or is under 18. Once approved, USCIS issues Form I-797 approval notice and a T visa work permit valid for four years. T visa holders can travel internationally with advance parole (Form I-131). After three years of continuous physical presence in T nonimmigrant status, T visa holders may apply for lawful permanent residence (green card) using Form I-485, provided they demonstrate they have complied with reasonable requests for assistance in the trafficking investigation or prosecution (or would suffer extreme hardship upon removal), and they have been a person of good moral character during their time in T status.

**Law Enforcement Declaration (Supplement B)**: While Form I-914 Supplement B (law enforcement declaration) is helpful and strengthens a T visa application, it is not required. Unlike the U visa where Supplement B certification is mandatory, T visa applicants can submit secondary evidence and a detailed personal declaration if they cannot obtain law enforcement cooperation. However, applicants over 18 must still demonstrate compliance with reasonable law enforcement requests unless they can show they were unable to cooperate due to physical or psychological trauma.

**Derivative Family Members**: T visa principal applicants can include certain family members on Form I-914 Supplement A. If the principal applicant is under 21, eligible derivatives include spouse, children, parents, and unmarried siblings under 18. If the principal is 21 or older, only spouse, children, and parents (if the applicant can demonstrate they would face extreme hardship with unusual and severe harm due to the trafficking) qualify. In some cases involving imminent danger, family members can be included even if located abroad. Derivative T visa holders receive the same four-year status and can apply for green cards at the same time as the principal.

**Common Issues**: Demonstrating that physical presence in the U.S. is due to trafficking can be challenging if the trafficking ended years ago or if the applicant entered the U.S. independently before being trafficked. The extreme hardship requirement must show unusual and severe harm beyond the normal difficulties of return to one's home country. Many trafficking victims face trauma-related challenges in recounting their experiences and compiling evidence. Lack of law enforcement cooperation or reluctance to engage with authorities can complicate applications, though it does not automatically bar eligibility. Inadmissibility issues such as unlawful presence, criminal history related to the trafficking experience, or document fraud require waivers, which must demonstrate the conduct was a result of trafficking. Continuous physical presence after approval is essential for green card eligibility, and departures require advance parole. Maintaining good moral character for three years is critical; certain criminal convictions can bar adjustment to permanent residence.
""",
    },
    "I-360": {
        "title": "Petition for Amerasian, Widow(er), or Special Immigrant",
        "form_url": "https://www.uscis.gov/i-360",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-360instr.pdf",
        "visa_types": ["VAWA", "EB-4", "SIJS"],
        "description": """
Form I-360 is the Petition for Amerasian, Widow(er), or Special Immigrant, used for multiple distinct immigration categories including VAWA self-petitions (abused spouses, children, and parents of U.S. citizens or lawful permanent residents), Special Immigrant Juvenile Status (SIJS), religious workers (EB-4), and special immigrants such as Afghan and Iraqi nationals who worked with the U.S. government.

**Who Should File**: Eligibility to file Form I-360 depends on the specific classification. VAWA self-petitioners are abused spouses, children, or parents of U.S. citizens or lawful permanent residents who have been subjected to battery or extreme cruelty. SIJS petitioners are unmarried individuals under 21 who have been abused, abandoned, or neglected by one or both parents and for whom reunification is not viable. Religious workers are ministers or individuals in religious vocations or occupations who have been members of a religious denomination for at least two years. Special immigrants include certain Afghan and Iraqi translators, interpreters, and individuals employed by or on behalf of the U.S. government, as well as certain international organization employees, physicians, and other specific categories.

**Eligibility Requirements**: VAWA self-petitioners must demonstrate: (1) qualifying relationship to a U.S. citizen or lawful permanent resident (spouse, child, or parent), (2) that they resided with the abuser, (3) that they were subjected to battery or extreme cruelty by the USC or LPR, and (4) good moral character. The abusive relationship need not be current; divorced spouses can petition within two years of divorce if the abuse was connected to the divorce. SIJS petitioners must have a valid state juvenile court order declaring them dependent on the court or placing them in custody of a state agency or individual, finding that reunification with one or both parents is not viable due to abuse, abandonment, neglect, or a similar basis, and determining that return to their country of origin is not in their best interest. Religious workers must have been a member of a religious denomination for at least two years immediately before filing and must be coming to work as a minister or in a religious vocation or occupation for a qualifying nonprofit religious organization. Afghan and Iraqi SIV petitioners must meet specific employment requirements with the U.S. government or military and have experienced or be experiencing an ongoing serious threat as a consequence of that employment.

**Required Documents**: VAWA self-petitions require Form I-360, evidence of the qualifying relationship (marriage certificate for spouses, birth certificates for children or parents), evidence of the abuser's U.S. citizenship or lawful permanent residence status, evidence of battery or extreme cruelty (police reports, protection orders, medical records, photographs, declarations from witnesses, psychological evaluations, personal statement), evidence of cohabitation (leases, utility bills, joint documents), and evidence of good moral character. SIJS petitions require the state juvenile court order containing all required findings, birth certificate, passport or other identity documents, and evidence supporting the court's findings. Religious worker petitions require evidence of the organization's tax-exempt status, attestation from the religious organization, evidence of the petitioner's membership for at least two years, and detailed description of the proposed employment. Special immigrant categories have unique documentation requirements based on the specific classification.

**Filing Fees**: The filing fee for Form I-360 varies by classification. VAWA self-petitioners and SIJS petitioners pay no filing fee; these petitions are filed free of charge. Religious workers (EB-4) and most other special immigrant categories have a filing fee of $435 (as of 2026). Biometric services fees may apply depending on the category.

**Processing Time**: Processing times vary significantly by category and service center. VAWA self-petitions typically take 12-28 months. SIJS petitions can take 6-18 months for I-360 approval, though adjustment of status afterward faces backlogs due to visa availability. Religious worker petitions process in 6-12 months. Afghan and Iraqi SIV cases have dedicated processing channels with varying timelines. Premium processing is not available for I-360 petitions.

**After Filing**: Upon approval of the I-360, petitioners receive Form I-797 approval notice. For VAWA self-petitioners, approval establishes eligibility to file for adjustment of status (Form I-485) or to proceed through consular processing for an immigrant visa. VAWA-approved individuals can apply for work authorization while the I-485 is pending. SIJS petitioners must wait for visa availability in the EB-4 category, which can have significant backlogs for certain countries, before filing I-485. Religious workers and other EB-4 special immigrants also file I-485 or proceed through consular processing after I-360 approval, subject to visa availability. Approved VAWA petitioners receive prima facie determination letters that can support applications for public benefits and employment authorization in some states.

**VAWA Confidentiality**: VAWA petitions are strictly confidential. USCIS will not disclose any information about the petition to the abuser or anyone else without the petitioner's consent, except in very limited circumstances such as national security investigations. This protection extends to related applications and petitions. Petitioners should explicitly request confidentiality when filing.

**SIJS and Age-Out Protection**: SIJS petitioners must be under 21 and unmarried when both the state court order is issued and when the I-360 is filed. However, once the I-360 is properly filed before the petitioner's 21st birthday, they are protected from aging out and can continue pursuing adjustment of status even after turning 21.

**Common Issues**: VAWA petitions often face challenges in demonstrating the qualifying relationship if documentation is limited, or in proving battery or extreme cruelty when there is no police involvement or protective orders. Extreme cruelty is broader than physical abuse and includes emotional, psychological, and economic abuse, but must be well-documented. Good moral character can be undermined by certain criminal convictions or fraud. SIJS cases require very specific judicial findings in the state court order; orders that do not use the required statutory language or fail to make all necessary findings will result in denial. The reunification finding must be with at least one parent, not necessarily both. Religious worker petitions face scrutiny regarding the legitimacy of the religious organization, whether the position qualifies as a religious occupation or vocation, and whether the petitioner has the required two years of membership. Special immigrant categories have highly specific eligibility requirements and documentation standards that must be precisely met.
""",
    },
    "I-526E": {
        "title": "Immigrant Petition by Standalone Investor",
        "form_url": "https://www.uscis.gov/i-526",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-526einstr.pdf",
        "visa_types": ["EB-5", "Green Card"],
        "description": """
Form I-526E is the Immigrant Petition by Standalone Investor, filed by foreign investors seeking permanent residence through the EB-5 Employment-Based Fifth Preference Immigrant Investor Program by making a direct investment in a new commercial enterprise without participation in a Regional Center. This form replaced the previous Form I-526 for direct investments after the EB-5 Reform and Integrity Act of 2022.

**Who Should File**: Foreign nationals who have invested or are actively in the process of investing the required capital amount in a new commercial enterprise in the United States and whose investment will create at least 10 full-time positions for qualifying U.S. workers may file Form I-526E. The investor must demonstrate that the capital was lawfully obtained and that the investment is at risk for the purpose of generating a return. Unlike Regional Center investments (Form I-956F), Form I-526E is for direct investments where the investor is directly involved in the management or policy formation of the enterprise.

**Eligibility Requirements**: To qualify for EB-5 classification through Form I-526E, the investor must: (1) invest or be actively in the process of investing the required minimum capital amount ($1,050,000 standard, or $800,000 if investing in a Targeted Employment Area (TEA) which is a rural area or area of high unemployment), (2) invest in a new commercial enterprise established after November 29, 1990, or in a troubled business (established before that date but that has lost net worth and is in restructuring), (3) demonstrate that the investment will benefit the U.S. economy by creating at least 10 full-time positions for qualifying U.S. workers (U.S. citizens, lawful permanent residents, or other immigrants authorized to work, not including the investor and their immediate family), (4) show that the capital invested was obtained through lawful means, (5) demonstrate the capital is at risk and not a guaranteed return or loan to the investor, and (6) be engaged in the management of the enterprise (through day-to-day management or policy formulation). The enterprise must be for-profit.

**Required Documents**: The I-526E petition requires extensive documentation including Form I-526E, comprehensive business plan showing the enterprise will create at least 10 qualifying jobs within two years (or within a reasonable time as approved by USCIS), evidence of investment of the required capital or active investment in process (bank wire transfers, stock certificates, promissory notes secured by assets, capital contribution agreements), organizational documents of the new commercial enterprise (articles of incorporation, operating agreements, partnership agreements), evidence of lawful source of funds (tax returns, business ownership documentation, salary statements, asset sales documentation, gift letters with donor's source documentation, inheritance documents, loan documents showing collateral), evidence the capital is at risk (not a guaranteed buyback, not a loan repayment to the investor), evidence of job creation or detailed projection and timeline showing 10 jobs will be created, proof of investor's engagement in management (organizational chart, job description, evidence of policy-making authority), and if applicable, evidence the investment location qualifies as a TEA. All foreign language documents must have certified English translations.

**Filing Fees**: The filing fee for Form I-526E is $3,675 (as of 2026). Additionally, an Immigrant Investor Program Integrity Fee of $1,000 applies, bringing the total to $4,675. These fees are significantly higher than most other immigrant petitions reflecting the complexity and resources required for adjudication. There is no premium processing available for I-526E petitions.

**Processing Time**: I-526E processing times are substantial, typically ranging from 24-48 months depending on service center capacity, complexity of the petition, and completeness of submitted evidence. USCIS prioritizes cases based on visa availability and has implemented measures to reduce backlogs, but the volume of petitions and required scrutiny result in lengthy processing. Requests for Evidence (RFEs) can add many months to the timeline.

**After Filing and Approval**: Upon I-526E approval, USCIS issues Form I-797 approval notice, establishing the investor's priority date (the date the I-526E was properly filed). If the investor is in the United States, they may file Form I-485 to adjust status to conditional permanent resident, either concurrently with I-526E or after approval if a visa is immediately available. If abroad, the case is sent to the National Visa Center for consular processing, and the investor applies for an immigrant visa at a U.S. embassy or consulate. Upon admission or adjustment, the investor and included family members receive conditional permanent residence valid for two years. Within the 90-day period before the two-year anniversary, the investor must file Form I-829 (Petition by Investor to Remove Conditions on Permanent Resident Status) demonstrating that the full investment was maintained throughout the conditional period and that the required 10 jobs were created or will be created within a reasonable time.

**Job Creation Requirements**: For direct EB-5 investments, the investor must show actual job creation of 10 full-time positions (at least 35 hours per week) for qualifying U.S. workers. Jobs must be created within two years of the investor's admission as a conditional permanent resident, though USCIS may allow a reasonable period beyond two years if demonstrated in the business plan. Job creation can be shown through tax records (IRS Form I-9, quarterly wage reports, tax documents), payroll records, and Form I-9 verifications. Jobs must be direct, not indirect or induced (unlike Regional Center investments).

**Conditional Permanent Residence**: EB-5 investors initially receive conditional permanent residence, not full permanent residence. Conditions are removed by filing Form I-829 during the 90-day window before the second anniversary of conditional status. Failure to timely file I-829 results in automatic termination of status. The I-829 petition must demonstrate the investment was sustained at risk throughout the conditional period and the required jobs were created and maintained.

**Common Issues**: The most common issues leading to RFEs or denials include insufficient evidence of lawful source of funds (incomplete paper trail, inability to document fund origins, use of third-party gifts without documenting the donor's lawful source), failure to demonstrate capital is at risk (structured as a loan, guaranteed return arrangements, insufficient exposure to loss), unrealistic business plans that fail to credibly demonstrate 10 jobs will be created, lack of investor engagement in management (passive investments do not qualify for I-526E; they require Regional Center participation via I-956F), failure to meet the minimum investment amount after accounting for administrative fees and expenses, incorrect TEA designation resulting in insufficient investment amount, investments made before the enterprise was properly established, commingling of investor capital without clear allocation, and job creation shortfalls (jobs not created within required timeframe or not qualifying full-time positions). Material changes to the business plan after approval can jeopardize the I-829 petition to remove conditions.
""",
    },
    "I-864": {
        "title": "Affidavit of Support Under Section 213A of the INA",
        "form_url": "https://www.uscis.gov/i-864",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-864instr.pdf",
        "visa_types": ["Green Card", "Family", "K-1"],
        "description": """
Form I-864, Affidavit of Support Under Section 213A of the INA, is a legally enforceable contract where a sponsor agrees to financially support an intending immigrant and accept financial responsibility for that individual. This form is required for most family-based immigrants and some employment-based immigrants to demonstrate they will not become a public charge.

**Who Should File**: Form I-864 must be filed by the petitioner (sponsor) in family-based immigration cases where a U.S. citizen or lawful permanent resident has filed Form I-130 (Petition for Alien Relative) or Form I-140 (Immigrant Petition for Alien Workers) for certain employment-based categories. The sponsor must be the petitioner, a U.S. citizen or lawful permanent resident, at least 18 years old, and domiciled in the United States or its territories. In cases where the petitioner does not meet the income requirements, a joint sponsor who meets all sponsor requirements independently may file a separate Form I-864 to supplement the primary sponsor's affidavit.

**Eligibility and Income Requirements**: The sponsor must demonstrate income at or above 125% of the Federal Poverty Guidelines for their household size (including the sponsor, spouse, dependents, and the intending immigrant(s)). For active duty military sponsors petitioning for spouses or children, the threshold is 100% of the poverty guidelines. Household size includes the sponsor, the sponsor's spouse, dependent children, other dependents listed on the sponsor's tax return, any individuals for whom the sponsor has previously filed an I-864 that is still enforceable, and the intending immigrant(s) being sponsored (including any derivative beneficiaries). Income must be demonstrated through current employment, self-employment, Social Security, pension, or other verifiable lawful income sources. If income is insufficient, assets can be used at a value of five times the difference between actual income and the required income (or three times for U.S. citizen sponsors of spouses or children).

**Required Documents**: The I-864 must be accompanied by comprehensive financial documentation including the sponsor's most recent federal tax return (IRS transcript or complete copy including all schedules and W-2s), proof of current income (recent pay stubs covering the most recent six months, employer letter stating salary and employment start date, or if self-employed, business tax returns and quarterly earnings statements), proof of U.S. citizenship or lawful permanent residence (copy of passport, birth certificate, naturalization certificate, or green card), and if using a joint sponsor or household member's income, a separate Form I-864 (joint sponsor) or Form I-864A (household member). If using assets, documentation of asset value and liquidity must be provided (bank statements, property appraisals, stock portfolios). All tax returns must be complete with all schedules, W-2s, and 1099s.

**Filing Fees**: There is no filing fee to submit Form I-864 to USCIS or the National Visa Center. However, obtaining IRS tax transcripts may have associated costs, and if using asset-based evidence, appraisals and valuations may incur fees.

**Joint Sponsors**: If the primary petitioning sponsor does not meet the 125% poverty guideline income requirement, a joint sponsor may file a separate Form I-864 to make up the shortfall. The joint sponsor must independently meet the 125% threshold for a household size that includes their own household members plus all the immigrants they are sponsoring. Joint sponsors must be U.S. citizens or lawful permanent residents, at least 18 years old, and domiciled in the United States. They are equally and independently liable for supporting the immigrant. Joint sponsors are commonly used when the petitioner has insufficient income, is unemployed, or is a student. There is no legal or familial relationship requirement between the joint sponsor and the immigrant.

**Household Member Income**: Form I-864A allows household members (individuals living with the sponsor) to combine their income with the sponsor's income to meet the poverty guideline threshold. The household member must complete Form I-864A and agree to make their income and assets available to support the sponsored immigrant. The household member's income can only be counted if they have lived with the sponsor for the previous six months and agree to be jointly liable. Common household members include the sponsor's spouse, adult children, parents, or other relatives living in the same residence.

**Legal Obligations and Enforceability**: Form I-864 is a legally enforceable contract under both federal and state law. The sponsor's obligation continues until the sponsored immigrant becomes a U.S. citizen, has worked 40 qualifying quarters (approximately 10 years) under the Social Security Act, dies, or permanently leaves the United States. Divorce does not terminate the obligation. The sponsored immigrant, federal government, or state/local government entity that provides a means-tested public benefit can sue the sponsor to recover benefits or seek financial support. Sponsors can be required to reimburse government agencies for public benefits used by the immigrant. Failure to provide support can result in court judgments, wage garnishment, and credit impacts.

**When I-864 is Required**: Form I-864 is required for immediate relatives of U.S. citizens (spouses, parents, unmarried children under 21), family preference immigrants (adult children, siblings, spouses and children of lawful permanent residents), certain employment-based immigrants (typically where a relative owns 5% or more of the petitioning company), and K-1 fiancé(e) visa holders adjusting status after marriage. It is not required for self-petitioning widows/widowers, VAWA self-petitioners, asylees, refugees, T or U visa holders adjusting status, special immigrants (SIJS, certain Iraqi/Afghan SIVs, religious workers, etc.), registry applicants, and certain other humanitarian categories.

**After Filing**: Form I-864 is submitted as part of the immigrant visa or adjustment of status application package. For consular processing cases, it is sent to the National Visa Center or brought to the immigrant visa interview. For adjustment of status cases, it is filed with Form I-485 or submitted upon USCIS request. USCIS or the consular officer reviews the I-864 to determine whether the intending immigrant is likely to become a public charge. If the sponsor's income is insufficient or documentation is incomplete, the case may be denied, or the sponsor may be given an opportunity to obtain a joint sponsor or provide additional evidence.

**Common Issues**: Insufficient income is the most frequent problem; sponsors who do not meet 125% of poverty guidelines must obtain a joint sponsor or use assets. Incomplete tax documentation (missing schedules, W-2s, or unsigned returns) results in RFEs. Self-employed sponsors often face additional scrutiny and must provide business tax returns and evidence of ongoing income. Sponsors who filed taxes as "Married Filing Separately" must provide their spouse's tax return as well. Discrepancies between stated income on the I-864 and actual tax returns trigger requests for explanation. Sponsors not currently domiciled in the U.S. (living abroad) must demonstrate intent to reestablish U.S. domicile before the immigrant's admission. Failure to include all household members and previously sponsored immigrants in the household size calculation results in incorrect poverty guideline assessment. Using assets requires careful documentation of liquidity and value; illiquid assets (retirement accounts with penalties, property that cannot be quickly sold) may not qualify. Outdated tax returns (older than one year from filing) may not be accepted; current income documentation is critical.
""",
    },
    "I-693": {
        "title": "Report of Medical Examination and Vaccination Record",
        "form_url": "https://www.uscis.gov/i-693",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-693instr.pdf",
        "visa_types": ["Green Card"],
        "description": """
Form I-693, Report of Medical Examination and Vaccination Record, is the medical examination form required for applicants seeking adjustment of status to lawful permanent residence in the United States. This form must be completed by a USCIS-designated civil surgeon and submitted as part of the Form I-485 application or upon USCIS request during the adjustment process.

**Who Should File**: Form I-693 is not filed by the applicant but rather completed and signed by a USCIS-designated civil surgeon after conducting a required medical examination of the adjustment of status applicant. The applicant is responsible for scheduling the examination, paying the civil surgeon's fees, and ensuring the completed sealed form is submitted to USCIS. All applicants for adjustment of status (Form I-485) must undergo this medical examination with limited exceptions (such as certain asylees and refugees who completed overseas medical examinations within the past year).

**Medical Examination Requirements**: The civil surgeon must conduct a physical examination covering mental health assessment, review of medical history, physical and mental abnormalities, tuberculosis testing (TB skin test or blood test and chest X-ray if applicable), testing for communicable diseases of public health significance (syphilis and gonorrhea screening for applicants ages 18 and older or 15-17 if risk factors exist), and review of vaccination records. The civil surgeon assesses whether the applicant has communicable diseases of public health significance, has failed to present documentation of required vaccinations, has or had a physical or mental disorder with associated harmful behavior, or is a drug abuser or addict. Class A conditions (serious communicable diseases, certain mental health disorders with harmful behavior, drug abuse/addiction) make an applicant inadmissible unless a waiver is obtained. Class B conditions are noted but do not affect admissibility.

**Required Vaccinations**: Applicants must provide proof of vaccination or receive vaccinations for the following vaccine-preventable diseases: mumps, measles, rubella, polio, tetanus and diphtheria toxoids, pertussis, Haemophilus influenzae type B (Hib), hepatitis A, hepatitis B, varicella (chickenpox), influenza (seasonal), pneumococcal disease, rotavirus, meningococcal disease, COVID-19, and any other vaccines recommended by the Advisory Committee on Immunization Practices (ACIP). Vaccination requirements are age-appropriate; not all vaccines are required for all age groups. Certain exceptions and waivers are available for medical contraindications (documented by a physician), moral/religious objections (applicant must sign a waiver statement), or if the vaccine is not age-appropriate or medically indicated. Blanket waivers apply to certain categories such as applicants adjusting from asylee or refugee status.

**Civil Surgeon Requirements**: The medical examination must be conducted by a USCIS-designated civil surgeon. USCIS maintains a searchable online list of designated civil surgeons by ZIP code on the USCIS website. Only civil surgeons currently authorized by USCIS can complete Form I-693. Regular physicians, even licensed and board-certified, cannot complete the form unless they are USCIS-designated. Applicants should verify the civil surgeon's designation status before scheduling an examination, as designations can be suspended or revoked.

**Cost**: There is no USCIS filing fee for Form I-693, but the civil surgeon's fee for conducting the examination can range from $200 to $700 or more depending on geographic location, whether vaccinations are needed, and the complexity of required tests (TB, syphilis, gonorrhea). These fees are not standardized and vary widely. The examination is generally not covered by health insurance as it is for immigration purposes, not medical treatment. Vaccinations, TB testing, and lab work are charged separately by many civil surgeons. Applicants should inquire about total costs before scheduling.

**Validity Period**: A completed Form I-693 signed by the civil surgeon is valid for two years from the date of the civil surgeon's signature, provided it is submitted to USCIS while valid and the applicant remains in the United States. If submitted with the initial I-485 application, the form must be signed no more than 60 days before filing the I-485. If USCIS requests the I-693 through a Request for Evidence (RFE) or interview notice, the form must be current at the time of submission (signed within 60 days). USCIS will reject or deny applications if the I-693 is expired, improperly completed, unsealed, or signed by a non-designated physician.

**Sealed Envelope Requirement**: Civil surgeons must place the completed Form I-693 in a sealed envelope and sign across the seal. The applicant must not open the envelope. The sealed envelope is submitted to USCIS either with the initial I-485 filing or at the adjustment of status interview. If the envelope is opened or the seal is broken, USCIS will reject the form and require a new examination.

**After Completion**: Once the civil surgeon completes Form I-693, the applicant receives the sealed envelope to submit to USCIS. The applicant should also request a copy of the completed form for their own records (the civil surgeon provides this separately from the sealed version). The sealed I-693 is submitted with Form I-485 or brought to the interview as instructed by USCIS. USCIS reviews the medical examination results as part of the admissibility determination. If the examination reveals a Class A condition (inadmissibility ground), the applicant may need to apply for a waiver (Form I-601 for general grounds or specific waivers for certain communicable diseases). If vaccinations are missing and no waiver applies, USCIS may issue an RFE requiring the applicant to complete vaccinations and submit an updated I-693.

**Common Issues**: Expired forms are the most common problem; applicants who file I-485 without the I-693 or with an outdated form receive RFEs requiring a new examination. Using a non-designated physician results in rejection; applicants must verify the civil surgeon's current designation status. Missing or incomplete vaccinations without valid waivers lead to RFEs and delays. Some applicants mistakenly open the sealed envelope, invalidating the form. Incomplete examinations (missing TB test, missing communicable disease screening, unsigned forms) result in RFEs. Applicants with positive TB tests require follow-up chest X-rays and possibly treatment documentation; active TB is a Class A condition requiring completion of treatment and medical clearance. Mental health conditions that led to harmful behavior require detailed evaluation and may trigger inadmissibility. Drug abuse or addiction findings require evidence of rehabilitation and possibly a waiver. Applicants who previously received certain vaccinations but lack documentation may need to be re-vaccinated or undergo serologic testing to prove immunity (titer tests). Civil surgeon errors (wrong form version, improper completion, failure to sign) necessitate returning to the civil surgeon for corrections or re-examination.
""",
    },
    "I-90": {
        "title": "Application to Replace Permanent Resident Card",
        "form_url": "https://www.uscis.gov/i-90",
        "instructions_url": "https://www.uscis.gov/sites/default/files/document/forms/i-90instr.pdf",
        "visa_types": ["Green Card"],
        "description": """
Form I-90, Application to Replace Permanent Resident Card, is used by lawful permanent residents (green card holders) to renew an expiring or expired green card, replace a lost, stolen, or damaged card, update information due to a legal name change or other biographical corrections, or replace a card issued with incorrect information. This form ensures that permanent residents maintain valid proof of their status.

**Who Should File**: Lawful permanent residents whose green cards are expiring within six months or have already expired, have been lost, stolen, mutilated, or destroyed, contain incorrect information due to USCIS error, need to be updated due to legal name change, or were issued as conditional permanent resident cards that have since been upgraded to 10-year cards should file Form I-90. Conditional permanent residents (those with two-year green cards based on marriage or EB-5 investment) should not use I-90 to remove conditions; they must file Form I-751 (marriage-based) or Form I-829 (EB-5 investment-based) instead. Commuter permanent residents who reside in Canada or Mexico but work in the U.S. and need to update their cards also use Form I-90.

**Eligibility Requirements**: To file Form I-90, the applicant must be a lawful permanent resident whose card is expiring, expired, lost, stolen, damaged, or contains errors. Applicants must not be in removal proceedings unless they have a pending Form I-751 or I-829 to remove conditional status. Permanent residents outside the United States for more than one year or who have abandoned their permanent residence should not file I-90; they may have lost their status and need to apply for a returning resident visa (SB-1) at a U.S. embassy or consulate. Permanent residents whose green cards were issued before their 14th birthday must replace the card when they turn 14 (filing I-90 within 30 days of their 14th birthday) and then renew at age 16 if they do not become U.S. citizens before then.

**Required Documents**: Documentation required depends on the reason for filing. For renewal of an expiring or expired card: copy of the current (or most recent) green card, front and back. For a lost or stolen card: copy of the card if available, police report if the card was stolen (recommended but not required), and any other identity documents. For a damaged or mutilated card: the actual damaged card must be submitted with the application. For legal name change: copy of the legal document evidencing the name change (marriage certificate, divorce decree, court order). For USCIS error (incorrect information on the card): copy of the incorrect card and evidence of the correct information (birth certificate, passport, court documents). For automatic conversion from conditional to permanent residence (rare circumstances where USCIS granted 10-year status but issued a 2-year card): copy of I-751 or I-829 approval notice. Two passport-style photographs may be required in certain cases.

**Filing Fees**: The filing fee for Form I-90 is $415, and the biometric services fee is $85, for a total of $500 (as of 2026). Fee waivers are not available for Form I-90. Payment can be made by check, money order, or credit card (using Form G-1450). Online filing via the USCIS online account system allows electronic payment and often results in faster processing.

**Online vs. Paper Filing**: USCIS strongly encourages online filing of Form I-90 through a USCIS online account. Online filing provides faster processing, electronic notifications, the ability to upload supporting documents, real-time case status updates, and eliminates mailing delays. Paper filing is still accepted but typically takes longer. Applicants filing online create a USCIS online account, complete the form electronically, upload supporting documents, pay the fee online, and receive immediate confirmation of filing.

**Processing Time**: Processing times for Form I-90 typically range from 6-12 months, though times vary by USCIS field office and whether the application was filed online or by paper. Online filings generally process faster. If a green card is expired or expiring and the I-90 receipt notice alone is insufficient for employment or travel, applicants can request an I-551 stamp in their passport at a USCIS field office by scheduling an InfoPass appointment, which serves as temporary evidence of permanent resident status (typically valid for one year). The receipt notice (Form I-797C) extends the validity of an expired green card for up to 24 months for employment authorization and certain other purposes, though it is not valid for travel without the physical card or I-551 stamp.

**After Filing**: Upon filing, USCIS issues a receipt notice (Form I-797C) confirming the application was received. Applicants are then scheduled for a biometric services appointment at a local Application Support Center (ASC) to provide fingerprints, photograph, and signature (unless biometrics were recently captured for another application). USCIS reviews the application and supporting documents. If additional evidence is needed, USCIS issues a Request for Evidence (RFE). Once approved, USCIS produces and mails the new green card to the applicant's address on file (or updated address if a change was filed). Delivery typically occurs within 30 days of approval. Applicants should verify the new card contains accurate information immediately upon receipt.

**Travel and Employment During Processing**: The Form I-90 receipt notice, in combination with an expired or expiring green card, extends the card's validity for up to 24 months for employment verification purposes (employers can accept the receipt notice with the expired card as proof of work authorization under Form I-9 rules). However, for international travel, the receipt notice alone is generally not sufficient. Permanent residents who need to travel while I-90 is pending should obtain an I-551 stamp (temporary evidence of permanent residence) in their passport at a USCIS office before departure. Without the stamp or a valid green card, airlines may refuse boarding and Customs and Border Protection may have difficulty verifying status upon return.

**Common Issues**: Failure to file for renewal before the card expires can create complications for travel and employment verification, though status as a permanent resident does not expire—only the card does. Lost or stolen cards should be reported, and police reports (though not required) can be helpful if identity theft is a concern. Applicants who provide incorrect addresses or fail to update USCIS of address changes (using Form AR-11 or online) may not receive notices or the replacement card. Damaged cards must be submitted with the application, leaving the applicant without a physical card during processing; requesting an I-551 stamp is advisable. Name change cases require legal documentation; informal name changes or use of nicknames are not acceptable. Applicants in removal proceedings generally cannot renew their green cards through I-90 and must resolve their proceedings first. Conditional permanent residents mistakenly filing I-90 instead of I-751 or I-829 will have their applications denied. Permanent residents who have been outside the U.S. for extended periods (especially over one year) may face questions about whether they abandoned their permanent residence; simply filing I-90 does not restore abandoned status, and they may need to apply for a returning resident visa (SB-1). Biometric appointment no-shows result in application denials; rescheduling is possible but must be done promptly.
""",
    },
}


async def ingest_forms_extended(dry_run=False, forms_filter=None):
    """
    Ingest extended USCIS forms data into Pinecone.

    Args:
        dry_run: If True, skip actual Pinecone upsert
        forms_filter: Optional list of form names to filter (e.g., ['I-140', 'I-129'])
    """
    logger.info("Starting extended forms ingestion")
    clients = await setup_clients()

    data = FORM_DATA
    if forms_filter:
        filter_set = set(forms_filter)
        data = {k: v for k, v in FORM_DATA.items() if k in filter_set}
        logger.info(f"Filtering to forms: {', '.join(sorted(filter_set))}")

    all_chunks = []
    all_metadata = []

    for form_name, entry in data.items():
        logger.info(f"Processing {form_name}: {entry['title']}")

        content = f"Form {form_name}: {entry['title']}\n\n{entry['description'].strip()}"
        chunks = chunk_text(content, chunk_size=512, overlap=50)

        logger.info(f"  Created {len(chunks)} chunks for {form_name}")

        for chunk_idx, chunk in enumerate(chunks):
            metadata = {
                "source": f"form_{form_name.lower().replace('-', '_')}",
                "document_title": f"Form {form_name}: {entry['title']}",
                "form_name": form_name,
                "form_url": entry["form_url"],
                "instructions_url": entry["instructions_url"],
                "visa_types": entry["visa_types"],
                "chunk_index": chunk_idx,
                "section": f"form_{form_name.lower().replace('-', '_')}_{chunk_idx}",
            }
            all_chunks.append(chunk)
            all_metadata.append(metadata)

    logger.info(f"Total chunks prepared: {len(all_chunks)}")

    if all_chunks:
        vectors_upserted = await upsert_to_pinecone(
            clients.index, all_chunks, all_metadata,
            source="form_extended", dry_run=dry_run,
        )
        logger.info(f"Extended forms ingestion complete: {vectors_upserted} vectors upserted")
    else:
        logger.warning("No chunks to ingest")

    return len(all_chunks)


async def main():
    parser = argparse.ArgumentParser(
        description="Ingest extended USCIS forms into Migravio RAG pipeline"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process chunks but skip Pinecone upsert"
    )
    parser.add_argument(
        "--forms",
        type=str,
        help="Comma-separated list of form names to ingest (e.g., I-140,I-129,I-589)"
    )

    args = parser.parse_args()

    forms_filter = None
    if args.forms:
        forms_filter = [f.strip().upper() for f in args.forms.split(",")]
        logger.info(f"Filtering to forms: {forms_filter}")

    try:
        await ingest_forms_extended(dry_run=args.dry_run, forms_filter=forms_filter)
        logger.info("Extended forms ingestion completed successfully")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
