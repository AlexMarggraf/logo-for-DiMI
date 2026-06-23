import math
import time
import importlib
from rclpy.action import ActionClient
import threading

from geometry_msgs.msg import Twist
from rclpy.node import Node


class Movement(Node):
    """ROS2 movement helper for DiMI/Tiago Logo commands.

    Distances are interpreted as centimeters, angles as degrees.
    Movement is open-loop/time-based: good enough for simple Logo demos, but not
    as accurate as odometry-based navigation.
    """

    LINEAR_SPEED = 0.2      # m/s
    ANGULAR_SPEED = 0.6     # rad/s
    PUBLISH_PERIOD = 0.1    # seconds
    STOP_SETTLE_TIME = 0.2  # seconds

    def __init__(self):
        super().__init__("movement")

        self.publisher_ = self.create_publisher(
            Twist,
            "/cmd_vel",
            10,
        )

        self.heading = 0
        self.x = 0
        self.y = 0

    def text_to_speech(self, text, wait=True):
        """Speak ``text`` out loud through the robot's TTS action server.

        This node is spun by a background executor in server.py, so we wait on the
        action futures via callbacks instead of spinning the node ourselves (which
        would clash with that executor). Degrades gracefully: if the TTS package or
        server is unavailable, it logs a warning and returns instead of crashing the
        Logo run.
        """

        text = str(text)
        if not text:
            return

        try:

            action_module = importlib.import_module(self.TTS_ACTION_MODULE)
            action_type = getattr(action_module, self.TTS_ACTION_CLASS)
        except (ImportError, AttributeError):
            self.get_logger().warning(
                "TTS action type not available; cannot speak."
            )
            return

        client = ActionClient(self, action_type, self.TTS_ACTION_NAME)

        if not client.wait_for_server(timeout_sec=self.TTS_TIMEOUT):
            self.get_logger().warning(
                f"TTS server '{self.TTS_ACTION_NAME}' not available; cannot speak."
            )
            return

        goal = action_type.Goal()
        goal.rawtext.text = text
        goal.rawtext.lang_id = self.TTS_LANGUAGE

        def await_future(future, timeout):
            done = threading.Event()
            future.add_done_callback(lambda _f: done.set())
            if not done.wait(timeout):
                return None
            return future.result()

        goal_handle = await_future(client.send_goal_async(goal), self.TTS_TIMEOUT)

        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().warning("TTS goal was not accepted.")
            return

        if wait:
            await_future(goal_handle.get_result_async(), timeout=None)

    # Friendly alias for Logo/action_set names.
    say = text_to_speech

    def fd(self, cm):
        """Move forward by ``cm`` centimeters."""
        cm = self._as_number(cm, "cm")

        if cm < 0:
            return self.bk(-cm)
        if cm == 0:
            return

        self._move(linear_x=self.LINEAR_SPEED, distance_cm=cm)

        self.x += math.sin(math.radians(self.heading)) * cm
        self.y += math.cos(math.radians(self.heading)) * cm
        self.print_coords()

        return None

    def bk(self, cm):
        """Move backward by ``cm`` centimeters."""
        cm = self._as_number(cm, "cm")

        if cm < 0:
            return self.fd(-cm)
        if cm == 0:
            return

        self._move(linear_x=-self.LINEAR_SPEED, distance_cm=cm)

        self.x -= math.sin(math.radians(self.heading)) * cm
        self.y -= math.cos(math.radians(self.heading)) * cm

        self.print_coords()
        return None

    def print_coords(self):
        print(f"curr cords x {self.x} y {self.y} heading {self.heading}")

    def set_x(self, new_x):
        if self.x == new_x:
            return None

        start_heading = self.heading
        self.setheading(90)
        self.fd(new_x - self.x)
        self.setheading(start_heading)
        self.print_coords()

        return None

    def set_y(self, new_y):
        print(f"set y {new_y}")
        if self.y == new_y:
            return None

        start_heading = self.heading
        self.setheading(0)
        self.fd(new_y - self.y)
        self.setheading(start_heading)
        self.print_coords()

        return None

    def set_xy(self, new_x, new_y):
        if self.x == new_x and self.y == new_y:
            return None
    

        start_heading = self.heading
        x_diff = self.x - new_x
        y_diff = self.y - new_y
        target_heading = math.degrees(math.atan2(x_diff, y_diff))
        print(f"xdiff {x_diff} ydiff {y_diff} target {target_heading}")
        self.setheading(target_heading)

        distance = math.sqrt(x_diff**2 + y_diff**2)

        self.bk(distance)        
        self.setheading(start_heading)

        self.print_coords()

        return None

    def move_x(self, cm, record=True, command_name="move_x"):
        """Move along the robot's X axis.

        Positive values move forward, negative values move backward.
        """
        cm = self._as_number(cm, "cm")

        if cm == 0:
            return

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


        self._rotate(angle, angular_z=-self.ANGULAR_SPEED)
        self.heading = (self.heading + angle) % 360

    def lt(self, angle, record=True):
        """Turn left by ``angle`` degrees."""
        angle = self._as_number(angle, "angle")

        if angle < 0:
            return self.rt(-angle, record=record)
        if angle == 0:
            return

        self._rotate(angle, angular_z=self.ANGULAR_SPEED)
        self.heading = (self.heading - angle) % 360

    def setheading(self, target):
        """Turn to an absolute heading using the shortest direction."""
        target = self._as_number(target, "target") % 360
        difference = (target - self.heading + 180) % 360 - 180
        print(f"setheading {target} difference {difference}")

        self.rt(difference)

    def home(self):
        self.set_xy(0, 0)

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
