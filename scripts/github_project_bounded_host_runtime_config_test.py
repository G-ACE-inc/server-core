#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(text, needle, label):
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main():
    dockerfile = (ROOT / "Dockerfile.bounded-host").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.project-control.yml").read_text(encoding="utf-8")
    ignore = (ROOT / "Dockerfile.bounded-host.dockerignore").read_text(encoding="utf-8")
    overlay = (ROOT / "docker-compose.source-reflect.yml").read_text(encoding="utf-8")

    require(dockerfile, "servercore_bounded_host_receiver.py", "dockerfile")
    require(dockerfile, "USER 65532:65532", "dockerfile")
    require(dockerfile, 'ENTRYPOINT ["python3", "/app/scripts/servercore_bounded_host_receiver.py"]', "dockerfile")
    require(compose, "server-core-bounded-host:", "compose")
    require(compose, "GACE_BOUNDED_HOST_CANONICAL_ROOT", "compose")
    require(compose, "GACE_BOUNDED_HOST_HMAC_KEY_FILE", "compose")
    require(compose, "target: /home/admin1/server-core", "compose")
    require(compose, "8789", "compose")
    if "server-core-bounded-host" in compose and "\n    ports:" in compose.split("server-core-bounded-host:")[1].split("networks:")[0]:
        raise AssertionError("bounded-host service must not publish host ports")
    require(ignore, "!operations/github-project-bounded-host.json", "dockerignore")
    require(ignore, "!scripts/servercore_bounded_host.py", "dockerignore")
    require(overlay, "GACE_HOST_SOURCE_REFLECT_SOCKET_DIR", "socket_overlay")
    require(overlay, "target: /run/gace", "socket_overlay")
    require(overlay, "read_only: true", "socket_overlay")
    if "servercore-source-reflect.sock" in overlay:
        raise AssertionError("socket file-level mount is forbidden (stale inode on restart)")
    print("BOUNDED_HOST_RUNTIME_CONFIG=PASS")


if __name__ == "__main__":
    main()
