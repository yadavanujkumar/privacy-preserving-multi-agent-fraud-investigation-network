from agents.fraud_investigator import process_alert

def test_process_alert_high_risk():
    tx_data = {"id": "1", "amount": 15000, "source": "A", "target": "B"}
    result = process_alert(tx_data)
    assert result["risk_score"] == 0.85
    assert "High risk" in result["summary"]

def test_process_alert_low_risk():
    tx_data = {"id": "2", "amount": 500, "source": "A", "target": "B"}
    result = process_alert(tx_data)
    assert result["risk_score"] == 0.1
    assert "normal" in result["summary"]