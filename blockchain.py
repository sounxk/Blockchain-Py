import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse

from flask import Flask, jsonify, request

class Block(object):

    def __init__(self, index, proof, previous_hash, transactions, timestamp=None):
        self.index = index
        self.proof = proof
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp or time.time()

    @property
    def get_block_hash(self):
        block_string = "{}{}{}{}{}".format(self.index, self.proof, self.previous_hash, self.transactions, self.timestamp)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def __repr__(self):
        return "{} - {} - {} - {} - {}".format(self.index, self.proof, self.previous_hash, self.transactions, self.timestamp)

#Main BlockChain class which will manage the chain, store transactions, and have other functions in it
class BlockChain(object):

    #constructor creates list to store the blockchain and another to store the transactions in it
    def __init__(self):
        self.chain = []
        self.current_node_transactions = []
        self.nodes = set()
        self.create_genesis_block()

    @property
    def get_serialized_chain(self):
        return [vars(block) for block in self.chain]

    # creation of the GENESIS block
    def create_genesis_block(self):
        self.create_new_block(proof=0, previous_hash=0)

    def create_new_block(self, proof, previous_hash):
      # creates a new block in the blockchain and returns the last block to the chain
        block = Block(
            index=len(self.chain),
            proof=proof,
            previous_hash=previous_hash,
            transactions=self.current_node_transactions
        )
        self.current_node_transactions = []  # Reset the transaction list

        self.chain.append(block)
        return block

    @staticmethod
    def is_valid_block(block, previous_block):
        if previous_block.index + 1 != block.index:
            return False

        elif previous_block.get_block_hash != block.previous_hash:
            return False

        elif not BlockChain.is_valid_proof(block.proof, previous_block.proof):
            return False

        elif block.timestamp <= previous_block.timestamp:
            return False

        return True

    def create_new_transaction(self, sender, recipient, amount):
       # adds a new transaction into the list of transactions which would go into the next mined block
        self.current_node_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return True

    @staticmethod
    def is_valid_transaction():
        # Not Implemented
        pass

    @staticmethod
    def create_proof_of_work(previous_proof):
        """
        Generate "Proof Of Work"
        A very simple `Proof of Work` Algorithm -
            - Find a number such that, sum of the number and previous POW number is divisible by 7
        """
        proof = previous_proof + 1
        while not BlockChain.is_valid_proof(proof, previous_proof):
            proof += 1

        return proof

    @staticmethod
    def is_valid_proof(proof, previous_proof):
        return (proof + previous_proof) % 7 == 0

    @property
    def get_last_block(self):
      # returns last block in the chain
        return self.chain[-1]

    def is_valid_chain(self):
        """
        Check if given blockchain is valid
        """
        previous_block = self.chain[0]
        current_index = 1

        while current_index < len(self.chain):

            block = self.chain[current_index]

            if not self.is_valid_block(block, previous_block):
                return False

            previous_block = block
            current_index += 1

        return True

    def mine_block(self, miner_address):
        # Sender "0" means that this node has mined a new block
        # For mining the Block(or finding the proof), we must be awarded with some amount(in our case this is 1)
        self.create_new_transaction(
            sender="0",
            recipient=miner_address,
            amount=1,
        )

        last_block = self.get_last_block

        last_proof = last_block.proof
        proof = self.create_proof_of_work(last_proof)

        last_hash = last_block.get_block_hash
        block = self.create_new_block(proof, last_hash)

        return vars(block)  # Return a native Dict type object

    def create_node(self, address):
       # add a new node to the list of nodes
        self.nodes.add(address)
        return True

    @staticmethod
    def get_block_object_from_block_data(block_data):
        return Block(
            block_data['index'],
            block_data['proof'],
            block_data['previous_hash'],
            block_data['transactions'],
            timestamp=block_data['timestamp']
        )

    # initiation of the node
app = Flask(__name__)

# generation of globally unique address 
node_identifier = str(uuid4()).replace('-', '')

# initiate the Blockchain
blockchain = BlockChain()

@app.route('/mine', methods=['GET'])
def mine():

    # first the PoW algorithm will run to find the new proof
    last_block = blockchain.last_block
    last_proof = get_last_block['proof']
    proof = blockchain.create_proof_of_work(last_proof)

    # 1 coin is added as a reqard for mining
    blockchain.create_new_transaction(
        sender=0,
        recipient=node_identifier,
        amount=1,
    )

    # forge the new block by adding it to the chain
    previous_hash = blockchain.get_block_hash(last_block)
    block = blockchain.create_new_block(proof, previous_hash)

    response = {
        'message': "Forged new block.",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response, 200)

@app.route('/transaction/new', methods=['GET'])
def create_new_transaction():

    values = request.get_json()
    required = ['sender', 'recipient', 'amont']

    if not all(k in values for k in required):
        return 'Missing values.', 400

    # create a new transaction
    index = blockchain.create_new_transaction(
        sender = values['sender'],
        recipient = values['recipient'],
        amount = values['amount']
    )

    response = {
        'message': f'Transaction will be added to the Block {index}',
    }
    return jsonify(response, 200)

@app.route('/chain', methods=['GET'])
def is_valid_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def create_node():
    values = request.get_json()

    print('values',values)
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    # register each newly added node
    for node in nodes: blockchain.register_node(node)

    response = {
        'message': "New nodes have been added",
        'all_nodes': list(blockchain.nodes),
    }

    return jsonify(response), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
