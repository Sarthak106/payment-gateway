from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog


async def log_audit(session: AsyncSession, actor: str, action: str, details: str | None = None) -> None:
    entry = AuditLog(actor=actor, action=action, details=details)
    session.add(entry)
    await session.flush()
