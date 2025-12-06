# Person detection message
# Published by perception node

std_msgs/Bool person_found
vision_msgs/BoundingBox2D bbox
std_msgs/Float32 distance  # Distance to person in meters
std_msgs/Float32 confidence  # Detection confidence (0.0-1.0)

