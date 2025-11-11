__version__ = "1.0.0.dev"

# version_info looks like (1, 2, 3, "dev") if __version__ is 1.2.3.dev
version_info = tuple(int(p) if p.isdigit() else p for p in __version__.split("."))
