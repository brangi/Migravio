"""
Humanitarian and protection visa overviews ingestion script for Migravio RAG pipeline.

Covers: U Visa, T Visa, VAWA, Asylum, Refugee, TPS, DACA, Withholding of Removal,
CAT, SIJS, Humanitarian Parole/CHNV, Cancellation of Removal

Usage:
    python scripts/ingest_visa_humanitarian.py [--dry-run] [--visa-types TPS,DACA]
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


HUMANITARIAN_VISAS = {
    "U Visa": {
        "name": "U Visa (Crime Victims)",
        "visa_types": ["U Visa"],
        "content": """
The U visa is a critical immigration protection for victims of certain serious crimes who have suffered substantial physical or mental abuse and are helpful to law enforcement in the investigation or prosecution of criminal activity. Created by Congress in 2000 under the Victims of Trafficking and Violence Protection Act, the U visa serves a dual purpose: providing immigration relief to crime victims while creating incentives for victims to cooperate with law enforcement without fear of deportation.

**Who Qualifies for U Visa Status:**

To be eligible for a U visa, you must meet several specific requirements. First, you must have been a victim of qualifying criminal activity. These crimes include domestic violence, sexual assault, rape, trafficking, kidnapping, abduction, extortion, involuntary servitude, false imprisonment, felonious assault, witness tampering, obstruction of justice, perjury, manslaughter, murder, torture, and many others. The full list includes over 30 crime categories and related offenses.

Second, you must have suffered substantial physical or mental abuse as a result of the crime. USCIS evaluates this on a case-by-case basis, considering factors such as the severity of the harm, the duration, and whether the harm was severe enough to affect your well-being or safety.

Third, you must possess information about the criminal activity. This means you have knowledge about the crime and can provide details about what happened. Fourth, you must have been helpful, are being helpful, or are likely to be helpful to law enforcement in the investigation or prosecution of the crime. This cooperation requirement is demonstrated through a law enforcement certification (Form I-918 Supplement B) signed by a federal, state, or local law enforcement official.

Fifth, the criminal activity must have violated US law or occurred in the United States, its territories, or possessions. Finally, you must be admissible to the United States. If you have certain criminal convictions or immigration violations, you may need to file a waiver (Form I-192) alongside your U visa petition.

**The Application Process:**

The U visa application process begins with obtaining a law enforcement certification. This is often the most challenging step. You must work with a qualifying law enforcement agency (police, prosecutors, judges, immigration authorities, or other investigative agencies) to have them complete Form I-918 Supplement B. This form certifies that you were a victim of qualifying criminal activity and have been, are being, or are likely to be helpful in the investigation or prosecution.

Law enforcement agencies are not required to sign certifications, and their willingness varies widely. Some jurisdictions have established procedures for U visa certifications, while others are less familiar with the process. Having an attorney advocate with law enforcement can significantly increase your chances of obtaining a certification.

Once you have the certification, you file Form I-918 (Petition for U Nonimmigrant Status) with USCIS. You should also file Form I-918 Supplement A for each qualifying family member you want to include. The filing fee was recently increased but waivers are available if you cannot afford it.

**Annual Cap and Processing Times:**

Congress created an annual cap of 10,000 U visas per fiscal year. Due to enormous demand, USCIS has maintained a massive backlog for years. As of 2026, applicants often wait 5-10 years or more from initial filing to final approval. However, USCIS has implemented a process where qualified applicants receive Bona Fide Determination notices while waiting. This determination grants work authorization and deferred action (protection from deportation) while your petition is pending.

When you file your U visa petition, you simultaneously file Form I-765 (Application for Employment Authorization). Once USCIS makes a bona fide determination that your petition is approvable, you receive work authorization even though you're still in the queue waiting for a visa number to become available.

**Derivative Family Members:**

U visa holders can include certain family members in their petitions. If you are 21 years or older, you can include your spouse and unmarried children under 21. If you are under 21 years old, you can include your spouse, unmarried children under 21, parents, and unmarried siblings under 18. These family members receive U visa derivative status and can obtain work authorization.

**Path to Permanent Residence:**

One of the most valuable aspects of U visa status is that it provides a clear path to a green card. After you have held U visa status for at least three years and have continued to cooperate with law enforcement as needed, you become eligible to apply for lawful permanent residence (a green card) by filing Form I-929. You must demonstrate that your presence in the United States is justified on humanitarian grounds, to ensure family unity, or is otherwise in the public interest.

**Protection and Benefits:**

While your U visa petition is pending with a bona fide determination, or once approved, you receive several important benefits. You have employment authorization and can work legally anywhere in the United States. You have deferred action or lawful status, protecting you from deportation. You may be eligible for certain public benefits depending on your state. You can apply for advance parole to travel outside the US, though travel should be carefully evaluated with an attorney as it carries some risk.

**Important Considerations:**

U visa cases involve detailed documentation of traumatic events. You should gather police reports, medical records, court records, protective orders, photographs of injuries, witness statements, and any other evidence of the crime and your cooperation with law enforcement. The certification from law enforcement is mandatory and cannot be waived, so building a relationship with the investigating agency early in the process is critical.

If you are in removal proceedings, a pending U visa petition may be a basis for requesting prosecutorial discretion or administrative closure of your case while you wait for adjudication. An immigration attorney can file motions with the immigration court to protect you while your petition is pending.

The U visa program recognizes that crime victims often face unique vulnerabilities and that their cooperation with law enforcement serves important public safety interests. It reflects a congressional determination that these victims deserve protection and an opportunity to remain lawfully in the United States.

Important: U visa cases involve complex legal proceedings that can significantly impact your immigration status and safety. This information is for general guidance only and is not legal advice. You should consult with a qualified immigration attorney who specializes in U visa cases before taking any action.
""",
    },
    "T Visa": {
        "name": "T Visa (Trafficking Victims)",
        "visa_types": ["T Visa"],
        "content": """
The T visa provides critical immigration protection for victims of severe forms of human trafficking. Established by the Trafficking Victims Protection Act of 2000, the T visa recognizes that trafficking victims often face extreme coercion, trauma, and fear that prevents them from seeking help or cooperating with authorities. This visa category offers victims a pathway to safety, stability, and ultimately permanent residence in the United States.

**What Constitutes Human Trafficking:**

Human trafficking takes two primary forms: sex trafficking and labor trafficking. Sex trafficking involves the recruitment, harboring, transportation, provision, obtaining, patronizing, or soliciting of a person for the purpose of a commercial sex act through force, fraud, or coercion. If the victim is under 18 years old, no proof of force, fraud, or coercion is required.

Labor trafficking involves the recruitment, harboring, transportation, provision, or obtaining of a person for labor or services through force, fraud, or coercion for the purpose of subjection to involuntary servitude, peonage, debt bondage, or slavery. Common scenarios include domestic servitude, agricultural work, construction, restaurant work, hotel work, and other industries where victims are controlled through threats, physical restraint, debt manipulation, document confiscation, or psychological coercion.

Trafficking differs from smuggling. Smuggling involves voluntary illegal entry into a country, while trafficking involves exploitation and control over a person. However, a smuggling situation can become trafficking if the smuggled person is subsequently subjected to forced labor or exploitation.

**Eligibility Requirements:**

To qualify for a T visa, you must meet several requirements. First, you must be a victim of a severe form of trafficking in persons as defined by federal law. This means you were subjected to sex trafficking or labor trafficking as described above.

Second, you must be physically present in the United States, American Samoa, the Commonwealth of the Northern Mariana Islands, or at a port of entry due to trafficking. This means the trafficking brought you to or keeps you in US territory.

Third, you must comply with any reasonable request from law enforcement for assistance in the investigation or prosecution of human trafficking. However, there are important exceptions to this requirement. If you are under 18 years old, you are not required to comply with law enforcement requests. If you have suffered trauma so severe that you are unable to cooperate, you may also be exempt. USCIS evaluates this on a case-by-case basis considering the trauma you experienced.

Fourth, you must demonstrate that you would suffer extreme hardship involving unusual and severe harm if you were removed from the United States. This is generally not difficult to establish given the nature of trafficking situations, where returning to your home country often means facing retribution from traffickers, re-trafficking, or severe economic or social harm.

Finally, you must be admissible to the United States. If you have certain criminal convictions or immigration violations, you can file Form I-192 for a waiver. Importantly, many criminal activities that trafficking victims were forced to commit (such as prostitution or using false documents) can be waived, particularly when they resulted from the trafficking situation.

**The Application Process:**

You apply for a T visa by filing Form I-914 (Application for T Nonimmigrant Status) with USCIS. Unlike the U visa, you do not need a law enforcement certification to file, though having a law enforcement declaration (Form I-914 Supplement B) significantly strengthens your case. If law enforcement provides a declaration confirming your status as a trafficking victim and your cooperation, USCIS gives this substantial weight.

You should also file Form I-914 Supplement A for each qualifying family member you want to include. Additionally, you file Form I-765 for employment authorization at the same time.

The application requires detailed documentation of the trafficking situation, your compliance with law enforcement (unless exempt), and the extreme hardship you would face if removed. Evidence can include police reports, medical records, psychological evaluations, letters from social service providers, affidavits from witnesses, evidence of the trafficking operation, and documentation of the harm you suffered.

**Annual Cap and Processing Times:**

Congress set an annual cap of 5,000 T visas per fiscal year. Unlike the U visa, the T visa program has historically not reached this cap, meaning processing times are generally faster—often 12-24 months, though times vary. You receive work authorization while your petition is pending, usually within several months of filing.

**Derivative Family Members:**

T visa holders can petition for certain family members to receive derivative T visas. If you are 21 years or older, you can include your spouse and unmarried children under 21. If you are under 21, you can also include your parents and unmarried siblings under 18.

In cases of extreme danger or hardship, you may also petition for adult children or adult siblings if necessary to avoid extreme hardship. These cases require additional documentation and USCIS discretion.

**Path to Permanent Residence:**

T visa holders can apply for lawful permanent residence (a green card) after holding T visa status for three years, or earlier if the trafficking investigation or prosecution is complete. To qualify, you must file Form I-914 and demonstrate either: (1) continuous physical presence in the US for at least three years since receiving T status, or (2) continuous physical presence for a shorter period if law enforcement certifies that the investigation or prosecution is complete and your continued presence is not required.

You must also show that you would suffer extreme hardship involving unusual and severe harm if removed, and that you have been a person of good moral character during your time in T status. You must have complied with reasonable law enforcement requests (unless exempt).

**Benefits and Protections:**

T visa holders receive immediate employment authorization upon approval. You can work for any employer in the United States. You also receive access to federal public benefits on the same basis as refugees, including assistance programs that help trafficking survivors rebuild their lives. These benefits include Medicaid, SNAP (food assistance), TANF (cash assistance), and access to refugee resettlement services.

You are protected from deportation while in T status. You can apply for advance parole (Form I-131) to travel outside the United States, though travel should be carefully planned with an attorney as it can affect your status.

**Important Considerations:**

Trafficking cases often involve severe trauma, and many survivors experience PTSD, anxiety, depression, and other psychological effects. Working with trauma-informed attorneys, social workers, and mental health professionals is crucial both for your recovery and for documenting your case.

If you are in removal proceedings, a pending T visa application may be grounds for administrative closure or prosecutorial discretion while USCIS adjudicates your petition.

Many trafficking survivors have been forced to commit criminal acts or immigration violations while under the control of traffickers. These should be explained in your application, and waivers are often granted when the criminal conduct resulted from the trafficking.

Confidentiality is important in trafficking cases. USCIS has policies to protect T visa applicants from having their information disclosed to traffickers. Your application information is generally protected from disclosure.

The T visa program recognizes that human trafficking is a severe human rights violation and that survivors deserve protection, support, and the opportunity to rebuild their lives in safety. It reflects a commitment to combating trafficking by providing immigration relief to those who have endured these horrific crimes.

Important: T visa cases involve complex legal proceedings that can significantly impact your immigration status and safety. This information is for general guidance only and is not legal advice. You should consult with a qualified immigration attorney who specializes in T visa and human trafficking cases before taking any action.
""",
    },
    "VAWA": {
        "name": "VAWA (Violence Against Women Act Self-Petition)",
        "visa_types": ["VAWA"],
        "content": """
The Violence Against Women Act (VAWA) self-petition is a critical immigration remedy that allows certain abused spouses, children, and parents of US citizens and lawful permanent residents (LPRs) to petition for themselves without the knowledge or consent of the abusive family member. Despite its name, VAWA protections are available to victims of all genders—men, women, and non-binary individuals can all qualify.

**The Purpose and History of VAWA:**

Congress enacted VAWA in 1994 recognizing that abusive US citizens and LPRs often use the immigration system as a tool of control over their family members. In traditional family-based immigration, the US citizen or LPR spouse or parent must petition for their family member, giving them tremendous power to threaten withdrawal of the petition or deportation. VAWA removes this control by allowing victims to self-petition independently.

