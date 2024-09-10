import os.path
import sys
from collections import defaultdict
import solidity
from slither.core.declarations import Contract, Function
from slither.slither import Slither
from typing import Set, Dict, List



class FuncNode:
    def __init__(self, function: Function):
        self.fathers = set()
        self.sons = set()
        self.function = function

    def __str__(self):
        return str(self.function)


class CallGraph:
    def __init__(self, sl):
        self.slither = sl
        self.func2node = {}

    def build_call_graph(self):
        for contract in self.slither.contracts:
            for function in contract.functions_and_modifiers:
                if not function.is_empty and function.is_implemented:
                    self.func2node[function] = FuncNode(function)

        for contract in self.slither.contracts:
            for function in contract.functions_and_modifiers:
                if not function.is_empty and function.is_implemented:
                    father_node = self.func2node[function]
                    for f in function.internal_calls:
                        if f in self.func2node.keys():
                            son_node = self.func2node[f]
                            father_node.sons.add(son_node)
                            son_node.fathers.add(father_node)

    def extract_func_call_list(self, end_function, path_contain_function=None):
        paths = []
        end_node = self.func2node[end_function]
        if path_contain_function is None:
            self.explore(end_node, [], paths, None)
        else:
            path_contain_node = self.func2node[path_contain_function]
            self.explore(end_node, [], paths, path_contain_node)
        return paths

    def explore(self, current_node: FuncNode, visited: list, paths: list, must_contained: FuncNode):
        if current_node in visited:
            return
        visited = visited + [current_node]
        if not current_node.fathers:
            if must_contained is None or must_contained in visited:
                paths.append(visited)
        for father in current_node.fathers:
            self.explore(father, visited, paths, must_contained)

    @staticmethod
    def extract_path_graph_nodes(path: List):
        all_nodes = set()
        for func in path:
            func: FuncNode
            all_nodes |= set(func.function.all_nodes())
        return all_nodes

    def get_function_fathers(self, f:Function):
        FN = self.func2node.get(f, None)
        if FN is None:
            return None
        FN: FuncNode
        return [f.function for f in FN.fathers]

    def explore_ancestors(self, current_node, ancestors:list, visited:list):
        if current_node in visited:
            return
        visited.append(current_node)
        if not current_node.fathers:
            ancestors.append(current_node)
        else:
            for f in current_node.fathers:
                self.explore_ancestors(f, ancestors, visited)

    def get_outtest_function_fathers(self, f:Function):
        FN = self.func2node.get(f, None)
        if FN is None:
            return None
        FN: FuncNode
        ancestors = []
        self.explore_ancestors(FN, ancestors, [])
        return [a.function for a in ancestors]


if __name__ == '__main__':
    solc_v = solidity.get_solc('test.sol')
    if solc_v is None:
        print('cannot get solc version')
    else:
        sl = Slither('test.sol', solc=solc_v)
        callgraph = CallGraph(sl)
        callgraph.build_call_graph()
        scan_reentrancy = reentrancy_call(sl)
        call_nodes, contained_functions = scan_reentrancy.extract()
        for i in range(len(call_nodes)):
            print(f'external call: {call_nodes[i]}')
            paths = callgraph.extract_func_call_list(call_nodes[i].function, contained_functions[i])
            print('path:', end = ' ')
            for path in paths:
                for f in path:
                    print('\t', f, end = ' ')
                print('>>>>>>>>>>>>>>>>>>>>')
                nodes = callgraph.extract_path_graph_nodes(path)
                for n in nodes:
                    print(n)