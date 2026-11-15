"""Clasificación heurística de activos. Es una ayuda, no un hecho: puede equivocarse."""

STABLE_SYMBOLS = {"usdt", "usdc", "dai", "busd", "tusd", "usde", "fdusd", "usds", "usdd", "pyusd",
                  "frax", "lusd", "susd", "eurc", "eurs", "usd0", "usdy", "rlusd", "usdg"}
DERIVATIVE_SYMBOLS = {"wbtc", "weth", "steth", "wsteth", "cbeth", "reth", "weeth", "ezeth", "rseth",
                      "wbeth", "cbbtc", "tbtc", "wavax", "wftm", "meth", "sweth", "oseth"}
NAME_HINTS = ("wrapped", "bridged", "staked", "restaked", "tokenized", "tokenised", "3x long", "3x short")
CATEGORY_STABLE = ("stablecoin",)
CATEGORY_DERIVATIVE = ("wrapped", "liquid staking", "liquid restaking", "tokenized")

STABLE = "Stablecoin"
DERIVATIVE = "Wrapped / derivado"
NON_GROWTH = {STABLE, DERIVATIVE}


def classify(row, categories=None):
    symbol = str(row.get("symbol") or "").lower()
    name = str(row.get("name") or "").lower()
    cats = " ".join(categories or []).lower()
    if symbol in STABLE_SYMBOLS or "stablecoin" in name or any(c in cats for c in CATEGORY_STABLE):
        return STABLE
    if symbol in DERIVATIVE_SYMBOLS or any(h in name for h in NAME_HINTS) \
            or any(c in cats for c in CATEGORY_DERIVATIVE):
        return DERIVATIVE
    cap = row.get("market_cap")
    if not cap:
        return "Sin capitalización"
    if cap >= 10_000_000_000:
        return "Consolidado"
    if cap >= 1_000_000_000:
        return "Intermedio"
    return "Emergente"
