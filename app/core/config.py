from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Yandex AI Studio ---
    YANDEX_API_KEY: str
    YANDEX_FOLDER_ID: str

    # --- Tailscale Cluster ---
    MASTER_HOST: str = "100.71.14.9"

    NEO4J_HOST: str = "100.126.216.18"
    NEO4J_PORT: str = "7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "hackathon2026password"

    CHROMA_HOST: str = "100.70.36.78"
    CHROMA_PORT: str = "8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
