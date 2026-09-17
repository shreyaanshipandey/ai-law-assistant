"""
One-off script to create the first admin account.
Run after the DB tables exist (they're auto-created on app startup):

    python seed_admin.py
"""
import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == settings.FIRST_ADMIN_EMAIL))
        if existing.scalar_one_or_none():
            print(f"Admin '{settings.FIRST_ADMIN_EMAIL}' already exists. Skipping.")
            return

        admin = User(
            full_name="System Administrator",
            email=settings.FIRST_ADMIN_EMAIL,
            hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        await db.commit()
        print(f"Admin created: {settings.FIRST_ADMIN_EMAIL} / {settings.FIRST_ADMIN_PASSWORD}")
        print("IMPORTANT: change this password immediately after first login.")


if __name__ == "__main__":
    asyncio.run(main())
