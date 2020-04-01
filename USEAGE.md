
## Features

Constraint optimization, or constraint programming (CP), is the name given to identifying feasible solutions out of a very large set of candidates, where the problem can be modeled in terms of arbitrary constraints. 

CP is based on feasibility (finding a feasible solution) rather than optimization (finding an optimal solution) and focuses on the constraints and variables rather than the objective function. In fact, a CP problem may not even have an objective function — the goal may simply be to narrow down a vary large set of possible solutions to a more manageable subset by adding constraints to the problem.

In this example we are going to solve an optimization problem and hence find the optimal solution

Consider the following linear optimization problem

Maximize 2x + 2y + 3z subject to the following constraints:

subject too;

2x + 7y + 3z <= 50

3x -5y + 7z <= 45

5x + 2y -6z <= 37

x, y, x => 0

x y z are integers

In this example we will aim to find an optimal solution using the CP-SAT solver

In order to increase computational speed, the CP-SAT solver works over the integers. This means all constraints and the objective must have integer coefficients. 

## Queries

The following queries can be run from the graphQL playground

{
  solveLinearCPProblem(
    vars: [
      { id: "x", lowerBound: 0, upperBound: 50 }
      { id: "y", lowerBound: 0, upperBound: 50 }
      { id: "z", lowerBound: 0, upperBound: 50 }
    ]
    constraints: [
      {
        id: "ct"
        lowerBound: 0
        upperBound: 50
        coefficients: [{ id: "x", value: 2 }, { id: "y", value: 7 }, { id: "z", value: 3 }]
      }
      {
        id: "ct2"
        lowerBound: 0
        upperBound: 45
        coefficients: [{ id: "x", value: 3 }, { id: "y", value: -5 }, { id: "z", value: 7 }]
      }
      {
        id: "ct3"
        lowerBound: 0
        upperBound: 37
        coefficients: [{ id: "x", value: 5 }, { id: "y", value: 2 }, { id: "z", value: -6 }]
      }
    ]

    objective: {
      id: "obj"
      coefficients: [{ id: "x", value: 2 }, { id: "y", value: 2 }, { id: "z", value: 3 }]
      maximize: true
    }
  ) {
    id
    status
    objectiveValue
    varValues {
      id
      value
    }
  }
}