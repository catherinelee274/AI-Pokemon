import os
import time
import logging
from pyboy import PyBoy
from pyboy.utils import WindowEvent
import numpy as np
from PIL import Image
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define button mapping
BUTTON_MAP = {
    "a": WindowEvent.PRESS_BUTTON_A,
    "b": WindowEvent.PRESS_BUTTON_B,
    "start": WindowEvent.PRESS_BUTTON_START,
    "select": WindowEvent.PRESS_BUTTON_SELECT,
    "up": WindowEvent.PRESS_ARROW_UP,
    "down": WindowEvent.PRESS_ARROW_DOWN,
    "left": WindowEvent.PRESS_ARROW_LEFT,
    "right": WindowEvent.PRESS_ARROW_RIGHT
}

BUTTON_RELEASE_MAP = {
    "a": WindowEvent.RELEASE_BUTTON_A,
    "b": WindowEvent.RELEASE_BUTTON_B,
    "start": WindowEvent.RELEASE_BUTTON_START,
    "select": WindowEvent.RELEASE_BUTTON_SELECT,
    "up": WindowEvent.RELEASE_ARROW_UP,
    "down": WindowEvent.RELEASE_ARROW_DOWN,
    "left": WindowEvent.RELEASE_ARROW_LEFT,
    "right": WindowEvent.RELEASE_ARROW_RIGHT
}

