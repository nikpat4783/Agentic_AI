from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    database_url: str = "sqlite:///./app.db"

    embedding_model_name: str = "all-MiniLM-L6-v2"

    cors_origins: str = "http://localhost:5173"

    ncbi_contact_email: str = ""

    max_agent_iterations: int = 6

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "agentic-rag-backend"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
