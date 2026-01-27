"""Pydantic models for Fix Bundles."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EnvActionType(str, Enum):
    """Type of environment action in a fix bundle.

    Attributes:
        INSTALL: Install a new package/dependency.
        UPGRADE: Upgrade an existing package.
        DOWNGRADE: Downgrade a package to a specific version.
        CONFIG: Change configuration settings.
        FLAG: Add/modify a flag or option.
        COMMAND: Run a shell command.
    """

    INSTALL = "install"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    CONFIG = "config"
    FLAG = "flag"
    COMMAND = "command"


class EnvAction(BaseModel):
    """Single environment action in a fix bundle.

    Attributes:
        order: Execution order (1-indexed).
        type: Type of action to perform.
        command: Command or action to execute.
        explanation: Human-readable explanation of the action.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    order: int = Field(..., ge=1, description="Execution order (1-indexed)")
    type: EnvActionType
    command: str = Field(..., min_length=1, max_length=500)
    explanation: str = Field(..., min_length=5, max_length=1000)


class Constraints(BaseModel):
    """Version constraints and compatibility info for a fix.

    Attributes:
        working_versions: Map of package/tool name to working version spec.
        incompatible_with: List of incompatible packages/versions.
        required_environment: Required environment conditions.
    """

    working_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of package/tool name to working version spec",
    )
    incompatible_with: List[str] = Field(
        default_factory=list,
        description="List of incompatible packages/versions",
    )
    required_environment: List[str] = Field(
        default_factory=list,
        description="Required environment conditions",
    )


class VerificationStep(BaseModel):
    """Step to verify a fix worked.

    Attributes:
        order: Execution order (1-indexed).
        command: Command to run for verification.
        expected_output: Expected output to confirm success.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    order: int = Field(..., ge=1)
    command: str = Field(..., min_length=1, max_length=500)
    expected_output: str = Field(..., min_length=1, max_length=1000)


class FixBundleCreate(BaseModel):
    """Model for creating a fix bundle.

    Attributes:
        env_actions: Ordered list of environment actions.
        constraints: Version constraints and compatibility.
        verification: Steps to verify fix worked.
        patch_diff: Optional unified diff format patch.
        code_fix: Optional corrected code snippet.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    env_actions: List[EnvAction] = Field(
        ...,
        min_length=1,
        description="Ordered list of environment actions",
    )
    constraints: Constraints = Field(default_factory=Constraints)
    verification: List[VerificationStep] = Field(
        ...,
        min_length=1,
        description="Steps to verify fix worked",
    )
    patch_diff: Optional[str] = Field(
        None,
        max_length=10000,
        description="Unified diff format patch",
    )
    code_fix: Optional[str] = Field(
        None,
        max_length=5000,
        description="Corrected code snippet",
    )

    @model_validator(mode="after")
    def validate_action_order(self) -> "FixBundleCreate":
        """Ensure env_actions have sequential order starting at 1.

        Returns:
            FixBundleCreate: Validated model instance.

        Raises:
            ValueError: If order is not sequential starting at 1.
        """
        orders = [a.order for a in self.env_actions]
        expected = list(range(1, len(self.env_actions) + 1))
        if sorted(orders) != expected:
            raise ValueError("env_actions must have sequential order starting at 1")
        return self

    @model_validator(mode="after")
    def validate_verification_order(self) -> "FixBundleCreate":
        """Ensure verification steps have sequential order starting at 1.

        Returns:
            FixBundleCreate: Validated model instance.

        Raises:
            ValueError: If order is not sequential starting at 1.
        """
        orders = [v.order for v in self.verification]
        expected = list(range(1, len(self.verification) + 1))
        if sorted(orders) != expected:
            raise ValueError("verification must have sequential order starting at 1")
        return self


class FixBundleResponse(FixBundleCreate):
    """Model for fix bundle API responses.

    Attributes:
        id: Unique identifier for the fix bundle.
        master_issue_id: ID of the parent master issue.
        version: Version number of this fix bundle.
        is_current: Whether this is the current active fix.
        created_at: Timestamp when fix was created.
        updated_at: Timestamp when fix was last updated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    master_issue_id: UUID
    version: int
    is_current: bool
    created_at: datetime
    updated_at: datetime
