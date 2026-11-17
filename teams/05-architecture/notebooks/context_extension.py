# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.3.0",
#     "datasets==5.0.0",
#     "huggingface-hub==1.33.0",
#     "numpy==2.5.5",
#     "pandas==3.1.1",
#     "torch==2.11.0",
#     "transformers==5.14.1",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell(hide_code=True)
def imports():
    import marimo as mo
    import torch
    import torch.nn.functional as F
    import transformers
    import pandas as pd
    import altair as alt
    import numpy as np
    import json
    import hashlib
    import math
    import time
    import copy
    import os
    import platform
    import importlib.metadata
    from pathlib import Path
    from datasets import load_dataset
    from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM
    from huggingface_hub.utils import disable_progress_bars

    disable_progress_bars()
    torch.manual_seed(1234)
    torch.set_num_threads(16)
    torch.set_float32_matmul_precision('highest')
    alt.theme.enable('default')
    import datetime


    return (
        AutoConfig,
        AutoModelForCausalLM,
        AutoTokenizer,
        F,
        Path,
        alt,
        copy,
        datetime,
        hashlib,
        importlib,
        json,
        load_dataset,
        math,
        mo,
        np,
        os,
        pd,
        platform,
        torch,
        transformers,
    )


@app.cell(hide_code=True)
def introduction(mo):
    mo.md(r"""
    # Does YaRN help a 2K model read 4K?

    **G5 context-extension experiment · original SmolLM-135M · fixed weights**

    We compare ordinary RoPE with **2× YaRN** at 2,048 and 4,096 tokens.
    Every run predicts the **same final 512 tokens**. The short input is the
    2K suffix of the long input, so we can distinguish extra context from a change in position encoding.

    Three documents form a small paired study. Lower next-token loss is better.
    """)
    return


@app.cell
def settings(Path, mo, os, platform, torch, transformers):
    MODEL_ID = 'HuggingFaceTB/SmolLM-135M'
    MODEL_REVISION = '1d461723eec654e65efdc40cf49301c89c0c92f4'
    DATASET_ID = 'Salesforce/wikitext'
    DATASET_REVISION = 'b08601e04326c79dfdd32d625aee71d232d685c3'
    NATIVE_LENGTH = 2048
    LONG_LENGTH = 4096
    TAIL_LENGTH = 512
    DOCUMENT_COUNT = 3
    TIMING_REPEATS = 3
    DEVICE = 'cuda'
    DTYPE = torch.bfloat16
    ARTIFACT_DIR = Path(mo.notebook_dir() or Path.cwd()) / 'g5_context' / 'artifacts'
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    assert torch.cuda.is_available(), 'This notebook expects the allocated CUDA sandbox.'
    assert torch.cuda.is_bf16_supported(), 'Use a consistent supported dtype across all runs.'
    hardware = {
        'gpu': torch.cuda.get_device_name(0),
        'vram_gib': round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2),
        'visible_vcpus': len(os.sched_getaffinity(0)),
        'visible_ram_gib': round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 2**30, 1),
        'python': platform.python_version(),
        'torch': torch.__version__,
        'transformers': transformers.__version__,
        'cuda': torch.version.cuda,
    }
    for _label, _file in [('container_memory_limit', 'memory.max'), ('container_cpu_quota', 'cpu.max')]:
        _path = Path('/sys/fs/cgroup') / _file
        if _path.exists():
            hardware[_label] = _path.read_text().strip()
    mo.md(f"**{hardware['gpu']}** · {hardware['vram_gib']:.1f} GiB VRAM · BF16 · batched SDPA scoring")
    return (
        ARTIFACT_DIR,
        DATASET_ID,
        DATASET_REVISION,
        DEVICE,
        DOCUMENT_COUNT,
        DTYPE,
        LONG_LENGTH,
        MODEL_ID,
        MODEL_REVISION,
        NATIVE_LENGTH,
        TAIL_LENGTH,
        TIMING_REPEATS,
        hardware,
    )


