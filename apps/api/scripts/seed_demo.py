from app.core.config import get_settings
from app.db.session import create_all_tables, session_scope
from app.services.dev_data import ensure_dev_demo_data_allowed
from app.services.seeding import seed_demo_data


def main() -> None:
    settings = get_settings()
    ensure_dev_demo_data_allowed(settings)

    create_all_tables()
    with session_scope() as session:
        counts = seed_demo_data(session)
    print(
        "Seeded demo data for local development only. "
        "Use `python -m scripts.reset_dev_demo_data` going forward. "
        f"{counts}"
    )


if __name__ == "__main__":
    main()
