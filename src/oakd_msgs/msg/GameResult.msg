# Game result message
# Published by game interaction node

std_msgs/String player_gesture  # "rock", "paper", or "scissors"
std_msgs/String robot_gesture   # "rock", "paper", or "scissors"
std_msgs/String result          # "win", "loss", or "tie"
std_msgs/Int32 round_number     # Current round number
std_msgs/Int32 total_rounds     # Total rounds in session
std_msgs/Bool game_done         # True when game session is complete

