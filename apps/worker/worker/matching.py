from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.models import Job, JobMatch, Resume, User
from job_focus_shared import MatchStrength, WorkMode

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
SENIORITY_ORDER = {
    "intern": 1,
    "entry": 2,
    "junior": 2,
    "associate": 3,
    "mid": 4,
    "manager": 4,
    "senior": 5,
    "lead": 6,
    "staff": 7,
    "principal": 8,
    "director": 9,
}
COMPONENT_MAX_SCORES = {
    "title": 25,
    "location": 15,
    "seniority": 10,
    "skills": 20,
    "authorization": 10,
    "salary": 10,
    "preferences": 10,
}


@dataclass(frozen=True, slots=True)
class MatchResult:
    score: int
    strength: MatchStrength
    rationale: str
    why_matched: dict[str, Any]


def calculate_match(user: User, resume: Resume | None, job: Job) -> MatchResult:
    profile = user.profile
    preferences = user.user_preferences

    title_component = _score_title(profile.target_roles if profile is not None else [], job)
    location_component = _score_location(profile.location if profile is not None else None, preferences, job)
    seniority_component = _score_seniority(profile, job)
    skills_component = _score_skills(resume, job)
    authorization_component = _score_authorization(profile, job)
    salary_component = _score_salary(preferences, job)
    preferences_component = _score_preferences(preferences, job)

    components = {
        "title": title_component,
        "location": location_component,
        "seniority": seniority_component,
        "skills": skills_component,
        "authorization": authorization_component,
        "salary": salary_component,
        "preferences": preferences_component,
    }
    total_score = sum(int(component["score"]) for component in components.values())
    strength = (
        MatchStrength.HIGH
        if total_score >= 85
        else MatchStrength.MEDIUM
        if total_score >= 70
        else MatchStrength.LOW
    )

    strengths = [
        component["summary"]
        for component in components.values()
        if int(component["score"]) >= max(1, int(component["maxScore"]) // 2)
    ]
    concerns = [
        component["summary"]
        for component in components.values()
        if int(component["score"]) == 0 and component["summary"]
    ]
    rationale = "; ".join(strengths[:3] or concerns[:3] or ["baseline compatibility only"])

    why_matched = {
        "totalScore": total_score,
        "components": components,
        "strengths": strengths,
        "concerns": concerns,
    }
    return MatchResult(
        score=total_score,
        strength=strength,
        rationale=rationale,
        why_matched=why_matched,
    )


def populate_job_match(job_match: JobMatch, result: MatchResult) -> None:
    job_match.match_score = result.score
    job_match.strength = result.strength
    job_match.rationale = result.rationale
    job_match.why_matched = result.why_matched


def _score_title(target_roles: list[str], job: Job) -> dict[str, Any]:
    title_lower = job.title.lower()
    title_tokens = _tokenize(job.title)
    role_matches = [role for role in target_roles if role.lower() in title_lower]
    overlap_terms = sorted(
        {
            token
            for role in target_roles
            for token in _tokenize(role)
            if token in title_tokens
        }
    )

    if role_matches:
        score = COMPONENT_MAX_SCORES["title"]
        summary = f"Title matches target role(s): {', '.join(role_matches)}."
    elif overlap_terms:
        score = min(COMPONENT_MAX_SCORES["title"], len(overlap_terms) * 5)
        summary = f"Title shares keywords with target roles: {', '.join(overlap_terms)}."
    else:
        score = 0
        summary = "Title does not align closely with target roles."

    return {
        "score": score,
        "maxScore": COMPONENT_MAX_SCORES["title"],
        "matchedRoles": role_matches,
        "overlapTerms": overlap_terms,
        "jobTitle": job.title,
        "summary": summary,
    }


def _score_location(profile_location: str | None, preferences: Any, job: Job) -> dict[str, Any]:
    preferred_work_modes = _lower_list(getattr(preferences, "preferred_work_modes", []))
    job_location_lower = job.location.lower()

    matched_locations = [
        location
        for location in getattr(preferences, "preferred_locations", [])
        if location.lower() in job_location_lower or job_location_lower in location.lower()
    ]
    profile_location_match = bool(profile_location and profile_location.lower() in job_location_lower)
    remote_preference = job.work_mode == WorkMode.REMOTE and "remote" in preferred_work_modes

    if remote_preference:
        score = COMPONENT_MAX_SCORES["location"]
        summary = "Remote location aligns with preferred work mode."
    elif matched_locations:
        score = 13
        summary = f"Job location matches preferred location(s): {', '.join(matched_locations)}."
    elif profile_location_match:
        score = 9
        summary = f"Job location aligns with profile location {profile_location}."
    else:
        score = 0
        summary = "Job location is outside stated location preferences."

    return {
        "score": score,
        "maxScore": COMPONENT_MAX_SCORES["location"],
        "jobLocation": job.location,
        "jobWorkMode": job.work_mode.value,
        "matchedPreferredLocations": matched_locations,
        "preferredWorkModes": list(getattr(preferences, "preferred_work_modes", [])) if preferences else [],
        "profileLocation": profile_location,
        "summary": summary,
    }


def _score_seniority(profile: Any, job: Job) -> dict[str, Any]:
    profile_seniority = _normalize_seniority(getattr(profile, "seniority_level", None))
    job_seniority = _normalize_seniority(job.seniority_level)
    profile_years = int(getattr(profile, "years_experience", 0) or 0)

    if job_seniority is None and profile_seniority is None:
        score = 5 if profile_years >= 3 else 0
        summary = "Limited seniority data, using years of experience as a fallback."
    elif job_seniority is None:
        score = 6
        summary = "Profile seniority is available even though the job seniority is unspecified."
    elif profile_seniority is None:
        score = 0
        summary = "Job seniority is specified but profile seniority is missing."
    else:
        profile_rank = SENIORITY_ORDER.get(profile_seniority, 0)
        job_rank = SENIORITY_ORDER.get(job_seniority, 0)
        difference = abs(profile_rank - job_rank)
        if difference == 0:
            score = COMPONENT_MAX_SCORES["seniority"]
        elif difference == 1:
            score = 8
        elif difference == 2:
            score = 5
        else:
            score = 0
        summary = f"Profile seniority {profile_seniority} compared with job seniority {job_seniority}."

    return {
        "score": score,
        "maxScore": COMPONENT_MAX_SCORES["seniority"],
        "profileSeniority": profile_seniority,
        "jobSeniority": job_seniority,
        "yearsExperience": profile_years,
        "summary": summary,
    }


def _score_skills(resume: Resume | None, job: Job) -> dict[str, Any]:
    if resume is None:
        return {
            "score": 0,
            "maxScore": COMPONENT_MAX_SCORES["skills"],
            "matchedSkills": [],
            "resumeSkills": [],
            "summary": "No resume is available for skills matching.",
        }

    searchable_text = f"{job.title} {job.description}".lower()
    matched_skills = [
        skill
        for skill in resume.skills
        if skill and skill.lower() in searchable_text
    ]
    score = min(COMPONENT_MAX_SCORES["skills"], len(matched_skills) * 4)
    summary = (
        f"Matched resume skills: {', '.join(matched_skills)}."
        if matched_skills
        else "No resume skills overlap was found in the job title or description."
    )
    return {
        "score": score,
        "maxScore": COMPONENT_MAX_SCORES["skills"],
        "matchedSkills": matched_skills,
        "resumeSkills": list(resume.skills),
        "summary": summary,
    }


def _score_authorization(profile: Any, job: Job) -> dict[str, Any]:
    authorization_regions = list(getattr(profile, "authorization_regions", [])) if profile else []
    requirement = job.authorization_requirement or ""
    requirement_lower = requirement.lower()

    if not requirement_lower:
        score = 6 if authorization_regions else 0
        summary = (
            "Authorization regions are available even though the job requirement is unspecified."
            if authorization_regions
            else "Authorization data is missing."
        )
    elif "us" in requirement_lower or "united states" in requirement_lower:
        if any(region.lower() in {"us", "usa", "united states"} for region in authorization_regions):
            score = COMPONENT_MAX_SCORES["authorization"]
            summary = "Profile includes United States work authorization."
        else:
            score = 0
            summary = "Job requires United States work authorization, but the profile does not confirm it."
    elif authorization_regions:
        score = 8
        summary = "Profile includes authorization regions relevant to the job."
    else:
        score = 0
        summary = "Job lists an authorization requirement that is not covered by the profile."

    return {
        "score": score,
        "maxScore": COMPONENT_MAX_SCORES["authorization"],
        "jobRequirement": job.authorization_requirement,
        "authorizationRegions": authorization_regions,
        "summary": summary,
    }


def _score_salary(preferences: Any, job: Job) -> dict[str, Any]:
    desired_min = getattr(preferences, "desired_salary_min", None) if preferences else None
    desired_max = getattr(preferences, "desired_salary_max", None) if preferences else None

    if desired_min is None and desired_max is None:
        score = 5 if job.salary_max > 0 else 0
        summary = "Salary preferences are not set, so the score stays neutral."
    elif job.salary_max == 0 and job.salary_min == 0:
        score = 0
        summary = "Job salary information is missing."
    else:
        lower_bound_ok = desired_min is None or job.salary_max >= desired_min
        upper_bound_ok = desired_max is None or job.salary_min <= desired_max
        if lower_bound_ok and upper_bound_ok:
            score = COMPONENT_MAX_SCORES["salary"]
            summary = "Job salary range overlaps the preferred salary range."
        elif desired_min is not None and job.salary_max >= int(desired_min * 0.9):
            score = 5
            summary = "Job salary is slightly below the preferred range."
        else:
            score = 0
            summary = "Job salary range does not meet the preferred range."

    return {
        "score": score,
        "maxScore": COMPONENT_MAX_SCORES["salary"],
        "jobSalaryMin": job.salary_min,
        "jobSalaryMax": job.salary_max,
        "desiredSalaryMin": desired_min,
        "desiredSalaryMax": desired_max,
        "summary": summary,
    }


def _score_preferences(preferences: Any, job: Job) -> dict[str, Any]:
    preferred_work_modes = _lower_list(getattr(preferences, "preferred_work_modes", []))
    preferred_employment_types = _lower_list(getattr(preferences, "preferred_employment_types", []))

    work_mode_match = not preferred_work_modes or job.work_mode.value in preferred_work_modes
    employment_type_match = (
        not preferred_employment_types or job.employment_type.value in preferred_employment_types
    )

    score = 0
    if work_mode_match:
        score += 6
    if employment_type_match:
        score += 4
    summary = "Work mode and employment type align with user preferences."
    if score == 0:
        summary = "Work mode and employment type are outside current user preferences."
    elif score < COMPONENT_MAX_SCORES["preferences"]:
        summary = "Only part of the work mode or employment type preference set matches."

    return {
        "score": score,
        "maxScore": COMPONENT_MAX_SCORES["preferences"],
        "preferredWorkModes": list(getattr(preferences, "preferred_work_modes", [])) if preferences else [],
        "preferredEmploymentTypes": list(getattr(preferences, "preferred_employment_types", []))
        if preferences
        else [],
        "jobWorkMode": job.work_mode.value,
        "jobEmploymentType": job.employment_type.value,
        "summary": summary,
    }


def _tokenize(value: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(value.lower()))


def _normalize_seniority(value: str | None) -> str | None:
    if value is None:
        return None
    lowered = value.lower()
    for label in SENIORITY_ORDER:
        if label in lowered:
            return label
    return lowered if lowered else None


def _lower_list(values: list[str]) -> list[str]:
    return [value.lower() for value in values]
