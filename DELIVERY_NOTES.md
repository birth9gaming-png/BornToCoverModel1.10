# Prototype 14.1 audit correction

- Primary picks follow model point advantage; higher opposing payouts cannot override that direction.
- Notre Dame -9.5 is the primary pick for the audited -9.86 projection. Its saved -122 odds still produce negative EV and a Pass at this price.
- Supported picks are ordered first by default, ahead of larger scenario-only estimates. Each market has an explicit Candidate/Lean/Pass/Review status. Negative EV is not highlighted green.
- Candidate qualification checks both markets; an unsupported larger estimate cannot hide a supported option in the other market.
- An alternate-line/price check helps assess buying points using the actual offered odds, without changing the model or placing a wager.
- Target-specific historical-model and weekly-learning status, per-slate counts and projection audit exports are visible.
- All 77 spread/total forecasts and fitted artifacts are numerically unchanged. Historical data and frozen records remain saved.
- 223 automated checks passed.
- Chromium visited all six tabs, displayed Notre Dame -9.5 with a Pass at this price, exercised the price check and verified a 390-pixel mobile layout without horizontal overflow.

The CFB Over tendency was reproduced and traced partly to the fitted league-wide +0.6546-point total offset. The total tree correction remains disabled after validation; historical calibration is active. This is a selection/display correction, not proof that the broad Over tendency or prediction accuracy is fixed.

Replace all app files, keep Secrets and cloud data, and reboot. No ten-season redownload or manual Apply Model step is required. Read `audit_report_v14_1.md` for the audited saved prices and model limitations.
