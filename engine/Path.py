"""
    'path' for things to move around on screen
"""
import math, random, os
import pygame
from pygame.locals import QUIT, KEYUP, K_ESCAPE
import conf
import Utility
from locals import PI, PIx2

class EndOfPath(Exception):
    """Raise at the end of a path."""
    pass

class Path:
    """A set of points."""

    def __init__(self, position=(0, 0), duration=None):
        """Initialize the Path

        @param position: initial coordinates
        @param duration: Seconds until Path should raise C{StopIteration}

        """

        self.position = [0, 0]
        self.position_old = [0, 0]
        self.set_position(position)
        self.position_old = self.position[:]
        self.direction_old = 0.0
        self.duration = duration
        self.set_end_time()
        self.paused = None

    def set_end_time(self, duration=None):
        """Path will raise StopIteration after self.duration seconds

        @param duration: Seconds until Path should raise C{StopIteration}.
            If duration is not specified (or is None) uses
            C{self.duration} so that C{set_endTime()} can be used to
            reset the C{Path} duration counter.

        """
        if duration is not None:
            self.duration = duration
        if self.duration is not None:
            self.endTime = pygame.time.get_ticks() + self.duration * 1000
        else:
            self.endTime = None

    def __iter__(self):
        return self

    def set_position(self, position):
        """Set position and update positionOld

        For many paths, this position will be overridden
        by the next call to next() and so it will never
        be seen.

        Also, many Drawable objects maintain their own position
        and so a call to that object's set_position may be more
        appropriate.

        """
        self.position_old[0], self.position_old[1] = self.position[0], self.position[1]
        self.position[0], self.position[1] = position[0], position[1]

    def get_position(self):
        """Return position along Path"""

        return self.position[0:2]

    def get_direction(self):
        """Return the direction from the previous location to the current location.

        """
        x, y = self.get_position()
        xo, yo = self.position_old
        dx = x - xo
        dy = y - yo
        direction = math.atan2(-dy, dx)
        if dx or dy:
            self.direction_old = direction
            return direction
        else:
            return self.direction_old

    def get_x(self):
        """return x component of position"""
        return self.position[0]

    def get_y(self):
        """return y component of position"""
        return self.position[1]

    def next(self):
        """return position

        @raises StopIteration: If duration has expired, or
        if position has been set to (None, None)

        """
        stop = 0
        if self.endTime is not None:
            t = pygame.time.get_ticks()
            if t > self.endTime:
                stop = 1
        position = self.get_position()
        if position == (None, None):
            stop = 1
        if stop:
            raise StopIteration
        else:
            return position

    def reset(self):
        """put path back to original state"""
        if self.duration is not None:
            self.set_end_time()

    def pause(self):
        """stop moving along path"""
        self.paused = pygame.time.get_ticks()

    def unpause(self):
        """resume moving along path"""
        self.paused = None
        self.ticks = pygame.time.get_ticks()

    def is_on_screen(self, slack=0):
        """true if path position is on main window

        Drawable objects should be using the C{pygsear.Drawable.onscreen} instead.

        @param slack: position can be this far off window and still return True.

        """
        x, y = self.get_position()
        minX = -slack
        minY = -slack
        maxX = conf.WINWIDTH + slack
        maxY = conf.WINHEIGHT + slack

        if (x >= minX and y >= minY and
                x <= maxX and y <= maxY):
            return 1
        else:
            return 0