class PokemonEmulator:
    def __init__(self, rom_path):
        """Initialize the Pokemon emulator with the specified ROM."""
        if not os.path.exists(rom_path):
            raise FileNotFoundError(f"ROM file not found: {rom_path}")
        
        logger.info(f"Initializing emulator with ROM: {rom_path}")
        self.rom_path = rom_path
        self.pyboy = PyBoy(rom_path, game_wrapper=True)
        self.game = self.pyboy.game_wrapper()
        self.screen_buffer = []
        self.last_screenshot = None
        self.frame_count = 0
        self.is_running = False
        
        # Game state tracking
        self.current_state = {
            "pokemon_team": [],
            "items": [],
            "location": "Unknown",
            "badges": 0,
            "money": 0,
            "coordinates": None,
        }
        
        logger.info("Emulator initialized successfully")

    def start(self):
        """Start the emulator."""
        if not self.is_running:
            logger.info("Starting emulator")
            self.is_running = True
    
    def stop(self):
        """Stop the emulator."""
        if self.is_running:
            logger.info("Stopping emulator")
            self.is_running = False
            self.pyboy.stop()
    
    def get_screenshot(self):
        """Get the current screenshot of the game."""
        screen_image = self.pyboy.screen_image()
        self.last_screenshot = screen_image
        return screen_image
    
    def get_screen_ndarray(self):
        """Get the current screen as a numpy array."""
        return np.array(self.get_screenshot())
    
    def save_screenshot(self, path):
        """Save the current screenshot to a file."""
        self.get_screenshot().save(path)
        logger.info(f"Screenshot saved to {path}")
    
    def execute_action(self, action):
        """Execute a game action (button press)."""
        if action not in BUTTON_MAP:
            logger.warning(f"Unknown action: {action}")
            return False
        
        logger.info(f"Executing action: {action}")
        self.pyboy.send_input(BUTTON_MAP[action])
        self.tick(5)  # Small delay after button press
        self.pyboy.send_input(BUTTON_RELEASE_MAP[action])
        self.tick(5)  # Small delay after button release
        return True
    
    def execute_sequence(self, actions, delay=10):
        """Execute a sequence of actions with delays between them."""
        logger.info(f"Executing sequence: {actions}")
        results = []
        for action in actions:
            result = self.execute_action(action)
            results.append(result)
            self.tick(delay)
        return results
    
    def tick(self, frames=1):
        """Advance the emulator by a number of frames."""
        for _ in range(frames):
            self.pyboy.tick()
            self.frame_count += 1

    def run_for_seconds(self, seconds):
        """Run the emulator for a specified number of seconds."""
        fps = 60
        frames = int(seconds * fps)
        logger.info(f"Running for {seconds} seconds ({frames} frames)")
        self.tick(frames)

    def get_money(self):
        # Money is stored as BCD, need to convert
        byte1 = self.pyboy.get_memory_value(0xD347)
        byte2 = self.pyboy.get_memory_value(0xD348)
        byte3 = self.pyboy.get_memory_value(0xD349)
        
        # Convert from BCD
        digit1 = (byte1 >> 4) & 0xF
        digit2 = byte1 & 0xF
        digit3 = (byte2 >> 4) & 0xF
        digit4 = byte2 & 0xF
        digit5 = (byte3 >> 4) & 0xF
        digit6 = byte3 & 0xF
        
        money = digit1 * 100000 + digit2 * 10000 + digit3 * 1000 + digit4 * 100 + digit5 * 10 + digit6
        return money
    def get_badges(self):
        badge_bits = self.pyboy.get_memory_value(0xD356)
        badge_count = bin(badge_bits).count('1')
        return badge_count
    
    def get_map_lookup(self, map_id):
        locations = {
            "0x5473": "Pallet Town",
            "0x547F": "Viridian City",
            "0x548D": "Pewter City",
            "0x5499": "Cerulean City",
            "0x54A7": "Lavender Town",
            "0x54B5": "Vermilion City",
            "0x54C4": "Celadon City",
            "0x54D1": "Fuchsia City",
            "0x54DE": "Cinnabar Island",
            "0x54EE": "Indigo Plateau",
            "0x54FD": "Saffron City",
            "0x550A": "Route 1",
            "0x5512": "Route 2",
            "0x551A": "Route 3",
            "0x5522": "Route 4",
            "0x552A": "Route 5",
            "0x5532": "Route 6",
            "0x553A": "Route 7",
            "0x5542": "Route 8",
            "0x554A": "Route 9",
            "0x5552": "Route 10",
            "0x555B": "Route 11",
            "0x5564": "Route 12",
            "0x556D": "Route 13",
            "0x5576": "Route 14",
            "0x557F": "Route 15",
            "0x5588": "Route 16",
            "0x5591": "Route 17",
            "0x559A": "Route 18",
            "0x55A3": "Sea Route 19",
            "0x55B0": "Sea Route 20",
            "0x55BD": "Sea Route 21",
            "0x55CA": "Route 22",
            "0x55D3": "Route 23",
            "0x55DC": "Route 24",
            "0x55E5": "Route 25",
            "0x55EE": "Viridian Forest",
            "0x55FE": "Mt. Moon",
            "0x5606": "Rock Tunnel",
            "0x5612": "Sea Cottage",
            "0x561E": "S.S. Anne",
            "0x5627": "Pokémon League",
            "0x5633": "Underground Path",
            "0x5644": "Pokémon Tower",
            "0x564F": "Seafoam Islands",
            "0x565F": "Victory Road",
            "0x566C": "Diglett's Cave",
            "0x567A": "Rocket HQ",
            "0x5684": "Silph Co.",
            "0x568E": "PKMN Mansion",
            "0x5698": "Safari Zone",
            "0x56A4": "Cerulean Cave",
            "0x56B2": "Power Plant",
        }

        if map_id not in locations: 
            return ''
        return locations[map_id]
                

    def get_location(self):
        map_id = self.pyboy.get_memory_value(0xD35E)
        return self.get_map_lookup(map_id)  # Would need to implement a map name lookup
    
    def get_items(self):
        items = []
        item_count = self.pyboy.get_memory_value(0xD31C)
        
        for i in range(item_count):
            # Each item entry is 2 bytes: item ID and quantity
            item_address = 0xD31D + (i * 2)
            item_id = self.pyboy.get_memory_value(item_address)
            item_quantity = self.pyboy.get_memory_value(item_address + 1)
            
            # Get item name from item ID (would need to implement a lookup table)
            item_name = self.get_item_name(item_id)
            
            items.append({
                "name": item_name,
                "count": item_quantity
            })
        
        return items
    
    def get_pokemon_team(self):
        pokemon_team = []
        team_size = self.pyboy.get_memory_value(0xD163)
        
        for i in range(team_size):
            # Calculate the starting address for this Pokémon
            pokemon_address = 0xD16B + (i * 44)
            
            # Read species, level, HP, etc.
            species_id = self.pyboy.get_memory_value(pokemon_address)
            level = self.pyboy.get_memory_value(pokemon_address + 8)
            current_hp = self.pyboy.get_memory_value(pokemon_address + 1) * 256 + self.pyboy.get_memory_value(pokemon_address + 2)
            max_hp = self.pyboy.get_memory_value(pokemon_address + 3) * 256 + self.pyboy.get_memory_value(pokemon_address + 4)
            
            # Get Pokémon name (stored in a different location, indexed by species_id)
            name = self.get_pokemon_name(species_id)
            
            pokemon_team.append({
                "name": name,
                "level": level,
                "hp": current_hp,
                "max_hp": max_hp
            })
        
        return pokemon_team
    
    def get_pokemon_coordinates(self):
        x =  self.pyboy.get_memory_value(0xD362)
        y =  self.pyboy.get_memory_value(0xD361)
        return '(' + str(x) +',' + str(y) + ')'

    def update_game_state(self):
        """Update the game state information."""
        # This is a placeholder - implementing actual game state extraction
        # would require deeper integration with PyBoy and game memory reading
        
        # For demo purposes, we'll just update with placeholder data
        logger.info("Updating game state")
        
        # In a real implementation, we would read memory locations to get:
        # - Current Pokémon team (species, levels, HP, moves)
        # - Items in inventory
        # - Current location (map ID)
        # - Badges collected
        # - Money
        # - Current battle state if in battle
        # TODO: update this

        # For now, just return placeholder data
        money = self.get_money()
        badges = self.get_badges()
        location = self.get_location()
        items = self.get_items()
        team = self.get_pokemon_team()
        coordinates = self.get_pokemon_coordinates()

        

        self.current_state = {
            "pokemon_team": team,
            "items": items,
            "location": location,
            "badges": badges,
            "money":  money,
            'coordinates': coordinates,
            # "current_pokemon": "SQUIRTLE"
        }

        logger.info(f'leecatherine current state: {self.current_state}')

        
        return self.current_state
    
    def get_state(self):
        """Get the current game state."""
        self.update_game_state()
        return self.current_state
    
    def detect_game_screen(self):
        """Detect what screen we're currently on (battle, overworld, menu, etc.)."""
        # This would use image recognition or memory reading to determine the current screen
        # For now, return a placeholder
        screens = ["overworld", "battle", "menu", "pokemon_list", "item_menu"]
        import random
        return random.choice(screens)

    def is_in_battle(self):
        """Check if the game is currently in a battle."""
        # This would use memory reading to determine if in battle
        # For now, return a placeholder
        return self.detect_game_screen() == "battle"

    def get_game_loop_frequency(self):
        """Return the target frequency for the game loop."""
        return 30  # 30 FPS 