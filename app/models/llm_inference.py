from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class LlmInference(TimestampMixin, Base):
    __tablename__ = "llm_inferences"

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    input_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False)
