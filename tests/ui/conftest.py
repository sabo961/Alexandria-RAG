"""
Playwright fixtures for Alexandria UI tests.

Provides fixtures for:
- Starting/stopping Streamlit server
- Browser and page configuration
- Base URL management
"""

import pytest
import subprocess
import time
import socket
import sys
import os


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for server to become available."""
    import urllib.request
    import urllib.error

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=5)
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def streamlit_server():
    """
    Start Streamlit server for test session.

    Yields the base URL for the running server.
    Automatically terminates the server after tests complete.
    """
    port = 8501
    base_url = f"http://localhost:{port}"

    # Check if server is already running (e.g., manual development server)
    if is_port_in_use(port):
        print(f"Streamlit server already running on port {port}")
        yield base_url
        return

    # Find the app file
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    app_path = os.path.join(project_root, 'alexandria_app.py')

    if not os.path.exists(app_path):
        pytest.skip(f"App file not found: {app_path}")

    # Start Streamlit server
    process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.headless", "true",
            "--server.port", str(port),
            "--browser.gatherUsageStats", "false",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=project_root,
    )

    # Wait for server to start
    if not wait_for_server(base_url, timeout=30):
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        pytest.fail(
            f"Streamlit server failed to start within 30 seconds.\n"
            f"stdout: {stdout.decode()}\n"
            f"stderr: {stderr.decode()}"
        )

    print(f"Streamlit server started on {base_url}")
    yield base_url

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    print("Streamlit server stopped")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="function")
def app_page(page, streamlit_server):
    """
    Navigate to the Alexandria app and wait for it to load.

    Returns a page object already navigated to the app.
    """
    page.goto(streamlit_server)
    # Wait for Streamlit to fully render (main container appears)
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=15000)
    return page
