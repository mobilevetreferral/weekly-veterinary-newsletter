#!/usr/bin/env python3
"""Generate a weekly veterinary newsletter draft from Europe PMC results."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv(BASE_DIR / ".env")

DEFAULT_BRAND_NAME = os.getenv("NEWSLETTER_BRAND_NAME", "Vet Weekly Digest")
DEFAULT_LOGO_URL = os.getenv(
    "NEWSLETTER_LOGO_URL",
    "https://mobilevetreferral.co.uk/wp-content/uploads/2024/01/mobile-vet-referral-high-resolution-logo-transparent.png",
)
DEFAULT_LOGO_ALT = os.getenv("NEWSLETTER_LOGO_ALT", "Mobile Vet Referral")
DEFAULT_CONTACT_NAME = os.getenv("NEWSLETTER_CONTACT_NAME", "Fabrizio Tucciarone")
DEFAULT_EDITOR_NAME = os.getenv("NEWSLETTER_EDITOR_NAME", DEFAULT_CONTACT_NAME)
DEFAULT_CONTACT_CREDENTIALS = os.getenv(
    "NEWSLETTER_CONTACT_CREDENTIALS",
    "DVM MRCVS GPcert(SAM) MSc PgCert(Endo) CertAVP",
)
DEFAULT_CONTACT_COMPANY = os.getenv("NEWSLETTER_CONTACT_COMPANY", "Mobile Vet Referral Ltd")
DEFAULT_CONTACT_LOCATION = os.getenv("NEWSLETTER_CONTACT_LOCATION", "Northampton")
DEFAULT_CONTACT_PHONE = os.getenv("NEWSLETTER_CONTACT_PHONE", "07440765031")
DEFAULT_CONTACT_WEBSITE = os.getenv("NEWSLETTER_CONTACT_WEBSITE", "https://www.mobilevetreferral.co.uk")
DEFAULT_SITE_URL = os.getenv("NEWSLETTER_SITE_URL", DEFAULT_CONTACT_WEBSITE)
DEFAULT_TIMEZONE = os.getenv("NEWSLETTER_TIMEZONE", "Europe/London")

TITLE_KEYWORDS = {
    "emergency": 3,
    "clinical": 3,
    "treatment": 3,
    "therapy": 3,
    "survival": 3,
    "diagnostic": 2,
    "prevalence": 2,
    "risk": 2,
    "icu": 2,
    "review": 2,
    "guideline": 2,
    "randomized": 2,
    "retrospective": 1,
    "prospective": 1,
}

ISSUE_THEMES = [
    (
        "client adherence and long-term disease management",
        ["owner persistence", "adherence", "self-efficacy", "immunotherapy", "asit", "atopic"],
    ),
    (
        "antimicrobial stewardship and prescribing behaviour",
        ["antimicrobial", "antibiotic", "prescribing", "stewardship", "acute diarrhea", "acute diarrhoea"],
    ),
    (
        "nutrition and preventive urinary care",
        ["urinary", "urolith", "struvite", "acidifying", "diet", "nutrition"],
    ),
    (
        "orthopaedic recognition and referral timing",
        ["tendon", "rupture", "orthopaedic", "achilles", "limb", "surgical option"],
    ),
    (
        "practical diagnostics and titre interpretation",
        [
            "elisa",
            "electrophoresis",
            "titer",
            "titre",
            "screening",
            "diagnostic laboratories",
            "immunoglobulin",
            "cytokine",
        ],
    ),
    (
        "oral medicine and immune dysregulation",
        ["gingivostomatitis", "stomatitis", "hypergammaglobulinemia", "oral inflammatory", "fcgs"],
    ),
    (
        "oncology, prognosis and emergency triage",
        ["oncology", "cancer", "lymphoma", "neoplasia", "survival", "prognosis", "icu", "critical care"],
    ),
    (
        "infectious disease surveillance and biosecurity",
        ["zoonotic", "import", "rabies", "brucella", "tick", "one health"],
    ),
]

STRUCTURED_LABEL_ALIASES = {
    "background": "background",
    "objective": "objective",
    "aim": "objective",
    "hypothesis/objectives": "objective",
    "study design": "design",
    "design": "design",
    "setting": "setting",
    "animals": "population",
    "animals and procedure": "population",
    "materials and methods": "methods",
    "interventions": "methods",
    "methods": "methods",
    "measurements and main results": "results",
    "results": "results",
    "conclusions and clinical relevance": "clinical_relevance",
    "conclusion": "conclusion",
    "conclusions": "conclusion",
    "conclusion and clinical relevance": "conclusion",
    "clinical relevance": "clinical_relevance",
    "clinical significance": "clinical_relevance",
    "practical relevance": "clinical_relevance",
    "clinical challenges": "background",
    "limitations": "limitations",
}

STRUCTURED_LABEL_PATTERN = re.compile(
    r"(?:(?<=^)|(?<=[.!?])|(?<=\n))\s*("
    + "|".join(re.escape(label) for label in sorted(STRUCTURED_LABEL_ALIASES, key=len, reverse=True))
    + r")\b:?\s+",
    re.IGNORECASE,
)


@dataclass
class Config:
    start_date: dt.date
    end_date: dt.date
    max_articles: int
    page_size: int = 25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a weekly dogs and cats veterinary newsletter draft."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Fetch papers and build a draft.")
    run_parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format.")
    run_parser.add_argument("--end-date", help="End date in YYYY-MM-DD format.")
    run_parser.add_argument(
        "--max-articles",
        type=int,
        default=6,
        help="Maximum number of articles to include in the newsletter.",
    )
    run_parser.add_argument(
        "--page-size",
        type=int,
        default=25,
        help="Number of records to request from Europe PMC.",
    )

    return parser.parse_args()


def resolve_dates(start_date_raw: str | None, end_date_raw: str | None) -> tuple[dt.date, dt.date]:
    today = today_in_config_timezone()
    end_date = dt.date.fromisoformat(end_date_raw) if end_date_raw else today
    start_date = dt.date.fromisoformat(start_date_raw) if start_date_raw else end_date - dt.timedelta(days=7)

    if start_date > end_date:
        raise ValueError("start date cannot be after end date")

    return start_date, end_date


def today_in_config_timezone() -> dt.date:
    try:
        return dt.datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()
    except Exception:
        return dt.date.today()


def build_query(config: Config) -> str:
    return (
        '(TITLE_ABS:"dog" OR TITLE_ABS:"dogs" OR TITLE_ABS:"canine" '
        'OR TITLE_ABS:"cat" OR TITLE_ABS:"cats" OR TITLE_ABS:"feline") '
        'AND (TITLE_ABS:"veterinary" OR TITLE_ABS:"veterinarian") '
        "AND HAS_ABSTRACT:Y "
        f"AND FIRST_PDATE:[{config.start_date.isoformat()} TO {config.end_date.isoformat()}]"
    )


def fetch_articles(config: Config) -> list[dict[str, Any]]:
    query = build_query(config)
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": str(config.page_size),
        "sort_date": "y",
    }
    url = f"{EUROPE_PMC_URL}?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.load(response)

    raw_results = payload.get("resultList", {}).get("result", [])
    articles = [normalize_article(item) for item in raw_results]
    articles = [item for item in articles if item["abstract"]]
    return rank_articles(articles)


def normalize_article(item: dict[str, Any]) -> dict[str, Any]:
    title = clean_text(item.get("title", "Untitled article"))
    abstract = clean_abstract_text(item.get("abstractText", ""))
    author_string = clean_text(item.get("authorString", ""))
    journal_info = item.get("journalInfo", {}) or {}
    journal_meta = journal_info.get("journal", {}) if isinstance(journal_info, dict) else {}
    journal = clean_text(item.get("journalTitle") or journal_meta.get("title", ""))
    publication_date = item.get("firstPublicationDate") or item.get("pubYear") or ""
    doi = clean_text(item.get("doi", ""))
    pmid = clean_text(item.get("pmid", ""))
    europe_pmc_id = clean_text(item.get("id", ""))
    source = clean_text(item.get("source", ""))

    if doi:
        article_url = f"https://doi.org/{doi}"
    elif source and europe_pmc_id:
        article_url = f"https://europepmc.org/article/{source}/{europe_pmc_id}"
    else:
        article_url = "https://europepmc.org/"

    return {
        "title": title,
        "abstract": abstract,
        "authors": author_string,
        "journal": journal,
        "publication_date": publication_date,
        "doi": doi,
        "pmid": pmid,
        "source": source,
        "article_url": article_url,
    }


def clean_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_abstract_text(value: str) -> str:
    text = clean_text(value)
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[.!?])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bconstructs-(?=perceived\b)", "constructs: ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bsocial support-and\b", "social support, and", text, flags=re.IGNORECASE)
    text = re.sub(r"\bc AD\b", "cAD", text)
    text = re.sub(r"\bp H\b", "pH", text)
    text = re.sub(r"\bFe LV\b", "FeLV", text)
    text = re.sub(r"\bIg G\b", "IgG", text)
    text = re.sub(r"\bIg M\b", "IgM", text)
    text = re.sub(r"\bBehavioral\b", "Behavioural", text)
    text = re.sub(r"\bbehavioral\b", "behavioural", text)
    return text


def rank_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for article in articles:
        title_score = keyword_score(article["title"])
        abstract_score = keyword_score(article["abstract"]) // 2
        article["score"] = title_score + abstract_score + min(len(article["abstract"]) // 250, 3)
    return sorted(articles, key=lambda item: (item["score"], item["publication_date"]), reverse=True)


def keyword_score(text: str) -> int:
    lowered = text.lower()
    score = 0
    for keyword, weight in TITLE_KEYWORDS.items():
        if keyword in lowered:
            score += weight
    return score


def sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text.strip())
    return [part.strip() for part in parts if part.strip()]


def strip_structured_label(text: str) -> str:
    labels = "|".join(
        re.escape(label) for label in sorted(STRUCTURED_LABEL_ALIASES, key=len, reverse=True)
    )
    pattern = rf"^({labels}):?\s+"
    return re.sub(pattern, "", text, flags=re.IGNORECASE).strip()


def normalize_sentence(text: str) -> str:
    cleaned = strip_structured_label(clean_text(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ;,-")
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


def truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    shortened = text[: max_length - 1].rsplit(" ", 1)[0]
    return f"{shortened}…"


def shorten_long_sentence(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text

    # Prefer a slightly overlong complete sentence over a clipped one.
    if len(text) <= max_length + 80:
        return text

    clauses = re.split(r"(?<=[,;:])\s+", text)
    kept: list[str] = []
    for clause in clauses:
        candidate = " ".join(kept + [clause]) if kept else clause
        if len(candidate) <= max_length:
            kept.append(clause)
        else:
            break

    if kept:
        shortened = " ".join(kept).rstrip(",;: ")
        if shortened and shortened[-1] not in ".!?":
            shortened += "."
        return shortened

    return truncate(text, max_length)


def limit_complete_sentences(text: str, max_length: int) -> str:
    sentences = [normalize_sentence(part) for part in sentence_split(text)]
    sentences = [sentence for sentence in sentences if sentence]
    if not sentences:
        return ""

    kept: list[str] = []
    for sentence in sentences:
        candidate = " ".join(kept + [sentence]) if kept else sentence
        if len(candidate) <= max_length:
            kept.append(sentence)
        else:
            break

    if kept:
        return " ".join(kept)

    return shorten_long_sentence(sentences[0], max_length)


def collect_sentences(*texts: str, max_sentences: int, max_chars: int) -> str:
    collected: list[str] = []
    seen: set[str] = set()

    for text in texts:
        for sentence in sentence_split(text):
            normalized = normalize_sentence(sentence)
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            candidate = " ".join(collected + [normalized]) if collected else normalized
            if collected and len(candidate) > max_chars:
                return " ".join(collected)

            if not collected and len(candidate) > max_chars:
                return shorten_long_sentence(normalized, max_chars)

            collected.append(normalized)
            seen.add(key)
            if len(collected) >= max_sentences:
                return " ".join(collected)

    return " ".join(collected)


def extract_structured_sections(abstract: str) -> dict[str, str]:
    matches = list(STRUCTURED_LABEL_PATTERN.finditer(abstract))
    if not matches:
        return {}

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        label = STRUCTURED_LABEL_ALIASES[match.group(1).lower()]
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(abstract)
        content = abstract[start:end].strip(" ;.")
        if not content:
            continue
        content = clean_section_content(label, content)
        if not content:
            continue
        if label in sections:
            sections[label] = f"{sections[label]} {content}".strip()
        else:
            sections[label] = content
    return sections


def clean_section_content(label: str, content: str) -> str:
    cleaned = content.strip(" ;.")

    low_value = {
        "and",
        "no were used",
        "no were used. materials and",
        "materials and",
    }
    if cleaned.lower() in low_value:
        return ""

    if label == "population" and cleaned.lower().startswith("no animals were used"):
        return ""

    return cleaned


def infer_study_design(article: dict[str, Any]) -> str:
    text = f"{article['title']} {article['abstract']}".lower()
    rules = [
        ("scoping review", "This is a scoping review synthesizing the available literature."),
        ("systematic review", "This is a systematic review of the available evidence."),
        ("review", "This paper is a narrative review rather than a primary interventional study."),
        ("prospective", "The abstract suggests a prospective design, which usually strengthens temporal interpretation."),
        ("retrospective", "The abstract suggests a retrospective design, so the findings should be interpreted with observational caveats."),
        ("case report", "This appears to be a case report and is most useful for pattern recognition rather than broad generalization."),
        ("case series", "This appears to be a case series, which is clinically informative but hypothesis-generating."),
        ("cohort", "The abstract indicates a cohort-style observational design."),
        ("randomized", "The study appears to use a randomized design, which may strengthen inference about intervention effects."),
    ]

    for needle, sentence in rules:
        if needle in text:
            return sentence

    return (
        "The abstract does not expose a strongly labelled methods section, so the full paper should be checked "
        "before quoting operational details in clinical discussion."
    )


def fallback_findings(abstract: str) -> str:
    sentences = [normalize_sentence(part) for part in sentence_split(abstract)]
    sentences = [sentence for sentence in sentences if sentence]
    if not sentences:
        return "The abstract was available, but the main findings could not be extracted cleanly."
    preferred = sentences[1:4] if len(sentences) > 2 else sentences[:2]
    return limit_complete_sentences(" ".join(preferred), 700)


def compose_technical_summary(article: dict[str, Any], sections: dict[str, str]) -> str:
    objective = collect_sentences(
        sections.get("background", ""),
        sections.get("objective", ""),
        max_sentences=1,
        max_chars=240,
    )
    design = collect_sentences(
        sections.get("design", ""),
        sections.get("methods", ""),
        sections.get("population", ""),
        max_sentences=2,
        max_chars=260,
    )
    results = collect_sentences(sections.get("results", ""), max_sentences=1, max_chars=240)
    conclusion = collect_sentences(
        sections.get("conclusion", ""),
        sections.get("clinical_relevance", ""),
        max_sentences=1,
        max_chars=220,
    )

    combined = " ".join(part for part in [objective, design, results, conclusion] if part)
    if combined:
        return limit_complete_sentences(combined, 760)

    return collect_sentences(article["abstract"], max_sentences=4, max_chars=760)

def compose_study_design(article: dict[str, Any], sections: dict[str, str]) -> str:
    structured = collect_sentences(
        sections.get("design", ""),
        sections.get("setting", ""),
        sections.get("population", ""),
        sections.get("methods", ""),
        max_sentences=4,
        max_chars=640,
    )
    return structured or infer_study_design(article)


def compose_key_findings(article: dict[str, Any], sections: dict[str, str]) -> str:
    findings = collect_sentences(
        sections.get("results", ""),
        sections.get("conclusion", ""),
        max_sentences=3,
        max_chars=700,
    )
    return findings or fallback_findings(article["abstract"])

def infer_practical_context(article: dict[str, Any]) -> str:
    text = f"{article['title']} {article['abstract']}".lower()
    rules = [
        (
            [
                "parvovirus",
                "cpv",
                "antibody titre",
                "antibody titers",
                "titre",
                "titer",
                "hemagglutination inhibition",
                "dot-blot elisa",
                "blood-donor",
                "blood donor",
                "plasma selection",
                "donor screening",
            ],
            "For irst-opinion clinicians, this supports more confident use of titre testing, clearer interpretation of vaccination status, and better coordination with referral centres or blood banks when donor screening or plasma selection matters.",
        ),
        (
            ["zoonotic", "import", "one health", "brucella", "rabies"],
            "For first-opinion vets, the practical consequence is more deliberate travel and import-history taking, earlier infectious-disease screening, and better staff and owner biosecurity communication.",
        ),
        (
            ["antimicrobial", "antibiotic", "resistance", "culture and susceptibility", "susceptibility testing"],
            "For first-opinion work, this can sharpen empirical antimicrobial choices, justify earlier culture and susceptibility testing, and strengthen antimicrobial stewardship discussions with colleagues and clients.",
        ),
        (
            ["immunotherapy", "atopic dermatitis", "atopic skin", "asit", "owner persistence"],
            "For first-opinion clinicians, the practical lesson is that long-term success depends as much on expectation-setting, cost discussions, and owner confidence as it does on choosing the right therapy at the outset.",
        ),
        (
            ["lymphoma", "oncology", "cancer", "neoplasia"],
            "In day-to-day practice, the key value is earlier suspicion, better staging and referral conversations, and more accurate communication about treatment intensity, prognosis, and likely owner decision points.",
        ),
        (
            ["urinary", "urolith", "struvite", "acidifying", "acidifier"],
            "For first-opinion clinicians, the main value is more precise nutritional counselling, better prevention planning in recurrent lower urinary tract disease, and more confident discussion of when diet may be sufficient and when further investigation is warranted.",
        ),
        (
            ["prevalence", "risk factor", "survival", "prognosis"],
            "At general-practice level, the paper helps with risk stratification, prognosis framing, and more realistic owner counselling before referral, intensive care, or major cost decisions.",
        ),
        (
            ["emergency", "hyperkalemia", "electrocardiogram", "arrhythmia", "acute kidney injury", "urethral obstruction"],
            "For first-opinion clinicians, the immediate application is tighter triage, earlier electrolyte or ECG assessment, and faster escalation when destabilization could become life-threatening.",
        ),
        (
            ["antiparasitic", "isoxazoline", "pyrethroid", "neurotoxicity", "pfas"],
            "For first-opinion clinicians, the message is to be more alert to adverse-effect history after ectoparasiticide exposure, to document signalment and timing carefully, and to escalate sooner when neurological signs follow recently administered products.",
        ),
        (
            ["gingivostomatitis", "stomatitis", "oromucosal", "hyperglobulinemia"],
            "In first-opinion practice, this supports earlier recognition that severe oral inflammatory disease may reflect wider immune dysregulation, which in turn helps justify baseline laboratory work, analgesic planning, and earlier referral for advanced dental or medical management.",
        ),
        (
            ["tendon", "rupture", "orthopaedic", "achilles"],
            "In first-opinion practice, the main implication is earlier recognition of injuries that are unlikely to do well with conservative management alone, together with quicker stabilisation and surgical referral discussions.",
        ),
        (
            ["diagnostic", "dermoscopy", "ultrasound", "ct", "imaging"],
            "In first-opinion practice, this is most useful for improving diagnostic sequencing, supporting referral-level investigations sooner, and explaining to owners why advanced imaging or visualisation may materially change management.",
        ),
        (
            ["review", "guideline"],
            "For first-opinion teams, this is best translated into protocol refinement, CPD teaching, and more standardised decisions across the practice rather than isolated case-by-case improvisation.",
        ),
        (
            ["seizure", "neurolog", "epilep"],
            "In first-opinion settings, the findings can guide baseline work-up, clarify referral thresholds, and improve owner conversations about recurrence risk and long-term disease control.",
        ),
        (
            ["nutrition", "diet", "food"],
            "For first-opinion practice, the main benefit is better nutritional counselling, clearer conversations about formulation risk or benefit, and more defensible recommendations to owners managing chronic disease.",
        ),
    ]

    for needles, sentence in rules:
        if any(needle in text for needle in needles):
            return sentence

    return (
        "For first-opinion clinicians, the practical value lies in better case selection, sharper owner communication, "
        "and more confident decisions about when additional diagnostics, monitoring, or referral are likely to alter outcome."
    )


def compose_first_opinion_relevance(article: dict[str, Any], sections: dict[str, str]) -> str:
    evidence = collect_sentences(
        sections.get("conclusion", ""),
        sections.get("clinical_relevance", ""),
        max_sentences=2,
        max_chars=320,
    )
    practical = infer_practical_context(article)
    if evidence:
        return limit_complete_sentences(f"{evidence} {practical}", 700)
    return practical


def build_article_analysis(article: dict[str, Any]) -> dict[str, Any]:
    sections = extract_structured_sections(article["abstract"])
    return {
        "sections": sections,
        "technical_summary": compose_technical_summary(article, sections),
        "study_design": compose_study_design(article, sections),
        "key_findings": compose_key_findings(article, sections),
        "first_opinion_relevance": compose_first_opinion_relevance(article, sections),
    }


def enrich_article(article: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(article)
    enriched["analysis"] = build_article_analysis(article)
    return enriched


def build_issue_slug(end_date: dt.date) -> str:
    return f"issue-{end_date.isoformat()}"


def format_website_label(url: str) -> str:
    label = re.sub(r"^https?://", "", url).rstrip("/")
    return label or url


def format_display_date(value: str) -> str:
    if not value:
        return "Unknown date"
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        return value
    return parsed.strftime("%d/%m/%Y")


def relative_to_workspace(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def join_phrases(phrases: list[str]) -> str:
    if not phrases:
        return ""
    if len(phrases) == 1:
        return phrases[0]
    if len(phrases) == 2:
        return f"{phrases[0]} and {phrases[1]}"
    return f"{', '.join(phrases[:-1])}, and {phrases[-1]}"


def infer_issue_themes(selected_articles: list[dict[str, Any]]) -> list[str]:
    scored: list[tuple[int, int, str]] = []

    for label, keywords in ISSUE_THEMES:
        article_hits = 0
        keyword_hits = 0
        for item in selected_articles:
            text = f"{item['title']} {item['abstract']}".lower()
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches:
                article_hits += 1
                keyword_hits += matches
        if article_hits:
            scored.append((article_hits, keyword_hits, label))

    scored.sort(reverse=True)
    return [label for _, _, label in scored[:3]]


def infer_editorial_close(themes: list[str]) -> str:
    theme_text = " ".join(themes).lower()

    if any(
        needle in theme_text
        for needle in ["diagnostics", "titre", "prescribing", "urinary care", "adherence"]
    ):
        return (
            "Several of these papers are immediately transferable to first-opinion work, particularly when the practical question is whether to test, treat, monitor, or refer."
        )

    if any(
        needle in theme_text
        for needle in ["oncology", "triage", "emergency", "referral timing", "orthopaedic"]
    ):
        return (
            "As a set, they sharpen judgement at the points where escalation, prognosis, and owner counselling matter most."
        )

    return (
        "Taken together, they reward the reader who wants not just new information, but sharper clinical judgement around triage, diagnostics, referral timing, and owner communication."
    )


def compose_editorial_note(selected_articles: list[dict[str, Any]]) -> str:
    themes = infer_issue_themes(selected_articles)
    if themes:
        lead = f"This week's issue brings together papers on {join_phrases(themes)}."
    else:
        lead = "This week's issue ranges across several areas of contemporary small-animal practice."

    close = infer_editorial_close(themes)
    return f"{lead} {close}"


def render_signature_markdown() -> list[str]:
    return [
        "## Prepared by",
        "",
        DEFAULT_CONTACT_NAME,
        DEFAULT_CONTACT_CREDENTIALS,
        DEFAULT_CONTACT_COMPANY,
        DEFAULT_CONTACT_LOCATION,
        f"Phone & WhatsApp: {DEFAULT_CONTACT_PHONE}",
        f"Website: [{format_website_label(DEFAULT_CONTACT_WEBSITE)}]({DEFAULT_CONTACT_WEBSITE})",
        "",
    ]


def render_review_summary(
    selected_articles: list[dict[str, Any]],
    config: Config,
    json_path: Path,
    markdown_path: Path,
    html_path: Path,
) -> str:
    issue_slug = build_issue_slug(config.end_date)
    parts = [
        f"# Issue Review Summary | {format_display_date(config.end_date.isoformat())}",
        "",
        f"- Issue slug: `{issue_slug}`",
        f"- Timezone: `{DEFAULT_TIMEZONE}`",
        f"- Source window: {format_display_date(config.start_date.isoformat())} to {format_display_date(config.end_date.isoformat())}",
        f"- Selected articles: {len(selected_articles)}",
        f"- JSON data: `{relative_to_workspace(json_path)}`",
        f"- Markdown draft: `{relative_to_workspace(markdown_path)}`",
        f"- HTML draft: `{relative_to_workspace(html_path)}`",
        "",
        "## Top article titles",
        "",
    ]

    for index, article in enumerate(selected_articles, start=1):
        parts.append(f"{index}. {article['title']}")

    parts.extend(
        [
            "",
            "## Monday review checklist",
            "",
            "- Review the issue title and date format.",
            "- Review article selection and editorial ordering.",
            "- Check the opening editorial note, logo, and closing signature.",
            "- Confirm British English tone and first-opinion relevance.",
            "- Paste the final HTML into Mailchimp, send test emails, and only then send to the audience.",
            "",
        ]
    )

    return "\n".join(parts).strip() + "\n"


def render_markdown(selected_articles: list[dict[str, Any]], config: Config) -> str:
    issue_title = f"{DEFAULT_BRAND_NAME} | Week ending {format_display_date(config.end_date.isoformat())}"
    intro = compose_editorial_note(selected_articles)

    parts: list[str] = []
    if DEFAULT_LOGO_URL:
        parts.extend(
            [
                f'<p><img src="{escape_attr(DEFAULT_LOGO_URL)}" alt="{escape_attr(DEFAULT_LOGO_ALT)}" width="190" /></p>',
                "",
            ]
        )

    parts.extend(
        [
            f"# {issue_title}",
            "",
            "## From the editor",
            "",
            intro,
            "",
            "## In this week's reading",
            "",
        ]
    )

    for index, article in enumerate(selected_articles, start=1):
        analysis = article["analysis"]
        parts.extend(
            [
                f"### {index}. {article['title']}",
                "",
                f"- Published: {format_display_date(article['publication_date'])}",
                f"- Journal: {article['journal'] or 'Unknown journal'}",
                f"- Authors: {article['authors'] or 'Unknown authors'}",
                f"- Link: {article['article_url']}",
                "",
                f"**Editorial summary:** {analysis['technical_summary']}",
                "",
                f"**How the paper was built:** {analysis['study_design']}",
                "",
                f"**What stands out:** {analysis['key_findings']}",
                "",
                f"**Why it matters in first opinion:** {analysis['first_opinion_relevance']}",
                "",
            ]
        )

    parts.extend(
        [
            "## Closing note",
            "",
            "This issue is written in British English and is intended as an editorial digest rather than a substitute for the full paper. "
            "Where an article's interpretation turns on methodology, case selection, or statistical nuance, the source paper remains the final authority.",
            "",
        ]
    )

    parts.extend(render_signature_markdown())

    return "\n".join(parts).strip() + "\n"


def render_contact_html() -> str:
    lines = [
        f'<p class="signature-name">{escape_html(DEFAULT_CONTACT_NAME)}</p>',
        f'<p>{escape_html(DEFAULT_CONTACT_CREDENTIALS)}</p>',
        f'<p>{escape_html(DEFAULT_CONTACT_COMPANY)} | {escape_html(DEFAULT_CONTACT_LOCATION)}</p>',
        f'<p>Phone &amp; WhatsApp: {escape_html(DEFAULT_CONTACT_PHONE)}</p>',
        f'<p><a href="{escape_attr(DEFAULT_CONTACT_WEBSITE)}">{escape_html(format_website_label(DEFAULT_CONTACT_WEBSITE))}</a></p>',
    ]
    return "".join(lines)


def render_html(selected_articles: list[dict[str, Any]], config: Config) -> str:
    editorial_note = compose_editorial_note(selected_articles)
    card_html = []
    for article in selected_articles:
        analysis = article["analysis"]
        card_html.append(
            f"""
            <section class="card">
              <h2>{escape_html(article["title"])}</h2>
              <p class="meta"><strong>Published:</strong> {escape_html(format_display_date(article["publication_date"]))} | <strong>Journal:</strong> {escape_html(article["journal"] or "Unknown journal")}</p>
              <p class="meta"><strong>Authors:</strong> {escape_html(article["authors"] or "Unknown authors")}</p>
              <p><strong>Editorial summary:</strong> {escape_html(analysis["technical_summary"])}</p>
              <p><strong>How the paper was built:</strong> {escape_html(analysis["study_design"])}</p>
              <p><strong>What stands out:</strong> {escape_html(analysis["key_findings"])}</p>
              <p><strong>Why it matters in first opinion:</strong> {escape_html(analysis["first_opinion_relevance"])}</p>
              <p><a class="article-link" href="{escape_attr(article["article_url"])}">Read the paper</a></p>
            </section>
            """.strip()
        )

    issue_title = f"{DEFAULT_BRAND_NAME} | Week ending {format_display_date(config.end_date.isoformat())}"
    logo_html = (
        f'<img class="logo" src="{escape_attr(DEFAULT_LOGO_URL)}" alt="{escape_attr(DEFAULT_LOGO_ALT)}" />'
        if DEFAULT_LOGO_URL
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en-GB">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape_html(issue_title)}</title>
    <style>
      body {{
        margin: 0;
        padding: 0;
        background: #f3f1ea;
        color: #16211d;
        font-family: Georgia, "Times New Roman", serif;
      }}
      .wrapper {{
        max-width: 760px;
        margin: 0 auto;
        padding: 30px 18px 48px;
      }}
      .hero {{
        background: linear-gradient(140deg, #e9efe8 0%, #fbfaf6 42%, #f5eee4 100%);
        border: 1px solid #d7ddcf;
        color: #16312a;
        padding: 28px;
        border-radius: 22px;
        box-shadow: 0 10px 30px rgba(22, 49, 42, 0.08);
      }}
      .hero-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        margin-bottom: 18px;
        flex-wrap: wrap;
      }}
      .logo {{
        max-width: 180px;
        height: auto;
        display: block;
      }}
      .issue-pill {{
        display: inline-block;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(22, 49, 42, 0.08);
        font-size: 13px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }}
      .hero h1 {{
        margin: 0 0 10px;
        font-size: 34px;
        line-height: 1.08;
      }}
      .hero p {{
        margin: 0 0 12px;
        font-size: 17px;
        line-height: 1.65;
      }}
      .editor-note {{
        margin-top: 18px;
        padding: 18px 20px;
        border-radius: 16px;
        background: rgba(255, 253, 248, 0.72);
        border: 1px solid rgba(22, 49, 42, 0.08);
      }}
      .editor-note h2 {{
        margin: 0 0 10px;
        font-size: 18px;
        line-height: 1.2;
      }}
      .editor-note p {{
        margin: 0;
        font-size: 16px;
      }}
      .signature {{
        margin-top: 26px;
        padding: 22px 24px;
        border: 1px solid #d7ddcf;
        border-radius: 18px;
        background: #fffdf8;
        color: #26443c;
      }}
      .signature p {{
        margin: 0 0 6px;
        font-size: 15px;
      }}
      .signature-name {{
        font-size: 17px;
        font-weight: 700;
      }}
      .button {{
        display: inline-block;
        margin-top: 12px;
        padding: 11px 16px;
        border-radius: 999px;
        background: #1d6050;
        color: #fffdf8;
        text-decoration: none;
        font-size: 14px;
      }}
      .card {{
        background: #fffdf8;
        margin-top: 18px;
        padding: 24px;
        border-radius: 18px;
        border: 1px solid #e4ddd1;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.04);
      }}
      .card h2 {{
        margin: 0 0 10px;
        font-size: 26px;
        line-height: 1.24;
      }}
      .card p {{
        margin: 0 0 12px;
        font-size: 16px;
        line-height: 1.7;
      }}
      .meta {{
        color: #5d615c;
        font-size: 14px;
      }}
      .article-link {{
        color: #0f5d4b;
        font-weight: 700;
      }}
      .footer {{
        margin-top: 26px;
        color: #5d615c;
        font-size: 14px;
        line-height: 1.6;
      }}
      @media (max-width: 640px) {{
        .hero h1 {{
          font-size: 28px;
        }}
        .card h2 {{
          font-size: 22px;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="wrapper">
      <section class="hero">
        <div class="hero-top">
          {logo_html}
          <span class="issue-pill">Week Ending {escape_html(format_display_date(config.end_date.isoformat()))}</span>
        </div>
        <h1>{escape_html(issue_title)}</h1>
        <div class="editor-note">
          <h2>From the editor</h2>
          <p>{escape_html(editorial_note)}</p>
        </div>
        <a class="button" href="{escape_attr(DEFAULT_CONTACT_WEBSITE)}">Visit Mobile Vet Referral</a>
      </section>
      {''.join(card_html)}
      <section class="signature">
        {render_contact_html()}
      </section>
      <p class="footer">Prepared in British English as an editorial digest for informed clinical reading. Where interpretation rests on methodology, case selection, or statistical nuance, the full paper remains the final authority.</p>
    </div>
  </body>
</html>
"""


