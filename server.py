import json
import os
import sys
from aiohttp import web

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import config
import database

routes = web.RouteTableDef()
bot_instance = None

def set_bot_instance(bot):
    global bot_instance
    bot_instance = bot

@routes.get('/')
async def index_handler(request):
    public_dir = os.path.join(os.path.dirname(__file__), "public")
    index_file = os.path.join(public_dir, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    return web.Response(text=html_content, content_type="text/html")

@routes.get('/api/config')
async def get_config(request):
    data = {
        "city_name": config.CITY_NAME,
        "country_name": config.COUNTRY_NAME,
        "city_center": {
            "lat": config.CITY_CENTER_LAT,
            "lng": config.CITY_CENTER_LNG
        },
        "default_zoom": config.DEFAULT_ZOOM,
        "statuses": config.STATUSES,
        "source_channel": config.SOURCE_CHANNEL
    }
    return web.json_response(data)

@routes.get('/api/events')
async def get_events(request):
    ttl_filter = request.query.get('ttl_filter')
    try:
        ttl_hours = float(ttl_filter) if ttl_filter else None
    except ValueError:
        ttl_hours = None

    events = database.get_active_events(ttl_filter_hours=ttl_hours)
    return web.json_response({"events": events})

@routes.post('/api/events/add')
async def add_event(request):
    try:
        data = await request.json()
        status = data.get("status")
        title = data.get("title")
        description = data.get("description", "")
        lat = data.get("lat")
        lng = data.get("lng")
        author_name = data.get("author_name", "Користувач")
        author_id = data.get("author_id", 0)
        custom_ttl_hours = data.get("custom_ttl_hours", 4)

        if not status or not title or lat is None or lng is None:
            return web.json_response({"success": False, "error": "Заповніть усі обов'язкові поля"}, status=400)

        new_ev = database.add_event(
            status=status,
            title=title,
            description=description,
            lat=lat,
            lng=lng,
            author_name=author_name,
            author_id=author_id,
            custom_ttl_hours=custom_ttl_hours
        )

        return web.json_response({"success": True, "event": new_ev})
    except Exception as e:
        print(f"Error adding event: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

@routes.post('/api/events/vote')
async def vote_event(request):
    try:
        data = await request.json()
        event_id = data.get("event_id")
        user_id = data.get("user_id", 0)
        vote_type = data.get("vote_type")  # "up" or "down"

        if not event_id or not vote_type:
            return web.json_response({"success": False, "error": "Некоректні дані голосування"}, status=400)

        res = database.vote_event(event_id, user_id, vote_type)
        return web.json_response(res)
    except Exception as e:
        print(f"Error voting event: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

@routes.get('/api/districts')
async def get_districts(request):
    districts = database.load_districts()
    return web.json_response({"districts": districts})

@routes.post('/api/districts')
async def update_districts(request):
    try:
        data = await request.json()
        districts = data.get("districts", [])
        database.save_districts(districts)
        return web.json_response({"success": True, "districts": districts})
    except Exception as e:
        print(f"Error updating districts: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

@routes.get('/api/routes')
async def get_routes(request):
    route_data = database.get_routes()
    return web.json_response({"routes": route_data})

@web.middleware
async def cors_middleware(request, handler):
    if request.method == 'OPTIONS':
        response = web.Response()
    else:
        response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

def create_app():
    app = web.Application(middlewares=[cors_middleware])
    app.add_routes(routes)
    
    public_dir = os.path.join(os.path.dirname(__file__), "public")
    app.router.add_static('/', public_dir, show_index=True)
    return app

if __name__ == "__main__":
    database.init_db()
    app = create_app()
    print(f"🚀 Запуск сервера «Карта Подій» Світловодськ на http://{config.WEB_SERVER_HOST}:{config.WEB_SERVER_PORT}")
    web.run_app(app, host=config.WEB_SERVER_HOST, port=config.WEB_SERVER_PORT)
