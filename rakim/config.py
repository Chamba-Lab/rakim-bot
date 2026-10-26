import re
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Un ID de Discord (snowflake) tiene entre 17 y 20 dígitos.
Snowflake = Annotated[int, Field(ge=10**16, lt=10**20)]


class Settings(BaseSettings):
    """Configuración del entorno (o de `.env`). Si falta algo, falla al arrancar."""

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    discord_token: SecretStr
    guild_id: Snowflake

    # Canal general (saludo) y canales que menciona el saludo.
    welcome_channel_id: Snowflake
    intro_channel_id: Snowflake
    ask_feedback_channel_id: Snowflake
    server_feedback_channel_id: Snowflake
    links_channel_id: Snowflake

    # Canal privado de logs y canal del aviso de bump (con un rol a mencionar, opcional).
    log_channel_id: Snowflake
    bump_channel_id: Snowflake
    bump_role_id: Snowflake | None = None

    # Disboard gestiona el bump; el patrón reconoce su confirmación de éxito.
    disboard_bot_id: Snowflake = 302050872383242240
    bump_success_pattern: str = "bump done"
    bump_cooldown_minutes: int = Field(default=120, gt=0)

    # Nombres legibles para los códigos de invitación: {"codigo": "nombre"}.
    invite_labels: dict[str, str] = {}

    state_path: str = "data/state.json"

    @property
    def bump_regex(self) -> re.Pattern[str]:
        return re.compile(self.bump_success_pattern, re.IGNORECASE)
