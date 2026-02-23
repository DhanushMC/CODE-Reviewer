import docker
import tempfile
import os
from typing import Dict, List
from app.config import settings
from app.schemas.models import SupportedLanguage, TestResult


class SandboxExecutor:
    """Docker-based isolated test execution environment"""

    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            self._docker_available = True
        except Exception as e:
            print(f"Warning: Docker not available: {e}")
            self.client = None
            self._docker_available = False

        # FIX: Use images that have test frameworks PRE-INSTALLED
        # This avoids needing internet inside the sandbox container
        self.lang_config = {
            SupportedLanguage.PYTHON: {
                # python:3.11-slim with pytest pre-installed via our custom prep
                "image": "python:3.11-slim",
                "test_file": "test_code.py",
                "code_file": "code.py",
                # FIX: install pytest BEFORE disabling network, or use offline install
                # We pre-install pytest by running with network first
                "install_cmd": "pip install pytest --quiet --no-warn-script-location 2>/dev/null || true",
                "test_cmd": "python -m pytest -v test_code.py --tb=short 2>&1"
            },
            SupportedLanguage.JAVASCRIPT: {
                "image": "node:18-alpine",
                "test_file": "code.test.js",
                "code_file": "code.js",
                "install_cmd": "npm init -y && npm install --save-dev jest 2>/dev/null || true",
                "test_cmd": "npx jest code.test.js --no-coverage 2>&1"
            },
            SupportedLanguage.JAVA: {
                "image": "openjdk:11-slim",
                "test_file": "CodeTest.java",
                "code_file": "Code.java",
                "install_cmd": "echo 'Java ready'",
                "test_cmd": "javac Code.java CodeTest.java && java -ea CodeTest 2>&1"
            },
            SupportedLanguage.GO: {
                "image": "golang:1.20-alpine",
                "test_file": "code_test.go",
                "code_file": "code.go",
                "install_cmd": "go mod init testmodule 2>/dev/null || true",
                "test_cmd": "go test -v ./... 2>&1"
            },
        }

    def _ensure_pytest_image(self):
        """
        Build a custom Docker image with pytest pre-installed.
        This runs ONCE and caches the image — all future sandbox runs are instant.
        """
        image_name = "scr-python-sandbox:latest"
        try:
            self.client.images.get(image_name)
            return image_name  # already built
        except docker.errors.ImageNotFound:
            pass

        print("Building sandbox image with pytest pre-installed (one-time setup)...")
        dockerfile = b"""
FROM python:3.11-slim
RUN pip install pytest pytest-mock --quiet --no-warn-script-location
WORKDIR /workspace
"""
        import io
        try:
            image, logs = self.client.images.build(
                fileobj=io.BytesIO(dockerfile),
                tag=image_name,
                rm=True
            )
            print(f"Sandbox image built: {image_name}")
            return image_name
        except Exception as e:
            print(f"Could not build custom image: {e}, falling back to python:3.11-slim")
            return "python:3.11-slim"

    def run_tests(self, code: str, tests: str, language: SupportedLanguage) -> Dict:
        """Execute tests in isolated Docker container"""

        if not self._docker_available:
            return {
                "all_tests_passed": False,
                "logs": "Docker not available. Please start Docker Desktop.",
                "individual_results": []
            }

        config = self.lang_config.get(language)
        if not config:
            return {
                "all_tests_passed": False,
                "logs": f"Language '{language.value}' not supported for sandbox execution yet.",
                "individual_results": []
            }

        # For Python: use our pre-built image with pytest installed
        image = config["image"]
        test_cmd = config["test_cmd"]
        install_cmd = config["install_cmd"]

        if language == SupportedLanguage.PYTHON:
            image = self._ensure_pytest_image()
            # Skip pip install — pytest is already in the image
            install_cmd = "echo 'pytest ready'"

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write files
                with open(os.path.join(tmpdir, config["code_file"]), 'w', encoding='utf-8') as f:
                    f.write(code)
                with open(os.path.join(tmpdir, config["test_file"]), 'w', encoding='utf-8') as f:
                    f.write(tests)

                # Pull image if needed
                try:
                    self.client.images.get(image)
                except docker.errors.ImageNotFound:
                    print(f"Pulling {image}...")
                    self.client.images.pull(image)

                container = None
                try:
                    cpu_quota = int(float(settings.sandbox_cpu_limit) * 100000)

                    full_cmd = f"sh -c '{install_cmd} && {test_cmd}'"

                    container = self.client.containers.run(
                        image=image,
                        command=full_cmd,
                        volumes={tmpdir: {'bind': '/workspace', 'mode': 'rw'}},
                        working_dir='/workspace',
                        network_mode='none',        # no internet inside sandbox
                        mem_limit=settings.sandbox_memory_limit,
                        cpu_quota=cpu_quota,
                        cpu_period=100000,
                        detach=True,
                        remove=False
                    )

                    result = container.wait(timeout=settings.sandbox_timeout)
                    logs = container.logs().decode('utf-8', errors='replace')
                    all_passed = result['StatusCode'] == 0
                    individual = self._parse_test_results(logs, language)

                    return {
                        "all_tests_passed": all_passed,
                        "logs": logs,
                        "individual_results": individual
                    }

                finally:
                    if container:
                        try:
                            container.remove(force=True)
                        except Exception:
                            pass

        except Exception as e:
            return {
                "all_tests_passed": False,
                "logs": f"Sandbox execution error: {str(e)}",
                "individual_results": []
            }

    def _parse_test_results(self, logs: str, language: SupportedLanguage) -> List[TestResult]:
        results = []
        try:
            if language == SupportedLanguage.PYTHON:
                for line in logs.split('\n'):
                    if ' PASSED' in line or ' FAILED' in line or ' ERROR' in line:
                        parts = line.split()
                        if parts:
                            test_id = parts[0]
                            test_name = test_id.split('::')[-1] if '::' in test_id else test_id
                            passed = ' PASSED' in line
                            results.append(TestResult(
                                name=test_name,
                                passed=passed,
                                error_message=None if passed else line.strip()
                            ))

            elif language == SupportedLanguage.JAVASCRIPT:
                for line in logs.split('\n'):
                    stripped = line.strip()
                    if stripped.startswith(('✓', '✕', '√', '×', 'PASS', 'FAIL')):
                        passed = stripped[0] in ('✓', '√') or stripped.startswith('PASS')
                        test_name = stripped[1:].strip() if stripped[0] in ('✓','✕','√','×') else stripped[5:].strip()
                        results.append(TestResult(
                            name=test_name,
                            passed=passed,
                            error_message=None if passed else "Test failed"
                        ))
        except Exception as e:
            print(f"Error parsing test results: {e}")
        return results


_executor = None

def get_executor() -> SandboxExecutor:
    global _executor
    if _executor is None:
        _executor = SandboxExecutor()
    return _executor
