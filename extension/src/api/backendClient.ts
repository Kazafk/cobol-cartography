/**
 * Thin HTTP client for the COBOL Cartography backend.
 *
 * Uses the global `fetch` API (available in Node 18+ and VS Code's extension
 * host runtime). All non-2xx responses are thrown as errors carrying the HTTP
 * status code so callers can react appropriately.
 */
export class BackendClient {
    private readonly baseUrl: string;
    private readonly apiKey: string | undefined;

    constructor(baseUrl: string, apiKey?: string) {
        this.baseUrl = baseUrl.replace(/\/$/, ''); // strip trailing slash
        this.apiKey = apiKey;
    }

    /**
     * Builds the common request headers, conditionally adding Authorization.
     */
    private buildHeaders(extra?: Record<string, string>): Record<string, string> {
        const headers: Record<string, string> = { ...extra };
        if (this.apiKey) {
            headers['Authorization'] = `Bearer ${this.apiKey}`;
        }
        return headers;
    }

    /**
     * Performs a GET request and returns the parsed JSON response body.
     * Throws an Error with the HTTP status code on non-2xx responses.
     */
    async get<T>(path: string): Promise<T> {
        const url = `${this.baseUrl}${path}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: this.buildHeaders(),
        });

        if (!response.ok) {
            throw new Error(
                `GET ${path} failed with status ${response.status}: ${response.statusText}`
            );
        }

        return response.json() as Promise<T>;
    }

    /**
     * Performs a POST request with a JSON body and returns the parsed JSON
     * response body.
     * Throws an Error with the HTTP status code on non-2xx responses.
     */
    async post<T>(path: string, body: unknown): Promise<T> {
        const url = `${this.baseUrl}${path}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: this.buildHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            throw new Error(
                `POST ${path} failed with status ${response.status}: ${response.statusText}`
            );
        }

        return response.json() as Promise<T>;
    }
}
