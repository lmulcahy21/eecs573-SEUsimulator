from f4pga_sdf_timing.sdf_timing.sdfparse import parse as parse_sdf

def get_delays(sdf_filepath: str):
    with open(sdf_filepath, 'r') as fp:
        return parse_sdf(fp.read())
    return None
    
if __name__ == '__main__':
    print(get_delays('sdf/fa.syn.sdf'))