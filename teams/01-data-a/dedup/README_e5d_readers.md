# Translation pairs: what to do

You read pairs of texts and answer one question for each pair:

> **Is one text a translation of the other?** yes, no or unsure

It takes about a minute a pair. Your answers tell us when our translation finder is right.

## Your sheets

Your zip holds one or two sheets. The file name says the languages and which copy is yours:

| Sheet | Languages | Pairs |
|---|---|---|
| `sa-en_reader1.csv`, `sa-en_reader2.csv` | Sanskrit and English | 32 |
| `sa-hi_reader1.csv`, `sa-hi_reader2.csv` | Sanskrit and Hindi | 46 |
| `hi-en_reader1.csv`, `hi-en_reader2.csv` | Hindi and English | 27 |

Two readers read each sheet, each on their own copy.

**Keep the zip private.** It holds text from web pages: don't share or upload it.

## Setup (one time)

You need Python 3 and nothing else. Check it in a terminal (Mac: Terminal; Windows: PowerShell):

```
python3 --version
```

On Windows, use `python` instead of `python3` in every command. If there is no Python 3, install it from
https://www.python.org/downloads/ and open a new terminal.

Unzip the file, for example into Downloads. You get:

```
e5d/
├── README.md              ← this page
├── view_e5d_sheets.py     ← the viewer
└── sheets/
    ├── readers_guide.md
    └── sa-en_reader1.csv  ← your sheet(s)
```

Don't rename or edit anything in `sheets/`.

## Run the viewer

Put your own name in the quotes.

**Mac / Linux**

```
cd ~/Downloads/e5d
python3 view_e5d_sheets.py --sheets sheets --name "Your Name"
```

**Windows PowerShell**

```
cd $HOME\Downloads\e5d
python view_e5d_sheets.py --sheets sheets --name "Your Name"
```

Then open **http://127.0.0.1:8000** in your browser. The page runs on your computer only; nothing goes online. Keep the
terminal open while you work; press **Ctrl+C** in it to stop.

## Record your answers

You record everything in the viewer page. For each pair you record **one answer** and, if you want, **a note**.

1. Click your sheet on the left. It shows how many you have answered, e.g. "12 / 32".
2. Read the two texts, side by side, one sentence per line.
3. Record your answer: click the button or press its key.

| Answer | When | Key |
|---|---|---|
| **yes** | Most sentences of the shorter text have a sentence with the same meaning in the other. A loose or partial translation, or one text being longer, is still **yes** | **y** |
| **no** | Not a translation, even if both are about the same topic, event or person, or share names, places, dates or numbers. Two news stories about one event, written separately, are **no** | **n** |
| **unsure** | You can't tell: too short, or you don't know one language well enough | **u** |

4. Record what you noticed in the **note** box, if anything, e.g. "only the first half is translated", "the Hindi is a
   summary", "half the text is a menu". Keep it short. Leave it empty if there is nothing to add.
5. Press **Enter** or **→** for the next pair (**←** goes back, **j** jumps to the next unanswered one).
6. Press **save** (**Ctrl+S** / **Cmd+S**) every few pairs. The button turns **orange** while you have unsaved answers
   and says **saved** when they are written.

Every save writes your answers to a file on your computer: `e5d/e5d_labels/<sheet>-<Your_Name>.csv`, one file per
sheet, e.g. `sa-en-reader1-Your_Name.csv`. You don't open or edit this file; the viewer keeps it up to date.

You can change an answer any time, and stop and come back later: run the same command with the same name and you
continue where you left off. Keys don't work while you type in the note box; click outside it first.

Some pairs have an answer we already know. Answer them like the others.

**Please:** read on your own, don't discuss the pairs with the other reader until you have both finished, and don't
look the texts up online or in a translation tool.

## Return your answers

You are done when each of your sheets shows all pairs answered on the left (e.g. "32 / 32") and the save button says
**saved**.

1. **Stop the viewer:** press **Ctrl+C** in the terminal.
2. **Find your answer files** in the `e5d_labels` folder, inside the `e5d` folder. To open it:

   Mac:
   ```
   open ~/Downloads/e5d/e5d_labels
   ```
   Windows:
   ```
   explorer $HOME\Downloads\e5d\e5d_labels
   ```

   You see one CSV per sheet, e.g. `sa-en-reader1-Your_Name.csv`. They hold your answers and notes only, no page
   text, so they are safe to send.
3. **Email the CSVs** as attachments to the person who sent you the zip, by the date in their email.
4. **Comment `done`** on [theschoolofai/era-v5-lab#729](https://github.com/theschoolofai/era-v5-lab/issues/729). Only
   the word `done`: no answers there, so the other reader isn't influenced.

Send only the CSVs from `e5d_labels`: not the zip, not the `sheets` folder (they hold page text). If you can't finish
every pair, send what you have and say so in the email.

### CSV format

The viewer writes it for you:

| Column | What it holds | Values |
|---|---|---|
| `item` | The pair's ID | filled in for you |
| `translation` | Your answer | `yes`, `no`, `unsure`, or empty if not answered |
| `note` | Your note | free text, may be empty |

Example:

```
item,translation,note
sa-en-025,yes,
sa-en-007,no,same topic only
sa-en-019,unsure,too short to tell
```

## If something goes wrong

| Problem | Fix |
|---|---|
| `python3: command not found` (Mac), or `python` not recognised (Windows) | Install Python 3 from https://www.python.org/downloads/ and open a new terminal |
| `Address already in use` | Add `--port 8001` to the command, then open http://127.0.0.1:8001 |
| `ERROR: no sheets` | You are not in the `e5d` folder. Run the `cd` line again |
| There is no `e5d_labels` folder, or no CSV in it | You haven't saved yet. Start the viewer again and press **save** |
| The page says "not saved" | Send the message to the person who sent you the zip |
| Anything else | Send a screenshot to the person who sent you the zip |

Thank you for reading!