@app.cell
def load_models(
    AutoConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    DEVICE,
    DTYPE,
    LONG_LENGTH,
    MODEL_ID,
    MODEL_REVISION,
    NATIVE_LENGTH,
    copy,
    mo,
):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    base_config = AutoConfig.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    assert base_config.max_position_embeddings == NATIVE_LENGTH
    assert base_config.num_attention_heads == 9 and base_config.num_key_value_heads == 3

    yarn_config = copy.deepcopy(base_config)
    yarn_config.max_position_embeddings = LONG_LENGTH
    yarn_config.rope_parameters = {
        'rope_type': 'yarn', 'rope_theta': 10000.0, 'factor': 2.0,
        'original_max_position_embeddings': NATIVE_LENGTH,
        'beta_fast': 32.0, 'beta_slow': 1.0,
    }
    with mo.status.spinner(title='Loading two identical weight sets with different rotary settings'):
        native_model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, revision=MODEL_REVISION, config=base_config,
            dtype=DTYPE, attn_implementation='sdpa',
        ).to(DEVICE).eval()
        yarn_model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, revision=MODEL_REVISION, config=yarn_config,
            dtype=DTYPE, attn_implementation='sdpa',
        ).to(DEVICE).eval()
    models = {'Original RoPE': native_model, 'YaRN ×2': yarn_model}
    parameter_count = sum(p.numel() for p in native_model.parameters())
    return (
        base_config,
        models,
        native_model,
        parameter_count,
        tokenizer,
        yarn_config,
        yarn_model,
    )


@app.cell
def data(
    DATASET_ID,
    DATASET_REVISION,
    DEVICE,
    DOCUMENT_COUNT,
    LONG_LENGTH,
    NATIVE_LENGTH,
    TAIL_LENGTH,
    hashlib,
    json,
    load_dataset,
    mo,
    pd,
    tokenizer,
    torch,
):
    def select_documents(rows, tokenizer, count, length):
        selected = []
        article_title, paragraphs = '', []
        def consider(title, paragraphs):
            text = '\n'.join(paragraphs).strip()
            ids = tokenizer(text, add_special_tokens=False, truncation=False)['input_ids']
            if title and len(ids) >= length:
                selected.append({
                    'title': title, 'available_tokens': len(ids), 'ids': ids[:length],
                    'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                    'tokens_sha256': hashlib.sha256(json.dumps(ids[:length]).encode()).hexdigest(),
                })
        for row in rows:
            line = row['text'].strip()
            # WikiText marks article titles with one equals sign on each side.
            new_article = line.startswith('= ') and line.endswith(' =') and not line.startswith('= =')
            if new_article:
                consider(article_title, paragraphs)
                if len(selected) == count:
                    return selected
                article_title, paragraphs = line.strip('= ').strip(), []
            elif line:
                paragraphs.append(line)
        consider(article_title, paragraphs)
        assert len(selected) >= count, 'Insufficient complete long articles in the selected split.'
        return selected[:count]

    with mo.status.spinner(title='Selecting the first three complete test articles with at least 4K tokens'):
        evaluation_dataset = load_dataset(
            'parquet', data_files={'test': f'hf://datasets/{DATASET_ID}@{DATASET_REVISION}/wikitext-103-raw-v1/test-00000-of-00001.parquet'}, split='test',
        )
        documents = select_documents(evaluation_dataset, tokenizer, DOCUMENT_COUNT, LONG_LENGTH)
    long_inputs = torch.tensor([d['ids'] for d in documents], dtype=torch.long, device=DEVICE)
    short_inputs = long_inputs[:, -NATIVE_LENGTH:].contiguous()
    target_ids = long_inputs[:, -TAIL_LENGTH:]
    assert torch.equal(target_ids, short_inputs[:, -TAIL_LENGTH:])
    document_table = pd.DataFrame([
        {'Document': d['title'], 'Available tokens': d['available_tokens'],
         'Used tokens': LONG_LENGTH, 'SHA256': d['tokens_sha256'][:16]}
        for d in documents
    ])
    mo.vstack([
        mo.md('## Evaluation text\nThe first three sufficiently long articles in the pinned WikiText-103 **test** split. Selection happens before scoring. Pretraining overlap with this older corpus is unknown.'),
        mo.ui.table(document_table, selection=None),
    ])
    return documents, long_inputs, short_inputs, target_ids


