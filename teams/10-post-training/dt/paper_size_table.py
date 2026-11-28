#!/usr/bin/env python3
"""Deletion Tuning against full fine-tuning (FFT) and LoRA by model size, from the paper's own tables
(arXiv 2611.10866v1, "The Surprising Effectiveness of Deleting Weights in LLM Post-Training"). See
../results/dt_paper_size_threshold.md.

    python dt/paper_size_table.py

The numbers below are copied from the paper's tables (best-checkpoint accuracy in %, adapter size in MB):
  Table 1  GRPO: Llama-3.2-1B/3B-Instruct and Llama-3-8B-Instruct on GSM8K; Qwen2.5-0.5B/3B/7B base on the
           six-benchmark SimpleRL-Zoo mean. Rows Base, FFT, LoRA r=1, LoRA r=4, MTH 99%, MTH 99.95%, Deletion Tuning.
  Table 2  GRPO at larger scale: Qwen2.5-14B and Qwen3-30B-A3B on SimpleRL-Zoo (Base, FFT, Deletion Tuning).
  Table 5  SFT: Llama-3.2-1B/3B-Instruct, mean over the 14 MMLU-Pro subjects and the 23 BBEH subtasks.
  Table 8  the six SimpleRL-Zoo benchmarks per Qwen size, FFT and Deletion Tuning rows.
  Tables 13-15  the paper's hyperparameter sweeps at Llama 8B and Qwen 7B (DT: eta x lambda x lr; FFT: lr x KL).
Derived here: DT minus FFT in points, DT / FFT accuracy, and the share of FFT's gain over the base model that DT
reaches, (DT - base) / (FFT - base). No other source.
"""
from __future__ import annotations

# (setting, model, base, fft, lora_r1, lora_r4, mth_99, mth_9995, dt, fft_mb, dt_mb); None = not in that table
ROWS = [
    ('GRPO, GSM8K (Table 1)', 'Llama 1B', 1.21, 60.50, 59.29, 60.58, 60.73, 58.61, 54.44, 4714, 1.0),
    ('GRPO, GSM8K (Table 1)', 'Llama 3B', 53.53, 82.49, 82.39, 82.44, 80.53, 82.17, 81.49, 12256, 3.1),
    ('GRPO, GSM8K (Table 1)', 'Llama 8B', 60.27, 83.24, 83.38, 82.87, 83.31, 83.07, 83.55, 30633, 8.4),
    ('GRPO, SimpleRL-Zoo (Table 1)', 'Qwen 0.5B', 10.44, 19.01, 20.30, 20.30, 21.84, 20.16, 17.64, 1885, 0.5),
    ('GRPO, SimpleRL-Zoo (Table 1)', 'Qwen 3B', 37.73, 44.35, 43.55, 43.59, 44.16, 43.87, 41.98, 11772, 2.7),
    ('GRPO, SimpleRL-Zoo (Table 1)', 'Qwen 7B', 40.18, 51.89, 52.13, 51.70, 52.03, 51.24, 52.32, 29051, 6.9),
    ('GRPO, SimpleRL-Zoo (Table 2)', 'Qwen 14B', 44.37, 54.87, None, None, None, None, 55.43, 56343, 11.4),
    ('GRPO, SimpleRL-Zoo (Table 2)', 'Qwen3 30B-A3B', 49.41, 58.43, None, None, None, None, 58.54, 116471, 29.6),
    ('SFT, MMLU-Pro (Table 5)', 'Llama 1B', 10.37, 16.97, None, None, None, None, 18.62, 4714, 1.0),
    ('SFT, MMLU-Pro (Table 5)', 'Llama 3B', 12.63, 21.19, None, None, None, None, 22.28, 12256, 3.1),
    ('SFT, BBEH (Table 5)', 'Llama 1B', 2.17, 8.35, None, None, None, None, 5.65, 4714, 1.0),
    ('SFT, BBEH (Table 5)', 'Llama 3B', 8.87, 11.39, None, None, None, None, 11.39, 12256, 3.1),
]


