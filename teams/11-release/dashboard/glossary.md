# Public dashboard glossary

| Term | Meaning |
| --- | --- |
| Token | A piece of text that the model reads or predicts, such as part of a word or a punctuation mark. |
| Training step | An update to the model during training. |
| Training loss (next-token) | A measure of how well the model predicts the next token in its training text. Lower loss means better predictions on that text. |
| Training loss (step-bucket mean) | The average next-token training loss over a group of consecutive training steps. |
| Held-out validation loss | Next-token prediction loss on text set aside from training, averaged per token. |
| Held-out validation bits per byte | Prediction loss on text set aside from training, measured in bits per byte of text. This lets readers compare runs that split text into tokens differently when the runs use the same validation text. |
| Learning rate schedule | The pattern of changes to the learning rate during training. The learning rate controls how much the model changes at each step. |
| Tokens per byte | The number of tokens per byte of encoded text. A lower value means the same text is split into fewer tokens. |
| Mixture-of-experts load balance | In the least balanced layer, divide the busiest expert's workload by the average expert workload. An expert is a part of the model that processes selected tokens. |
