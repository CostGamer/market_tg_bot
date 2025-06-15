from .settings import Settings
from .database import DatabaseConnection

all_settings = Settings()
db_connection = DatabaseConnection(all_settings)
