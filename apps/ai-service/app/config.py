from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "immigration-docs"
    firebase_admin_service_account: str = ""

    # Model names via OpenRouter
    model_simple: str = "anthropic/claude-haiku-4-5"
    model_complex: str = "anthropic/claude-sonnet-4-5"

    class Config:
        env_file = ".env"


settings = Settings()