@app.cell(hide_code=True)
def window_diagram(mo):
    _svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 200" role="img" aria-label="Both context windows predict identical last 512 tokens">\n<g font-family="system-ui,sans-serif" font-size="14" fill="#334155">\n<text x="12" y="58">2K input</text><text x="12" y="118">4K input</text>\n<rect x="110" y="32" width="380" height="38" fill="#f1f5f9" rx="4"/>\n<rect x="490" y="32" width="285" height="38" fill="#93c5fd"/>\n<rect x="775" y="32" width="95" height="38" fill="#fbbf24" rx="3"/>\n<rect x="110" y="92" width="665" height="38" fill="#93c5fd" rx="4"/>\n<rect x="775" y="92" width="95" height="38" fill="#fbbf24" rx="3"/>\n<text x="110" y="154">0</text><text x="475" y="154">2,048</text><text x="749" y="154">3,584</text><text x="835" y="154">4,096</text>\n<rect x="260" y="177" width="14" height="14" fill="#93c5fd"/><text x="282" y="189">Context tokens</text>\n<rect x="470" y="177" width="14" height="14" fill="#fbbf24"/><text x="492" y="189">Same 512 scored targets</text>\n</g></svg>'
    mo.vstack([mo.md('## A matched comparison\nPositions reset to zero inside each input. The extra 2K tokens are the only input difference between lengths.'), mo.Html(_svg)])
    return


@app.cell
def score_function(F, TAIL_LENGTH, torch):
    @torch.inference_mode()
    def score_tail(model, inputs, tail_length=TAIL_LENGTH):
        # Only 513 hidden rows enter the vocabulary head. The final row predicts
        # a token outside the input, so discard it and score the preceding 512.
        outputs = model(input_ids=inputs, use_cache=False, logits_to_keep=tail_length + 1)
        prediction_logits = outputs.logits[:, :-1, :].float()
        targets = inputs[:, -tail_length:]
        losses = F.cross_entropy(
            prediction_logits.reshape(-1, prediction_logits.shape[-1]),
            targets.reshape(-1), reduction='none',
        ).view(inputs.shape[0], tail_length)
        return losses

    return (score_tail,)


