import yaml

def read_config(config_file:str)->dict:
    # Load config file
    f = open(config_file, "r")
    config = yaml.load(f, Loader=yaml.FullLoader)
    f.close()
    return config

def retrieve_attribute(config_file:str, *args):
    config = read_config(config_file)
    output = config.copy()
    for attribute in args:
        output = output[attribute]
    print(output)

# def get_xvfi_settings(config:dict)->dict:
#     for settings in config['XVFI_settings']:
#         if settings['dataset'] == config['DATA-GEN-PARAMS']['XVFI_pretrained']:
#             return settings
#     return NotImplementedError