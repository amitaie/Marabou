'''
Top contributors (to current version):
    - Christopher Lazarus
    - Kyle Julian
    - Andrew Wu
    
This file is part of the Marabou project.
Copyright (c) 2017-2019 by the authors listed in the file AUTHORS
in the top-level source directory) and their institutional affiliations.
All rights reserved. See the file COPYING in the top-level source
directory for licensing information.

Marabou defines key functions that make up the main user interface to Maraboupy
'''

import warnings
from maraboupy.MarabouCore import *

# Import parsers if required packages are installed
try:
    from maraboupy.MarabouNetworkNNet import *
except ImportError:
    warnings.warn("NNet parser is unavailable because the numpy package is not installed")
try:
    from maraboupy.MarabouNetworkTF import *
except ImportError:
    warnings.warn("Tensorflow parser is unavailable because tensorflow package is not installed")
try:
    from maraboupy.MarabouNetworkONNX import *
except ImportError:
    warnings.warn("ONNX parser is unavailable because onnx or onnxruntime packages are not installed")

def read_nnet(filename, normalize=False):
    """Constructs a MarabouNetworkNnet object from a .nnet file

    Args:
        filename (str): Path to the .nnet file
        normalize (bool, optional): If true, incorporate input/output normalization
                  into first and last layers of network

    Returns:
        :class:`~maraboupy.MarabouNetworkNNet.MarabouNetworkNNet`
    """
    return MarabouNetworkNNet(filename, normalize=normalize)


def read_tf(filename, inputNames=None, outputNames=None, modelType="frozen", savedModelTags=[]):
    """Constructs a MarabouNetworkTF object from a frozen Tensorflow protobuf

    Args:
        filename (str): Path to tensorflow network
        inputNames (list of str, optional): List of operation names corresponding to inputs
        outputNames (list of str, optional): List of operation names corresponding to outputs
        modelType (str, optional): Type of model to read. The default is "frozen" for a frozen graph.
                            Can also use "savedModel_v1" or "savedModel_v2" for the SavedModel format
                            created from either tensorflow versions 1.X or 2.X respectively.
        savedModelTags (list of str, optional): If loading a SavedModel, the user must specify tags used, default is []

    Returns:
        :class:`~maraboupy.MarabouNetworkTF.MarabouNetworkTF`
    """
    return MarabouNetworkTF(filename, inputNames, outputNames, modelType, savedModelTags)

def read_onnx(filename, inputNames=None, outputNames=None):
    """Constructs a MarabouNetworkONNX object from an ONNX file

    Args:
        filename (str): Path to the ONNX file
        inputNames (list of str, optional): List of node names corresponding to inputs
        outputNames (list of str, optional): List of node names corresponding to outputs

    Returns:
        :class:`~maraboupy.MarabouNetworkONNX.MarabouNetworkONNX`
    """
    return MarabouNetworkONNX(filename, inputNames, outputNames)

def load_query(filename):
    """Load the serialized inputQuery from the given filename

    Args:
        filename (str): File to read for loading input query

    Returns:
        :class:`~maraboupy.MarabouCore.InputQuery`
    """
    return MarabouCore.loadQuery(filename)

def solve_query(ipq, filename="", verbose=True, options=None, propertyFilename=""):
    """Function to solve query represented by this network

    Args:
        ipq (:class:`~maraboupy.MarabouCore.InputQuery`): InputQuery object, which can be obtained from
                   :func:`~maraboupy.MarabouNetwork.getInputQuery` or :func:`~maraboupy.Marabou.load_query`
        filename (str, optional): Path to redirect output to, defaults to ""
        verbose (bool, optional): Whether to print out solution after solve finishes, defaults to True
        options: (:class:`~maraboupy.MarabouCore.Options`): Object for specifying Marabou options
        propertyFilename (str, optional): Path to property file

    Returns:
        (tuple): tuple containing:
            - exitCode (str): A string representing the exit code (sat/unsat/TIMEOUT/ERROR/UNKNOWN/QUIT_REQUESTED).
            - vals (Dict[int, float]): Empty dictionary if UNSAT, otherwise a dictionary of SATisfying values for variables
            - stats (:class:`~maraboupy.MarabouCore.Statistics`, optional): A Statistics object to how Marabou performed
    """
    if propertyFilename:
        MarabouCore.loadProperty(ipq, propertyFilename)
    if options is None:
        options = createOptions()
    exitCode, vals, stats = MarabouCore.solve(ipq, options, filename)
    if verbose:
        if stats.hasTimedOut():
            print ("TO")
        elif len(vals)==0:
            print("unsat")
        else:
            print("sat")
            for i in range(ipq.getNumInputVariables()):
                print("input {} = {}".format(i, vals[ipq.inputVariableByIndex(i)]))
            for i in range(ipq.getNumOutputVariables()):
                print("output {} = {}".format(i, vals[ipq.outputVariableByIndex(i)]))

    return [exitCode, vals, stats]

