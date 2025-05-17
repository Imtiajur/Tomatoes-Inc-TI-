# -*- coding: utf-8 -*-
"""
Created on Apr 1, 2025
@author: imtia
Deterministic Model using Mean Demand
"""

import gurobipy as gp
from gurobipy import GRB

try:
    # Define sets
    PRODUCTS = ['Paste', 'Ketchup', 'Salsa']
    RESOURCES = ['Labor', 'Tomatoes', 'Sugar', 'Spices']
    PERIODS = [1, 2, 3]

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

    # Demand mean (average of good and bad scenarios)
    demand_mean = {'Paste': 150, 'Ketchup': 35, 'Salsa': 12.5}

    # Create model
    m = gp.Model("Tomatoes_Inc_Deterministic")

    # Decision variables
    x = m.addVars(PRODUCTS, PERIODS, name="produce", lb=0)
    e = m.addVars(RESOURCES, PERIODS, name="extra_resource", lb=0)
    s = m.addVars(PRODUCTS, PERIODS, name="storage", lb=0)

    # Objective function
    m.setObjective(
        gp.quicksum(prod_cost[p] * x[p, t] for p in PRODUCTS for t in PERIODS) +
        gp.quicksum(extra_cost[r] * e[r, t] for r in RESOURCES for t in PERIODS) +
        gp.quicksum(storage_cost[p] * s[p, t] for p in PRODUCTS for t in PERIODS),
        GRB.MINIMIZE
    )

    # Resource constraints
    for t in PERIODS:
        for r in RESOURCES:
            m.addConstr(
                gp.quicksum(resource_use[p][r] * x[p, t] for p in PRODUCTS) <= resource_limit[r] + e[r, t],
                name=f"resource_{r}_period_{t}"
            )

    # Inventory balance
    for p in PRODUCTS:
        # Period 1
        m.addConstr(x[p, 1] == s[p, 1] + demand_mean[p], name=f"inv_{p}_1")
        # Periods 2 and 3
        for t in [2, 3]:
            m.addConstr(x[p, t] + s[p, t - 1] == s[p, t] + demand_mean[p], name=f"inv_{p}_{t}")

    # Solve the model
    m.optimize()

    # Output
    if m.status == GRB.OPTIMAL:
        print(f"\n Optimal Total Cost: ${m.ObjVal:.2f}\n")

        print("Production Plan:")
        for p in PRODUCTS:
            for t in PERIODS:
                print(f"  {p} - Period {t}: Produce = {x[p, t].X:.2f}")

        print("\n Storage Plan:")
        for p in PRODUCTS:
            for t in PERIODS:
                print(f"  {p} - Period {t}: Storage = {s[p, t].X:.2f}")

        print("\n Extra Resource Usage:")
        for r in RESOURCES:
            for t in PERIODS:
                print(f"  {r} - Period {t}: Extra used = {e[r, t].X:.2f}")
    else:
        print("No optimal solution found.")

except gp.GurobiError as e:
    print(f"Error: {e}")
