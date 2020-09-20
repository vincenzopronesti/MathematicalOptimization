#!/usr/bin/env python3

import cutting_stock
DRAW_LIB = True
try:
    import matplotlib.pyplot as plt
except Exception:
    DRAW_LIB = False


def drawF2(cutting_stock_problem_solutions, number_of_sub_problem_executions, save=False, path=None):  
    # x axis values 
    x = [i for i in range(1, len(cutting_stock_problem_solutions) + 1)] 
    # corresponding y axis values 
    y = cutting_stock_problem_solutions
    
    # plotting the points  
    plt.plot(x, y, color='green', linestyle='dashed', linewidth = 3, 
            marker='o', markerfacecolor='blue', markersize=12) 
    
    # setting x and y axis range 
    plt.ylim(0, max(y) + 2) 
    plt.xlim(0, len(x) + 2) 
    
    # naming the x axis 
    plt.xlabel('Number of solved problems') 
    # naming the y axis 
    plt.ylabel('Solution value') 
    
    # giving a title to my graph 
    if path is not None:
        plt.title(path[:-4]) 
    
    if save:
        plt.savefig(path[:-4] + ".png")
        plt.clf()
    else:
        # function to show the plot 
        plt.show() 

def drawF(cutting_stock_problem_solutions, number_of_sub_problem_executions, acceptable_sol):
    # x-coordinates of left sides of bars  
    left = [i for i in range(len(cutting_stock_problem_solutions))] 
    
    # heights of bars 
    height = [e for e in cutting_stock_problem_solutions] 
   
    # labels for bars 
    tick_label = ['Trivial patterns']
    for i in range(1,len(cutting_stock_problem_solutions) - 1):
        tick_label += ['Iteration %d' % i]
    tick_label += ['Integer variables']
    
    # plotting a bar chart 
    plt.bar(left, height, tick_label = tick_label, width = 0.4) 

    label = height
    for i in range(len(height)):
        plt.text(x = left[i] , y = height[i]+0.2, s = label[i], size = 20, color='red')

    # add threshold line for 90 percent accurate solution
    plt.axhline(y=acceptable_sol,linewidth=1, color='k')

    # naming the x-axis 
    plt.xlabel('Cutting stock problem solutions') 
    # naming the y-axis 
    plt.ylabel('Objective function values') 
    # plot title 
    plt.title('') 
    
    # function to show the plot 
    plt.show() 


if __name__ == "__main__":
    cutting_stock_problem_solutions, number_of_sub_problem_executions = cutting_stock.main()
    drawF2(cutting_stock_problem_solutions, number_of_sub_problem_executions)
