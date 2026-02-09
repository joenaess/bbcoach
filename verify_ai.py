import sys
import os

sys.path.append(os.path.abspath("src"))
from bbcoach.ai.coach import BasketballCoach

print("Initializing Coach...")
coach = BasketballCoach(device="cuda")  # Or check availability
print("Coach initialized.")
response = coach.ask("Player X has 10 points", "Is he good?")
print(f"Response: {response}")