VAWA is fundamentally about safety and autonomy. It recognizes that no one should be forced to remain in an abusive relationship to maintain immigration status or to achieve lawful permanent residence. It also protects US citizen children who should not have to choose between their parent and their safety.

**Who Can File a VAWA Self-Petition:**

There are three main categories of VAWA self-petitioners:

First, abused spouses. You may self-petition if you are or were married to a US citizen or LPR who subjected you to battery or extreme cruelty. This includes current marriages and marriages that ended in divorce within the past two years, provided the abuse was connected to the divorce. You must have resided with the abusive spouse at some point during the marriage.

Second, abused children. You may self-petition if you are the unmarried child under 21 (or under 25 in some cases) of a US citizen or LPR who abused you or your parent. Children who aged out while their VAWA petition was pending may still be protected under the Child Status Protection Act.

Third, abused parents. If you are the parent of a US citizen child who abused you, you may self-petition. This category only applies when the abuser is a US citizen, not an LPR, and the citizen child must be at least 21 years old.

**What Constitutes Battery or Extreme Cruelty:**

VAWA does not require only physical violence. Battery or extreme cruelty is defined broadly to include physical violence, sexual abuse, psychological abuse, emotional abuse, economic control, isolation, threats, intimidation, humiliation, and other harmful behavior. The abuse must rise to a certain level of severity, but USCIS evaluates this holistically considering the totality of the relationship.

Examples include: hitting, slapping, punching, choking, rape or sexual assault, forced sexual acts, threats of harm to you or your children, threats of deportation, destruction of property, extreme jealousy and possessiveness, isolating you from friends and family, controlling all finances and withholding money, preventing you from working or attending school, constant criticism and verbal degradation, and threats to take away children.

You do not need a police report or protective order to establish abuse, though these strengthen your case. USCIS accepts many forms of evidence including affidavits from you and witnesses, medical records, psychological evaluations, photos of injuries, threatening messages, and evidence of the controlling behavior.

**The Application Process:**

You file Form I-360 (Petition for Amerasian, Widow(er), or Special Immigrant) with USCIS. Despite the form name, this is the correct form for VAWA self-petitions. The form is filed under the "abused spouse," "abused child," or "abused parent" category.

Critically, VAWA petitions are CONFIDENTIAL. USCIS has strict policies prohibiting disclosure of your petition to the abuser. USCIS will not contact your abusive family member or notify them of your petition. This confidentiality extends to information sharing with ICE—USCIS generally does not refer VAWA petitioners to ICE for enforcement action.

Along with Form I-360, you submit evidence of the qualifying relationship (marriage certificate, birth certificate), evidence that your family member is a US citizen or LPR, evidence of the abuse, evidence that you resided with the abuser, and evidence of your good moral character. You file this as a comprehensive package.

There is currently no filing fee for Form I-360 when filed as a VAWA self-petition, making it accessible to those fleeing abuse.

**Good Moral Character Requirement:**

VAWA requires that you demonstrate good moral character during the relevant period. USCIS evaluates this based on your overall conduct. Certain criminal convictions can bar a finding of good moral character, but USCIS also considers the context, including whether any criminal behavior resulted from the abuse.

For example, if you were arrested for fighting back against your abuser in self-defense, this context matters. If your abuser forced you to commit crimes, this is also considered. You can submit evidence such as police reports, letters from community members, employment records, school records, and other documentation showing your character.

**Prima Facie Determination and Work Authorization:**

When USCIS reviews your VAWA petition, they first determine whether you have established a "prima facie case"—meaning your evidence is sufficient on its face to support your claim. If you receive a prima facie determination, you become eligible to apply for work authorization immediately by filing Form I-765. This can take several months but provides crucial economic independence while your petition is being fully adjudicated.

The prima facie determination also makes you eligible for certain public benefits under some state laws, though this varies by state.

**Path to Permanent Residence:**

Once USCIS approves your VAWA I-360 petition, you have an approved self-petition. If you are in the United States, you can then apply for adjustment of status (green card) by filing Form I-485. If your abusive family member was a US citizen, a visa number is immediately available. If they were an LPR, you may need to wait for a visa number to become available based on the family preference system, though current wait times for this category are relatively short.

If you are outside the United States when your I-360 is approved, you can apply for an immigrant visa through consular processing.

**Special Protections:**

VAWA petitioners receive several special protections. First, as mentioned, the petition is confidential. Second, VAWA petitioners are generally protected from deportation while their petition is pending, though this is discretionary and having an attorney advocate for you is important.

Third, if you entered the US without inspection or have other immigration violations, these can be forgiven when you apply for your green card. You can file Form I-601 (waiver of inadmissibility) if you have certain grounds of inadmissibility.

Fourth, if you are in removal proceedings, your pending or approved VAWA petition may be grounds for termination or administrative closure of your case. Immigration judges have discretion to grant this relief.

**VAWA for Derivative Children:**

If you are approved for a VAWA self-petition as an abused spouse or parent, your unmarried children under 21 can be included as derivatives on your petition or can file their own VAWA petitions if they were also abused. This ensures that you do not have to leave your children behind when you escape the abusive situation.

**Important Considerations:**

VAWA cases require careful documentation of the abuse, which can be emotionally difficult. Working with a trauma-informed immigration attorney and potentially a counselor or advocate can help you navigate this process. Organizations such as domestic violence shelters, legal aid offices, and immigrant rights organizations often have specialized VAWA programs.

Safety planning is essential. If you are still living with or in contact with your abuser, filing a VAWA petition without proper safety measures in place can be dangerous. Although the petition is confidential, your abuser may notice other changes (such as you applying for work authorization or moving out) and escalate the abuse. Domestic violence advocates can help you create a safety plan.

Evidence gathering should be done carefully and safely. If collecting documents, photos, or other evidence would put you at risk, prioritize your safety. USCIS understands that abuse victims may have limited access to documents.

You do not need to have a protective order or police report to file VAWA, though these can strengthen your case. Many abuse victims never call the police due to fear, language barriers, or immigration concerns, and USCIS recognizes this reality.

VAWA self-petitions reflect a congressional recognition that the immigration system should not trap people in abusive relationships. By allowing self-petitioning, VAWA empowers abuse survivors to take control of their immigration future and escape dangerous situations without fear of losing their path to lawful status.

Important: VAWA cases involve complex legal proceedings that can significantly impact your immigration status and safety. This information is for general guidance only and is not legal advice. You should consult with a qualified immigration attorney who specializes in VAWA cases before taking any action. If you are in immediate danger, please contact the National Domestic Violence Hotline at 1-800-799-7233.
""",
    },
    "Asylum": {
        "name": "Asylum (Affirmative and Defensive)",
        "visa_types": ["Asylum"],
        "content": """
Asylum is a form of protection granted to individuals who are in the United States and unable or unwilling to return to their home country because of persecution or a well-founded fear of persecution based on race, religion, nationality, membership in a particular social group, or political opinion. Asylum law in the United States is rooted in international refugee treaties and reflects a commitment to protecting those fleeing persecution.

**The Legal Standard for Asylum:**

To qualify for asylum, you must demonstrate either that you have suffered past persecution or that you have a well-founded fear of future persecution in your home country. The persecution must be on account of one of five protected grounds: race, religion, nationality, membership in a particular social group, or political opinion.

Persecution is serious harm or suffering, or a significant threat to your life or freedom. It goes beyond discrimination or harassment—it must rise to a level that fundamentally threatens your safety or liberty. Examples include physical violence, torture, imprisonment, death threats, sexual violence, forced marriage, female genital mutilation, severe economic deprivation intentionally inflicted, and denial of basic human rights.

The persecution must be inflicted by the government or by groups that the government is unable or unwilling to control. If you are fleeing gang violence, domestic violence, or other private harm, you must show that the government cannot or will not protect you.

**The Five Protected Grounds:**

Race includes persecution based on ethnic identity, skin color, or membership in a racial group. Religion covers persecution for religious beliefs, practices, or identity, including persecution for lack of religious belief. Nationality often overlaps with ethnicity and includes persecution based on national origin or citizenship.

Membership in a particular social group is the most complex ground and has been the subject of extensive legal development. A particular social group must have members who share a common immutable characteristic (something they cannot change or should not be required to change), be defined with sufficient particularity (clearly defined), and be socially distinct in the country of origin (recognized as a distinct group). Examples have included women fleeing domestic violence in countries where the government does not protect them, LGBTQ individuals in countries where homosexuality is criminalized, victims of female genital mutilation, and victims of gang recruitment.

