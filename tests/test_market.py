import pytest
import sys
sys.path.insert(0, "/tmp/market-in-a-readme")

from market import parse_order, match_orders, compute_mid, compute_pnl


# --- parse_order ---

def test_parse_limit_buy():
    result = parse_order("BUY 10 STAR @ 100")
    assert result == {"side": "BUY", "ticker": "STAR", "qty": 10.0, "price": 100.0, "order_type": "LIMIT"}

def test_parse_limit_sell():
    result = parse_order("SELL 5 COMMIT @ 48.5")
    assert result == {"side": "SELL", "ticker": "COMMIT", "qty": 5.0, "price": 48.5, "order_type": "LIMIT"}

def test_parse_market_buy():
    result = parse_order("MARKET BUY 10 FORK")
    assert result == {"side": "BUY", "ticker": "FORK", "qty": 10.0, "price": None, "order_type": "MARKET"}

def test_parse_market_sell():
    result = parse_order("MARKET SELL 5 STAR")
    assert result == {"side": "SELL", "ticker": "STAR", "qty": 5.0, "price": None, "order_type": "MARKET"}

def test_parse_cancel():
    result = parse_order("CANCEL #7")
    assert result == {"order_type": "CANCEL", "target_issue": 7}

def test_parse_case_insensitive():
    result = parse_order("buy 10 star @ 100")
    assert result["side"] == "BUY"
    assert result["ticker"] == "STAR"

def test_parse_invalid_returns_none():
    assert parse_order("hello world") is None
    assert parse_order("BUY STAR") is None
    assert parse_order("BUY 10 INVALID @ 100") is None


# --- match_orders ---

def make_state():
    return {
        "STAR":   {"bids": [], "asks": [], "trades": [], "filled_issues": []},
        "COMMIT": {"bids": [], "asks": [], "trades": [], "filled_issues": []},
        "FORK":   {"bids": [], "asks": [], "trades": [], "filled_issues": []},
        "portfolios": {},
        "leaderboard": {}
    }

def test_limit_orders_match_when_crossing():
    state = make_state()
    state["STAR"]["bids"].append({"issue": 1, "qty": 10.0, "price": 100.0, "ts": 1000, "user": "alice"})
    state["STAR"]["asks"].append({"issue": 2, "qty": 10.0, "price": 100.0, "ts": 1001, "user": "bob"})
    trades = match_orders(state, "STAR")
    assert len(trades) == 1
    assert trades[0]["price"] == 100.0
    assert trades[0]["qty"] == 10.0
    assert len(state["STAR"]["bids"]) == 0
    assert len(state["STAR"]["asks"]) == 0

def test_limit_orders_no_match_when_not_crossing():
    state = make_state()
    state["STAR"]["bids"].append({"issue": 1, "qty": 10.0, "price": 99.0, "ts": 1000, "user": "alice"})
    state["STAR"]["asks"].append({"issue": 2, "qty": 10.0, "price": 101.0, "ts": 1001, "user": "bob"})
    trades = match_orders(state, "STAR")
    assert len(trades) == 0
    assert len(state["STAR"]["bids"]) == 1
    assert len(state["STAR"]["asks"]) == 1

def test_price_time_priority():
    state = make_state()
    state["STAR"]["bids"].append({"issue": 3, "qty": 10.0, "price": 100.0, "ts": 3000, "user": "carol"})
    state["STAR"]["asks"].append({"issue": 1, "qty": 5.0,  "price": 100.0, "ts": 1000, "user": "alice"})
    state["STAR"]["asks"].append({"issue": 2, "qty": 10.0, "price": 100.0, "ts": 2000, "user": "bob"})
    trades = match_orders(state, "STAR")
    assert trades[0]["ask_issue"] == 1  # alice fills first (earlier ts)


# --- compute_mid ---

def test_compute_mid_both_sides():
    state = make_state()
    state["STAR"]["bids"].append({"issue": 1, "qty": 10.0, "price": 99.0, "ts": 1000, "user": "alice"})
    state["STAR"]["asks"].append({"issue": 2, "qty": 10.0, "price": 101.0, "ts": 1001, "user": "bob"})
    assert compute_mid(state, "STAR") == 100.0

def test_compute_mid_fallback_to_last_trade():
    state = make_state()
    state["STAR"]["trades"].append({"price": 98.0, "qty": 5.0, "ts": "12:00 UTC", "bid_issue": 1, "ask_issue": 2})
    assert compute_mid(state, "STAR") == 98.0

def test_compute_mid_no_data_returns_none():
    state = make_state()
    assert compute_mid(state, "STAR") is None


# --- compute_pnl ---

def test_compute_pnl_profit():
    assert compute_pnl(10.0, 100.0, 110.0) == pytest.approx(100.0)

def test_compute_pnl_loss():
    assert compute_pnl(5.0, 50.0, 40.0) == pytest.approx(-50.0)

def test_compute_pnl_zero_qty():
    assert compute_pnl(0.0, 100.0, 110.0) == 0.0
