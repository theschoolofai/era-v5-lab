#!/usr/bin/env python3
"""summarize.py on tiny hand-made inputs (standard library only, under a second):  python test_summarize.py"""
import json, tempfile, unittest
from pathlib import Path

import summarize as sm

PROMPT = [7, 3, 9]


def g5(target, top1):
    """A G5 reference entry for PROMPT: target_lp for positions 0..T-2, top-1 ids for positions 0..T-1."""
    return dict(target_lp=target, top_ids=[[t, 0] for t in top1], top_lp=[[-1.0, -2.0]] * len(top1),
                margin=[0.5] * len(top1))


def engine(target, top1, first_none=False):
    """An engine result in sgl_probe.py's layout (first_none: vllm_probe.py's None in position 0)."""
    itl = [None if first_none else [None, PROMPT[0], None]] + [[lp, t, None] for lp, t in zip(target, PROMPT[1:])]
    itop = [None] + [[[-1.0, i, None]] for i in top1[:-1]]
    return dict(input_token_logprobs=itl, input_top_logprobs=itop, output_top_logprobs=[[[-1.0, top1[-1], None]]])


class Alignment(unittest.TestCase):
    def test_engine_entry_i_is_g5_position_i_minus_1(self):
        target, top1 = sm.from_engine(engine([-0.5, -0.25], [11, 12, 13]), PROMPT)
        self.assertEqual(target, [-0.5, -0.25])
        self.assertEqual(top1, [11, 12, 13])     # input_top_logprobs[1], [2], then the generated token

    def test_vllm_layout_reads_the_same(self):
        self.assertEqual(sm.from_engine(engine([-0.5, -0.25], [11, 12, 13], first_none=True), PROMPT),
                         sm.from_engine(engine([-0.5, -0.25], [11, 12, 13]), PROMPT))

    def test_wrong_prompt_ids_raise(self):
        with self.assertRaises(ValueError):
            sm.from_engine(engine([-0.5, -0.25], [11, 12, 13]), [7, 3, 8])


class Metrics(unittest.TestCase):
    def test_compare(self):
        a = [([-1.0, -2.0], [1, 2, 3])]
        b = [([-1.25, -1.75], [1, 9, 3])]
        self.assertEqual(sm.compare(a, b), dict(same_top1=2, positions=3, mean_abs_dlp=0.25, max_abs_dlp=0.25,
                                                over_0p1=2))

    def test_fp32_error_takes_the_root_cause(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / 'x.log'
            log.write_text('info\ntriton.runtime.errors.OutOfResources: out of resource: shared memory\n'
                           'RuntimeError: Engine core initialization failed. See root cause above.\n')
            self.assertEqual(sm.fp32_error(log), 'OutOfResources: out of resource: shared memory')


class EndToEnd(unittest.TestCase):
    def test_build(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / 'ref').mkdir(); (d / 'runs').mkdir()
            exact, other = g5([-0.5, -0.25], [11, 12, 13]), g5([-0.75, -0.25], [11, 99, 13])
            (d / 'ref/prompts.json').write_text(json.dumps([PROMPT]))
            (d / 'ref/ref.json').write_text(json.dumps(dict(spec={}, seed=0, fp32_nobias=[exact], bf16_nobias=[exact],
                                                            fp32_full=[other])))
            (d / 'ref/variants.json').write_text(json.dumps(dict(fp16_autocast=[exact], bf16_pure=[exact],
                                                                 fp16_pure=[exact], fp32_no_router_bias=[other])))
            run = dict(sglang='0.5.23', torch='t', gpu='g', single=[engine([-0.75, -0.25], [11, 99, 13])],
                       batched=[engine([-0.75, -0.25], [11, 99, 13])])
            for name in sm.RUNS:
                (d / f'runs/{name}.json').write_text(json.dumps(run))
            for name in sm.FP32:
                (d / f'runs/{name}.log').write_text('RuntimeError: failed to dispatch data type Float\n')
            v = sm.build(d / 'ref', d / 'runs', {})
        r = v['runs']['c2_s002_bf16']
        self.assertEqual(r['single']['g5']['same_top1'], 2)                   # matches the bias-on reference less
        self.assertEqual(r['single']['g5_router_bias_off']['same_top1'], 3)   # and the bias-off one exactly
        self.assertEqual(r['single_vs_batched']['max_abs_dlp'], 0.0)
        self.assertEqual(v['fp32']['c1_s002_fp32']['error'], 'RuntimeError: failed to dispatch data type Float')
        self.assertEqual(v['prompts'], dict(count=1, lengths=[3], top1_positions=3, logprob_positions=2))


if __name__ == '__main__':
    unittest.main()
