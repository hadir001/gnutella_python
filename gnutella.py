import yaml
import random
import time
import threading
from datetime import datetime

class Node:
    def __init__(self, address, neighbors):
        self.address = address  # Unique address of the node
        self.neighbors = neighbors  # List of neighbor node addresses
        self.documents = {}  # Local document metadata from a .yaml file
        self.requests = {}  # Dictionary to store request id and list of initiators

    # Load documents from a YAML file
    def load_documents(self, yaml_file):
        with open(yaml_file, 'r') as f:
            self.documents = yaml.safe_load(f)

    # Initiate a search request (R1) for a document by ID
    def initiate_request(self, doc_id, ttl=3):
        request_id = self._generate_unique_id()
        print(f"{self.address} initiated search for document '{doc_id}' with TTL={ttl}")
        self.requests[request_id] = [self.address]  # Store this node as the initiator
        self.send_request(doc_id, request_id, ttl, None)  # No sender initially

    # Send R1 request to all neighbors (using threads for parallel communication)
    def send_request(self, doc_id, request_id, ttl, sender_address):
        threads = []
        for neighbor in self.neighbors:
            # Avoid sending the request back to the node that sent it
            if neighbor.address == sender_address:
                continue
            t = threading.Thread(target=neighbor.receive_request, args=(doc_id, request_id, ttl, self.address))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    # Receive R1 request from another node
    def receive_request(self, doc_id, request_id, ttl, sender_address):
        # Check if the request ID is new, if not, add sender to the list if not already there
        if request_id not in self.requests:
            self.requests[request_id] = []
        
        if sender_address not in self.requests[request_id]:  # Only add if not already listed
            #print(f"{self.address} received request '{request_id}' for document '{doc_id}' from {sender_address}")
            self.requests[request_id].append(sender_address)

            # Check if the node has the document
            if self.has_document(doc_id):
                self.send_response(doc_id, request_id)

            # Forward the request if TTL > 1
            if ttl > 1:
                forwardable_neighbors = [neighbor for neighbor in self.neighbors if neighbor.address != sender_address]
                if forwardable_neighbors:
                    print(f"{self.address} forwards request to neighbors (TTL={ttl-1})")
                    self.send_request(doc_id, request_id, ttl - 1, sender_address)
            else:
                print(f"Node {self.address} stops forwarding request (TTL=0)")

    # Check if the node has the requested document
    def has_document(self, doc_id):
        for doc in self.documents:
            if doc['Id'] == doc_id:
                return True
        return False

   # Send a response to the last node that sent the request
    def send_response(self, doc_id, request_id):
        path_stack = []  # Initialize the path stack for tracking

        # Check if there is at least one requester for the request_id
        if self.requests[request_id]:
            last_requester = self.requests[request_id][-1]  # Get the last requester only
            #print(f"{self.address} found the document '{doc_id}' and is responding to the last requester: {last_requester}")
            self.forward_response(list(path_stack), request_id, last_requester)

    def forward_response(self, path_stack, request_id, target_address):
        path_stack.append(self.address)

        # Find the next hop address using the requests dictionary (who sent this request to this node)
        next_hop_address = self.requests.get(request_id)
                # Check if the response has reached the original requester
        if self.requests[request_id] == None:  # We reached the requester
                    path_stack.append(next_hop_address)
                    print(f"Document found! Response for '{request_id}' reached {next_hop_address}. Path: {path_stack}")
        else:
            # Forward response to the next hop based on the requester's path
            next_hop_address = self.requests[request_id][-1]  # Use last requester path
            for neighbor in self.neighbors:
                if neighbor.address == next_hop_address:
                    print(f"{self.address} forwards response for request '{request_id}' to {next_hop_address}. Path: {path_stack}")
                    neighbor.forward_response(list(path_stack), request_id, target_address)  # Send a copy of the path stack
                    break

    # Generate a unique request ID
    def _generate_unique_id(self):
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"req_{current_time}"

# Example with 6 nodes where A is the sender 
if __name__ == "__main__":
    # Simulating 6 nodes with neighbors
    node_a = Node("Node_A", [])
    node_b = Node("Node_B", [])
    node_c = Node("Node_C", [])
    node_d = Node("Node_D", [])
    node_e = Node("Node_E", [])
    node_g = Node("Node_G", [])
    node_f = Node("Node_F", [])

    # Setting up neighbor relationships
    node_a.neighbors = [node_b, node_c]
    node_b.neighbors = [node_a, node_g]
    node_c.neighbors = [node_a, node_e, node_d]
    node_d.neighbors = [node_c, node_f]
    node_e.neighbors = [node_c]
    node_g.neighbors = [node_b, node_f]
    node_f.neighbors = [node_g, node_d]

    # Load documents into each node
    node_a.load_documents("node_a_documents.yaml")
    node_b.load_documents("node_b_documents.yaml")
    node_c.load_documents("node_c_documents.yaml")
    node_d.load_documents("node_d_documents.yaml")
    node_e.load_documents("node_e_documents.yaml")
    node_g.load_documents("node_g_documents.yaml")
    node_f.load_documents("node_f_documents.yaml")

    # Node A initiates a search for a document with ID "doc123"
    node_a.initiate_request("doc123", ttl=3)
