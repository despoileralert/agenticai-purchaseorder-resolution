import boto3

REGION = "us-east-1"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION,
)


def call_llm(prompt: str, system_prompt: str | None = None) -> str:
    client = boto3.client("bedrock-runtime", region_name=REGION)
    response = client.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        # system=[{"text": system_prompt}],
        inferenceConfig={"temperature": 0, "maxTokens": 200}
    )
    return response["output"]["message"]["content"][0]["text"]

print(call_llm("Reply with exactly: Bedrock works"))
