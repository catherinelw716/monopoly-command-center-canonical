"""Focused confirmation around the lower deployment boundary found by the coarse pre-lock search."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from monopoly_simulator import load_regular_rules
from monopoly_tournament_optimizer import OptimizerConfig, default_field_scenarios, evaluate_portfolio_across_scenarios, load_field_state, prepare_field_paths, serialize_bets
from monopoly_robust_optimizer import _current_week_downside, _scenario_utility, shrink_probabilities
from run_week3_sunday_robust import load_probs
from run_week3_prelock_second_stage import build_portfolio, ROOT, SNAPSHOT, MODEL, STATE, RULES

OUTPUT = ROOT / "v2/results/week3_prelock_second_stage_confirm.json"
FRACTIONS=(0.05,0.06,0.07,0.08,0.10,0.12)
STRUCTURES=((6,5),(6,6),(5,5),(6,4),(4,4))
EDGE_SHRINK_FACTORS=(1.00,0.75,0.50,0.25)

def main():
    state=load_field_state(STATE); rules=load_regular_rules(RULES)
    _,probs,ranking=load_probs(SNAPSHOT,MODEL)
    balances={"Catherine":state.catherine_balance,"Amanda":state.amanda_balance}
    scenarios=default_field_scenarios(); cfg=OptimizerConfig(simulations=3000,seed=716)
    prepared=prepare_field_paths(state,scenarios,cfg)
    prob_sets={f:shrink_probabilities(probs,f) for f in EDGE_SHRINK_FACTORS}
    rows=[]
    for cg,ag in STRUCTURES:
        for cf in FRACTIONS:
            for af in FRACTIONS:
                bets=build_portfolio(balances,rules,probs,cf,af,cg,ag)
                stress=[]; weighted=[]; base=None; down0=None
                for idx,factor in enumerate(EDGE_SHRINK_FACTORS):
                    pset=prob_sets[factor]
                    down=_current_week_downside(balances,bets,pset,rules,cfg,seed=cfg.seed+5000+idx*100,alpha=0.10)
                    retention=float(down['minimum_entry_cvar_retention'])
                    m=evaluate_portfolio_across_scenarios(balances,bets,pset,rules,state,scenarios,cfg,prepared_field_paths=prepared)
                    weighted.append(_scenario_utility(m['weighted'],retention))
                    if factor==1.0: base=m; down0=down
                    for sm in m['by_scenario'].values(): stress.append(_scenario_utility(sm,retention))
                w=base['weighted']
                rows.append({'c_games':cg,'a_games':ag,'c_fraction':cf,'a_fraction':af,
                    'bets_by_entry':serialize_bets(bets),'outlay_by_entry':base['outlay_by_entry'],'household_outlay':base['household_outlay'],
                    'robust_floor_utility':min(stress),'robust_average_utility':float(np.mean(weighted)),
                    'base_expected_household_prize_share':w['expected_household_prize_share'],'base_p_any_cash':w['p_any_cash'],
                    'base_future_minimum_failure_risk':w['future_minimum_failure_risk'],'base_current_week_downside':down0})
    def key(r): return (r['robust_floor_utility'],r['robust_average_utility'],r['base_expected_household_prize_share'],-r['base_future_minimum_failure_risk'],-r['household_outlay'])
    rows.sort(key=key,reverse=True)
    by=[]
    for cg,ag in STRUCTURES:
        subset=[r for r in rows if r['c_games']==cg and r['a_games']==ag]; by.append(max(subset,key=key))
    by.sort(key=key,reverse=True)
    result={'status':'WEEK3_PRELOCK_SECOND_STAGE_LOWER_BOUND_CONFIRM','simulations':cfg.simulations,'fractions':list(FRACTIONS),'structures':[list(x) for x in STRUCTURES],
        'best_overall':rows[0],'best_by_structure':by,'top20':rows[:20],'probability_ranking':ranking,
        'guardrails':['Focused confirmation after coarse optimum hit 8% lower grid boundary.','Common random numbers and same frozen probability model.','Incremental stake only on material price edges.']}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps({'best_overall':rows[0],'best_by_structure':by},indent=2,sort_keys=True))
if __name__=='__main__': main()
