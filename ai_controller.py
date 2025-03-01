#!/usr/bin/env python3
"""
AI Controller Framework for Grok Plays Pokémon
This module provides a framework for multiple AIs to control the game.
"""

import time
import requests
import re
import json
import logging
import random
from abc import ABC, abstractmethod
import anthropic
import os
from prompts import get_vlm_user_prompt
from dotenv import load_dotenv
import base64
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:5000/api"


# Load environment variables from .env file
load_dotenv()

# Access the API key
claude_api_key = os.getenv("API_KEY")


class PokemonAI(ABC):
    """
    Abstract base class for AI controllers.
    Each AI implementation should extend this class.
    """
    
    def __init__(self, name):
        """Initialize the AI controller."""
        self.name = name
        self.game_state = {}
        self.screen_state = None
        self.screen_description = None
        self.previous_actions = []
        self.current_role = "player"  # "player" or "pokemon"
    
    @abstractmethod
    def decide_action(self, game_state, screen_state=None, role="player"):
        """
        Decide what action to take based on the current game state.
        
        Args:
            game_state: Current state of the game (Pokémon, items, location, etc.)
            screen_state: Optional screenshot or screen data
            role: Current role ("player" or "pokemon")
            
        Returns:
            action: The action to take (e.g., "a", "b", "up", etc.)
            commentary: Commentary about the decision
        """
        pass
    
    def update_state(self, game_state, screen_state=None):
        """Update the AI's knowledge of the game state."""
        self.game_state = game_state
        self.screen_state = screen_state
    
    def record_action(self, action):
        """Record an action taken by the AI."""
        self.previous_actions.append(action)
        # Keep only the last 20 actions
        if len(self.previous_actions) > 20:
            self.previous_actions.pop(0)
    
    def set_role(self, role):
        """Set the current role of the AI."""
        if role in ["player", "pokemon"]:
            self.current_role = role
        else:
            logger.warning(f"Invalid role: {role}. Must be 'player' or 'pokemon'.")

class GrokAI(PokemonAI):
    """
    Grok AI implementation for playing Pokémon.
    """
    
    def __init__(self):
        """Initialize the Grok AI."""
        super().__init__("Grok")
    
    def decide_action(self, game_state, screen_state=None, role="player"):
        """Grok's decision-making logic."""
        # This is a simplified placeholder for Grok's actual decision-making
        # In a real implementation, this would connect to Grok's API
        
        self.update_state(game_state, screen_state)
        
        # Different logic based on role
        if role == "player":
            return self._decide_player_action()
        elif role == "pokemon":
            return self._decide_pokemon_action()
        
    def _decide_player_action(self):
        """Decide actions for player movement and exploration."""
        location = self.game_state.get("location", "")
        # Starting the game
        if location == "PALLET TOWN" and not self.previous_actions:
            return "a", "Let's start our Pokémon adventure!"
        
        # Choose starter Pokémon
        if "SQUIRTLE" not in str(self.game_state) and len(self.previous_actions) < 15:
            # Try to navigate to and select Squirtle
            if random.random() < 0.5:
                return "a", "Exploring the options..."
            else:
                return random.choice(["up", "down", "left", "right"]), "Looking for Squirtle..."
        
        # Basic exploration logic
        if random.random() < 0.3:
            # Talk to NPCs or interact with objects
            return "a", "Let's see what this person has to say!"
        else:
            # Move around
            direction = random.choice(["up", "down", "left", "right"])
            return direction, f"Exploring in the {direction} direction."
    
    def _decide_pokemon_action(self):
        """Decide actions during Pokémon battles."""
        # Get current Pokémon info
        pokemon_team = self.game_state.get("pokemon_team", [])
        
        if not pokemon_team:
            return "a", "Let's see what happens next in this battle!"
        
        # Check if we should use an item
        current_pokemon = pokemon_team[0]
        hp_percent = current_pokemon.get("hp", 0) / current_pokemon.get("max_hp", 1)
        
        if hp_percent < 0.3:
            return "b", "Our Pokémon is low on health! Let's use a potion."
        
        # Choose a move based on simple type advantage (placeholder logic)
        return "a", "Using our strongest move! It should be super effective!"



