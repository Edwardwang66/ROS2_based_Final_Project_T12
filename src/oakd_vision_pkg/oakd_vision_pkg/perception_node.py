#!/usr/bin/env python3
"""
OAK-D Perception Node with TPU Acceleration
All CV computations run on OAK-D Lite's TPU for acceleration
References: ucsd_robocar_sensor2_pkg for sensor integration patterns
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String
from sensor_msgs.msg import Image
from vision_msgs.msg import BoundingBox2D, Point2D
from oakd_msgs.msg import PersonDetection
import cv2
import numpy as np
from cv_bridge import CvBridge
import os

try:
    import depthai as dai
    DEPTHAI_AVAILABLE = True
except ImportError:
    DEPTHAI_AVAILABLE = False
    print("Warning: depthai not available. Using mock mode.")


class PerceptionNode(Node):
    """
    Perception node for OAK-D camera with TPU acceleration
    All neural network inference runs on OAK-D Lite's TPU (Myriad X)
    
    Publishes:
        - /person_detection (oakd_msgs/PersonDetection)
        - /obstacle_ahead (std_msgs/Bool)
        - /hand_gesture (std_msgs/String) - "rock", "paper", "scissors", or "none"
    """

    def __init__(self):
        super().__init__('perception_node')
        
        # Publishers
        self.person_detection_pub = self.create_publisher(
            PersonDetection, '/person_detection', 10
        )
        self.obstacle_ahead_pub = self.create_publisher(
            Bool, '/obstacle_ahead', 10
        )
        self.hand_gesture_pub = self.create_publisher(
            String, '/hand_gesture', 10
        )
        self.image_pub = self.create_publisher(
            Image, '/oakd/rgb/image_raw', 10
        )
        self.depth_pub = self.create_publisher(
            Image, '/oakd/depth/image_raw', 10
        )
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Parameters
        self.declare_parameter('target_distance', 1.0)  # meters
        self.declare_parameter('obstacle_threshold', 0.5)  # meters
        self.declare_parameter('obstacle_roi_width', 0.3)  # fraction of image width
        self.declare_parameter('obstacle_roi_height', 0.4)  # fraction of image height
        self.declare_parameter('person_confidence_threshold', 0.5)
        self.declare_parameter('use_mock_mode', False)
        self.declare_parameter('person_model_path', 'models/mobilenet-ssd_openvino_2021.4_6shave.blob')
        self.declare_parameter('rps_model_path', 'models/hand_gesture_rps_openvino_2021.4_6shave.blob')
        
        # State variables
        self.current_frame = None
        self.current_depth = None
        self.person_detections = []
        self.hand_gesture_result = "none"
        
        # Initialize OAK-D pipeline with TPU models
        if DEPTHAI_AVAILABLE and not self.get_parameter('use_mock_mode').value:
            self.init_oakd_pipeline_with_tpu()
        else:
            self.get_logger().warn("Running in mock mode - no OAK-D hardware")
            # In mock mode, use timer to simulate data
            self.create_timer(0.1, self.mock_perception_callback)
        
        # Main processing timer
        self.create_timer(0.1, self.perception_callback)
        
        self.get_logger().info('Perception node initialized with TPU acceleration')

    def init_oakd_pipeline_with_tpu(self):
        """Initialize OAK-D pipeline with NeuralNetwork nodes running on TPU"""
        try:
            # Create pipeline
            self.pipeline = dai.Pipeline()
            
            # Define sources
            cam_rgb = self.pipeline.create(dai.node.ColorCamera)
            cam_rgb.setPreviewSize(300, 300)  # Standard size for MobileNet-SSD
            cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
            cam_rgb.setInterleaved(False)
            cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
            
            # Depth
            mono_left = self.pipeline.create(dai.node.MonoCamera)
            mono_right = self.pipeline.create(dai.node.MonoCamera)
            stereo = self.pipeline.create(dai.node.StereoDepth)
            
            mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
            mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
            mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
            mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
            
            stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
            stereo.setDepthAlign(dai.CameraBoardSocket.RGB)
            stereo.setOutputSize(640, 480)
            
            # Person Detection Neural Network (runs on TPU)
            person_nn = self.pipeline.create(dai.node.MobileNetDetectionNetwork)
            person_nn.setConfidenceThreshold(self.get_parameter('person_confidence_threshold').value)
            person_nn.setBlobPath(self.get_parameter('person_model_path').value)
            person_nn.setNumInferenceThreads(2)
            person_nn.input.setBlocking(False)
            
            # Hand Gesture Recognition Neural Network (runs on TPU)
            # Using a separate NN for gesture recognition
            gesture_nn = self.pipeline.create(dai.node.NeuralNetwork)
            gesture_model_path = self.get_parameter('rps_model_path').value
            if os.path.exists(gesture_model_path):
                gesture_nn.setBlobPath(gesture_model_path)
            else:
                self.get_logger().warn(f"RPS model not found at {gesture_model_path}, gesture recognition disabled")
                gesture_nn = None
            
            # Create manipulators for image preprocessing
            # For person detection - use camera preview directly
            # For gesture - crop hand region from full frame
            
            # XLinkOut
            xout_rgb = self.pipeline.create(dai.node.XLinkOut)
            xout_rgb.setStreamName("rgb")
            
            xout_preview = self.pipeline.create(dai.node.XLinkOut)
            xout_preview.setStreamName("preview")
            
            xout_depth = self.pipeline.create(dai.node.XLinkOut)
            xout_depth.setStreamName("depth")
            
            xout_person_nn = self.pipeline.create(dai.node.XLinkOut)
            xout_person_nn.setStreamName("person_nn")
            
            if gesture_nn is not None:
                xout_gesture_nn = self.pipeline.create(dai.node.XLinkOut)
                xout_gesture_nn.setStreamName("gesture_nn")
            
            # Linking
            cam_rgb.preview.link(person_nn.input)
            cam_rgb.video.link(xout_rgb.input)  # Full resolution for display
            cam_rgb.preview.link(xout_preview.input)
            
            person_nn.out.link(xout_person_nn.input)
            
            if gesture_nn is not None:
                # For gesture recognition, we'll use the preview stream
                # In a more sophisticated setup, you'd crop hand regions
                cam_rgb.preview.link(gesture_nn.input)
                gesture_nn.out.link(xout_gesture_nn.input)
            
            mono_left.out.link(stereo.left)
            mono_right.out.link(stereo.right)
            stereo.depth.link(xout_depth.input)
            
            # Connect to device
            self.device = dai.Device(self.pipeline)
            self.q_rgb = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.q_preview = self.device.getOutputQueue(name="preview", maxSize=4, blocking=False)
            self.q_depth = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            self.q_person_nn = self.device.getOutputQueue(name="person_nn", maxSize=4, blocking=False)
            
            if gesture_nn is not None:
                self.q_gesture_nn = self.device.getOutputQueue(name="gesture_nn", maxSize=4, blocking=False)
            else:
                self.q_gesture_nn = None
            
            self.get_logger().info('OAK-D pipeline with TPU acceleration initialized successfully')
            
        except Exception as e:
            self.get_logger().error(f'Failed to initialize OAK-D: {str(e)}')
            self.get_logger().warn('Falling back to mock mode')
            self.create_timer(0.1, self.mock_perception_callback)

    def perception_callback(self):
        """Main perception callback - processes frames and publishes results"""
        if not DEPTHAI_AVAILABLE or self.get_parameter('use_mock_mode').value:
            return  # Mock mode uses separate callback
        
        # Get frames from OAK-D
        in_rgb = self.q_rgb.tryGet()
        in_preview = self.q_preview.tryGet()
        in_depth = self.q_depth.tryGet()
        in_person_nn = self.q_person_nn.tryGet()
        in_gesture_nn = self.q_gesture_nn.tryGet() if self.q_gesture_nn else None
        
        if in_rgb is None or in_depth is None:
            return
        
        # Convert to OpenCV format
        frame = in_rgb.getCvFrame()
        preview_frame = in_preview.getCvFrame() if in_preview else frame
        depth_frame = in_depth.getFrame()
        
        # Publish raw images
        try:
            rgb_msg = self.bridge.cv2_to_imgmsg(frame, "rgb8")
            rgb_msg.header.stamp = self.get_clock().now().to_msg()
            rgb_msg.header.frame_id = "oakd_rgb_optical_frame"
            self.image_pub.publish(rgb_msg)
            
            depth_msg = self.bridge.cv2_to_imgmsg(depth_frame, "16UC1")
            depth_msg.header.stamp = self.get_clock().now().to_msg()
            depth_msg.header.frame_id = "oakd_depth_optical_frame"
            self.depth_pub.publish(depth_msg)
        except Exception as e:
            self.get_logger().error(f'Error publishing images: {str(e)}')
        
        # Process neural network outputs (all computed on TPU)
        person_detection = self.process_person_detection(in_person_nn, depth_frame, preview_frame)
        obstacle_ahead = self.check_obstacle(depth_frame)
        hand_gesture = self.process_gesture_recognition(in_gesture_nn, preview_frame)
        
        # Publish results
        self.person_detection_pub.publish(person_detection)
        self.obstacle_ahead_pub.publish(Bool(data=obstacle_ahead))
        self.hand_gesture_pub.publish(String(data=hand_gesture))

    def mock_perception_callback(self):
        """Mock callback for testing without hardware"""
        # Create mock detection
        person_msg = PersonDetection()
        person_msg.person_found.data = False
        person_msg.distance.data = 0.0
        person_msg.confidence.data = 0.0
        
        self.person_detection_pub.publish(person_msg)
        self.obstacle_ahead_pub.publish(Bool(data=False))
        self.hand_gesture_pub.publish(String(data="none"))

    def process_person_detection(self, detections, depth_frame, preview_frame):
        """
        Process person detection results from TPU
        MobileNet-SSD outputs detections with class labels
        Class 15 in COCO dataset is "person"
        """
        person_msg = PersonDetection()
        person_msg.person_found.data = False
        person_msg.distance.data = 0.0
        person_msg.confidence.data = 0.0
        
        if detections is None:
            return person_msg
        
        dets = detections.detections
        preview_h, preview_w = preview_frame.shape[:2]
        
        # Find person with highest confidence
        best_person = None
        best_confidence = 0.0
        
        for detection in dets:
            # MobileNet-SSD: label 15 is person in COCO dataset
            # Some models use label 1 for person
            if detection.label == 15 or detection.label == 1:
                if detection.confidence > best_confidence:
                    best_confidence = detection.confidence
                    best_person = detection
        
        if best_person is not None and best_confidence >= self.get_parameter('person_confidence_threshold').value:
            person_msg.person_found.data = True
            person_msg.confidence.data = float(best_confidence)
            
            # Calculate bounding box (normalized coordinates)
            bbox = BoundingBox2D()
            bbox.center = Point2D()
            bbox.center.x = float(best_person.xmin + best_person.xmax) / 2.0
            bbox.center.y = float(best_person.ymin + best_person.ymax) / 2.0
            bbox.size_x = float(best_person.xmax - best_person.xmin)
            bbox.size_y = float(best_person.ymax - best_person.ymin)
            person_msg.bbox = bbox
            
            # Calculate distance from depth map
            # Map normalized bbox to actual depth frame coordinates
            depth_h, depth_w = depth_frame.shape[:2]
            x_min = int(best_person.xmin * depth_w)
            x_max = int(best_person.xmax * depth_w)
            y_min = int(best_person.ymin * depth_h)
            y_max = int(best_person.ymax * depth_h)
            
            # Extract depth in bbox region
            depth_roi = depth_frame[y_min:y_max, x_min:x_max]
            valid_depths = depth_roi[depth_roi > 0]
            valid_depths = valid_depths[valid_depths < 10000]  # Remove outliers
            
            if len(valid_depths) > 0:
                # Use median depth for stability
                depth_mm = np.median(valid_depths)
                person_msg.distance.data = depth_mm / 1000.0  # Convert mm to meters
        
        return person_msg

    def process_gesture_recognition(self, gesture_output, frame):
        """
        Process hand gesture recognition results from TPU
        Returns: "rock", "paper", "scissors", or "none"
        """
        if gesture_output is None:
            return "none"
        
        try:
            # Get neural network output
            output = gesture_output.getLayerFp16("output")  # Adjust layer name based on model
            
            # Assuming output is [rock_prob, paper_prob, scissors_prob]
            if len(output) >= 3:
                rock_prob = output[0]
                paper_prob = output[1]
                scissors_prob = output[2]
                
                # Find class with highest probability
                max_prob = max(rock_prob, paper_prob, scissors_prob)
                threshold = 0.5  # Confidence threshold
                
                if max_prob < threshold:
                    return "none"
                
                if rock_prob == max_prob:
                    return "rock"
                elif paper_prob == max_prob:
                    return "paper"
                elif scissors_prob == max_prob:
                    return "scissors"
        except Exception as e:
            self.get_logger().debug(f'Error processing gesture: {str(e)}')
        
        return "none"

    def check_obstacle(self, depth_frame):
        """
        Check if there's an obstacle ahead using depth map
        Returns True if obstacle detected
        """
        if depth_frame is None or depth_frame.size == 0:
            return False
        
        h, w = depth_frame.shape[:2]
        threshold = self.get_parameter('obstacle_threshold').value
        roi_width = self.get_parameter('obstacle_roi_width').value
        roi_height = self.get_parameter('obstacle_roi_height').value
        
        # Define ROI in center of image
        x_min = int(w * (0.5 - roi_width / 2))
        x_max = int(w * (0.5 + roi_width / 2))
        y_min = int(h * (0.5 - roi_height / 2))
        y_max = int(h * (0.5 + roi_height / 2))
        
        roi = depth_frame[y_min:y_max, x_min:x_max]
        
        # Filter out invalid depth values (0 or very large)
        valid_depths = roi[roi > 0]
        valid_depths = valid_depths[valid_depths < 10000]  # Remove outliers
        
        if len(valid_depths) == 0:
            return False
        
        # Use 10th percentile to detect nearby obstacles
        depth_percentile = np.percentile(valid_depths, 10)
        
        # Convert from mm to meters if needed (OAK-D typically outputs mm)
        depth_m = depth_percentile / 1000.0
        
        return depth_m < threshold


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
