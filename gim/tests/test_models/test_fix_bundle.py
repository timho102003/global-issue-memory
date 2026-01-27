"""Tests for fix bundle models."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.fix_bundle import (
    Constraints,
    EnvAction,
    EnvActionType,
    FixBundleCreate,
    FixBundleResponse,
    VerificationStep,
)


class TestEnvAction:
    """Tests for EnvAction model."""

    def test_valid_env_action(self) -> None:
        """Test creating a valid env action."""
        action = EnvAction(
            order=1,
            type=EnvActionType.UPGRADE,
            command="pip install langchain-core>=0.2.0",
            explanation="Install langchain-core which contains the new tool decorator",
        )
        assert action.order == 1
        assert action.type == EnvActionType.UPGRADE

    def test_order_must_be_positive(self) -> None:
        """Test that order must be >= 1."""
        with pytest.raises(ValidationError):
            EnvAction(
                order=0,
                type=EnvActionType.INSTALL,
                command="pip install package",
                explanation="Install the package",
            )

    def test_command_cannot_be_empty(self) -> None:
        """Test that command cannot be empty."""
        with pytest.raises(ValidationError):
            EnvAction(
                order=1,
                type=EnvActionType.COMMAND,
                command="",
                explanation="Run the command",
            )

    def test_explanation_min_length(self) -> None:
        """Test that explanation must have minimum length."""
        with pytest.raises(ValidationError):
            EnvAction(
                order=1,
                type=EnvActionType.CONFIG,
                command="export VAR=value",
                explanation="Do",
            )


class TestConstraints:
    """Tests for Constraints model."""

    def test_valid_constraints(self) -> None:
        """Test creating valid constraints."""
        constraints = Constraints(
            working_versions={"langchain-core": ">=0.2.0", "python": ">=3.9"},
            incompatible_with=["langchain<0.2.0"],
            required_environment=["pip"],
        )
        assert constraints.working_versions["python"] == ">=3.9"
        assert len(constraints.incompatible_with) == 1

    def test_default_empty_constraints(self) -> None:
        """Test that constraints default to empty."""
        constraints = Constraints()
        assert constraints.working_versions == {}
        assert constraints.incompatible_with == []
        assert constraints.required_environment == []


class TestVerificationStep:
    """Tests for VerificationStep model."""

    def test_valid_verification_step(self) -> None:
        """Test creating a valid verification step."""
        step = VerificationStep(
            order=1,
            command="python -c \"from langchain_core.tools import tool; print('OK')\"",
            expected_output="OK",
        )
        assert step.order == 1
        assert "langchain_core" in step.command

    def test_order_must_be_positive(self) -> None:
        """Test that order must be >= 1."""
        with pytest.raises(ValidationError):
            VerificationStep(
                order=0,
                command="python --version",
                expected_output="Python 3.11",
            )


class TestFixBundleCreate:
    """Tests for FixBundleCreate model."""

    def test_valid_fix_bundle_create(self) -> None:
        """Test creating a valid fix bundle."""
        bundle = FixBundleCreate(
            env_actions=[
                EnvAction(
                    order=1,
                    type=EnvActionType.UPGRADE,
                    command="pip install langchain-core>=0.2.0",
                    explanation="Install langchain-core with new tool decorator",
                )
            ],
            constraints=Constraints(
                working_versions={"langchain-core": ">=0.2.0"}
            ),
            verification=[
                VerificationStep(
                    order=1,
                    command="python -c \"from langchain_core.tools import tool\"",
                    expected_output="No output (successful import)",
                )
            ],
        )
        assert len(bundle.env_actions) == 1
        assert len(bundle.verification) == 1

    def test_env_actions_order_validation(self) -> None:
        """Test that env_actions must have sequential order starting at 1."""
        with pytest.raises(ValidationError) as exc_info:
            FixBundleCreate(
                env_actions=[
                    EnvAction(
                        order=2,
                        type=EnvActionType.INSTALL,
                        command="pip install pkg1",
                        explanation="Install first package",
                    ),
                    EnvAction(
                        order=3,
                        type=EnvActionType.INSTALL,
                        command="pip install pkg2",
                        explanation="Install second package",
                    ),
                ],
                verification=[
                    VerificationStep(
                        order=1,
                        command="test",
                        expected_output="ok",
                    )
                ],
            )
        assert "sequential order" in str(exc_info.value)

    def test_verification_order_validation(self) -> None:
        """Test that verification must have sequential order starting at 1."""
        with pytest.raises(ValidationError) as exc_info:
            FixBundleCreate(
                env_actions=[
                    EnvAction(
                        order=1,
                        type=EnvActionType.INSTALL,
                        command="pip install pkg",
                        explanation="Install package",
                    )
                ],
                verification=[
                    VerificationStep(
                        order=2,
                        command="test1",
                        expected_output="ok1",
                    ),
                    VerificationStep(
                        order=4,
                        command="test2",
                        expected_output="ok2",
                    ),
                ],
            )
        assert "sequential order" in str(exc_info.value)

    def test_multiple_actions_correct_order(self) -> None:
        """Test fix bundle with multiple actions in correct order."""
        bundle = FixBundleCreate(
            env_actions=[
                EnvAction(
                    order=1,
                    type=EnvActionType.INSTALL,
                    command="pip install pkg1",
                    explanation="Install first package",
                ),
                EnvAction(
                    order=2,
                    type=EnvActionType.CONFIG,
                    command="export VAR=value",
                    explanation="Set environment variable",
                ),
                EnvAction(
                    order=3,
                    type=EnvActionType.COMMAND,
                    command="python setup.py",
                    explanation="Run setup script",
                ),
            ],
            verification=[
                VerificationStep(
                    order=1,
                    command="python -c 'import pkg1'",
                    expected_output="No output (successful import)",
                ),
                VerificationStep(
                    order=2,
                    command="echo $VAR",
                    expected_output="value",
                ),
            ],
        )
        assert len(bundle.env_actions) == 3
        assert len(bundle.verification) == 2

    def test_optional_fields(self) -> None:
        """Test that patch_diff and code_fix are optional."""
        bundle = FixBundleCreate(
            env_actions=[
                EnvAction(
                    order=1,
                    type=EnvActionType.INSTALL,
                    command="pip install pkg",
                    explanation="Install package",
                )
            ],
            verification=[
                VerificationStep(
                    order=1,
                    command="test",
                    expected_output="ok",
                )
            ],
        )
        assert bundle.patch_diff is None
        assert bundle.code_fix is None

    def test_with_code_fix(self) -> None:
        """Test fix bundle with code fix."""
        bundle = FixBundleCreate(
            env_actions=[
                EnvAction(
                    order=1,
                    type=EnvActionType.UPGRADE,
                    command="pip install langchain-core",
                    explanation="Install langchain-core",
                )
            ],
            verification=[
                VerificationStep(
                    order=1,
                    command="python test.py",
                    expected_output="OK",
                )
            ],
            code_fix="from langchain_core.tools import tool",
        )
        assert bundle.code_fix == "from langchain_core.tools import tool"


class TestFixBundleResponse:
    """Tests for FixBundleResponse model."""

    def test_valid_fix_bundle_response(self) -> None:
        """Test creating a valid fix bundle response."""
        response = FixBundleResponse(
            id=uuid4(),
            master_issue_id=uuid4(),
            version=1,
            is_current=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            env_actions=[
                EnvAction(
                    order=1,
                    type=EnvActionType.INSTALL,
                    command="pip install pkg",
                    explanation="Install package",
                )
            ],
            verification=[
                VerificationStep(
                    order=1,
                    command="test",
                    expected_output="ok",
                )
            ],
        )
        assert response.version == 1
        assert response.is_current is True


class TestEnvActionType:
    """Tests for EnvActionType enum."""

    def test_all_action_types(self) -> None:
        """Test all env action types have correct values."""
        assert EnvActionType.INSTALL.value == "install"
        assert EnvActionType.UPGRADE.value == "upgrade"
        assert EnvActionType.DOWNGRADE.value == "downgrade"
        assert EnvActionType.CONFIG.value == "config"
        assert EnvActionType.FLAG.value == "flag"
        assert EnvActionType.COMMAND.value == "command"
