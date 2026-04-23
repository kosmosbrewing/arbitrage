def update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask):
    check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask})


def update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask):
    check_data[ticker].update({"close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})


def update_open_position_data(ticker, position_data, open_gimp):
    position_data[ticker]['open_install_count'] += 1
    position_data[ticker]['accum_open_install_count'] += 1
    position_data[ticker]['position_gimp_accum'] += open_gimp
    position_data[ticker]['position_gimp'] = round(
        position_data[ticker]['position_gimp_accum'] / position_data[ticker]['open_install_count'],
        2,
    )
    position_data[ticker]['position'] = 1
    position_data[ticker]['close_count'] = 0


def update_close_trade_data(ticker, trade_data):
    trade_data[ticker].update({
        "open_bid_price": 0,
        "open_ask_price": 0,
        "close_bid_price": 0,
        "close_ask_price": 0,
        "open_quantity": 0,
        "close_quantity": 0,
        "total_quantity": 0,
        "trade_profit": 0,
    })


def update_close_position_data(ticker, position_data):
    position_data[ticker].update({
        "position": 0,
        "close_count": 0,
        "position_gimp_accum": 0,
        "open_install_count": 0,
        "close_install_count": 0,
    })


def get_ticker_profit(trade_data, open_profit, close_profit, total_fee, ticker):
    total_profit = round(open_profit + close_profit - total_fee, 2)
    trade_data[ticker].update({"trade_profit": total_profit})
    trade_data[ticker]['profit_count'] += 1
    trade_data[ticker]['total_profit'] += trade_data[ticker]['trade_profit']
    return trade_data
