# Elmino Game Flow

## Main Flow
1. Users are created
2. Users join queue with stake
3. When 3 users join, a game is created automatically
4. Game status becomes active automatically
5. current_turn_user_id is set automatically to the first queued player
6. Current player fetches question
7. Current player submits answer
8. Answer is validated
9. Score is updated
10. Turn moves to next player
11. Repeat until question set ends
12. Game status becomes finished
13. winner_user_id is set

## Rules Confirmed
- Only current_turn_user_id can answer
- Wrong-turn answer returns error
- Correct answer gives score
- Wrong answer reduces or affects score
- Game can reach finished state
- No manual SQL activation is needed anymore

## Current Technical Gap
- Edge cases should be validated more strictly
- Automated tests are not added yet

