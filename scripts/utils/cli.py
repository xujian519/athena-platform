#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, env=None) -> None:
    r = subprocess.run(cmd, cwd=str(ROOT), env=env)
    return r.returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('list')

    subparsers.add_parser('build-legal-kg')

    subparsers.add_parser('migrate-neo4j')

    p_large_fast = subparsers.add_parser('large-kg-fast')
    p_large_fast.add_argument('--max-files', type=int, default=200)
    p_large_fast.add_argument('--no-ai', action='store_true')

    subparsers.add_parser('test-performance')

    subparsers.add_parser('verify-kg-neo4j')

    subparsers.add_parser('deploy-neo4j')

    subparsers.add_parser('deploy-qdrant')

    args = parser.parse_args()

    if args.command == 'list':
        logger.info('build-legal-kg')
        logger.info('migrate-neo4j')
        logger.info('large-kg-fast')
        logger.info('test-performance')
        logger.info('verify-kg-neo4j')
        logger.info('deploy-neo4j')
        logger.info('deploy-qdrant')
        sys.exit(0)

    if args.command == 'build-legal-kg':
        sys.exit(
            run(
                [
                    sys.executable,
                    str(ROOT / 'scripts' / 'kg' / 'build_production_legal_kg.py'),
                ]
            )
        )

    if args.command == 'migrate-neo4j':
        sys.exit(
            run(
                [
                    sys.executable,
                    str(ROOT / 'scripts' / 'db' / 'simple_migrate_to_neo4j.py'),
                ]
            )
        )

    if args.command == 'large-kg-fast':
        cmd = [
            sys.executable,
            str(ROOT / 'scripts' / 'kg' / 'ollama_large_scale_legal_kg.py'),
            '--fast',
            '--max-files',
            str(args.max_files),
        ]
        if args.no_ai:
            cmd.append('--no-ai')
        env = os.environ.copy()
        env['FAST_MODE'] = '1'
        env['OLLAMA_MIN_INTERVAL'] = '0.1'
        sys.exit(run(cmd, env=env))

    if args.command == 'test-performance':
        sys.exit(
            run(
                [
                    sys.executable,
                    str(
                        ROOT / 'scripts' / 'testing' / 'test_performance_comparison.py'
                    ),
                ]
            )
        )

    if args.command == 'verify-kg-neo4j':
        sys.exit(
            run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / 'scripts'
                        / 'db'
                        / 'verify_production_kg_quality_neo4j.py'
                    ),
                ]
            )
        )

    if args.command == 'deploy-neo4j':
        sys.exit(
            run(
                [
                    'bash',
                    str(ROOT / 'scripts' / 'ops' / 'deploy_neo4j.sh'),
                ]
            )
        )

    if args.command == 'deploy-qdrant':
        sys.exit(run(['bash', str(ROOT / 'scripts' / 'ops' / 'deploy_qdrant.sh')]))

    parser.print_help()


if __name__ == '__main__':
    main()