BENCH = ('GSM8K', 'MATH500', 'Minerva', 'OlympiadBench', 'AIME24', 'AMC23')
PROBLEMS = {'AIME24': 30, 'AMC23': 40}   # problems per set; the table's values are multiples of 1/30 and 1/40
TABLE8 = {   # model: (FFT row, Deletion Tuning row)
    'Qwen 0.5B': ((48.07, 36.00, 4.78, 7.73, 0.00, 17.50), (44.12, 33.40, 5.51, 6.98, 3.33, 12.50)),
    'Qwen 3B': ((83.62, 66.20, 23.16, 26.45, 16.67, 50.00), (83.78, 66.20, 22.79, 25.78, 13.33, 40.00)),
    'Qwen 7B': ((91.43, 78.20, 33.46, 39.92, 13.33, 55.00), (91.28, 78.80, 32.72, 40.29, 23.33, 47.50)),
}


# Table 13 (Llama 8B, GSM8K) and Table 14 (Qwen 7B, SimpleRL-Zoo): DT for eta 1/2048, 1/4096, 1/8192 (rows) x
# (lambda 0, lr 1e-4), (lambda 0, lr 3e-4), (lambda 1e-5, lr 1e-4), (lambda 1e-5, lr 3e-4); Table 15: FFT for
# (lr 5e-7, KL 0), (5e-7, 1e-4), (1e-6, 0), (1e-6, 1e-4).
SWEEPS = {
    'Llama 8B': {'dt': (83.40, 82.49, 82.34, 83.55, 83.02, 82.03, 83.09, 83.09, 83.40, 82.49, 83.09, 83.02),
                 'fft': (83.23, 82.55, 83.24, 81.89), 'fft_main': 83.24},
    'Qwen 7B': {'dt': (51.79, 51.92, 49.60, 52.32, 52.23, 52.80, 50.29, 51.91, 51.14, 52.10, 51.29, 52.34),
                'fft': (50.55, 51.89, 51.93, 50.79), 'fft_main': 51.89},
}


def main() -> None:
    print('setting                       model           base    FFT  best LoRA/MTH    DT  DT-FFT  DT/FFT  '
          'DT share of FFT gain  FFT MB / DT MB')
    for setting, model, base, fft, l1, l4, m99, m9995, dt, fft_mb, dt_mb in ROWS:
        others = [x for x in (l1, l4, m99, m9995) if x is not None]
        best = f'{max(others):6.2f}' if others else '     -'
        print(f'{setting:29s} {model:14s} {base:6.2f} {fft:6.2f}  {best:>13s} {dt:6.2f} {dt - fft:+7.2f} '
              f'{dt / fft:7.1%} {(dt - base) / (fft - base):21.1%} {fft_mb / dt_mb:15,.0f}x')
    print('\nSimpleRL-Zoo per benchmark (Table 8): DT minus FFT, points (problems, for the two small sets)')
    print('model      ' + ''.join(f'{b:>16s}' for b in BENCH) + '   mean')
    for model, (fft, dt) in TABLE8.items():
        cells = []
        for b, f, d in zip(BENCH, fft, dt):
            c = f'{d - f:+.2f}'
            if b in PROBLEMS:
                c += f' ({round((d - f) / 100 * PROBLEMS[b]):+d})'
            cells.append(f'{c:>16s}')
        print(f'{model:11s}' + ''.join(cells) + f'  {sum(dt) / 6 - sum(fft) / 6:+.2f}')
    print('\nHyperparameter sweeps (Tables 13-15): spread = best - worst setting, points')
    for model, sw in SWEEPS.items():
        dt, fft = sw['dt'], sw['fft']
        print(f'{model:9s} DT {len(dt)} settings {min(dt):.2f} to {max(dt):.2f} (spread {max(dt) - min(dt):.2f}); '
              f'FFT {len(fft)} settings {min(fft):.2f} to {max(fft):.2f} (spread {max(fft) - min(fft):.2f}); '
              f'DT settings at or above the main FFT number {sw["fft_main"]:.2f}: {sum(x >= sw["fft_main"] for x in dt)}')


if __name__ == '__main__':
    main()
