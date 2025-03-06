__version__ = (0, 8, 1)
USER_AGENT = (
    "Wikipedia-API/"
    + ".".join(str(s) for s in __version__)
    + "; https://github.com/martin-majlis/Wikipedia-API/"
)

print(USER_AGENT)