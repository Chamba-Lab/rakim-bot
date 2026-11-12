import re
from datetime import time
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .daily_topic import parse_times, select_presets, split_list
from .roulette import load_presets

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
    links_channel_id: Snowflake

    # El saludo espera al mensaje nativo de entrada de Discord para no salir antes. Con
    # false (mensajes nativos desactivados) se usa una pausa fija corta.
    welcome_wait_system_message: bool = True

    # Canal privado de logs y canal del aviso de bump (con un rol y/o una persona a mencionar, opcionales).
    log_channel_id: Snowflake
    bump_channel_id: Snowflake
    bump_role_id: Snowflake | None = None
    bump_user_id: Snowflake | None = None

    # Disboard gestiona el bump; el patrón reconoce su confirmación de éxito.
    disboard_bot_id: Snowflake = 302050872383242240
    bump_success_pattern: str = "bump done"
    bump_cooldown_minutes: int = Field(default=120, gt=0)

    # Nombres legibles para los códigos de invitación: {"codigo": "nombre"}.
    invite_labels: dict[str, str] = {}

    # Tema del día en el canal general: horas de Lima separadas por coma (vacío lo apaga),
    # rol a mencionar (opcional) y grupos de `roulette.json` de los que sale.
    daily_topic_times: str = ""
    daily_topic_role_id: Snowflake | None = None
    daily_topic_presets: str = "employability,icebreaker-culture,daily-learning"

    # Roles de las preguntas del Onboarding para `/miembros`: IDs separados por coma.
    country_role_ids: str = ""
    stage_role_ids: str = ""
    notification_role_ids: str = ""  # Avisos, Eventos y Actividades

    state_path: str = "data/state.json"

    @field_validator("country_role_ids", "stage_role_ids", "notification_role_ids")
    @classmethod
    def _valid_role_ids(cls, value: str) -> str:
        parse_ids(value)
        return value

    @field_validator("daily_topic_times")
    @classmethod
    def _valid_times(cls, value: str) -> str:
        parse_times(value)
        return value

    @field_validator("daily_topic_presets")
    @classmethod
    def _known_presets(cls, value: str) -> str:
        select_presets(load_presets(), split_list(value))
        return value

    @property
    def bump_regex(self) -> re.Pattern[str]:
        return re.compile(self.bump_success_pattern, re.IGNORECASE)

    @property
    def topic_times(self) -> list[time]:
        return parse_times(self.daily_topic_times)

    @property
    def topic_preset_ids(self) -> list[str]:
        return split_list(self.daily_topic_presets)

    @property
    def country_roles(self) -> list[int]:
        return parse_ids(self.country_role_ids)

    @property
    def stage_roles(self) -> list[int]:
        return parse_ids(self.stage_role_ids)

    @property
    def notification_roles(self) -> list[int]:
        return parse_ids(self.notification_role_ids)


def parse_ids(text: str) -> list[int]:
    """«123, 456» → IDs de Discord. Falla si alguno no lo parece."""
    ids = []
    for part in split_list(text):
        if not part.isdigit() or not 10**16 <= int(part) < 10**20:
            raise ValueError(f"ID de Discord no válido: {part!r}")
        ids.append(int(part))
    return ids
