"""
In this module, the single static assignment forms are implemented to allow
further analysis. The module contain a single class named SSA.
"""
import ast
import astor
from functools import reduce
from collections import OrderedDict
import networkx as nx
from ..core.vars_visitor import get_vars

def parse_val(node):
    # does not return anything
    if isinstance(node, ast.Constant):
       return node.value
    if isinstance(node, ast.Str):
        if hasattr(node, "value"):
            return node.value
        else:
            return node.s
    return "other"


class SSA:
    """
    Build SSA graph from a given AST node based on the CFG.
    """
    def __init__ (self):
        """
        Args:
            src: the source code as input.
        """
        # the class SSA takes a module as the input
        self.numbering = {}  # numbering variables
        self.var_values = {}  # numbering variables
        self.global_live_idents = []
        self.ssa_blocks = []
        self.error_paths = {}
        self.dom = {}

        self.block_ident_gen = {}
        self.block_ident_use = {}
        self.reachable_table = {}
        id2block = {}
        self.unreachable_names = {}
        self.undefined_names_from = {}
        self.global_names = []

    def get_attribute_stmts(self, stmts):
        call_stmts = []
        for stmt in stmts:
            if isinstance(stmt,ast.Call) and isinstance(stmt.func, ast.Attribute):
                call_stmts += [stmt]

    def get_identifiers(self, ast_node):
        """
        Extract all identifiers from the given AST node.
        Args:
            ast_node: AST node.
        """
        if ast_node is None:
            return []
        res = get_vars(ast_node)
        idents = [r['name'] for r in res if  r['name'] is not None and "." not in r['name']]
        return idents

    def compute_SSA(self, cfg):
        """
        Compute single static assignment form representations for a given CFG.
        During the computing, constant value and alias pairs are generated. The following steps are used to compute SSA representations:
        step 1a: compute the dominance frontier
        step 1b: use dominance frontier to place phi node
        if node X contains assignment to a, put phi node for an in dominance frontier of X
        adding phi function may require introducing additional phi function
        start from the entry node
        step2: rename variables so only one definition per name

        Args:
            cfg: a control flow graph.
        """
        # to count how many times a var is defined
        ident_name_counter = {}
        # constant assignment dict
        ident_const_dict = {}
        # step 1a: compute the dominance frontier
        all_blocks = cfg.get_all_blocks()
        id2blocks = {block.id: block for block in all_blocks}

        block_loaded_idents = {block.id: [] for block in all_blocks}
        block_stored_idents = {block.id: [] for block in all_blocks}

        block_const_dict = {block.id: [] for block in all_blocks}

        block_renamed_stored = {block.id: [] for block in all_blocks}
        block_renamed_loaded = {block.id: [] for block in all_blocks}

        DF = self.compute_DF(all_blocks)

        for block in all_blocks:
            df_nodes = DF[block.id]
            tmp_const_dict = {}

            for idx, stmt in enumerate(block.statements):
                stmt_const_dict = {}
                stored_idents, loaded_idents, func_names = self.get_stmt_idents_ctx(
                    stmt, const_dict=stmt_const_dict
                )
                tmp_const_dict[idx] = stmt_const_dict
                block_loaded_idents[block.id] += [loaded_idents]
                block_stored_idents[block.id] += [stored_idents]
                block_renamed_loaded[block.id] += [
                    {ident: set() for ident in loaded_idents}
                ]

            block_const_dict[block.id] = tmp_const_dict

        for block in all_blocks:
            stored_idents = block_stored_idents[block.id]
            loaded_idents = block_loaded_idents[block.id]
            n_stmts = len(stored_idents)
            assert n_stmts == len(loaded_idents)
            affected_idents = []
            tmp_const_dict = block_const_dict[block.id]
            for i in range(n_stmts):
                stmt_stored_idents = stored_idents[i]
                stmt_loaded_idents = loaded_idents[i]
                stmt_renamed_stored = {}

                for ident in stmt_stored_idents:
                    affected_idents.append(ident)
                    if ident in ident_name_counter:
                        ident_name_counter[ident] += 1
                    else:
                        ident_name_counter[ident] = 0
                    # rename the var name as the number of assignments
                    stmt_const_dict = tmp_const_dict[i]
                    if ident in stmt_const_dict:
                        ident_const_dict[(ident, ident_name_counter[ident])] = (
                            stmt_const_dict[ident]
                        )

                    stmt_renamed_stored[ident] = ident_name_counter[ident]
                block_renamed_stored[block.id] += [stmt_renamed_stored]

                # same block, number used identifiers
                for ident in stmt_loaded_idents:
                    # a list of dictions for each of idents used in this statement
                    phi_loaded_idents = block_renamed_loaded[block.id][i]
                    if ident in ident_name_counter:
                        phi_loaded_idents[ident].add(ident_name_counter[ident])

            df_block_ids = DF[block.id]
            for df_block_id in df_block_ids:
                df_block = id2blocks[df_block_id]
                block_ident_gen_produced = []
                df_block_stored_idents = block_stored_idents[df_block_id]
                for af_ident in affected_idents:
                    # this for-loop process every statement in the block
                    for idx, phi_loaded_idents in enumerate(
                        block_renamed_loaded[df_block_id]
                    ):
                        block_ident_gen_produced.extend(df_block_stored_idents[idx])
                        if af_ident in block_ident_gen_produced:
                            continue
                        # place phi function here this var used
                        # if af_ident has been assigned in this block beforclee this statement, then discard it
                        # so theck af_ident has been generated in this block
                        if af_ident in phi_loaded_idents:
                            phi_loaded_idents[af_ident].add(
                                ident_name_counter[af_ident]
                            )

        return block_renamed_loaded, ident_const_dict

    def compute_SSA2(self, cfg, used_var_names = []):
        """
        Compute single static assignment form representations for a given CFG.
        During the computing, constant value and alias pairs are generated. The following steps are used to compute SSA representations:
        step 1a: compute the dominance frontier
        step 1b: use dominance frontier to place phi node
        if node X contains assignment to a, put phi node for an in dominance frontier of X
        adding phi function may require introducing additional phi function
        start from the entry node
        step2: rename variables so only one definition per name

        Args:
            cfg: a control flow graph.
        """
        # to count how many times a var is defined
        ident_name_counter = {}
        # constant assignment dict
        ident_const_dict = {}
        # step 1a: compute the dominance frontier
        all_blocks = cfg.get_all_blocks()
        id2blocks = {block.id: block for block in all_blocks}

        block_loaded_idents = {block.id: [] for block in all_blocks}
        block_stored_idents = {block.id: [] for block in all_blocks}

        block_const_dict = {block.id: [] for block in all_blocks}

        block_renamed_stored = {block.id: [] for block in all_blocks}
        block_renamed_loaded = {block.id: [] for block in all_blocks}

        block_renamed_phi_stored = {block.id: [] for block in all_blocks}
        block_renamed_phi_loaded = {block.id: [] for block in all_blocks}

        block_phi_variables_needed = {block.id: [] for block in all_blocks}

        DF = self.compute_DF(all_blocks)

        # Initialize the load and store variables for each statement in each block
        # and save the constant assignments as well
        for block in all_blocks:
            df_nodes = DF[block.id]
            tmp_const_dict = {}

            for idx, stmt in enumerate(block.statements):
                stmt_const_dict = {}
                stored_idents, loaded_idents, func_names = self.get_stmt_idents_ctx(stmt,
                                                 [], stmt_const_dict, used_var_names)
                tmp_const_dict[idx] = stmt_const_dict
                block_loaded_idents[block.id] += [loaded_idents]
                block_stored_idents[block.id] += [stored_idents]
                block_renamed_loaded[block.id] += [{ident: set() for ident in loaded_idents}]

            block_const_dict[block.id] = tmp_const_dict

        self.lookup_phi_placements(DF, all_blocks, block_phi_variables_needed, block_stored_idents)

        # For each block
        for block in all_blocks:
            stored_idents = block_stored_idents[block.id]
            loaded_idents = block_loaded_idents[block.id]
            n_stmts = len(stored_idents)
            assert (n_stmts == len(loaded_idents))
            affected_idents = []
            tmp_const_dict = block_const_dict[block.id]

            # Preset store variables for phi assignments to have correct renaming numbering
            for phi_var in block_phi_variables_needed[block.id]:
                if phi_var in ident_name_counter:
                    ident_name_counter[phi_var] += 1
                else:
                    ident_name_counter[phi_var] = 0

                stmt_renamed_stored = {}
                stmt_renamed_stored[phi_var] = ident_name_counter[phi_var]
                block_renamed_phi_stored[block.id] += [stmt_renamed_stored]

            # For each statement in the current block
            for i in range(n_stmts):
                stmt_stored_idents = stored_idents[i]  # variables which are on the left side of an assignment etc.
                stmt_loaded_idents = loaded_idents[i]  # variables which are on the right side of an assignment etc.

                # Assign the renamed loaded variables as load names
                # This has to happen before the stored variable renaming otherwise
                # assignments to a variable depending on its old value are not working like b = b + 1
                for ident in stmt_loaded_idents:
                    stmt_renamed_stored = {}
                    # a list of dictionaries for each of idents used in this statement
                    phi_loaded_idents = block_renamed_loaded[block.id][i]
                    if ident in ident_name_counter:
                        phi_loaded_idents[ident].add(ident_name_counter[ident])

                stmt_renamed_stored = {}
                # Each statement assigning a value to a variable v has to increase the name counter for v
                # so that there is no reassignment
                # Assign the renamed stored variable names
                for ident in stmt_stored_idents:
                    affected_idents.append(ident)
                    if ident in ident_name_counter:
                        ident_name_counter[ident] += 1
                    else:
                        ident_name_counter[ident] = 0
                    # rename the var name as the number of assignments
                    stmt_const_dict = tmp_const_dict[i]
                    if ident in stmt_const_dict:
                        ident_const_dict[(ident, ident_name_counter[ident])] = stmt_const_dict[ident]

                    stmt_renamed_stored[ident] = ident_name_counter[ident]
                block_renamed_stored[block.id] += [stmt_renamed_stored]

        # Set the loaded variable names for the phi assignments in all blocks
        # This is done at last, to have all predecessors already initialized
        for block in all_blocks:
            stored_idents = block_stored_idents[block.id]
            loaded_idents = block_loaded_idents[block.id]
            n_stmts = len(stored_idents)
            assert (n_stmts == len(loaded_idents))

            # Preset variables for phi assignments in upcoming blocks
            for phi_var in block_phi_variables_needed[block.id]:
                stmt_renamed_loaded = {}
                stmt_renamed_loaded[phi_var] = self.recursive_find_var_usages_in_predecessors(phi_var, block_renamed_stored, block_renamed_phi_stored, block.predecessors)
                block_renamed_phi_loaded[block.id] += [stmt_renamed_loaded]

        return block_renamed_stored, block_renamed_loaded, block_renamed_phi_stored, block_renamed_phi_loaded, ident_const_dict


    def lookup_phi_placements(self, DF, all_blocks, block_phi_variables_needed, block_stored_idents):
        for block in all_blocks:
            stored_idents = block_stored_idents[block.id]
            n_stmts = len(stored_idents)

            affected_idents = []
            for i in range(n_stmts):
                stmt_stored_idents = stored_idents[i]  # variables which are on the left side of an assignment etc.
                for ident in stmt_stored_idents:
                    affected_idents.append(ident)

            df_block_ids = DF[block.id]
            for df_block_id in df_block_ids:
                for af_ident in affected_idents:
                    if af_ident not in block_phi_variables_needed[df_block_id]:
                        block_phi_variables_needed[df_block_id].append(af_ident)


    def recursive_find_var_usages_in_predecessors(self, var_searched, block_renamed_stored, block_renamed_phi_stored, predecessors, searched_preds = []):
        nrs = []

        for pred in predecessors:
            if pred in searched_preds:
                continue
            found = False
            pred = pred.source
            highest_nr = -1
            for var_dict in block_renamed_stored[pred.id] + block_renamed_phi_stored[pred.id]:
                for var in var_dict.keys():
                    if var == var_searched:
                        highest_nr = var_dict[var]

            if highest_nr >= 0: # found an entry
                nrs.append(highest_nr)
            else:
                nrs += self.recursive_find_var_usages_in_predecessors(var_searched, block_renamed_stored, block_renamed_phi_stored, pred.predecessors, searched_preds + predecessors)
        return nrs


    def get_stmt_idents_ctx(self, stmt, del_set=[], const_dict = {}, used_var_names = []):
        """
        Extract the contextual information of each of identifiers.
        For assignment statements, the assigned values for each of variables will be stored.
        In addition, the del_set will store all deleted variables.
        Args:
            stmt: statement from AST trees.
            del_set: deleted identifiers
            const_dict: a mapping relationship between variables and their assigned values in this statement
        """
        # if this is a definition of class/function, ignore
        stored_idents = []
        loaded_idents = []
        func_names = []
        # assignment with only one target

        if isinstance(stmt, ast.Assign):
            targets = stmt.targets
            value = stmt.value
            if len(targets) == 1:
                if hasattr(targets[0], "id"):
                    left_name = stmt.targets[0].id
                    left_name = self.get_global_unique_name(left_name, used_var_names)
                    const_dict[left_name] = stmt.value
                elif isinstance(targets[0], ast.Attribute):
                    left_name = astor.to_source(stmt.targets[0]).strip()
                    left_name = self.get_global_unique_name(left_name, used_var_names)
                    const_dict[left_name] = value
                # multiple targets are represented as tuple
                elif isinstance(targets[0], ast.Tuple):
                    # value is also represented as tuple
                    if isinstance(value, ast.Tuple):
                        for elt, val in zip(targets[0].elts, value.elts):
                            if hasattr(elt, "id"):
                                left_name = elt.id
                                left_name = self.get_global_unique_name(left_name, used_var_names)
                                const_dict[left_name] = val
                            elif isinstance(targets[0], ast.Attribute):
                                #TODO: resolve attributes
                                pass
                    # value is represented as call
                    if isinstance(value, ast.Call):
                        for elt in targets[0].elts:
                            if hasattr(elt, "id"):
                                left_name = elt.id
                                left_name = self.get_global_unique_name(left_name, used_var_names)
                                const_dict[left_name] = value
                            elif isinstance(targets[0], ast.Attribute):
                                #TODO: resolve attributes
                                pass
            else:
                # Note  in some python versions, there are more than one target for an assignment
                # while in some other python versions, multiple targets are deemed as ast.Tuple type in assignment statement
                for target in stmt.targets:
                    # this is an assignment to tuple such as a,b = fun()
                    # then no valid constant value can be recorded for this statement
                    if hasattr(target, "id"):
                        left_name = target.id
                        left_name = self.get_global_unique_name(left_name, used_var_names)
                        const_dict[left_name] = None  # TODO: design a type for these kind of values
                    elif isinstance(stmt.targets[0], ast.Attribute):
                        #TODO: resolve attributes
                        pass



        # one target assignment with type annotations
        if isinstance(stmt, ast.AnnAssign):
            if hasattr(stmt.target, "id"):
                left_name = stmt.target.id
                left_name = self.get_global_unique_name(left_name, used_var_names)
                const_dict[left_name] = stmt.value
            elif isinstance(stmt.target, ast.Attribute):
                #TODO: resolve attributes
                pass
        if isinstance(stmt, ast.AugAssign):
            # note here , we need to rewrite this value to its extended form
            # if the statement is "a += 1", then the assigned value should be a+1
            if hasattr(stmt.target, "id"):
                left_name = stmt.target.id
                left_name = self.get_global_unique_name(left_name, used_var_names)
                extended_right = ast.BinOp(ast.Name(left_name, ast.Load()), stmt.op, stmt.value)
                const_dict[left_name] = extended_right
            elif isinstance(stmt.target, ast.Attribute):
                #TODO: resolve attributes
                pass
        if isinstance(stmt, ast.For):
            # there is a variation of assignment in for loop
            # in the case of :  for i in [1,2,3]
            # the element of stmt.iter is the value of this assignment
            if hasattr(stmt.target, "id"):
                left_name = stmt.target.id
                left_name = self.get_global_unique_name(left_name, used_var_names)
                iter_value = stmt.iter
                # make a iter call
                #iter_node = ast.Call(ast.Name("iter", ast.Load()), [stmt.iter], [])
                # make a next call
                #next_call_node = ast.Call(ast.Name("next", ast.Load()), [iter_node], [])
                const_dict[left_name] = iter_value

            elif isinstance(stmt.target, ast.Tuple):
                # to handle for-loop uch as:
                # for x, y in fun():
                for elt in stmt.target.elts:
                    if hasattr(elt, "id"):
                        left_name = elt.id
                        left_name = self.get_global_unique_name(left_name, used_var_names)
                        const_dict[left_name] = stmt.iter
            elif isinstance(stmt.target, ast.Attribute):
                #TODO: resolve attributes
                pass



        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            left_name = stmt.name
            left_name = self.get_global_unique_name(left_name, used_var_names)
            stored_idents.append(left_name)
            const_dict[left_name] = stmt
            func_names.append(left_name)
            new_stmt = stmt
            new_stmt.body = []
            ident_info = get_vars(new_stmt)
            for r in ident_info:
                if r['name'] is None:
                    continue
                if r['usage'] == "load":
                    loaded_idents.append(r['name'])
            return stored_idents, loaded_idents, func_names

        if isinstance(stmt, ast.ClassDef):
            left_name = stmt.name
            left_name = self.get_global_unique_name(left_name, used_var_names)
            stored_idents.append(left_name)
            const_dict[left_name] = None
            func_names.append(left_name)
            return stored_idents, loaded_idents, func_names

        # if this is control flow statements, we should not visit its body to avoid duplicates
        # as they are already in the next blocks
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            for alias in stmt.names:
                if alias.asname is None:
                    stored_idents += [alias.name.split('.')[0]]
                else:
                    stored_idents += [alias.asname.split('.')[0]]
            return stored_idents, loaded_idents, []

        if isinstance(stmt, (ast.Try)):
            for handler in stmt.handlers:
                if handler.name is not None:
                    stored_idents.append(self.get_global_unique_name(handler.name, used_var_names))

                if isinstance(handler.type, ast.Name):
                    loaded_idents.append(self.get_global_unique_name(handler.type.id, used_var_names))
                elif isinstance(handler.type, ast.Attribute) and isinstance(handler.type.value, ast.Name):
                    loaded_idents.append(self.get_global_unique_name(handler.type.value.id, used_var_names))
            return stored_idents, loaded_idents, []
        if isinstance(stmt, ast.Global):
            for name in stmt.names:
                self.global_names.append(self.get_global_unique_name(name, used_var_names))
            return stored_idents, loaded_idents, []

        visit_node = stmt

        if isinstance(visit_node,(ast.If, ast.IfExp)):
            # visit_node.body = []
            # visit_node.orlse=[]
            visit_node = stmt.test

        elif isinstance(visit_node, (ast.With)):
            visit_node.body = []
            visit_node.orlse=[]

        elif isinstance(visit_node, (ast.While)):
            visit_node.body = []

        elif isinstance(visit_node, (ast.For)):
            visit_node.body = []

        elif isinstance(visit_node, ast.Return):
            # imaginary variable
            stored_idents.append("<ret>")
            const_dict["<ret>"] = visit_node.value
        elif isinstance(visit_node, ast.Yield):
            # imaginary variable
            stored_idents.append("<ret>")
            const_dict["<ret>"] = visit_node.value

        ident_info = get_vars(visit_node)
        for r in ident_info:
            if r['name'] is None or "_hidden_" in r['name']:
                continue
            if r['usage'] == 'store':
                stored_idents.append(self.get_global_unique_name(r['name'], used_var_names))
            else:
                loaded_idents.append(self.get_global_unique_name(r['name'], used_var_names))
            if r['usage'] == 'del':
                del_set.append(self.get_global_unique_name(r['name'], used_var_names))
        return stored_idents, loaded_idents, []

    def get_global_unique_name(self, var_name, used_var_names):
        idx = 2
        appendix = ""
        while (var_name + appendix) in used_var_names:
            appendix = "_" + str(idx)
            idx += 1
        return var_name + appendix

    def to_json(self):
        pass

    def print_block(self, block):
        return block.get_source()

    # compute the dominators
    def compute_idom(self, ssa_blocks):
        """
        Compute immediate dominators for each of blocks
        Args:
            ssa_blocks: blocks from a control flow graph.
        """
        # construct the Graph
        entry_block = ssa_blocks[0]
        G = nx.DiGraph()
        for block in ssa_blocks:
            G.add_node(block.id)
            exits = block.exits
            preds =  block.predecessors
            for link in preds+exits:
                G.add_edge(link.source.id, link.target.id)
        # DF = nx.dominance_frontiers(G, entry_block.id)
        idom = nx.immediate_dominators(G, entry_block.id)
        return idom

    # compute dominance frontiers
    def compute_DF(self, ssa_blocks):
        """
        Compute dominating frontiers for each of blocks
        Args:
            ssa_blocks: blocks from a control flow graph.
        """
        # construct the Graph
        entry_block = ssa_blocks[0]
        G = nx.DiGraph()
        for block in ssa_blocks:
            G.add_node(block.id)
            exits = block.exits
            preds = block.predecessors
            for link in preds+exits:
                G.add_edge(link.source.id, link.target.id)

        # Add entry edge 0-1 and set starting node to 0
        # -> so that the entry node is not in its own immediate dominator set
        # This is due to a wrong behaviour of the nx library
        #G.add_edge(0, entry_block.id)

        # TODO: Check for networkx to implement fixes in idom calculation (idom = {start: None})
        #       and in dominance frontiers to extend the if with (or u == start)
        # DF = nx.dominance_frontiers(G, entry_block.id)

        # Use this implementation if the library is not changed

        # Add entry edge 0-1 and set starting node to 0
        # -> so that the entry node is not in its own immediate dominator set
        # This is due to a wrong behaviour of the nx library
        G.add_edge(0, entry_block.id)
        DF = nx.dominance_frontiers(G, 0)
        return DF

