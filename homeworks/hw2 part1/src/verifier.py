# src/verifier.py
from difflib import SequenceMatcher
from src.schemas import Discrepancy, VerificationResult, CVProfile, SocialCandidate

def sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def norm_company(s: str) -> str:
    if not s:
        return ""
    s = s.lower().replace(",", " ").replace(".", " ")
    aliases = {
        "bytedance": "bytedance",
        "byte dance": "bytedance",
        "meta platforms": "meta",
        "facebook": "meta",
    }
    for k, v in aliases.items():
        if k in s:
            return v
    return " ".join(s.split())

def compare_basic(cv: CVProfile, linkedin_profile: dict | None, facebook_profile: dict | None):
    discrepancies = []

    # 姓名
    li_name = (linkedin_profile or {}).get("name") or (linkedin_profile or {}).get("full_name")
    if li_name:
        s = sim(cv.full_name, li_name)
        if s >= 0.90:
            discrepancies.append(Discrepancy(
                field="identity.name", severity="low", status="match",
                cv_value=cv.full_name, social_value=li_name, evidence="LinkedIn profile name matched"
            ))
        elif s >= 0.70:
            discrepancies.append(Discrepancy(
                field="identity.name", severity="medium", status="partial_match",
                cv_value=cv.full_name, social_value=li_name, evidence="LinkedIn profile name similar"
            ))
        else:
            discrepancies.append(Discrepancy(
                field="identity.name", severity="high", status="mismatch",
                cv_value=cv.full_name, social_value=li_name, evidence="LinkedIn profile name differs"
            ))
    else:
        discrepancies.append(Discrepancy(
            field="identity.name", severity="medium", status="missing",
            cv_value=cv.full_name, social_value=None, evidence="No LinkedIn name available"
        ))

    # 工作经历（以CV中的前2条为例）
    li_exps = (linkedin_profile or {}).get("experiences", []) or (linkedin_profile or {}).get("experience", [])
    li_exps_text = " | ".join([
        f"{x.get('company','')} {x.get('title','')} {x.get('start_date','')}-{x.get('end_date','')}"
        for x in li_exps[:10] if isinstance(x, dict)
    ]).lower()

    for idx, exp in enumerate(cv.experiences[:3]):
        company = norm_company(exp.company)
        title = (exp.title or "").lower()
        has_company = company and (company in norm_company(li_exps_text))
        has_title = title and (title in li_exps_text)

        if has_company and has_title:
            status, sev = "match", "low"
        elif has_company or has_title:
            status, sev = "partial_match", "medium"
        else:
            status, sev = "mismatch", "high"

        discrepancies.append(Discrepancy(
            field=f"experience[{idx}]",
            severity=sev,
            status=status,
            cv_value=f"{exp.company} / {exp.title} / {exp.start_date}-{exp.end_date}",
            social_value=li_exps_text[:500] if li_exps_text else None,
            evidence="Compared against LinkedIn experiences"
        ))

    # 教育（学校 + 毕业年份）
    li_edu = (linkedin_profile or {}).get("education", []) or []
    li_edu_text = " | ".join([
        f"{x.get('school','')} {x.get('degree','')} {x.get('field_of_study','')} {x.get('end_year','')}"
        for x in li_edu if isinstance(x, dict)
    ]).lower()

    for idx, edu in enumerate(cv.education[:2]):
        school_ok = (edu.school or "").lower() in li_edu_text if edu.school else False
        year_ok = (edu.graduation_year or "").lower() in li_edu_text if edu.graduation_year else False

        if school_ok and (year_ok or not edu.graduation_year):
            status, sev = "match", "low"
        elif school_ok or year_ok:
            status, sev = "partial_match", "medium"
        else:
            status, sev = "mismatch", "high"

        discrepancies.append(Discrepancy(
            field=f"education[{idx}]",
            severity=sev,
            status=status,
            cv_value=f"{edu.school} / {edu.degree} / {edu.field_of_study} / {edu.graduation_year}",
            social_value=li_edu_text[:500] if li_edu_text else None,
            evidence="Compared against LinkedIn education"
        ))

    return discrepancies