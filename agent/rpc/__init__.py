"""
GLTCH RPC Module
JSON-RPC server for gateway communication.
"""

from agent.rpc.server import RPCServer, handle_rpc_request

__all__ = ["RPCServer", "handle_rpc_request"]
