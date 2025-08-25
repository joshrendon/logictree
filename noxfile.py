
import nox


@nox.session
def smoke(session):
    session.install("pytest", "pytest-cov")
    session.run("pytest", "-m", "smoke or unit or cli", "--maxfail=1")

@nox.session
def nightly(session):
    session.install("pytest", "pytest-cov")
    session.run("pytest", "-m", "not (slow or flaky or dev)")

@nox.session
def weekly(session):
    session.install("pytest", "pytest-cov")
    session.run("pytest", "-m", "slow or mutation or props")

@nox.session
def release(session):
    session.install("pytest", "pytest-cov")
    session.run("pytest", "-m", "not flaky", "--cov=logictree", "--cov-fail-under=90")
