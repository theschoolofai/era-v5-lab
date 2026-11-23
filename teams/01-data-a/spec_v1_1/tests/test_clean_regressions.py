"""Synthetic regressions for code-pack F1 dispatch and Sanskrit number preservation (#734)."""
import importlib.util
from pathlib import Path

import pytest

@pytest.fixture
def cleaner():
    path = Path(__file__).resolve().parents[1] / 'clean.py'
    spec = importlib.util.spec_from_file_location('regression_v1_1', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def document(pack, text, lang):
    return dict(doc_id='synthetic', text=text, url='', pack_id=pack, lang_label=lang)


@pytest.mark.parametrize('pack, lang, prefix, string_line', [
    ('code-cpp', 'cpp', '//', 'const char* owner = "{email}";'),
    ('code-go', 'go', '//', 'package main\nconst owner = "{email}"'),
    ('code-java', 'java', '//', 'class A {{ String owner = "{email}"; }}'),
    ('code-js-ts', 'typescript', '//', 'const owner: string = "{email}";'),
    ('code-python', 'python', '#', 'owner = "{email}"'),
    ('code-rust', 'rust', '//', 'const OWNER: &str = "{email}";'),
])
def test_generic_code_tag_masks_contacts_with_the_packs_parser(cleaner, pack, lang, prefix, string_line):
    c = cleaner
    pytest.importorskip('tree_sitter_language_pack')
    email = 'jordan' + '@' + 'mail.io'
    for text in (f'{prefix} by {email}\n', string_line.format(email=email) + '\n'):
        row = document(pack, text, 'code')
        original = dict(row)
        result = c.f1(row)
        assert result == c.f1(dict(row, lang_label=lang))
        assert result == ('fix', text.replace(email, '<EMAIL>'))
        assert c.f1(dict(row, text=result[1])) == ('keep', result[1])
        assert row == original


def test_generic_code_tag_preserves_arithmetic_and_runs_in_clean(cleaner):
    c = cleaner
    pytest.importorskip('tree_sitter_language_pack')
    text = 'package main\nvar x = 555-010-0199\n'
    assert c.f1(document('code-go', text, 'code')) == ('keep', text)
    text = 'package main // by jordan' + '@' + 'mail.io\n'
    assert c.clean(document('code-go', text, 'code')) == ('fix', 'package main // by <EMAIL>\n')


def test_explicit_code_language_is_preserved(cleaner, monkeypatch):
    c = cleaner
    seen = []
    def spans(text, lang):
        seen.append(lang)
        return [(0, len(text.encode('utf-8')))]
    monkeypatch.setattr(c, '_f1_text_spans', spans)
    c.f1(document('code-js-ts', '// by jordan' + '@' + 'mail.io\n', 'javascript'))
    assert seen == ['javascript']


def test_unknown_code_pack_does_not_guess_a_parser(cleaner):
    c = cleaner
    text = '// by jordan' + '@' + 'mail.io\n'
    assert c._shared_f1(document('code-unknown', text, 'code')) == ('keep', text)


@pytest.mark.parametrize('text', ['श्लोकः॥१०० अनन्तरम्।', 'श्लोकः॥100 अनन्तरम्।',
                                 'वर्षे १९९६तमे संवत्सरे।', 'वर्षे 1996तमे संवत्सरे।',
                                 'वर्षा१९९६तमे संवत्सरे।'])
def test_sanskrit_b4_preserves_numbers_and_removes_wiki_markup(cleaner, text):
    c = cleaner
    row = document('ind-sa-fw2', text, 'san_Deva')
    rule = c._RULE['DB-B4-004']()
    assert rule(row) == ('keep', text)
    marked = "{{template}}'''[[लेखः|" + text + "]]'''↩"
    assert rule(dict(row, text=marked)) == ('fix', text)


# ---------------------------------------------------------------- code-adjacent packs: e-mail addresses only
CADJ = [('cadj-commits', 'code'), ('cadj-notebooks', 'code')]


@pytest.mark.parametrize('pack, lang', CADJ)
def test_code_adjacent_packs_mask_private_emails_and_nothing_else(cleaner, pack, lang):
    c = cleaner
    private = 'jordan.lee' + '@' + 'mail.io'
    text = ('Fix the parser\n\nSigned-off-by: Jordan Lee <' + private + '>\n'
            'support' + '@' + 'acme.io, dev' + '@' + 'example.com, someone' + '@' + 'users.noreply.github.com, logo' + '@' + '2x.png\n'
            'ping 192.168.127.12 or call +1 (555) 010-0199; part 307-355-022; rgb 255 239 213\n'
            '42 Wallaby Way, Sydney\n')
    action, out = c.clean(document(pack, text, lang))
    assert (action, out) == ('fix', text.replace(private, '<EMAIL>'))
    assert c.clean(document(pack, out, lang)) == ('keep', out)


@pytest.mark.parametrize('pack, lang', CADJ)
def test_code_adjacent_packs_never_drop(cleaner, pack, lang):
    c = cleaner
    card = ''.join(f'user{i}' + '@' + 'mail.io\n' for i in range(8))
    action, out = c.clean(document(pack, card, lang))
    assert action == 'fix' and out == '<EMAIL>\n' * 8
    assert c.clean(document(pack, 'no address here\n', lang)) == ('keep', 'no address here\n')


def test_code_adjacent_packs_are_a_family_with_only_the_shared_f1(cleaner):
    c = cleaner
    for pack, _ in CADJ:
        assert c._FAMILY[pack] == 'code-adjacent' and pack in c.SCOPE['f1_rule.py']
        assert not [rid for rid, packs in c.SCOPE.items() if pack in packs and rid != 'f1_rule.py']


def test_stackexchange_keeps_its_email_like_strings(cleaner):
    # ssh and git logins, URLs with a user name and systemd units there are not a person's address
    c = cleaner
    text = 'try `ssh pi' + '@' + 'raspberrypi.com` or git clone https://me' + '@' + 'bitbucket.org/x.git\n'
    assert c.clean(document('cadj-stackexchange', text, 'en')) == ('keep', text)
    assert 'cadj-stackexchange' not in c._FAMILY and 'cadj-stackexchange' not in c.SCOPE['f1_rule.py']


@pytest.mark.parametrize('pack, lang', CADJ)
def test_code_adjacent_packs_follow_the_cadj_commits_medicine(cleaner, pack, lang):
    # diagnosis/submissions/cadj-commits/kunal2016/medicine.md, medicine 1: test domains and mail@ stay, LinkedIn profiles go
    c = cleaner
    profile, short = 'https://www.linkedin.com/in/jane-doe-123/', 'http://linkedin.com/in/jdoe'
    text = ('fake = "jane' + '@' + 'test.com"; mail' + '@' + 'acme.io; x' + '@' + 'domain.com\n'
            'see ' + profile + ' and ' + short + '\n')
    action, out = c.clean(document(pack, text, lang))
    placeholder = 'https://www.linkedin.com/in/example'
    assert (action, out) == ('fix', text.replace(profile, placeholder).replace(short, placeholder))
    assert c.clean(document(pack, out, lang)) == ('keep', out)
