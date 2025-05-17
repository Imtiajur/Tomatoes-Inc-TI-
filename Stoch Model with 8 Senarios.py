# -*- coding: utf-8 -*-
"""
Created on Mar 8, 2025
@author: imtia
"""

import gurobipy as gp
from gurobipy import GRB

try:
    # Define sets
    PRODUCTS = ['Paste', 'Ketchup', 'Salsa']
    RESOURCES = ['Labor', 'Tomatoes', 'Sugar', 'Spices']
    PERIODS = [1, 2, 3]
    SCENARIOS = [
        'GGG', 'GGB', 'GBG', 'GBB',
        'BGG', 'BGB', 'BBG', 'BBB'
    ]
    SCENARIO_PROB = 1 / len(SCENARIOS)

    # Production costs
    prod_cost = {'Paste': 1.0, 'Ketchup': 1.5, 'Salsa': 2.5}

    # Resource use per product
    resource_use = {
        'Paste':   {'Labor': 0.5, 'Tomatoes': 1.0, 'Sugar': 0.0, 'Spices': 0.25},
        'Ketchup': {'Labor': 0.8, 'Tomatoes': 0.5, 'Sugar': 0.5, 'Spices': 1.0},
        'Salsa':   {'Labor': 1.0, 'Tomatoes': 0.5, 'Sugar': 1.0, 'Spices': 3.0},
    }

    # Resource availability and extra cost
    resource_limit = {'Labor': 200, 'Tomatoes': 250, 'Sugar': 300, 'Spices': 100}
    extra_cost = {'Labor': 2.0, 'Tomatoes': 0.5, 'Sugar': 1.0, 'Spices': 1.0}

    # Storage cost per product
    storage_cost = {'Paste': 0.5, 'Ketchup': 0.25, 'Salsa': 0.2}

    # Unmet demand penalty
    unmet_cost = {'Paste': 2.0, 'Ketchup': 3.0, 'Salsa': 6.0}

    # Demand for each scenario
    demand_good = {'Paste': 200, 'Ketchup': 40, 'Salsa': 20}
    demand_bad = {'Paste': 100, 'Ketchup': 30, 'Salsa': 5}

    # Function to get demand for a product in a period for a scenario
    def get_demand(prod, period, scen):
        if scen[period - 1] == 'G':
            return demand_good[prod]
        else:
            return demand_bad[prod]

    # Create model
    m = gp.Model("Tomatoes_Inc_Stochastic")

    # First-stage variables
    x = m.addVars(PRODUCTS, PERIODS, name="produce", lb=0)
    e = m.addVars(RESOURCES, PERIODS, name="extra_resource", lb=0)

    # Second-stage variables for each scenario
    s = m.addVars(PRODUCTS, PERIODS, SCENARIOS, name="storage", lb=0)
    u = m.addVars(PRODUCTS, PERIODS, SCENARIOS, name="unmet", lb=0)

    # Objective: Minimize expected cost
    production_cost = gp.quicksum(prod_cost[p] * x[p, t] for p in PRODUCTS for t in PERIODS)
    resource_extra_cost = gp.quicksum(extra_cost[r] * e[r, t] for r in RESOURCES for t in PERIODS)
    storage_penalty = SCENARIO_PROB * gp.quicksum(storage_cost[p] * s[p, t, w] for p in PRODUCTS for t in PERIODS for w in SCENARIOS)
    unmet_penalty = SCENARIO_PROB * gp.quicksum(unmet_cost[p] * u[p, t, w] for p in PRODUCTS for t in PERIODS for w in SCENARIOS)

    m.setObjective(production_cost + resource_extra_cost + storage_penalty + unmet_penalty, GRB.MINIMIZE)

    # Resource constraints
    for t in PERIODS:
        for r in RESOURCES:
            m.addConstr(
                gp.quicksum(resource_use[p][r] * x[p, t] for p in PRODUCTS) <= resource_limit[r] + e[r, t],
                name=f"resource_{r}_period_{t}"
            )

    # Inventory balance per scenario
    for w in SCENARIOS:
        for p in PRODUCTS:
            # Period 1
            m.addConstr(
                x[p, 1] == s[p, 1, w] + get_demand(p, 1, w) - u[p, 1, w],
                name=f"inventory_{p}_1_{w}"
            )
            # Period 2 and 3
            for t in [2, 3]:
                m.addConstr(
                    x[p, t] + s[p, t - 1, w] == s[p, t, w] + get_demand(p, t, w) - u[p, t, w],
                    name=f"inventory_{p}_{t}_{w}"
                )

    # Solve
    m.optimize()

    # Output
    if m.status == GRB.OPTIMAL:
        print(f"\nOptimal Expected Cost: ${m.ObjVal:.2f}")
        for p in PRODUCTS:
            for t in PERIODS:
                print(f"{p} - Period {t}: Produce {x[p, t].X:.2f}")

        print("\n--- Extra Resource Usage ---")
        for r in RESOURCES:
            for t in PERIODS:
                print(f"{r} - Period {t}: Extra Used = {e[r, t].X:.2f}")

        print("\n--- Scenario Summary (Storage & Unmet Demand) ---")
        for w in SCENARIOS:
            print(f"\nScenario: {w}")
            for p in PRODUCTS:
                for t in PERIODS:
                    print(f"{p} - Period {t}: Storage = {s[p,t,w].X:.2f}, Unmet = {u[p,t,w].X:.2f}")
    else:
        print("No optimal solution found.")

except gp.GurobiError as e:
    print(f"Error: {e}")