@app.cell
def checks(
    DEVICE,
    DOCUMENT_COUNT,
    F,
    NATIVE_LENGTH,
    TAIL_LENGTH,
    math,
    mo,
    native_model,
    parameter_count,
    pd,
    score_tail,
    short_inputs,
    target_ids,
    torch,
    yarn_model,
):
    checks = []
    def check(name, condition, detail):
        assert bool(condition), f'{name}: {detail}'
        checks.append({'Check': name, 'Outcome': 'PASS', 'Detail': detail})

    check('Identical pretrained weights', all(
        torch.equal(p, q) for p, q in zip(native_model.parameters(), yarn_model.parameters())
    ), f'{parameter_count:,} parameters per model')
    check('Identical scored targets', torch.equal(short_inputs[:, -TAIL_LENGTH:], target_ids),
          f'{DOCUMENT_COUNT} × {TAIL_LENGTH} target IDs in every condition')
    _rotary = yarn_model.model.rotary_emb
    _i = torch.arange(0, 64, 2, device=DEVICE).float()
    _base_frequencies = 10000.0 ** (-_i / 64)
    _low = math.floor(64 * math.log(NATIVE_LENGTH / (32 * 2 * math.pi)) / (2 * math.log(10000)))
    _high = math.ceil(64 * math.log(NATIVE_LENGTH / (1 * 2 * math.pi)) / (2 * math.log(10000)))
    _ramp = ((torch.arange(32, device=DEVICE).float() - _low) / (_high - _low)).clamp(0, 1)
    _expected = _base_frequencies * (1 - _ramp) + (_base_frequencies / 2) * _ramp
    check('YaRN uses original 2K reference', torch.allclose(_rotary.inv_freq, _expected, atol=1e-7, rtol=1e-6),
          f'Frequency-ramp bounds {_low} and {_high}, extension factor 2')
    check('YaRN attention scale applied once', abs(float(_rotary.attention_scaling) - (1 + 0.1 * math.log(2))) < 1e-6,
          f'Rotary amplitude factor {float(_rotary.attention_scaling):.8f}')

    with torch.inference_mode():
        _probe = short_inputs[:1, :128]
        _full = native_model(input_ids=_probe, use_cache=False).logits[:, -33:-1, :].float()
        _expected_loss = F.cross_entropy(_full.reshape(-1, _full.shape[-1]), _probe[:, -32:].reshape(-1), reduction='none').view(1, 32)
        _trimmed_loss = score_tail(native_model, _probe, tail_length=32)
    check('Tail projection and next-token shift', torch.allclose(_trimmed_loss, _expected_loss, atol=1e-5, rtol=1e-5),
          f'Max loss difference {(_trimmed_loss - _expected_loss).abs().max().item():.3g}')

    _sdpa_loss = score_tail(native_model, short_inputs).mean(1)
    native_model.set_attn_implementation('eager')
    try:
        _eager_loss = score_tail(native_model, short_inputs).mean(1)
    finally:
        native_model.set_attn_implementation('sdpa')
    backend_max_nll_difference = (_sdpa_loss - _eager_loss).abs().max().item()
    check('SDPA versus eager numerical drift', backend_max_nll_difference < 0.02,
          f'Max per-document mean NLL difference {backend_max_nll_difference:.6f} nats/token (BF16 screen <0.02)')
    checks_frame = pd.DataFrame(checks)
    mo.vstack([mo.md('## Correctness before speed\nFrequency math, target alignment and a BF16 backend check run before the comparisons.'), mo.ui.table(checks_frame, selection=None)])
    return backend_max_nll_difference, check, checks


