import json
from memory.structured.models import UserProfile, get_session


async def get_profile(user_id: str = "default") -> dict:
    session = get_session()
    profile = session.query(UserProfile).filter_by(id=user_id).first()
    if not profile:
        session.close()
        return {
            "preferred_tone": "professional",
            "target_audience": "general",
            "language": "en",
            "taboo_topics": [],
            "style_preferences": {},
        }
    result = {
        "preferred_tone": profile.preferred_tone,
        "target_audience": profile.target_audience,
        "language": profile.language,
        "taboo_topics": json.loads(profile.taboo_topics or "[]"),
        "style_preferences": json.loads(profile.style_preferences or "{}"),
    }
    session.close()
    return result


async def update_profile(user_id: str = "default", **kwargs):
    session = get_session()
    profile = session.query(UserProfile).filter_by(id=user_id).first()
    if not profile:
        profile = UserProfile(id=user_id)
        session.add(profile)

    for key, value in kwargs.items():
        if hasattr(profile, key):
            if key in ("taboo_topics", "style_preferences"):
                value = json.dumps(value, ensure_ascii=False)
            setattr(profile, key, value)

    session.commit()
    session.close()
