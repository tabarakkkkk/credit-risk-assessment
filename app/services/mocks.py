"""Explicit unavailable-service states; no fabricated model answers."""


def unavailable(service_name):
    return {"status": "unavailable", "service": service_name, "message": f"{service_name} is not configured in this project."}
