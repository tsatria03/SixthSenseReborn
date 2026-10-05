---
name: free_games_plan
description: "FINISHED 2026-10-05, confirmed by tunmi13productions. Games are free: the coin cost, the recharge clock and the main menu's coin row are gone, so nobody waits for coins. The dev's todo line was 'Remove the coin limit'; of three options the dev picked free games with the coin row dropped."
metadata:
  type: project
---

**Status: FINISHED 2026-10-05, confirmed by tunmi13productions** (built 2026-10-04). Code: `main_controller.py` (the row, the cost, the clock), `app_delegate.py` (the grant, the spoken coin words, `playNoCoin_`), `stage_1_e.py` (the restart), their docstrings, and the coin tests in menu.py (11 removed, 2 reworked), pause.py, weapon_range.py and window.py. The todo line is "Remove the coin limit, so you do not have to wait for coins to charge before you can play."

## Decision (the dev, 2026-10-04)
Of three options (free games and drop the coin row, free games and keep the row, unlimited coins), **free games with the coin row dropped.** The original spent a coin per game, from ten at the start, and gave one back every 30 minutes up to five.

## What goes
- Starting a game from the menu and restarting from the pause panel never need or spend a coin, and there is no "no coin" message or sound.
- The recharge clock and the catch-up for time spent away, and the first-run grant of ten coins.
- The coins row in the main menu, the window text's coin line, and the code that read the count and the minutes aloud (the spoken-number types for coins, 3 to 5). The digit reader itself stays: scores, gold and weapon stats use it.
- The coin tests in menu.py and the coin lines in the readme.

## What stays
- `COIN`, `FIREST`, `COIN_TIMER` and `COIN_TIMER_START` in an existing save are simply never read again; nothing deletes them.
- The recordings for "no coin", "number of coins" and the coin words stay in the bundle, unused, as the sound files are never deleted unless the dev asks.
- `--debug` no longer has coin behaviour to skip; its note about coins is dropped.
