import math
import time
from rclpy.node import Node
from rclpy.action import ActionClient
from tts_msgs.action import TTS
from geometry_msgs.msg import Twist


class Movement(Node):

    LINEAR_SPEED = 0.2
    ANGULAR_SPEED = 0.6
    PUBLISH_PERIOD = 0.1
    STOP_SETTLE_TIME = 0.2

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

    def fd(self, cm):
        cm = self._as_number(cm, "cm")

        if cm < 0:
            return self.bk(-cm)
        if cm == 0:
            return

        self._move(linear_x=self.LINEAR_SPEED, distance_cm=cm)

        self.x += math.sin(math.radians(self.heading)) * cm
        self.y += math.cos(math.radians(self.heading)) * cm

        return None

    def bk(self, cm):
        cm = self._as_number(cm, "cm")

        if cm < 0:
            return self.fd(-cm)
        if cm == 0:
            return

        self._move(linear_x=-self.LINEAR_SPEED, distance_cm=cm)

        self.x -= math.sin(math.radians(self.heading)) * cm
        self.y -= math.cos(math.radians(self.heading)) * cm

        return None

    def set_x(self, new_x):
        if self.x == new_x:
            return None

        self.setheading(90)
        self.fd(new_x - self.x)
        self.setheading(0)

        return None

    def set_y(self, new_y):
        if self.y == new_y:
            return None

        self.setheading(0)
        self.fd(new_y - self.y)
        self.setheading(0)

        return None

    def set_xy(self, new_x, new_y):
        if self.x == new_x and self.y == new_y:
            return None
    
        x_diff = self.x - new_x
        y_diff = self.y - new_y
        target_heading = math.degrees(math.atan2(x_diff, y_diff))
        self.setheading(target_heading)

        distance = math.sqrt(x_diff**2 + y_diff**2)

        self.bk(distance)        
        self.setheading(0)

        return None

    def move_x(self, cm, record=True, command_name="move_x"):
        cm = self._as_number(cm, "cm")

        if cm == 0:
            return

        direction = 1 if cm > 0 else -1
        self._move(linear_x=direction * self.LINEAR_SPEED, distance_cm=abs(cm))

    def move_y(self, cm, record=True, command_name="move_y"):
        cm = self._as_number(cm, "cm")

        if cm == 0:
            return

        direction = 1 if cm > 0 else -1
        self._move(linear_y=direction * self.LINEAR_SPEED, distance_cm=abs(cm))

    movex = move_x
    movey = move_y

    def rt(self, angle, record=True):
        angle = self._as_number(angle, "angle")

        if angle < 0:
            return self.lt(-angle, record=record)
        if angle == 0:
            return


        self._rotate(angle, angular_z=-self.ANGULAR_SPEED)
        self.heading = (self.heading + angle) % 360

    def lt(self, angle, record=True):
        angle = self._as_number(angle, "angle")

        if angle < 0:
            return self.rt(-angle, record=record)
        if angle == 0:
            return

        self._rotate(angle, angular_z=self.ANGULAR_SPEED)
        self.heading = (self.heading - angle) % 360

    def setheading(self, target):
        target = self._as_number(target, "target") % 360
        difference = (target - self.heading + 180) % 360 - 180

        self.rt(difference)

    def home(self):
        self.set_xy(0, 0)

    def stop(self):
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
    
    def text_to_speech(self, text):
        node = TTSClient()
        node.speak(text)
        node.destroy_node()

    @staticmethod
    def _as_number(value, name):
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number, got {type(value).__name__}")
        return value

class TTSClient(Node):
    def __init__(self):
        super().__init__('tts_client')

        self.client = ActionClient(
            self,
            TTS,
            '/tts_engine/tts'
        )

        self.client.wait_for_server()

    def speak(self, text):
        goal = TTS.Goal()
        goal.input = text
        goal.locale = "en_US"

        self.client.send_goal_async(goal)
