import re
import sys


denominations = {100: 0, 50: 0, 20: 0, 10: 0, 5: 0, 2: 0, 1: 0}


def record_amount(amount):
    '''inspiration from: https://stackoverflow.com/a/17867594'''

    for denom in denominations.keys():
        count = int(amount / denom)
        denominations[denom] += count
        amount -= denom * count

    if amount != 0:
        raise RuntimeError('amount not zero: {}'.format(amount))


def main():

    amount_re = re.compile(r'\$?\s*([0-9]+)(\.00)?')

    for line in sys.stdin.readlines():

        data = line.strip()

        if len(data) == 0:
            continue

        re_match = amount_re.match(data)

        if re_match is None:
            print('bogus data: {}'.format(data))

        record_amount(int(re_match.group(1)))

    for denom, count in denominations.items():

        if count != 0:
            print(
                '{:>4}: {:2} = {:>4}'.format(
                    '$' + str(denom), count, '$' + str(denom * count)
                )
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
