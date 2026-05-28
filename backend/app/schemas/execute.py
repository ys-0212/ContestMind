from typing import Literal, Optional
from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    code: str = Field(..., description="Source code to execute")
    language: str = Field(..., description="Language: cpp, python, java, javascript")
    stdin: str = Field("", description="Standard input for the program")
    expected_output: Optional[str] = Field(
        None, description="If provided, stdout is compared and matched_expected is set"
    )


class ExecuteResponse(BaseModel):
    # Output streams
    stdout: str = Field("", description="Program standard output")
    stderr: str = Field("", description="Program standard error / compile errors")
    exit_code: int = Field(0, description="Process exit code (0 = success)")

    # Verdict
    status: str = Field(
        "ok",
        description=(
            "ok | accepted | wrong_answer | compile_error | runtime_error | tle | error"
        ),
    )
    matched_expected: Optional[bool] = Field(
        None,
        description="True/False when expected_output was provided; None otherwise",
    )
    error: Optional[str] = Field(None, description="High-level error label if service failed")
