from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings. Eeach field can be overriden by an environment variable
    with the FIRDGED_ prefix, or by a line in a local .env file.
    Example: FRIDGED_DATABASE_URL=sqlite:///./other.db
    """

    # extra="ignore": unrelated lines in .env must not crash the app
    model_config = SettingsConfigDict(env_prefix="FRIDGED_", env_file=".env", extra="ignore")

    # Where the SQLite file lives (relative to the folder you start the app from)
    database_url: str = "sqlite:///./fridged.db"

    # Used to decide which week or month an event belongs to
    # Everything is stored in UTC. This is only for reporting periods.
    timezone: str = "Europe/Stockholm"


# One shared instance that the rest of the app imports
settings = Settings()
