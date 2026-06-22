import math
import time

from geometry_msgs.msg import Twist
from rclpy.node import Node


class Movement(Node):
    """ROS2 movement helper for DiMI/Tiago Logo commands.

    Distances are interpreted as centimeters, angles as degrees.
    Movement is open-loop/time-based: good enough for simple Logo demos, but not
    as accurate as odometry-based navigation.
    """

    LINEAR_SPEED = 0.1      # m/s
    ANGULAR_SPEED = 0.3     # rad/s
    PUBLISH_PERIOD = 0.1    # seconds
    STOP_SETTLE_TIME = 0.2  # seconds

    def __init__(self):
        super().__init__("movement")

        self.publisher_ = self.create_publisher(
            Twist,
            "/cmd_vel",
            10,
        )

        self.history = []
        self.heading = 0

    def fd(self, cm, record=True):
        """Move forward by ``cm`` centimeters."""
        cm = self._as_number(cm, "cm")

        if cm < 0:
            return self.bk(-cm, record=record)
        if cm == 0:
            return

        if record:
            self.history.append(("fd", cm))

        self._move(linear_x=self.LINEAR_SPEED, distance_cm=cm)

    def bk(self, cm, record=True):
        """Move backward by ``cm`` centimeters."""
        cm = self._as_number(cm, "cm")

        if cm < 0:
            return self.fd(-cm, record=record)
        if cm == 0:
            return

        if record:
            self.history.append(("bk", cm))

        self._move(linear_x=-self.LINEAR_SPEED, distance_cm=cm)

    def move_x(self, cm, record=True, command_name="move_x"):
        """Move along the robot's X axis.

        Positive values move forward, negative values move backward.
        """
        cm = self._as_number(cm, "cm")

        if cm == 0:
            return

        if record:
            self.history.append((command_name, cm))

        direction = 1 if cm > 0 else -1
        self._move(linear_x=direction * self.LINEAR_SPEED, distance_cm=abs(cm))

    def move_y(self, cm, record=True, command_name="move_y"):
        """Move along the robot's Y axis.

        Positive values move left, negative values move right. This only works if
        the robot base accepts lateral velocity commands.
        """
        cm = self._as_number(cm, "cm")

        if cm == 0:
            return

        if record:
            self.history.append((command_name, cm))

        direction = 1 if cm > 0 else -1
        self._move(linear_y=direction * self.LINEAR_SPEED, distance_cm=abs(cm))

    # Friendly aliases for Logo/action_set names.
    movex = move_x
    movey = move_y

    def rt(self, angle, record=True):
        """Turn right by ``angle`` degrees."""
        angle = self._as_number(angle, "angle")

        if angle < 0:
            return self.lt(-angle, record=record)
        if angle == 0:
            return

        if record:
            self.history.append(("rt", angle))

        self._rotate(angle, angular_z=-self.ANGULAR_SPEED)
        self.heading = (self.heading - angle) % 360

    def lt(self, angle, record=True):
        """Turn left by ``angle`` degrees."""
        angle = self._as_number(angle, "angle")

        if angle < 0:
            return self.rt(-angle, record=record)
        if angle == 0:
            return

        if record:
            self.history.append(("lt", angle))

        self._rotate(angle, angular_z=self.ANGULAR_SPEED)
        self.heading = (self.heading + angle) % 360

    def setheading(self, target):
        """Turn to an absolute heading using the shortest direction."""
        target = self._as_number(target, "target") % 360
        difference = (target - self.heading + 180) % 360 - 180

        if difference > 0:
            self.lt(difference)
        elif difference < 0:
            self.rt(-difference)

        self.heading = target

    def home(self):
        """Undo recorded movements and clear the movement history."""
        commands = list(reversed(self.history))

        for command, value in commands:
            if command in ("fd", "move_x"):
                self.move_x(-value, record=False)
            elif command == "bk":
                self.move_x(value, record=False)
            elif command == "move_y":
                self.move_y(-value, record=False)
            elif command == "rt":
                self.lt(value, record=False)
            elif command == "lt":
                self.rt(value, record=False)

        self.history.clear()
        self.heading = 0

    def stop(self):
        """Publish a zero velocity command."""
        self.publisher_.publish(Twist())
        time.sleep(self.STOP_SETTLE_TIME)

    def _move(self, distance_cm, linear_x=0.0, linear_y=0.0):
        msg = Twist()
        msg.linear.x = linear_x
        msg.linear.y = linear_y

        speed = max(abs(linear_x), abs(linear_y))
        duration = (distance_cm / 100.0) / speed

        self._publish_for_duration(msg, duration)
        self.stop()

    def _rotate(self, angle_degrees, angular_z):
        msg = Twist()
        msg.angular.z = angular_z

        duration = math.radians(angle_degrees) / abs(angular_z)

        self._publish_for_duration(msg, duration)
        self.stop()

    def _publish_for_duration(self, msg, duration):
        end_time = time.time() + duration

        while True:
            remaining = end_time - time.time()
            if remaining <= 0:
                break
            self.publisher_.publish(msg)
            time.sleep(min(self.PUBLISH_PERIOD, remaining))

    @staticmethod
    def _as_number(value, name):
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number, got {type(value).__name__}")
        return value
