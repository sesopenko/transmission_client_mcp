"""Unit tests for Dockerfile correctness."""

from pathlib import Path


def test_dockerfile_does_not_set_uv_compile_bytecode() -> None:
    """Dockerfile must not set UV_COMPILE_BYTECODE=1.

    The fastmcp library uses beartype's claw import hook, which intercepts
    module loading at runtime. When UV_COMPILE_BYTECODE=1 is active during
    uv sync, uv pre-compiles .pyc files in a way that is incompatible with
    beartype's custom loader. At container startup, beartype's get_code()
    reads those pre-compiled .pyc files and raises
    ValueError: bad marshal data (unknown type code).
    """
    dockerfile = Path(__file__).parents[2] / "Dockerfile"
    content = dockerfile.read_text()
    assert "UV_COMPILE_BYTECODE=1" not in content, (
        "Dockerfile must not set UV_COMPILE_BYTECODE=1: pre-compiled bytecode "
        "is incompatible with beartype's claw import hook used by fastmcp, "
        "causing ValueError: bad marshal data at container startup."
    )
