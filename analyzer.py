import argparse
import csv
import os


class Col(object):
    asin = 0
    upc = 1
    ean = 2
    title = 3
    purchase_cost = 4
    sales_rank = 5
    buy_box_or_lowest_price = 6
    total_cost = 7
    profit = 8
    roi = 9
    link_amazon = 10
    sold_by_amazon = 11
    product_group = 12
    weight = 13
    number_of_items = 14
    ratings = 15
    offers_at_lowest_price = 16
    fba_offers_at_lowest_price = 17
    mfn_offers_at_lowest_price = 18
    link_keepa = 19
    link_camel_camel_camel = 20
    referral_fee = 21
    variable_closing_fee = 22
    per_item_fee = 23
    fba_weight_handling = 24
    fba_pick_and_pack = 25
    fba_order_handling = 26
    total_fba_fees = 27
    total_fees = 28


def roi_rule(line):
    try:
        total_cost = float(line[Col.total_cost])
        profit = float(line[Col.profit])
    except ValueError:
        return False

    roi = int((profit / total_cost) * 100)
    if roi < 10 or roi > 150:
        return False

    line[Col.roi] = roi
    return True


def upc_rule(line):
    upc = line[Col.upc]
    if not upc:
        return False
    upc = upc.replace(' ', '')
    return bool(upc)


def asin_rule(line):
    asin = line[Col.asin]
    if not asin:
        return False
    asin = asin.replace(' ', '')
    return bool(asin)


def profit_rule(line):
    try:
        profit = float(line[Col.profit])
    except ValueError:
        return False
    
    return profit >= 4


def sold_by_amazon_rule(line):
    return not bool(line[Col.sold_by_amazon])


def sales_rank_rule(line):
    return bool(line[Col.sales_rank])
        

RULES = [
    asin_rule,
    upc_rule,
    sales_rank_rule,
    sold_by_amazon_rule,
    profit_rule,
    roi_rule
]


def analyze_line(line):
    for pass_rule in RULES:
        if not pass_rule(line):
            return False

    return True


def analyze(file):
    dirname = os.path.dirname(csv_file)
    filename = os.path.basename(csv_file).replace(".csv", "")
    inventory_file = "{}/{}.reviewed.csv".format(dirname, filename)

    inventory = []
    with open(csv_file, "r") as read_file:
        reader = csv.reader(read_file, delimiter=',')
        for line_no, line in enumerate(list(reader)):
            if line_no == 0:
                inventory.append(line)
            elif analyze_line(line):
                inventory.append(line)

    with open(inventory_file, "w") as write_file:
        writer = csv.writer(write_file)
        writer.writerows(inventory)


parser = argparse.ArgumentParser(description='Eliminate a')
parser.add_argument('messy_csv')


if __name__ == '__main__':
    args = vars(parser.parse_args())
    csv_file = args["messy_csv"]
    
    analyze(csv_file)