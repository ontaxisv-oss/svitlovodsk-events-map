import json
import os
import math
import time
from datetime import datetime

import config

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
DISTRICTS_FILE = os.path.join(DATA_DIR, "districts.json")

def load_districts():
    _ensure_dir()
    if not os.path.exists(DISTRICTS_FILE):
        return []
    try:
        with open(DISTRICTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading districts: {e}")
        return []

def save_districts(districts):
    _ensure_dir()
    with open(DISTRICTS_FILE, "w", encoding="utf-8") as f:
        json.dump(districts, f, ensure_ascii=False, indent=2)

# Маршрути (відключено)
SVITLOVODSK_ROUTES = []

# Начальні події Світловодська
INITIAL_EVENTS = []

def _ensure_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def init_db():
    _ensure_dir()
    if not os.path.exists(EVENTS_FILE):
        save_events(INITIAL_EVENTS)

def load_events():
    _ensure_dir()
    if not os.path.exists(EVENTS_FILE):
        save_events(INITIAL_EVENTS)
        return INITIAL_EVENTS
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading events: {e}")
        return INITIAL_EVENTS

def save_events(events):
    _ensure_dir()
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def get_active_events(ttl_filter_hours=None):
    events = load_events()
    now = int(time.time())
    active = []

    for ev in events:
        # Перевірка на прострочення (TTL)
        if ev.get("expires_at", 0) <= now:
            continue
        
        # Перевірка на антирейтинг (якщо багато голосів "Не погодитися")
        if ev.get("downvotes", 0) - ev.get("upvotes", 0) >= 3:
            continue

        # Якщо користувач задав фільтр відображення часу (наприклад, тільки події молодші N годин)
        if ttl_filter_hours and isinstance(ttl_filter_hours, (int, float)):
            age_seconds = now - ev.get("created_at", now)
            if age_seconds > ttl_filter_hours * 3600:
                continue

        # Обчислити залишок хвилин до зникання
        remaining_sec = ev.get("expires_at", 0) - now
        ev["remaining_minutes"] = max(1, math.ceil(remaining_sec / 60))
        active.append(ev)

    return active

def add_event(status, title, description, lat, lng, author_name="Анонім", author_id=0, custom_ttl_hours=4):
    events = load_events()
    now = int(time.time())
    ttl_seconds = int(custom_ttl_hours * 3600)
    
    new_id = f"ev_{int(now * 1000)}"
    new_event = {
        "id": new_id,
        "status": status,  # "green" | "red" | "yellow"
        "title": title,
        "description": description,
        "lat": float(lat),
        "lng": float(lng),
        "created_at": now,
        "expires_at": now + ttl_seconds,
        "author_name": author_name,
        "author_id": author_id,
        "upvotes": 1,
        "downvotes": 0,
        "voted_users": {str(author_id): "up"}
    }
    
    events.append(new_event)
    save_events(events)
    return new_event

def vote_event(event_id, user_id, vote_type):
    events = load_events()
    now = int(time.time())
    user_str = str(user_id)

    for ev in events:
        if ev.get("id") == event_id:
            voted = ev.setdefault("voted_users", {})
            prev_vote = voted.get(user_str)

            if prev_vote == vote_type:
                # Користувач уже голосував так само
                return {"success": False, "message": "Ви вже проголосували за цю подію", "event": ev}

            # Скасувати попередній голос якщо був
            if prev_vote == "up":
                ev["upvotes"] = max(0, ev["upvotes"] - 1)
                ev["expires_at"] -= config.UPVOTE_EXTEND_MINUTES * 60
            elif prev_vote == "down":
                ev["downvotes"] = max(0, ev["downvotes"] - 1)
                ev["expires_at"] += config.DOWNVOTE_REDUCE_MINUTES * 60

            # Застосувати новий голос
            if vote_type == "up":
                ev["upvotes"] += 1
                ev["expires_at"] += config.UPVOTE_EXTEND_MINUTES * 60
                voted[user_str] = "up"
            elif vote_type == "down":
                ev["downvotes"] += 1
                ev["expires_at"] -= config.DOWNVOTE_REDUCE_MINUTES * 60
                voted[user_str] = "down"

            # Оновити залишок хвилин
            remaining_sec = max(0, ev["expires_at"] - now)
            ev["remaining_minutes"] = math.ceil(remaining_sec / 60)

            save_events(events)
            return {"success": True, "event": ev}

    return {"success": False, "message": "Подію не знайдено"}

def get_routes():
    return SVITLOVODSK_ROUTES
