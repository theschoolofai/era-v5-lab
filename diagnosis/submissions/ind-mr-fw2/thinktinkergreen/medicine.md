# Medicine sheet: ind-mr-fw2 (thinktinkergreen)

Write one section for each disease that you found more than five times.

## Medicine 1: C3 (Truncated document)

1. **Disease:** C3 (Truncated document), count in pack: 20. Examples: `626fc9159542b61c`: `'Tags: Diabetes, Health, Health Tips, ...'@2770 | 'Tags: Diabetes, Health, Health Tips, ...'@2770 | 'Diabetes Tips : शुगर लेव्हल होणार नाह...'@838 | 'जेव्हा तुमच्या पेशी इन्सुलिनच्या सिग्...'@925 | ' News 18 Marathi यांना दुजोरा देत नाही'@2501`; `5c05e18231a55839`: `'Maharashtra News, Latest Maharashtra ...'@1715 | 'Maharashtra News, Latest Maharashtra ...'@1715 | ' |'@1791`; `c8ad1802a6fbb058`: `'Maharashtra News, Latest Maharashtra ...'@1698 | 'Maharashtra News, Latest Maharashtra ...'@1698 | ' |'@1774`.
2. **Medicine:** Drop truncated documents ending mid-sentence, or trim trailing incomplete fragments.
   ```python
   # If document terminates without valid terminal, drop or trim to last terminal
   clean = trim_to_last_sentence(text)
   ```
3. **Action:** drop the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 2: C4 (Two documents joined)

1. **Disease:** C4 (Two documents joined), count in pack: 6. Examples: `a84ec9a0a34a3f12`: `'\nCopyright ©'@923`; `d40a6e0c632b3dd0`: `'\nCopyright ©'@1685 | 'त ि'@696 | 'ि'@698`; `cedda2a2f29ef819`: `'\nCopyright ©'@1181`.
2. **Medicine:** Detect merged documents with mid-text copyright/boundary markers and split or drop.
   ```python
   # Drop concatenated documents lacking clear boundaries
   clean = split_joined_documents(text)
   ```
3. **Action:** drop the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 3: D3 (Mixed language (code-mixing))

1. **Disease:** D3 (Mixed language (code-mixing)), count in pack: 59. Examples: `00eed90bde196e9c`: `'How To Find Sweet Watermelon: उन्हाळ्...'@0`; `45099f1718f10018`: `'Lioness And leopard Fight Viral Video...'@0 | ' या व्हिडीओला इन्स्टाग्रामवर wildtrails'@1440 | 'in वर शेअर करण्यात आला आहे'@1480`; `924d41c82dfe4138`: `'Viral Video: सोशल मीडियावर व्हायरल हो...'@0 | 'ट्रॅव्हल कपल अशा एका अकाऊंटवरून अलीकड...'@669 | 'Video: विमानात आंघोळ'@1105`.
2. **Medicine:** Label natural code-mixed sentences per Rule R4; trim extraneous English scraping boilerplate.
   ```python
   # Natural code-mixing is preserved; English scraping trailers are stripped
   clean = strip_scraping_trailers(text)
   ```
3. **Action:** fix the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

## Medicine 4: G4 (Over-normalised)

1. **Disease:** G4 (Over-normalised), count in pack: 10. Examples: `5c05e18231a55839`: `'Maharashtra News, Latest Maharashtra ...'@1715 | 'Maharashtra News, Latest Maharashtra ...'@1715 | ' |'@1791`; `c8ad1802a6fbb058`: `'Maharashtra News, Latest Maharashtra ...'@1698 | 'Maharashtra News, Latest Maharashtra ...'@1698 | ' |'@1774`; `052f2791183c599c`: `'विश्वाचे आर्त - भाग १५ - १३० दाण्यांच...'@0 | 'काही प्रमाणात Dean Michael Ornish ह्य...'@11412 | ' अधिक ग्लूटन आवश्यक असलेल्या ब्रेडकरि...'@18747 | ' केक वगैरे पदार्थांत ग्लूटन कमी असलेल...'@18820 | ' |'@22014`.
2. **Medicine:** Normalize ASCII pipe '|' used in place of Devanagari danda '।' without mutating markdown tables.
   ```python
   clean = regex.sub(r'(?<=[\p{Devanagari}\p{M}])\s*\|\s*(?=[\p{Devanagari}\s]|$)', ' । ', text)
   clean = regex.sub(r'(?<=[\p{Devanagari}\p{M}])\s*\|\|\s*', ' ॥ ', clean)
   ```
3. **Action:** fix the text.
4. **Harm test:** PENDING (Gold set not available or pending human baseline).
5. **Side effects:** Rare edge cases where unusual character patterns carry intended semantic meaning.