class ClaudeAI(PokemonAI):
    """
    Claude AI implementation for playing Pokémon.
    """
    
    def __init__(self):
        """Initialize the Claude AI."""
        super().__init__("Claude")
        self.strategy = "balanced"  # balanced, aggressive, defensive
    
        self.client = anthropic.Anthropic(
            api_key=claude_api_key,
        )

    def is_base64(self, data):
        """Check if the given bytes are valid base64 encoded."""
        try:
            # Decode and re-encode to check validity
            decoded = base64.b64decode(data, validate=True)
            return base64.b64encode(decoded).strip() == data.strip()
        except (ValueError, TypeError):
            return False

    def process_image(self, image): 
        img_media = "image/png"
        img_data = base64.b64encode(image).decode("utf-8")
        return img_media, img_data

    def _vlm_call(self, user_prompt, image): 
        if type(image) != bytes:
            return None
        
        img_media, img_data = self.process_image(image) 
        # if not self.is_base64(img_data):
        #     return None

        model_id = 'claude-3-5-sonnet-20241022' 
        return self.client.messages.create(
            model=model_id,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": img_media,
                                "data": img_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ],
                }
            ],
        )

    def _llm_call(self,user_prompt, system_prompt=None ): 
        system_prompt = 'user' if not system_prompt else system_prompt
        res = ''
        with self.client.messages.stream(
            model="claude-3-7-sonnet-20250219",
            max_tokens=64000,
            thinking={
                "type": "enabled",
                "budget_tokens": 32000
            },
            messages=[
                {"role": system_prompt, "content": user_prompt}
            ]
        ) as stream: 
            for text in stream.text_stream:
                print(text, end="", flush=True)
                res += text 

        return res
        
    def decide_action(self, game_state, screen_state=None, role="player"):
        """Claude's decision-making logic."""
        # This is a simplified placeholder for Claude's actual decision-making
        # In a real implementation, this would connect to Claude's API
        
        self.update_state(game_state, screen_state)
        if screen_state:
            loc = self.game_state.get('location', '')
            coord = self.game_state.get('coordinates', '')
            vlm_user_prompt = get_vlm_user_prompt(loc, coord)
            vlm_out = self._vlm_call(vlm_user_prompt, screen_state)
            self.screen_description = vlm_out
            # logger.info('leecatherine: vlm output:', vlm_out)


        # VLM here to process screen_state
        
        # Different logic based on role
        if role == "player":
            return self._decide_player_action()
        elif role == "pokemon":
            return self._decide_pokemon_action()
    
  
    
    
    def _decide_player_action(self):
        """
        Advanced movement and exploration strategy using Claude 3.7 Sonnet reasoning.
        Makes context-aware decisions based on current game state, location, and goals.
        """
        # Gather all relevant game state information
        location = self.game_state.get("location", "Unknown")
        coordinates = self.game_state.get("coordinates", "")
        pokemon_team = self.game_state.get("pokemon_team", [])
        badges = self.game_state.get("badges", 0)
        money = self.game_state.get("money", 0)
        items = self.game_state.get("items", [])
        
        # Log complete game state for debugging
        logger.info(f'Game State: {json.dumps(self.game_state, indent=2)}')
        
        # Create context for the LLM
        context = self._build_game_context(location, coordinates, pokemon_team, badges, money, items)
        
        # Prepare action history for context
        action_history = self._format_action_history()
        
        # Generate prompt for the LLM
        prompt = f"""
        You are playing Pokémon Red. Based on the following game state, decide the next optimal action.
        
        CURRENT GAME STATE:
        {context}
        
        RECENT ACTIONS:
        {action_history}
        
        SCREEN DESCRIPTION:
        {self.screen_description if hasattr(self, 'screen_description') else 'No screen description available'}
        
        What should be the next action? Choose one: up, down, left, right, a, b, start, select.
        Provide your reasoning and then your final decision in the format:
        REASONING: [your strategic thinking]
        ACTION: [chosen action]
        """
        
        try:
            # Call the LLM with the prompt
            response = self._llm_call(user_prompt=prompt)
            
            logger.info(f'Reasoning raw output:', {response}) 

            # Parse the LLM response
            action, reasoning = self._parse_llm_response(response)
            
            # If we couldn't get a valid action from the LLM, fall back to basic exploration
            if not action:
                return self._fallback_exploration()
            
            return action, reasoning
        
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return self._fallback_exploration()

    def _build_game_context(self, location, coordinates, pokemon_team, badges, money, items):
        """Build a detailed context description for the LLM."""
        # Format Pokémon team information
        team_info = "None" if not pokemon_team else "\n".join([
            f"- {pokemon.get('name', 'UNKNOWN')} (Lv.{pokemon.get('level', '?')}) "
            f"HP: {pokemon.get('hp', '?')}/{pokemon.get('max_hp', '?')}"
            for pokemon in pokemon_team
        ])
        
        # Format item information
        items_info = "None" if not items else "\n".join([
            f"- {item.get('name', 'UNKNOWN')} x{item.get('count', 0)}"
            for item in items
        ])
        
        # Game progress indicators
        progress = f"Badges: {badges}/8"
        
        # Determine current game objectives based on location and progress
        objectives = self._determine_current_objectives(location, badges, pokemon_team)
        
        return f"""
        Location: {location}
        Coordinates: {coordinates}
        Money: ${money}
        Progress: {progress}
        
        Pokémon Team:
        {team_info}
        
        Items:
        {items_info}
        
        Current Objectives:
        {objectives}
        """

    def _determine_current_objectives(self, location, badges, pokemon_team):
        """Determine what the player should be trying to accomplish based on game state."""
        # Early game objectives
        if badges == 0:
            if "Pallet Town" in location and not pokemon_team:
                return "- Get your first Pokémon from Professor Oak's Lab\n- Begin your journey to become a Pokémon Master"
            elif "Pallet Town" in location and pokemon_team:
                return "- Head north to Route 1\n- Travel to Viridian City"
            elif "Route 1" in location:
                return "- Travel north to Viridian City\n- Train your starter Pokémon"
            elif "Viridian City" in location:
                return "- Visit the Pokémon Center to heal\n- Stock up on supplies\n- Head north to Viridian Forest"
            elif "Viridian Forest" in location:
                return "- Navigate through the forest\n- Catch Bug-type Pokémon\n- Reach Pewter City"
            elif "Pewter City" in location:
                return "- Challenge Brock at the Pewter Gym\n- Aim to earn your first badge"
    
        # Mid-game objectives based on badge count
        elif badges == 1:
            return "- Head east to Mt. Moon\n- Make your way to Cerulean City\n- Prepare to challenge Misty"
        elif badges == 2:
            return "- Explore east of Cerulean\n- Head south to Vermilion City\n- Prepare to battle Lt. Surge"
        
        # Late game progression
        elif badges >= 6:
            return "- Prepare for the Elite Four\n- Train your team to higher levels\n- Ensure balanced type coverage"
        
        # Default objectives
        return "- Explore the current area\n- Train your Pokémon\n- Find and challenge the next Gym Leader"

    def _format_action_history(self):
        """Format recent actions for context."""
        if not self.previous_actions:
            return "No previous actions recorded."
        
        # Take the last 10 actions
        recent_actions = self.previous_actions[-10:]
        formatted_actions = []
        
        for action in recent_actions:
            # If the action is a tuple with action and reasoning
            if isinstance(action, tuple) and len(action) == 2:
                formatted_actions.append(f"{action[0]} - {action[1]}")
            else:
                formatted_actions.append(str(action))
        
        return "\n".join(formatted_actions)

    def _parse_llm_response(self, response):
        """Extract the action and reasoning from the LLM response."""
        try:
            # Extract action from the response
            action_match = re.search(r"ACTION:\s*(\w+)", response, re.IGNORECASE)
            reasoning_match = re.search(r"REASONING:\s*(.*?)(?=ACTION:|$)", response, re.IGNORECASE | re.DOTALL)
            
            if action_match:
                action = action_match.group(1).lower()
                # Validate action is one of the allowed buttons
                if action not in ["up", "down", "left", "right", "a", "b", "start", "select"]:
                    logger.warning(f"Invalid action received from LLM: {action}")
                    return None, None
            else:
                logger.warning("No action found in LLM response")
                return None, None
            
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "Strategic movement based on analysis."
            
            return action, reasoning
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
        return None, None

    def _simulated_claude_response(self, prompt):
        """Generate a simulated Claude response for testing without API access."""
        # Extract key information from prompt to inform the simulated response
        location = "Unknown"
        if "Location:" in prompt:
            location_match = re.search(r"Location:\s*([^\n]+)", prompt)
            if location_match:
                location = location_match.group(1).strip()
        
        # Generate contextual response based on location
        if "Pallet Town" in location:
            return """
            REASONING: I'm in Pallet Town, the starting location. If I don't have a Pokémon yet, I should head to Professor Oak's lab which is typically located to the north of the player's starting position. The professor will give me my first Pokémon.
            
            ACTION: up
            """
        elif "Route 1" in location:
            return """
            REASONING: Route 1 connects Pallet Town and Viridian City. Since I'm just starting out, I should continue north to reach Viridian City where I can heal my Pokémon and buy supplies. There might be wild Pokémon in the tall grass that I can battle for experience.
            
            ACTION: up
            """
        elif "Viridian City" in location:
            return """
            REASONING: In Viridian City, I should first visit the Pokémon Center to heal my team. Then I should visit the Poké Mart to buy supplies if I have enough money. After that, I should head north toward Viridian Forest to continue my journey to Pewter City.
            
            ACTION: a
            """
        else:
            # Default exploration behavior
            directions = ["up", "down", "left", "right"]
            action = random.choice(directions)
            return f"""
            REASONING: I'm in {location} and should explore this area to find items, trainers, and potentially new Pokémon to catch. I'll try moving {action} to discover what's in that direction.
            
            ACTION: {action}
            """

    def _fallback_exploration(self):
        """Fallback strategy when LLM fails or is unavailable."""
        # Avoid repeating the last direction
        recent_moves = self.previous_actions[-3:] if self.previous_actions else []
        
        # Extract just the direction part if we have tuples
        recent_directions = []
        for move in recent_moves:
            if isinstance(move, tuple) and len(move) == 2:
                recent_directions.append(move[0])
            else:
                recent_directions.append(move)
        
        # Avoid backtracking
        avoid = None
        if recent_directions and recent_directions[-1] == "up":
            avoid = "down"
        elif recent_directions and recent_directions[-1] == "down":
            avoid = "up"
        elif recent_directions and recent_directions[-1] == "left":
            avoid = "right"
        elif recent_directions and recent_directions[-1] == "right":
            avoid = "left"
        
        options = ["up", "down", "left", "right"]
        if avoid and avoid in options:
            options.remove(avoid)
        
        action = random.choice(options)
        reasoning = "Exploring the area to find new paths and Pokémon."
        
        return action, reasoning


    def _decide_pokemon_action(self):
        """Claude's battle strategy."""
        # Get current Pokémon info
        pokemon_team = self.game_state.get("pokemon_team", [])
        
        if not pokemon_team:
            return "a", "Analyzing the battle situation..."
        
        # More strategic battle approach
        current_pokemon = pokemon_team[0]
        hp_percent = current_pokemon.get("hp", 0) / current_pokemon.get("max_hp", 1)
        
        # Consider switching if health is low
        if hp_percent < 0.2 and len(pokemon_team) > 1:
            if random.random() < 0.7:  # 70% chance to switch
                return "b", "Strategic retreat - let's switch to a healthier Pokémon."
        
        # Type-based strategy (placeholder)
        if random.random() < 0.4:
            return "down", "Let's select a move with type advantage."
        else:
            return "a", "This move should be effective based on type matchups."