Political opinion includes actual political beliefs, perceived political beliefs (even if you don't actually hold them), and political neutrality in situations where the persecutor demands you take a side. It also includes imputed political opinion—where the persecutor believes you hold certain political views even if you don't.

**The Nexus Requirement:**

You must establish a "nexus"—a connection—between the persecution and one of the five protected grounds. This means the persecution must be on account of your race, religion, nationality, particular social group membership, or political opinion. If you are fleeing general violence or crime without a connection to a protected ground, you do not qualify for asylum, though you may qualify for other forms of relief like withholding of removal or CAT protection.

**Affirmative vs. Defensive Asylum:**

There are two processes for seeking asylum: affirmative and defensive.

Affirmative asylum is when you file Form I-589 proactively with USCIS while you are in the United States in valid status or within one year of your arrival. USCIS schedules an interview at an asylum office where an asylum officer reviews your application. If the officer grants asylum, you receive asylum status. If the officer does not grant asylum and you are out of status, your case is referred to immigration court for defensive asylum proceedings.

Defensive asylum is when you apply for asylum as a defense against removal in immigration court. This happens if you were referred from the affirmative process, if you were apprehended by immigration authorities, or if you are already in removal proceedings. In defensive cases, you present your asylum claim to an immigration judge who decides whether to grant asylum.

**The One-Year Filing Deadline:**

You must file your asylum application within one year of your last arrival in the United States, unless you can show changed circumstances that materially affect your eligibility or extraordinary circumstances that prevented timely filing. Changed circumstances include regime changes in your country, new evidence of persecution, or changes in your personal situation that create a new basis for asylum. Extraordinary circumstances include serious illness, legal disability, ineffective assistance of counsel, mental health conditions, or having filed for other immigration relief within the one-year period.

The one-year deadline is strictly enforced, and missing it can bar you from asylum. However, you may still be eligible for withholding of removal or CAT protection, which have no filing deadline but also no path to a green card.

**Credible Fear and Reasonable Fear Screenings:**

If you arrive at a port of entry or are apprehended shortly after entering the US and express fear of return, you go through an expedited removal process. You receive a credible fear interview with an asylum officer. Credible fear means there is a significant possibility that you could establish eligibility for asylum. If you pass this screening, you are placed in full removal proceedings where you can apply for asylum.

If you have a prior removal order or certain criminal convictions, you receive a reasonable fear screening instead. This is a higher standard—you must show a reasonable possibility of persecution or torture. If you pass, you can apply for withholding of removal or CAT protection, but not asylum.

**Work Authorization:**

If you file an affirmative asylum application, you can apply for work authorization (Form I-765) after your application has been pending for 150 days, and USCIS generally grants it after 180 days. This "asylum clock" stops running if you cause delays in your case (such as requesting continuances).

If you are in immigration court proceedings, you can also apply for work authorization if your asylum application has been pending for at least 150 days and you have not caused unreasonable delays.

**Bars to Asylum:**

Certain factors can bar you from asylum eligibility. These include: persecution of others (if you participated in persecuting others), conviction of a particularly serious crime (aggravated felonies and some other serious crimes), firm resettlement in another country before arriving in the US, terrorist activity or support, and safe third country agreements (agreements requiring you to seek asylum in the first safe country you transit through).

Additionally, the one-year filing deadline operates as a bar unless you qualify for an exception.

**Dependents:**

If you are granted asylum, you can include your spouse and unmarried children under 21 as dependents, even if they are abroad. You file Form I-730 (Refugee/Asylee Relative Petition) within two years of being granted asylum. There is no fee for Form I-730, and once approved, your family members can travel to the US as derivative asylees.

**Path to Permanent Residence:**

After you have been in asylum status for one year, you can apply for a green card by filing Form I-485. Asylees are eligible to adjust status after one year of physical presence in the US as an asylee. There is an annual limit of 10,000 asylee green cards, but USCIS has historically processed these applications and the wait is usually not long.

**Termination of Asylum:**

Asylum can be terminated if conditions in your home country change such that you no longer have a well-founded fear of persecution, if you obtained asylum through fraud, if you voluntarily returned to your home country without a good reason, or if you obtain citizenship or permanent residence in another country. USCIS or DHS can initiate termination proceedings.

**Travel and Refugee Travel Documents:**

As an asylee, you generally should not travel back to your home country, as this can be viewed as re-availment (re-availing yourself of your home country's protection) and can result in termination of your asylum status. If you need to travel internationally, you can apply for a Refugee Travel Document (Form I-131), which allows you to travel to other countries. However, traveling to your home country is highly risky and can lead to loss of asylum status.

**Asylum vs. Withholding vs. CAT:**

Asylum provides the most benefits: work authorization, a path to a green card, ability to petition for family members, and the possibility of traveling with a Refugee Travel Document. Withholding of removal (discussed in another section) has a higher standard of proof, provides no path to a green card, and has no derivative benefits but is available even if asylum is barred. CAT protection (Convention Against Torture) has a different standard based on likelihood of torture and also provides no path to permanent residence.

**Important Case Preparation Considerations:**

Asylum cases require detailed personal testimony and extensive supporting evidence. You should gather country condition reports (State Department reports, human rights reports from Amnesty International, Human Rights Watch, or other reputable organizations), medical records documenting harm, psychological evaluations documenting trauma, police reports or other official documentation of persecution, affidavits from witnesses, news articles about conditions in your country, and expert testimony when available.

Your written statement (which forms part of Form I-589) should be detailed, chronological, and specific. Vague or inconsistent statements can undermine your credibility, which is central to asylum cases. Working with an experienced asylum attorney is critical to properly prepare and present your case.

If you are fleeing domestic violence, gang violence, or other private harm, establishing the particular social group and showing government inability or unwillingness to protect you requires sophisticated legal analysis and careful evidence gathering. These cases have become more complex in recent years due to changing legal standards.

**Important: Asylum cases involve complex legal proceedings that can determine whether you are removed from the United States and returned to the country where you fear persecution. This information is for general guidance only and is not legal advice. Asylum law is highly complex and constantly evolving through court decisions and policy changes. You should consult with a qualified immigration attorney who specializes in asylum cases before taking any action. If you are in removal proceedings or fear imminent deportation, seek legal assistance immediately.**
""",
    },
    "Refugee": {
        "name": "Refugee Status",
        "visa_types": ["Refugee"],
        "content": """
Refugee status is a form of protection for individuals who are outside of their home country and unable or unwilling to return due to persecution or a well-founded fear of persecution based on race, religion, nationality, membership in a particular social group, or political opinion. While refugee status and asylum are based on the same legal standard, the key difference is location: refugees apply from outside the United States, while asylum seekers apply from within the US or at a port of entry.

**How the US Refugee Program Works:**

The United States Refugee Admissions Program (USRAP) is administered through a partnership between the Department of State, Department of Homeland Security (USCIS), and Department of Health and Human Services. Each fiscal year, the President, in consultation with Congress, determines the maximum number of refugees who may be admitted and allocates this number across different regions of the world.

The refugee ceiling has varied dramatically over the years. In fiscal year 2016, the US admitted over 80,000 refugees. This number dropped significantly to 22,000 in 2018, then to historic lows around 11,000-15,000 in 2019-2021. As of 2026, the refugee ceiling has been raised but still remains subject to annual determinations and political considerations.

**Who Can Access the Refugee Program:**

You cannot simply apply to be a refugee. Instead, you must be referred to the US refugee program by the United Nations High Commissioner for Refugees (UNHCR), a US embassy, or a designated non-governmental organization. Referrals are typically made for individuals in the following situations:

First, persons in refugee camps or urban refugee situations in countries that have granted them temporary refuge but where long-term stay is not possible. Second, individuals who have fled their home country and are living in dangerous or unstable situations. Third, persons facing imminent danger who have no other durable solution available.

Priority is often given to individuals with family members already in the United States, persons facing particular vulnerability (religious minorities, LGBTQ individuals in dangerous situations, women at risk, survivors of torture or violence), and members of groups of special concern to the US.

**The Refugee Application Process:**

Once you receive a referral, you enter a multi-step vetting process. First, you complete a Resettlement Support Center (RSC) interview where you provide biographical information and details about your persecution claim. Second, USCIS officers conduct in-person interviews (sometimes abroad at refugee processing centers) to determine whether you meet the refugee definition.

USCIS applies the same legal standard used in asylum cases: you must establish persecution or a well-founded fear of persecution on account of race, religion, nationality, membership in a particular social group, or political opinion. You must also be outside of your home country and unable or unwilling to return.

Third, you undergo extensive security vetting, including biometric screening, database checks against law enforcement and intelligence databases, and multi-agency security reviews. This is the most rigorous screening process for any category of travelers to the United States and can take many months or even years.

Fourth, you undergo medical screening to check for certain health conditions. While most medical conditions are not bars to refugee admission, you must complete required vaccinations and treatment for certain communicable diseases.

Fifth, you attend cultural orientation classes to prepare for resettlement in the United States. Finally, travel arrangements are made, and you are admitted to the US as a refugee.

**Arrival in the United States:**

Upon arrival, you are immediately granted refugee status and employment authorization. You receive a Form I-94 stamped with your refugee admission. You are automatically authorized to work in the United States without needing to apply for a separate work permit.

You are connected with a resettlement agency (one of nine national voluntary agencies contracted with the State Department) that helps you with initial resettlement needs: temporary housing, enrollment in English classes, job placement assistance, school enrollment for children, cultural orientation, and connection to social services.

**Benefits and Support:**

Refugees are eligible for federal public benefits on the same basis as US citizens for the first several years after arrival. This includes Medicaid, SNAP (food assistance), TANF (cash assistance), and Refugee Cash Assistance (RCA) for those who don't qualify for TANF. States and localities may also provide additional refugee support services.

You receive assistance finding employment—usually within the first few months after arrival. The resettlement program prioritizes early economic self-sufficiency.

**Path to Permanent Residence:**

Refugees must apply for a green card (lawful permanent residence) one year after admission to the United States. You file Form I-485 (Application to Register Permanent Residence or Adjust Status) along with supporting documents. There is a filing fee, but fee waivers are available if you cannot afford it.

Unlike most other categories of adjustment of status, refugees do not need to wait for a visa number or prove that they are admissible—your admission as a refugee already established these factors. Once approved, you receive a green card backdated to one year before the approval, crediting you with an extra year toward eventual citizenship eligibility.

**Family Reunification:**

Within two years of being admitted as a refugee, you can file Form I-730 (Refugee/Asylee Relative Petition) to bring your spouse and unmarried children under 21 to the United States as derivative refugees. There is no filing fee for Form I-730. Once approved, your family members undergo security and medical screening and are admitted as refugees with the same rights and benefits you received.

It's critical to file Form I-730 within two years of your admission as a refugee. After two years, this option is no longer available, and you would need to wait until you obtain a green card or citizenship to petition for family members through the normal family-based immigration process, which takes much longer.

**Derivative Refugee Status:**

If your spouse or children are with you when you are approved for refugee status abroad, they are included as derivatives and admitted to the US with you. They receive the same status, benefits, and green card eligibility as you.

**Bars to Refugee Status:**

The same bars that apply to asylum also apply to refugee status: participation in persecution of others, particularly serious crimes, firm resettlement in another country, terrorist activity, danger to US security, and certain other criminal or security-related grounds.

Security screening for refugees is extremely thorough, and any indication of terrorist connections, criminal activity, or misrepresentation can result in denial or indefinite delay of your case.

**Travel and Documentation:**

Once admitted as a refugee, you can travel outside the United States using a Refugee Travel Document (Form I-131). However, traveling back to your home country is extremely risky—it suggests that you no longer fear persecution and can result in termination of your refugee status and denial of your green card application.

**Pathway to Citizenship:**

After you have been a lawful permanent resident (green card holder) for five years, you can apply for US citizenship by filing Form N-400 (Application for Naturalization). Importantly, your time as a refugee counts toward this five-year requirement. Because your green card is backdated to one year before approval, refugees often become eligible for citizenship about four years after receiving their green cards.

**Differences Between Refugee Status and Asylum:**

While the legal standard is the same, there are important practical differences. Refugees apply from outside the US and go through a UN or embassy referral process; asylum seekers apply from within the US or at the border. Refugees receive automatic work authorization and immediate access to resettlement assistance; asylum seekers must wait for work authorization and generally do not receive resettlement support. Refugees must apply for green cards after one year; asylees have the same requirement but the process is slightly different.

**Challenges and Considerations:**

The refugee process is extremely lengthy, often taking several years from initial referral to US arrival. During this time, you remain in a refugee situation, which may be unstable or unsafe. There is no way to expedite the process.

Annual refugee admissions caps mean that even if you are approved, you may wait months or years for an actual admission slot. Regional allocations and priority designations also affect wait times.

Family separation is a significant challenge. If your family members are not with you when you apply or if some family members don't meet the refugee definition, they may not be able to join you.

Security concerns, even unsubstantiated or based on misunderstandings, can delay or derail refugee applications indefinitely. The security screening process is opaque, and applicants often have no visibility into the reason for delays.

**Important: Refugee cases involve complex legal and factual determinations that significantly impact your ability to find safety and rebuild your life. This information is for general guidance only and is not legal advice. You should consult with a qualified immigration attorney or refugee assistance organization if you have questions about your specific situation. Legal representation can be particularly important if your case is delayed or denied.**
""",
    },
    "TPS": {
        "name": "TPS (Temporary Protected Status)",
        "visa_types": ["TPS"],
        "content": """
Temporary Protected Status (TPS) is a temporary immigration status granted to nationals of designated countries that are experiencing armed conflict, environmental disasters, epidemics, or other extraordinary and temporary conditions that make it unsafe for their nationals to return. TPS does not provide a direct path to permanent residence or citizenship, but it offers critical temporary protection from deportation and work authorization for individuals who cannot safely return home.

**How TPS Designation Works:**

The Secretary of Homeland Security has the authority to designate a country for TPS based on one or more of three statutory conditions: ongoing armed conflict that would pose a serious threat to personal safety if nationals were returned; environmental disaster (earthquake, hurricane, epidemic) that has resulted in a substantial but temporary disruption of living conditions; or extraordinary and temporary conditions in the country that prevent nationals from returning safely.

TPS designations are published in the Federal Register and specify the designation period (typically 6 to 18 months), the registration period during which nationals can apply, and the eligibility requirements. Designations can be extended if conditions in the country have not improved, and they can be terminated if the Secretary determines that conditions have changed such that TPS is no longer warranted.

**Countries Currently Designated for TPS (as of 2026):**

As of early 2026, the following countries have TPS designation: **Venezuela, El Salvador, Honduras, Haiti, Nicaragua, Guatemala, Nepal, Somalia, South Sudan, Sudan, Syria, Ukraine, Myanmar (Burma), and Yemen.**

These designations are critical for large immigrant communities in the United States, particularly nationals of Venezuela, El Salvador, Honduras, Haiti, and Nicaragua. For example, hundreds of thousands of Venezuelans in the US have TPS protection due to the ongoing political, humanitarian, and economic crisis in Venezuela. Similarly, Salvadorans, Hondurans, and Nicaraguans have had TPS protection for many years due to natural disasters and subsequent deteriorating conditions.

It is essential to check the current TPS designation for your country, as designations can be extended, terminated, or newly granted. USCIS publishes Federal Register notices announcing any changes to TPS designations.

**Eligibility Requirements:**

To be eligible for TPS, you must: (1) be a national of a country designated for TPS, or a person without nationality who last habitually resided in the designated country; (2) have been continuously physically present in the United States since the effective date specified in the Federal Register notice for your country; (3) have continuously resided in the United States since the date specified in the Federal Register notice (usually the designation date); (4) register during the open registration period or re-registration period; and (5) not be subject to certain criminal or security-related bars.

Continuous physical presence means you have been physically in the US since the specified date with only brief, casual, and innocent departures. Continuous residence means you have maintained residence in the US since the specified date; it allows for brief departures but not an abandonment of US residence.

**Criminal and Security Bars:**

You are ineligible for TPS if you have been convicted of one felony or two or more misdemeanors committed in the United States, or if you are subject to certain mandatory bars to asylum (persecution of others, terrorist activity, danger to US security). Even if you have a criminal conviction, depending on the nature and timing of the conviction, you may still be eligible, so it's important to consult with an attorney.

**The TPS Application Process:**

You apply for TPS by filing Form I-821 (Application for Temporary Protected Status) during the designated registration or re-registration period. You also file Form I-765 (Application for Employment Authorization) at the same time to receive work authorization, and Form I-821D if applicable. There are filing fees, but fee waivers are available for those who cannot afford them.

You must provide evidence of your nationality (passport, birth certificate, national identity document), evidence of your continuous residence and continuous physical presence (utility bills, rent receipts, employment records, medical records, school records), and evidence of identity. Two passport-style photos are required.

USCIS processes your application and, if approved, grants you TPS status and issues an Employment Authorization Document (EAD) valid for the duration of the TPS designation period. You must re-register during each re-registration period to maintain your status.

**Re-Registration:**

TPS is temporary and must be renewed. Before each TPS designation period expires, USCIS publishes a Federal Register notice announcing the extension of the designation and opening a re-registration period (usually 60 days). During this period, current TPS holders must file Form I-821 and Form I-765 again to renew their status and work authorization for the next designation period.

Failing to re-register on time can result in loss of TPS status and work authorization. If you miss the re-registration period, you may be able to file a late initial registration if you can show good cause for the delay, but this is discretionary and should be avoided.

**Benefits of TPS:**

TPS provides several important benefits. First, you cannot be deported from the United States during the TPS designation period. Immigration authorities will not remove you to your home country. Second, you receive employment authorization and can work legally for any employer in the US.

Third, you can obtain a Social Security number if you don't already have one. Fourth, you can apply for travel authorization (advance parole) using Form I-131. If approved, you can travel abroad and return to the US, though travel is subject to certain conditions and risks.

Fifth, in some states, TPS holders are eligible for certain public benefits, such as driver's licenses or professional licenses, though this varies by state.

**What TPS Does NOT Provide:**

TPS is a temporary status. It does not, by itself, provide a path to a green card or permanent residence. If TPS is terminated for your country, you revert to whatever immigration status you had before (or no status if you were undocumented). You can be placed in removal proceedings once TPS ends.

TPS does not cure unlawful presence. If you entered the US without inspection, TPS does not change that. However, time spent in TPS status is not counted as unlawful presence for purposes of the 3-year and 10-year bars, which is important if you later become eligible to adjust status through another avenue (such as a family petition).

**Pathway to Permanent Residence:**

While TPS itself does not lead to a green card, many TPS holders become eligible for permanent residence through other routes. If a US citizen immediate relative (spouse, parent if you are under 21, or adult child if you are the parent) petitions for you, you may be able to adjust status to permanent residence. If you entered the US lawfully with a visa (even if you overstayed), you can generally adjust status. If you entered without inspection, you would typically need to leave the US and process through a consulate, but this triggers unlawful presence bars.

Some TPS holders have been able to obtain green cards through employment-based petitions if they have a US employer willing to sponsor them and they meet the requirements.

Congress has periodically considered legislation that would provide a path to permanent residence for long-term TPS holders, but as of 2026, no such legislation has passed. Some TPS holders have maintained status for 10, 20, or even 30 years while conditions in their home countries remain unsafe.

**Travel Authorization:**

TPS holders can apply for advance parole to travel outside the United States. You file Form I-131 (Application for Travel Document) and, if approved, can travel abroad for a specific purpose (family emergency, work, etc.) and return. However, travel is risky if you have other immigration violations or criminal issues, as you may be questioned or denied reentry. Always consult with an attorney before traveling on advance parole.

**Children Born in the US:**

If you have TPS status and your child is born in the United States, your child is a US citizen by birth. Once your child turns 21, they can petition for you as an immediate relative of a US citizen, providing you with a pathway to a green card (subject to admissibility and other requirements).

**Impact of TPS Termination:**

When the Secretary of Homeland Security determines that conditions in a country have improved sufficiently, TPS can be terminated. Terminations are generally announced at least 60 days before the current designation expires, with a wind-down period (often 6-12 months) to allow individuals to prepare.

If TPS is terminated, you lose protection from deportation and work authorization once the wind-down period ends. You must either depart the US voluntarily, obtain another immigration status, or face potential removal proceedings.

There have been significant legal and political battles over TPS terminations. For example, attempted terminations of TPS for El Salvador, Haiti, Nicaragua, and Sudan were challenged in court and temporarily blocked for several years before eventually being reinstated by subsequent administrations.

**TPS for Venezuelans: A Critical Protection:**

The TPS designation for Venezuela is particularly important given the massive humanitarian and political crisis in that country and the hundreds of thousands of Venezuelans who have fled to the United States in recent years. The designation has been extended multiple times and provides essential work authorization and protection from deportation for a vulnerable population.

For Venezuelans, TPS has become a lifeline while conditions in Venezuela remain unsafe for return. However, because TPS is temporary and subject to political decisions, Venezuelan TPS holders face uncertainty about their long-term status. Advocacy efforts continue to push for a pathway to permanent residence for long-term TPS holders.

**State-Level Benefits:**

Many states allow TPS holders to obtain driver's licenses, which is crucial for employment and daily life. Some states also allow TPS holders to access in-state tuition at public universities, professional and occupational licenses, and certain state-funded public benefits. Eligibility varies by state, so you should check your state's specific rules.

**Important Considerations:**

TPS is time-sensitive. You must register or re-register during designated periods, and missing deadlines can result in loss of status. Set reminders for re-registration periods and monitor USCIS announcements.

TPS does not protect you from deportation if you commit certain crimes or engage in certain conduct that makes you removable. Even with TPS, you must comply with US laws.

If you have TPS and also have a pending asylum application, adjustment of status application, or other immigration benefit, work closely with an attorney to understand how these interact.

TPS is subject to political changes. Administrations have differing views on TPS, and designations can be extended or terminated based on policy shifts. Staying informed and planning for the possibility of termination is important.

**This is critical protection for immigrant communities from Venezuela, El Salvador, Honduras, Haiti, Nicaragua, and other designated countries. If you are from one of these countries, check immediately whether you are eligible for TPS and whether a registration period is currently open.**

Important: TPS cases involve complex legal proceedings that can significantly impact your immigration status and safety. This information is for general guidance only and is not legal advice. You should consult with a qualified immigration attorney who specializes in TPS cases before taking any action, particularly if you have criminal history or other complicating factors.
""",
    },
    "DACA": {
        "name": "DACA (Deferred Action for Childhood Arrivals)",
        "visa_types": ["DACA"],
        "content": """
Deferred Action for Childhood Arrivals (DACA) is an administrative immigration policy that provides temporary protection from deportation and work authorization for certain undocumented individuals who were brought to the United States as children. DACA is not a visa, legal status, or pathway to citizenship—it is a discretionary exercise of prosecutorial discretion by the Department of Homeland Security. However, for hundreds of thousands of young immigrants, DACA has provided critical stability, work authorization, and the ability to pursue education and careers.

**The History and Legal Status of DACA:**

DACA was announced by the Obama administration in June 2012 as a response to the failure of Congress to pass comprehensive immigration reform, particularly the DREAM Act, which would have provided a pathway to legal status for undocumented youth. DACA was implemented as an exercise of DHS's prosecutorial discretion to defer deportation for certain low-priority individuals.

DACA has faced significant legal challenges. In 2017, the Trump administration announced the termination of DACA, leading to years of litigation. In 2020, the Supreme Court ruled that the termination process was unlawful and reinstated DACA. However, in 2021, a federal judge in Texas ruled that DACA itself was unlawful, though that decision only applied to new applications and existing DACA recipients could continue to renew.

As of 2026, DACA remains in legal limbo. Current DACA recipients can renew their status, but new applications are not being processed due to the ongoing litigation and injunctions. The program's future depends on court decisions and potential congressional action. This creates significant uncertainty for DACA recipients and for those who would be eligible but cannot currently apply.

**Eligibility Requirements:**

To be eligible for DACA, you must meet all of the following requirements as of the time you submit your initial application:

First, you were under the age of 31 as of June 15, 2012. Second, you came to the United States before reaching your 16th birthday. Third, you have continuously resided in the United States since June 15, 2007, up to the present time.

Fourth, you were physically present in the United States on June 15, 2012, and at the time of making your request for DACA. Fifth, you had no lawful status on June 15, 2012 (meaning you never had lawful immigration status, or any status you had expired before that date).

Sixth, you are currently in school, have graduated or obtained a certificate of completion from high school, have obtained a general education development (GED) certificate, or are an honorably discharged veteran of the Coast Guard or Armed Forces of the United States.

Seventh, you have not been convicted of a felony, significant misdemeanor, or three or more other misdemeanors, and do not otherwise pose a threat to national security or public safety.

**What DACA Provides:**

If approved for DACA, you receive: (1) Deferred action—a promise from DHS that you are not an enforcement priority and will not be deported for a renewable two-year period; (2) Employment authorization—an Employment Authorization Document (EAD) that allows you to work legally for any employer in the United States; (3) A Social Security number, if you don't already have one; (4) In most states, eligibility for a driver's license; and (5) In some cases, advance parole to travel outside the United States, though this carries significant risks and should only be pursued with legal advice.

**What DACA Does NOT Provide:**

DACA is not a legal status. It does not make you a lawful permanent resident, does not provide a visa, and does not put you on any path to citizenship or a green card. DACA is temporary and must be renewed every two years. DACA can be terminated at any time by DHS, either on an individual basis (if you no longer meet the requirements or engage in certain conduct) or through a policy change affecting the entire program.

DACA does not cure your unlawful presence in the United States. If DACA ends and you do not obtain another form of legal status, you could be placed in removal proceedings and deported.

DACA does not allow you to petition for family members to immigrate to the United States. Only lawful permanent residents and US citizens can sponsor family members, and DACA is neither.

**The DACA Application Process:**

To apply for DACA (when new applications are being accepted), you file Form I-821D (Consideration of Deferred Action for Childhood Arrivals), Form I-765 (Application for Employment Authorization), and Form I-765 Worksheet. There is a filing fee, though fee exemptions were available in certain circumstances.

You must provide extensive documentation proving: your identity and age (passport, birth certificate, school records), your entry to the US before age 16 (passport stamps, travel records, school records, medical records), your continuous residence since June 15, 2007 (utility bills, rent receipts, employment records, school records, medical records, tax returns), your physical presence on June 15, 2012, your educational status (high school diploma, GED, school transcripts, enrollment records), and lack of disqualifying criminal convictions.

The documentation requirements are extensive, and many applicants have difficulty proving continuous residence, particularly for the early years. USCIS accepts a wide range of documents, but they must cover the entire period from June 15, 2007, to the present with minimal gaps.

**DACA Renewal:**

DACA must be renewed every two years. You should file your renewal application (Form I-821D and Form I-765) approximately 120-150 days before your current DACA expires. USCIS generally processes renewals and issues new work authorization before the current period expires, but processing times can vary.

Failing to renew on time can result in a gap in work authorization and protection from deportation. If you miss the renewal deadline, you may be able to file a late renewal, but USCIS treats this as a new initial application and has discretion to deny it.

**Criminal Convictions and DACA:**

DACA has strict requirements regarding criminal history. A single felony conviction disqualifies you. A "significant misdemeanor"—defined as a misdemeanor involving violence, threat, sexual abuse or exploitation, burglary, DUI, drug trafficking, or for which you were sentenced to more than 90 days—also disqualifies you. Three or more misdemeanors of any kind disqualify you.

If you are arrested or convicted of a crime while you have DACA, you must report this to USCIS, and your DACA may be terminated. Even if the conviction doesn't technically fall into a disqualifying category, USCIS retains discretion to deny or terminate DACA if it determines you pose a threat to public safety or national security.

**Advance Parole for DACA Recipients:**

In certain circumstances, DACA recipients can apply for advance parole—permission to travel outside the United States for humanitarian, educational, or employment purposes. You file Form I-131 (Application for Travel Document), and if approved, you can travel and return.

However, advance parole carries risks. If you have ever been unlawfully present in the US for more than 180 days after age 18, leaving the US (even with advance parole) can trigger the 3-year or 10-year unlawful presence bar, making you inadmissible when you try to return. Additionally, if a new administration terminates DACA while you are abroad, you could be stranded outside the US.

Advance parole should only be pursued with careful legal advice and for compelling reasons.

**Pathways to Legal Status for DACA Recipients:**

While DACA itself does not lead to a green card, DACA recipients may become eligible for lawful permanent residence through other routes. The most common pathways include:

Marriage to a US citizen: If you marry a US citizen, they can petition for you with Form I-130. However, if you entered the US without inspection (illegally crossed the border), you generally cannot adjust status in the US and would need to process through a consulate abroad, triggering unlawful presence bars unless you qualify for a waiver.

If you entered the US with a visa or through advance parole and then fell out of status, you may be able to adjust status in the US based on your US citizen spouse's petition. This is a complex area, and DACA recipients with US citizen spouses should consult an experienced immigration attorney.

Employment-based petitions: Some DACA recipients have been sponsored for employment-based green cards by employers. This requires the employer to go through the labor certification process (for most categories) and file an I-140 petition. However, similar to family-based cases, if you entered without inspection, you face barriers to adjusting status.

Special legislation: Congress has repeatedly considered legislation (such as various versions of the DREAM Act or the American Dream and Promise Act) that would provide a pathway to permanent residence for DACA recipients and other Dreamers. As of 2026, no such legislation has passed, but advocacy efforts continue.

**State-Level Benefits:**

Many states allow DACA recipients to obtain driver's licenses and state identification cards. Some states provide in-state tuition at public colleges and universities for DACA recipients who meet residency requirements. A few states have created state-funded financial aid programs for DACA students.

However, eligibility varies widely by state. Some states have explicitly barred DACA recipients from certain benefits, while others have expanded access.

**Federal Benefits:**

DACA recipients are generally not eligible for federal means-tested public benefits, including Medicaid (except emergency Medicaid in some states), SNAP (food stamps), SSI, federal housing assistance, or most federal financial aid for college. However, some private scholarships and institutional aid are available to DACA students.

DACA recipients can obtain Social Security numbers and can work and pay taxes. They are required to file tax returns like any other worker.

**Mental Health and Community Impact:**

DACA recipients live with significant uncertainty and stress. The program's temporary nature, the ongoing litigation, the inability to visit family abroad without risk, and the lack of a pathway to permanent status create psychological burdens. Studies have shown that DACA has provided significant mental health and economic benefits to recipients, but the precarity of the program remains a source of anxiety.

Many DACA recipients are "mixed-status" families—they may have US citizen siblings or parents with legal status, while they themselves remain in limbo. This creates complex family dynamics and challenges.

**What Happens If DACA Ends:**

If DACA is terminated (either for an individual or through a program-wide termination), recipients lose their work authorization and protection from deportation. They would revert to being undocumented and could be placed in removal proceedings if encountered by immigration authorities.

In the event of a program-wide termination, there would likely be a wind-down period, but recipients would need to explore other options for legal status or face the possibility of deportation.

**The "Dreamers" Movement:**

DACA recipients are often referred to as "Dreamers" after the DREAM Act (Development, Relief, and Education for Alien Minors), the proposed legislation that would have provided a pathway to legal status. The Dreamer movement has been one of the most visible and organized immigrant rights movements in recent years, advocating for permanent legislative solutions.

**Important: DACA is a temporary administrative program subject to ongoing legal challenges and policy changes. It does not provide legal status or a pathway to permanent residence. This information is for general guidance only and is not legal advice. DACA recipients and those who would be eligible for DACA should consult with a qualified immigration attorney to understand their options, particularly if they have criminal history, travel plans, or potential eligibility for other forms of relief. If you are a DACA recipient considering marriage, employment sponsorship, or other pathways to legal status, legal advice is essential.**
""",
    },
    "Withholding of Removal": {
        "name": "Withholding of Removal",
        "visa_types": ["Withholding of Removal"],
        "content": """
Withholding of removal is a form of protection for individuals who face persecution in their home country but do not qualify for asylum or for whom asylum has been denied. It is based on the same statutory provision as asylum (the Immigration and Nationality Act, following the 1951 Refugee Convention) but requires a higher standard of proof and provides fewer benefits. While withholding of removal does not lead to permanent residence or allow you to petition for family members, it does prevent the US government from deporting you to the specific country where you would face persecution.

**The Legal Standard for Withholding of Removal:**

To qualify for withholding of removal, you must demonstrate that it is "more likely than not" that you would be persecuted in your home country on account of race, religion, nationality, membership in a particular social group, or political opinion. This is a higher standard than asylum, which requires only a "well-founded fear" of persecution (generally understood as a 10% or greater chance).

"More likely than not" means greater than 50% probability. You must present sufficient evidence to convince an immigration judge that if you were returned to your country, it is more probable than not that you would be persecuted.

The definition of persecution and the protected grounds (race, religion, nationality, particular social group, political opinion) are the same as for asylum. You must show that the persecution is on account of one of these five grounds and that the government is the persecutor or is unable or unwilling to control private actors who would persecute you.

**Why Apply for Withholding Instead of Asylum:**

Most people apply for withholding of removal because they are barred from asylum but still face persecution. Common reasons for asylum ineligibility include: missing the one-year filing deadline for asylum applications, having a particularly serious crime conviction that bars asylum, having firmly resettled in another country before coming to the US, or being subject to the safe third country or other asylum bars.

Withholding of removal has no filing deadline, so even if you've been in the US for many years, you can still apply. It is available even to individuals with certain criminal convictions that would bar asylum, as long as the conviction is not an aggravated felony or does not fall under other mandatory bars to withholding.

**Mandatory Bars to Withholding of Removal:**

You are barred from withholding of removal if: you ordered, incited, assisted, or otherwise participated in the persecution of others on account of a protected ground; you have been convicted of a "particularly serious crime" in the United States (aggravated felonies are considered particularly serious crimes, and other serious felonies may also qualify); there are serious reasons to believe you have committed a serious nonpolitical crime outside the United States; or there are reasonable grounds to believe you are a danger to the security of the United States.

The "particularly serious crime" bar is significant. Aggravated felonies—a broad category under immigration law—automatically bar withholding of removal. Additionally, immigration judges can determine on a case-by-case basis that other felonies or even serious misdemeanors constitute particularly serious crimes depending on the nature, circumstances, and sentence.

**The Withholding of Removal Process:**

Withholding of removal is only available as a defense in removal (deportation) proceedings before an immigration judge. You cannot apply affirmatively to USCIS like you can with asylum. If you are in removal proceedings and your asylum claim is denied (or you are ineligible for asylum), you can apply for withholding of removal in the same hearing.

You present your claim to an immigration judge, providing testimony and evidence that you face persecution in your home country. The judge evaluates the credibility of your testimony, the consistency of your statements, and the corroborating evidence (country condition reports, expert testimony, medical records, affidavits, etc.).

If the judge finds that you have met the higher "more likely than not" standard, the judge grants withholding of removal. This means the US government cannot deport you to the specific country where you face persecution.

**What Withholding of Removal Provides:**

Withholding of removal provides a limited set of protections. First, you cannot be removed to the country where you would face persecution. The removal order is entered, but it is not executed to that specific country. If there is another country to which you are removable and where you would not face persecution, the government can deport you there (though this is rare in practice).

Second, you receive work authorization. After being granted withholding of removal, you can apply for an Employment Authorization Document (EAD) by filing Form I-765. You can renew this authorization periodically.

Third, you are not deported and can remain in the United States indefinitely as long as withholding remains in effect.

**What Withholding of Removal Does NOT Provide:**

Withholding of removal has significant limitations compared to asylum. First, there is no pathway to a green card or permanent residence. You remain in a form of limbo—you can stay and work, but you do not accrue time toward permanent residence or citizenship.

Second, you cannot petition for family members to join you in the United States. Unlike asylees, who can file Form I-730 for derivative family members, individuals with withholding of removal have no mechanism to reunify with spouse or children.

Third, you cannot obtain a refugee travel document. While some individuals with withholding may be able to apply for advance parole in limited circumstances, international travel is extremely restricted and risky.

Fourth, withholding can be terminated if country conditions change such that you would no longer face persecution. If the government demonstrates changed circumstances, your withholding can be revoked, and you can be deported.

Fifth, withholding only applies to the specific country where you would face persecution. If you are removable to another country and do not face persecution there, the government could theoretically remove you to that third country.

**Termination of Withholding:**

The government can move to terminate withholding of removal if: (1) there is a fundamental change in circumstances in your home country such that you no longer face persecution; (2) you engage in conduct that would have made you ineligible for withholding in the first place (such as committing a particularly serious crime); or (3) there are reasonable grounds to believe you are a danger to the United States.

If the government files a motion to terminate, you have the right to a hearing before an immigration judge where you can present evidence that you still face persecution or that conditions have not meaningfully changed.

**Withholding vs. Asylum: Key Differences:**

| Feature | Asylum | Withholding of Removal |
|---------|--------|------------------------|
| Standard of proof | Well-founded fear (~10% chance) | More likely than not (>50% chance) |
| Filing deadline | One year from arrival (with exceptions) | No deadline |
| Criminal bars | Some felonies and aggravated felonies | Particularly serious crimes/aggravated felonies |
| Path to green card | Yes, after one year | No |
| Family reunification | Yes, Form I-730 for spouse/children | No |
| Travel | Refugee travel document available | Very limited, no travel document |
| Termination | Discretionary, difficult to terminate | Can be terminated if conditions change |

**Withholding vs. CAT Protection:**

Withholding of removal is also different from protection under the Convention Against Torture (CAT). CAT protection is available if you would more likely than not be tortured by or with the acquiescence of a government official if returned to your country. CAT has no bars (even aggravated felons can receive CAT protection), but it provides even fewer benefits than withholding—no path to permanent residence, no family reunification, and can be terminated if risk of torture diminishes.

Many applicants apply for asylum, withholding of removal, and CAT protection in the alternative, presenting all three claims to the immigration judge.

**Evidence and Documentation:**

Proving the "more likely than not" standard requires strong evidence. You should present: detailed personal testimony about the persecution you suffered or fear; country condition reports from the State Department, human rights organizations (Amnesty International, Human Rights Watch), and academic sources; expert testimony from country conditions experts or regional specialists; medical or psychological evaluations documenting harm or trauma; news articles and reports about conditions affecting people in your situation; and affidavits from witnesses or others with knowledge of your claim.

Your credibility is central. Inconsistencies between your testimony and prior statements, your written application, or other evidence can undermine your claim. Working with an experienced attorney to prepare your testimony and organize your evidence is critical.

**Strategic Considerations:**

If you are in removal proceedings and ineligible for asylum, withholding of removal may be your only option to remain in the United States. While the benefits are limited, they are far preferable to deportation to a country where you face persecution.

If you have a particularly serious crime conviction, you may be barred from both asylum and withholding. In that case, CAT protection (if you would be tortured) may be your only remaining defense against removal.

If you are granted withholding of removal, you should explore whether any other pathways to permanent residence might become available—such as a US citizen family member petitioning for you, an employment-based petition, special legislation, or adjustment through another avenue. While withholding itself does not provide a path to a green card, it allows you to remain in the US and potentially access other forms of relief in the future.

**Practical Implications:**

Living with withholding of removal means indefinite uncertainty. You can work and live in the US, but you cannot advance to permanent residence, cannot travel freely, and cannot reunify with family. Many individuals with withholding live in this status for decades.

You should maintain valid work authorization by timely filing Form I-765 renewals. You should avoid any criminal activity, as even a minor conviction could trigger termination proceedings or removal. You should stay informed about conditions in your home country, as improvements could lead the government to seek termination of your withholding.

If you have US citizen children, once they turn 21, they may be able to petition for you. However, you would likely need to depart the US and process through a consulate abroad, which triggers unlawful presence bars if you accrued unlawful presence. This is a complex area requiring careful legal analysis.

**Important: Withholding of removal cases involve complex legal proceedings in immigration court that can determine whether you are deported to a country where you face persecution. This information is for general guidance only and is not legal advice. You should consult with a qualified immigration attorney who specializes in removal defense and withholding of removal cases before taking any action. If you are in removal proceedings, seek legal representation immediately.**
""",
    },
    "CAT": {
        "name": "CAT (Convention Against Torture)",
        "visa_types": ["CAT"],
        "content": """
Protection under the Convention Against Torture (CAT) is a form of relief available to individuals facing removal from the United States who can demonstrate that they would more likely than not be tortured if returned to their home country. CAT protection is based on the United Nations Convention Against Torture and Other Cruel, Inhuman or Degrading Treatment or Punishment, which the United States ratified in 1994. CAT provides a critical safety net for individuals who face torture but may not qualify for asylum or withholding of removal due to criminal convictions or other bars.

**What is Torture Under CAT:**

For purposes of CAT protection, torture is defined as any act by which severe pain or suffering, whether physical or mental, is intentionally inflicted on a person for purposes such as obtaining information or a confession, punishing the person, intimidating or coercing the person, or for any reason based on discrimination of any kind. The act must be inflicted by or at the instigation of or with the consent or acquiescence of a public official or other person acting in an official capacity.

Key elements of the torture definition: First, the harm must constitute severe pain or suffering, not just discomfort or hardship. Second, the harm must be intentionally inflicted for a prohibited purpose (punishment, coercion, intimidation, discrimination, etc.). Third, critically, the torture must be inflicted by or with the consent or acquiescence of government officials. Purely private acts, even if they constitute torture, do not qualify unless the government is involved or turns a blind eye.

The "acquiescence" requirement means that if the government is aware of torture being inflicted by private actors and willfully accepts it (by not intervening or providing protection), this can satisfy the CAT standard. For example, if a gang or cartel tortures individuals and the government knows about it but does nothing, this may constitute acquiescence.

**The Legal Standard for CAT Protection:**

To qualify for CAT protection, you must establish that it is "more likely than not" (greater than 50% probability) that you would be tortured if removed to your home country. This is the same standard as withholding of removal but applied to torture rather than persecution.

You must show: (1) the torture you would face meets the definition above; (2) it would be inflicted by or with government acquiescence; (3) you personally would be tortured (not just that torture occurs in the country generally); and (4) the likelihood is greater than 50%.

**No Bars to CAT Protection:**

The most significant feature of CAT protection is that there are no bars. Unlike asylum and withholding of removal, CAT protection is available even if you have been convicted of aggravated felonies, particularly serious crimes, or any other criminal offense. You can receive CAT protection even if you participated in the persecution of others, committed serious nonpolitical crimes, or pose a danger to US security.

This makes CAT protection the last-resort defense for individuals who are statutorily barred from all other forms of relief but genuinely face torture if removed.

**Two Forms of CAT Protection: Withholding vs. Deferral:**

There are two forms of CAT protection, and immigration judges determine which applies based on your circumstances.

**Withholding of Removal Under CAT:** This is granted if you are not subject to mandatory detention and are not otherwise barred from withholding of removal under the relevant statute. Withholding under CAT means the US cannot remove you to the country where you would be tortured. Like non-CAT withholding, you receive work authorization and can remain in the US indefinitely unless conditions change.

**Deferral of Removal Under CAT:** This is granted if you are subject to mandatory detention or are otherwise barred from withholding (for example, due to an aggravated felony conviction). Deferral also prevents removal to the country of torture, but it is even more precarious than withholding. Deferral can be terminated at any time if the immigration authorities determine that you are no longer likely to be tortured or if there is a diplomatic assurance from the receiving country that you will not be tortured. Additionally, individuals granted deferral can be kept in immigration detention.

Deferral is less protective than withholding and is subject to review every six months or whenever the government seeks termination.

**The CAT Application Process:**

CAT protection is only available as a defense in removal proceedings before an immigration judge. You present your CAT claim alongside or in the alternative to asylum and withholding of removal.

You must provide detailed evidence of: the torture you would face, the government's involvement or acquiescence, and the likelihood that you personally would be tortured. Evidence can include: your personal testimony about past torture or threats; country condition reports documenting torture practices in your country (State Department reports, UN reports, human rights organizations); expert testimony from country conditions experts or torture specialists; medical or psychological evaluations documenting past torture or trauma; and affidavits from witnesses or other individuals with knowledge of conditions in the country.

Country condition evidence is particularly important in CAT cases. You must show not just that torture occurs in your country, but that government officials engage in or tolerate torture, and that you would be at risk.

**What CAT Protection Provides:**

CAT protection (whether withholding or deferral) provides: (1) protection from removal to the country where you would be tortured; (2) work authorization (you can apply for an EAD); and (3) the ability to remain in the United States.

If you receive withholding under CAT, you generally cannot be detained solely based on your immigration status (though you can be detained if you have certain criminal convictions). If you receive deferral, you may be subject to mandatory detention or periodic detention reviews.

**What CAT Protection Does NOT Provide:**

CAT protection has severe limitations. First, there is no pathway to permanent residence or citizenship. You remain in a form of limbo indefinitely.

Second, you cannot petition for family members to join you. There is no derivative CAT protection for spouses or children.

Third, you have no travel document and cannot leave the United States. Unlike asylees or even withholding recipients who may in rare cases obtain advance parole, CAT protection does not include any travel authorization.

Fourth, CAT protection can be terminated if the government demonstrates that you are no longer likely to be tortured (for example, due to a change in government or change in conditions in your country). For deferral cases, the standard for termination is even lower—the government can terminate if they obtain diplomatic assurances that you will not be tortured.

Fifth, individuals with CAT protection often face continued immigration enforcement attention. If conditions change or if a third country is willing to accept you, the government may remove you to that third country.

**Termination and Review:**

The government can file a motion to terminate CAT protection at any time if they believe conditions have changed such that you are no longer likely to be tortured. You have the right to a hearing where you can present updated evidence that the risk of torture remains.

For deferral of removal, the government reviews your case every six months or as needed. If the government obtains diplomatic assurances from your home country that you will not be tortured, they can terminate deferral and remove you. Diplomatic assurances are controversial—human rights organizations have documented cases where assurances were given but individuals were tortured upon return. However, US law allows termination of deferral based on such assurances.

**CAT vs. Asylum and Withholding:**

| Feature | Asylum | Withholding of Removal | CAT Protection |
|---------|--------|------------------------|----------------|
| Standard | Well-founded fear | More likely than not (persecution) | More likely than not (torture) |
| Bars | Criminal, security, firm resettlement, 1-year deadline | Particularly serious crime, security | None |
| Path to green card | Yes | No | No |
| Family reunification | Yes | No | No |
| Travel | Yes (Refugee Travel Document) | Limited | No |
| Termination | Difficult | If conditions change | If conditions change or diplomatic assurances |

**Evidence Challenges in CAT Cases:**

Proving the "more likely than not" standard for torture requires strong evidence. Merely showing that torture occurs in your country is not enough—you must show that you personally would be tortured. This often requires demonstrating that you belong to a group targeted for torture (political dissidents, ethnic minorities, LGBTQ individuals, journalists, etc.) and that the government is involved.

Proving government acquiescence can be difficult. You must show that the government knows about the torture and willfully accepts it, not just that the government is weak or has limited resources. Evidence of police cooperation with gangs, military involvement in violence, or official policies condoning torture is critical.

Expert testimony is highly valuable in CAT cases. Experts can testify about torture practices in your country, patterns of government involvement, and the likelihood that you would be targeted.

**Strategic Considerations:**

CAT protection is often the last line of defense for individuals with serious criminal convictions who are barred from asylum and withholding. If you have an aggravated felony or particularly serious crime conviction, CAT may be your only option.

Many applicants apply for asylum, withholding of removal, and CAT protection in the alternative, presenting all three claims to the immigration judge. The judge evaluates each claim separately and grants the highest level of protection for which you qualify.

If you receive CAT protection (especially deferral), you should continuously monitor conditions in your home country. If conditions improve or if the government changes in a way that reduces the risk of torture, the US government may seek to terminate your protection and remove you.

**Practical Implications:**

Living under CAT protection is extremely restrictive. You cannot travel, cannot obtain permanent residence, and cannot reunify with family. You may be subject to detention or supervision. You live with the constant possibility that your protection will be terminated and you will be deported.

However, for individuals who genuinely face torture, CAT protection is life-saving. It prevents return to countries where you would face severe harm.

If you have US citizen children, they may be able to petition for you once they turn 21, but the process is complex due to your immigration status and any criminal convictions. You would likely need to depart the US and apply from abroad, and you may be subject to permanent bars or require waivers. This requires careful legal analysis.

**Detention and CAT Deferral:**

Individuals granted deferral of removal under CAT are often subject to prolonged immigration detention. While the government cannot remove you to the country where you would be tortured, they can detain you indefinitely while seeking a third country willing to accept you or while waiting for conditions to change.

Some individuals with CAT deferral have been detained for years. Periodic custody reviews may allow for release on supervision (such as GPS monitoring or check-ins with ICE), but this is discretionary.

**Important: CAT protection cases involve complex legal proceedings in immigration court that can determine whether you are removed to a country where you face torture. This information is for general guidance only and is not legal advice. You should consult with a qualified immigration attorney who specializes in removal defense and CAT protection cases before taking any action. If you are in removal proceedings, especially with criminal convictions, seek experienced legal representation immediately.**
""",
    },
    "SIJS": {
        "name": "SIJS (Special Immigrant Juvenile Status)",
        "visa_types": ["SIJS", "EB-4"],
        "content": """
Special Immigrant Juvenile Status (SIJS) is an immigration protection for children in the United States who have been abused, neglected, or abandoned by one or both parents and for whom it would not be in their best interest to return to their home country. SIJS provides a pathway to lawful permanent residence (a green card) for vulnerable children, recognizing that they should not be forced to return to situations where they were harmed or cannot be properly cared for.

**Who Qualifies for SIJS:**

To be eligible for SIJS, you must meet several requirements. First, you must be under 21 years old and unmarried. Even if you are 18, 19, or 20 years old, you can still qualify as long as you remain unmarried and under 21 at the time you file your SIJS petition (Form I-360).

Second, you must be physically present in the United States. There is no requirement for how you entered the US or what immigration status you currently have (or don't have). Many SIJS applicants are undocumented, while others may have overstayed visas or entered with inspection.

Third, you must be under the jurisdiction of a juvenile court in the United States, or you must have been declared dependent on a juvenile court or legally committed to or placed under the custody of a state agency, department, or individual appointed by a state or juvenile court. In practice, this means you need a state court order.

Fourth, the state juvenile or family court must have made specific findings: (1) that reunification with one or both parents is not viable due to abuse, neglect, abandonment, or a similar basis under state law; and (2) that it is not in your best interest to return to your home country or your parents' home country.

These court findings are the foundation of the SIJS petition. Without a qualifying state court order, you cannot apply for SIJS.

**What Constitutes Abuse, Neglect, or Abandonment:**

Abuse includes physical abuse, sexual abuse, emotional abuse, and other forms of maltreatment. Neglect means the failure of a parent to provide necessary care, supervision, education, medical treatment, or other needs. Abandonment means the parent has voluntarily relinquished parental duties and has failed to maintain contact or provide support.

Importantly, the abuse, neglect, or abandonment does not need to meet a criminal standard. Family courts evaluate these issues based on state family law, which often has a lower threshold than criminal law. For example, a parent who left the child with relatives and has not provided financial support or maintained contact for years may be found to have abandoned the child, even if no criminal abandonment charge was filed.

The court must find that reunification with one or both parents is not viable. This does not necessarily mean both parents—if one parent abused or neglected you, but the other parent is safe and capable, you may still qualify if reunification with the abusive parent is not viable.

**The State Court Process:**

The first step in an SIJS case is obtaining the required findings from a state juvenile or family court. The process varies by state, but generally involves filing a petition in state court requesting that the court make findings of abuse, neglect, or abandonment and that it is not in your best interest to return to your home country.

In some states, this happens through a dependency or custody proceeding. In others, it can be done through a guardianship or custody case. Some states have created streamlined SIJS procedures, while others require more traditional family court proceedings.

You will need an attorney (or in some jurisdictions, may be able to proceed pro se with guidance) to file the state court petition. Many legal aid organizations, children's law centers, and immigration nonprofits assist with SIJS state court cases.

The court will hold a hearing where you (and potentially witnesses, social workers, or other parties) testify about the abuse, neglect, or abandonment and why it is not in your best interest to return to your country. The court evaluates evidence such as affidavits, school records, medical records, psychological evaluations, child protective services reports, and testimony.

If the court makes the required findings, it issues an order containing specific language required for SIJS purposes. This order is critical—it must explicitly state the findings regarding abuse/neglect/abandonment, lack of viability of reunification, and that return is not in your best interest.

**The Federal USCIS Process (Form I-360):**

Once you have the state court order with the required findings, you file Form I-360 (Petition for Amerasian, Widow(er), or Special Immigrant) with USCIS under the Special Immigrant Juvenile category. You submit the state court order, evidence of your age, evidence of your dependency on the court or placement, and other supporting documents.

There is currently no filing fee for Form I-360 when filed as an SIJS petition. USCIS reviews your petition and, if approved, grants you SIJS classification. This approval means USCIS has determined you meet the federal requirements for SIJS.

**Adjustment of Status to Permanent Residence:**

After your I-360 is approved, you can apply for adjustment of status (a green card) by filing Form I-485. SIJS falls under the employment-based fourth preference (EB-4) category for special immigrants. You must wait for a visa number to become available in this category.

For most countries, visa numbers are immediately available, meaning you can file your I-485 concurrently with or shortly after your I-360. However, for countries with high demand (particularly India, Mexico, the Philippines, and China), there can be significant backlogs. As of 2026, the backlog for Mexico and other countries has grown, and some SIJS applicants wait several years for a visa number.

When you file Form I-485, you also file Form I-765 (for work authorization) and Form I-131 (for advance parole, allowing travel). You can receive work authorization and a travel document while your green card application is pending.

**Special Protections and Considerations:**

SIJS applicants receive several important protections. First, USCIS generally does not share information from SIJS petitions with ICE for enforcement purposes. This is a confidentiality protection to encourage vulnerable children to come forward without fear of deportation.

Second, certain grounds of inadmissibility are waived for SIJS applicants. When you apply for your green card, you can request a waiver of most grounds of inadmissibility (except national security and certain other serious grounds) by filing Form I-601. This means that even if you entered the US illegally, overstayed a visa, or have other immigration violations, you can still adjust status.

Third, public benefits received by SIJS applicants generally do not count against them under the public charge rule. SIJS applicants are explicitly exempt from public charge inadmissibility.

**Age-Out Protections:**

One of the most important aspects of SIJS is the age-out protection. You must be under 21 and unmarried when you file your Form I-360. However, if you file before turning 21, you are protected from aging out—even if you turn 21 or marry while your I-360 or I-485 is pending, your application is generally protected under the Child Status Protection Act (CSPA).

There have been some legal challenges and evolving interpretations of age-out protections in SIJS cases, so it's important to work with an attorney and file as early as possible if you are approaching 21.

**Derivative Family Members:**

Unlike many other immigration categories, SIJS does not provide derivative benefits for family members. You cannot include your parents or siblings on your SIJS petition. However, once you obtain your green card, you can eventually petition for certain family members (though this would be years in the future and subject to family preference visa backlogs).

If you have children of your own, they may be able to obtain derivative status as dependents on your I-485, but this is a complex area given the nature of SIJS (which is for juveniles who themselves have suffered abuse or neglect).

**Travel Considerations:**

Before you receive advance parole (Form I-131 approval), traveling outside the United States can be extremely risky. If you leave the US without advance parole, you may be unable to return and may abandon your SIJS application.

Even with advance parole, travel should be carefully considered. If you travel back to your home country, this could undermine the state court's finding that it is not in your best interest to return there. USCIS could question whether you still qualify for SIJS if you voluntarily return to the country from which you sought protection.

Travel to third countries (not your home country) with advance parole is generally safer, but you should consult with an attorney before making any international travel plans.

**Consent of the Attorney General:**

Form I-360 includes a section on "consent" for SIJS cases. In the past, applicants needed to request the consent of the Attorney General (now delegated to USCIS) to the grant of SIJS. USCIS's approval of your I-360 constitutes this consent. However, the consent requirement is an important part of the statute and means that USCIS retains discretion to deny SIJS even if you meet the technical requirements.

USCIS can deny consent if they determine that the state court proceedings were sought primarily to obtain immigration benefits rather than for legitimate dependency or custody purposes. This is rare, but USCIS scrutinizes cases where the state court proceeding appears solely focused on SIJS with no genuine child welfare basis.

**Interactions with Other Relief:**

SIJS can be pursued alongside other forms of relief. For example, if you also qualify for VAWA (as an abused child of a USC or LPR), you could file both VAWA and SIJS petitions. If you have DACA, you can still apply for SIJS, and SIJS provides a pathway to a green card that DACA does not.

SIJS is often a better option than U visa for children who have been abused by parents, because SIJS has no annual cap and no law enforcement certification requirement. However, if the abuse involved a qualifying crime and you cooperated with law enforcement, a U visa might also be an option.

**Common Scenarios:**

SIJS cases arise in many different situations. Common examples include: a child whose parent brought them to the US but then abandoned them with relatives and stopped providing support; a child who was physically or sexually abused by a parent in their home country and fled to the US; a child whose parent died or became incapable of caring for them, and it is not safe for the child to return; a child in foster care in the US due to abuse or neglect; and a child whose parent is abusive, neglectful, or incarcerated and cannot or will not care for the child.

**Strategic Considerations:**

Timing is critical in SIJS cases. If you are approaching age 21, you should move quickly to obtain the state court order and file Form I-360. Delays can result in aging out and losing eligibility.

The state court order must contain specific language. Working with an attorney experienced in SIJS is essential to ensure the order includes all required findings in language that USCIS will accept.

Evidence for the state court hearing should be comprehensive—affidavits, medical records, school records, psychological evaluations, child protective services records, and any documentation of abuse, neglect, or abandonment. The stronger your evidence, the more likely the court is to make the findings.

If you are undocumented or have removal orders, SIJS can be pursued even while in removal proceedings. An immigration attorney can file motions in immigration court to administratively close your case while you pursue SIJS.

**Long-Term Pathway:**

SIJS provides a pathway not just to a green card, but eventually to US citizenship. Once you have been a lawful permanent resident for five years (or three years if you marry a US citizen), you can apply for naturalization. This means SIJS offers a permanent solution for children who have been abused, neglected, or abandoned.

**Important: SIJS cases involve complex state court proceedings and federal immigration petitions that can significantly impact your ability to remain in the United States and obtain permanent residence. This information is for general guidance only and is not legal advice. You should consult with a qualified immigration attorney who specializes in SIJS cases before taking any action. If you are approaching age 21, seek legal assistance immediately to avoid aging out.**
""",
    },
    "Humanitarian Parole": {
        "name": "Humanitarian Parole / CHNV",
        "visa_types": ["Humanitarian Parole"],
        "content": """
Humanitarian parole is a discretionary immigration mechanism that allows individuals who are otherwise inadmissible to the United States to temporarily enter the country for urgent humanitarian reasons or significant public benefit. Parole does not grant legal status or provide a pathway to permanent residence, but it allows temporary presence in the US and the ability to apply for work authorization. Humanitarian parole has been used in a variety of situations, from medical emergencies to large-scale humanitarian programs.

**The CHNV Parole Program (Cuba, Haiti, Nicaragua, Venezuela) — TERMINATED:**

One of the most significant recent uses of humanitarian parole was the CHNV program announced in January 2023 to provide temporary protection for nationals of Cuba, Haiti, Nicaragua, and Venezuela. This program allowed up to 30,000 individuals per month from these four countries to be paroled into the United States for up to two years if they had a US-based supporter and passed security vetting.

**However, as of March 25, 2025, the CHNV parole program was officially terminated by executive order.** No new applications are being accepted, and no new grants of parole under CHNV are being issued.

For individuals who previously received CHNV parole, their status remains valid until the end of their authorized parole period (typically two years from entry). After that period expires, individuals must depart the United States or obtain another form of lawful status (such as asylum, TPS, or a family-based petition).

**Current Alternatives for CHNV-Affected Nationals:**

For nationals of Cuba, Haiti, Nicaragua, and Venezuela who were relying on CHNV or are now seeking protection, several alternatives may be available:

First, **Temporary Protected Status (TPS)** is currently designated for Venezuela, Haiti, Nicaragua, and El Salvador (not Cuba as of 2026). Venezuelan, Haitian, and Nicaraguan nationals who were in the United States by the cutoff date specified in the TPS designation may be eligible to apply for TPS, which provides work authorization and protection from deportation (though TPS does not lead to a green card).

Second, **Asylum** remains available for individuals who have a well-founded fear of persecution based on race, religion, nationality, political opinion, or membership in a particular social group. Asylum has a one-year filing deadline (with exceptions) and provides a pathway to permanent residence.

Third, **family-based petitions** may be available if you have a US citizen or lawful permanent resident spouse, parent, or child who can petition for you.

Fourth, other forms of protection such as withholding of removal or CAT protection may be available in removal proceedings if you face persecution or torture.

**General Humanitarian Parole (Non-CHNV):**

Outside of the terminated CHNV program, general humanitarian parole remains available on a case-by-case basis for individuals with urgent humanitarian reasons or where parole would provide a significant public benefit.

You apply for humanitarian parole by filing Form I-131 (Application for Travel Document), specifically checking the humanitarian parole option. The application is filed by a US-based sponsor (usually a family member or organization) or by the individual seeking parole if they are abroad.

**Urgent Humanitarian Parole** is granted for situations such as: a medical emergency where an individual needs urgent treatment not available in their home country; a family emergency such as the death or serious illness of a close family member in the US; or other compelling circumstances where parole is the only way to address an urgent need.

**Significant Public Benefit Parole** is granted where the individual's presence in the US would serve an important public interest, such as: participating in legal proceedings as a witness or party; assisting law enforcement or government agencies; or other situations where the public interest in the individual's presence outweighs concerns about their admission.

**Requirements for Humanitarian Parole:**

Parole is discretionary, meaning USCIS has full authority to grant or deny applications based on the circumstances. You must demonstrate: (1) an urgent humanitarian reason or significant public benefit; (2) that you are not otherwise admissible to the United States (if you are admissible, you should apply for a visa rather than parole); (3) that parole is the only or most appropriate mechanism for you to enter the US; and (4) that you merit a favorable exercise of discretion.

USCIS evaluates parole applications on a case-by-case basis considering the totality of the circumstances. Evidence should include detailed explanation of the humanitarian need, medical records (for medical emergencies), death certificates or hospital records (for family emergencies), letters from doctors or other professionals, evidence of the relationship between the beneficiary and the sponsor, and evidence that parole is the only viable option.

**Processing and Approval:**

USCIS processes Form I-131 humanitarian parole applications at their discretion. Some applications are processed quickly (within weeks) in truly urgent situations, while others can take many months. There is no guaranteed processing time, and applicants often face frustration with delays.

If approved, USCIS issues a grant of parole, usually for a specific period (often 1-2 years, but can be shorter for specific purposes). The individual can then travel to the US and be paroled into the country by Customs and Border Protection at a port of entry.

**What Parole Provides:**

Humanitarian parole allows you to be physically present in the United States temporarily. You are not admitted as a nonimmigrant or immigrant—you are paroled. Once in the US on parole, you can apply for work authorization by filing Form I-765. Work authorization is granted at USCIS's discretion and is typically approved for the duration of the parole period.

You are authorized to remain in the US for the duration specified in your parole grant. You can apply for extension or re-parole if the humanitarian circumstances continue, though this is also discretionary.

**What Parole Does NOT Provide:**

Parole is not a visa and does not grant lawful status. You are considered an "applicant for admission" while on parole, not a lawful nonimmigrant. Parole does not provide a pathway to a green card or permanent residence on its own. You cannot adjust status to permanent residence based solely on humanitarian parole (with a few exceptions, such as Cubans under the Cuban Adjustment Act or Afghans/Ukrainians under recent special legislation).

Parole does not allow you to petition for family members. You cannot accumulate time toward permanent residence or citizenship based on parole. When your parole period ends, you must depart the United States or obtain another form of lawful status. Remaining in the US after parole expires results in unlawful presence and makes you subject to removal.

**Advanced Parole vs. Humanitarian Parole:**

It's important to distinguish humanitarian parole from advance parole. Advance parole is a travel document issued to individuals who are already in the United States in certain statuses (such as adjustment of status applicants, DACA recipients, or TPS holders) allowing them to travel abroad and return. Advance parole is filed using the same Form I-131 but is a different category.

Humanitarian parole is for individuals who are outside the US seeking to enter temporarily for urgent humanitarian reasons.

**Cubans and the Cuban Adjustment Act:**

Cuban nationals who are paroled into the United States (or who arrive by other means) have a unique benefit: under the Cuban Adjustment Act, Cubans can apply for a green card after one year of physical presence in the US. This makes parole particularly valuable for Cubans, as it provides a pathway to permanent residence that is not available to other paroled nationals.

However, the Cuban Adjustment Act has been subject to political debate, and its future is uncertain. As of 2026, it remains in effect but has faced calls for repeal or modification.

**Afghans, Ukrainians, and Special Parole Programs:**

In recent years, the US government has created large-scale parole programs for Afghans (following the US withdrawal from Afghanistan in 2021) and Ukrainians (following Russia's invasion of Ukraine in 2022). These programs (known as "Uniting for Ukraine" for Ukrainians and various Afghan programs) allowed tens of thousands of individuals to be paroled into the US for humanitarian reasons.

Congress has considered and in some cases passed legislation providing pathways to permanent residence for certain paroled Afghans and Ukrainians. These are complex, evolving programs, and individuals in these categories should seek legal advice to understand their options.

**Parole in Place:**

A separate concept is "parole in place," which is parole granted to individuals who are already in the United States unlawfully. This has been used in limited circumstances, such as for immediate family members of US military service members. Parole in place allows the individual to remain in the US lawfully, making them eligible to adjust status to permanent residence if they have an approved immigrant petition.

As of 2026, parole in place is available on a limited basis and requires specific eligibility. It is not widely available to the general undocumented population.

**Expiration and Departure:**

When your humanitarian parole expires, you are required to depart the United States unless you have obtained another form of lawful status. Remaining in the US after parole expires accrues unlawful presence, which can trigger 3-year or 10-year bars to future admission if you depart.

If you obtained another form of status before your parole expired (such as asylum, TPS, adjustment of status, or a nonimmigrant visa), you can remain lawfully. Many parolees use the parole period to explore other immigration options, file asylum applications, or have family members petition for them.

**Strategic Considerations:**

Humanitarian parole is highly discretionary, and approval is never guaranteed. You should only apply if you have a genuine urgent humanitarian need and strong supporting evidence.

If you have the option to apply for a visa (such as a visitor visa, student visa, or immigrant visa), you should generally pursue that route instead of parole, as visas provide more stability and, in some cases, a pathway to longer-term status.

If you are paroled into the US, immediately consult with an immigration attorney to determine whether you are eligible for any other form of relief (asylum, TPS, adjustment of status, etc.) that could provide long-term stability.

If your parole is expiring and you have not obtained another status, you should consult with an attorney about your options: applying for re-parole, filing for asylum or other relief, or departing the US to avoid accruing unlawful presence.

**Important: Humanitarian parole cases involve discretionary decision-making by USCIS and can significantly impact your ability to enter and remain in the United States temporarily. This information is for general guidance only and is not legal advice. The CHNV program has been terminated as of March 25, 2025, and individuals previously relying on CHNV should consult with a qualified immigration attorney to understand their options going forward. If you are seeking humanitarian parole, consult with an immigration attorney to evaluate your eligibility and prepare a strong application.**
""",
    },
    "Cancellation of Removal": {
        "name": "Cancellation of Removal",
        "visa_types": ["Cancellation of Removal"],
        "content": """
Cancellation of removal is a form of relief available in immigration court proceedings that allows certain long-term residents of the United States to avoid deportation and obtain lawful permanent residence (a green card). There are two types of cancellation: cancellation for lawful permanent residents (LPRs) and cancellation for non-permanent residents. Both require significant physical presence in the US, good moral character, and meeting other strict requirements. Cancellation is granted at the discretion of an immigration judge and is subject to annual caps, making it highly competitive.

**Cancellation of Removal for Non-Lawful Permanent Residents:**

This form of cancellation is available to individuals who are not lawful permanent residents (green card holders) but who have lived in the United States for many years and have strong family ties. It is one of the few pathways for undocumented individuals or those in temporary status to obtain a green card without having to leave the United States.

**Eligibility Requirements:**

To qualify for non-LPR cancellation, you must meet all of the following requirements:

First, you must have been physically present in the United States for a continuous period of at least 10 years immediately preceding the date you apply for cancellation. This 10-year period ends on the date you are placed in removal proceedings (when you receive a Notice to Appear or NTA). Any period of physical presence after the NTA does not count toward the 10 years.

Continuous physical presence means you have been in the US for 10 years without a single absence of 90 days or more, or multiple absences totaling 180 days or more. Even a single absence of 90 days or more breaks the continuous presence, and you must start the 10-year count over again.

Second, you must have been a person of good moral character during the 10-year period. Good moral character is evaluated based on criminal history, truthfulness, payment of taxes, and overall conduct. Certain criminal convictions automatically bar a finding of good moral character, including aggravated felonies, murder, and certain other serious crimes. Even lesser criminal conduct can affect the good moral character determination.

Third, you must demonstrate that your removal would result in exceptional and extremely unusual hardship to your qualifying relative—your spouse, parent, or child who is a US citizen or lawful permanent resident. This is a very high standard. Normal hardship that would result from family separation is not enough. The hardship must be exceptional (beyond what is typical in removal cases) and extremely unusual (significantly beyond what would normally be expected).

Fourth, you must not have been convicted of certain disqualifying criminal offenses. You are ineligible if you have been convicted of an aggravated felony (as defined in immigration law, which is a broad category), certain crimes involving moral turpitude, drug trafficking, persecution of others, terrorist activity, or other serious crimes.

**The Exceptional and Extremely Unusual Hardship Standard:**

This is the most challenging element of non-LPR cancellation. The hardship must be to a qualifying relative—your US citizen or LPR spouse, parent, or child. Hardship to you (the person in removal proceedings) or to other family members (such as siblings, grandparents, or non-citizen children) is not considered, except to the extent it indirectly affects a qualifying relative.

Immigration judges consider factors such as: the age of the qualifying relative (hardship to young children or elderly parents is given more weight); health conditions or special needs of the qualifying relative; the qualifying relative's ties to the United States (how long they've lived here, whether they speak English, employment, education, community connections); the qualifying relative's ties to your home country (whether they have ever lived there, speak the language, have family or support networks there); the country conditions in your home country and the impact on the qualifying relative if they had to relocate there; and the financial, medical, educational, and psychological consequences of your removal.

Examples of exceptional and extremely unusual hardship might include: a US citizen child with severe medical or developmental needs who depends on you for care and for whom no adequate care is available in your home country; a US citizen spouse with serious health conditions who cannot work and depends on your income and care; or a situation where relocation to your home country would place the qualifying relative in danger or would result in the loss of critical medical treatment.

Ordinary economic hardship, the difficulty of raising children as a single parent, or the emotional pain of family separation—while significant—are generally not enough to meet the exceptional and extremely unusual standard.

**The 4,000 Annual Cap:**

Congress imposed an annual cap of 4,000 on the number of non-LPR cancellation grants per fiscal year. Because demand far exceeds this cap, many applicants who meet the legal requirements and whose cases are granted by an immigration judge still cannot receive cancellation immediately. Instead, they are placed on a waiting list and receive cancellation when a slot becomes available, which can take several years. While waiting, they remain in removal proceedings but with protection from deportation.

**The Application Process:**

Cancellation of removal is only available as a defense in removal proceedings before an immigration judge. You cannot apply affirmatively to USCIS. If you are placed in removal proceedings (usually by receiving a Notice to Appear from ICE or after a credible fear interview at the border), you can apply for cancellation.

You file Form EOIR-42A (Application for Cancellation of Removal and Adjustment of Status for Certain Nonpermanent Residents) with the immigration court. You must provide extensive evidence of your 10 years of physical presence (utility bills, rent receipts, employment records, tax returns, school records, medical records, dated photographs, affidavits from friends and family, etc.), your good moral character (letters of recommendation, evidence of community ties, employment history, tax records, police clearances), and the exceptional and extremely unusual hardship your qualifying relative would suffer (medical records, psychological evaluations, expert testimony about country conditions, affidavits from the qualifying relative and others, financial documentation, school records, etc.).

The hearing is your opportunity to present testimony and evidence. You testify about your time in the US, your family, and the hardship your removal would cause. Your qualifying relatives testify about the impact your removal would have on them. Expert witnesses (such as psychologists, medical doctors, or country conditions experts) may testify. The immigration judge evaluates the credibility of the testimony and the strength of the evidence.

If the judge finds that you meet all the requirements and that you merit a favorable exercise of discretion, the judge grants cancellation and adjusts your status to lawful permanent resident. You receive a green card.

**Cancellation of Removal for Lawful Permanent Residents:**

This form of cancellation is available to individuals who are already green card holders but who are in removal proceedings due to criminal convictions or other grounds of removability. It allows LPRs to retain their green cards and remain in the United States despite the removal ground.

**Eligibility Requirements for LPR Cancellation:**

First, you must have been lawfully admitted for permanent residence for at least 5 years. Second, you must have resided in the United States continuously for at least 7 years after having been admitted in any status (this can include time before you became an LPR, such as time on a visa or in another status).

Third, you must not have been convicted of an aggravated felony. This is an absolute bar—any aggravated felony conviction makes you ineligible for LPR cancellation, no matter how strong your equities or how minor the offense may seem. Aggravated felonies under immigration law include a wide range of crimes, many of which are not actually aggravated or felonies under criminal law.

**No Hardship Requirement for LPR Cancellation:**

Unlike non-LPR cancellation, LPR cancellation does not require you to prove exceptional and extremely unusual hardship to a qualifying relative. Instead, the immigration judge exercises discretion based on the totality of your circumstances: the length of time you've lived in the US, your family ties, your employment and community ties, your criminal history, rehabilitation, and other positive and negative factors.

**No Annual Cap for LPR Cancellation:**

There is no annual cap on LPR cancellation. If you meet the requirements and the judge grants your application, you retain your green card immediately.

**Stop-Time Rule:**

Both LPR and non-LPR cancellation are subject to the "stop-time rule." For non-LPR cancellation, the 10 years of continuous physical presence stops accruing on the earlier of: (1) the date you commit certain crimes (such as crimes involving moral turpitude or aggravated felonies); or (2) the date you are served with a Notice to Appear.

This means that if you have been in the US for 8 years and then receive a Notice to Appear, you cannot reach the 10-year requirement—your clock stopped at 8 years. Similarly, if you have been in the US for 12 years but committed a disqualifying crime after only 9 years, you are credited with only 9 years.

For LPR cancellation, the stop-time rule works similarly—your continuous residence stops accruing upon commission of certain crimes or service of the NTA.

**Discretionary Nature of Cancellation:**

Even if you meet all the statutory requirements for cancellation, the immigration judge has discretion to deny your application based on negative factors. Judges weigh positive factors (length of residence, family ties, employment, rehabilitation, community involvement, hardship to family) against negative factors (criminal history, immigration violations, fraud, lack of rehabilitation).

Serious criminal conduct, even if it doesn't legally bar cancellation, can result in a discretionary denial. Conversely, strong equities—such as decades of residence, US citizen children, employment, and community ties—can support a favorable discretionary grant.

**Appeals and Review:**

If the immigration judge denies your cancellation application, you can appeal to the Board of Immigration Appeals (BIA). If the BIA affirms the denial, you may be able to seek further review in federal court, though the scope of review is limited.

If the judge grants cancellation, the government (DHS/ICE) can appeal the decision to the BIA. During the appeal, you generally remain in the US.

**Practical Considerations:**

Cancellation cases are document-intensive. Gathering 10 years of continuous presence evidence can be challenging, especially if you did not maintain organized records. Start collecting evidence as early as possible: bills, receipts, school records, medical records, employment records, tax returns, and any dated documents showing your presence.

Hardship evidence for non-LPR cancellation should be detailed and specific. Generic statements about how hard it would be to live in another country are not enough. You need medical records, psychological evaluations, expert reports, and detailed testimony about the specific, individualized hardship your qualifying relative would face.

Criminal history is a critical factor. If you have any criminal convictions, consult with an immigration attorney to determine whether you are eligible for cancellation and whether the convictions are aggravated felonies or otherwise disqualifying.

Timing matters. If you are approaching the 10-year mark and have not yet been placed in removal proceedings, you should be extremely cautious about any actions that could lead to an NTA (such as applying for immigration benefits for which you are not eligible, traveling internationally, or coming to the attention of immigration authorities).

**Alternatives to Cancellation:**

If you do not qualify for cancellation, other forms of relief may be available depending on your circumstances: asylum or withholding of removal if you fear persecution; adjustment of status based on a family or employment petition; T or U visa if you are a victim of trafficking or certain crimes; VAWA self-petition if you are a victim of domestic violence; or voluntary departure, which allows you to leave the US on your own terms rather than being removed.

**Important: Cancellation of removal cases involve complex legal proceedings in immigration court that determine whether you can remain in the United States and obtain permanent residence. This information is for general guidance only and is not legal advice. The exceptional and extremely unusual hardship standard is very high, and cancellation is granted at the discretion of the immigration judge. You should consult with a qualified immigration attorney who specializes in removal defense and cancellation of removal cases before taking any action. If you are in removal proceedings or at risk of being placed in proceedings, seek experienced legal representation immediately.**
""",
    },
}


async def ingest_visa_humanitarian(dry_run=False, visa_types_filter=None):
    """Ingest humanitarian visa overviews into Pinecone."""
    if visa_types_filter:
        categories = {k: v for k, v in HUMANITARIAN_VISAS.items() if k in visa_types_filter}
    else:
        categories = HUMANITARIAN_VISAS

    logger.info(f"Ingesting {len(categories)} humanitarian visa categories (dry_run={dry_run})")

    clients = await setup_clients()

    all_chunks = []
    all_metadata = []

    for category_key, category_data in categories.items():
        logger.info(f"Processing: {category_data['name']}")

        chunks = chunk_text(
            text=category_data["content"],
            chunk_size=512,
            overlap=50
        )

        logger.info(f"  Created {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source_type": "visa_overview",
                "visa_category": "humanitarian",
                "visa_name": category_data["name"],
                "visa_types": category_data["visa_types"],
                "document_title": category_data["name"],
                "chunk_index": i,
            })

    logger.info(f"Total chunks to upsert: {len(all_chunks)}")

    vectors_upserted = await upsert_to_pinecone(
        clients.index, all_chunks, all_metadata,
        source="visa_overview", dry_run=dry_run,
    )
    logger.info(f"Humanitarian visa ingestion complete: {vectors_upserted} vectors upserted")


async def main():
    parser = argparse.ArgumentParser(description="Ingest humanitarian visa overviews into Pinecone")
    parser.add_argument("--dry-run", action="store_true", help="Run without upserting to Pinecone")
    parser.add_argument(
        "--visa-types",
        type=str,
        help="Comma-separated list of visa types to ingest (e.g., 'TPS,DACA,Asylum')"
    )
    args = parser.parse_args()

    visa_types_filter = None
    if args.visa_types:
        visa_types_filter = [vt.strip() for vt in args.visa_types.split(",")]
        logger.info(f"Filtering to visa types: {visa_types_filter}")

    await ingest_visa_humanitarian(dry_run=args.dry_run, visa_types_filter=visa_types_filter)


if __name__ == "__main__":
    asyncio.run(main())
