import os
import json
from web3 import Web3
from typing import Optional
import logging
from pydantic import BaseModel
from threading import Lock


class Notification(BaseModel):
    sender: str
    content: str
    timestamp: int

logger = logging.getLogger(__name__)

CONTRACT_ABI_PATH = os.getenv("CONTRACT_ABI_PATH", "./contract_abi.json")

class BlockchainClient:
    def __init__(self):
        self.web3_provider = os.getenv("WEB3_PROVIDER_URI", "https://otter.bordel.wtf/erigon")
        self.contract_address = os.getenv("CONTRACT_ADDRESS", "0xA261536da2a6652461A20e45424ED7add2DD6133")
        self.private_key = os.getenv("PRIVATE_KEY", "52068cf810e2a2fb90328d3ea18c027ddf203514e0445f6ba8188bcf75617eda")
        self.w3: Optional[Web3] = None
        self.contract = None
        self.account = None
        self.nonce_lock = Lock()
        self.current_nonce: Optional[int] = None
        
    def connect(self):
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.web3_provider))
            
            if not self.w3.is_connected():
                raise Exception(f"Failed to connect to blockchain at {self.web3_provider}")
            
            logger.info(f"Connected to blockchain at {self.web3_provider}")
            
            if not self.contract_address:
                logger.warning("CONTRACT_ADDRESS not set. Blockchain operations will fail.")
                return
            
            if not self.private_key:
                logger.warning("PRIVATE_KEY not set. Blockchain operations will fail.")
                return
            
            with open(CONTRACT_ABI_PATH, 'r') as f:
                contract_abi = json.load(f)
            
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=contract_abi
            )
            
            self.account = self.w3.eth.account.from_key(self.private_key)
            logger.info(f"Initialized contract at {self.contract_address} with account {self.account.address}")
            
        except Exception as e:
            logger.error(f"Error connecting to blockchain: {e}")
            raise
    
    def add_notification(self, latitude: float, longitude: float, content: str) -> str:
        if not self.w3 or not self.contract or not self.account:
            raise Exception("Blockchain client not properly initialized")
        
        with self.nonce_lock:
            try:
                lat_scaled = int(latitude * 1e6)
                lon_scaled = int(longitude * 1e6)
                
                if self.current_nonce is None:
                    self.current_nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
                
                nonce = self.current_nonce
                logger.info(f"Using nonce {nonce} for transaction")
                
                transaction = self.contract.functions.addNotification(
                    lat_scaled,
                    lon_scaled,
                    content
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': nonce,
                    'gas': 2000000,
                    'gasPrice': self.w3.eth.gas_price
                })
                
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                
                self.current_nonce += 1
                
                logger.info(f"Transaction sent: {tx_hash.hex()}")
                
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if tx_receipt['status'] == 1:
                    logger.info(f"Notification added successfully for coordinates ({latitude}, {longitude}). Tx: {tx_hash.hex()}")
                    return tx_hash.hex()
                else:
                    self.current_nonce = None
                    raise Exception(f"Transaction failed with status {tx_receipt['status']}")
                    
            except Exception as e:
                self.current_nonce = None
                logger.error(f"Error adding notification to blockchain: {e}")
                raise
    
    def get_notifications(self, latitude: float, longitude: float, since: int) -> list[Notification]:
        if not self.w3 or not self.contract:
            raise Exception("Blockchain client not properly initialized")
        
        try:
            lat_scaled = int(latitude * 1e6)
            lon_scaled = int(longitude * 1e6)
            
            notifications = self.contract.functions.getNotificationsSince(
                lat_scaled,
                lon_scaled,
                since
            ).call()
            
            result = []
            for notification in notifications:
                result.append(Notification(
                    sender=notification[0],
                    content=notification[1],
                    timestamp=notification[2]
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting notifications from blockchain: {e}")
            raise
