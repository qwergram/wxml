# Example

An example implementation.

```py
# rakan/__main__.py
from rakan import PyRakan as BaseRakan
import random

class Rakan(BaseRakan):
    """
    An example step
    Argument can be passed in.

    Arguments are completely arbritary and can be rewritten by the user.
    """
    def step(self, max_value=1, *args, **kwargs):
        # Rakan is able to propose a random move in O(d)
        precinct, district = self.propose_random_move()
        # Completely random
        if random.randint(0, max_value) == 1:
            self.move_precinct(precinct, district)

    """
    An example walk.
    Perhaps there is specific behavior for the 10 steps
    and specific behavior for the last 10.

    Arguments are completely arbritary and can be rewritten by the user.
    """
    def walk(self, *args, **kwargs):
        # for instance:
        for i in range(10):
            self.step(max_value=1)

        for i in range(10):
            self.step(max_value=2)
```

Users are then able to modify step, and walk to their liking. The users have access to the following methods on `Rakan`.
