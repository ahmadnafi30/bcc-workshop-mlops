import importlib.util
import shutil
import sys
from pathlib import Path


# cek satu import tanpa menjalankan package-nya
def check_import(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


# print status sederhana yang gampang dibaca peserta
def print_check(name: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "MISSING"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")


# cek environment workshop dasar sebelum masuk ke data pipeline
def main() -> None:
    root = Path(__file__).resolve().parents[1]
    required_modules = [
        "pandas",
        "sklearn",
        "dvc",
        "mlflow",
        "fastapi",
        "prometheus_client",
    ]

    python_ok = sys.version_info[:2] == (3, 11)
    print_check(
        "Python 3.11",
        python_ok,
        sys.version.split()[0],
    )

    pyproject_ok = (root / "pyproject.toml").exists()
    print_check("repository root", pyproject_ok, str(root))

    imports_ok = True
    for module_name in required_modules:
        ok = check_import(module_name)
        imports_ok = imports_ok and ok
        print_check(f"import {module_name}", ok)

    docker_path = shutil.which("docker")
    print_check(
        "Docker CLI",
        docker_path is not None,
        docker_path or "optional until Docker section",
    )

    all_required_ok = python_ok and pyproject_ok and imports_ok

    print()
    if all_required_ok:
        print("core workshop environment looks ready.")
        raise SystemExit(0)

    print("core setup is incomplete. run uv sync and check the items above.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
