"""Fly the points exported from SuiNav. Coordinates are north, east, down."""
import argparse
import csv
import math
import time
from pymavlink import mavutil


def load_points(path):
    with open(path, encoding="utf-8-sig") as file:
        return [tuple(map(float, row)) for row in csv.reader(
            line for line in file if line.strip() and not line.lstrip().startswith("#"))]


def subdivide(start, end):
    # Shorten straight legs to fit the game's 10.5 m / 3 m command limits.
    count = max(1, math.ceil(math.dist(start[:2], end[:2]) / 8),
                math.ceil(abs(end[2] - start[2]) / 2))
    return [tuple(a + (b-a)*i/count for a, b in zip(start, end))
            for i in range(1, count + 1)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    parser.add_argument("--port", type=int, default=14560)
    args = parser.parse_args()
    points = load_points(args.csv)

    drone = mavutil.mavlink_connection(f"udpout:127.0.0.1:{args.port}")
    # Register a local telemetry peer; start the game before running this script.
    while drone.wait_heartbeat(timeout=.5) is None:
        drone.mav.heartbeat_send(6, 8, 0, 0, 4)
    system, component = drone.target_system, drone.target_component

    def position():
        p = drone.recv_match(type="LOCAL_POSITION_NED", blocking=True, timeout=3)
        if p is None:
            raise SystemExit("Telemetry stopped; check the game's status.")
        while (newer := drone.recv_match(type="LOCAL_POSITION_NED", blocking=False)) is not None:
            p = newer
        return (p.x, p.y, p.z), math.hypot(p.vx, p.vy, p.vz)

    def send(point):
        drone.mav.set_position_target_local_ned_send(
            0, system, component, 1, 3576, *point, 0, 0, 0, 0, 0, 0, 0, 0)

    def fly(point):
        for _ in range(300):  # About a minute; don't wait forever on a blocked leg.
            send(point)
            time.sleep(.2)
            current, speed = position()
            if math.dist(current, point) < .25 and speed < .25:
                return
        raise SystemExit("Point not reached. Check the route for walls.")

    try:
        drone.mav.command_long_send(system, component, 400, 0, 1, 0, 0, 0, 0, 0, 0)
        drone.mav.set_mode_send(system, 1, 6)  # OFFBOARD
        fly(position()[0])  # Stop patrol first.
        for index, point in enumerate(points, 1):
            print(f"Point {index}/{len(points)}: {point}", flush=True)
            for target in subdivide(position()[0], point):
                fly(target)
        for _ in range(30):  # Keep sending the final point for six seconds.
            send(points[-1])
            time.sleep(.2)
        print("Done. Check SuiDrone for the completion result.")
    finally:
        drone.mav.set_mode_send(system, 1, 4)  # HOLD, including on Ctrl+C.
        drone.close()


if __name__ == "__main__":
    main()
