import uvicorn
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
import json
import os

# Import game logic
from core.game_manager import game_manager
from core.game import Game
from core.game import Game
from core.items import ITEMS
from core.game_config import config

app = FastAPI(title="Buckshot Roulette Dashboard")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# --- Pydantic Models ---
class CustomSettings(BaseModel):
    shell_counts: Optional[dict] = None # {'live': int, 'blank': int}
    items_per_round: Optional[int] = None
    item_probabilities: Optional[dict] = None
    total_shells: Optional[int] = None
    live_ratio: Optional[float] = None # 0.0 to 1.0

class CreateGameRequest(BaseModel):
    player_ids: List[int]
    custom_settings: Optional[CustomSettings] = None

class ActionRequest(BaseModel):
    action: str # 'shoot', 'use'
    target_id: Optional[int] = None
    item_name: Optional[str] = None

class MessageRequest(BaseModel):
    message: str

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main Dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/game/{game_id}", response_class=HTMLResponse)
async def game_control_panel(request: Request, game_id: str):
    """Game Control Panel UI"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return templates.TemplateResponse("game_control.html", {"request": request, "game_id": game_id})

@app.get("/game/{game_id}/player/{player_id}", response_class=HTMLResponse)
async def player_view_ui(request: Request, game_id: str, player_id: int):
    """Player View UI"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return templates.TemplateResponse("player_view.html", {"request": request, "game_id": game_id, "player_id": player_id})

# --- API Endpoints ---

@app.get("/api/games")
async def get_games():
    """List all active games"""
    games = []
    for gid, game in game_manager.games.items():
        # Calculate shell counts
        live_shells = game.shotgun.chamber.count("live")
        blank_shells = game.shotgun.chamber.count("blank")
        
        # Get player stats
        player_stats = []
        for p in game.players:
            player_stats.append({
                "id": p.id,
                "lives": p.lives,
            })
            try:
                player_stats[-1]["max_lives"] = p.max_lives
            except AttributeError:
                print(f"DEBUG: Player object {p} missing max_lives. Dir: {dir(p)}")
                player_stats[-1]["max_lives"] = 999 # Fallback

        games.append({
            "id": gid,
            "round": game.round_number,
            "players": len(game.players),
            "is_over": game.is_game_over(),
            "is_terminated": game.is_terminated,
            "shell_counts": {"live": live_shells, "blank": blank_shells},
            "current_turn": game.current_player_index + 1 if game.players else 0,
            "player_stats": player_stats
        })
    return {"games": games}

@app.post("/api/game/create")
async def create_game(request: CreateGameRequest):
    """Create a new game session with optional custom settings"""
    try:
        settings_dict = request.custom_settings.dict() if request.custom_settings else None
        # Remove None values to let logic.py handle defaults
        if settings_dict:
            settings_dict = {k: v for k, v in settings_dict.items() if v is not None}
            
        game_id = game_manager.create_game(request.player_ids, settings_dict)
        
        # Start the first round immediately for convenience
        game = game_manager.get_game(game_id)
        if game:
            game.start_new_round()
        return {"game_id": game_id, "message": "Game created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/game/{game_id}/state")
async def get_game_state(game_id: str):
    """Get current game state JSON"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.get_state()

@app.post("/api/game/{game_id}/action")
async def execute_action(game_id: str, action: ActionRequest):
    """Execute a player action (Shoot or Use Item)"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.is_game_over():
         return {"success": False, "message": "Game is over"}

    action_data = {
        "action": action.action,
        "target_id": action.target_id,
        "item_name": action.item_name
    }
    
    try:
        game.handle_action(action_data)
        return {"success": True, "message": "Action executed", "state": game.get_state()}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/game/{game_id}/terminate")
async def terminate_game(game_id: str):
    """Force terminate the game"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    game.force_end()
    return {"success": True, "message": "Game terminated"}

@app.post("/api/game/{game_id}/message")
async def send_message(game_id: str, req: MessageRequest):
    """Send admin message to players"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    game.broadcast_message(req.message)
    return {"success": True, "message": "Message sent"}

@app.post("/api/game/{game_id}/undo")
async def undo_game(game_id: str):
    """Undo the last action"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.undo():
        return {"success": True, "message": "Undo successful", "state": game.get_state()}
    else:
        return {"success": False, "message": "Nothing to undo"}

@app.get("/api/game/{game_id}/logs")
async def get_game_logs(game_id: str):
    """Get full game logs"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"logs": game.logs}

@app.post("/api/game/{game_id}/reset")
async def reset_game(game_id: str):
    """Reset the game (Not fully implemented in Game class, so we might just restart round or create new)"""
    # For now, let's just start a new round as a "soft reset" or re-create logic
    # Since Game class doesn't have a full reset, we will just start a new round 1
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game.round_number = 0
    game.round_number = 0
    for p in game.players:
        p.lives = config.rules.get('initial_lives', 3)
        p.items = []
        p.skip_turns = 0
    
    game.start_new_round()
    return {"success": True, "message": "Game reset", "state": game.get_state()}

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    print("Starting Web Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
