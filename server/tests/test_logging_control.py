import requests
from app.services.logging_service import logging_service


def test_disable_client_logging():
    response = requests.post("http://127.0.0.1:8000/command", json={"prompt": "disable logging on the client"})
    assert response.status_code == 200
    assert response.json() == {"command": "client_command", "args": {"action": "disable_logging"}}


def test_enable_client_logging():
    response = requests.post("http://127.0.0.1:8000/command", json={"prompt": "enable logging on the client"})
    assert response.status_code == 200
    assert response.json() == {"command": "client_command", "args": {"action": "enable_logging"}}


def test_disable_single_server_service_logging():
    response = requests.post("http://127.0.0.1:8000/command", json={"prompt": "disable logging for the llm service"})
    assert response.status_code == 200
    assert logging_service.get_logging_level("llm") == "off"


def test_enable_single_server_service_logging():
    response = requests.post("http://127.0.0.1:8000/command", json={"prompt": "enable logging for the llm service"})
    assert response.status_code == 200
    assert logging_service.get_logging_level("llm") == "on"


def test_disable_all_server_services_logging():
    response = requests.post("http://127.0.0.1:8000/command", json={"prompt": "turn off all server logs"})
    assert response.status_code == 200
    services = logging_service.config.get("services", [])
    for service in services:
        assert logging_service.get_logging_level(service) == "off"


def test_enable_all_server_services_logging():
    response = requests.post("http://127.0.0.1:8000/command", json={"prompt": "turn on all server logs"})
    assert response.status_code == 200
    services = logging_service.config.get("services", [])
    for service in services:
        assert logging_service.get_logging_level(service) == "on"
