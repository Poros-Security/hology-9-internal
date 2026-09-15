# Intended solve material

`send_waypoints.py` is maintainer-only validation material. It is not shipped
to players and does not contain a route or maze solution. The intended solve is:

1. Start the team's DynamicContainer and launch the client against its instance
   address.
2. Use SuiNav to inspect the visible maze and choose a collision-free route.
3. Export those player-selected points and run the Python script.
4. The client uploads the MAVLink recording; the verifier independently replays
   it and returns that container's dynamic flag only if the target hold succeeds.

The generic runner splits long straight legs but never finds detours around
walls. A player may use their own pymavlink script instead.
