"""k-neighborhood. Neighbors may sit in another document — that is the spillover."""


def around(units: list[dict], n: int, k: int = 1) -> dict:
    focus = units[n]
    return {
        "focus": focus["id"],
        "before": [u["id"] for u in units[max(0, n - k) : n]],
        "after": [u["id"] for u in units[n + 1 : n + 1 + k]],
    }


def by_id(units: list[dict], uid: str, k: int = 1) -> dict:
    for u in units:
        if u["id"] == uid:
            return around(units, u["n"], k)
    raise KeyError(uid)
