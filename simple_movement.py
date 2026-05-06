#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time
import math


class SimpleMove(Node):

    def __init__(self):
        super().__init__('simple_move')
        self.publisher_ = self.create_publisher(
            Twist,
            '/mobile_base_controller/cmd_vel',
            10
        )

    def move_forward(self, speed=0.1, distance=0.5):
        msg = Twist()
        msg.linear.x = speed

        duration = distance / speed
        end_time = time.time() + duration

        while time.time() < end_time:
            self.publisher_.publish(msg)
            time.sleep(0.1)

        self.stop()

    def rotate_90(self, angular_speed=0.3):
        msg = Twist()
        msg.angular.z = angular_speed

        angle = math.pi / 2
        duration = angle / angular_speed
        end_time = time.time() + duration

        while time.time() < end_time:
            self.publisher_.publish(msg)
            time.sleep(0.1)

        self.stop()

    def move_left(self, speed=0.1, distance=0.5):
        msg = Twist()
        msg.linear.y = 0.1

        duration = distance / speed
        end_time = time.time() + duration

        while time.time() < end_time:
            self.publisher_.publish(msg)
            time.sleep(0.1)

        self.stop()

    def stop(self):
        msg = Twist()
        self.publisher_.publish(msg)
        time.sleep(1)


def main(args=None):
    rclpy.init(args=args)

    node = SimpleMove()

    time.sleep(2)

    node.get_logger().info("Forward 0.5m")
    node.move_forward()

    node.get_logger().info("Rotate 90 degree")
    node.rotate_90()

    node.get_logger().info("Move left 0.5m")
    node.move_left()

    node.get_logger().info("Done")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
