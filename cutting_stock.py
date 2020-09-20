#!/usr/bin/env python3

from gurobipy import *
import random
import math
import time
import logging

import util
from ModelException import ModelException


###### CONFIG
INSTANCE_PATH = "toRun/Waescher_TEST0058.txt"

APX = True
SUB_PROB_DIFF = 0.00001
PREV_NEXT_DIFF = 0.1
NUM_OF_SAME_VAL_TO_STOP = 80

###### LOGGER
logger = logging.getLogger(__name__) # Set up logger
if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())
    file_handler = logging.FileHandler('RunLog.log')
    formatter = logging.Formatter(
        fmt='%(asctime)s %(filename)s:%(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
logger.info('Begin')


def initData(max_roll_length, module_lengths, module_demands):
    random.seed()
    logger.info('Generating random data')
    number_of_modules = random.randint(30, 70)
    mod_len_dem = {}
    # generate random data
    while len(mod_len_dem) != number_of_modules:
        val_len = random.randint(1, int(max_roll_length/ random.randint(3, 10)))
        if val_len not in mod_len_dem.keys():
            mod_len_dem[val_len] = random.randint(1, 10)
    # sort module length and demand lists by module length
    while len(mod_len_dem) != 0:
        max_len = max(mod_len_dem.keys())
        dem_max_len = mod_len_dem[max_len]
        module_lengths += [max_len]
        module_demands += [dem_max_len]
        del mod_len_dem[max_len]


def findTrivialPatterns(A, module_lengths, max_roll_length):
    """ Finds a cutting patter that contains the maximum 
    number of modules of the same length (and zero for the 
    other lengths), for each module length."""
    logger.info('Finding trivial solution')
    m = len(module_lengths)
    for i in range(m):
        pat = [0]*m
        pat[i] = int(max_roll_length / module_lengths[i])
        A.append(pat)


def masterProblem(current_available_patterns, number_of_modules, 
    max_roll_length, module_lengths, module_demands, relax=True):
    """ Optimization model for finding the minimum number of base rolls, 
    with the currently available patterns, such that all the orders are 
    satisfied. Generated patterns are stored in the list 
    current_available_patterns, where current_available_patterns[k][i] 
    holds the number of times width i is used in pattern k; that number 
    multiplied by the number of times pattern k is used cutting_patterns[k] 
    must satisfy the ordered number of width i, module_demands[i]. 
    The objective is to minimize the number of base rolls needed, 
    which is given by the sum of cutting_patterns[k] for all patterns k."""
    try:
        # Create optimization model
        m = Model('cutting_stock')

        if relax == True:
            # cutting_patterns[i] is the number of times that the i-th pattern is used
            cutting_patterns = m.addVars(len(current_available_patterns), 
                vtype=GRB.CONTINUOUS, name="cutting_patterns")
            # vtype= BINARY, CONTINUOUS, INTEGER
        else:
            # final run will be executed with integer variables
            cutting_patterns = m.addVars(len(current_available_patterns), 
                vtype=GRB.INTEGER, name="cutting_patterns")

        constraints = []
        for module in range(number_of_modules):
            constraints += [m.addConstr(sum(cutting_patterns[i] * 
                current_available_patterns[i][module]  
                for i in range(len(cutting_patterns))) >= module_demands[module], 
                "demand[%s]" % module)]

        m.setObjective(cutting_patterns.sum('*'), GRB.MINIMIZE)

        m.optimize()

        if m.status == GRB.Status.INFEASIBLE:
            raise ModelException("Infeasible model")

        if m.status == GRB.Status.UNBOUNDED:
            raise ModelException("Unbounded model")

        #if m.status == GRB.Status.OPTIMAL:
        #    print("optimum")

        # sol with next integer value
        ceil_sols = []
        if relax:
            for v in m.getVars():
                #print('%s %g' % (v.varName, v.x))
                x = math.ceil(v.x)
                ceil_sols += [x]

        print('obj: %g' % m.objVal)

        logger.info('master result: ' + str(m.objVal))

        #m.reset()
        res = m.objVal

        if relax:
            lambda_params = []
            for module in range(number_of_modules):
                lambda_params += [constraints[module].Pi]
            return res, lambda_params, sum(ceil_sols)
        else:
            #print("returning int/float sol: " + str(m.objVal))
            return res
    except GurobiError as e:
        print('Error code ' + str(e.errno) + ': ' + str(e))
    except AttributeError:
        print('Encountered an attribute error')


def subProblem(lambda_params, number_of_modules, max_roll_length, 
    module_lengths, module_demands):
    """knapsack subproblem to find a new cutting pattern"""
    logger.info('Starting knapsack problem')
    try:
        m = Model('knapsack')

        y = []
        for module in range(number_of_modules):
            y += [m.addVar(lb=0, vtype=GRB.INTEGER ,name="y[%s]" % module)]

        m.addConstr(sum(y[i] * module_lengths[i] 
            for i in range(number_of_modules)) <= max_roll_length)

        m.setObjective(sum(lambda_params[i] * y[i] 
            for i in range(number_of_modules)), GRB.MAXIMIZE)

        m.optimize()

        resNewPattern = []
        for v in m.getVars():
            #print('%s %g' % (v.varName, v.x))
            resNewPattern += [int(v.x)]

        #print('obj: %g' % m.objVal)
        res = m.objVal
        #print('retuning res: ' + str(res))
        #print('new generated column: ' + str(resNewPattern))

        logger.info('knapsack result: ' + str(res))
        return res, resNewPattern

    except GurobiError as e:
        print('Error code ' + str(e.errno) + ': ' + str(e))
    except AttributeError:
        print('Encountered an attribute error')


def driver(number_of_modules, max_roll_length, 
    module_lengths, module_demands, apx=APX):
    """ 
    Basic schema:
    1) Find trivial cutting patters and add them to 
        the available cutting patterns
    2) Solve cutting stock problem with the available 
        cutting patters
    3) Solve knapsack subproblem to find a new cutting patter
    4) If this cutting patters is useful (objective 
        function > 1) add it to the available cutting patters 
        and go to 2), else go to 5)
    5) Solve cutting stock problem with integer variables 
        and the cutting patterns previously found

    if apx is True, everytime a new cutting stock solution 
    is found it is compared with the former one to check 
    if they differ for less than PREV_NEXT_DIFF. if this 
    happens for more than NUM_OF_SAME_VAL_TO_STOP times 
    in a row, then the cutting pattern currently available 
    are used to solve the integer problem.
    """

    current_available_patterns = []

    cutting_stock_problem_solutions = []
    cutting_stock_problem_ceil_solutions = []

    keep_executing = True
    number_of_sub_problem_executions = 0

    findTrivialPatterns(current_available_patterns, 
        module_lengths, max_roll_length)

    count_to_break = 0
    prev = None
    next = None

    while keep_executing:
        # solve cutting stock problem
        try:
            master_res, lambda_params, ceil_res = masterProblem(
                current_available_patterns, number_of_modules, 
                max_roll_length, module_lengths, module_demands)
            logger.info("master_res = " + str(master_res))
            logger.info("lambda_params = " + str(lambda_params))
        except ModelException as e:
            print(str(e))
            return

        cutting_stock_problem_solutions += [master_res]
        cutting_stock_problem_ceil_solutions += [ceil_res]

        if apx is True:
            # check if solution is improving
            if prev is None:
                prev = master_res
                #logger.info("comp: prev is None")
            elif prev is not None and next is None:
                next = master_res
                #logger.info("comp: comparing prev: " + str(prev) + " and next: " + str(next))
                if (abs(prev - next) < PREV_NEXT_DIFF):
                    count_to_break += 1
                    #logger.info("comp: updating count_to_break: " + str(count_to_break))
                else:
                    #logger.info("comp: setting count_to_break to 0")
                    count_to_break = 0
            else:
                prev = next
                next = master_res
                #logger.info("comp: comparing prev: " + str(prev) + " and next: " + str(next))
                if (abs(prev - next) < PREV_NEXT_DIFF):
                    count_to_break += 1
                    #logger.info("comp: updating count_to_break: " + str(count_to_break))
                else:
                    #logger.info("comp: setting count_to_break to 0")
                    count_to_break = 0

            if count_to_break > NUM_OF_SAME_VAL_TO_STOP:
                # if the cutting stock solution is the 'same' 
                # after NUM_OF_SAME_VAL_TO_STOP, then stop exectuting
                keep_executing = False
                break

        # solve the knapsack subproblem
        try:
            sub_res, res_new_pattern = subProblem(
                lambda_params, number_of_modules, max_roll_length, 
                module_lengths, module_demands)
            logger.info("sub_res = " + str(sub_res))
            logger.info("new_pattern = " + str(res_new_pattern))
        except ModelException as e:
            print(str(e))
            return
        number_of_sub_problem_executions += 1

        # check if the knapsack solution can be used 
        # to get a better cutting stock solution
        if sub_res <= 1 + SUB_PROB_DIFF:#1.00001:
            # no other pattern would improve the current solution
            keep_executing = False 
            # found optimum solution (with current patterns)
        else:
            # sub_res > 1 + SUB_PROB_DIFF, found a new pattern to add
            current_available_patterns += [res_new_pattern]

    # last run with integer variables and final cutting pattern configuration
    logger.info('Final integer execution')
    start = time.time()
    master_res = masterProblem(current_available_patterns, 
        number_of_modules, max_roll_length, module_lengths, 
        module_demands, relax=False)
    end = time.time()
    cutting_stock_problem_solutions += [master_res]
    integer_problem_resolution_time = end - start
    return cutting_stock_problem_solutions, number_of_sub_problem_executions, cutting_stock_problem_ceil_solutions, integer_problem_resolution_time


def main():
    module_lengths = []
    module_demands = []
    max_roll_length = 10000
    number_of_modules = 0


    if INSTANCE_PATH is None:
        # generate random instance
        initData(max_roll_length, module_lengths, module_demands)
        number_of_modules = len(module_demands)
        util.exportData(number_of_modules, max_roll_length, module_lengths, module_demands)
    else:
        # or import an existing instance
        #number_of_modules, max_roll_length, module_lengths, module_demands = util.readExternalData("Waescher_TEST0044.txt")
        number_of_modules, max_roll_length, module_lengths, module_demands = util.readExternalData(INSTANCE_PATH)

    # solve
    return driver(number_of_modules, max_roll_length, module_lengths, module_demands, apx=APX)

if __name__ == "__main__":
    main()
