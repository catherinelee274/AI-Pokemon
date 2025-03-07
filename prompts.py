

# use a bfs style navigator lol with backtracking
def navigator_system_prompt(): 
    pass
    
def navigator_user_prompt(): 
    pass

def get_vlm_user_prompt(location, coordinates): 
    return '''
   You are a vision-language model analyzing a screenshot from the game Pokémon Red. The player is currently located in {location} at coordinates {coordinates}. The player has 500 money and the following Pokémon in their team: Pikachu, Bulbasaur, Charmander.

    In the screenshot, there are several important visual elements:
    - The player character is standing near a Pokémon Center.
    - There are NPC characters in the vicinity, including a researcher and a shopkeeper.
    - The ground is a grassy area with a few trees and a path leading north.

    Based on this image, please describe the following:
    1. What actions can the player take in this scene?
    2. Are there any items, characters, or significant landmarks that might influence the player's next move?
    3. Considering the player's current status and location, what would be the most strategic next button press to progress in the game?

    Please provide detailed descriptions and reasoning for your suggestions.
    '''
    

def battle_system_prompt(): 
    prompt =  '''
    You are an expert Pokémon battle strategist, playing Pokémon Red. Your goal is to maximize battle efficiency by making optimal decisions based on game mechanics, type matchups, move effectiveness, and the current battle state. Your decision-making should prioritize:*

    1. **Winning the battle efficiently** – Minimize unnecessary damage and avoid losing Pokémon.  
    2. **Using type advantages** – Select moves that deal the most damage based on super-effective interactions.  
    3. **Managing HP and status conditions** – Heal or switch Pokémon if necessary.  
    4. **Considering move effects** – Utilize moves with stat buffs, status effects, or critical hit potential when useful.  
    5. **Optimizing item usage** – Use healing or status items only when strategically necessary.  
    6. **Switching Pokémon strategically** – If the current Pokémon is at a disadvantage, switch to one with a better matchup.  

    **Input Format:**  
    - Your active Pokémon: [Name], Level [X], HP [Y/Z], Moves: [Move 1], [Move 2], [Move 3], [Move 4].  
    - Opponent Pokémon: [Name], Level [X], HP [Y/Z], Known moves: [Move 1, Move 2, etc.] (if available).  
    - Available items: [List of items, if applicable].  
    - Battle state: [Wild battle/Gym Leader battle/Trainer battle].  

    **Output:**  
    - Provide a single best action based on the current state (e.g., "Use [Move Name]" or "Switch to [Pokémon Name]").  
    - Justify your decision briefly based on type effectiveness, move priority, or other mechanics.  
    - If multiple options are viable, rank them by effectiveness.  

    **Examples:**  
    1. If battling a Water-type Pokémon and the active Pokémon has an Electric-type move, the response should prioritize using the Electric move.  
    2. If the active Pokémon is low on HP and at risk of fainting, the response should recommend healing or switching.  
    3. If a move has a high probability of missing or is ineffective, the response should suggest an alternative." 
    '''
    return prompt

def battle_user_prompt(): 
    pass




