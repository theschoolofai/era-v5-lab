# Reading translation pairs: a guide for readers

Thank you for helping. This guide tells you what you will receive, how to open it, how to answer, and what to send
back.

## What you are doing

We are cleaning the text that the lab's model will learn from. Sometimes the same text appears twice in two
languages: once in English and once translated into Hindi, for example. We have a tool that finds such pairs, but it
makes mistakes. Your answers tell us when it is right and when it is wrong, so we can set it up well.

You will see pairs of texts. For each pair you answer one question:

> **Is one text a translation of the other?**

Your answer is **yes**, **no** or **unsure**.

## What you will receive

A zip file. When you unzip it you will see:

```
e5d/
├── README.md               this guide
├── view_e5d_sheets.py      the program that shows you the pairs
└── sheets/
    ├── readers_guide.md     a short version of how to answer
    ├── sa-en_reader1.csv    your pairs (this name is an example)
    └── sa-hi_reader1.csv
```

Your file names tell you the two languages: `sa` is Sanskrit, `hi` is Hindi and `en` is English. So `sa-en` means
Sanskrit and English. Each file holds 50 pairs.

**Please keep the zip private.** It contains text from web pages. Do not share it or upload it anywhere.

## Before you start (once)

You need **Python 3** on your computer. To check, open a terminal (Mac: the Terminal app; Windows: PowerShell) and
type:

```
python3 --version
```

On Windows, type `python --version` instead. If you see something like `Python 3.12.1`, you are ready. If not,
install Python 3 from https://www.python.org/downloads/ and try again. Nothing else needs to be installed.

## Open the pairs

1. Unzip the file, for example into your Downloads folder.
2. Open a terminal and go into the unzipped folder:

   Mac:
   ```
   cd ~/Downloads/e5d
   ```
   Windows:
   ```
   cd $HOME\Downloads\e5d
   ```
3. Start the program. Put your own name in the quotes:

   Mac:
   ```
   python3 view_e5d_sheets.py --sheets sheets --name "Your Name"
   ```
   Windows:
   ```
   python view_e5d_sheets.py --sheets sheets --name "Your Name"
   ```
4. Open your web browser and go to **http://127.0.0.1:8000**.

The page runs only on your own computer. Nothing is sent over the internet.

Keep the terminal window open while you work. To stop, click on the terminal and press **Ctrl+C**.

## What you see

- **On the left:** your files, each with how many pairs you have answered, for example "12 / 50 answered". Click
  a file to open it.
- **In the middle:** one pair at a time. The two texts are side by side, one sentence per line. They are marked
  `text_1` and `text_2`.
- **Below the texts:** three buttons, **yes**, **no** and **unsure**, and a box for a note.
- **At the top:** a **save** button.

## How to answer

Read both texts. Then ask yourself: **does one text say the same thing as the other, sentence by sentence, in another
language?**

**Answer yes** when one text is a translation of the other:
- most sentences of the shorter text have a sentence with the same meaning in the longer text;
- a loose or imperfect translation is still **yes**;
- if one text is longer, or has extra sentences, it can still be **yes**.

**Answer no** when they are not translations, even if:
- both talk about the same topic, event or person;
- both mention the same names, places, dates or numbers;
- both come from the same kind of website.

Two news stories about the same event, written separately, are **no**.

**Answer unsure** when you really cannot tell. For example, the text is too short, or you don't know one of the
languages well enough for this pair.

**Use the note** for anything you want to tell us. For example: "only the first half is translated" or "the Hindi
text is a summary, not a translation".

Some files include a few pairs whose answer we already know. Answer them like any other pair.

## Moving around

| To do this | Click | Or press |
|---|---|---|
| Answer yes | yes | **y** |
| Answer no | no | **n** |
| Answer unsure | unsure | **u** |
| Next pair | next → | **→** or **Enter** |
| Previous pair | ← previous | **←** |
| Next pair you haven't answered | next unanswered | **j** |
| Save | save | **Ctrl+S** (Windows) or **Cmd+S** (Mac) |

The keys don't work while you are typing in the note box. Click outside the box first.

You can change an answer at any time: go back to the pair and press another button.

## Saving

**Press save often.** The save button turns **orange** while you have answers that are not saved yet, and shows
how many. After you save, it says **saved**.

If you close the page or the browser by mistake, your unsaved answers are kept in the browser, and they come back
when you open the page again. Still, save often: answers reach your answer file only when you press save.

You don't have to finish in one go. Stop the program (Ctrl+C), and next time start it again with the same command
and the same name. You will continue where you left off.

## Please

- **Read on your own.** Don't discuss the pairs with the other reader before you have both finished.
- **Don't look the texts up** online or in a translation tool. We need your own judgement.
- **Don't edit the files** in the `sheets` folder.

## When you have finished

Your answers are saved in a folder called **`e5d_labels`**, next to the `sheets` folder. There is one file for each
of your sheets, for example:

```
e5d/e5d_labels/sa-en-reader1-Your_Name.csv
```

Each file has three columns: `item`, `translation` and `note`. It contains your answers only, no text from the
pages.

**Send these files** to the person who sent you the zip. They are small and safe to share.

## If something goes wrong

| Problem | What to do |
|---|---|
| `python3: command not found` (Mac) or `python` is not recognised (Windows) | Install Python 3 from https://www.python.org/downloads/ and open a new terminal |
| `Address already in use` | Something else is using the page's address. Add `--port 8001` at the end of the command, then go to http://127.0.0.1:8001 |
| `ERROR: no sheets` | You are not in the unzipped `e5d` folder, or the `sheets` folder is missing. Check step 2 |
| The page shows "not saved" | Copy the message and send it to the person who sent you the zip |
| Anything else | Send a screenshot to the person who sent you the zip |

Thank you for reading!
