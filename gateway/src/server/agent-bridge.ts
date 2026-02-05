/**
 * GLTCH Agent Bridge
 * Communicates with the Python agent via JSON-RPC
 */

export interface RPCRequest {
  jsonrpc: '2.0';
  method: string;
  params?: object;
  id: number | string;
}

export interface RPCResponse {
  jsonrpc: '2.0';
  result?: any;
  error?: {
    code: number;
    message: string;
  };
  id: number | string | null;
}

export class AgentBridge {
  private url: string;
  private connected: boolean = false;
  private requestId: number = 1;

  constructor(url: string) {
    this.url = url;
  }

  async ping(): Promise<boolean> {
    try {
      const result = await this.rpc({
        jsonrpc: '2.0',
        method: 'ping',
        params: {},
        id: this.requestId++
      });
      this.connected = !result.error;
      return this.connected;
    } catch {
      this.connected = false;
      return false;
    }
  }

  isConnected(): boolean {
    return this.connected;
  }

  async rpc(request: RPCRequest): Promise<RPCResponse> {
    try {
      const response = await fetch(this.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json() as RPCResponse;
      this.connected = true;
      return data;
    } catch (error) {
      this.connected = false;
      return {
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: error instanceof Error ? error.message : 'Connection failed'
        },
        id: request.id
      };
    }
  }

  async chat(
    message: string,
    sessionId: string = 'default',
    channel: string = 'webchat',
    user?: string
  ): Promise<any> {
    const result = await this.rpc({
      jsonrpc: '2.0',
      method: 'chat_sync',
      params: {
        message,
        session_id: sessionId,
        channel,
        user
      },
      id: this.requestId++
    });

    if (result.error) {
      throw new Error(result.error.message);
    }

    return result.result;
  }

  async getStatus(): Promise<any> {
    const result = await this.rpc({
      jsonrpc: '2.0',
      method: 'status',
      params: {},
      id: this.requestId++
    });

    if (result.error) {
      throw new Error(result.error.message);
    }

    return result.result;
  }

  async setMode(mode: string): Promise<any> {
    const result = await this.rpc({
      jsonrpc: '2.0',
      method: 'set_mode',
      params: { mode },
      id: this.requestId++
    });

    if (result.error) {
      throw new Error(result.error.message);
    }

    return result.result;
  }

  async setMood(mood: string): Promise<any> {
    const result = await this.rpc({
      jsonrpc: '2.0',
      method: 'set_mood',
      params: { mood },
      id: this.requestId++
    });

    if (result.error) {
      throw new Error(result.error.message);
    }

    return result.result;
  }

  async toggleNetwork(state: boolean): Promise<any> {
    const result = await this.rpc({
      jsonrpc: '2.0',
      method: 'toggle_network',
      params: { state },
      id: this.requestId++
    });

    if (result.error) {
      throw new Error(result.error.message);
    }

    return result.result;
  }
}