@app.cell
def run_experiment(
    DOCUMENT_COUNT,
    LONG_LENGTH,
    NATIVE_LENGTH,
    TAIL_LENGTH,
    TIMING_REPEATS,
    check,
    documents,
    long_inputs,
    math,
    mo,
    models,
    np,
    pd,
    score_tail,
    short_inputs,
    torch,
):
    conditions = [
        ('A', 'Original RoPE', NATIVE_LENGTH),
        ('B', 'Original RoPE', LONG_LENGTH),
        ('C', 'YaRN ×2', LONG_LENGTH),
        ('D', 'YaRN ×2', NATIVE_LENGTH),
    ]
    result_rows = []
    timing_rows = []
    token_losses = {}

    with mo.status.progress_bar(total=len(conditions), title='Batched paired evaluation') as _progress:
        for _run, _method, _length in conditions:
            _inputs = short_inputs if _length == NATIVE_LENGTH else long_inputs
            _model = models[_method]
            # Warm up each shape before timing. All three articles share one batch.
            _losses = score_tail(_model, _inputs)
            assert torch.isfinite(_losses).all()
            torch.cuda.synchronize()
            _elapsed = []
            _peak = []
            for _repeat in range(TIMING_REPEATS):
                torch.cuda.reset_peak_memory_stats()
                _start, _end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                _start.record()
                _measured = score_tail(_model, _inputs)
                _end.record()
                torch.cuda.synchronize()
                assert torch.isfinite(_measured).all()
                _elapsed.append(_start.elapsed_time(_end))
                _peak.append(torch.cuda.max_memory_allocated() / 2**20)
            token_losses[_run] = _losses.cpu().numpy()
            for _doc, _loss in zip(documents, _losses.mean(1).tolist()):
                result_rows.append({'Run': _run, 'Method': _method, 'Context': _length,
                                    'Document': _doc['title'], 'NLL': _loss,
                                    'Perplexity': math.exp(_loss), 'Scored tokens': TAIL_LENGTH})
            timing_rows.append({'Run': _run, 'Method': _method, 'Context': _length,
                                'Median GPU ms': float(np.median(_elapsed)),
                                'Min GPU ms': min(_elapsed), 'Max GPU ms': max(_elapsed),
                                'Input tokens per second': DOCUMENT_COUNT * _length / (np.median(_elapsed) / 1000),
                                'Peak allocated MiB': max(_peak), 'Batch': DOCUMENT_COUNT})
            _progress.update()
    results = pd.DataFrame(result_rows)
    timings = pd.DataFrame(timing_rows)
    summary = results.groupby(['Run', 'Method', 'Context'], as_index=False).agg(
        NLL=('NLL', 'mean'), scored_tokens=('Scored tokens', 'sum'))
    summary['Perplexity'] = np.exp(summary['NLL'])
    paired = results.pivot(index='Document', columns='Run', values='NLL')
    paired['Long change C−B'] = paired['C'] - paired['B']
    paired['Short change D−A'] = paired['D'] - paired['A']
    check('All four real input lengths scored', len(results) == 4 * DOCUMENT_COUNT and set(summary['scored_tokens']) == {DOCUMENT_COUNT * TAIL_LENGTH},
          '12 document-condition rows, 1,536 scored tokens per condition')
    mo.vstack([mo.md('## Measured language loss\nNLL is in nats per target token. Perplexity is exp(mean NLL), using the same targets in every row.'), mo.ui.table(summary.round(5), selection=None)])
    return conditions, paired, results, summary, timings, token_losses


@app.cell
def loss_charts(alt, mo, paired, results):
    _base = alt.Chart(results).encode(
        x=alt.X('Context:O', title='Input context tokens'),
        y=alt.Y('NLL:Q', title='Tail NLL · lower is better', scale=alt.Scale(zero=False)),
        color=alt.Color('Method:N', scale=alt.Scale(domain=['Original RoPE','YaRN ×2'], range=['#2563eb','#d97706'])),
        tooltip=['Document:N','Method:N','Context:O',alt.Tooltip('NLL:Q',format='.4f')],
    )
    loss_chart = (_base.mark_line(point=True).properties(width=230, height=210)
                  .facet(column=alt.Column('Document:N', title=None)).resolve_scale(y='independent'))
    _changes = paired.reset_index().melt(id_vars='Document', value_vars=['Long change C−B','Short change D−A'], var_name='Comparison',value_name='NLL change')
    delta_chart = alt.Chart(_changes).mark_bar(size=18).encode(
        y=alt.Y('Document:N',title=None), x=alt.X('NLL change:Q',title='YaRN minus original · negative favors YaRN'),
        color=alt.Color('Comparison:N',scale=alt.Scale(range=['#2563eb','#d97706'])),
        tooltip=['Document','Comparison',alt.Tooltip('NLL change:Q',format='.5f')],
    ).properties(width=620,height=100).facet(row=alt.Row('Comparison:N',title=None,header=alt.Header(labelAngle=0,labelAlign='left'))).resolve_scale(x='independent')
    mo.vstack([mo.ui.altair_chart(loss_chart), mo.ui.altair_chart(delta_chart)])
    return delta_chart, loss_chart


