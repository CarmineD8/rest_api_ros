import threading
from flask import Flask, request, jsonify

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped



class Nav2API(Node):
    def __init__(self):
        super().__init__("rest_api_gateway")
        self.action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')


app = Flask(__name__)

rclpy.init()
node = Nav2API()



@app.route("/go_to", methods=["POST"])
def go_to():

    # Prende parametri da query string
    x = float(request.args.get("x", 0.0))
    y = float(request.args.get("y", 0.0))
    yaw = float(request.args.get("yaw", 0.0))

    if not node.action_client.wait_for_server(timeout_sec=2.0):
        return jsonify({"error": "NavigateToPose Action Server not available"})

    goal_msg = NavigateToPose.Goal()
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.w = 1.0  # Yaw semplificato

    goal_msg.pose = pose

    # Invia goal
    future_goal = node.action_client.send_goal_async(goal_msg)
    rclpy.spin_until_future_complete(node, future_goal)

    goal_handle = future_goal.result()
    if not goal_handle.accepted:
        return jsonify({"status": "Goal rejected"})

    # Aspetta il risultato
    future_result = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, future_result)

    result = future_result.result()

    return jsonify({"status": "Goal finished", "result": str(result)})


def ros_spin():
    rclpy.spin(node)


if __name__ == "__main__":
    
    # Thread dedicato a ROS2
    ros_thread = threading.Thread(target=ros_spin, daemon=True)
    ros_thread.start()

    ip = "0.0.0.0"
    port = 8000

    print("\n======================================")
    print("  ROS2 + REST API NAVIGATION GATEWAY  ")
    print("======================================")
    print(f"API on: http://{ip}:{port}")
    print("======================================\n")

    # Avvia Flask
    app.run(host=ip, port=port)
