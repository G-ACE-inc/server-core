#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(text, needle, label):
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main():
    dockerfile = (ROOT / "Dockerfile.project-control").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.project-control.yml").read_text(encoding="utf-8")
    ignore = (ROOT / "Dockerfile.project-control.dockerignore").read_text(encoding="utf-8")

    require(dockerfile, "RUN apk add --no-cache ca-certificates github-cli", "dockerfile")
    require(dockerfile, "USER 65532:65532", "dockerfile")
    require(dockerfile, "GH_CONFIG_DIR=/run/gh", "dockerfile")
    require(dockerfile, 'ENTRYPOINT ["python3", "/app/scripts/github_project_internal_receiver.py"]', "dockerfile")

    for name in (
        "GACE_SERVER_UID",
        "GACE_SERVER_GID",
        "GACE_PROJECT_CONTROL_GH_CONFIG_DIR",
        "GACE_PROJECT_CONTROL_DELIVERY_SECRET_FILE",
        "GACE_INTERNAL_NETWORK_NAME",
    ):
        require(compose, name, "compose")
    require(compose, "target: /run/gh", "compose")
    require(compose, "target: /run/secrets/project-control-delivery", "compose")
    require(compose, "read_only: true", "compose")
    require(compose, "no-new-privileges:true", "compose")
    require(compose, "cap_drop:", "compose")
    require(compose, "- ALL", "compose")
    require(compose, "gace-internal:", "compose")
    require(compose, "external: true", "compose")
    require(compose, "expose:", "compose")
    if "\n    ports:" in compose:
        raise AssertionError("compose: receiver must not publish a host port")
    if "network_mode: host" in compose:
        raise AssertionError("compose: host networking is forbidden")

    for expected in (
        "!operations/github-project-control.json",
        "!scripts/github_project_control.py",
        "!scripts/github_project_internal_receiver.py",
    ):
        require(ignore, expected, "dockerignore")

    print("PROJECT_CONTROL_RUNTIME_CONFIG=PASS")


if __name__ == "__main__":
    main()
