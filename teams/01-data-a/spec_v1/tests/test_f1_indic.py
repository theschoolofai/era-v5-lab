"""F1 on the Indic packs (ind-*): the Indic path of tools/f1_rule.py, under the TSAI ruling (31 Oct): <PHONE> and <EMAIL>
for a private person, organisations and public offices kept. Every value is made up; emails are joined at run time.

  python -m pytest spec_v1/tests/test_f1_indic.py
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import clean as c

AT = "@"


def ind(text, pack="ind-hi-fw2", lang="hin_Deva"):
    return {"doc_id": "x", "text": text, "url": "http://a/b", "lang_label": lang, "pack_id": pack}


@pytest.mark.parametrize("text, expect", [
    ("\u092e\u0947\u0930\u093e \u0928\u0902\u092c\u0930 9876543210 \u0939\u0948", "\u092e\u0947\u0930\u093e \u0928\u0902\u092c\u0930 <PHONE> \u0939\u0948"),                              # a bare mobile is private
    ("\u0938\u0902\u092a\u0930\u094d\u0915: +91 98765 43210, \u0927\u0928\u094d\u092f\u0935\u093e\u0926", "\u0938\u0902\u092a\u0930\u094d\u0915: <PHONE>, \u0927\u0928\u094d\u092f\u0935\u093e\u0926"),                  # +91, spaced
    ("\u092e\u094b. \u096f\u096e\u096d\u096c\u096b\u096a\u0969\u0968\u0967\u0966", "\u092e\u094b. <PHONE>"),                                                 # Devanagari digits
    ("Call me on 98765-43210 any time.", "Call me on <PHONE> any time."),
    ("\u092e\u094b\u092c\u093e\u0907\u0932 \u0928\u0902. 0 98765 43210", "\u092e\u094b\u092c\u093e\u0907\u0932 \u0928\u0902. <PHONE>"),
    ("\u0918\u0930: 011-23456789", "\u0918\u0930: <PHONE>"),                                                # a landline with a home label
    ("Home: 080-2345 6789", "Home: <PHONE>"),
    (f"\u0908\u092e\u0947\u0932 ravi.kumar{AT}gmail.com \u092a\u0930 \u0932\u093f\u0916\u0947\u0902", "\u0908\u092e\u0947\u0932 <EMAIL> \u092a\u0930 \u0932\u093f\u0916\u0947\u0902"),
])
def test_a_private_persons_contact_gets_a_placeholder(text, expect):
    assert c.f1(ind(text)) == ("fix", expect)


@pytest.mark.parametrize("text", [
    "\u0935\u093f\u0936\u094d\u0935\u0935\u093f\u0926\u094d\u092f\u093e\u0932\u092f \u0915\u093e\u0930\u094d\u092f\u093e\u0932\u092f: 9876543210",                    # the block names an office
    "\u092a\u0941\u0932\u093f\u0938 \u0939\u0947\u0932\u094d\u092a\u0932\u093e\u0907\u0928 9876543210",
    "Office: 011-23456789",                                  # a landline with no private label
    "Helpline (toll free): 1800 180 1551",                   # toll-free
    f"Contact info{AT}univ.ac.in for admission.",            # a role mailbox, an Indian organisation domain
    f"\u0935\u093f\u092d\u093e\u0917 \u0915\u093e \u0908\u092e\u0947\u0932 head{AT}dept.gov.in",                    # .gov.in
    f"\u092a\u094d\u0930\u0935\u0947\u0936 \u0915\u0947 \u0932\u093f\u090f admissions{AT}college.edu \u092a\u0930",
    f"\u09ac\u09bf\u09b6\u09cd\u09ac\u09ac\u09bf\u09a6\u09cd\u09af\u09be\u09b2\u09af\u09bc\u09c7\u09b0 \u09a0\u09bf\u0995\u09be\u09a8\u09be: registrar.office{AT}mail.example.org",
    "ISBN 978-81-7525-766-5 \u0935\u0930\u094d\u0937 2024",                      # not phone numbers
    "\u0915\u0941\u0932 1234567890123 \u0930\u0941\u092a\u092f\u0947",
    "\u0926\u093f\u0928\u093e\u0902\u0915 01-2024 1234 \u0914\u0930 \u092a\u093f\u0928 110001",
])
def test_organisations_public_offices_and_other_numbers_stay(text):
    assert c.f1(ind(text)) == ("keep", text)


@pytest.mark.parametrize("pack, lang, text, expect", [
    ("ind-bn-fw2", "ben_Beng", "\u0986\u09ae\u09be\u09b0 \u09a8\u09ae\u09cd\u09ac\u09b0 \u09ef\u09ee\u09ed\u09ec\u09eb\u09ea\u09e9\u09e8\u09e7\u09e6", "\u0986\u09ae\u09be\u09b0 \u09a8\u09ae\u09cd\u09ac\u09b0 <PHONE>"),             # Bengali digits
    ("ind-ta-sangraha-v", "tam_Taml", "\u0b95\u0bc8\u0baa\u0bc7\u0b9a\u0bbf: 98765 43210", "\u0b95\u0bc8\u0baa\u0bc7\u0b9a\u0bbf: <PHONE>"),
    ("ind-te-fw2", "tel_Telu", "\u0c2e\u0c4a\u0c2c\u0c48\u0c32\u0c4d 9876543210", "\u0c2e\u0c4a\u0c2c\u0c48\u0c32\u0c4d <PHONE>"),
    ("ind-kn-fw2", "kan_Knda", "\u0cae\u0cca\u0cac\u0cc8\u0cb2\u0ccd: \u0cef\u0cee\u0ced\u0cec\u0ceb\u0cea\u0ce9\u0ce8\u0ce7\u0ce6", "\u0cae\u0cca\u0cac\u0cc8\u0cb2\u0ccd: <PHONE>"),                 # Kannada digits
    ("ind-gu-fw2", "guj_Gujr", "\u0aae\u0acb\u0aac\u0abe\u0a87\u0ab2 \u0aef\u0aee\u0aed\u0aec\u0aeb\u0aea\u0ae9\u0ae8\u0ae7\u0ae6", "\u0aae\u0acb\u0aac\u0abe\u0a87\u0ab2 <PHONE>"),                     # Gujarati digits
])
def test_every_indic_script(pack, lang, text, expect):
    assert c.f1(ind(text, pack, lang)) == ("fix", expect)


@pytest.mark.parametrize("pack, lang, text", [
    ("ind-ta-sangraha-v", "tam_Taml", "\u0b9a\u0bc6\u0ba9\u0bcd\u0ba9\u0bc8 \u0bae\u0bbe\u0ba8\u0b95\u0bb0\u0bbe\u0b9f\u0bcd\u0b9a\u0bbf \u0b85\u0bb2\u0bc1\u0bb5\u0bb2\u0b95\u0bae\u0bcd: 9876543210"),
    ("ind-kn-fw2", "kan_Knda", "\u0cac\u0cc6\u0c82\u0c97\u0cb3\u0cc2\u0cb0\u0cc1 \u0cb5\u0cbf\u0cb6\u0ccd\u0cb5\u0cb5\u0cbf\u0ca6\u0ccd\u0caf\u0cbe\u0cb2\u0caf \u0c95\u0c9a\u0cc7\u0cb0\u0cbf 9876543210"),
    ("ind-bn-fw2", "ben_Beng", "\u0995\u09b2\u0995\u09be\u09a4\u09be \u09aa\u09cc\u09b0\u09b8\u09ad\u09be \u0995\u09be\u09b0\u09cd\u09af\u09be\u09b2\u09af\u09bc \u09ef\u09ee\u09ed\u09ec\u09eb\u09ea\u09e9\u09e8\u09e7\u09e6"),
])
def test_organisation_words_in_every_script(pack, lang, text):
    assert c.f1(ind(text, pack, lang)) == ("keep", text)


def test_joiners_nukta_and_the_rest_of_the_text_stay():
    zwj, zwnj = chr(0x200D), chr(0x200C)
    text = f"\u0915\u094d{zwj}\u0937, \u0915\u094d{zwnj}\u0937 \u0914\u0930 \u091c\u093c\u093f\u0928\u094d\u0926\u0917\u0940\u0964 \u092e\u0947\u0930\u093e \u0928\u0902\u092c\u0930 9876543210 \u0939\u0948\u0964"
    action, new = c.f1(ind(text))
    assert action == "fix" and new == text.replace("9876543210", "<PHONE>")


def test_a_second_run_changes_nothing():
    text = f"\u0938\u0902\u092a\u0930\u094d\u0915: +91 98765 43210 \u092f\u093e ravi{AT}gmail.com\n\u0915\u093e\u0930\u094d\u092f\u093e\u0932\u092f: 011-23456789"
    _, once = c.f1(ind(text))
    assert c.f1(ind(once)) == ("keep", once)


def test_clean_runs_the_indic_f1_last_on_every_indic_pack():
    indic = {p for p, f in c._FAMILY.items() if f == "indic"}
    assert indic and indic <= c.SCOPE["f1_rule.py"]
    action, new = c.clean(ind("\u092f\u0939 \u090f\u0915 \u0938\u093e\u0927\u093e\u0930\u0923 \u0935\u093e\u0915\u094d\u092f \u0939\u0948\u0964\n\u092e\u0947\u0930\u093e \u0928\u0902\u092c\u0930 9876543210 \u0939\u0948\u0964\n"))
    assert "<PHONE>" in new and "9876543210" not in new


@pytest.mark.parametrize("pack", ["en-dclm", "math-finemath", "sci-finepdfs", None])
def test_the_indic_path_runs_only_on_indic_packs(pack):
    doc = dict(ind("\u092e\u0947\u0930\u093e \u0928\u0902\u092c\u0930 9876543210 \u0939\u0948"), pack_id=pack)
    assert c._shared_f1(doc)[1] == doc["text"]
