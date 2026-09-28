import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_FOLDER = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_FOLDER, "rent_manager.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "meter_images")
PDF_FOLDER = os.path.join(BASE_DIR, "generated_bills", "pdf")

MIN_ELECTRICITY_RATE = 11
MAX_ELECTRICITY_RATE = 20

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# Login configuration. Change these environment variables in production.
ADMIN_USERNAME = os.environ.get("RENTLEDGER_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get(
    "RENTLEDGER_ADMIN_PASSWORD_HASH",
    "pbkdf2:sha256:600000$01a00a9e592ebd93dbe9a8f863f20939$0351ff4bc3be05041e767bdd15bb07255cd841410c534efdfb8ae669727ee6df"
)
