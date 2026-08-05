from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Create a settings object with one required field (database_url).
    We search the .env file and load in the the database_url from that 
    """
    database_url: str
    read_cache_ttl_seconds: int = 30
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
