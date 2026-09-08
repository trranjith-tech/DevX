from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DevX Backend"
    debug: bool = False

    jwt_secret_key: str = "CHANGE_THIS_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    cors_origins: str = "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500,https://trranjith-tech.github.io"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        required_origins = {
            "http://localhost:3000",
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "https://trranjith-tech.github.io",
        }
        configured_origins = {o.strip() for o in self.cors_origins.split(",") if o.strip()}
        return sorted(configured_origins | required_origins)


settings = Settings()
