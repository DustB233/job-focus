from __future__ import annotations

from app.models import Job, Profile, Resume, User, UserPreference
from job_focus_shared import EmploymentType, MatchStrength, PacketStatus, WorkMode

from worker.matching import calculate_match
from worker.packets import generate_packet_draft


def build_user(*, authorization_regions: list[str] | None = None) -> User:
    user = User(email="demo@jobfocus.dev", hashed_password="demo-password", is_active=True)
    user.profile = Profile(
        full_name="Avery Collins",
        headline="Senior Product Operations Manager moving into AI platform roles.",
        location="Seattle, WA",
        target_roles=["AI Platform Operations", "Program Manager", "Product Operations"],
        years_experience=8,
        seniority_level="senior",
        authorization_regions=authorization_regions if authorization_regions is not None else ["US"],
    )
    user.user_preferences = UserPreference(
        preferred_locations=["Remote - US", "Seattle, WA"],
        preferred_work_modes=["remote", "hybrid"],
        preferred_employment_types=["full_time"],
        desired_salary_min=150000,
        desired_salary_max=190000,
        auto_apply_enabled=False,
        auto_apply_min_score=85,
    )
    return user


def build_resume() -> Resume:
    return Resume(
        version=2,
        title="Avery Collins - AI Platform Resume",
        file_name="avery-collins-resume-v2.pdf",
        summary="Scaled automation, recruiting systems, and cross-functional launch operations in SaaS teams.",
        skills=["Automation", "Python", "SQL", "Stakeholder Management"],
        is_default=True,
    )


def build_job() -> Job:
    return Job(
        company="Northstar Labs",
        title="Senior AI Platform Operations Manager",
        location="Remote - US",
        work_mode=WorkMode.REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        salary_min=160000,
        salary_max=185000,
        description=(
            "Lead AI platform operations, workflow automation, stakeholder management, "
            "and recruiting systems. US work authorization required."
        ),
        application_url="https://boards.greenhouse.io/northstar/jobs/12345",
        seniority_level="senior",
        authorization_requirement="US work authorization required",
        raw_payload={},
        normalized_payload={},
    )


def test_calculate_match_scores_required_dimensions_and_structures_why_matched() -> None:
    user = build_user()
    resume = build_resume()
    job = build_job()

    result = calculate_match(user, resume, job)

    assert result.score >= 85
    assert result.strength == MatchStrength.HIGH
    assert "components" in result.why_matched
    assert set(result.why_matched["components"].keys()) == {
        "title",
        "location",
        "seniority",
        "skills",
        "authorization",
        "salary",
        "preferences",
    }
    assert "AI Platform Operations" in result.why_matched["components"]["title"]["matchedRoles"]
    assert "Automation" in result.why_matched["components"]["skills"]["matchedSkills"]
    assert "Stakeholder Management" in result.why_matched["components"]["skills"]["matchedSkills"]
    assert result.why_matched["components"]["authorization"]["score"] == 10
    assert result.why_matched["components"]["salary"]["score"] == 10


def test_generate_packet_draft_uses_only_approved_structured_data() -> None:
    user = build_user()
    resume = build_resume()
    job = build_job()
    match_result = calculate_match(user, resume, job)

    draft = generate_packet_draft(user, resume, job, match_result.why_matched)

    assert draft.status == PacketStatus.WAITING_REVIEW
    assert draft.selected_resume_version == 2
    assert "Tailored for Senior AI Platform Operations Manager" in (draft.tailored_resume_summary or "")
    assert "Automation" in (draft.tailored_resume_summary or "")
    assert "Avery Collins is pursuing Senior AI Platform Operations Manager opportunities" in (
        draft.cover_note or ""
    )
    assert draft.screening_answers == {
        "work_authorization": "Authorized to work in the United States.",
        "years_experience": "8 years of relevant experience.",
        "location_flexibility": "Based in Seattle, WA and open to Remote - US, Seattle, WA opportunities.",
        "work_mode_preference": "Preferred work modes: remote, hybrid.",
    }
    assert draft.missing_fields == []


def test_generate_packet_draft_blocks_when_approved_screening_data_is_missing() -> None:
    user = build_user(authorization_regions=[])
    resume = build_resume()
    job = build_job()
    match_result = calculate_match(user, resume, job)

    draft = generate_packet_draft(user, resume, job, match_result.why_matched)

    assert draft.status == PacketStatus.NEEDS_USER_INPUT
    assert "authorization_regions" in draft.missing_fields
    assert "work_authorization" not in draft.screening_answers
    assert draft.screening_answers["years_experience"] == "8 years of relevant experience."