@app.cell
def batch_scaling(
    DEVICE,
    DOCUMENT_COUNT,
    LONG_LENGTH,
    TIMING_REPEATS,
    alt,
    long_inputs,
    mo,
    np,
    pd,
    results,
    score_tail,
    token_losses,
    torch,
    yarn_model,
):

    # Repeated fixtures change the workload size, not the quality sample count.
    _ = results
    batch_scaling_rows = []
    for _batch in [3, 6, 12, 24, 48]:
        _batch_inputs = long_inputs.repeat(_batch // DOCUMENT_COUNT, 1)
        _warmup = score_tail(yarn_model, _batch_inputs)
        assert torch.isfinite(_warmup).all()
        torch.cuda.synchronize()
        _milliseconds, _peaks = [], []
        for _repeat in range(TIMING_REPEATS):
            torch.cuda.reset_peak_memory_stats()
            _start, _end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            _start.record()
            _batch_loss = score_tail(yarn_model, _batch_inputs)
            _end.record()
            torch.cuda.synchronize()
            _milliseconds.append(_start.elapsed_time(_end))
            _peaks.append(torch.cuda.max_memory_allocated() / 2**20)
            assert torch.isfinite(_batch_loss).all()
        assert torch.allclose(_batch_loss[:DOCUMENT_COUNT].mean(1),
                              torch.tensor(token_losses['C'], device=DEVICE).mean(1), atol=0.02, rtol=0)
        batch_scaling_rows.append({'Batch': _batch, 'Median GPU ms': float(np.median(_milliseconds)),
            'Input tokens per second': _batch * LONG_LENGTH / (np.median(_milliseconds) / 1000),
            'Peak allocated MiB': max(_peaks)})
        del _batch_inputs, _batch_loss, _warmup
    batch_scaling_results = pd.DataFrame(batch_scaling_rows)
    throughput_chart = alt.Chart(batch_scaling_results).mark_line(point=True, color='#2563eb').encode(
        x=alt.X('Batch:O', title='Batched 4K inputs'),
        y=alt.Y('Input tokens per second:Q', title='Input tokens / second'),
        tooltip=['Batch',alt.Tooltip('Median GPU ms:Q',format='.2f'),
                 alt.Tooltip('Input tokens per second:Q',format=',.0f'),
                 alt.Tooltip('Peak allocated MiB:Q',format='.1f')],
    ).properties(width=650,height=220)
    mo.vstack([
        mo.md('## How much batching helps\nThese repeated fixtures measure GPU throughput. There are still only three distinct quality samples. Every batch passes a finite-loss and numerical-drift check.'),
        mo.ui.altair_chart(throughput_chart),
        mo.ui.table(batch_scaling_results.round(2),selection=None),
    ])

    return batch_scaling_results, throughput_chart


@app.cell
def precision_check(
    AutoModelForCausalLM,
    DEVICE,
    MODEL_ID,
    MODEL_REVISION,
    NATIVE_LENGTH,
    base_config,
    batch_scaling_results,
    conditions,
    copy,
    documents,
    long_inputs,
    mo,
    np,
    pd,
    score_tail,
    short_inputs,
    torch,
    yarn_config,
):

    _ = batch_scaling_results
    precision_rows = []
    with mo.status.spinner(title='Checking whether the quality conclusion survives FP32 arithmetic'):
        _fp32_models = {
            'Original RoPE': AutoModelForCausalLM.from_pretrained(
                MODEL_ID, revision=MODEL_REVISION, config=copy.deepcopy(base_config),
                dtype=torch.float32, attn_implementation='sdpa').to(DEVICE).eval(),
            'YaRN ×2': AutoModelForCausalLM.from_pretrained(
                MODEL_ID, revision=MODEL_REVISION, config=copy.deepcopy(yarn_config),
                dtype=torch.float32, attn_implementation='sdpa').to(DEVICE).eval(),
        }
        for _run, _method, _length in conditions:
            _inputs = short_inputs if _length == NATIVE_LENGTH else long_inputs
            _fp32_losses = score_tail(_fp32_models[_method], _inputs)
            assert torch.isfinite(_fp32_losses).all()
            for _document, _loss in zip(documents, _fp32_losses.mean(1).tolist()):
                precision_rows.append({'Run':_run, 'Method':_method, 'Context':_length,
                                       'Document':_document['title'],'NLL':_loss})
        del _fp32_models, _fp32_losses
        torch.cuda.empty_cache()
    precision_results = pd.DataFrame(precision_rows)
    precision_summary = precision_results.groupby(['Run','Method','Context'],as_index=False).agg(NLL=('NLL','mean'))
    precision_summary['Perplexity'] = np.exp(precision_summary['NLL'])
    mo.vstack([
        mo.md('## Precision sensitivity\nThe same checkpoint and target tokens are scored again in FP32 with SDPA and highest float32 matmul precision. These quality checks are separate from BF16 timing.'),
        mo.ui.table(precision_summary.round(6),selection=None),
    ])

    return precision_results, precision_summary


@app.cell(hide_code=True)
def interpretation(DOCUMENT_COUNT, math, mo, paired, precision_summary):

    long_delta = float(paired['Long change C−B'].mean())
    short_delta = float(paired['Short change D−A'].mean())
    long_vs_native = float((paired['C'] - paired['A']).mean())
    long_wins = int((paired['Long change C−B'] < 0).sum())
    _fp32_means = precision_summary.set_index('Run')['NLL']
    _fp32_long_delta = float(_fp32_means['C'] - _fp32_means['B'])
    _fp32_short_delta = float(_fp32_means['D'] - _fp32_means['A'])
    mo.md(f"""
    ## What this sample says

    At 4K, YaRN changes mean tail loss by **{long_delta:+.5f} nats/token**
    and lowers loss on **{long_wins}/{DOCUMENT_COUNT} documents**.
    Compared with native 2K, its 4K loss is **{long_vs_native:+.5f} nats/token**
    ({100 * math.expm1(long_vs_native):+.2f}% perplexity).

    YaRN {'largely recovers native-window quality' if abs(long_vs_native) < 0.1 else 'changes native-window quality'} on this sample.
    {'The longer context does not improve mean loss over native 2K here.' if long_vs_native >= 0 else 'Mean loss also improves over native 2K here.'}

    The BF16 short-window change is **{short_delta:+.5f} nats/token**,
    with mixed per-document differences. In FP32, the changes are
    **{_fp32_long_delta:+.5f}** at 4K and **{_fp32_short_delta:+.5f}** at 2K.
    These are descriptive measurements on three documents, not a general short-context verdict.

    This **inference-only retrofit** measures loss on fixed English Wikipedia tails.
    Retrieval, distant-fact use, multilingual quality and continued training need their own evaluation.
    TSAI chooses the production context schedule.
    """)

    return long_delta, long_vs_native, short_delta


@app.cell(hide_code=True)
def performance(mo, timings):
    mo.vstack([
        mo.md('## Efficient enough to submit\nThree documents are batched. CUDA timing excludes warm-up, downloads and model loading. It covers forward execution and tail scoring, without KV caching. Both model copies remain resident during every measurement.'),
        mo.ui.table(timings.round(2), selection=None),
        mo.md('**Optimizations used** · SDPA attention after an eager comparison · BF16 · inference mode · only 513 vocabulary-head rows · one cached dataset load. These are evaluation throughput measurements, not training or generation benchmarks.'),
    ])
    return


@app.cell(hide_code=True)
def export(
    ARTIFACT_DIR,
    DATASET_ID,
    DATASET_REVISION,
    DOCUMENT_COUNT,
    DTYPE,
    MODEL_ID,
    MODEL_REVISION,
    backend_max_nll_difference,
    batch_scaling_results,
    checks,
    datetime,
    delta_chart,
    documents,
    hardware,
    importlib,
    json,
    long_delta,
    long_vs_native,
    loss_chart,
    mo,
    native_model,
    np,
    paired,
    precision_results,
    precision_summary,
    results,
    short_delta,
    summary,
    throughput_chart,
    timings,
    token_losses,
    yarn_model,
):
    manifest = {
        'experiment': 'SmolLM-135M inference-only YaRN2 2K/4K',
        'model_id': MODEL_ID, 'model_revision': MODEL_REVISION,
        'dataset_id': DATASET_ID, 'dataset_revision': DATASET_REVISION,
        'dataset_config': 'wikitext-103-raw-v1', 'dataset_split': 'test',
        'selection': 'first three complete articles with at least 4096 tokens; first 4096 tokens of each',
        'short_input': 'last 2048 tokens of each fixed 4096-token input',
        'scoring': 'same last512 target IDs; full input; last513 logit rows with final row dropped',
        'dtype': str(DTYPE), 'attention_backend': 'sdpa', 'batch_size': DOCUMENT_COUNT,
        'native_rope': native_model.config.rope_parameters,
        'yarn_rope': yarn_model.config.rope_parameters,
        'yarn_attention_factor': float(yarn_model.model.rotary_emb.attention_scaling),
        'seed': 1234, 'hardware': hardware,
        'versions': {p:importlib.metadata.version(p) for p in ['torch','transformers','datasets','huggingface-hub','pandas','altair']},
        'checks': checks, 'backend_max_nll_difference': backend_max_nll_difference,
        'long_mean_nll_change': long_delta, 'short_mean_nll_change': short_delta,
        'executed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'precision_sensitivity': precision_summary.to_dict(orient='records'),
        'batch_scaling': batch_scaling_results.to_dict(orient='records'),
        'long_vs_native_nll_change': long_vs_native,
        'timing_scope': 'GPU forward plus tail cross-entropy; one shape warmup; 3 timed repeats; both models resident',
    }
    batch_scaling_results.to_csv(ARTIFACT_DIR/'batch_scaling.csv',index=False)
    precision_results.to_csv(ARTIFACT_DIR/'fp32_sensitivity.csv',index=False)
    throughput_chart.save(str(ARTIFACT_DIR/'throughput_chart.html'))
    results.to_csv(ARTIFACT_DIR/'document_results.csv',index=False)
    summary.to_csv(ARTIFACT_DIR/'summary.csv',index=False)
    paired.to_csv(ARTIFACT_DIR/'paired_changes.csv')
    timings.to_csv(ARTIFACT_DIR/'timings.csv',index=False)
    (ARTIFACT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,default=str))
    (ARTIFACT_DIR/'input_fixtures.json').write_text(json.dumps(documents,indent=2))
    np.savez_compressed(ARTIFACT_DIR/'per_token_nll.npz',**token_losses)
    loss_chart.save(str(ARTIFACT_DIR/'loss_chart.html'))
    delta_chart.save(str(ARTIFACT_DIR/'paired_changes_chart.html'))
    mo.vstack([
        mo.md(f'## Evidence saved\nCSV results, per-token losses, exact input IDs and the execution manifest are in `{ARTIFACT_DIR}`.'),
        mo.download(data=(ARTIFACT_DIR/'manifest.json').read_bytes(),filename='g5_context_manifest.json',label='Download execution manifest'),
        mo.download(data=results.to_csv(index=False).encode(),filename='g5_context_results.csv',label='Download measured results'),
        mo.accordion({'Environment and rotary settings':mo.json(manifest), 'Sources':mo.md('[Checkpoint](https://huggingface.co/HuggingFaceTB/SmolLM-135M) · [WikiText](https://huggingface.co/datasets/Salesforce/wikitext) · [YaRN](https://arxiv.org/abs/2309.00071) · [Framework RoPE API](https://huggingface.co/docs/transformers/main/en/internal/rope_utils)')}),
    ])
    return


if __name__ == "__main__":
    app.run()
