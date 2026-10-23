"""Summarize native TorchBench logs locally; never runs a benchmark.

Example: python summarize_timings.py --run baseline=/path/run.log --output-dir out
The user supplies labels; toggles and environment must be checked separately.
"""
import argparse
import csv
import json
from pathlib import Path
import re
import statistics


def parse_run(label, path):
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    result = {'label': label, 'log': str(path.resolve()), 'modes': {}}
    samples = []
    bounds = None
    for mode in ('eager', 'compile'):
        summaries = list(re.finditer(
            rf'\[{mode}\] summary \[(\d+)-(\d+)\].*?avg step time: ([\d.]+) ms', text))
        if len(summaries) != 1:
            raise ValueError(f'{label}/{mode}: expected one native summary, got {len(summaries)}')
        start, end = map(int, summaries[0].group(1, 2))
        if end < start or (bounds is not None and bounds != (start, end)):
            raise ValueError(f'{label}: inconsistent aggregation intervals')
        bounds = (start, end)
        timings = {}
        for match in re.finditer(rf'\[{mode}\] step: (\d+) step_time: ([\d.eE+-]+) ms', text):
            step, latency = int(match[1]), float(match[2])
            if step in timings or not (0 < latency < float('inf')):
                raise ValueError(f'{label}/{mode}: duplicate step or invalid latency at {step}')
            timings[step] = latency
            samples.append({'run': label, 'mode': mode, 'step': step, 'latency_ms': latency})
        missing = sorted(set(range(start, end + 1)) - timings.keys())
        if missing:
            raise ValueError(f'{label}/{mode}: missing selected steps {missing}')
        values = [timings[step] for step in range(start, end + 1)]
        mean = statistics.mean(values)
        if abs(mean - float(summaries[0][3])) > 0.0051:
            raise ValueError(f'{label}/{mode}: raw mean does not match printed summary')
        result['modes'][mode] = {'mean_ms': mean, 'median_ms': statistics.median(values),
                                 'min_ms': min(values), 'max_ms': max(values),
                                 'all_steps': len(timings), 'selected_steps': len(values)}
    eager, compile = (result['modes'][m]['mean_ms'] for m in ('eager', 'compile'))
    result.update({'start_step': bounds[0], 'end_step': bounds[1],
                   'speedup': eager / compile,
                   'latency_reduction_percent': 100 * (1 - compile / eager),
                   'pass_accuracy_seen': bool(re.search(r'^pass_accuracy\s*$', text, re.M))})
    return result, samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='append', required=True, metavar='LABEL=LOG')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    results, samples, labels = [], [], set()
    for spec in args.run:
        label, separator, log = spec.partition('=')
        if not separator or not label or not log or label in labels:
            parser.error('--run must contain a unique nonempty LABEL=LOG')
        labels.add(label)
        try:
            result, rows = parse_run(label, Path(log))
        except (OSError, ValueError) as error:
            parser.error(str(error))
        results.append(result)
        samples.extend(rows)
    if len({(r['start_step'], r['end_step']) for r in results}) > 1:
        parser.error('Runs use different aggregation intervals; compare them separately')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    with (args.output_dir / 'timing_samples.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['run', 'mode', 'step', 'latency_ms'])
        writer.writeheader()
        writer.writerows(samples)
    lines = ['# 原生 TorchBench E2E 耗时对比', '',
             '| 配置标签 | eager 均值（ms） | compile 均值（ms） | 加速比 | 耗时降低 | 统计区间 | 精度通过日志 |',
             '| --- | ---: | ---: | ---: | ---: | --- | --- |']
    for run in results:
        label = run['label'].replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {label} | {run['modes']['eager']['mean_ms']:.3f} | "
                     f"{run['modes']['compile']['mean_ms']:.3f} | {run['speedup']:.3f}x | "
                     f"{run['latency_reduction_percent']:.2f}% | {run['start_step']}～{run['end_step']} | "
                     f"{'是' if run['pass_accuracy_seen'] else '未发现'} |")
    lines += ['', '统计使用原始单步耗时，未剔除慢步。配置标签由调用者提供；需另行核对版本、模型、debug/profiler 开关及计时范围。',
              '只有 debug 和 profiler 均关闭的同配置测量可作为对应的 E2E 基线；此脚本不自动判定环境有效性。', '']
    (args.output_dir / 'comparison.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps([{'label': r['label'], 'speedup': r['speedup']} for r in results], ensure_ascii=False))


if __name__ == '__main__':
    main()
