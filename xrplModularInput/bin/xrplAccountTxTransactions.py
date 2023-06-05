
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

        return scheme


    def validate_input(self, validation_definition):
        # validate input
        pass


    ### Make a function to call the client URL
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
