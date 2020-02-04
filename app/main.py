from __future__ import print_function
from ariadne import ObjectType, QueryType, MutationType, gql, make_executable_schema
from ariadne.asgi import GraphQL
from asgi_lifespan import Lifespan, LifespanMiddleware
from graphqlclient import GraphQLClient

# HTTP request library for access token call
import requests
# .env
from dotenv import load_dotenv
import os

# Google OR Tools

from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

# Load environment variables
load_dotenv()


def getAuthToken():
    authProvider = os.getenv('AUTH_PROVIDER')
    authDomain = os.getenv('AUTH_DOMAIN')
    authClientId = os.getenv('AUTH_CLIENT_ID')
    authSecret = os.getenv('AUTH_SECRET')
    authIdentifier = os.getenv('AUTH_IDENTIFIER')

    # Short-circuit for 'no-auth' scenario.
    if(authProvider == ''):
        print('Auth provider not set. Aborting token request...')
        return None

    url = ''
    if authProvider == 'keycloak':
        url = f'{authDomain}/auth/realms/{authIdentifier}/protocol/openid-connect/token'
    else:
        url = f'https://{authDomain}/oauth/token'

    payload = {
        'grant_type': 'client_credentials',
        'client_id': authClientId,
        'client_secret': authSecret,
        'audience': authIdentifier
    }

    headers = {'content-type': 'application/x-www-form-urlencoded'}

    r = requests.post(url, data=payload, headers=headers)
    response_data = r.json()
    print("Finished auth token request...")
    return response_data['access_token']


def getClient():

    graphqlClient = None

    # Build as closure to keep scope clean.

    def buildClient(client=graphqlClient):
        # Cached in regular use cases.
        if (client is None):
            print('Building graphql client...')
            token = getAuthToken()
            if (token is None):
                # Short-circuit for 'no-auth' scenario.
                print('Failed to get access token. Abandoning client setup...')
                return None
            url = os.getenv('MAANA_ENDPOINT_URL')
            client = GraphQLClient(url)
            client.inject_token('Bearer '+token)
        return client
    return buildClient()

# Define types using Schema Definition Language (https://graphql.org/learn/schema/)
# Wrapping string in gql function provides validation and better error traceback
type_defs = gql("""

type CPSolution {
  id: ID!
  status: String
  objectiveValue: Int
  varValues: [IntVarValue]
}

type IntegerLinearCoefficient {
  id: ID!
  value: Int
}

input IntegerLinearCoefficientAsInput {
  id: ID!
  value: Int
}

type IntegerLinearConstraint {
  id: ID!
  upperBound: Int
  lowerBound: Int
  coefficients: [IntegerLinearCoefficient]
}

input IntegerLinearConstraintAsInput {
  id: ID!
  upperBound: Int
  lowerBound: Int
  coefficients: [IntegerLinearCoefficientAsInput]
}

type IntVar {
  id: ID!
  lowerBound: Int
  upperBound: Int
}

input IntVarAsInput {
  id: ID!
  lowerBound: Int
  upperBound: Int
}

type IntVarValue {
  id: ID!
  value: Int
}

type IntegerLinearObjective {
  id: ID!
  coefficients: [IntegerLinearCoefficient]
  maximize: Boolean
}

input IntegerLinearObjectiveAsInput {
  id: ID!
  coefficients: [IntegerLinearCoefficientAsInput]
  maximize: Boolean
}

###

type Query {
    
    solveLinearCPProblem(
        vars: [IntVarAsInput], 
        constraints: [IntegerLinearConstraintAsInput], 
        objective: IntegerLinearObjectiveAsInput
        ): CPSolution
}
""")

# Map resolver functions to Query fields using QueryType
query = QueryType()

# Resolvers are simple python functions

#Resolver for Simple Constraint Programming
@query.field("solveLinearCPProblem")
def resolve_solveLinearCPProblem(*_, vars, constraints, objective):
    id = 'CP_SAT_SOLVER'

    #Create the model
    model = cp_model.CpModel()

    # Create variables
    varDict = {}
    for var in vars:
        varDict[var["id"]] = model.NewIntVar(
            var["lowerBound"],
            var["upperBound"],
            var["id"])

    # Create Constraints
    # model.Add(var1*coeff1 + var2*coeff2 <= upperBound)
    
    for constraint in constraints:
        model.Add(sum( (varDict[coef["id"]] * coef["value"] for coef in constraint["coefficients"]))  <= constraint["upperBound"])
    # Create Objective

    if(objective["maximize"]):
        model.Maximize( sum( (varDict[coef["id"]] * coef["value"] for coef in objective["coefficients"]))  )

    # Run Solver
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        status = "OPTIMAL"
        varValues = []
        for key, item in varDict.items():
            varValues.append({"id": key, "value": solver.Value(item)})
        
        return {
            "id": id,
            "status": status,
            "objectiveValue": solver.ObjectiveValue(),
            "varValues": varValues
        }


#end of Simple Constraint Programming Resolver   


# Create executable GraphQL schema
schema = make_executable_schema(type_defs, [query])

# --- ASGI app

# Create an ASGI app using the schema, running in debug mode
# Set context with authenticated graphql client.
app = GraphQL(
    schema, debug=True)

#context_value={'client': getClient()}

# 'Lifespan' is a standalone ASGI app.
# It implements the lifespan protocol,
# and allows registering lifespan event handlers.
lifespan = Lifespan()


@lifespan.on_event("startup")
async def startup():
    print("Starting up...")
    print("... done!")


@lifespan.on_event("shutdown")
async def shutdown():
    print("Shutting down...")
    print("... done!")

# 'LifespanMiddleware' returns an ASGI app.
# It forwards lifespan requests to 'lifespan',
# and anything else goes to 'app'.
app = LifespanMiddleware(app, lifespan=lifespan)
