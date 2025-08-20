#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path


def build_commands(cfg: dict) -> list:
    lines = [
        f"set frequency tx {cfg['frequency']['tx']}",
        f"set frequency rx {cfg['frequency']['rx']}",
        f"set samplerate tx {cfg['samplerate']['tx']}",
        f"set samplerate rx {cfg['samplerate']['rx']}",
        f"set bandwidth tx {cfg['bandwidth']['tx']}",
        f"set bandwidth rx {cfg['bandwidth']['rx']}",
        f"set txvga1 {cfg['txvga1']}",
        f"set txvga2 {cfg['txvga2']}",
        f"set gain rx {cfg['rx_gain']}",
    ]
    tx_cfg = cfg.get('tx', {})
    tx_config = tx_cfg.get('config')
    if tx_config:
        lines.append(
            "tx config file={file} format={format} repeat={repeat} delay={delay}".format(**tx_config)
        )
    if tx_cfg.get('start'):
        lines.append('tx start')
    rx_cfg = cfg.get('rx', {})
    rx_config = rx_cfg.get('config')
    if rx_config:
        parts = [
            f"file={rx_config['file']}",
            f"format={rx_config['format']}",
        ]
        if 'n' in rx_config:
            parts.append(f"n={rx_config['n']}")
        lines.append('rx config ' + ' '.join(parts))
    if rx_cfg.get('start'):
        lines.append('rx start')
    return lines


def main():
    base_dir = Path(__file__).resolve().parent
    cfg_path = base_dir / 'blade_rf_a4_config.json'
    out_dir = base_dir / 'Outputs'
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / 'blade_rf_a4.txt'

    with cfg_path.open() as f:
        cfg = json.load(f)

    lines = build_commands(cfg)
    with out_path.open('w') as f:
        f.write('\n'.join(lines) + '\n')

    try:
        subprocess.run(['bladeRF-cli', '-s', str(out_path)], check=True)
    except FileNotFoundError:
        print('bladeRF-cli not found. Please install the BladeRF command line tools.')
    except subprocess.CalledProcessError as e:
        print('bladeRF-cli returned an error:', e)


if __name__ == '__main__':
    main()
