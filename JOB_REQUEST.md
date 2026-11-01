# Job request

Use a job request when your team needs a run that you cannot do on Colab, Kaggle or your own machine.
TSAI runs approved requests and returns the logs and the results to the repository.

## How to send a request

1. Make one file for each job: `teams/<NN>-<name>/jobs/<YYYY-MM-DD>-<short-name>.md`.
2. Copy the block below into the file and fill in each line.
3. Open a pull request. Your team lead reviews it and approves it.
4. TSAI runs the job after the approval. The results come back in a pull request to
   `teams/<NN>-<name>/jobs/results/<YYYY-MM-DD>-<short-name>/`.

```
Team:            <NN>-<name>
Owner:           <your name as on Axiom> (<github handle>)
Lead approval:   <lead github handle>
Question:        <one sentence: the one question that this job answers>
Script:          teams/<NN>-<name>/<topic>/<file>.py   (in this PR or already merged)
Command:         python <file>.py --config <path>      (one line, no shell pipes)
Config:          teams/<NN>-<name>/<topic>/<config>.yaml
Inputs:          <public dataset name, sample pack id, or "synthetic">
Hardware:        CPU | 1 GPU                           (1 GPU unless TSAI agrees to more)
Max time:        <minutes>                             (TSAI stops the job at this limit)
Precision:       fp32 | bf16 | fp8 | fp4 | not used
Measures:        <the numbers that you need, for example step time in ms, max abs error>
Expected result: <your estimate, so that a surprise is easy to see>
Outputs:         out/*.json, out/*.csv, profiler trace (50 MB or less in total)
Test log:        <link to the log of the same script on Colab, Kaggle or your own machine>
```

## Rules

1. The script must run with no network access and no keys. It reads only its inputs. It writes only to `./out/`.
2. Run the script on Colab, Kaggle or your own machine first. Attach that log. TSAI does not run a script with no test log.
3. One job answers one question. Make a new request for a new question.
4. Do not put secrets, passwords or personal data in the script, the config or the inputs.
5. If a job fails two times, it goes back to the team. Fix it and send a new request.
6. Do not send a job request to clean the full data. TSAI applies the approved cleaning rules (spec v1).
