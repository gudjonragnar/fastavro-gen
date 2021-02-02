import nox


@nox.session(python=["3.8", "3.9"])
def test(session):
    session.install("fastavro", "black", "pytest")
    session.install(".")

    # Show the pip version.
    session.run("pip", "--version")
    # Print the Python version and bytesize.
    session.run("python", "--version")

    session.run("pytest", "tests")


@nox.session
def typecheck(session):
    session.install("mypy")

    session.run("mypy", "--ignore-missing-imports", "fastavro_gen")