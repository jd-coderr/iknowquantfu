import { createX402AxiosClient } from "@x402/axios";
import { ExactEvmScheme, toClientEvmSigner } from "@x402/evm";
import { privateKeyToAccount } from "viem/accounts";
import { createPublicClient, http } from "viem";
import { base } from "viem/chains";

const CMC_X402_QUOTES_URL =
  "https://pro-api.coinmarketcap.com/x402/v3/cryptocurrency/quotes/latest";

function normalizePrivateKey(value) {
  if (!value) return null;
  const trimmed = String(value).trim();
  return trimmed.startsWith("0x") ? trimmed : `0x${trimmed}`;
}

function normalizeSymbol(value) {
  return (
    String(value || "ETH")
      .toUpperCase()
      .replace("USDT", "")
      .replace("/", "")
      .replace("-", "")
      .trim() || "ETH"
  );
}

function extractPrice(payload, symbol) {
  try {
    const data = payload?.data || {};
    const coinData = data[symbol] || data[symbol.toUpperCase()] || Object.values(data)[0];
    const price = coinData?.quote?.USD?.price;
    return typeof price === "number" ? price : Number(price);
  } catch {
    return null;
  }
}

function safeHeaders(headers) {
  const output = {};
  for (const [key, value] of Object.entries(headers || {})) {
    const lower = String(key).toLowerCase();
    if (
      lower === "authorization" ||
      lower === "payment" ||
      lower === "payment-signature" ||
      lower === "x-api-key" ||
      lower === "cookie" ||
      lower === "set-cookie"
    ) {
      output[key] = "REDACTED";
    } else {
      output[key] = value;
    }
  }
  return output;
}

async function main() {
  const symbol = normalizeSymbol(process.argv[2] || "ETH");
  const privateKey = normalizePrivateKey(
    process.env.X402_EVM_PRIVATE_KEY || process.env.EVM_PRIVATE_KEY
  );

  if (!privateKey) {
    console.log(
      JSON.stringify({
        success: false,
        paid: false,
        used_in_decision: false,
        status: "not_configured",
        message: "Missing X402_EVM_PRIVATE_KEY or EVM_PRIVATE_KEY",
        symbol,
      })
    );
    process.exit(0);
  }

  const account = privateKeyToAccount(privateKey);

  const publicClient = createPublicClient({
    chain: base,
    transport: http(),
  });

  const signer = toClientEvmSigner(account, publicClient);

  const client = createX402AxiosClient({
    schemes: [new ExactEvmScheme(signer)],
  });

  try {
    const response = await client.get(CMC_X402_QUOTES_URL, {
      params: { symbol },
      timeout: 30000,
    });

    const priceUsd = extractPrice(response.data, symbol);
    const success = Boolean(response.status === 200 && priceUsd);

    console.log(
      JSON.stringify({
        success,
        paid: response.status === 200,
        used_in_decision: success,
        status: response.status === 200 ? "paid" : "request_failed",
        http_status: response.status,
        symbol,
        price_usd: priceUsd,
        provider: "CoinMarketCap",
        protocol: "x402",
        endpoint: CMC_X402_QUOTES_URL,
        payment_network: "Base",
        payment_chain_id: 8453,
        payment_asset: "USDC",
        expected_price_usd: "0.01",
        wallet_address: account.address,
        payment_response_header_present: Boolean(
          response.headers?.["payment-response"] ||
            response.headers?.["x-payment-response"]
        ),
        response_headers: safeHeaders(response.headers),
        message:
          response.status === 200
            ? "CMC x402 quote paid and returned successfully through TypeScript SDK."
            : "CMC x402 request returned non-200 status.",
      })
    );
  } catch (error) {
    const status = error?.response?.status || null;
    const data = error?.response?.data || null;
    const headers = error?.response?.headers || null;

    console.log(
      JSON.stringify({
        success: false,
        paid: false,
        used_in_decision: false,
        status: "error",
        http_status: status,
        symbol,
        provider: "CoinMarketCap",
        protocol: "x402",
        endpoint: CMC_X402_QUOTES_URL,
        payment_network: "Base",
        payment_chain_id: 8453,
        payment_asset: "USDC",
        expected_price_usd: "0.01",
        wallet_address: account.address,
        response_body_preview: data,
        response_headers: safeHeaders(headers),
        message: error?.message || "CMC x402 TypeScript request failed.",
      })
    );
  }
}

main();