class ComplexObjectPath(Path):
    def __init__(self, startLocation=(100, 100),
                    vx=0, vy=0,
                    ax=0, ay=0,
                    gx=0, gy=0, # gx, gy is constant accel part (ie gravity)
                    duration=None):
        
        Path.__init__(self, startLocation, duration=duration)
        self.set_startLocation(startLocation)
        self.set_startVelocity((vx, vy))
        self.set_startAcceleration((ax, ay))
        self.set_gravity(gx, gy)
        self.set_restriction()
        self.reset()

    def reset(self):
        """
            go to initial position, velocity and acceleration
        """
        self._direction = 0
        self.set_position(self.startLocation)
        self.set_velocity(vx=self.vx0, vy=self.vy0)
        self.set_acceleration(ax=self.ax0, ay=self.ay0)
        self.speed_sign = 1
        self.set_turnRate()

    def set_restriction(self, onscreen=None, **kw):
        """Set a constraint on the path.

        Restrictions are set as keyword arguments. So far these are
        the contraints that work:
            - speed: maximum speed

            - xMin: minimum x-value
            - yMin: minimum y-value
            - xMax: maximum x-value
            - yMax: maximum y-value

            - vxMin: minimum x-velocity (remember negative values)
            - vyMin: minimum y-velocity
            - vxMax: maximum x-velocity
            - vyMax: maximum y-velocity

        @param onscreen: set to nonzero value if the object should be limited
            to staying on the screen.

        """

        if onscreen is not None:
            self.restriction['xMin'] = 0
            self.restriction['yMin'] = 0
            self.restriction['xMax'] = conf.WINWIDTH
            self.restriction['yMax'] = conf.WINHEIGHT

        if not hasattr(self, 'restriction'):
            self.restriction = {    'speed': 2000,

                                    'vxMax': 5000,
                                    'vxMin': -5000,
                                    'vyMax': 5000,
                                    'vyMin': -5000,

                                    'xMax': None,
                                    'xMin': None,
                                    'yMax': None,
                                    'yMin': None,
                                }

        for side, val in kw.items():
            self.restriction[side] = val

    def show_restrictions(self):
        if hasattr(self, 'restriction'):
            for key, val in self.restriction.items():
                print key, val

    def set_startLocation(self, location=None):
        """Set location to go back to on reset()


        @param location: (x, y) position
            If location is not given (or None), sets startLocation to
            current location.

        """

        if location is None:
            location = self.get_position()
        self.startLocation = location

    def set_startVelocity(self, vel=None):
        """Set velocity to go back to on reset()

        @param vel: (vx, vy) horizontal and vertical velocity components

        """
        if vel is None:
            vel = self.get_velocity()
        self.vx0, self.vy0 = vel

    def set_startAcceleration(self, accel=None):
        """Set acceleration to back go to on reset()

        @param accel: (ax, ay) horizontal and vertical acceleration components

        """
        if accel is None:
            accel = self.get_acceleration()
        self.ax0, self.ay0 = accel

    def _set_velocity(self, vx=None, vy=None):
        if vx is not None:
            self.vx = vx
        if vy is not None:
            self.vy = vy

    def set_velocity(self, special=None, vx=None, vy=None):
        """Set velocity

        @param special: Set to 'random' for a random velocity
        @param vx: horizontal velocity component
        @param vy: vertical velocity component

        """

        vxMax = self.restriction['vxMax']
        vxMin = self.restriction['vxMin']
        vyMax = self.restriction['vyMax']
        vyMin = self.restriction['vyMin']
        max_speed = self.restriction['speed']

        if special == 'random':
            if vx is None:
                vx = random.uniform(vxMin, vxMax)
            if vy is None:
                vy = random.uniform(vyMin, vyMax)

        if vx is not None:
            vx = max(vx, vxMin)
            vx = min(vx, vxMax)
        if vy is not None:
            vy = max(vy, vyMin)
            vy = min(vy, vyMax)

        self._set_velocity(vx, vy)

        speed = self.get_speed()
        if speed > max_speed:
            self.set_speed(max_speed)

    def get_velocity(self):
        """return velocity"""

        return self.vx, self.vy

    def get_speed(self):
        """return speed"""

        vx = self.vx
        vy = self.vy
        return math.hypot(vx, vy)

    def set_speed(self, speed=None, change=None):
        """Change speed while keeping the same direction of movement.

        @param speed: New speed (must set speed OR change)
        @param change: Change in speed (must set speed OR change)

        """

        if (speed is None and change is None) or (speed is not None and change is not None):
            raise TypeError, 'must give speed or acceleration'

        d = self.get_direction()
        sign = self.speed_sign
        if speed is not None:
            if speed < 0:
                self.speed_sign = -1
                if sign >= 0:
                    d += PI
                speed = abs(speed)

            else:
                self.speed_sign = 1

            vx = speed * math.cos(d)
            vy = -speed * math.sin(d)
            self._set_velocity(vx, vy)

        else:
            speed = self.get_speed()
            speed += change
            self.set_speed(speed)

    def get_direction(self):
        """return direction of travel

        Direction is given in radians. 0 radians is towards the right
        edge of the screen.

        """

        vx = self.vx
        vy = self.vy

        if vx and vy:
            direction = math.atan2(-self.vy, self.vx)
            self._direction = direction
        else:
            direction = self._direction

        return direction

    def set_direction(self, direction):
        """set direction of travel

        Maintains current speed.

        """

        s = self.get_speed()
        vx = s * math.cos(direction)
        vy = s * math.sin(direction)
        self.set_velocity(vx=vx, vy=-vy)

    def distance(self, point):
        """return distance to a point"""

        x, y = self.get_position()
        x1, y1 = point

        return math.hypot((x1 - x), (y1 - y))

    def direction(self, point):
        """return direction to a point"""

        x, y = self.get_position()
        x1, y1 = point

        return math.atan2(-(y1 - y), (x1 - x))

    def set_turnRate(self, turnRate=0):
        """set turn rate in rad/s"""

        self.turnRate = turnRate

    def turn(self, rad=None):
        """turn to the left by radians"""

        #print rad
        direction = self.get_direction()
        #print 'dr', direction, rad
        self.set_direction(direction + rad)

    def turn_right(self):
        self.set_turnRate(-1)

    def turn_left(self):
        self.set_turnRate(1)

    def turn_straight(self):
        self.set_turnRate()

    def turn_towards(self, point):
        """turn as quickly as possible towards a point"""

        direction = self.direction(point)
        moving = self.get_direction()

        rad = (moving - direction) % PIx2

        if rad > PI:
            rad -= PIx2
        elif rad < -PI:
            rad += PIx2

        if rad > 0.1:
            self.turn_right()
        elif rad < -0.1:
            self.turn_left()
        else:
            self.turn_straight()

    def set_acceleration(self, ax=None, ay=None):
        """Set acceleration. Change in speed depends on the
        acceleration and the time between frames.

        @param ax: horizontal acceleration component
        @param ay: vertical acceleration component

        """

        if ax is not None:
            self.ax = ax
            self.dex = False
        if ay is not None:
            self.ay = ay
            self.dey = False

    def accelerate(self, acc):
        """Accelerate in the direction currently moving.

        Accelerates toward 0 (right side of screen) if not moving.

        """

        direction = self.get_direction()
        ax = acc * math.cos(direction)
        ay = acc * math.sin(direction)

        self.set_acceleration(ax=ax, ay=ay)

    def get_acceleration(self):
        """return acceleration

        Note that the acceleration may actually be a deceleration.

        """

        return self.ax, self.ay

    def set_deceleration(self, dex=None, dey=None):
        """Set deceleration. Like acceleration, but acts to oppose
        the current velocity and will not change a 0 velocity.

        Can only accelerate or decelerate in a particular direction.

        Note that when using deceleration, the ax or ay value is always
        kept as an absolute value and a deceleration flag. There is no
        way to do "negative acceleration".

        @param dex: horizontal acceleration component
        @param dey: vertical acceleration component

        """

        vx, vy = self.get_velocity()
        if dex is not None:
            self.ax = abs(dex)
            self.dex = True
        if dey is not None:
            self.ay = abs(dey)
            self.dey = True

    def decelerate(self, dec):
        """Decelerate according to the direction currently moving.

        """

        direction = self.get_direction()
        dex = dec * math.cos(direction)
        dey = dec * math.sin(direction)

        self.set_deceleration(dex=dex, dey=dey)

    def set_gravity(self, gx=None, gy=None):
        """Set constant portion of acceleration (ie gravity)

        @param gx: horizontal acceleration component
        @param gy: vertical acceleration component

        """

        if gx is not None:
            self.gx = gx
        if gy is not None:
            self.gy = gy

    def next(self, t=None):
        """return next position along path"""

        if t is None:
            ticks = conf.ticks
            dt = min(ticks, conf.MAX_TICK)
            t = dt / 1000.0

        if self.turnRate:
            self.turn(self.turnRate * t)

        sign = self.speed_sign
        vx, vy = self.get_velocity()
        ax, ay = self.get_acceleration()

        if self.dex:
            if vx > 0:
                ax = -ax
        if self.dey:
            if vy > 0:
                ay = -ay

        Ax = self.gx + ax
        Ay = self.gy + ay
        vx = sign * self.vx + (Ax * t)
        vy = sign * self.vy + (Ay * t)

        self.set_velocity(vx=vx, vy=vy)

        x, y = self.get_position()
        x += (vx * t) + (Ax * t**2) / 2
        y += (vy * t) + (Ay * t**2) / 2

        xMax = self.restriction.get('xMax', None)
        xMin = self.restriction.get('xMin', None)
        yMax = self.restriction.get('yMax', None)
        yMin = self.restriction.get('yMin', None)

        if xMax is not None:
            x = min(x, xMax)
        if xMin is not None:
            x = max(x, xMin)
        if yMax is not None:
            y = min(y, yMax)
        if yMin is not None:
            y = max(y, yMin)

        self.set_position((x, y))
        return Path.next(self)

    def bounce_x(self):
        """reverse travel in x-direction"""
        self.vx = -self.vx

    def bounce_y(self):
        """reverse travel in y-direction"""
        self.vy = -self.vy