class AIManager:
    """
    Manager class for handling multiple AIs and coordinating their actions.
    """
    
    def __init__(self):
        """Initialize the AI Manager."""
        self.grok = GrokAI()
        self.claude = ClaudeAI()
        self.active_player_ai = self.claude  # Default player AI
        self.active_pokemon_ai = self.claude  # Default Pokémon AI
        self.dual_mode = False  # Whether dual AI mode is enabled
    
    def set_active_player_ai(self, ai_name):
        """Set the active player AI."""
        if ai_name.lower() == "grok":
            self.active_player_ai = self.grok
        elif ai_name.lower() == "claude":
            self.active_player_ai = self.claude
        else:
            logger.warning(f"Unknown AI: {ai_name}. Using Grok as default.")
            self.active_player_ai = self.grok
        
        logger.info(f"Set active player AI to {self.active_player_ai.name}")
    
    def set_active_pokemon_ai(self, ai_name):
        """Set the active Pokémon AI."""
        if ai_name.lower() == "grok":
            self.active_pokemon_ai = self.grok
        elif ai_name.lower() == "claude":
            self.active_pokemon_ai = self.claude
        else:
            logger.warning(f"Unknown AI: {ai_name}. Using Claude as default.")
            self.active_pokemon_ai = self.claude
        
        logger.info(f"Set active Pokémon AI to {self.active_pokemon_ai.name}")
    
    def set_dual_mode(self, enabled):
        """Enable or disable dual AI mode."""
        self.dual_mode = enabled
        logger.info(f"Dual AI mode {'enabled' if enabled else 'disabled'}")
    
    def get_action(self, game_state, screen_state=None):
        """
        Get the next action from the appropriate AI based on game state.
        
        In dual mode, this selects between player AI and Pokémon AI based on
        whether the game is in a battle or not.
        
        In single mode, it always uses the player AI regardless of game state.
        """
        # Determine if we're in a battle
        in_battle = self._is_in_battle(game_state)
        
        if self.dual_mode and in_battle:
            # We're in a battle, use the Pokémon AI
            ai = self.active_pokemon_ai
            role = "pokemon"
            prefix = f"[{ai.name} as Pokémon] "
        else:
            # We're exploring or dual mode is off, use the player AI
            ai = self.active_player_ai
            role = "player" if not in_battle else "pokemon"  # Still specify the correct role even in single mode
            
            if self.dual_mode:
                prefix = f"[{ai.name} as Trainer] "
            else:
                # In single mode, make it clear if we're in battle or not
                prefix = f"[{ai.name}] " if not in_battle else f"[{ai.name} in Battle] "
        
        # Get the AI's decision
        action, commentary = ai.decide_action(game_state, screen_state, role)
        
        # Record the action
        ai.record_action(action)
        
        # Add AI name prefix to commentary
        commentary = prefix + commentary
        
        return action, commentary
    
    def _is_in_battle(self, game_state):
        """Determine if the game is currently in a battle."""
        # This is a simplified placeholder - would need game-specific logic
        # Could check for battle indicator in game_state or screen_state
        # For now, we'll use a simple heuristic
        if "battle" in str(game_state).lower() or game_state.get("screen", "") == "battle":
            return True
        return False


