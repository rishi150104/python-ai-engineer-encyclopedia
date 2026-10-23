import copy

DEFAULTS = {"model": "m1", "options": {"temperature": 0.2, "stop": ["END"]}}


def build_request_buggy(overrides):
    cfg = dict(DEFAULTS)                      # shallow: "options" is still shared
    cfg["options"]["temperature"] = overrides["temperature"]
    return cfg


def build_request_safe(overrides):
    cfg = copy.deepcopy(DEFAULTS)
    cfg["options"]["temperature"] = overrides["temperature"]
    return cfg


build_request_buggy({"temperature": 0.9})
print("after buggy call, module default:", DEFAULTS["options"]["temperature"])
DEFAULTS["options"]["temperature"] = 0.2
build_request_safe({"temperature": 0.9})
print("after safe call, module default:", DEFAULTS["options"]["temperature"])
