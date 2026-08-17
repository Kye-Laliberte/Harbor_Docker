from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    model_config = ConfigDict(env_file=".env")


settings = Settings()