def get_game_screenshot():
    """Get screenshot from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/screenshot")
        return response.content
    except Exception as e:
        logger.error(f"Error getting game status during get_game_screenshot: {e}")
        return {"status": "error"}
    
def get_game_status():
    """Get the current game status from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        return response.json()
    except Exception as e:
        logger.error(f"Error getting game status: {e}")
        return {"status": "error"}

def get_game_state():
    """Get the current game state from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/state")
        return response.json()
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        return {}

def execute_action(action, commentary=None):
    """Execute a single game action with optional commentary."""
    data = {"action": action}
    if commentary:
        data["commentary"] = commentary
    
    try:
        response = requests.post(f"{API_BASE_URL}/execute_action", json=data)
        result = response.json()
        if result.get("success"):
            logger.info(f"Action executed: {action}")
        else:
            logger.warning(f"Failed to execute action: {action} - {result.get('error')}")
        return result
    except Exception as e:
        logger.error(f"Error executing action: {e}")
        return {"success": False, "error": str(e)}

def start_game():
    """Start the game."""
    try:
        response = requests.get(f"{API_BASE_URL}/start_game")
        return response.json()
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        return {"success": False, "error": str(e)}

def demo():
    """Demo of the AI controller framework."""
    logger.info("Starting AI controller demo")
    
    # Create AI manager
    manager = AIManager()
    
    # Example: Set active AIs and mode
    manager.set_active_player_ai("claude")
    manager.set_active_pokemon_ai("claude")
    manager.set_dual_mode(False)
    
    # Start the game if not running
    status = get_game_status()
    if status.get("status") != "running":
        logger.info("Starting the game")
        start_game()
        time.sleep(2)  # Wait for game to initialize
    
    # Run the AIs for a few steps
    while True:
        # Get current game state
        state = get_game_state()

        screen = get_game_screenshot() # should be a PIL image
        
        # Get AI's decision
        action, commentary = manager.get_action(state, screen_state=screen)
        
        # Execute the action
        execute_action(action, commentary)
        
        # Wait a bit before next action
        time.sleep(1)
    
    logger.info("AI controller demo completed")

if __name__ == "__main__":
    demo() 