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
