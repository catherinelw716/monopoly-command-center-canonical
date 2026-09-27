"""Focused high-resolution confirmation for top Week 3 second-stage structures."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from monopoly_simulator import load_regular_rules
from monopoly_tournament_optimizer import OptimizerConfig, default_field_scenarios, evaluate_portfolio_across_scenarios, load_field_state, prepare_field_paths, serialize_bets
from monopoly_robust_optimizer import _current_week_downside, _scenario_utility, shrink_probabilities
from run_week3_sunday_robust import load_probs
from run_week3_second_stage_sizing import build_portfolio, CANDIDATES

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'v2/season_2026/week_02_field_state.json'
RULES=ROOT/'v2/monopoly_contract.json'
SNAPSHOT=ROOT/'v2/season_2026/week_03_current_market_2026-09-27_1120ET.json'
MODEL=ROOT/'v2/model_artifacts/v2_global_hybrid_2016_2025.json'
OUTPUT=ROOT/'v2/results/week3_second_stage_confirm.json'

STRUCTURES=((4,4),(5,4),(5,5))
C_FRACS=(0.12,0.15,0.18)
A_FRACS=(0.18,0.20,0.22)
SHRINK=(1.0,0.75,0.5,0.25)

def main():
    state=load_field_state(STATE); rules=load_regular_rules(RULES)
    _, probs, _=load_probs(SNAPSHOT,MODEL)
    balances={'Catherine':state.catherine_balance,'Amanda':state.amanda_balance}
    scenarios=default_field_scenarios(); cfg=OptimizerConfig(simulations=5000,seed=716)
    prepared=prepare_field_paths(state,scenarios,cfg)
    psets={f:shrink_probabilities(probs,f) for f in SHRINK}
    rows=[]
    for cg,ag in STRUCTURES:
      for cf in C_FRACS:
       for af in A_FRACS:
        bets=build_portfolio(balances,rules,cf,af,cg,ag)
        utilities=[]; weighted_utils=[]; base=None; downside0=None
        for i,f in enumerate(SHRINK):
            downside=_current_week_downside(balances,bets,psets[f],rules,cfg,seed=cfg.seed+5000+i*100,alpha=0.10)
            retention=float(downside['minimum_entry_cvar_retention'])
            metrics=evaluate_portfolio_across_scenarios(balances,bets,psets[f],rules,state,scenarios,cfg,prepared_field_paths=prepared)
            weighted_utils.append(_scenario_utility(metrics['weighted'],retention))
            utilities.extend(_scenario_utility(m,retention) for m in metrics['by_scenario'].values())
            if f==1.0: base=metrics; downside0=downside
        w=base['weighted']
        rows.append({'c_games':cg,'a_games':ag,'c_fraction':cf,'a_fraction':af,'bets_by_entry':serialize_bets(bets),'household_outlay':base['household_outlay'],'robust_floor_utility':min(utilities),'robust_average_utility':float(np.mean(weighted_utils)),'base_expected_household_prize_share':w['expected_household_prize_share'],'base_p_any_cash':w['p_any_cash'],'base_future_minimum_failure_risk':w['future_minimum_failure_risk'],'base_current_week_downside':downside0})
    def key(r): return (r['robust_floor_utility'],r['robust_average_utility'],r['base_expected_household_prize_share'],-r['base_future_minimum_failure_risk'],-r['household_outlay'])
    rows.sort(key=key,reverse=True)
    by_structure=[]
    for s in STRUCTURES:
        subset=[r for r in rows if (r['c_games'],r['a_games'])==s]
        by_structure.append(max(subset,key=key))
    by_structure.sort(key=key,reverse=True)
    result={'status':'WEEK3_SECOND_STAGE_CONFIRM_5000_CRN','simulations':5000,'structures':list(map(list,STRUCTURES)),'best_overall':rows[0],'best_by_structure':by_structure,'top10':rows[:10],'stable_candidate_order':CANDIDATES}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps({'best_overall':rows[0],'best_by_structure':by_structure},indent=2,sort_keys=True))

if __name__=='__main__': main()
