# COMP 440 HW3 write-up

Name: Nayla Trigueros

Type each answer after the `>` under its question. An answer can run over several lines, but a blank line
ends it: to start a new paragraph, put a line with just `>` between the two. In a table, fill every cell
of every numbered row. Claude may paste a program's output where a question asks for it, but never an
answer. The homework page ticks a step when every answer in its section is filled in.

## Learning goals

In this homework you will:

- Understand what makes a program an *agent*. You will study a language model that picks the next Wikipedia search query, reads the page that comes back, and decides when to stop.
- Gain hands-on experience with the loop around the model by writing it yourself: its tools, its instructions, and its limit of 12 lookups.
- Compare the agent with two simpler methods on your claims, and measure how effective each one is.
- Check the agent's evidence yourself, and decide whether accuracy alone is a fair measure of it.

For extra credit, in Part 3, you find out why the agent fails on your claims, make one change, and see where Wikipedia, which is written by its volunteer editors, is thin, out of date or wrong.

# Part 0: Set up and check one claim

## 0a. Get your copy running

There is nothing to write for this step except your name, after `Name:` at the top of this file.

## 0b. Ask the model to assess a claim without tools

What verdict did the model give (*supported*, *refuted* or *doesn't say*), and what reason did it give? Quote the lines of the output that show them.

> Verdict: doesn't say
Explanation: I cannot confirm from memory who composed "Persian Surgery Dervishes" or what English Wikipedia states about that composer's birth date, so I can't verify the June 24, 1935 claim.

## 0c. Give it one search

Which Wikipedia page did it read? Quote the line of the output that shows it.

>Verdict: doesn't say
Explanation: The provided Wikipedia text covers only Ahmet Zappa's birth date (May 15, 1974) and career summary, and does not mention the composer of "Persian Surgery Dervishes" or any birth date of such a composer.

Did that page settle the claim correctly? If not, why do you think the search led there?

> No. It searched for a name that doesn't seem to be associated with the search. (the composer is Terry Riley)

## 0d. Run the agent and read its trace

In one or two sentences, how did the agent get from the claim to its verdict? Point to the trace entries by their numbers.

> 1- looked up the composer, 2- looked up the album, 3- looked up Tyler Perry.

Which lookup would you have done differently, and how? If none, which one surprised you?

> I would have skipped trace 2, since the information it needs is already on lookup 1.

Describe Wikidata briefly. Why may it be important to this task?

> It gives background information for a given search. Since we want to know details about a person, it helps by providing that necessary info.

# Part 1: How the agent works

## 1a. Design the loop

Your loop should repeatedly call the model with the message history so far, and ask for its next step. It should check whether the model has given an answer yet. If not, it should make the lookups that step asks for, and add what they return to the history. It should also pay attention to whether the loop has reached its limit: a claim that runs out of lookups cannot be decided. One limit is set for you: 12 lookups for a claim.

The Background and an example outline are under 1a on the homework page, and in [instructions/part1.md](instructions/part1.md#1a-design-the-loop).

Write your outline of the loop in the code block: what it remembers, what it repeats, and every way it stops.

```
Remember:
  1. The history: the claim and starting instructions, then every model reply and every turn of lookup results, in order.
     Set at the start. Added to after each model call, and added to once per model reply that asked for lookups (all of that reply's results together, plus any limit note).
  2. The lookups used: none yet. Goes up by one each time a lookup is actually made. Nothing else changes it.
  3. The turns taken: none yet. Goes up by one each time the model is called.
  4. The results of this reply: empty at the start of each turn.
     Filled as each lookup in this reply is made. Emptied once added to the history.
  Fixed, never changed: the lookup limit (12), turn cap (20).

Repeat:
    If the turns taken have reached the turn cap:
        Stop with no verdict.
    Send the whole history to the model and get its next step. Count the turn.
    Add the model's reply to the history.

    If the step contains an answer:
        Stop with that answer. (Any lookups in the same step are not made.)

    Work out the lookups remaining (limit minus lookups used).

    If the step asks for lookups and none remain:
        Stop with no verdict.

    If the step asks for lookups:
        Start with the results of this reply empty.
        Take the requested lookups in order, only as many as remain.
        For each one taken:
            Make it, put its result (errors and empty results count) in the results of this reply, and add one to the lookups used.
            Do not add it to the history yet.
        If some were left out for the limit:
            Put a note in the results of this reply saying which were not made and that no lookups remain, so the model must answer now.
        Now add all the results of this reply to the history together, as one turn, in the order the lookups were asked.

    If the step asks for nothing and gives no answer:
        Go on to the next turn.

Ways the loop stops:
  1. The model gives an answer: stop with that answer.
  2. The model asks for lookups when all 12 are used: stop with no verdict.
  3. The turn cap is reached without an answer: stop with no verdict.
```

List each thing your loop remembers from one turn to the next, and say what would go wrong without it.

>The model remembers nothing between calls, so without the history it would see only the bare claim every time. It would repeat the same lookups, never see what they returned, and never reach an answer.  Without lookups count, the loop cannot tell when 12 is reached. It would either run past the limit, which breaks the rule, or never recognize a claim that has run out of lookups and so cannot be decided Lookups only count when they are made, so a model that stalls (no lookup, no answer, turn after turn) never uses any of its 12. Without a turn count, that loop would never stop.


Now open `reference_loop.py` and compare it with your loop. Describe one difference in implementation and the resulting effects on agent behavior.

>The main difference is how each loop enforces the 12-lookup limit. The reference checks the limit once per turn, before a batch starts, and then runs every lookup the model asked for. So if 11 lookups are used and the model asks for 3, the reference runs all 3 and ends at 14. My outline takes only as many lookups as remain, skips the rest, and adds a note telling the model none are left, so it never goes over 12. The effect is that the reference lets the model see everything it asked for on its last turn but can overshoot the limit, while mine stays within the limit but gives the model a partial batch on its last turn.

## 1b. Be the agent

The claim: "Vic & Anthony's Steakhouse is located at the American casino that was combined with the California Club. The casino is owned by Landry's, Inc."

List your lookups, in order. Ask Claude to paste every column but the last from `runs/part1/lookups.jsonl`. Type "Why you chose it" yourself.

| # | Tool | What you asked for | Why you chose it |
|---|---|---|---|
| 1 | search | Vic and Anthony's Steakhouse| Simplest

What is your verdict on the claim, and which sentence or sentences from what you read is it based on?

> verdict is verified from 1 lookup, as i can deduct that it is owned by Landry's Inc. by line 3 and 4.

## 1c. Watch the agent work

List the three traces you read closely. At least one should be a claim the agent got wrong (if it got any wrong).

| # | Claim (first few words) | Articles | Did it match the dataset's label? | Did it get there for a good reason? Why or why not |
|---|---|---|---|---|
| 1 | Myles Kennedy and Robert Palmer| Myles Kennedy, Robert Palmer(singer)|yes| yes, as the results indicate the claim is correct |
| 2 |The rule of the dynasty that was active | History of Egypt, Ptolemaic dynasty, Rosetta Stone| no| yes, its fair enough, since the second sentence is wrong |
| 3 | The quartets that released One Thousand Years | Age of Chance, One Thousand Years of Trouble, Vector (band)| yes | yes, as Vector is not a rock band but a metal one|

Which trace did you find most interesting, and what did the agent do well or badly in it?

> I thought it was interesting that it was so detailed with the Rosetta Stone one. I wouldve brushed over the fact that it is from a different "book".

## 1d. Write the agent's instructions

What changed in the agent's traces after you wrote your instructions? Give one claim as an example.

> One that didn't match before but does match after: The rule of the dynasty that was active when the stone was inscribed was 275 years long. The reasoning it gives is that "Hystory of Egypt" is a loose paraphrasing and not a definitive role. 

## 1e. Start the full run, and predict

Predict the share of claims each version will get right (its verdict matches the dataset's label), as a percentage. A guess is fine; the reasons are what I grade.

| Version | 2 articles | 3 articles | 4 articles | Why you think so |
|---|---|---|---|---|
| No tools | 10%| 40%| 50%| Without any tools, it will likely need more lookups|
| One search |20% | 35%| 45% | With one search, it might get to the right answer faster but not quite|
| Agent | 30%| 45%| 25%| An agent will be faster and more efficient|

How many lookups will the agent make per claim, on average? Why?

> On average, it will make around 3-4. This is because it often needs more than two, but very rarely needs more than 5, so an inbetween those two seems a good standard.

# Part 2: The agent against the baselines

## 2a. Compare accuracy

Ask Claude to paste the report of your full run, from `runs/part2/report.txt`, into the empty block below.

```
Share of claims where the verdict matched the label:

                          no-tools  one-search       agent
HoVer, 2 articles         18/34       18/34       23/34   
HoVer, 3 articles         23/33       16/33       25/33   
HoVer, 4 articles         20/33       17/33       23/33   
All                       61/100      51/100      71/100  

HoVer, supported          16/50        1/50       28/50   
HoVer, not supported      45/50       50/50       43/50   

Average per claim:

                         lookups   seconds
no-tools                     0.0       3.4
one-search                   2.0       4.3
agent                        5.5       8.3

2 runs gave no verdict (for example a refusal, or out of lookups). They count as wrong. The results viewer lists them on this run's page, under "Claims with no verdict, or that stopped with an error".
```

How do the results compare with your predictions? Where were you furthest off? Use the numbers from your run, by number of articles.

> for 3 nd 4 articles, I was off in thinking that 1 lookup would outperform no tools, when it actually did pretty good and almost as good as the agent at times.

Does the gap between the agent and the one-search baseline grow with the number of articles? What in the claims or the traces explains what you see?

> Not much between 2 and 3 articles, but yes by 3 and 4 (almost 20 verdicts-difference). The more articles, the more the one-search struggled to reach a verdict on the claim.

The no-tools baseline read nothing. How did it do, and what does that tell you about these claims?

> It did pretty well, which means these claims are probably not too difficult to deduct or don't require much confirmation.

## 2b. Check the evidence yourself

Fill in one row for each of the first five claims in your full run, in the order of the claims file, where the agent's verdict is *supported* or *refuted*.

| # | Claim (first few words) | Agent's verdict | Matched the dataset's label? | Does the quoted evidence support that verdict? | Why or why not |
|---|---|---|---|---|---|
| 1 | Gregg Rolie and Rob Tyner, are not a keyboardist.|refuted | no| yes| as the wikipedia article claims Greff is indeed a keyboardist|
| 2 |Patrick Mercer was suspended in April 2014.| refuted| no|yes | he resigned first|
| 3 |Queen Medb of Connacht made her invasion in a province |supported |yes | yes| the invasion was in the northern part and a dialect of Scots is spoken|
| 4 |John McTiernan is the director of 1999 American heist film | refuted| yes|yes | cast list is wrong|
| 5 |The Formula One World Champion is the winner of the 1963 Lombank Trophy | refuted| no| yes| the winner is a different person|

Of the five, how many matched the dataset's label, and for how many of those does the quoted evidence support the verdict?

> 2 matched, and their quoted evidence does hold for the verdict.

Is accuracy alone a good measure of this agent? Why or why not?

> Not by itself, but it is an important measure. We would want an agent that is able to reach the correct claims with the appropiate evidence.

# Part 3 (extra credit): Why the agent fails, and one change

## 3a. Sort the failures

Fill in one row for each of the first eight failures in your full run, rows 1 to 8 of the claims table for runs/part2 with "Result" in "The agent" box set to "does not match the dataset's label (any reason)". If you have fewer than eight, fill a row for each and delete the rest.

| Row | Claim (first few words) | Your label | The entry of the trace that shows it | Is the dataset's label right? (yes, no or can't tell) | Claude's label |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |
| 8 | | | | | |

Where did you and Claude disagree, and who do you think is right?

>

Which kind of failure was most common? If no kind repeats, say which failure you will aim at in 3b, and why.

>

## 3b. Make one change

What did you change, and why did you expect it to help?

>

How many of your evaluation claims did the agent match before the change and after it? Which of your failures from 3a now match?

>

Quote one claim the agent matched before the change and not after it, if there is one, and say what you think happened. If there is none, say so.

>

## 3c. Write it up

What does the agent's loop add over one search, what does it cost, and when would you not use an agent for a job like this? Use your numbers from Part 2 and Part 3.

>

What did your claims show you about Wikipedia as a source? Where it was thin or wrong, why might that be, given who writes it?

>

Your numbers rest on 100 claims. Which of your conclusions would you trust on another 100 claims, which might be chance, and what would you measure to find out?

>
