#!/usr/bin/env python3

import os
import time
import datetime

DRAW_PLOT = True
try:
    import draw
except Exception:
    DRAW_PLOT = False

import cutting_stock

def readExternalData(path):
    f = open(path, 'r')
    lines = f.readlines()
    module_length = []
    module_demand = []
    try:
        number_of_items = int(lines[0])
        max_roll_length = int(lines[1])
        for i in range(2, number_of_items + 2):
            length = int(lines[i].split()[0])
            demand = int(lines[i].split()[1])
            #print('length: ' + str(length) + ", demand: " + str(demand))
            module_length.append(length)
            module_demand.append(demand)
    except:
        raise Exception("Bad format in file: " + path)
    f.close()
    #module_length = list(reversed(module_length))
    #module_demand = list(reversed(module_demand))
    return number_of_items, max_roll_length, module_length,  module_demand

def exportData(number_of_modules, max_roll_length, module_lengths, module_demands):
    f = open('rand_inst:{:%Y-%m-%d %H:%M:%S}.txt'.format(datetime.datetime.now()), 'w')
    f.write(str(number_of_modules) + '\n')
    f.write(str(max_roll_length) + '\n')
    for i in range(number_of_modules):
        f.write(str(module_lengths[i]) + ' ' + str(module_demands[i]) + '\n')
    f.close()

def statsGenerator():
    out = open('stats.csv', 'w')
    out.write('problemName,numberOfSubproblemResolution,timeWithIntegerResolution,timeWithApx,totalNumberOfExecutions,trivialSolVal,finalRealSol,intSolValWithIntVars,intSolFromCeiling\n')
    for file in os.listdir("./toRun"):
        if file.endswith(".txt") and not file.startswith("stats"):
            problemName = file[:-4]
            number_of_modules, max_roll_length, module_lengths, module_demands = readExternalData("toRun/" + file)
            
            start = time.time()
            cutting_stock_problem_solutions, number_of_sub_problem_executions, ceiling_solution, integer_problem_resolution_time = cutting_stock.driver(number_of_modules, max_roll_length, module_lengths, module_demands)
            end = time.time()

            if DRAW_PLOT:
                draw.drawF2(cutting_stock_problem_solutions, number_of_sub_problem_executions, save=True, path="toRun/" + file)

            #if DRAW_PLOT:
            #    draw.drawF2(ceiling_solution, len(ceiling_solution), save=True, path="toRun/" + file + "ceil")
            
            total_time = end - start
            trivialSolVal = str(cutting_stock_problem_solutions[0])
            finalRealSol = str(cutting_stock_problem_solutions[-2])
            intSolValWithIntVars = str(cutting_stock_problem_solutions[-1])
            intSolFromCeiling = str(ceiling_solution[-1])
            out.write(problemName + ',' + str(number_of_sub_problem_executions) + ',' + 
                    str(total_time) + ',' + str(total_time - integer_problem_resolution_time) + ',' + str(len(cutting_stock_problem_solutions)) + ',' + 
                    trivialSolVal + ',' + finalRealSol + ',' + intSolValWithIntVars + ',' + intSolFromCeiling + '\n')
    out.close()


if __name__ == "__main__":
    #readExternalData("Waescher_TEST0005.txt")
    statsGenerator()
