# Import all models so they register with Base.metadata when this package
# is first imported.  Without this, init_db() → Base.metadata.create_all()
# would find zero tables to create.
from app.models.db_models import (  # noqa: F401
    Job,
    Match,
    Profile,
    ResumeVersion,
    User,
)
