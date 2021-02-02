from fastavro_gen import asdict, fromdict


def roundtrip(record):
    as_dict = asdict(record)
    return fromdict(type(record), as_dict)
