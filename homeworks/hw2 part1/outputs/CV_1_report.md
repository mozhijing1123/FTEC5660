# CV Verification Report - CV_1.pdf

**Person:** John Smith
**Overall Status:** verified
**Confidence:** 0.12

## Selected Profiles
- LinkedIn: {'platform': 'linkedin', 'candidate_id': '9', 'display_name': 'John Smith', 'profile_url': 'https://linkedin.com/in/9', 'score': 0.96, 'reason': "Strong match: same name; current/most recent role 'Engineer' at ByteDance from 2020, matching CV experience; location Singapore matches CV; education is BSc in Marketing at McGill University with graduation year 2009, exactly matching CV; skills include Content Creation, SEO, and Social Media, aligning closely with CV skills."}
- Facebook: {'platform': 'facebook', 'candidate_id': '213', 'display_name': 'John Smith', 'profile_url': 'https://facebook.com/213', 'score': 0.55, 'reason': 'Moderate match: name John Smith, based in Singapore with hometown Hong Kong, which fits CV location string mentioning Singapore and Kowloon (Hong Kong). However, job is Scientist at Traveloka, not Engineer at ByteDance, and there is no explicit McGill/Marketing signal; kept as a plausible but uncertain candidate based mainly on name and SG/HK linkage.'}

## Summary
The LinkedIn candidate with ID 9 is an extremely strong match to the CV: same name, role as Engineer at ByteDance starting in 2020, location in Singapore, and a BSc in Marketing from McGill University graduating in 2009, along with overlapping skills in Content Creation, SEO, and Social Media. These alignments cover all core CV elements: identity, employment, education, location, and skills. Other LinkedIn and Facebook profiles either conflict on education, employer, or industry and are clearly weaker matches, suggesting they belong to different individuals sharing a common name. There are no detected contradictions between the CV and the best-matching social profile. Based on this, the CV details appear accurate and are well supported by the online profile evidence.

## Discrepancies
- **identity.name** | missing | severity=medium
  - CV: John Smith
  - Social: None
  - Evidence: No LinkedIn name available
- **experience[0]** | mismatch | severity=high
  - CV: ByteDance / Engineer / 2020-Present
  - Social: None
  - Evidence: Compared against LinkedIn experiences
- **education[0]** | mismatch | severity=high
  - CV: McGill University / Bachelor of Science (BSc) / Marketing / 2009
  - Social: None
  - Evidence: Compared against LinkedIn education