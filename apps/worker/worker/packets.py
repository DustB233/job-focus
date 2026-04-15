from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models import Job, Resume, User
from job_focus_shared import PacketStatus


APPROVED_SCREENING_ANSWER_KEYS = {
    "work_authorization",
    "years_experience",
    "location_flexibility",
    "work_mode_preference",
}


@dataclass(frozen=True, slots=True)
class PacketDraft:
    status: PacketStatus
    selected_resume_version: int | None
    tailored_resume_summary: str | None
    cover_note: str | None
    screening_answers: dict[str, str]
    missing_fields: list[str]


def generate_packet_draft(
    user: User,
    resume: Resume | None,
    job: Job,
    why_matched: dict[str, Any] | None = None,
) -> PacketDraft:
    profile = user.profile
    missing_fields: list[str] = []

    if profile is None:
        missing_fields.append("profile")
    if resume is None:
        missing_fields.append("resume")

    summary = _build_tailored_resume_summary(resume, job, why_matched) if resume is not None else None
    cover_note = _build_cover_note(user, resume, job, why_matched) if profile is not None else None
    screening_answers = _build_screening_answers(user, job, missing_fields)

    status = PacketStatus.WAITING_REVIEW if not missing_fields else PacketStatus.NEEDS_USER_INPUT
    return PacketDraft(
        status=status,
        selected_resume_version=resume.version if resume is not None else None,
        tailored_resume_summary=summary,
        cover_note=cover_note,
        screening_answers=screening_answers,
        missing_fields=missing_fields,
    )


def _build_tailored_resume_summary(
    resume: Resume,
    job: Job,
    why_matched: dict[str, Any] | None,
) -> str:
    matched_skills = _extract_matched_skills(why_matched)
    if matched_skills:
        skill_phrase = ", ".join(matched_skills[:3])
        return (
            f"{resume.summary} Tailored for {job.title} with emphasis on {skill_phrase}."
        )
    return f"{resume.summary} Tailored for {job.title} at {job.company}."


def _build_cover_note(
    user: User,
    resume: Resume | None,
    job: Job,
    why_matched: dict[str, Any] | None,
) -> str:
    profile = user.profile
    assert profile is not None

    matched_skills = _extract_matched_skills(why_matched)
    primary_role = profile.target_roles[0] if profile.target_roles else profile.headline
    note = (
        f"{profile.full_name} is pursuing {job.title} opportunities and brings "
        f"{profile.years_experience} years of experience in {primary_role}."
    )
    if matched_skills:
        note += f" Relevant strengths include {', '.join(matched_skills[:3])}."
    elif resume is not None and resume.skills:
        note += f" Core strengths include {', '.join(resume.skills[:3])}."
    return note


def _build_screening_answers(user: User, job: Job, missing_fields: list[str]) -> dict[str, str]:
    profile = user.profile
    preferences = user.user_preferences
    answers: dict[str, str] = {}

    if profile is None:
        return answers

    if job.authorization_requirement:
        authorization_answer = _build_work_authorization_answer(profile.authorization_regions)
        if authorization_answer is None:
            missing_fields.append("authorization_regions")
        else:
            answers["work_authorization"] = authorization_answer

    answers["years_experience"] = f"{profile.years_experience} years of relevant experience."

    location_answer = _build_location_answer(profile.location, getattr(preferences, "preferred_locations", []))
    if location_answer is None:
        missing_fields.append("preferred_locations")
    else:
        answers["location_flexibility"] = location_answer

    work_mode_answer = _build_work_mode_answer(getattr(preferences, "preferred_work_modes", []))
    if work_mode_answer is None:
        missing_fields.append("preferred_work_modes")
    else:
        answers["work_mode_preference"] = work_mode_answer

    return {key: value for key, value in answers.items() if key in APPROVED_SCREENING_ANSWER_KEYS}


def _build_work_authorization_answer(authorization_regions: list[str]) -> str | None:
    lowered = {region.lower() for region in authorization_regions}
    if "us" in lowered or "usa" in lowered or "united states" in lowered:
        return "Authorized to work in the United States."
    if authorization_regions:
        return f"Authorized to work in: {', '.join(authorization_regions)}."
    return None


def _build_location_answer(profile_location: str | None, preferred_locations: list[str]) -> str | None:
    if preferred_locations:
        return (
            f"Based in {profile_location or preferred_locations[0]} and open to "
            f"{', '.join(preferred_locations)} opportunities."
        )
    if profile_location:
        return f"Based in {profile_location}."
    return None


def _build_work_mode_answer(preferred_work_modes: list[str]) -> str | None:
    if not preferred_work_modes:
        return None
    return f"Preferred work modes: {', '.join(preferred_work_modes)}."


def _extract_matched_skills(why_matched: dict[str, Any] | None) -> list[str]:
    if not why_matched:
        return []
    components = why_matched.get("components", {})
    if not isinstance(components, dict):
        return []
    skills_component = components.get("skills", {})
    if not isinstance(skills_component, dict):
        return []
    matched_skills = skills_component.get("matchedSkills", [])
    if not isinstance(matched_skills, list):
        return []
    return [str(skill) for skill in matched_skills]