def escape_html(value: str) -> str:
    return html.escape(value or "", quote=False)


def escape_attr(value: str) -> str:
    return html.escape(value or "", quote=True)


def write_issue_files(articles: list[dict[str, Any]], config: Config) -> dict[str, Path]:
    issue_slug = build_issue_slug(config.end_date)
    data_dir = DATA_DIR / issue_slug
    output_dir = OUTPUT_DIR / issue_slug
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_articles = [enrich_article(item) for item in articles[: config.max_articles]]

    json_path = data_dir / "articles.json"
    markdown_path = output_dir / "newsletter.md"
    html_path = output_dir / "newsletter.html"
    summary_path = output_dir / "review-summary.md"

    json_path.write_text(json.dumps(selected_articles, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(selected_articles, config), encoding="utf-8")
    html_path.write_text(render_html(selected_articles, config), encoding="utf-8")
    summary_path.write_text(
        render_review_summary(selected_articles, config, json_path, markdown_path, html_path),
        encoding="utf-8",
    )

    return {
        "json": json_path,
        "markdown": markdown_path,
        "html": html_path,
        "summary": summary_path,
    }


def run(config: Config) -> int:
    articles = fetch_articles(config)
    if not articles:
        print("No matching articles were found for this period.", file=sys.stderr)
        return 1

    paths = write_issue_files(articles, config)
    print(f"Fetched {len(articles)} candidate articles.")
    print(f"Saved JSON: {paths['json']}")
    print(f"Saved Markdown draft: {paths['markdown']}")
    print(f"Saved HTML draft: {paths['html']}")
    print(f"Saved review summary: {paths['summary']}")
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "run":
        start_date, end_date = resolve_dates(args.start_date, args.end_date)
        config = Config(
            start_date=start_date,
            end_date=end_date,
            max_articles=args.max_articles,
            page_size=args.page_size,
        )
        return run(config)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
