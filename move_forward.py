timeout 5 ros2 topic pub /mobile_base_controller/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}, angular: {z: 0.0}}" --rate 10
