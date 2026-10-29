# Medicine sheet: ind-mr-fw2 (thinktinkergreen)

Write one section for each disease that you found more than five times.

## Medicine 1: A6 (Wrong or mixed script)

1. **Disease:** A6 (Wrong or mixed script), count in pack: 10. Examples: `1870bd9485daced5`: `'shantसंविधानाच्या'@2742`; `70386fb4070fc50f`: `'Articleकसब्याच्या'@591 | 'Previous Articleकसब्याच्या रिंगणात बि...'@582 | 'Next Article अपघातातील जखमी पत्रकार श...'@638 | 'Related Posts'@699 | 'Add A Comment'@713 | 'Previous Articleकसब्याच्या रिंगणात बि...'@582 | 'Next Article अपघातातील जखमी पत्रकार श...'@638`; `875818dd2944faba`: `'aptडॅप्टेशन्सची'@1050 | ' 2013 चे कॅरी त्यानुसार million 30 दश...'@1160 | ' 2007 चे धुकं जवळपास मिळवले Million 6...'@1303 | ' पण एकंदरीत सोनी बहुधा खूष असेल जर गड...'@1976`.
2. **Medicine:** Insert whitespace at fused Latin-Indic script boundaries caused by HTML tag-drop.
   ```python
   clean = regex.sub(r'(\p{Latin})(?=[\p{Devanagari}])', r'\1 ', text)
   clean = regex.sub(r'([\p{Devanagari}])(?=\p{Latin})', r'\1 ', clean)
   ```
3. **Action:** fix the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 2: C2 (Repeated lines)

1. **Disease:** C2 (Repeated lines), count in pack: 8. Examples: `052f2791183c599c`: `'विश्वाचे आर्त - भाग १५ - १३० दाण्यांच...'@0 | 'काही प्रमाणात Dean Michael Ornish ह्य...'@11412 | ' अधिक ग्लूटन आवश्यक असलेल्या ब्रेडकरि...'@18747 | ' केक वगैरे पदार्थांत ग्लूटन कमी असलेल...'@18820 | ' |'@22014`; `1f6ac623059aea97`: `'1 6 मार्च 2019 रोजी मुख्यमंत्री देवें...'@0 | 'A 3 रे'@133 | 'B 2 रे'@140 | 'C 4 थे'@147`; `2542e8ad88e5f64e`: `'मैत्रिणीला वाढदिवसाच्या शुभेच्छा मराठ...'@0 | 'मैत्रिणीला वाढदिवसाच्या शुभेच्छा मराठ...'@0 | ' आज आम्ही तुमच्या जिवलग मैत्रिणीच्या ...'@227 | ' Birthday wishes in marathi for best ...'@540`.
2. **Medicine:** Deduplicate repeated identical lines within document, preserving first occurrence.
   ```python
   seen = set()
   clean = '\n'.join(line for line in text.splitlines() if not (line.strip() and line.strip() in seen or seen.add(line.strip())))
   ```
3. **Action:** fix the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Poetry, choruses in songs, or intentional legal refrains may be deduplicated.

## Medicine 3: C3 (Truncated document)

1. **Disease:** C3 (Truncated document), count in pack: 56. Examples: `626fc9159542b61c`: `'Tags: Diabetes, Health, Health Tips, ...'@2770 | 'Tags: Diabetes, Health, Health Tips, ...'@2770 | 'Diabetes Tips : शुगर लेव्हल होणार नाह...'@838 | 'जेव्हा तुमच्या पेशी इन्सुलिनच्या सिग्...'@925 | ' News 18 Marathi यांना दुजोरा देत नाही'@2501`; `5c05e18231a55839`: `'Maharashtra News, Latest Maharashtra ...'@1715 | 'Maharashtra News, Latest Maharashtra ...'@1715 | ' |'@1791`; `c8ad1802a6fbb058`: `'Maharashtra News, Latest Maharashtra ...'@1698 | 'Maharashtra News, Latest Maharashtra ...'@1698 | ' |'@1774`.
2. **Medicine:** Drop truncated documents ending mid-sentence, or trim trailing incomplete fragments.
   ```python
   # If document terminates without valid terminal, drop or trim to last terminal
   clean = trim_to_last_sentence(text)
   ```
3. **Action:** drop the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 4: C4 (Two documents joined)

1. **Disease:** C4 (Two documents joined), count in pack: 8. Examples: `a84ec9a0a34a3f12`: `'\nCopyright ©'@923`; `d40a6e0c632b3dd0`: `'\nCopyright ©'@1685 | 'त ि'@696 | 'ि'@698`; `cedda2a2f29ef819`: `'\nCopyright ©'@1181`.
2. **Medicine:** Detect merged documents with mid-text copyright/boundary markers and split or drop.
   ```python
   # Drop concatenated documents lacking clear boundaries
   clean = split_joined_documents(text)
   ```
3. **Action:** drop the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 5: C5 (Lists of keywords or links)

