from multiprocessing import Process, Manager, set_start_method, get_start_method
from multiprocessing.managers import DictProxy
import os
import sys
from types import ModuleType
import unittest

TEST_CLASS_NAME = "Test"

def allowlist(event, args):
    "Raises PermissionError if non-allowlisted operation is attempted."
    
    eventtype = event.split(".", maxsplit=1)[0]
    allowed_events = [
        "os.listdir", # needed for import
        "import", # needed for import
        "exec", # needed for import 
        "compile", # needed for import
        "marshal.loads", # needed for import
        "sys._getframe", # needed for collections lib
        "sys.excepthook", # needed for raising exceptions
        "builtins.id", # needed for multiprocessing comms
        "socket.__new__", # needed for multiprocessing comms
        "socket.connect", # needed for multiprocessing comms
        "os.putenv", # process has its own environment
        "os.unsetenv" # process has its own environment
    ]
    allowed_eventtypes = [
        "object" # needed for normal operation
    ]
    if event not in allowed_events and eventtype not in allowed_eventtypes:
        if event == "open":
            filepath, mode, _ = args
            if mode != "r":
                raise PermissionError("Filesystem is read-only")
            if not (filepath.startswith("/opt/python/") or filepath.startswith("/var/lang/")):
                raise PermissionError(f"Read access to file '{filepath}' is not allowed")
        else:
            raise PermissionError(f"{event} is not allowed")

def execute_tests(test_code_str: str, func_code_str: str, shared_dict: DictProxy) -> None:
    """This function is run in a separate, restricted process.
    It communicates with the parent process through DictProxy."""
    
    # only allow selected operations from now on
    sys.addaudithook(allowlist)
    
    # start with clean environment
    os.environ.clear()

    try:
        # create a new module and execute function and test code inside it
        unittest_module = ModuleType('unittest_module')
        exec(func_code_str, unittest_module.__dict__)
        exec(test_code_str, unittest_module.__dict__)
    
        # extract the test class
        test_class = getattr(unittest_module, TEST_CLASS_NAME)
    
        # create TestResult object to store results
        result = unittest.TestResult()
    
        # run the unittest and store results in TestResult object
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.run(result)
        
        # generate the result dictionary
        results_dict = {
            'total': result.testsRun,
            'failures': [str(f[1]) for f in result.failures],
            'errors': [str(e[1]) for e in result.errors],
            'skipped': [str(s[1]) for s in result.skipped],
            'successful': result.wasSuccessful()
        }
    
        # save output to a dict that can be read from parent process
        shared_dict.update(results_dict)
    
    except:
        # executing the untrusted code failed, most likely syntax error
        import traceback
        shared_dict.update({"error": traceback.format_exc()})

def lambda_handler(event, context) -> dict:
    """Receives user input, spawns a separate process (with restricted permissions,
    separate resources and environment) for running untrusted code"""
    
    # if not yet set, configure start method to spawn a separate process for each invokation
    # slow, but better isolation
    if get_start_method(allow_none=True) != 'spawn':
        set_start_method('spawn')

    # read user input
    source_func = event['func']
    source_test = event['test']
    
    # prepare the shared dict
    manager = Manager()
    shared_dict = manager.dict()

    # run execute_tests function in a separate process
    p = Process(target=execute_tests, args=(source_test, source_func, shared_dict))
    p.start()
    
    # wait for the process to finish
    p.join()

    # fetch the results from DictProxy, and cast to dictionary
    return dict(shared_dict)