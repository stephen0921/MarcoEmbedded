import re
import argparse
import sys


class my_exception(Exception):
    def __str__(self):
        print '\033[41m Some thing is wrong!\033[0m'


class macro(object):
    def __init__(self, name, pattern, all_paths):
        self.name = name;
        self.pattern = pattern;
        self.left_paths = all_paths;
        self.root = True;
        self.embedded_level = 0;
        self.children = [];

    def __str__(self):
        info = '==== macro ====\n'
        info += 'name = %s, pattern = %s\n' % (self.name, self.pattern)
        for path in self.left_paths:
            info += ', has path: %s\n' % path
        info += ', root = %s\n' % self.root
        for child in self.children:
            info += ', has child with name: %s\n' % child.name
        return info

    def unroot(self):
        self.root = False

    def add_paths(self, paths):
        for path in paths:
            if re.search(self.pattern, path):
                self.left_paths.append(path)
        
    def filter_path(self, pattern):
        if re.search(self.pattern, pattern):
            backup = self.left_paths[:]
            for path in self.left_paths:
                # print self.name
                if re.search(pattern, path):
                    # print 'pattern = %s' % pattern
                    # print 'path = %s' % path
                    backup.remove(path)
                else:
                    pass
            self.left_paths = backup

    def add_child(self, child):
        self.children.append(child)

    def children_sort(self):
        sorted(self.children, key=lambda macro: macro.pattern)
    
    def print_paths(self, f_h, embedded_level=0):
        level = embedded_level
        head = ' ' * level
        head += '`ifndef %s\n' % self.name
        f_h.write(head)
        if len(self.children) > 0:
            embedded_level = embedded_level + 1
            for child in self.children:
                child.print_paths(f_h, embedded_level);
        for line in self.left_paths:
            f_h.write(line)
            f_h.write('\n')
        tail = ' ' * level
        tail += '`endif // %s\n' % self.name
        f_h.write(tail)


def debug(args):
    b_paths = ['top/u_dut/u_b/u_c','top/u_dut/u_b/u_c/u_d']
    b_macro = macro(name='B_BFM', pattern='top/u_dut/u_b', all_paths=b_paths)

    a_paths = ['top/u_dut/u_a/u_e', 'top/u_dut/u_a']
    a_macro = macro(name='A_BFM', pattern='top/u_dut', all_paths=a_paths)
    a_macro.children = [b_macro]
    a_macro.print_paths(f_h=args.path_file)

    line = a_macro.name + ':' + a_macro.pattern + '\n' 
    args.macro_file.write(line)
    line = b_macro.name + ':' + b_macro.pattern + '\n' 
    args.macro_file.write(line)
    # print a_macro.all_paths
    # print "==="
    # print a_macro.left_paths
    
def gen(args):
    macro_dict = dict()
    paths = []
    macro_insts = []
    # process the macro file
    try:
        for line in args.input_macro_file:
            if re.search('\s*#', line) or \
               re.search('^\s*\n$', line) or \
               re.search('^\s*$', line):
                continue
            else:
                match = re.search('(\w+)\s*:\s*([\w\.\/]+)[\.\/]?$', line)
                if match:
                    macro_name = match.group(1)
                    macro_pattern = match.group(2)
                    macro_dict[macro_name] = macro_pattern
                else:
                    print "Unknow format in macro file"
                    raise my_exception
    except Exception:
        exit()

    print macro_dict
    
    # process the path file
    try:
        lines = args.input_path_file.readlines()
        for line in lines:
            line = line.rstrip()
            if re.search('\s*\/\/', line) or \
               re.search('^\s*\n$', line) or \
               re.search('^\s*$', line):
                continue
            else:
                match = re.search('\s*([\w\.\/]+)[\.\/]?$', line)
                if match:
                    # print 'match'
                    path = match.group(1)
                    # print path
                    paths.append(path)
        
    except Exception:
        exit()

    # initialize macro insts
    for (name, pattern) in macro_dict.items():
        macro_inst = macro(name, pattern, [])
        macro_inst.add_paths(paths)
        macro_insts.append(macro_inst)
        # print macro_inst

    # for macro_inst in macro_insts:
    #     macro_inst.children_sort()
    #     print macro_inst
        
    for macro_inst in macro_insts:
        for another_macro_inst in macro_insts:
            if macro_inst.name == another_macro_inst.name:
                continue
            else:
                macro_inst.filter_path(another_macro_inst.pattern)
                if re.search(macro_inst.pattern, another_macro_inst.pattern):
                    another_macro_inst.unroot()
                    macro_inst.add_child(another_macro_inst)

    for macro_inst in macro_insts:
        macro_inst.children_sort()
        if macro_inst.root == True:
            macro_inst.print_paths(args.output_file)

        
def main():
    # get options from command line
    parser = argparse.ArgumentParser(
        description='Process macro embedded.')

    subparsers = parser.add_subparsers()

    debug_parser = subparsers.add_parser('debug')

    debug_parser.add_argument('-om', dest='macro_file', metavar='out-file', type=argparse.FileType('w'), required=True, help='the output macro file for demo')
    debug_parser.add_argument('-op', dest='path_file', metavar='out-file', type=argparse.FileType('w'), required=True, help='the output path file for demo')
    debug_parser.set_defaults(func=debug)

    gen_parser = subparsers.add_parser('gen')
    
    gen_parser.add_argument('-im', dest='input_macro_file', metavar='in-file', type=argparse.FileType('r'), required=True, help='the input macro file')
    gen_parser.add_argument('-ip', dest='input_path_file', metavar='in-file', type=argparse.FileType('r'), required=True, help='the input path file')
    gen_parser.add_argument('-o', dest='output_file', metavar='out-file', type=argparse.FileType('w'), default='gen.txt', help='the output verilog paths file with macro embeded')
    gen_parser.set_defaults(func=gen)

    if len(sys.argv) == 1:
        args = parser.parse_args(['-h'])
    else:
        args = parser.parse_args()

    args.func(args)


if __name__ == '__main__':
    main()
    
