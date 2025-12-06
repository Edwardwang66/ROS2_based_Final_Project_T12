#!/usr/bin/env python3
"""
Game Interaction Node
Handles Rock-Paper-Scissors game logic
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Int32
from oakd_msgs.msg import GameResult
import random


class GameNode(Node):
    """
    Game interaction node for Rock-Paper-Scissors
    Subscribes:
        - /current_state (std_msgs/String)
        - /hand_gesture (std_msgs/String)
    Publishes:
        - /game_result (oakd_msgs/GameResult)
        - /game_done (std_msgs/Bool)
    """

    def __init__(self):
        super().__init__('game_node')
        
        # Publishers
        self.game_result_pub = self.create_publisher(
            GameResult, '/game_result', 10
        )
        self.game_done_pub = self.create_publisher(
            Bool, '/game_done', 10
        )
        
        # Subscribers
        self.current_state_sub = self.create_subscription(
            String, '/current_state', self.state_callback, 10
        )
        self.hand_gesture_sub = self.create_subscription(
            String, '/hand_gesture', self.gesture_callback, 10
        )
        
        # Game state
        self.current_state = "IDLE"
        self.current_gesture = "none"
        self.game_active = False
        self.round_number = 0
        self.total_rounds = 3
        self.player_score = 0
        self.robot_score = 0
        
        # Parameters
        self.declare_parameter('total_rounds', 3)
        self.declare_parameter('gesture_timeout', 5.0)  # seconds
        self.declare_parameter('round_delay', 2.0)  # seconds between rounds
        
        # Timer for game logic
        self.create_timer(0.1, self.game_logic_callback)
        
        self.get_logger().info('Game node initialized')

    def state_callback(self, msg):
        """Callback for state updates"""
        self.current_state = msg.data
        
        # Start game when entering INTERACT state
        if self.current_state == "INTERACT" and not self.game_active:
            self.start_game()
        elif self.current_state != "INTERACT" and self.game_active:
            self.reset_game()

    def gesture_callback(self, msg):
        """Callback for hand gesture updates"""
        self.current_gesture = msg.data

    def start_game(self):
        """Start a new game session"""
        self.get_logger().info('Starting RPS game session')
        self.game_active = True
        self.round_number = 0
        self.player_score = 0
        self.robot_score = 0
        self.total_rounds = self.get_parameter('total_rounds').value

    def reset_game(self):
        """Reset game state"""
        self.game_active = False
        self.round_number = 0
        self.player_score = 0
        self.robot_score = 0
        self.current_gesture = "none"

    def game_logic_callback(self):
        """Main game logic callback"""
        if not self.game_active:
            return
        
        if self.round_number >= self.total_rounds:
            # Game complete
            self.end_game()
            return
        
        # Check if we have a valid gesture
        if self.current_gesture not in ["rock", "paper", "scissors"]:
            return  # Wait for valid gesture
        
        # Play round
        self.play_round()

    def play_round(self):
        """Play a single round of RPS"""
        self.round_number += 1
        
        player_gesture = self.current_gesture
        robot_gesture = self.generate_robot_gesture()
        
        # Determine winner
        result = self.determine_winner(player_gesture, robot_gesture)
        
        if result == "win":
            self.player_score += 1
        elif result == "loss":
            self.robot_score += 1
        
        # Publish result
        game_result = GameResult()
        game_result.player_gesture.data = player_gesture
        game_result.robot_gesture.data = robot_gesture
        game_result.result.data = result
        game_result.round_number.data = self.round_number
        game_result.total_rounds.data = self.total_rounds
        game_result.game_done.data = False
        
        self.game_result_pub.publish(game_result)
        
        self.get_logger().info(
            f'Round {self.round_number}/{self.total_rounds}: '
            f'Player: {player_gesture}, Robot: {robot_gesture}, Result: {result}'
        )
        
        # Reset gesture to wait for next round
        self.current_gesture = "none"

    def generate_robot_gesture(self):
        """Generate random robot gesture"""
        return random.choice(["rock", "paper", "scissors"])

    def determine_winner(self, player, robot):
        """
        Determine winner of RPS round
        Returns: "win", "loss", or "tie"
        """
        if player == robot:
            return "tie"
        
        winning_combinations = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        if winning_combinations[player] == robot:
            return "win"
        else:
            return "loss"

    def end_game(self):
        """End game session and publish final results"""
        self.get_logger().info(
            f'Game complete! Score - Player: {self.player_score}, '
            f'Robot: {self.robot_score}'
        )
        
        # Publish final result
        game_result = GameResult()
        game_result.player_gesture.data = "none"
        game_result.robot_gesture.data = "none"
        game_result.result.data = "win" if self.player_score > self.robot_score else "loss"
        game_result.round_number.data = self.total_rounds
        game_result.total_rounds.data = self.total_rounds
        game_result.game_done.data = True
        
        self.game_result_pub.publish(game_result)
        
        # Signal game done
        self.game_done_pub.publish(Bool(data=True))
        
        # Reset
        self.reset_game()


def main(args=None):
    rclpy.init(args=args)
    node = GameNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

