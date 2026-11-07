#!/usr/bin/env python3
"""Independently solve the six examples and check the displayed TeX results.

All arithmetic uses exact rational numbers; no scientific package is required.
"""
from fractions import Fraction as F
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def transpose(a):
    return list(map(list, zip(*a)))


def product(a, b):
    return [[sum(x * y for x, y in zip(row, column)) for column in zip(*b)] for row in a]


def inverse(a):
    n = len(a)
    rows = [[F(x) for x in row] + [F(i == j) for j in range(n)] for i, row in enumerate(a)]
    for i in range(n):
        pivot = next(k for k in range(i, n) if rows[k][i])
        rows[i], rows[pivot] = rows[pivot], rows[i]
        scale = rows[i][i]
        rows[i] = [x / scale for x in rows[i]]
        for k in range(n):
            if k != i:
                scale = rows[k][i]
                rows[k] = [a - scale * b for a, b in zip(rows[k], rows[i])]
    return [row[n:] for row in rows]


def add(a, b):
    return [[x + y for x, y in zip(row, other)] for row, other in zip(a, b)]


def matrix(text):
    return [[F(value.strip()) for value in row.split('&')] for row in text.split('\\\\')]


def displayed(text, symbol):
    matches = re.findall(re.escape(symbol + '=\\begin{bmatrix}') + r'(.*?)' + re.escape('\\end{bmatrix}'), text, re.S)
    for value in matches:
        try:
            return matrix(value)
        except ValueError:
            continue  # A symbolic general equation may precede the numeric example.
    raise AssertionError(f'Missing displayed numeric result: {symbol}')


def gls(a, y, covariance, prior=None):
    w = inverse(covariance)
    n = product(product(transpose(a), w), a)
    b = product(product(transpose(a), w), y)
    if prior:
        mean, prior_cov = prior
        precision = inverse(prior_cov)
        n = add(n, precision)
        b = add(b, product(precision, mean))
    posterior_cov = inverse(n)
    return product(posterior_cov, b), posterior_cov


def check_scalar(file, covariance):
    beta, cov = gls([[1], [1]], [[10], [12]], covariance)
    text = (ROOT / 'content/lessons' / file).read_text()
    # The decimal values printed in the scalar examples are exact.
    beta_match = re.search(r'\\boxed\{\\hat\\beta=(?:\\frac\{\d+\}\{\d+\}=)?([0-9.]+)', text)
    cov_match = re.search(r'\\boxed\{C_\{\\hat\\beta\}=(?:\\frac\{\d+\}\{\d+\}=)?([0-9.]+)', text)
    assert beta_match and cov_match, file
    assert beta == [[F(beta_match[1])]], file
    assert cov == [[F(cov_match[1])]], file


def main():
    check_scalar('case-1-grouped-observations.html', [[1, F(1, 2)], [F(1, 2), 4]])
    check_scalar('case-2-independent-groups.html', [[1, 0], [0, 4]])
    a = [[1, 0, 0], [1, 0, 1], [0, 1, 0], [0, 1, 1]]
    y = [[10], [12], [20], [23]]
    identity = [[int(i == j) for j in range(4)] for i in range(4)]
    correlated = [[1, 0, F(1, 2), 0], [0, 1, 0, F(1, 2)], [F(1, 2), 0, 4, 0], [0, F(1, 2), 0, 4]]
    independent = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 4, 0], [0, 0, 0, 4]]
    prior = ([[10], [20], [2]], [[4, 0, 0], [0, 4, 0], [0, 0, 1]])
    cases = [
        ('04-lesson.html', identity, None, 'C_{\\hat\\beta}'),
        ('case-4-heterogeneous-covariance.html', correlated, None, 'C_{\\hat\\beta}'),
        ('case-5-independent-local-global.html', independent, None, 'C_{\\hat\\beta}'),
        ('05-lesson.html', independent, prior, 'C_{\\beta\\mid y}'),
    ]
    for file, covariance, prior_info, covariance_symbol in cases:
        beta, cov = gls(a, y, covariance, prior_info)
        text = (ROOT / 'content/lessons' / file).read_text()
        assert beta == displayed(text, '\\hat\\beta'), f'{file}: estimate'
        assert cov == displayed(text, covariance_symbol), f'{file}: covariance'
    print('PASS: six displayed parameter estimates and all six covariance results match exact GLS/prior calculations.')


if __name__ == '__main__':
    main()
