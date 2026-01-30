"""GIM ID service for identity management.

This module handles CRUD operations for GIM identities stored in Supabase.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from src.auth.models import (
    GIMIdentity,
    GIMIdentityCreate,
    GIMIdentityResponse,
    GIMIdentityStatus,
)
from src.config import get_settings
from src.db.supabase_client import (
    get_record,
    get_supabase_client,
    insert_record,
    query_records,
    update_record,
)

logger = logging.getLogger(__name__)

TABLE_NAME = "gim_identities"


class GIMIdService:
    """Service for managing GIM identities.

    Handles creation, validation, and revocation of GIM IDs.
    """

    async def create_identity(
        self,
        request: Optional[GIMIdentityCreate] = None,
    ) -> GIMIdentityResponse:
        """Create a new GIM identity.

        Args:
            request: Optional creation request with description/metadata.

        Returns:
            GIMIdentityResponse: The created identity details.
        """
        settings = get_settings()

        data: dict[str, Any] = {
            "daily_search_limit": settings.default_daily_search_limit,
        }

        if request:
            if request.description:
                data["description"] = request.description
            if request.metadata:
                data["metadata"] = request.metadata

        record = await insert_record(TABLE_NAME, data)

        logger.info("Created new GIM identity")

        return GIMIdentityResponse(
            gim_id=UUID(record["gim_id"]),
            created_at=datetime.fromisoformat(record["created_at"]),
            description=record.get("description"),
        )

    async def get_identity_by_gim_id(
        self,
        gim_id: UUID,
    ) -> Optional[GIMIdentity]:
        """Get identity by GIM ID.

        Args:
            gim_id: The GIM ID to look up.

        Returns:
            GIMIdentity: The identity if found, None otherwise.
        """
        record = await get_record(TABLE_NAME, str(gim_id), id_column="gim_id")
        if record:
            return self._record_to_identity(record)
        return None

    async def get_identity_by_id(
        self,
        identity_id: UUID,
    ) -> Optional[GIMIdentity]:
        """Get identity by internal ID.

        Args:
            identity_id: The internal identity ID.

        Returns:
            GIMIdentity: The identity if found, None otherwise.
        """
        record = await get_record(TABLE_NAME, str(identity_id))
        if record:
            return self._record_to_identity(record)
        return None

    async def validate_gim_id(
        self,
        gim_id: UUID,
    ) -> Optional[GIMIdentity]:
        """Validate a GIM ID and return identity if active.

        Args:
            gim_id: The GIM ID to validate.

        Returns:
            GIMIdentity: The identity if valid and active, None otherwise.
        """
        identity = await self.get_identity_by_gim_id(gim_id)

        if identity is None:
            logger.warning("GIM ID not found")
            return None

        if identity.status != GIMIdentityStatus.ACTIVE:
            logger.warning(f"GIM ID not active (status={identity.status})")
            return None

        return identity

    async def update_last_used(
        self,
        identity_id: UUID,
    ) -> None:
        """Update the last_used_at timestamp.

        Args:
            identity_id: The identity ID to update.
        """
        await update_record(
            TABLE_NAME,
            str(identity_id),
            {"last_used_at": datetime.now(timezone.utc).isoformat()},
        )

    async def revoke_identity(
        self,
        gim_id: UUID,
    ) -> bool:
        """Revoke a GIM identity.

        Args:
            gim_id: The GIM ID to revoke.

        Returns:
            bool: True if revoked, False if not found.
        """
        identity = await self.get_identity_by_gim_id(gim_id)
        if identity is None:
            return False

        await update_record(
            TABLE_NAME,
            str(identity.id),
            {"status": GIMIdentityStatus.REVOKED.value},
        )

        logger.info("Revoked GIM identity")
        return True

    async def suspend_identity(
        self,
        gim_id: UUID,
    ) -> bool:
        """Suspend a GIM identity.

        Args:
            gim_id: The GIM ID to suspend.

        Returns:
            bool: True if suspended, False if not found.
        """
        identity = await self.get_identity_by_gim_id(gim_id)
        if identity is None:
            return False

        await update_record(
            TABLE_NAME,
            str(identity.id),
            {"status": GIMIdentityStatus.SUSPENDED.value},
        )

        logger.info("Suspended GIM identity")
        return True

    async def reactivate_identity(
        self,
        gim_id: UUID,
    ) -> bool:
        """Reactivate a suspended GIM identity.

        Args:
            gim_id: The GIM ID to reactivate.

        Returns:
            bool: True if reactivated, False if not found or not suspended.
        """
        identity = await self.get_identity_by_gim_id(gim_id)
        if identity is None:
            return False

        if identity.status != GIMIdentityStatus.SUSPENDED:
            logger.warning(f"Cannot reactivate: identity is {identity.status}")
            return False

        await update_record(
            TABLE_NAME,
            str(identity.id),
            {"status": GIMIdentityStatus.ACTIVE.value},
        )

        logger.info("Reactivated GIM identity")
        return True

    # Whitelist of stat fields that can be incremented
    ALLOWED_STAT_FIELDS: frozenset[str] = frozenset({
        "total_searches",
        "total_submissions",
        "total_confirmations",
        "total_reports",
    })

    async def increment_stat(
        self,
        identity_id: UUID,
        stat_field: str,
    ) -> None:
        """Increment a lifetime stat field.

        Args:
            identity_id: The identity ID.
            stat_field: The stat field to increment (total_searches, etc.).

        Raises:
            ValueError: If stat_field is not in the allowed whitelist.
        """
        if stat_field not in self.ALLOWED_STAT_FIELDS:
            raise ValueError(f"Invalid stat field: {stat_field}")

        # Get current value and increment
        identity = await self.get_identity_by_id(identity_id)
        if identity:
            current_value = getattr(identity, stat_field, 0)
            await update_record(
                TABLE_NAME,
                str(identity_id),
                {stat_field: current_value + 1},
            )

    async def list_identities(
        self,
        status: Optional[GIMIdentityStatus] = None,
        limit: int = 100,
    ) -> list[GIMIdentity]:
        """List GIM identities.

        Args:
            status: Optional status filter.
            limit: Maximum number of identities to return.

        Returns:
            list[GIMIdentity]: List of identities.
        """
        filters = {}
        if status:
            filters["status"] = status.value

        records = await query_records(
            TABLE_NAME,
            filters=filters if filters else None,
            limit=limit,
            order_by="created_at",
            ascending=False,
        )

        return [self._record_to_identity(r) for r in records]

    def _record_to_identity(self, record: dict[str, Any]) -> GIMIdentity:
        """Convert database record to GIMIdentity model.

        Args:
            record: Database record.

        Returns:
            GIMIdentity: The identity model.
        """
        return GIMIdentity(
            id=UUID(record["id"]),
            gim_id=UUID(record["gim_id"]),
            created_at=datetime.fromisoformat(record["created_at"]),
            last_used_at=(
                datetime.fromisoformat(record["last_used_at"])
                if record.get("last_used_at")
                else None
            ),
            status=GIMIdentityStatus(record["status"]),
            daily_search_limit=record.get("daily_search_limit", 100),
            daily_search_used=record.get("daily_search_used", 0),
            daily_reset_at=(
                datetime.fromisoformat(record["daily_reset_at"])
                if record.get("daily_reset_at")
                else None
            ),
            total_searches=record.get("total_searches", 0),
            total_submissions=record.get("total_submissions", 0),
            total_confirmations=record.get("total_confirmations", 0),
            total_reports=record.get("total_reports", 0),
            description=record.get("description"),
            metadata=record.get("metadata", {}),
        )


# Module-level singleton
_gim_id_service: Optional[GIMIdService] = None


def get_gim_id_service() -> GIMIdService:
    """Get GIM ID service singleton.

    Returns:
        GIMIdService: The GIM ID service instance.
    """
    global _gim_id_service
    if _gim_id_service is None:
        _gim_id_service = GIMIdService()
    return _gim_id_service
