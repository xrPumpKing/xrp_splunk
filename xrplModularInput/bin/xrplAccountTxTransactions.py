

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
    def xrplGetData(self,JSON_RPC_URL,rAddress):
        client = JsonRpcClient(JSON_RPC_URL)
        acct=rAddress
        ledger_index_min=-1
        acct_transactions_request=xrpl.models.requests.AccountTx(account=acct, ledger_index_min=ledger_index_min)
        processing_1=client.request(acct_transactions_request).result["transactions"]
        return processing_1


    def stream_events(self, inputs, ew):
        # Splunk Enterprise calls the modular input, streams XML describing the inputs to stdin and waits for XML on stfout describing events

        for input_name,input_item in inputs.inputs.items():
            JSON_RPC_URL = input_item["JSON_RPC_URL"]
            rAddress = input_item["rAddress"]
            get_full_history = input_item["get_full_history"]
            logger.info(get_full_history)

            result = self.xrplGetData(JSON_RPC_URL,rAddress)
            print(result)
            for i in result:
                event = Event()
                event.stanza = input_name
                event.data = json.dumps(i)
                ew.write_event(event)


        
        pass

if __name__=="__main__":
    sys.exit(xrplAccountTxTransactions().run(sys.argv))
