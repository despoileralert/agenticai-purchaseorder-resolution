# Agentic AI 3-way Purchase order exception resolution agent

This project will let a purchasing client track order invoices and receipt records to check for any discrepancies in orders made and goods received. The agentic system flags this to a human who will then decide whether or not to have an agent autonomously call a emailing tool to reach out to the supplier to, and another agent to make a separate purchase should the original supplier encounter issues in fulfiling their end of the order.

# Architectural diagram
Invoice arrives → three-way match against PO and goods receipt → flags the $340 discrepancy → drafts the supplier email asking about it \
OR \
Supplier emails "shipment delayed 2 weeks" → agent parses it, checks which production orders depend on that part, finds an alternate supplier with stock, prices the switch, and puts a recommendation in front of a human for approval (Diagram comes later)