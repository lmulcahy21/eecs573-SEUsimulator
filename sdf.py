from f4pga_sdf_timing.sdf_timing.sdfparse import parse as parse_sdf

if __name__ == '__main__':
    with open('sdf/fa.syn.sdf', 'r') as fp:
        print(parse_sdf(fp.read()))