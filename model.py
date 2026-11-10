"""Foreguild revenue model. Every input is an ASSUMPTION unless marked otherwise.
Run: python3 model.py           -> prints scenario tables
     python3 model.py --json    -> JSON used by the HTML page
"""
import json, sys

PLANS = {  # price, creator payouts, screening+compute, market seed, payments/support (share of price)
    "Spark":    dict(price=199,  payout=48,  compute=8,  seed=22, support=0.03, mix=0.50),
    "Pulse":    dict(price=499,  payout=240, compute=20, seed=43, support=0.03, mix=0.35),
    "Campaign": dict(price=1199, payout=600, compute=40, seed=86, support=0.03, mix=0.15),
}

SCEN = {
    # new paying clients per month (months 1..12), monthly churn, fixed cost per month
    "Low":  dict(new=[0,1,2,2,3,3,3,4,4,4,4,5],           churn=0.15, fixed=[3000]*6+[4000]*6),
    "Base": dict(new=[0,3,4,5,6,7,8,8,9,9,10,10],         churn=0.12, fixed=[3500]*6+[5000]*6),
    "High": dict(new=[1,5,7,9,11,13,15,17,18,19,20,22],   churn=0.08, fixed=[4000]*6+[7500]*6),
}
OTHER_PER_CLIENT = 12  # open-board fees (15%) + contest screening, per active client per month


def unit(plan):
    p = PLANS[plan]
    contrib = p["price"] - p["payout"] - p["compute"] - p["seed"] - p["price"] * p["support"]
    return contrib


def run(name):
    s = SCEN[name]
    active = 0.0
    rows, cum_rev, cum_net, breakeven = [], 0.0, 0.0, None
    blended_price = sum(PLANS[k]["price"] * PLANS[k]["mix"] for k in PLANS)
    blended_contrib = sum(unit(k) * PLANS[k]["mix"] for k in PLANS)
    for m in range(12):
        active = active * (1 - s["churn"]) + s["new"][m]
        mrr = active * blended_price
        other = active * OTHER_PER_CLIENT
        contrib = active * blended_contrib + other
        net = contrib - s["fixed"][m]
        cum_rev += mrr + other
        cum_net += net
        if breakeven is None and net >= 0:
            breakeven = m + 1
        rows.append(dict(month=m + 1, clients=round(active, 1), revenue=round(mrr + other),
                         contribution=round(contrib), fixed=s["fixed"][m], net=round(net)))
    return dict(name=name, rows=rows, year1_revenue=round(cum_rev), year1_net=round(cum_net),
                breakeven_month=breakeven, blended_price=round(blended_price),
                blended_contrib=round(blended_contrib, 1))


if __name__ == "__main__":
    out = {k: run(k) for k in SCEN}
    out["units"] = {k: dict(price=PLANS[k]["price"], contribution=round(unit(k)),
                            margin=round(unit(k) / PLANS[k]["price"] * 100)) for k in PLANS}
    if "--json" in sys.argv:
        print(json.dumps(out, indent=1))
    else:
        for k in PLANS:
            u = out["units"][k]
            print(f"{k:9s} ${u['price']:>5}  contribution ${u['contribution']:>4}  ({u['margin']}%)")
        for k in SCEN:
            r = out[k]
            m12 = r["rows"][-1]
            print(f"\n{k}: M12 clients {m12['clients']}, M12 revenue ${m12['revenue']:,}/mo, "
                  f"year-1 revenue ${r['year1_revenue']:,}, year-1 net ${r['year1_net']:,}, "
                  f"first profitable month {r['breakeven_month']}")
