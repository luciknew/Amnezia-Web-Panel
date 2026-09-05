"""Shared Docker helpers for protocol managers."""

_COMPOSE_INSTALL_SCRIPT = r"""
if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y || true
    apt-get install -y ca-certificates curl gnupg || exit 1
    install -m 0755 -d /etc/apt/keyrings
    . /etc/os-release
    DOCKER_DISTRO="$ID"
    case "$ID" in
        linuxmint|pop|elementary|zorin) DOCKER_DISTRO="ubuntu" ;;
        kali|parrot) DOCKER_DISTRO="debian" ;;
    esac
    if [ ! -s /etc/apt/keyrings/docker.asc ]; then
        curl -fsSL "https://download.docker.com/linux/${DOCKER_DISTRO}/gpg" -o /etc/apt/keyrings/docker.asc || exit 1
        chmod a+r /etc/apt/keyrings/docker.asc
    fi
    CODENAME="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${DOCKER_DISTRO} ${CODENAME} stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -y || exit 1
    apt-get install -y docker-buildx-plugin docker-compose-plugin || exit 1
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y dnf-plugins-core || exit 1
    . /etc/os-release
    dnf config-manager --add-repo "https://download.docker.com/linux/${ID}/docker-ce.repo" \
        || dnf config-manager --add-repo "https://download.docker.com/linux/centos/docker-ce.repo" \
        || exit 1
    dnf makecache || true
    dnf install -y docker-buildx-plugin docker-compose-plugin || exit 1
elif command -v yum >/dev/null 2>&1; then
    yum install -y yum-utils || exit 1
    . /etc/os-release
    yum-config-manager --add-repo "https://download.docker.com/linux/${ID}/docker-ce.repo" \
        || yum-config-manager --add-repo "https://download.docker.com/linux/centos/docker-ce.repo" \
        || exit 1
    yum makecache || true
    yum install -y docker-buildx-plugin docker-compose-plugin || exit 1
else
    echo "Unsupported package manager" >&2
    exit 1
fi
docker compose version
"""


def ensure_docker_compose(ssh):
    """Make sure `docker compose` is available, installing the plugin if needed.

    Why: `docker-buildx-plugin` and `docker-compose-plugin` only ship in Docker's
    official apt/yum repo. When Docker was installed from distro packages
    (e.g. `docker.io` on Ubuntu), that repo is not configured and a plain
    `apt-get install docker-compose-plugin` fails. So we add the repo,
    refresh package lists, then install.
    """
    out, _, code = ssh.run_command("docker compose version 2>/dev/null")
    if code == 0 and out.strip():
        return

    out, err, code = ssh.run_sudo_script(_COMPOSE_INSTALL_SCRIPT, timeout=300)
    if code != 0:
        raise RuntimeError(f"Failed to install docker compose plugin: {err or out}")


# Markers of "the v2 plugin isn't here", as opposed to "the command ran and
# failed". Only the former justifies retrying with v1: retrying a genuine
# failure replaces its message with `docker-compose: not found` and hides the
# real cause (that cost us a wrong diagnosis on a permission error once).
_V2_MISSING = (
    "is not a docker command",
    "unknown docker command",
    "docker: not found",
    "docker: command not found",
)


def _v2_plugin_missing(output):
    lowered = (output or '').lower()
    return any(marker in lowered for marker in _V2_MISSING)


def compose_exec(ssh, remote_dir, args, timeout=900):
    """Run an arbitrary `docker compose` subcommand, falling back to v1 syntax."""
    out, err, code = ssh.run_sudo_command(
        f"sh -c 'cd {remote_dir} && docker compose {args}'", timeout=timeout)
    if code != 0 and _v2_plugin_missing(f"{out}\n{err}"):
        return ssh.run_sudo_command(
            f"sh -c 'cd {remote_dir} && docker-compose {args}'", timeout=timeout)
    return out, err, code


def compose_up(ssh, remote_dir, timeout=900, build=True):
    """Run `docker compose up -d` in `remote_dir`, falling back to v1 syntax."""
    flags = "-d --build" if build else "-d"
    return compose_exec(ssh, remote_dir, f"up {flags}", timeout=timeout)
