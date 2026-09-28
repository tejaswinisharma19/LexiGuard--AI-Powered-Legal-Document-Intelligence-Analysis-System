"""
Constitution of India Knowledge Base Module
Contains official constitutional text data, metadata (Part, Chapter, Article, Clause),
and local retrieval logic for Constitutional RAG.
"""

CONSTITUTION_DATA = [
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "General / Right to Equality",
        "article": "Article 14",
        "title": "Equality before law",
        "text": "The State shall not deny to any person equality before the law or the equal protection of the laws within the territory of India.",
        "keywords": ["equality", "equal protection", "equality before law", "discrimination", "article 14"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Equality",
        "article": "Article 15",
        "title": "Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth",
        "text": "The State shall not discriminate against any citizen on grounds only of religion, race, caste, sex, place of birth or any of them.",
        "keywords": ["discrimination", "caste", "religion", "sex", "article 15"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Equality",
        "article": "Article 16",
        "title": "Equality of opportunity in matters of public employment",
        "text": "There shall be equality of opportunity for all citizens in matters relating to employment or appointment to any office under the State.",
        "keywords": ["public employment", "employment", "opportunity", "article 16"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Freedom",
        "article": "Article 19(1)(a)",
        "title": "Protection of certain rights regarding freedom of speech, etc.",
        "text": "All citizens shall have the right to freedom of speech and expression; to assemble peaceably and without arms; to form associations or unions; to move freely throughout the territory of India; to reside and settle in any part of the territory of India.",
        "keywords": ["freedom of speech", "speech and expression", "expression", "freedom", "assemble", "article 19", "19(1)(a)"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Freedom",
        "article": "Article 20",
        "title": "Protection in respect of conviction for offences",
        "text": "No person shall be convicted of any offence except for violation of a law in force at the time of the commission of the act charged as an offence, nor be subjected to a penalty greater than that which might have been inflicted under the law in force at the time of the commission of the offence.",
        "keywords": ["conviction", "double jeopardy", "self-incrimination", "ex post facto", "article 20"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Freedom",
        "article": "Article 21",
        "title": "Protection of life and personal liberty",
        "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
        "keywords": ["life and personal liberty", "life", "personal liberty", "liberty", "privacy", "article 21"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Freedom",
        "article": "Article 21A",
        "title": "Right to Education",
        "text": "The State shall provide free and compulsory education to all children of the age of six to fourteen years in such manner as the State may, by law, determine.",
        "keywords": ["education", "free education", "children", "article 21a"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Freedom",
        "article": "Article 22",
        "title": "Protection against arrest and detention in certain cases",
        "text": "No person who is arrested shall be detained in custody without being informed, as soon as may be, of the grounds for such arrest nor shall he be denied the right to consult, and to be defended by, a legal practitioner of his choice.",
        "keywords": ["arrest", "detention", "legal practitioner", "article 22"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right against Exploitation",
        "article": "Article 23",
        "title": "Prohibition of traffic in human beings and forced labour",
        "text": "Traffic in human beings and begar and other similar forms of forced labour are prohibited and any contravention of this provision shall be an offence punishable in accordance with law.",
        "keywords": ["forced labour", "human trafficking", "begar", "article 23"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Freedom of Religion",
        "article": "Article 25",
        "title": "Freedom of conscience and free profession, practice and propagation of religion",
        "text": "Subject to public order, morality and health, all persons are equally entitled to freedom of conscience and the right freely to profess, practise and propagate religion.",
        "keywords": ["freedom of religion", "religion", "conscience", "article 25"]
    },
    {
        "part": "Part III — Fundamental Rights",
        "chapter": "Right to Constitutional Remedies",
        "article": "Article 32",
        "title": "Remedies for enforcement of rights conferred by this Part",
        "text": "The right to move the Supreme Court by appropriate proceedings for the enforcement of the rights conferred by this Part is guaranteed. The Supreme Court shall have power to issue directions or orders or writs.",
        "keywords": ["constitutional remedies", "writs", "supreme court", "habeas corpus", "article 32"]
    },
    {
        "part": "Part IV — Directive Principles of State Policy",
        "chapter": "Directive Principles",
        "article": "Article 44",
        "title": "Uniform civil code for the citizens",
        "text": "The State shall endeavour to secure for the citizens a Uniform Civil Code throughout the territory of India.",
        "keywords": ["uniform civil code", "ucc", "civil code", "article 44"]
    },
    {
        "part": "Part IVA — Fundamental Duties",
        "chapter": "Fundamental Duties",
        "article": "Article 51A",
        "title": "Fundamental duties",
        "text": "It shall be the duty of every citizen of India to abide by the Constitution and respect its ideals and institutions, the National Flag and the National Anthem; to cherish and follow the noble ideals which inspired our national struggle for freedom.",
        "keywords": ["fundamental duties", "duties", "national flag", "article 51a"]
    },
    {
        "part": "Part XX — Amendment of the Constitution",
        "chapter": "Amendment",
        "article": "Article 368",
        "title": "Power of Parliament to amend the Constitution and procedure therefor",
        "text": "Notwithstanding anything in this Constitution, Parliament may in exercise of its constituent power amend by way of addition, variation or repeal any provision of this Constitution in accordance with the procedure laid down in this article.",
        "keywords": ["amend constitution", "amendment", "parliament power", "article 368"]
    }
]


def search_constitution(query: str):
    """
    Local-first search over the Constitution Knowledge Base.
    Returns matching Constitutional Provision dict or None if not found.
    """
    if not query:
        return None

    q_lower = query.lower().strip()

    # Exact article match check (e.g. "article 14", "article 19", "article 21")
    for item in CONSTITUTION_DATA:
        art_clean = item["article"].lower()
        if art_clean in q_lower or art_clean.replace(" ", "") in q_lower.replace(" ", ""):
            return item

    # Keyword / Semantic score match
    best_item = None
    best_score = 0

    for item in CONSTITUTION_DATA:
        score = 0
        for kw in item["keywords"]:
            if kw in q_lower:
                score += 3
        if item["title"].lower() in q_lower:
            score += 4
        
        # Check matching words in title/text
        words = q_lower.split()
        for w in words:
            if len(w) > 3:
                if w in item["title"].lower():
                    score += 1
                if w in item["text"].lower():
                    score += 0.5

        if score > best_score:
            best_score = score
            best_item = item

    if best_score >= 2:
        return best_item

    return None
