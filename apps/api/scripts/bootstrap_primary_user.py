from __future__ import annotations

import argparse
import getpass

from app.db.session import session_scope
from app.services.bootstrap_primary_user import (
    PrimaryUserBootstrapInput,
    bootstrap_primary_user,
)
from job_focus_shared import EmploymentType, WorkMode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the first real primary user for a live Job Focus deployment."
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--password")
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--headline", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--target-role", action="append", required=True)
    parser.add_argument("--years-experience", required=True, type=int)
    parser.add_argument("--seniority-level")
    parser.add_argument("--authorization-region", action="append", required=True)
    parser.add_argument("--preferred-location", action="append", required=True)
    parser.add_argument(
        "--preferred-work-mode",
        action="append",
        required=True,
        choices=[mode.value for mode in WorkMode],
    )
    parser.add_argument(
        "--preferred-employment-type",
        action="append",
        default=[],
        choices=[employment_type.value for employment_type in EmploymentType],
    )
    parser.add_argument("--desired-salary-min", type=int)
    parser.add_argument("--desired-salary-max", type=int)
    parser.add_argument("--auto-apply-enabled", action="store_true")
    parser.add_argument("--auto-apply-min-score", type=int, default=85)
    parser.add_argument("--resume-title", required=True)
    parser.add_argument("--resume-file-name", required=True)
    parser.add_argument("--resume-summary", required=True)
    parser.add_argument("--resume-skill", action="append", required=True)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    password = args.password or getpass.getpass("Primary user password: ")

    payload = PrimaryUserBootstrapInput(
        email=args.email,
        password=password,
        full_name=args.full_name,
        headline=args.headline,
        location=args.location,
        target_roles=args.target_role,
        years_experience=args.years_experience,
        seniority_level=args.seniority_level,
        authorization_regions=args.authorization_region,
        preferred_locations=args.preferred_location,
        preferred_work_modes=[WorkMode(value) for value in args.preferred_work_mode],
        preferred_employment_types=[
            EmploymentType(value) for value in args.preferred_employment_type
        ],
        desired_salary_min=args.desired_salary_min,
        desired_salary_max=args.desired_salary_max,
        auto_apply_enabled=args.auto_apply_enabled,
        auto_apply_min_score=args.auto_apply_min_score,
        resume_title=args.resume_title,
        resume_file_name=args.resume_file_name,
        resume_summary=args.resume_summary,
        resume_skills=args.resume_skill,
    )

    with session_scope() as session:
        result = bootstrap_primary_user(session, payload)

    print(
        "Bootstrapped primary user "
        f"{result.email} (user_id={result.user_id}, profile_id={result.profile_id}, "
        f"preferences_id={result.preferences_id}, resume_id={result.resume_id})."
    )


if __name__ == "__main__":
    main()
