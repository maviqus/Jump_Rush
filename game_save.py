#  filename: game_save.py
#  Persistent save system for game progress

import json
import os

SAVE_FILE = "game_save.json"

def load_game_data():
    """Load saved game data or return defaults"""
    default_data = {
        "player_name": "Player",
        "total_coins": 0,
        "unlocked_avatars": ["avatar.png", "Blue Lightning.png", "Clown.png", "Green Eye.png"],  # Default avatars always unlocked
        "completed_levels": [],
        "best_times": {},
        "selected_avatar": "avatar.png",
        "high_scores": {
            "coins": [],
            "times": {}
        }
    }
    
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                # Ensure all required keys exist
                for key, value in default_data.items():
                    if key not in data:
                        data[key] = value
                return data
        else:
            return default_data
    except Exception as e:
        print(f"Error loading save data: {e}")
        return default_data

def save_game_data(data):
    """Save game data to file"""
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving game data: {e}")
        return False

def add_coins(amount):
    """Add coins and check for avatar unlocks"""
    data = load_game_data()
    old_coins = data["total_coins"]
    data["total_coins"] += amount
    
    # Check for avatar unlock at 15 coins
    unlocked_avatar = None
    if old_coins < 15 and data["total_coins"] >= 15:
        unlocked_avatar = unlock_random_avatar(data)
    
    save_game_data(data)
    data["new_unlock"] = unlocked_avatar  # Add this info to returned data
    return data

def unlock_random_avatar(data):
    """Unlock a random avatar from available avatars"""
    import random
    
    # Get all available avatar files
    avatar_dir = os.path.join("images", "avatar")
    all_avatars = []
    
    if os.path.isdir(avatar_dir):
        for fn in os.listdir(avatar_dir):
            if fn.lower().endswith(('.png', '.jpg', '.jpeg')):
                all_avatars.append(fn)
    
    # Find avatars not yet unlocked
    locked_avatars = [av for av in all_avatars if av not in data["unlocked_avatars"]]
    
    if locked_avatars:
        # Unlock a random avatar
        new_avatar = random.choice(locked_avatars)
        data["unlocked_avatars"].append(new_avatar)
        return new_avatar
    
    return None

def complete_level(level_num, time_taken):
    """Mark a level as completed and update high scores."""
    data = load_game_data()
    if level_num not in data["completed_levels"]:
        data["completed_levels"].append(level_num)
    
    update_high_scores(data, level_num, time_taken)
    save_game_data(data)
    return data

def update_high_scores(data, level_num, time_taken):
    """Update high scores for coins and times."""
    player_name = data.get("player_name", "Player")
    total_coins = data.get("total_coins", 0)

    # Update coin high scores
    coin_scores = data["high_scores"]["coins"]
    player_coin_score = next((score for score in coin_scores if score["name"] == player_name), None)
    if player_coin_score:
        player_coin_score["coins"] = total_coins
    else:
        coin_scores.append({"name": player_name, "coins": total_coins})
    data["high_scores"]["coins"] = sorted(coin_scores, key=lambda x: x["coins"], reverse=True)[:10]

    # Update time high scores
    level_str = str(level_num)
    if level_str not in data["high_scores"]["times"]:
        data["high_scores"]["times"][level_str] = []
    
    time_scores = data["high_scores"]["times"][level_str]
    player_time_score = next((score for score in time_scores if score["name"] == player_name), None)
    if player_time_score:
        if time_taken < player_time_score["time"]:
            player_time_score["time"] = time_taken
    else:
        time_scores.append({"name": player_name, "time": time_taken})
    data["high_scores"]["times"][level_str] = sorted(time_scores, key=lambda x: x["time"])[:10]

def get_unlocked_avatars():
    """Get list of unlocked avatar filenames"""
    data = load_game_data()
    return data["unlocked_avatars"]

def get_total_coins():
    """Get total coins collected"""
    data = load_game_data()
    return data["total_coins"]

def is_level_unlocked(level_num):
    """Check if a level is unlocked (1-indexed)"""
    if level_num <= 1:
        return True  # Level 1 is always unlocked
    
    data = load_game_data()
    # Level N is unlocked if level N-1 is completed
    return (level_num - 1) in data["completed_levels"]

def get_selected_avatar():
    """Get currently selected avatar filename"""
    data = load_game_data()
    selected = data.get("selected_avatar")
    if selected and selected in data["unlocked_avatars"]:
        return selected
    # Default to first unlocked avatar
    return data["unlocked_avatars"][0] if data["unlocked_avatars"] else "avatar.png"

def set_best_time(level_num, time_taken):
    """Set the best time for a level if it's better than current"""
    data = load_game_data()
    if 'best_times' not in data:
        data['best_times'] = {}
    key = str(level_num)
    current = data['best_times'].get(key)
    if current is None or time_taken < current:
        data['best_times'][key] = time_taken
        save_game_data(data)

def get_best_times():
    """Get best times for all levels"""
    data = load_game_data()
    return data.get('best_times', {})
