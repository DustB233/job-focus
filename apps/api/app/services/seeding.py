from __future__ import annotations

from datetime import datetime, timezone

from job_focus_shared import (
    ApplicationStatus,
    EmploymentType,
    JobSource,
    MatchStrength,
    PacketStatus,
    WorkMode,
)
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import (
    Application,
    ApplicationEvent,
    ApplicationPacket,
    AuthSession,
    Job,
    JobMatch,
    JobSourceConfig,
    Profile,
    Resume,
    User,
    UserPreference,
)

DEMO_USER_ID = "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9"
DEMO_PROFILE_ID = "344c06ca-29c6-4428-b6ad-b45d4c432af2"
DEMO_PREFERENCE_ID = "f0915f25-d23c-4743-b585-a21e0d450e46"
DEMO_RESUME_ID = "8d926335-6bbf-4fe0-9021-b0a2769038d6"
DEMO_SESSION_ID = "51fe10a8-56a6-418a-906f-a6e6b352cf6b"
DEMO_PACKET_IDS = [
    "7806e446-54d9-45fa-9f26-6432143af6f3",
    "38bf8cb7-9890-4fd0-82c0-77d92354ca34",
    "735d57a1-a7a8-4caf-b97d-bf7e32e4585b",
]
DEMO_APPLICATION_IDS = [
    "9985d07f-a74e-42c1-9d0e-2d0b13c34074",
    "eae6b6f3-c7e4-4b64-a96b-cb5c80eb8571",
    "9a0d54b6-c112-48f0-86c9-16687e7ca44f",
]
DEMO_JOB_SOURCE_IDS = {
    JobSource.GREENHOUSE: "4de97149-68d8-4a0d-a949-ed9734ec4a8a",
    JobSource.LEVER: "4f55cfd6-115e-4e2f-b20d-027c3f0f30af",
    JobSource.ASHBY: "85cfdf69-c532-4d9b-b3a2-8a81834dedf4",
    JobSource.MANUAL: "648948cc-bdfc-4d3f-abaa-1f304b6b7cf4",
}
DEMO_JOB_IDS = [
    "c2b7d44e-c26c-418e-a8fe-a23810e51e26",
    "c46f8d95-d508-4efa-b0f2-8ae0c640d95d",
    "ff193830-6d3f-492e-89ab-a94ef7511f9a",
]
DEMO_MATCH_IDS = [
    "d826f1d9-f9be-4705-90c3-2bcf2d0a5be1",
    "d5650b28-07ef-4fa4-8fb9-f588d3d85c3e",
]
DEMO_EVENT_IDS = [
    "c3a35af7-86ea-4ae8-b7d7-4e55de6184dc",
    "3b65b7e0-3db3-45c9-82d7-7c45df784e56",
    "a05508ab-e43a-40e3-927f-84c9ed9151bf",
    "f2051180-f4b9-4408-a236-fbf2e8a97acc",
    "4206cc14-529f-4a1a-b523-53d78f8325e5",
    "f0fbef82-c3b7-4f3a-a589-1c4f2f78ca1b",
]


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seed_demo_data(session: Session) -> dict[str, int]:
    session.execute(delete(ApplicationEvent))
    session.execute(delete(Application))
    session.execute(delete(ApplicationPacket))
    session.execute(delete(JobMatch))
    session.execute(delete(Job))
    session.execute(delete(AuthSession))
    session.execute(delete(Resume))
    session.execute(delete(UserPreference))
    session.execute(delete(Profile))
    session.execute(delete(User))
    session.execute(delete(JobSourceConfig))

    job_sources = [
        JobSourceConfig(
            id=DEMO_JOB_SOURCE_IDS[JobSource.GREENHOUSE],
            slug=JobSource.GREENHOUSE,
            display_name="Greenhouse",
            base_url="https://boards-api.greenhouse.io/v1/boards",
        ),
        JobSourceConfig(
            id=DEMO_JOB_SOURCE_IDS[JobSource.LEVER],
            slug=JobSource.LEVER,
            display_name="Lever",
            base_url="https://api.lever.co/v0/postings",
        ),
        JobSourceConfig(
            id=DEMO_JOB_SOURCE_IDS[JobSource.ASHBY],
            slug=JobSource.ASHBY,
            display_name="Ashby",
            base_url="https://jobs.ashbyhq.com",
        ),
        JobSourceConfig(
            id=DEMO_JOB_SOURCE_IDS[JobSource.MANUAL],
            slug=JobSource.MANUAL,
            display_name="Manual Link",
            base_url=None,
            is_active=False,
        ),
    ]

    user = User(
        id=DEMO_USER_ID,
        email="demo@jobfocus.dev",
        hashed_password="demo-password",
        is_active=True,
        created_at=dt("2026-04-12T09:00:00Z"),
        updated_at=dt("2026-04-12T09:00:00Z"),
    )
    profile = Profile(
        id=DEMO_PROFILE_ID,
        user_id=DEMO_USER_ID,
        full_name="Avery Collins",
        headline="Senior Product Operations Manager moving into AI platform roles.",
        location="Seattle, WA",
        target_roles=["Product Operations", "Program Manager", "AI Platform Operations"],
        years_experience=8,
        seniority_level="senior",
        authorization_regions=["US"],
        created_at=dt("2026-04-12T09:00:00Z"),
        updated_at=dt("2026-04-12T09:00:00Z"),
    )
    preferences = UserPreference(
        id=DEMO_PREFERENCE_ID,
        user_id=DEMO_USER_ID,
        preferred_locations=["Remote - US", "Seattle, WA"],
        preferred_work_modes=["remote", "hybrid"],
        preferred_employment_types=["full_time"],
        desired_salary_min=150000,
        desired_salary_max=190000,
        auto_apply_enabled=False,
        auto_apply_min_score=88,
        created_at=dt("2026-04-12T09:00:00Z"),
        updated_at=dt("2026-04-12T09:00:00Z"),
    )
    resume = Resume(
        id=DEMO_RESUME_ID,
        user_id=DEMO_USER_ID,
        version=1,
        title="Avery Collins - Product Ops Resume",
        file_name="avery-collins-resume.pdf",
        summary="Scaled hiring operations, workflow automation, and GTM reporting across venture-backed SaaS teams.",
        skills=["SQL", "Python", "Notion", "Automation", "Stakeholder Management", "Hiring Ops"],
        is_default=True,
        created_at=dt("2026-04-12T09:30:00Z"),
        updated_at=dt("2026-04-12T09:30:00Z"),
    )

    jobs = [
        Job(
            id=DEMO_JOB_IDS[0],
            job_source_id=DEMO_JOB_SOURCE_IDS[JobSource.GREENHOUSE],
            external_job_id="northstar-ai-program-manager",
            company="Northstar Labs",
            title="AI Program Manager",
            location="Remote - US",
            work_mode=WorkMode.REMOTE,
            employment_type=EmploymentType.FULL_TIME,
            salary_min=155000,
            salary_max=185000,
            description="Lead cross-functional delivery for AI product launches and process automation.",
            application_url="https://boards.greenhouse.io/northstar/jobs/12345",
            seniority_level="senior",
            authorization_requirement="US work authorization required",
            raw_payload={"id": 12345, "title": "AI Program Manager"},
            normalized_payload={"company": "Northstar Labs", "title": "AI Program Manager"},
            posted_at=dt("2026-04-11T18:00:00Z"),
            created_at=dt("2026-04-11T18:00:00Z"),
            updated_at=dt("2026-04-11T18:00:00Z"),
        ),
        Job(
            id=DEMO_JOB_IDS[1],
            job_source_id=DEMO_JOB_SOURCE_IDS[JobSource.LEVER],
            external_job_id="relay-ops-systems-lead",
            company="Relay Commerce",
            title="Operations Systems Lead",
            location="San Francisco, CA",
            work_mode=WorkMode.HYBRID,
            employment_type=EmploymentType.FULL_TIME,
            salary_min=145000,
            salary_max=172000,
            description="Own business systems, recruiting workflows, and operational analytics.",
            application_url="https://jobs.lever.co/relay/abc123",
            seniority_level="lead",
            authorization_requirement="US work authorization required",
            raw_payload={"id": "relay-ops-systems-lead", "text": "Operations Systems Lead"},
            normalized_payload={"company": "Relay Commerce", "title": "Operations Systems Lead"},
            posted_at=dt("2026-04-10T14:00:00Z"),
            created_at=dt("2026-04-10T14:00:00Z"),
            updated_at=dt("2026-04-10T14:00:00Z"),
        ),
        Job(
            id=DEMO_JOB_IDS[2],
            job_source_id=DEMO_JOB_SOURCE_IDS[JobSource.ASHBY],
            external_job_id="meridian-platform-ops-manager",
            company="Meridian AI",
            title="Platform Operations Manager",
            location="New York, NY",
            work_mode=WorkMode.REMOTE,
            employment_type=EmploymentType.FULL_TIME,
            salary_min=160000,
            salary_max=195000,
            description="Build playbooks, scorecards, and launch systems for AI customer operations.",
            application_url="https://jobs.ashbyhq.com/meridian/xyz987",
            seniority_level="senior",
            authorization_requirement="US work authorization required",
            raw_payload={"id": "xyz987", "title": "Platform Operations Manager"},
            normalized_payload={"company": "Meridian AI", "title": "Platform Operations Manager"},
            posted_at=dt("2026-04-09T16:30:00Z"),
            created_at=dt("2026-04-09T16:30:00Z"),
            updated_at=dt("2026-04-09T16:30:00Z"),
        ),
    ]

    matches = [
        JobMatch(
            id=DEMO_MATCH_IDS[0],
            user_id=DEMO_USER_ID,
            job_id=DEMO_JOB_IDS[0],
            match_score=91,
            strength=MatchStrength.HIGH,
            rationale="Role lines up with AI operations, stakeholder leadership, and remote-first preference.",
            why_matched={
                "totalScore": 91,
                "components": {
                    "title": {"score": 25, "summary": "Strong title overlap"},
                    "skills": {
                        "score": 16,
                        "matchedSkills": ["Automation", "Python"],
                        "summary": "Skills overlap surfaced in the role description.",
                    },
                },
                "strengths": [
                    "Strong title overlap",
                    "Remote preference aligned",
                    "Skills overlap: Automation, Python",
                ],
                "concerns": [],
            },
            created_at=dt("2026-04-12T10:00:00Z"),
            updated_at=dt("2026-04-12T10:00:00Z"),
        ),
        JobMatch(
            id=DEMO_MATCH_IDS[1],
            user_id=DEMO_USER_ID,
            job_id=DEMO_JOB_IDS[1],
            match_score=78,
            strength=MatchStrength.MEDIUM,
            rationale="Strong systems overlap, slightly lower fit because of hybrid location constraints.",
            why_matched={
                "totalScore": 78,
                "components": {
                    "title": {"score": 20, "summary": "Good title overlap"},
                    "location": {
                        "score": 6,
                        "summary": "Location fit is weaker than remote-first roles.",
                    },
                },
                "strengths": ["Good title overlap", "Operational systems skills are relevant"],
                "concerns": ["Location fit is weaker than remote-first roles"],
            },
            created_at=dt("2026-04-12T10:05:00Z"),
            updated_at=dt("2026-04-12T10:05:00Z"),
        ),
    ]

    packets = [
        ApplicationPacket(
            id=DEMO_PACKET_IDS[0],
            user_id=DEMO_USER_ID,
            job_id=DEMO_JOB_IDS[0],
            resume_id=DEMO_RESUME_ID,
            status=PacketStatus.WAITING_REVIEW,
            selected_resume_version=1,
            tailored_resume_summary="Targeted for cross-functional AI launch operations and workflow automation programs.",
            cover_note="I have led cross-functional operating cadences and automation rollouts in fast-growing SaaS teams.",
            screening_answers={
                "work_authorization": "Authorized to work in the United States.",
                "years_experience": "8 years of relevant experience.",
                "location_flexibility": "Based in Seattle, WA and open to Remote - US, Seattle, WA opportunities.",
                "work_mode_preference": "Preferred work modes: remote, hybrid.",
            },
            missing_fields=[],
            created_at=dt("2026-04-12T10:45:00Z"),
            updated_at=dt("2026-04-12T10:45:00Z"),
        ),
        ApplicationPacket(
            id=DEMO_PACKET_IDS[1],
            user_id=DEMO_USER_ID,
            job_id=DEMO_JOB_IDS[1],
            resume_id=DEMO_RESUME_ID,
            status=PacketStatus.FINALIZED,
            selected_resume_version=1,
            tailored_resume_summary="Positioned around systems ownership, analytics, and automation delivery.",
            cover_note="I have owned systems programs and recruiting workflow improvements across SaaS operations teams.",
            screening_answers={
                "work_authorization": "Authorized to work in the United States.",
                "years_experience": "8 years of relevant experience.",
            },
            missing_fields=[],
            created_at=dt("2026-04-12T12:00:00Z"),
            updated_at=dt("2026-04-12T12:00:00Z"),
        ),
        ApplicationPacket(
            id=DEMO_PACKET_IDS[2],
            user_id=DEMO_USER_ID,
            job_id=DEMO_JOB_IDS[2],
            resume_id=DEMO_RESUME_ID,
            status=PacketStatus.FINALIZED,
            selected_resume_version=1,
            tailored_resume_summary="Framed for AI customer operations systems and launch playbooks.",
            cover_note="I’m excited to bring operational rigor to AI customer programs and scale repeatable systems.",
            screening_answers={
                "work_authorization": "Authorized to work in the United States.",
                "years_experience": "8 years of relevant experience.",
            },
            missing_fields=[],
            created_at=dt("2026-04-12T13:00:00Z"),
            updated_at=dt("2026-04-12T13:00:00Z"),
        ),
    ]

    applications = [
        Application(
            id=DEMO_APPLICATION_IDS[0],
            user_id=DEMO_USER_ID,
            job_id=DEMO_JOB_IDS[0],
            current_packet_id=DEMO_PACKET_IDS[0],
            status=ApplicationStatus.WAITING_REVIEW,
            notes="Resume is tailored. Cover note still needs a final pass.",
            submitted_at=None,
            last_error=None,
            blocking_reason=None,
            duplicate_of_application_id=None,
            created_at=dt("2026-04-12T11:00:00Z"),
            updated_at=dt("2026-04-12T11:00:00Z"),
        ),
        Application(
            id=DEMO_APPLICATION_IDS[1],
            user_id=DEMO_USER_ID,
            job_id=DEMO_JOB_IDS[1],
            current_packet_id=DEMO_PACKET_IDS[1],
            status=ApplicationStatus.FAILED,
            notes="Lever rejected the submission because a required field was missing.",
            submitted_at=None,
            last_error="required_phone_missing",
            blocking_reason=None,
            duplicate_of_application_id=None,
            created_at=dt("2026-04-12T11:30:00Z"),
            updated_at=dt("2026-04-12T12:15:00Z"),
        ),
        Application(
            id=DEMO_APPLICATION_IDS[2],
            user_id=DEMO_USER_ID,
            job_id=DEMO_JOB_IDS[2],
            current_packet_id=DEMO_PACKET_IDS[2],
            status=ApplicationStatus.SUBMITTED,
            notes="Submitted successfully through the ATS adapter.",
            submitted_at=dt("2026-04-12T13:20:00Z"),
            last_error=None,
            blocking_reason=None,
            duplicate_of_application_id=None,
            created_at=dt("2026-04-12T12:45:00Z"),
            updated_at=dt("2026-04-12T13:20:00Z"),
        ),
    ]

    events = [
        ApplicationEvent(
            id=DEMO_EVENT_IDS[0],
            application_id=DEMO_APPLICATION_IDS[0],
            from_status=None,
            to_status=ApplicationStatus.DISCOVERED,
            event_type="created",
            actor="seed",
            note="Discovered from inbound job match.",
            payload={},
            created_at=dt("2026-04-12T10:40:00Z"),
        ),
        ApplicationEvent(
            id=DEMO_EVENT_IDS[1],
            application_id=DEMO_APPLICATION_IDS[0],
            from_status=ApplicationStatus.DISCOVERED,
            to_status=ApplicationStatus.SHORTLISTED,
            event_type="status_changed",
            actor="seed",
            note="Shortlisted because the match score crossed the review threshold.",
            payload={"matchScore": 91},
            created_at=dt("2026-04-12T10:42:00Z"),
        ),
        ApplicationEvent(
            id=DEMO_EVENT_IDS[2],
            application_id=DEMO_APPLICATION_IDS[0],
            from_status=ApplicationStatus.SHORTLISTED,
            to_status=ApplicationStatus.WAITING_REVIEW,
            event_type="status_changed",
            actor="seed",
            note="Packet prepared and queued for final review.",
            payload={"packetId": DEMO_PACKET_IDS[0]},
            created_at=dt("2026-04-12T10:50:00Z"),
        ),
        ApplicationEvent(
            id=DEMO_EVENT_IDS[3],
            application_id=DEMO_APPLICATION_IDS[1],
            from_status=None,
            to_status=ApplicationStatus.DISCOVERED,
            event_type="created",
            actor="seed",
            note="Created from seeded failure scenario.",
            payload={},
            created_at=dt("2026-04-12T11:40:00Z"),
        ),
        ApplicationEvent(
            id=DEMO_EVENT_IDS[4],
            application_id=DEMO_APPLICATION_IDS[1],
            from_status=ApplicationStatus.SUBMITTING,
            to_status=ApplicationStatus.FAILED,
            event_type="apply_failed",
            actor="worker",
            note="Missing required phone number for Lever submission.",
            payload={"errorCode": "required_phone_missing", "provider": "lever"},
            created_at=dt("2026-04-12T12:15:00Z"),
        ),
        ApplicationEvent(
            id=DEMO_EVENT_IDS[5],
            application_id=DEMO_APPLICATION_IDS[2],
            from_status=ApplicationStatus.SUBMITTING,
            to_status=ApplicationStatus.SUBMITTED,
            event_type="apply_succeeded",
            actor="worker",
            note="Ashby submission confirmed.",
            payload={
                "confirmationNumber": "ASHBY-20481",
                "submittedAt": "2026-04-12T13:20:00.000Z",
            },
            created_at=dt("2026-04-12T13:20:00Z"),
        ),
    ]

    auth_session = AuthSession(
        id=DEMO_SESSION_ID,
        user_id=DEMO_USER_ID,
        token_hash="demo-session-token",
        expires_at=datetime(2026, 4, 19, 9, 0, 0, tzinfo=timezone.utc),
        revoked_at=None,
        created_at=dt("2026-04-12T09:05:00Z"),
        updated_at=dt("2026-04-12T09:05:00Z"),
    )

    session.add_all(
        [
            *job_sources,
            user,
            profile,
            preferences,
            resume,
            *jobs,
            *matches,
            *packets,
            *applications,
            *events,
            auth_session,
        ]
    )
    session.commit()

    return {
        "users": 1,
        "profiles": 1,
        "preferences": 1,
        "resumes": 1,
        "job_sources": len(job_sources),
        "jobs": len(jobs),
        "matches": len(matches),
        "application_packets": len(packets),
        "applications": len(applications),
        "application_events": len(events),
        "auth_sessions": 1,
    }
