from __future__ import print_function
from __future__ import division 
import copy
import numpy as np
import time

class Agent0(object):

    def __init__(self, env, goal_left, recursion_depth=3):
        """
        env: should be Foosball environment object.
        goal_left: True if player goal is on left side (note sure).
        recursion_depth: How many wall bounces into the future to consider.
        """
        self.env = env
        self.goal_left = goal_left
        self.recursion_depth = recursion_depth
        # get wall lines and bounds.
        self.upper_bound = self.env.ball_radius
        self.lower_bound = self.env.height - self.env.ball_radius
        self.left_bound = self.env.ball_radius
        self.right_bound = self.env.width - self.env.ball_radius
        self.top_wall = self.line([self.left_bound, self.upper_bound], [self.right_bound, self.upper_bound])
        self.bottom_wall = self.line([self.left_bound, self.lower_bound], [self.right_bound, self.lower_bound])
        self.left_wall = self.line([self.left_bound, self.upper_bound], [self.left_bound, self.lower_bound])
        self.right_wall = self.line([self.right_bound, self.upper_bound], [self.right_bound, self.lower_bound])
        # get player lines and bounds. 
        self.players = [player for player in self.env.players if player.goal_left == goal_left]
        self.player_lines = []
        for player in self.players:
            self.player_lines.append(self.line([player.x, self.upper_bound], [player.x, self.lower_bound]))
        # --------------------------
        self.previous_velocity = np.zeros(2, dtype=np.float32)
        self.target_positions = [None, None, None, None] # target y positions for each player (where the ball will be)

    def line(self, p1, p2):
        A = (p1[1] - p2[1])
        B = (p2[0] - p1[0])
        C = (p1[0]*p2[1] - p2[0]*p1[1])
        return A, B, -C

    def intersection(self, L1, L2):
        D  = L1[0] * L2[1] - L1[1] * L2[0]
        Dx = L1[2] * L2[1] - L1[1] * L2[2]
        Dy = L1[0] * L2[2] - L1[2] * L2[0]
        if D != 0:
            x = Dx / D
            y = Dy / D
            return x,y
        else:
            return False

    def bounce(self, ball_pos, ball_vel):
        """
        Given a wall intersection point and a current ball velocity, return
        a new ball velocity.
        """
        new_vel = copy.deepcopy(ball_vel)
        new_pos = list(copy.deepcopy(ball_pos))
        if ball_pos[0] <= self.left_bound+0.5:
            new_vel[0] *= -1
            new_pos[0] = self.left_bound+0.5
        if ball_pos[1] <= self.upper_bound+0.5:
            new_vel[1] *= -1
            new_pos[1] = self.upper_bound+0.5
        if ball_pos[0] >= self.right_bound-0.5:
            new_vel[0] *= -1
            new_pos[0] = self.right_bound-0.5
        if ball_pos[1] >= self.lower_bound-0.5:
            new_vel[1] *= -1
            new_pos[1] = self.lower_bound-0.5
        return new_vel, new_pos

    def predict_player_intersections(self, ball_pos, ball_vel, ref_time, rec_depth=0):
        """
        Takes ball position ``ball_pos``, ball velocity ``ball_vel``, and current time ``ref_time`` as input.
        Returns list of predicted player intersection y-coordinates along with the predicted time of said event.
        Format: [<player_0>, <player_1>, <player_2>, <player_4>] where <player...> is a tuple (<y-position>, <direction>, <time>)
        Returns ``None`` when there is no predicted intersection for a given player.
        Example: [None, None, None, (20.0, True, 259.0)]; ball intersects player 4 line at y=20, towards our goal, at time 259.

        Note: ^^^ predicted time not yet implemented.
        """
        if rec_depth >= self.recursion_depth: # recursion depth exceeded.
            print('Warning: recursion depth exceeded.')
            return [None, None, None, None]
        # Calculate ball vector line from position and velocity
        ball_line = self.line([ball_pos[0], ball_pos[1]], [ball_pos[0]+ball_vel[0]*1.0, ball_pos[1]+ball_vel[1]*1.0])
        # Calculate intersection between the ball vector line and player lines.
        player_intersections = [None, None, None, None]
        for idx, player_line in enumerate(self.player_lines):
            if (ball_vel[0] > 0 and self.players[idx].x > ball_pos[0]) or (ball_vel[0] < 0 and self.players[idx].x < ball_pos[0]):
                intersection = self.intersection(ball_line, player_line)
                if intersection:
                    x, y = intersection
                    if x > self.left_bound and x < self.right_bound and y > self.upper_bound and y < self.lower_bound:
                        player_intersections[idx] = (intersection[1], ball_vel[0] > 0, 0.0)
        if not all([i is None for i in player_intersections]):
            return player_intersections # calculate intersection times and directions. TODO
        else: # if there are no player line intersections, then find intersection with wall.
            wall0 = self.right_wall if ball_vel[0] > 0 else self.left_wall # consider ball vector direction when evaluating walls.
            wall1 = self.bottom_wall if ball_vel[1] > 0 else self.top_wall
            wall_intersections = [self.intersection(ball_line, wall) for wall in [wall0, wall1]]
            wall_intersections = [intersection for intersection in wall_intersections if intersection is not None]
            wall_collisions = [(x, y) for (x, y) in wall_intersections if x >= self.left_bound and x <= self.right_bound and y >= self.upper_bound and y <= self.lower_bound]
            wall_collision_pos = wall_collisions[0] if len(wall_collisions) > 0 else None
            if wall_collision_pos is None:
                print('Warning: wall_collision_pos is None')
                return [None, None, None, None]
            new_vel, new_pos = self.bounce(wall_collision_pos, ball_vel)
            return self.predict_player_intersections(new_pos, new_vel, 0, rec_depth=rec_depth+1) # TODO add ref_time

    def servo_players(self):
        """
        Move paddles to target positions.
        """
        moves = [(1,0), (5,4), (9,8), (13,12)] # (up, down)
        for idx, target_y in enumerate(self.target_positions):
            if target_y is not None:
                # Select which guy to use as the servoing reference.
                positions = [y + self.players[idx].offset for y in self.players[idx].ys]
                candidate_ys = [idx_ for idx_, y in enumerate(self.players[idx].ys) if target_y >= y and target_y <= y + self.players[idx].max_y]
                if len(candidate_ys) > 0:
                    ordered = sorted([(abs(positions[idx_]-target_y), idx_) for idx_ in candidate_ys])
                    position = positions[ordered[0][1]] # Select the closest guy.
                    if position > target_y + 1.0 and self.players[idx].offset > 0:
                        return moves[idx][0] # move up
                    elif position < target_y - 1.0 and self.players[idx].offset < self.players[idx].max_y:
                        return moves[idx][1] # move down
        return 8 # arbitrary action.

    def select_action(self):
        """
        Select an action based on predictions of ball movement.
        """
        if np.array_equal(self.env.ball_vel, self.previous_velocity): # only recalculate if ball velocity changes.
            return self.servo_players()
        print('recalculating', time.time())
        self.previous_velocity = copy.deepcopy(self.env.ball_vel)
        player_intersections = self.predict_player_intersections(self.env.ball_pos, self.env.ball_vel, 0.01) # Note: Hardcoded time.
        for idx, intersection in enumerate(player_intersections):
            if intersection is not None:
                (y, moving_right, ts) = intersection
                if moving_right == self.goal_left: # Slightly confusing.
                    # move intersecting players into the path of the ball.
                    self.target_positions[idx] = intersection[0] # set y position as target.
                else: # ball heading away from our goal.
                    self.target_positions[idx] = intersection[0] + 200.0/len(self.players[idx].ys) # move intersecting players out of the way.
        # ---------------------------------------------------------
        move = self.servo_players()
        return move