class VelocityPath(Path):
    """Move according to velocity in pixels per frame."""

    def __init__(self, startLocation=(100, 100), vx=0, vy=0, duration=None):
        Path.__init__(self, startLocation, duration=duration)
        self.set_velocity(vx, vy)

    def next(self):
        x, y = self.position
        position = (x+self.vx, y+self.vy)
        self.set_position(position)
        return Path.next(self)

    def accelerate(self, ax=0, ay=0):
        self.set_velocity(self.vx+ax, self.vy+ay)

    def set_velocity(self, vx=None, vy=None):
        if vx is not None:
            self.vx = vx
        if vy is not None:
            self.vy = vy

    def get_speed(self):
        vx = self.vx
        vy = self.vy
        return math.hypot(vx, vy)

    def get_direction(self):
        return math.atan2(self.vy, self.vx)


class AccelerationPath(VelocityPath):
    """Move according to vel and accel in pixels per second."""

    def __init__(self, startLocation=(100, 100),
                    vx=0, vy=0,
                    ax=0, ay=0,
                    gx=0, gy=0, # gx, gy is constant accel part (ie gravity)
                    duration=None):
        VelocityPath.__init__(self, startLocation, vx, vy, duration=duration)
        self.vx0, self.vy0 = vx, vy
        self.ax0, self.ay0 = ax, ay
        self.gx0, self.gy0 = gx, gy
        self.reset()

    def reset(self):
        self.set_velocity(self.vx0, self.vy0)
        self.set_acceleration(self.ax0, self.ay0)
        self.set_gravity(self.gx0, self.gy0)
        self.ticks = pygame.time.get_ticks()

    def set_acceleration(self, ax=None, ay=None):
        if ax is not None:
            self.ax = ax
        if ay is not None:
            self.ay = ay

    def set_gravity(self, gx=None, gy=None):
        if gx is not None:
            self.gx = gx
        if gy is not None:
            self.gy = gy

    def next(self, t=None):
        """Use velocity and acceleration info to move sprite,
        and return position.

        @param t: Number of ticks since last update.

        @returns: position.

        """

        if t is None:
            ticks = pygame.time.get_ticks()
            t = ticks - self.ticks
            self.ticks = ticks

        Ax = self.gx + self.ax
        Ay = self.gy + self.ay
        self.vx += Ax * t
        self.vy += Ay * t

        x, y = self.get_position()
        x += (self.vx * t) + (Ax * t**2) / 2
        y += (self.vy * t) + (Ay * t**2) / 2
        self.set_position((x, y))
        return Path.next(self)