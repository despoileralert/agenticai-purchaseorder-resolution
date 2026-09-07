import boto3
import json

from .models import ItemMatchResult, ReplacementRequest, SupplierOffer, ValidatedOffer, EmailDraft

REGION = "us-east-1"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Helper function for parsing json
def parse_json_response(text: str) -> dict:
    text = text.strip()

    # Handle ```json ... ``` responses
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last Markdown fences
        lines = lines[1:-1]
        text = "\n".join(lines)

    return json.loads(text)

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION
)


def call_llm(prompt: str, system_prompt: str | None = None) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"text": prompt}
            ],
        }
    ]

    kwargs = {
        "modelId": MODEL_ID,
        "messages": messages,
        "inferenceConfig": {
            "temperature": 0,
            "maxTokens": 1000,
        },
    }

    if system_prompt:
        kwargs["system"] = [
            {"text": system_prompt}
        ]

    response = bedrock.converse(**kwargs)

    return response["output"]["message"]["content"][0]["text"]


def validate_item_match(request: ReplacementRequest, offer: SupplierOffer) -> ItemMatchResult:
    prompt = f"""
    Determine whether the supplier's item is equivalent to the requested item.

    Requested item:
    Part number: {request.part_number}
    Vendor name: {request.vendor_name}

    Supplier item:
    Part number: {offer.part_number}
    Supplier name: {offer.supplier_name}
    
    Return ONLY valid JSON using this exact structure:

    {{
        "is_match": true | false,
        "confidence": 0.0,
        "reason": "brief explanation"
    }}

    Be conservative.
    Differences in dimensions, material, model, specification, rating or compatibility
    may make the item unsuitable.
    """

    response = call_llm(prompt)
    # print(response)
    data = parse_json_response(response)

    return ItemMatchResult.model_validate(data)

def draft_purchase_email(request: ReplacementRequest, recommendation: ValidatedOffer) -> EmailDraft:
    prompt = f"""
    Draft a concise professional purchase request.
        
    Supplier: {recommendation.offer.supplier_name}
    Email: {recommendation.offer.supplier_email}
    Part: {request.part_number}
    Quantity: {request.quantity}
    Quoted unit price: SGD {recommendation.offer.unit_price}
    
    Do not invent delivery dates, prices, quantities, specifications or commercial terms.
    
    Ask the supplier to confirm availability, final price and expected delivery date.
    
    Return ONLY valid JSON:

    {{
        "subject": "...",
        "body": "..."
    }}
    """

    response = call_llm(prompt)
    data = parse_json_response(response)

    return EmailDraft.model_validate(data)
