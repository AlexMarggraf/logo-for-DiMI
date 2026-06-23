import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from tts_msgs.action import TTS

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
    
def main():
    rclpy.init()

    node = TTSClient()
    node.speak("sane raus undav rein")

    rclpy.spin_once(node, timeout_sec=2.0)

    node.destroy_node()
    rclpy.shutdown() 

if __name__ == "__main__":
    main()
