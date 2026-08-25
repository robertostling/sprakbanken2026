import datetime
from pathlib import Path
from typing import Annotated, Any, List, Union
import json
from pydantic import BaseModel, ConfigDict, Field, RootModel


class Question(BaseModel):
    """A question formulation with its corresponding language code."""
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, description="Question text.")
    language: str = Field(..., min_length=2, description="Language code (e.g. 'ENG', 'SWE').")


class DateAnswerItem(BaseModel):
    """An answer tied to a single point-in-time date."""
    model_config = ConfigDict(extra="forbid")

    date: datetime.date = Field(..., description="Point-in-time date (YYYY-MM-DD).")
    answer: str = Field(..., description="The answer text.")
    source: str = Field(..., description="Source citation or URL.")


class DateRange(BaseModel):
    """A date interval with 'from' and 'to' boundaries."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_date: datetime.date = Field(..., alias="from", description="Start date (YYYY-MM-DD).")
    to_date: datetime.date = Field(..., alias="to", description="End date (YYYY-MM-DD).")


class DateRangeAnswerItem(BaseModel):
    """An answer tied to a date range interval."""
    model_config = ConfigDict(extra="forbid")

    date_range: DateRange = Field(..., description="Date range interval.")
    answer: str = Field(..., description="The answer text.")
    source: str = Field(..., description="Source citation or URL.")


class DateLanguageAnswers(BaseModel):
    """Group of point-in-time date answers for a specific language."""
    model_config = ConfigDict(extra="forbid")

    language: str = Field(..., min_length=2, description="Language code.")
    answers: List[DateAnswerItem] = Field(..., min_length=1, description="List of date answers.")


class DateRangeLanguageAnswers(BaseModel):
    """Group of date range answers for a specific language."""
    model_config = ConfigDict(extra="forbid")

    language: str = Field(..., min_length=2, description="Language code.")
    answers: List[DateRangeAnswerItem] = Field(..., min_length=1, description="List of date range answers.")


class DateEntry(BaseModel):
    """Dataset entry where all answers are point-in-time dates."""
    model_config = ConfigDict(extra="forbid")

    questions: List[Question] = Field(..., min_length=1, description="List of questions across languages.")
    answers: List[DateLanguageAnswers] = Field(..., min_length=1, description="Answers partitioned by language.")


class DateRangeEntry(BaseModel):
    """Dataset entry where all answers are date ranges."""
    model_config = ConfigDict(extra="forbid")

    questions: List[Question] = Field(..., min_length=1, description="List of questions across languages.")
    answers: List[DateRangeLanguageAnswers] = Field(..., min_length=1, description="Answers partitioned by language.")


Entry = Annotated[Union[DateEntry, DateRangeEntry], Field(union_mode="left_to_right")]


class Dataset(RootModel[List[Entry]]):
    """Multilingual temporal QA dataset containing a list of entries."""

    @classmethod
    def load_json(cls, path_or_str: Union[str, Path]) -> "Dataset":
        """Load and validate dataset from a JSON file path or JSON string."""
        path = Path(path_or_str)
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return cls.model_validate(raw)
        return cls.model_validate_json(path_or_str)

    def save_json(self, path: Union[str, Path], indent: int = 2) -> None:
        """Save dataset to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(by_alias=True, mode="json"), f, indent=indent, ensure_ascii=False)
            f.write("\n")
