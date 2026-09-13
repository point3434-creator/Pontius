"""Budget selection uses cost and iteration order only, never observed error."""
import math


def select(checkpoints, budget):
    if type(budget) not in (int, float) or not math.isfinite(budget) or budget <= 0:
        raise ValueError('budget must be positive')
    seen = set()
    for row in checkpoints:
        iteration, cost = row['iterations'], row['charged_seconds']
        if type(iteration) is not int or iteration <= 0 or iteration in seen:
            raise ValueError('checkpoint iterations must be unique positive integers')
        if type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
            raise ValueError('checkpoint cost must be finite and nonnegative')
        seen.add(iteration)
    affordable = [row for row in checkpoints if row['charged_seconds'] <= budget]
    return max(affordable, key=lambda row: row['iterations']) if affordable else None
