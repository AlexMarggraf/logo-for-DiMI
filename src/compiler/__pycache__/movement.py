class Movement(Node):

    def __init__(self):
        super().__init__("movement")

        self.publisher_ = self.create_publisher(
            Twist,
            "/mobile_base_controller/cmd_vel",
            10
        )

        self.history = []
        self.heading = 0

    def fd(self, cm):
        meters = cm / 100.0

        self.history.append(("fd", cm))

        msg = Twist()
        msg.linear.x = 0.1

        duration = meters / 0.1
        end_time = time.time() + duration

        while time.time() < end_time:
            self.publisher_.publish(msg)
            time.sleep(0.1)

        self.stop()

    def bk(self, cm):
        meters = cm / 100.0

        self.history.append(("bk", cm))

        msg = Twist()
        msg.linear.x = -0.1

        duration = meters / 0.1
        end_time = time.time() + duration

        while time.time() < end_time:
            self.publisher_.publish(msg)
            time.sleep(0.1)

        self.stop()

    def rt(self, angle):
        self.history.append(("rt", angle))

        angular_speed = 0.3

        msg = Twist()
        msg.angular.z = -angular_speed

        duration = math.radians(angle) / angular_speed
        end_time = time.time() + duration

        while time.time() < end_time:
            self.publisher_.publish(msg)
            time.sleep(0.1)

        self.heading = (self.heading + angle) % 360
        self.stop()

    def lt(self, angle):
        self.history.append(("lt", angle))

        angular_speed = 0.3

        msg = Twist()
        msg.angular.z = angular_speed

        duration = math.radians(angle) / angular_speed
        end_time = time.time() + duration

        while time.time() < end_time:
            self.publisher_.publish(msg)
            time.sleep(0.1)

        self.heading = (self.heading - angle) % 360
        self.stop()

    def setheading(self, target):
        difference = target - self.heading

        if difference > 180:
            difference -= 360

        if difference < -180:
            difference += 360

        if difference > 0:
            self.rt(difference)
        else:
            self.lt(abs(difference))

        self.heading = target

    def home(self):
        commands = list(reversed(self.history))

        for command, value in commands:
            if command == "fd":
                self.bk(value)
            elif command == "bk":
                self.fd(value)
            elif command == "rt":
                self.lt(value)
            elif command == "lt":
                self.rt(value)

    def stop(self):
        msg = Twist()
        self.publisher_.publish(msg)
        time.sleep(1)