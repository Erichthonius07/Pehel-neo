from fastapi import APIRouter
from app.api.v1.endpoints import auth, issues, geo, feed, authority, chat, admin, comments

router = APIRouter()

router.include_router(auth.router)
router.include_router(issues.router)
router.include_router(comments.router)
router.include_router(geo.router)
router.include_router(feed.router)
router.include_router(authority.router)
router.include_router(chat.router)
router.include_router(admin.router)
