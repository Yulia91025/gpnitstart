import random


class SomeDevice:

    def get_data() -> tuple[float]:
        x = random.uniform(10, 100)
        y = random.uniform(10, 100)
        z = random.uniform(10, 100)
        return (x, y, z)
