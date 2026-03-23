from agents.fraud_investigator import process_alert


def test_process_alert_high_risk_amount():
    """High-value amount alone should produce a risk score of 0.45."""
    tx_data = {"id": "1", "amount": 15000, "source": "US-acct-A", "target": "US-acct-B"}
    result = process_alert(tx_data)
    assert result["risk_score"] == 0.45
    assert "high_amount" in result["summary"]


def test_process_alert_high_risk_amount_and_cross_region():
    """High-value cross-region transaction should score 0.55."""
    tx_data = {"id": "2", "amount": 20000, "source": "US-acct-A", "target": "EU-acct-B"}
    result = process_alert(tx_data)
    assert result["risk_score"] == 0.55
    assert "cross_region" in result["summary"]


def test_process_alert_low_risk():
    """Low-value same-region transaction with no velocity should score 0.0."""
    tx_data = {"id": "3", "amount": 500, "source": "US-acct-A", "target": "US-acct-C"}
    result = process_alert(tx_data)
    assert result["risk_score"] == 0.0
    assert "LOW" in result["summary"]


def test_process_alert_velocity_breach():
    """Velocity breach should add 0.10 to the score."""
    tx_data = {
        "id": "4",
        "amount": 500,
        "source": "US-acct-A",
        "target": "US-acct-B",
        "is_velocity_breach": True,
    }
    result = process_alert(tx_data)
    assert result["risk_score"] == 0.10
    assert "velocity_breach" in result["risk_factors"]


def test_process_alert_critical_risk():
    """High-value + cross-region + velocity breach = 0.65 (MEDIUM/HIGH)."""
    tx_data = {
        "id": "5",
        "amount": 50000,
        "source": "US-acct-A",
        "target": "EU-acct-B",
        "is_velocity_breach": True,
    }
    result = process_alert(tx_data)
    assert result["risk_score"] == 0.65
    assert "HIGH" in result["summary"]
