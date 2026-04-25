import os
from pathlib import Path
from datetime import date, timedelta

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, SessionLocal
from models import Game


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


def load_rawg_key():
    key = os.getenv("RAWG_API_KEY")
    if key:
        return key.strip()

    if ENV_PATH.exists():
        for encoding in ["utf-8", "utf-8-sig", "cp949", "utf-16"]:
            try:
                content = ENV_PATH.read_text(encoding=encoding)

                for line in content.splitlines():
                    line = line.strip()

                    if not line:
                        continue

                    if line.startswith("RAWG_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")

                    if "=" not in line:
                        return line.strip().strip('"').strip("'")

            except Exception:
                continue

    return None

def load_admin_sync_key():
    key = os.getenv("ADMIN_SYNC_KEY")
    if key:
        return key.strip()

    if ENV_PATH.exists():
        for encoding in ["utf-8", "utf-8-sig", "cp949", "utf-16"]:
            try:
                content = ENV_PATH.read_text(encoding=encoding)

                for line in content.splitlines():
                    line = line.strip()

                    if line.startswith("ADMIN_SYNC_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")

            except Exception:
                continue

    return None

RAWG_API_KEY = load_rawg_key()
ADMIN_SYNC_KEY = load_admin_sync_key()
RAWG_BASE_URL = "https://api.rawg.io/api"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Game Release Calendar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def game_to_dict(game):
    return {
        "id": game.rawg_id,
        "title": game.title,
        "platforms": game.platforms.split("|") if game.platforms else [],
        "release_date": game.release_date,
        "genre": game.genre,
        "status": game.status,
        "description": game.description,
        "image": game.image,
    }


@app.get("/")
def home():
    return {"message": "게임 출시일 앱 백엔드 실행 성공!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/debug/env")
def debug_env():
    return {
        "env_file_path": str(ENV_PATH),
        "env_file_exists": ENV_PATH.exists(),
        "rawg_key_loaded": bool(RAWG_API_KEY),
        "key_length": len(RAWG_API_KEY) if RAWG_API_KEY else 0,
        "admin_sync_key_loaded": bool(ADMIN_SYNC_KEY),
    }


@app.post("/games/sync")
async def sync_games_from_rawg(x_admin_key: str | None = Header(default=None)):
    if not ADMIN_SYNC_KEY:
        raise HTTPException(status_code=500, detail="관리자 키가 설정되지 않았습니다.")

    if x_admin_key != ADMIN_SYNC_KEY:
        raise HTTPException(status_code=403, detail="관리자 권한이 없습니다.")

    if not RAWG_API_KEY:
        return {"error": "RAWG_API_KEY가 설정되지 않았습니다."}

    today = date.today()
    one_year_later = today + timedelta(days=365)

    params = {
        "key": RAWG_API_KEY,
        "dates": f"{today},{one_year_later}",
        "ordering": "released",
        "page_size": 40,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{RAWG_BASE_URL}/games", params=params)

    if response.status_code != 200:
        return {
            "error": "RAWG API 요청 실패",
            "status_code": response.status_code,
            "detail": response.text,
        }

    data = response.json()
    db = SessionLocal()

    saved_count = 0
    updated_count = 0

    try:
        for item in data.get("results", []):
            release_date = item.get("released")
            rawg_id = item.get("id")
            title = item.get("name")

            if not release_date or not rawg_id or not title:
                continue

            platforms = []
            for platform_info in item.get("platforms") or []:
                platform_name = platform_info.get("platform", {}).get("name")
                if platform_name:
                    platforms.append(platform_name)

            genres = []
            for genre in item.get("genres") or []:
                genre_name = genre.get("name")
                if genre_name:
                    genres.append(genre_name)

            existing_game = db.query(Game).filter(Game.rawg_id == rawg_id).first()

            if existing_game:
                existing_game.title = title
                existing_game.platforms = "|".join(platforms)
                existing_game.release_date = release_date
                existing_game.genre = ", ".join(genres) if genres else "Unknown"
                existing_game.status = "Coming Soon"
                existing_game.description = "RAWG API에서 가져온 게임 출시 예정 정보입니다."
                existing_game.image = item.get("background_image") or ""
                updated_count += 1
            else:
                new_game = Game(
                    rawg_id=rawg_id,
                    title=title,
                    platforms="|".join(platforms),
                    release_date=release_date,
                    genre=", ".join(genres) if genres else "Unknown",
                    status="Coming Soon",
                    description="RAWG API에서 가져온 게임 출시 예정 정보입니다.",
                    image=item.get("background_image") or "",
                )
                db.add(new_game)
                saved_count += 1

        db.commit()

        return {
            "message": "RAWG 게임 데이터 DB 저장 완료",
            "saved_count": saved_count,
            "updated_count": updated_count,
        }

    except Exception as e:
        db.rollback()
        return {"error": "DB 저장 중 오류", "detail": str(e)}

    finally:
        db.close()


@app.get("/games/upcoming")
def get_upcoming_games(platform: str | None = None):
    db = SessionLocal()

    try:
        query = db.query(Game).order_by(Game.release_date.asc())
        games = query.all()

        result = [game_to_dict(game) for game in games]

        if platform:
            result = [
                game
                for game in result
                if any(platform.lower() in p.lower() for p in game["platforms"])
            ]

        return {"games": result}

    finally:
        db.close()


@app.get("/games/search")
def search_games(query: str):
    db = SessionLocal()

    try:
        games = (
            db.query(Game)
            .filter(Game.title.ilike(f"%{query}%"))
            .order_by(Game.release_date.asc())
            .all()
        )

        return {"games": [game_to_dict(game) for game in games]}

    finally:
        db.close()