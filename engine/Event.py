"""
    Keyboard event handling
"""
import pygame
from pygame.locals import K_LSHIFT, K_RSHIFT, K_LCTRL, K_RCTRL, K_LALT, K_RALT, \
     KEYDOWN, KEYUP, QUIT
import conf

MODIFIERS = [K_LSHIFT, K_RSHIFT, K_LCTRL, K_RCTRL, K_LALT, K_RALT]
TIMEOUT = -1
KEY = -2
class Event(pygame.sprite.Sprite):
    """Relates Pygame Events with related actions."""

    def __init__(self, type, callback=None, **kwargs):
        """
            Initialize the event.
        """
        if kwargs.has_key('group'):
            group = kwargs['group']
            del(kwargs['group'])
        else:
            group = ()
        pygame.sprite.Sprite.__init__(self, group)

        self.type = type
        try:
            for t in type:
                if t > 0:
                    pygame.event.set_allowed(t)
        except TypeError:
            if type > 0:
                pygame.event.set_allowed(type)

        if callback is None:
            self.callback = self.nop
        else:
            self.callback = callback
        self.kwargs = kwargs

        self.enable()

    def add(self, group):
        """
            Add this event to an event group."""
        if group:
            pygame.sprite.Sprite.add(self, group)

    def enable(self):
        """Allow callbacks to go through."""

        self.enabled = 1

    def disable(self):
        """Do not allow callbacks to go through."""

        self.enabled = 0

    def nop(self, ev, **kwargs):
        """Do nothing."""

        pass

    def call(self, pygame_event, **kwargs):
        """
            Perform the callback, if enabled.
        """
        kwargs.update(self.kwargs)
        if self.enabled:
            self.callback(pygame_event, **kwargs)

class QUIT_Event(Event):
    def __init__(self, callback, **kwargs):
        """
            Initialize a QUIT Event
            - quit event is generated when the window close button is clicked.
            - callback: function to call when the event occurs.
            - kwargs: additional parameters passed to callback.
        """
        Event.__init__(self, QUIT, callback, **kwargs)


class KEY_Event(Event):
    """Keyboard events."""

    def __init__(self, type=KEY, key=None, callback=None, on_press=None, on_hold=None, on_release=None, **kwargs):
        """
            Initialize a keyboard event.
        """
        if type == KEY:
            group = EventGroup()
            if callback is not None:
                group.add(KEYDOWN_Event(key=key, callback=callback, **kwargs))
                group.add(KEYUP_Event(key=key, callback=callback, **kwargs))
            if on_press is not None:
                group.add(KEYDOWN_Event(key=key, callback=on_press, **kwargs))
            if on_release is not None:
                group.add(KEYUP_Event(key=key, callback=on_release, **kwargs))
            if on_hold is not None:
                group.add(TIMEOUT_Event(0, count=-1, callback=self.check_holding, **kwargs))
                group.add(KEYDOWN_Event(key=key, callback=self.press))
                group.add(KEYUP_Event(key=key, callback=self.release))
                self.key_held = 0
            self.contains = group
        else:
            self.contains = None
        Event.__init__(self, type, callback, **kwargs)

        self.on_press = on_press
        self.on_hold = on_hold
        self.on_release = on_release
        try:
            len(key)
            self.key = key
        except TypeError:
            if key is not None:
                self.key = [key]
            else:
                self.key = None

    def press(self, ev, **kwargs):
        self.key_held = 1

    def release(self, ev, **kwargs):
        self.key_held = 0

    def check_holding(self, ev, **kwargs):
        if self.key_held:
            self.on_hold(ev, **kwargs)

    def call(self, pygame_event, **kwargs):
        """
            perform the callback, if the event is enabled, and the key is pressed
        """
        if hasattr(pygame_event, 'key'):
            key = pygame_event.key
        else:
            raise TypeError
        if self.key is None or key in self.key:
            if self.contains is None:
                Event.call(self, pygame_event, **kwargs)
            else:
                pygame_event_type = pygame_event.type
                for event in self.contains.events():
                    event_type = event.type
                    if pygame_event_type == event_type:
                        event.call(pygame_event, **kwargs)


class KEYDOWN_Event(KEY_Event):
    def __init__(self, key=None, callback=None, **kwargs):
        """
            KEYDOWN is generated when the key is first pressed.
        """
        KEY_Event.__init__(self, KEYDOWN, key, callback, **kwargs)


class KEYUP_Event(KEY_Event):
    def __init__(self, key=None, callback=None, **kwargs):
        """
            KEYUP is generated when the key is released
        """
        KEY_Event.__init__(self, KEYUP, key, callback, **kwargs)


class TIMEOUT_Event(Event):
    def __init__(self, delay, count=1, callback=None, keepalive=False, **kwargs):
        """
            Init a TIMEOUT Event
        """

        Event.__init__(self, TIMEOUT, callback, **kwargs)
        self.delay = delay
        self.count_original = count
        self.keepalive = keepalive

        self.reset()

    def reset(self):
        self.ticks = self.delay
        self.set_count(self.count_original)
        self.enable()

    def set_count(self, count=1):
        self.count = count

    def tick(self, ticks):
        """
            count down ticks until time to call.
        """
        self.ticks -= ticks
        if self.ticks < 0:
            self.call(None)

    def call(self, pygame_event, **kwargs):
        Event.call(self, pygame_event, **kwargs)
        self.ticks = self.delay
        if self.count > 0:
            self.count -= 1

        if self.count == 0:
            self.disable()
            if not self.keepalive:
                self.kill()


class EventGroup(pygame.sprite.Group):
    def __init__(self, event=()):
        """
            Init the grouop event
        """
        pygame.sprite.Group.__init__(self, event)
        self.TIMEOUT_Events = pygame.sprite.Group()

    def add(self, event):
        """
            add the event to the container.
        """
        pygame.sprite.Group.add(self, event)
        if hasattr(event, 'events'):
            events = event.events()
        else:
            try:
                len(event)
                events = event
            except TypeError:
                events=[event]

        for event in events:
            try:
                event_type = event.type
            except AttributeError:
                pass
            else:
                if event_type == TIMEOUT:
                    self.TIMEOUT_Events.add(event)

                elif event_type == KEY:
                    for ev in event.contains.sprites():
                        self.add(ev)

    def events(self):
        """return a list of all events in this group."""
        return self.sprites()

    def enable(self):
        for event in self.events():
            event.enable()

    def disable(self):
        """
            do not allow callbacks to any sprites in this group to go through.
        """
        for event in self.events():
            event.disable()

    def check(self):
        """
            go through the pygame event queue and callback to events that should be triggered.
        """
        for pygame_event in pygame.event.get():
            pygame_event_type = pygame_event.type
            for event in self.events():
                event_type = event.type
                if pygame_event_type == event_type:
                    event.call(pygame_event)

        if self.TIMEOUT_Events:
            ticks = conf.ticks
            for event in self.TIMEOUT_Events.sprites():
                event.tick(ticks)

    def kill(self):
        """ 
            remove all of the events from all of the groups
        """
        for event in self.events():
            event.disable()
            event.kill()
        for event in self.TIMEOUT_Events.sprites():
            event.disable()
            event.kill()
