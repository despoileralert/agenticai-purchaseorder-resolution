import streamlit as st
import json

from src.agenticai_purchaseorder_resolution.agents.workflow_agents import InvoiceExtractionAgent
from agenticai_purchaseorder_resolution.utils.tools import extract_invoice
from orchestration.graph import orchestrator
from repositories.repository import get_all_order_items, save_parsed_invoice, clear_database

st.set_page_config(page_title="Purchase Order Resolution", page_icon="📦", layout="centered")

# clear_database()
# st.session_state.clear()

def initialize_state():
    if "orders" not in st.session_state:
        st.session_state.orders = []

    if "pending_approval" not in st.session_state:
        st.session_state.pending_approval = None


initialize_state()

@st.cache_resource
def get_invoice_agent():
    return InvoiceExtractionAgent(tools=[extract_invoice])


# Temporary mock agent 1
def parse_invoice(uploaded_file):
    invoice_agent = get_invoice_agent()
    # task = "Can you extract structured data from the invoice b92929cd_7204_465d_b7bf_f8946a395f53_inv_2026_4100.pdf under the bucket \
    #            textract-console-us-east-1-886235d2-d763-4a23-b78a-7f0375f8038d?"

    # task = "Can you extract structured data from the invoice INV-2026-4100.pdf under the bucket \
    #         textract-console-ap-southeast-1-56e9d1de-c238-48a1-b770-926a9e7?"
    # result = invoice_agent.run(task)
    # invoice = json.loads(result)

    # mock result
    invoice = {
        "line_items": [
            {"part_number": "30112", "quantity": 250, "unit_price": 349.38},
            {"part_number": "88204", "quantity": 25, "unit_price": 123.79}
        ],
        "vendor_id": "5a2c1ca6-30ca-45b9-98c8-abc23e5062c4",
        "invoice_id": "INV-2026-4100",
        "expected_delivery_date": None,
        "purchase_order_id": "PO-82046",
        "delivery_dates": [],
        "vendor_info": {"name": "Meridian Components Pte Ltd.", "contact": None}
    }
    save_parsed_invoice(invoice)
    parsed_invoice = []
    for item in invoice["line_items"]:
        parsed_invoice.append({
            "part_number": item["part_number"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "vendor_id": invoice["vendor_id"],
            "invoice_id": invoice["invoice_id"],
            "expected_delivery_date": invoice["expected_delivery_date"],
            "purchase_order_id": invoice["purchase_order_id"],
            "delivery_dates": invoice["delivery_dates"],
            "vendor_name": invoice["vendor_info"]["name"],
            "vendor_contact": invoice["vendor_info"]["contact"]
        })
    return parsed_invoice


def show_main_page():
    st.title("Purchase Order Resolution")
    st.write("Upload an invoice to begin processing.")

    uploaded_file = st.file_uploader("Invoice", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        if st.button("Process Invoice", type="primary"):
            with st.spinner("Parsing invoice..."):
                invoice = parse_invoice(uploaded_file)
                st.success("Invoice parsed successfully!")
                for item in invoice:
                    st.session_state.orders.append(item)

            # st.rerun()

    if not st.session_state.orders:
        return

    st.divider()
    orders = get_all_order_items()
    if orders:
        st.subheader("Orders")
        st.dataframe(st.session_state.orders, width="stretch", hide_index=True)

    st.divider()
    if st.button("Track Orders", type="primary", width="stretch"):
        with st.spinner("Checking supplier updates..."):
            result = orchestrator.invoke({
                "orders": st.session_state.orders
            })

        replacement = result.get("replacement_result")

        if replacement:
            st.session_state.pending_approval = replacement
            st.rerun()

        else:
            st.success("No replacement action is required!")

# Approval screen
def show_approval():
    replacement = st.session_state.pending_approval

    st.title("Replacement Approval")
    st.warning(
        "The original item is unavailable. "
        "A replacement supplier has been found."
    )
    st.subheader("Item")
    st.write(
        f"**Part Number:** "
        f"{replacement["request"].part_number}"
    )
    st.write(
        f"**Quantity:** "
        f"{replacement["request"].quantity}"
    )
    st.divider()

    # Recommendation
    st.subheader("Recommended Supplier")

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Supplier",
        replacement["recommended_offer"].offer.supplier_name,
    )
    col2.metric(
        "Unit Price",
        (
            "SGD "
            f"{replacement["recommended_offer"].offer.unit_price:.2f}"
        ),
    )
    col3.metric(
        "Total",
        (
            "SGD "
            f"{(replacement["request"].quantity * replacement["recommended_offer"].offer.unit_price):.2f}"
        ),
    )
    st.divider()

    # Email preview
    st.subheader("Email Preview")
    st.text_input("To", value=replacement["recommended_offer"].offer.supplier_email, disabled=True)
    subject = st.text_input("Subject", value=replacement["email_draft"].subject)
    body = st.text_area("Message", value=replacement["email_draft"].body, height=300)

    st.caption("Review or edit the email before approving.")

    st.divider()

    # Approval
    reject_col, approve_col = st.columns(2)

    with reject_col:
        if st.button("Reject", width="stretch"):
            replacement["status"] = "REJECTED"
            st.session_state.pending_approval = None
            st.rerun()

    with approve_col:
        if st.button("Approve & Send", type="primary", width="stretch"):
            replacement["email_subject"] = subject
            replacement["email_body"] = body
            replacement["status"] = "APPROVED"
            # To add email sending or routing

            st.success("Purchase request approved.")
            st.session_state.pending_approval = None

# Application routing
if st.session_state.pending_approval:
    show_approval()
else:
    show_main_page()
