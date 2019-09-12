import rlp
from eth_utils import keccak, to_checksum_address, to_bytes
def mk_contract_address(sender, nonce):
         """ Create a contract address using eth-utils. """
         sender_bytes = to_bytes(hexstr=sender)
         raw = rlp.encode([sender_bytes, nonce])
         h = keccak(raw)
         address_bytes = h[12:]
         return to_checksum_address(address_bytes)

for x in range(1,255):
         addr = mk_contract_address("0x2f5551674A7c8CB6DFb117a7F2016C849054fF80",x)
         print(f"nonce: {x} contract: {addr}")
