from dataclasses import asdict as as_dict
import fastavro_gen.type_gen as gen
import fastavro_gen.from_dict as from_dict

generate = gen.read_schemas_and_generate_classes
asdict = as_dict
fromdict = from_dict.fromdict
