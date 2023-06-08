

### Set up logging
import sys, os
import logging, logging.handlers
import splunk
def setup_logging():
    logger = logging.getLogger('splunk.foo')    
    SPLUNK_HOME = os.environ['SPLUNK_HOME']
    
    LOGGING_DEFAULT_CONFIG_FILE = os.path.join(SPLUNK_HOME, 'etc', 'log.cfg')
    LOGGING_LOCAL_CONFIG_FILE = os.path.join(SPLUNK_HOME, 'etc', 'log-local.cfg')
    LOGGING_STANZA_NAME = 'python'
    LOGGING_FILE_NAME = "foo.log"
    BASE_LOG_PATH = os.path.join('var', 'log', 'splunk')
    LOGGING_FORMAT = "%(asctime)s %(levelname)-s\t%(module)s:%(lineno)d - %(message)s"
    splunk_log_handler = logging.handlers.RotatingFileHandler(os.path.join(SPLUNK_HOME, BASE_LOG_PATH, LOGGING_FILE_NAME), mode='a') 
    splunk_log_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logger.addHandler(splunk_log_handler)
    splunk.setupSplunkLogger(logger, LOGGING_DEFAULT_CONFIG_FILE, LOGGING_LOCAL_CONFIG_FILE, LOGGING_STANZA_NAME)
    return logger
logger = setup_logging()
logger.info("hello world!")
SPLUNK_HOME = os.environ['SPLUNK_HOME']
logger.info(SPLUNK_HOME)
SPLUNK_DB = os.environ['SPLUNK_DB']
logger.info(SPLUNK_DB)
###


import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

import xrpl
from xrpl.clients import JsonRpcClient

from splunklib.modularinput import *

