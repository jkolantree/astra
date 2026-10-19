"""Intentional algebraic fault control; never a physical result."""

import argparse

import wki_check_algebra as candidate

p = argparse.ArgumentParser()
p.add_argument("--group", choices=list(candidate.EXPECTED_RESIDUAL_COUNTS), required=True)
p.add_argument("--output", required=True)
args = p.parse_args()
original = candidate.build_checks


def altered():
    checks = original()
    checks[args.group]["residuals"][0] += 1
    return checks


candidate.build_checks = altered
raise SystemExit(candidate.main(["--output", args.output]))
