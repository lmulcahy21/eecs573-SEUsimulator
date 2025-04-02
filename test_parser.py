from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

# Parse Verilog file
ast, directives = parse(['full_adder_1bit.vg'])
# ast.show()
# print(directives)
# Traverse AST to extract instances and connections
from pyverilog.vparser.ast import InstanceList, PortArg, ModuleDef, Paramlist, Pointer


# ast:
#  Description
#       - ModuleDef
#           - ParamList
#           - PortList

# Module:        self.lineno = lineno
        # self.name = name
        # self.paramlist = paramlist
        # self.portlist = portlist
        # self.items = items
        # self.default_nettype = default_nettype

# Goal: break up the parsed AST into a graph of connections, each wire has ptr to where

def main():
    instances = []
    description = ast.children()[0] # Source -> Tuple(Description) -> Tuple(ModuleDefs)
    for module in description.children():
        # paramlist = module.paramlist
        portlist = module.portlist
        items = module.items
        print(items)
        # module.show()
        for child in module.children():
            if isinstance(child, InstanceList):
                # child.show()
                for inst in child.instances:
                    instance_name = inst.name
                    module_type = child.module
                    ports = []
                    for port in inst.portlist:
                        if isinstance(port, PortArg):
                            ports.append((port.portname, port.argname))
                    # generate ports dict
                    ports_dict = {}
                    for port in ports:
                        ports_dict[port[0]] = port[1]
                        # pointers index into an array/multiwidth wire, separate bits tho
                        # ie. B[38] =
                        # Pointer:  (at 498)
                        #   ->Identifier: B (at 498)
                        #   ->IntConst: 38 (at 498)
                        if(isinstance(port[1], Pointer)):
                            port[1].show()
                            #ports_dict[port[0]] = port[1].name
                    instances.append({
                        'type': module_type,
                        'name': instance_name,
                        'ports': ports_dict
                    })
            elif isinstance(child, PortArg):
                # child.show()
                pass
            else:
                child.show()
                pass
    print("Instances:")
    for inst in instances:
        print(f"Instance Name: {inst['name']}, Type: {inst['type']}, Ports: {inst['ports']}")


if __name__ == "__main__":
    main()