class xrplAccountTxTransactions(Script):

    def get_scheme(self):
        # returns scheme
        scheme = Scheme("XRPL Account Transactions")
        scheme.use_external_validation = False
        scheme.use_single_instance = False
        scheme.description = "Description of scheme for XRPL Account Transactions modular input where is this?"

        JSON_RPC_URL = Argument("JSON_RPC_URL")
        JSON_RPC_URL.title = "JSON RPC URL for connection"
        JSON_RPC_URL.data_type = Argument.data_type_string
        JSON_RPC_URL.description = "JSON RPC URL description change me"
        JSON_RPC_URL.required_on_create = True
        JSON_RPC_URL.required_on_edit = True
        scheme.add_argument(JSON_RPC_URL)

        rAddress = Argument("rAddress")
        rAddress.title = "r Address for searching"
        rAddress.data_type = Argument.data_type_string
        rAddress.description = "r Address description change me"
        rAddress.required_on_create = True
        rAddress.required_on_edit = True
        scheme.add_argument(rAddress)

        get_full_history = Argument("get_full_history")
        get_full_history.title = "Get full account transaction history"
        get_full_history.data_type = Argument.data_type_boolean
        get_full_history.description = "get full history description change me"
        get_full_history.required_on_create = True
        get_full_history.required_on_edit = False
        scheme.add_argument(get_full_history)

        return scheme


    def validate_input(self, validation_definition):
        # validate input
        pass


    ### Make a function to get the transactions
    def xrplGetData(self,JSON_RPC_URL,rAddress,get_full_history, input_name, ew):
        client = JsonRpcClient(JSON_RPC_URL)
        acct=rAddress

        # If select get full account history, loop through and get the whole account history
        if get_full_history=="1":
            logger.info("get_full_history is set to 1")
            
            ledger_index_min=-1
            acct_transactions_request=xrpl.models.requests.AccountTx(account=acct, ledger_index_min=ledger_index_min, forward=True, limit=1)
            ledger_data=client.request(acct_transactions_request).result


            # Create checkpoint file
            logger.info(ledger_data["transactions"][0]["tx"]["ledger_index"])
            f = open(os.path.join(SPLUNK_DB,'modinputs',input_name.replace('://',"_")), "a")
            f.write(str(ledger_data["transactions"][0]["tx"]["ledger_index"]))
            f.write("\n")
            f.close()

            # First write the first set to Splunk
            result = ledger_data["transactions"]
            logger.info(result)
            for i in result:
                #logger.info(i)
                event = Event()
                event.stanza = input_name
                event.data = json.dumps(i)
                #logger.info(event)
                ew.write_event(event)
                logger.info(event)

            # Second repeat the call and write to Splunk if Marker is there
            while True:
                if "marker" not in ledger_data:
                    break
                ledger_marker = xrpl.models.requests.AccountTx(account=acct, ledger_index_min=ledger_index_min, limit=10, forward=True, marker=ledger_data["marker"])
                ledger_data = client.request(ledger_marker).result
                result = ledger_data["transactions"]
                #logger.info(result)
                for i in result:
                    event = Event()
                    event.stanza = input_name
                    event.data = json.dumps(i)
                    ew.write_event(event)
        
        # Else just get the most recent transaction and start from there
        else:
            logger.info(SPLUNK_HOME)
            logger.info("get_full_history is not set to 1, just get 10 recent transactions and monitor from now on")
            ledger_index_min=-1
            acct_transactions_request=xrpl.models.requests.AccountTx(account=acct, ledger_index_min=ledger_index_min, forward=False, limit=1)
            ledger_data=client.request(acct_transactions_request).result


            # Create checkpoint file
            logger.info(ledger_data["transactions"][0]["tx"]["ledger_index"])
            f = open(os.path.join(SPLUNK_DB,'modinputs',input_name.replace('://',"_")), "a")
            f.write(str(ledger_data["transactions"][0]["tx"]["ledger_index"]))
            f.write("\n")
            f.close()

            result = ledger_data["transactions"]
            logger.info(result)
            for i in result:
                #logger.info(i)
                event = Event()
                event.stanza = input_name
                event.data = json.dumps(i)
                #logger.info(event)
                ew.write_event(event)
                logger.info(event)



        pass





    def get_updates_only(self,JSON_RPC_URL,rAddress,get_full_history, input_name, ew):
        
        # Read the latest checkpoint into a variable
        logger.info("TESTq")
        logger.info(os.path.join(SPLUNK_DB,'modinputs',input_name.replace('://',"_")))
        g = open(os.path.join(SPLUNK_DB,'modinputs',input_name.replace('://',"_")), 'r')
        logger.info("TEST")
        lines = g.read().splitlines()
        last_line = lines[-1]
        logger.info("LAST LINE: ")
        logger.info(last_line)

        # Get latest transactions since the latest checkmark 1 tx first -> get the latest checkmark from the latest tx -> update the checkmark file -> get remaining transactions using marker
        client = JsonRpcClient(JSON_RPC_URL)
        acct=rAddress
        ledger_index_min = last_line
        acct_transactions_request=xrpl.models.requests.AccountTx(account=acct, ledger_index_min=ledger_index_min, forward=False, limit=1)
        ledger_data=client.request(acct_transactions_request).result
        logger.info(ledger_data)

        # Create checkpoint file
        logger.info(ledger_data["transactions"][0]["tx"]["ledger_index"])
        f = open(os.path.join(SPLUNK_DB,'modinputs',input_name.replace('://',"_")), "a")
        f.write(str(ledger_data["transactions"][0]["tx"]["ledger_index"]))
        f.write("\n")
        f.close()

        if str(ledger_data["transactions"][0]["tx"]["ledger_index"])==last_line:
            logger.info("ITS THE SAME LINE")
            return

        result = ledger_data["transactions"]
        logger.info(result)
        for i in result:
            #logger.info(i)
            event = Event()
            event.stanza = input_name
            event.data = json.dumps(i)
            ew.write_event(event)
            logger.info(event)

        while True:
            logger.inf("HERE")
            if "marker" not in ledger_data:
                break
            ledger_marker = xrpl.models.requests.AccountTx(account=acct, ledger_index_min=ledger_index_min, limit=10, forward=True, marker=ledger_data["marker"])
            ledger_data = client.request(ledger_marker).result
            result = ledger_data["transactions"]
            #logger.info(result)
            for i in result:
                event = Event()
                event.stanza = input_name
                event.data = json.dumps(i)
                ew.write_event(event)

        
        pass

    def stream_events(self, inputs, ew):
        # Splunk Enterprise calls the modular input, streams XML describing the inputs to stdin and waits for XML on stfout describing events

        for input_name,input_item in inputs.inputs.items():
            JSON_RPC_URL = input_item["JSON_RPC_URL"]
            rAddress = input_item["rAddress"]
            get_full_history = input_item["get_full_history"]
            logger.info(get_full_history)
            logger.info(type(get_full_history))

            # First check if the checkpoint file exists, if so run the function to carry on from where it left off
            from os.path import exists
            file_exists = exists(os.path.join(SPLUNK_DB,'modinputs',input_name.replace('://',"_")))
            logger.info(os.path.join(SPLUNK_DB,'modinputs',input_name.replace('://',"_")))
            logger.info(file_exists)

            # If file checkpoint exists need to take that as input for the get transactions function
            if file_exists:
                logger.info("File exists get only the updates")
                
                result = self.get_updates_only(JSON_RPC_URL,rAddress,get_full_history, input_name, ew)

            # If the file does not exist need to run the initial transactions gathering
            else:
                logger.info("File does not exist, this is the first input")
                result = self.xrplGetData(JSON_RPC_URL,rAddress,get_full_history, input_name, ew)

        
        pass

if __name__=="__main__":
    sys.exit(xrplAccountTxTransactions().run(sys.argv))
