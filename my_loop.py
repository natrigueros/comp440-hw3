"""Your agent's loop, which you design in step 1a. The homework page says what the
loop is for, under "1a. Design the loop" (also in instructions/part1.md), and the
check tells you each rule it must follow when your loop breaks it.

You design the loop as an outline in plain words, in WRITEUP.md under 1a. The
loop below the line that says where it goes is Claude's translation of that
outline, written with the parts in loop_parts.py: each line of your outline is a
comment, with about one line of Python for it under it. To change the loop,
change your outline and ask Claude to translate it again.

Check it after each translation. The check uses a scripted stand-in for the
model and for Wikipedia, so it needs no key and costs nothing:

    uv run python check_loop.py

Part 0 runs the agent on the reference loop. Once every rule passes, the agent
runs on this loop and no other: the runs of 1c and later need it to pass.
"""

import anthropic

# The names below include every one the file had before the parts, so that a loop written
# then still runs.
from agent import (ACCEPTED, DECLINED, INSTRUCTIONS, MAX_REJECTED, MAX_STEPS, MODEL, NO_ANSWER,
                   OUT_OF_STEPS, RAN_OUT, REJECTED, REJECTED_TOO_OFTEN, REMINDED, REMINDER,
                   TOOLS, answer_problem, clean_answer, finish, run_tool)
from loop_parts import Conversation


def run_agent(claim, client=None, max_steps=MAX_STEPS, lookup=run_tool):
    """Check one claim. Returns what talk.accept() or talk.stop() returns."""
    client = client or anthropic.Anthropic()
    system = INSTRUCTIONS.read_text()
    messages = [{"role": "user", "content": f"Claim: {claim}"}]
    trace, read_so_far = [], []
    talk = Conversation(claim, client, system, messages, trace, read_so_far, lookup)
    steps = 0          # lookups made so far
    rejected = 0       # answers sent back so far

    # Your loop should repeatedly call the model with the message history so far, and ask for
    # its next step. It should check whether the model has given an answer yet. If not, it should
    # make the lookups that step asks for, and add what they return to the history. It should
    # also pay attention to whether the loop has reached its limit: a claim that runs out of
    # lookups cannot be decided.
    # ---- your loop goes below this line (step 1a) ----

    # Remember:
    #   1. The history: the claim and starting instructions, then every model reply and every turn of lookup results, in order.
    #      Set at the start. Added to after each model call, and added to once per model reply that asked for lookups (all of that reply's results together, plus any limit note).
    #      (This is messages, set up above; talk adds to it.)
    #   2. The lookups used: none yet. Goes up by one each time a lookup is actually made. Nothing else changes it.
    #      (This is steps, set up above.)
    #   3. The turns taken: none yet. Goes up by one each time the model is called.
    turns = 0
    #   4. The results of this reply: empty at the start of each turn.
    #      Filled as each lookup in this reply is made. Emptied once added to the history.
    #      (talk keeps this list itself: talk.give() puts a result in it, and talk.send_results() adds it to the history and empties it.)
    #   Fixed, never changed: the lookup limit (12), turn cap (20).
    #   (The lookup limit is max_steps.)
    turn_cap = 20

    # Repeat:
    while True:
        # If the turns taken have reached the turn cap:
        if turns >= turn_cap:
            # Stop with no verdict.
            return talk.stop(NO_ANSWER, steps)
        # Send the whole history to the model and get its next step. Count the turn.
        reply = talk.ask()
        turns += 1
        # Add the model's reply to the history.
        # (talk.ask() has already added it.)

        # If the step contains an answer:
        if reply.answer is not None:
            # Stop with that answer. (Any lookups in the same step are not made.)
            return talk.accept(reply.answer, steps)

        # Work out the lookups remaining (limit minus lookups used).
        remaining = max_steps - steps

        # If the step asks for lookups and none remain:
        if reply.lookups and remaining <= 0:
            # Stop with no verdict.
            return talk.stop(RAN_OUT, steps)

        # If the step asks for lookups:
        if reply.lookups:
            # Start with the results of this reply empty.
            # (talk's list is empty here: the last send_results() emptied it.)
            # Take the requested lookups in order, only as many as remain.
            taken = reply.lookups[:remaining]
            # For each one taken:
            for call in taken:
                # Make it, put its result (errors and empty results count) in the results of this reply, and add one to the lookups used.
                result = talk.run(call)
                talk.give(call, result)
                steps += 1
                # Do not add it to the history yet.
            # If some were left out for the limit:
            left_out = reply.lookups[remaining:]
            if left_out:
                # Put a note in the results of this reply saying which were not made and that no lookups remain, so the model must answer now.
                for call in left_out:
                    talk.give(call, OUT_OF_STEPS.format(n=max_steps))
            # Now add all the results of this reply to the history together, as one turn, in the order the lookups were asked.
            talk.send_results()

        # If the step asks for nothing and gives no answer:
        if not reply.lookups and reply.answer is None:
            # Go on to the next turn.
            continue

    # Ways the loop stops:
    #   1. The model gives an answer: stop with that answer.
    #   2. The model asks for lookups when all 12 are used: stop with no verdict.
    #   3. The turn cap is reached without an answer: stop with no verdict.
    # (These are the three returns above.)
