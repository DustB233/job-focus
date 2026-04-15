from enum import StrEnum


class WorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class JobSource(StrEnum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    MANUAL = "manual"


class MatchStrength(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceHealthStatus(StrEnum):
    HEALTHY = "healthy"
    WARNING = "warning"
    INACTIVE = "inactive"


class ReviewAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class ApplicationStatus(StrEnum):
    DISCOVERED = "discovered"
    SHORTLISTED = "shortlisted"
    DRAFT_READY = "draft_ready"
    NEEDS_USER_INPUT = "needs_user_input"
    WAITING_REVIEW = "waiting_review"
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"
    FAILED = "failed"
    BLOCKED = "blocked"
    DUPLICATE = "duplicate"


class PacketStatus(StrEnum):
    DRAFT_READY = "draft_ready"
    NEEDS_USER_INPUT = "needs_user_input"
    WAITING_REVIEW = "waiting_review"
    FINALIZED = "finalized"