def createOptions(numWorkers=1, initialTimeout=5, initialSplits=0, onlineSplits=2,
                  timeoutInSeconds=0, timeoutFactor=1.5, verbosity=2, snc=False,
                  splittingStrategy="auto", sncSplittingStrategy="auto",
                  restoreTreeStates=False, splitThreshold=20, solveWithMILP=False,
                  preprocessorBoundTolerance=0.0000000001, dumpBounds=False,
                  tighteningStrategy="deeppoly", milpTightening="none", milpSolverTimeout=0,
                  numSimulations=10, numBlasThreads=1, performLpTighteningAfterSplit=False,
                  lpSolver="", produceProofs=False):
    """Create an options object for how Marabou should solve the query

    Args:
        numWorkers (int, optional): Number of workers to use in Split-and-Conquer(SnC) mode, defaults to 4
        initialTimeout (int, optional): Initial timeout in seconds for SnC mode before dividing, defaults to 5
        initialSplits (int, optional): Number of time sto perform the initial partitioning.
            This creates 2^(initialSplits) sub-problems for SnC mode, defaults to 0
        onlineSplits (int, optional): Number of times to perform the online partitioning when a sub-query
            time out. This creates 2^(onlineSplits) sub-problems for SnC mode, defaults to 2
        timeoutInSeconds (int, optional): Timeout duration for Marabouin seconds, defaults to 0
        timeoutFactor (float, optional): Timeout factor for SnC mode, defaults to 1.5
        verbosity (int, optional): Verbosity level for Marabou, defaults to 2
        snc (bool, optional): If SnC mode should be used, defaults to False
        splittingStrategy (string, optional): Specifies which partitioning strategy to use (auto/largest-interval/relu-violation/polarity/earliest-relu)
        sncSplittingStrategy (string, optional): Specifies which partitioning strategy to use in the SnC mode (auto/largest-interval/polarity).
        restoreTreeStates (bool, optional): Whether to restore tree states in dnc mode, defaults to False
        solveWithMILP (bool, optional): Whther to solve the input query with a MILP encoding. Currently only works when Gurobi is installed. Defaults to False.
        preprocessorBoundTolerance ( float, optional): epsilon value for preprocess bound tightening . Defaults to 10^-10.
        dumpBounds (bool, optional): Print out the bounds of each neuron after preprocessing. defaults to False
        tighteningStrategy (string, optional): The abstract-interpretation-based bound tightening techniques used during the search (deeppoly/sbt/none). default to deeppoly.
        milpTightening (string, optional): The (mi)lp-based bound tightening techniques used to preprocess the query (milp-inc/lp-inc/milp/lp/none). default to lp.
        milpSolverTimeout (float, optional): Timeout duration for MILP
        numSimulations (int, optional): Number of simulations generated per neuron, defaults to 10
        numBlasThreads (int, optional): Number of threads to use when using OpenBLAS matrix multiplication (e.g., for DeepPoly analysis), defaults to 1
        performLpTighteningAfterSplit (bool, optional): Whether to perform a LP tightening after a case split, defaults to False
        lpSolver (string, optional): the engine for solving LP (native/gurobi).
    Returns:
        :class:`~maraboupy.MarabouCore.Options`
    """
    options = Options()
    options._numWorkers = numWorkers
    options._initialTimeout = initialTimeout
    options._initialDivides = initialSplits
    options._onlineDivides = onlineSplits
    options._timeoutInSeconds = timeoutInSeconds
    options._timeoutFactor = timeoutFactor
    options._verbosity = verbosity
    options._snc = snc
    options._splittingStrategy = splittingStrategy
    options._sncSplittingStrategy = sncSplittingStrategy
    options._restoreTreeStates = restoreTreeStates
    options._splitThreshold = splitThreshold
    options._solveWithMILP = solveWithMILP
    options._preprocessorBoundTolerance = preprocessorBoundTolerance
    options._dumpBounds = dumpBounds
    options._tighteningStrategy = tighteningStrategy
    options._milpTightening = milpTightening
    options._milpSolverTimeout = milpSolverTimeout
    options._numSimulations = numSimulations
    options._numBlasThreads = numBlasThreads
    options._performLpTighteningAfterSplit = performLpTighteningAfterSplit
    options._lpSolver = lpSolver
    options._produceProofs = produceProofs
    return options
