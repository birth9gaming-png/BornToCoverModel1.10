# Born to Cover — Prototype 14.1

This update corrects pick direction, Candidate qualification and misleading negative-EV display. Fitted coefficients, projected scores, historical datasets and cloud persistence remain the Prototype 14 recipe.

## Install

1. Extract `football_dashboard_prototype14_1.zip`.
2. Replace your repository's app files with **all contents of the `football_dashboard` folder**, including `projection_audit.py`, other Python modules, `requirements.txt`, `.streamlit/config.toml`, `model_recipe_v14.json` and `ready_workspace_v14.json.gz`.
3. Keep existing Streamlit Secrets, private sharing and the `app.py` entry path. Reboot.
4. Confirm **Prototype 14.1** in the sidebar. Your existing cloud workspace, historical seasons, models and frozen records restore as before. No historical download or retraining is required.

The fitted artifact filenames deliberately retain `v14`: this update changes selection/display, not their numerical weights. A fresh installation uses the included saved preview; host keys enable live updates. Keys are not included in this package.

## Picks follow the model direction

The main spread/total choice follows the strongest point advantage available at your selected books. Once that direction is chosen, the app compares prices that offer positive point advantage on that side. An opposing team's larger payout cannot switch the primary model pick.

For the audited example, the model spread is Notre Dame -9.86 and the available Notre Dame line is -9.5. The primary pick is **Notre Dame -9.5**, not BYU +9.5. At the saved -122 price its estimated EV is negative, so it also says **Pass at this price**. Direction and wager value are separate.

Both markets remain visible. The default order puts supported Candidates and Leans ahead of scenario reviews; raw EV and kickoff ordering remain available. Green marks the stronger supported selection; negative-EV markets have no green recommendation. Large estimates dependent on unfitted scenarios are marked for review. A qualifying spread remains a Candidate even if the total has a larger unsupported EV.

In **Matchup reasons, availability and market history**, use **Check an alternate spread and price** to enter the offered line and American odds when buying points. It recalculates estimated win/push chance and EV. The check does not change weights, place a wager or enter the forecast ledger.

## What the audit found

- The uploaded current slate reproduced all ten highest-EV CFB totals as Overs.
- CFB total calibration is 10% statistical forecast, 90% market reference, plus a fitted +0.6546-point league-wide offset and eligible scenario effects. This creates many small Over leans. It is not evidence that ten Overs are strong bets.
- CFB's total tree correction is disabled because it failed validation. The separate historical total calibration remains active. CFB spread and NFL total trees are enabled; NFL spread trees are disabled. Other fitted calibration layers remain.
- The saved prices produced one CFB Candidate (Florida State–Miami Over 55.5 at -105) and one NFL Candidate (Carolina +1.5 at Philadelphia at -112). These are **replayed estimates**, not current betting recommendations.
- All 77 projected spreads and totals exactly matched before/after the update. No balancing quota or coefficient change was used to change the pick mix.

See `audit_report_v14_1.md` for exact results and limitations. The broad CFB total lean remains a modeling limitation requiring stronger later-game validation; this update does not claim improved betting accuracy.

## Historical data and new learning

The saved history includes 8,234 CFB and 2,639 NFL games. Eligible production fits use 5,878 CFB and 2,290 NFL reconstructions through 2025. Prior pair meetings are also included when available, with recency decay and sample-size shrinkage; this is not memorizing every matchup's outcome.

The current backup has 74 archived forecasts and zero settled near-kickoff records eligible for a coefficient update. Team inputs can refresh as results arrive, while new coefficients still require 100 same-recipe settled records across six weeks and later-period score/probability checks. Near-kickoff records are captured while the app is open inside 90 minutes of kickoff. A sleeping app does not continuously collect them.

**Method & Validation** now shows target-specific tree status, calibration type, training-through season, fitted offset and weekly-learning status. Each game board has Candidate/Lean/Pass counts and a downloadable projection audit.

## Existing features

The dark responsive interface, separate all-games Anytime Touchdowns tab, injuries/weather/rest/division layers, CFB context, directional market-story candidates, movement history, trends, R2 conflict checks and all-in-one Setup remain.

Public splits/sharp attribution still need a dated source. ATTD recency/usage/red-zone probabilities and live injury/weather inputs remain scoring scenarios. Old or post-kickoff quotes cannot become current selections.

## Run and verify

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest discover -s tests
```

223 automated checks passed. The original `validation_report_v14.md` remains for the recipe's historical numbers; those checks precede the full-history production refit and are not a held-out test of final artifacts. Normal startup uses preloaded models and history.