1. **Disease:** C5 (Lists of keywords or links), count in pack: 9. Examples: `626fc9159542b61c`: `'Tags: Diabetes, Health, Health Tips, ...'@2770 | 'Tags: Diabetes, Health, Health Tips, ...'@2770 | 'Diabetes Tips : शुगर लेव्हल होणार नाह...'@838 | 'जेव्हा तुमच्या पेशी इन्सुलिनच्या सिग्...'@925 | ' News 18 Marathi यांना दुजोरा देत नाही'@2501`; `654e623661c0b8c6`: `'Tags: गणेश नाईक'@1802 | 'Raj Thackeray Rally : राणे शिवसेना सो...'@617 | ' राज ठाकरेंनी पहिल्यांदाच सांगितली In...'@674 | 'Raj Thackeray Rally: सभेआधी 'राज'पुत्...'@807`; `f2c7bce34d00c7fe`: `'Tags: Corona, Corona vaccine, Corona ...'@3470 | 'Tags: Corona, Corona vaccine, Corona ...'@3470 | 'मुंबई, 23 डिसेंबर: ब्रिटनमध्ये कोरोना...'@0 | ' राज्य सरकारच्या या निर्णयावर एमआयएमच...'@297 | 'Live Updates : हिंगोलीमध्ये वादळी वाऱ...'@871`.
2. **Medicine:** Strip SEO keyword lists and tag clouds appended to article text.
   ```python
   clean = regex.sub(r'\n\s*(?:Tags|Keywords|टॅग्ज)\s*:.*$', '', text, flags=regex.I)
   ```
3. **Action:** drop the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 6: D3 (Mixed language (code-mixing))

1. **Disease:** D3 (Mixed language (code-mixing)), count in pack: 226. Examples: `00eed90bde196e9c`: `'How To Find Sweet Watermelon: उन्हाळ्...'@0`; `45099f1718f10018`: `'Lioness And leopard Fight Viral Video...'@0 | ' या व्हिडीओला इन्स्टाग्रामवर wildtrails'@1440 | 'in वर शेअर करण्यात आला आहे'@1480`; `924d41c82dfe4138`: `'Viral Video: सोशल मीडियावर व्हायरल हो...'@0 | 'ट्रॅव्हल कपल अशा एका अकाऊंटवरून अलीकड...'@669 | 'Video: विमानात आंघोळ'@1105`.
2. **Medicine:** Label natural code-mixed sentences per Rule R4; trim extraneous English scraping boilerplate.
   ```python
   # Natural code-mixing is preserved; English scraping trailers are stripped
   clean = strip_scraping_trailers(text)
   ```
3. **Action:** fix the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 7: F1 (Personal data)

1. **Disease:** F1 (Personal data), count in pack: 8. Examples: `26dda2c33506f1ff`: 'Fact Check: हे चित्र भारताचे नाही, बा...'@0 | 'आम्हाला हा फोटो 16 एप्रिल 2021 रोजी फ...'@947 | 'Faisal Caesar नावाच्या ट्विटर हँडलने ...'@1365 | phone at offset 2435; `dac55ea8bc131eb1`: 'व सदर व्यक्तीला गडचिरोली जिल्हा रुग्ण...'@1180 | phone at offset 108; `6169b09fe7801904`: 'जेव्हा लिथियम-आयन फॉस्फेट बॅटरीची उर्...'@349 | 'सौर बॅटरी 48V200Ah Lifepo4 स्टँड बॅटर...'@934 | phone at offset 1155.
2. **Medicine:** Redact personal data (phone numbers, emails, national IDs) using standardized placeholder.
   ```python
   # Rule R2: redact PII values to preserve privacy
   clean = redact_pii(text, mask='<PII>')
   ```
3. **Action:** fix the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 8: G1 (Cut at vowel sign)

1. **Disease:** G1 (Cut at vowel sign), count in pack: 7. Examples: `d40a6e0c632b3dd0`: `'\nCopyright ©'@1685 | 'त ि'@696 | 'ि'@698`; `b511159269dc64a0`: `'ि'@598`; `506a604b057244e5`: `'९ ः'@180 | 'ः'@182`.
2. **Medicine:** Remove corrupt whitespace between Indic base consonant and following dependent vowel mark.
   ```python
   clean = regex.sub(r'([\p{Devanagari}\p{Bengali}...])\s+([\u0901-\u094f...])', r'\1\2', text)
   ```
3. **Action:** fix the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Isolated diacritics intentionally displayed in typography dictionaries may be merged.

## Medicine 9: G4 (Over-normalised)

1. **Disease:** G4 (Over-normalised), count in pack: 25. Examples: `5c05e18231a55839`: `'Maharashtra News, Latest Maharashtra ...'@1715 | 'Maharashtra News, Latest Maharashtra ...'@1715 | ' |'@1791`; `c8ad1802a6fbb058`: `'Maharashtra News, Latest Maharashtra ...'@1698 | 'Maharashtra News, Latest Maharashtra ...'@1698 | ' |'@1774`; `052f2791183c599c`: `'विश्वाचे आर्त - भाग १५ - १३० दाण्यांच...'@0 | 'काही प्रमाणात Dean Michael Ornish ह्य...'@11412 | ' अधिक ग्लूटन आवश्यक असलेल्या ब्रेडकरि...'@18747 | ' केक वगैरे पदार्थांत ग्लूटन कमी असलेल...'@18820 | ' |'@22014`.
2. **Medicine:** Normalize ASCII pipe '|' used in place of Devanagari danda '।' without mutating markdown tables.
   ```python
   clean = regex.sub(r'(?<=[\p{Devanagari}\p{M}])\s*\|\s*(?=[\p{Devanagari}\s]|$)', ' । ', text)
   clean = regex.sub(r'(?<=[\p{Devanagari}\p{M}])\s*\|\|\s*', ' ॥ ', clean)
   ```
3. **Action:** fix the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

