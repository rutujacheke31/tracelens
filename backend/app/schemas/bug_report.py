from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class BugReportResponse(BaseModel):
    id: int
    description: str

    screenshot_filename: str | None
    screenshot_size_bytes: int | None

    supporting_file_filename: str | None
    supporting_file_size_bytes: int | None

    status: str
    analysis_result: dict[str, Any] | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )